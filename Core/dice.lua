local Traits = require("Data.attributes_abilities")

local Dice = {}

local function clamp(val, minV, maxV)
    if val < minV then return minV end
    if val > maxV then return maxV end
    return val
end

local function degreeLabel(total)
    if total <= 0 then return "Nenhum" end
    if total == 1 then return "Marginal" end
    if total == 2 then return "Moderado" end
    if total == 3 then return "Completo" end
    if total == 4 then return "Excepcional" end
    return "Fenomenal"
end

function Dice.buildPool(params)
    params = params or {}
    local warnings = {}
    local attrVal = tonumber(params.attrVal) or 0
    local abilityVal = tonumber(params.abilityVal) or 0
    local bonusDice = tonumber(params.bonusDice) or 0
    local diff = tonumber(params.difficulty) or 6
    local diffMod = tonumber(params.difficultyMod) or 0
    local autoSuccesses = tonumber(params.autoSuccesses) or 0
    if params.spendWillpower then
        autoSuccesses = autoSuccesses + 1
    end

    if params.incapacitated and not params.ignoreWoundPenalty and not params.storytellerOverride then
        return {
            canRoll = false,
            pool = 0,
            effectiveDifficulty = clamp(diff, 2, 10),
            autoSuccesses = autoSuccesses,
            warnings = warnings,
            blockReason = "Personagem Incapacitado não pode realizar ações físicas.",
        }
    end

    if params.abilityCategory and abilityVal <= 0 then
        local rule = Traits.getZeroRankRule(params.abilityCategory)
        if not rule.allowed and not params.storytellerOverride then
            return {
                canRoll = false,
                pool = 0,
                effectiveDifficulty = clamp(diff, 2, 10),
                autoSuccesses = autoSuccesses,
                warnings = warnings,
                blockReason = rule.reason,
            }
        end
        if rule.diffMod ~= 0 then
            diffMod = diffMod + rule.diffMod
            table.insert(warnings, rule.reason)
        end
    end

    local woundPen = 0
    if not params.ignoreWoundPenalty then
        woundPen = math.abs(tonumber(params.woundPenalty) or 0)
    end

    local pool = attrVal + abilityVal + bonusDice - woundPen
    local effectiveDiff = clamp(diff + diffMod, 2, 10)

    if pool <= 0 and autoSuccesses <= 0 and not params.storytellerOverride then
        return {
            canRoll = false,
            pool = 0,
            effectiveDifficulty = effectiveDiff,
            autoSuccesses = 0,
            warnings = warnings,
            blockReason = "Parada reduzida a zero ou menos pelas penalidades.",
        }
    end

    return {
        canRoll = true,
        pool = math.max(0, pool),
        effectiveDifficulty = effectiveDiff,
        autoSuccesses = autoSuccesses,
        warnings = warnings,
        blockReason = nil,
    }
end

function Dice.evaluate(results, difficulty, options)
    options = options or {}
    local diff = clamp(tonumber(difficulty) or 6, 2, 10)
    local specialty = options.specialty == true
    local autoSuccesses = tonumber(options.autoSuccesses) or 0
    if options.spendWillpower then
        autoSuccesses = autoSuccesses + 1
    end

    local rawSuccesses = 0
    local ones = 0
    results = results or {}

    for _, v in ipairs(results) do
        local face = tonumber(v) or 0
        if face == 1 then
            ones = ones + 1
        elseif face >= diff then
            if face == 10 and specialty then
                rawSuccesses = rawSuccesses + 2
            else
                rawSuccesses = rawSuccesses + 1
            end
        end
    end

    local rolledNet = math.max(0, rawSuccesses - ones)
    local totalSuccesses = rolledNet + autoSuccesses

    local outcome = "failure"
    if totalSuccesses > 0 then
        outcome = "success"
    elseif rawSuccesses == 0 and autoSuccesses == 0 and ones > 0 then
        outcome = "botch"
    end

    return {
        rawSuccesses = rawSuccesses,
        ones = ones,
        rolledNet = rolledNet,
        autoSuccesses = autoSuccesses,
        totalSuccesses = totalSuccesses,
        outcome = outcome,
        degree = degreeLabel(totalSuccesses),
        difficulty = diff,
        diceCount = #results,
    }
end

return Dice
