local BgEngine = require("Core.backgrounds_engine")
local BgCatalog = require("Data.backgrounds_catalog")
local MFCatalog = require("Data.merits_flaws_catalog")
local Traits = require("Data.attributes_abilities")

-- 0. Integridade do Catálogo de Antecedentes (13 antecedentes oficiais V20)
local expectedBgOrder = {
    "allies", "alternate_identity", "contacts", "domain", "fame", "generation",
    "herd", "influence", "mentor", "resources", "retainers", "rituals", "status",
}
assert(#BgCatalog.ORDER == 13, "Esperado exatamente 13 antecedentes em BgCatalog.ORDER")

local vampireOnlyExpected = {
    domain = true,
    generation = true,
    herd = true,
    rituals = true,
}

local bgKeyCount = 0
for _ in pairs(BgCatalog.BACKGROUNDS) do
    bgKeyCount = bgKeyCount + 1
end
assert(bgKeyCount == 13, "BgCatalog.BACKGROUNDS deve conter exatamente 13 entradas")

for idx, id in ipairs(BgCatalog.ORDER) do
    assert(id == expectedBgOrder[idx], "Ordem incorreta em BgCatalog.ORDER[" .. idx .. "]: " .. tostring(id))
    local entry = BgCatalog.BACKGROUNDS[id]
    assert(type(entry) == "table", "Antecedente ausente: " .. tostring(id))
    assert(entry.id == id, "entry.id divergente em " .. id)
    assert(type(entry.name) == "string" and #entry.name > 0, "Nome pt-BR ausente em " .. id)
    assert(entry.vampireOnly == (vampireOnlyExpected[id] == true), "vampireOnly incorreto em " .. id)
    if id == "contacts" then
        assert(entry.defaultDiff == 7, "Contatos deve ter defaultDiff == 7 (V20, p. 112)")
    else
        assert(entry.defaultDiff == 6, "defaultDiff esperado 6 em " .. id)
    end
    if id == "generation" then
        assert(entry.actionTitle == nil, "Geração não deve ter ação rolável direta")
    else
        assert(type(entry.actionTitle) == "string" and #entry.actionTitle > 0, "actionTitle ausente em " .. id)
    end
    assert(type(entry.summary) == "string" and entry.summary:find("V20, p%.") ~= nil, "summary sem citação V20 em " .. id)
end

-- Tabelas oficiais de Rebanho e Recursos
local expectedVessels = { [0] = 0, [1] = 3, [2] = 7, [3] = 15, [4] = 30, [5] = 60 }
for dots = 0, 5 do
    assert(BgCatalog.HERD_VESSELS[dots] == expectedVessels[dots], "HERD_VESSELS incorreto para nível " .. dots)
    assert(type(BgCatalog.RESOURCES_TIERS[dots]) == "string" and #BgCatalog.RESOURCES_TIERS[dots] > 0, "RESOURCES_TIERS ausente em " .. dots)
end

-- Integridade do Catálogo de Qualidades, Defeitos e Numina
local expectedItems = {
    "acute_senses", "ambidextrous", "iron_will", "huge_size",
    "additional_disc", "gen_14th", "gen_15th", "bad_sight",
}
assert(#MFCatalog.ORDER == #expectedItems, "MFCatalog.ORDER deve ter 8 itens")
local mfItemCount = 0
for _ in pairs(MFCatalog.ITEMS) do mfItemCount = mfItemCount + 1 end
assert(mfItemCount == #expectedItems, "MFCatalog.ITEMS deve ter exatamente 8 itens")

for idx, itemId in ipairs(expectedItems) do
    assert(MFCatalog.ORDER[idx] == itemId, "Ordem incorreta em MFCatalog.ORDER[" .. idx .. "]")
    local it = MFCatalog.ITEMS[itemId]
    assert(type(it) == "table" and it.id == itemId, "Item ausente em MFCatalog.ITEMS: " .. itemId)
    assert(type(it.name) == "string" and #it.name > 0, "Nome ausente em " .. itemId)
    assert(it.tipo == "qualidade" or it.tipo == "defeito", "tipo inválido em " .. itemId)
    assert(type(it.pontos) == "number" and it.pontos >= 1, "pontos inválido em " .. itemId)
    assert(type(it.effect) == "string" and #it.effect > 0, "effect ausente em " .. itemId)
    assert(type(it.summary) == "string" and it.summary:find("V20, p%.") ~= nil, "summary sem citação V20 em " .. itemId)
end

local expectedNumina = { "true_faith", "hedge_magic", "psychic" }
assert(#MFCatalog.NUMINA_ORDER == #expectedNumina, "MFCatalog.NUMINA_ORDER deve ter 3 itens")
local numinaCount = 0
for _ in pairs(MFCatalog.NUMINA) do numinaCount = numinaCount + 1 end
assert(numinaCount == #expectedNumina, "MFCatalog.NUMINA deve ter exatamente 3 entradas")

for idx, numId in ipairs(expectedNumina) do
    assert(MFCatalog.NUMINA_ORDER[idx] == numId, "Ordem incorreta em MFCatalog.NUMINA_ORDER[" .. idx .. "]")
    local nm = MFCatalog.NUMINA[numId]
    assert(type(nm) == "table" and nm.id == numId, "Numina ausente: " .. numId)
    assert(type(nm.name) == "string" and #nm.name > 0, "Nome ausente em " .. numId)
    assert(Traits.ATTRIBUTES[nm.poolAttr] ~= nil or nm.poolAttr == "attr_fdv_ref", "poolAttr inválido em " .. numId)
    assert(nm.defaultDiff == 7, "defaultDiff esperado 7 em " .. numId)
    assert(type(nm.summary) == "string" and nm.summary:find("V20, p%.") ~= nil, "summary sem citação V20 em " .. numId)
end

-- Verificação passo a passo de Rebanho (0..5 -> {0, 3, 7, 15, 30, 60}) e Recursos (0..5) via deriveSheetEffects
for dots = 0, 5 do
    local stepFx = BgEngine.deriveSheetEffects(13, {
        { bg_id = "herd", nivel = dots },
        { bg_id = "resources", nivel = dots },
    })
    assert(stepFx.herdVessels == expectedVessels[dots], "deriveSheetEffects herdVessels incorreto em " .. dots)
    assert(stepFx.huntingBonusDice == dots, "deriveSheetEffects huntingBonusDice incorreto em " .. dots)
    assert(stepFx.resourcesLabel == BgCatalog.RESOURCES_TIERS[dots], "deriveSheetEffects resourcesLabel incorreto em " .. dots)
end

-- 1. Geração derivada (13 - 3 = 10ª), Rebanho (+2 dados caça, 7 recipientes), Domínio (-2 dif caça), Recursos 3, Fama 2, Status 1
local mockVamp = { nome = "[TESTE_E2E] Marcus Ventrue", baseGen = 13 }
local fx = BgEngine.deriveSheetEffects(mockVamp.baseGen, {
    { bg_id = "generation", nivel = 3 },
    { bg_id = "herd",       nivel = 2 },
    { bg_id = "domain",     nivel = 2 },
    { bg_id = "resources",  nivel = 3 },
    { bg_id = "fame",       nivel = 2 },
    { bg_id = "status",     nivel = 1 },
})
assert(fx.effectiveGeneration == 10)
assert(fx.herdVessels == 7 and fx.huntingBonusDice == 2 and fx.huntingDiffMod == -2)
assert(fx.fameSocialDiffMod == -2 and fx.statusSocialBonusDice == 1)
assert(fx.resourcesLabel:find("Classe Média Alta") ~= nil)

-- Piso de 4ª geração e teto de 5 pontos nos antecedentes cumulativos + segurança contra strings/NaN/nil
local fxElder = BgEngine.deriveSheetEffects(13, {
    { bg_id = "generation", nivel = 12 },
    { bg_id = "herd",       nivel = "3" },
    { bg_id = "herd",       nivel = 4 },
})
assert(fxElder.effectiveGeneration == 4, "Geração efetiva deve ter piso na 4ª Geração")
assert(fxElder.herdVessels == 60 and fxElder.huntingBonusDice == 5, "Rebanho acumulado deve limitar em 5 pontos (60 recipientes)")

local fxEmpty = BgEngine.deriveSheetEffects(nil, nil)
assert(fxEmpty.effectiveGeneration == 13)
assert(fxEmpty.herdVessels == 0 and fxEmpty.huntingBonusDice == 0 and fxEmpty.huntingDiffMod == 0)
assert(fxEmpty.fameSocialDiffMod == 0 and fxEmpty.statusSocialBonusDice == 0)
assert(tostring(fxEmpty.huntingDiffMod) == "0" and tostring(fxEmpty.fameSocialDiffMod) == "0")
assert(fxEmpty.resourcesLabel == BgCatalog.RESOURCES_TIERS[0])

local fxMalformed = BgEngine.deriveSheetEffects(0 / 0, {
    "entrada_invalida",
    { bg_id = "herd", nivel = 0 / 0 },
    { bg_id = "domain", nivel = -3 },
})
assert(fxMalformed.effectiveGeneration == 13 and fxMalformed.herdVessels == 0 and fxMalformed.huntingDiffMod == 0)

-- 2. Rolagem de rede de Contatos Secundários (Carisma + Contatos, dif 7) e demais antecedentes
local roll = BgEngine.buildActionRoll("contacts", 3, 4)
assert(roll.canRoll == true and roll.pool == 7 and roll.defaultDiff == 7 and roll.title == "Sondar Rede de Contatos")

local alliesRoll = BgEngine.buildActionRoll("allies", 2, 3)
assert(alliesRoll.canRoll == true and alliesRoll.pool == 5 and alliesRoll.defaultDiff == 6 and alliesRoll.title == "Acionar Aliados")

local pureBgRoll = BgEngine.buildActionRoll("retainers", 2, 0)
assert(pureBgRoll.canRoll == true and pureBgRoll.pool == 2 and pureBgRoll.defaultDiff == 6)

local genRoll = BgEngine.buildActionRoll("generation", 3, 4)
assert(genRoll.canRoll == false and genRoll.pool == 0)

local zeroDotsRoll = BgEngine.buildActionRoll("contacts", 0, 4)
assert(zeroDotsRoll.canRoll == false and zeroDotsRoll.pool == 0)

local invalidBgRoll = BgEngine.buildActionRoll(nil, 0 / 0, nil)
assert(invalidBgRoll.canRoll == false and invalidBgRoll.pool == 0)

-- 3. Qualidades e Defeitos: teto oficial de +7 pontos de bônus oriundos de Defeitos + Tamanho Grande
local mf = BgEngine.aggregateMeritsFlaws({
    { item_id = "huge_size", tipo = "qualidade", pontos = 4, ativo = true },
    { item_id = "flaw_1",    tipo = "defeito",   pontos = 5, ativo = true },
    { item_id = "flaw_2",    tipo = "defeito",   pontos = 4, ativo = true },
})
assert(mf.totalMeritCost == 4)
assert(mf.totalFlawGainRaw == 9 and mf.effectiveFlawBonus == 7, "Defeitos só concedem até +7 pontos de bônus na V20")
assert(mf.hugeSize == true)
assert(mf.perceptionDiffMod == 0 and mf.hasAdditionalDisc == false and mf.thinBloodGenOverride == nil)

-- Qualidades/Defeitos adicionais: Sentidos Aguçados (-2 dif), Deficiência Visual (+2 dif), Disciplina Adicional, Sangue-Fraco 14ª/15ª e itens inativos
local mfFull = BgEngine.aggregateMeritsFlaws({
    { item_id = "acute_senses",    tipo = "qualidade", pontos = 1, ativo = true },
    { item_id = "additional_disc", tipo = "qualidade", pontos = 5, ativo = true },
    { item_id = "gen_14th",        tipo = "defeito",   pontos = 2, ativo = true },
    { item_id = "bad_sight",       tipo = "defeito",   pontos = 1, ativo = false },
    { item_id = "huge_size",       tipo = "qualidade", pontos = 4, ativo = "false" },
})
assert(mfFull.totalMeritCost == 6 and mfFull.totalFlawGainRaw == 2 and mfFull.effectiveFlawBonus == 2)
assert(mfFull.perceptionDiffMod == -2, "Sentidos Aguçados ativo (-2) com Deficiência Visual inativa deve resultar em -2")
assert(mfFull.hasAdditionalDisc == true)
assert(mfFull.hugeSize == false, "Tamanho Grande com ativo='false' não deve ativar")
assert(mfFull.thinBloodGenOverride == 14)

-- Ordem independente entre 14ª e 15ª Geração + fallback automático de pontos/tipo pelo catálogo
local mfThinOrderA = BgEngine.aggregateMeritsFlaws({
    { item_id = "gen_15th" },
    { item_id = "gen_14th" },
})
local mfThinOrderB = BgEngine.aggregateMeritsFlaws({
    { item_id = "gen_14th" },
    { item_id = "gen_15th" },
})
assert(mfThinOrderA.thinBloodGenOverride == 15 and mfThinOrderB.thinBloodGenOverride == 15)
assert(mfThinOrderA.totalFlawGainRaw == 6 and mfThinOrderA.effectiveFlawBonus == 6)

-- Modificador customizado via mod_tipo sem item_id de catálogo
local mfCustom = BgEngine.aggregateMeritsFlaws({
    { nome = "[TESTE_E2E] Olhos Turvos", tipo = "defeito", pontos = 1, mod_tipo = "perception_diff_+2", ativo = true },
})
assert(mfCustom.perceptionDiffMod == 2 and mfCustom.effectiveFlawBonus == 1)

local mfEmpty = BgEngine.aggregateMeritsFlaws(nil)
assert(mfEmpty.totalMeritCost == 0 and mfEmpty.totalFlawGainRaw == 0 and mfEmpty.effectiveFlawBonus == 0)

-- 4. Motor de Numina para Mortais (Fé Verdadeira, Magia de Cerca, Fenômeno Psíquico)
local mockMortal = { nome = "[TESTE_E2E] Padre Inacio Mortal", fdv_perm = 7, attr_inteligencia = 4, attr_percepcao = 3 }
local faithRoll = BgEngine.buildNuminaRoll("true_faith", 3, 0)
assert(faithRoll.canRoll == true and faithRoll.pool == 3 and faithRoll.defaultDiff == 7 and faithRoll.poolAttr == "attr_fdv_ref")

local hedgeRoll = BgEngine.buildNuminaRoll("hedge_magic", 2, mockMortal.attr_inteligencia)
assert(hedgeRoll.canRoll == true and hedgeRoll.pool == 6 and hedgeRoll.defaultDiff == 7 and hedgeRoll.poolAttr == "attr_inteligencia")

local psychicRoll = BgEngine.buildNuminaRoll("psychic", 3, mockMortal.attr_percepcao)
assert(psychicRoll.canRoll == true and psychicRoll.pool == 6 and psychicRoll.defaultDiff == 7 and psychicRoll.poolAttr == "attr_percepcao")

assert(BgEngine.buildNuminaRoll("true_faith", 0, 5).canRoll == false)
assert(BgEngine.buildNuminaRoll("inexistente", 2, 3).canRoll == false)
