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
    ATTRIBUTES_BY_COL,
    BACKGROUNDS_LIST,
    BG_MAIN,
    BG_PANEL,
    BORDER_VAMP,
    CLANS,
    DISCIPLINES_LIST,
    MERITS_FLAWS_OPTIONS,
    MORALITY_PATHS,
    TEXT_ALERT,
    TEXT_GOLD,
    TEXT_MAIN,
    TEXT_MUTED,
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
                    <layout align="top" height="640">
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

                        <rectangle align="top" height="170" color="{BG_PANEL}" strokeColor="{border}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=8, bottom=8}}" margins="{{bottom=10}}">
                            <label align="top" height="22" text="ARMAMENTO &amp; MANOBRAS EQUIPADAS (NOME • ATRIB • HAB • DIF • DANO • TIPO • MUNIÇÃO)" fontColor="{accent}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
{chr(10).join(weapon_rows)}
                        </rectangle>

{health_track_xml(accent, border, is_vampire=is_vampire)}
                    </layout>
                </scrollBox>
            </tab>"""


def build_tab6_morality(clan: dict, accent: str) -> str:
    v1_items = lua_str_list(["Consciência", "Convicção"])
    v1_vals = lua_str_list(["consciencia", "conviccao"])
    v2_items = lua_str_list(["Autocontrole", "Instinto"])
    v2_vals = lua_str_list(["autocontrole", "instinto"])
    path_items = lua_str_list([n for _, n in MORALITY_PATHS])
    path_vals = lua_str_list([i for i, _ in MORALITY_PATHS])

    return f"""            <tab name="tabMoralidade" title="6. Moralidade &amp; Besta">
                <scrollBox align="client" padding="{{left=10, right=10, top=10, bottom=10}}">
                    <layout align="top" height="520">
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

                        <rectangle align="top" height="190" color="{BG_PANEL}" strokeColor="{accent}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=10, bottom=10}}">
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
                        </rectangle>
                    </layout>
                </scrollBox>
            </tab>"""


def build_tab7_xp(accent: str, border: str = BORDER_VAMP, extra_top_card: str = "") -> str:
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
    xp_campo_items, xp_campo_vals = all_xp_upgradable_field_options()
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
        ("cura_tipo", "bashing"),
        ("armadura_absorcao", "0"),
        ("tem_tamanho_grande", "false"),
        ("frenesi_dif", "6"),
        ("rotschreck_dif", "6"),
        ("em_frenesi", "false"),
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
        ("disc_slot1_cat", "cla"),
        ("disc_slot1_pwr_lvl", "1"),
        ("disc_slot2_id", d2),
        ("disc_slot2_nivel", "1" if d2 else "0"),
        ("disc_slot2_cat", "cla"),
        ("disc_slot2_pwr_lvl", "1"),
        ("disc_slot3_id", d3),
        ("disc_slot3_nivel", "1" if d3 else "0"),
        ("disc_slot3_cat", "cla"),
        ("disc_slot3_pwr_lvl", "1"),
    ]

    for i in range(4, 10):
        defaults.extend([
            (f"disc_slot{i}_id", ""),
            (f"disc_slot{i}_nivel", "0"),
            (f"disc_slot{i}_cat", "fora_cla"),
            (f"disc_slot{i}_pwr_lvl", "1"),
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
{build_tab7_xp(accent, border=BORDER_VAMP)}
        </tabControl>
    </rectangle>

{datalinks}
</form>
"""
    validate_generated_lfm_xml(xml_out)
    return xml_out


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera ficha vampírica LFM parametrizada por clã para o Firecast SDK 3.7b.")
    parser.add_argument("--clan", default="brujah", help="Identificador do clã V20 (ex.: brujah).")
    parser.add_argument("--out", default="", help="Caminho opcional de saída .lfm.")
    args = parser.parse_args()

    clan = CLANS[args.clan.lower().strip()]
    xml_content = generate_vampire_lfm(args.clan)
    out_path = args.out or os.path.join(ROOT, "Sheets", f"{clan['formName']}.lfm")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(xml_content)
    print(f"[OK] Gerado {os.path.relpath(out_path, ROOT)}")


if __name__ == "__main__":
    main()
