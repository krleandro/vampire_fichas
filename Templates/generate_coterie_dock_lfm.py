#!/usr/bin/env python3
"""Gerador do painel acoplável tablesDock da Coterie & Iniciativa V20 (Sheets/frmV20CoterieDock.lfm)."""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from Templates.theme_gothic import (  # noqa: E402
    BG_CARD,
    BG_MAIN,
    BG_PANEL,
    BORDER_VAMP,
    TEXT_ALERT,
    TEXT_GOLD,
    TEXT_MAIN,
    TEXT_MUTED,
    assert_align,
    root_datalinks_xml,
    validate_generated_lfm_xml,
    xml_esc,
)

ACCENT_DOCK = "#9E1B24"


def _build_tab1_scene_and_initiative() -> str:
    init_rows_xml = "\n".join(
        f'                            <label name="lblInitRow{i}" align="top" height="20" text="{i}. —" '
        f'fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("leading")}" wordWrap="false"/>'
        for i in range(1, 11)
    )
    pub_rows_xml = "\n".join(
        f'                            <label name="lblPubSlot{i}" align="top" height="20" text="• —" '
        f'fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}" wordWrap="false"/>'
        for i in range(1, 9)
    )

    return f"""            <tab name="tabCenaIniciativa" title="1. Cena &amp; Iniciativa">
                <scrollBox align="client" padding="{{left=6, right=6, top=6, bottom=6}}">
                    <layout align="top" height="630">
                        <rectangle align="top" height="66" color="{BG_PANEL}" strokeColor="{ACCENT_DOCK}" strokeSize="1" xradius="6" yradius="6" padding="{{left=8, right=8, top=6, bottom=6}}" margins="{{bottom=6}}">
                            <layout align="top" height="24">
                                <label name="lblCenaTitulo" align="client" text="Cena Noturna" fontColor="{TEXT_GOLD}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                                <button name="btnRefreshDock" align="right" width="68" text="Atualizar" fontSize="10" margins="{{left=4}}">
                                    <event name="onClick">if CoterieDockBridge ~= nil then CoterieDockBridge.refreshDock(self) end</event>
                                </button>
                            </layout>
                            <label name="lblRodadaInfo" align="client" text="Rodada 1 • DECLARAÇÃO (Menor -&gt; Maior)" fontColor="{TEXT_MUTED}" fontSize="10" fontStyle="bold" horzTextAlign="{assert_align("leading")}" margins="{{top=4}}"/>
                        </rectangle>

                        <rectangle name="layNpcQuickControls" align="top" height="78" color="{BG_PANEL}" strokeColor="{BORDER_VAMP}" strokeSize="1" xradius="6" yradius="6" padding="{{left=8, right=8, top=6, bottom=6}}" margins="{{bottom=6}}">
                            <layout align="top" height="26">
                                <edit name="edtNpcInitNome" align="left" width="124" field="npc_init_nome" textPrompt="Nome NPC" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=4}}"/>
                                <label align="left" width="28" text="Mod:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("trailing")}" margins="{{right=2}}"/>
                                <edit name="edtNpcInitMod" align="left" width="34" field="npc_init_mod" type="number" fontColor="{TEXT_GOLD}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=4}}"/>
                                <checkBox name="chkNpcInitOculto" align="client" field="npc_init_oculto" text="Oculto" fontColor="{TEXT_ALERT}" fontSize="10"/>
                            </layout>
                            <layout align="top" height="28" margins="{{top=6}}">
                                <button name="btnAddNpcInit" align="left" width="90" text="+ Rolar NPC" fontSize="10" fontStyle="bold" margins="{{right=4}}">
                                    <event name="onClick">if CoterieDockBridge ~= nil then CoterieDockBridge.addQuickNpcInitiative(self) end</event>
                                </button>
                                <button name="btnTogglePhase" align="left" width="106" text="Alternar Fase" fontSize="10" margins="{{right=4}}">
                                    <event name="onClick">if CoterieDockBridge ~= nil then CoterieDockBridge.toggleCombatPhase(self) end</event>
                                </button>
                                <button name="btnClearInit" align="client" text="Limpar" fontSize="10">
                                    <event name="onClick">if CoterieDockBridge ~= nil then CoterieDockBridge.clearInitiative(self) end</event>
                                </button>
                            </layout>
                        </rectangle>

                        <rectangle align="top" height="244" color="{BG_PANEL}" strokeColor="{BORDER_VAMP}" strokeSize="1" xradius="6" yradius="6" padding="{{left=8, right=8, top=8, bottom=8}}" margins="{{bottom=6}}">
                            <label align="top" height="20" text="ORDEM DE INICIATIVA V20" fontColor="{ACCENT_DOCK}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}" margins="{{bottom=4}}"/>
{init_rows_xml}
                        </rectangle>

                        <rectangle align="top" height="206" color="{BG_PANEL}" strokeColor="{BORDER_VAMP}" strokeSize="1" xradius="6" yradius="6" padding="{{left=8, right=8, top=8, bottom=8}}">
                            <label align="top" height="20" text="CONDIÇÃO APARENTE DA COTERIE" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}" margins="{{bottom=4}}"/>
{pub_rows_xml}
                        </rectangle>
                    </layout>
                </scrollBox>
            </tab>"""


def _build_storyteller_card(idx: int) -> str:
    return f"""                        <rectangle name="rectStCard{idx}" align="top" height="108" visible="false" color="{BG_CARD}" strokeColor="{BORDER_VAMP}" strokeSize="1" xradius="6" yradius="6" padding="{{left=8, right=8, top=6, bottom=6}}" margins="{{bottom=6}}">
                            <label name="lblStCardTitle{idx}" align="top" height="18" text="—" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            <label name="lblStCardStats{idx}" align="top" height="32" text="" wordWrap="true" fontColor="{TEXT_MAIN}" fontSize="10" horzTextAlign="{assert_align("leading")}" margins="{{top=2}}"/>
                            <label name="lblStCardFlags{idx}" align="top" height="16" text="" wordWrap="true" fontColor="{TEXT_ALERT}" fontSize="10" fontStyle="bold" horzTextAlign="{assert_align("leading")}" margins="{{top=2}}"/>
                            <layout align="top" height="24" margins="{{top=4}}">
                                <button name="btnStBloodMinus{idx}" align="left" width="66" text="-1 Vitae" fontSize="10" margins="{{right=4}}">
                                    <event name="onClick">if CoterieDockBridge ~= nil then CoterieDockBridge.adjustCardBlood(self, {idx}, -1) end</event>
                                </button>
                                <button name="btnStBloodPlus{idx}" align="left" width="66" text="+1 Vitae" fontSize="10" margins="{{right=4}}">
                                    <event name="onClick">if CoterieDockBridge ~= nil then CoterieDockBridge.adjustCardBlood(self, {idx}, 1) end</event>
                                </button>
                                <button name="btnStApproveXp{idx}" align="client" visible="false" text="Aprovar XP" fontSize="10" fontStyle="bold">
                                    <event name="onClick">if CoterieDockBridge ~= nil then CoterieDockBridge.approveCardXP(self, {idx}) end</event>
                                </button>
                            </layout>
                        </rectangle>"""


def _build_tab2_storyteller_coterie() -> str:
    cards_xml = "\n".join(_build_storyteller_card(i) for i in range(1, 9))
    return f"""            <tab name="tabNarradorCoterie" title="2. Narrador (Coterie)" visible="false">
                <scrollBox align="client" padding="{{left=6, right=6, top=6, bottom=6}}">
                    <layout align="top" height="1060">
                        <rectangle align="top" height="104" color="{BG_PANEL}" strokeColor="{ACCENT_DOCK}" strokeSize="1" xradius="6" yradius="6" padding="{{left=8, right=8, top=6, bottom=6}}" margins="{{bottom=6}}">
                            <label align="top" height="18" text="COMANDOS EM LOTE DO NARRADOR" fontColor="{ACCENT_DOCK}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            <layout align="top" height="28" margins="{{top=4}}">
                                <button name="btnBatchAwaken" align="left" width="142" text="Despertar Coterie" fontSize="10" fontStyle="bold" margins="{{right=4}}">
                                    <event name="onClick">if CoterieDockBridge ~= nil then CoterieDockBridge.batchAwakenNightly(self) end</event>
                                </button>
                                <button name="btnBatchNewTurn" align="client" text="+1 Rodada / Turno" fontSize="10" fontStyle="bold">
                                    <event name="onClick">if CoterieDockBridge ~= nil then CoterieDockBridge.batchNewTurn(self) end</event>
                                </button>
                            </layout>
                            <layout align="top" height="28" margins="{{top=4}}">
                                <button name="btnBatchEndScene" align="client" text="Encerrar Cena (Limpar Buffs &amp; Agarrão)" fontSize="10">
                                    <event name="onClick">if CoterieDockBridge ~= nil then CoterieDockBridge.batchEndScene(self) end</event>
                                </button>
                            </layout>
                        </rectangle>

                        <rectangle align="top" height="36" color="{BG_PANEL}" strokeColor="{BORDER_VAMP}" strokeSize="1" xradius="6" yradius="6" padding="{{left=6, right=6, top=4, bottom=4}}" margins="{{bottom=6}}">
                            <button name="btnStPrevPage" align="left" width="58" text="&lt; Ant." fontSize="10">
                                <event name="onClick">if CoterieDockBridge ~= nil then CoterieDockBridge.changePage(self, -1) end</event>
                            </button>
                            <button name="btnStNextPage" align="right" width="58" text="Próx. &gt;" fontSize="10">
                                <event name="onClick">if CoterieDockBridge ~= nil then CoterieDockBridge.changePage(self, 1) end</event>
                            </button>
                            <label name="lblStPageInfo" align="client" text="Página 1/1 (0 fichas)" fontColor="{TEXT_MUTED}" fontSize="10" fontStyle="bold" horzTextAlign="{assert_align("center")}"/>
                        </rectangle>

{cards_xml}
                    </layout>
                </scrollBox>
            </tab>"""


def generate_coterie_dock_lfm() -> str:
    defaults = [
        ("npc_init_nome", "NPC"),
        ("npc_init_mod", "4"),
        ("npc_init_oculto", "false"),
    ]
    datalinks = root_datalinks_xml(defaults)
    title_attr = xml_esc("Vampiro V20 - Painel da Coterie & Iniciativa")

    xml_out = f"""<?xml version="1.0" encoding="UTF-8"?>
<form name="frmV20CoterieDock" formType="tablesDock" dataType="br.com.v20.CoterieDock" title="{title_attr}" width="340" height="580" theme="dark">

    <script>
        <![CDATA[
        local CoterieDockBridge = _G.V20CoterieDockBridge or require("Adapter.coterie_dock_bridge")
        if CoterieDockBridge ~= nil and CoterieDockBridge.installLocalUiGuard ~= nil then
            CoterieDockBridge.installLocalUiGuard(self)
        end
        self._onBeforeDestroy = function(fObj)
            if CoterieDockBridge ~= nil and CoterieDockBridge.disconnectDock ~= nil then
                CoterieDockBridge.disconnectDock(fObj)
            end
        end
        ]]>
    </script>

    <rectangle align="client" color="{BG_MAIN}">
        <tabControl name="pgcDock" align="client" margins="{{left=4, right=4, top=4, bottom=4}}">
{_build_tab1_scene_and_initiative()}
{_build_tab2_storyteller_coterie()}
        </tabControl>
    </rectangle>

{datalinks}
    <event name="OnNodeReady">if CoterieDockBridge ~= nil and CoterieDockBridge.ensureIsolatedSheet ~= nil then CoterieDockBridge.ensureIsolatedSheet(self) end</event>
    <event name="OnShow">if CoterieDockBridge ~= nil then CoterieDockBridge.connectDock(self) end</event>
    <event name="OnHide">if CoterieDockBridge ~= nil then CoterieDockBridge.disconnectDock(self) end</event>
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
    parser = argparse.ArgumentParser(
        description="Gera o painel acoplável tablesDock da Coterie & Iniciativa V20 (Sheets/frmV20CoterieDock.lfm)."
    )
    parser.add_argument("--out", default="", help="Caminho opcional de saída .lfm.")
    args = parser.parse_args()

    xml_content = generate_coterie_dock_lfm()
    out_path = args.out or os.path.join(ROOT, "Sheets", "frmV20CoterieDock.lfm")
    _write_if_changed(out_path, xml_content)


if __name__ == "__main__":
    main()
