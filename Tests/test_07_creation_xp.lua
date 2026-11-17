local V20 = require("Core.v20_init")

-- 0. Bundle idempotente Core.v20_init (15 módulos Data/ e Core/)
assert(type(V20) == "table" and _G.V20 == V20, "V20 global deve ser inicializado e retornado")
local expectedModules = {
    "Traits", "Generations", "Clans", "MoralityCatalog",
    "DisciplinesCatalog", "BackgroundsCatalog", "MeritsFlawsCatalog",
    "Dice", "Blood", "Health", "WillpowerMorality",
    "DisciplinesEngine", "BackgroundsEngine", "Creation", "Experience",
}
for _, key in ipairs(expectedModules) do
    assert(type(V20[key]) == "table", "Módulo ausente em V20: " .. key)
end
package.loaded["Core.v20_init"] = nil
local V20Reloaded = require("Core.v20_init")
assert(rawequal(V20, V20Reloaded), "Core.v20_init deve ser idempotente ao recarregar")

-- 1. Custos oficiais de XP V20 (incluindo Caitiff x6, Nova Disciplina 10, Nova Habilidade 3, Fora do Clã x7, Clã x5)
assert(V20.Experience.calculateUpgradeCost("ability", 0, {}) == 3)
assert(V20.Experience.calculateUpgradeCost("ability", 2, {}) == 4)
assert(V20.Experience.calculateUpgradeCost("attribute", 3, {}) == 12)
assert(V20.Experience.calculateUpgradeCost("discipline", 0, { costCategory = "fora_cla" }) == 10)
assert(V20.Experience.calculateUpgradeCost("discipline", 0, { costCategory = "cla" }) == 10)
assert(V20.Experience.calculateUpgradeCost("discipline", 0, { costCategory = "caitiff" }) == 10)
assert(V20.Experience.calculateUpgradeCost("discipline", 2, { costCategory = "cla" }) == 10)
assert(V20.Experience.calculateUpgradeCost("discipline", 2, { costCategory = "fora_cla" }) == 14)
assert(V20.Experience.calculateUpgradeCost("discipline", 2, { costCategory = "caitiff" }) == 12)
assert(V20.Experience.calculateUpgradeCost("discipline", 3) == 21, "Omissão de opts deve assumir fora_cla (x7)")
assert(V20.Experience.calculateUpgradeCost("secondary_path", 0, {}) == 7)
assert(V20.Experience.calculateUpgradeCost("secondary_path", 3, {}) == 12)
assert(V20.Experience.calculateUpgradeCost("virtue", 3, {}) == 6)
assert(V20.Experience.calculateUpgradeCost("morality", 6, {}) == 12)
assert(V20.Experience.calculateUpgradeCost("willpower", 5, {}) == 5)
assert(V20.Experience.calculateUpgradeCost("willpower", 0, {}) == 1)
assert(V20.Experience.calculateUpgradeCost("ability", "2", {}) == 4, "Deve aceitar números em string vindos do NDB")
assert(V20.Experience.calculateUpgradeCost("unknown_kind", 3, {}) == 0)
assert(V20.Experience.calculateUpgradeCost("ability", 0 / 0, nil) == 3, "NaN deve ser tratado com segurança como 0")

-- 2. Validação de criação Vampiro Neófito (7/5/3, 13/9/5, 15 Bônus + Defeitos até +7)
local validVamp = {
    nome = "[TESTE_E2E] Jack Brujah",
    profile = "vampire_neonate",
    cla_id = "brujah",
    attrGroups = { 5, 7, 3 },     -- permutação válida de 7/5/3
    abilityGroups = { 9, 13, 5 }, -- permutação válida de 13/9/5
    maxBaseAbility = 3,
    baseDisciplines = 3,
    baseBackgrounds = 5,
    baseVirtues = 7,
    flawsBonus = 4, -- 15 + 4 = 19 bônus disponíveis
    freebiePurchases = {
        attributes = 1,  -- 5
        abilities = 2,   -- 4
        disciplines = 1, -- 7
        willpower = 3,   -- 3 -> total = 19
    },
}
local cv = V20.Creation.validate(validVamp)
assert(cv.valid == true and cv.freebiesAvailable == 19 and cv.freebiesSpent == 19 and cv.freebiesRemaining == 0)

-- Teto de +7 de defeitos na criação (flawsBonus = 10 -> apenas +7 contam => 22 disponíveis)
validVamp.flawsBonus = 10
local cvFlawCap = V20.Creation.validate(validVamp)
assert(cvFlawCap.valid == true and cvFlawCap.freebiesAvailable == 22 and cvFlawCap.freebiesRemaining == 3)

-- Estouro de Pontos de Bônus (23 gastos > 22 disponíveis)
validVamp.freebiePurchases.backgrounds = 4 -- +4 => 23 gastos
assert(V20.Creation.validate(validVamp).valid == false)
validVamp.freebiePurchases.backgrounds = 0
validVamp.flawsBonus = 4

-- Tentativa de compra negativa em freebiePurchases deve ser bloqueada
validVamp.freebiePurchases.merits = -5
assert(V20.Creation.validate(validVamp).valid == false)
validVamp.freebiePurchases.merits = 0

-- Habilidade base > 3 antes de bônus deve invalidar criação
validVamp.maxBaseAbility = 4
local cvHabCap = V20.Creation.validate(validVamp)
assert(cvHabCap.valid == false and #cvHabCap.errors >= 1)
validVamp.maxBaseAbility = 3

-- Guarda obrigatória Nosferatu: Aparência deve ser 0
local nosf = {
    nome = "[TESTE_E2E] Zelios Nosferatu",
    profile = "vampire_neonate",
    cla_id = "nosferatu",
    attr_aparencia = 0,
    attrGroups = { 7, 5, 3 },
    abilityGroups = { 13, 9, 5 },
    maxBaseAbility = 3,
    baseDisciplines = 3,
    baseBackgrounds = 5,
    baseVirtues = 7,
}
assert(V20.Creation.validate(nosf).valid == true)
nosf.attr_aparencia = 1
local cvNosfFail = V20.Creation.validate(nosf)
assert(cvNosfFail.valid == false, "Nosferatu com Aparência ~= 0 deve invalidar criação")

-- Perfis Mortais (Padrão 6/4/3 + 11/7/4 + 21 Bônus; Heroico 7/5/3 + 13/9/5 + 15 Bônus; 0 Disciplinas)
local mortalStd = {
    nome = "[TESTE_E2E] Helena Mortal",
    profile = "mortal_standard_643",
    attrGroups = { 6, 4, 3 },
    abilityGroups = { 11, 7, 4 },
    maxBaseAbility = 3,
    baseDisciplines = 0,
    baseBackgrounds = 5,
    baseVirtues = 7,
    freebiePurchases = {
        attributes = 2,  -- 10
        abilities = 3,   -- 6
        virtues = 1,     -- 2
        morality = 1,    -- 1
        merits = 2,      -- 2 -> total = 21
    },
}
local cvMortalStd = V20.Creation.validate(mortalStd)
assert(cvMortalStd.valid == true and cvMortalStd.freebiesAvailable == 21 and cvMortalStd.freebiesRemaining == 0)

mortalStd.baseDisciplines = 1
assert(V20.Creation.validate(mortalStd).valid == false, "Mortal não possui pontos iniciais de Disciplina")

local mortalHeroic = {
    nome = "[TESTE_E2E] Viktor Caçador",
    profile = "mortal_heroic_753",
    attrGroups = { 7, 5, 3 },
    abilityGroups = { 13, 9, 5 },
    maxBaseAbility = 3,
    baseDisciplines = 0,
    baseBackgrounds = 5,
    baseVirtues = 7,
}
local cvMortalHeroic = V20.Creation.validate(mortalHeroic)
assert(cvMortalHeroic.valid == true and cvMortalHeroic.freebiesAvailable == 15 and cvMortalHeroic.freebiesRemaining == 15)

-- Resiliência contra entrada nil / malformada
local cvEmpty = V20.Creation.validate(nil)
assert(cvEmpty.valid == false and type(cvEmpty.errors) == "table" and #cvEmpty.errors > 0)

-- 3. Fluxo de XP com aprovação do Narrador vs compra direta, recusa e proteção contra gasto duplo
local ch = { nome = "[TESTE_E2E] Jack Brujah", xp_total = 20, xp_gasto = 0, xp_exige_aprovacao = true, attr_forca = 3 }
local sub = V20.Experience.submitUpgrade(ch, {
    traitKind = "attribute", field = "attr_forca", currentRating = 3, label = "Força 3 -> 4", author = "tester_e2e"
}, { isMestre = false })
assert(sub.ok == true and sub.auditEntry.status == "pendente" and sub.newState.attr_forca == 3 and sub.newState.xp_gasto == 0)
assert(ch.attr_forca == 3 and ch.xp_gasto == 0, "submitUpgrade não deve mutar estado original")

-- Segundo pedido concorrente de 12 XP (ainda cabe nos 20 XP antes da 1ª aprovação, mas falhará na 2ª aprovação)
local sub2 = V20.Experience.submitUpgrade(sub.newState, {
    traitKind = "attribute", field = "attr_destreza", currentRating = 3, label = "Destreza 3 -> 4", author = "tester_e2e"
}, { isMestre = false })
assert(sub2.ok == true and sub2.auditEntry.status == "pendente")

local app = V20.Experience.resolvePending(sub.newState, sub.auditEntry, true, "NarradorMestre")
assert(app.ok == true and app.updatedEntry.status == "aprovado" and app.updatedEntry.aprovador_login == "NarradorMestre")
assert(app.newState.attr_forca == 4 and app.newState.xp_gasto == 12)

-- Reprocessar entrada já aprovada deve falhar
local appDup = V20.Experience.resolvePending(app.newState, app.updatedEntry, true, "NarradorMestre")
assert(appDup.ok == false)

-- Aprovar o 2º pedido sem saldo restante suficiente (custo 12 > saldo 8) deve falhar sem cobrar XP
local appNoFunds = V20.Experience.resolvePending(app.newState, sub2.auditEntry, true, "NarradorMestre")
assert(appNoFunds.ok == false and appNoFunds.newState.xp_gasto == 12)

-- Recusar o 2º pedido marca como recusado sem cobrar XP
local rej = V20.Experience.resolvePending(app.newState, sub2.auditEntry, false, "NarradorMestre")
assert(rej.ok == true and rej.updatedEntry.status == "recusado" and rej.newState.xp_gasto == 12)

-- XP insuficiente na submissão bloqueia (exceto com storytellerOverride)
local noXp = V20.Experience.submitUpgrade(app.newState, {
    traitKind = "discipline", field = "disc_celerity", currentRating = 0, label = "Celeridade 0 -> 1", author = "tester_e2e"
}, { isMestre = false })
assert(noXp.ok == false and noXp.auditEntry == nil)

local overrideXp = V20.Experience.submitUpgrade(app.newState, {
    traitKind = "discipline", field = "disc_celerity", currentRating = 0, label = "Celeridade 0 -> 1", author = "NarradorMestre"
}, { isMestre = true, storytellerOverride = true })
assert(overrideXp.ok == true and overrideXp.auditEntry.status == "aprovado" and overrideXp.newState.disc_celerity == 1 and overrideXp.newState.xp_gasto == 22)

-- Compra direta quando xp_exige_aprovacao == false (ou string "false" do NDB)
local chDirect = { nome = "[TESTE_E2E] Helena Mortal", xp_total = 10, xp_gasto = 0, xp_exige_aprovacao = "false", hab_ocultismo = 0 }
local directUp = V20.Experience.submitUpgrade(chDirect, {
    traitKind = "ability", field = "hab_ocultismo", currentRating = 0, label = "Ocultismo 0 -> 1", author = "tester_e2e"
}, { isMestre = false })
assert(directUp.ok == true and directUp.auditEntry.status == "aprovado" and directUp.newState.hab_ocultismo == 1 and directUp.newState.xp_gasto == 3)

-- Guarda Nosferatu em XP: proibido comprar Aparência
local nosfXp = { nome = "[TESTE_E2E] Zelios Nosferatu", cla_id = "nosferatu", xp_total = 30, xp_gasto = 0, xp_exige_aprovacao = false, attr_aparencia = 0 }
local nosfUp = V20.Experience.submitUpgrade(nosfXp, {
    traitKind = "attribute", field = "attr_aparencia", currentRating = 0, label = "Aparência 0 -> 1", author = "tester_e2e"
}, { isMestre = true })
assert(nosfUp.ok == false)

-- 4. Transição Mortal -> Carniçal / Numina / Humano
local mortal = { nome = "[TESTE_E2E] Helena Mortal", isVampire = false, mortal_sobrenatural_modo = "humano" }
local ghoul = V20.Creation.applyMortalSupernaturalMode(mortal, "carnical")
assert(ghoul.isGhoul == true and ghoul.hasNumina == false and ghoul.sangue_max == 2 and ghoul.sangue_por_turno == 1 and ghoul.ghoulPotence == 1)
assert(mortal.isGhoul == nil, "applyMortalSupernaturalMode não deve mutar tabela original")

local numinaMortal = V20.Creation.applyMortalSupernaturalMode(ghoul, "numina")
assert(numinaMortal.isGhoul == false and numinaMortal.hasNumina == true and numinaMortal.sangue_max == 0 and numinaMortal.sangue_por_turno == 0 and numinaMortal.ghoulPotence == 0)

local backHuman = V20.Creation.applyMortalSupernaturalMode(numinaMortal, "humano")
assert(backHuman.mortal_sobrenatural_modo == "humano" and backHuman.isGhoul == false and backHuman.hasNumina == false and backHuman.sangue_max == 0 and backHuman.ghoulPotence == 0)

local fallbackHuman = V20.Creation.applyMortalSupernaturalMode(ghoul, "modo_desconhecido")
assert(fallbackHuman.mortal_sobrenatural_modo == "humano" and fallbackHuman.isGhoul == false and fallbackHuman.sangue_max == 0)

-- 5. Regressão Finding #1 (Lua 5.4 %d float crash & NaN/±huge em Generations.get) e Finding #4 (guarda anti-aprovação duplicada de nível)
assert(V20.Generations.get(0 / 0).generation == 13, "NaN em Generations.get deve cair para 13ª geração")
assert(V20.Generations.get(math.huge).generation == 13, "+math.huge em Generations.get deve cair para 13ª geração")
assert(V20.Generations.get(-math.huge).generation == 13, "-math.huge em Generations.get deve cair para 13ª geração")

local floatXpLow = { nome = "[TESTE_E2E] Float XP", xp_total = "2.5", xp_gasto = "0.5", xp_exige_aprovacao = true, attr_forca = 3 }
local floatSubFail = V20.Experience.submitUpgrade(floatXpLow, {
    traitKind = "attribute", field = "attr_forca", label = "Força 3 -> 4", author = "tester_e2e"
}, { isMestre = false })
assert(floatSubFail.ok == false and floatSubFail.error:find("disponível 2") ~= nil, "xp_total='2.5' não pode quebrar string.format('%d') no Lua 5.4")

local floatXpEnough = { nome = "[TESTE_E2E] Float XP Ok", xp_total = "14.9", xp_gasto = "2.4", xp_exige_aprovacao = false, attr_forca = 3 }
local floatSubOk = V20.Experience.submitUpgrade(floatXpEnough, {
    traitKind = "attribute", field = "attr_forca", label = "Força 3 -> 4", author = "tester_e2e"
}, { isMestre = false })
assert(floatSubOk.ok == true and floatSubOk.newState.xp_gasto == 14 and math.type(floatSubOk.newState.xp_gasto) == "integer")

local floatPendState = { nome = "[TESTE_E2E] Float Pending", xp_total = "2.5", xp_gasto = "0", attr_forca = 1 }
local floatPendEntry = { status = "pendente", custo_xp = "4.7", campo_alvo = "attr_forca", novo_valor = "2.0" }
local floatResFail = V20.Experience.resolvePending(floatPendState, floatPendEntry, true, "NarradorMestre")
assert(floatResFail.ok == false, "resolvePending com xp_total='2.5' e custo 4 deve recusar sem crash")

floatPendState.xp_total = "6.8"
local floatResOk = V20.Experience.resolvePending(floatPendState, floatPendEntry, true, "NarradorMestre")
assert(floatResOk.ok == true and floatResOk.newState.xp_gasto == 4 and floatResOk.newState.attr_forca == 2 and math.type(floatResOk.newState.xp_gasto) == "integer")

-- Guarda em resolvePending quando campo_alvo já atingiu ou superou novo_valor
local alreadyUpgradedState = { nome = "[TESTE_E2E] Duplicado", xp_total = 30, xp_gasto = 0, attr_forca = 4 }
local stalePending = { status = "pendente", custo_xp = 12, campo_alvo = "attr_forca", novo_valor = 4 }
local dupLevelRes = V20.Experience.resolvePending(alreadyUpgradedState, stalePending, true, "NarradorMestre")
assert(
    dupLevelRes.ok == false
    and dupLevelRes.error == "Característica já atingiu ou superou o nível solicitado."
    and dupLevelRes.newState.xp_gasto == 0,
    "resolvePending deve rejeitar evolução se o campo já atingiu novo_valor"
)

-- Creation.validate com decimais em attrGroups / freebiePurchases não deve quebrar %d no Lua 5.4
local floatCreation = V20.Creation.validate({
    nome = "[TESTE_E2E] Float Creation",
    profile = "vampire_neonate",
    attrGroups = { "8.5", 5, 3 },
    abilityGroups = { 13, 9, 5 },
    baseDisciplines = "3.5",
    baseBackgrounds = 5,
    baseVirtues = 7,
    freebiePurchases = { attributes = "4.5" },
})
assert(floatCreation.valid == false and math.type(floatCreation.freebiesSpent) == "integer")


