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

SUITE_VERSION = "1.0.3"
MAX_SHEET_WIDTH = 1180

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

CLAN_ORDER: list[str] = [
    "brujah",
    "gangrel",
    "malkavian",
    "nosferatu",
    "toreador",
    "tremere",
    "ventrue",
    "assamite",
    "setite",
    "giovanni",
    "lasombra",
    "ravnos",
    "tzimisce",
    "caitiff",
]

THAUMATURGY_PATHS_LIST: list[tuple[str, str]] = [
    ("path_of_blood", "Linha do Sangue"),
    ("lure_of_flames", "Sedutor das Chamas"),
    ("movement_of_the_mind", "Movimento da Mente"),
    ("path_of_conjuring", "Linha da Conjuração"),
    ("hands_of_destruction", "Mãos da Destruição"),
    ("weather_control", "Controle do Clima"),
]

NECROMANCY_PATHS_LIST: list[tuple[str, str]] = [
    ("sepulchre_path", "Linha do Sepulcro"),
    ("bone_path", "Linha dos Ossos"),
    ("ash_path", "Linha das Cinzas"),
]

ALL_BLOOD_MAGIC_PATHS_LIST: list[tuple[str, str]] = (
    [("", "— Selecionar Linha Secundária —")]
    + [(pid, f"[Taum] {pname}") for pid, pname in THAUMATURGY_PATHS_LIST]
    + [(pid, f"[Necro] {pname}") for pid, pname in NECROMANCY_PATHS_LIST]
)

RITUALS_LIST: list[tuple[str, str]] = [
    ("thau_rit_1_sacred_haven", "[Taum Nv 1] Defesa do Refúgio Sagrado"),
    ("thau_rit_1_wake_fresheness", "[Taum Nv 1] Despertar com o Frescor da Tarde"),
    ("thau_rit_2_vitae_infusion", "[Taum Nv 2] Foco Principal de Infusão de Vitae"),
    ("thau_rit_2_ward_ghouls", "[Taum Nv 2] Proteção Contra Carniçais"),
    ("thau_rit_3_incorporeal_passage", "[Taum Nv 3] Passagem Incorpórea"),
    ("thau_rit_3_ward_kindred", "[Taum Nv 3] Proteção Contra Membros"),
    ("thau_rit_4_heart_stone", "[Taum Nv 4] Coração de Pedra"),
    ("thau_rit_4_ward_spirits", "[Taum Nv 4] Proteção Contra Espíritos"),
    ("thau_rit_5_abandon_fetters", "[Taum Nv 5] Abandonar os Grilhões"),
    ("thau_rit_5_blood_contract", "[Taum Nv 5] Contrato de Sangue"),
    ("necro_rit_1_call_hungry", "[Necro Nv 1] Chamado dos Mortos Famintos"),
    ("necro_rit_1_eyes_grave", "[Necro Nv 1] Olhos da Sepultura"),
    ("necro_rit_2_hand_glory", "[Necro Nv 2] Mão da Glória"),
    ("necro_rit_2_sight_shroud", "[Necro Nv 2] Olhar Além da Mortalha"),
    ("necro_rit_3_unearthly_chain", "[Necro Nv 3] Ritual da Corrente Desenterrada"),
    ("necro_rit_3_skull_chalice", "[Necro Nv 3] Cálice de Crânio"),
    ("necro_rit_4_charon_kiss", "[Necro Nv 4] Ósculo de Caronte"),
    ("necro_rit_4_rend_shroud", "[Necro Nv 4] Rasgar a Mortalha"),
    ("necro_rit_5_grasp_ghostly", "[Necro Nv 5] Aperto Fantasmagórico"),
    ("necro_rit_5_dark_exile", "[Necro Nv 5] Exílio Sombrio"),
]

COMBAT_MANEUVER_OPTIONS: list[tuple[str, str]] = [
    ("strike", "Soco (Des+Briga, Dif 6)"),
    ("kick", "Chute (Des+Briga, Dif 7, For+1)"),
    ("bite", "Mordida Vampírica (Agarrão, Agrav.)"),
    ("claw", "Garras (Des+Briga, For+1)"),
    ("clinch", "Agarrão / Clinch (For+Briga)"),
    ("hold", "Segurar / Hold (For+Briga, s/ Dano)"),
    ("tackle", "Encontrão / Tackle (For+Briga, Dif 7)"),
    ("sweep_brawl", "Rasteira — Briga (Dif 7)"),
    ("disarm_brawl", "Desarmar — Briga (Dif 7)"),
    ("weapon_strike", "Golpe com Arma Equipada (Slot)"),
    ("stake_heart", "Estacar Coração (Dif 9, Letal)"),
    ("disarm_melee", "Desarmar com Arma (+1 Dif)"),
    ("sweep_melee", "Rasteira com Arma (+1 Dif)"),
    ("single_shot", "Tiro Único (Slot Arma de Fogo)"),
    ("double_tap", "Tiro Duplo Rápido (+1d, +1 Dif)"),
    ("three_round_burst", "Rajada Curta 3 Tiros (+2d, +1 Dif)"),
    ("full_auto", "Rajada Completa (+10d, +2 Dif)"),
    ("dodge", "Defesa: Esquiva Ativa (Des+Esp)"),
    ("block", "Defesa: Bloqueio (Des+Briga)"),
    ("parry", "Defesa: Aparar (Des+Arm. Brancas)"),
]

TARGET_LOCATION_OPTIONS: list[tuple[str, str]] = [
    ("nenhum", "Sem Alvo Específico"),
    ("membro", "Membro / Arma (+1 Dif)"),
    ("cabeca", "Cabeça / Vital (+2 Dif, +1d)"),
]

COVER_LEVEL_OPTIONS: list[tuple[str, str]] = [
    ("nenhuma", "Sem Cobertura"),
    ("leve", "Cobertura Leve (+1 Dif)"),
    ("boa", "Boa Cobertura (+2 Dif)"),
    ("superior", "Cobertura Superior (+3 Dif)"),
]

FLANK_MODE_OPTIONS: list[tuple[str, str]] = [
    ("frontal", "Frontal (+0 Dif)"),
    ("flanco", "Flanco (-1 Dif)"),
    ("retaguarda", "Retaguarda (-2 Dif)"),
]

COMBAT_MANEUVER_FIELD_DEFAULTS: list[tuple[str, str]] = [
    ("cmb_manobra_id", "strike"),
    ("cmb_arma_slot", "1"),
    ("cmb_acoes_normais", "1"),
    ("cmb_acao_ordem", "1"),
    ("cmb_menor_parada", "0"),
    ("cmb_acao_rapidez", "false"),
    ("cmb_mira_turnos", "0"),
    ("cmb_tem_luneta", "false"),
    ("cmb_alvo_localizado", "nenhum"),
    ("cmb_cobertura", "nenhuma"),
    ("cmb_posicao", "frontal"),
    ("cmb_defesa_alvo_sucessos", "0"),
    ("cmb_forca_alvo", "2"),
    ("cmb_defesas_feitas_turno", "0"),
    ("em_agarrao", "false"),
    ("armadura_penalidade", "0"),
    ("rapidez_acoes_extras", "0"),
    ("cmb_manobra_resumo", "Soco (V20, p. 276) — Manobra padrão desarmada (Força Contundente; V20, p. 276)."),
    ("cmb_dano_pendente_ativo", "false"),
    ("cmb_dano_pendente_parada", "0"),
    ("cmb_dano_pendente_auto", "0"),
    ("cmb_dano_pendente_tipo", "bashing"),
    ("cmb_dano_pendente_estaca", "false"),
    ("cmb_dano_pendente_cabeca", "false"),
    ("cmb_dano_pendente_manobra", ""),
    ("cmb_dano_pendente_resumo", "Nenhum dano encadeado pendente."),
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


def all_xp_upgradable_field_options(is_vampire: bool = True) -> tuple[str, str]:
    items: list[str] = []
    values: list[str] = []
    for _, rows in ATTRIBUTES_BY_COL:
        for aid, aname, _ in rows:
            items.append(f"Atributo: {aname}")
            values.append(aid)
    for _, rows in ABILITIES_BY_COL:
        for hid, hname in rows:
            items.append(f"Habilidade: {hname}")
            values.append(hid)
    for i in range(1, 5):
        items.append(f"Hab. Secundária #{i}")
        values.append(f"hab_extra{i}_val")
    for i in range(1, 10):
        items.append(f"Disciplina Slot #{i}")
        values.append(f"disc_slot{i}_nivel")
    if is_vampire:
        for i in range(1, 5):
            items.append(f"Linha Secundária #{i}")
            values.append(f"bm_sec{i}_nivel")
    items.extend([
        "Virtude 1 (Consciência/Convicção)",
        "Virtude 2 (Autocontrole/Instinto)",
        "Virtude 3 (Coragem)",
        "Moralidade / Humanidade / Trilha",
        "Força de Vontade Permanente",
    ])
    values.extend([
        "virtude1_val",
        "virtude2_val",
        "virtude3_val",
        "moralidade_val",
        "fdv_perm",
    ])
    return lua_str_list(items), lua_str_list(values)


def build_mode_permissions_lua(is_vampire: bool = True) -> str:
    perm_edits: list[str] = []
    perm_ctrls: list[str] = []

    if is_vampire:
        perm_edits.extend([
            "edtGeracaoBase",
            "edtFreebieAttributes",
            "edtFreebieAbilities",
            "edtFreebieDisciplines",
            "edtFreebieBackgrounds",
            "edtFreebieVirtues",
            "edtFreebieMorality",
            "edtFreebieWillpower",
        ])
        perm_ctrls.extend(["btnRolarVitaeInicial", "btnConcluirCriacao"])
    else:
        perm_edits.extend([
            "edtFreebieAttributes",
            "edtFreebieAbilities",
            "edtFreebieBackgrounds",
            "edtFreebieVirtues",
            "edtFreebieMorality",
            "edtFreebieWillpower",
        ])
        perm_ctrls.extend(["cmbMortalPerfil", "btnConcluirCriacao"])

    for _, rows in ATTRIBUTES_BY_COL:
        for aid, _, _ in rows:
            perm_edits.extend([f"edt_{aid}", f"edt_spec_{aid}"])
            perm_ctrls.extend([f"btnMinus_{aid}", f"btnPlus_{aid}"])

    for _, rows in ABILITIES_BY_COL:
        for hid, _ in rows:
            perm_edits.extend([f"edt_{hid}", f"edt_spec_{hid}"])
            perm_ctrls.extend([f"btnMinus_{hid}", f"btnPlus_{hid}"])

    for i in range(1, 5):
        perm_edits.extend([f"edtHabExtraNome{i}", f"edtHabExtraVal{i}", f"edtHabExtraEspec{i}"])

    if is_vampire:
        for i in range(1, 10):
            perm_edits.append(f"edtDiscSlotNivel{i}")
            perm_ctrls.extend([f"cmbDiscSlotId{i}", f"cmbDiscSlotCat{i}"])
    else:
        for i in range(1, 5):
            perm_edits.append(f"edtDiscSlotNivel{i}")
            perm_ctrls.append(f"cmbDiscSlotId{i}")
        for nid, _ in NUMINA_LIST:
            perm_edits.append(f"edtNumina_{nid}")

    for bid, _, vamp_only, _ in BACKGROUNDS_LIST:
        if (not is_vampire) and vamp_only and bid in ("generation", "rituals"):
            continue
        perm_edits.append(f"edtBg_{bid}")

    for i in range(1, 7):
        perm_edits.extend([f"edtMfNome{i}", f"edtMfPontos{i}"])
        perm_ctrls.extend([f"chkMfAtivo{i}", f"cmbMfId{i}", f"cmbMfTipo{i}"])

    perm_ctrls.append("chkTamanhoGrande")

    perm_edits.extend(["edtVirtude1Val", "edtVirtude2Val", "edtVirtude3Val", "edtMoralidadeVal", "edtFdvPerm"])
    if is_vampire:
        perm_ctrls.extend([
            "cmbVirtude1Tipo",
            "cmbVirtude2Tipo",
            "cmbMoralidadeTipo",
            "cmbAssamitaMaldicaoModo",
        ])
        perm_edits.extend([
            "edtBmSecNivel1",
            "edtBmSecNivel2",
            "edtBmSecNivel3",
            "edtBmSecNivel4",
            "edtGangrelTracosQtd",
            "edtMalkavPerturbacao",
            "edtVentruePresaRestrita",
            "edtRavnosVicio",
            "edtTzimisceOrigemTerra",
            "edtToreadorFocoArte",
        ])

    mestre_edits = ["edtXpTotal", "edtXpGasto"]
    mestre_ctrls = ["cmbModoFicha", "chkXpExigeAprovacao", "chkNarradorOverride", "btnAprovarXP", "btnRecusarXP"]
    if not is_vampire:
        mestre_edits.append("edtCarnicalDiscMax")
        mestre_ctrls.append("cmbMortalSobrenaturalModo")

    def _lua_arr(names: list[str]) -> str:
        return "{ " + ", ".join(f'"{n}"' for n in names) + " }"

    mode_tail = (
        """
            local lockThauPrim = lockPerm and ((tonumber(sheet.bm_thau_prim_nivel) or 0) > 0)
            if self.cmbBmThauPrimId ~= nil then self.cmbBmThauPrimId:setEnabled(not lockThauPrim) end
            local lockNecroPrim = lockPerm and ((tonumber(sheet.bm_necro_prim_nivel) or 0) > 0)
            if self.cmbBmNecroPrimId ~= nil then self.cmbBmNecroPrimId:setEnabled(not lockNecroPrim) end
            for secIdx = 1, 4 do
                local secOwned = (tonumber(sheet["bm_sec" .. secIdx .. "_nivel"]) or 0) > 0
                local lockSecChoice = lockPerm and secOwned
                local cDisc = self["cmbBmSecDisc" .. secIdx]
                local cPath = self["cmbBmSecPathId" .. secIdx]
                if cDisc ~= nil then cDisc:setEnabled(not lockSecChoice) end
                if cPath ~= nil then cPath:setEnabled(not lockSecChoice) end
            end
            if self.tabMagiaSangue ~= nil then
                local mostrarBM = (V20Bridge ~= nil and V20Bridge.hasBloodMagicAccess ~= nil and V20Bridge.hasBloodMagicAccess(sheet)) or false
                if (not mostrarBM) and self.pgcPrincipal ~= nil and self.pgcPrincipal.getTabIndex ~= nil and self.pgcPrincipal:getTabIndex() == 7 then
                    if self.pgcPrincipal.setTabIndex ~= nil then
                        self.pgcPrincipal:setTabIndex(0)
                    end
                end
                self.tabMagiaSangue:setVisible(mostrarBM)
            end"""
        if is_vampire
        else '\n            local modoSob = sheet.mortal_sobrenatural_modo or "humano"\n'
        '            if self.btnFrenesiCarnical ~= nil then self.btnFrenesiCarnical:setVisible(modoSob == "carnical") end'
    )

    return f"""        local PERM_EDITS = {_lua_arr(perm_edits)}
        local PERM_CTRLS = {_lua_arr(perm_ctrls)}
        local MESTRE_EDITS = {_lua_arr(mestre_edits)}
        local MESTRE_CTRLS = {_lua_arr(mestre_ctrls)}

        local function atualizarPermissoesModo(self)
            if self == nil or sheet == nil or V20Bridge == nil then return end
            local isMestre = V20Bridge.isStoryteller(sheet)
            local modo = sheet.modo_ficha or "criacao"
            local stOverride = (sheet.narrador_override == true or sheet.narrador_override == "true") and isMestre
            local lockPerm = ((modo == "jogo") and (not stOverride)) or ((modo == "narrador_livre") and (not isMestre))
            for _, nm in ipairs(PERM_EDITS) do
                if self[nm] ~= nil then self[nm]:setReadOnly(lockPerm) end
            end
            for _, nm in ipairs(PERM_CTRLS) do
                if self[nm] ~= nil then self[nm]:setEnabled(not lockPerm) end
            end
            if sheet.cla_id == "nosferatu" and not stOverride then
                if self.edt_attr_aparencia ~= nil then self.edt_attr_aparencia:setReadOnly(true) end
                if self.btnMinus_attr_aparencia ~= nil then self.btnMinus_attr_aparencia:setEnabled(false) end
                if self.btnPlus_attr_aparencia ~= nil then self.btnPlus_attr_aparencia:setEnabled(false) end
            end
            for _, nm in ipairs(MESTRE_EDITS) do
                if self[nm] ~= nil then self[nm]:setReadOnly(not isMestre) end
            end
            for _, nm in ipairs(MESTRE_CTRLS) do
                if self[nm] ~= nil then self[nm]:setEnabled(isMestre) end
            end{mode_tail}
        end"""


def build_responsive_layout_lua(is_vampire: bool = True) -> str:
    page_tabs = [
        "layPageTab1",
        "layPageTab2",
        "layPageTab3",
        "layPageTab4",
        "layPageTab5",
        "layPageTab6",
        "layPageTab7",
    ]
    if is_vampire:
        page_tabs.append("layPageTab8")
    page_tabs.append("layPageTabSobre")

    col3_pairs = [
        ("colBio1_1", "colBio1_2"),
        ("colBio2_1", "colBio2_2"),
        ("colAttr1", "colAttr2"),
        ("colHab1", "colHab2"),
        ("colVirt1", "colVirt2"),
    ]
    if is_vampire:
        col3_pairs.insert(2, ("colBio3_1", "colBio3_2"))

    col2_left = ["colHabExtra1"]
    if not is_vampire:
        col2_left.append("colMortalRow3_1")

    tabs_lua = "{ " + ", ".join(f'"{t}"' for t in page_tabs) + " }"
    pairs_lua = "{ " + ", ".join(f'{{ "{a}", "{b}" }}' for a, b in col3_pairs) + " }"
    col2_lua = "{ " + ", ".join(f'"{c}"' for c in col2_left) + " }"

    return f"""        local PAGE_TABS = {tabs_lua}
        local COL3_PAIRS = {pairs_lua}
        local COL2_LEFT = {col2_lua}
        local QUICK_CMB_BTNS = {{ "btnQuickCmb1", "btnQuickCmb2", "btnQuickCmb3", "btnQuickCmb4" }}

        local function ajustarLayoutResponsivo(self)
            if self == nil then return end
            local rootW = 0
            if self.rectRootBg ~= nil and self.rectRootBg.getWidth ~= nil then
                rootW = tonumber(self.rectRootBg:getWidth()) or 0
            end
            if rootW <= 100 and self.getWidth ~= nil then
                rootW = tonumber(self:getWidth()) or 0
            end
            if rootW <= 100 then
                rootW = {MAX_SHEET_WIDTH}
            end

            local barMargin = math.max(0, math.floor((rootW - 26 - {MAX_SHEET_WIDTH}) / 2))
            if self.layHeaderInner ~= nil then
                self.layHeaderInner:setMargins({{ left = barMargin, right = barMargin, top = 0, bottom = 0 }})
            end
            if self.layFooterInner ~= nil then
                self.layFooterInner:setMargins({{ left = barMargin, right = barMargin, top = 0, bottom = 0 }})
            end

            local availW = math.max(720, rootW - 52)
            local pageW = math.min({MAX_SHEET_WIDTH}, availW)
            local sideMargin = math.max(0, math.floor((availW - pageW) / 2))
            for _, pName in ipairs(PAGE_TABS) do
                local pCtrl = self[pName]
                if pCtrl ~= nil then
                    pCtrl:setMargins({{ left = sideMargin, right = sideMargin, top = 0, bottom = 0 }})
                end
            end

            local innerW = math.max(694, pageW - 26)
            local col3W = math.max(220, math.floor((innerW - 20) / 3))
            for _, pair in ipairs(COL3_PAIRS) do
                local c1 = self[pair[1]]
                local c2 = self[pair[2]]
                if c1 ~= nil then c1:setWidth(col3W) end
                if c2 ~= nil then c2:setWidth(col3W) end
            end

            local col2W = math.max(320, math.floor((innerW - 14) / 2))
            for _, leftName in ipairs(COL2_LEFT) do
                local cLeft = self[leftName]
                if cLeft ~= nil then cLeft:setWidth(col2W) end
            end

            local quickW = math.max(132, math.floor((innerW - 32) / 5))
            for _, bName in ipairs(QUICK_CMB_BTNS) do
                local bCtrl = self[bName]
                if bCtrl ~= nil then bCtrl:setWidth(quickW) end
            end
        end"""


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
            <layout name="layHeaderInner" align="client">
                <layout align="top" height="28">
                    <label align="left" width="180" text="{xml_esc(subtitle_label)}" fontColor="{accent_color}" fontSize="13" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                    <label align="left" width="48" text="Nome:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("trailing")}" margins="{{right=4}}"/>
                    <edit align="left" width="240" field="nome" textPrompt="Nome do Personagem" fontColor="{TEXT_MAIN}" fontSize="12" fontStyle="bold"/>
                    {gen_or_prof_xml}
                    <label align="left" width="70" text="Vitalidade:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("trailing")}" margins="{{left=8, right=4}}"/>
                    <label align="left" width="125" field="vitalidade_resumo" fontColor="{TEXT_MAIN}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
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
            </layout>
        </rectangle>"""


def dice_roller_footer_xml(accent_color: str, border_color: str) -> str:
    attr_items, attr_vals = all_attr_options(include_virtual=True)
    hab_items, hab_vals = all_hab_options(include_none=True, include_backgrounds=True)
    return f"""        <rectangle name="barFooterRoller" align="bottom" height="76" color="{BG_PANEL}" strokeColor="{border_color}" strokeSize="1" padding="{{left=12, right=12, top=6, bottom=6}}">
            <layout name="layFooterInner" align="client">
                <layout align="top" height="30">
                    <label align="left" width="58" text="Atributo:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                    <comboBox align="left" width="165" field="roll_attr_id" items="{attr_items}" values="{attr_vals}" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=8}}"/>
                    <label align="left" width="68" text="Habilidade:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("leading")}"/>
                    <comboBox align="left" width="205" field="roll_hab_id" items="{hab_items}" values="{hab_vals}" fontColor="{TEXT_MAIN}" fontSize="11" margins="{{right=8}}"/>
                    <label align="left" width="46" text="Bônus:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("trailing")}" margins="{{right=4}}"/>
                    <edit align="left" width="42" field="roll_bonus_dice" type="number" fontColor="{TEXT_MAIN}" fontSize="11" horzTextAlign="{assert_align("center")}" margins="{{right=8}}"/>
                    <label align="left" width="28" text="Dif:" fontColor="{TEXT_MUTED}" fontSize="11" horzTextAlign="{assert_align("trailing")}" margins="{{right=4}}"/>
                    <edit align="left" width="40" field="roll_diff" type="number" fontColor="{TEXT_GOLD}" fontSize="12" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{right=8}}"/>
                    <button align="right" width="152" text="ROLAR NO CHAT" fontSize="12" fontStyle="bold">
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
            f'<button align="right" width="40" text="+Buff" fontSize="9" hint="Blood Buff (+1 Físico por 1 Vitae)" margins="{{left=3}}">'
            f'<event name="onClick">if sheet ~= nil then V20Bridge.applyBloodBuff(sheet, \'{blood_buff_key}\') end</event>'
            f"</button>"
            f'<label align="right" width="18" field="buff_{blood_buff_key}" fontColor="{TEXT_ALERT}" fontSize="10" fontStyle="bold" horzTextAlign="{assert_align("center")}"/>'
        )
    spec_xml = (
        f'<edit name="edt_{spec_field}" align="client" field="{spec_field}" textPrompt="Especialidade" fontColor="{TEXT_MUTED}" fontSize="10" margins="{{left=4}}"/>'
        if with_specialty
        else ""
    )
    return f"""                        <layout align="top" height="28" margins="{{bottom=2}}">
                            <button align="left" width="112" text="{xml_esc(label_text)}" fontSize="10" horzTextAlign="{assert_align("leading")}" hint="Selecionar na parada de dados">
                                <event name="onClick">if sheet ~= nil then V20Bridge.selectRollTrait(sheet, '{kind}', '{field_id}') end</event>
                            </button>
                            <button name="btnMinus_{field_id}" align="left" width="22" text="-" fontSize="11">
                                <event name="onClick">if sheet ~= nil then V20Bridge.adjustResource(sheet, '{field_id}', -1, {min_val}, '{max_cap_field}') end</event>
                            </button>
                            <edit name="edt_{field_id}" align="left" width="32" field="{field_id}" type="number" fontColor="{TEXT_GOLD}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("center")}"/>
                            <button name="btnPlus_{field_id}" align="left" width="22" text="+" fontSize="11">
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
        f'<checkBox align="left" width="115" field="dano_fonte_solar" text="Luz Solar" fontColor="{TEXT_GOLD}" fontSize="10"/>'
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
                        <checkBox name="chkTamanhoGrande" align="left" width="130" field="tem_tamanho_grande" text="Tamanho Grande (+1)" fontColor="{TEXT_MAIN}" fontSize="10"/>
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


def suite_credits_tab_xml(
    tab_title: str,
    accent_color: str,
    border_color: str,
    model_label: str,
    compact: bool = False,
) -> str:
    pad = "8" if compact else "14"
    title_sz = "13" if compact else "17"
    author_sz = "12" if compact else "14"
    meta_sz = "10" if compact else "11"
    hero_h = "156" if compact else "176"
    upd_h = "96" if compact else "86"
    body_h = "230" if compact else "210"
    total_h = "525" if compact else "525"
    btn_upd_w = "152" if compact else "215"
    page_name_attr = "" if compact else 'name="layPageTabSobre" '

    return f"""            <tab name="tabSobreSuite" title="{xml_esc(tab_title)}">
                <scrollBox align="client" padding="{{left=10, right=10, top=10, bottom=10}}">
                    <layout {page_name_attr}align="top" height="{total_h}">
                        <rectangle name="crdSobreIdentificacao" align="top" height="{hero_h}" color="{BG_PANEL}" strokeColor="{accent_color}" strokeSize="1" xradius="6" yradius="6" padding="{{left={pad}, right={pad}, top=14, bottom=14}}" margins="{{bottom=10}}">
                            <label name="lblSobreSelo" align="top" height="20" text="IDENTIFICAÇÃO DA SUÍTE • RRPG FIRECAST SDK 3.7b" fontColor="{TEXT_MUTED}" fontSize="10" fontStyle="bold" horzTextAlign="{assert_align("center")}"/>
                            <label name="lblSobreTituloPrincipal" align="top" height="44" text="Suite de plugins para Vampiro - A máscara V 20" wordWrap="true" fontColor="{TEXT_GOLD}" fontSize="{title_sz}" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{top=6}}"/>
                            <label name="lblSobreAutoria" align="top" height="30" text="Desenvolvida por Mestre Carlos (krmirim)" wordWrap="true" fontColor="{accent_color}" fontSize="{author_sz}" fontStyle="bold" horzTextAlign="{assert_align("center")}" margins="{{top=4}}"/>
                            <label name="lblSobreVersaoModelo" align="top" height="28" text="{xml_esc(f'Versão {SUITE_VERSION} • {model_label}')}" wordWrap="true" fontColor="{TEXT_MAIN}" fontSize="{meta_sz}" horzTextAlign="{assert_align("center")}" margins="{{top=6}}"/>
                        </rectangle>

                        <rectangle name="crdSobreAtualizador" align="top" height="{upd_h}" color="{BG_PANEL}" strokeColor="{border_color}" strokeSize="1" xradius="6" yradius="6" padding="{{left={pad}, right={pad}, top=8, bottom=8}}" margins="{{bottom=10}}">
                            <label name="lblUpdateStatus" align="top" height="22" text="{xml_esc(f'Versão instalada: v{SUITE_VERSION} • Repositório: github.com/krleandro/vampire_fichas')}" wordWrap="true" fontColor="{TEXT_GOLD}" fontSize="10" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            <layout align="top" height="30" margins="{{top=6}}">
                                <button name="btnVerificarAtualizacao" align="left" width="{btn_upd_w}" text="Verificar / Atualizar" fontSize="10" fontStyle="bold" margins="{{right=6}}">
                                    <event name="onClick">if _G.V20AutoUpdater ~= nil then _G.V20AutoUpdater.checkAndInstall(self, {{ manual = true }}) end</event>
                                </button>
                                <button name="btnAbrirGithub" align="client" text="Abrir GitHub Oficial" fontSize="10">
                                    <event name="onClick">if _G.V20AutoUpdater ~= nil then _G.V20AutoUpdater.openRepository() end</event>
                                </button>
                            </layout>
                        </rectangle>

                        <rectangle name="crdSobreModulos" align="top" height="{body_h}" color="{BG_PANEL}" strokeColor="{border_color}" strokeSize="1" xradius="6" yradius="6" padding="{{left={pad}, right={pad}, top=12, bottom=12}}">
                            <label name="lblSobreEscopoTitulo" align="top" height="22" text="ECOSSISTEMA INTEGRADO V20 (16 FORMULÁRIOS)" fontColor="{accent_color}" fontSize="11" fontStyle="bold" horzTextAlign="{assert_align("leading")}"/>
                            <label name="lblSobreItem1" align="top" height="36" text="• 15 Modelos de Ficha dedicados: 13 Clãs Tradicionais, Caitiff e Ficha Mortal (Humano, Carniçal e Numina)." wordWrap="true" fontColor="{TEXT_MAIN}" fontSize="{meta_sz}" horzTextAlign="{assert_align("leading")}" margins="{{top=6}}"/>
                            <label name="lblSobreItem2" align="top" height="36" text="• Painel acoplável TablesDock da Coterie &amp; Iniciativa V20 sincronizado na sala com proteção anti-metajogo." wordWrap="true" fontColor="{TEXT_MAIN}" fontSize="{meta_sz}" horzTextAlign="{assert_align("leading")}" margins="{{top=4}}"/>
                            <label name="lblSobreItem3" align="top" height="42" text="• Automação universal de 17 Disciplinas, 9 Linhas e 20 Rituais de Magia do Sangue, 14 Fraquezas, 20 Manobras de Combate Assistido, Gerações 4ª–15ª e Auditoria de XP." wordWrap="true" fontColor="{TEXT_MAIN}" fontSize="{meta_sz}" horzTextAlign="{assert_align("leading")}" margins="{{top=4}}"/>
                            <label name="lblSobreReferencia" align="top" height="26" text="Referência mecânica: Vampire: The Masquerade — 20th Anniversary Edition (V20)." wordWrap="true" fontColor="{TEXT_MUTED}" fontSize="10" horzTextAlign="{assert_align("leading")}" margins="{{top=8}}"/>
                        </rectangle>
                    </layout>
                </scrollBox>
            </tab>"""


def validate_generated_lfm_xml(xml_text: str) -> None:
    root = ET.fromstring(xml_text)
    seen_names: set[str] = set()
    for el in root.iter():
        if el.tag not in ALLOWED_TAGS:
            raise ValueError(f"Tag não permitida gerada no LFM: <{el.tag}>")
        if el.tag != "event" and el is not root and "name" in el.attrib:
            nm = el.attrib["name"]
            if nm in seen_names:
                raise ValueError(f"Atributo name duplicado no LFM: '{nm}'")
            seen_names.add(nm)
        for attr in ("horzTextAlign", "vertTextAlign"):
            if attr in el.attrib and el.attrib[attr] not in VALID_ALIGNS:
                raise ValueError(f"{attr} inválido: {el.attrib[attr]}")
    direct_dl = [c for c in root if c.tag == "dataLink"]
    all_dl = list(root.iter("dataLink"))
    if len(direct_dl) != len(all_dl) or len(direct_dl) < 1:
        raise ValueError("Todos os <dataLink> devem ser filhos diretos de <form>")
