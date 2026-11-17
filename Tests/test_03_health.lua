local Blood = require("Core.generation_blood")
local Health = require("Core.health")

-- 1. Empilhamento (* > X > /), todos os 7 níveis padrão V20, Tamanho Imenso (8 caixas) e estados de Torpor/Morte
local st = {
    name = "[TESTE_E2E] Jack Brujah",
    bashing = 2,
    lethal = 1,
    aggravated = 1,
    hugeSize = false,
    isVampire = true,
}
local info = Health.getStatus(st)
assert(info.totalBoxes == 7)
assert(info.boxes[1] == "*" and info.boxes[2] == "X" and info.boxes[3] == "/" and info.boxes[4] == "/")
assert(info.boxes[5] == "" and info.boxes[6] == "" and info.boxes[7] == "")
assert(info.currentLevelName == "Ferido Gravemente" and info.penalty == -2)
assert(info.incapacitated == false and info.torporOrDeath == nil)

-- Saudável (0 níveis preenchidos) e segurança contra nil
local healthy = Health.getStatus({ name = "[TESTE_E2E] Elena Toreador", isVampire = true })
assert(healthy.totalBoxes == 7 and healthy.currentLevelName == "Saudável" and healthy.penalty == 0 and healthy.incapacitated == false)
assert(Health.getStatus(nil).currentLevelName == "Saudável")

-- Verificação de todos os 7 níveis padrão na ordem exata V20
local expectedLevels = {
    { filled = 1, name = "Escoriado",         penalty = 0,  incapacitated = false },
    { filled = 2, name = "Machucado",         penalty = -1, incapacitated = false },
    { filled = 3, name = "Ferido",            penalty = -1, incapacitated = false },
    { filled = 4, name = "Ferido Gravemente", penalty = -2, incapacitated = false },
    { filled = 5, name = "Espancado",         penalty = -2, incapacitated = false },
    { filled = 6, name = "Aleijado",          penalty = -5, incapacitated = false },
    { filled = 7, name = "Incapacitado",      penalty = 0,  incapacitated = true  },
}
for _, exp in ipairs(expectedLevels) do
    local s = Health.getStatus({ name = "[TESTE_E2E] Marcus Ventrue", isVampire = true, bashing = exp.filled })
    assert(s.currentLevelName == exp.name, "Nível incorreto em " .. exp.filled .. ": " .. tostring(s.currentLevelName))
    assert(s.penalty == exp.penalty, "Penalidade incorreta em " .. exp.filled)
    assert(s.incapacitated == exp.incapacitated, "Flag incapacitado incorreta em " .. exp.filled)
    assert(s.torporOrDeath == nil, "Apenas contundente não deve disparar Torpor/Morte")
end

-- Qualidade Tamanho Imenso (Huge Size): +1 caixa Escoriado (Extra) -> 8 caixas
local stHuge = { name = "[TESTE_E2E] Viktor Gangrel Imenso", hugeSize = true, isVampire = true, bashing = 1 }
local infoHuge1 = Health.getStatus(stHuge)
assert(infoHuge1.totalBoxes == 8 and infoHuge1.currentLevelName == "Escoriado (Extra)" and infoHuge1.penalty == 0)
local infoHuge2 = Health.getStatus({ name = "[TESTE_E2E] Viktor Gangrel Imenso", hugeSize = true, isVampire = true, bashing = 2 })
assert(infoHuge2.currentLevelName == "Escoriado" and infoHuge2.penalty == 0)
local infoHuge7 = Health.getStatus({ name = "[TESTE_E2E] Viktor Gangrel Imenso", hugeSize = true, isVampire = true, lethal = 7 })
assert(infoHuge7.currentLevelName == "Aleijado" and infoHuge7.penalty == -5 and infoHuge7.torporOrDeath == nil)
local infoHuge8 = Health.getStatus({ name = "[TESTE_E2E] Viktor Gangrel Imenso", hugeSize = true, isVampire = true, lethal = 8 })
assert(infoHuge8.currentLevelName == "Incapacitado" and infoHuge8.incapacitated == true and infoHuge8.torporOrDeath == "Torpor (ou Morte se sem sangue)")

-- Torpor / Morte Final (Vampiro vs Mortal)
local vTorpor = Health.getStatus({ name = "[TESTE_E2E] Jack Brujah", isVampire = true, lethal = 5, aggravated = 2 })
assert(vTorpor.incapacitated == true and vTorpor.torporOrDeath == "Torpor (ou Morte se sem sangue)")

local mCrit = Health.getStatus({ name = "[TESTE_E2E] Roberto Mortal", isVampire = false, lethal = 7 })
assert(mCrit.incapacitated == true and mCrit.torporOrDeath == "Agonia Crítica / Morte")

local vFinal = Health.getStatus({ name = "[TESTE_E2E] Jack Brujah", isVampire = true, aggravated = 7 })
assert(vFinal.incapacitated == true and vFinal.torporOrDeath == "Morte Final")

local mDead = Health.getStatus({ name = "[TESTE_E2E] Roberto Mortal", isVampire = false, aggravated = 7 })
assert(mDead.incapacitated == true and mDead.torporOrDeath == "Morte")

-- 2. Upgrade de Contundente para Letal quando estoura 7 níveis (e imutabilidade)
local stFull = { name = "[TESTE_E2E] Jack Brujah", bashing = 7, lethal = 0, aggravated = 0, isVampire = true }
local after = Health.applyDamage(stFull, 2, "bashing", { isVampire = true })
assert(after.lethal == 2 and after.bashing == 5 and after.aggravated == 0, "Excedente contundente deve virar letal")
assert(stFull.bashing == 7 and stFull.lethal == 0, "applyDamage não deve mutar a tabela original")

-- Contundente não converte Letal em Agravado quando trilha já está toda em Letal
local stAllLethal = { name = "[TESTE_E2E] Jack Brujah", bashing = 0, lethal = 7, aggravated = 0, isVampire = true }
local afterMoreBash = Health.applyDamage(stAllLethal, 3, "bashing", { isVampire = true })
assert(afterMoreBash.lethal == 7 and afterMoreBash.aggravated == 0 and afterMoreBash.bashing == 0)

-- Dano Letal desloca/converte Contundente quando trilha cheia, mas não sobrescreve Agravado
local stMixed = { name = "[TESTE_E2E] Jack Brujah", bashing = 3, lethal = 3, aggravated = 1, isVampire = true }
local afterLethal = Health.applyDamage(stMixed, 2, "lethal", { isVampire = true })
assert(afterLethal.aggravated == 1 and afterLethal.lethal == 5 and afterLethal.bashing == 1)
local afterExcessLethal = Health.applyDamage(afterLethal, 5, "lethal", { isVampire = true })
assert(afterExcessLethal.aggravated == 1 and afterExcessLethal.lethal == 6 and afterExcessLethal.bashing == 0)

-- Dano Agravado desloca Contundente primeiro e depois Letal até preencher toda a trilha
local stForAgg = { name = "[TESTE_E2E] Jack Brujah", bashing = 2, lethal = 4, aggravated = 1, isVampire = true }
local afterAgg = Health.applyDamage(stForAgg, 4, "aggravated", { isVampire = true })
assert(afterAgg.aggravated == 5 and afterAgg.lethal == 2 and afterAgg.bashing == 0)

-- 3. Arma de fogo em Vampiro vira Contundente e divide pela metade após absorção; Tiro na Cabeça e Mortal permanecem Letal
local vShot = Health.applyDamage({ name = "[TESTE_E2E] Jack Brujah", bashing = 0, lethal = 0, aggravated = 0 }, 5, "lethal", {
    isVampire = true, isFirearm = true, halveBashing = true
})
assert(vShot.bashing == 2 and vShot.lethal == 0, "5 contundente pós-absorção / 2 = 2 contundente")

-- 1 nível contundente pós-absorção dividido pela metade arredonda para baixo (0) conforme especificação V20/brief
local vGlance = Health.applyDamage({ name = "[TESTE_E2E] Jack Brujah", bashing = 0, lethal = 0, aggravated = 0 }, 1, "bashing", {
    isVampire = true, halveBashing = true
})
assert(vGlance.bashing == 0)

-- Tiro na cabeça (headshot) em Vampiro permanece Letal e NÃO é dividido pela metade
local vHeadshot = Health.applyDamage({ name = "[TESTE_E2E] Jack Brujah", bashing = 0, lethal = 0, aggravated = 0 }, 5, "lethal", {
    isVampire = true, isFirearm = true, headshot = true, halveBashing = true
})
assert(vHeadshot.lethal == 5 and vHeadshot.bashing == 0, "Headshot de arma de fogo em vampiro permanece letal")

-- Fallback seguro para state.isVampire quando opts.isVampire é omitido
local vImplicit = Health.applyDamage({ name = "[TESTE_E2E] Jack Brujah", isVampire = true, bashing = 0, lethal = 0, aggravated = 0 }, 4, "lethal", {
    isFirearm = true, halveBashing = true
})
assert(vImplicit.bashing == 2 and vImplicit.lethal == 0)

local mShot = Health.applyDamage({ name = "[TESTE_E2E] Roberto Mortal", bashing = 0, lethal = 0, aggravated = 0 }, 3, "lethal", {
    isVampire = false, isFirearm = true, halveBashing = true
})
assert(mShot.lethal == 3 and mShot.bashing == 0, "Arma de fogo em mortal permanece letal")

-- 4. Absorção: Mortal, Carniçal e Vampiro (Contundente, Letal, Agravado e integração com Blood Buff em Vigor)
local mSoak = Health.buildSoakPool({ name = "[TESTE_E2E] Roberto Mortal", isVampire = false, attr_vigor = 3, armor = 0 }, "lethal")
assert(mSoak.canSoak == false and mSoak.pool == 0 and mSoak.difficulty == 6 and type(mSoak.reason) == "string")

-- Mortal COM armadura absorve Letal apenas com os dados da armadura (sem Vigor)
local mArmorLethal = Health.buildSoakPool({ name = "[TESTE_E2E] Roberto Mortal", isVampire = false, attr_vigor = 3, armor = 2 }, "lethal")
assert(mArmorLethal.canSoak == true and mArmorLethal.pool == 2 and mArmorLethal.reason == nil)

-- Mortal absorve Contundente com Vigor + Armadura
local mBash = Health.buildSoakPool({ name = "[TESTE_E2E] Roberto Mortal", isVampire = false, attr_vigor = 3, armor = 2 }, "bashing")
assert(mBash.canSoak == true and mBash.pool == 5)

-- Carniçal absorve Letal com Vigor + Fortitude + Armadura
local gSoak = Health.buildSoakPool({ name = "[TESTE_E2E] Igor Carniçal", isVampire = false, isGhoul = true, attr_vigor = 3, fortitude = 1, armor = 1 }, "lethal")
assert(gSoak.canSoak == true and gSoak.pool == 5)

local vSoak = Health.buildSoakPool({ name = "[TESTE_E2E] Jack Brujah", isVampire = true, attr_vigor = 3, fortitude = 2, armor = 1 }, "lethal")
assert(vSoak.canSoak == true and vSoak.pool == 6 and vSoak.difficulty == 6)

-- Integração com Blood Buff em Vigor
local vBuffedRes = Blood.applyPhysicalBuff({
    name = "[TESTE_E2E] Jack Brujah",
    isVampire = true,
    generation = 13,
    currentBlood = 10,
    spentThisTurn = 0,
    attr_vigor = 3,
    buff_vigor = 0,
    fortitude = 1,
    armor = 1,
}, "vigor")
assert(vBuffedRes.ok == true)
local vBuffSoak = Health.buildSoakPool(vBuffedRes.newState, "lethal")
assert(vBuffSoak.canSoak == true and vBuffSoak.pool == 6, "Blood Buff em Vigor (+1) deve somar na parada de absorção")

-- Agravado exige Fortitude > 0 e usa apenas Fortitude
local vAggNoFort = Health.buildSoakPool({ name = "[TESTE_E2E] Jack Brujah", isVampire = true, attr_vigor = 4, fortitude = 0, armor = 2 }, "aggravated")
assert(vAggNoFort.canSoak == false and vAggNoFort.pool == 0 and vAggNoFort.reason == "Dano Agravado exige Fortitude para absorção.")

local vAgg = Health.buildSoakPool({ name = "[TESTE_E2E] Jack Brujah", isVampire = true, attr_vigor = 4, fortitude = 2, armor = 0 }, "aggravated")
assert(vAgg.canSoak == true and vAgg.pool == 2, "Agravado só usa Fortitude (+ armadura aplicável)")

-- 5. Cura pelo sangue (Contundente, Letal, Agravado, limites por turno, Sangue Fraco 15ª ger. e PF-2)
-- Mortal não cura com sangue
local mHeal = Health.healWithBlood({ name = "[TESTE_E2E] Roberto Mortal", isVampire = false, bashing = 2, currentBlood = 5 }, "bashing", {})
assert(mHeal.ok == false and mHeal.error == "Apenas vampiros e carniçais curam ferimentos com sangue.")

-- Cura Letal básica e respeito ao limite por turno da 13ª geração
local vHeal = Health.healWithBlood({
    name = "[TESTE_E2E] Jack Brujah",
    isVampire = true,
    generation = 13,
    currentBlood = 8,
    spentThisTurn = 0,
    bashing = 1,
    lethal = 1,
    aggravated = 0,
}, "lethal", {})
assert(vHeal.ok == true and vHeal.newState.lethal == 0 and vHeal.newState.currentBlood == 7 and vHeal.newState.spentThisTurn == 1)

-- Segundo nível no mesmo turno para 13ª geração falha pelo limite de 1 sangue/turno
local vHealSameTurn = Health.healWithBlood(vHeal.newState, "bashing", {})
assert(vHealSameTurn.ok == false and vHealSameTurn.newState.bashing == 1 and vHealSameTurn.newState.currentBlood == 7)

-- No turno seguinte (ou com bypassTurnLimit), cura o contundente restante
local vHealNextTurn = Health.healWithBlood(Blood.newTurn(vHeal.newState), "bashing", {})
assert(vHealNextTurn.ok == true and vHealNextTurn.newState.bashing == 0 and vHealNextTurn.newState.currentBlood == 6)

-- Tentativa de curar tipo de dano zerado falha sem gastar sangue
local vHealNone = Health.healWithBlood(vHealNextTurn.newState, "lethal", {})
assert(vHealNone.ok == false and vHealNone.newState.currentBlood == 6 and vHealNone.error == "Nenhum dano desse tipo para curar.")

-- PF-2 #2: 15ª Geração (doubleCost = true -> custo 2, perTurn = 1, usableBlood = 6) com bypassTurnLimit
local st15Heal = {
    name = "[TESTE_E2E] Lucas Sangue-Fraco 15",
    isVampire = true,
    generation = 15,
    currentBlood = 10,
    spentThisTurn = 0,
    bashing = 2,
    lethal = 2,
    aggravated = 0,
}
local r15NoBypass = Health.healWithBlood(st15Heal, "lethal", {})
assert(r15NoBypass.ok == false and r15NoBypass.newState.currentBlood == 10, "Sem bypassTurnLimit, custo 2 excede perTurn = 1 da 15ª geração")

local r15Bypass1 = Health.healWithBlood(st15Heal, "lethal", { bypassTurnLimit = true })
assert(r15Bypass1.ok == true and r15Bypass1.newState.lethal == 1 and r15Bypass1.newState.currentBlood == 8 and r15Bypass1.newState.thinBloodUsed == 2)

local r15Bypass2 = Health.healWithBlood(r15Bypass1.newState, "lethal", { bypassTurnLimit = true })
local r15Bypass3 = Health.healWithBlood(r15Bypass2.newState, "bashing", { bypassTurnLimit = true })
assert(r15Bypass3.ok == true and r15Bypass3.newState.currentBlood == 4 and r15Bypass3.newState.thinBloodUsed == 6)

local r15FloorBlocked = Health.healWithBlood(r15Bypass3.newState, "bashing", { bypassTurnLimit = true })
assert(r15FloorBlocked.ok == false and r15FloorBlocked.newState.currentBlood == 4 and r15FloorBlocked.newState.bashing == 1, "Piso inerte de 4 pontos da 15ª geração deve bloquear cura adicional")

-- Cura de Dano Agravado: 5 pontos de sangue durante descanso diurno, e PF-2 #1 (Força de Vontade extra)
local stAgg = {
    name = "[TESTE_E2E] Jack Brujah",
    isVampire = true,
    generation = 13,
    currentBlood = 10,
    spentThisTurn = 0,
    aggravated = 2,
    fdv_temp = 1,
}
local rAgg1 = Health.healWithBlood(stAgg, "aggravated", {})
assert(rAgg1.ok == true and rAgg1.newState.aggravated == 1 and rAgg1.newState.currentBlood == 5 and rAgg1.newState.fdv_temp == 1)

-- Segundo nível Agravado na mesma noite exige useWillpowerForExtra = true (+5 sangue e -1 FdV temporária)
local rAgg2 = Health.healWithBlood(rAgg1.newState, "aggravated", { useWillpowerForExtra = true })
assert(rAgg2.ok == true and rAgg2.newState.aggravated == 0 and rAgg2.newState.currentBlood == 0 and rAgg2.newState.fdv_temp == 0)

-- Nenhum nível Agravado restante
local rAggNone = Health.healWithBlood(rAgg2.newState, "aggravated", {})
assert(rAggNone.ok == false and rAggNone.error == "Nenhum nível de dano Agravado para curar.")

-- PF-2 #1: useWillpowerForExtra = true com fdv_temp < 1 (e sem storytellerOverride) falha ANTES de gastar sangue!
local stAggNoWP = {
    name = "[TESTE_E2E] Jack Brujah",
    isVampire = true,
    generation = 8,
    currentBlood = 12,
    spentThisTurn = 0,
    aggravated = 2,
    fdv_temp = 0,
}
local rAggNoWP = Health.healWithBlood(stAggNoWP, "aggravated", { useWillpowerForExtra = true })
assert(
    rAggNoWP.ok == false
    and rAggNoWP.error == "Força de Vontade temporária insuficiente para curar nível Agravado adicional."
    and rAggNoWP.newState.currentBlood == 12
    and rAggNoWP.newState.spentThisTurn == 0
    and rAggNoWP.newState.aggravated == 2,
    "PF-2 #1: falta de FdV temporária deve falhar ANTES de Blood.spend sem descontar sangue"
)

-- PF-2 #1 com storytellerOverride = true permite curar mesmo com fdv_temp == 0 sem negativar fdv_temp
local rAggOverride = Health.healWithBlood(stAggNoWP, "aggravated", { useWillpowerForExtra = true, storytellerOverride = true })
assert(rAggOverride.ok == true and rAggOverride.newState.aggravated == 1 and rAggOverride.newState.currentBlood == 7 and rAggOverride.newState.fdv_temp == 0)
