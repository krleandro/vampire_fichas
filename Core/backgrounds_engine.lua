local BgCatalog = require("Data.backgrounds_catalog")
local MFCatalog = require("Data.merits_flaws_catalog")

local BgEngine = {}

local function safeNum(val, default)
    local n = tonumber(val)
    if n == nil or n ~= n or n == math.huge or n == -math.huge then
        return default
    end
    return n
end

local function safeNonNegInt(val, default)
    return math.max(0, math.floor(safeNum(val, default or 0)))
end

function BgEngine.deriveSheetEffects(baseGeneration, backgroundsList)
    local baseGen = math.floor(safeNum(baseGeneration, 13))
    local genDots = 0
    local herdDots = 0
    local domainDots = 0
    local resDots = 0
    local fameDots = 0
    local statusDots = 0

    if type(backgroundsList) == "table" then
        for _, bg in ipairs(backgroundsList) do
            if type(bg) == "table" and bg.ativo ~= false and bg.ativo ~= "false" then
                local n = safeNonNegInt(bg.nivel, 0)
                if bg.bg_id == "generation" then
                    genDots = genDots + n
                elseif bg.bg_id == "herd" then
                    herdDots = math.min(5, herdDots + n)
                elseif bg.bg_id == "domain" then
                    domainDots = math.min(5, domainDots + n)
                elseif bg.bg_id == "resources" then
                    resDots = math.min(5, resDots + n)
                elseif bg.bg_id == "fame" then
                    fameDots = math.min(5, fameDots + n)
                elseif bg.bg_id == "status" then
                    statusDots = math.min(5, statusDots + n)
                end
            end
        end
    end

    local effGen = math.max(4, baseGen - genDots)
    return {
        effectiveGeneration = effGen,
        herdVessels = BgCatalog.HERD_VESSELS[herdDots] or 0,
        huntingBonusDice = herdDots,
        huntingDiffMod = domainDots > 0 and -domainDots or 0,
        resourcesLabel = BgCatalog.RESOURCES_TIERS[resDots] or BgCatalog.RESOURCES_TIERS[0],
        fameSocialDiffMod = fameDots > 0 and -fameDots or 0,
        statusSocialBonusDice = statusDots,
    }
end

function BgEngine.buildActionRoll(bgId, dots, attrVal)
    local entry = type(bgId) == "string" and BgCatalog.BACKGROUNDS[bgId] or nil
    local n = safeNonNegInt(dots, 0)
    local a = safeNonNegInt(attrVal, 0)
    if not entry or not entry.actionTitle or n <= 0 then
        return { canRoll = false, pool = 0, defaultDiff = 6, title = "Antecedente sem ação rolável" }
    end
    return {
        canRoll = true,
        pool = a + n,
        defaultDiff = entry.defaultDiff or 6,
        title = entry.actionTitle,
    }
end

function BgEngine.buildNuminaRoll(numinaId, dots, attrVal)
    local entry = type(numinaId) == "string" and MFCatalog.NUMINA[numinaId] or nil
    local n = safeNonNegInt(dots, 0)
    local a = safeNonNegInt(attrVal, 0)
    if not entry or n <= 0 then
        return {
            canRoll = false,
            pool = 0,
            poolAttr = nil,
            defaultDiff = 7,
            title = "Numina sem ação rolável",
        }
    end
    return {
        canRoll = true,
        pool = a + n,
        poolAttr = entry.poolAttr,
        defaultDiff = entry.defaultDiff or 7,
        title = entry.name,
    }
end

function BgEngine.aggregateMeritsFlaws(itemsList)
    local meritCost = 0
    local flawGain = 0
    local hugeSize = false
    local percDiffMod = 0
    local hasAddDisc = false
    local thinGen = nil

    if type(itemsList) == "table" then
        for _, it in ipairs(itemsList) do
            if type(it) == "table" and it.ativo ~= false and it.ativo ~= "false" then
                local cat = type(it.item_id) == "string" and MFCatalog.ITEMS[it.item_id] or nil
                local rawPts = (it.pontos ~= nil) and it.pontos or (cat and cat.pontos)
                local pts = safeNonNegInt(rawPts, 0)
                local itemTipo = it.tipo or (cat and cat.tipo) or "qualidade"

                if itemTipo == "defeito" then
                    flawGain = flawGain + pts
                else
                    meritCost = meritCost + pts
                end

                local eff = (cat and cat.effect) or it.mod_tipo
                if eff == "extra_bruised_box" then
                    hugeSize = true
                elseif eff == "perception_diff_-2" then
                    percDiffMod = percDiffMod - 2
                elseif eff == "perception_diff_+2" then
                    percDiffMod = percDiffMod + 2
                elseif eff == "additional_in_clan_disc" then
                    hasAddDisc = true
                elseif eff == "force_gen_14" then
                    thinGen = math.max(thinGen or 0, 14)
                elseif eff == "force_gen_15" then
                    thinGen = math.max(thinGen or 0, 15)
                end
            end
        end
    end

    return {
        totalMeritCost = meritCost,
        totalFlawGainRaw = flawGain,
        effectiveFlawBonus = math.min(7, flawGain),
        hugeSize = hugeSize,
        perceptionDiffMod = percDiffMod,
        hasAdditionalDisc = hasAddDisc,
        thinBloodGenOverride = thinGen,
    }
end

return BgEngine
