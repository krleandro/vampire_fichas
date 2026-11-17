local BMCat = require("Data.blood_magic_catalog")
local Blood = require("Core.generation_blood")
local WM = require("Core.willpower_morality")

local BMEngine = {}

local function copyState(s)
    local o = {}
    for k, v in pairs(s or {}) do o[k] = v end
    return o
end

local function isTrue(v)
    return v == true or v == "true" or v == 1 or v == "1"
end

local function safeNonNegInt(v, default)
    local n = tonumber(v)
    if n == nil or n ~= n or n == math.huge or n == -math.huge then return default or 0 end
    n = math.floor(n)
    return n < 0 and 0 or n
end

local function resolveOverride(state, opts)
    if opts and opts.storytellerOverride ~= nil then
        return isTrue(opts.storytellerOverride)
    end
    return isTrue(state and state.storytellerOverride)
end

local function spendWillpowerNormalized(nextSt, wCost, override)
    local rawStateOverride = nextSt.storytellerOverride
    nextSt.storytellerOverride = nil
    local wRes = WM.spendWillpower(nextSt, wCost, { storytellerOverride = override })
    nextSt.storytellerOverride = rawStateOverride
    if wRes.newState then
        wRes.newState.storytellerOverride = rawStateOverride
    end
    return wRes
end

function BMEngine.derivePrimaryPathLevel(discDots)
    return math.min(5, safeNonNegInt(discDots, 0))
end

function BMEngine.validateSecondaryPathUpgrade(params)
    params = params or {}
    local parentDots = safeNonNegInt(params.parentDiscDots, 0)
    local target = safeNonNegInt(params.targetLevel, 1)
    local primId = params.primaryPathId or ""
    local secId = params.secondaryPathId or ""

    if secId == "" then
        return { ok = false, error = "Selecione uma Linha Secundária válida antes de evoluir." }
    end
    if primId ~= "" and primId == secId then
        return { ok = false, error = "A Linha Secundária não pode ser idêntica à Linha Primária." }
    end
    if target > 5 then
        return { ok = false, error = "Linhas de Taumaturgia/Necromancia têm nível máximo 5." }
    end
    if target >= 1 and parentDots < 2 then
        return { ok = false, error = "Exige nível mínimo 2 na Linha Primária/Disciplina para iniciar Linha Secundária (V20, p. 212)." }
    end
    local primLvl = BMEngine.derivePrimaryPathLevel(parentDots)
    if target >= 1 and primLvl < 5 and target >= primLvl then
        return { ok = false, error = string.format("Linha Secundária (%d) deve permanecer inferior à Linha Primária (%d) até que a Primária atinja 5 (V20, p. 212).", target, primLvl) }
    end
    return { ok = true, error = nil }
end

function BMEngine.getPathTable(tradition, pathId)
    if tradition == "necromancy" then
        return BMCat.NECROMANCY_PATHS[pathId]
    end
    return BMCat.THAUMATURGY_PATHS[pathId]
end

function BMEngine.activatePathPower(state, tradition, pathId, pathDots, level, opts)
    opts = opts or {}
    local override = resolveOverride(state, opts)
    local pTable = BMEngine.getPathTable(tradition, pathId)
    if not pTable then
        return { ok = false, newState = copyState(state), rollSpec = nil, error = "Linha de Magia do Sangue não encontrada." }
    end
    local lvl = math.max(1, math.min(5, safeNonNegInt(level, 1)))
    local dots = safeNonNegInt(pathDots, 0)
    if dots < lvl and not override then
        return { ok = false, newState = copyState(state), rollSpec = nil, error = string.format("Nível insuficiente na %s (possui %d, requer %d).", pTable.name, dots, lvl) }
    end

    local power = pTable.powers[lvl]
    local nextSt = copyState(state)
    local bCost = safeNonNegInt(power.cost and power.cost.blood, 0)
    local wCost = safeNonNegInt(power.cost and power.cost.willpower, 0)

    if bCost > 0 then
        local bRes = Blood.spend(nextSt, bCost, {
            forDisciplineOrHeal = true,
            bypassTurnLimit = isTrue(opts.bypassTurnLimit),
            storytellerOverride = override,
        })
        if not bRes.ok then
            return { ok = false, newState = copyState(state), rollSpec = nil, error = bRes.error }
        end
        nextSt = bRes.newState
    end

    if wCost > 0 then
        local wRes = spendWillpowerNormalized(nextSt, wCost, override)
        if not wRes.ok then
            return { ok = false, newState = copyState(state), rollSpec = nil, error = wRes.error }
        end
        nextSt = wRes.newState
    end

    return {
        ok = true,
        newState = nextSt,
        rollSpec = power.pool and {
            powerName = pTable.name .. " — " .. power.name,
            attr = power.pool.attr,
            hab = power.pool.hab,
            defaultDiff = power.defaultDiff or 6,
            diffHint = power.diffHint or "",
        } or nil,
        error = nil,
    }
end

function BMEngine.castRitual(state, ritualIdOrCustom, parentDiscDots, opts)
    opts = opts or {}
    local override = resolveOverride(state, opts)
    local rit = type(ritualIdOrCustom) == "table" and ritualIdOrCustom or BMCat.RITUALS[ritualIdOrCustom]
    if not rit then
        return { ok = false, newState = copyState(state), rollSpec = nil, error = "Ritual não encontrado no grimório." }
    end
    local reqLvl = math.max(1, safeNonNegInt(rit.level, 1))
    local haveDots = safeNonNegInt(parentDiscDots, 0)
    if haveDots < reqLvl and not override then
        return {
            ok = false,
            newState = copyState(state),
            rollSpec = nil,
            error = string.format("Conhecimento insuficiente na disciplina para conjurar '%s' (requer nível %d, possui %d).", rit.name or "Ritual", reqLvl, haveDots),
        }
    end

    local nextSt = copyState(state)
    local bCost = safeNonNegInt(rit.cost and rit.cost.blood, 0)
    local wCost = safeNonNegInt(rit.cost and rit.cost.willpower, 0)

    if bCost > 0 then
        local bRes = Blood.spend(nextSt, bCost, {
            forDisciplineOrHeal = true,
            bypassTurnLimit = true,
            storytellerOverride = override,
        })
        if not bRes.ok then
            return { ok = false, newState = copyState(state), rollSpec = nil, error = bRes.error }
        end
        nextSt = bRes.newState
    end

    if wCost > 0 then
        local wRes = spendWillpowerNormalized(nextSt, wCost, override)
        if not wRes.ok then
            return { ok = false, newState = copyState(state), rollSpec = nil, error = wRes.error }
        end
        nextSt = wRes.newState
    end

    local fallbackDiff = math.min(9, 3 + reqLvl)
    local diff = safeNonNegInt(rit.defaultDiff, fallbackDiff)
    if diff <= 0 then diff = fallbackDiff end

    return {
        ok = true,
        newState = nextSt,
        rollSpec = {
            powerName = "Ritual: " .. (rit.name or "Customizado"),
            attr = "attr_inteligencia",
            hab = "hab_ocultismo",
            defaultDiff = diff,
            diffHint = rit.summary or "",
        },
        error = nil,
    }
end

function BMEngine.hasBloodMagicAccess(clanId, disciplinesList, ritualsBgDots)
    if clanId == "tremere" or clanId == "giovanni" then
        return true
    end
    if safeNonNegInt(ritualsBgDots, 0) >= 1 then
        return true
    end
    for _, d in ipairs(disciplinesList or {}) do
        if type(d) == "table"
            and (d.disc_id == "thaumaturgy" or d.disc_id == "necromancy")
            and (safeNonNegInt(d.nivel, 0) >= 1 or d.selected == true or d.selected == "true")
        then
            return true
        end
    end
    return false
end

return BMEngine
