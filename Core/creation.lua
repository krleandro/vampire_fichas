local Creation = {}

local function safeNum(val, default)
    local n = tonumber(val)
    if n == nil or n ~= n or n == math.huge or n == -math.huge then
        return default
    end
    return n
end

Creation.FREEBIE_COSTS = {
    attributes = 5,
    abilities = 2,
    disciplines = 7,
    backgrounds = 1,
    virtues = 2,
    morality = 1,
    willpower = 1,
    merits = 1, -- multiplicado pelos pontos da qualidade
}

local FREEBIE_KEYS_ORDER = {
    "attributes", "abilities", "disciplines", "backgrounds",
    "virtues", "morality", "willpower", "merits",
}

Creation.PROFILES = {
    vampire_neonate = {
        attr = { 7, 5, 3 }, abilities = { 13, 9, 5 }, disciplines = 3, backgrounds = 5, virtues = 7, freebies = 15,
    },
    mortal_standard_643 = {
        attr = { 6, 4, 3 }, abilities = { 11, 7, 4 }, disciplines = 0, backgrounds = 5, virtues = 7, freebies = 21,
    },
    mortal_heroic_753 = {
        attr = { 7, 5, 3 }, abilities = { 13, 9, 5 }, disciplines = 0, backgrounds = 5, virtues = 7, freebies = 15,
    },
}

local function sortedDesc(list)
    local copy = {}
    if type(list) == "table" then
        for i, v in ipairs(list) do
            copy[i] = safeNum(v, 0)
        end
    end
    table.sort(copy, function(a, b) return a > b end)
    return copy
end

local function matchesTargets(given, targets, errors, label)
    local s = sortedDesc(given)
    for i = 1, #targets do
        local val = s[i] or 0
        if val > targets[i] then
            table.insert(errors, string.format("%s excede o limite do grupo %d (%d > %d).", label, i, val, targets[i]))
        elseif val < targets[i] then
            table.insert(errors, string.format("%s possui pontos não distribuídos no grupo %d (%d < %d).", label, i, val, targets[i]))
        end
    end
    for i = #targets + 1, #s do
        if (s[i] or 0) ~= 0 then
            table.insert(errors, string.format("%s possui grupo excedente inválido na posição %d.", label, i))
        end
    end
end

function Creation.validate(state)
    state = type(state) == "table" and state or {}
    local prof = Creation.PROFILES[state.profile or "vampire_neonate"] or Creation.PROFILES.vampire_neonate
    local errors = {}

    matchesTargets(state.attrGroups or { 0, 0, 0 }, prof.attr, errors, "Atributos")
    matchesTargets(state.abilityGroups or { 0, 0, 0 }, prof.abilities, errors, "Habilidades")

    if safeNum(state.maxBaseAbility, 0) > 3 then
        table.insert(errors, "Nenhuma Habilidade pode ultrapassar 3 pontos antes dos Pontos de Bônus (V20, p. 80).")
    end

    if state.cla_id == "nosferatu" and safeNum(state.attr_aparencia, 0) ~= 0 then
        table.insert(errors, "Nosferatu possui Aparência obrigatoriamente igual a 0.")
    end

    if safeNum(state.baseDisciplines, 0) ~= prof.disciplines then
        table.insert(errors, string.format("Disciplinas iniciais devem somar %d pontos.", prof.disciplines))
    end
    if safeNum(state.baseBackgrounds, 0) ~= prof.backgrounds then
        table.insert(errors, string.format("Antecedentes iniciais devem somar %d pontos.", prof.backgrounds))
    end
    if safeNum(state.baseVirtues, 0) ~= prof.virtues then
        table.insert(errors, string.format("Virtudes iniciais devem somar %d pontos.", prof.virtues))
    end

    local flawBonus = math.min(7, math.max(0, math.floor(safeNum(state.flawsBonus, 0))))
    local available = prof.freebies + flawBonus
    local fp = type(state.freebiePurchases) == "table" and state.freebiePurchases or {}
    local spent = 0
    for _, k in ipairs(FREEBIE_KEYS_ORDER) do
        local cost = Creation.FREEBIE_COSTS[k]
        local qty = safeNum(fp[k], 0)
        if qty < 0 then
            table.insert(errors, string.format("Compra negativa inválida de Pontos de Bônus em '%s'.", k))
            qty = 0
        end
        spent = spent + (qty * cost)
    end

    if spent > available then
        table.insert(errors, string.format("Pontos de Bônus excedidos (%d gastos de %d disponíveis).", spent, available))
    end

    return {
        valid = (#errors == 0),
        freebiesAvailable = available,
        freebiesSpent = spent,
        freebiesRemaining = available - spent,
        errors = errors,
    }
end

function Creation.applyMortalSupernaturalMode(state, mode)
    local nextSt = {}
    if type(state) == "table" then
        for k, v in pairs(state) do
            nextSt[k] = v
        end
    end

    if mode == "carnical" then
        nextSt.mortal_sobrenatural_modo = "carnical"
        nextSt.isGhoul = true
        nextSt.hasNumina = false
        nextSt.sangue_max = 2
        nextSt.sangue_por_turno = 1
        nextSt.ghoulPotence = 1
    elseif mode == "numina" then
        nextSt.mortal_sobrenatural_modo = "numina"
        nextSt.isGhoul = false
        nextSt.hasNumina = true
        nextSt.sangue_max = 0
        nextSt.sangue_por_turno = 0
        nextSt.ghoulPotence = 0
    else
        nextSt.mortal_sobrenatural_modo = "humano"
        nextSt.isGhoul = false
        nextSt.hasNumina = false
        nextSt.sangue_max = 0
        nextSt.sangue_por_turno = 0
        nextSt.ghoulPotence = 0
    end

    return nextSt
end

return Creation
