local Traits = require("Data.attributes_abilities")
local Dice = require("Core.dice")

-- 1. Catálogo completo: 9 atributos e 30 habilidades
assert(#Traits.ATTRIBUTE_ORDER == 9, "Esperado 9 atributos")
assert(#Traits.ABILITY_ORDER == 30, "Esperado 30 habilidades")
assert(Traits.ATTRIBUTES.attr_forca.name == "Força")
assert(Traits.ABILITIES.hab_investigacao.category == "knowledges")

-- Verificação estrutural das categorias de atributos (3 por categoria) e habilidades (10 por categoria)
local attrCats = { physical = 0, social = 0, mental = 0 }
for _, attrId in ipairs(Traits.ATTRIBUTE_ORDER) do
    local entry = Traits.ATTRIBUTES[attrId]
    assert(entry ~= nil and entry.id == attrId and type(entry.name) == "string", "Atributo inválido: " .. tostring(attrId))
    attrCats[entry.category] = (attrCats[entry.category] or 0) + 1
end
assert(attrCats.physical == 3 and attrCats.social == 3 and attrCats.mental == 3, "Esperado 3 atributos por categoria")

local habCats = { talents = 0, skills = 0, knowledges = 0 }
for _, habId in ipairs(Traits.ABILITY_ORDER) do
    local entry = Traits.ABILITIES[habId]
    assert(entry ~= nil and entry.id == habId and type(entry.name) == "string", "Habilidade inválida: " .. tostring(habId))
    habCats[entry.category] = (habCats[entry.category] or 0) + 1
end
assert(habCats.talents == 10 and habCats.skills == 10 and habCats.knowledges == 10, "Esperado 10 habilidades por categoria")

local zTalent = Traits.getZeroRankRule("talents")
assert(zTalent.allowed == true and zTalent.diffMod == 0 and zTalent.reason == nil)
local zSkill = Traits.getZeroRankRule("skills")
assert(zSkill.allowed == true and zSkill.diffMod == 1 and type(zSkill.reason) == "string")
local zKnow = Traits.getZeroRankRule("knowledges")
assert(zKnow.allowed == false and zKnow.diffMod == 0 and type(zKnow.reason) == "string")

-- 2. Regra V20 crítica: [8, 1] na dif 6 é FALHA SIMPLES, nunca Botch!
local r1 = Dice.evaluate({8, 1}, 6, {})
assert(r1.rawSuccesses == 1, "rawSuccesses deveria ser 1")
assert(r1.ones == 1, "ones deveria ser 1")
assert(r1.rolledNet == 0, "rolledNet deveria ser 0")
assert(r1.totalSuccesses == 0, "totalSuccesses deveria ser 0")
assert(r1.outcome == "failure", "Em V20, ter sucesso cancelado por 1 é falha simples, não botch!")
assert(r1.degree == "Nenhum")
assert(r1.diceCount == 2)

-- 3. Falha Crítica (Botch) real: zero sucessos brutos e pelo menos um 1
local r2 = Dice.evaluate({4, 5, 1}, 6, {})
assert(r2.outcome == "botch", "Zero sucessos brutos com 1 deve ser botch")
assert(r2.degree == "Nenhum")

-- Falha simples sem 1s: zero sucessos brutos e zero 1s
local r2b = Dice.evaluate({2, 4, 5}, 6, {})
assert(r2b.outcome == "failure", "Zero sucessos sem dados 1 deve ser falha simples")

-- 4. Especialidade: 10 vale 2 sucessos (sem explosão), e um 1 cancela apenas 1 deles
local r3 = Dice.evaluate({10, 1}, 6, { specialty = true })
assert(r3.rawSuccesses == 2)
assert(r3.totalSuccesses == 1)
assert(r3.outcome == "success")
assert(r3.degree == "Marginal")
assert(r3.diceCount == 2)

local r3NoSpec = Dice.evaluate({10}, 6, { specialty = false })
assert(r3NoSpec.rawSuccesses == 1 and r3NoSpec.totalSuccesses == 1)

-- Graus de sucesso V20 (2..5+) e clamp de dificuldade
assert(Dice.evaluate({6, 7}, 6, {}).degree == "Moderado")
assert(Dice.evaluate({6, 7, 8}, 6, {}).degree == "Completo")
assert(Dice.evaluate({6, 7, 8, 9}, 6, {}).degree == "Excepcional")
assert(Dice.evaluate({6, 7, 8, 9, 10}, 6, {}).degree == "Fenomenal")
assert(Dice.evaluate({2}, 1, {}).difficulty == 2)
assert(Dice.evaluate({10}, 12, {}).difficulty == 10)

-- 5. Gasto de Força de Vontade (+1 sucesso automático imune a 1s e imune a botch)
local r4 = Dice.evaluate({1, 1, 2}, 6, { spendWillpower = true })
assert(r4.autoSuccesses == 1)
assert(r4.totalSuccesses == 1, "FdV garante 1 sucesso mesmo com dados 1")
assert(r4.outcome == "success")

-- 6. Regras de Habilidade 0: Perícia soma +1 dif; Conhecimento bloqueia sem override
local pSkill0 = Dice.buildPool({
    actorName = "[TESTE_E2E] Jack Brujah",
    attrVal = 3,
    abilityVal = 0,
    abilityCategory = "skills",
    difficulty = 6,
    woundPenalty = -1,
})
assert(pSkill0.canRoll == true)
assert(pSkill0.pool == 2, "3 - 1 de ferimento = 2 dados")
assert(pSkill0.effectiveDifficulty == 7, "Perícia 0 deve subir dificuldade em +1")
assert(#pSkill0.warnings == 1)

local pKnow0 = Dice.buildPool({
    actorName = "[TESTE_E2E] Jack Brujah",
    attrVal = 4,
    abilityVal = 0,
    abilityCategory = "knowledges",
    difficulty = 6,
})
assert(pKnow0.canRoll == false, "Conhecimento 0 não pode testar sem autorização do Narrador")
assert(type(pKnow0.blockReason) == "string")

local pKnow0Override = Dice.buildPool({
    actorName = "[TESTE_E2E] Jack Brujah",
    attrVal = 4,
    abilityVal = 0,
    abilityCategory = "knowledges",
    difficulty = 6,
    storytellerOverride = true,
})
assert(pKnow0Override.canRoll == true and pKnow0Override.pool == 4)

local pTalent0 = Dice.buildPool({
    actorName = "[TESTE_E2E] Jack Brujah",
    attrVal = 3,
    abilityVal = 0,
    abilityCategory = "talents",
    difficulty = 6,
})
assert(pTalent0.canRoll == true and pTalent0.effectiveDifficulty == 6 and #pTalent0.warnings == 0)

local pAbsorb = Dice.buildPool({
    actorName = "[TESTE_E2E] Jack Brujah",
    attrVal = 4,
    abilityVal = 2,
    difficulty = 6,
    woundPenalty = -5,
    ignoreWoundPenalty = true,
})
assert(pAbsorb.pool == 6, "Absorção deve ignorar penalidade de ferimento")

-- Incapacitado e parada zerada por penalidades (salvo sucesso automático)
local pIncap = Dice.buildPool({
    actorName = "[TESTE_E2E] Jack Brujah",
    attrVal = 4,
    abilityVal = 2,
    incapacitated = true,
})
assert(pIncap.canRoll == false and type(pIncap.blockReason) == "string")

local pZero = Dice.buildPool({
    actorName = "[TESTE_E2E] Jack Brujah",
    attrVal = 2,
    abilityVal = 1,
    woundPenalty = -5,
})
assert(pZero.canRoll == false and pZero.pool == 0)

local pZeroWithWillpower = Dice.buildPool({
    actorName = "[TESTE_E2E] Jack Brujah",
    attrVal = 2,
    abilityVal = 1,
    woundPenalty = -5,
    spendWillpower = true,
})
assert(pZeroWithWillpower.canRoll == true and pZeroWithWillpower.pool == 0 and pZeroWithWillpower.autoSuccesses == 1)
