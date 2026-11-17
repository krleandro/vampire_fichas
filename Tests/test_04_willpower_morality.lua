local Clans = require("Data.clans")
local MoralityVirtues = require("Data.morality_virtues")
local WM = require("Core.willpower_morality")

-- 1. Todos os 13 clãs tradicionais + Caitiff presentes (14 entradas), Nosferatu com appearanceZero
assert(#Clans.ORDER == 14, "Esperado 14 entradas em Clans.ORDER (13 clãs + Caitiff)")

local expectedOrder = {
    "brujah", "gangrel", "malkavian", "nosferatu", "toreador", "tremere", "ventrue",
    "assamite", "setite", "giovanni", "lasombra", "ravnos", "tzimisce", "caitiff",
}
for i, cid in ipairs(expectedOrder) do
    assert(Clans.ORDER[i] == cid, "Ordem incorreta no índice " .. i .. ": " .. tostring(Clans.ORDER[i]))
    local c = Clans.CLANS[cid]
    assert(type(c) == "table", "Clã ausente em Clans.CLANS: " .. cid)
    assert(c.id == cid, "Campo id divergente em " .. cid)
    assert(type(c.dataType) == "string" and c.dataType:match("^br%.com%.v20%.%w+$") ~= nil, "dataType inválido em " .. cid)
    assert(type(c.name) == "string" and #c.name > 0, "Nome pt-BR ausente em " .. cid)
    assert(type(c.accentColor) == "string" and c.accentColor:match("^#%x%x%x%x%x%x$") ~= nil, "accentColor inválida em " .. cid)
    assert(type(c.appearanceZero) == "boolean", "appearanceZero deve ser boolean em " .. cid)
    assert(type(c.disciplines) == "table", "disciplines deve ser tabela em " .. cid)
    assert(type(c.weaknessId) == "string" and #c.weaknessId > 0, "weaknessId ausente em " .. cid)
    assert(type(c.weaknessSummary) == "string" and #c.weaknessSummary > 0, "weaknessSummary ausente em " .. cid)
    if cid == "nosferatu" then
        assert(c.appearanceZero == true, "Nosferatu deve ter appearanceZero == true")
    else
        assert(c.appearanceZero == false, cid .. " deve ter appearanceZero == false")
    end
    if cid == "caitiff" then
        assert(#c.disciplines == 0, "Caitiff não possui disciplinas de clã")
    else
        assert(#c.disciplines == 3, cid .. " deve ter exatamente 3 disciplinas de clã")
    end
end

assert(Clans.CLANS.brujah.disciplines[1] == "celerity")
assert(Clans.CLANS.brujah.disciplines[2] == "potence")
assert(Clans.CLANS.brujah.disciplines[3] == "presence")
assert(Clans.CLANS.brujah.accentColor == "#9E1B24")
assert(Clans.CLANS.nosferatu.appearanceZero == true)
assert(#Clans.CLANS.caitiff.disciplines == 0)

local expectedClanDisciplines = {
    brujah    = { "celerity", "potence", "presence" },
    gangrel   = { "animalism", "fortitude", "protean" },
    malkavian = { "auspex", "dementation", "obfuscate" },
    nosferatu = { "animalism", "obfuscate", "potence" },
    toreador  = { "auspex", "celerity", "presence" },
    tremere   = { "auspex", "dominate", "thaumaturgy" },
    ventrue   = { "dominate", "fortitude", "presence" },
    assamite  = { "celerity", "obfuscate", "quietus" },
    setite    = { "obfuscate", "presence", "serpentis" },
    giovanni  = { "dominate", "necromancy", "potence" },
    lasombra  = { "dominate", "obtenebration", "potence" },
    ravnos    = { "animalism", "chimerstry", "fortitude" },
    tzimisce  = { "animalism", "auspex", "vicissitude" },
}
for cid, discs in pairs(expectedClanDisciplines) do
    for idx = 1, 3 do
        assert(Clans.CLANS[cid].disciplines[idx] == discs[idx], "Disciplina incorreta em " .. cid .. "[" .. idx .. "]")
    end
end

-- 2. Trilhas, Estímulos e Modificador de Aura V20 (p. 312)
assert(#MoralityVirtues.PATHS == 8, "Esperado 8 trilhas em MoralityVirtues.PATHS")
assert(MoralityVirtues.PATHS[1].id == "humanidade" and MoralityVirtues.PATHS[1].v1 == "consciencia" and MoralityVirtues.PATHS[1].v2 == "autocontrole")
assert(MoralityVirtues.PATHS[2].id == "metamorfose" and MoralityVirtues.PATHS[2].v1 == "conviccao" and MoralityVirtues.PATHS[2].v2 == "instinto")
assert(#MoralityVirtues.FRENZY_STIMULI == 5 and MoralityVirtues.FRENZY_STIMULI[5].diff == 8)
assert(#MoralityVirtues.ROTSCHRECK_STIMULI == 5 and MoralityVirtues.ROTSCHRECK_STIMULI[5].diff == 9)

assert(MoralityVirtues.getAuraModifier(10).diffMod == -2)
assert(MoralityVirtues.getAuraModifier(9).diffMod == -1)
assert(MoralityVirtues.getAuraModifier(8).diffMod == -1)
assert(MoralityVirtues.getAuraModifier(7).diffMod == 0)
assert(MoralityVirtues.getAuraModifier(6).diffMod == 0)
assert(MoralityVirtues.getAuraModifier(5).diffMod == 0)
assert(MoralityVirtues.getAuraModifier(4).diffMod == 0)
assert(MoralityVirtues.getAuraModifier(3).diffMod == 1)
assert(MoralityVirtues.getAuraModifier(2).diffMod == 1)
assert(MoralityVirtues.getAuraModifier(1).diffMod == 2)
assert(MoralityVirtues.getAuraModifier(0).diffMod == 5)
assert(MoralityVirtues.getAuraModifier(nil).diffMod == 0, "Score nil deve usar padrão 7 (Neutra = 0)")
assert(MoralityVirtues.getAuraModifier(0 / 0).diffMod == 0, "Score NaN deve usar padrão seguro 7 (Neutra = 0)")
assert(MoralityVirtues.getAuraModifier(1.5).diffMod == 2, "Score fracionário deve arredondar para baixo com segurança")
assert(WM.getAuraModifier(10).diffMod == -2 and WM.getAuraModifier(1).diffMod == 2)

-- 3. Gasto de Força de Vontade temporária (imutabilidade, bloqueio e storytellerOverride)
local stWP = { name = "[TESTE_E2E] Jack Brujah", fdv_temp = 3, fdv_perm = 6 }
local wp1 = WM.spendWillpower(stWP, 1)
assert(wp1.ok == true and wp1.newState.fdv_temp == 2 and wp1.error == nil)
assert(stWP.fdv_temp == 3, "spendWillpower não deve mutar a tabela original")

local wp2 = WM.spendWillpower(wp1.newState, 2)
assert(wp2.ok == true and wp2.newState.fdv_temp == 0)

local wpFail = WM.spendWillpower(wp2.newState, 1)
assert(wpFail.ok == false and wpFail.newState.fdv_temp == 0 and wpFail.error == "Força de Vontade temporária insuficiente.")

local wpOverride = WM.spendWillpower({ name = "[TESTE_E2E] Jack Brujah", fdv_temp = 0, storytellerOverride = true }, 1)
assert(wpOverride.ok == true and wpOverride.newState.fdv_temp == 0)
assert(WM.spendWillpower(nil, 1).ok == false)

-- 4. Fraqueza Brujah no Frenesi: +2 de dificuldade (teto 10) e bloqueia evitar com FdV
local fBrujah = WM.prepareFrenzyCheck({
    name = "[TESTE_E2E] Jack Brujah",
    cla_id = "brujah",
    virtude2_tipo = "autocontrole",
    virtude2_val = 3,
}, 6)
assert(fBrujah.pool == 3)
assert(fBrujah.difficulty == 8, "Brujah soma +2 na dificuldade de Frenesi")
assert(fBrujah.canAvoidWithWillpower == false, "Brujah não pode gastar FdV para evitar entrar em Frenesi")
assert(#fBrujah.notes >= 2)

-- Teto de dificuldade 10 na Fraqueza Brujah (9 + 2 -> 10)
local fBrujahCap = WM.prepareFrenzyCheck({
    name = "[TESTE_E2E] Jack Brujah",
    cla_id = "brujah",
    virtude2_tipo = "instinto",
    virtude2_val = 2,
}, 9)
assert(fBrujahCap.pool == 2 and fBrujahCap.difficulty == 10 and fBrujahCap.canAvoidWithWillpower == false)
assert(#fBrujahCap.notes == 3, "Brujah com Instinto deve incluir nota base + Instinto + Fraqueza Brujah")

-- Não-Brujah mantém dificuldade base e pode evitar com Força de Vontade
local fToreador = WM.prepareFrenzyCheck({
    name = "[TESTE_E2E] Elena Toreador",
    cla_id = "toreador",
    virtude2_tipo = "autocontrole",
    virtude2_val = 4,
}, 6)
assert(fToreador.pool == 4 and fToreador.difficulty == 6 and fToreador.canAvoidWithWillpower == true)

-- Seguidor de Trilha com Instinto (não-Brujah)
local fTzimisce = WM.prepareFrenzyCheck({
    name = "[TESTE_E2E] Dragos Tzimisce",
    cla_id = "tzimisce",
    virtude2_tipo = "instinto",
    virtude2_val = 4,
}, 6)
assert(fTzimisce.pool == 4 and fTzimisce.difficulty == 6 and fTzimisce.canAvoidWithWillpower == true and #fTzimisce.notes == 2)

-- 5. Rötschreck (Coragem) e Degeneração (Consciência/Convicção dif 8)
local rotBrujah = WM.prepareRotschreckCheck({
    name = "[TESTE_E2E] Jack Brujah",
    cla_id = "brujah",
    virtude3_val = 4,
}, 9)
assert(rotBrujah.pool == 4 and rotBrujah.difficulty == 9, "Rötschreck usa Coragem sem penalidade de Fraqueza Brujah")
assert(WM.prepareRotschreckCheck({ name = "[TESTE_E2E] Jack Brujah", virtude3_val = 2 }, 15).difficulty == 10)
assert(WM.prepareRotschreckCheck({ name = "[TESTE_E2E] Jack Brujah", virtude3_val = 2 }, 1).difficulty == 2)

local degConsc = WM.prepareDegenerationCheck({
    name = "[TESTE_E2E] Elena Toreador",
    virtude1_tipo = "consciencia",
    virtude1_val = 3,
})
assert(degConsc.pool == 3 and degConsc.difficulty == 8 and degConsc.virtueUsed == "Consciência")

local degConv = WM.prepareDegenerationCheck({
    name = "[TESTE_E2E] Dragos Tzimisce",
    virtude1_tipo = "conviccao",
    virtude1_val = 4,
})
assert(degConv.pool == 4 and degConv.difficulty == 8 and degConv.virtueUsed == "Convicção")

-- 6. Despertar Noturno desconta 1 de sangue, zera spentThisTurn e alerta risco de fome quando reserva baixa
local stAwkLow = {
    name = "[TESTE_E2E] Jack Brujah",
    isVampire = true,
    generation = 13,
    currentBlood = 3,
    spentThisTurn = 1,
    virtude2_val = 3,
}
local awk = WM.awakenNightly(stAwkLow)
assert(awk.ok == true and awk.newState.currentBlood == 2 and awk.newState.spentThisTurn == 0 and awk.hungerFrenzyRisk == true)
assert(type(awk.warning) == "string" and awk.warning:find("Fome intensa") ~= nil)
assert(stAwkLow.currentBlood == 3 and stAwkLow.spentThisTurn == 1, "awakenNightly não deve mutar estado original")

-- Vampiro saciado ao despertar não dispara risco de Frenesi de fome
local awkFed = WM.awakenNightly({
    name = "[TESTE_E2E] Elena Toreador",
    isVampire = true,
    generation = 12,
    currentBlood = 9,
    spentThisTurn = 1,
    virtude2_val = 3,
})
assert(awkFed.ok == true and awkFed.newState.currentBlood == 8 and awkFed.newState.spentThisTurn == 0 and awkFed.hungerFrenzyRisk == false and awkFed.warning == nil)

-- Vampiro sem sangue ao despertar entra em Torpor por inanição
local awkStarved = WM.awakenNightly({
    name = "[TESTE_E2E] Marcus Ventrue",
    isVampire = true,
    generation = 13,
    currentBlood = 0,
    virtude2_val = 4,
})
assert(awkStarved.ok == false and awkStarved.newState.currentBlood == 0 and awkStarved.hungerFrenzyRisk == true)
assert(awkStarved.warning == "Sem sangue ao despertar: personagem entra em Torpor por inanição!")

-- Sangue-Fraco 15ª geração pode usar o piso de sustento (4 pts) para despertar pagando apenas 1 pt (V20, p. 487)
local awkThin = WM.awakenNightly({
    name = "[TESTE_E2E] Lucas Sangue-Fraco 15",
    isVampire = true,
    generation = 15,
    currentBlood = 4,
    virtude2_val = 5,
})
assert(awkThin.ok == true and awkThin.newState.currentBlood == 3 and awkThin.hungerFrenzyRisk == false)

-- Mortal não gasta sangue nem tem risco de Frenesi de fome no despertar noturno
local awkMortal = WM.awakenNightly({
    name = "[TESTE_E2E] Roberto Mortal",
    isVampire = false,
    currentBlood = 0,
})
assert(awkMortal.ok == true and awkMortal.hungerFrenzyRisk == false and awkMortal.warning == nil)
assert(WM.awakenNightly(nil).ok == true)
assert(WM.prepareFrenzyCheck(nil, nil).difficulty == 6 and WM.prepareFrenzyCheck(nil, nil).pool == 1)
assert(WM.prepareRotschreckCheck(nil, nil).difficulty == 6 and WM.prepareRotschreckCheck(nil, nil).pool == 1)
assert(WM.prepareDegenerationCheck(nil).difficulty == 8 and WM.prepareDegenerationCheck(nil).virtueUsed == "Consciência")
