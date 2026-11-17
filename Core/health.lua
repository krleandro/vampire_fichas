local Blood = require("Core.generation_blood")

local Health = {}

Health.STANDARD_LEVELS = {
    { name = "Escoriado",         penalty = 0,  incapacitated = false },
    { name = "Machucado",         penalty = -1, incapacitated = false },
    { name = "Ferido",            penalty = -1, incapacitated = false },
    { name = "Ferido Gravemente", penalty = -2, incapacitated = false },
    { name = "Espancado",         penalty = -2, incapacitated = false },
    { name = "Aleijado",          penalty = -5, incapacitated = false },
    { name = "Incapacitado",      penalty = 0,  incapacitated = true  },
}

local function copyState(s)
    local o = {}
    for k, v in pairs(s or {}) do o[k] = v end
    return o
end

local function buildLevels(hugeSize)
    local levels = {}
    if hugeSize then
        table.insert(levels, { name = "Escoriado (Extra)", penalty = 0, incapacitated = false })
    end
    for _, lv in ipairs(Health.STANDARD_LEVELS) do
        table.insert(levels, lv)
    end
    return levels
end

function Health.getStatus(state)
    state = state or {}
    local levels = buildLevels(state.hugeSize == true)
    local totalBoxes = #levels
    local agg = math.max(0, math.floor(tonumber(state.aggravated) or 0))
    local let = math.max(0, math.floor(tonumber(state.lethal) or 0))
    local bas = math.max(0, math.floor(tonumber(state.bashing) or 0))

    local boxes = {}
    for i = 1, totalBoxes do
        if i <= agg then
            boxes[i] = "*"
        elseif i <= (agg + let) then
            boxes[i] = "X"
        elseif i <= (agg + let + bas) then
            boxes[i] = "/"
        else
            boxes[i] = ""
        end
    end

    local filled = math.min(totalBoxes, agg + let + bas)
    local currentLevelName = "Saudável"
    local penalty = 0
    local incapacitated = false

    if filled > 0 then
        local lv = levels[filled]
        currentLevelName = lv.name
        penalty = lv.penalty
        incapacitated = lv.incapacitated
    end

    local torporOrDeath = nil
    if agg >= totalBoxes then
        torporOrDeath = state.isVampire and "Morte Final" or "Morte"
    elseif (agg + let) >= totalBoxes then
        torporOrDeath = state.isVampire and "Torpor (ou Morte se sem sangue)" or "Agonia Crítica / Morte"
    end

    return {
        totalBoxes = totalBoxes,
        boxes = boxes,
        currentLevelName = currentLevelName,
        penalty = penalty,
        incapacitated = incapacitated,
        torporOrDeath = torporOrDeath,
    }
end

function Health.applyDamage(state, amount, damageType, opts)
    opts = opts or {}
    local nextSt = copyState(state)
    local dmg = math.max(0, math.floor(tonumber(amount) or 0))
    local dtype = damageType or "bashing"

    local isVampire
    if opts.isVampire ~= nil then
        isVampire = (opts.isVampire == true)
    else
        isVampire = (nextSt.isVampire == true)
    end

    if isVampire and opts.isFirearm and not opts.headshot and dtype == "lethal" then
        dtype = "bashing"
    end

    if isVampire and dtype == "bashing" and opts.halveBashing then
        dmg = math.floor(dmg / 2)
    end

    local levels = buildLevels(nextSt.hugeSize == true)
    local cap = #levels
    local agg = math.max(0, math.floor(tonumber(nextSt.aggravated) or 0))
    local let = math.max(0, math.floor(tonumber(nextSt.lethal) or 0))
    local bas = math.max(0, math.floor(tonumber(nextSt.bashing) or 0))

    for _ = 1, dmg do
        if dtype == "aggravated" then
            if (agg + let + bas) < cap then
                agg = agg + 1
            elseif bas > 0 then
                bas = bas - 1
                agg = agg + 1
            elseif let > 0 then
                let = let - 1
                agg = agg + 1
            end
        elseif dtype == "lethal" then
            if (agg + let + bas) < cap then
                let = let + 1
            elseif bas > 0 then
                bas = bas - 1
                let = let + 1
            elseif (agg + let) < cap then
                let = let + 1
            end
        else -- bashing
            if (agg + let + bas) < cap then
                bas = bas + 1
            elseif bas > 0 then
                bas = bas - 1
                let = let + 1
            end
        end
    end

    nextSt.aggravated = math.min(cap, agg)
    nextSt.lethal = math.min(cap - nextSt.aggravated, let)
    nextSt.bashing = math.min(cap - nextSt.aggravated - nextSt.lethal, bas)
    return nextSt
end

function Health.buildSoakPool(state, damageType)
    state = state or {}
    local vigor = math.max(0, (tonumber(state.attr_vigor) or 1) + (tonumber(state.buff_vigor) or 0))
    local fort = math.max(0, tonumber(state.fortitude) or 0)
    local armor = math.max(0, tonumber(state.armor) or 0)
    local diff = tonumber(state.soakDifficulty) or 6
    local isVampOrGhoul = (state.isVampire == true) or (state.isGhoul == true)

    if damageType == "aggravated" then
        if fort <= 0 then
            return { canSoak = false, pool = 0, difficulty = diff, reason = "Dano Agravado exige Fortitude para absorção." }
        end
        return { canSoak = true, pool = fort, difficulty = diff, reason = nil }
    elseif damageType == "lethal" then
        if not isVampOrGhoul and armor <= 0 and fort <= 0 then
            return { canSoak = false, pool = 0, difficulty = diff, reason = "Mortais não absorvem dano Letal sem armadura." }
        end
        local base = isVampOrGhoul and vigor or 0
        return { canSoak = true, pool = base + fort + armor, difficulty = diff, reason = nil }
    end

    return { canSoak = true, pool = vigor + fort + armor, difficulty = diff, reason = nil }
end

function Health.healWithBlood(state, damageType, opts)
    state = state or {}
    opts = opts or {}
    if not state.isVampire and not state.isGhoul then
        return { ok = false, newState = copyState(state), error = "Apenas vampiros e carniçais curam ferimentos com sangue." }
    end

    if damageType == "aggravated" then
        if (tonumber(state.aggravated) or 0) <= 0 then
            return { ok = false, newState = copyState(state), error = "Nenhum nível de dano Agravado para curar." }
        end
        local wp = tonumber(state.fdv_temp) or 0
        if opts.useWillpowerForExtra == true and wp < 1 and not opts.storytellerOverride then
            return {
                ok = false,
                newState = copyState(state),
                error = "Força de Vontade temporária insuficiente para curar nível Agravado adicional.",
            }
        end
        local sp = Blood.spend(state, 5, {
            forDisciplineOrHeal = true,
            bypassTurnLimit = true,
            storytellerOverride = opts.storytellerOverride,
        })
        if not sp.ok then
            return { ok = false, newState = sp.newState, error = sp.error }
        end
        local nextSt = sp.newState
        nextSt.aggravated = math.max(0, (tonumber(nextSt.aggravated) or 0) - 1)
        if opts.useWillpowerForExtra then
            nextSt.fdv_temp = math.max(0, wp - 1)
        end
        return { ok = true, newState = nextSt, error = nil }
    end

    local field = (damageType == "lethal") and "lethal" or "bashing"
    if (tonumber(state[field]) or 0) <= 0 then
        return { ok = false, newState = copyState(state), error = "Nenhum dano desse tipo para curar." }
    end

    local sp = Blood.spend(state, 1, {
        forDisciplineOrHeal = true,
        bypassTurnLimit = opts.bypassTurnLimit,
        storytellerOverride = opts.storytellerOverride,
    })
    if not sp.ok then
        return { ok = false, newState = sp.newState, error = sp.error }
    end
    local nextSt = sp.newState
    nextSt[field] = math.max(0, (tonumber(nextSt[field]) or 0) - 1)
    return { ok = true, newState = nextSt, error = nil }
end

return Health
