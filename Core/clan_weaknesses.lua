local WM = require("Core.willpower_morality")
local Health = require("Core.health")
local Blood = require("Core.generation_blood")

local CW = {}

local SOCIAL_ATTRS = { attr_carisma = true, attr_manipulacao = true, attr_aparencia = true }

local function copyState(s)
    local o = {}
    for k, v in pairs(s or {}) do o[k] = v end
    return o
end

local function isTrue(v)
    return v == true or v == "true" or v == 1 or v == "1"
end

local function nonEmpty(s)
    return type(s) == "string" and s:match("%S") ~= nil
end

local function safeNonNegInt(v, default)
    local n = tonumber(v)
    if n == nil or n ~= n or n == math.huge or n == -math.huge then return default or 0 end
    n = math.floor(n)
    return n < 0 and 0 or n
end

function CW.getSocialBaseFreeDots(clanId)
    return (clanId == "nosferatu") and 2 or 3
end

function CW.validateCreationRequirements(state)
    state = state or {}
    local errors = {}
    local cid = state.cla_id

    if cid == "nosferatu" and safeNonNegInt(state.attr_aparencia, 0) ~= 0 then
        table.insert(errors, "Nosferatu possui Aparência permanentemente igual a 0 (V20, p. 61).")
    elseif cid == "malkavian" and not nonEmpty(state.malkav_perturbacao) then
        table.insert(errors, "Malkaviano exige definir a Perturbação incurável inicial (V20, p. 59).")
    elseif cid == "ventrue" and not nonEmpty(state.ventrue_presa_restrita) then
        table.insert(errors, "Ventrue exige definir o tipo exclusivo de recipiente mortal da alimentação (V20, p. 71).")
    elseif cid == "ravnos" and not nonEmpty(state.ravnos_vicio_descricao) then
        table.insert(errors, "Ravnos exige definir o Vício específico da fraqueza de clã (V20, p. 63).")
    end

    return { valid = (#errors == 0), errors = errors }
end

function CW.computeRollModifiers(state)
    state = state or {}
    local cid = state.cla_id
    local attrId = state.attrId
    local habId = state.habId
    local buffs = state.activeBuffs or {}
    local warnings = {}
    local bonusDiceMod = 0
    local diffMod = 0
    local poolDivisor = 1

    if cid == "nosferatu" and attrId == "attr_aparencia" and not isTrue(state.storytellerOverride) then
        if not buffs.obf_mask then
            return {
                blocked = true,
                blockReason = "Maldição Nosferatu: Aparência 0 causa falha automática sem Máscara das Mil Faces (V20, p. 61).",
                bonusDiceMod = 0,
                diffMod = 0,
                poolDivisor = 1,
                warnings = warnings,
            }
        end
    end

    if cid == "setite" and isTrue(state.setita_luz_forte) then
        bonusDiceMod = bonusDiceMod - 1
        table.insert(warnings, "Fraqueza Setita: -1 dado sob luz forte.")
    end

    if cid == "lasombra" and isTrue(state.lasombra_vigiado_espelhos) then
        if SOCIAL_ATTRS[attrId or ""] or habId == "hab_furtividade" or habId == "hab_labia" then
            diffMod = diffMod + 1
            table.insert(warnings, "Fraqueza Lasombra: +1 dif perante espelhos/câmeras.")
        end
    end

    if cid == "caitiff" and isTrue(state.caitiff_estigma_ativo) and SOCIAL_ATTRS[attrId or ""] then
        diffMod = diffMod + 2
        table.insert(warnings, "Estigma Social Caitiff: +2 dif com Membros estabelecidos.")
    end

    if cid == "tzimisce" then
        local days = math.min(10, safeNonNegInt(state.tzimisce_dias_sem_terra, 0))
        if days > 0 then
            poolDivisor = math.floor(2 ^ days)
            table.insert(warnings, string.format("Fraqueza Tzimisce: %d dia(s) sem terra natal (parada / %d, mín. 1).", days, poolDivisor))
        end
    end

    return {
        blocked = false,
        blockReason = nil,
        bonusDiceMod = bonusDiceMod,
        diffMod = diffMod,
        poolDivisor = poolDivisor,
        warnings = warnings,
    }
end

function CW.computeSolarExtraDamage(clanId, amount, isSolar)
    local amt = safeNonNegInt(amount, 0)
    if not isTrue(isSolar) or amt <= 0 then return 0 end
    if clanId == "setite" then return 2 end
    if clanId == "lasombra" then return 1 end
    return 0
end

function CW.endBrujahFrenzyWithWP(state)
    state = state or {}
    if not isTrue(state.em_frenesi) then
        return { ok = false, newState = copyState(state), error = "O personagem não está em Frenesi ativo no momento." }
    end
    local wRes = WM.spendWillpower(state, 1, { storytellerOverride = state.storytellerOverride })
    if not wRes.ok then
        return { ok = false, newState = wRes.newState, error = wRes.error }
    end
    local nextSt = wRes.newState
    nextSt.em_frenesi = false
    return { ok = true, newState = nextSt, error = nil }
end

function CW.recordGangrelFrenzy(state)
    local nextSt = copyState(state)
    local count = safeNonNegInt(nextSt.gangrel_tracos_qtd, 0) + 1
    nextSt.gangrel_tracos_qtd = count
    local target = nextSt.gangrel_attr_penalizado
    if not SOCIAL_ATTRS[target or ""] then
        target = "attr_carisma"
    end
    if count > 0 and (count % 5 == 0) then
        local cur = safeNonNegInt(nextSt[target], 1)
        local nextVal = math.max(0, cur - 1)
        nextSt[target] = nextVal
        return { newState = nextSt, penalizedAttr = target, newAttrVal = nextVal }
    end
    return { newState = nextSt, penalizedAttr = nil, newAttrVal = nil }
end

function CW.suppressMalkavianDerangement(state)
    state = state or {}
    local wRes = WM.spendWillpower(state, 1, { storytellerOverride = state.storytellerOverride })
    if not wRes.ok then
        return { ok = false, newState = wRes.newState, error = wRes.error }
    end
    local nextSt = wRes.newState
    nextSt.malkav_suprimida_cena = true
    return { ok = true, newState = nextSt, error = nil }
end

function CW.recordTremereDrink(state)
    local nextSt = copyState(state)
    local cur = safeNonNegInt(nextSt.tremere_laco_goles, 0)
    local step = math.min(2, cur + 1)
    nextSt.tremere_laco_goles = step
    return { newState = nextSt, fullBond = (step >= 2), step = step }
end

function CW.checkVentrueFeeding(state)
    state = state or {}
    if state.cla_id == "ventrue" and state.ventrue_presa_compativel ~= nil and not isTrue(state.ventrue_presa_compativel) then
        return {
            allowed = false,
            reason = "Restrição Ventrue: sangue fora da preferência alimentar é vomitado imediatamente (0 vitae ganha; V20, p. 71).",
        }
    end
    return { allowed = true, reason = nil }
end

function CW.ingestAssamiteVitae(state, points)
    local pts = math.max(1, safeNonNegInt(points, 1))
    local damaged = Health.applyDamage(state, pts, "lethal", { isVampire = true, isFirearm = false, halveBashing = false })
    local mode = (state and state.assamita_maldicao_modo) or "ur_shulgi"
    if mode == "tremere_classica" then
        return { newState = damaged, lethalApplied = pts, addictionDiff = nil, bloodAdded = 0 }
    end
    local gained = Blood.gain(damaged, pts)
    local diff = math.min(10, 3 + pts)
    return { newState = gained.newState, lethalApplied = pts, addictionDiff = diff, bloodAdded = gained.added }
end

function CW.computeGiovanniKissDamage(bloodPoints)
    local pts = math.max(1, safeNonNegInt(bloodPoints, 1))
    local let = pts * 2
    return { lethalToVessel = let, fatalRisk = (let >= 7) }
end

function CW.resetTzimisceSoil(state)
    local nextSt = copyState(state)
    nextSt.tzimisce_dias_sem_terra = 0
    return nextSt
end

return CW
