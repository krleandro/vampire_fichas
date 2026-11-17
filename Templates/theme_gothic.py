#!/usr/bin/env python3
"""Tokens visuais góticos V20 e construtores XML compatíveis com o compilador SDK 3.7b."""
from __future__ import annotations

import xml.etree.ElementTree as ET

BG_MAIN = "#0D0D11"
BG_PANEL = "#16161E"
BG_CARD = "#1D1D28"
BG_INPUT = "#111118"
BORDER_VAMP = "#3A1C24"
BORDER_MORTAL = "#24303E"
ACCENT_MORTAL = "#C48F36"
TEXT_MAIN = "#ECE8E1"
TEXT_MUTED = "#9E9890"
TEXT_GOLD = "#D9B45B"
TEXT_ALERT = "#E05A5A"

VALID_ALIGNS = {"leading", "center", "trailing"}

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

CLANS: dict[str, dict] = {
    "brujah": {
        "id": "brujah",
        "dataType": "br.com.v20.Brujah",
        "formName": "frmBrujah",
        "name": "Brujah",
        "accentColor": "#9E1B24",
        "appearanceZero": False,
        "disciplines": ["celerity", "potence", "presence"],
        "weaknessSummary": "+2 na dificuldade para resistir ao Frenesi (máx. 10); não pode gastar FdV para evitar o Frenesi, apenas 1 FdV para encerrá-lo após começar (V20, p. 49).",
    },
    "gangrel": {
        "id": "gangrel",
        "dataType": "br.com.v20.Gangrel",
        "formName": "frmGangrel",
        "name": "Gangrel",
        "accentColor": "#4F6D3A",
        "appearanceZero": False,
        "disciplines": ["animalism", "fortitude", "protean"],
        "weaknessSummary": "Adquire 1 característica animal a cada Frenesi; a cada 5 características, perde 1 ponto permanente de Atributo Social (V20, p. 53).",
    },
    "malkavian": {
        "id": "malkavian",
        "dataType": "br.com.v20.Malkavian",
        "formName": "frmMalkavian",
        "name": "Malkaviano",
        "accentColor": "#6B3FA0",
        "appearanceZero": False,
        "disciplines": ["auspex", "dementation", "obfuscate"],
        "weaknessSummary": "Possui ao menos 1 Perturbação incurável desde o Abraço; pode gastar 1 FdV para suprimi-la por 1 cena (V20, p. 59).",
    },
    "nosferatu": {
        "id": "nosferatu",
        "dataType": "br.com.v20.Nosferatu",
        "formName": "frmNosferatu",
        "name": "Nosferatu",
        "accentColor": "#5C5346",
        "appearanceZero": True,
        "disciplines": ["animalism", "obfuscate", "potence"],
        "weaknessSummary": "Aparência permanentemente 0; falha automática na maioria dos testes baseados em Aparência (V20, p. 61).",
    },
    "toreador": {
        "id": "toreador",
        "dataType": "br.com.v20.Toreador",
        "formName": "frmToreador",
        "name": "Toreador",
        "accentColor": "#B8336A",
        "appearanceZero": False,
        "disciplines": ["auspex", "celerity", "presence"],
        "weaknessSummary": "Diante de grande beleza, testa Autocontrole/Instinto (dif. 6) ou fica fascinado pela cena (V20, p. 67).",
    },
    "tremere": {
        "id": "tremere",
        "dataType": "br.com.v20.Tremere",
        "formName": "frmTremere",
        "name": "Tremere",
        "accentColor": "#8C1D40",
        "appearanceZero": False,
        "disciplines": ["auspex", "dominate", "thaumaturgy"],
        "weaknessSummary": "Bastam 2 goles (em vez de 3) de sangue de outro vampiro para formar Laço de Sangue completo (V20, p. 69).",
    },
    "ventrue": {
        "id": "ventrue",
        "dataType": "br.com.v20.Ventrue",
        "formName": "frmVentrue",
        "name": "Ventrue",
        "accentColor": "#2E5A88",
        "appearanceZero": False,
        "disciplines": ["dominate", "fortitude", "presence"],
        "weaknessSummary": "Alimenta-se apenas de um tipo específico de recipiente mortal; vomita qualquer outro sangue humano (V20, p. 71).",
    },
    "assamite": {
        "id": "assamite",
        "dataType": "br.com.v20.Assamite",
        "formName": "frmAssamite",
        "name": "Assamita",
        "accentColor": "#7A4419",
        "appearanceZero": False,
        "disciplines": ["celerity", "obfuscate", "quietus"],
        "weaknessSummary": "Sofre 1 nível Letal não absorvível por ponto de vitae vampírica ingerida e vício em sangue cainita (V20, p. 49).",
    },
    "setite": {
        "id": "setite",
        "dataType": "br.com.v20.Setite",
        "formName": "frmSetite",
        "name": "Seguidores de Set",
        "accentColor": "#A67C1E",
        "appearanceZero": False,
        "disciplines": ["obfuscate", "presence", "serpentis"],
        "weaknessSummary": "Recebe +2 níveis de dano por luz solar e perde 1 dado em todas as paradas sob luz forte (V20, p. 51).",
    },
    "giovanni": {
        "id": "giovanni",
        "dataType": "br.com.v20.Giovanni",
        "formName": "frmGiovanni",
        "name": "Giovanni",
        "accentColor": "#3B5949",
        "appearanceZero": False,
        "disciplines": ["dominate", "necromancy", "potence"],
        "weaknessSummary": "O Beijo causa dor excruciante e causa o dobro de dano letal no recipiente humano (V20, p. 55).",
    },
    "lasombra": {
        "id": "lasombra",
        "dataType": "br.com.v20.Lasombra",
        "formName": "frmLasombra",
        "name": "Lasombra",
        "accentColor": "#3A3F5E",
        "appearanceZero": False,
        "disciplines": ["dominate", "obtenebration", "potence"],
        "weaknessSummary": "Não possui reflexo em espelhos/câmeras e sofre +1 nível de dano agravado pela luz solar (V20, p. 57).",
    },
    "ravnos": {
        "id": "ravnos",
        "dataType": "br.com.v20.Ravnos",
        "formName": "frmRavnos",
        "name": "Ravnos",
        "accentColor": "#9C4A1A",
        "appearanceZero": False,
        "disciplines": ["animalism", "chimerstry", "fortitude"],
        "weaknessSummary": "Possui um vício específico; quando tem oportunidade de praticá-lo, testa Autocontrole/Instinto dif. 6 para resistir (V20, p. 63).",
    },
    "tzimisce": {
        "id": "tzimisce",
        "dataType": "br.com.v20.Tzimisce",
        "formName": "frmTzimisce",
        "name": "Tzimisce",
        "accentColor": "#731928",
        "appearanceZero": False,
        "disciplines": ["animalism", "auspex", "vicissitude"],
        "weaknessSummary": "Deve repousar com 2 punhados de terra natal/importante; a cada 24h sem ela, paradas divididas pela metade (V20, p. 71).",
    },
    "caitiff": {
        "id": "caitiff",
        "dataType": "br.com.v20.Caitiff",
        "formName": "frmCaitiff",
        "name": "Caitiff",
        "accentColor": "#5A5A66",
        "appearanceZero": False,
        "disciplines": [],
        "weaknessSummary": "Sem disciplinas de clã (evolui qualquer disciplina por Atual x 6 XP); +2 dif. em testes Sociais com Membros estabelecidos (V20, p. 73).",
    },
}

ATTRIBUTES_BY_COL: list[tuple[str, list[tuple[str, str, str]]]] = [
    (
        "FÍSICOS",
        [
            ("attr_forca", "Força", "forca"),
            ("attr_destreza", "Destreza", "destreza"),
            ("attr_vigor", "Vigor", "vigor"),
        ],
    ),
    (
        "SOCIAIS",
        [
            ("attr_carisma", "Carisma", ""),
            ("attr_manipulacao", "Manipulação", ""),
            ("attr_aparencia", "Aparência", ""),
        ],
    ),
    (
        "MENTAIS",
        [
            ("attr_percepcao", "Percepção", ""),
            ("attr_inteligencia", "Inteligência", ""),
            ("attr_raciocinio", "Raciocínio", ""),
        ],
    ),
]

ABILITIES_BY_COL: list[tuple[str, list[tuple[str, str]]]] = [
    (
        "TALENTOS",
        [
            ("hab_prontidao", "Prontidão"),
            ("hab_esportes", "Esportes"),
            ("hab_consciencia", "Consciência"),
            ("hab_briga", "Briga"),
            ("hab_empatia", "Empatia"),
            ("hab_expressao", "Expressão"),
            ("hab_intimidacao", "Intimidação"),
            ("hab_lideranca", "Liderança"),
            ("hab_manha", "Manha"),
            ("hab_labia", "Lábia"),
        ],
    ),
    (
        "PERÍCIAS",
        [
            ("hab_empatia_animais", "Empatia c/ Animais"),
            ("hab_oficios", "Ofícios"),
            ("hab_conducao", "Condução"),
            ("hab_etiqueta", "Etiqueta"),
            ("hab_armas_fogo", "Armas de Fogo"),
            ("hab_arrombamento", "Arrombamento"),
            ("hab_armas_brancas", "Armas Brancas"),
            ("hab_performance", "Performance"),
            ("hab_furtividade", "Furtividade"),
            ("hab_sobrevivencia", "Sobrevivência"),
        ],
    ),
    (
        "CONHECIMENTOS",
        [
            ("hab_academicos", "Acadêmicos"),
            ("hab_computador", "Computador"),
            ("hab_financas", "Finanças"),
            ("hab_investigacao", "Investigação"),
            ("hab_direito", "Direito"),
            ("hab_medicina", "Medicina"),
            ("hab_ocultismo", "Ocultismo"),
            ("hab_politica", "Política"),
            ("hab_ciencias", "Ciências"),
            ("hab_tecnologia", "Tecnologia"),
        ],
    ),
]

DISCIPLINES_LIST: list[tuple[str, str]] = [
    ("animalism", "Animalismo"),
    ("auspex", "Auspícios"),
    ("celerity", "Rapidez"),
    ("chimerstry", "Quimerismo"),
    ("dementation", "Demência"),
    ("dominate", "Dominação"),
    ("fortitude", "Fortitude"),
    ("necromancy", "Necromancia (Sepulcro)"),
    ("obfuscate", "Ofuscação"),
    ("obtenebration", "Tenebrosidade"),
    ("potence", "Potência"),
    ("presence", "Presença"),
    ("protean", "Metamorfose"),
    ("quietus", "Quietus"),
    ("serpentis", "Serpentis"),
    ("thaumaturgy", "Taumaturgia (Sangue)"),
    ("vicissitude", "Vicissitude"),
]

BACKGROUNDS_LIST: list[tuple[str, str, bool, str | None]] = [
    ("allies", "Aliados", False, "Acionar"),
    ("alternate_identity", "Identidade Alternativa", False, "Testar"),
    ("contacts", "Contatos", False, "Sondar"),
    ("domain", "Domínio", True, "Caçar"),
    ("fame", "Fama", False, "Usar"),
    ("generation", "Geração", True, None),
    ("herd", "Rebanho", True, "Caçar"),
    ("influence", "Influência", False, "Exercer"),
    ("mentor", "Mentor", False, "Consultar"),
    ("resources", "Recursos", False, "Liquidar"),
    ("retainers", "Lacaios", False, "Comandar"),
    ("rituals", "Rituais", True, "Celebrar"),
    ("status", "Status", False, "Invocar"),
]

MERITS_FLAWS_OPTIONS: list[tuple[str, str]] = [
    ("", "— Selecionar Catálogo / Custom —"),
    ("acute_senses", "Qualidade: Sentidos Aguçados (1 pt, -2 dif Percepção)"),
    ("ambidextrous", "Qualidade: Ambidestro (1 pt)"),
    ("iron_will", "Qualidade: Vontade de Ferro (3 pts)"),
    ("huge_size", "Qualidade: Tamanho Grande (4 pts, +1 Escoriado)"),
    ("additional_disc", "Qualidade: Disciplina Adicional (5 pts)"),
    ("gen_14th", "Defeito: 14ª Geração / Sangue-Fraco (+2 pts)"),
    ("gen_15th", "Defeito: 15ª Geração / Sangue-Fraco (+4 pts)"),
    ("bad_sight", "Defeito: Deficiência Visual (+1 pt, +2 dif Percepção)"),
    ("custom", "Personalizada / Outra do V20 Corebook"),
]

MORALITY_PATHS: list[tuple[str, str]] = [
    ("humanidade", "Humanidade"),
    ("metamorfose", "Trilha da Metamorfose"),
    ("noite", "Trilha da Noite"),
    ("ossos", "Trilha dos Ossos"),
    ("sangue", "Trilha do Sangue"),
    ("tifao", "Trilha de Tifão"),
    ("paradoxo", "Trilha do Paradoxo"),
    ("reis", "Trilha dos Reis / Honra"),
]

NUMINA_LIST: list[tuple[str, str]] = [
    ("true_faith", "Fé Verdadeira (FdV Dif 7)"),
    ("hedge_magic", "Magia de Cerca (Inteligência Dif 7)"),
    ("psychic", "Fenômeno Psíquico (Percepção Dif 7)"),
]


def xml_esc(val: str) -> str:
    return (
        str(val)
        .replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def lua_str_list(items: list[str]) -> str:
    escaped = [str(it).replace("\\", "\\\\").replace("'", "\\'") for it in items]
    raw = "{" + ", ".join(f"'{it}'" for it in escaped) + "}"
    return xml_esc(raw)


def assert_align(align: str) -> str:
    if align not in VALID_ALIGNS:
        raise ValueError(f"Alinhamento inválido '{align}'; use apenas {sorted(VALID_ALIGNS)}")
    return align


def all_attr_options(include_virtual: bool = False) -> tuple[str, str]:
    items = []
    values = []
    for _, rows in ATTRIBUTES_BY_COL:
        for aid, aname, _ in rows:
            items.append(aname)
            values.append(aid)
    if include_virtual:
        items.extend(["Força de Vontade (Poder)", "Coragem (Virtude)"])
        values.extend(["attr_fdv_ref", "hab_coragem_ref"])
    return lua_str_list(items), lua_str_list(values)


def all_hab_options(include_none: bool = True, include_backgrounds: bool = True) -> tuple[str, str]:
    items: list[str] = []
    values: list[str] = []
    if include_none:
        items.append("— Apenas Atributo —")
        values.append("none")
    for _, rows in ABILITIES_BY_COL:
        for hid, hname in rows:
            items.append(hname)
            values.append(hid)
    if include_backgrounds:
        for bid, bname, _, _ in BACKGROUNDS_LIST:
            items.append(f"Antecedente: {bname}")
            values.append(f"bg_{bid}")
    items.extend(["Autocontrole/Instinto", "Coragem"])
    values.extend(["hab_autocontrole_ref", "hab_coragem_ref"])
    return lua_str_list(items), lua_str_list(values)


def make_root_datalink(fields: list[str], defaults: list[str], on_change_lua: str = "") -> str:
    if len(fields) != len(defaults):
        raise ValueError("fields e defaults devem possuir o mesmo tamanho em make_root_datalink")
    f_lua = lua_str_list(fields)
    d_lua = lua_str_list(defaults)
    ev = f'<event name="onChange">{on_change_lua}</event>' if on_change_lua else ""
    return f'    <dataLink fields="{f_lua}" defaultValues="{d_lua}">{ev}</dataLink>'


def root_datalinks_xml(field_defaults: list[tuple[str, str]], on_change_lua: str = "", chunk_size: int = 30) -> str:
    lines: list[str] = []
    for idx in range(0, len(field_defaults), chunk_size):
        chunk = field_defaults[idx : idx + chunk_size]
        fields = [k for k, _ in chunk]
        defaults = [v for _, v in chunk]
        lines.append(make_root_datalink(fields, defaults, on_change_lua=on_change_lua))
    return "\n".join(lines)


def header_bar_xml(accent_color: str, border_color: str, subtitle_label: str, is_vampire: bool = True) -> str:
    gen_or_prof_xml = (
        f'<label align="left" width="64" text="Geração:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("trailing")}" margins="{{right=4}}"/>'
        f'<label align="left" width="32" field="geracao" fontColor="{TEXT_GOLD}" fontSize="13" fontStyle="bold" horzTextAlign="{assert_align("center")}"/>'
        if is_vampire
        else f'<label align="left" width="54" text="Perfil:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("trailing")}" margins="{{right=4}}"/>'
        f'<label align="left" width="90" field="mortal_sobrenatural_modo" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("center")}"/>'
    )

    awaken_btn = (
        '<button align="right" width="88" text="Despertar" fontSize="11" fontStyle="bold" margins="{left=4}">'
        '<event name="onClick">if sheet ~= nil then V20Bridge.awakenNightly(sheet) end</event>'
        "</button>"
        if is_vampire
        else ""
    )

    blood_visible = "true" if is_vampire else "false"
    return f"""        <rectangle name="barHeaderTop" align="top" height="74" color="{BG_PANEL}" strokeColor="{accent_color}" strokeSize="1" padding="{{left=12, right=12, top=6, bottom=6}}">
            <layout align="top" height="28">
                <label align="left" width="175" text="{xml_esc(subtitle_label)}" fontColor="{accent_color}" fontSize="13" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                <label align="left" width="48" text="Nome:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("trailing")}" margins="{{right=4}}"/>
                <edit align="left" width="210" field="nome" textPrompt="Nome do Personagem" fontColor="{TEXT_MAIN}" fontSize="12" fontStyle="bold"/>
                {gen_or_prof_xml}
                <label align="left" width="70" text="Vitalidade:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("trailing")}" margins="{{left=8, right=4}}"/>
                <label align="left" width="120" field="vitalidade_resumo" fontColor="{TEXT_MAIN}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                <label align="client" field="vitalidade_alerta" fontColor="{TEXT_ALERT}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
            </layout>
            <layout align="top" height="30" margins="{{top=4}}">
                <layout name="pnlHeaderBlood" align="left" width="320" visible="{blood_visible}">
                    <label align="left" width="54" text="Sangue:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                    <button align="left" width="24" text="-" fontSize="12" fontStyle="bold">
                        <event name="onClick">if sheet ~= nil then V20Bridge.adjustResource(sheet, 'sangue_atual', -1, 0, 'sangue_max') end</event>
                    </button>
                    <label align="left" width="32" field="sangue_atual" fontColor="{TEXT_ALERT}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("center")}"/>
                    <label align="left" width="12" text="/" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("center")}"/>
                    <label align="left" width="28" field="sangue_max" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}"/>
                    <button align="left" width="24" text="+" fontSize="12" fontStyle="bold" margins="{{right=8}}">
                        <event name="onClick">if sheet ~= nil then V20Bridge.adjustResource(sheet, 'sangue_atual', 1, 0, 'sangue_max') end</event>
                    </button>
                    <label align="left" width="46" text="Turno:" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("trailing")}"/>
                    <label align="left" width="22" field="sangue_gasto_turno" fontColor="{TEXT_GOLD}" fontSize="11" horzTextAlign="{assert_align("center")}"/>
                    <label align="left" width="10" text="/" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("center")}"/>
                    <label align="left" width="24" field="sangue_por_turno" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("center")}"/>
                </layout>
                <layout align="left" width="215">
                    <label align="left" width="66" text="FdV Temp:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                    <button align="left" width="24" text="-" fontSize="12" fontStyle="bold">
                        <event name="onClick">if sheet ~= nil then V20Bridge.adjustResource(sheet, 'fdv_temp', -1, 0, 'fdv_perm') end</event>
                    </button>
                    <label align="left" width="28" field="fdv_temp" fontColor="{TEXT_GOLD}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("center")}"/>
                    <label align="left" width="12" text="/" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("center")}"/>
                    <label align="left" width="28" field="fdv_perm" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}"/>
                    <button align="left" width="24" text="+" fontSize="12" fontStyle="bold">
                        <event name="onClick">if sheet ~= nil then V20Bridge.adjustResource(sheet, 'fdv_temp', 1, 0, 'fdv_perm') end</event>
                    </button>
                </layout>
                <button align="right" width="94" text="Novo Turno" fontSize="11" margins="{{left=4}}">
                    <event name="onClick">if sheet ~= nil then V20Bridge.newTurn(sheet) end</event>
                </button>
                <button align="right" width="76" text="Curar" fontSize="11" margins="{{left=4}}">
                    <event name="onClick">if sheet ~= nil then V20Bridge.healDamage(sheet, 'bashing') end</event>
                </button>
                {awaken_btn}
            </layout>
        </rectangle>"""


def dice_roller_footer_xml(accent_color: str, border_color: str) -> str:
    attr_items, attr_vals = all_attr_options(include_virtual=True)
    hab_items, hab_vals = all_hab_options(include_none=True, include_backgrounds=True)
    return f"""        <rectangle name="barFooterRoller" align="bottom" height="76" color="{BG_PANEL}" strokeColor="{border_color}" strokeSize="1" padding="{{left=12, right=12, top=6, bottom=6}}">
            <layout align="top" height="30">
                <label align="left" width="58" text="Atributo:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                <comboBox align="left" width="145" field="roll_attr_id" items="{attr_items}" values="{attr_vals}" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=8}}"/>
                <label align="left" width="68" text="Habilidade:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                <comboBox align="left" width="175" field="roll_hab_id" items="{hab_items}" values="{hab_vals}" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=8}}"/>
                <label align="left" width="46" text="Bônus:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("trailing")}" margins="{{right=4}}"/>
                <edit align="left" width="42" field="roll_bonus_dice" type="number" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=8}}"/>
                <label align="left" width="28" text="Dif:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("trailing")}" margins="{{right=4}}"/>
                <edit align="left" width="40" field="roll_diff" type="number" fontColor="{TEXT_GOLD}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{right=8}}"/>
                <button align="right" width="142" text="ROLAR NO CHAT" fontSize="12" fontStyle="bold">
                    <event name="onClick">if sheet ~= nil then V20Bridge.rollFromSheet(sheet) end</event>
                </button>
            </layout>
            <layout align="top" height="28" margins="{{top=4}}">
                <checkBox align="left" width="82" field="roll_usar_espec" text="Espec. (10=2)" fontColor="{TEXT_MAIN}" fontSize="10"/>
                <checkBox align="left" width="84" field="roll_gastar_fdv" text="+1 FdV Auto" fontColor="{TEXT_GOLD}" fontSize="10"/>
                <checkBox align="left" width="76" field="roll_usar_fama" text="Usar Fama" fontColor="{TEXT_MAIN}" fontSize="10"/>
                <checkBox align="left" width="82" field="roll_usar_status" text="Usar Status" fontColor="{TEXT_MAIN}" fontSize="10"/>
                <checkBox align="left" width="106" field="roll_ignorar_ferimento" text="Ignorar Ferim." fontColor="{TEXT_MAIN}" fontSize="10"/>
                <label align="client" field="roll_equacao_resumo" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("trailing")}"/>
            </layout>
        </rectangle>"""


def trait_row_xml(
    field_id: str,
    label_text: str,
    kind: str = "attr",
    max_cap_field: str = "atributo_max_geracao",
    min_val: int = 0,
    with_specialty: bool = True,
    blood_buff_key: str = "",
) -> str:
    spec_field = f"spec_{field_id}"
    buff_xml = ""
    if blood_buff_key:
        buff_xml = (
            f'<button align="right" width="44" text="+Buff" fontSize="9" hint="Blood Buff (+1 Físico por 1 Vitae)" margins="{{left=3}}">'
            f'<event name="onClick">if sheet ~= nil then V20Bridge.applyBloodBuff(sheet, \'{blood_buff_key}\') end</event>'
            f"</button>"
            f'<label align="right" width="22" field="buff_{blood_buff_key}" fontColor="{TEXT_ALERT}" fontSize="10" fontStyle="bold" horzTextAlign="{assert_align("center")}"/>'
        )
    spec_xml = (
        f'<edit align="client" field="{spec_field}" textPrompt="Especialidade" fontColor="{TEXT_MUTED}" fontSize="10" margins="{{left=4}}"/>'
        if with_specialty
        else ""
    )
    return f"""                        <layout align="top" height="28" margins="{{bottom=2}}">
                            <button align="left" width="118" text="{xml_esc(label_text)}" fontSize="10" horzTextAlign="{assert_align("leading")}" hint="Selecionar na parada de dados">
                                <event name="onClick">if sheet ~= nil then V20Bridge.selectRollTrait(sheet, '{kind}', '{field_id}') end</event>
                            </button>
                            <button align="left" width="22" text="-" fontSize="11">
                                <event name="onClick">if sheet ~= nil then V20Bridge.adjustResource(sheet, '{field_id}', -1, {min_val}, '{max_cap_field}') end</event>
                            </button>
                            <edit align="left" width="34" field="{field_id}" type="number" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("center")}"/>
                            <button align="left" width="22" text="+" fontSize="11">
                                <event name="onClick">if sheet ~= nil then V20Bridge.adjustResource(sheet, '{field_id}', 1, {min_val}, '{max_cap_field}') end</event>
                            </button>
                            {buff_xml}
                            {spec_xml}
                        </layout>"""


def health_track_xml(accent_color: str, border_color: str, is_vampire: bool = True) -> str:
    dmg_items = lua_str_list(["Contundente (/)", "Letal (X)", "Agravado (*)"])
    dmg_vals = lua_str_list(["bashing", "lethal", "aggravated"])
    vamp_firearm_checks = (
        f'<checkBox align="left" width="150" field="dano_arma_fogo" text="Arma de Fogo (-> Cont.)" fontColor="{TEXT_MAIN}" fontSize="10"/>'
        f'<checkBox align="left" width="135" field="dano_tiro_cabeca" text="Tiro na Cabeça (Letal)" fontColor="{TEXT_ALERT}" fontSize="10"/>'
        f'<checkBox align="left" width="155" field="dano_dividir_contundente" text="Dividir Contundente / 2" fontColor="{TEXT_MAIN}" fontSize="10"/>'
        if is_vampire
        else f'<label align="left" width="320" text="Regra Mortal: Armas de Fogo causam dano Letal; Absorção Letal exige Armadura." fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}"/>'
    )
    levels = [
        ("0. Escoriado Extra (Tam. Grande)", "health_box_0"),
        ("1. Escoriado (0)", "health_box_1"),
        ("2. Machucado (-1)", "health_box_2"),
        ("3. Ferido (-1)", "health_box_3"),
        ("4. Ferido Gravemente (-2)", "health_box_4"),
        ("5. Espancado (-2)", "health_box_5"),
        ("6. Aleijado (-5)", "health_box_6"),
        ("7. Incapacitado (Imóvel)", "health_box_7"),
    ]
    rows_xml = "\n".join(
        f'                    <layout align="top" height="22">'
        f'<label align="left" width="190" text="{xml_esc(lbl)}" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>'
        f'<label align="left" width="54" field="{fld}" fontColor="{TEXT_GOLD}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("center")}"/>'
        f"</layout>"
        for lbl, fld in levels
    )
    return f"""                <rectangle align="top" height="340" color="{BG_PANEL}" strokeColor="{border_color}" strokeSize="1" xradius="6" yradius="6" padding="{{left=12, right=12, top=10, bottom=10}}" margins="{{bottom=10}}">
                    <label align="top" height="22" text="VITALIDADE, ABSORÇÃO E APLICADOR ASSISTIDO DE DANO (V20)" fontColor="{accent_color}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                    <layout align="top" height="26" margins="{{top=4}}">
                        <label align="left" width="80" text="Contundente:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                        <edit align="left" width="38" field="dano_contundente" type="number" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=10}}"/>
                        <label align="left" width="42" text="Letal:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                        <edit align="left" width="38" field="dano_letal" type="number" fontColor="{TEXT_GOLD}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=10}}"/>
                        <label align="left" width="66" text="Agravado:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                        <edit align="left" width="38" field="dano_aggravado" type="number" fontColor="{TEXT_ALERT}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=12}}"/>
                        <label align="left" width="66" text="Armadura:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                        <edit align="left" width="38" field="armadura_absorcao" type="number" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=8}}"/>
                        <checkBox align="left" width="130" field="tem_tamanho_grande" text="Tamanho Grande (+1)" fontColor="{TEXT_MAIN}" fontSize="10"/>
                    </layout>
                    <layout align="top" height="28" margins="{{top=4}}">
                        <label align="left" width="36" text="Qtd:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                        <edit align="left" width="38" field="dano_aplicar_qtd" type="number" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=6}}"/>
                        <comboBox align="left" width="140" field="dano_aplicar_tipo" items="{dmg_items}" values="{dmg_vals}" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=8}}"/>
                        <button align="left" width="106" text="Aplicar Dano" fontSize="11" fontStyle="bold" margins="{{right=10}}">
                            <event name="onClick">if sheet ~= nil then V20Bridge.applyDamage(sheet, nil, nil) end</event>
                        </button>
                        <comboBox align="left" width="135" field="cura_tipo" items="{dmg_items}" values="{dmg_vals}" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=6}}"/>
                        <button align="left" width="112" text="Curar c/ Vitae" fontSize="11" margins="{{right=8}}">
                            <event name="onClick">if sheet ~= nil then V20Bridge.healDamage(sheet, nil) end</event>
                        </button>
                        <button align="left" width="118" text="Rolar Absorção" fontSize="11">
                            <event name="onClick">if sheet ~= nil then V20Bridge.rollSoak(sheet, sheet.dano_aplicar_tipo) end</event>
                        </button>
                    </layout>
                    <layout align="top" height="24" margins="{{top=4, bottom=4}}">
                        {vamp_firearm_checks}
                    </layout>
{rows_xml}
                </rectangle>"""


def validate_generated_lfm_xml(xml_text: str) -> None:
    root = ET.fromstring(xml_text)
    for el in root.iter():
        if el.tag not in ALLOWED_TAGS:
            raise ValueError(f"Tag não permitida gerada no LFM: <{el.tag}>")
        for attr in ("horzTextAlign", "vertTextAlign"):
            if attr in el.attrib and el.attrib[attr] not in VALID_ALIGNS:
                raise ValueError(f"{attr} inválido: {el.attrib[attr]}")
    direct_dl = [c for c in root if c.tag == "dataLink"]
    all_dl = list(root.iter("dataLink"))
    if len(direct_dl) != len(all_dl) or len(direct_dl) < 1:
        raise ValueError("Todos os <dataLink> devem ser filhos diretos de <form>")
