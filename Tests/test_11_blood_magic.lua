local V20 = require("Core.v20_init")
local BMCat = V20.BloodMagicCatalog
local BMEng = V20.BloodMagicEngine

assert(type(BMCat) == "table", "V20.BloodMagicCatalog deve estar registrado em Core.v20_init")
assert(type(BMEng) == "table", "V20.BloodMagicEngine deve estar registrado em Core.v20_init")

-- 0. PF2-2 item 3: atribuição idempotente em Core.v20_init mesmo com _G.V20 pré-existente
_G.V20 = { ExistingMarker = true }
package.loaded["Core.v20_init"] = nil
local V20Reloaded = require("Core.v20_init")
assert(V20Reloaded.ExistingMarker == true, "Core.v20_init deve preservar tabela V20 existente")
assert(V20Reloaded.BloodMagicCatalog == BMCat, "V20.BloodMagicCatalog deve ser atribuído idempotentemente")
assert(V20Reloaded.BloodMagicEngine == BMEng, "V20.BloodMagicEngine deve ser atribuído idempotentemente")
_G.V20 = V20
package.loaded["Core.v20_init"] = V20

-- 1. Catálogo completo: 6 linhas Taumaturgia (30 poderes), 3 linhas Necromancia (15 poderes) e 20 rituais
assert(#BMCat.THAUMATURGY_ORDER == 6, "Devem existir 6 linhas de Taumaturgia")
assert(#BMCat.NECROMANCY_ORDER == 3, "Devem existir 3 linhas de Necromancia")
assert(#BMCat.RITUAL_ORDER == 20, "Devem existir 20 rituais clássicos")

local seenPowerIds = {}
for _, pid in ipairs(BMCat.THAUMATURGY_ORDER) do
    local path = BMCat.THAUMATURGY_PATHS[pid]
    assert(path ~= nil and path.id == pid and type(path.name) == "string" and #path.powers == 5, "Linha Taumatúrgica inválida: " .. tostring(pid))
    for lvl = 1, 5 do
        local pw = path.powers[lvl]
        assert(pw.level == lvl, "Nível incorreto em " .. tostring(pw.id))
        assert(not seenPowerIds[pw.id], "ID de poder duplicado: " .. tostring(pw.id))
        seenPowerIds[pw.id] = true
        assert(pw.cost.blood == 1 and pw.cost.willpower == 0, "Taumaturgia padrão custa 1 Sangue")
        assert(pw.pool and pw.pool.attr == "attr_fdv_ref" and pw.pool.hab == nil, "Taumaturgia padrão rola FdV")
        assert(pw.defaultDiff == lvl + 3, "Dificuldade Taumatúrgica deve ser nível + 3")
        assert(type(pw.summary) == "string" and pw.summary:find("V20, p.") ~= nil, "Resumo deve citar página do V20: " .. tostring(pw.id))
    end
end

for _, pid in ipairs(BMCat.NECROMANCY_ORDER) do
    local path = BMCat.NECROMANCY_PATHS[pid]
    assert(path ~= nil and path.id == pid and type(path.name) == "string" and #path.powers == 5, "Linha Necromântica inválida: " .. tostring(pid))
    for lvl = 1, 5 do
        local pw = path.powers[lvl]
        assert(pw.level == lvl, "Nível incorreto em " .. tostring(pw.id))
        assert(not seenPowerIds[pw.id], "ID de poder duplicado: " .. tostring(pw.id))
        seenPowerIds[pw.id] = true
        assert(type(pw.pool) == "table" and type(pw.pool.attr) == "string", "Poder Necromântico deve ter pool válida: " .. tostring(pw.id))
        assert(type(pw.summary) == "string" and pw.summary:find("V20, p.") ~= nil, "Resumo deve citar página do V20: " .. tostring(pw.id))
    end
end

local thauRitCount, necroRitCount = 0, 0
for _, rid in ipairs(BMCat.RITUAL_ORDER) do
    local r = BMCat.RITUALS[rid]
    assert(r ~= nil and r.id == rid, "Ritual ausente: " .. tostring(rid))
    assert(r.level >= 1 and r.level <= 5, "Nível de ritual inválido: " .. tostring(rid))
    assert(r.defaultDiff == math.min(9, 3 + r.level), "Dificuldade padrão de ritual deve ser 3 + nível")
    assert(type(r.summary) == "string" and r.summary:find("V20, p.") ~= nil, "Resumo de ritual deve citar V20: " .. tostring(rid))
    if r.tradition == "thaumaturgy" then
        thauRitCount = thauRitCount + 1
    elseif r.tradition == "necromancy" then
        necroRitCount = necroRitCount + 1
    end
end
assert(thauRitCount == 10 and necroRitCount == 10, "Devem existir 10 rituais Taumatúrgicos e 10 Necromânticos")

-- 2. Regras V20 de Linha Primária vs Linha Secundária (p. 159 e p. 212)
assert(BMEng.derivePrimaryPathLevel(6) == 5)
assert(BMEng.derivePrimaryPathLevel(4) == 4)
assert(BMEng.derivePrimaryPathLevel(0) == 0)
assert(BMEng.derivePrimaryPathLevel(-2) == 0)
assert(BMEng.derivePrimaryPathLevel("3") == 3)
assert(BMEng.derivePrimaryPathLevel(nil) == 0)

assert(BMEng.validateSecondaryPathUpgrade({
    parentDiscDots = 1, primaryPathId = "path_of_blood", secondaryPathId = "lure_of_flames", targetLevel = 1
}).ok == false, "Primária precisa estar em >= 2 para iniciar Secundária")

assert(BMEng.validateSecondaryPathUpgrade({
    parentDiscDots = 2, primaryPathId = "path_of_blood", secondaryPathId = "lure_of_flames", targetLevel = 1
}).ok == true, "Primária em 2 permite iniciar Secundária em 1")

assert(BMEng.validateSecondaryPathUpgrade({
    parentDiscDots = 3, primaryPathId = "path_of_blood", secondaryPathId = "lure_of_flames", targetLevel = 3
}).ok == false, "Secundária não pode igualar Primária antes de Primária atingir 5")

assert(BMEng.validateSecondaryPathUpgrade({
    parentDiscDots = 4, primaryPathId = "path_of_blood", secondaryPathId = "lure_of_flames", targetLevel = 3
}).ok == true, "Primária em 4 permite Secundária em 3")

assert(BMEng.validateSecondaryPathUpgrade({
    parentDiscDots = 5, primaryPathId = "path_of_blood", secondaryPathId = "lure_of_flames", targetLevel = 5
}).ok == true, "Quando Primária está em 5, Secundária pode chegar a 5")

assert(BMEng.validateSecondaryPathUpgrade({
    parentDiscDots = 5, primaryPathId = "path_of_blood", secondaryPathId = "path_of_blood", targetLevel = 1
}).ok == false, "Secundária não pode duplicar a Linha Primária")

assert(BMEng.validateSecondaryPathUpgrade({
    parentDiscDots = 5, primaryPathId = "path_of_blood", secondaryPathId = "", targetLevel = 1
}).ok == false, "Secundária vazia deve ser rejeitada")

assert(BMEng.validateSecondaryPathUpgrade({
    parentDiscDots = 5, primaryPathId = "path_of_blood", secondaryPathId = "lure_of_flames", targetLevel = 6
}).ok == false, "Secundária não pode exceder nível 5")

-- 3. Ativação de poder de Linha de Taumaturgia e Necromancia
local st = {
    nome = "[TESTE_E2E] Tremere",
    isVampire = true,
    generation = 12,
    currentBlood = 8,
    spentThisTurn = 0,
    fdv_temp = 6,
}
local pRes = BMEng.activatePathPower(st, "thaumaturgy", "lure_of_flames", 3, 3, {})
assert(pRes.ok == true and pRes.newState.currentBlood == 7 and pRes.newState.spentThisTurn == 1)
assert(pRes.rollSpec.attr == "attr_fdv_ref" and pRes.rollSpec.hab == nil and pRes.rollSpec.defaultDiff == 6)
assert(st.currentBlood == 8 and st.spentThisTurn == 0, "activatePathPower não deve mutar o estado de entrada")

-- Necromancia (Linha dos Ossos 2: 1 Sangue + 1 FdV, Inteligência + Ocultismo dif 7)
local nRes = BMEng.activatePathPower(st, "necromancy", "bone_path", 2, 2, {})
assert(nRes.ok == true and nRes.newState.currentBlood == 7 and nRes.newState.fdv_temp == 5)
assert(nRes.rollSpec.attr == "attr_inteligencia" and nRes.rollSpec.hab == "hab_ocultismo" and nRes.rollSpec.defaultDiff == 7)

-- Rollback atômico quando há sangue suficiente mas falta FdV
local stNoWP = {
    nome = "[TESTE_E2E] Giovanni Sem FdV",
    isVampire = true,
    generation = 12,
    currentBlood = 8,
    spentThisTurn = 0,
    fdv_temp = 0,
}
local nFailWP = BMEng.activatePathPower(stNoWP, "necromancy", "bone_path", 2, 2, {})
assert(nFailWP.ok == false and nFailWP.newState.currentBlood == 8 and nFailWP.newState.fdv_temp == 0, "Falha de FdV não deve descontar sangue")

-- Nível insuficiente e linha inválida
assert(BMEng.activatePathPower(st, "thaumaturgy", "lure_of_flames", 2, 3, {}).ok == false)
assert(BMEng.activatePathPower(st, "thaumaturgy", "linha_inexistente", 5, 1, {}).ok == false)

-- PF2-2 item 2: normalização estrita de storytellerOverride (string NDB "false" / 0 / "0" jamais atua como truthy)
local stExhausted = {
    nome = "[TESTE_E2E] Tremere Exausto",
    isVampire = true,
    generation = 12,
    currentBlood = 0,
    spentThisTurn = 1,
    fdv_temp = 0,
    storytellerOverride = "false",
}
assert(BMEng.activatePathPower(stExhausted, "necromancy", "bone_path", 1, 2, { storytellerOverride = "false" }).ok == false)
assert(BMEng.activatePathPower(stExhausted, "necromancy", "bone_path", 2, 2, { storytellerOverride = "false" }).ok == false)
assert(BMEng.activatePathPower(stExhausted, "necromancy", "bone_path", 2, 2, { storytellerOverride = 0 }).ok == false)
assert(BMEng.activatePathPower(stExhausted, "necromancy", "bone_path", 2, 2, { storytellerOverride = "0" }).ok == false)
assert(BMEng.activatePathPower(stNoWP, "necromancy", "bone_path", 2, 2, { storytellerOverride = "false" }).ok == false)

local pOverrideOk = BMEng.activatePathPower(stExhausted, "necromancy", "bone_path", 1, 2, { storytellerOverride = true })
assert(pOverrideOk.ok == true and pOverrideOk.newState.currentBlood == 0 and pOverrideOk.newState.fdv_temp == 0)
local pOverrideStrTrue = BMEng.activatePathPower(stExhausted, "necromancy", "bone_path", 1, 2, { storytellerOverride = "true" })
assert(pOverrideStrTrue.ok == true)

-- 4. Conjuração de Ritual Taumatúrgico e Necromântico + Ritual Customizado
local rFail = BMEng.castRitual(st, "thau_rit_4_heart_stone", 3, {})
assert(rFail.ok == false)
local rOk = BMEng.castRitual(st, "thau_rit_4_heart_stone", 4, {})
assert(rOk.ok == true and rOk.rollSpec.attr == "attr_inteligencia" and rOk.rollSpec.hab == "hab_ocultismo" and rOk.rollSpec.defaultDiff == 7)

-- Exílio Sombrio (Nv 5 Necromancia: 2 Sangue + 1 FdV, ignora limite por turno de 1 sangue da 12ª geração)
local rExile = BMEng.castRitual(st, "necro_rit_5_dark_exile", 5, {})
assert(rExile.ok == true and rExile.newState.currentBlood == 6 and rExile.newState.fdv_temp == 5 and rExile.rollSpec.defaultDiff == 8)

-- PF2-2 item 2 em castRitual
assert(BMEng.castRitual(stExhausted, "necro_rit_5_dark_exile", 3, { storytellerOverride = "false" }).ok == false)
assert(BMEng.castRitual(stExhausted, "necro_rit_5_dark_exile", 5, { storytellerOverride = "false" }).ok == false)
assert(BMEng.castRitual(stNoWP, "necro_rit_5_dark_exile", 5, { storytellerOverride = "false" }).ok == false)
assert(BMEng.castRitual(stExhausted, "necro_rit_5_dark_exile", 3, { storytellerOverride = "1" }).ok == true)

-- Ritual customizado estruturado e ritual inexistente
local rCustom = BMEng.castRitual(st, {
    name = "[TESTE_E2E] Círculo Hermético",
    tradition = "thaumaturgy",
    level = 2,
    cost = { blood = 1, willpower = 0 },
    summary = "Ritual experimental de teste.",
}, 2, {})
assert(rCustom.ok == true and rCustom.newState.currentBlood == 7 and rCustom.rollSpec.defaultDiff == 5)
assert(BMEng.castRitual(st, "ritual_inexistente", 5, {}).ok == false)

-- 5. Visibilidade dinâmica da aba Magia do Sangue (incluindo PF2-2 item 1: d.selected == true / "true")
assert(BMEng.hasBloodMagicAccess("tremere", {}, 0) == true)
assert(BMEng.hasBloodMagicAccess("giovanni", {}, 0) == true)
assert(BMEng.hasBloodMagicAccess("brujah", {}, 0) == false)
assert(BMEng.hasBloodMagicAccess("brujah", { { disc_id = "thaumaturgy", nivel = 1 } }, 0) == true)
assert(BMEng.hasBloodMagicAccess("caitiff", { { disc_id = "necromancy", nivel = 1 } }, 0) == true)
assert(BMEng.hasBloodMagicAccess("toreador", {}, 1) == true)

-- PF2-2 item 1: selecionar Taumaturgia/Necromancia na criação já revela Aba 8 mesmo com nivel = 0
assert(BMEng.hasBloodMagicAccess("brujah", { { disc_id = "thaumaturgy", nivel = 0, selected = true } }, 0) == true)
assert(BMEng.hasBloodMagicAccess("caitiff", { { disc_id = "necromancy", nivel = 0, selected = "true" } }, 0) == true)
assert(BMEng.hasBloodMagicAccess("brujah", { { disc_id = "thaumaturgy", nivel = 0, selected = false } }, 0) == false)
assert(BMEng.hasBloodMagicAccess("brujah", { { disc_id = "thaumaturgy", nivel = 0, selected = "false" } }, 0) == false)
assert(BMEng.hasBloodMagicAccess("brujah", { { disc_id = "thaumaturgy", nivel = 0 } }, 0) == false)
assert(BMEng.hasBloodMagicAccess("brujah", { { disc_id = "potence", nivel = 0, selected = true } }, 0) == false)

-- 6. Segurança contra nil nas funções públicas
assert(BMEng.getPathTable(nil, nil) == nil)
assert(BMEng.validateSecondaryPathUpgrade(nil).ok == false)
assert(BMEng.activatePathPower(nil, nil, nil, nil, nil, nil).ok == false)
assert(BMEng.castRitual(nil, nil, nil, nil).ok == false)
assert(BMEng.hasBloodMagicAccess(nil, nil, nil) == false)
