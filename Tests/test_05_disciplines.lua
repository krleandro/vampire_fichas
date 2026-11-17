local Catalog = require("Data.disciplines_catalog")
local Engine = require("Core.disciplines_engine")
local Clans = require("Data.clans")
local Traits = require("Data.attributes_abilities")

-- 1. Todas as 17 disciplinas clássicas cadastradas com 5 poderes cada (85 poderes oficiais)
local expectedOrder = {
    "animalism", "auspex", "celerity", "chimerstry", "dementation", "dominate",
    "fortitude", "necromancy", "obfuscate", "obtenebration", "potence", "presence",
    "protean", "quietus", "serpentis", "thaumaturgy", "vicissitude",
}
assert(#Catalog.ORDER == 17, "Esperado 17 disciplinas em Catalog.ORDER")

local specialAttrs = { attr_fdv_ref = true }
local specialHabs = { hab_autocontrole_ref = true, hab_coragem_ref = true }
local seenPowerIds = {}
local totalPowers = 0

for idx, id in ipairs(Catalog.ORDER) do
    assert(id == expectedOrder[idx], "Ordem incorreta em Catalog.ORDER[" .. idx .. "]: " .. tostring(id))
    local d = Catalog.DISCIPLINES[id]
    assert(d ~= nil and #d.powers == 5, "Disciplina inválida ou sem 5 poderes: " .. tostring(id))
    assert(d.id == id, "d.id divergente em " .. id)
    assert(type(d.name) == "string" and #d.name > 0, "Nome pt-BR ausente em " .. id)
    assert(type(d.hasPaths) == "boolean", "hasPaths deve ser boolean em " .. id)
    if id == "necromancy" or id == "thaumaturgy" then
        assert(d.hasPaths == true, id .. " deve ter hasPaths == true")
    else
        assert(d.hasPaths == false, id .. " deve ter hasPaths == false")
    end

    for lvl = 1, 5 do
        local pw = d.powers[lvl]
        assert(type(pw) == "table", "Poder ausente em " .. id .. " nível " .. lvl)
        assert(pw.level == lvl, "Nível incorreto em " .. tostring(pw.id))
        assert(type(pw.id) == "string" and #pw.id > 0, "id ausente no poder")
        assert(not seenPowerIds[pw.id], "id de poder duplicado: " .. pw.id)
        seenPowerIds[pw.id] = true
        assert(type(pw.name) == "string" and #pw.name > 0, "Nome ausente em " .. pw.id)
        assert(type(pw.cost) == "table", "cost ausente em " .. pw.id)
        assert(type(pw.cost.blood) == "number" and pw.cost.blood >= 0, "cost.blood inválido em " .. pw.id)
        assert(type(pw.cost.willpower) == "number" and pw.cost.willpower >= 0, "cost.willpower inválido em " .. pw.id)
        assert(type(pw.defaultDiff) == "number" and pw.defaultDiff >= 2 and pw.defaultDiff <= 10, "defaultDiff inválida em " .. pw.id)
        assert(type(pw.diffHint) == "string" and #pw.diffHint > 0, "diffHint ausente em " .. pw.id)
        assert(type(pw.summary) == "string" and pw.summary:find("V20, p%.") ~= nil, "summary sem citação V20 em " .. pw.id)
        if pw.pool ~= nil then
            assert(Traits.ATTRIBUTES[pw.pool.attr] ~= nil or specialAttrs[pw.pool.attr] == true, "attr inválido em " .. pw.id .. ": " .. tostring(pw.pool.attr))
            if pw.pool.hab ~= nil then
                assert(Traits.ABILITIES[pw.pool.hab] ~= nil or specialHabs[pw.pool.hab] == true, "hab inválida em " .. pw.id .. ": " .. tostring(pw.pool.hab))
            end
        end
        totalPowers = totalPowers + 1
    end
end
assert(totalPowers == 85, "Esperado exatamente 85 poderes oficiais nas 17 disciplinas V20")

-- Todas as disciplinas de clã referenciadas em Data/clans.lua existem no catálogo
for cid, clan in pairs(Clans.CLANS) do
    for _, did in ipairs(clan.disciplines) do
        assert(Catalog.DISCIPLINES[did] ~= nil, "Disciplina de clã inexistente no catálogo (" .. cid .. " -> " .. tostring(did) .. ")")
    end
end

-- 2. Classificação automática de custo: Brujah comprando Dominação = fora_cla; com Qualidade = cla; Caitiff = caitiff
assert(Engine.classifyCostCategory("brujah", "potence", false) == "cla")
assert(Engine.classifyCostCategory("brujah", "celerity", false) == "cla")
assert(Engine.classifyCostCategory("brujah", "presence", false) == "cla")
assert(Engine.classifyCostCategory("brujah", "dominate", false) == "fora_cla")
assert(Engine.classifyCostCategory("brujah", "dominate", true) == "cla")
assert(Engine.classifyCostCategory("caitiff", "dominate", false) == "caitiff")
assert(Engine.classifyCostCategory("caitiff", "potence", true) == "caitiff")
assert(Engine.classifyCostCategory("tremere", "thaumaturgy", false) == "cla")
assert(Engine.classifyCostCategory("lasombra", "obtenebration", false) == "cla")
assert(Engine.classifyCostCategory("tzimisce", "vicissitude", false) == "cla")
assert(Engine.classifyCostCategory("giovanni", "necromancy", false) == "cla")
assert(Engine.classifyCostCategory("unknown_clan", "potence", false) == "fora_cla")

-- 2b. Desbloqueio ordenado de poderes (1..dots) + poderes customizados (trilhas secundárias / combinadas)
assert(#Engine.getUnlockedPowers("obtenebration", 0) == 0)
assert(#Engine.getUnlockedPowers("obtenebration", nil) == 0)
assert(#Engine.getUnlockedPowers("obtenebration", 0 / 0) == 0)
local unlocked3 = Engine.getUnlockedPowers("obtenebration", 3)
assert(#unlocked3 == 3 and unlocked3[1].id == "obt_1" and unlocked3[2].id == "obt_2" and unlocked3[3].id == "obt_3")

local unlockedCustom = Engine.getUnlockedPowers("thaumaturgy", 3, {
    { id = "lure_flames_4", level = 4, name = "Chamas Nível 4" },
    { id = "lure_flames_2", level = 2, name = "Palma de Chamas" },
    { id = "lure_flames_1", level = 1, name = "Vela Mental" },
})
assert(#unlockedCustom == 5, "3 da linha primária + 2 customizados <= nível 3")
for i = 2, #unlockedCustom do
    assert(unlockedCustom[i].level >= unlockedCustom[i - 1].level, "getUnlockedPowers deve retornar lista ordenada por nível")
end

-- 3. Brujah usando poder fora do clã (Tenebrosidade 3 - Braços do Abismo): desconta sangue e retorna parada Manipulação + Ocultismo dif 7
local st = {
    nome = "[TESTE_E2E] Jack Brujah",
    isVampire = true,
    generation = 12,
    currentBlood = 8,
    spentThisTurn = 0,
    fdv_temp = 5,
    attr_manipulacao = 3,
    hab_ocultismo = 2,
    activeBuffs = {},
}
local power = Catalog.DISCIPLINES.obtenebration.powers[3]
local act = Engine.activatePower(st, { disc_id = "obtenebration", nivel = 3 }, power, {})
assert(act.ok == true)
assert(act.newState.currentBlood == 7, "Braços do Abismo deve descontar 1 ponto de sangue")
assert(act.newState.spentThisTurn == 1)
assert(st.currentBlood == 8 and st.spentThisTurn == 0, "activatePower não deve mutar estado original")
assert(act.rollSpec.attr == "attr_manipulacao" and act.rollSpec.hab == "hab_ocultismo" and act.rollSpec.defaultDiff == 7)
assert(act.rollSpec.powerName == "Braços do Abismo")

-- Bloqueio por nível insuficiente (e permissão via storytellerOverride)
local powerLv4 = Catalog.DISCIPLINES.obtenebration.powers[4]
local lowLvl = Engine.activatePower(st, { disc_id = "obtenebration", nivel = 3 }, powerLv4, {})
assert(lowLvl.ok == false and lowLvl.newState.currentBlood == 8)
local overrideLvl = Engine.activatePower(st, { disc_id = "obtenebration", nivel = 3 }, powerLv4, { storytellerOverride = true })
assert(overrideLvl.ok == true and overrideLvl.newState.currentBlood == 6)

-- Custo de Força de Vontade + atomicidade em custo misto (Sangue + FdV) + não vazar storytellerOverride
local serpSkin = Catalog.DISCIPLINES.serpentis.powers[3] -- 1 Sangue + 1 FdV
local stNoWP = {
    nome = "[TESTE_E2E] Kemintiri Setita",
    isVampire = true,
    generation = 10,
    currentBlood = 6,
    spentThisTurn = 0,
    fdv_temp = 0,
    activeBuffs = {},
}
local failMixed = Engine.activatePower(stNoWP, { disc_id = "serpentis", nivel = 3 }, serpSkin, {})
assert(failMixed.ok == false and failMixed.newState.currentBlood == 6 and failMixed.newState.fdv_temp == 0, "Falha de FdV não deve descontar sangue")

local okMixedOverride = Engine.activatePower(stNoWP, { disc_id = "serpentis", nivel = 3 }, serpSkin, { storytellerOverride = true })
assert(okMixedOverride.ok == true and okMixedOverride.newState.currentBlood == 5 and okMixedOverride.newState.storytellerOverride == nil)
assert(okMixedOverride.buffToggled.id == "serp_skin" and okMixedOverride.buffToggled.active == true)

-- Taumaturgia (V20, p. 212): todos os poderes da Linha do Sangue (thau_1..thau_5) gastam 1 Sangue (0 FdV) e rolam FdV (dif = nível + 3)
for lvl = 1, 5 do
    local tpw = Catalog.DISCIPLINES.thaumaturgy.powers[lvl]
    assert(tpw.cost.blood == 1 and tpw.cost.willpower == 0, "Taumaturgia nível " .. lvl .. " deve custar 1 Sangue e 0 FdV (V20, p. 212)")
    assert(tpw.defaultDiff == lvl + 3, "Taumaturgia nível " .. lvl .. " deve ter dif = nível + 3")
end
local stTremere = {
    nome = "[TESTE_E2E] Strauss Tremere",
    isVampire = true,
    generation = 10,
    currentBlood = 9,
    spentThisTurn = 0,
    fdv_temp = 7,
    activeBuffs = {},
}
local actThau1 = Engine.activatePower(stTremere, { disc_id = "thaumaturgy", nivel = 5 }, Catalog.DISCIPLINES.thaumaturgy.powers[1], {})
assert(actThau1.ok == true)
assert(actThau1.newState.currentBlood == 8, "thau_1 deve descontar 1 ponto de sangue")
assert(actThau1.newState.fdv_temp == 7, "thau_1 não deve descontar Força de Vontade temporária")
assert(actThau1.rollSpec.attr == "attr_fdv_ref" and actThau1.rollSpec.hab == nil and actThau1.rollSpec.defaultDiff == 4)

local stTremereTurn2 = Engine.clearTurnEffects(actThau1.newState)
local actThau5 = Engine.activatePower(stTremereTurn2, { disc_id = "thaumaturgy", nivel = 5 }, Catalog.DISCIPLINES.thaumaturgy.powers[5], {})
assert(actThau5.ok == true and actThau5.newState.currentBlood == 7 and actThau5.newState.fdv_temp == 7)
assert(actThau5.rollSpec.attr == "attr_fdv_ref" and actThau5.rollSpec.defaultDiff == 8)

-- 4. Modificadores de Potência ativa (sucessos automáticos), Rapidez ativa (ações extras ignorando limite/turno) e Fortitude
local st2 = {
    nome = "[TESTE_E2E] Elena Toreador",
    isVampire = true,
    generation = 13,
    currentBlood = 8,
    spentThisTurn = 1,
    fdv_temp = 5,
    activeBuffs = {},
}
local celRes = Engine.activateCelerityActions(st2, 2)
assert(celRes.ok == true and celRes.newState.currentBlood == 6 and celRes.newState.activeCelerityActions == 2)
assert(st2.currentBlood == 8 and st2.activeCelerityActions == nil, "activateCelerityActions não deve mutar estado original")

local mods = Engine.computeCombatModifiers(celRes.newState, {
    { disc_id = "potence", nivel = 3, activeAuto = true },
    { disc_id = "celerity", nivel = 2 },
    { disc_id = "fortitude", nivel = 2 },
})
assert(mods.activePotenceAuto == 3 and mods.passivePotenceDice == 0)
assert(mods.activeCelerityActions == 2 and mods.passiveCelerityDice == 0)
assert(mods.fortitudeSoak == 2)

-- Rapidez parcial: Rapidez 3 com 2 ações extras deixa +1 dado passivo de Destreza
local modsPartialCel = Engine.computeCombatModifiers(celRes.newState, {
    { disc_id = "celerity", nivel = 3 },
})
assert(modsPartialCel.activeCelerityActions == 2 and modsPartialCel.passiveCelerityDice == 1)

-- 5. Ativação explícita de Potência automática via 1 ponto de sangue (respeitando limite/turno da geração)
local stPot = {
    nome = "[TESTE_E2E] Theo Bell Brujah",
    isVampire = true,
    generation = 13,
    currentBlood = 8,
    spentThisTurn = 0,
    fdv_temp = 5,
    activeBuffs = {},
}
-- Modo passivo padrão (0 sangue)
local passiveMods = Engine.computeCombatModifiers(stPot, { { disc_id = "potence", nivel = 4 } })
assert(passiveMods.passivePotenceDice == 4 and passiveMods.activePotenceAuto == 0)

-- Ativação via Engine.activatePotenceAuto gasta 1 de sangue e converte Potência em sucessos automáticos
local potAutoRes = Engine.activatePotenceAuto(stPot)
assert(potAutoRes.ok == true and potAutoRes.newState.currentBlood == 7 and potAutoRes.newState.spentThisTurn == 1 and potAutoRes.newState.activePotenceAuto == true)
local activePotMods = Engine.computeCombatModifiers(potAutoRes.newState, { { disc_id = "potence", nivel = 4 } })
assert(activePotMods.activePotenceAuto == 4 and activePotMods.passivePotenceDice == 0)

-- Se já gastou 1 de sangue no turno (13ª geração, limite 1/turno), Potência ativa bloqueia (diferente de Rapidez!)
local stTurnFull = {
    nome = "[TESTE_E2E] Jack Brujah",
    isVampire = true,
    generation = 13,
    currentBlood = 8,
    spentThisTurn = 1,
    activeBuffs = {},
}
local potBlocked = Engine.activatePotenceAuto(stTurnFull)
assert(potBlocked.ok == false and potBlocked.newState.currentBlood == 8)

-- Ativação de Potência via Engine.activatePower também funciona limpamente (liga por 1 Sangue, desliga sem custo)
local potViaPower = Engine.activatePower(stPot, { disc_id = "potence", nivel = 3 }, Catalog.DISCIPLINES.potence.powers[3], {})
assert(potViaPower.ok == true and potViaPower.newState.currentBlood == 7 and potViaPower.newState.activePotenceAuto == true)
local potOffViaPower = Engine.activatePower(potViaPower.newState, { disc_id = "potence", nivel = 3 }, Catalog.DISCIPLINES.potence.powers[3], {})
assert(potOffViaPower.ok == true and potOffViaPower.newState.currentBlood == 7 and potOffViaPower.newState.activePotenceAuto == false)

-- 6. Toggle Buffs de cena (Forma Zulo, Sentidos Aguçados, Forma da Besta, Pele da Víbora) e desativação sem recobrar custo
local stZulo = {
    nome = "[TESTE_E2E] Dragos Tzimisce",
    isVampire = true,
    generation = 8, -- 8ª geração permite até 3 pontos de sangue por turno
    currentBlood = 10,
    spentThisTurn = 0,
    fdv_temp = 6,
    activeBuffs = {},
}
local zuloPower = Catalog.DISCIPLINES.vicissitude.powers[4]
local zuloOn = Engine.activatePower(stZulo, { disc_id = "vicissitude", nivel = 4 }, zuloPower, {})
assert(zuloOn.ok == true and zuloOn.newState.currentBlood == 8 and zuloOn.buffToggled.active == true)

local auspexOn = Engine.activatePower(zuloOn.newState, { disc_id = "auspex", nivel = 3 }, Catalog.DISCIPLINES.auspex.powers[1], {})
local beastOn = Engine.activatePower(auspexOn.newState, { disc_id = "protean", nivel = 4 }, Catalog.DISCIPLINES.protean.powers[4], {})
assert(beastOn.ok == true and beastOn.newState.currentBlood == 7)

local sceneMods = Engine.computeCombatModifiers(beastOn.newState, {
    { disc_id = "vicissitude", nivel = 4 },
    { disc_id = "auspex", nivel = 3 },
    { disc_id = "protean", nivel = 4 },
})
assert(sceneMods.sceneAttrMods.forca == 3 and sceneMods.sceneAttrMods.destreza == 3 and sceneMods.sceneAttrMods.vigor == 3)
assert(sceneMods.perceptionDiffMod == -5, "Auspícios 3 (-3) + Forma da Besta (-2) = -5 na dif de Percepção")

local skinMods = Engine.computeCombatModifiers(okMixedOverride.newState, { { disc_id = "serpentis", nivel = 3 } })
assert(skinMods.soakDiffOverride == 5)

-- Desativar Forma Zulo não cobra mais 2 de sangue
local zuloOff = Engine.activatePower(beastOn.newState, { disc_id = "vicissitude", nivel = 4 }, zuloPower, {})
assert(zuloOff.ok == true and zuloOff.newState.currentBlood == 7 and zuloOff.buffToggled.active == false)
local afterOffMods = Engine.computeCombatModifiers(zuloOff.newState, { { disc_id = "vicissitude", nivel = 4 } })
assert(afterOffMods.sceneAttrMods.forca == 0)

-- 7. Rapidez via activatePower (string ID, ignora limite/turno, respeita teto de nível), Sangue-Fraco 15ª (custo dobrado), Carniçal e limpeza de turno/cena
local celViaP1 = Engine.activatePower(stTurnFull, { disc_id = "celerity", nivel = 2 }, "cel_1", {})
assert(celViaP1.ok == true and celViaP1.newState.currentBlood == 7 and celViaP1.newState.activeCelerityActions == 1)
local celViaP2 = Engine.activatePower(celViaP1.newState, { disc_id = "celerity", nivel = 2 }, "cel_2", {})
assert(celViaP2.ok == true and celViaP2.newState.currentBlood == 6 and celViaP2.newState.activeCelerityActions == 2)
local celViaP3 = Engine.activatePower(celViaP2.newState, { disc_id = "celerity", nivel = 2 }, "cel_2", {})
assert(celViaP3.ok == false and celViaP3.newState.currentBlood == 6, "Não deve exceder ações extras além do nível de Rapidez")

local stThin15 = {
    nome = "[TESTE_E2E] Lucas Sangue-Fraco 15",
    isVampire = true,
    generation = 15, -- doubleCost = true (1 -> 2 pontos de sangue), perTurn = 1, exige bypassTurnLimit p/ custo 2
    currentBlood = 10,
    spentThisTurn = 0,
    activeBuffs = {},
}
local thinCel = Engine.activateCelerityActions(stThin15, 1)
assert(thinCel.ok == true and thinCel.newState.currentBlood == 8, "15ª geração deve pagar 2 de sangue para 1 ação de Rapidez")

local ghoulMods = Engine.computeCombatModifiers({ nome = "[TESTE_E2E] Renfield Carnical", isGhoul = true, ghoulPotence = 1 }, {})
assert(ghoulMods.passivePotenceDice == 1 and ghoulMods.activePotenceAuto == 0)

local resetTurn = Engine.clearTurnEffects(potViaPower.newState)
assert(resetTurn.activePotenceAuto == false and resetTurn.activeCelerityActions == 0 and resetTurn.spentThisTurn == 0)
local resetScene = Engine.clearSceneBuffs(beastOn.newState)
assert(next(resetScene.activeBuffs) == nil and resetScene.activeCelerityActions == 0 and resetScene.activePotenceAuto == false)

-- Segurança contra nil/entradas inválidas
assert(Engine.activatePower(nil, nil, nil, nil).ok == false)
assert(Engine.activateCelerityActions(nil, 1).ok == false)
assert(Engine.activatePotenceAuto(nil).ok == false)
local emptyMods = Engine.computeCombatModifiers(nil, nil)
assert(emptyMods.passivePotenceDice == 0 and emptyMods.fortitudeSoak == 0 and emptyMods.perceptionDiffMod == 0)
