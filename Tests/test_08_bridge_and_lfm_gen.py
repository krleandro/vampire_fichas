#!/usr/bin/env python3
"""Valida a ponte Firecast em Lua 5.4 (com mock de sala/rolado.ops) e a geração XML dos LFMs."""
import importlib.util
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from Tests.run_tests import run_lua_file  # noqa: E402

SKILL_COMPILER = r"C:\Users\Cliente\.gemini\config\skills\firecast-ficha\scripts\compile_firecast_rpk.py"
REF_GUI_LUA = r"c:\Users\Cliente\OneDrive\Documentos\event\firecast_event_ficha\sdk\rrpgGUI.lua"

ALLOWED_TAGS = {
    "form",
    "script",
    "tabControl",
    "tab",
    "scrollBox",
    "layout",
    "rectangle",
    "label",
    "edit",
    "comboBox",
    "checkBox",
    "button",
    "textEditor",
    "dataLink",
    "event",
}

FORM_EXTRA_ATTRS = {"name", "formType", "dataType", "title", "align", "theme"}


def load_skill_compiler():
    spec = importlib.util.spec_from_file_location("compile_firecast_rpk", SKILL_COMPILER)
    assert spec is not None and spec.loader is not None, f"Compilador não encontrado em {SKILL_COMPILER}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def verify_lfm_xml_and_compile(
    compiler,
    gui_sdk: str,
    rel_path: str,
    expected_dt: str,
    expected_name: str,
    expected_form_type: str = "sheetTemplate",
) -> ET.Element:
    full = os.path.join(ROOT, rel_path)
    assert os.path.exists(full), f"Arquivo {rel_path} não gerado"
    root = ET.parse(full).getroot()
    assert root.tag == "form", f"Raiz de {rel_path} deve ser <form>"
    assert root.attrib.get("dataType") == expected_dt, f"dataType inesperado em {rel_path}"
    assert root.attrib.get("name") == expected_name, f"name inesperado em {rel_path}"
    assert root.attrib.get("formType") == expected_form_type, (
        f"formType deve ser {expected_form_type} em {rel_path}, obteve {root.attrib.get('formType')}"
    )
    assert root.attrib.get("theme") == "dark", f"theme deve ser dark em {rel_path}"
    assert root.attrib.get("title"), f"title obrigatório em {rel_path}"

    allowed_ctrl_attrs = set(compiler.PROP_MAP.keys()) | {"name"}

    for el in root.iter():
        assert el.tag not in ("recordList", "template"), f"Tag proibida <{el.tag}> em {rel_path} (Ruling T8-1)"
        assert el.tag in ALLOWED_TAGS, f"Tag desconhecida <{el.tag}> em {rel_path}"

        if el is root:
            unknown = set(el.attrib.keys()) - (allowed_ctrl_attrs | FORM_EXTRA_ATTRS)
            assert not unknown, f"Atributos inválidos em <form> ({rel_path}): {unknown}"
        elif el.tag == "event":
            assert set(el.attrib.keys()) == {"name"}, f"<event> só deve ter atributo name em {rel_path}"
        elif el.tag == "script":
            assert not el.attrib, f"<script> não deve ter atributos em {rel_path}"
        else:
            unknown = set(el.attrib.keys()) - allowed_ctrl_attrs
            assert not unknown, f"Atributos fora do PROP_MAP em <{el.tag}> ({rel_path}): {unknown}"
            # Shape-only props permitidos apenas em <rectangle>
            shape_only = {"color", "strokeColor", "strokeSize", "xradius", "yradius"}
            if el.tag != "rectangle":
                bad_shape = set(el.attrib.keys()) & shape_only
                assert not bad_shape, f"Atributos exclusivos de <rectangle> usados em <{el.tag}> ({rel_path}): {bad_shape}"
            if el.tag == "dataLink":
                bad_dl = set(el.attrib.keys()) - {"name", "field", "fields", "defaultValues"}
                assert not bad_dl, f"Atributos inválidos em <dataLink> ({rel_path}): {bad_dl}"

        for attr in ("horzTextAlign", "vertTextAlign"):
            if attr in el.attrib:
                assert el.attrib[attr] in ("leading", "center", "trailing"), (
                    f"{attr}='{el.attrib[attr]}' inválido em {rel_path}"
                )

    # Regra 2 SDK 3.7b: todos os <dataLink> devem ser filhos diretos de <form>
    direct_datalinks = [c for c in root if c.tag == "dataLink"]
    all_datalinks = list(root.iter("dataLink"))
    assert len(direct_datalinks) == len(all_datalinks) and len(direct_datalinks) >= 1, (
        f"Todos os <dataLink> em {rel_path} devem ser filhos diretos de <form>"
    )

    # Dry-run de compilação LFM -> Lua 5.4 + auditoria contra sdk/rrpgGUI.lua
    lua_code = compiler.compile_lfm_to_lua(full)
    compiler.validate_lua_syntax(lua_code, f"@{rel_path}.lua")
    assert 'rawset(obj, "_oldSetNodeObjectFunction", obj.setNodeObject);' in lua_code
    assert 'rawget(obj, "setNodeObject")' not in lua_code
    assert 'cacheMode = "none"' in lua_code

    if gui_sdk:
        methods = set(re.findall(r":(set[A-Za-z0-9_]+)\(", lua_code))
        missing = [
            m for m in sorted(methods)
            if m not in ("setNodeObject", "setNodeDatabase", "setName") and m not in gui_sdk
        ]
        assert not missing, f"Métodos GUI inexistentes em sdk/rrpgGUI.lua ({rel_path}): {missing}"

    return root


def main() -> None:
    compiler = load_skill_compiler()
    gui_sdk = ""
    if os.path.exists(REF_GUI_LUA):
        with open(REF_GUI_LUA, "r", encoding="utf-8", errors="ignore") as f:
            gui_sdk = f.read()

    # 1. Gerar os 14 LFMs vampíricos (--all-clans + compatibilidade --clan) e o LFM Mortal
    subprocess.run(
        [sys.executable, os.path.join(ROOT, "Templates", "generate_vampire_lfm.py"), "--all-clans"],
        check=True,
    )
    subprocess.run(
        [sys.executable, os.path.join(ROOT, "Templates", "generate_vampire_lfm.py"), "--clan", "brujah"],
        check=True,
    )
    subprocess.run(
        [sys.executable, os.path.join(ROOT, "Templates", "generate_mortal_lfm.py")],
        check=True,
    )
    dock_gen_script = os.path.join(ROOT, "Templates", "generate_coterie_dock_lfm.py")
    assert os.path.exists(dock_gen_script), "Templates/generate_coterie_dock_lfm.py não encontrado"
    subprocess.run([sys.executable, dock_gen_script], check=True)
    dock_idem = subprocess.run([sys.executable, dock_gen_script], capture_output=True, text=True, check=True)
    assert "Inalterado" in dock_idem.stdout, (
        f"Segunda execução de generate_coterie_dock_lfm.py deve ser idempotente (_write_if_changed): {dock_idem.stdout}"
    )

    expected_vampire_sheets = [
        ("brujah", "Sheets/frmBrujah.lfm", "br.com.v20.Brujah", "frmBrujah", "Vampiro V20 - Brujah"),
        ("gangrel", "Sheets/frmGangrel.lfm", "br.com.v20.Gangrel", "frmGangrel", "Vampiro V20 - Gangrel"),
        ("malkavian", "Sheets/frmMalkavian.lfm", "br.com.v20.Malkavian", "frmMalkavian", "Vampiro V20 - Malkaviano"),
        ("nosferatu", "Sheets/frmNosferatu.lfm", "br.com.v20.Nosferatu", "frmNosferatu", "Vampiro V20 - Nosferatu"),
        ("toreador", "Sheets/frmToreador.lfm", "br.com.v20.Toreador", "frmToreador", "Vampiro V20 - Toreador"),
        ("tremere", "Sheets/frmTremere.lfm", "br.com.v20.Tremere", "frmTremere", "Vampiro V20 - Tremere"),
        ("ventrue", "Sheets/frmVentrue.lfm", "br.com.v20.Ventrue", "frmVentrue", "Vampiro V20 - Ventrue"),
        ("assamite", "Sheets/frmAssamite.lfm", "br.com.v20.Assamite", "frmAssamite", "Vampiro V20 - Assamita"),
        ("setite", "Sheets/frmSetite.lfm", "br.com.v20.Setite", "frmSetite", "Vampiro V20 - Seguidores de Set"),
        ("giovanni", "Sheets/frmGiovanni.lfm", "br.com.v20.Giovanni", "frmGiovanni", "Vampiro V20 - Giovanni"),
        ("lasombra", "Sheets/frmLasombra.lfm", "br.com.v20.Lasombra", "frmLasombra", "Vampiro V20 - Lasombra"),
        ("ravnos", "Sheets/frmRavnos.lfm", "br.com.v20.Ravnos", "frmRavnos", "Vampiro V20 - Ravnos"),
        ("tzimisce", "Sheets/frmTzimisce.lfm", "br.com.v20.Tzimisce", "frmTzimisce", "Vampiro V20 - Tzimisce"),
        ("caitiff", "Sheets/frmCaitiff.lfm", "br.com.v20.Caitiff", "frmCaitiff", "Vampiro V20 - Caitiff"),
    ]

    vampire_roots: dict[str, ET.Element] = {}
    for cid, rel_p, exp_dt, exp_form, exp_title in expected_vampire_sheets:
        r_el = verify_lfm_xml_and_compile(compiler, gui_sdk, rel_p, exp_dt, exp_form)
        assert r_el.attrib.get("title") == exp_title, f"Título inesperado em {rel_p}: {r_el.attrib.get('title')}"
        seen_ctrl_names: set[str] = set()
        for el in r_el.iter():
            if el is not r_el and el.tag != "event" and "name" in el.attrib:
                nm = el.attrib["name"]
                assert nm not in seen_ctrl_names, f"Controle duplicado '{nm}' em {rel_p}"
                seen_ctrl_names.add(nm)
        tabs = list(r_el.iter("tab"))
        assert len(tabs) == 8, f"{rel_p} deve possuir 8 abas (incluindo tabMagiaSangue), encontrou {len(tabs)}"
        bm_tabs = [t for t in tabs if t.attrib.get("name") == "tabMagiaSangue"]
        assert len(bm_tabs) == 1, f"tabMagiaSangue ausente em {rel_p}"
        expected_vis = "true" if cid in ("tremere", "giovanni") else "false"
        assert bm_tabs[0].attrib.get("visible") == expected_vis, (
            f"tabMagiaSangue em {rel_p} deve iniciar visible='{expected_vis}', obteve '{bm_tabs[0].attrib.get('visible')}'"
        )
        script_txt = "\n".join((sc.text or "") for sc in r_el.iter("script"))
        assert "hasBloodMagicAccess" in script_txt and "setTabIndex(0)" in script_txt, (
            f"Script de {rel_p} deve alternar tabMagiaSangue dinamicamente via V20Bridge.hasBloodMagicAccess e setTabIndex(0)"
        )
        fields_set = {el.attrib.get("field") for el in r_el.iter() if "field" in el.attrib}
        for req_bm_f in (
            "dano_fonte_solar",
            "bm_thau_prim_id",
            "bm_thau_prim_nivel",
            "bm_necro_prim_id",
            "bm_necro_prim_nivel",
            "bm_sec1_nivel",
            "bm_sec4_nivel",
            "bm_ritual_id",
            "ritual_custom_nome",
        ):
            assert req_bm_f in fields_set, f"Campo '{req_bm_f}' ausente em {rel_p}"
        xp_combos = [el for el in r_el.iter("comboBox") if el.attrib.get("field") == "xp_loja_campo"]
        assert len(xp_combos) == 1
        for sec_i in range(1, 5):
            assert f"'bm_sec{sec_i}_nivel'" in xp_combos[0].attrib.get("values", ""), (
                f"bm_sec{sec_i}_nivel deve constar em xp_loja_campo ({rel_p})"
            )
        dl_blob_v = "\n".join(el.attrib.get("fields", "") for el in r_el.findall("dataLink"))
        assert "'dano_fonte_solar'" in dl_blob_v, f"dano_fonte_solar deve estar registrado em <dataLink> ({rel_p})"
        vampire_roots[cid] = r_el

    brujah_root = vampire_roots["brujah"]
    mortal_root = verify_lfm_xml_and_compile(
        compiler, gui_sdk, "Sheets/frmMortal.lfm", "br.com.v20.Mortal", "frmMortal"
    )
    assert mortal_root.attrib.get("title") == "Vampiro V20 - Mortal"

    dock_root = verify_lfm_xml_and_compile(
        compiler,
        gui_sdk,
        "Sheets/frmV20CoterieDock.lfm",
        "br.com.v20.CoterieDock",
        "frmV20CoterieDock",
        expected_form_type="tablesDock",
    )
    assert dock_root.attrib.get("title") == "Vampiro V20 - Painel da Coterie & Iniciativa"
    assert dock_root.attrib.get("width") == "340" and dock_root.attrib.get("height") == "580"
    seen_dock_names: set[str] = set()
    for el in dock_root.iter():
        if el is not dock_root and el.tag != "event" and "name" in el.attrib:
            nm = el.attrib["name"]
            assert nm not in seen_dock_names, f"Controle duplicado '{nm}' em frmV20CoterieDock.lfm"
            seen_dock_names.add(nm)
    for req_dock_ctrl in (
        "pgcDock",
        "tabCenaIniciativa",
        "tabNarradorCoterie",
        "layNpcQuickControls",
        "edtNpcInitNome",
        "edtNpcInitMod",
        "chkNpcInitOculto",
        "btnAddNpcInit",
        "btnTogglePhase",
        "btnClearInit",
        "lblStPageInfo",
        "btnStPrevPage",
        "btnStNextPage",
        "btnBatchAwaken",
        "btnBatchNewTurn",
        "btnBatchEndScene",
    ):
        assert req_dock_ctrl in seen_dock_names, f"Controle '{req_dock_ctrl}' ausente em frmV20CoterieDock.lfm"
    for idx_i in range(1, 11):
        row_nm = f"lblInitRow{idx_i}"
        assert row_nm in seen_dock_names, f"{row_nm} ausente em frmV20CoterieDock.lfm"
        row_els = [el for el in dock_root.iter("label") if el.attrib.get("name") == row_nm]
        assert len(row_els) == 1 and "field" not in row_els[0].attrib, (
            f"{row_nm} não deve ter atributo field direto para garantir filtragem por papel"
        )
    for idx_p in range(1, 9):
        pub_nm = f"lblPubSlot{idx_p}"
        assert pub_nm in seen_dock_names, f"{pub_nm} ausente em frmV20CoterieDock.lfm"
        pub_els = [el for el in dock_root.iter("label") if el.attrib.get("name") == pub_nm]
        assert len(pub_els) == 1 and "field" not in pub_els[0].attrib, (
            f"{pub_nm} não deve ter atributo field direto"
        )
        for st_prefix in (
            "rectStCard",
            "lblStCardTitle",
            "lblStCardStats",
            "lblStCardFlags",
            "btnStBloodMinus",
            "btnStBloodPlus",
            "btnStApproveXp",
        ):
            assert f"{st_prefix}{idx_p}" in seen_dock_names, (
                f"{st_prefix}{idx_p} ausente em frmV20CoterieDock.lfm"
            )
    dock_form_events = {child.attrib.get("name") for child in dock_root if child.tag == "event"}
    assert {"OnShow", "OnHide"}.issubset(dock_form_events), (
        f"frmV20CoterieDock.lfm deve declarar <event name='OnShow'> e <event name='OnHide'> na raiz <form>: {dock_form_events}"
    )
    dock_script_txt = "\n".join((sc.text or "") for sc in dock_root.iter("script"))
    assert "_onBeforeDestroy" in dock_script_txt, "frmV20CoterieDock.lfm deve registrar self._onBeforeDestroy"

    dock_bridge_path = os.path.join(ROOT, "Adapter", "coterie_dock_bridge.lua")
    assert os.path.exists(dock_bridge_path), "Adapter/coterie_dock_bridge.lua não encontrado"
    with open(dock_bridge_path, "r", encoding="utf-8") as f:
        compiler.validate_lua_syntax(f.read(), "@Adapter/coterie_dock_bridge.lua")

    # Verificar campos estruturais obrigatórios em frmBrujah.lfm
    brujah_tabs = list(brujah_root.iter("tab"))
    assert len(brujah_tabs) == 8, f"frmBrujah.lfm deve possuir 8 abas, encontrou {len(brujah_tabs)}"
    brujah_fields = {el.attrib.get("field") for el in brujah_root.iter() if "field" in el.attrib}
    for req_field in (
        "nome",
        "attr_forca",
        "hab_briga",
        "bg_allies",
        "bg_generation",
        "bg_herd",
        "bg_domain",
        "bg_resources",
        "bg_status",
        "disc_slot1_id",
        "disc_slot4_id",
        "disc_slot9_id",
        "auditoria_xp_log",
        "roll_attr_id",
        "roll_diff",
        "health_box_0",
        "health_box_1",
        "health_box_7",
    ):
        assert req_field in brujah_fields, f"Campo obrigatório '{req_field}' ausente em frmBrujah.lfm"
    assert "health_box_8" not in brujah_fields, "health_box_8 não deve existir; caixa extra de Tamanho Grande fica no topo (health_box_0)"

    # Verificar campos estruturais obrigatórios em frmMortal.lfm
    mortal_tabs = list(mortal_root.iter("tab"))
    assert len(mortal_tabs) >= 6, f"frmMortal.lfm deve possuir ao menos 6 abas, encontrou {len(mortal_tabs)}"
    mortal_fields = {el.attrib.get("field") for el in mortal_root.iter() if "field" in el.attrib}
    for req_field in (
        "nome",
        "mortal_perfil",
        "mortal_sobrenatural_modo",
        "auditoria_xp_log",
        "roll_attr_id",
        "health_box_0",
        "health_box_1",
        "health_box_7",
    ):
        assert req_field in mortal_fields, f"Campo obrigatório '{req_field}' ausente em frmMortal.lfm"
    assert "health_box_8" not in mortal_fields, "health_box_8 não deve existir em frmMortal.lfm"

    # Verificar controles nomeados de permissões, comboBox de XP e dataLinks reativos (Findings #2, #4, #6)
    for root_el, label_lfm, is_mortal in ((brujah_root, "frmBrujah.lfm", False), (mortal_root, "frmMortal.lfm", True)):
        xp_campo_combos = [el for el in root_el.iter("comboBox") if el.attrib.get("field") == "xp_loja_campo"]
        xp_campo_edits = [el for el in root_el.iter("edit") if el.attrib.get("field") == "xp_loja_campo"]
        assert len(xp_campo_combos) == 1 and len(xp_campo_edits) == 0, (
            f"{label_lfm} deve usar <comboBox field='xp_loja_campo'/> no lugar de <edit>"
        )
        vals_str = xp_campo_combos[0].attrib.get("values", "")
        for expected_xp_field in (
            "attr_forca",
            "hab_briga",
            "disc_slot1_nivel",
            "disc_slot9_nivel",
            "virtude1_val",
            "virtude2_val",
            "virtude3_val",
            "moralidade_val",
            "fdv_perm",
        ):
            assert f"'{expected_xp_field}'" in vals_str, f"'{expected_xp_field}' ausente em xp_loja_campo ({label_lfm})"

        xp_cat_combos = [el for el in root_el.iter("comboBox") if el.attrib.get("field") == "xp_loja_cat_custo"]
        assert len(xp_cat_combos) == 1 and "'auto'" in xp_cat_combos[0].attrib.get("values", ""), (
            f"xp_loja_cat_custo deve incluir 'auto' em {label_lfm}"
        )

        named_ctrls = {el.attrib.get("name") for el in root_el.iter() if "name" in el.attrib}
        for req_ctrl in (
            "cmbModoFicha",
            "edtXpTotal",
            "edtXpGasto",
            "chkXpExigeAprovacao",
            "chkNarradorOverride",
            "edt_attr_forca",
            "btnPlus_attr_forca",
            "chkTamanhoGrande",
        ):
            assert req_ctrl in named_ctrls, f"Controle nomeado '{req_ctrl}' ausente em {label_lfm}"
        if is_mortal:
            assert "'bm_sec1_nivel'" not in vals_str, "Ficha Mortal não deve listar bm_sec1_nivel na Loja de XP"
            for m_ctrl in ("cmbMortalSobrenaturalModo", "edtCarnicalDiscMax", "btnFrenesiCarnical"):
                assert m_ctrl in named_ctrls, f"Controle mortal '{m_ctrl}' ausente em {label_lfm}"

        dl_blob = "\n".join(
            (el.attrib.get("fields", "") + " || " + el.attrib.get("defaultValues", ""))
            for el in root_el.findall("dataLink")
        )
        assert "'tem_tamanho_grande'" in dl_blob, f"tem_tamanho_grande ausente nos <dataLink> de {label_lfm}"
        for slot_i in range(1, 7):
            assert f"'mf_slot{slot_i}_nome'" in dl_blob, f"mf_slot{slot_i}_nome ausente nos <dataLink> de {label_lfm}"

        dl_events = [ev.text or "" for dl in root_el.findall("dataLink") for ev in dl.findall("event")]
        assert all("atualizarPermissoesModo(self)" in txt for txt in dl_events), (
            f"<dataLink> onChange deve invocar atualizarPermissoesModo(self) em {label_lfm}"
        )

    # Validar sintaxe Lua 5.4 de Adapter/firecast_bridge.lua
    bridge_path = os.path.join(ROOT, "Adapter", "firecast_bridge.lua")
    assert os.path.exists(bridge_path), "Adapter/firecast_bridge.lua não encontrado"
    with open(bridge_path, "r", encoding="utf-8") as f:
        compiler.validate_lua_syntax(f.read(), "@Adapter/firecast_bridge.lua")

    # 2. Testar todos os métodos de V20Bridge na lua54x64.dll (com isolamento [TESTE_E2E] e limpeza garantida)
    lua_probe = os.path.join(ROOT, "output", "probe_test_e2e_bridge.lua")
    os.makedirs(os.path.dirname(lua_probe), exist_ok=True)
    try:
        with open(lua_probe, "w", encoding="utf-8") as f:
            f.write(r'''
local Bridge = require("Adapter.firecast_bridge")
assert(_G.V20Bridge == Bridge, "V20Bridge deve ser registrado em _G")

local sentMessages = {}
local dialogMessages = {}
local nextFaces = { 10, 8, 1 }
local isMestreFlag = false

local mockDialogs = {
    showMessage = function(msg)
        table.insert(dialogMessages, tostring(msg))
    end
}

local mockFirecast = {
    interpretarRolagem = function(expr)
        return {
            expr = expr,
            ops = { { tipo = "dado", resultados = nextFaces } },
            rolarLocalmente = function(self)
                self.ops = { { tipo = "dado", resultados = nextFaces } }
            end
        }
    end,
    getMesaDe = function(_)
        return {
            meuJogador = { isMestre = isMestreFlag, login = "test_e2e_player" },
            activeChat = {
                rolarDados = function(_, rol, title, cb)
                    cb({ ops = { { tipo = "dado", resultados = nextFaces } } })
                end,
                enviarMensagem = function(_, msg)
                    table.insert(sentMessages, msg)
                end,
            }
        }
    end
}

-- 2.1 syncDerivedFields + rollFromSheet básico (10 espec + 8 - 1 = 2 sucessos)
local mockSheet = {
    nome = "[TESTE_E2E] Jack Brujah",
    cla_id = "brujah",
    is_vampire = true,
    geracao_base = 13,
    attr_forca = 3,
    attr_destreza = 3,
    attr_vigor = 3,
    attr_carisma = 2,
    attr_manipulacao = 3,
    attr_aparencia = 2,
    attr_percepcao = 2,
    attr_inteligencia = 2,
    attr_raciocinio = 3,
    hab_investigacao = 1,
    hab_ocultismo = 2,
    hab_manha = 2,
    roll_attr_id = "attr_percepcao",
    roll_hab_id = "hab_investigacao",
    roll_diff = 6,
    roll_usar_espec = true,
    roll_gastar_fdv = false,
    fdv_perm = 6,
    fdv_temp = 5,
    virtude1_tipo = "consciencia",
    virtude1_val = 3,
    virtude2_tipo = "autocontrole",
    virtude2_val = 3,
    virtude3_val = 4,
    moralidade_val = 7,
    sangue_atual = 8,
}

Bridge.syncDerivedFields(mockSheet)
assert(mockSheet.geracao == 13, "Geracao 13 esperada")
assert(mockSheet.sangue_max == 10 and mockSheet.sangue_por_turno == 1)
assert(mockSheet.vitalidade_label == "Saudável" and mockSheet.vitalidade_resumo == "Saudável")
assert(mockSheet.aura_label ~= nil and mockSheet.aura_resumo == mockSheet.aura_label)
assert(mockSheet.penalidade_ferimento == 0)

Bridge.rollFromSheet(mockSheet, {}, mockFirecast, mockDialogs)
assert(#sentMessages == 1, "Deveria ter enviado diagnóstico V20 no chat")
assert(sentMessages[1]:find("2 Sucesso") ~= nil, "Esperado 2 sucessos: " .. sentMessages[1])

-- 2.2 Regressão PF-3: gasto de FdV NÃO pode contar em dobro (+1 autoSuccess exato)
sentMessages = {}
nextFaces = { 4, 2, 3 }
mockSheet.roll_usar_espec = false
mockSheet.roll_gastar_fdv = true
mockSheet.fdv_temp = 5
Bridge.rollFromSheet(mockSheet, {}, mockFirecast, mockDialogs)
assert(mockSheet.fdv_temp == 4, "Deveria descontar 1 FdV temporária")
assert(#sentMessages == 1)
assert(sentMessages[1]:find("1 Sucesso") ~= nil, "Gasto de FdV sem sucessos nos dados deve resultar em exatamente 1 Sucesso! Msg: " .. sentMessages[1])
mockSheet.roll_gastar_fdv = false

-- 2.3 Fallback fora de sala (getMesaDe == nil)
dialogMessages = {}
nextFaces = { 9, 7, 2 }
local offlineFirecast = {
    interpretarRolagem = mockFirecast.interpretarRolagem,
    getMesaDe = function(_) return nil end,
}
Bridge.rollFromSheet(mockSheet, {}, offlineFirecast, mockDialogs)
assert(#dialogMessages == 1 and dialogMessages[1]:find("2 Sucesso") ~= nil, "Fallback offline deve exibir showMessage")

-- 2.4 syncDerivedFields com Antecedentes flat (bg_*) E nós NDB opcionais
mockSheet.bg_generation = 5
mockSheet.bg_herd = 2
mockSheet.bg_domain = 1
mockSheet.bg_resources = 3
mockSheet.mf_huge_size = true
Bridge.syncDerivedFields(mockSheet)
assert(mockSheet.geracao == 8 and mockSheet.sangue_max == 15 and mockSheet.sangue_por_turno == 3)
assert(mockSheet.caca_bonus_dados == 2 and mockSheet.caca_mod_dif == -1)

local mockNdbSheet = {
    nome = "[TESTE_E2E] Ancilla NDB",
    is_vampire = true,
    geracao_base = 13,
    rclAntecedentes_node = { { bg_id = "generation", nivel = 3 } },
}
local mockNdb = {
    getChildNodes = function(node) return node end
}
Bridge.syncDerivedFields(mockNdbSheet, mockNdb)
assert(mockNdbSheet.geracao == 10 and mockNdbSheet.sangue_max == 13)
mockSheet.bg_generation = 0
mockSheet.mf_huge_size = false
Bridge.syncDerivedFields(mockSheet)

-- 2.5 activateDisciplinePower com refs virtuais PF-3 (Taumaturgia attr_fdv_ref e Tenebrosidade hab_coragem_ref)
sentMessages = {}
nextFaces = { 8, 7, 6, 5, 2, 2 } -- Dif 4 -> 4 sucessos
mockSheet.sangue_atual = 10
mockSheet.sangue_gasto_turno = 0
local thauRes = Bridge.activateDisciplinePower(
    mockSheet,
    { disc_id = "thaumaturgy", nivel = 3 },
    "thau_1",
    mockFirecast,
    mockDialogs
)
assert(thauRes.ok == true, "thau_1 deveria ativar com sucesso")
assert(mockSheet.sangue_atual == 9, "thau_1 custa 1 sangue")
assert(#sentMessages == 1 and sentMessages[1]:find("Dif 4") ~= nil, "thau_1 deve rolar FdV Dif 4: " .. tostring(sentMessages[1]))

Bridge.newTurn(mockSheet, mockFirecast, mockDialogs)
assert(mockSheet.sangue_gasto_turno == 0, "newTurn deve zerar gasto do turno")

-- Tenebrosidade Nv 4 (obt_4: 2 sangue -> requer geração c/ gasto >= 2 ou múltiplos turnos; vamos usar 8ª geração!)
mockSheet.bg_generation = 5
Bridge.syncDerivedFields(mockSheet)
mockSheet.sangue_atual = 12
sentMessages = {}
nextFaces = { 9, 8, 7, 3, 2, 2, 2 }
local obtRes = Bridge.activateDisciplinePower(
    mockSheet,
    { disc_id = "obtenebration", nivel = 4 },
    "obt_4",
    mockFirecast,
    mockDialogs
)
assert(obtRes.ok == true, "obt_4 deveria ativar na 8ª geração: " .. tostring(obtRes.error))
assert(mockSheet.sangue_atual == 10, "obt_4 custa 2 sangue")
assert(#sentMessages == 1 and sentMessages[1]:find("Dif 7") ~= nil, "obt_4 deve rolar Manipulação + Coragem Dif 7: " .. tostring(sentMessages[1]))

-- Animalismo Nv 5 (anim_5: hab_autocontrole_ref)
sentMessages = {}
local animRes = Bridge.activateDisciplinePower(
    mockSheet,
    { disc_id = "animalism", nivel = 5 },
    "anim_5",
    mockFirecast,
    mockDialogs
)
assert(animRes.ok == true and #sentMessages == 1 and sentMessages[1]:find("Dif 8") ~= nil)

-- 2.6 Fraqueza Brujah em rollFrenzy (+2 dificuldade, bloqueia FdV preventivo) + Rötschreck + Degeneração
sentMessages = {}
nextFaces = { 9, 8, 2 }
mockSheet.fdv_temp = 5
mockSheet.roll_gastar_fdv = true
Bridge.rollFrenzy(mockSheet, 6, mockFirecast, mockDialogs)
assert(mockSheet.fdv_temp == 5, "Brujah NÃO pode gastar FdV para evitar Frenesi preventivamente")
assert(#sentMessages == 1 and sentMessages[1]:find("Dif 8") ~= nil, "Brujah soma +2 na dif de Frenesi (6 -> 8): " .. sentMessages[1])
assert(sentMessages[1]:find("Fraqueza Brujah") ~= nil, "Deve exibir nota da Fraqueza Brujah")
mockSheet.roll_gastar_fdv = false

sentMessages = {}
Bridge.rollRotschreck(mockSheet, 5, mockFirecast, mockDialogs)
assert(#sentMessages == 1 and sentMessages[1]:find("Dif 5") ~= nil)

sentMessages = {}
Bridge.rollDegeneration(mockSheet, mockFirecast, mockDialogs)
assert(#sentMessages == 1 and sentMessages[1]:find("Dif 8") ~= nil)

-- 2.7 Caça com Rebanho + Domínio, Despertar, Blood Buff, Dano, Cura, Absorção, Iniciativa
Bridge.newTurn(mockSheet, mockFirecast, mockDialogs)
mockSheet.sangue_atual = 6
sentMessages = {}
nextFaces = { 8, 7, 6, 5, 4, 3 }
Bridge.huntWithHerdDomain(mockSheet, { difficulty = 6 }, mockFirecast, mockDialogs)
assert(#sentMessages == 1 and sentMessages[1]:find("Dif 5") ~= nil, "Domínio 1 reduz dif de caça de 6 para 5: " .. sentMessages[1])
assert(mockSheet.sangue_atual > 6, "Caça bem-sucedida deve recuperar vitae")

Bridge.newTurn(mockSheet, mockFirecast, mockDialogs)
local prevBlood = mockSheet.sangue_atual
Bridge.applyBloodBuff(mockSheet, "forca", mockFirecast, mockDialogs)
assert(mockSheet.buff_forca == 1 and mockSheet.sangue_atual == prevBlood - 1)
Bridge.clearSceneBuffs(mockSheet, mockFirecast, mockDialogs)
assert(mockSheet.buff_forca == 0)

Bridge.awakenNightly(mockSheet, mockFirecast, mockDialogs)
Bridge.applyDamage(mockSheet, 2, "lethal", { isFirearm = true, headshot = false }, mockFirecast, mockDialogs)
assert((tonumber(mockSheet.dano_contundente) or 0) == 2, "Arma de fogo normal em vampiro converte para contundente")
Bridge.healDamage(mockSheet, "bashing", {}, mockFirecast, mockDialogs)
assert((tonumber(mockSheet.dano_contundente) or 0) == 1, "Cura deve remover 1 nível contundente")

sentMessages = {}
Bridge.rollSoak(mockSheet, "lethal", mockFirecast, mockDialogs)
assert(#sentMessages == 1)

sentMessages = {}
nextFaces = { 7 }
Bridge.rollInitiative(mockSheet, mockFirecast, mockDialogs)
assert(#sentMessages == 1 and sentMessages[1]:find("Iniciativa") ~= nil)

-- 2.8 Validação de Criação, Loja/Aprovação de XP e logAudit
local auditEntry = Bridge.logAudit(
    mockSheet, nil, mockFirecast, "nota_narrador", "[TESTE_E2E] Registro inicial", 0, "aprovado", nil, nil
)
assert(auditEntry.tipo_evento == "nota_narrador")
assert((mockSheet.auditoria_xp_log or ""):find("Registro inicial") ~= nil)

mockSheet.xp_total = 20
mockSheet.xp_gasto = 0
mockSheet.xp_exige_aprovacao = true
isMestreFlag = false
local subRes = Bridge.submitOrApproveXP(
    mockSheet,
    "submit",
    { traitKind = "willpower", field = "fdv_perm", label = "Força de Vontade" },
    nil,
    mockFirecast,
    mockDialogs
)
assert(subRes.ok == true and mockSheet.xp_pendente_status == "pendente")
assert(mockSheet.fdv_perm == 6, "Enquanto pendente, fdv_perm permanece 6")

local blockedApprove = Bridge.submitOrApproveXP(mockSheet, "approve", nil, nil, mockFirecast, mockDialogs)
assert(blockedApprove.ok == false, "Jogador comum não pode aprovar XP pendente")

isMestreFlag = true
local okApprove = Bridge.submitOrApproveXP(mockSheet, "approve", nil, nil, mockFirecast, mockDialogs)
assert(okApprove.ok == true and mockSheet.fdv_perm == 7 and mockSheet.xp_gasto == 6)

local valCreation = Bridge.validateCreationOnSheet(mockSheet, nil, mockFirecast, mockDialogs)
assert(type(valCreation) == "table" and valCreation.valid ~= nil)

-- 2.9 Transição Mortal -> Carniçal e Numina
local mortalSheet = {
    nome = "[TESTE_E2E] Elena Mortal",
    is_vampire = false,
    mortal_perfil = "padrao_643",
    mortal_sobrenatural_modo = "humano",
    dano_letal = 0,
}
Bridge.syncDerivedFields(mortalSheet)
assert(mortalSheet.sangue_max == 0 and mortalSheet.isGhoul == false)

mortalSheet.mortal_sobrenatural_modo = "carnical"
Bridge.syncDerivedFields(mortalSheet)
assert(mortalSheet.isGhoul == true and mortalSheet.sangue_max == 2 and mortalSheet.sangue_por_turno == 1 and mortalSheet.ghoulPotence == 1)

mortalSheet.mortal_sobrenatural_modo = "numina"
Bridge.syncDerivedFields(mortalSheet)
assert(mortalSheet.hasNumina == true and mortalSheet.isGhoul == false and mortalSheet.sangue_max == 0)

-- 2.10 Compatibilidade real com NodeFacade do Firecast NDB (onde pairs() não itera atributos e tabelas virariam sub-nós)
local backingAttrs = {
    nome = "[TESTE_E2E] Facade Brujah",
    cla_id = "brujah",
    is_vampire = "true",
    geracao_base = "13",
    fdv_perm = "5",
    fdv_temp = "5",
    sangue_atual = "10",
    xp_total = "15",
    xp_gasto = "0",
    xp_exige_aprovacao = "false",
}
local mockNodeFacade = setmetatable({ __nodeFacadeFlag = true }, {
    __index = function(_, k) return backingAttrs[k] end,
    __newindex = function(_, k, v)
        assert(type(v) ~= "table" and type(v) ~= "function", "Proibido gravar tabela/função direta em NodeFacade: " .. tostring(k))
        backingAttrs[k] = v
    end,
})
Bridge.syncDerivedFields(mockNodeFacade)
assert(mockNodeFacade.sangue_max == 10 and mockNodeFacade.geracao == 13)
isMestreFlag = false
local facadeXpRes = Bridge.submitOrApproveXP(
    mockNodeFacade,
    "submit",
    { traitKind = "willpower", field = "fdv_perm", label = "FdV Facade" },
    nil,
    mockFirecast,
    mockDialogs
)
assert(facadeXpRes.ok == true and mockNodeFacade.fdv_perm == 6 and mockNodeFacade.xp_gasto == 5)

-- 2.11 Fix Round 1 #1: validateCreationOnSheet com Pontos de Bônus em Atributos e Habilidades (incluindo Habilidade 3 -> 4)
local neonateCreation = {
    nome = "[TESTE_E2E] Neófito Completo Brujah",
    cla_id = "brujah",
    is_vampire = true,
    modo_ficha = "criacao",
    -- Físicos: base 7 + 1 bônus = 8 (4+3+4 = 11 pontos totais -> 11 - 3 = 8 acima da base)
    attr_forca = 4,
    attr_destreza = 3,
    attr_vigor = 4,
    -- Sociais: base 3 (2+2+2 -> 3 acima da base)
    attr_carisma = 2,
    attr_manipulacao = 2,
    attr_aparencia = 2,
    -- Mentais: base 5 (3+2+3 -> 5 acima da base)
    attr_percepcao = 3,
    attr_inteligencia = 2,
    attr_raciocinio = 3,
    -- Talentos: base 13 + 2 bônus = 15 (hab_briga elevada de 3 p/ 4 via bônus!)
    hab_briga = 4,
    hab_prontidao = 3,
    hab_esportes = 3,
    hab_intimidacao = 3,
    hab_manha = 2,
    -- Perícias: base 9
    hab_armas_brancas = 3,
    hab_armas_fogo = 3,
    hab_furtividade = 3,
    -- Conhecimentos: base 5
    hab_investigacao = 2,
    hab_ocultismo = 3,
    -- Disciplinas: 3 base
    disc_slot1_id = "celerity",
    disc_slot1_nivel = 1,
    disc_slot2_id = "potence",
    disc_slot2_nivel = 1,
    disc_slot3_id = "presence",
    disc_slot3_nivel = 1,
    -- Antecedentes: 5 base
    bg_resources = 2,
    bg_herd = 2,
    bg_domain = 1,
    -- Virtudes: 7 base (1+3, 1+2, 1+2)
    virtude1_val = 4,
    virtude2_val = 3,
    virtude3_val = 3,
    -- Compras de Bônus: 1 Atributo (5) + 2 Habilidades (4) + 6 FdV (6) = 15 pontos exatos
    freebie_attributes = 1,
    freebie_abilities = 2,
    freebie_willpower = 6,
}
local okCreation = Bridge.validateCreationOnSheet(neonateCreation, nil, mockFirecast, mockDialogs, true)
assert(okCreation.valid == true, "Criação Neófito c/ bônus em Atrib/Hab deveria ser válida: " .. table.concat(okCreation.errors or {}, "; "))
assert(neonateCreation.modo_ficha == "jogo", "Criação válida com lockIfValid=true deve entrar em modo_ficha='jogo'")

-- Contra-prova: Habilidade 4 sem declarar freebie_abilities deve falhar na trava pré-bônus
neonateCreation.modo_ficha = "criacao"
neonateCreation.freebie_abilities = 0
local badCreation = Bridge.validateCreationOnSheet(neonateCreation, nil, mockFirecast, mockDialogs, false)
assert(badCreation.valid == false, "Habilidade 4 sem freebie_abilities deve ser rejeitada")

-- 2.12 Fix Round 1 #2: mf_slot1..6 de catálogo preservam cat.tipo e cat.pontos mesmo com defaults de <dataLink>
local mfSlotSheet = {
    nome = "[TESTE_E2E] Sangue-Fraco Gigante",
    cla_id = "brujah",
    is_vampire = true,
    geracao_base = 13,
    mf_slot1_ativo = "true",
    mf_slot1_id = "gen_14th",
    mf_slot1_tipo = "qualidade",
    mf_slot1_pontos = "0",
    mf_slot2_ativo = "true",
    mf_slot2_id = "huge_size",
    mf_slot2_tipo = "qualidade",
    mf_slot2_pontos = "0",
}
Bridge.syncDerivedFields(mfSlotSheet)
assert(mfSlotSheet.defeitos_bonus == 2, "gen_14th deve conceder +2 de bônus de defeitos mesmo com mf_slot1_tipo='qualidade' e pontos='0', obteve: " .. tostring(mfSlotSheet.defeitos_bonus))
assert(mfSlotSheet.qualidades_total == 4, "huge_size deve custar 4 de qualidades mesmo com mf_slot2_pontos='0', obteve: " .. tostring(mfSlotSheet.qualidades_total))
assert(mfSlotSheet.geracao == 14, "gen_14th deve forçar 14ª geração, obteve: " .. tostring(mfSlotSheet.geracao))
assert(mfSlotSheet.tem_tamanho_grande == true, "huge_size deve sincronizar tem_tamanho_grande == true")

-- 2.13 Fix Round 1 #3: Guarda anti-reentrância e setIfChanged em syncDerivedFields
local proxyStore = {
    nome = "[TESTE_E2E] Proxy Guard",
    cla_id = "brujah",
    is_vampire = true,
    geracao_base = 13,
}
local writeCount = 0
local reentrantDepth = 0
local maxReentrantDepth = 0
local proxySheet
proxySheet = setmetatable({}, {
    __index = function(_, k) return proxyStore[k] end,
    __newindex = function(_, k, v)
        proxyStore[k] = v
        writeCount = writeCount + 1
        reentrantDepth = reentrantDepth + 1
        if reentrantDepth > maxReentrantDepth then maxReentrantDepth = reentrantDepth end
        -- Simula <dataLink> onChange disparando syncDerivedFields reentrantemente a cada escrita
        Bridge.syncDerivedFields(proxySheet)
        reentrantDepth = reentrantDepth - 1
    end,
})
Bridge.syncDerivedFields(proxySheet)
assert(maxReentrantDepth == 1, "Guarda anti-reentrância deve impedir recursão em onChange, profundidade: " .. tostring(maxReentrantDepth))
writeCount = 0
Bridge.syncDerivedFields(proxySheet)
assert(writeCount == 0, "Segunda chamada sem alterações não deve regravar campos no NDB, escritas: " .. tostring(writeCount))

-- 2.14 Fix Round 1 #4: Alinhamento de health_box_0..7 com e sem Tamanho Grande
local healthTest = {
    nome = "[TESTE_E2E] Trilha Vitalidade",
    cla_id = "brujah",
    is_vampire = true,
    dano_contundente = 1,
    dano_letal = 0,
    dano_aggravado = 0,
    tem_tamanho_grande = false,
}
Bridge.syncDerivedFields(healthTest)
assert(healthTest.health_box_0 == "-", "Sem Tamanho Grande, health_box_0 deve ser '-', obteve: " .. tostring(healthTest.health_box_0))
assert(healthTest.health_box_1 == "[/]", "Sem Tamanho Grande, 1 contundente marca Escoriado em health_box_1")
assert(healthTest.health_box_7 == "[ ]", "Incapacitado (health_box_7) deve estar vazio")

healthTest.tem_tamanho_grande = true
Bridge.syncDerivedFields(healthTest)
assert(healthTest.health_box_0 == "[/]", "Com Tamanho Grande, 1 contundente marca Escoriado Extra em health_box_0")
assert(healthTest.health_box_1 == "[ ]", "Com Tamanho Grande e 1 dano, Escoriado padrão (health_box_1) deve estar vazio")
assert(healthTest.health_box_7 == "[ ]", "Incapacitado continua mapeado em health_box_7")

healthTest.dano_contundente = 0
healthTest.dano_letal = 8
Bridge.syncDerivedFields(healthTest)
assert(healthTest.vitalidade_resumo == "Incapacitado")
assert(healthTest.health_box_0 == "[X]" and healthTest.health_box_7 == "[X]", "Com 8 níveis letais em Tamanho Grande, health_box_0..7 ficam todos [X]")

-- 2.15 Finding #1: Coerção inteira de XP decimal ("2.5") no Bridge sem crash Lua 5.4
local decSheet = {
    nome = "[TESTE_E2E] Decimal XP",
    cla_id = "brujah",
    is_vampire = true,
    xp_total = "2.5",
    xp_gasto = "0.5",
    xp_exige_aprovacao = false,
    attr_forca = 3,
}
Bridge.syncDerivedFields(decSheet)
assert(decSheet.xp_disponivel == 2 and math.type(decSheet.xp_disponivel) == "integer")
local decFail = Bridge.submitOrApproveXP(
    decSheet, "submit", { field = "attr_forca" }, nil, mockFirecast, mockDialogs
)
assert(decFail.ok == false and decFail.error:find("disponível 2") ~= nil)

-- 2.16 Finding #2: modo_ficha ("criacao" | "jogo" | "narrador_livre") e chaves exclusivas do Narrador
local modeSheet = {
    nome = "[TESTE_E2E] Trava Modo Jogo",
    cla_id = "brujah",
    is_vampire = true,
    modo_ficha = "jogo",
    attr_forca = 3,
    sangue_atual = 8,
    fdv_temp = 5,
    dano_contundente = 0,
}
isMestreFlag = false
dialogMessages = {}
local blockedPerm = Bridge.adjustResource(modeSheet, "attr_forca", 1, 1, "atributo_max_geracao", mockFirecast, mockDialogs)
assert(blockedPerm.ok == false and modeSheet.attr_forca == 3, "Atributo permanente deve ser bloqueado em modo_ficha='jogo'")
assert(#dialogMessages >= 1 and dialogMessages[#dialogMessages]:find("Aba 7") ~= nil, "Mensagem deve orientar uso da Aba 7 (XP)")

local okTempBlood = Bridge.adjustResource(modeSheet, "sangue_atual", -2, 0, "sangue_max", mockFirecast, mockDialogs)
assert(okTempBlood.ok == true and modeSheet.sangue_atual == 6, "sangue_atual temporário deve continuar liberado em modo_ficha='jogo'")
local okTempWP = Bridge.adjustResource(modeSheet, "fdv_temp", -1, 0, "fdv_perm", mockFirecast, mockDialogs)
assert(okTempWP.ok == true and modeSheet.fdv_temp == 4, "fdv_temp temporário deve continuar liberado em modo_ficha='jogo'")

-- Não-Narrador bloqueado de trocar modo_ficha ou mortal_sobrenatural_modo
local blockSetMode = Bridge.setSheetMode(modeSheet, "narrador_livre", mockFirecast, mockDialogs)
assert(blockSetMode.ok == false and modeSheet.modo_ficha == "jogo", "Jogador comum não pode mudar modo_ficha")

local mortalGuardSheet = {
    nome = "[TESTE_E2E] Mortal Guard",
    is_vampire = false,
    mortal_sobrenatural_modo = "humano",
}
local blockSetSob = Bridge.setMortalSupernaturalMode(mortalGuardSheet, "carnical", mockFirecast, mockDialogs)
assert(blockSetSob.ok == false and mortalGuardSheet.mortal_sobrenatural_modo == "humano", "Jogador comum não pode mudar mortal_sobrenatural_modo")

-- narrador_livre bloqueado para jogador comum e auditado para o Narrador (isMestre = true)
modeSheet.modo_ficha = "narrador_livre"
local blockFreeNonMaster = Bridge.adjustResource(modeSheet, "attr_forca", 1, 1, "atributo_max_geracao", mockFirecast, mockDialogs)
assert(blockFreeNonMaster.ok == false and modeSheet.attr_forca == 3, "narrador_livre deve bloquear jogador que não é Mestre")

isMestreFlag = true
local okSetMode = Bridge.setSheetMode(modeSheet, "jogo", mockFirecast, mockDialogs)
assert(okSetMode.ok == true and modeSheet.modo_ficha == "jogo")
local okSetFree = Bridge.setSheetMode(modeSheet, "narrador_livre", mockFirecast, mockDialogs)
assert(okSetFree.ok == true and modeSheet.modo_ficha == "narrador_livre")

local okFreeMaster = Bridge.adjustResource(modeSheet, "attr_forca", 1, 1, "atributo_max_geracao", mockFirecast, mockDialogs)
assert(okFreeMaster.ok == true and modeSheet.attr_forca == 4, "Narrador em narrador_livre deve ajustar característica")
assert((modeSheet.auditoria_xp_log or ""):find("3 %-> 4") ~= nil, "Edição livre do Narrador deve registrar antes -> depois em logAudit")

local okSetSob = Bridge.setMortalSupernaturalMode(mortalGuardSheet, "carnical", mockFirecast, mockDialogs)
assert(okSetSob.ok == true and mortalGuardSheet.mortal_sobrenatural_modo == "carnical" and mortalGuardSheet.isGhoul == true)

-- 2.17 Finding #3: Sangue-Fraco de 15ª Geração canalizando ações de 1 ponto base (custo 2 em 2 turnos) na UI
local gen15Sheet = {
    nome = "[TESTE_E2E] ThinBlood 15 UI",
    cla_id = "brujah",
    is_vampire = true,
    mf_gen_15th = true,
    sangue_atual = 10,
    sangue_gasto_turno = 0,
    sangue_fraco_usado = 0,
    dano_contundente = 2,
    attr_forca = 2,
    disc_slot1_id = "potence",
    disc_slot1_nivel = 1,
}
Bridge.syncDerivedFields(gen15Sheet)
assert(gen15Sheet.geracao == 15 and gen15Sheet.sangue_usavel_max == 6 and gen15Sheet.sangue_por_turno == 1)

sentMessages = {}
local g15Heal1 = Bridge.healDamage(gen15Sheet, "bashing", {}, mockFirecast, mockDialogs)
assert(g15Heal1.ok == true and gen15Sheet.sangue_atual == 8 and gen15Sheet.sangue_gasto_turno == 2 and gen15Sheet.dano_contundente == 1)
assert(#sentMessages == 1 and sentMessages[1]:find("(15ª Geração: 2 pts de vitae canalizados em 2 turnos)", 1, true) ~= nil)

-- Segundo gasto no mesmo turno deve falhar pois sangue_gasto_turno == 2
local g15HealSameTurn = Bridge.healDamage(gen15Sheet, "bashing", {}, mockFirecast, mockDialogs)
assert(g15HealSameTurn.ok == false and gen15Sheet.sangue_atual == 8)

Bridge.newTurn(gen15Sheet, mockFirecast, mockDialogs)
sentMessages = {}
local g15Buff = Bridge.applyBloodBuff(gen15Sheet, "forca", mockFirecast, mockDialogs)
assert(g15Buff.ok == true and gen15Sheet.sangue_atual == 6 and gen15Sheet.sangue_gasto_turno == 2 and gen15Sheet.buff_forca == 1)
assert(#sentMessages == 1 and sentMessages[1]:find("(15ª Geração: 2 pts de vitae canalizados em 2 turnos)", 1, true) ~= nil)

local g15BuffSameTurn = Bridge.applyBloodBuff(gen15Sheet, "destreza", mockFirecast, mockDialogs)
assert(g15BuffSameTurn.ok == false and gen15Sheet.sangue_atual == 6)

Bridge.newTurn(gen15Sheet, mockFirecast, mockDialogs)
sentMessages = {}
local g15Pot = Bridge.activateDisciplineSlot(gen15Sheet, 1, mockFirecast, mockDialogs)
assert(g15Pot.ok == true and gen15Sheet.sangue_atual == 4 and gen15Sheet.sangue_gasto_turno == 2 and gen15Sheet.potencia_ativa_turno == true)
assert(#sentMessages == 1 and sentMessages[1]:find("(15ª Geração: 2 pts de vitae canalizados em 2 turnos)", 1, true) ~= nil)

-- 2.18 Finding #4: Loja de XP — guarda pendente, validação campo/tipo, auto-classificação (Clã/Fora/AddDisc/Caitiff) e tetos V20
local xpSuite = {
    nome = "[TESTE_E2E] XP Ceilings & AutoCat",
    cla_id = "brujah",
    is_vampire = true,
    geracao_base = 13,
    xp_total = 100,
    xp_gasto = 0,
    xp_exige_aprovacao = true,
    attr_forca = 5,
    hab_briga = 5,
    virtude1_val = 5,
    moralidade_val = 10,
    fdv_perm = 10,
    disc_slot1_id = "potence",
    disc_slot1_nivel = 1,
    disc_slot4_id = "auspex",
    disc_slot4_nivel = 1,
    disc_slot5_id = "celerity",
    disc_slot5_nivel = 5,
}
isMestreFlag = false
-- Tetos V20 bloqueiam submissão sem override
assert(Bridge.submitOrApproveXP(xpSuite, "submit", { field = "attr_forca" }, nil, mockFirecast, mockDialogs).ok == false)
assert(Bridge.submitOrApproveXP(xpSuite, "submit", { field = "hab_briga" }, nil, mockFirecast, mockDialogs).ok == false)
assert(Bridge.submitOrApproveXP(xpSuite, "submit", { field = "virtude1_val" }, nil, mockFirecast, mockDialogs).ok == false)
assert(Bridge.submitOrApproveXP(xpSuite, "submit", { field = "moralidade_val" }, nil, mockFirecast, mockDialogs).ok == false)
assert(Bridge.submitOrApproveXP(xpSuite, "submit", { field = "fdv_perm" }, nil, mockFirecast, mockDialogs).ok == false)
assert(Bridge.submitOrApproveXP(xpSuite, "submit", { field = "disc_slot5_nivel" }, nil, mockFirecast, mockDialogs).ok == false)

-- Campo inválido e mismatch traitKind/campo devem falhar
assert(Bridge.submitOrApproveXP(xpSuite, "submit", { field = "sangue_max" }, nil, mockFirecast, mockDialogs).ok == false)
assert(Bridge.submitOrApproveXP(xpSuite, "submit", { traitKind = "willpower", field = "disc_slot1_nivel" }, nil, mockFirecast, mockDialogs).ok == false)

-- Submissão pendente bloqueia 2ª submissão até resolução
local pend1 = Bridge.submitOrApproveXP(xpSuite, "submit", { field = "disc_slot1_nivel", costCategory = "auto" }, nil, mockFirecast, mockDialogs)
assert(pend1.ok == true and xpSuite.xp_pendente_status == "pendente" and xpSuite.xp_pendente_custo == 5, "Potência em Brujah deve custar 5 XP (auto -> cla)")
local pendBlocked = Bridge.submitOrApproveXP(xpSuite, "submit", { field = "disc_slot4_nivel", costCategory = "auto" }, nil, mockFirecast, mockDialogs)
assert(pendBlocked.ok == false and pendBlocked.error:find("pendente") ~= nil, "Deve bloquear nova solicitação enquanto houver pendente")

-- Guarda de nível duplicado na aprovação
isMestreFlag = true
xpSuite.disc_slot1_nivel = 2
local staleApprove = Bridge.submitOrApproveXP(xpSuite, "approve", nil, nil, mockFirecast, mockDialogs)
assert(staleApprove.ok == false and xpSuite.xp_gasto == 0, "Não deve aprovar nem descontar XP se o nível já foi atingido")
xpSuite.disc_slot1_nivel = 1
local validApprove = Bridge.submitOrApproveXP(xpSuite, "approve", nil, nil, mockFirecast, mockDialogs)
assert(validApprove.ok == true and xpSuite.disc_slot1_nivel == 2 and xpSuite.xp_gasto == 5)

-- Auto-classificação fora do clã (x7) vs Qualidade Disciplina Adicional (x5) vs Caitiff (x6)
xpSuite.xp_exige_aprovacao = false
isMestreFlag = false
xpSuite.xp_loja_tipo = "auto"
xpSuite.xp_loja_campo = "disc_slot4_nivel"
xpSuite.xp_loja_cat_custo = "auto"
local outClanUp = Bridge.submitOrApproveXP(xpSuite, "submit", nil, nil, mockFirecast, mockDialogs)
assert(outClanUp.ok == true and xpSuite.disc_slot4_nivel == 2 and xpSuite.xp_gasto == 12, "Auspícios Nv 1->2 fora do clã deve custar 7 XP (5+7=12)")

xpSuite.mf_slot1_ativo = true
xpSuite.mf_slot1_id = "additional_disc"
local addDiscUp = Bridge.submitOrApproveXP(xpSuite, "submit", nil, nil, mockFirecast, mockDialogs)
assert(addDiscUp.ok == true and xpSuite.disc_slot4_nivel == 3 and xpSuite.xp_gasto == 22, "Com Disciplina Adicional, Auspícios Nv 2->3 deve custar 10 XP (x5)")

local caitiffXp = {
    nome = "[TESTE_E2E] Caitiff AutoCat",
    cla_id = "caitiff",
    is_vampire = true,
    xp_total = 30,
    xp_gasto = 0,
    xp_exige_aprovacao = false,
    disc_slot1_id = "auspex",
    disc_slot1_nivel = 2,
    disc_slot1_cat = "cla",
    xp_loja_tipo = "auto",
    xp_loja_campo = "disc_slot1_nivel",
    xp_loja_cat_custo = "auto",
}
local caitRes = Bridge.submitOrApproveXP(caitiffXp, "submit", nil, nil, mockFirecast, mockDialogs)
assert(caitRes.ok == true and caitiffXp.disc_slot1_nivel == 3 and caitiffXp.xp_gasto == 12, "Caitiff Nv 2->3 deve custar 12 XP (x6)")

-- Teto de Disciplina em Mortal Humano (0) vs Carniçal (carnical_disc_max default 1)
local humanXp = {
    nome = "[TESTE_E2E] Mortal Sem Disc",
    is_vampire = false,
    mortal_sobrenatural_modo = "humano",
    xp_total = 30,
    xp_gasto = 0,
    xp_exige_aprovacao = false,
    disc_slot2_id = "fortitude",
    disc_slot2_nivel = 0,
}
assert(Bridge.submitOrApproveXP(humanXp, "submit", { field = "disc_slot2_nivel" }, nil, mockFirecast, mockDialogs).ok == false)

-- 2.19 Finding #5: Carniçal (Ghoul) com Potência 1 automática destravada e ativável em 1 clique no Slot 1
local ghoulAutoSheet = {
    nome = "[TESTE_E2E] Renfield Slot 1",
    is_vampire = false,
    mortal_sobrenatural_modo = "carnical",
    sangue_atual = 2,
    sangue_gasto_turno = 0,
    disc_slot1_id = "potence",
    disc_slot1_nivel = 0,
    disc_slot1_pwr_lvl = 1,
    xp_total = 30,
    xp_gasto = 0,
    xp_exige_aprovacao = false,
}
Bridge.syncDerivedFields(ghoulAutoSheet)
assert(ghoulAutoSheet.isGhoul == true and ghoulAutoSheet.ghoulPotence == 1)
assert((ghoulAutoSheet.disc_slot1_resumo or ""):find("%[Requer Nv") == nil, "Potência Nv 1 do Carniçal deve aparecer destravada no resumo: " .. tostring(ghoulAutoSheet.disc_slot1_resumo))
local ghoulDiscs = Bridge.collectDisciplines(ghoulAutoSheet)
assert(#ghoulDiscs == 1 and ghoulDiscs[1].disc_id == "potence" and ghoulDiscs[1].nivel == 1)

sentMessages = {}
local ghoulPotAct = Bridge.activateDisciplineSlot(ghoulAutoSheet, 1, mockFirecast, mockDialogs)
assert(ghoulPotAct.ok == true and ghoulAutoSheet.sangue_atual == 1 and ghoulAutoSheet.potencia_ativa_turno == true and ghoulAutoSheet.potencia_sucessos_ativos == 1)
-- Teto de Disciplina Carniçal default = 1 bloqueia compra de Potência 1 -> 2 sem aumentar carnical_disc_max
assert(Bridge.submitOrApproveXP(ghoulAutoSheet, "submit", { field = "disc_slot1_nivel" }, nil, mockFirecast, mockDialogs).ok == false)

-- 2.20 Finding #6: Espelhamento bidirecional dano_agravado <-> dano_aggravado
local aggMirrorSheet = {
    nome = "[TESTE_E2E] Mirror Agravado",
    is_vampire = true,
    dano_agravado = 2,
}
Bridge.syncDerivedFields(aggMirrorSheet)
assert(aggMirrorSheet.dano_aggravado == 2 and aggMirrorSheet.dano_agravado == 2)
assert(aggMirrorSheet.vitalidade_resumo == "Machucado")
aggMirrorSheet.dano_aggravado = 3
Bridge.syncDerivedFields(aggMirrorSheet)
assert(aggMirrorSheet.dano_agravado == 3, "Alterar dano_aggravado deve espelhar em dano_agravado")
aggMirrorSheet.dano_agravado = 1
Bridge.syncDerivedFields(aggMirrorSheet)
assert(aggMirrorSheet.dano_aggravado == 1, "Alterar dano_agravado deve espelhar em dano_aggravado")

-- 2.21 Subprojeto 2: Nosferatu 7/5/3 na criação + falha automática em Aparência + desbloqueio via obf_mask
local nosfCreation = {
    nome = "[TESTE_E2E] Nosferatu 7/5/3",
    cla_id = "nosferatu",
    is_vampire = true,
    modo_ficha = "criacao",
    -- Físicos: 7 (4+2+4 -> 3+1+3 = 7)
    attr_forca = 4, attr_destreza = 2, attr_vigor = 4,
    -- Mentais: 5 (3+3+2 -> 2+2+1 = 5)
    attr_percepcao = 3, attr_inteligencia = 3, attr_raciocinio = 2,
    -- Sociais Nosferatu (base gratuita = 2, Aparência = 0): Carisma 3 + Manipulação 2 + Aparência 0 -> (3-1)+(2-1)+0 = 3!
    attr_carisma = 3, attr_manipulacao = 2, attr_aparencia = 0,
    -- Habilidades 13 / 9 / 5
    hab_prontidao = 3, hab_esportes = 2, hab_briga = 3, hab_intimidacao = 3, hab_manha = 2,
    hab_furtividade = 3, hab_empatia_animais = 3, hab_sobrevivencia = 3,
    hab_computador = 3, hab_investigacao = 2,
    -- Disciplinas: 3
    disc_slot1_id = "animalism", disc_slot1_nivel = 1,
    disc_slot2_id = "obfuscate", disc_slot2_nivel = 3,
    disc_slot3_id = "potence",   disc_slot3_nivel = 0,
    -- Antecedentes: 5
    bg_contacts = 2, bg_herd = 2, bg_resources = 1,
    -- Virtudes: 7 (3+3+4 -> 2+2+3 = 7)
    virtude1_val = 3, virtude2_val = 3, virtude3_val = 4,
    -- 1 ponto bônus de disciplina (7) + 8 FdV (8) = 15
    freebie_disciplines = 1, freebie_willpower = 8,
    sangue_atual = 10, fdv_perm = 6, fdv_temp = 6,
}
local nosfOk = Bridge.validateCreationOnSheet(nosfCreation, nil, mockFirecast, mockDialogs, false)
assert(nosfOk.valid == true, "Criação Nosferatu 7/5/3 com Aparência 0 deve ser válida: " .. table.concat(nosfOk.errors or {}, "; "))

nosfCreation.attr_aparencia = 1
local nosfBad = Bridge.validateCreationOnSheet(nosfCreation, nil, mockFirecast, mockDialogs, false)
assert(nosfBad.valid == false, "Nosferatu com Aparência 1 deve falhar na criação")
nosfCreation.attr_aparencia = 0

dialogMessages = {}
local nosfAppBlocked = Bridge.rollFromSheet(nosfCreation, { attrId = "attr_aparencia", habId = "hab_intimidacao", difficulty = 6 }, mockFirecast, mockDialogs)
assert(nosfAppBlocked.ok == false and tostring(nosfAppBlocked.error):find("Nosferatu") ~= nil, "Nosferatu sem obf_mask deve falhar automaticamente em Aparência")

-- Ativar Máscara das Mil Faces (obf_3) desbloqueia testes de Aparência (inclusive Aparência pura!)
nextFaces = { 8, 7, 6, 5, 4 }
local maskAct = Bridge.activateDisciplinePower(nosfCreation, 2, "obf_3", mockFirecast, mockDialogs)
assert(maskAct.ok == true, "obf_3 deveria ativar")
sentMessages = {}
nextFaces = { 9 }
local nosfAppMasked = Bridge.rollFromSheet(nosfCreation, { attrId = "attr_aparencia", difficulty = 6 }, mockFirecast, mockDialogs)
assert(nosfAppMasked.ok == true and #sentMessages == 1 and sentMessages[1]:find("1 Sucesso") ~= nil, "Nosferatu com obf_mask ativo deve rolar Aparência com sucesso")

-- 2.22 Tzimisce: parada dividida por 2^dias (8 -> 2 com 2 dias) e resetTzimisceSoil
local lastRolledExpr = nil
local captureFirecast = {
    interpretarRolagem = function(expr)
        lastRolledExpr = expr
        return mockFirecast.interpretarRolagem(expr)
    end,
    getMesaDe = mockFirecast.getMesaDe,
}
local tzimSheet = {
    nome = "[TESTE_E2E] Voivode Tzimisce",
    cla_id = "tzimisce",
    is_vampire = true,
    attr_inteligencia = 4,
    hab_medicina = 4,
    tzimisce_dias_sem_terra = 2,
    tzimisce_origem_terra = "Cárpatos",
}
sentMessages = {}
nextFaces = { 8, 9 }
local tzRoll = Bridge.rollFromSheet(tzimSheet, { attrId = "attr_inteligencia", habId = "hab_medicina", difficulty = 6 }, captureFirecast, mockDialogs)
assert(tzRoll.ok == true and lastRolledExpr == "2d10", "Tzimisce com 2 dias sem terra deve dividir 8 dados por 4 -> 2d10, obteve: " .. tostring(lastRolledExpr))
assert(sentMessages[1]:find("Fraqueza Tzimisce") ~= nil)

Bridge.resetTzimisceSoil(tzimSheet, captureFirecast, mockDialogs)
assert(tzimSheet.tzimisce_dias_sem_terra == 0)
nextFaces = { 8, 8, 8, 8, 8, 8, 8, 8 }
Bridge.rollFromSheet(tzimSheet, { attrId = "attr_inteligencia", habId = "hab_medicina", difficulty = 6 }, captureFirecast, mockDialogs)
assert(lastRolledExpr == "8d10", "Após resetTzimisceSoil, parada deve voltar para 8d10, obteve: " .. tostring(lastRolledExpr))

-- 2.23 Setita (-1 dado sob luz forte + +2 Agravado solar) e Lasombra (+1 dif espelhos + +1 Agravado solar)
local setiteSheet = {
    nome = "[TESTE_E2E] Hesha Setita",
    cla_id = "setite",
    is_vampire = true,
    attr_manipulacao = 3,
    hab_labia = 2,
    setita_luz_forte = true,
    dano_fonte_solar = true,
}
nextFaces = { 7, 7, 7, 7 }
Bridge.rollFromSheet(setiteSheet, { attrId = "attr_manipulacao", habId = "hab_labia", difficulty = 6 }, captureFirecast, mockDialogs)
assert(lastRolledExpr == "4d10", "Setita sob luz forte deve perder 1 dado (5 -> 4d10), obteve: " .. tostring(lastRolledExpr))

Bridge.applyDamage(setiteSheet, 2, "aggravated", {}, mockFirecast, mockDialogs)
assert(setiteSheet.dano_aggravado == 4, "Setita recebendo 2 de dano com dano_fonte_solar=true deve sofrer 4 níveis Agravados, obteve: " .. tostring(setiteSheet.dano_aggravado))

local lasombraSheet = {
    nome = "[TESTE_E2E] Lucita Lasombra",
    cla_id = "lasombra",
    is_vampire = true,
    attr_manipulacao = 3,
    hab_furtividade = 2,
    lasombra_vigiado_espelhos = true,
    dano_fonte_solar = true,
}
sentMessages = {}
nextFaces = { 8, 7, 6, 5, 4 }
Bridge.rollFromSheet(lasombraSheet, { attrId = "attr_manipulacao", habId = "hab_furtividade", difficulty = 6 }, captureFirecast, mockDialogs)
assert(sentMessages[1]:find("Dif 7") ~= nil, "Lasombra vigiado por espelhos deve receber +1 dif (6 -> 7): " .. tostring(sentMessages[1]))

Bridge.applyDamage(lasombraSheet, 2, "bashing", {}, mockFirecast, mockDialogs)
assert(lasombraSheet.dano_aggravado == 3, "Lasombra recebendo 2 de dano solar deve converter e somar +1 Agravado (= 3), obteve: " .. tostring(lasombraSheet.dano_aggravado))

-- 2.24 Brujah endBrujahFrenzy, Gangrel 5º traço + logAudit, Malkavian, Toreador, Tremere, Ventrue, Assamita, Giovanni, Ravnos e Caitiff
local brujahFrenzySheet = {
    nome = "[TESTE_E2E] Brujah Frenético",
    cla_id = "brujah",
    is_vampire = true,
    em_frenesi = true,
    fdv_perm = 5,
    fdv_temp = 4,
}
local endFr = Bridge.endBrujahFrenzy(brujahFrenzySheet, mockFirecast, mockDialogs)
assert(endFr.ok == true and brujahFrenzySheet.em_frenesi == false and brujahFrenzySheet.fdv_temp == 3)

local gangrelSheet = {
    nome = "[TESTE_E2E] Ramona Gangrel",
    cla_id = "gangrel",
    is_vampire = true,
    gangrel_tracos_qtd = 4,
    gangrel_attr_penalizado = "attr_carisma",
    attr_carisma = 3,
}
local gfRes = Bridge.recordGangrelFrenzy(gangrelSheet, mockFirecast, mockDialogs)
assert(gfRes.ok == true and gangrelSheet.gangrel_tracos_qtd == 5 and gangrelSheet.attr_carisma == 2)
assert((gangrelSheet.auditoria_xp_log or ""):find("Carisma") ~= nil, "5º traço Gangrel deve gravar perda permanente em logAudit")

-- Malkaviano: trava de criação + supressão por FdV + limpeza em clearSceneBuffs
local malkSheet = {
    nome = "[TESTE_E2E] Anatole Malkav",
    cla_id = "malkavian",
    is_vampire = true,
    malkav_perturbacao = "",
    fdv_perm = 5,
    fdv_temp = 3,
}
local malkInvalid = Bridge.validateCreationOnSheet(malkSheet, nil, mockFirecast, mockDialogs, false)
assert(malkInvalid.valid == false and table.concat(malkInvalid.errors, " "):find("Perturbação") ~= nil)
local supMalk = Bridge.suppressMalkavianDerangement(malkSheet, mockFirecast, mockDialogs)
assert(supMalk.ok == true and malkSheet.malkav_suprimida_cena == true and malkSheet.fdv_temp == 2)

-- Toreador: falha marca toreador_fascinado_cena = true; clearSceneBuffs limpa Malkav e Toreador
local torSheet = {
    nome = "[TESTE_E2E] Victoria Toreador",
    cla_id = "toreador",
    is_vampire = true,
    virtude2_val = 2,
}
nextFaces = { 2, 3 }
Bridge.rollToreadorFascination(torSheet, mockFirecast, mockDialogs)
assert(torSheet.toreador_fascinado_cena == true, "Falha em Fascínio Toreador deve marcar toreador_fascinado_cena=true")
Bridge.clearSceneBuffs(torSheet, mockFirecast, mockDialogs)
Bridge.clearSceneBuffs(malkSheet, mockFirecast, mockDialogs)
assert(torSheet.toreador_fascinado_cena == false and malkSheet.malkav_suprimida_cena == false, "clearSceneBuffs deve limpar malkav_suprimida_cena e toreador_fascinado_cena")

-- Tremere: 2 goles = Laço de Sangue Completo (2/2)
local tremSheet = {
    nome = "[TESTE_E2E] Aisling Tremere",
    cla_id = "tremere",
    is_vampire = true,
    tremere_laco_goles = 0,
    tremere_regente_nome = "Etrius",
}
local tr1 = Bridge.recordTremereDrink(tremSheet, mockFirecast, mockDialogs)
assert(tr1.step == 1 and tr1.fullBond == false)
local tr2 = Bridge.recordTremereDrink(tremSheet, mockFirecast, mockDialogs)
assert(tr2.step == 2 and tr2.fullBond == true and tostring(tremSheet.tremere_laco_status):find("2/2") ~= nil)

-- Ventrue: trava de criação + bloqueio de caça incompatível
local ventSheet = {
    nome = "[TESTE_E2E] Jan Pieterzoon",
    cla_id = "ventrue",
    is_vampire = true,
    sangue_atual = 4,
    ventrue_presa_restrita = "",
    ventrue_presa_compativel = false,
}
local ventInvalid = Bridge.validateCreationOnSheet(ventSheet, nil, mockFirecast, mockDialogs, false)
assert(ventInvalid.valid == false and table.concat(ventInvalid.errors, " "):find("Ventrue") ~= nil)
nextFaces = { 9, 9, 9 }
local ventHuntBlocked = Bridge.huntWithHerdDomain(ventSheet, {}, mockFirecast, mockDialogs)
assert(ventHuntBlocked.ok == false and ventSheet.sangue_atual == 4, "Ventrue com presa incompatível não deve ganhar sangue")

-- Assamita: Ur-Shulgi vs Tremere Clássica
local assamSheet = {
    nome = "[TESTE_E2E] Tariq Assamita",
    cla_id = "assamite",
    is_vampire = true,
    geracao_base = 12,
    sangue_atual = 4,
    virtude2_val = 2,
    assamita_maldicao_modo = "ur_shulgi",
}
nextFaces = { 2, 3 } -- falha no teste de vício dif 5
local urRes = Bridge.ingestAssamiteVitae(assamSheet, 2, mockFirecast, mockDialogs)
assert(urRes.ok == true and assamSheet.dano_letal == 2 and assamSheet.sangue_atual == 6 and assamSheet.assamita_vicio_ativo == true)

assamSheet.assamita_maldicao_modo = "tremere_classica"
local trCurseRes = Bridge.ingestAssamiteVitae(assamSheet, 1, mockFirecast, mockDialogs)
assert(trCurseRes.ok == true and assamSheet.dano_letal == 3 and assamSheet.sangue_atual == 6, "Tremere clássica causa dano letal sem ganhar sangue")

-- Giovanni: 2x dano letal no Beijo (direto e na caça)
local gioSheet = {
    nome = "[TESTE_E2E] Isabel Giovanni",
    cla_id = "giovanni",
    is_vampire = true,
    sangue_atual = 3,
}
sentMessages = {}
local kissRes = Bridge.applyGiovanniKiss(gioSheet, 4, mockFirecast, mockDialogs)
assert(kissRes.ok == true and kissRes.lethalToVessel == 8 and kissRes.fatalRisk == true and gioSheet.sangue_atual == 7)
assert(#sentMessages >= 1 and sentMessages[#sentMessages]:find("8") ~= nil)

sentMessages = {}
nextFaces = { 8, 8, 8 }
Bridge.huntWithHerdDomain(gioSheet, { difficulty = 6 }, mockFirecast, mockDialogs)
assert(sentMessages[#sentMessages]:find("6 níveis Letais") ~= nil, "Caça Giovanni com 3 sucessos deve anunciar 6 níveis letais no recipiente")

-- Ravnos: trava de criação + compulsão ativa em falha
local ravSheet = {
    nome = "[TESTE_E2E] Khalil Ravnos",
    cla_id = "ravnos",
    is_vampire = true,
    ravnos_vicio_descricao = "",
    virtude2_val = 2,
}
local ravInvalid = Bridge.validateCreationOnSheet(ravSheet, nil, mockFirecast, mockDialogs, false)
assert(ravInvalid.valid == false and table.concat(ravInvalid.errors, " "):find("Ravnos") ~= nil)
nextFaces = { 2, 2 }
Bridge.rollRavnosVice(ravSheet, mockFirecast, mockDialogs)
assert(ravSheet.ravnos_compulsao_ativa == true)

-- Caitiff: +2 dif Social em rollFromSheet com caitiff_estigma_ativo = true
local caitSocial = {
    nome = "[TESTE_E2E] Pária Caitiff",
    cla_id = "caitiff",
    is_vampire = true,
    attr_carisma = 3,
    hab_labia = 2,
    caitiff_estigma_ativo = true,
}
sentMessages = {}
nextFaces = { 9, 8, 7, 6, 5 }
Bridge.rollFromSheet(caitSocial, { attrId = "attr_carisma", habId = "hab_labia", difficulty = 6 }, mockFirecast, mockDialogs)
assert(sentMessages[1]:find("Dif 8") ~= nil, "Caitiff com estigma ativo deve sofrer +2 dif Social (6 -> 8): " .. tostring(sentMessages[1]))

-- 2.25 Magia do Sangue, Acesso Dinâmico (Aba 8), Linhas Secundárias na Loja de XP e Rituais
assert(Bridge.hasBloodMagicAccess({ cla_id = "tremere", is_vampire = true }) == true)
assert(Bridge.hasBloodMagicAccess({ cla_id = "giovanni", is_vampire = true }) == true)

local bmBrujah = {
    nome = "[TESTE_E2E] Brujah Ocultista",
    cla_id = "brujah",
    is_vampire = true,
    geracao_base = 12,
    sangue_atual = 10,
    fdv_perm = 6,
    fdv_temp = 6,
    attr_inteligencia = 3,
    hab_ocultismo = 3,
    xp_total = 30,
    xp_gasto = 0,
    xp_exige_aprovacao = false,
    bm_thau_prim_id = "path_of_blood",
    bm_sec1_disc = "thaumaturgy",
    bm_sec1_path_id = "lure_of_flames",
    bm_sec1_nivel = 0,
}
assert(Bridge.hasBloodMagicAccess(bmBrujah) == false, "Brujah sem Taumaturgia/Necromancia/Rituais não tem acesso inicial")

-- Selecionar Taumaturgia mesmo em nível 0 (criação) já libera Aba 8
bmBrujah.disc_slot4_id = "thaumaturgy"
bmBrujah.disc_slot4_nivel = 0
assert(Bridge.hasBloodMagicAccess(bmBrujah) == true, "Selecionar Taumaturgia no slot já deve liberar Aba 8")

-- Taumaturgia Nv 2 -> compra Linha Secundária 0 -> 1 por 7 XP, e bloqueia 1 -> 2 enquanto Primária for 2
bmBrujah.disc_slot4_nivel = 2
Bridge.syncDerivedFields(bmBrujah)
assert(bmBrujah.bm_thau_prim_nivel == 2)

isMestreFlag = false
local secBuy1 = Bridge.submitOrApproveXP(bmBrujah, "submit", { field = "bm_sec1_nivel" }, nil, mockFirecast, mockDialogs)
assert(secBuy1.ok == true and bmBrujah.bm_sec1_nivel == 1 and bmBrujah.xp_gasto == 7, "Compra de Linha Secundária 0->1 deve custar 7 XP")

local secBlocked2 = Bridge.submitOrApproveXP(bmBrujah, "submit", { field = "bm_sec1_nivel" }, nil, mockFirecast, mockDialogs)
assert(secBlocked2.ok == false and bmBrujah.bm_sec1_nivel == 1, "Deve bloquear Linha Secundária 1->2 enquanto Taumaturgia Primária estiver em 2")

bmBrujah.disc_slot4_nivel = 3
local secBuy2 = Bridge.submitOrApproveXP(bmBrujah, "submit", { field = "bm_sec1_nivel" }, nil, mockFirecast, mockDialogs)
assert(secBuy2.ok == true and bmBrujah.bm_sec1_nivel == 2 and bmBrujah.xp_gasto == 11, "Com Primária 3, Linha Secundária 1->2 deve custar 4 XP (total 11)")

-- Ativar poder da Linha Primária e da Linha Secundária + Conjurar Ritual Oficial e Customizado
sentMessages = {}
nextFaces = { 8, 7, 6, 5, 4, 3 }
local actPrim = Bridge.activatePrimaryBloodMagic(bmBrujah, "thaumaturgy", 2, mockFirecast, mockDialogs)
assert(actPrim.ok == true and bmBrujah.sangue_atual == 9 and sentMessages[1]:find("Dif 5") ~= nil)

Bridge.newTurn(bmBrujah, mockFirecast, mockDialogs)
sentMessages = {}
local actSec = Bridge.activateSecondaryBloodMagic(bmBrujah, 1, 2, mockFirecast, mockDialogs)
assert(actSec.ok == true and bmBrujah.sangue_atual == 8 and sentMessages[1]:find("Punhado de Chamas") ~= nil)

-- Ritual Nv 4 bloqueado com Taumaturgia 3; Ritual Nv 2 aprovado
local ritFail = Bridge.castCatalogRitual(bmBrujah, "thau_rit_4_heart_stone", mockFirecast, mockDialogs)
assert(ritFail.ok == false, "Ritual Nv 4 deve ser bloqueado com Taumaturgia 3")

sentMessages = {}
local ritOk = Bridge.castCatalogRitual(bmBrujah, "thau_rit_2_ward_ghouls", mockFirecast, mockDialogs)
assert(ritOk.ok == true and bmBrujah.sangue_atual == 7 and sentMessages[1]:find("Proteção Contra Carniçais") ~= nil)

bmBrujah.ritual_custom_nome = "[TESTE_E2E] Selo Carmesim"
bmBrujah.ritual_custom_trad = "thaumaturgy"
bmBrujah.ritual_custom_nivel = 2
bmBrujah.ritual_custom_sangue = 1
bmBrujah.ritual_custom_fdv = 0
bmBrujah.ritual_custom_dif = 5
sentMessages = {}
local ritCustomOk = Bridge.castCustomRitual(bmBrujah, mockFirecast, mockDialogs)
assert(ritCustomOk.ok == true and bmBrujah.sangue_atual == 6 and sentMessages[1]:find("Selo Carmesim") ~= nil)

-- Canalização 15ª Geração em Magia do Sangue (2 vitae em 2 turnos) e trava de Linha Secundária em validateCreationOnSheet
local gen15Bm = {
    nome = "[TESTE_E2E] ThinBlood Taumaturgo",
    cla_id = "caitiff",
    is_vampire = true,
    mf_gen_15th = true,
    sangue_atual = 8,
    sangue_gasto_turno = 0,
    sangue_fraco_usado = 0,
    fdv_perm = 6,
    fdv_temp = 6,
    disc_slot1_id = "thaumaturgy",
    disc_slot1_nivel = 1,
    bm_thau_prim_id = "path_of_blood",
    bm_sec1_disc = "thaumaturgy",
    bm_sec1_path_id = "lure_of_flames",
    bm_sec1_nivel = 1,
}
local badSecCreation = Bridge.validateCreationOnSheet(gen15Bm, nil, mockFirecast, mockDialogs, false)
assert(badSecCreation.valid == false, "Linha Secundária Nv 1 com Taumaturgia Nv 1 deve ser rejeitada na criação")

sentMessages = {}
nextFaces = { 8, 7, 6, 5, 4, 3 }
local g15BmAct = Bridge.activatePrimaryBloodMagic(gen15Bm, "thaumaturgy", 1, mockFirecast, mockDialogs)
assert(g15BmAct.ok == true and gen15Bm.sangue_atual == 6 and gen15Bm.sangue_gasto_turno == 2)
assert(sentMessages[1]:find("(15ª Geração: 2 pts de vitae canalizados em 2 turnos)", 1, true) ~= nil)

-- 2.26 Fix Round 1: bm_sec1..4 contabilizados em discDots na criação + bloqueio de Linhas Secundárias duplicadas
local tremereCreation = {
    nome = "[TESTE_E2E] Tremere Neófito Linhas",
    cla_id = "tremere",
    is_vampire = true,
    modo_ficha = "criacao",
    -- Mentais: 7 (4+4+2 -> 3+3+1 = 7)
    attr_percepcao = 4, attr_inteligencia = 4, attr_raciocinio = 2,
    -- Sociais: 5 (3+3+2 -> 2+2+1 = 5)
    attr_carisma = 3, attr_manipulacao = 3, attr_aparencia = 2,
    -- Físicos: 3 (2+2+2 -> 1+1+1 = 3)
    attr_forca = 2, attr_destreza = 2, attr_vigor = 2,
    -- Habilidades: 13 Conhecimentos / 9 Talentos / 5 Perícias
    hab_ocultismo = 3, hab_academicos = 3, hab_investigacao = 3, hab_ciencias = 2, hab_medicina = 2,
    hab_prontidao = 3, hab_consciencia = 3, hab_empatia = 3,
    hab_etiqueta = 3, hab_furtividade = 2,
    -- Disciplinas iniciais = 3 pontos totais: Taumaturgia 2 + Linha Secundária (Sedutor das Chamas) 1!
    disc_slot1_id = "auspex",      disc_slot1_nivel = 0,
    disc_slot2_id = "dominate",    disc_slot2_nivel = 0,
    disc_slot3_id = "thaumaturgy", disc_slot3_nivel = 2,
    bm_thau_prim_id = "path_of_blood",
    bm_sec1_disc = "thaumaturgy",
    bm_sec1_path_id = "lure_of_flames",
    bm_sec1_nivel = 1,
    -- Antecedentes = 5
    bg_mentor = 2, bg_resources = 2, bg_rituals = 1,
    -- Virtudes = 7 (3+4+3 -> 2+3+2 = 7)
    virtude1_val = 3, virtude2_val = 4, virtude3_val = 3,
    -- 15 pontos de bônus gastos em Força de Vontade/Antecedentes? 15 em FdV/Moralidade -> vamos gastar 5 FdV (5) + 3 Antec extras? Não: 5 FdV = 5 restantes 10 (permitido <= 15, ou exato 7 Disc + 8 FdV abaixo!)
    freebie_disciplines = 0,
    freebie_willpower = 5,
}
-- (a) Taumaturgia 2 + bm_sec1_nivel 1 = 3 pontos iniciais de Disciplina -> VÁLIDO!
local trSecValid = Bridge.validateCreationOnSheet(tremereCreation, nil, mockFirecast, mockDialogs, false)
assert(trSecValid.valid == true, "Criação Tremere (Taumaturgia 2 + Secundária 1 = 3 Disciplinas) deve ser válida: " .. table.concat(trSecValid.errors or {}, "; "))

-- (b) Taumaturgia 3 + bm_sec1_nivel 1 (= 4 pontos) com freebie_disciplines = 0 -> REJEITADO (sem ponto grátis!)
tremereCreation.disc_slot3_nivel = 3
local trUnpaidSec = Bridge.validateCreationOnSheet(tremereCreation, nil, mockFirecast, mockDialogs, false)
assert(trUnpaidSec.valid == false, "bm_sec1_nivel=1 acima dos 3 pontos base sem freebie_disciplines deve ser rejeitado!")

-- Pagando freebie_disciplines = 1 (7 pts + 5 FdV = 12/15) -> VÁLIDO!
tremereCreation.freebie_disciplines = 1
local trPaidSec = Bridge.validateCreationOnSheet(tremereCreation, nil, mockFirecast, mockDialogs, false)
assert(trPaidSec.valid == true, "Com freebie_disciplines=1, Taumaturgia 3 + Secundária 1 deve ser válida: " .. table.concat(trPaidSec.errors or {}, "; "))

-- (c) Linhas Secundárias duplicadas em dois slots (bm_sec1 e bm_sec2 com 'lure_of_flames') -> REJEITADO na criação e na Loja de XP!
tremereCreation.bm_sec2_disc = "thaumaturgy"
tremereCreation.bm_sec2_path_id = "lure_of_flames"
tremereCreation.bm_sec2_nivel = 1
tremereCreation.freebie_disciplines = 2
tremereCreation.freebie_willpower = 1
local trDupCreation = Bridge.validateCreationOnSheet(tremereCreation, nil, mockFirecast, mockDialogs, false)
assert(trDupCreation.valid == false, "Linha Secundária duplicada entre bm_sec1 e bm_sec2 deve ser rejeitada na criação!")

bmBrujah.xp_total = 50
bmBrujah.bm_sec2_disc = "thaumaturgy"
bmBrujah.bm_sec2_path_id = "lure_of_flames"
bmBrujah.bm_sec2_nivel = 0
local dupXpRes = Bridge.submitOrApproveXP(bmBrujah, "submit", { field = "bm_sec2_nivel" }, nil, mockFirecast, mockDialogs)
assert(dupXpRes.ok == false and bmBrujah.bm_sec2_nivel == 0, "Loja de XP deve rejeitar compra de Linha Secundária duplicada em outro slot!")

-- 2.27 Subprojeto 3 Task 3: Estúdio de Manobras V20 (Divisão, Rapidez, Agarrão -> Mordida -> Dano + Potência, Guardas PF3-3)
assert(type(Bridge.executeCombatManeuver) == "function", "executeCombatManeuver ausente em V20Bridge")
assert(type(Bridge.rollPendingCombatDamage) == "function", "rollPendingCombatDamage ausente em V20Bridge")

local combatSheet = {
    nome = "[TESTE_E2E] Theo Bell Combate",
    cla_id = "brujah",
    is_vampire = true,
    geracao_base = 10,
    sangue_atual = 10,
    sangue_gasto_turno = 0,
    fdv_perm = 6,
    fdv_temp = 6,
    attr_forca = 3,
    attr_destreza = 4,
    attr_vigor = 3,
    attr_percepcao = 3,
    attr_raciocinio = 3,
    hab_briga = 3,
    hab_esportes = 3,
    hab_armas_brancas = 3,
    hab_armas_fogo = 3,
    disc_slot1_id = "celerity",
    disc_slot1_nivel = 2,
    disc_slot2_id = "potence",
    disc_slot2_nivel = 2,
    cmb_manobra_id = "strike",
    cmb_acoes_normais = 2,
    cmb_acao_ordem = 1,
    cmb_menor_parada = 5,
    cmb_acao_rapidez = false,
    cmb_defesa_alvo_sucessos = 0,
    cmb_forca_alvo = 2,
    cmb_defesas_feitas_turno = 0,
    em_agarrao = false,
}
Bridge.syncDerivedFields(combatSheet)
-- Destreza(4) + Rapidez passiva(2) + Briga(3) = 9; menor parada = 5; 2 ações normais -> 1ª = 5-2 = 3d10, 2ª = 5-3 = 2d10
sentMessages = {}
nextFaces = { 8, 7, 3 }
local splitAct1 = Bridge.executeCombatManeuver(combatSheet, {}, captureFirecast, mockDialogs)
assert(splitAct1.ok == true and lastRolledExpr == "3d10", "1ª ação dividida (base 5, 2 ações) deve rolar 3d10, obteve: " .. tostring(lastRolledExpr))

combatSheet.cmb_acao_ordem = 2
nextFaces = { 8, 4 }
local splitAct2 = Bridge.executeCombatManeuver(combatSheet, {}, captureFirecast, mockDialogs)
assert(splitAct2.ok == true and lastRolledExpr == "2d10", "2ª ação dividida (base 5, 2 ações) deve rolar 2d10, obteve: " .. tostring(lastRolledExpr))

-- Ativando 1 ação extra de Rapidez: rapidez_acoes_extras = 1, rapidez_dados_passivos cai de 2 p/ 1 -> Des(4)+RapPass(1)+Briga(3) = 8d10 sem divisão!
Bridge.newTurn(combatSheet, captureFirecast, mockDialogs)
local actCel1 = Bridge.activateDisciplinePower(combatSheet, "celerity", "cel_1", captureFirecast, mockDialogs)
assert(actCel1.ok == true and combatSheet.rapidez_acoes_extras == 1)
combatSheet.cmb_acao_rapidez = true
combatSheet.cmb_acoes_normais = 3
combatSheet.cmb_acao_ordem = 3
combatSheet.cmb_menor_parada = 4
nextFaces = { 9, 8, 7, 6, 5, 4, 3, 2 }
local celStrike = Bridge.executeCombatManeuver(combatSheet, {}, captureFirecast, mockDialogs)
assert(celStrike.ok == true and lastRolledExpr == "8d10", "Ação de Rapidez deve ignorar divisão de paradas e rolar 8d10, obteve: " .. tostring(lastRolledExpr))
assert(combatSheet.rapidez_acoes_extras == 0, "Ação de Rapidez deve consumir 1 de rapidez_acoes_extras")

-- Segunda tentativa de Rapidez sem ações extras restantes deve falhar
dialogMessages = {}
local celEmpty = Bridge.executeCombatManeuver(combatSheet, {}, captureFirecast, mockDialogs)
assert(celEmpty.ok == false and #dialogMessages >= 1, "Sem rapidez_acoes_extras deve bloquear ação extra de Rapidez")
combatSheet.cmb_acao_rapidez = false
combatSheet.cmb_acoes_normais = 1
combatSheet.cmb_acao_ordem = 1
combatSheet.cmb_menor_parada = 0

-- PF3-3 #3: Rolagem bloqueada (Incapacitado ou luz forte Setita zerando parada) NÃO desperdiça Rapidez nem incrementa defesas!
Bridge.newTurn(combatSheet, captureFirecast, mockDialogs)
Bridge.activateDisciplinePower(combatSheet, "celerity", "cel_1", captureFirecast, mockDialogs)
assert(combatSheet.rapidez_acoes_extras == 1)
combatSheet.dano_letal = 7 -- Incapacitado
Bridge.syncDerivedFields(combatSheet)
assert(combatSheet.incapacitado == true)
local incapCel = Bridge.executeCombatManeuver(combatSheet, { maneuverId = "strike", isCelerityAction = true }, captureFirecast, mockDialogs)
assert(incapCel.ok == false and combatSheet.rapidez_acoes_extras == 1, "Rolagem bloqueada por Incapacitado NÃO pode gastar rapidez_acoes_extras!")
local incapDef = Bridge.executeCombatManeuver(combatSheet, { maneuverId = "dodge" }, captureFirecast, mockDialogs)
assert(incapDef.ok == false and combatSheet.cmb_defesas_feitas_turno == 0, "Defesa bloqueada por Incapacitado NÃO pode incrementar cmb_defesas_feitas_turno!")
combatSheet.dano_letal = 0
Bridge.syncDerivedFields(combatSheet)

local setiteFragile = {
    nome = "[TESTE_E2E] Setita Ofuscado",
    cla_id = "setite",
    is_vampire = true,
    attr_destreza = 1,
    hab_esportes = 0,
    hab_briga = 0,
    setita_luz_forte = true,
    rapidez_acoes_extras = 1,
    cmb_defesas_feitas_turno = 0,
}
local setiteBlockedCel = Bridge.executeCombatManeuver(setiteFragile, { maneuverId = "strike", isCelerityAction = true }, captureFirecast, mockDialogs)
assert(setiteBlockedCel.ok == false and setiteFragile.rapidez_acoes_extras == 1, "Luz forte Setita reduzindo parada de 1 p/ 0 não pode gastar rapidez_acoes_extras!")
local setiteBlockedDef = Bridge.executeCombatManeuver(setiteFragile, { maneuverId = "dodge" }, captureFirecast, mockDialogs)
assert(setiteBlockedDef.ok == false and setiteFragile.cmb_defesas_feitas_turno == 0, "Luz forte Setita reduzindo defesa p/ 0 não pode incrementar cmb_defesas_feitas_turno!")

-- Defesas ativas cumulativas (-1 dado por defesa prévia no turno) + reset em newTurn
Bridge.newTurn(combatSheet, captureFirecast, mockDialogs)
-- combatSheet: Des(4) + RapPassiva(2) + Esportes(3) = 9d10 na 1ª esquiva, 8d10 na 2ª esquiva
nextFaces = { 8, 8, 8, 8, 8, 8, 8, 8, 8 }
local d1 = Bridge.executeCombatManeuver(combatSheet, { maneuverId = "dodge" }, captureFirecast, mockDialogs)
assert(d1.ok == true and lastRolledExpr == "9d10" and combatSheet.cmb_defesas_feitas_turno == 1)
nextFaces = { 8, 8, 8, 8, 8, 8, 8, 8 }
local d2 = Bridge.executeCombatManeuver(combatSheet, { maneuverId = "dodge" }, captureFirecast, mockDialogs)
assert(d2.ok == true and lastRolledExpr == "8d10" and combatSheet.cmb_defesas_feitas_turno == 2)
Bridge.newTurn(combatSheet, captureFirecast, mockDialogs)
assert(combatSheet.cmb_defesas_feitas_turno == 0, "newTurn deve zerar cmb_defesas_feitas_turno")

-- Encadeamento Clinch (c/ Potência Automática no ataque Força + dano!) -> em_agarrao = true -> Bite Agravado -> rollPendingCombatDamage
local biteBeforeGrapple = Bridge.executeCombatManeuver(combatSheet, { maneuverId = "bite" }, captureFirecast, mockDialogs)
assert(biteBeforeGrapple.ok == false, "Mordida deve falhar antes de estar em agarrão")

-- Ativa Potência por sangue (Potência 2 -> activePotenceAuto = 2, passivePotenceDice = 0)
local actPotAuto = Bridge.activateDisciplinePower(combatSheet, "potence", "pot_2", captureFirecast, mockDialogs)
assert(actPotAuto.ok == true and combatSheet.potencia_ativa_turno == true and combatSheet.potencia_sucessos_ativos == 2)

-- Clinch usa Força(3) + Briga(3) = 6d10 + 2 autoSuccesses de Potência no ataque (V20, p. 192 / PF3-3 #1)!
-- Com dados todos baixos {2,3,2,3,4,5} (0 nos dados) + 2 autoSuccesses de Potência - 1 defesa = 1 sucesso líquido!
combatSheet.cmb_defesa_alvo_sucessos = 1
sentMessages = {}
nextFaces = { 2, 3, 2, 3, 4, 5 }
local clinchRes = Bridge.executeCombatManeuver(combatSheet, { maneuverId = "clinch" }, captureFirecast, mockDialogs)
assert(clinchRes.ok == true and lastRolledExpr == "6d10", "Clinch com Potência ativa deve rolar For(3)+Briga(3)=6d10")
assert(combatSheet.em_agarrao == true, "Clinch bem-sucedido (graças aos 2 auto-sucessos de Potência) deve ligar em_agarrao = true!")
assert(combatSheet.cmb_dano_pendente_ativo == true and combatSheet.cmb_dano_pendente_parada == 3 and combatSheet.cmb_dano_pendente_auto == 2)

-- Agora em Agarrão, Mordida Vampírica: Des(4) + RapPassiva(2) + Briga(3) + 1 (precisão mordida) = 10d10, Dif 6
combatSheet.cmb_defesa_alvo_sucessos = 1
sentMessages = {}
nextFaces = { 9, 8, 7, 6, 2, 2, 2, 2, 2, 2 } -- 4 sucessos de ataque - 1 defesa = 3 líquidos (carryOver = 2)
local biteRes = Bridge.executeCombatManeuver(combatSheet, { maneuverId = "bite" }, captureFirecast, mockDialogs)
assert(biteRes.ok == true and lastRolledExpr == "10d10", "Mordida vampírica deve rolar 10d10, obteve: " .. tostring(lastRolledExpr))
-- Dano base Mordida = Força(3) + 1 = 4; carryOver = 2 -> parada = 6d10 + 2 auto (Potência) Agravado!
assert(combatSheet.cmb_dano_pendente_ativo == true)
assert(combatSheet.cmb_dano_pendente_tipo == "aggravated")
assert(combatSheet.cmb_dano_pendente_parada == 6, "Esperado 6 dados de dano na mordida, obteve: " .. tostring(combatSheet.cmb_dano_pendente_parada))
assert(combatSheet.cmb_dano_pendente_auto == 2, "Esperado 2 auto-sucessos de Potência no dano, obteve: " .. tostring(combatSheet.cmb_dano_pendente_auto))
assert(sentMessages[#sentMessages]:find("6d10") ~= nil and sentMessages[#sentMessages]:find("Agravado") ~= nil)

-- Rolar dano pendente: ignora penalidade de ferimento e fraqueza de clã (testando ferimento -5 + Tzimisce/Setita simulados)
combatSheet.dano_letal = 6 -- Aleijado (-5)
Bridge.syncDerivedFields(combatSheet)
sentMessages = {}
nextFaces = { 9, 8, 7, 2, 2, 2 } -- 3 sucessos rolados + 2 autoSuccesses de Potência = 5 níveis Agravados!
local dmgRollRes = Bridge.rollPendingCombatDamage(combatSheet, captureFirecast, mockDialogs)
assert(dmgRollRes.ok == true and lastRolledExpr == "6d10", "Dano encadeado deve ignorar penalidade de ferimento (-5) e rolar 6d10!")
assert(combatSheet.cmb_dano_pendente_ativo == false, "rollPendingCombatDamage deve limpar cmb_dano_pendente_ativo")
assert(sentMessages[#sentMessages]:find("Dano Bruto %(aggravated%): 5") ~= nil, "Esperado 5 níveis agravados (3 rolados + 2 auto): " .. tostring(sentMessages[#sentMessages]))

-- Caso extremo: parada rolada 0 + autoSuccesses > 0 em rollPendingCombatDamage (allowZeroPoolWithAuto)
combatSheet.cmb_dano_pendente_ativo = true
combatSheet.cmb_dano_pendente_parada = 0
combatSheet.cmb_dano_pendente_auto = 2
combatSheet.cmb_dano_pendente_tipo = "bashing"
combatSheet.cmb_dano_pendente_estaca = false
sentMessages = {}
local zeroPoolAutoDmg = Bridge.rollPendingCombatDamage(combatSheet, captureFirecast, mockDialogs)
assert(zeroPoolAutoDmg.ok == true and combatSheet.cmb_dano_pendente_ativo == false)
assert(sentMessages[#sentMessages]:find("Dano Bruto %(bashing%): 2") ~= nil)

-- Sem dano pendente ativo, rollPendingCombatDamage avisa via showMessage
dialogMessages = {}
local noPendingDmg = Bridge.rollPendingCombatDamage(combatSheet, captureFirecast, mockDialogs)
assert(noPendingDmg.ok == false and #dialogMessages >= 1)

-- clearSceneBuffs limpa em_agarrao, cmb_defesas_feitas_turno e cmb_dano_pendente_ativo
combatSheet.cmb_defesas_feitas_turno = 2
combatSheet.cmb_dano_pendente_ativo = true
Bridge.clearSceneBuffs(combatSheet, captureFirecast, mockDialogs)
assert(combatSheet.em_agarrao == false and combatSheet.cmb_defesas_feitas_turno == 0 and combatSheet.cmb_dano_pendente_ativo == false)

-- PF3-3 #2: Buffs de garras/língua agravadas (prot_claws) e Carícia de Baal (quie_baal) na arma equipada
local buffCombatSheet = {
    nome = "[TESTE_E2E] Assamita Metamorfose",
    cla_id = "assamite",
    is_vampire = true,
    geracao_base = 10,
    sangue_atual = 10,
    attr_forca = 3,
    attr_destreza = 4,
    hab_briga = 3,
    hab_armas_brancas = 4,
    disc_slot1_id = "protean",
    disc_slot1_nivel = 2,
    disc_slot2_id = "quietus",
    disc_slot2_nivel = 4,
    arma1_nome = "[TESTE_E2E] Khopesh",
    arma1_attr = "attr_destreza",
    arma1_hab = "hab_armas_brancas",
    arma1_dif = 6,
    arma1_dano = 3,
    arma1_tipo = "lethal",
}
Bridge.activateDisciplinePower(buffCombatSheet, "protean", "prot_2", captureFirecast, mockDialogs)
Bridge.newTurn(buffCombatSheet, captureFirecast, mockDialogs)
Bridge.activateDisciplinePower(buffCombatSheet, "quietus", "quie_4", captureFirecast, mockDialogs)
nextFaces = { 8, 8, 2, 2, 2, 2, 2 }
Bridge.executeCombatManeuver(buffCombatSheet, { maneuverId = "claw" }, captureFirecast, mockDialogs)
assert(buffCombatSheet.cmb_dano_pendente_tipo == "aggravated", "Garras com prot_claws ativo devem gerar dano agravado")
nextFaces = { 8, 8, 2, 2, 2, 2, 2, 2 }
Bridge.executeCombatManeuver(buffCombatSheet, { maneuverId = "weapon_strike", weaponSlot = 1 }, captureFirecast, mockDialogs)
assert(buffCombatSheet.cmb_dano_pendente_tipo == "aggravated", "Golpe de lâmina com quie_baal ativo deve gerar dano agravado")

-- 2.28 Estaca no Coração (stake_heart): dif mínima 9 e alerta de paralisia/torpor com >= 3 níveis de dano
local stakeSheet = {
    nome = "[TESTE_E2E] Caçador Estacador",
    is_vampire = false,
    mortal_sobrenatural_modo = "humano",
    attr_forca = 3,
    attr_destreza = 4,
    hab_armas_brancas = 4,
    arma1_nome = "[TESTE_E2E] Estaca de Freixo",
    arma1_dano = 1,
    arma1_dif = 6,
    arma1_tipo = "lethal",
    cmb_manobra_id = "stake_heart",
    cmb_posicao = "retaguarda",
    cmb_defesa_alvo_sucessos = 0,
}
sentMessages = {}
nextFaces = { 9, 9, 4, 3, 2, 2, 2, 2 } -- Dif 9 -> 2 sucessos líquidos -> baseDamage(3+1=4) + carryOver(1) = 5d10
local stakeAtk = Bridge.executeCombatManeuver(stakeSheet, {}, captureFirecast, mockDialogs)
assert(stakeAtk.ok == true and sentMessages[#sentMessages]:find("Dif 9") ~= nil, "stake_heart deve manter dificuldade mínima 9 mesmo pela retaguarda")
assert(stakeSheet.cmb_dano_pendente_ativo == true and stakeSheet.cmb_dano_pendente_estaca == true and stakeSheet.cmb_dano_pendente_parada == 5)

sentMessages = {}
nextFaces = { 8, 7, 6, 3, 2 } -- 3 sucessos na Dif 6 -> dispara alerta de Estaca no Coração!
local stakeDmg = Bridge.rollPendingCombatDamage(stakeSheet, captureFirecast, mockDialogs)
assert(stakeDmg.ok == true and stakeSheet.cmb_dano_pendente_ativo == false)
assert(sentMessages[#sentMessages]:find("ESTACA NO CORAÇÃO") ~= nil, "3+ níveis com estaca devem emitir alerta de paralisia/torpor: " .. tostring(sentMessages[#sentMessages]))

-- 2.29 Gancho de Iniciativa para Task 4 (V20CoterieDockBridge.recordSheetInitiative online e offline)
local recordedInits = {}
_G.V20CoterieDockBridge = {
    recordSheetInitiative = function(sh, d10Face, initMod, totalInit, fcArg)
        table.insert(recordedInits, { nome = sh.nome, d10 = d10Face, mod = initMod, total = totalInit, hasFc = (fcArg ~= nil) })
    end,
}
nextFaces = { 8 }
Bridge.rollInitiative(stakeSheet, captureFirecast, mockDialogs)
nextFaces = { 6 }
Bridge.rollInitiative(stakeSheet, offlineFirecast, mockDialogs)
_G.V20CoterieDockBridge = nil
assert(#recordedInits == 2, "recordSheetInitiative deve ser chamado tanto online quanto no fallback local")
assert(recordedInits[1].d10 == 8 and recordedInits[1].total == 8 + recordedInits[1].mod and recordedInits[1].hasFc == true)
assert(recordedInits[2].d10 == 6 and recordedInits[2].total == 6 + recordedInits[2].mod and recordedInits[2].hasFc == true)

-- 2.30 Unificação Aba 3 <-> Aba 8 (Taumaturgia e Necromancia delegando resumo e ativação p/ Linha Primária)
local thauCohesion = {
    nome = "[TESTE_E2E] Magus Tremere Coesão",
    cla_id = "tremere",
    is_vampire = true,
    geracao_base = 11,
    sangue_atual = 10,
    fdv_perm = 7,
    fdv_temp = 7,
    disc_slot3_id = "thaumaturgy",
    disc_slot3_nivel = 3,
    disc_slot3_pwr_lvl = 2,
    bm_thau_prim_id = "lure_of_flames",
    disc_slot4_id = "necromancy",
    disc_slot4_nivel = 2,
    disc_slot4_pwr_lvl = 1,
    bm_necro_prim_id = "bone_path",
}
Bridge.syncDerivedFields(thauCohesion)
assert((thauCohesion.disc_slot3_resumo or ""):find("Sedutor das Chamas") ~= nil,
    "disc_slot3_resumo na Aba 3 deve refletir a Linha Primária 'Sedutor das Chamas' da Aba 8: " .. tostring(thauCohesion.disc_slot3_resumo))
assert((thauCohesion.disc_slot3_resumo or ""):find("Punhado de Chamas") ~= nil,
    "disc_slot3_resumo deve exibir o poder Nv 2 de Sedutor das Chamas: " .. tostring(thauCohesion.disc_slot3_resumo))
assert((thauCohesion.disc_slot4_resumo or ""):find("Linha dos Ossos") ~= nil,
    "disc_slot4_resumo na Aba 3 deve refletir a Linha Primária 'Linha dos Ossos' de Necromancia: " .. tostring(thauCohesion.disc_slot4_resumo))

-- Ativar Slot 3 na Aba 3 delega para activatePrimaryBloodMagic (Sedutor das Chamas) e emite alerta de falha crítica taumatúrgica em botch!
sentMessages = {}
nextFaces = { 1, 2, 3, 2, 2, 2, 2 } -- Botch!
local slotBotchRes = Bridge.activateDisciplineSlot(thauCohesion, 3, captureFirecast, mockDialogs)
assert(slotBotchRes.ok == true and thauCohesion.sangue_atual == 9)
assert(sentMessages[#sentMessages]:find("Sedutor das Chamas") ~= nil,
    "activateDisciplineSlot(3) deve rolar Sedutor das Chamas: " .. tostring(sentMessages[#sentMessages]))
assert(sentMessages[#sentMessages]:find("Falha Crítica Taumatúrgica") ~= nil,
    "activateDisciplineSlot(3) em Taumaturgia deve preservar o alerta de Falha Crítica Taumatúrgica (-1 FdV Perm): " .. tostring(sentMessages[#sentMessages]))
''' )
        run_lua_file(lua_probe)
    finally:
        if os.path.exists(lua_probe):
            os.remove(lua_probe)

    # 2b. Verificar controles do Estúdio de Manobras V20 (Aba 5) e <dataLink>s nas 15 fichas (14 vampíricas + 1 mortal)
    all_15_roots = [(f"Sheets/{CLAN_F}.lfm", vampire_roots[cid]) for cid, _, _, CLAN_F, _ in expected_vampire_sheets] + [
        ("Sheets/frmMortal.lfm", mortal_root)
    ]
    req_combat_studio_ctrls = (
        "crdEstudioManobras",
        "cmbCmbManobraId",
        "cmbCmbArmaSlot",
        "cmbCmbAcoesNormais",
        "cmbCmbAcaoOrdem",
        "edtCmbMenorParada",
        "chkCmbAcaoRapidez",
        "edtCmbMiraTurnos",
        "chkCmbTemLuneta",
        "cmbCmbAlvoLocalizado",
        "cmbCmbCobertura",
        "cmbCmbPosicao",
        "edtCmbDefesaAlvo",
        "edtCmbForcaAlvo",
        "edtCmbDefesasTurno",
        "chkCmbEmAgarrao",
        "edtArmaduraPenalidade",
        "btnCmbExecutarManobra",
        "lblCmbDanoPendenteResumo",
        "btnCmbRolarDanoPendente",
    )
    req_combat_dl_fields = (
        "cmb_manobra_id",
        "cmb_arma_slot",
        "cmb_acoes_normais",
        "cmb_acao_ordem",
        "cmb_menor_parada",
        "cmb_acao_rapidez",
        "cmb_mira_turnos",
        "cmb_tem_luneta",
        "cmb_alvo_localizado",
        "cmb_cobertura",
        "cmb_posicao",
        "cmb_defesa_alvo_sucessos",
        "cmb_forca_alvo",
        "cmb_defesas_feitas_turno",
        "em_agarrao",
        "armadura_penalidade",
        "cmb_dano_pendente_ativo",
        "cmb_dano_pendente_parada",
        "cmb_dano_pendente_auto",
        "cmb_dano_pendente_tipo",
        "cmb_dano_pendente_estaca",
        "cmb_dano_pendente_cabeca",
        "cmb_dano_pendente_resumo",
    )
    expected_20_maneuvers = (
        "strike", "kick", "bite", "claw", "clinch", "hold", "tackle", "sweep_brawl", "disarm_brawl",
        "weapon_strike", "stake_heart", "disarm_melee", "sweep_melee",
        "single_shot", "double_tap", "three_round_burst", "full_auto",
        "dodge", "block", "parry",
    )
    for rel_15, root_15 in all_15_roots:
        names_15 = {el.attrib.get("name") for el in root_15.iter() if "name" in el.attrib}
        for c_nm in req_combat_studio_ctrls:
            assert c_nm in names_15, f"Controle do Estúdio de Manobras '{c_nm}' ausente em {rel_15}"
        man_combos = [el for el in root_15.iter("comboBox") if el.attrib.get("name") == "cmbCmbManobraId"]
        assert len(man_combos) == 1
        man_vals_str = man_combos[0].attrib.get("values", "")
        for m_id in expected_20_maneuvers:
            assert f"'{m_id}'" in man_vals_str, f"Manobra '{m_id}' ausente em cmbCmbManobraId ({rel_15})"
        dl_15_blob = "\n".join(el.attrib.get("fields", "") for el in root_15.findall("dataLink"))
        for c_fld in req_combat_dl_fields:
            assert f"'{c_fld}'" in dl_15_blob, f"Campo '{c_fld}' ausente nos <dataLink> raiz de {rel_15}"

    # 3. Instanciar e exercitar em runtime na lua54x64.dll TODAS as 15 fichas compiladas (.lfm.lua)
    sandbox_lfm_dir = os.path.join(ROOT, "output", "probe_test_e2e_15_forms")
    os.makedirs(sandbox_lfm_dir, exist_ok=True)
    probe_forms_lua = os.path.join(sandbox_lfm_dir, "run_15_forms.lua")
    all_15_specs = expected_vampire_sheets + [
        ("mortal", "Sheets/frmMortal.lfm", "br.com.v20.Mortal", "frmMortal", "Vampiro V20 - Mortal")
    ]
    try:
        compiled_paths: list[tuple[str, str, str]] = []
        for cid, rel_lfm, _, form_name, _ in all_15_specs:
            lua_src = compiler.compile_lfm_to_lua(os.path.join(ROOT, rel_lfm))
            out_file = os.path.join(sandbox_lfm_dir, f"{form_name}.lfm.lua")
            with open(out_file, "w", encoding="utf-8", newline="\n") as f:
                f.write(lua_src)
            compiled_paths.append((cid, form_name, out_file.replace("\\", "/")))

        lua_entries = ",\n".join(
            f'    {{ cid = "{cid}", formName = "{fn}", path = "{p}" }}'
            for cid, fn, p in compiled_paths
        )
        with open(probe_forms_lua, "w", encoding="utf-8", newline="\n") as f:
            f.write(f'''
local Bridge = require("Adapter.firecast_bridge")
local FORMS = {{
{lua_entries}
}}

local allControls = {{}}
local activeListeners = {{}}
local nextHandle = 100
local nextListenerId = 1

local ctrlProto = {{}}
local ctrlMeta = {{ __index = ctrlProto }}
local ALLOWED_SETTERS = {{
    "setAlign", "setWidth", "setHeight", "setLeft", "setTop",
    "setColor", "setStrokeColor", "setStrokeSize", "setXradius", "setYradius",
    "setMargins", "setPadding", "setText", "setFontColor", "setFontSize",
    "setHorzTextAlign", "setVertTextAlign", "setWordWrap", "setField", "setType",
    "setTransparent", "setTextPrompt", "setItems", "setValues", "setValue",
    "setTitle", "setSRC", "setStyle", "setOptimize", "setFields", "setDefaultValues",
    "setReadOnly", "setHitTest", "setCursor", "setHint", "setVisible", "setEnabled",
    "setName", "setFormType", "setDataType", "setTheme"
}}
for _, mName in ipairs(ALLOWED_SETTERS) do
    ctrlProto[mName] = function(self, val) self._props[mName] = val end
end
function ctrlProto:getTabIndex() return self._tabIdx or 0 end
function ctrlProto:setTabIndex(idx) self._tabIdx = idx end
function ctrlProto:beginUpdate() end
function ctrlProto:endUpdate() end
function ctrlProto:setParent(p) table.insert(p._children, self) end
function ctrlProto:addEventListener(evName, fn, ctx)
    local id = nextListenerId
    nextListenerId = nextListenerId + 1
    local rec = {{ id = id, ctrl = self, evName = evName, fn = fn, ctx = ctx }}
    activeListeners[id] = rec
    table.insert(self._listeners, rec)
    return id
end
function ctrlProto:setNodeObject(nodeObject)
    self._nodeObject = nodeObject
    if nodeObject ~= nil then
        for _, child in ipairs(self._children) do
            if child._tag == "dataLink" then
                local fields = child._props.setFields
                local defaults = child._props.setDefaultValues
                if type(fields) == "table" and type(defaults) == "table" then
                    for i, fName in ipairs(fields) do
                        if nodeObject[fName] == nil and defaults[i] ~= nil then
                            nodeObject[fName] = defaults[i]
                        end
                    end
                end
                for _, lRec in ipairs(child._listeners) do
                    if lRec.evName == "onChange" and activeListeners[lRec.id] ~= nil then
                        lRec.fn(child)
                    end
                end
            end
        end
    end
end
function ctrlProto:setNodeDatabase(nodeObject) self:setNodeObject(nodeObject) end
function ctrlProto:destroy()
    assert(not self._destroyed)
    for _, ch in ipairs(self._children) do assert(ch._destroyed == true) end
    self._destroyed = true
end

_G._obj_newObject = function(tag)
    nextHandle = nextHandle + 1
    local h = nextHandle
    allControls[h] = setmetatable({{ handle = h, _tag = tag, _props = {{}}, _children = {{}}, _listeners = {{}}, _destroyed = false, _tabIdx = 0 }}, ctrlMeta)
    return h
end
_G.GUI = {{ fromHandle = function(h) return assert(allControls[h]) end }}
_G.gui = _G.GUI
_G._gui_assignInitialParentForForm = function(_) end
_G.lfm_setPropAsString = function(ctrl, prop, val) ctrl._props[prop] = tostring(val) end
_G.showMessage = function(_) end
_G.Dialogs = {{ showMessage = _G.showMessage }}
_G.Firecast = {{
    registrarForm = function(_) end,
    registrarDataType = function(_) end,
    interpretarRolagem = function(expr)
        return {{ expr = expr, ops = {{ {{ tipo = "dado", resultados = {{ 8, 7, 6 }} }} }}, rolarLocalmente = function() end }}
    end,
    getMesaDe = function(_)
        return {{
            meuJogador = {{ isMestre = false, login = "test_e2e_15forms" }},
            activeChat = {{
                rolarDados = function(_, _, _, cb) cb({{ ops = {{ {{ tipo = "dado", resultados = {{ 8, 7, 6 }} }} }} }}) end,
                enviarMensagem = function(_, _) end,
            }},
        }}
    end,
}}
_G.RRPG = _G.Firecast
_G.rrpg = _G.Firecast
_G.NDB = {{ getChildNodes = function(_) return {{}} end }}

package.preload["firecast.lua"] = function() return _G.Firecast end
package.preload["rrpgObjs.lua"] = function()
    return {{
        beginObjectsLoading = function() end,
        endObjectsLoading = function() end,
        removeEventListenerById = function(id) activeListeners[id] = nil end,
    }}
end
package.preload["rrpgGUI.lua"] = function() return _G.GUI end
package.preload["rrpgDialogs.lua"] = function() return _G.Dialogs end
package.preload["rrpgLFM.lua"] = function() return true end
package.preload["ndb.lua"] = function() return _G.NDB end
package.preload["locale.lua"] = function() return true end
package.preload["utils.lua"] = function()
    return {{
        tryFinally = function(t, f)
            local ok, err = pcall(t)
            f()
            if not ok then error(err, 0) end
        end
    }}
end

for _, entry in ipairs(FORMS) do
    local spec = dofile(entry.path)
    assert(type(spec) == "table" and spec.name == entry.formName)
    local inst = spec.new()
    local mockNode = {{ nome = "[TESTE_E2E] Form " .. entry.formName }}
    inst:setNodeObject(mockNode)

    if entry.cid ~= "mortal" then
        assert(inst.tabMagiaSangue ~= nil, "tabMagiaSangue deve existir em " .. entry.formName)
        local expectedInitialBM = (entry.cid == "tremere" or entry.cid == "giovanni")
        assert(inst.tabMagiaSangue._props.setVisible == expectedInitialBM,
            "Visibilidade inicial incorreta de tabMagiaSangue em " .. entry.formName)

        if not expectedInitialBM then
            -- Revela Aba 8 ao selecionar Taumaturgia ou Rituais e retorna p/ aba 0 ao remover enquanto na aba 7
            mockNode.bg_rituals = 1
            inst:setNodeObject(mockNode)
            assert(inst.tabMagiaSangue._props.setVisible == true, "tabMagiaSangue deve aparecer com bg_rituals=1 em " .. entry.formName)

            inst.pgcPrincipal:setTabIndex(7)
            mockNode.bg_rituals = 0
            inst:setNodeObject(mockNode)
            assert(inst.tabMagiaSangue._props.setVisible == false, "tabMagiaSangue deve ocultar ao zerar acesso em " .. entry.formName)
            assert(inst.pgcPrincipal:getTabIndex() == 0, "pgcPrincipal deve voltar ao índice 0 ao ocultar Aba 8 ativa em " .. entry.formName)

            -- Em modo_ficha='jogo', cmbBmThauPrimId e cmbBmNecroPrimId só travam quando bm_*_prim_nivel > 0
            mockNode.modo_ficha = "jogo"
            inst:setNodeObject(mockNode)
            assert(inst.cmbBmThauPrimId._props.setEnabled == true,
                "cmbBmThauPrimId deve permanecer habilitado em modo_ficha='jogo' quando bm_thau_prim_nivel == 0 em " .. entry.formName)
            assert(inst.cmbBmNecroPrimId._props.setEnabled == true,
                "cmbBmNecroPrimId deve permanecer habilitado em modo_ficha='jogo' quando bm_necro_prim_nivel == 0 em " .. entry.formName)
            mockNode.disc_slot4_id = "thaumaturgy"
            mockNode.disc_slot4_nivel = 1
            inst:setNodeObject(mockNode)
            assert(inst.cmbBmThauPrimId._props.setEnabled == false,
                "cmbBmThauPrimId deve travar em modo_ficha='jogo' quando bm_thau_prim_nivel > 0 em " .. entry.formName)
            mockNode.disc_slot4_id = ""
            mockNode.disc_slot4_nivel = 0
            mockNode.modo_ficha = "criacao"
            inst:setNodeObject(mockNode)
        else
            -- Tremere (Taumaturgia >= 1) ou Giovanni (Necromancia >= 1): trava o primário já adquirido (>0), libera o outro (=0)
            mockNode.modo_ficha = "jogo"
            inst:setNodeObject(mockNode)
            if entry.cid == "tremere" then
                assert(inst.cmbBmThauPrimId._props.setEnabled == false and inst.cmbBmNecroPrimId._props.setEnabled == true)
            elseif entry.cid == "giovanni" then
                assert(inst.cmbBmNecroPrimId._props.setEnabled == false and inst.cmbBmThauPrimId._props.setEnabled == true)
            end
            mockNode.modo_ficha = "criacao"
            inst:setNodeObject(mockNode)
        end
    end

    -- Dispara todos os listeners do formulário provando 0 erros de runtime
    local ids = {{}}
    for id, lRec in pairs(activeListeners) do
        if lRec.ctx == inst then table.insert(ids, id) end
    end
    table.sort(ids)
    for _, id in ipairs(ids) do
        local lRec = activeListeners[id]
        if lRec ~= nil then lRec.fn(lRec.ctrl) end
    end

    inst:destroy()
    assert(inst._destroyed == true)
end
''')
        run_lua_file(probe_forms_lua)

        # 4. E2E de CoterieDockBridge + frmV20CoterieDock (Jogador vs Narrador, 0 vazamentos de dados ou observers)
        build_mod_spec = importlib.util.spec_from_file_location(
            "build_v20_suite", os.path.join(ROOT, "tools", "build_v20_suite.py")
        )
        assert build_mod_spec is not None and build_mod_spec.loader is not None
        build_mod = importlib.util.module_from_spec(build_mod_spec)
        build_mod_spec.loader.exec_module(build_mod)
        dock_compiled_lua = build_mod.compile_v20_lfm(
            compiler, os.path.join(ROOT, "Sheets", "frmV20CoterieDock.lfm")
        )
        dock_compiled_file = os.path.join(sandbox_lfm_dir, "frmV20CoterieDock.lfm.lua")
        with open(dock_compiled_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(dock_compiled_lua)
        dock_compiled_lua_path = dock_compiled_file.replace("\\", "/")

        probe_dock_lua = os.path.join(sandbox_lfm_dir, "run_dock_e2e.lua")
        with open(probe_dock_lua, "w", encoding="utf-8", newline="\n") as f:
            f.write(f'''
local Bridge = require("Adapter.firecast_bridge")
local DockBridge = require("Adapter.coterie_dock_bridge")
assert(_G.V20CoterieDockBridge == DockBridge, "V20CoterieDockBridge deve ser exposto em _G")
assert(DockBridge.ROOM_NDB_NAME == "v20_coterie_dock_v1", "ROOM_NDB_NAME inesperado")

local allControls = {{}}
local activeListeners = {{}}
local specialForms = {{}}
local createdObservers = {{}}
local chatMessages = {{}}
local dialogMessages = {{}}
local nextHandle = 1000
local nextListenerId = 1
local nextDiceFaces = {{ 5 }}
local currentIsMestre = false

local ctrlProto = {{}}
local ctrlMeta = {{ __index = ctrlProto }}
local ALLOWED_SETTERS = {{
    "setAlign", "setWidth", "setHeight", "setLeft", "setTop",
    "setColor", "setStrokeColor", "setStrokeSize", "setXradius", "setYradius",
    "setMargins", "setPadding", "setText", "setFontColor", "setFontSize",
    "setHorzTextAlign", "setVertTextAlign", "setWordWrap", "setField", "setType",
    "setTransparent", "setTextPrompt", "setItems", "setValues", "setValue",
    "setTitle", "setSRC", "setStyle", "setOptimize", "setFields", "setDefaultValues",
    "setReadOnly", "setHitTest", "setCursor", "setHint", "setVisible", "setEnabled",
    "setName", "setFormType", "setDataType", "setTheme"
}}
for _, mName in ipairs(ALLOWED_SETTERS) do
    ctrlProto[mName] = function(self, val) self._props[mName] = val end
end
function ctrlProto:getTabIndex() return self._tabIdx or 0 end
function ctrlProto:setTabIndex(idx) self._tabIdx = idx end
function ctrlProto:beginUpdate() end
function ctrlProto:endUpdate() end
function ctrlProto:setParent(p) table.insert(p._children, self) end
function ctrlProto:addEventListener(evName, fn, ctx)
    local id = nextListenerId
    nextListenerId = nextListenerId + 1
    local rec = {{ id = id, ctrl = self, evName = evName, fn = fn, ctx = ctx }}
    activeListeners[id] = rec
    table.insert(self._listeners, rec)
    return id
end
function ctrlProto:setNodeObject(nodeObject)
    self._nodeObject = nodeObject
    if nodeObject ~= nil then
        for _, child in ipairs(self._children) do
            if child._tag == "dataLink" then
                local fields = child._props.setFields
                local defaults = child._props.setDefaultValues
                if type(fields) == "table" and type(defaults) == "table" then
                    for i, fName in ipairs(fields) do
                        if nodeObject[fName] == nil and defaults[i] ~= nil then
                            nodeObject[fName] = defaults[i]
                        end
                    end
                end
                for _, lRec in ipairs(child._listeners) do
                    if lRec.evName == "onChange" and activeListeners[lRec.id] ~= nil then
                        lRec.fn(child)
                    end
                end
            end
        end
    end
end
function ctrlProto:setNodeDatabase(nodeObject) self:setNodeObject(nodeObject) end
function ctrlProto:destroy()
    assert(not self._destroyed)
    for _, ch in ipairs(self._children) do assert(ch._destroyed == true) end
    self._destroyed = true
end

_G._obj_newObject = function(tag)
    nextHandle = nextHandle + 1
    local h = nextHandle
    allControls[h] = setmetatable({{ handle = h, _tag = tag, _props = {{}}, _children = {{}}, _listeners = {{}}, _destroyed = false, _tabIdx = 0 }}, ctrlMeta)
    return h
end
_G.GUI = {{ fromHandle = function(h) return assert(allControls[h]) end }}
_G.gui = _G.GUI
_G._gui_assignInitialParentForForm = function(_) end
_G.lfm_setPropAsString = function(ctrl, prop, val) ctrl._props[prop] = tostring(val) end
_G.showMessage = function(msg) table.insert(dialogMessages, tostring(msg)) end
_G.Dialogs = {{ showMessage = _G.showMessage }}

-- NodeFacade simulado estrito (proíbe gravar table/function e notifica observers ativos)
local function makeStrictNodeFacade(initialTbl)
    local store = {{}}
    for k, v in pairs(initialTbl or {{}}) do store[k] = v end
    local proxy = {{ __nodeFacadeFlag = true }}
    setmetatable(proxy, {{
        __index = function(_, k) return store[k] end,
        __newindex = function(_, k, v)
            assert(type(v) ~= "table" and type(v) ~= "function",
                "Proibido gravar table/function em NodeFacade: " .. tostring(k))
            local prev = store[k]
            store[k] = v
            if prev ~= v then
                for _, obs in ipairs(createdObservers) do
                    if obs.enabled and obs.node == proxy and type(obs.onChanged) == "function" then
                        obs.onChanged(proxy, k, prev)
                    end
                end
            end
        end,
    }})
    return proxy, store
end

local roomNode, roomStore = makeStrictNodeFacade({{}})

local tremereSheet, _ = makeStrictNodeFacade({{
    nome = "[TESTE_E2E] Tremere",
    cla_id = "tremere",
    is_vampire = true,
    geracao_base = 12,
    attr_destreza = 2,
    attr_raciocinio = 3,
    sangue_atual = 9,
    virtude2_val = 4,
    fdv_perm = 6,
    fdv_temp = 5,
    dano_contundente = 1,
    moralidade_val = 7,
    xp_total = 20,
    xp_gasto = 0,
    xp_exige_aprovacao = true,
}})
Bridge.syncDerivedFields(tremereSheet)

local brujahSheet, _ = makeStrictNodeFacade({{
    nome = "[TESTE_E2E] Brujah",
    cla_id = "brujah",
    is_vampire = true,
    geracao_base = 11,
    attr_destreza = 4,
    attr_raciocinio = 3,
    sangue_atual = 8,
    virtude2_val = 3,
    fdv_perm = 5,
    fdv_temp = 5,
    dano_letal = 4,
    buff_forca = 2,
    em_agarrao = true,
    cmb_defesas_feitas_turno = 2,
    cmb_dano_pendente_ativo = true,
    moralidade_val = 6,
}})
Bridge.syncDerivedFields(brujahSheet)

local nosferatuHiddenSheet, _ = makeStrictNodeFacade({{
    nome = "[TESTE_E2E] Ancião Nosferatu Oculto",
    cla_id = "nosferatu",
    is_vampire = true,
    geracao_base = 7,
    attr_destreza = 5,
    attr_raciocinio = 5,
    sangue_atual = 15,
    virtude2_val = 4,
    fdv_perm = 8,
    fdv_temp = 8,
    moralidade_val = 5,
}})
Bridge.syncDerivedFields(nosferatuHiddenSheet)

local bibItemsBySheet = {{}}
local itemTremere = {{
    codigoInterno = 101,
    tipo = "personagem",
    nome = "[TESTE_E2E] Tremere",
    dataType = "br.com.v20.Tremere",
    visivel = true,
    visivelRecursivamente = true,
    loadSheetNDB = function(_, cb) cb(tremereSheet) end,
}}
local itemBrujah = {{
    codigoInterno = 102,
    tipo = "personagem",
    nome = "[TESTE_E2E] Brujah",
    dataType = "br.com.v20.Brujah",
    visivel = true,
    visivelRecursivamente = true,
    loadSheetNDB = function(_, cb) cb(brujahSheet) end,
}}
local itemNosferatu = {{
    codigoInterno = 103,
    tipo = "personagem",
    nome = "[TESTE_E2E] Ancião Nosferatu Oculto",
    dataType = "br.com.v20.Nosferatu",
    visivel = false,
    visivelRecursivamente = false,
    loadSheetNDB = function(_, cb) cb(nosferatuHiddenSheet) end,
}}
bibItemsBySheet[tremereSheet] = itemTremere
bibItemsBySheet[brujahSheet] = itemBrujah
bibItemsBySheet[nosferatuHiddenSheet] = itemNosferatu

local pastaSecreta = {{
    tipo = "diretorio",
    nome = "[TESTE_E2E] Pasta NPCs Secretos",
    visivel = false,
    visivelRecursivamente = false,
    filhos = {{ itemNosferatu }},
}}

local simulatedMesa = {{
    nome = "[TESTE_E2E] Sala Crônica Noturna",
    meuJogador = setmetatable({{}}, {{
        __index = function(_, k)
            if k == "isMestre" then return currentIsMestre end
            if k == "login" then return currentIsMestre and "test_e2e_narrador" or "test_e2e_jogador" end
            return nil
        end
    }}),
    biblioteca = {{
        filhos = {{
            itemTremere,
            itemBrujah,
            pastaSecreta,
        }},
    }},
    abrirNDBDeMesa = function(_, ndbName, cb, opcoes)
        assert(ndbName == "v20_coterie_dock_v1", "Nome inesperado do room NDB: " .. tostring(ndbName))
        assert(type(opcoes) == "table" and opcoes.criar == true, "abrirNDBDeMesa deve passar {{ criar = true }}")
        cb(roomNode)
    end,
    activeChat = {{
        rolarDados = function(_, _, _, cb)
            cb({{ ops = {{ {{ tipo = "dado", resultados = nextDiceFaces }} }} }})
        end,
        enviarMensagem = function(_, msg)
            table.insert(chatMessages, tostring(msg))
        end,
    }},
}}

_G.Firecast = {{
    registrarForm = function(_) end,
    registrarDataType = function(_) end,
    registrarSpecialForm = function(spec) specialForms[spec.name] = spec end,
    interpretarRolagem = function(expr)
        return {{
            expr = expr,
            ops = {{ {{ tipo = "dado", resultados = nextDiceFaces }} }},
            rolarLocalmente = function(self)
                self.ops = {{ {{ tipo = "dado", resultados = nextDiceFaces }} }}
            end,
        }}
    end,
    getMesaDe = function(obj)
        if type(obj) == "table" and rawget(obj, "_isMemNdb") == true then
            return nil
        end
        return simulatedMesa
    end,
    getPersonagemDe = function(s) return bibItemsBySheet[s] end,
    getBibliotecaItemDe = function(s) return bibItemsBySheet[s] end,
}}
_G.RRPG = _G.Firecast
_G.rrpg = _G.Firecast

local memNdbAllocCount = 0
_G.NDB = {{
    getChildNodes = function(_) return {{}} end,
    newMemNodeDatabase = function(initial)
        memNdbAllocCount = memNdbAllocCount + 1
        local memNode, _ = makeStrictNodeFacade(initial or {{}})
        rawset(memNode, "_isMemNdb", true)
        return memNode
    end,
    getNodeHandle = function(nodeObj)
        if type(nodeObj) == "table" and rawget(nodeObj, "__nodeFacadeFlag") == true then
            return 9001
        end
        return nil
    end,
    newObserver = function(nodeObj)
        local obs = {{ node = nodeObj, enabled = true, onChanged = nil }}
        table.insert(createdObservers, obs)
        return obs
    end,
}}

package.preload["firecast.lua"] = function() return _G.Firecast end
package.preload["rrpgObjs.lua"] = function()
    return {{
        beginObjectsLoading = function() end,
        endObjectsLoading = function() end,
        removeEventListenerById = function(id) activeListeners[id] = nil end,
    }}
end
package.preload["rrpgGUI.lua"] = function() return _G.GUI end
package.preload["rrpgDialogs.lua"] = function() return _G.Dialogs end
package.preload["rrpgLFM.lua"] = function() return true end
package.preload["ndb.lua"] = function() return _G.NDB end
package.preload["locale.lua"] = function() return true end
package.preload["utils.lua"] = function()
    return {{ tryFinally = function(t, f) local ok, e = pcall(t); f(); if not ok then error(e, 0) end end }}
end
package.preload["v20_loader.lua"] = function() return true end

-- Submete 1 pedido de XP pendente no Tremere enquanto jogador
currentIsMestre = false
local xpSub = Bridge.submitOrApproveXP(
    tremereSheet,
    "submit",
    {{ traitKind = "willpower", field = "fdv_perm", label = "FdV Permanente" }},
    _G.NDB,
    _G.Firecast,
    _G.Dialogs
)
assert(xpSub.ok == true and tremereSheet.xp_pendente_status == "pendente")

-- Rolar Iniciativa nos 2 PJs visíveis e no NPC oculto via V20Bridge.rollInitiative
-- Tremere: Des 2 + Rac 3 - Ferim 0 = 5; d10=3 -> Total 8
nextDiceFaces = {{ 3 }}
Bridge.rollInitiative(tremereSheet, _G.Firecast, _G.Dialogs)
-- Brujah: Des 4 + Rac 3 - Ferim 2 (Ferido Gravemente c/ 4 letais) = 5; d10=9 -> Total 14
nextDiceFaces = {{ 9 }}
Bridge.rollInitiative(brujahSheet, _G.Firecast, _G.Dialogs)
-- Nosferatu Oculto: Des 5 + Rac 5 = 10; d10=10 -> Total 20 (Oculto!)
nextDiceFaces = {{ 10 }}
Bridge.rollInitiative(nosferatuHiddenSheet, _G.Firecast, _G.Dialogs)

local dockSpec = dofile("{dock_compiled_lua_path}")
assert(specialForms["frmV20CoterieDock"] == dockSpec, "frmV20CoterieDock deve registrar registrarSpecialForm")

local function assertRoomNodeHasZeroPrivateData()
    local forbiddenSubstrings = {{
        "sangue", "fdv", "moralidade", "cla_id", "geracao", "xp_", "Humanidade"
    }}
    for k, v in pairs(roomStore) do
        local ks = tostring(k)
        for _, bad in ipairs(forbiddenSubstrings) do
            assert(ks:find(bad, 1, true) == nil, "Chave privada vazada em roomNode: " .. ks)
        end
        if ks:match("^init_row%d+_txt$") or ks:match("^pub_slot%d+_txt$") then
            local vs = tostring(v)
            assert(vs:find("Nosferatu", 1, true) == nil and vs:find("Oculto", 1, true) == nil,
                "NPC oculto vazado em slot público do roomNode (" .. ks .. "): " .. vs)
        end
    end
end

-- 4.1 Visão do Jogador (isMestre = false)
currentIsMestre = false
local playerDock = dockSpec.new()
playerDock.pgcDock:setTabIndex(1)
DockBridge.connectDock(playerDock, _G.Firecast, _G.NDB)

assert(playerDock.pgcDock:getTabIndex() == 0, "Jogador deve ser redirecionado para a Aba 0")
assert(playerDock.tabNarradorCoterie._props.setVisible == false, "tabNarradorCoterie deve ficar oculta para Jogador")
assert(playerDock.layNpcQuickControls._props.setVisible == false, "Controles rápidos de NPC devem ficar ocultos para Jogador")

-- Fase inicial = declaracao (ascendente: Tremere 8 antes de Brujah 14; Nosferatu 20 oculto NÃO aparece!)
local pRow1 = tostring(playerDock.lblInitRow1._props.setText or "")
local pRow2 = tostring(playerDock.lblInitRow2._props.setText or "")
local pRow3 = tostring(playerDock.lblInitRow3._props.setText or "")
assert(pRow1:find("Tremere", 1, true) ~= nil and pRow1:find("8", 1, true) ~= nil, "Linha 1 Jogador inesperada: " .. pRow1)
assert(pRow2:find("Brujah", 1, true) ~= nil and pRow2:find("14", 1, true) ~= nil, "Linha 2 Jogador inesperada: " .. pRow2)
assert(pRow3:find("Nosferatu", 1, true) == nil and pRow3:find("20", 1, true) == nil, "Linha 3 Jogador não deve exibir NPC oculto: " .. pRow3)
for i = 1, 10 do
    local txt = tostring(playerDock["lblInitRow" .. i]._props.setText or "")
    assert(txt:find("Nosferatu", 1, true) == nil and txt:find("Oculto", 1, true) == nil, "NPC oculto vazou na Iniciativa do Jogador: " .. txt)
end
for i = 1, 8 do
    local ptxt = tostring(playerDock["lblPubSlot" .. i]._props.setText or "")
    assert(ptxt:find("Nosferatu", 1, true) == nil and ptxt:find("Oculto", 1, true) == nil, "NPC oculto vazou no Resumo Público: " .. ptxt)
end
local pub1 = tostring(playerDock.lblPubSlot1._props.setText or "")
local pub2 = tostring(playerDock.lblPubSlot2._props.setText or "")
assert(pub1:find("Tremere", 1, true) ~= nil and pub1:find("Escoriado", 1, true) ~= nil, "PubSlot1 inesperado: " .. pub1)
assert(pub2:find("Brujah", 1, true) ~= nil and pub2:find("Ferido", 1, true) ~= nil, "PubSlot2 inesperado: " .. pub2)
assertRoomNodeHasZeroPrivateData()

-- Tentativas de mutação por Jogador comum DEVEM ser bloqueadas no backend
dialogMessages = {{}}
assert(DockBridge.toggleCombatPhase(playerDock, _G.Firecast, _G.Dialogs).ok == false)
assert(DockBridge.addQuickNpcInitiative(playerDock, _G.Firecast, _G.Dialogs).ok == false)
assert(DockBridge.clearInitiative(playerDock, _G.Firecast, _G.Dialogs).ok == false)
assert(DockBridge.adjustCardBlood(playerDock, 1, -1, _G.Firecast, _G.Dialogs).ok == false)
assert(DockBridge.approveCardXP(playerDock, 1, _G.Firecast, _G.NDB, _G.Dialogs).ok == false)
assert(DockBridge.batchAwakenNightly(playerDock, _G.Firecast, _G.Dialogs).ok == false)
assert(DockBridge.batchNewTurn(playerDock, _G.Firecast, _G.Dialogs).ok == false)
assert(DockBridge.batchEndScene(playerDock, _G.Firecast, _G.Dialogs).ok == false)
assert(#dialogMessages >= 8, "Todas as tentativas ilegais do Jogador devem avisar bloqueio de permissão")
assert(tremereSheet.sangue_atual == 9 and tremereSheet.fdv_perm == 6, "Nenhuma ficha pode ter sido mutada pelo Jogador")

playerDock:destroy()
for _, obs in ipairs(createdObservers) do
    assert(obs.enabled == false, "destroy() do playerDock deve desativar observer via _onBeforeDestroy")
end

-- 4.2 Visão do Narrador (isMestre = true)
createdObservers = {{}}
currentIsMestre = true
local stDock = dockSpec.new()
DockBridge.connectDock(stDock, _G.Firecast, _G.NDB)

assert(stDock.tabNarradorCoterie._props.setVisible == true, "tabNarradorCoterie deve ficar visível para o Narrador")
assert(#createdObservers == 4, "Narrador deve conectar 1 observer no roomNode + 3 nos charNodes (sem duplicar), obteve: " .. #createdObservers)
for _, obs in ipairs(createdObservers) do assert(obs.enabled == true) end

-- Verificar Iniciativa do Narrador em Declaração (ascendente: 8, 14, [Oculto] 20)
assert(tostring(stDock.lblInitRow1._props.setText):find("Tremere", 1, true) ~= nil)
assert(tostring(stDock.lblInitRow2._props.setText):find("Brujah", 1, true) ~= nil)
assert(tostring(stDock.lblInitRow3._props.setText):find("[Oculto] [TESTE_E2E] Ancião Nosferatu Oculto", 1, true) ~= nil,
    "Narrador deve enxergar [Oculto] na Iniciativa: " .. tostring(stDock.lblInitRow3._props.setText))

-- Verificar Cartões do Narrador (3 ativos, 5 ocultos)
assert(stDock.rectStCard1._props.setVisible == true)
assert(stDock.rectStCard2._props.setVisible == true)
assert(stDock.rectStCard3._props.setVisible == true)
assert(stDock.rectStCard4._props.setVisible == false)
assert(tostring(stDock.lblStCardTitle1._props.setText):find("Tremere", 1, true) ~= nil)
assert(tostring(stDock.lblStCardFlags1._props.setText):find("[XP Pendente]", 1, true) ~= nil)
assert(stDock.btnStApproveXp1._props.setVisible == true)
assert(tostring(stDock.lblStCardFlags2._props.setText):find("[Agarrão]", 1, true) ~= nil)
assert(tostring(stDock.lblStCardFlags3._props.setText):find("[Oculto]", 1, true) ~= nil)
assertRoomNodeHasZeroPrivateData()

-- Alternar Fase: Declaração (ascendente) -> Ação (descendente: 20, 14, 8)
local phaseRes = DockBridge.toggleCombatPhase(stDock, _G.Firecast, _G.Dialogs)
assert(phaseRes.ok == true and roomNode.combate_fase == "acao")
assert(tostring(stDock.lblInitRow1._props.setText):find("Nosferatu", 1, true) ~= nil,
    "Na Fase de Ação, maior Iniciativa (20) age primeiro: " .. tostring(stDock.lblInitRow1._props.setText))
assert(tostring(stDock.lblInitRow3._props.setText):find("Tremere", 1, true) ~= nil)
-- E no roomNode público, init_row1_txt deve ser Brujah (14) e jamais o Nosferatu oculto!
assert(tostring(roomNode.init_row1_txt or ""):find("Brujah", 1, true) ~= nil)
assertRoomNodeHasZeroPrivateData()

-- Adicionar NPC rápido oculto pelo Dock
stDock.sheet.npc_init_nome = "[TESTE_E2E] Carniçal Vigia"
stDock.sheet.npc_init_mod = 4
stDock.sheet.npc_init_oculto = true
nextDiceFaces = {{ 7 }}
local quickRes = DockBridge.addQuickNpcInitiative(stDock, _G.Firecast, _G.Dialogs)
assert(quickRes.ok == true)
assertRoomNodeHasZeroPrivateData()

-- Ajustar Sangue pelo Cartão 1 (Tremere: 9 -> 8)
local bloodRes = DockBridge.adjustCardBlood(stDock, 1, -1, _G.Firecast, _G.Dialogs)
assert(bloodRes.ok == true and tremereSheet.sangue_atual == 8)
assert(tostring(stDock.lblStCardStats1._props.setText):find("8/11", 1, true) ~= nil,
    "Stats do cartão 1 devem refletir Sangue 8/11: " .. tostring(stDock.lblStCardStats1._props.setText))

-- Aprovar XP pendente pelo Cartão 1 (Tremere fdv_perm: 6 -> 7)
chatMessages = {{}}
local appRes = DockBridge.approveCardXP(stDock, 1, _G.Firecast, _G.NDB, _G.Dialogs)
assert(appRes.ok == true and tremereSheet.fdv_perm == 7 and tremereSheet.xp_pendente_status == "aprovado")
assert(stDock.btnStApproveXp1._props.setVisible == false, "Botão Aprovar XP deve ocultar após aprovação")
assert(#chatMessages == 1, "approveCardXP deve postar 1 mensagem consolidada no chat, obteve: " .. #chatMessages)

-- batchAwakenNightly: gasta 1 Vitae em cada vampiro e posta EXATAMENTE 1 boletim consolidado no chat
chatMessages = {{}}
local awkRes = DockBridge.batchAwakenNightly(stDock, _G.Firecast, _G.Dialogs)
assert(awkRes.ok == true)
assert(tremereSheet.sangue_atual == 7 and brujahSheet.sangue_atual == 7 and nosferatuHiddenSheet.sangue_atual == 14)
assert(#chatMessages == 1, "batchAwakenNightly deve enviar apenas 1 boletim único no chat, enviou: " .. #chatMessages)
assert(chatMessages[1]:find("Nosferatu", 1, true) == nil, "Boletim público no chat não deve revelar nome de NPC oculto: " .. chatMessages[1])

-- batchNewTurn: reseta turno nas fichas, incrementa rodada_atual (1 -> 2), volta fase p/ declaracao e posta 1 msg
brujahSheet.sangue_gasto_turno = 2
chatMessages = {{}}
local turnRes = DockBridge.batchNewTurn(stDock, _G.Firecast, _G.Dialogs)
assert(turnRes.ok == true and tonumber(roomNode.rodada_atual) == 2 and roomNode.combate_fase == "declaracao")
assert(brujahSheet.sangue_gasto_turno == 0 and brujahSheet.cmb_defesas_feitas_turno == 0)
assert(#chatMessages == 1, "batchNewTurn deve enviar 1 anúncio único no chat, enviou: " .. #chatMessages)

-- batchEndScene: limpa buffs de cena, agarrão e dano pendente, reseta rodada p/ 1 e posta 1 msg
chatMessages = {{}}
local endRes = DockBridge.batchEndScene(stDock, _G.Firecast, _G.Dialogs)
assert(endRes.ok == true and tonumber(roomNode.rodada_atual) == 1)
assert(brujahSheet.buff_forca == 0 and brujahSheet.em_agarrao == false and brujahSheet.cmb_dano_pendente_ativo == false)
assert(#chatMessages == 1, "batchEndScene deve enviar 1 anúncio único no chat, enviou: " .. #chatMessages)

-- Torpor por inanição em batchAwakenNightly quando sangue_atual == 0
tremereSheet.sangue_atual = 0
chatMessages = {{}}
local torpAwk = DockBridge.batchAwakenNightly(stDock, _G.Firecast, _G.Dialogs)
assert(torpAwk.ok == true and tremereSheet.em_torpor == true)
assert(#chatMessages == 1 and chatMessages[1]:find("Torpor", 1, true) ~= nil,
    "Boletim único deve alertar entrada em Torpor: " .. tostring(chatMessages[1]))

-- Paginação (changePage) ao expandir biblioteca dinamicamente p/ 10 fichas (2 páginas: 8 + 2)
for extraIdx = 4, 10 do
    local extraNode, _ = makeStrictNodeFacade({{
        nome = "[TESTE_E2E] Membro Extra #" .. extraIdx,
        cla_id = "caitiff",
        is_vampire = true,
        geracao_base = 13,
        sangue_atual = 6,
    }})
    table.insert(simulatedMesa.biblioteca.filhos, {{
        codigoInterno = 200 + extraIdx,
        tipo = "personagem",
        nome = "[TESTE_E2E] Membro Extra #" .. extraIdx,
        dataType = "br.com.v20.Caitiff",
        visivel = true,
        visivelRecursivamente = true,
        loadSheetNDB = function(_, cb) cb(extraNode) end,
    }})
end
local pgRes = DockBridge.changePage(stDock, 1, _G.Firecast, _G.NDB)
assert(pgRes.ok == true and pgRes.page == 2 and pgRes.totalPages == 2,
    "changePage(+1) deve avançar p/ página 2/2 ao detectar 10 fichas: page=" .. tostring(pgRes.page))
assert(stDock.rectStCard1._props.setVisible == true and stDock.rectStCard2._props.setVisible == true and stDock.rectStCard3._props.setVisible == false)
local pgBack = DockBridge.changePage(stDock, -1, _G.Firecast, _G.NDB)
assert(pgBack.page == 1 and stDock.rectStCard8._props.setVisible == true)

-- Limpar Iniciativa e desconectar Dock do Narrador -> 0 observers ativos!
assert(DockBridge.clearInitiative(stDock, _G.Firecast, _G.Dialogs).ok == true)
assert(tonumber(roomNode.init_count) == 0)
assert(#createdObservers == 11, "1 observer do roomNode + 10 charNodes únicos sem duplicar, total criado: " .. #createdObservers)

DockBridge.disconnectDock(stDock)
for idx, obs in ipairs(createdObservers) do
    assert(obs.enabled == false, "Observer #" .. idx .. " continuou ativo após disconnectDock!")
end
stDock:destroy()

-- 4.3 Regressão Finding #1: _localUiNode via NDB.newMemNodeDatabase() + isolamento contra NDB de sala em setNodeObject (pré e pós OnShow)
createdObservers = {{}}
currentIsMestre = true
local hostSharedDockNdbPre, hostSharedStorePre = makeStrictNodeFacade({{}})
local hostSharedDockNdbPost, hostSharedStorePost = makeStrictNodeFacade({{}})

local memCountBefore = memNdbAllocCount
local isoDock = dockSpec.new()
-- Host do Firecast injeta o NDB compartilhado de tablesDock ANTES de OnShow
isoDock:setNodeObject(hostSharedDockNdbPre)
DockBridge.connectDock(isoDock, _G.Firecast, _G.NDB)

assert(memNdbAllocCount > memCountBefore, "connectDock/guard deve alocar _localUiNode via NDB.newMemNodeDatabase()")
assert(type(isoDock.sheet) == "table" and rawget(isoDock.sheet, "__nodeFacadeFlag") == true and rawget(isoDock.sheet, "_isMemNdb") == true,
    "isoDock.sheet deve ser um NodeFacade de memória (_isMemNdb) para que _gui_assignNodeObject vincule controles Delphi reais")
assert(_G.NDB.getNodeHandle(isoDock.sheet) ~= nil, "ndb.getNodeHandle(isoDock.sheet) não pode ser nil!")
assert(isoDock.sheet ~= hostSharedDockNdbPre, "isoDock.sheet jamais pode permanecer apontando para NDB compartilhado de sala")

-- Narrador preenche rascunho de NPC oculto e rola + Rolar NPC
chatMessages = {{}}
isoDock.sheet.npc_init_nome = "[TESTE_E2E] Sabbat Infiltrado"
isoDock.sheet.npc_init_mod = 6
isoDock.sheet.npc_init_oculto = true
nextDiceFaces = {{ 8 }}
local isoQuickRes = DockBridge.addQuickNpcInitiative(isoDock, _G.Firecast, _G.Dialogs)
assert(isoQuickRes.ok == true and isoQuickRes.hidden == true and isoQuickRes.total == 14)
assert(#chatMessages == 0, "NPC rápido oculto jamais pode vazar rolagem no activeChat!")
for k, _ in pairs(hostSharedStorePre) do
    error("Vazamento proibido no NDB compartilhado pré-OnShow: chave " .. tostring(k))
end

-- Host do Firecast injeta outro NDB compartilhado DEPOIS de OnShow (ex.: OnNodeReady / carga assíncrona)
isoDock:setNodeDatabase(hostSharedDockNdbPost)
assert(isoDock.sheet == rawget(isoDock, "_localUiNode") and isoDock.sheet ~= hostSharedDockNdbPost,
    "setNodeObject/setNodeDatabase pós-OnShow não pode substituir _localUiNode por NDB de sala!")
isoDock.sheet.npc_init_nome = "[TESTE_E2E] Arconte Secreto"
for k, _ in pairs(hostSharedStorePost) do
    error("Vazamento proibido no NDB compartilhado pós-OnShow: chave " .. tostring(k))
end
assertRoomNodeHasZeroPrivateData()

-- 4.4 Regressão Finding #3: Alternância dinâmica de visivel / visivelRecursivamente no meio da sessão antes de rollInitiative
-- Tremere estava visível no cache; Narrador oculta Tremere p/ emboscada e rola Iniciativa
DockBridge.clearInitiative(isoDock, _G.Firecast, _G.Dialogs)
tremereSheet.em_torpor = false
Bridge.syncDerivedFields(tremereSheet)
itemTremere.visivel = false
itemTremere.visivelRecursivamente = false
nextDiceFaces = {{ 4 }}
Bridge.rollInitiative(tremereSheet, _G.Firecast, _G.Dialogs)
assert(tostring(roomNode.init_row1_txt or "") == "",
    "Tremere recém-ocultado NÃO pode aparecer em init_row1_txt público, obteve: " .. tostring(roomNode.init_row1_txt))
assert(tostring(isoDock.lblInitRow1._props.setText):find("[Oculto] [TESTE_E2E] Tremere", 1, true) ~= nil,
    "Dock do Narrador deve refletir imediatamente [Oculto] após ocultar Tremere: " .. tostring(isoDock.lblInitRow1._props.setText))

-- Nosferatu estava oculto no cache; Narrador revela pasta + Nosferatu e rola Iniciativa
pastaSecreta.visivel = true
pastaSecreta.visivelRecursivamente = true
itemNosferatu.visivel = true
itemNosferatu.visivelRecursivamente = true
nextDiceFaces = {{ 9 }}
Bridge.rollInitiative(nosferatuHiddenSheet, _G.Firecast, _G.Dialogs)
assert(tostring(roomNode.init_row1_txt or ""):find("Nosferatu", 1, true) ~= nil,
    "Nosferatu recém-revelado DEVE entrar em init_row1_txt público, obteve: " .. tostring(roomNode.init_row1_txt))

DockBridge.disconnectDock(isoDock)
isoDock:destroy()
for _, obs in ipairs(createdObservers) do
    assert(obs.enabled == false, "Todos os observers do isoDock devem estar desativados")
end

-- 4.5 Regressão Finding #2: abrirNDBDeMesa assíncrono (estilo setTimeout) em batchNewTurn e batchEndScene
local deferredCallbacks = {{}}
local asyncChatLog = {{}}
local asyncRoomNode, _ = makeStrictNodeFacade({{
    cena_titulo = "[TESTE_E2E] Cena Assíncrona",
    rodada_atual = 4,
    combate_fase = "acao",
}})
local asyncMesa = {{
    nome = "[TESTE_E2E] Sala Async NDB",
    meuJogador = {{ isMestre = true, login = "test_e2e_narrador_async" }},
    biblioteca = {{ filhos = {{ itemBrujah }} }},
    abrirNDBDeMesa = function(_, ndbName, cb, opcoes)
        assert(ndbName == "v20_coterie_dock_v1" and opcoes and opcoes.criar == true)
        table.insert(deferredCallbacks, function() cb(asyncRoomNode) end)
    end,
    activeChat = {{
        enviarMensagem = function(_, msg) table.insert(asyncChatLog, tostring(msg)) end,
    }},
}}
local asyncFc = {{
    getMesaDe = function(obj)
        if type(obj) == "table" and rawget(obj, "_isMemNdb") == true then return nil end
        return asyncMesa
    end,
}}

local asyncTurnForm = {{}}
brujahSheet.sangue_gasto_turno = 1
DockBridge.batchNewTurn(asyncTurnForm, asyncFc, _G.Dialogs)
assert(#asyncChatLog == 0, "batchNewTurn assíncrono NÃO pode enviar boletim antes do callback de abrirNDBDeMesa!")
assert(#deferredCallbacks == 1, "Deve haver 1 callback pendente de abrirNDBDeMesa")
deferredCallbacks[1]()
deferredCallbacks = {{}}
assert(tonumber(asyncRoomNode.rodada_atual) == 5 and asyncRoomNode.combate_fase == "declaracao",
    "Após callback async, rodada_atual deve avançar 4 -> 5, obteve: " .. tostring(asyncRoomNode.rodada_atual))
assert(#asyncChatLog == 1 and asyncChatLog[1]:find("Rodada 5", 1, true) ~= nil,
    "Boletim de batchNewTurn deve anunciar 'Rodada 5' (e não Rodada 2!): " .. tostring(asyncChatLog[1]))

asyncChatLog = {{}}
asyncRoomNode.combate_fase = "acao"
local asyncSceneForm = {{}}
brujahSheet.buff_forca = 2
DockBridge.batchEndScene(asyncSceneForm, asyncFc, _G.Dialogs)
assert(#asyncChatLog == 0 and tonumber(asyncRoomNode.rodada_atual) == 5,
    "batchEndScene assíncrono NÃO pode anunciar nem mutar roomNode antes do callback de abrirNDBDeMesa!")
assert(#deferredCallbacks == 1)
deferredCallbacks[1]()
deferredCallbacks = {{}}
assert(tonumber(asyncRoomNode.rodada_atual) == 1 and asyncRoomNode.combate_fase == "declaracao")
assert(#asyncChatLog == 1, "Boletim de batchEndScene deve ser enviado dentro do callback de abrirNDBDeMesa")
''')
        run_lua_file(probe_dock_lua)
    finally:
        import shutil
        shutil.rmtree(sandbox_lfm_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
