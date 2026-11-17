local MoralityVirtues = {}

MoralityVirtues.PATHS = {
    { id = "humanidade",   name = "Humanidade",                v1 = "consciencia", v2 = "autocontrole" },
    { id = "metamorfose",  name = "Trilha da Metamorfose",     v1 = "conviccao",   v2 = "instinto" },
    { id = "noite",        name = "Trilha da Noite",           v1 = "conviccao",   v2 = "instinto" },
    { id = "ossos",        name = "Trilha dos Ossos",          v1 = "conviccao",   v2 = "autocontrole" },
    { id = "sangue",       name = "Trilha do Sangue",          v1 = "conviccao",   v2 = "autocontrole" },
    { id = "tifao",        name = "Trilha de Tifão",           v1 = "conviccao",   v2 = "autocontrole" },
    { id = "paradoxo",     name = "Trilha do Paradoxo",        v1 = "conviccao",   v2 = "autocontrole" },
    { id = "reis",         name = "Trilha dos Reis / Honra",   v1 = "conviccao",   v2 = "autocontrole" },
}

MoralityVirtues.FRENZY_STIMULI = {
    { label = "Cheiro de sangue (faminto)", diff = 4 },
    { label = "Visão de sangue (faminto)",  diff = 6 },
    { label = "Humilhação / Provocação",    diff = 4 },
    { label = "Ameaça à vida / Amado ferido", diff = 6 },
    { label = "Gosto de sangue (faminto)",  diff = 8 },
}

MoralityVirtues.ROTSCHRECK_STIMULI = {
    { label = "Acender isqueiro / vela",    diff = 3 },
    { label = "Tocha / Fogueira pequena",   diff = 5 },
    { label = "Fogo próximo / Incêndio",    diff = 7 },
    { label = "Queimadura / Luz solar velada", diff = 8 },
    { label = "Luz solar direta",           diff = 9 },
}

function MoralityVirtues.getAuraModifier(score)
    local s = tonumber(score)
    if s == nil or s ~= s then s = 7 end
    s = math.floor(s)
    if s >= 10 then return { diffMod = -2, label = "Radiante (-2 dif Social)" } end
    if s >= 8  then return { diffMod = -1, label = "Calorosa (-1 dif Social)" } end
    if s >= 4  then return { diffMod = 0,  label = "Neutra (0 dif Social)" } end
    if s >= 2  then return { diffMod = 1,  label = "Fria / Predatória (+1 dif Social)" } end
    if s == 1  then return { diffMod = 2,  label = "Monstruosa (+2 dif Social)" } end
    return { diffMod = 5, label = "Perdido para a Besta" }
end

return MoralityVirtues
