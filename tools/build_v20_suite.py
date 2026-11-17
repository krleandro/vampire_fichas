#!/usr/bin/env python3
"""tools/build_v20_suite.py — Compilador Multi-DataType e Empacotador SDK 3.7b para Vampiro_V20_Suite.rpk."""
import argparse
import datetime
import glob
import hashlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
import zipfile

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SKILL_COMPILER = r"C:\Users\Cliente\.gemini\config\skills\firecast-ficha\scripts\compile_firecast_rpk.py"
REF_SDK_DIR = r"c:\Users\Cliente\OneDrive\Documentos\event\firecast_event_ficha\sdk"
REF_CLN = r"c:\Users\Cliente\OneDrive\Documentos\event\firecast_event_ficha\output\rdkObjs\_rdkCompiledLang.cln"

CLAN_FORM_FILES = [
    "Sheets/frmBrujah.lfm",
    "Sheets/frmGangrel.lfm",
    "Sheets/frmMalkavian.lfm",
    "Sheets/frmNosferatu.lfm",
    "Sheets/frmToreador.lfm",
    "Sheets/frmTremere.lfm",
    "Sheets/frmVentrue.lfm",
    "Sheets/frmAssamite.lfm",
    "Sheets/frmSetite.lfm",
    "Sheets/frmGiovanni.lfm",
    "Sheets/frmLasombra.lfm",
    "Sheets/frmRavnos.lfm",
    "Sheets/frmTzimisce.lfm",
    "Sheets/frmCaitiff.lfm",
]
LFM_ENTRIES = CLAN_FORM_FILES + ["Sheets/frmMortal.lfm"]


def _xml_text(val: str) -> str:
    return escape(val or "")


def _xml_attr(val: str) -> str:
    return escape(val or "", {'"': "&quot;", "'": "&apos;"})


def load_base_compiler():
    spec = importlib.util.spec_from_file_location("compile_firecast_rpk", SKILL_COMPILER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Compilador base não encontrado em {SKILL_COMPILER}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def compile_v20_lfm(compiler, lfm_path: str) -> str:
    """
    Compila um arquivo .lfm via compilador base SDK 3.7b e aplica pós-processamento V20:
    1. Injeta require("v20_loader.lua"); após utils.lua;
    2. Propaga width/height na raiz <form> (ex.: tablesDock 340x580);
    3. Compila tags <event name="..."> filhas diretas de <form> em obj._e_form_event{k}
       e libera em ordem reversa dentro de obj:_releaseEvents();
    4. Injeta hook if self._onBeforeDestroy ~= nil then self:_onBeforeDestroy(); end; no início de obj:destroy();
    5. Quando formType == "tablesDock", injeta Firecast.registrarSpecialForm(_{form_name}); após registrarDataType.
    """
    root = ET.parse(lfm_path).getroot()
    form_name = root.attrib.get("name", "frmFicha")
    form_type = root.attrib.get("formType", "sheetTemplate")
    theme = root.attrib.get("theme", "dark")

    raw_lua = compiler.compile_lfm_to_lua(lfm_path)
    header_anchor = 'local __o_Utils = require("utils.lua");'
    if header_anchor not in raw_lua:
        raise RuntimeError(f"Âncora de cabeçalho SDK não encontrada ao compilar {lfm_path}")
    injected = raw_lua.replace(
        header_anchor,
        header_anchor + '\nrequire("v20_loader.lua");',
        1,
    )

    dim_lines: list[str] = []
    if "width" in root.attrib:
        dim_lines.append(f'    obj:setWidth({root.attrib["width"]});')
    if "height" in root.attrib:
        dim_lines.append(f'    obj:setHeight({root.attrib["height"]});')
    if dim_lines:
        theme_anchor = f'    obj:setTheme("{theme}");'
        if theme_anchor in injected:
            injected = injected.replace(
                theme_anchor,
                theme_anchor + "\n" + "\n".join(dim_lines),
                1,
            )

    form_events: list[tuple[str, str]] = []
    for child in root:
        if child.tag == "event":
            ev_name = child.attrib["name"]
            ev_code = (child.text or "").strip()
            form_events.append((ev_name, ev_code))

    release_anchor = "    function obj:_releaseEvents()"
    if release_anchor not in injected:
        raise RuntimeError(f"Âncora _releaseEvents não encontrada ao compilar {lfm_path}")

    if form_events:
        add_lines: list[str] = []
        for k, (ev_name, ev_code) in enumerate(form_events):
            esc_ev = ev_name.replace("\\", "\\\\").replace('"', '\\"')
            add_lines.append(f'    obj._e_form_event{k} = obj:addEventListener("{esc_ev}",')
            add_lines.append("        function (_)")
            for line in ev_code.splitlines():
                add_lines.append("            " + line)
            add_lines.append("        end, obj);")
            add_lines.append("")

        rem_lines: list[str] = []
        for k in range(len(form_events) - 1, -1, -1):
            rem_lines.append(f"        __o_rrpgObjs.removeEventListenerById(self._e_form_event{k});")

        injected = injected.replace(
            release_anchor,
            "\n".join(add_lines) + "\n" + release_anchor + "\n" + "\n".join(rem_lines),
            1,
        )

    destroy_anchor = "    function obj:destroy()\n        self:_releaseEvents();"
    if destroy_anchor not in injected:
        raise RuntimeError(f"Âncora obj:destroy() não encontrada ao compilar {lfm_path}")
    injected = injected.replace(
        destroy_anchor,
        "    function obj:destroy()\n"
        "        if self._onBeforeDestroy ~= nil then self:_onBeforeDestroy(); end;\n"
        "        self:_releaseEvents();",
        1,
    )

    if form_type == "tablesDock":
        dt_reg_anchor = f"Firecast.registrarDataType(_{form_name});"
        if dt_reg_anchor not in injected:
            raise RuntimeError(f"Âncora registrarDataType não encontrada ao compilar {lfm_path}")
        injected = injected.replace(
            dt_reg_anchor,
            f"{dt_reg_anchor}\nFirecast.registrarSpecialForm(_{form_name});",
            1,
        )

    return injected


def build_multi_assembled_xml(mod_path: str, lfm_entries: list[str], rpk_filename: str) -> str:
    mod_root = ET.parse(mod_path).getroot()
    mod_id = (mod_root.findtext("id") or "").strip()
    version = (mod_root.findtext("version") or "").strip()
    info = mod_root.find("info")
    if info is None:
        raise RuntimeError(f"Bloco <info> ausente em {mod_path}")
    name = (info.findtext("name") or "").strip()
    desc = (info.findtext("description") or "").strip()
    author = (info.findtext("author") or "").strip()
    site = (info.findtext("site") or "").strip()
    contact = (info.findtext("contact") or "").strip()

    dt_lines, asm_lines = [], []
    for rel in lfm_entries:
        rel_norm = rel.replace("\\", "/")
        r = ET.parse(os.path.join(ROOT, rel_norm)).getroot()
        f_name = r.attrib["name"]
        f_type = r.attrib.get("formType", "sheetTemplate")
        d_type = r.attrib["dataType"]
        f_title = r.attrib["title"]
        dt_lines.append(
            f'        <dataType title="{_xml_attr(f_title)}" name="{_xml_attr(f_name)}" '
            f'lfmFile="{_xml_attr(rel_norm)}">{_xml_text(d_type)}</dataType>'
        )
        asm_lines.append(
            f'            <dataType id="{_xml_attr(d_type)}" formType="{_xml_attr(f_type)}" '
            f'lfmFile="{_xml_attr(rel_norm)}" formName="{_xml_attr(f_name)}">\n'
            f'                <info title="{_xml_attr(f_title)}"/>\n'
            f"            </dataType>"
        )

    now_str = datetime.datetime.now().strftime("%d%m%Y%H%M%S")
    digest = hashlib.sha1(f"{mod_id}:{version}:{now_str}".encode("utf-8")).hexdigest()
    uid = hashlib.md5(f"{mod_id}:{now_str}".encode("utf-8")).hexdigest()[:24]

    assembled_xml = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<module sdkVersion="3.7b" originalPluginFileName="{_xml_attr(rpk_filename)}" '
        f'compilationDate="{_xml_attr(now_str)}" sdkApiVersion="88" sdkMinorApiVersion="2" '
        f'compilationDigest="{_xml_attr(digest)}" compilationUniqueID="{_xml_attr(uid)}">\n'
        f"    <id>{_xml_text(mod_id)}</id>\n"
        f"    <version>{_xml_text(version)}</version>\n"
        f'    <info lang="pt-BR">\n'
        f"        <name>{_xml_text(name)}</name>\n"
        f"        <description>{_xml_text(desc)}</description>\n"
        f"        <author>{_xml_text(author)}</author>\n"
        f"        <site>{_xml_text(site)}</site>\n"
        f"        <contact>{_xml_text(contact)}</contact>\n"
        f"    </info>\n"
        f"    <dataTypes>\n" + "\n".join(dt_lines) + "\n    </dataTypes>\n"
        f"    <assembledFeatures>\n        <dataTypes>\n" + "\n".join(asm_lines) + "\n        </dataTypes>\n    </assembledFeatures>\n"
        f"    <name>{_xml_text(name)}</name>\n"
        f"    <description>{_xml_text(desc)}</description>\n"
        f"    <author>{_xml_text(author)}</author>\n"
        f"    <site>{_xml_text(site)}</site>\n"
        f"    <contact>{_xml_text(contact)}</contact>\n"
        f"</module>\n"
    )
    ET.fromstring(assembled_xml)
    return assembled_xml


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Compila e empacota a suíte Vampiro: A Máscara V20 para o RRPG Firecast (SDK 3.7b)."
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join(ROOT, "dist"),
        help="Diretório de saída para Vampiro_V20_Suite.rpk/.rdk (padrão: <ROOT>/dist).",
    )
    parser.add_argument(
        "--skip-regenerate",
        action="store_true",
        help="Pula a regeneração prévia dos arquivos .lfm em Sheets/.",
    )
    args = parser.parse_args(argv)

    compiler = load_base_compiler()
    if not args.skip_regenerate:
        subprocess.run(
            [sys.executable, os.path.join(ROOT, "Templates", "generate_vampire_lfm.py"), "--all-clans"],
            check=True,
        )
        subprocess.run(
            [sys.executable, os.path.join(ROOT, "Templates", "generate_mortal_lfm.py")],
            check=True,
        )

    if not os.path.exists(REF_CLN):
        raise FileNotFoundError(f"_rdkCompiledLang.cln não encontrado em {REF_CLN}")

    # PF-4: Auditar métodos :setXxx( contra a concatenação de AMBOS sdk/rrpgGUI.lua E sdk/rrpgObjs.lua
    with open(os.path.join(REF_SDK_DIR, "rrpgGUI.lua"), "r", encoding="utf-8", errors="ignore") as f:
        gui_sdk = f.read()
    with open(os.path.join(REF_SDK_DIR, "rrpgObjs.lua"), "r", encoding="utf-8", errors="ignore") as f:
        objs_sdk = f.read()
    sdk_methods_ref = gui_sdk + "\n" + objs_sdk

    for lua_src in sorted(
        glob.glob(os.path.join(ROOT, "Data", "*.lua"))
        + glob.glob(os.path.join(ROOT, "Core", "*.lua"))
        + glob.glob(os.path.join(ROOT, "Adapter", "*.lua"))
        + [os.path.join(ROOT, "v20_shim.dlua"), os.path.join(ROOT, "v20_loader.lua")]
    ):
        with open(lua_src, "r", encoding="utf-8") as f:
            compiler.validate_lua_syntax(f.read(), "@" + os.path.relpath(lua_src, ROOT).replace("\\", "/"))

    # Fix Round 1: Prepend require("v20_shim.dlua"); na linha 1 de Core/*.lua e Adapter/*.lua no .rpk
    # para garantir que o auto-boot alfabético do VHD do Firecast inicialize o shim antes de qualquer require.
    shim_prefix = 'require("v20_shim.dlua"); '
    packaged_modules: dict[str, str] = {}
    for folder in ("Data", "Core", "Adapter"):
        for p in sorted(glob.glob(os.path.join(ROOT, folder, "*.lua"))):
            rel_entry = f"{folder}/{os.path.basename(p)}"
            with open(p, "r", encoding="utf-8") as f:
                src_txt = f.read()
            if folder in ("Core", "Adapter") and not src_txt.startswith(shim_prefix):
                src_txt = shim_prefix + src_txt
                compiler.validate_lua_syntax(src_txt, f"@{rel_entry}")
            packaged_modules[rel_entry] = src_txt

    compiled_map: dict[str, str] = {}
    for rel in LFM_ENTRIES:
        injected = compile_v20_lfm(compiler, os.path.join(ROOT, rel))
        compiler.validate_lua_syntax(injected, f"@{rel}.lua")
        methods = set(re.findall(r":(set[A-Za-z0-9_]+)\(", injected))
        missing = [
            m
            for m in sorted(methods)
            if m not in ("setNodeObject", "setNodeDatabase") and m not in sdk_methods_ref
        ]
        if missing:
            raise RuntimeError(f"Métodos inválidos em {rel} frente a sdk/rrpgGUI.lua + sdk/rrpgObjs.lua: {missing}")
        compiled_map[rel] = injected

    dist_dir = os.path.abspath(args.output_dir)
    os.makedirs(dist_dir, exist_ok=True)
    out_rpk = os.path.join(dist_dir, "Vampiro_V20_Suite.rpk")
    out_rdk = os.path.join(dist_dir, "Vampiro_V20_Suite.rdk")
    assembled_xml = build_multi_assembled_xml(
        os.path.join(ROOT, "module.xml"), LFM_ENTRIES, "Vampiro_V20_Suite.rpk"
    )

    with zipfile.ZipFile(out_rpk, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("module.xml", assembled_xml)
        zf.write(REF_CLN, "_rdkCompiledLang.cln")
        zf.write(os.path.join(ROOT, "v20_shim.dlua"), "v20_shim.dlua")
        zf.write(os.path.join(ROOT, "v20_loader.lua"), "v20_loader.lua")
        for rel_entry, lua_txt in packaged_modules.items():
            zf.writestr(rel_entry, lua_txt)
        for rel, lua_txt in compiled_map.items():
            zf.write(os.path.join(ROOT, rel), rel)
            zf.writestr(rel + ".lua", lua_txt)
        for item in sorted(os.listdir(REF_SDK_DIR)):
            s = os.path.join(REF_SDK_DIR, item)
            if os.path.isfile(s):
                zf.write(s, f"sdk/{item}")

    shutil.copy2(out_rpk, out_rdk)
    print(f"[OK] Gerado {out_rpk} e {out_rdk} ({len(LFM_ENTRIES)} modelos de ficha)")


if __name__ == "__main__":
    main()
