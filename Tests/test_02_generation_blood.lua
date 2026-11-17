local Generations = require("Data.generations")
local Blood = require("Core.generation_blood")

-- 1. Tabela completa de Gerações (4ª a 15ª), limites V20 e fallbacks seguros
for gen = 4, 15 do
    local row = Generations.get(gen)
    assert(row ~= nil and row.generation == gen, "Geração ausente ou inválida: " .. tostring(gen))
    assert(type(row.traitMax) == "number" and type(row.discMax) == "number")
    assert(type(row.bloodMax) == "number" and type(row.usableBlood) == "number")
    assert(type(row.perTurn) == "number" and type(row.doubleCost) == "boolean")
end

local g4 = Blood.deriveStats(4)
assert(g4.bloodMax == 50 and g4.usableBlood == 50 and g4.perTurn == 10 and g4.traitMax == 9 and g4.discMax == 9 and g4.doubleCost == false)

local g7 = Blood.deriveStats(7)
assert(g7.bloodMax == 20 and g7.perTurn == 4 and g7.traitMax == 6 and g7.discMax == 6)

local g8 = Blood.deriveStats(8)
assert(g8.bloodMax == 15 and g8.perTurn == 3 and g8.traitMax == 5 and g8.discMax == 5)

local g13 = Blood.deriveStats(13)
assert(g13.bloodMax == 10 and g13.usableBlood == 10 and g13.perTurn == 1 and g13.traitMax == 5 and g13.discMax == 5 and g13.doubleCost == false)

local g14 = Blood.deriveStats(14)
assert(g14.bloodMax == 10 and g14.usableBlood == 8 and g14.perTurn == 1 and g14.traitMax == 5 and g14.discMax == 4 and g14.doubleCost == false)

local g15 = Blood.deriveStats(15)
assert(g15.bloodMax == 10 and g15.usableBlood == 6 and g15.perTurn == 1 and g15.traitMax == 5 and g15.discMax == 3 and g15.doubleCost == true)

-- Fallbacks e clamps seguros
assert(Blood.deriveStats(nil).generation == 13, "Fallback nil deve retornar 13ª geração")
assert(Blood.deriveStats("invalido").generation == 13, "Fallback inválido deve retornar 13ª geração")
assert(Generations.get(2).generation == 4, "Geração < 4 deve limitar em 4ª")
assert(Generations.get(18).generation == 15, "Geração > 15 deve limitar em 15ª")
assert(Generations.get("9").generation == 9 and Generations.get("9").perTurn == 2)
assert(Generations.get(8.7).generation == 8, "Geração fracionária deve truncar com segurança")

-- 2. Gasto respeitando limite por turno, imutabilidade, novo turno e exceção de Rapidez
local st = {
    name = "[TESTE_E2E] Jack Brujah",
    generation = 13,
    currentBlood = 10,
    spentThisTurn = 0,
    attr_forca = 3,
    buff_forca = 0,
}
local res1 = Blood.spend(st, 1, { forDisciplineOrHeal = true })
assert(res1.ok == true and res1.costApplied == 1)
assert(res1.newState.currentBlood == 9 and res1.newState.spentThisTurn == 1)
assert(st.currentBlood == 10 and st.spentThisTurn == 0, "Estado original deve ser imutável")
assert(res1.newState.name == "[TESTE_E2E] Jack Brujah")

local res2 = Blood.spend(res1.newState, 1, { forDisciplineOrHeal = true })
assert(res2.ok == false and res2.costApplied == 0 and type(res2.error) == "string", "13ª geração não pode gastar 2 pontos normais no mesmo turno")

local resCel = Blood.spend(res1.newState, 2, { bypassTurnLimit = true, forDisciplineOrHeal = true })
assert(resCel.ok == true and resCel.costApplied == 2 and resCel.newState.currentBlood == 7 and resCel.newState.spentThisTurn == 3, "Rapidez pode exceder limite por turno na V20")

local afterTurn = Blood.newTurn(resCel.newState)
assert(afterTurn.spentThisTurn == 0 and afterTurn.currentBlood == 7)
local resNextTurn = Blood.spend(afterTurn, 1, { forDisciplineOrHeal = true })
assert(resNextTurn.ok == true and resNextTurn.newState.currentBlood == 6)

-- Gasto zero/negativo e reserva insuficiente
local resZero = Blood.spend(st, 0, { forDisciplineOrHeal = true })
assert(resZero.ok == true and resZero.costApplied == 0 and resZero.newState.currentBlood == 10)

local stEmpty = { name = "[TESTE_E2E] Jack Brujah", generation = 13, currentBlood = 0, spentThisTurn = 0 }
local resEmpty = Blood.spend(stEmpty, 1, { forDisciplineOrHeal = true })
assert(resEmpty.ok == false and resEmpty.error == "Reserva de sangue insuficiente.")
local resOverride = Blood.spend(stEmpty, 1, { forDisciplineOrHeal = true, storytellerOverride = true })
assert(resOverride.ok == true and resOverride.newState.currentBlood == 0)

-- 3. Sangue Fraco (V20 p. 487 / PF-1): piso inerte de sustentação vs despertar noturno (14ª e 15ª Geração)
-- 3a. 14ª Geração: bloodMax = 10, usableBlood = 8, piso inerte = 2 (sustentação/despertar)
local st14 = { name = "[TESTE_E2E] Clara Sangue-Fraco 14", generation = 14, currentBlood = 3, spentThisTurn = 0 }
local r14Ok = Blood.spend(st14, 1, { forDisciplineOrHeal = true })
assert(r14Ok.ok == true and r14Ok.costApplied == 1 and r14Ok.newState.currentBlood == 2)

local st14AtFloor = Blood.newTurn(r14Ok.newState)
local r14Blocked = Blood.spend(st14AtFloor, 1, { forDisciplineOrHeal = true })
assert(
    r14Blocked.ok == false and r14Blocked.costApplied == 0
    and r14Blocked.error == "Sangue Fraco atingiu o limite de vitae utilizável para poderes/cura.",
    "14ª geração deve bloquear poderes/cura ao tentar consumir o piso inerte (2 pontos)"
)

local r14Awaken = Blood.spend(st14AtFloor, 1, { forDisciplineOrHeal = false })
assert(
    r14Awaken.ok == true and r14Awaken.costApplied == 1 and r14Awaken.newState.currentBlood == 1,
    "14ª geração deve permitir gasto não-poder/cura (despertar noturno) no piso de sustentação"
)

-- Rastreio cumulativo thinBloodUsed independente do piso
local st14UsedCap = { name = "[TESTE_E2E] Clara Sangue-Fraco 14", generation = 14, currentBlood = 6, spentThisTurn = 0, thinBloodUsed = 8 }
local r14UsedCapBlocked = Blood.spend(st14UsedCap, 1, { forDisciplineOrHeal = true })
assert(
    r14UsedCapBlocked.ok == false and r14UsedCapBlocked.costApplied == 0
    and r14UsedCapBlocked.error == "Sangue Fraco atingiu o limite de vitae utilizável para poderes/cura.",
    "14ª geração deve bloquear quando thinBloodUsed já atingiu usableBlood (8)"
)

-- 3b. 15ª Geração: bloodMax = 10, usableBlood = 6, piso inerte = 4, custo dobrado para poderes/cura
local st15 = { name = "[TESTE_E2E] Lucas Sangue-Fraco 15", generation = 15, currentBlood = 10, spentThisTurn = 0 }
local r15_1 = Blood.spend(st15, 1, { forDisciplineOrHeal = true, bypassTurnLimit = true })
assert(r15_1.ok == true and r15_1.costApplied == 2 and r15_1.newState.currentBlood == 8)

local r15_2 = Blood.spend(r15_1.newState, 1, { forDisciplineOrHeal = true, bypassTurnLimit = true })
local r15_3 = Blood.spend(r15_2.newState, 1, { forDisciplineOrHeal = true, bypassTurnLimit = true })
assert(r15_3.ok == true and r15_3.newState.currentBlood == 4 and r15_3.newState.thinBloodUsed == 6)

local r15BlockedAtFloor = Blood.spend(r15_3.newState, 1, { forDisciplineOrHeal = true, bypassTurnLimit = true })
assert(
    r15BlockedAtFloor.ok == false and r15BlockedAtFloor.costApplied == 0
    and r15BlockedAtFloor.error == "Sangue Fraco atingiu o limite de vitae utilizável para poderes/cura.",
    "15ª geração deve bloquear poderes/cura ao atingir o piso inerte de 4 pontos"
)

-- Mesmo com thinBloodUsed = 0, se currentBlood = 5 na 15ª geração, custo 2 cairia para 3 (< piso 4) e deve bloquear
local st15Partial = { name = "[TESTE_E2E] Lucas Sangue-Fraco 15", generation = 15, currentBlood = 5, spentThisTurn = 0, thinBloodUsed = 0 }
local r15PartialBlocked = Blood.spend(st15Partial, 1, { forDisciplineOrHeal = true, bypassTurnLimit = true })
assert(
    r15PartialBlocked.ok == false and r15PartialBlocked.costApplied == 0
    and r15PartialBlocked.error == "Sangue Fraco atingiu o limite de vitae utilizável para poderes/cura.",
    "15ª geração com 5 pontos não pode gastar 2 para poderes/cura invadindo o piso inerte de 4"
)

-- Despertar noturno na 15ª geração (sem forDisciplineOrHeal): custa 1 (sem dobrar) e pode usar o piso inerte
local st15AwakenTurn = Blood.newTurn(r15_3.newState)
local r15Awaken = Blood.spend(st15AwakenTurn, 1, {})
assert(
    r15Awaken.ok == true and r15Awaken.costApplied == 1 and r15Awaken.newState.currentBlood == 3,
    "15ª geração deve poder gastar 1 ponto normal do piso inerte para despertar à noite"
)

-- 4. Alimentação (Blood.gain): respeita teto da geração e restaura uso de Sangue Fraco
local gained15 = Blood.gain(r15_3.newState, 8)
assert(gained15.newState.currentBlood == 10 and gained15.added == 6 and gained15.newState.thinBloodUsed == 0)
local r15AfterFeed = Blood.spend(Blood.newTurn(gained15.newState), 1, { forDisciplineOrHeal = true, bypassTurnLimit = true })
assert(r15AfterFeed.ok == true and r15AfterFeed.newState.currentBlood == 8)

local gained4 = Blood.gain({ name = "[TESTE_E2E] Ancião Matusalém", generation = 4, currentBlood = 47 }, 10)
assert(gained4.newState.currentBlood == 50 and gained4.added == 3)

local gainZero = Blood.gain({ name = "[TESTE_E2E] Clara Sangue-Fraco 14", generation = 14, currentBlood = 6, thinBloodUsed = 4 }, 0)
assert(gainZero.added == 0 and gainZero.newState.thinBloodUsed == 4)

-- 5. Blood Buff Físico até traitMax + 1 e limpeza de cena
local stBuff = {
    name = "[TESTE_E2E] Jack Brujah",
    generation = 13,
    currentBlood = 10,
    spentThisTurn = 0,
    attr_forca = 5,
    buff_forca = 0,
    attr_destreza = 3,
    buff_destreza = 0,
    attr_vigor = 2,
    buff_vigor = 0,
}

local bInvalid = Blood.applyPhysicalBuff(stBuff, "carisma")
assert(bInvalid.ok == false and bInvalid.newState.currentBlood == 10, "Atributo Social/Mental não recebe Blood Buff")

local b1 = Blood.applyPhysicalBuff(stBuff, "forca")
assert(b1.ok == true and b1.effectiveAttr == 6 and b1.temporaryAboveMax == true and b1.newState.currentBlood == 9)

-- Mesmo turno na 13ª geração: segundo buff para destreza deve falhar pelo limite por turno
local bSameTurn = Blood.applyPhysicalBuff(b1.newState, "destreza")
assert(bSameTurn.ok == false and bSameTurn.newState.currentBlood == 9)

local b2 = Blood.newTurn(b1.newState)
local b3 = Blood.applyPhysicalBuff(b2, "forca")
assert(b3.ok == false and b3.effectiveAttr == 6 and b3.temporaryAboveMax == true and b3.newState.currentBlood == 9, "Não pode ultrapassar traitMax + 1 com Blood Buff")

local bDex = Blood.applyPhysicalBuff(b2, "destreza")
assert(bDex.ok == true and bDex.effectiveAttr == 4 and bDex.temporaryAboveMax == false and bDex.newState.currentBlood == 8)

local cleared = Blood.clearSceneBuffs(bDex.newState)
assert(cleared.buff_forca == 0 and cleared.buff_destreza == 0 and cleared.buff_vigor == 0 and cleared.spentThisTurn == 0)
assert(cleared.currentBlood == 8 and cleared.attr_forca == 5)

-- Escalonamento de Ancião (7ª geração: traitMax = 6 -> Blood Buff até 7)
local stElder = {
    name = "[TESTE_E2E] Helena Anciã 7",
    generation = 7,
    currentBlood = 20,
    spentThisTurn = 0,
    attr_vigor = 6,
    buff_vigor = 0,
}
local bElder1 = Blood.applyPhysicalBuff(stElder, "vigor")
assert(bElder1.ok == true and bElder1.effectiveAttr == 7 and bElder1.temporaryAboveMax == true)
local bElder2 = Blood.applyPhysicalBuff(bElder1.newState, "vigor")
assert(bElder2.ok == false and bElder2.effectiveAttr == 7 and bElder2.newState.currentBlood == 19)
