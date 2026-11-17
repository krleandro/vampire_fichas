local BMCatalog = {}

local function tp(lvl, id, name, summary)
    return {
        id = id, level = lvl, name = name,
        cost = { blood = 1, willpower = 0 },
        pool = { attr = "attr_fdv_ref", hab = nil },
        defaultDiff = lvl + 3,
        diffHint = string.format("1 Sangue; testa FdV dif %d (botch perde 1 FdV perm.)", lvl + 3),
        summary = summary,
    }
end

local function np(lvl, id, name, blood, wp, attr, hab, diff, hint, summary)
    return {
        id = id, level = lvl, name = name,
        cost = { blood = blood or 0, willpower = wp or 0 },
        pool = attr and { attr = attr, hab = hab } or nil,
        defaultDiff = diff or 6,
        diffHint = hint or "Dif 6",
        summary = summary,
    }
end

BMCatalog.THAUMATURGY_ORDER = {
    "path_of_blood", "lure_of_flames", "movement_of_the_mind",
    "path_of_conjuring", "hands_of_destruction", "weather_control",
}

BMCatalog.THAUMATURGY_PATHS = {
    path_of_blood = {
        id = "path_of_blood", name = "Linha do Sangue",
        powers = {
            tp(1, "pob_1", "Um Gosto por Sangue", "Analisa geração, vitae restante e diablerie por uma gota (V20, p. 214)."),
            tp(2, "pob_2", "Fúria do Sangue", "Força outro vampiro a gastar sangue contra sua vontade ao toque (V20, p. 214)."),
            tp(3, "pob_3", "Sangue de Potência", "Reduz temporariamente a Geração efetiva por 1 hora (V20, p. 215)."),
            tp(4, "pob_4", "Furto de Vitae", "Drena sangue de alvo até 15m pelo ar sem contato físico (V20, p. 215)."),
            tp(5, "pob_5", "Caldeirão de Sangue", "Ferve o sangue nas veias causando dano Agravado ao toque (V20, p. 216)."),
        },
    },
    lure_of_flames = {
        id = "lure_of_flames", name = "Sedutor das Chamas",
        powers = {
            tp(1, "lof_1", "Vela", "Conjura pequena chama na palma (1 dado Agravado/turno, dif absorção 3; V20, p. 219)."),
            tp(2, "lof_2", "Punhado de Chamas", "Chama equivalente a tocha (1 dado Agravado/turno, dif absorção 4; V20, p. 219)."),
            tp(3, "lof_3", "Fogueira", "Labaredas intensas à vista (2 dados Agravados/turno, dif absorção 5; V20, p. 219)."),
            tp(4, "lof_4", "Pira", "Coluna ardente de fogo (2 dados Agravados/turno, dif absorção 7; V20, p. 219)."),
            tp(5, "lof_5", "Inferno", "Conflagração devastadora (3 dados Agravados/turno, dif absorção 9; V20, p. 219)."),
        },
    },
    movement_of_the_mind = {
        id = "movement_of_the_mind", name = "Movimento da Mente",
        powers = {
            tp(1, "mom_1", "Meio Quilo", "Move telecineticamente objetos de até 0,5 kg (V20, p. 220)."),
            tp(2, "mom_2", "Dez Quilos", "Ergue e arremessa objetos de até 10 kg mentalmente (V20, p. 220)."),
            tp(3, "mom_3", "Cem Quilos", "Ergue até 100 kg ou permite voo telecinético próprio lento (V20, p. 221)."),
            tp(4, "mom_4", "Meia Tonelada", "Ergue e arremessa massas de até 250–500 kg (V20, p. 221)."),
            tp(5, "mom_5", "Uma Tonelada", "Manipula até 500–1000 kg e arremessa seres vivos com impacto letal (V20, p. 221)."),
        },
    },
    path_of_conjuring = {
        id = "path_of_conjuring", name = "Linha da Conjuração",
        powers = {
            tp(1, "poc_1", "Invocar a Forma Simples", "Materializa objeto inanimado homogêneo simples por turnos (V20, p. 222)."),
            tp(2, "poc_2", "Permanência", "Gasta +3 Sangue para tornar permanente uma forma simples conjurada (V20, p. 222)."),
            tp(3, "poc_3", "Magia do Ferreiro", "Conjura objetos complexos com múltiplos materiais e peças móveis (V20, p. 223)."),
            tp(4, "poc_4", "Reverter Conjuração", "Dissolve instantaneamente criações conjuradas anteriores (V20, p. 223)."),
            tp(5, "poc_5", "Poder Sobre a Vida", "Conjura criatura ou simulacro biológico temporário obediente (V20, p. 223)."),
        },
    },
    hands_of_destruction = {
        id = "hands_of_destruction", name = "Mãos da Destruição",
        powers = {
            tp(1, "hod_1", "Decomposição", "Envelhece e apodrece matéria inanimada ao toque (V20, p. 225)."),
            tp(2, "hod_2", "Retorcer Madeira", "Deforma e estilhaça estruturas de madeira à vista (V20, p. 225)."),
            tp(3, "hod_3", "Toque Ácido", "Secreta fluido corrosivo que causa dano Agravado em carne/metal (V20, p. 226)."),
            tp(4, "hod_4", "Atrofia", "Murcha permanentemente ou pela noite um membro da vítima ao toque (V20, p. 226)."),
            tp(5, "hod_5", "Transformar em Pó", "Envelhece mortais até a morte ou inflige dano Agravado severo (V20, p. 226)."),
        },
    },
    weather_control = {
        id = "weather_control", name = "Controle do Clima",
        powers = {
            tp(1, "wc_1", "Névoa", "Conjura banco denso de neblina ocultando visão local (V20, p. 228)."),
            tp(2, "wc_2", "Chuva ou Neve", "Desencadeia precipitação intensa prejudicando percepção e tráfego (V20, p. 229)."),
            tp(3, "wc_3", "Vendaval", "Levanta ventos violentos que dificultam disparos e movimentação (V20, p. 229)."),
            tp(4, "wc_4", "Tempestade", "Invoca tormenta completa sobre a região em minutos (V20, p. 229)."),
            tp(5, "wc_5", "Ataque de Relâmpago", "Descarrega raio direto causando 10 dados de dano Letal/Agravado (V20, p. 229)."),
        },
    },
}

BMCatalog.NECROMANCY_ORDER = { "sepulchre_path", "bone_path", "ash_path" }

BMCatalog.NECROMANCY_PATHS = {
    sepulchre_path = {
        id = "sepulchre_path", name = "Linha do Sepulcro",
        powers = {
            np(1, "sep_1", "Visão do Cadáver", 0, 0, "attr_percepcao", "hab_consciencia", 6, "Dif 6", "Vê a última imagem registrada pelos olhos de um cadáver (V20, p. 160)."),
            np(2, "sep_2", "Invocar a Alma", 0, 1, "attr_percepcao", "hab_ocultismo", 7, "1 FdV; Dif = FdV do fantasma", "Chama o espectro de um falecido através da Mortalha (V20, p. 161)."),
            np(3, "sep_3", "Compelir a Alma", 0, 1, "attr_manipulacao", "hab_ocultismo", 6, "1 FdV; Dif = FdV da aparição", "Comanda um fantasma invocado por uma cena ou hora (V20, p. 162)."),
            np(4, "sep_4", "Assombração", 1, 0, "attr_manipulacao", "hab_ocultismo", 7, "1 Sangue; Dif = FdV da aparição", "Ancora uma aparição a um local ou objeto específico (V20, p. 162)."),
            np(5, "sep_5", "Tormento", 0, 0, "attr_vigor", "hab_empatia", 6, "Dif = FdV da aparição", "Inflige dano direto ao corpus espiritual de um fantasma (V20, p. 163)."),
        },
    },
    bone_path = {
        id = "bone_path", name = "Linha dos Ossos",
        powers = {
            np(1, "bon_1", "Tremor", 1, 0, "attr_destreza", "hab_ocultismo", 6, "1 Sangue; Dif 6", "Move repentinamente um membro de um cadáver próximo (V20, p. 164)."),
            np(2, "bon_2", "Passo do Aprendiz", 1, 1, "attr_inteligencia", "hab_ocultismo", 7, "1 Sangue + 1 FdV; Dif 7", "Reanima cadáveres como zumbis lentos para tarefas simples (V20, p. 165)."),
            np(3, "bon_3", "Trôpego", 1, 1, "attr_raciocinio", "hab_ocultismo", 6, "1 Sangue/cadáver + 1 FdV; Dif 6", "Ergue guardiões mortos-vivos agressivos capazes de combater (V20, p. 165)."),
            np(4, "bon_4", "Roubar a Vida", 0, 1, "attr_manipulacao", "hab_medicina", 7, "1 FdV; Dif 7", "Extrai temporariamente a alma de um ser vivo do próprio corpo (V20, p. 166)."),
            np(5, "bon_5", "Infusão Daemônica", 2, 1, "attr_inteligencia", "hab_ocultismo", 6, "2 Sangue + 1 FdV; Dif 6", "Prende um espectro num cadáver fresco criando servo inteligente (V20, p. 167)."),
        },
    },
    ash_path = {
        id = "ash_path", name = "Linha das Cinzas",
        powers = {
            np(1, "ash_1", "Visão da Mortalha", 0, 0, "attr_percepcao", "hab_consciencia", 7, "Dif 7", "Enxerga fantasmas e estruturas das Terras Sombrias pela cena (V20, p. 169)."),
            np(2, "ash_2", "Línguas Sem Vida", 0, 1, "attr_percepcao", "hab_ocultismo", 6, "1 FdV; Dif 6", "Conversa claramente com aparições sem atravessar a Mortalha (V20, p. 170)."),
            np(3, "ash_3", "Mão Morta", 0, 1, "attr_raciocinio", "hab_ocultismo", 7, "1 FdV (+1 Sangue/cena extra); Dif 7", "Toca objetos e espíritos nas Terras Sombrias a partir do mundo físico (V20, p. 170)."),
            np(4, "ash_4", "Exumação", 1, 1, "attr_destreza", "hab_ocultismo", 7, "1 Sangue + 1 FdV; Dif 7/8", "Cruza fisicamente a Mortalha para adentrar ou sair das Terras Sombrias (V20, p. 170)."),
            np(5, "ash_5", "Domínio da Mortalha", 0, 2, "attr_fdv_ref", nil, 6, "2 FdV; testa FdV dif 6", "Ergue ou rebaixa a densidade local da Mortalha drasticamente (V20, p. 171)."),
        },
    },
}

local function rit(id, tradition, lvl, name, blood, wp, diff, summary)
    return {
        id = id,
        tradition = tradition,
        level = lvl,
        name = name,
        cost = { blood = blood or 0, willpower = wp or 0 },
        defaultDiff = diff or math.min(9, 3 + lvl),
        summary = summary,
    }
end

BMCatalog.RITUAL_ORDER = {
    "thau_rit_1_sacred_haven", "thau_rit_1_wake_fresheness",
    "thau_rit_2_vitae_infusion", "thau_rit_2_ward_ghouls",
    "thau_rit_3_incorporeal_passage", "thau_rit_3_ward_kindred",
    "thau_rit_4_heart_stone", "thau_rit_4_ward_spirits",
    "thau_rit_5_abandon_fetters", "thau_rit_5_blood_contract",
    "necro_rit_1_call_hungry", "necro_rit_1_eyes_grave",
    "necro_rit_2_hand_glory", "necro_rit_2_sight_shroud",
    "necro_rit_3_unearthly_chain", "necro_rit_3_skull_chalice",
    "necro_rit_4_charon_kiss", "necro_rit_4_rend_shroud",
    "necro_rit_5_grasp_ghostly", "necro_rit_5_dark_exile",
}

BMCatalog.RITUALS = {
    thau_rit_1_sacred_haven        = rit("thau_rit_1_sacred_haven",        "thaumaturgy", 1, "Defesa do Refúgio Sagrado",          1, 0, 4, "Veda aposento contra a luz solar enquanto o conjurador permanecer dentro (V20, p. 231)."),
    thau_rit_1_wake_fresheness     = rit("thau_rit_1_wake_fresheness",     "thaumaturgy", 1, "Despertar com o Frescor da Tarde",   0, 0, 4, "Permite despertar imediatamente diante de perigo diurno sem teto de Humanidade (V20, p. 233)."),
    thau_rit_2_vitae_infusion      = rit("thau_rit_2_vitae_infusion",      "thaumaturgy", 2, "Foco Principal de Infusão de Vitae", 1, 0, 5, "Condensa 1 ponto de sangue num pequeno objeto para consumo futuro (V20, p. 235)."),
    thau_rit_2_ward_ghouls         = rit("thau_rit_2_ward_ghouls",         "thaumaturgy", 2, "Proteção Contra Carniçais",          1, 0, 5, "Glifo protetor que causa 3 dados Letais a carniçais que tocarem o objeto (V20, p. 235)."),
    thau_rit_3_incorporeal_passage = rit("thau_rit_3_incorporeal_passage", "thaumaturgy", 3, "Passagem Incorpórea",                0, 0, 6, "Torna o taumaturgo imaterial por horas mediante espelho estilhaçado (V20, p. 236)."),
    thau_rit_3_ward_kindred        = rit("thau_rit_3_ward_kindred",        "thaumaturgy", 3, "Proteção Contra Membros",            1, 0, 6, "Glifo com vitae que inflige 3 dados Agravados a outros vampiros ao toque (V20, p. 237)."),
    thau_rit_4_heart_stone         = rit("thau_rit_4_heart_stone",         "thaumaturgy", 4, "Coração de Pedra",                   0, 0, 7, "Petrifica o coração conferindo proteção contra estacas (-Empatia/Consciência; V20, p. 238)."),
    thau_rit_4_ward_spirits        = rit("thau_rit_4_ward_spirits",        "thaumaturgy", 4, "Proteção Contra Espíritos",          0, 0, 7, "Selo hermético que bloqueia e fere espíritos/aparições (V20, p. 239)."),
    thau_rit_5_abandon_fetters     = rit("thau_rit_5_abandon_fetters",     "thaumaturgy", 5, "Abandonar os Grilhões",              2, 1, 8, "Rompe de forma dolorosa um Laço de Sangue existente (V20, p. 239)."),
    thau_rit_5_blood_contract      = rit("thau_rit_5_blood_contract",      "thaumaturgy", 5, "Contrato de Sangue",                 1, 0, 8, "Pacto indissolúvel escrito em vitae que pune fisicamente quem violá-lo (V20, p. 240)."),

    necro_rit_1_call_hungry        = rit("necro_rit_1_call_hungry",        "necromancy",  1, "Chamado dos Mortos Famintos",        0, 0, 4, "Permite ouvir sussurros e lamúrias através da Mortalha local (V20, p. 176)."),
    necro_rit_1_eyes_grave         = rit("necro_rit_1_eyes_grave",         "necromancy",  1, "Olhos da Sepultura",                 0, 0, 4, "Inflige visões súbitas da própria morte à vítima escolhida (V20, p. 176)."),
    necro_rit_2_hand_glory         = rit("necro_rit_2_hand_glory",         "necromancy",  2, "Mão da Glória",                      1, 0, 5, "Mão mumificada acesa que paralisa moradores adormecidos de um local (V20, p. 177)."),
    necro_rit_2_sight_shroud       = rit("necro_rit_2_sight_shroud",       "necromancy",  2, "Olhar Além da Mortalha",             0, 0, 5, "Revela se objetos ou pessoas possuem grilhões espectrais ativos (V20, p. 177)."),
    necro_rit_3_unearthly_chain    = rit("necro_rit_3_unearthly_chain",    "necromancy",  3, "Ritual da Corrente Desenterrada",    0, 0, 6, "Sintoniza osso falange para rastrear infalivelmente o grilhão de um espírito (V20, p. 178)."),
    necro_rit_3_skull_chalice      = rit("necro_rit_3_skull_chalice",      "necromancy",  3, "Cálice de Crânio",                   1, 0, 6, "Compartilha percepção sensorial ou absorve maldições via crânio preparado (V20, p. 179)."),
    necro_rit_4_charon_kiss        = rit("necro_rit_4_charon_kiss",        "necromancy",  4, "Ósculo de Caronte",                  1, 0, 7, "Garante que um mortal prestes a morrer se torne uma aparição após o óbito (V20, p. 180)."),
    necro_rit_4_rend_shroud        = rit("necro_rit_4_rend_shroud",        "necromancy",  4, "Rasgar a Mortalha",                  1, 1, 7, "Reduz temporariamente a barreira da Mortalha facilitando travessias e invocações (V20, p. 181)."),
    necro_rit_5_grasp_ghostly      = rit("necro_rit_5_grasp_ghostly",      "necromancy",  5, "Aperto Fantasmagórico",              0, 1, 8, "Traz um objeto das Terras Sombrias como relíquia sólida para o mundo material (V20, p. 182)."),
    necro_rit_5_dark_exile         = rit("necro_rit_5_dark_exile",         "necromancy",  5, "Exílio Sombrio",                     2, 1, 8, "Arremessa temporariamente uma vítima para as Terras Sombrias (V20, p. 183)."),
}

return BMCatalog
