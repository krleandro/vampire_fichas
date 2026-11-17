local BgCatalog = {}

BgCatalog.ORDER = {
    "allies", "alternate_identity", "contacts", "domain", "fame", "generation",
    "herd", "influence", "mentor", "resources", "retainers", "rituals", "status",
}

BgCatalog.HERD_VESSELS = { [0] = 0, [1] = 3, [2] = 7, [3] = 15, [4] = 30, [5] = 60 }

BgCatalog.RESOURCES_TIERS = {
    [0] = "Indigente (Sem renda fixa)",
    [1] = "Economias Modestas (~R$ 2.500/mês)",
    [2] = "Classe Média (~R$ 6.000/mês)",
    [3] = "Classe Média Alta / Confortável (~R$ 20.000/mês)",
    [4] = "Rico / Abastado (~R$ 80.000/mês)",
    [5] = "Multimilionário (~R$ 350.000+/mês)",
}

BgCatalog.BACKGROUNDS = {
    allies = {
        id = "allies",
        name = "Aliados",
        vampireOnly = false,
        defaultDiff = 6,
        actionTitle = "Acionar Aliados",
        summary = "Confederados mortais leais dispostos a auxiliar o personagem conforme poder e quantidade (V20, p. 111).",
    },
    alternate_identity = {
        id = "alternate_identity",
        name = "Identidade Alternativa",
        vampireOnly = false,
        defaultDiff = 6,
        actionTitle = "Sustentar Disfarce Documental",
        summary = "Persona secundária convincente com histórico e documentação de cobertura (V20, p. 111).",
    },
    contacts = {
        id = "contacts",
        name = "Contatos",
        vampireOnly = false,
        defaultDiff = 7,
        actionTitle = "Sondar Rede de Contatos",
        summary = "Informantes principais por ponto e rede secundária de rumores via Carisma + Contatos dif. 7 (V20, p. 112).",
    },
    domain = {
        id = "domain",
        name = "Domínio",
        vampireOnly = true,
        defaultDiff = 6,
        actionTitle = "Patrulhar / Caçar no Domínio",
        summary = "Território reconhecido de alimentação; reduz a dificuldade de caça em -1 por ponto (V20, p. 112).",
    },
    fame = {
        id = "fame",
        name = "Fama",
        vampireOnly = false,
        defaultDiff = 6,
        actionTitle = "Usar Reconhecimento Público",
        summary = "Renome na sociedade mortal; reduz dificuldade de testes Sociais com admiradores em -1 por ponto (V20, p. 114).",
    },
    generation = {
        id = "generation",
        name = "Geração",
        vampireOnly = true,
        defaultDiff = 6,
        actionTitle = nil,
        summary = "Reduz a Geração inicial em 1 degrau por ponto abaixo da 13ª, até a 8ª na criação padrão (V20, p. 114).",
    },
    herd = {
        id = "herd",
        name = "Rebanho",
        vampireOnly = true,
        defaultDiff = 6,
        actionTitle = "Alimentar-se do Rebanho",
        summary = "Grupo fiel de 3 a 60 recipientes mortais; concede +1 dado por ponto nos testes de caça (V20, p. 114).",
    },
    influence = {
        id = "influence",
        name = "Influência",
        vampireOnly = false,
        defaultDiff = 6,
        actionTitle = "Exercer Influência Institucional",
        summary = "Poder indireto sobre instituições políticas, policiais, midiáticas ou econômicas mortais (V20, p. 114).",
    },
    mentor = {
        id = "mentor",
        name = "Mentor",
        vampireOnly = false,
        defaultDiff = 6,
        actionTitle = "Solicitar Conselho/Auxílio do Mentor",
        summary = "Ancião ou patrono experiente que aconselha e pode interceder pelo personagem (V20, p. 115).",
    },
    resources = {
        id = "resources",
        name = "Recursos",
        vampireOnly = false,
        defaultDiff = 6,
        actionTitle = "Liquidar Recursos / Aquisição",
        summary = "Renda mensal líquida, bens e patrimônio disponíveis para manutenção e compras (V20, p. 115).",
    },
    retainers = {
        id = "retainers",
        name = "Lacaios",
        vampireOnly = false,
        defaultDiff = 6,
        actionTitle = "Comandar Lacaio",
        summary = "Servos dedicados, como carniçais ou asseclas condicionados, a serviço direto do personagem (V20, p. 116).",
    },
    rituals = {
        id = "rituals",
        name = "Rituais",
        vampireOnly = true,
        defaultDiff = 6,
        actionTitle = "Consultar Grimório de Rituais",
        summary = "Conhecimento e aptidão na condução de Ritae e cerimônias vampíricas sectárias (V20, p. 117).",
    },
    status = {
        id = "status",
        name = "Status",
        vampireOnly = false,
        defaultDiff = 6,
        actionTitle = "Invocar Prestígio de Status",
        summary = "Reputação formal entre os Membros; adiciona dados em interações Sociais de prestígio (V20, p. 118).",
    },
}

return BgCatalog
