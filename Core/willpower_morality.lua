local MoralityVirtues = require("Data.morality_virtues")

local WM = {}

local function copyState(s)
    local o = {}
    for k, v in pairs(s or {}) do o[k] = v end
    return o
end

local function safeNum(val, default)
    local n = tonumber(val)
    if n == nil or n ~= n then return default end
    return n
end

function WM.spendWillpower(state, amount, opts)
    state = state or {}
    opts = opts or {}
    local cost = math.max(1, math.floor(safeNum(amount, 1)))
    local cur = math.floor(safeNum(state.fdv_temp, 0))
    local override = state.storytellerOverride or opts.storytellerOverride
    if cur < cost and not override then
        return { ok = false, newState = copyState(state), error = "Força de Vontade temporária insuficiente." }
    end
    local nextSt = copyState(state)
    nextSt.fdv_temp = math.max(0, cur - cost)
    return { ok = true, newState = nextSt, error = nil }
end

function WM.awakenNightly(state)
    state = state or {}
    local nextSt = copyState(state)
    if not state.isVampire then
        return { ok = true, newState = nextSt, hungerFrenzyRisk = false, warning = nil }
    end
    local cur = math.floor(safeNum(state.currentBlood, 0))
    if cur <= 0 then
        return {
            ok = false,
            newState = nextSt,
            hungerFrenzyRisk = true,
            warning = "Sem sangue ao despertar: personagem entra em Torpor por inanição!",
        }
    end
    nextSt.currentBlood = cur - 1
    nextSt.spentThisTurn = 0
    local selfControl = math.floor(safeNum(state.virtude2_val, 1))
    local threshold = math.max(2, 7 - selfControl)
    local hungry = nextSt.currentBlood <= threshold
    return {
        ok = true,
        newState = nextSt,
        hungerFrenzyRisk = hungry,
        warning = hungry and string.format("Fome intensa (%d pts restantes): risco de Frenesi diante de sangue!", nextSt.currentBlood) or nil,
    }
end

function WM.prepareFrenzyCheck(state, stimulusDiff)
    state = state or {}
    local baseDiff = math.floor(safeNum(stimulusDiff, 6))
    local v2 = math.max(0, math.floor(safeNum(state.virtude2_val, 1)))
    local notes = { "Acumule 5 sucessos em testes estendidos para conter a Besta totalmente." }
    local canAvoidWP = true

    if state.virtude2_tipo == "instinto" then
        table.insert(notes, "Instinto: controla e cavalga o Frenesi em vez de resistir passivamente (V20, p. 313).")
    end

    if state.cla_id == "brujah" then
        baseDiff = math.min(10, baseDiff + 2)
        canAvoidWP = false
        table.insert(notes, "Fraqueza Brujah: +2 na dificuldade (máx. 10) e proibido gastar FdV para evitar o Frenesi (V20, p. 49).")
    end

    return {
        pool = v2,
        difficulty = math.max(2, math.min(10, baseDiff)),
        canAvoidWithWillpower = canAvoidWP,
        notes = notes,
    }
end

function WM.prepareRotschreckCheck(state, stimulusDiff)
    state = state or {}
    local baseDiff = math.floor(safeNum(stimulusDiff, 6))
    local courage = math.max(0, math.floor(safeNum(state.virtude3_val, 1)))
    return {
        pool = courage,
        difficulty = math.max(2, math.min(10, baseDiff)),
    }
end

function WM.prepareDegenerationCheck(state)
    state = state or {}
    local v1 = math.max(0, math.floor(safeNum(state.virtude1_val, 1)))
    local vName = (state.virtude1_tipo == "conviccao") and "Convicção" or "Consciência"
    return {
        pool = v1,
        difficulty = 8,
        virtueUsed = vName,
    }
end

WM.getAuraModifier = MoralityVirtues.getAuraModifier

return WM
