local Clans = require("Data.clans")
local Catalog = require("Data.disciplines_catalog")
local Blood = require("Core.generation_blood")
local WM = require("Core.willpower_morality")

local Engine = {}

local function safeNum(val, default)
    local n = tonumber(val)
    if n == nil or n ~= n or n == math.huge or n == -math.huge then return default end
    return n
end

local function copyState(s)
    local o = {}
    for k, v in pairs(s or {}) do o[k] = v end
    local buffs = {}
    for k, v in pairs((s and s.activeBuffs) or {}) do buffs[k] = v end
    o.activeBuffs = buffs
    return o
end

local function resolvePower(discEntry, power)
    if type(power) == "table" then
        return power
    end
    if type(power) == "string" and discEntry and discEntry.disc_id then
        local cat = Catalog.DISCIPLINES[discEntry.disc_id]
        if cat then
            for _, pw in ipairs(cat.powers) do
                if pw.id == power then
                    return pw
                end
            end
        end
    end
    return nil
end

function Engine.classifyCostCategory(clanId, discId, hasAdditionalDiscMerit)
    if clanId == "caitiff" then
        return "caitiff"
    end
    if hasAdditionalDiscMerit then
        return "cla"
    end
    local clan = Clans.CLANS[clanId or "brujah"]
    if clan then
        for _, cid in ipairs(clan.disciplines) do
            if cid == discId then
                return "cla"
            end
        end
    end
    return "fora_cla"
end

function Engine.getUnlockedPowers(discId, dots, customPowers)
    local lvl = math.max(0, math.floor(safeNum(dots, 0)))
    local indexed = {}
    local seq = 0

    local cat = Catalog.DISCIPLINES[discId]
    if cat then
        for _, pw in ipairs(cat.powers) do
            if pw.level <= lvl then
                seq = seq + 1
                table.insert(indexed, { pw = pw, lvl = pw.level, seq = seq })
            end
        end
    end

    for _, cp in ipairs(customPowers or {}) do
        if type(cp) == "table" then
            local cpLvl = math.max(1, math.floor(safeNum(cp.level, 1)))
            if cpLvl <= lvl then
                seq = seq + 1
                table.insert(indexed, { pw = cp, lvl = cpLvl, seq = seq })
            end
        end
    end

    table.sort(indexed, function(a, b)
        if a.lvl ~= b.lvl then
            return a.lvl < b.lvl
        end
        return a.seq < b.seq
    end)

    local out = {}
    for i, item in ipairs(indexed) do
        out[i] = item.pw
    end
    return out
end

function Engine.activatePotenceAuto(state, opts)
    opts = opts or {}
    if state and state.activePotenceAuto == true and not opts.storytellerOverride then
        return {
            ok = false,
            newState = copyState(state),
            error = "Potência automática já está ativa neste turno.",
        }
    end

    local bRes = Blood.spend(copyState(state), 1, {
        forDisciplineOrHeal = true,
        bypassTurnLimit = (opts.bypassTurnLimit == true),
        storytellerOverride = opts.storytellerOverride,
    })
    if not bRes.ok then
        return { ok = false, newState = copyState(state), error = bRes.error }
    end

    local nextSt = copyState(bRes.newState)
    nextSt.activePotenceAuto = true
    return { ok = true, newState = nextSt, error = nil }
end

function Engine.activateCelerityActions(state, pointsToActivate, opts)
    opts = opts or {}
    local pts = math.max(1, math.floor(safeNum(pointsToActivate, 1)))
    local curActions = math.max(0, math.floor(safeNum(state and state.activeCelerityActions, 0)))
    local maxDots = opts.maxDots or (state and state.celerityDots)
    if maxDots ~= nil and not opts.storytellerOverride then
        local cap = math.max(0, math.floor(safeNum(maxDots, 0)))
        if (curActions + pts) > cap then
            return {
                ok = false,
                newState = copyState(state),
                error = "Ações extras excedem o nível de Rapidez.",
            }
        end
    end

    local bRes = Blood.spend(copyState(state), pts, {
        forDisciplineOrHeal = true,
        bypassTurnLimit = true,
        storytellerOverride = opts.storytellerOverride,
    })
    if not bRes.ok then
        return { ok = false, newState = copyState(state), error = bRes.error }
    end

    local nextSt = copyState(bRes.newState)
    nextSt.activeCelerityActions = curActions + pts
    return { ok = true, newState = nextSt, error = nil }
end

function Engine.activatePower(state, discEntry, power, opts)
    opts = opts or {}
    local resolved = resolvePower(discEntry, power)
    if type(resolved) ~= "table" then
        return {
            ok = false,
            newState = copyState(state),
            rollSpec = nil,
            buffToggled = nil,
            error = "Poder de Disciplina inválido.",
        }
    end

    local dots = math.floor(safeNum(discEntry and discEntry.nivel, 0))
    local reqLevel = math.max(1, math.floor(safeNum(resolved.level, 1)))
    if dots < reqLevel and not opts.storytellerOverride then
        return {
            ok = false,
            newState = copyState(state),
            rollSpec = nil,
            buffToggled = nil,
            error = "Nível insuficiente na Disciplina para este poder.",
        }
    end

    local discId = discEntry and discEntry.disc_id

    -- Potência ativa no turno: 1 ponto de Sangue converte dados em sucessos automáticos (ou desliga sem custo)
    if discId == "potence" and not opts.passiveOnly then
        local nextSt = copyState(state)
        if nextSt.activePotenceAuto == true and not opts.recast then
            nextSt.activePotenceAuto = false
            return {
                ok = true,
                newState = nextSt,
                rollSpec = nil,
                buffToggled = { id = "potence_auto", active = false },
                error = nil,
            }
        end
        local potRes = Engine.activatePotenceAuto(state, opts)
        if not potRes.ok then
            return {
                ok = false,
                newState = copyState(state),
                rollSpec = nil,
                buffToggled = nil,
                error = potRes.error,
            }
        end
        return {
            ok = true,
            newState = potRes.newState,
            rollSpec = nil,
            buffToggled = { id = "potence_auto", active = true },
            error = nil,
        }
    end

    -- Rapidez via activatePower: +1 ação extra por ativação até o limite de pontos da Disciplina
    if discId == "celerity" then
        local celRes = Engine.activateCelerityActions(state, 1, {
            maxDots = dots,
            storytellerOverride = opts.storytellerOverride,
        })
        if not celRes.ok then
            return {
                ok = false,
                newState = copyState(state),
                rollSpec = nil,
                buffToggled = nil,
                error = celRes.error,
            }
        end
        return {
            ok = true,
            newState = celRes.newState,
            rollSpec = nil,
            buffToggled = nil,
            error = nil,
        }
    end

    local nextSt = copyState(state)
    local isDeactivating = (resolved.toggleBuff ~= nil)
        and (nextSt.activeBuffs[resolved.toggleBuff.id] ~= nil)
        and (not opts.recast)

    if not isDeactivating then
        local bCost = math.max(0, math.floor(safeNum(resolved.cost and resolved.cost.blood, 0)))
        local wCost = math.max(0, math.floor(safeNum(resolved.cost and resolved.cost.willpower, 0)))

        if bCost > 0 then
            local bypass = (discEntry and discEntry.disc_id == "celerity") or (opts.bypassTurnLimit == true)
            local bRes = Blood.spend(nextSt, bCost, {
                forDisciplineOrHeal = true,
                bypassTurnLimit = bypass,
                storytellerOverride = opts.storytellerOverride,
            })
            if not bRes.ok then
                return { ok = false, newState = copyState(state), rollSpec = nil, buffToggled = nil, error = bRes.error }
            end
            nextSt = copyState(bRes.newState)
        end

        if wCost > 0 then
            local wRes = WM.spendWillpower(nextSt, wCost, { storytellerOverride = opts.storytellerOverride })
            if not wRes.ok then
                return { ok = false, newState = copyState(state), rollSpec = nil, buffToggled = nil, error = wRes.error }
            end
            nextSt = copyState(wRes.newState)
        end
    end

    local buffToggled = nil
    if resolved.toggleBuff then
        local bid = resolved.toggleBuff.id
        if nextSt.activeBuffs[bid] and not opts.recast then
            nextSt.activeBuffs[bid] = nil
            buffToggled = { id = bid, active = false }
        else
            nextSt.activeBuffs[bid] = resolved.toggleBuff
            buffToggled = { id = bid, active = true }
        end
    end

    local rollSpec = nil
    if resolved.pool and not isDeactivating then
        rollSpec = {
            powerName = resolved.name,
            attr = resolved.pool.attr,
            hab = resolved.pool.hab,
            defaultDiff = resolved.defaultDiff or 6,
            diffHint = resolved.diffHint or "",
        }
    end

    return {
        ok = true,
        newState = nextSt,
        rollSpec = rollSpec,
        buffToggled = buffToggled,
        error = nil,
    }
end

function Engine.computeCombatModifiers(state, disciplinesList)
    state = state or {}
    local out = {
        passivePotenceDice = 0,
        activePotenceAuto = 0,
        passiveCelerityDice = 0,
        activeCelerityActions = math.max(0, math.floor(safeNum(state.activeCelerityActions, 0))),
        fortitudeSoak = 0,
        sceneAttrMods = { forca = 0, destreza = 0, vigor = 0 },
        perceptionDiffMod = 0,
        soakDiffOverride = nil,
    }

    local potenceDots = 0
    local potenceEntryAuto = false
    local celerityDots = 0
    local fortitudeDots = 0
    local auspexDots = 0

    for _, d in ipairs(disciplinesList or {}) do
        if type(d) == "table" then
            local n = math.max(0, math.floor(safeNum(d.nivel, 0)))
            if d.disc_id == "potence" and n > 0 then
                if n > potenceDots then potenceDots = n end
                if d.activeAuto then potenceEntryAuto = true end
            elseif d.disc_id == "celerity" and n > 0 then
                if n > celerityDots then celerityDots = n end
            elseif d.disc_id == "fortitude" and n > 0 then
                if n > fortitudeDots then fortitudeDots = n end
            elseif d.disc_id == "auspex" and n > 0 then
                if n > auspexDots then auspexDots = n end
            end
        end
    end

    if potenceDots == 0 then
        potenceDots = math.max(0, math.floor(safeNum(state.ghoulPotence, 0)))
    end

    if potenceDots > 0 then
        if potenceEntryAuto or state.activePotenceAuto then
            out.activePotenceAuto = potenceDots
        else
            out.passivePotenceDice = potenceDots
        end
    end

    if celerityDots > 0 then
        if out.activeCelerityActions > 0 then
            out.passiveCelerityDice = math.max(0, celerityDots - out.activeCelerityActions)
        else
            out.passiveCelerityDice = celerityDots
        end
    end

    out.fortitudeSoak = fortitudeDots

    local buffs = state.activeBuffs or {}
    if buffs.vici_zulo then
        out.sceneAttrMods.forca = out.sceneAttrMods.forca + 3
        out.sceneAttrMods.destreza = out.sceneAttrMods.destreza + 3
        out.sceneAttrMods.vigor = out.sceneAttrMods.vigor + 3
    end
    if buffs.auspex_senses and auspexDots > 0 then
        out.perceptionDiffMod = out.perceptionDiffMod - auspexDots
    end
    if buffs.prot_beast then
        out.perceptionDiffMod = out.perceptionDiffMod - 2
    end
    if buffs.serp_skin then
        out.soakDiffOverride = 5
    end

    return out
end

function Engine.clearTurnEffects(state)
    local nextSt = copyState(state)
    nextSt.activeCelerityActions = 0
    nextSt.activePotenceAuto = false
    nextSt.spentThisTurn = 0
    return nextSt
end

function Engine.clearSceneBuffs(state)
    local nextSt = copyState(state)
    nextSt.activeBuffs = {}
    nextSt.activeCelerityActions = 0
    nextSt.activePotenceAuto = false
    return nextSt
end

return Engine
