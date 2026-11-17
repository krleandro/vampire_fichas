local MFCatalog = {}

MFCatalog.ORDER = {
    "acute_senses", "ambidextrous", "iron_will", "huge_size",
    "additional_disc", "gen_14th", "gen_15th", "bad_sight",
}

MFCatalog.ITEMS = {
    acute_senses = {
        id = "acute_senses",
        name = "Sentidos Aguçados",
        tipo = "qualidade",
        pontos = 1,
        effect = "perception_diff_-2",
        summary = "Reduz em -2 a dificuldade de testes de Percepção ligados ao sentido aguçado (V20, p. 479).",
    },
    ambidextrous = {
        id = "ambidextrous",
        name = "Ambidestro",
        tipo = "qualidade",
        pontos = 1,
        effect = "no_offhand_penalty",
        summary = "Elimina a penalidade de dificuldade por usar a mão inábil em ações físicas (V20, p. 480).",
    },
    iron_will = {
        id = "iron_will",
        name = "Vontade de Ferro",
        tipo = "qualidade",
        pontos = 3,
        effect = "resist_dominate_+3",
        summary = "Gasta 1 FdV para ignorar Dominação ou soma +3 dados para resistir a controle mental (V20, p. 485).",
    },
    huge_size = {
        id = "huge_size",
        name = "Tamanho Grande",
        tipo = "qualidade",
        pontos = 4,
        effect = "extra_bruised_box",
        summary = "Corpo imenso; concede 1 nível adicional de Vitalidade Escoriado sem penalidade (V20, p. 480).",
    },
    additional_disc = {
        id = "additional_disc",
        name = "Disciplina Adicional",
        tipo = "qualidade",
        pontos = 5,
        effect = "additional_in_clan_disc",
        summary = "Adota 1 Disciplina extra tratada como Disciplina de Clã para custos de evolução (V20, p. 494).",
    },
    gen_14th = {
        id = "gen_14th",
        name = "Décima Quarta Geração",
        tipo = "defeito",
        pontos = 2,
        effect = "force_gen_14",
        summary = "Sangue-Fraco de 14ª Geração: apenas 8 de 10 pontos de sangue usáveis e Disciplinas máx. 4 (V20, p. 481).",
    },
    gen_15th = {
        id = "gen_15th",
        name = "Décima Quinta Geração",
        tipo = "defeito",
        pontos = 4,
        effect = "force_gen_15",
        summary = "Sangue-Fraco de 15ª Geração: 6 pontos usáveis, custo dobrado de sangue e Disciplinas máx. 3 (V20, p. 481).",
    },
    bad_sight = {
        id = "bad_sight",
        name = "Deficiência Visual",
        tipo = "defeito",
        pontos = 1,
        effect = "perception_diff_+2",
        summary = "Aumenta em +2 a dificuldade de testes de Percepção visual não corrigidos (V20, p. 481).",
    },
}

MFCatalog.NUMINA_ORDER = {
    "true_faith", "hedge_magic", "psychic",
}

MFCatalog.NUMINA = {
    true_faith = {
        id = "true_faith",
        name = "Fé Verdadeira",
        poolAttr = "attr_fdv_ref",
        defaultDiff = 7,
        summary = "Repele vampiros (teste de Fé vs FdV/Autocontrole) e protege contra Dominação (V20, p. 372).",
    },
    hedge_magic = {
        id = "hedge_magic",
        name = "Magia de Cerca",
        poolAttr = "attr_inteligencia",
        defaultDiff = 7,
        summary = "Trilhas lineares de feitiçaria mortal ritualística e encantamentos (V20, p. 375).",
    },
    psychic = {
        id = "psychic",
        name = "Fenômeno Psíquico",
        poolAttr = "attr_percepcao",
        defaultDiff = 7,
        summary = "Aptidão psíquica humana como telepatia, pirocinese ou clarividência (V20, p. 492).",
    },
}

return MFCatalog
