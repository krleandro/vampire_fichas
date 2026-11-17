#!/usr/bin/env python3
"""Gerador parametrizado de fichas vampíricas V20 (.lfm) para RRPG Firecast SDK 3.7b."""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from Templates.theme_gothic import (  # noqa: E402
    ABILITIES_BY_COL,
    ALL_BLOOD_MAGIC_PATHS_LIST,
    ATTRIBUTES_BY_COL,
    BACKGROUNDS_LIST,
    BG_MAIN,
    BG_PANEL,
    BORDER_VAMP,
    CLAN_ORDER,
    CLANS,
    COMBAT_MANEUVER_FIELD_DEFAULTS,
    COMBAT_MANEUVER_OPTIONS,
    COVER_LEVEL_OPTIONS,
    DISCIPLINES_LIST,
    FLANK_MODE_OPTIONS,
    MERITS_FLAWS_OPTIONS,
    MORALITY_PATHS,
    NECROMANCY_PATHS_LIST,
    RITUALS_LIST,
    TARGET_LOCATION_OPTIONS,
    TEXT_ALERT,
    TEXT_GOLD,
    TEXT_MAIN,
    TEXT_MUTED,
    THAUMATURGY_PATHS_LIST,
    all_attr_options,
    all_hab_options,
    all_xp_upgradable_field_options,
    assert_align,
    build_mode_permissions_lua,
    dice_roller_footer_xml,
    header_bar_xml,
    health_track_xml,
    lua_str_list,
    root_datalinks_xml,
    suite_credits_tab_xml,
    trait_row_xml,
    validate_generated_lfm_xml,
    xml_esc,
)


def build_tab1_creation(clan: dict, accent: str) -> str:
    modo_items = lua_str_list(["Criação Validada (7/5/3)", "Modo Jogo (XP)", "Edição Livre (Narrador)"])
    modo_vals = lua_str_list(["criacao", "jogo", "narrador_livre"])
    return f"""            <tab name="tabCriacao" title="1. Personagem &amp; Criação">
                <scrollBox align="client" padding="{{left=10, right=10, top=10, bottom=10}}">
                    <layout align="top" height="720">
                        <rectangle align="top" height="175" color="{BG_PANEL}" strokeColor="{BORDER_VAMP}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=10, bottom=10}}" margins="{{bottom=10}}">
                            <label align="top" height="22" text="IDENTIDADE CAINITA — CLÃ {xml_esc(clan['name'].upper())}" fontColor="{accent}" fontSize="13" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            <layout align="top" height="28" margins="{{top=6}}">
                                <label align="left" width="75" text="Jogador:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit align="left" width="180" field="jogador" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=10}}"/>
                                <label align="left" width="70" text="Crônica:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit align="left" width="190" field="cronica" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=10}}"/>
                                <label align="left" width="70" text="Conceito:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit align="client" field="conceito" fontColor="{TEXT_MAIN}" fontSize="11"/>
                            </layout>
                            <layout align="top" height="28" margins="{{top=6}}">
                                <label align="left" width="75" text="Natureza:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit align="left" width="180" field="natureza" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=10}}"/>
                                <label align="left" width="70" text="Comport.:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit align="left" width="190" field="comportamento" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=10}}"/>
                                <label align="left" width="70" text="Senhor:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit align="client" field="senhor_regente" fontColor="{TEXT_MAIN}" fontSize="11"/>
                            </layout>
                            <layout align="top" height="28" margins="{{top=6}}">
                                <label align="left" width="95" text="Geração Base:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtGeracaoBase" align="left" width="44" field="geracao_base" type="number" fontColor="{TEXT_GOLD}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=10}}"/>
                                <label align="left" width="105" text="Geração Efetiva:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <label align="left" width="38" field="geracao" fontColor="{TEXT_GOLD}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{right=14}}"/>
                                <label align="left" width="85" text="Modo Ficha:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <comboBox name="cmbModoFicha" align="left" width="210" field="modo_ficha" items="{modo_items}" values="{modo_vals}" fontColor="{TEXT_MAIN}" fontSize="11"/>
                            </layout>
                        </rectangle>

                        <rectangle align="top" height="250" color="{BG_PANEL}" strokeColor="{BORDER_VAMP}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=10, bottom=10}}" margins="{{bottom=10}}">
                            <label align="top" height="22" text="ASSISTENTE DE CRIAÇÃO NEÓFITO V20 (7/5/3 • 13/9/5 • 15 PONTOS DE BÔNUS)" fontColor="{accent}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            <label align="top" height="20" text="Informe os pontos extras comprados com Pontos de Bônus (Atrib: 5, Hab: 2, Disc: 7, Antec: 1, Virt: 2, Moral: 1, FdV: 1):" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                            <layout align="top" height="28" margins="{{top=6}}">
                                <label align="left" width="85" text="Bônus Atrib:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtFreebieAttributes" align="left" width="40" field="freebie_attributes" type="number" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=10}}"/>
                                <label align="left" width="80" text="Bônus Hab:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtFreebieAbilities" align="left" width="40" field="freebie_abilities" type="number" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=10}}"/>
                                <label align="left" width="80" text="Bônus Disc:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtFreebieDisciplines" align="left" width="40" field="freebie_disciplines" type="number" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=10}}"/>
                                <label align="left" width="85" text="Bônus Antec:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtFreebieBackgrounds" align="left" width="40" field="freebie_backgrounds" type="number" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}"/>
                            </layout>
                            <layout align="top" height="28" margins="{{top=4}}">
                                <label align="left" width="85" text="Bônus Virt:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtFreebieVirtues" align="left" width="40" field="freebie_virtues" type="number" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=10}}"/>
                                <label align="left" width="80" text="Bônus Moral:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtFreebieMorality" align="left" width="40" field="freebie_morality" type="number" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=10}}"/>
                                <label align="left" width="80" text="Bônus FdV:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtFreebieWillpower" align="left" width="40" field="freebie_willpower" type="number" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=14}}"/>
                                <button name="btnRolarVitaeInicial" align="left" width="160" text="Rolar 1d10 Vitae Inicial" fontSize="11">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.rollInitialBlood(sheet) end</event>
                                </button>
                            </layout>
                            <layout align="top" height="32" margins="{{top=8}}">
                                <button name="btnValidarCriacao" align="left" width="150" text="Validar Criação V20" fontSize="11" margins="{{right=8}}">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.validateCreationOnSheet(sheet, nil, nil, nil, false) end</event>
                                </button>
                                <button name="btnConcluirCriacao" align="left" width="245" text="Concluir Criação -&gt; Modo Jogo" fontSize="11" fontStyle="bold">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.validateCreationOnSheet(sheet, nil, nil, nil, true) end</event>
                                </button>
                            </layout>
                            <label align="client" field="criacao_resumo_status" wordWrap="true" fontColor="{TEXT_GOLD}" fontSize="11" horzTextAlign="{assert_align("leading")}" margins="{{top=6}}"/>
                        </rectangle>

                        <rectangle align="top" height="120" color="{BG_PANEL}" strokeColor="{accent}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=10, bottom=10}}">
                            <label align="top" height="22" text="FRAQUEZA HEREDITÁRIA DO CLÃ {xml_esc(clan['name'].upper())}" fontColor="{accent}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            <label align="client" text="{xml_esc(clan['weaknessSummary'])}" wordWrap="true" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                        </rectangle>
                    </layout>
                </scrollBox>
            </tab>"""


def build_tab2_traits(clan: dict, accent: str, is_vampire: bool = True, border: str = BORDER_VAMP) -> str:
    attr_cols_xml = []
    for idx, (col_title, rows) in enumerate(ATTRIBUTES_BY_COL):
        align_pos = "left" if idx < 2 else "client"
        width_attr = 'width="305" margins="{right=8}"' if idx < 2 else ""
        r_xml = []
        for aid, aname, bkey in rows:
            min_v = 0 if (clan.get("appearanceZero") and aid == "attr_aparencia") else 1
            r_xml.append(
                trait_row_xml(
                    aid,
                    aname,
                    kind="attr",
                    max_cap_field="atributo_max_geracao",
                    min_val=min_v,
                    with_specialty=True,
                    blood_buff_key=bkey if is_vampire else "",
                )
            )
        joined_rows = "\n".join(r_xml)
        attr_cols_xml.append(
            f"""                            <layout align="{align_pos}" {width_attr}>
                                <label align="top" height="20" text="{xml_esc(col_title)}" fontColor="{accent}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("center")}"/>
{joined_rows}
                            </layout>"""
        )

    hab_cols_xml = []
    for idx, (col_title, rows) in enumerate(ABILITIES_BY_COL):
        align_pos = "left" if idx < 2 else "client"
        width_attr = 'width="305" margins="{right=8}"' if idx < 2 else ""
        r_xml = [
            trait_row_xml(hid, hname, kind="hab", max_cap_field="atributo_max_geracao", min_val=0, with_specialty=True)
            for hid, hname in rows
        ]
        joined_rows = "\n".join(r_xml)
        hab_cols_xml.append(
            f"""                            <layout align="{align_pos}" {width_attr}>
                                <label align="top" height="20" text="{xml_esc(col_title)}" fontColor="{accent}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("center")}"/>
{joined_rows}
                            </layout>"""
        )

    extra_rows = []
    for i in range(1, 5):
        extra_rows.append(
            f"""                            <layout align="top" height="26" margins="{{bottom=2}}">
                                <edit name="edtHabExtraNome{i}" align="left" width="190" field="hab_extra{i}_nome" textPrompt="Habilidade Extra #{i}" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=6}}"/>
                                <edit name="edtHabExtraVal{i}" align="left" width="42" field="hab_extra{i}_val" type="number" fontColor="{TEXT_GOLD}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=6}}"/>
                                <edit name="edtHabExtraEspec{i}" align="client" field="hab_extra{i}_espec" textPrompt="Especialidade / Categoria" fontColor="{TEXT_MUTED}" fontSize="10"/>
                            </layout>"""
        )

    clear_buffs_btn = (
        '<button align="right" width="175" text="Encerrar Cena (Limpar Buffs)" fontSize="10">'
        '<event name="onClick">if sheet ~= nil then V20Bridge.clearSceneBuffs(sheet) end</event>'
        "</button>"
        if is_vampire
        else ""
    )

    return f"""            <tab name="tabAtributos" title="2. Atributos &amp; Habilidades">
                <scrollBox align="client" padding="{{left=10, right=10, top=10, bottom=10}}">
                    <layout align="top" height="760">
                        <rectangle align="top" height="158" color="{BG_PANEL}" strokeColor="{border}" strokeSize="1" xradius="6" yradius="6" padding="{{left=10, right=10, top=8, bottom=8}}" margins="{{bottom=10}}">
                            <layout align="top" height="22">
                                <label align="left" width="380" text="ATRIBUTOS V20 (CLIQUE NO NOME PARA CARREGAR NA PARADA)" fontColor="{accent}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                                {clear_buffs_btn}
                            </layout>
                            <layout align="client" margins="{{top=4}}">
{chr(10).join(attr_cols_xml)}
                            </layout>
                        </rectangle>

                        <rectangle align="top" height="365" color="{BG_PANEL}" strokeColor="{border}" strokeSize="1" xradius="6" yradius="6" padding="{{left=10, right=10, top=8, bottom=8}}" margins="{{bottom=10}}">
                            <label align="top" height="22" text="HABILIDADES OFICIAIS V20 (PERÍCIA 0 = +1 DIF • CONHECIMENTO 0 = BLOQUEADO)" fontColor="{accent}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            <layout align="client" margins="{{top=4}}">
{chr(10).join(hab_cols_xml)}
                            </layout>
                        </rectangle>

                        <rectangle align="top" height="155" color="{BG_PANEL}" strokeColor="{border}" strokeSize="1" xradius="6" yradius="6" padding="{{left=10, right=10, top=8, bottom=8}}">
                            <label align="top" height="22" text="HABILIDADES SECUNDÁRIAS / OFÍCIOS ESPECÍFICOS" fontColor="{accent}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
{chr(10).join(extra_rows)}
                        </rectangle>
                    </layout>
                </scrollBox>
            </tab>"""


def build_tab3_disciplines(accent: str) -> str:
    disc_items = lua_str_list(["— Nenhuma —"] + [n for _, n in DISCIPLINES_LIST])
    disc_vals = lua_str_list([""] + [i for i, _ in DISCIPLINES_LIST])
    cat_items = lua_str_list(["De Clã (x5)", "Fora do Clã (x7)", "Caitiff (x6)", "Linha Secundária (x4)"])
    cat_vals = lua_str_list(["cla", "fora_cla", "caitiff", "linha_secundaria"])
    lvl_items = lua_str_list(["Poder Nv 1", "Poder Nv 2", "Poder Nv 3", "Poder Nv 4", "Poder Nv 5"])
    lvl_vals = lua_str_list(["1", "2", "3", "4", "5"])

    slot_cards = []
    for i in range(1, 10):
        badge = f"CLÃ #{i}" if i <= 3 else f"EXTRA #{i - 3}"
        slot_cards.append(
            f"""                        <rectangle align="top" height="62" color="{BG_PANEL}" strokeColor="{BORDER_VAMP}" strokeSize="1" xradius="5" yradius="5" padding="{{left=10, right=10, top=6, bottom=6}}" margins="{{bottom=6}}">
                            <layout align="top" height="26">
                                <label align="left" width="66" text="{badge}" fontColor="{accent}" fontSize="10" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                                <comboBox name="cmbDiscSlotId{i}" align="left" width="185" field="disc_slot{i}_id" items="{disc_items}" values="{disc_vals}" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=6}}"/>
                                <label align="left" width="36" text="Nível:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("trailing")}" margins="{{right=4}}"/>
                                <edit name="edtDiscSlotNivel{i}" align="left" width="36" field="disc_slot{i}_nivel" type="number" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{right=6}}"/>
                                <comboBox name="cmbDiscSlotCat{i}" align="left" width="140" field="disc_slot{i}_cat" items="{cat_items}" values="{cat_vals}" fontColor="{TEXT_MUTED}" fontSize="10" margins="{{right=6}}"/>
                                <comboBox name="cmbDiscSlotPwrLvl{i}" align="left" width="110" field="disc_slot{i}_pwr_lvl" items="{lvl_items}" values="{lvl_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=6}}"/>
                                <button name="btnDiscSlotAtivar{i}" align="right" width="118" text="Ativar / Rolar" fontSize="11" fontStyle="bold">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.activateDisciplineSlot(sheet, {i}) end</event>
                                </button>
                            </layout>
                            <label align="client" field="disc_slot{i}_resumo" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}" margins="{{top=2}}"/>
                        </rectangle>"""
        )

    attr_items, attr_vals = all_attr_options(include_virtual=True)
    hab_items, hab_vals = all_hab_options(include_none=True, include_backgrounds=False)

    return f"""            <tab name="tabDisciplinas" title="3. Disciplinas &amp; Poderes">
                <scrollBox align="client" padding="{{left=10, right=10, top=10, bottom=10}}">
                    <layout align="top" height="860">
                        <rectangle align="top" height="72" color="{BG_PANEL}" strokeColor="{accent}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=8, bottom=8}}" margins="{{bottom=8}}">
                            <layout align="top" height="26">
                                <label align="left" width="135" text="MODIFICADORES ATIVOS:" fontColor="{accent}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                                <label align="client" field="buffs_cena_resumo" fontColor="{TEXT_GOLD}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <button align="right" width="135" text="Potência Automática" fontSize="10" margins="{{left=4}}">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.activateDisciplinePower(sheet, 'potence', 'pot_1') end</event>
                                </button>
                                <button align="right" width="125" text="+1 Ação Rapidez" fontSize="10" margins="{{left=4}}">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.activateDisciplinePower(sheet, 'celerity', 'cel_1') end</event>
                                </button>
                                <button align="right" width="120" text="Limpar Buffs Cena" fontSize="10" margins="{{left=4}}">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.clearSceneBuffs(sheet) end</event>
                                </button>
                            </layout>
                            <label align="client" text="Catálogo Universal V20: todas as 17 Disciplinas Clássicas (incluindo Taumaturgia, Necromancia e Tenebrosidade) disponíveis em qualquer slot." fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}" margins="{{top=4}}"/>
                        </rectangle>

{chr(10).join(slot_cards)}

                        <rectangle align="top" height="110" color="{BG_PANEL}" strokeColor="{BORDER_VAMP}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=8, bottom=8}}" margins="{{top=4}}">
                            <label align="top" height="20" text="PODER CUSTOMIZADO / ANCIÃO (6+) / TRILHA OU RITUAL SECUNDÁRIO" fontColor="{accent}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            <layout align="top" height="28" margins="{{top=4}}">
                                <edit align="left" width="185" field="custom_pwr_nome" textPrompt="Nome do Poder / Ritual" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=6}}"/>
                                <label align="left" width="44" text="Sangue:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("trailing")}" margins="{{right=3}}"/>
                                <edit align="left" width="34" field="custom_pwr_sangue" type="number" fontColor="{TEXT_ALERT}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=6}}"/>
                                <label align="left" width="30" text="FdV:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("trailing")}" margins="{{right=3}}"/>
                                <edit align="left" width="34" field="custom_pwr_fdv" type="number" fontColor="{TEXT_GOLD}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=6}}"/>
                                <comboBox align="left" width="135" field="custom_pwr_attr" items="{attr_items}" values="{attr_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=6}}"/>
                                <comboBox align="left" width="135" field="custom_pwr_hab" items="{hab_items}" values="{hab_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=6}}"/>
                                <edit align="left" width="34" field="custom_pwr_dif" type="number" fontColor="{TEXT_GOLD}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=6}}"/>
                                <button align="right" width="120" text="Ativar Custom" fontSize="11" fontStyle="bold">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.activateCustomPower(sheet) end</event>
                                </button>
                            </layout>
                        </rectangle>
                    </layout>
                </scrollBox>
            </tab>"""


def build_tab4_backgrounds(accent: str, border: str = BORDER_VAMP, is_vampire: bool = True) -> str:
    bg_rows = []
    for bid, bname, vamp_only, act_label in BACKGROUNDS_LIST:
        if (not is_vampire) and vamp_only and bid in ("generation", "rituals"):
            continue
        btn_xml = (
            f'<button align="right" width="92" text="{xml_esc(act_label)}" fontSize="10">'
            f'<event name="onClick">if sheet ~= nil then V20Bridge.rollBackgroundAction(sheet, \'{bid}\') end</event>'
            f"</button>"
            if act_label
            else f'<label align="right" width="92" text="(Passivo)" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("center")}"/>'
        )
        bg_rows.append(
            f"""                            <layout align="top" height="26" margins="{{bottom=2}}">
                                <label align="left" width="155" text="{xml_esc(bname)}" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtBg_{bid}" align="left" width="38" field="bg_{bid}" type="number" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{right=8}}"/>
                                <edit align="client" field="bg_notes_{bid}" textPrompt="Detalhes / Esfera / Recipientes" fontColor="{TEXT_MUTED}" fontSize="10" margins="{{right=8}}"/>
                                {btn_xml}
                            </layout>"""
        )

    ret_rows = []
    for i in range(1, 5):
        ret_rows.append(
            f"""                            <layout align="top" height="26" margins="{{bottom=2}}">
                                <edit align="left" width="165" field="lacaio{i}_nome" textPrompt="Aliado / Lacaio #{i}" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=6}}"/>
                                <edit align="left" width="130" field="lacaio{i}_papel" textPrompt="Papel / Domitor" fontColor="{TEXT_MUTED}" fontSize="10" margins="{{right=6}}"/>
                                <label align="left" width="48" text="Parada:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("trailing")}" margins="{{right=3}}"/>
                                <edit align="left" width="36" field="lacaio{i}_parada" type="number" fontColor="{TEXT_GOLD}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=6}}"/>
                                <label align="left" width="46" text="Sangue:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("trailing")}" margins="{{right=3}}"/>
                                <edit align="left" width="36" field="lacaio{i}_sangue" type="number" fontColor="{TEXT_ALERT}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=6}}"/>
                                <edit align="client" field="lacaio{i}_notas" textPrompt="Vitalidade / Notas" fontColor="{TEXT_MUTED}" fontSize="10" margins="{{right=6}}"/>
                                <button align="right" width="84" text="Acionar" fontSize="10">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.rollAllyOrRetainer(sheet, {i}) end</event>
                                </button>
                            </layout>"""
        )

    mf_items = lua_str_list([n for _, n in MERITS_FLAWS_OPTIONS])
    mf_vals = lua_str_list([i for i, _ in MERITS_FLAWS_OPTIONS])
    tipo_items = lua_str_list(["Qualidade", "Defeito"])
    tipo_vals = lua_str_list(["qualidade", "defeito"])

    mf_rows = []
    for i in range(1, 7):
        mf_rows.append(
            f"""                            <layout align="top" height="26" margins="{{bottom=2}}">
                                <checkBox name="chkMfAtivo{i}" align="left" width="56" field="mf_slot{i}_ativo" text="Ativo" fontColor="{TEXT_MAIN}" fontSize="10"/>
                                <comboBox name="cmbMfId{i}" align="left" width="255" field="mf_slot{i}_id" items="{mf_items}" values="{mf_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=6}}"/>
                                <edit name="edtMfNome{i}" align="client" field="mf_slot{i}_nome" textPrompt="Descrição / Qualidade Customizada" fontColor="{TEXT_MUTED}" fontSize="10" margins="{{right=6}}"/>
                                <comboBox name="cmbMfTipo{i}" align="left" width="95" field="mf_slot{i}_tipo" items="{tipo_items}" values="{tipo_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=6}}"/>
                                <edit name="edtMfPontos{i}" align="right" width="38" field="mf_slot{i}_pontos" type="number" fontColor="{TEXT_GOLD}" fontSize="11" horzTextAlign="{assert_align("center")}"/>
                            </layout>"""
        )

    hunt_bar = (
        f'<layout align="top" height="28" margins="{{top=4, bottom=6}}">'
        f'<label align="left" width="110" text="Faixa Recursos:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>'
        f'<label align="left" width="245" field="recursos_faixa" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>'
        f'<label align="left" width="80" text="Recipientes:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("trailing")}" margins="{{right=4}}"/>'
        f'<label align="left" width="36" field="rebanho_recipientes" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}"/>'
        f'<button align="right" width="195" text="Caçar (Rebanho + Domínio)" fontSize="11" fontStyle="bold">'
        f'<event name="onClick">if sheet ~= nil then V20Bridge.huntWithHerdDomain(sheet) end</event>'
        f"</button>"
        f"</layout>"
        if is_vampire
        else f'<layout align="top" height="26" margins="{{top=4, bottom=6}}">'
        f'<label align="left" width="115" text="Faixa Financeira:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>'
        f'<label align="client" field="recursos_faixa" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>'
        f"</layout>"
    )

    bg_box_h = 440 if is_vampire else 390
    return f"""            <tab name="tabAntecedentes" title="4. Antecedentes &amp; Qualidades">
                <scrollBox align="client" padding="{{left=10, right=10, top=10, bottom=10}}">
                    <layout align="top" height="880">
                        <rectangle align="top" height="{bg_box_h}" color="{BG_PANEL}" strokeColor="{border}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=8, bottom=8}}" margins="{{bottom=10}}">
                            <label align="top" height="22" text="ANTECEDENTES V20 &amp; AÇÕES DE REDE" fontColor="{accent}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            {hunt_bar}
{chr(10).join(bg_rows)}
                        </rectangle>

                        <rectangle align="top" height="155" color="{BG_PANEL}" strokeColor="{border}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=8, bottom=8}}" margins="{{bottom=10}}">
                            <label align="top" height="22" text="ALIADOS, LACAIOS &amp; CARNIÇAIS VINCULADOS" fontColor="{accent}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
{chr(10).join(ret_rows)}
                        </rectangle>

                        <rectangle align="top" height="220" color="{BG_PANEL}" strokeColor="{border}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=8, bottom=8}}">
                            <label align="top" height="22" text="QUALIDADES &amp; DEFEITOS V20 (TETO +7 DEFEITOS NA CRIAÇÃO)" fontColor="{accent}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
{chr(10).join(mf_rows)}
                        </rectangle>
                    </layout>
                </scrollBox>
            </tab>"""


def build_tab5_combat(accent: str, border: str = BORDER_VAMP, is_vampire: bool = True) -> str:
    attr_items, attr_vals = all_attr_options(include_virtual=False)
    hab_items, hab_vals = all_hab_options(include_none=False, include_backgrounds=False)
    dmg_items = lua_str_list(["Contundente", "Letal", "Agravado"])
    dmg_vals = lua_str_list(["bashing", "lethal", "aggravated"])

    man_items = lua_str_list([lbl for _, lbl in COMBAT_MANEUVER_OPTIONS])
    man_vals = lua_str_list([mid for mid, _ in COMBAT_MANEUVER_OPTIONS])
    slot_items = lua_str_list(["Slot Arma #1", "Slot Arma #2", "Slot Arma #3", "Slot Arma #4"])
    slot_vals = lua_str_list(["1", "2", "3", "4"])
    act_tot_items = lua_str_list([
        "1 Ação (Sem Divisão)",
        "2 Ações (-2 / -3)",
        "3 Ações (-3 / -4 / -5)",
        "4 Ações (-4..-7)",
        "5 Ações (-5..-9)",
    ])
    act_tot_vals = lua_str_list(["1", "2", "3", "4", "5"])
    act_ord_items = lua_str_list(["1ª Ação", "2ª Ação", "3ª Ação", "4ª Ação", "5ª Ação"])
    act_ord_vals = lua_str_list(["1", "2", "3", "4", "5"])
    loc_items = lua_str_list([lbl for _, lbl in TARGET_LOCATION_OPTIONS])
    loc_vals = lua_str_list([lid for lid, _ in TARGET_LOCATION_OPTIONS])
    cov_items = lua_str_list([lbl for _, lbl in COVER_LEVEL_OPTIONS])
    cov_vals = lua_str_list([cid for cid, _ in COVER_LEVEL_OPTIONS])
    flk_items = lua_str_list([lbl for _, lbl in FLANK_MODE_OPTIONS])
    flk_vals = lua_str_list([fid for fid, _ in FLANK_MODE_OPTIONS])

    weapon_rows = []
    for i in range(1, 5):
        weapon_rows.append(
            f"""                            <layout align="top" height="28" margins="{{bottom=3}}">
                                <edit align="left" width="155" field="arma{i}_nome" textPrompt="Arma / Manobra #{i}" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=6}}"/>
                                <comboBox align="left" width="115" field="arma{i}_attr" items="{attr_items}" values="{attr_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=4}}"/>
                                <comboBox align="left" width="135" field="arma{i}_hab" items="{hab_items}" values="{hab_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=4}}"/>
                                <edit align="left" width="34" field="arma{i}_dif" type="number" fontColor="{TEXT_GOLD}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=4}}"/>
                                <edit align="left" width="36" field="arma{i}_dano" type="number" fontColor="{TEXT_ALERT}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=4}}"/>
                                <comboBox align="left" width="105" field="arma{i}_tipo" items="{dmg_items}" values="{dmg_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=4}}"/>
                                <edit align="client" field="arma{i}_municao" textPrompt="Munição" fontColor="{TEXT_MUTED}" fontSize="10" margins="{{right=6}}"/>
                                <button align="right" width="82" text="Atacar" fontSize="10" fontStyle="bold">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.rollWeaponAttack(sheet, {i}) end</event>
                                </button>
                            </layout>"""
        )

    return f"""            <tab name="tabCombate" title="5. Combate &amp; Vitalidade">
                <scrollBox align="client" padding="{{left=10, right=10, top=10, bottom=10}}">
                    <layout align="top" height="880">
                        <rectangle align="top" height="68" color="{BG_PANEL}" strokeColor="{border}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=8, bottom=8}}" margins="{{bottom=10}}">
                            <label align="top" height="20" text="ATALHOS RÁPIDOS DE COMBATE V20" fontColor="{accent}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            <layout align="top" height="28" margins="{{top=4}}">
                                <button align="left" width="145" text="Iniciativa (1d10+Mod)" fontSize="10" fontStyle="bold" margins="{{right=6}}">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.rollInitiative(sheet) end</event>
                                </button>
                                <button align="left" width="115" text="Briga (Des+Bri)" fontSize="10" margins="{{right=6}}">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.rollFromSheet(sheet, {{attrId='attr_destreza', habId='hab_briga', difficulty=6, label='Ataque de Briga'}}) end</event>
                                </button>
                                <button align="left" width="125" text="Esquiva (Des+Esp)" fontSize="10" margins="{{right=6}}">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.rollFromSheet(sheet, {{attrId='attr_destreza', habId='hab_esportes', difficulty=6, label='Esquiva'}}) end</event>
                                </button>
                                <button align="left" width="135" text="Armas Brancas" fontSize="10" margins="{{right=6}}">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.rollFromSheet(sheet, {{attrId='attr_destreza', habId='hab_armas_brancas', difficulty=6, label='Armas Brancas'}}) end</event>
                                </button>
                                <button align="left" width="135" text="Armas de Fogo" fontSize="10">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.rollFromSheet(sheet, {{attrId='attr_destreza', habId='hab_armas_fogo', difficulty=6, label='Armas de Fogo'}}) end</event>
                                </button>
                            </layout>
                        </rectangle>

                        <rectangle name="crdEstudioManobras" align="top" height="236" color="{BG_PANEL}" strokeColor="{accent}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=8, bottom=8}}" margins="{{bottom=10}}">
                            <label name="lblTituloEstudioManobras" align="top" height="20" text="ESTÚDIO DE MANOBRAS V20, DIVISÃO DE PARADAS &amp; DANO ENCADEADO" fontColor="{accent}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            <layout align="top" height="28" margins="{{top=4}}">
                                <label align="left" width="58" text="Manobra:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <comboBox name="cmbCmbManobraId" align="left" width="245" field="cmb_manobra_id" items="{man_items}" values="{man_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=6}}"/>
                                <comboBox name="cmbCmbArmaSlot" align="left" width="110" field="cmb_arma_slot" items="{slot_items}" values="{slot_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=6}}"/>
                                <label align="left" width="72" text="Pen. Armad.:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("trailing")}" margins="{{right=3}}"/>
                                <edit name="edtArmaduraPenalidade" align="left" width="34" field="armadura_penalidade" type="number" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=8}}"/>
                                <checkBox name="chkCmbEmAgarrao" align="left" width="115" field="em_agarrao" text="Em Agarrão" fontColor="{TEXT_GOLD}" fontSize="10" fontStyle="bold"/>
                            </layout>
                            <layout align="top" height="28" margins="{{top=4}}">
                                <label align="left" width="46" text="Ações:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <comboBox name="cmbCmbAcoesNormais" align="left" width="150" field="cmb_acoes_normais" items="{act_tot_items}" values="{act_tot_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=6}}"/>
                                <comboBox name="cmbCmbAcaoOrdem" align="left" width="88" field="cmb_acao_ordem" items="{act_ord_items}" values="{act_ord_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=6}}"/>
                                <label align="left" width="88" text="Menor Parada:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("trailing")}" margins="{{right=3}}"/>
                                <edit name="edtCmbMenorParada" align="left" width="36" field="cmb_menor_parada" type="number" fontColor="{TEXT_GOLD}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=8}}"/>
                                <checkBox name="chkCmbAcaoRapidez" align="left" width="128" field="cmb_acao_rapidez" text="Ação de Rapidez" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=4}}"/>
                                <label align="left" width="52" text="Extras:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("trailing")}" margins="{{right=3}}"/>
                                <label name="lblCmbRapidezExtras" align="left" width="26" field="rapidez_acoes_extras" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("center")}"/>
                            </layout>
                            <layout align="top" height="28" margins="{{top=4}}">
                                <label align="left" width="36" text="Mira:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtCmbMiraTurnos" align="left" width="32" field="cmb_mira_turnos" type="number" fontColor="{TEXT_GOLD}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=4}}"/>
                                <checkBox name="chkCmbTemLuneta" align="left" width="68" field="cmb_tem_luneta" text="Luneta" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=6}}"/>
                                <comboBox name="cmbCmbAlvoLocalizado" align="left" width="185" field="cmb_alvo_localizado" items="{loc_items}" values="{loc_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=6}}"/>
                                <comboBox name="cmbCmbCobertura" align="left" width="165" field="cmb_cobertura" items="{cov_items}" values="{cov_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=6}}"/>
                                <comboBox name="cmbCmbPosicao" align="client" field="cmb_posicao" items="{flk_items}" values="{flk_vals}" fontColor="{TEXT_MAIN}" fontSize="10"/>
                            </layout>
                            <layout align="top" height="28" margins="{{top=4}}">
                                <label align="left" width="84" text="Sucessos Def.:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtCmbDefesaAlvo" align="left" width="34" field="cmb_defesa_alvo_sucessos" type="number" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=8}}"/>
                                <label align="left" width="68" text="Força Alvo:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("trailing")}" margins="{{right=3}}"/>
                                <edit name="edtCmbForcaAlvo" align="left" width="34" field="cmb_forca_alvo" type="number" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=8}}"/>
                                <label align="left" width="92" text="Defesas Turno:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("trailing")}" margins="{{right=3}}"/>
                                <edit name="edtCmbDefesasTurno" align="left" width="34" field="cmb_defesas_feitas_turno" type="number" fontColor="{TEXT_GOLD}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=8}}"/>
                                <button name="btnCmbExecutarManobra" align="right" width="175" text="Executar Manobra V20" fontSize="11" fontStyle="bold">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.executeCombatManeuver(sheet, nil) end</event>
                                </button>
                            </layout>
                            <label name="lblCmbManobraResumo" align="top" height="20" field="cmb_manobra_resumo" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}" margins="{{top=4}}"/>
                            <layout align="top" height="30" margins="{{top=4}}">
                                <label align="left" width="98" text="Dano Encadeado:" fontColor="{TEXT_GOLD}" fontSize="10" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                                <label name="lblCmbDanoPendenteResumo" align="client" field="cmb_dano_pendente_resumo" fontColor="{TEXT_MAIN}" fontSize="10" horzTextAlign="{assert_align("leading")}" margins="{{right=8}}"/>
                                <button name="btnCmbRolarDanoPendente" align="right" width="175" text="Rolar Dano Encadeado" fontSize="11" fontStyle="bold">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.rollPendingCombatDamage(sheet) end</event>
                                </button>
                            </layout>
                        </rectangle>

                        <rectangle align="top" height="170" color="{BG_PANEL}" strokeColor="{border}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=8, bottom=8}}" margins="{{bottom=10}}">
                            <label align="top" height="22" text="ARMAMENTO &amp; MANOBRAS EQUIPADAS (NOME • ATRIB • HAB • DIF • DANO • TIPO • MUNIÇÃO)" fontColor="{accent}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
{chr(10).join(weapon_rows)}
                        </rectangle>

{health_track_xml(accent, border, is_vampire=is_vampire)}
                    </layout>
                </scrollBox>
            </tab>"""


def build_clan_weakness_controls_xml(clan: dict, accent: str) -> str:
    cid = clan["id"]
    if cid == "brujah":
        return f"""                            <layout align="top" height="32" margins="{{top=8}}">
                                <button name="btnBrujahEncerrarFrenesi" align="left" width="245" text="Encerrar Frenesi Ativo (-1 FdV)" fontSize="11" fontStyle="bold" margins="{{right=10}}">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.endBrujahFrenzy(sheet) end</event>
                                </button>
                                <label align="client" text="Frenesi Brujah: +2 dif automática (máx. 10) e FdV preventiva bloqueada (V20, p. 49)." fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                            </layout>"""
    if cid == "gangrel":
        soc_items = lua_str_list(["Carisma", "Manipulação", "Aparência"])
        soc_vals = lua_str_list(["attr_carisma", "attr_manipulacao", "attr_aparencia"])
        return f"""                            <layout align="top" height="30" margins="{{top=8}}">
                                <label align="left" width="95" text="Traços Animais:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtGangrelTracosQtd" align="left" width="38" field="gangrel_tracos_qtd" type="number" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{right=8}}"/>
                                <label align="left" width="95" text="Atrib. Penaliz.:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <comboBox name="cmbGangrelAttrPenalizado" align="left" width="125" field="gangrel_attr_penalizado" items="{soc_items}" values="{soc_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=8}}"/>
                                <button name="btnGangrelRegistrarFrenesi" align="left" width="235" text="Registrar Frenesi Gangrel (+1 Traço)" fontSize="10" fontStyle="bold">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.recordGangrelFrenzy(sheet) end</event>
                                </button>
                            </layout>
                            <layout align="top" height="28" margins="{{top=4}}">
                                <edit name="edtGangrelTracosLista" align="client" field="gangrel_tracos_lista" textPrompt="Características animais adquiridas (a cada 5 traços, -1 permanente no Atributo Social escolhido)..." fontColor="{TEXT_MAIN}" fontSize="10"/>
                            </layout>"""
    if cid == "malkavian":
        return f"""                            <layout align="top" height="30" margins="{{top=8}}">
                                <label align="left" width="85" text="Perturbação:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtMalkavPerturbacao" align="left" width="235" field="malkav_perturbacao" textPrompt="Perturbação incurável obrigatória..." fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=8}}"/>
                                <checkBox name="chkMalkavSuprimidaCena" align="left" width="145" field="malkav_suprimida_cena" text="Suprimida na Cena" fontColor="{TEXT_GOLD}" fontSize="10" margins="{{right=8}}"/>
                                <button name="btnMalkavSuprimir" align="left" width="245" text="Suprimir Perturbação na Cena (-1 FdV)" fontSize="10" fontStyle="bold">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.suppressMalkavianDerangement(sheet) end</event>
                                </button>
                            </layout>"""
    if cid == "nosferatu":
        return f"""                            <layout align="top" height="32" margins="{{top=8}}">
                                <button name="btnNosferatuMascara" align="left" width="265" text="Alternar Máscara das Mil Faces (Ofuscação 3)" fontSize="10" fontStyle="bold" margins="{{right=10}}">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.activateDisciplinePower(sheet, 'obfuscate', 'obf_3') end</event>
                                </button>
                                <label align="client" text="Aparência permanentemente 0: falha automática sem Máscara das Mil Faces ativa (V20, p. 61)." fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                            </layout>"""
    if cid == "toreador":
        return f"""                            <layout align="top" height="30" margins="{{top=8}}">
                                <label align="left" width="82" text="Foco de Arte:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtToreadorFocoArte" align="left" width="225" field="toreador_foco_arte" textPrompt="Arte / Beleza que desperta fascínio..." fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=8}}"/>
                                <checkBox name="chkToreadorFascinadoCena" align="left" width="145" field="toreador_fascinado_cena" text="Fascinado na Cena" fontColor="{TEXT_ALERT}" fontSize="10" margins="{{right=8}}"/>
                                <button name="btnToreadorTestarFascinio" align="left" width="235" text="Testar Fascínio Estético (Dif 6)" fontSize="10" fontStyle="bold">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.rollToreadorFascination(sheet) end</event>
                                </button>
                            </layout>"""
    if cid == "tremere":
        return f"""                            <layout align="top" height="30" margins="{{top=8}}">
                                <label align="left" width="65" text="Regente:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtTremereRegenteNome" align="left" width="155" field="tremere_regente_nome" textPrompt="Domitor / Regente" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=8}}"/>
                                <label align="left" width="44" text="Goles:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtTremereLacoGoles" align="left" width="36" field="tremere_laco_goles" type="number" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{right=8}}"/>
                                <button name="btnTremereRegistrarGole" align="left" width="195" text="Registrar Gole de Vitae (+1)" fontSize="10" fontStyle="bold" margins="{{right=8}}"/>
                                <label align="client" field="tremere_laco_status" fontColor="{TEXT_ALERT}" fontSize="10" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            </layout>""".replace(
            '<button name="btnTremereRegistrarGole" align="left" width="195" text="Registrar Gole de Vitae (+1)" fontSize="10" fontStyle="bold" margins="{right=8}"/>',
            '<button name="btnTremereRegistrarGole" align="left" width="195" text="Registrar Gole de Vitae (+1)" fontSize="10" fontStyle="bold" margins="{right=8}"><event name="onClick">if sheet ~= nil then V20Bridge.recordTremereDrink(sheet) end</event></button>',
        )
    if cid == "ventrue":
        return f"""                            <layout align="top" height="30" margins="{{top=8}}">
                                <label align="left" width="105" text="Presa Exclusiva:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtVentruePresaRestrita" align="left" width="295" field="ventrue_presa_restrita" textPrompt="Tipo exclusivo de recipiente mortal (obrigatório)..." fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=10}}"/>
                                <checkBox name="chkVentruePresaCompativel" align="left" width="235" field="ventrue_presa_compativel" text="Presa Compatível na Caça Atual" fontColor="{TEXT_GOLD}" fontSize="10"/>
                            </layout>"""
    if cid == "assamite":
        modo_it = lua_str_list(["Ur-Shulgi (Letal + Vitae + Vício)", "Tremere Clássica (Letal, 0 Vitae)"])
        modo_vl = lua_str_list(["ur_shulgi", "tremere_classica"])
        return f"""                            <layout align="top" height="30" margins="{{top=8}}">
                                <comboBox name="cmbAssamitaMaldicaoModo" align="left" width="235" field="assamita_maldicao_modo" items="{modo_it}" values="{modo_vl}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=8}}"/>
                                <label align="left" width="68" text="Qtd Vitae:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtAssamitaVitaeQtd" align="left" width="36" field="assamita_vitae_qtd" type="number" fontColor="{TEXT_GOLD}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=8}}"/>
                                <checkBox name="chkAssamitaVicioAtivo" align="left" width="105" field="assamita_vicio_ativo" text="Vício Ativo" fontColor="{TEXT_ALERT}" fontSize="10" margins="{{right=8}}"/>
                                <button name="btnAssamitaIngerirVitae" align="left" width="175" text="Ingerir Vitae Cainita" fontSize="10" fontStyle="bold">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.ingestAssamiteVitae(sheet, nil) end</event>
                                </button>
                            </layout>"""
    if cid == "setite":
        return f"""                            <layout align="top" height="30" margins="{{top=8}}">
                                <checkBox name="chkSetitaLuzForte" align="left" width="280" field="setita_luz_forte" text="Sob Luz Forte (-1 dado em todas as paradas)" fontColor="{TEXT_ALERT}" fontSize="11" fontStyle="bold" margins="{{right=10}}"/>
                                <label align="client" text="Luz Solar (Aba 5) soma automaticamente +2 níveis de dano Agravado (V20, p. 51)." fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                            </layout>"""
    if cid == "giovanni":
        return f"""                            <layout align="top" height="30" margins="{{top=8}}">
                                <label align="left" width="125" text="Vitae Drenada (N):" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtGiovanniBeijoPontos" align="left" width="40" field="giovanni_beijo_pontos" type="number" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{right=10}}"/>
                                <button name="btnGiovanniBeijo" align="left" width="215" text="Aplicar O Beijo Doloroso" fontSize="10" fontStyle="bold" margins="{{right=10}}">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.applyGiovanniKiss(sheet, nil) end</event>
                                </button>
                                <label align="client" text="Causa 2xN níveis Letais no recipiente mortal (morte/choque em >= 7)." fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                            </layout>"""
    if cid == "lasombra":
        return f"""                            <layout align="top" height="30" margins="{{top=8}}">
                                <checkBox name="chkLasombraEspelhos" align="left" width="330" field="lasombra_vigiado_espelhos" text="Vigiado por Espelhos/Câmeras (+1 dif Social/Furtiv.)" fontColor="{TEXT_GOLD}" fontSize="10" fontStyle="bold" margins="{{right=10}}"/>
                                <label align="client" text="Luz Solar (Aba 5) soma automaticamente +1 nível Agravado (V20, p. 57)." fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                            </layout>"""
    if cid == "ravnos":
        return f"""                            <layout align="top" height="30" margins="{{top=8}}">
                                <label align="left" width="88" text="Vício Ravnos:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtRavnosVicio" align="left" width="235" field="ravnos_vicio_descricao" textPrompt="Vício específico obrigatório..." fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=8}}"/>
                                <checkBox name="chkRavnosCompulsaoAtiva" align="left" width="135" field="ravnos_compulsao_ativa" text="Compulsão Ativa" fontColor="{TEXT_ALERT}" fontSize="10" margins="{{right=8}}"/>
                                <button name="btnRavnosTestarVicio" align="left" width="235" text="Resistir ao Vício Ravnos (Dif 6)" fontSize="10" fontStyle="bold">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.rollRavnosVice(sheet) end</event>
                                </button>
                            </layout>"""
    if cid == "tzimisce":
        return f"""                            <layout align="top" height="30" margins="{{top=8}}">
                                <label align="left" width="82" text="Terra Natal:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtTzimisceOrigemTerra" align="left" width="185" field="tzimisce_origem_terra" textPrompt="Origem dos 2 punhados de terra..." fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=8}}"/>
                                <label align="left" width="95" text="Dias s/ Terra:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtTzimisceDiasSemTerra" align="left" width="38" field="tzimisce_dias_sem_terra" type="number" fontColor="{TEXT_ALERT}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{right=8}}"/>
                                <button name="btnTzimisceRepousarTerra" align="left" width="265" text="Repousar com 2 Punhados de Terra Natal" fontSize="10" fontStyle="bold">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.resetTzimisceSoil(sheet) end</event>
                                </button>
                            </layout>"""
    # caitiff
    return f"""                            <layout align="top" height="30" margins="{{top=8}}">
                                <checkBox name="chkCaitiffEstigmaAtivo" align="left" width="340" field="caitiff_estigma_ativo" text="Estigma Social Caitiff Ativo (+2 dif Social c/ Membros)" fontColor="{TEXT_ALERT}" fontSize="10" fontStyle="bold" margins="{{right=10}}"/>
                                <label align="client" text="Sem disciplinas de clã: qualquer disciplina evolui por Atual x 6 XP (10 XP nova)." fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                            </layout>"""


def build_tab6_morality(clan: dict, accent: str) -> str:
    v1_items = lua_str_list(["Consciência", "Convicção"])
    v1_vals = lua_str_list(["consciencia", "conviccao"])
    v2_items = lua_str_list(["Autocontrole", "Instinto"])
    v2_vals = lua_str_list(["autocontrole", "instinto"])
    path_items = lua_str_list([n for _, n in MORALITY_PATHS])
    path_vals = lua_str_list([i for i, _ in MORALITY_PATHS])
    weakness_ctrls = build_clan_weakness_controls_xml(clan, accent)

    return f"""            <tab name="tabMoralidade" title="6. Moralidade &amp; Besta">
                <scrollBox align="client" padding="{{left=10, right=10, top=10, bottom=10}}">
                    <layout align="top" height="600">
                        <rectangle align="top" height="165" color="{BG_PANEL}" strokeColor="{BORDER_VAMP}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=10, bottom=10}}" margins="{{bottom=10}}">
                            <label align="top" height="22" text="VIRTUDES, TRILHA DE MORALIDADE &amp; MODIFICADOR DE AURA" fontColor="{accent}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            <layout align="top" height="28" margins="{{top=6}}">
                                <comboBox name="cmbVirtude1Tipo" align="left" width="135" field="virtude1_tipo" items="{v1_items}" values="{v1_vals}" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=6}}"/>
                                <edit name="edtVirtude1Val" align="left" width="38" field="virtude1_val" type="number" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{right=14}}"/>
                                <comboBox name="cmbVirtude2Tipo" align="left" width="135" field="virtude2_tipo" items="{v2_items}" values="{v2_vals}" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=6}}"/>
                                <edit name="edtVirtude2Val" align="left" width="38" field="virtude2_val" type="number" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{right=14}}"/>
                                <label align="left" width="68" text="Coragem:" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtVirtude3Val" align="left" width="38" field="virtude3_val" type="number" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("center")}"/>
                            </layout>
                            <layout align="top" height="28" margins="{{top=8}}">
                                <label align="left" width="78" text="Moralidade:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <comboBox name="cmbMoralidadeTipo" align="left" width="215" field="moralidade_tipo" items="{path_items}" values="{path_vals}" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=8}}"/>
                                <edit name="edtMoralidadeVal" align="left" width="42" field="moralidade_val" type="number" fontColor="{TEXT_GOLD}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{right=12}}"/>
                                <label align="left" width="44" text="Aura:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <label align="client" field="aura_resumo" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            </layout>
                            <layout align="top" height="28" margins="{{top=8}}">
                                <label align="left" width="135" text="FdV Permanente:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtFdvPerm" align="left" width="42" field="fdv_perm" type="number" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{right=14}}"/>
                                <checkBox align="left" width="210" field="em_frenesi" text="Em Frenesi Ativo (Ignora Ferim.)" fontColor="{TEXT_ALERT}" fontSize="11" fontStyle="bold"/>
                            </layout>
                        </rectangle>

                        <rectangle align="top" height="265" color="{BG_PANEL}" strokeColor="{accent}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=10, bottom=10}}">
                            <label align="top" height="22" text="A BESTA INTERIOR — FRENESI, RÖTSCHRECK &amp; FRAQUEZA {xml_esc(clan['name'].upper())}" fontColor="{accent}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            <label align="top" height="38" text="{xml_esc(clan['weaknessSummary'])}" wordWrap="true" fontColor="{TEXT_MAIN}" fontSize="10" horzTextAlign="{assert_align("leading")}" margins="{{top=4}}"/>
                            <layout align="top" height="32" margins="{{top=8}}">
                                <label align="left" width="95" text="Dif. Estímulo:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit align="left" width="40" field="frenesi_dif" type="number" fontColor="{TEXT_GOLD}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=8}}"/>
                                <button align="left" width="155" text="Testar Frenesi" fontSize="11" fontStyle="bold" margins="{{right=14}}">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.rollFrenzy(sheet, nil) end</event>
                                </button>
                                <label align="left" width="90" text="Dif. Fogo/Sol:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit align="left" width="40" field="rotschreck_dif" type="number" fontColor="{TEXT_GOLD}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=8}}"/>
                                <button align="left" width="155" text="Testar Rötschreck" fontSize="11" fontStyle="bold">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.rollRotschreck(sheet, nil) end</event>
                                </button>
                            </layout>
                            <layout align="top" height="32" margins="{{top=8}}">
                                <button align="left" width="245" text="Testar Degeneração (Consc./Conv. Dif 8)" fontSize="11">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.rollDegeneration(sheet) end</event>
                                </button>
                            </layout>
{weakness_ctrls}
                        </rectangle>
                    </layout>
                </scrollBox>
            </tab>"""


def build_tab7_xp(accent: str, border: str = BORDER_VAMP, extra_top_card: str = "", is_vampire: bool = True) -> str:
    xp_tipo_items = lua_str_list([
        "Automático (pelo Campo)",
        "Atributo (Atual x4)",
        "Habilidade (Nova 3 / Atual x2)",
        "Disciplina (Nova 10 / Clã x5 / Fora x7)",
        "Linha Secundária (Nova 7 / Atual x4)",
        "Virtude (Atual x2)",
        "Moralidade (Atual x2)",
        "Força de Vontade (Atual x1)",
    ])
    xp_tipo_vals = lua_str_list([
        "auto",
        "attribute",
        "ability",
        "discipline",
        "secondary_path",
        "virtue",
        "morality",
        "willpower",
    ])
    xp_campo_items, xp_campo_vals = all_xp_upgradable_field_options(is_vampire=is_vampire)
    xp_cat_items = lua_str_list(["Automático (pela Ficha)", "De Clã (x5)", "Caitiff (x6)", "Fora do Clã (x7)"])
    xp_cat_vals = lua_str_list(["auto", "cla", "caitiff", "fora_cla"])

    return f"""            <tab name="tabExperiencia" title="7. Experiência &amp; Narrador">
                <scrollBox align="client" padding="{{left=10, right=10, top=10, bottom=10}}">
                    <layout align="top" height="760">
{extra_top_card}
                        <rectangle align="top" height="190" color="{BG_PANEL}" strokeColor="{border}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=10, bottom=10}}" margins="{{bottom=10}}">
                            <label align="top" height="22" text="EVOLUÇÃO POR EXPERIÊNCIA (XP) &amp; FILA DE APROVAÇÃO DO NARRADOR" fontColor="{accent}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            <layout align="top" height="28" margins="{{top=4}}">
                                <label align="left" width="68" text="XP Total:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtXpTotal" align="left" width="48" field="xp_total" type="number" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{right=10}}"/>
                                <label align="left" width="68" text="XP Gasto:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <edit name="edtXpGasto" align="left" width="48" field="xp_gasto" type="number" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=10}}"/>
                                <label align="left" width="95" text="XP Disponível:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                                <label align="left" width="48" field="xp_disponivel" fontColor="{TEXT_GOLD}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{right=14}}"/>
                                <checkBox name="chkXpExigeAprovacao" align="left" width="185" field="xp_exige_aprovacao" text="Exigir Aprovação Mestre" fontColor="{TEXT_MAIN}" fontSize="10"/>
                                <checkBox name="chkNarradorOverride" align="left" width="165" field="narrador_override" text="Override do Narrador" fontColor="{TEXT_ALERT}" fontSize="10"/>
                            </layout>
                            <layout align="top" height="28" margins="{{top=6}}">
                                <comboBox name="cmbXpLojaTipo" align="left" width="195" field="xp_loja_tipo" items="{xp_tipo_items}" values="{xp_tipo_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=6}}"/>
                                <comboBox name="cmbXpLojaCampo" align="left" width="175" field="xp_loja_campo" items="{xp_campo_items}" values="{xp_campo_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=6}}"/>
                                <comboBox name="cmbXpLojaCatCusto" align="left" width="140" field="xp_loja_cat_custo" items="{xp_cat_items}" values="{xp_cat_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=6}}"/>
                                <edit name="edtXpLojaDescricao" align="client" field="xp_loja_descricao" textPrompt="Rótulo p/ Auditoria" fontColor="{TEXT_MUTED}" fontSize="10" margins="{{right=6}}"/>
                                <button name="btnSolicitarXP" align="right" width="135" text="Solicitar Evolução" fontSize="10" fontStyle="bold">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.submitOrApproveXP(sheet, 'submit', nil) end</event>
                                </button>
                            </layout>
                            <layout align="top" height="30" margins="{{top=8}}">
                                <label align="left" width="75" text="Pendente:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <label align="left" width="85" field="xp_pendente_status" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                                <label align="client" field="xp_pendente_desc" fontColor="{TEXT_MAIN}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <button name="btnRecusarXP" align="right" width="115" text="Recusar (Mestre)" fontSize="10" margins="{{left=6}}">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.submitOrApproveXP(sheet, 'reject', nil) end</event>
                                </button>
                                <button name="btnAprovarXP" align="right" width="115" text="Aprovar (Mestre)" fontSize="10" fontStyle="bold">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.submitOrApproveXP(sheet, 'approve', nil) end</event>
                                </button>
                            </layout>
                        </rectangle>

                        <rectangle align="top" height="230" color="{BG_PANEL}" strokeColor="{border}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=10, bottom=10}}" margins="{{bottom=10}}">
                            <label align="top" height="22" text="HISTÓRICO AUDITÁVEL IMUTÁVEL DE XP E ALTERAÇÕES DO NARRADOR" fontColor="{accent}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            <textEditor align="client" field="auditoria_xp_log" readOnly="true" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{top=4}}"/>
                        </rectangle>

                        <rectangle align="top" height="170" color="{BG_PANEL}" strokeColor="{border}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=10, bottom=10}}">
                            <label align="top" height="22" text="DIÁRIO DA CRÔNICA, LAÇOS DE SANGUE &amp; ANOTAÇÕES" fontColor="{accent}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            <textEditor align="client" field="notas_cronica" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{top=4}}"/>
                        </rectangle>
                    </layout>
                </scrollBox>
            </tab>"""


def build_tab8_blood_magic(clan: dict, accent: str) -> str:
    bm_visible = "true" if clan["id"] in ("tremere", "giovanni") else "false"
    thau_items = lua_str_list([n for _, n in THAUMATURGY_PATHS_LIST])
    thau_vals = lua_str_list([i for i, _ in THAUMATURGY_PATHS_LIST])
    necro_items = lua_str_list([n for _, n in NECROMANCY_PATHS_LIST])
    necro_vals = lua_str_list([i for i, _ in NECROMANCY_PATHS_LIST])
    sec_path_items = lua_str_list([n for _, n in ALL_BLOOD_MAGIC_PATHS_LIST])
    sec_path_vals = lua_str_list([i for i, _ in ALL_BLOOD_MAGIC_PATHS_LIST])
    trad_items = lua_str_list(["Taumaturgia", "Necromancia"])
    trad_vals = lua_str_list(["thaumaturgy", "necromancy"])
    lvl_items = lua_str_list(["Poder Nv 1", "Poder Nv 2", "Poder Nv 3", "Poder Nv 4", "Poder Nv 5"])
    lvl_vals = lua_str_list(["1", "2", "3", "4", "5"])
    rit_items = lua_str_list([n for _, n in RITUALS_LIST])
    rit_vals = lua_str_list([i for i, _ in RITUALS_LIST])

    sec_cards = []
    for i in range(1, 5):
        sec_cards.append(
            f"""                        <rectangle align="top" height="60" color="{BG_PANEL}" strokeColor="{BORDER_VAMP}" strokeSize="1" xradius="5" yradius="5" padding="{{left=10, right=10, top=6, bottom=6}}" margins="{{bottom=6}}">
                            <layout align="top" height="26">
                                <label align="left" width="56" text="SEC #{i}" fontColor="{accent}" fontSize="10" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                                <comboBox name="cmbBmSecDisc{i}" align="left" width="115" field="bm_sec{i}_disc" items="{trad_items}" values="{trad_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=6}}"/>
                                <comboBox name="cmbBmSecPathId{i}" align="left" width="235" field="bm_sec{i}_path_id" items="{sec_path_items}" values="{sec_path_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=6}}"/>
                                <label align="left" width="38" text="Nível:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("trailing")}" margins="{{right=4}}"/>
                                <edit name="edtBmSecNivel{i}" align="left" width="36" field="bm_sec{i}_nivel" type="number" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{right=6}}"/>
                                <comboBox name="cmbBmSecPwrLvl{i}" align="left" width="108" field="bm_sec{i}_pwr_lvl" items="{lvl_items}" values="{lvl_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=6}}"/>
                                <button name="btnBmSecAtivar{i}" align="right" width="138" text="Ativar Secundária" fontSize="10" fontStyle="bold">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.activateSecondaryBloodMagic(sheet, {i}, nil) end</event>
                                </button>
                            </layout>
                            <label align="client" field="bm_sec{i}_resumo" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}" margins="{{top=2}}"/>
                        </rectangle>"""
        )

    return f"""            <tab name="tabMagiaSangue" title="8. Magia do Sangue &amp; Rituais" visible="{bm_visible}">
                <scrollBox align="client" padding="{{left=10, right=10, top=10, bottom=10}}">
                    <layout align="top" height="720">
                        <rectangle align="top" height="165" color="{BG_PANEL}" strokeColor="{accent}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=8, bottom=8}}" margins="{{bottom=10}}">
                            <label align="top" height="22" text="LINHAS PRIMÁRIAS — TAUMATURGIA &amp; NECROMANCIA (SINCRONIZADAS COM A ABA 3)" fontColor="{accent}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            <layout align="top" height="28" margins="{{top=4}}">
                                <label align="left" width="125" text="Prim. Taumaturgia:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <comboBox name="cmbBmThauPrimId" align="left" width="215" field="bm_thau_prim_id" items="{thau_items}" values="{thau_vals}" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=8}}"/>
                                <label align="left" width="42" text="Nível:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("trailing")}" margins="{{right=4}}"/>
                                <label align="left" width="28" field="bm_thau_prim_nivel" fontColor="{TEXT_GOLD}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{right=8}}"/>
                                <comboBox name="cmbBmThauPrimPwrLvl" align="left" width="115" field="bm_thau_prim_pwr_lvl" items="{lvl_items}" values="{lvl_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=8}}"/>
                                <button name="btnBmThauPrimAtivar" align="right" width="190" text="Ativar Linha Taumaturgia" fontSize="10" fontStyle="bold">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.activatePrimaryBloodMagic(sheet, 'thaumaturgy', nil) end</event>
                                </button>
                            </layout>
                            <label align="top" height="22" field="bm_thau_prim_resumo" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}" margins="{{top=2}}"/>
                            <layout align="top" height="28" margins="{{top=6}}">
                                <label align="left" width="125" text="Prim. Necromancia:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>
                                <comboBox name="cmbBmNecroPrimId" align="left" width="215" field="bm_necro_prim_id" items="{necro_items}" values="{necro_vals}" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=8}}"/>
                                <label align="left" width="42" text="Nível:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("trailing")}" margins="{{right=4}}"/>
                                <label align="left" width="28" field="bm_necro_prim_nivel" fontColor="{TEXT_GOLD}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{right=8}}"/>
                                <comboBox name="cmbBmNecroPrimPwrLvl" align="left" width="115" field="bm_necro_prim_pwr_lvl" items="{lvl_items}" values="{lvl_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=8}}"/>
                                <button name="btnBmNecroPrimAtivar" align="right" width="190" text="Ativar Linha Necromancia" fontSize="10" fontStyle="bold">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.activatePrimaryBloodMagic(sheet, 'necromancy', nil) end</event>
                                </button>
                            </layout>
                            <label align="client" field="bm_necro_prim_resumo" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}" margins="{{top=2}}"/>
                        </rectangle>

                        <label align="top" height="20" text="LINHAS SECUNDÁRIAS V20 (EXIGE PRIMÁRIA &gt;= 2 • NOVA: 7 XP • EVOLUÇÃO: ATUAL x4 XP NA ABA 7)" fontColor="{accent}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}" margins="{{bottom=4}}"/>
{chr(10).join(sec_cards)}

                        <rectangle align="top" height="165" color="{BG_PANEL}" strokeColor="{BORDER_VAMP}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=8, bottom=8}}" margins="{{top=6}}">
                            <label align="top" height="22" text="GRIMÓRIO DE 20 RITUAIS CLÁSSICOS V20 &amp; CONJURAÇÃO CUSTOMIZADA (INTELIGÊNCIA + OCULTISMO)" fontColor="{accent}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            <layout align="top" height="28" margins="{{top=4}}">
                                <comboBox name="cmbBmRitualId" align="left" width="455" field="bm_ritual_id" items="{rit_items}" values="{rit_vals}" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=8}}"/>
                                <button name="btnBmConjurarRitualOficial" align="right" width="195" text="Conjurar Ritual Oficial" fontSize="10" fontStyle="bold">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.castCatalogRitual(sheet, nil) end</event>
                                </button>
                            </layout>
                            <label align="top" height="24" field="bm_ritual_catalogo_resumo" fontColor="{TEXT_GOLD}" fontSize="10" horzTextAlign="{assert_align("leading")}" margins="{{top=2}}"/>
                            <layout align="top" height="28" margins="{{top=8}}">
                                <edit name="edtRitualCustomNome" align="left" width="185" field="ritual_custom_nome" textPrompt="Nome do Ritual Customizado" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=6}}"/>
                                <comboBox name="cmbRitualCustomTrad" align="left" width="115" field="ritual_custom_trad" items="{trad_items}" values="{trad_vals}" fontColor="{TEXT_MAIN}" fontSize="10" margins="{{right=6}}"/>
                                <label align="left" width="28" text="Nv:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("trailing")}" margins="{{right=3}}"/>
                                <edit name="edtRitualCustomNivel" align="left" width="32" field="ritual_custom_nivel" type="number" fontColor="{TEXT_GOLD}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=6}}"/>
                                <label align="left" width="46" text="Sangue:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("trailing")}" margins="{{right=3}}"/>
                                <edit name="edtRitualCustomSangue" align="left" width="32" field="ritual_custom_sangue" type="number" fontColor="{TEXT_ALERT}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=6}}"/>
                                <label align="left" width="30" text="FdV:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("trailing")}" margins="{{right=3}}"/>
                                <edit name="edtRitualCustomFdv" align="left" width="32" field="ritual_custom_fdv" type="number" fontColor="{TEXT_GOLD}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=6}}"/>
                                <label align="left" width="26" text="Dif:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("trailing")}" margins="{{right=3}}"/>
                                <edit name="edtRitualCustomDif" align="left" width="32" field="ritual_custom_dif" type="number" fontColor="{TEXT_GOLD}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=6}}"/>
                                <button name="btnBmConjurarRitualCustom" align="right" width="125" text="Conjurar Custom" fontSize="10" fontStyle="bold">
                                    <event name="onClick">if sheet ~= nil then V20Bridge.castCustomRitual(sheet) end</event>
                                </button>
                            </layout>
                        </rectangle>
                    </layout>
                </scrollBox>
            </tab>"""


def generate_vampire_lfm(clan_id: str) -> str:
    key = clan_id.lower().strip()
    if key not in CLANS:
        raise ValueError(f"Clã desconhecido: {clan_id}")
    clan = CLANS[key]
    accent = clan["accentColor"]
    form_name = clan["formName"]
    data_type = clan["dataType"]
    title = f"Vampiro V20 - {clan['name']}"

    in_clan = clan["disciplines"]
    d1 = in_clan[0] if len(in_clan) > 0 else ""
    d2 = in_clan[1] if len(in_clan) > 1 else ""
    d3 = in_clan[2] if len(in_clan) > 2 else ""
    slot13_cat = "caitiff" if clan["id"] == "caitiff" else "cla"
    slot49_cat = "caitiff" if clan["id"] == "caitiff" else "fora_cla"
    default_sec_trad = "necromancy" if clan["id"] == "giovanni" else "thaumaturgy"
    default_rit_id = "necro_rit_1_call_hungry" if clan["id"] == "giovanni" else "thau_rit_1_sacred_haven"

    defaults: list[tuple[str, str]] = [
        ("nome", f"Neófito {clan['name']}"),
        ("cla_id", clan["id"]),
        ("is_vampire", "true"),
        ("modo_ficha", "criacao"),
        ("geracao_base", "13"),
        ("geracao", "13"),
        ("sangue_atual", "10"),
        ("sangue_max", "10"),
        ("sangue_usavel_max", "10"),
        ("sangue_por_turno", "1"),
        ("sangue_gasto_turno", "0"),
        ("fdv_perm", "5"),
        ("fdv_temp", "5"),
        ("virtude1_tipo", "consciencia"),
        ("virtude1_val", "2"),
        ("virtude2_tipo", "autocontrole"),
        ("virtude2_val", "2"),
        ("virtude3_val", "3"),
        ("moralidade_tipo", "humanidade"),
        ("moralidade_nome", "Humanidade"),
        ("moralidade_val", "7"),
        ("dano_contundente", "0"),
        ("dano_letal", "0"),
        ("dano_aggravado", "0"),
        ("dano_aplicar_qtd", "1"),
        ("dano_aplicar_tipo", "bashing"),
        ("dano_fonte_solar", "false"),
        ("cura_tipo", "bashing"),
        ("armadura_absorcao", "0"),
        ("tem_tamanho_grande", "false"),
        ("frenesi_dif", "6"),
        ("rotschreck_dif", "6"),
        ("em_frenesi", "false"),
        ("gangrel_tracos_qtd", "0"),
        ("gangrel_tracos_lista", ""),
        ("gangrel_attr_penalizado", "attr_carisma"),
        ("malkav_perturbacao", ""),
        ("malkav_suprimida_cena", "false"),
        ("toreador_foco_arte", ""),
        ("toreador_fascinado_cena", "false"),
        ("tremere_laco_goles", "0"),
        ("tremere_regente_nome", ""),
        ("tremere_laco_status", "Sem Laço (0/2 goles)"),
        ("ventrue_presa_restrita", ""),
        ("ventrue_presa_compativel", "true"),
        ("assamita_maldicao_modo", "ur_shulgi"),
        ("assamita_vitae_qtd", "1"),
        ("assamita_vicio_ativo", "false"),
        ("setita_luz_forte", "false"),
        ("giovanni_beijo_pontos", "1"),
        ("lasombra_vigiado_espelhos", "false"),
        ("ravnos_vicio_descricao", ""),
        ("ravnos_compulsao_ativa", "false"),
        ("tzimisce_origem_terra", ""),
        ("tzimisce_dias_sem_terra", "0"),
        ("caitiff_estigma_ativo", "true"),
        ("bm_thau_prim_id", "path_of_blood"),
        ("bm_thau_prim_nivel", "1" if "thaumaturgy" in in_clan else "0"),
        ("bm_thau_prim_pwr_lvl", "1"),
        ("bm_necro_prim_id", "sepulchre_path"),
        ("bm_necro_prim_nivel", "1" if "necromancy" in in_clan else "0"),
        ("bm_necro_prim_pwr_lvl", "1"),
        ("bm_ritual_id", default_rit_id),
        ("ritual_custom_nome", ""),
        ("ritual_custom_trad", default_sec_trad),
        ("ritual_custom_nivel", "1"),
        ("ritual_custom_sangue", "0"),
        ("ritual_custom_fdv", "0"),
        ("ritual_custom_dif", "4"),
        ("roll_attr_id", "attr_destreza"),
        ("roll_hab_id", "hab_briga"),
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
        ("xp_loja_campo", "hab_briga"),
        ("xp_loja_cat_custo", "auto"),
        ("xp_pendente_status", "nenhum"),
        ("disc_slot1_id", d1),
        ("disc_slot1_nivel", "1" if d1 else "0"),
        ("disc_slot1_cat", slot13_cat),
        ("disc_slot1_pwr_lvl", "1"),
        ("disc_slot2_id", d2),
        ("disc_slot2_nivel", "1" if d2 else "0"),
        ("disc_slot2_cat", slot13_cat),
        ("disc_slot2_pwr_lvl", "1"),
        ("disc_slot3_id", d3),
        ("disc_slot3_nivel", "1" if d3 else "0"),
        ("disc_slot3_cat", slot13_cat),
        ("disc_slot3_pwr_lvl", "1"),
    ]

    for i in range(4, 10):
        defaults.extend([
            (f"disc_slot{i}_id", ""),
            (f"disc_slot{i}_nivel", "0"),
            (f"disc_slot{i}_cat", slot49_cat),
            (f"disc_slot{i}_pwr_lvl", "1"),
        ])

    for i in range(1, 5):
        defaults.extend([
            (f"bm_sec{i}_disc", default_sec_trad),
            (f"bm_sec{i}_path_id", ""),
            (f"bm_sec{i}_nivel", "0"),
            (f"bm_sec{i}_pwr_lvl", "1"),
        ])

    for _, rows in ATTRIBUTES_BY_COL:
        for aid, _, _ in rows:
            val = "0" if (clan["appearanceZero"] and aid == "attr_aparencia") else "1"
            defaults.append((aid, val))

    for _, rows in ABILITIES_BY_COL:
        for hid, _ in rows:
            defaults.append((hid, "0"))

    for bid, _, _, _ in BACKGROUNDS_LIST:
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
        on_change_lua="if sheet ~= nil and V20Bridge ~= nil then V20Bridge.syncDerivedFields(sheet); atualizarPermissoesModo(self); end",
        chunk_size=32,
    )

    perms_lua = build_mode_permissions_lua(is_vampire=True)

    xml_out = f"""<?xml version="1.0" encoding="UTF-8"?>
<form name="{form_name}" formType="sheetTemplate" dataType="{data_type}" title="{xml_esc(title)}" align="client" theme="dark">

    <script>
        <![CDATA[
        local V20Bridge = _G.V20Bridge or require("Adapter.firecast_bridge")

{perms_lua}
        ]]>
    </script>

    <rectangle align="client" color="{BG_MAIN}">
{header_bar_xml(accent, BORDER_VAMP, f"CLÃ {clan['name'].upper()} (V20)", is_vampire=True)}
{dice_roller_footer_xml(accent, BORDER_VAMP)}

        <tabControl name="pgcPrincipal" align="client" margins="{{left=6, right=6, top=6, bottom=6}}">
{build_tab1_creation(clan, accent)}
{build_tab2_traits(clan, accent, is_vampire=True, border=BORDER_VAMP)}
{build_tab3_disciplines(accent)}
{build_tab4_backgrounds(accent, border=BORDER_VAMP, is_vampire=True)}
{build_tab5_combat(accent, border=BORDER_VAMP, is_vampire=True)}
{build_tab6_morality(clan, accent)}
{build_tab7_xp(accent, border=BORDER_VAMP, is_vampire=True)}
{build_tab8_blood_magic(clan, accent)}
{suite_credits_tab_xml("9. Sobre", accent, BORDER_VAMP, f"Clã {clan['name']} ({data_type})")}
        </tabControl>
    </rectangle>

{datalinks}
    <event name="OnShow">if _G.V20AutoUpdater ~= nil then _G.V20AutoUpdater.checkOnOpen(self) end</event>
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
    parser = argparse.ArgumentParser(description="Gera ficha vampírica LFM parametrizada por clã para o Firecast SDK 3.7b.")
    parser.add_argument("--clan", default="brujah", help="Identificador do clã V20 (ex.: brujah).")
    parser.add_argument("--all-clans", action="store_true", help="Gera os 14 modelos vampíricos de uma só vez em Sheets/.")
    parser.add_argument("--out", default="", help="Caminho opcional de saída .lfm (quando --clan único).")
    args = parser.parse_args()

    if args.all_clans:
        out_dir = os.path.join(ROOT, "Sheets")
        os.makedirs(out_dir, exist_ok=True)
        for cid in CLAN_ORDER:
            clan = CLANS[cid]
            xml_content = generate_vampire_lfm(cid)
            out_path = os.path.join(out_dir, f"{clan['formName']}.lfm")
            _write_if_changed(out_path, xml_content)
        return

    clan = CLANS[args.clan.lower().strip()]
    xml_content = generate_vampire_lfm(args.clan)
    out_path = args.out or os.path.join(ROOT, "Sheets", f"{clan['formName']}.lfm")
    _write_if_changed(out_path, xml_content)


if __name__ == "__main__":
    main()
