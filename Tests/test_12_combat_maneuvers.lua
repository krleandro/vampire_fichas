local V20 = require("Core.v20_init")
local Cat = require("Data.combat_maneuvers_catalog")
local CM = require("Core.combat_maneuvers")

assert(V20.CombatManeuversCatalog == Cat)
assert(V20.CombatManeuvers == CM)

-- Registro idempotente em Core.v20_init mesmo com _G.V20 pré-existente
_G.V20 = { ExistingMarker = true }
package.loaded["Core.v20_init"] = nil
local V20Reloaded = require("Core.v20_init")
assert(V20Reloaded.ExistingMarker == true, "Core.v20_init deve preservar tabela V20 existente")
assert(V20Reloaded.CombatManeuversCatalog == Cat, "V20.CombatManeuversCatalog deve ser atribuído idempotentemente")
assert(V20Reloaded.CombatManeuvers == CM, "V20.CombatManeuvers deve ser atribuído idempotentemente")
_G.V20 = V20
package.loaded["Core.v20_init"] = V20

-- Catálogo completo das 20 manobras oficiais V20 e tabelas táticas
local expectedOrder = {
    "strike", "kick", "bite", "claw", "clinch", "hold", "tackle", "sweep_brawl", "disarm_brawl",
    "weapon_strike", "stake_heart", "disarm_melee", "sweep_melee",
    "single_shot", "double_tap", "three_round_burst", "full_auto",
    "dodge", "block", "parry",
}
assert(#Cat.MANEUVER_ORDER == 20, "Esperadas 20 manobras oficiais V20")
for idx, id in ipairs(Cat.MANEUVER_ORDER) do
    assert(id == expectedOrder[idx], "Ordem inesperada no índice " .. tostring(idx) .. ": " .. tostring(id))
    local m = Cat.MANEUVERS[id]
    assert(
        m ~= nil and m.id == id and type(m.name) == "string" and type(m.page) == "string" and type(m.summary) == "string",
        "Manobra inválida: " .. tostring(id)
    )
    assert(m.page:find("V20, p.") ~= nil, "Página V20 ausente na manobra: " .. tostring(id))
end
assert(Cat.TARGET_LOCATIONS.nenhum and Cat.TARGET_LOCATIONS.membro and Cat.TARGET_LOCATIONS.cabeca)
assert(Cat.COVER_LEVELS.nenhuma and Cat.COVER_LEVELS.leve and Cat.COVER_LEVELS.boa and Cat.COVER_LEVELS.superior)
assert(Cat.FLANK_MODES.frontal and Cat.FLANK_MODES.flanco and Cat.FLANK_MODES.retaguarda)

-- 1. Divisão de paradas pela menor parada (V20, p. 248) vs Ação de Rapidez (p. 142)
local sp1 = CM.computeSplitPool(7, 2, 1, 5, false)
assert(sp1.usedBase == 5 and sp1.splitPenalty == 2 and sp1.poolAfterSplit == 3 and sp1.bypassedByCelerity == false)
local sp2 = CM.computeSplitPool(7, 2, 2, 5, false)
assert(sp2.usedBase == 5 and sp2.splitPenalty == 3 and sp2.poolAfterSplit == 2)
local spSingle = CM.computeSplitPool(7, 1, 1, 4, false)
assert(spSingle.usedBase == 7 and spSingle.splitPenalty == 0 and spSingle.poolAfterSplit == 7 and spSingle.bypassedByCelerity == false)
local spOwnBase = CM.computeSplitPool(6, 3, 3, 0, false)
assert(spOwnBase.usedBase == 6 and spOwnBase.splitPenalty == 5 and spOwnBase.poolAfterSplit == 1)
local spCel = CM.computeSplitPool(7, 3, 2, 4, true)
assert(spCel.poolAfterSplit == 7 and spCel.splitPenalty == 0 and spCel.bypassedByCelerity == true)

-- Quando a divisão zera ou negativa a parada, V20 p. 248 bloqueia a ação
local zeroSplit = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Neófito Lento",
    isVampire = true,
    maneuverId = "strike",
    attrs = { attr_destreza = 2, attr_forca = 2, attr_percepcao = 2 },
    habs = { hab_briga = 1 },
    totalNormalActions = 3,
    actionNumber = 1,
    lowestBasePool = 3,
})
assert(zeroSplit.canRoll == false and type(zeroSplit.reason) == "string")

-- Rapidez exige rapidez_acoes_extras >= 1 (salvo storytellerOverride) e marca consumeCelerityAction
local celBlocked = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Toreador Sem Sangue",
    isVampire = true,
    maneuverId = "strike",
    isCelerityAction = true,
    celerityActionsLeft = 0,
    attrs = { attr_destreza = 4, attr_forca = 2 },
    habs = { hab_briga = 2 },
})
assert(celBlocked.canRoll == false and celBlocked.consumeCelerityAction == false)

local celAllowed = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Toreador Veloz",
    isVampire = true,
    maneuverId = "strike",
    isCelerityAction = true,
    celerityActionsLeft = 2,
    totalNormalActions = 3,
    actionNumber = 3,
    lowestBasePool = 3,
    attrs = { attr_destreza = 4, attr_forca = 2 },
    habs = { hab_briga = 2 },
})
assert(celAllowed.canRoll == true and celAllowed.poolBeforeClanDivisor == 6 and celAllowed.splitPenalty == 0 and celAllowed.consumeCelerityAction == true)

-- 2. Mordida vampírica exige Agarrão prévio (salvo storytellerOverride), +1 precisão e dano Força+1 Agravado
local biteBlocked = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Brujah",
    isVampire = true,
    maneuverId = "bite",
    inGrapple = false,
    attrs = { attr_destreza = 3, attr_forca = 3 },
    habs = { hab_briga = 3 },
})
assert(biteBlocked.canRoll == false)

local biteOverride = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Brujah Override",
    isVampire = true,
    maneuverId = "bite",
    inGrapple = false,
    storytellerOverride = true,
    attrs = { attr_destreza = 3, attr_forca = 3 },
    habs = { hab_briga = 3 },
})
assert(biteOverride.canRoll == true and biteOverride.poolBeforeClanDivisor == 7)

local biteOk = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Brujah",
    isVampire = true,
    maneuverId = "bite",
    inGrapple = true,
    attrs = { attr_destreza = 3, attr_forca = 3 },
    habs = { hab_briga = 3 },
})
assert(biteOk.canRoll == true and biteOk.poolBeforeClanDivisor == 7 and biteOk.difficulty == 6)
assert(biteOk.baseDamage == 4 and biteOk.damageType == "aggravated")

-- Mortal usando bite não ganha +1 dado vampírico nem dano agravado
local biteMortal = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Mortal",
    isVampire = false,
    maneuverId = "bite",
    inGrapple = true,
    attrs = { attr_destreza = 3, attr_forca = 2 },
    habs = { hab_briga = 2 },
})
assert(biteMortal.canRoll == true and biteMortal.poolBeforeClanDivisor == 5 and biteMortal.damageType == "lethal")

-- 3. Garras: Agravado com Metamorfose 2 (naturalAggravated), Letal caso contrário
local clawAgg = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Gangrel",
    isVampire = true,
    maneuverId = "claw",
    naturalAggravated = true,
    attrs = { attr_destreza = 4, attr_forca = 3 },
    habs = { hab_briga = 3 },
})
assert(clawAgg.canRoll == true and clawAgg.damageType == "aggravated" and clawAgg.baseDamage == 4)

local clawLethal = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Gangrel Sem Garras",
    isVampire = true,
    maneuverId = "claw",
    naturalAggravated = false,
    attrs = { attr_destreza = 4, attr_forca = 3 },
    habs = { hab_briga = 3 },
})
assert(clawLethal.canRoll == true and clawLethal.damageType == "lethal")

-- 3b. PF3-3: weaponAggravated (Quietus 4 Carícia de Baal / quie_baal) promove weapon_strike corpo a corpo a Agravado
local baalBlade = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Assamita Baal",
    isVampire = true,
    maneuverId = "weapon_strike",
    weaponAggravated = true,
    attrs = { attr_destreza = 4, attr_forca = 3 },
    habs = { hab_armas_brancas = 4 },
    weapon = { nome = "[TESTE_E2E] Cimitarra", attr = "attr_destreza", hab = "hab_armas_brancas", dif = 6, dano = 3, tipo = "lethal" },
})
assert(baalBlade.canRoll == true and baalBlade.baseDamage == 6 and baalBlade.damageType == "aggravated")

local normalBlade = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Assamita Sem Baal",
    isVampire = true,
    maneuverId = "weapon_strike",
    weaponAggravated = "false",
    attrs = { attr_destreza = 4, attr_forca = 3 },
    habs = { hab_armas_brancas = 4 },
    weapon = { nome = "[TESTE_E2E] Cimitarra", attr = "attr_destreza", hab = "hab_armas_brancas", dif = 6, dano = 3, tipo = "lethal" },
})
assert(normalBlade.canRoll == true and normalBlade.baseDamage == 6 and normalBlade.damageType == "lethal")

-- weapon_strike com arma de fogo não soma Força e não recebe weaponAggravated de lâmina
local gunInWeaponStrike = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Atirador Slot",
    isVampire = true,
    maneuverId = "weapon_strike",
    weaponAggravated = true,
    attrs = { attr_destreza = 3, attr_forca = 4 },
    habs = { hab_armas_fogo = 3 },
    weapon = { nome = "[TESTE_E2E] Pistola Pesada", attr = "attr_destreza", hab = "hab_armas_fogo", dif = 6, dano = 4, tipo = "bashing" },
})
assert(gunInWeaponStrike.canRoll == true and gunInWeaponStrike.baseDamage == 4 and gunInWeaponStrike.damageType == "bashing")

-- 4. Estaca no Coração: dificuldade mínima fixa 9 mesmo com flanco/retaguarda, e paralisia em >= 3 níveis
local stake = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Caçador",
    isVampire = true,
    maneuverId = "stake_heart",
    flankMode = "retaguarda",
    attrs = { attr_destreza = 4, attr_forca = 3 },
    habs = { hab_armas_brancas = 3 },
    weapon = { nome = "[TESTE_E2E] Estaca de Carvalho", dano = 1, dif = 6, tipo = "lethal", hab = "hab_armas_brancas" },
})
assert(stake.canRoll == true and stake.difficulty == 9 and stake.isStaking == true and stake.baseDamage == 4)
assert(CM.checkStakingParalyze(2, true).paralyzed == false)
assert(CM.checkStakingParalyze(3, true).paralyzed == true)
assert(CM.checkStakingParalyze(4, false).paralyzed == false)

-- 5. Armas de fogo: Rajada Curta (+2d, +1 dif), Rajada Completa (+10d, +2 dif), Mira limitada à Percepção (+1 luneta), Cabeça Letal
local burst = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Toreador Atirador",
    isVampire = true,
    maneuverId = "three_round_burst",
    coverLevel = "boa",
    attrs = { attr_destreza = 3, attr_forca = 4, attr_percepcao = 2 },
    habs = { hab_armas_fogo = 3 },
    weapon = { nome = "[TESTE_E2E] Submetralhadora", attr = "attr_destreza", hab = "hab_armas_fogo", dif = 6, dano = 4, tipo = "lethal" },
})
-- pool: 3 + 3 + 2 (rajada) = 8; dif: 6 + 1 (rajada) + 2 (cobertura boa) = 9; dano base arma de fogo NÃO soma Força (= 4)
assert(burst.canRoll == true and burst.poolBeforeClanDivisor == 8 and burst.difficulty == 9 and burst.baseDamage == 4)

local doubleTap = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Policial Tático",
    isVampire = false,
    maneuverId = "double_tap",
    attrs = { attr_destreza = 3, attr_forca = 2 },
    habs = { hab_armas_fogo = 3 },
    weapon = { nome = "[TESTE_E2E] Pistola 9mm", attr = "attr_destreza", hab = "hab_armas_fogo", dif = 6, dano = 4, tipo = "lethal" },
})
assert(doubleTap.canRoll == true and doubleTap.poolBeforeClanDivisor == 7 and doubleTap.difficulty == 7 and doubleTap.baseDamage == 4)

local aimedHead = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Sniper",
    isVampire = true,
    maneuverId = "single_shot",
    aimTurns = 5,
    hasScope = true,
    targetLocation = "cabeca",
    attrs = { attr_destreza = 3, attr_forca = 2, attr_percepcao = 3 },
    habs = { hab_armas_fogo = 2 },
    weapon = { nome = "[TESTE_E2E] Rifle", attr = "attr_destreza", hab = "hab_armas_fogo", dif = 6, dano = 8, tipo = "bashing" },
})
-- Mira limitada a Percepção (3) + 1 (luneta) = +4 dados -> 3 + 2 + 4 = 9; Cabeça: +2 dif (8), +1 dado dano extra, Letal
assert(aimedHead.poolBeforeClanDivisor == 9 and aimedHead.difficulty == 8 and aimedHead.isHeadshot == true)
assert(aimedHead.extraTargetedDice == 1 and aimedHead.damageType == "lethal")

local fullAuto = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Brujah Metralhadora",
    isVampire = true,
    maneuverId = "full_auto",
    attrs = { attr_destreza = 3, attr_forca = 3 },
    habs = { hab_armas_fogo = 2 },
    weapon = { nome = "[TESTE_E2E] Fuzil Automático", dif = 6, dano = 5, tipo = "bashing", hab = "hab_armas_fogo" },
})
assert(fullAuto.poolBeforeClanDivisor == 15 and fullAuto.difficulty == 8)

-- 6. Defesas ativas cumulativas (-1 dado por defesa prévia no turno)
local def2 = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Defensor",
    isVampire = true,
    maneuverId = "dodge",
    priorDefensesThisTurn = 2,
    attrs = { attr_destreza = 4 },
    habs = { hab_esportes = 3 },
})
assert(def2.canRoll == true and def2.isDefense == true and def2.poolBeforeClanDivisor == 5 and def2.noDamage == true)

local blockDef = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Pugilista",
    isVampire = false,
    maneuverId = "block",
    priorDefensesThisTurn = 1,
    attrs = { attr_destreza = 3 },
    habs = { hab_briga = 3 },
})
assert(blockDef.canRoll == true and blockDef.isDefense == true and blockDef.poolBeforeClanDivisor == 5)

local parryDef = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Duelista",
    isVampire = true,
    maneuverId = "parry",
    priorDefensesThisTurn = 0,
    attrs = { attr_destreza = 4 },
    habs = { hab_armas_brancas = 3 },
})
assert(parryDef.canRoll == true and parryDef.isDefense == true and parryDef.poolBeforeClanDivisor == 7)

-- 6b. Manobras de Agarrão (clinch/hold), Chute, Encontrão, Rasteiras, Ferimentos, Armadura e Frenesi
local clinchPrep = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Nosferatu Lutador",
    isVampire = true,
    maneuverId = "clinch",
    armorDexPenalty = 2, -- clinch usa Força, não sofre penalidade de Destreza da armadura!
    woundPenalty = -2,
    emFrenesi = true,    -- em Frenesi ignora penalidade de ferimento!
    attrs = { attr_forca = 4, attr_destreza = 2 },
    habs = { hab_briga = 3 },
})
assert(clinchPrep.canRoll == true and clinchPrep.attrUsed == "attr_forca" and clinchPrep.poolBeforeClanDivisor == 7)
assert(clinchPrep.setsGrappleOnHit == true and clinchPrep.baseDamage == 4 and clinchPrep.damageType == "bashing")
local clinchPost = CM.computePostAttackDamage({
    maneuver = clinchPrep,
    attackSuccesses = 2,
    attackOutcome = "success",
    defenseSuccesses = 0,
})
assert(clinchPost.hit == true and clinchPost.setsGrapple == true and clinchPost.damageDicePool == 5)

local holdPrep = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Nosferatu Imobilizador",
    isVampire = true,
    maneuverId = "hold",
    attrs = { attr_forca = 4, attr_destreza = 2 },
    habs = { hab_briga = 2 },
})
assert(holdPrep.canRoll == true and holdPrep.noDamage == true and holdPrep.setsGrappleOnHit == true)
local holdPost = CM.computePostAttackDamage({
    maneuver = holdPrep,
    attackSuccesses = 1,
    attackOutcome = "success",
    defenseSuccesses = 0,
})
assert(holdPost.hit == true and holdPost.noDamage == true and holdPost.setsGrapple == true and holdPost.damageDicePool == 0)

local kickPenalized = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Lutador Ferido de Colete",
    isVampire = true,
    maneuverId = "kick",
    woundPenalty = -2,
    armorDexPenalty = 1,
    clanDiceMod = -1,
    attrs = { attr_destreza = 4, attr_forca = 3 },
    habs = { hab_briga = 3 },
})
-- ownPool = 7; -2 ferimento -1 armadura -1 clã = 3; dif = 6 + 1 = 7; dano = 3 + 1 = 4 contundente
assert(kickPenalized.canRoll == true and kickPenalized.poolBeforeClanDivisor == 3 and kickPenalized.difficulty == 7)
assert(kickPenalized.baseDamage == 4 and kickPenalized.damageType == "bashing")

local tacklePrep = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Brujah Investida",
    isVampire = true,
    maneuverId = "tackle",
    flankMode = "flanco",
    attrs = { attr_forca = 4, attr_destreza = 3 },
    habs = { hab_briga = 2 },
})
-- dif: 6 + 1 (tackle) - 1 (flanco) = 6; dano: Força(4) + 1 = 5 contundente
assert(tacklePrep.canRoll == true and tacklePrep.attrUsed == "attr_forca" and tacklePrep.poolBeforeClanDivisor == 6)
assert(tacklePrep.difficulty == 6 and tacklePrep.baseDamage == 5 and tacklePrep.damageType == "bashing")

local sweepBrawlPrep = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Artista Marcial",
    isVampire = false,
    maneuverId = "sweep_brawl",
    targetLocation = "membro",
    attrs = { attr_destreza = 4, attr_forca = 2 },
    habs = { hab_briga = 3 },
})
-- dif: 6 + 1 (sweep) + 1 (membro) = 8; dano: Força(2) contundente, extraTargetedDice = 0
assert(sweepBrawlPrep.canRoll == true and sweepBrawlPrep.difficulty == 8 and sweepBrawlPrep.baseDamage == 2 and sweepBrawlPrep.extraTargetedDice == 0)

local sweepMeleePrep = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Guarda de Bastão",
    isVampire = false,
    maneuverId = "sweep_melee",
    attrs = { attr_destreza = 3, attr_forca = 3 },
    habs = { hab_armas_brancas = 3 },
    weapon = { nome = "[TESTE_E2E] Bastão Longo", dif = 6, dano = 2, tipo = "bashing", hab = "hab_armas_brancas" },
})
assert(sweepMeleePrep.canRoll == true and sweepMeleePrep.difficulty == 7 and sweepMeleePrep.baseDamage == 3 and sweepMeleePrep.damageType == "bashing")

local disarmBrawlPrep = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Desarmador Desarmado",
    isVampire = false,
    maneuverId = "disarm_brawl",
    attrs = { attr_destreza = 4, attr_forca = 2 },
    habs = { hab_briga = 3 },
})
assert(disarmBrawlPrep.canRoll == true and disarmBrawlPrep.difficulty == 7 and disarmBrawlPrep.isDisarm == true and disarmBrawlPrep.noDamage == true)

-- Limites de dificuldade [3, 10] e Estaca [9, 10]
local minDiffClamp = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Atacante Surpresa",
    isVampire = true,
    maneuverId = "strike",
    flankMode = "retaguarda",
    extraDiffMod = -5,
    attrs = { attr_destreza = 3, attr_forca = 2 },
    habs = { hab_briga = 2 },
})
assert(minDiffClamp.difficulty == 3)

local maxDiffClamp = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Atirador Cego",
    isVampire = true,
    maneuverId = "full_auto",
    coverLevel = "superior",
    targetLocation = "cabeca",
    attrs = { attr_destreza = 3, attr_forca = 2 },
    habs = { hab_armas_fogo = 2 },
    weapon = { nome = "[TESTE_E2E] Metralhadora", dif = 7, dano = 6, tipo = "lethal", hab = "hab_armas_fogo" },
})
assert(maxDiffClamp.difficulty == 10)

local stakeMaxDiff = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Caçador Cobertura",
    isVampire = false,
    maneuverId = "stake_heart",
    coverLevel = "superior",
    attrs = { attr_destreza = 4, attr_forca = 3 },
    habs = { hab_armas_brancas = 3 },
})
assert(stakeMaxDiff.difficulty == 10 and stakeMaxDiff.baseDamage == 4)

-- 7. Encadeamento Ataque -> Sucessos Líquidos -> Parada de Dano (Potência passiva vs Potência automática por sangue)
local postPassive = CM.computePostAttackDamage({
    maneuver = biteOk,
    attackSuccesses = 4,
    attackOutcome = "success",
    defenseSuccesses = 1,
    passivePotenceDice = 2,
    autoPotenceSuccesses = 0,
})
-- netHits = 3 -> carryOver = 2; baseDamage(4) + carryOver(2) + passivePotence(2) = 8 dados, 0 auto
assert(postPassive.hit == true and postPassive.netHits == 3 and postPassive.carryOverDice == 2)
assert(postPassive.damageDicePool == 8 and postPassive.autoSuccesses == 0 and postPassive.damageType == "aggravated")

local postAuto = CM.computePostAttackDamage({
    maneuver = biteOk,
    attackSuccesses = 4,
    attackOutcome = "success",
    defenseSuccesses = 1,
    passivePotenceDice = 2,
    autoPotenceSuccesses = 2,
})
-- Potência ativada com sangue: 2 sucessos automáticos + 6 dados rolados (base 4 + carryOver 2)
assert(postAuto.hit == true and postAuto.damageDicePool == 6 and postAuto.autoSuccesses == 2)

-- Armas de fogo não somam Potência no dano
local postRanged = CM.computePostAttackDamage({
    maneuver = burst,
    attackSuccesses = 3,
    attackOutcome = "success",
    defenseSuccesses = 0,
    passivePotenceDice = 3,
    autoPotenceSuccesses = 3,
})
assert(postRanged.hit == true and postRanged.damageDicePool == 6 and postRanged.autoSuccesses == 0)

-- Cabeça com Rifle soma extraTargetedDice (+1) na parada de dano encadeada
local postAimedHead = CM.computePostAttackDamage({
    maneuver = aimedHead,
    attackSuccesses = 2,
    attackOutcome = "success",
    defenseSuccesses = 0,
})
-- baseDamage(8) + extraTargetedDice(1) + carryOver(1) = 10 dados Letais
assert(postAimedHead.hit == true and postAimedHead.damageDicePool == 10 and postAimedHead.damageType == "lethal" and postAimedHead.isHeadshot == true)

-- Desarme compara netHits > Força do oponente; botch marca botchedSelf
local disarmPrep = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Esgrimista",
    isVampire = true,
    maneuverId = "disarm_melee",
    attrs = { attr_destreza = 4, attr_forca = 3 },
    habs = { hab_armas_brancas = 4 },
    weapon = { nome = "[TESTE_E2E] Rapieira", dif = 6, dano = 2, tipo = "lethal", hab = "hab_armas_brancas" },
})
assert(disarmPrep.difficulty == 7 and disarmPrep.noDamage == true and disarmPrep.isDisarm == true)
local disarmWin = CM.computePostAttackDamage({
    maneuver = disarmPrep,
    attackSuccesses = 4,
    attackOutcome = "success",
    defenseSuccesses = 0,
    targetStrength = 3,
})
assert(disarmWin.hit == true and disarmWin.noDamage == true and disarmWin.disarm.disarmed == true)
local disarmBotch = CM.computePostAttackDamage({
    maneuver = disarmPrep,
    attackSuccesses = 0,
    attackOutcome = "botch",
    defenseSuccesses = 0,
    targetStrength = 3,
})
assert(disarmBotch.hit == false and disarmBotch.disarm.botchedSelf == true)

-- 8. PF3-1: Strings "false" e 0 do NDB do Firecast JAMAIS são tratadas como truthy em Lua
local spNdbFalse = CM.computeSplitPool(7, 2, 1, 5, "false")
assert(spNdbFalse.bypassedByCelerity == false and spNdbFalse.poolAfterSplit == 3)
local spNdbZero = CM.computeSplitPool(7, 2, 1, 5, 0)
assert(spNdbZero.bypassedByCelerity == false and spNdbZero.poolAfterSplit == 3)
local spNdbStrTrue = CM.computeSplitPool(7, 2, 1, 5, "true")
assert(spNdbStrTrue.bypassedByCelerity == true and spNdbStrTrue.poolAfterSplit == 7)

local ndbBiteBlocked = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Vampiro NDB String False",
    isVampire = "false",
    maneuverId = "bite",
    inGrapple = "false",
    storytellerOverride = "false",
    attrs = { attr_destreza = 3, attr_forca = 3 },
    habs = { hab_briga = 3 },
})
assert(ndbBiteBlocked.canRoll == false, "inGrapple='false' e storytellerOverride='false' não podem liberar Mordida")

local ndbFlagsFalse = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Gangrel NDB Flags False",
    isVampire = "false",
    maneuverId = "claw",
    isCelerityAction = "false",
    hasScope = "false",
    naturalAggravated = "false",
    weaponAggravated = "false",
    storytellerOverride = 0,
    emFrenesi = "false",
    ignoreWoundPenalty = "false",
    woundPenalty = -2,
    totalNormalActions = 2,
    actionNumber = 1,
    attrs = { attr_destreza = 4, attr_forca = 3 },
    habs = { hab_briga = 3 },
})
-- ownPool = 7; split (2 ações, 1ª) = 7 - 2 = 5; woundPenalty (-2 não ignorado!) = 3; naturalAggravated="false" => lethal
assert(ndbFlagsFalse.canRoll == true and ndbFlagsFalse.poolBeforeClanDivisor == 3 and ndbFlagsFalse.damageType == "lethal")
assert(CM.checkStakingParalyze(4, "false").paralyzed == false)
assert(CM.checkStakingParalyze(4, 0).paralyzed == false)
assert(CM.checkStakingParalyze(3, "1").paralyzed == true)

-- 9. Segurança contra nil nas funções públicas
assert(CM.computeSplitPool(nil, nil, nil, nil, nil).poolAfterSplit == 0)
assert(CM.prepareManeuverRoll(nil).canRoll == false)
assert(CM.computePostAttackDamage(nil).hit == false)
assert(CM.checkStakingParalyze(nil, nil).paralyzed == false)
