#!/usr/bin/env python3
"""tools/build_v20_suite.py — Compilador Multi-DataType e Empacotador SDK 3.7b para Vampiro_V20_Suite.rpk."""
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


def main() -> None:
    compiler = load_base_compiler()
    subprocess.run(
        [sys.executable, os.path.join(ROOT, "Templates", "generate_vampire_lfm.py"), "--clan", "brujah"],
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
        + [os.path.join(ROOT, "v20_loader.lua")]
    ):
        with open(lua_src, "r", encoding="utf-8") as f:
            compiler.validate_lua_syntax(f.read(), "@" + os.path.relpath(lua_src, ROOT).replace("\\", "/"))

    lfm_entries = ["Sheets/frmBrujah.lfm", "Sheets/frmMortal.lfm"]
    compiled_map = {}
    anchor = 'local __o_Utils = require("utils.lua");'
    for rel in lfm_entries:
        raw_lua = compiler.compile_lfm_to_lua(os.path.join(ROOT, rel))
        if anchor not in raw_lua:
            raise RuntimeError(f"Âncora de cabeçalho SDK não encontrada ao compilar {rel}")
        injected = raw_lua.replace(
            anchor,
            anchor + '\nrequire("v20_loader.lua");',
            1,
        )
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

    dist_dir = os.path.join(ROOT, "dist")
    os.makedirs(dist_dir, exist_ok=True)
    out_rpk = os.path.join(dist_dir, "Vampiro_V20_Suite.rpk")
    out_rdk = os.path.join(dist_dir, "Vampiro_V20_Suite.rdk")
    assembled_xml = build_multi_assembled_xml(
        os.path.join(ROOT, "module.xml"), lfm_entries, "Vampiro_V20_Suite.rpk"
    )

    with zipfile.ZipFile(out_rpk, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("module.xml", assembled_xml)
        zf.write(REF_CLN, "_rdkCompiledLang.cln")
        zf.write(os.path.join(ROOT, "v20_loader.lua"), "v20_loader.lua")
        for folder in ("Data", "Core", "Adapter"):
            for p in sorted(glob.glob(os.path.join(ROOT, folder, "*.lua"))):
                zf.write(p, f"{folder}/{os.path.basename(p)}")
        for rel, lua_txt in compiled_map.items():
            zf.write(os.path.join(ROOT, rel), rel)
            zf.writestr(rel + ".lua", lua_txt)
        for item in sorted(os.listdir(REF_SDK_DIR)):
            s = os.path.join(REF_SDK_DIR, item)
            if os.path.isfile(s):
                zf.write(s, f"sdk/{item}")

    shutil.copy2(out_rpk, out_rdk)
    print(f"[OK] Gerado {out_rpk} e {out_rdk}")


if __name__ == "__main__":
    main()
