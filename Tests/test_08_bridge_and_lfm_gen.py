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

    # 1. Gerar os LFMs Brujah e Mortal
    subprocess.run(
        [sys.executable, os.path.join(ROOT, "Templates", "generate_vampire_lfm.py"), "--clan", "brujah"],
        check=True,
    )
    subprocess.run(
        [sys.executable, os.path.join(ROOT, "Templates", "generate_mortal_lfm.py")],
        check=True,
    )

    brujah_root = verify_lfm_xml_and_compile(
        compiler, gui_sdk, "Sheets/frmBrujah.lfm", "br.com.v20.Brujah", "frmBrujah"
    )
    mortal_root = verify_lfm_xml_and_compile(
        compiler, gui_sdk, "Sheets/frmMortal.lfm", "br.com.v20.Mortal", "frmMortal"
    )

    # Verificar abas e campos estruturais obrigatórios em frmBrujah.lfm
    brujah_tabs = list(brujah_root.iter("tab"))
    assert len(brujah_tabs) == 7, f"frmBrujah.lfm deve possuir 7 abas, encontrou {len(brujah_tabs)}"
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
''')
        run_lua_file(lua_probe)
    finally:
        if os.path.exists(lua_probe):
            os.remove(lua_probe)


if __name__ == "__main__":
    main()
