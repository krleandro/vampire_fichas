#!/usr/bin/env python3
"""Gerador de ficha Mortal / Carniçal / Numina V20 (Sheets/frmMortal.lfm) para RRPG Firecast SDK 3.7b."""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from Templates.generate_vampire_lfm import (  # noqa: E402
    build_tab2_traits,
    build_tab4_backgrounds,
    build_tab5_combat,
    build_tab7_xp,
)
from Templates.theme_gothic import (  # noqa: E402
    ABILITIES_BY_COL,
    ACCENT_MORTAL,
    ATTRIBUTES_BY_COL,
    BACKGROUNDS_LIST,
    BG_MAIN,
    BG_PANEL,
    BORDER_MORTAL,
    COMBAT_MANEUVER_FIELD_DEFAULTS,
    DISCIPLINES_LIST,
    NUMINA_LIST,
    TEXT_ALERT,
    TEXT_GOLD,
    TEXT_MAIN,
    TEXT_MUTED,
    assert_align,
    build_mode_permissions_lua,
    dice_roller_footer_xml,
    header_bar_xml,
    lua_str_list,
    root_datalinks_xml,
    suite_credits_tab_xml,
    validate_generated_lfm_xml,
    xml_esc,
)


def build_mortal_tab1() -> str:
    perfil_items = lua_str_list(["Mortal Padrão V20 (6/4/3 • 11/7/4 • 21 Bônus)", "Mortal Heroico (7/5/3 • 13/9/5 • 15 Bônus)"])
    perfil_vals = lua_str_list(["padrao_643", "heroico_753"])
    modo_items = lua_str_list(["Criação Validada", "Modo Jogo (XP)", "Edição Livre (Narrador)"])
    modo_vals = lua_str_list(["criacao", "jogo", "narrador_livre"])

    return f"""            <tab name="tabCriacao" title="1. Mortal &amp; Criação">
                <scrollBox align="client" padding="{{left=10, right=10, top=10, bottom=10}}">
                    <layout align="top" height="620">
                        <rectangle align="top" height="180" color="{BG_PANEL}" strokeColor="{BORDER_MORTAL}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=10, bottom=10}}" margins="{{bottom=10}}">
                            <label align="top" height="22" text="REGISTRO BIOGRÁFICO HUMANO — VAMPIRO V20" fontColor="{ACCENT_MORTAL}" fontSize="13" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            <layout align="top" height="28" margins="{{top=6}}">
                                <label align="left" width="75" text="Jogador:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit align="left" width="180" field="jogador" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=10}}"/>
                                <label align="left" width="70" text="Crônica:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit align="left" width="190" field="cronica" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=10}}"/>
                                <label align="left" width="75" text="Ocupação:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit align="client" field="ocupacao" fontColor="{TEXT_MAIN}" fontSize="11"/>
                            </layout>
                            <layout align="top" height="28" margins="{{top=6}}">
                                <label align="left" width="75" text="Natureza:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit align="left" width="180" field="natureza" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=10}}"/>
                                <label align="left" width="70" text="Comport.:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit align="left" width="190" field="comportamento" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=10}}"/>
                                <label align="left" width="75" text="Formação:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit align="client" field="formacao" fontColor="{TEXT_MAIN}" fontSize="11"/>
                            </layout>
                            <layout align="top" height="28" margins="{{top=6}}">
                                <label align="left" width="85" text="Perfil V20:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <comboBox name="cmbMortalPerfil" align="left" width="320" field="mortal_perfil" items="{perfil_items}" values="{perfil_vals}" fontColor="{TEXT_GOLD}" fontSize="11" margins="{{right=14}}"/>
                                <label align="left" width="85" text="Modo Ficha:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <comboBox name="cmbModoFicha" align="client" field="modo_ficha" items="{modo_items}" values="{modo_vals}" fontColor="{TEXT_MAIN}" fontSize="11"/>
                            </layout>
                        </rectangle>

                        <rectangle align="top" height="240" color="{BG_PANEL}" strokeColor="{BORDER_MORTAL}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=10, bottom=10}}">
                            <label align="top" height="22" text="ASSISTENTE DE CRIAÇÃO MORTAL V20 (6/4/3 PADRÃO OU 7/5/3 HEROICO)" fontColor="{ACCENT_MORTAL}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            <layout align="top" height="28" margins="{{top=6}}">
                                <label align="left" width="85" text="Bônus Atrib:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtFreebieAttributes" align="left" width="40" field="freebie_attributes" type="number" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=10}}"/>
                                <label align="left" width="80" text="Bônus Hab:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtFreebieAbilities" align="left" width="40" field="freebie_abilities" type="number" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=10}}"/>
                                <label align="left" width="85" text="Bônus Antec:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtFreebieBackgrounds" align="left" width="40" field="freebie_backgrounds" type="number" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=10}}"/>
                                <label align="left" width="80" text="Bônus Virt:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtFreebieVirtues" align="left" width="40" field="freebie_virtues" type="number" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}"/>
                            </layout>
                            <layout align="top" height="28" margins="{{top=4}}">
                                <label align="left" width="85" text="Bônus Moral:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtFreebieMorality" align="left" width="40" field="freebie_morality" type="number" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=10}}"/>
                                <label align="left" width="80" text="Bônus FdV:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtFreebieWillpower" align="left" width="40" field="freebie_willpower" type="number" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}"/>
                            </layout>
                            <layout align="top" height="32" margins="{{top=8}}">
                                <button name="btnValidarCriacao" align="left" width="160" text="Validar Criação Mortal" fontSize="11" margins="{{right=8}}">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.validateCreationOnSheet(sheet, nil, nil, nil, false) end</event>
                                </button>
                                <button name="btnConcluirCriacao" align="left" width="245" text="Concluir Criação -&gt; Modo Jogo" fontSize="11" fontStyle="bold">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.validateCreationOnSheet(sheet, nil, nil, nil, true) end</event>
                                </button>
                            </layout>
                            <label align="client" field="criacao_resumo_status" wordWrap="true" fontColor="{TEXT_GOLD}" fontSize="11" horzTextAlign="{assert_align("leading")}" margins="{{top=6}}"/>
                        </rectangle>
                    </layout>
                </scrollBox>
            </tab>"""


def build_mortal_tab3() -> str:
    disc_items = lua_str_list(["— Nenhuma —"] + [n for _, n in DISCIPLINES_LIST])
    disc_vals = lua_str_list([""] + [i for i, _ in DISCIPLINES_LIST])
    lvl_items = lua_str_list(["Poder Nv 1", "Poder Nv 2", "Poder Nv 3"])
    lvl_vals = lua_str_list(["1", "2", "3"])

    ghoul_slots = []
    for i in range(1, 5):
        ghoul_slots.append(
            f"""                            <layout align="top" height="28" margins="{{bottom=3}}">
                                <comboBox name="cmbDiscSlotId{i}" align="left" width="195" field="disc_slot{i}_id" items="{disc_items}" values="{disc_vals}" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=6}}"/>
                                <edit name="edtDiscSlotNivel{i}" align="left" width="36" field="disc_slot{i}_nivel" type="number" fontColor="{TEXT_GOLD}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=6}}"/>
                                <comboBox name="cmbDiscSlotPwrLvl{i}" align="left" width="105" field="disc_slot{i}_pwr_lvl" items="{lvl_items}" values="{lvl_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=6}}"/>
                                <label align="client" field="disc_slot{i}_resumo" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}" margins="{{right=6}}"/>
                                <button name="btnDiscSlotAtivar{i}" align="right" width="110" text="Ativar / Rolar" fontSize="10" fontStyle="bold">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.activateDisciplineSlot(sheet, {i}) end</event>
                                </button>
                            </layout>"""
        )

    numina_rows = []
    for nid, nlabel in NUMINA_LIST:
        numina_rows.append(
            f"""                            <layout align="top" height="28" margins="{{bottom=3}}">
                                <label align="left" width="280" text="{xml_esc(nlabel)}" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtNumina_{nid}" align="left" width="42" field="numina_{nid}" type="number" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{right=10}}"/>
                                <button align="left" width="135" text="Rolar Numina" fontSize="10" fontStyle="bold">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.rollNuminaAction(sheet, '{nid}') end</event>
                                </button>
                            </layout>"""
        )

    return f"""            <tab name="tabOcupacao" title="3. Ocupação, Bens &amp; Dons">
                <scrollBox align="client" padding="{{left=10, right=10, top=10, bottom=10}}">
                    <layout align="top" height="780">
                        <rectangle align="top" height="210" color="{BG_PANEL}" strokeColor="{BORDER_MORTAL}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=10, bottom=10}}" margins="{{bottom=10}}">
                            <label align="top" height="22" text="VÍNCULOS HUMANOS, EQUIPAMENTOS CIVIS &amp; CONHECIMENTO DO OCULTO" fontColor="{ACCENT_MORTAL}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            <label align="top" height="18" text="Vínculos, Família, Empregador e Rede Civil:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}" margins="{{top=4}}"/>
                            <textEditor align="top" height="65" field="vinculos_humanos" fontColor="{TEXT_MAIN}" fontSize="11"/>
                            <label align="top" height="18" text="Equipamentos, Documentos, Veículos e Exposição ao Sobrenatural:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}" margins="{{top=6}}"/>
                            <textEditor align="client" field="equipamentos_civis" fontColor="{TEXT_MAIN}" fontSize="11"/>
                        </rectangle>

                        <rectangle name="pnlCarnical" visible="false" align="top" height="240" color="{BG_PANEL}" strokeColor="{TEXT_ALERT}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=10, bottom=10}}" margins="{{bottom=10}}">
                            <label align="top" height="22" text="CONDIÇÃO CARNIÇAL (GHOUL) — VITAE DO DOMITOR &amp; POTÊNCIA 1 AUTOMÁTICA" fontColor="{TEXT_ALERT}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            <layout align="top" height="28" margins="{{top=4, bottom=6}}">
                                <label align="left" width="70" text="Domitor:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit align="left" width="180" field="senhor_regente" textPrompt="Nome / Clã do Regente" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=10}}"/>
                                <button align="left" width="90" text="+Buff Força" fontSize="10" margins="{{right=4}}">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.applyBloodBuff(sheet, 'forca') end</event>
                                </button>
                                <button align="left" width="95" text="+Buff Destreza" fontSize="10" margins="{{right=4}}">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.applyBloodBuff(sheet, 'destreza') end</event>
                                </button>
                                <button align="left" width="90" text="+Buff Vigor" fontSize="10" margins="{{right=6}}">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.applyBloodBuff(sheet, 'vigor') end</event>
                                </button>
                                <button align="right" width="110" text="Limpar Buffs" fontSize="10">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.clearSceneBuffs(sheet) end</event>
                                </button>
                            </layout>
{chr(10).join(ghoul_slots)}
                        </rectangle>

                        <rectangle name="pnlNumina" visible="false" align="top" height="150" color="{BG_PANEL}" strokeColor="{TEXT_GOLD}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=10, bottom=10}}">
                            <label align="top" height="22" text="DONS NUMINA (FÉ VERDADEIRA, MAGIA DE CERCA &amp; FENÔMENOS PSÍQUICOS)" fontColor="{TEXT_GOLD}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
{chr(10).join(numina_rows)}
                        </rectangle>
                    </layout>
                </scrollBox>
            </tab>"""


def build_mortal_tab6() -> str:
    return f"""            <tab name="tabMoralidade" title="6. Moralidade &amp; Psique">
                <scrollBox align="client" padding="{{left=10, right=10, top=10, bottom=10}}">
                    <layout align="top" height="420">
                        <rectangle align="top" height="175" color="{BG_PANEL}" strokeColor="{BORDER_MORTAL}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=10, bottom=10}}" margins="{{bottom=10}}">
                            <label align="top" height="22" text="VIRTUDES HUMANAS, HUMANIDADE &amp; FORÇA DE VONTADE" fontColor="{ACCENT_MORTAL}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            <layout align="top" height="28" margins="{{top=6}}">
                                <label align="left" width="95" text="Consciência:" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtVirtude1Val" align="left" width="40" field="virtude1_val" type="number" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{right=16}}"/>
                                <label align="left" width="95" text="Autocontrole:" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtVirtude2Val" align="left" width="40" field="virtude2_val" type="number" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{right=16}}"/>
                                <label align="left" width="75" text="Coragem:" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtVirtude3Val" align="left" width="40" field="virtude3_val" type="number" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("center")}"/>
                            </layout>
                            <layout align="top" height="28" margins="{{top=8}}">
                                <label align="left" width="95" text="Humanidade:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtMoralidadeVal" align="left" width="42" field="moralidade_val" type="number" fontColor="{TEXT_GOLD}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{right=14}}"/>
                                <label align="left" width="95" text="FdV Perm.:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtFdvPerm" align="left" width="42" field="fdv_perm" type="number" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{right=14}}"/>
                                <label align="left" width="44" text="Aura:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <label align="client" field="aura_resumo" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            </layout>
                            <layout align="top" height="32" margins="{{top=10}}">
                                <button align="left" width="225" text="Testar Degeneração (Consciência Dif 8)" fontSize="11" margins="{{right=10}}">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.rollDegeneration(sheet) end</event>
                                </button>
                                <button align="left" width="185" text="Testar Coragem / Pânico" fontSize="11" margins="{{right=10}}">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.rollRotschreck(sheet, 6) end</event>
                                </button>
                                <button name="btnFrenesiCarnical" visible="false" align="left" width="185" text="Frenesi Carniçal" fontSize="11">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.rollFrenzy(sheet, 6) end</event>
                                </button>
                            </layout>
                        </rectangle>
                    </layout>
                </scrollBox>
            </tab>"""


def generate_mortal_lfm() -> str:
    modo_sob_items = lua_str_list([
        "Humano Puro (Padrão)",
        "Carniçal / Ghoul (Vitae máx 2 + Potência 1)",
        "Numina (Fé Verdadeira / Magia de Cerca / Psíquico)",
    ])
    modo_sob_vals = lua_str_list(["humano", "carnical", "numina"])

    narrador_switch_card = f"""                        <rectangle align="top" height="84" color="{BG_PANEL}" strokeColor="{ACCENT_MORTAL}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=8, bottom=8}}" margins="{{bottom=10}}">
                            <label align="top" height="22" text="CHAVE DO NARRADOR — TRANSIÇÃO SOBRENATURAL EM JOGO (HUMANO | CARNIÇAL | NUMINA)" fontColor="{ACCENT_MORTAL}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            <layout align="top" height="30" margins="{{top=4}}">
                                <label align="left" width="140" text="Condição Sobrenatural:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <comboBox name="cmbMortalSobrenaturalModo" align="left" width="390" field="mortal_sobrenatural_modo" items="{modo_sob_items}" values="{modo_sob_vals}" fontColor="{TEXT_GOLD}" fontSize="11" margins="{{right=12}}"/>
                                <label align="left" width="110" text="Teto Disc. Ghoul:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtCarnicalDiscMax" align="left" width="38" field="carnical_disc_max" type="number" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}"/>
                            </layout>
                        </rectangle>"""

    mortal_meta = {"id": "mortal", "name": "Mortal", "appearanceZero": False}

    defaults: list[tuple[str, str]] = [
        ("nome", "Mortal V20"),
        ("is_vampire", "false"),
        ("modo_ficha", "criacao"),
        ("mortal_perfil", "padrao_643"),
        ("mortal_sobrenatural_modo", "humano"),
        ("carnical_disc_max", "1"),
        ("sangue_atual", "0"),
        ("sangue_max", "0"),
        ("sangue_por_turno", "0"),
        ("sangue_gasto_turno", "0"),
        ("fdv_perm", "5"),
        ("fdv_temp", "5"),
        ("virtude1_tipo", "consciencia"),
        ("virtude1_val", "3"),
        ("virtude2_tipo", "autocontrole"),
        ("virtude2_val", "3"),
        ("virtude3_val", "3"),
        ("moralidade_tipo", "humanidade"),
        ("moralidade_nome", "Humanidade"),
        ("moralidade_val", "7"),
        ("dano_contundente", "0"),
        ("dano_letal", "0"),
        ("dano_aggravado", "0"),
        ("dano_aplicar_qtd", "1"),
        ("dano_aplicar_tipo", "bashing"),
        ("cura_tipo", "bashing"),
        ("armadura_absorcao", "0"),
        ("tem_tamanho_grande", "false"),
        ("roll_attr_id", "attr_percepcao"),
        ("roll_hab_id", "hab_investigacao"),
        ("roll_bonus_dice", "0"),
        ("roll_diff", "6"),
        ("roll_usar_espec", "false"),
        ("roll_gastar_fdv", "false"),
        ("roll_usar_fama", "false"),
        ("roll_usar_status", "false"),
        ("roll_ignorar_ferimento", "false"),
        ("xp_total", "0"),
        ("xp_gasto", "0"),
        ("xp_exige_aprovacao", "true"),
        ("narrador_override", "false"),
        ("xp_loja_tipo", "auto"),
        ("xp_loja_campo", "hab_investigacao"),
        ("xp_loja_cat_custo", "auto"),
        ("xp_pendente_status", "nenhum"),
        ("disc_slot1_id", "potence"),
        ("disc_slot1_nivel", "0"),
        ("disc_slot1_pwr_lvl", "1"),
        ("disc_slot2_id", ""),
        ("disc_slot2_nivel", "0"),
        ("disc_slot2_pwr_lvl", "1"),
        ("disc_slot3_id", ""),
        ("disc_slot3_nivel", "0"),
        ("disc_slot3_pwr_lvl", "1"),
        ("disc_slot4_id", ""),
        ("disc_slot4_nivel", "0"),
        ("disc_slot4_pwr_lvl", "1"),
        ("numina_true_faith", "0"),
        ("numina_hedge_magic", "0"),
        ("numina_psychic", "0"),
    ]

    for _, rows in ATTRIBUTES_BY_COL:
        for aid, _, _ in rows:
            defaults.append((aid, "1"))

    for _, rows in ABILITIES_BY_COL:
        for hid, _ in rows:
            defaults.append((hid, "0"))

    for bid, _, vamp_only, _ in BACKGROUNDS_LIST:
        if not (vamp_only and bid in ("generation", "rituals")):
            defaults.append((f"bg_{bid}", "0"))

    for i in range(1, 7):
        defaults.extend([
            (f"mf_slot{i}_ativo", "true"),
            (f"mf_slot{i}_id", ""),
            (f"mf_slot{i}_nome", ""),
            (f"mf_slot{i}_tipo", "qualidade"),
            (f"mf_slot{i}_pontos", "0"),
        ])

    defaults.extend(COMBAT_MANEUVER_FIELD_DEFAULTS)

    datalinks = root_datalinks_xml(
        defaults,
        on_change_lua="if sheet ~= nil and V20Bridge ~= nil then V20Bridge.syncDerivedFields(sheet); atualizarVisibilidadeMortal(self); atualizarPermissoesModo(self); end",
        chunk_size=32,
    )

    perms_lua = build_mode_permissions_lua(is_vampire=False)

    xml_out = f"""<?xml version="1.0" encoding="UTF-8"?>
<form name="frmMortal" formType="sheetTemplate" dataType="br.com.v20.Mortal" title="Vampiro V20 - Mortal" align="client" theme="dark">

    <script>
        <![CDATA[
        local V20Bridge = _G.V20Bridge or require("Adapter.firecast_bridge")

        local function atualizarVisibilidadeMortal(formObj)
            if formObj == nil or sheet == nil then return end
            local modo = sheet.mortal_sobrenatural_modo or "humano"
            local isCarnical = (modo == "carnical")
            local isNumina = (modo == "numina")
            if formObj.pnlHeaderBlood ~= nil then formObj.pnlHeaderBlood:setVisible(isCarnical) end
            if formObj.pnlCarnical ~= nil then formObj.pnlCarnical:setVisible(isCarnical) end
            if formObj.pnlNumina ~= nil then formObj.pnlNumina:setVisible(isNumina) end
            if formObj.btnFrenesiCarnical ~= nil then formObj.btnFrenesiCarnical:setVisible(isCarnical) end
        end

{perms_lua}
        ]]>
    </script>

    <rectangle align="client" color="{BG_MAIN}">
{header_bar_xml(ACCENT_MORTAL, BORDER_MORTAL, "MORTAL / INQUISIDOR (V20)", is_vampire=False)}
{dice_roller_footer_xml(ACCENT_MORTAL, BORDER_MORTAL)}

        <tabControl name="pgcPrincipal" align="client" margins="{{left=6, right=6, top=6, bottom=6}}">
{build_mortal_tab1()}
{build_tab2_traits(mortal_meta, ACCENT_MORTAL, is_vampire=False, border=BORDER_MORTAL)}
{build_mortal_tab3()}
{build_tab4_backgrounds(ACCENT_MORTAL, border=BORDER_MORTAL, is_vampire=False)}
{build_tab5_combat(ACCENT_MORTAL, border=BORDER_MORTAL, is_vampire=False)}
{build_mortal_tab6()}
{build_tab7_xp(ACCENT_MORTAL, border=BORDER_MORTAL, extra_top_card=narrador_switch_card, is_vampire=False)}
{suite_credits_tab_xml("8. Sobre", ACCENT_MORTAL, BORDER_MORTAL, "Mortal / Carniçal / Numina (br.com.v20.Mortal)")}
        </tabControl>
    </rectangle>

{datalinks}
</form>
"""
    validate_generated_lfm_xml(xml_out)
    return xml_out


def _write_if_changed(out_path: str, xml_content: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as existing_f:
            existing = existing_f.read()
        if existing.replace("\r\n", "\n") == xml_content.replace("\r\n", "\n"):
            print(f"[OK] Inalterado {os.path.relpath(out_path, ROOT)}")
            return
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(xml_content)
    print(f"[OK] Gerado {os.path.relpath(out_path, ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera a ficha Mortal LFM (Sheets/frmMortal.lfm) para o Firecast SDK 3.7b.")
    parser.add_argument("--out", default="", help="Caminho opcional de saída .lfm.")
    args = parser.parse_args()

    xml_content = generate_mortal_lfm()
    out_path = args.out or os.path.join(ROOT, "Sheets", "frmMortal.lfm")
    _write_if_changed(out_path, xml_content)


if __name__ == "__main__":
    main()
