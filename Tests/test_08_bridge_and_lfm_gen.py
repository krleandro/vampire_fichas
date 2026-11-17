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


def verify_lfm_xml_and_compile(compiler, gui_sdk: str, rel_path: str, expected_dt: str, expected_name: str) -> ET.Element:
    full = os.path.join(ROOT, rel_path)
    assert os.path.exists(full), f"Arquivo {rel_path} não gerado"
    root = ET.parse(full).getroot()
    assert root.tag == "form", f"Raiz de {rel_path} deve ser <form>"
    assert root.attrib.get("dataType") == expected_dt, f"dataType inesperado em {rel_path}"
    assert root.attrib.get("name") == expected_name, f"name inesperado em {rel_path}"
    assert root.attrib.get("formType") == "sheetTemplate", f"formType deve ser sheetTemplate em {rel_path}"
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
''' )
        run_lua_file(lua_probe)
    finally:
        if os.path.exists(lua_probe):
            os.remove(lua_probe)

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
    finally:
        import shutil
        shutil.rmtree(sandbox_lfm_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
