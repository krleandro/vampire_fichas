local Generations = require("Data.generations")

local Blood = {}

local function shallowCopy(t)
    local out = {}
    for k, v in pairs(t or {}) do out[k] = v end
    return out
end

function Blood.deriveStats(genNumber)
    return Generations.get(genNumber)
end

function Blood.spend(state, amount, opts)
    state = state or {}
    opts = opts or {}
    local baseAmount = tonumber(amount) or 0
    if baseAmount <= 0 then
        return { ok = true, newState = shallowCopy(state), costApplied = 0, error = nil }
    end

    local stats = Blood.deriveStats(state.generation)
    local cost = baseAmount
    if opts.forDisciplineOrHeal and stats.doubleCost then
        cost = cost * 2
    end

    local cur = tonumber(state.currentBlood) or 0
    local spentTurn = tonumber(state.spentThisTurn) or 0

    if cur < cost and not opts.storytellerOverride then
        return { ok = false, newState = shallowCopy(state), costApplied = 0, error = "Reserva de sangue insuficiente." }
    end

    if opts.forDisciplineOrHeal and stats.usableBlood < stats.bloodMax and not opts.storytellerOverride then
        local unusableFloor = stats.bloodMax - stats.usableBlood
        local usedSoFar = tonumber(state.thinBloodUsed) or 0
        if (cur - cost) < unusableFloor or (usedSoFar + cost) > stats.usableBlood then
            return {
                ok = false,
                newState = shallowCopy(state),
                costApplied = 0,
                error = "Sangue Fraco atingiu o limite de vitae utilizável para poderes/cura.",
            }
        end
    end

    if not opts.bypassTurnLimit and not opts.storytellerOverride then
        if (spentTurn + cost) > stats.perTurn then
            return {
                ok = false,
                newState = shallowCopy(state),
                costApplied = 0,
                error = string.format("Limite de gasto de sangue por turno excedido (%d/%d).", spentTurn + cost, stats.perTurn),
            }
        end
    end

    local nextSt = shallowCopy(state)
    nextSt.currentBlood = math.max(0, cur - cost)
    nextSt.spentThisTurn = spentTurn + cost
    if opts.forDisciplineOrHeal and stats.usableBlood < stats.bloodMax then
        nextSt.thinBloodUsed = (tonumber(state.thinBloodUsed) or 0) + cost
    end
    return { ok = true, newState = nextSt, costApplied = cost, error = nil }
end

function Blood.gain(state, amount)
    state = state or {}
    local stats = Blood.deriveStats(state.generation)
    local cur = tonumber(state.currentBlood) or 0
    local add = math.max(0, tonumber(amount) or 0)
    local nextSt = shallowCopy(state)
    nextSt.currentBlood = math.min(stats.bloodMax, cur + add)
    if add > 0 then
        nextSt.thinBloodUsed = 0
    end
    return { newState = nextSt, added = nextSt.currentBlood - cur }
end

function Blood.newTurn(state)
    state = state or {}
    local nextSt = shallowCopy(state)
    nextSt.spentThisTurn = 0
    return nextSt
end

function Blood.applyPhysicalBuff(state, attrKey, opts)
    state = state or {}
    opts = opts or {}
    local valid = { forca = true, destreza = true, vigor = true }
    if not valid[attrKey] then
        return { ok = false, newState = shallowCopy(state), effectiveAttr = 0, temporaryAboveMax = false, error = "Apenas Atributos Físicos recebem Blood Buff." }
    end

    local stats = Blood.deriveStats(state.generation)
    local baseVal = tonumber(state["attr_" .. attrKey]) or 1
    local curBuff = tonumber(state["buff_" .. attrKey]) or 0
    local maxAllowed = stats.traitMax + 1

    if (baseVal + curBuff + 1) > maxAllowed and not opts.storytellerOverride then
        return {
            ok = false,
            newState = shallowCopy(state),
            effectiveAttr = baseVal + curBuff,
            temporaryAboveMax = (baseVal + curBuff) > stats.traitMax,
            error = string.format("Blood Buff limitado a %d (máx. da geração + 1; V20 p. 268).", maxAllowed),
        }
    end

    local spendRes = Blood.spend(state, 1, {
        forDisciplineOrHeal = true,
        bypassTurnLimit = opts.bypassTurnLimit,
        storytellerOverride = opts.storytellerOverride,
    })
    if not spendRes.ok then
        return {
            ok = false,
            newState = spendRes.newState,
            effectiveAttr = baseVal + curBuff,
            temporaryAboveMax = (baseVal + curBuff) > stats.traitMax,
            error = spendRes.error,
        }
    end

    local nextSt = spendRes.newState
    nextSt["buff_" .. attrKey] = curBuff + 1
    local eff = baseVal + nextSt["buff_" .. attrKey]
    return {
        ok = true,
        newState = nextSt,
        effectiveAttr = eff,
        temporaryAboveMax = eff > stats.traitMax,
        error = nil,
    }
end

function Blood.clearSceneBuffs(state)
    state = state or {}
    local nextSt = shallowCopy(state)
    nextSt.buff_forca = 0
    nextSt.buff_destreza = 0
    nextSt.buff_vigor = 0
    nextSt.spentThisTurn = 0
    return nextSt
end

return Blood
