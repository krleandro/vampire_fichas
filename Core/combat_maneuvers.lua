local Catalog = require("Data.combat_maneuvers_catalog")

local CombatManeuvers = {}

local function isTrue(v)
    return v == true or v == "true" or v == 1 or v == "1"
end

local function nonEmpty(s)
    return type(s) == "string" and s:match("%S") ~= nil
end

local function safeInt(v, default)
    local n = tonumber(v)
    if n == nil or n ~= n or n == math.huge or n == -math.huge then
        return default or 0
    end
    return math.floor(n)
end

local function safeNonNegInt(v, default)
    local n = safeInt(v, default)
    return n < 0 and 0 or n
end

local function clamp(val, minV, maxV)
    if val < minV then return minV end
    if val > maxV then return maxV end
    return val
end

local function normalizeDamageType(raw, fallback)
    if raw == "bashing" or raw == "lethal" or raw == "aggravated" or raw == "none" then
        return raw
    end
    if raw == "contundente" then return "bashing" end
    if raw == "letal" then return "lethal" end
    if raw == "agravado" then return "aggravated" end
    return fallback or "bashing"
end

local DAMAGE_TYPE_LABEL = {
    bashing    = "Contundente",
    lethal     = "Letal",
    aggravated = "Agravado",
    none       = "Sem Dano",
}

function CombatManeuvers.computeSplitPool(ownPool, totalNormalActions, actionNumber, lowestBasePool, isCelerityAction)
    local own = safeInt(ownPool, 0)
    if isTrue(isCelerityAction) then
        return {
            poolAfterSplit = own,
            splitPenalty = 0,
            usedBase = own,
            bypassedByCelerity = true,
        }
    end

    local total = math.max(1, safeInt(totalNormalActions, 1))
    if total <= 1 then
        return {
            poolAfterSplit = own,
            splitPenalty = 0,
            usedBase = own,
            bypassedByCelerity = false,
        }
    end

    local low = safeInt(lowestBasePool, 0)
    local base = (low > 0) and math.min(own, low) or own
    local idx = clamp(safeInt(actionNumber, 1), 1, total)
    local splitPenalty = total + (idx - 1)
    return {
        poolAfterSplit = base - splitPenalty,
        splitPenalty = splitPenalty,
        usedBase = base,
        bypassedByCelerity = false,
    }
end

function CombatManeuvers.prepareManeuverRoll(ctx)
    if type(ctx) ~= "table" then
        return {
            canRoll = false,
            reason = "Contexto de manobra inválido.",
            maneuverId = "",
            maneuverName = "Manobra Inválida",
            category = "brawl",
            attrUsed = "attr_destreza",
            habUsed = "hab_briga",
            isDefense = false,
            noDamage = true,
            isFirearm = false,
            poolBeforeClanDivisor = 0,
            difficulty = 6,
            splitPenalty = 0,
            consumeCelerityAction = false,
            setsGrappleOnHit = false,
            isDisarm = false,
            isStaking = false,
            isHeadshot = false,
            baseDamage = 0,
            extraTargetedDice = 0,
            damageType = "none",
            notes = {},
        }
    end

    local maneuverId = nonEmpty(ctx.maneuverId) and ctx.maneuverId or "strike"
    local m = Catalog.MANEUVERS[maneuverId]
    if not m then
        return {
            canRoll = false,
            reason = "Manobra de combate desconhecida: " .. tostring(maneuverId),
            maneuverId = tostring(maneuverId),
            maneuverName = tostring(maneuverId),
            category = "brawl",
            attrUsed = "attr_destreza",
            habUsed = "hab_briga",
            isDefense = false,
            noDamage = true,
            isFirearm = false,
            poolBeforeClanDivisor = 0,
            difficulty = 6,
            splitPenalty = 0,
            consumeCelerityAction = false,
            setsGrappleOnHit = false,
            isDisarm = false,
            isStaking = false,
            isHeadshot = false,
            baseDamage = 0,
            extraTargetedDice = 0,
            damageType = "none",
            notes = {},
        }
    end

    local isVampire           = isTrue(ctx.isVampire)
    local inGrapple           = isTrue(ctx.inGrapple)
    local isCelerityAction    = isTrue(ctx.isCelerityAction)
    local hasScope            = isTrue(ctx.hasScope)
    local naturalAggravated   = isTrue(ctx.naturalAggravated)
    local weaponAggravated    = isTrue(ctx.weaponAggravated)
    local storytellerOverride = isTrue(ctx.storytellerOverride)
    local emFrenesi           = isTrue(ctx.emFrenesi) or isTrue(ctx.em_frenesi)
    local ignoreWoundPenalty  = isTrue(ctx.ignoreWoundPenalty) or isTrue(ctx.roll_ignorar_ferimento)

    local attrs  = type(ctx.attrs) == "table" and ctx.attrs or {}
    local habs   = type(ctx.habs) == "table" and ctx.habs or {}
    local weapon = type(ctx.weapon) == "table" and ctx.weapon or nil
    local notes  = {}

    local attrId = m.defaultAttr
    local habId  = m.defaultHab
    if m.usesSlotTraits and weapon then
        if nonEmpty(weapon.attr) then attrId = weapon.attr end
        if nonEmpty(weapon.hab) then habId = weapon.hab end
    end
    if nonEmpty(ctx.attrId) then attrId = ctx.attrId end
    if nonEmpty(ctx.habId) then habId = ctx.habId end

    local locEntry   = (not m.isDefense) and Catalog.TARGET_LOCATIONS[ctx.targetLocation or "nenhum"] or Catalog.TARGET_LOCATIONS.nenhum
    locEntry         = locEntry or Catalog.TARGET_LOCATIONS.nenhum
    local coverEntry = (not m.isDefense) and Catalog.COVER_LEVELS[ctx.coverLevel or "nenhuma"] or Catalog.COVER_LEVELS.nenhuma
    coverEntry       = coverEntry or Catalog.COVER_LEVELS.nenhuma
    local flankEntry = (not m.isDefense) and Catalog.FLANK_MODES[ctx.flankMode or "frontal"] or Catalog.FLANK_MODES.frontal
    flankEntry       = flankEntry or Catalog.FLANK_MODES.frontal

    local isHeadshot        = (not m.noDamage) and isTrue(locEntry.isHeadshot)
    local extraTargetedDice = (not m.noDamage) and safeNonNegInt(locEntry.extraDamageDice, 0) or 0

    local baseDiff = 6
    if m.fixedDiff ~= nil then
        baseDiff = m.fixedDiff
    elseif m.usesWeaponSlot and weapon and tonumber(weapon.dif) and tonumber(weapon.dif) > 0 then
        baseDiff = safeInt(weapon.dif, 6)
    end

    local rawDiff = baseDiff
        + safeInt(m.diffMod, 0)
        + safeInt(locEntry.diffMod, 0)
        + safeInt(coverEntry.diffMod, 0)
        + safeInt(flankEntry.diffMod, 0)
        + safeInt(ctx.extraDiffMod, 0)

    local difficulty = clamp(rawDiff, 3, 10)
    if m.isStaking then
        difficulty = math.max(9, math.min(10, rawDiff))
    end

    local forca      = safeNonNegInt(attrs.attr_forca, 0)
    local weaponDmg  = weapon and safeNonNegInt(weapon.dano, 0) or 0
    local weaponHab  = (weapon and nonEmpty(weapon.hab)) and weapon.hab or m.defaultHab
    local isFirearm  = (m.category == "ranged") or (m.id == "weapon_strike" and weaponHab == "hab_armas_fogo")
    local baseDamage = 0
    local damageType = "none"

    if not m.noDamage then
        if m.id == "bite" then
            baseDamage = forca + 1
            damageType = isVampire and "aggravated" or "lethal"
        elseif m.id == "claw" then
            baseDamage = forca + 1
            damageType = naturalAggravated and "aggravated" or "lethal"
        elseif m.id == "stake_heart" then
            baseDamage = forca + math.max(1, weaponDmg)
            damageType = "lethal"
        elseif m.id == "weapon_strike" then
            if isFirearm then
                baseDamage = weaponDmg
                damageType = normalizeDamageType(weapon and weapon.tipo, "lethal")
                if isHeadshot and damageType == "bashing" then
                    damageType = "lethal"
                end
            else
                baseDamage = forca + weaponDmg
                damageType = normalizeDamageType(weapon and weapon.tipo, "lethal")
                if weaponAggravated then
                    damageType = "aggravated"
                    table.insert(notes, "Carícia de Baal ativa: arma branca causa dano Agravado (V20, p. 204).")
                end
            end
        elseif m.category == "ranged" then
            baseDamage = weaponDmg
            damageType = normalizeDamageType(weapon and weapon.tipo, "lethal")
            if isHeadshot and damageType == "bashing" then
                damageType = "lethal"
            end
        else
            baseDamage = forca + safeInt(m.strDamageBonus, 0)
            damageType = normalizeDamageType(m.damageType, "bashing")
        end
    end

    local function buildResult(canRoll, reason, poolBeforeClanDivisor, splitPenalty, consumeCelerity)
        return {
            canRoll               = canRoll,
            reason                = reason,
            maneuverId            = m.id,
            maneuverName          = m.name,
            category              = m.category,
            attrUsed              = attrId,
            habUsed               = habId,
            isDefense             = m.isDefense,
            noDamage              = m.noDamage,
            isFirearm             = isFirearm,
            poolBeforeClanDivisor = poolBeforeClanDivisor,
            difficulty            = difficulty,
            splitPenalty          = splitPenalty,
            consumeCelerityAction = consumeCelerity,
            setsGrappleOnHit      = m.setsGrapple,
            isDisarm              = m.isDisarm,
            isStaking             = m.isStaking,
            isHeadshot            = isHeadshot,
            baseDamage            = baseDamage,
            extraTargetedDice     = extraTargetedDice,
            damageType            = damageType,
            notes                 = notes,
        }
    end

    if m.requiresGrapple and not inGrapple and not storytellerOverride then
        return buildResult(
            false,
            "Mordida Vampírica exige estar em Agarrão ativo (Clinch ou Segurar) antes de morder (V20, p. 276).",
            0, 0, false
        )
    end

    if isCelerityAction and ctx.celerityActionsLeft ~= nil and safeInt(ctx.celerityActionsLeft, 0) < 1 and not storytellerOverride then
        return buildResult(
            false,
            "Sem ações extras de Rapidez disponíveis neste turno (ative Rapidez antes de rolar; V20, p. 142).",
            0, 0, false
        )
    end

    local attrVal   = safeNonNegInt(attrs[attrId], 0)
    local habVal    = safeNonNegInt(habs[habId], 0)
    local percepcao = safeNonNegInt(attrs.attr_percepcao, 0)

    local accBonus = safeInt(m.accBonus, 0)
    if m.id == "bite" then
        accBonus = isVampire and safeInt(m.vampireAccBonus, 1) or 0
    end

    local aimTurns = safeNonNegInt(ctx.aimTurns, 0)
    local aimBonus = 0
    if m.allowAim and aimTurns > 0 then
        local aimCap = percepcao + (hasScope and 1 or 0)
        aimBonus = math.max(0, math.min(aimTurns, aimCap))
        if aimBonus > 0 then
            table.insert(notes, string.format("Mira (%d turno(s)%s): +%d dado(s) (V20, p. 274).", aimTurns, hasScope and " c/ luneta" or "", aimBonus))
        end
    end

    local bonusDice = safeInt(ctx.bonusDice, 0)
    local defenseExtraPenalty = m.isDefense and math.max(0, safeInt(ctx.priorDefensesThisTurn, 0)) or 0
    if defenseExtraPenalty > 0 then
        table.insert(notes, string.format("Defesa ativa cumulativa: -%d dado(s) (V20, p. 274).", defenseExtraPenalty))
    end

    local ownPool = attrVal + habVal + accBonus + aimBonus + bonusDice - defenseExtraPenalty
    local split = CombatManeuvers.computeSplitPool(
        ownPool,
        ctx.totalNormalActions,
        ctx.actionNumber,
        ctx.lowestBasePool,
        isCelerityAction
    )

    if split.bypassedByCelerity then
        table.insert(notes, "Ação Extra de Rapidez: sem penalidade de divisão de paradas (V20, p. 142).")
    elseif split.splitPenalty > 0 then
        table.insert(notes, string.format("Divisão de parada (base %d): -%d dados (V20, p. 248).", split.usedBase, split.splitPenalty))
    end

    local woundPen = (ignoreWoundPenalty or emFrenesi) and 0 or math.abs(safeInt(ctx.woundPenalty, 0))
    local armorPen = (attrId == "attr_destreza") and math.abs(safeInt(ctx.armorDexPenalty, 0)) or 0
    local clanDiceMod = safeInt(ctx.clanDiceMod, 0)

    if locEntry.id ~= "nenhum" then
        table.insert(notes, string.format("Alvo localizado (%s): +%d dif%s.", locEntry.name, locEntry.diffMod, extraTargetedDice > 0 and (", +" .. extraTargetedDice .. "d dano") or ""))
    end
    if coverEntry.id ~= "nenhuma" then
        table.insert(notes, string.format("%s: +%d dif.", coverEntry.name, coverEntry.diffMod))
    end
    if flankEntry.id ~= "frontal" then
        table.insert(notes, string.format("Posição (%s): %d dif.", flankEntry.name, flankEntry.diffMod))
    end

    local poolBeforeClanDivisor = split.poolAfterSplit - woundPen - armorPen + clanDiceMod
    if poolBeforeClanDivisor <= 0 then
        return buildResult(
            false,
            "Parada de dados reduzida a zero ou menos pelas penalidades/divisão de ações — ação impossível (V20, p. 248).",
            poolBeforeClanDivisor,
            split.splitPenalty,
            false
        )
    end

    return buildResult(
        true,
        nil,
        poolBeforeClanDivisor,
        split.splitPenalty,
        isCelerityAction
    )
end

function CombatManeuvers.computePostAttackDamage(params)
    if type(params) ~= "table" then
        return {
            hit              = false,
            netHits          = 0,
            carryOverDice    = 0,
            noDamage         = true,
            damageDicePool   = 0,
            autoSuccesses    = 0,
            damageDifficulty = 6,
            damageType       = "none",
            isHeadshot       = false,
            isStaking        = false,
            setsGrapple      = false,
            disarm           = nil,
            summary          = "Ataque inválido.",
        }
    end

    local m                 = type(params.maneuver) == "table" and params.maneuver or {}
    local mName             = m.maneuverName or m.name or "Manobra"
    local category          = m.category or "brawl"
    local noDamage          = isTrue(m.noDamage) or isTrue(m.isDefense)
    local isHeadshot        = isTrue(m.isHeadshot)
    local isStaking         = isTrue(m.isStaking)
    local setsGrappleFlag   = isTrue(m.setsGrappleOnHit) or isTrue(m.setsGrapple)
    local isDisarm          = isTrue(m.isDisarm)
    local isFirearm         = isTrue(m.isFirearm) or (category == "ranged")
    local baseDamage        = safeNonNegInt(m.baseDamage, 0)
    local extraTargetedDice = safeNonNegInt(m.extraTargetedDice, 0)
    local damageType        = normalizeDamageType(m.damageType, noDamage and "none" or "bashing")

    local rawAtkSucc = params.attackSuccesses ~= nil and params.attackSuccesses or params.totalSuccesses
    local atkSucc    = safeNonNegInt(rawAtkSucc, 0)
    local defSucc    = safeNonNegInt(params.defenseSuccesses, 0)
    local outcome    = tostring(params.attackOutcome or params.outcome or "")
    local isBotch    = (outcome == "botch")
    if isBotch then
        atkSucc = 0
    end

    local rawNet        = atkSucc - defSucc
    local hit           = (not isBotch) and (rawNet >= 1)
    local netHits       = hit and rawNet or 0
    local carryOverDice = hit and (netHits - 1) or 0
    local setsGrapple   = hit and setsGrappleFlag

    local disarm = nil
    local targetStrength = safeNonNegInt(params.targetStrength, 0)
    if isDisarm then
        disarm = {
            attempted   = true,
            disarmed    = hit and (netHits > targetStrength),
            botchedSelf = isBotch,
        }
    end

    local damageDicePool = 0
    local autoSuccesses  = 0

    if hit and not noDamage then
        local appliesPotence = (category == "brawl" or category == "melee") and not isFirearm
        local passivePot     = safeNonNegInt(params.passivePotenceDice, 0)
        local autoPot        = safeNonNegInt(params.autoPotenceSuccesses, 0)
        local meleePotDice   = 0

        if appliesPotence then
            if autoPot > 0 then
                autoSuccesses = autoPot
                meleePotDice  = 0
            else
                meleePotDice  = passivePot
                autoSuccesses = 0
            end
        end

        damageDicePool = math.max(0, baseDamage + extraTargetedDice + carryOverDice + meleePotDice)
        if damageDicePool == 0 and autoSuccesses == 0 then
            damageDicePool = 1
        end
    end

    local summary
    if isBotch then
        if isDisarm then
            summary = string.format("Falha Crítica em %s: atacante perde a própria arma / sofre o revés (V20, p. 276)!", mName)
        else
            summary = string.format("Falha Crítica em %s: o ataque falhou catastroficamente!", mName)
        end
    elseif not hit then
        summary = string.format("%s sem acerto líquido (%d sucesso(s) de ataque vs %d de defesa).", mName, atkSucc, defSucc)
    elseif isDisarm and disarm then
        if disarm.disarmed then
            summary = string.format("Desarme bem-sucedido em %s (%d sucessos líquidos > Força %d do alvo; V20, p. 276)!", mName, netHits, targetStrength)
        else
            summary = string.format("Ataque atingiu, mas não desarmou (%d sucesso(s) líquido(s) <= Força %d do alvo; V20, p. 276).", netHits, targetStrength)
        end
    elseif noDamage then
        if setsGrapple then
            summary = string.format("%s bem-sucedido (%d sucesso(s) líquido(s)): Agarrão/Imobilização ativo (V20, p. 276)!", mName, netHits)
        else
            summary = string.format("%s bem-sucedido (%d sucesso(s) líquido(s)).", mName, netHits)
        end
    else
        local dtypeLabel = DAMAGE_TYPE_LABEL[damageType] or damageType
        local autoPart = (autoSuccesses > 0) and string.format(" + %d auto (Potência)", autoSuccesses) or ""
        local flags = {}
        if setsGrapple then table.insert(flags, "[Agarrão Ativo]") end
        if isHeadshot then table.insert(flags, "[Cabeça/Vital]") end
        if isStaking then table.insert(flags, "[Estaca: >=3 pós-absorção paralisa vampiro]") end
        local flagSuffix = (#flags > 0) and (" " .. table.concat(flags, " ")) or ""
        summary = string.format(
            "Acerto em %s (%d sucesso(s) líquido(s)) → Parada de Dano: %dd10%s %s (dif 6)%s",
            mName, netHits, damageDicePool, autoPart, dtypeLabel, flagSuffix
        )
    end

    return {
        hit              = hit,
        netHits          = netHits,
        carryOverDice    = carryOverDice,
        noDamage         = noDamage,
        damageDicePool   = damageDicePool,
        autoSuccesses    = autoSuccesses,
        damageDifficulty = 6,
        damageType       = (hit and not noDamage) and damageType or (noDamage and "none" or damageType),
        isHeadshot       = isHeadshot,
        isStaking        = isStaking,
        setsGrapple      = setsGrapple,
        disarm           = disarm,
        summary          = summary,
    }
end

function CombatManeuvers.checkStakingParalyze(finalDamageLevels, isVampireTarget)
    local dmg = safeNonNegInt(finalDamageLevels, 0)
    if isTrue(isVampireTarget) and dmg >= 3 then
        return {
            paralyzed = true,
            message = string.format(
                "Estaca atravessou o coração (%d níveis efetivos >= 3): vampiro paralisado em Torpor/Imobilização (V20, p. 279)!",
                dmg
            ),
        }
    end
    return {
        paralyzed = false,
        message = nil,
    }
end

return CombatManeuvers
