local AttributesAbilities = {}

AttributesAbilities.ATTRIBUTE_ORDER = {
    "attr_forca", "attr_destreza", "attr_vigor",
    "attr_carisma", "attr_manipulacao", "attr_aparencia",
    "attr_percepcao", "attr_inteligencia", "attr_raciocinio",
}

AttributesAbilities.ATTRIBUTES = {
    attr_forca        = { id = "attr_forca",        name = "Força",        category = "physical" },
    attr_destreza     = { id = "attr_destreza",     name = "Destreza",     category = "physical" },
    attr_vigor        = { id = "attr_vigor",        name = "Vigor",        category = "physical" },
    attr_carisma      = { id = "attr_carisma",      name = "Carisma",      category = "social" },
    attr_manipulacao  = { id = "attr_manipulacao",  name = "Manipulação",  category = "social" },
    attr_aparencia    = { id = "attr_aparencia",    name = "Aparência",    category = "social" },
    attr_percepcao    = { id = "attr_percepcao",    name = "Percepção",    category = "mental" },
    attr_inteligencia = { id = "attr_inteligencia", name = "Inteligência", category = "mental" },
    attr_raciocinio   = { id = "attr_raciocinio",   name = "Raciocínio",   category = "mental" },
}

AttributesAbilities.ABILITY_ORDER = {
    -- Talentos (10)
    "hab_prontidao", "hab_esportes", "hab_consciencia", "hab_briga", "hab_empatia",
    "hab_expressao", "hab_intimidacao", "hab_lideranca", "hab_manha", "hab_labia",
    -- Perícias (10)
    "hab_empatia_animais", "hab_oficios", "hab_conducao", "hab_etiqueta", "hab_armas_fogo",
    "hab_arrombamento", "hab_armas_brancas", "hab_performance", "hab_furtividade", "hab_sobrevivencia",
    -- Conhecimentos (10)
    "hab_academicos", "hab_computador", "hab_financas", "hab_investigacao", "hab_direito",
    "hab_medicina", "hab_ocultismo", "hab_politica", "hab_ciencias", "hab_tecnologia",
}

AttributesAbilities.ABILITIES = {
    hab_prontidao       = { id = "hab_prontidao",       name = "Prontidão",           category = "talents" },
    hab_esportes        = { id = "hab_esportes",        name = "Esportes",            category = "talents" },
    hab_consciencia     = { id = "hab_consciencia",     name = "Consciência",         category = "talents" },
    hab_briga           = { id = "hab_briga",           name = "Briga",               category = "talents" },
    hab_empatia         = { id = "hab_empatia",         name = "Empatia",             category = "talents" },
    hab_expressao       = { id = "hab_expressao",       name = "Expressão",           category = "talents" },
    hab_intimidacao     = { id = "hab_intimidacao",     name = "Intimidação",         category = "talents" },
    hab_lideranca       = { id = "hab_lideranca",       name = "Liderança",           category = "talents" },
    hab_manha           = { id = "hab_manha",           name = "Manha",               category = "talents" },
    hab_labia           = { id = "hab_labia",           name = "Lábia",               category = "talents" },

    hab_empatia_animais = { id = "hab_empatia_animais", name = "Empatia com Animais", category = "skills" },
    hab_oficios         = { id = "hab_oficios",         name = "Ofícios",             category = "skills" },
    hab_conducao        = { id = "hab_conducao",        name = "Condução",            category = "skills" },
    hab_etiqueta        = { id = "hab_etiqueta",        name = "Etiqueta",            category = "skills" },
    hab_armas_fogo      = { id = "hab_armas_fogo",      name = "Armas de Fogo",       category = "skills" },
    hab_arrombamento    = { id = "hab_arrombamento",    name = "Arrombamento",        category = "skills" },
    hab_armas_brancas   = { id = "hab_armas_brancas",   name = "Armas Brancas",       category = "skills" },
    hab_performance     = { id = "hab_performance",     name = "Performance",         category = "skills" },
    hab_furtividade     = { id = "hab_furtividade",     name = "Furtividade",         category = "skills" },
    hab_sobrevivencia   = { id = "hab_sobrevivencia",   name = "Sobrevivência",       category = "skills" },

    hab_academicos      = { id = "hab_academicos",      name = "Acadêmicos",          category = "knowledges" },
    hab_computador      = { id = "hab_computador",      name = "Computador",          category = "knowledges" },
    hab_financas        = { id = "hab_financas",        name = "Finanças",            category = "knowledges" },
    hab_investigacao    = { id = "hab_investigacao",    name = "Investigação",        category = "knowledges" },
    hab_direito         = { id = "hab_direito",         name = "Direito",             category = "knowledges" },
    hab_medicina        = { id = "hab_medicina",        name = "Medicina",            category = "knowledges" },
    hab_ocultismo       = { id = "hab_ocultismo",       name = "Ocultismo",           category = "knowledges" },
    hab_politica        = { id = "hab_politica",        name = "Política",            category = "knowledges" },
    hab_ciencias        = { id = "hab_ciencias",        name = "Ciências",            category = "knowledges" },
    hab_tecnologia      = { id = "hab_tecnologia",      name = "Tecnologia",          category = "knowledges" },
}

function AttributesAbilities.getZeroRankRule(category)
    if category == "skills" then
        return { allowed = true, diffMod = 1, reason = "Perícia sem pontos: +1 na dificuldade (V20, p. 253)." }
    elseif category == "knowledges" then
        return { allowed = false, diffMod = 0, reason = "Conhecimento sem pontos não pode ser testado sem autorização do Narrador (V20, p. 253)." }
    end
    return { allowed = true, diffMod = 0, reason = nil }
end

return AttributesAbilities
