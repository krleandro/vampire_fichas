local Catalog = {}

Catalog.ORDER = {
    "animalism", "auspex", "celerity", "chimerstry", "dementation", "dominate",
    "fortitude", "necromancy", "obfuscate", "obtenebration", "potence", "presence",
    "protean", "quietus", "serpentis", "thaumaturgy", "vicissitude",
}

local function p(lvl, id, name, blood, wp, attr, hab, diff, hint, buff, summary)
    return {
        id = id, level = lvl, name = name,
        cost = { blood = blood or 0, willpower = wp or 0 },
        pool = attr and { attr = attr, hab = hab } or nil,
        defaultDiff = diff or 6, diffHint = hint or "Dif 6",
        toggleBuff = buff, summary = summary,
    }
end

Catalog.DISCIPLINES = {
    animalism = {
        id = "animalism", name = "Animalismo", hasPaths = false,
        powers = {
            p(1, "anim_1", "Sussurros Fera", 0, 0, "attr_manipulacao", "hab_empatia_animais", 6, "Dif 6 (mamíferos predadores) a 8", nil, "Comunica-se mentalmente e impõe comandos simples a animais (V20, p. 128)."),
            p(2, "anim_2", "O Chamado", 0, 0, "attr_carisma", "hab_sobrevivencia", 6, "Dif 6; convoca animais da espécie escolhida", nil, "Convoca animais da vizinhança conforme número de sucessos (V20, p. 129)."),
            p(3, "anim_3", "Acalmar a Besta", 0, 0, "attr_manipulacao", "hab_intimidacao", 7, "Dif 7 (ou Empatia p/ tirar do Frenesi)", nil, "Subjuga a Besta em mortais ou retira vampiros do Frenesi (V20, p. 130)."),
            p(4, "anim_4", "Subjugar o Espírito", 0, 1, "attr_manipulacao", "hab_empatia_animais", 8, "Dif 8 (possui corpo do animal)", nil, "Transfere a consciência vampírica para o corpo de um animal (V20, p. 131)."),
            p(5, "anim_5", "Expulsar a Besta", 0, 0, "attr_manipulacao", "hab_autocontrole_ref", 8, "Dif 8 ao beirar Frenesi", nil, "Transfere o próprio Frenesi iminente para outro alvo próximo (V20, p. 132)."),
        },
    },
    auspex = {
        id = "auspex", name = "Auspícios", hasPaths = false,
        powers = {
            p(1, "ausp_1", "Sentidos Aguçados", 0, 0, nil, nil, 6, "Ativação livre (-N dif Percepção)", { id = "auspex_senses", perceptionDiffMod = -1 }, "Dobra o alcance sensorial e reduz dificuldade de Percepção pelo nível de Auspícios (V20, p. 134)."),
            p(2, "ausp_2", "Percepção da Aura", 0, 0, "attr_percepcao", "hab_empatia", 8, "Dif 8", nil, "Lê emoções, natureza vampírica, magia e diablerie na aura do alvo (V20, p. 135)."),
            p(3, "ausp_3", "O Toque do Espírito", 0, 0, "attr_percepcao", "hab_empatia", 8, "Dif 5 a 9 conforme idade da impressão", nil, "Extrai visões psicométricas do último possuidor de um objeto ou local (V20, p. 136)."),
            p(4, "ausp_4", "Telepatia", 0, 0, "attr_inteligencia", "hab_labia", 6, "Dif = FdV permanente do alvo (1 FdV contra vampiros)", nil, "Projeta pensamentos e lê a mente superficial ou profunda (V20, p. 137)."),
            p(5, "ausp_5", "Projeção Psíquica", 0, 1, "attr_percepcao", "hab_consciencia", 7, "Dif 7 a 9 conforme distância", nil, "Separa a consciência em corpo astral invisível e veloz (V20, p. 138)."),
        },
    },
    celerity = {
        id = "celerity", name = "Rapidez", hasPaths = false,
        powers = {
            p(1, "cel_1", "Rapidez 1", 1, 0, nil, nil, 6, "+1 dado Destreza passivo OU 1 Sangue = +1 ação extra", nil, "Velocidade sobrenatural: +1 Destreza passivo ou +1 ação física extra no turno (V20, p. 142)."),
            p(2, "cel_2", "Rapidez 2", 1, 0, nil, nil, 6, "Até 2 ações físicas extras por 1 Sangue cada", nil, "Eleva bônus passivo de Destreza para +2 ou até 2 ações extras (V20, p. 142)."),
            p(3, "cel_3", "Rapidez 3", 1, 0, nil, nil, 6, "Até 3 ações físicas extras por 1 Sangue cada", nil, "Eleva bônus passivo de Destreza para +3 ou até 3 ações extras (V20, p. 142)."),
            p(4, "cel_4", "Rapidez 4", 1, 0, nil, nil, 6, "Até 4 ações físicas extras por 1 Sangue cada", nil, "Eleva bônus passivo de Destreza para +4 ou até 4 ações extras (V20, p. 142)."),
            p(5, "cel_5", "Rapidez 5", 1, 0, nil, nil, 6, "Até 5 ações físicas extras por 1 Sangue cada", nil, "Eleva bônus passivo de Destreza para +5 ou até 5 ações extras (V20, p. 142)."),
        },
    },
    chimerstry = {
        id = "chimerstry", name = "Quimerismo", hasPaths = false,
        powers = {
            p(1, "chim_1", "Ignis Fatuus", 0, 1, nil, nil, 6, "1 FdV; ilusão estática de 1 sentido", nil, "Cria miragem menor perceptível por um único sentido (V20, p. 143)."),
            p(2, "chim_2", "Fata Morgana", 1, 1, nil, nil, 6, "1 Sangue + 1 FdV; ilusão multissensorial estática", nil, "Cria ilusão completa que afeta todos os sentidos sem causar dano físico (V20, p. 144)."),
            p(3, "chim_3", "Aparição", 1, 0, nil, nil, 6, "+1 Sangue para dar movimento à ilusão", nil, "Concede movimento, som contínuo e comportamento verossímil à ilusão (V20, p. 144)."),
            p(4, "chim_4", "Permanência", 1, 0, nil, nil, 6, "1 Sangue torna a ilusão persistente", nil, "Mantém ilusões de Ignis Fatuus ou Fata Morgana mesmo sem presença do criador (V20, p. 144)."),
            p(5, "chim_5", "Realidade Horrível", 0, 1, "attr_manipulacao", "hab_labia", 6, "Dif = Percepção + Autocontrole da vítima", nil, "Alucinação psicossomática capaz de ferir diretamente uma vítima (V20, p. 145)."),
        },
    },
    dementation = {
        id = "dementation", name = "Demência", hasPaths = false,
        powers = {
            p(1, "dem_1", "Paixão", 0, 0, "attr_carisma", "hab_empatia", 6, "Dif = Humanidade/Trilha do alvo", nil, "Amplifica ou embota radicalmente as emoções atuais do alvo (V20, p. 146)."),
            p(2, "dem_2", "Assombrar a Alma", 1, 0, "attr_manipulacao", "hab_ocultismo", 6, "Dif = Percepção + Autocontrole do alvo", nil, "Assombra a vítima com visões fugazes nos cantos da percepção (V20, p. 147)."),
            p(3, "dem_3", "Olhos do Caos", 0, 0, "attr_percepcao", "hab_ocultismo", 6, "Dif variável (6 a 9 conforme obscuridade)", nil, "Decifra padrões ocultos, naturezas reais e mensagens cifradas na loucura (V20, p. 148)."),
            p(4, "dem_4", "A Voz da Loucura", 1, 0, "attr_manipulacao", "hab_empatia", 7, "Dif 7; induz Frenesi/Rötschreck coletivo", nil, "Conduz ouvintes ao pânico cego ou fúria irracional (V20, p. 148)."),
            p(5, "dem_5", "Insanidade Total", 1, 0, "attr_manipulacao", "hab_intimidacao", 6, "Dif = FdV atual da vítima", nil, "Desperta cinco perturbações graves simultâneas na mente do alvo (V20, p. 149)."),
        },
    },
    dominate = {
        id = "dominate", name = "Dominação", hasPaths = false,
        powers = {
            p(1, "dom_1", "Comando", 0, 0, "attr_manipulacao", "hab_intimidacao", 6, "Dif = FdV permanente do alvo; 1 palavra", nil, "Impõe ordem imediata de uma única palavra via contato visual (V20, p. 152)."),
            p(2, "dom_2", "Hipnotizar", 0, 0, "attr_manipulacao", "hab_lideranca", 6, "Dif = FdV permanente do alvo", nil, "Implanta diretriz complexa imediata ou ativada por gatilho no subconsciente (V20, p. 152)."),
            p(3, "dom_3", "A Mente Esquecida", 0, 0, "attr_raciocinio", "hab_labia", 6, "Dif = FdV permanente do alvo", nil, "Apaga, vasculha ou reescreve memórias da vítima sob olhar fixo (V20, p. 154)."),
            p(4, "dom_4", "Condicionamento", 0, 0, "attr_carisma", "hab_lideranca", 6, "Dif = FdV permanente; teste estendido ao longo do tempo", nil, "Quebra gradualmente a autonomia do servo, facilitando dominações futuras sem olhar (V20, p. 155)."),
            p(5, "dom_5", "Possessão", 0, 1, "attr_carisma", "hab_intimidacao", 7, "Disputa de FdV e domina corpo mortal", nil, "Assume controle absoluto do corpo físico de um mortal (V20, p. 155)."),
        },
    },
    fortitude = {
        id = "fortitude", name = "Fortitude", hasPaths = false,
        powers = {
            p(1, "fort_1", "Fortitude 1", 0, 0, nil, nil, 6, "Passivo: +1 dado Absorção Contundente/Letal/Agravado", nil, "Resistência sobrenatural a danos normais, fogo e luz solar (V20, p. 157)."),
            p(2, "fort_2", "Fortitude 2", 0, 0, nil, nil, 6, "Passivo: +2 dados de Absorção", nil, "Concede +2 dados em paradas de Absorção inclusive contra Agravado (V20, p. 157)."),
            p(3, "fort_3", "Fortitude 3", 0, 0, nil, nil, 6, "Passivo: +3 dados de Absorção", nil, "Concede +3 dados em paradas de Absorção inclusive contra Agravado (V20, p. 157)."),
            p(4, "fort_4", "Fortitude 4", 0, 0, nil, nil, 6, "Passivo: +4 dados de Absorção", nil, "Concede +4 dados em paradas de Absorção inclusive contra Agravado (V20, p. 157)."),
            p(5, "fort_5", "Fortitude 5", 0, 0, nil, nil, 6, "Passivo: +5 dados de Absorção", nil, "Concede +5 dados em paradas de Absorção inclusive contra Agravado (V20, p. 157)."),
        },
    },
    necromancy = {
        id = "necromancy", name = "Necromancia (Linha do Sepulcro)", hasPaths = true,
        powers = {
            p(1, "necro_1", "Visão do Cadáver", 0, 0, "attr_percepcao", "hab_consciencia", 6, "Dif 6 (enxerga últimos momentos nos olhos do morto)", nil, "Contempla a última cena presenciada por um cadáver (V20, p. 160)."),
            p(2, "necro_2", "Invocar a Alma", 0, 1, "attr_percepcao", "hab_ocultismo", 7, "Dif = FdV do espectro (ou 7)", nil, "Chama o fantasma de um falecido de volta através da Mortalha (V20, p. 161)."),
            p(3, "necro_3", "Compelir a Alma", 0, 1, "attr_manipulacao", "hab_ocultismo", 6, "Dif = FdV atual da aparição", nil, "Obriga uma aparição invocada a obedecer ordens por uma cena/hora (V20, p. 162)."),
            p(4, "necro_4", "Assombração", 1, 0, "attr_manipulacao", "hab_ocultismo", 7, "Dif = FdV da aparição; prende a local/objeto", nil, "Atrela um espírito a um objeto ou aposento específico (V20, p. 162)."),
            p(5, "necro_5", "Tormento", 0, 0, "attr_vigor", "hab_empatia", 6, "Dif = FdV da aparição (causa dano letal espiritual)", nil, "Golpeia diretamente o corpus de uma aparição com energia entrópica (V20, p. 163)."),
        },
    },
    obfuscate = {
        id = "obfuscate", name = "Ofuscação", hasPaths = false,
        powers = {
            p(1, "obf_1", "Manto das Sombras", 0, 0, nil, nil, 6, "Automático se imóvel e em cobertura", { id = "obf_cloak", stealthActive = true }, "Oculta-se das vistas enquanto permanecer imóvel na penumbra (V20, p. 184)."),
            p(2, "obf_2", "Presença Invisível", 0, 0, "attr_raciocinio", "hab_furtividade", 6, "Automático, ou Raciocínio + Furtividade se arriscar ruído", { id = "obf_unseen", stealthActive = true }, "Move-se pelo ambiente sem ser notado por observadores comuns (V20, p. 185)."),
            p(3, "obf_3", "Máscara das Mil Faces", 0, 0, "attr_manipulacao", "hab_performance", 7, "Dif 7", nil, "Projeta feições ilusórias escolhidas na mente de quem o observa (V20, p. 186)."),
            p(4, "obf_4", "Desaparecer do Olho da Mente", 0, 0, "attr_carisma", "hab_furtividade", 6, "Dif = Raciocínio + Prontidão das testemunhas", nil, "Desaparece abruptamente mesmo diante de olhares diretos (V20, p. 187)."),
            p(5, "obf_5", "Cobrir o Grupo", 0, 0, nil, nil, 6, "Estende poderes de Ofuscação a 1 aliado por ponto de Furtividade", nil, "Oculta ou disfarça companheiros próximos sob o mesmo véu mental (V20, p. 187)."),
        },
    },
    obtenebration = {
        id = "obtenebration", name = "Tenebrosidade", hasPaths = false,
        powers = {
            p(1, "obt_1", "Jogo de Sombras", 1, 0, nil, nil, 6, "1 Sangue/cena: +1 Furtividade/Intimidação, sufoca inimigos (-1 Vigor)", { id = "obt_shadowplay", bonusIntimidation = 1 }, "Dobra sombras naturais ao redor para intimidar e sufocar (V20, p. 189)."),
            p(2, "obt_2", "Mortalha das Trevas", 1, 0, "attr_manipulacao", "hab_ocultismo", 7, "Dif 7; nuvem cega e tira -2 Vigor dos mortais dentro", nil, "Cria esfera de escuridão abissal impenetrável até por visão aguçada (V20, p. 189)."),
            p(3, "obt_3", "Braços do Abismo", 1, 0, "attr_manipulacao", "hab_ocultismo", 7, "Dif 7; 1 tentáculo por sucesso (For/Des = nível Tenebrosidade)", nil, "Invoca tentáculos sólidos do Abismo para agarrar e esmagar (V20, p. 190)."),
            p(4, "obt_4", "Metamorfose Sombria", 2, 0, "attr_manipulacao", "hab_coragem_ref", 7, "2 Sangue; +1 ataque tentacular e -2 dados em inimigos adjacentes", { id = "obt_blackmeta", extraShadowAttack = true }, "Funde o corpo às trevas abissais ganhando tentáculos e terror (V20, p. 190)."),
            p(5, "obt_5", "Forma Tenebrosa", 3, 0, nil, nil, 6, "3 Sangue (3 turnos); imune a ataques físicos, vulnerável a fogo/sol", { id = "obt_tenebrous", shadowForm = true }, "Transforma o corpo inteiro em mancha fluida de escuridão pura (V20, p. 191)."),
        },
    },
    potence = {
        id = "potence", name = "Potência", hasPaths = false,
        powers = {
            p(1, "pot_1", "Potência 1", 0, 0, nil, nil, 6, "+1 dado Força passivo OU 1 Sangue = 1 sucesso automático no turno", nil, "Força vampírica sobre-humana em paradas de Força e dano corpo a corpo (V20, p. 192)."),
            p(2, "pot_2", "Potência 2", 0, 0, nil, nil, 6, "+2 dados Força passivos OU 1 Sangue = 2 sucessos automáticos", nil, "Eleva Potência para 2 dados ou 2 sucessos automáticos por 1 Sangue (V20, p. 192)."),
            p(3, "pot_3", "Potência 3", 0, 0, nil, nil, 6, "+3 dados Força passivos OU 1 Sangue = 3 sucessos automáticos", nil, "Eleva Potência para 3 dados ou 3 sucessos automáticos por 1 Sangue (V20, p. 192)."),
            p(4, "pot_4", "Potência 4", 0, 0, nil, nil, 6, "+4 dados Força passivos OU 1 Sangue = 4 sucessos automáticos", nil, "Eleva Potência para 4 dados ou 4 sucessos automáticos por 1 Sangue (V20, p. 192)."),
            p(5, "pot_5", "Potência 5", 0, 0, nil, nil, 6, "+5 dados Força passivos OU 1 Sangue = 5 sucessos automáticos", nil, "Eleva Potência para 5 dados ou 5 sucessos automáticos por 1 Sangue (V20, p. 192)."),
        },
    },
    presence = {
        id = "presence", name = "Presença", hasPaths = false,
        powers = {
            p(1, "pres_1", "Fascínio", 0, 0, "attr_carisma", "hab_performance", 7, "Dif 7 (afeta quantidade de pessoas conforme sucessos)", nil, "Desperta admiração magnética nos presentes ao redor (V20, p. 193)."),
            p(2, "pres_2", "Olhar Aterrorizante", 0, 0, "attr_carisma", "hab_intimidacao", 6, "Dif = Raciocínio + Coragem do alvo", nil, "Revela a face predatória vampírica causando medo paralisante ou fuga (V20, p. 194)."),
            p(3, "pres_3", "Transe", 0, 0, "attr_aparencia", "hab_empatia", 6, "Dif = FdV permanente do alvo", nil, "Inspira devoção emocional profunda no alvo por horas a semanas (V20, p. 195)."),
            p(4, "pres_4", "Convocação", 1, 0, "attr_carisma", "hab_labia", 5, "Dif 5 (conhecidos) ou 7 (encontro breve)", nil, "Chama psiquicamente um indivíduo conhecido para vir até você (V20, p. 195)."),
            p(5, "pres_5", "Majestade", 0, 1, nil, nil, 6, "1 FdV; alvos testam Coragem (dif = Carisma + Intimidação) p/ agir contra", { id = "pres_majesty", majestyActive = true }, "Aura soberana esmagadora que impede hostilidade direta na cena (V20, p. 196)."),
        },
    },
    protean = {
        id = "protean", name = "Metamorfose", hasPaths = false,
        powers = {
            p(1, "prot_1", "Olhos da Besta", 0, 0, nil, nil, 6, "Ativação livre (olhos vermelhos, visão total no escuro; +1 dif Social c/ mortais)", { id = "prot_eyes", nightVision = true }, "Enxerga perfeitamente na escuridão absoluta sem fonte de luz (V20, p. 197)."),
            p(2, "prot_2", "Garras da Besta", 1, 0, nil, nil, 6, "1 Sangue: garras causam Força + 1 de dano Agravado e -2 dif escalar", { id = "prot_claws", naturalAggravatedBonus = 1 }, "Transforma as unhas em garras letais que infligem dano Agravado (V20, p. 197)."),
            p(3, "prot_3", "Fusão com a Terra", 1, 0, nil, nil, 6, "1 Sangue: afunda no solo natural para proteção diurna", nil, "Funde o corpo à terra nua para abrigar-se do sol durante o dia (V20, p. 198)."),
            p(4, "prot_4", "Forma da Besta", 1, 0, nil, nil, 6, "1 Sangue (3 turnos): Forma de Lobo (For+1 Agrav, mov x2) ou Morcego (voo)", { id = "prot_beast", perceptionDiffMod = -2 }, "Assume a forma física de predador (lobo) ou fuga (morcego) (V20, p. 199)."),
            p(5, "prot_5", "Forma de Névoa", 1, 0, nil, nil, 6, "1 Sangue (3 turnos): imune a ataques físicos, -1 dado fogo/sol", { id = "prot_mist", mistForm = true }, "Dissolve o corpo em nuvem incorpórea de névoa (V20, p. 199)."),
        },
    },
    quietus = {
        id = "quietus", name = "Quietus", hasPaths = false,
        powers = {
            p(1, "quie_1", "Silêncio Mortal", 1, 0, nil, nil, 6, "1 Sangue (1 hora): anula todos os sons em raio de 6m", { id = "quie_silence", silenceAura = true }, "Cria zona de silêncio absoluto ao redor do Assamita (V20, p. 201)."),
            p(2, "quie_2", "Toque do Escorpião", 1, 0, "attr_fdv_ref", nil, 6, "Gasta Sangue + rola FdV (dif = Vigor + Fortitude do alvo) p/ reduzir Vigor", nil, "Converte vitae em veneno de contato que corrói o Vigor da vítima (V20, p. 201)."),
            p(3, "quie_3", "Chamado de Dagon", 0, 1, "attr_vigor", nil, 6, "Após tocar alvo, disputa estendida de Vigor contra Vigor da vítima (1 FdV)", nil, "Rompe os vasos internos do alvo à distância causando dano letal (V20, p. 202)."),
            p(4, "quie_4", "Carícia de Baal", 1, 0, nil, nil, 6, "1 Sangue por ataque na lâmina: converte dano da arma em Agravado", { id = "quie_baal", weaponAggravated = true }, "Ungir lâmina com vitae torna seu corte letalmente Agravado (V20, p. 202)."),
            p(5, "quie_5", "Gosto da Morte", 1, 0, "attr_vigor", "hab_esportes", 6, "Cospe sangue cáustico à distância (2 dados de dano Agravado por Sangue gasto)", nil, "Projeta jato ácido de vitae causando queimaduras Agravadas (V20, p. 203)."),
        },
    },
    serpentis = {
        id = "serpentis", name = "Serpentis", hasPaths = false,
        powers = {
            p(1, "serp_1", "Os Olhos da Serpente", 0, 0, nil, nil, 9, "Imobiliza mortais em contato visual; sobrenaturais resistem com FdV dif 9", nil, "Olhar dourado hipnótico que congela vítimas no lugar (V20, p. 208)."),
            p(2, "serp_2", "A Língua da Áspide", 0, 0, nil, nil, 6, "Língua bifurcada causa Força de dano Agravado e bebe sangue em combate", { id = "serp_tongue", naturalAggravatedBonus = 0 }, "Alonga a língua em ferrão cortante que causa feridas Agravadas (V20, p. 208)."),
            p(3, "serp_3", "A Pele da Víbora", 1, 1, nil, nil, 5, "1 Sangue + 1 FdV: dificuldade de Absorção cai para 5, mordida Agravada", { id = "serp_skin", soakDiffOverride = 5 }, "Escamas flexíveis reduzem dificuldade de Absorção para 5 e facilitam escapulir (V20, p. 209)."),
            p(4, "serp_4", "A Forma da Cobra", 1, 0, nil, nil, 6, "1 Sangue: transforma-se em naja negra gigante com mordida venenosa fatal", { id = "serp_cobra", cobraForm = true }, "Assume corpo ofídico letal a mortais e esguio em frestas (V20, p. 209)."),
            p(5, "serp_5", "O Coração das Trevas", 0, 0, nil, nil, 8, "Noite de lua nova: remove o próprio coração (-2 dif resistir Frenesi, imune a estaca)", nil, "Extrai e esconde o próprio coração em urna, impedindo paralisia por estaca (V20, p. 210)."),
        },
    },
    thaumaturgy = {
        id = "thaumaturgy", name = "Taumaturgia (Linha do Sangue)", hasPaths = true,
        powers = {
            p(1, "thau_1", "Um Gosto por Sangue", 0, 1, "attr_fdv_ref", nil, 4, "Testa FdV (dif = nível do poder + 3 = 4)", nil, "Identifica geração, sangue restante, natureza vampírica e diablerie por 1 gota (V20, p. 214)."),
            p(2, "thau_2", "Fúria do Sangue", 0, 1, "attr_fdv_ref", nil, 5, "Testa FdV dif 5 ao tocar alvo; força gasto de sangue da vítima", nil, "Obriga outro vampiro a queimar vitae involuntariamente e amplia dif. de Frenesi (V20, p. 214)."),
            p(3, "thau_3", "Sangue de Potência", 0, 1, "attr_fdv_ref", nil, 6, "Testa FdV dif 6; reduz efetivamente a Geração por 1 hora", nil, "Concentra temporariamente o próprio sangue para operar em Geração mais baixa (V20, p. 215)."),
            p(4, "thau_4", "Furto de Vitae", 0, 1, "attr_fdv_ref", nil, 7, "Testa FdV dif 7; drena sangue à distância (até 15m) sem Laço completo imediato", nil, "Arranca torrente de sangue da vítima pelo ar direto para o taumaturgo (V20, p. 215)."),
            p(5, "thau_5", "Caldeirão de Sangue", 0, 1, "attr_fdv_ref", nil, 8, "Testa FdV dif 8 ao toque; ferve 1 ponto de sangue por sucesso (1 Agravado cada)", nil, "Ferve o sangue nas veias do alvo, matando mortais e causando dano Agravado a Membros (V20, p. 216)."),
        },
    },
    vicissitude = {
        id = "vicissitude", name = "Vicissitude", hasPaths = false,
        powers = {
            p(1, "vici_1", "Aspecto Maleável", 1, 0, "attr_inteligencia", "hab_medicina", 6, "1 Sangue por parte alterada; Inteligência + Moldar Corpo/Medicina", nil, "Altera feições, voz, altura e tom de pele do próprio corpo (V20, p. 241)."),
            p(2, "vici_2", "Moldar Carne", 1, 0, "attr_destreza", "hab_medicina", 6, "1 Sangue; esculpe carne e gordura própria ou de terceiros", nil, "Deforma, desloca ou aprimora tecidos moles em si ou num alvo agarrado (V20, p. 242)."),
            p(3, "vici_3", "Moldar Ossos", 1, 0, "attr_forca", "hab_medicina", 7, "1 Sangue; esculpe ossos em espinhos ou armas (causa Letal sem anestesia)", nil, "Torce, funde e afia estruturas ósseas como armamento ou suplício (V20, p. 242)."),
            p(4, "vici_4", "Forma Horripilante", 2, 0, nil, nil, 6, "2 Sangue: +3 Força, +3 Destreza, +3 Vigor, Aparência 0, Briga +1 dano", { id = "vici_zulo", attrModPhysical = 3 }, "Assume a monstruosa forma guerreira Zulo com +3 em todos os Físicos (V20, p. 243)."),
            p(5, "vici_5", "Forma Sanguínea", 0, 0, nil, nil, 6, "Converte membros ou todo o corpo em vitae senciente imune a estacas/golpes", { id = "vici_bloodform", bloodForm = true }, "Liquefaz o próprio corpo em poça consciente de sangue vampírico (V20, p. 243)."),
        },
    },
}

return Catalog
