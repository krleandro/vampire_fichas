local CW = require("Core.clan_weaknesses")
local DiscCatalog = require("Data.disciplines_catalog")
local DiscEngine = require("Core.disciplines_engine")

-- 0. Máscara das Mil Faces (obf_3) tem toggleBuff obf_mask e integra com Core.v20_init (PF2-1 item 3)
local obf3 = DiscCatalog.DISCIPLINES.obfuscate.powers[3]
assert(obf3.id == "obf_3", "Terceiro poder de Ofuscação deve ser obf_3")
assert(obf3.toggleBuff ~= nil, "obf_3 deve possuir toggleBuff")
assert(obf3.toggleBuff.id == "obf_mask" and obf3.toggleBuff.maskThousandFaces == true, "toggleBuff de obf_3 deve ser obf_mask")

local V20 = require("Core.v20_init")
assert(V20.ClanWeaknesses == CW, "V20.ClanWeaknesses deve apontar para Core.clan_weaknesses")

-- PF2-1 item 3: mesmo se _G.V20 já tiver sido inicializado antes sem ClanWeaknesses, require("Core.v20_init") deve atribuí-lo
_G.V20 = { ExistingMarker = true }
package.loaded["Core.v20_init"] = nil
local V20Reloaded = require("Core.v20_init")
assert(V20Reloaded.ExistingMarker == true and V20Reloaded.ClanWeaknesses == CW, "V20.ClanWeaknesses deve ser registrado mesmo com _G.V20 pré-existente")
_G.V20 = V20
package.loaded["Core.v20_init"] = V20

-- 1. Brujah: encerrar frenesi ativo gasta 1 FdV (e encaminha storytellerOverride conforme PF2-1 item 2)
local bOrig = { nome = "[TESTE_E2E] Brujah", cla_id = "brujah", em_frenesi = true, fdv_temp = 4 }
local b = CW.endBrujahFrenzyWithWP(bOrig)
assert(b.ok == true and b.newState.em_frenesi == false and b.newState.fdv_temp == 3 and b.error == nil)
assert(bOrig.em_frenesi == true and bOrig.fdv_temp == 4, "endBrujahFrenzyWithWP não deve mutar estado original")

local bNotFrenzy = CW.endBrujahFrenzyWithWP({ nome = "[TESTE_E2E] Brujah Calmo", cla_id = "brujah", em_frenesi = false, fdv_temp = 4 })
assert(bNotFrenzy.ok == false and type(bNotFrenzy.error) == "string")

local bNoWP = CW.endBrujahFrenzyWithWP({ nome = "[TESTE_E2E] Brujah Exausto", cla_id = "brujah", em_frenesi = true, fdv_temp = 0 })
assert(bNoWP.ok == false and bNoWP.newState.fdv_temp == 0)

local bOverride = CW.endBrujahFrenzyWithWP({
    nome = "[TESTE_E2E] Brujah Override",
    cla_id = "brujah",
    em_frenesi = "true",
    fdv_temp = 0,
    storytellerOverride = true,
})
assert(bOverride.ok == true and bOverride.newState.em_frenesi == false and bOverride.newState.fdv_temp == 0)

-- 2. Gangrel: a cada 5 traços animais reduz 1 ponto do atributo social alvo (sem cair abaixo de 0)
local g = {
    nome = "[TESTE_E2E] Gangrel",
    cla_id = "gangrel",
    gangrel_tracos_qtd = 4,
    gangrel_attr_penalizado = "attr_carisma",
    attr_carisma = 3,
}
local g5 = CW.recordGangrelFrenzy(g)
assert(g5.newState.gangrel_tracos_qtd == 5 and g5.penalizedAttr == "attr_carisma" and g5.newAttrVal == 2 and g5.newState.attr_carisma == 2)
assert(g.gangrel_tracos_qtd == 4 and g.attr_carisma == 3, "recordGangrelFrenzy não deve mutar estado original")

local g6 = CW.recordGangrelFrenzy(g5.newState)
assert(g6.newState.gangrel_tracos_qtd == 6 and g6.penalizedAttr == nil and g6.newAttrVal == nil and g6.newState.attr_carisma == 2)

local gFallback = CW.recordGangrelFrenzy({
    nome = "[TESTE_E2E] Gangrel Fallback",
    cla_id = "gangrel",
    gangrel_tracos_qtd = 9,
    gangrel_attr_penalizado = "attr_forca", -- inválido -> fallback attr_carisma
    attr_carisma = 0,
})
assert(gFallback.newState.gangrel_tracos_qtd == 10 and gFallback.penalizedAttr == "attr_carisma" and gFallback.newAttrVal == 0)

-- 3. Malkaviano: perturbação obrigatória na criação + supressão por 1 FdV (e storytellerOverride PF2-1 item 2)
assert(CW.validateCreationRequirements({ nome = "[TESTE_E2E] Malkav Vazio", cla_id = "malkavian", malkav_perturbacao = "" }).valid == false)
assert(CW.validateCreationRequirements({ nome = "[TESTE_E2E] Malkav Espacos", cla_id = "malkavian", malkav_perturbacao = "   " }).valid == false)
assert(CW.validateCreationRequirements({ nome = "[TESTE_E2E] Malkav Valido", cla_id = "malkavian", malkav_perturbacao = "Paranoia" }).valid == true)

local mkOrig = { nome = "[TESTE_E2E] Malkav", cla_id = "malkavian", fdv_temp = 3 }
local mk = CW.suppressMalkavianDerangement(mkOrig)
assert(mk.ok == true and mk.newState.malkav_suprimida_cena == true and mk.newState.fdv_temp == 2 and mk.error == nil)
assert(mkOrig.fdv_temp == 3 and mkOrig.malkav_suprimida_cena == nil, "suppressMalkavianDerangement não deve mutar estado original")

local mkNoWP = CW.suppressMalkavianDerangement({ nome = "[TESTE_E2E] Malkav Sem FdV", cla_id = "malkavian", fdv_temp = 0 })
assert(mkNoWP.ok == false and mkNoWP.newState.fdv_temp == 0)

local mkOverride = CW.suppressMalkavianDerangement({
    nome = "[TESTE_E2E] Malkav Override",
    cla_id = "malkavian",
    fdv_temp = 0,
    storytellerOverride = true,
})
assert(mkOverride.ok == true and mkOverride.newState.malkav_suprimida_cena == true and mkOverride.newState.fdv_temp == 0)

-- 4. Nosferatu: 2 pontos sociais grátis na base; Aparência 0 obrigatória; falha automática em Aparência salvo obf_mask ou storytellerOverride
assert(CW.getSocialBaseFreeDots("nosferatu") == 2)
assert(CW.getSocialBaseFreeDots("toreador") == 3)
assert(CW.getSocialBaseFreeDots("brujah") == 3)
assert(CW.getSocialBaseFreeDots(nil) == 3)

assert(CW.validateCreationRequirements({ nome = "[TESTE_E2E] Nosferatu Inv", cla_id = "nosferatu", attr_aparencia = 1 }).valid == false)
assert(CW.validateCreationRequirements({ nome = "[TESTE_E2E] Nosferatu Val", cla_id = "nosferatu", attr_aparencia = 0 }).valid == true)

local nFail = CW.computeRollModifiers({ nome = "[TESTE_E2E] Nosferatu", cla_id = "nosferatu", attrId = "attr_aparencia", activeBuffs = {} })
assert(nFail.blocked == true and type(nFail.blockReason) == "string" and nFail.blockReason:find("Nosferatu") ~= nil)

local nStringFalseOverride = CW.computeRollModifiers({
    nome = "[TESTE_E2E] Nosferatu NDB False",
    cla_id = "nosferatu",
    attrId = "attr_aparencia",
    activeBuffs = {},
    storytellerOverride = "false",
})
assert(nStringFalseOverride.blocked == true, "storytellerOverride='false' da NDB não deve desbloquear Aparência Nosferatu")

local nMask = CW.computeRollModifiers({
    nome = "[TESTE_E2E] Nosferatu Mascarado",
    cla_id = "nosferatu",
    attrId = "attr_aparencia",
    activeBuffs = { obf_mask = { id = "obf_mask" } },
})
assert(nMask.blocked == false)

local nOverride = CW.computeRollModifiers({
    nome = "[TESTE_E2E] Nosferatu Mestre",
    cla_id = "nosferatu",
    attrId = "attr_aparencia",
    activeBuffs = {},
    storytellerOverride = true,
})
assert(nOverride.blocked == false)

-- Integração real com DisciplinesEngine: ativar obf_3 liga obf_mask e desbloqueia teste de Aparência
local stNosf = {
    nome = "[TESTE_E2E] Nosferatu Obf3",
    cla_id = "nosferatu",
    isVampire = true,
    generation = 12,
    currentBlood = 8,
    fdv_temp = 5,
    attrId = "attr_aparencia",
    activeBuffs = {},
}
local actMaskOn = DiscEngine.activatePower(stNosf, { disc_id = "obfuscate", nivel = 3 }, obf3, {})
assert(actMaskOn.ok == true and actMaskOn.buffToggled.id == "obf_mask" and actMaskOn.buffToggled.active == true)
assert(CW.computeRollModifiers(actMaskOn.newState).blocked == false)
local actMaskOff = DiscEngine.activatePower(actMaskOn.newState, { disc_id = "obfuscate", nivel = 3 }, obf3, {})
assert(actMaskOff.ok == true and actMaskOff.buffToggled.active == false)
assert(CW.computeRollModifiers(actMaskOff.newState).blocked == true)

-- 5. Tremere: 2 goles já completam Laço de Sangue (2/2)
local tOrig = { nome = "[TESTE_E2E] Tremere", cla_id = "tremere", tremere_laco_goles = 0 }
local t1 = CW.recordTremereDrink(tOrig)
assert(t1.step == 1 and t1.fullBond == false and t1.newState.tremere_laco_goles == 1)
assert(tOrig.tremere_laco_goles == 0, "recordTremereDrink não deve mutar estado original")
local t2 = CW.recordTremereDrink(t1.newState)
assert(t2.step == 2 and t2.fullBond == true and t2.newState.tremere_laco_goles == 2)
local t3 = CW.recordTremereDrink(t2.newState)
assert(t3.step == 2 and t3.fullBond == true, "recordTremereDrink deve limitar em 2 goles")

-- 6. Ventrue: restrição obrigatória na criação + bloqueio de presa incompatível (PF2-1 item 1: boolean false e strings NDB "false"/0/"0")
assert(CW.validateCreationRequirements({ nome = "[TESTE_E2E] Ventrue Sem Presa", cla_id = "ventrue", ventrue_presa_restrita = "" }).valid == false)
assert(CW.validateCreationRequirements({ nome = "[TESTE_E2E] Ventrue Com Presa", cla_id = "ventrue", ventrue_presa_restrita = "Aristocratas" }).valid == true)

assert(CW.checkVentrueFeeding({ nome = "[TESTE_E2E] Ventrue", cla_id = "ventrue", ventrue_presa_compativel = false }).allowed == false)
assert(CW.checkVentrueFeeding({ nome = "[TESTE_E2E] Ventrue", cla_id = "ventrue", ventrue_presa_compativel = "false" }).allowed == false)
assert(CW.checkVentrueFeeding({ nome = "[TESTE_E2E] Ventrue", cla_id = "ventrue", ventrue_presa_compativel = 0 }).allowed == false)
assert(CW.checkVentrueFeeding({ nome = "[TESTE_E2E] Ventrue", cla_id = "ventrue", ventrue_presa_compativel = "0" }).allowed == false)
assert(CW.checkVentrueFeeding({ nome = "[TESTE_E2E] Ventrue", cla_id = "ventrue", ventrue_presa_compativel = true }).allowed == true)
assert(CW.checkVentrueFeeding({ nome = "[TESTE_E2E] Ventrue", cla_id = "ventrue", ventrue_presa_compativel = "true" }).allowed == true)
assert(CW.checkVentrueFeeding({ nome = "[TESTE_E2E] Ventrue", cla_id = "ventrue", ventrue_presa_compativel = nil }).allowed == true)
assert(CW.checkVentrueFeeding({ nome = "[TESTE_E2E] Brujah", cla_id = "brujah", ventrue_presa_compativel = false }).allowed == true)

-- 7. Assamita: Ur-Shulgi (letal não absorvível + sangue ganho + dif vício) vs Tremere Clássica (letal + 0 sangue)
local aUrOrig = {
    nome = "[TESTE_E2E] Assamita", isVampire = true, cla_id = "assamite", generation = 12,
    currentBlood = 5, bashing = 0, lethal = 0, aggravated = 0, assamita_maldicao_modo = "ur_shulgi",
}
local aUr = CW.ingestAssamiteVitae(aUrOrig, 2)
assert(aUr.lethalApplied == 2 and aUr.newState.lethal == 2 and aUr.bloodAdded == 2 and aUr.newState.currentBlood == 7 and aUr.addictionDiff == 5)
assert(aUrOrig.lethal == 0 and aUrOrig.currentBlood == 5, "ingestAssamiteVitae não deve mutar estado original")

local aUrCap = CW.ingestAssamiteVitae({
    nome = "[TESTE_E2E] Assamita Vicio Max", isVampire = true, cla_id = "assamite", generation = 12,
    currentBlood = 2, bashing = 0, lethal = 0, aggravated = 0,
}, 8)
assert(aUrCap.addictionDiff == 10, "Dificuldade do teste de vício Assamita deve ter teto 10")

local aTr = CW.ingestAssamiteVitae({
    nome = "[TESTE_E2E] Assamita Antigo", isVampire = true, cla_id = "assamite", generation = 12,
    currentBlood = 5, bashing = 0, lethal = 0, aggravated = 0, assamita_maldicao_modo = "tremere_classica",
}, 2)
assert(aTr.lethalApplied == 2 and aTr.newState.lethal == 2 and aTr.bloodAdded == 0 and aTr.newState.currentBlood == 5 and aTr.addictionDiff == nil)

-- 8. Setita (-1 dado sob luz forte, +2 agravado solar) e Lasombra (+1 dif espelhos, +1 agravado solar)
local sMod = CW.computeRollModifiers({ nome = "[TESTE_E2E] Setita", cla_id = "setite", setita_luz_forte = true })
assert(sMod.bonusDiceMod == -1 and #sMod.warnings == 1)
assert(CW.computeRollModifiers({ nome = "[TESTE_E2E] Setita Escuro", cla_id = "setite", setita_luz_forte = false }).bonusDiceMod == 0)

assert(CW.computeSolarExtraDamage("setite", 2, true) == 2)
assert(CW.computeSolarExtraDamage("setite", 0, true) == 0)
assert(CW.computeSolarExtraDamage("setite", 2, false) == 0)
assert(CW.computeSolarExtraDamage("lasombra", 2, true) == 1)
assert(CW.computeSolarExtraDamage("lasombra", 0, true) == 0)
assert(CW.computeSolarExtraDamage("toreador", 2, true) == 0)

local lModStealth = CW.computeRollModifiers({
    nome = "[TESTE_E2E] Lasombra",
    cla_id = "lasombra",
    lasombra_vigiado_espelhos = true,
    habId = "hab_furtividade",
})
assert(lModStealth.diffMod == 1 and #lModStealth.warnings == 1)

local lModSocial = CW.computeRollModifiers({
    nome = "[TESTE_E2E] Lasombra Social",
    cla_id = "lasombra",
    lasombra_vigiado_espelhos = true,
    attrId = "attr_manipulacao",
})
assert(lModSocial.diffMod == 1)

local lModCombat = CW.computeRollModifiers({
    nome = "[TESTE_E2E] Lasombra Combate",
    cla_id = "lasombra",
    lasombra_vigiado_espelhos = true,
    attrId = "attr_forca",
    habId = "hab_briga",
})
assert(lModCombat.diffMod == 0, "Combate físico sem atributo social/furtividade/lábia não sofre +1 dif de espelho")

-- 9. Giovanni: dobro de dano letal no recipiente
local gioSafe = CW.computeGiovanniKissDamage(3)
assert(gioSafe.lethalToVessel == 6 and gioSafe.fatalRisk == false)
local gio = CW.computeGiovanniKissDamage(4)
assert(gio.lethalToVessel == 8 and gio.fatalRisk == true)

-- 10. Ravnos (vício obrigatório), Tzimisce (divisor 2^dias) e Caitiff (+2 dif Social)
assert(CW.validateCreationRequirements({ nome = "[TESTE_E2E] Ravnos Sem Vicio", cla_id = "ravnos", ravnos_vicio_descricao = "" }).valid == false)
assert(CW.validateCreationRequirements({ nome = "[TESTE_E2E] Ravnos Com Vicio", cla_id = "ravnos", ravnos_vicio_descricao = "Jogos de azar" }).valid == true)

local tzMod0 = CW.computeRollModifiers({ nome = "[TESTE_E2E] Tzimisce Com Terra", cla_id = "tzimisce", tzimisce_dias_sem_terra = 0 })
assert(tzMod0.poolDivisor == 1)
local tzMod = CW.computeRollModifiers({ nome = "[TESTE_E2E] Tzimisce Sem Terra", cla_id = "tzimisce", tzimisce_dias_sem_terra = 2 })
assert(tzMod.poolDivisor == 4 and #tzMod.warnings == 1)

local tzOrig = { nome = "[TESTE_E2E] Tzimisce", tzimisce_dias_sem_terra = 3 }
local tzReset = CW.resetTzimisceSoil(tzOrig)
assert(tzReset.tzimisce_dias_sem_terra == 0 and tzOrig.tzimisce_dias_sem_terra == 3)

local caiMod = CW.computeRollModifiers({
    nome = "[TESTE_E2E] Caitiff",
    cla_id = "caitiff",
    caitiff_estigma_ativo = true,
    attrId = "attr_carisma",
})
assert(caiMod.diffMod == 2 and #caiMod.warnings == 1)

local caiPhys = CW.computeRollModifiers({
    nome = "[TESTE_E2E] Caitiff Fisico",
    cla_id = "caitiff",
    caitiff_estigma_ativo = true,
    attrId = "attr_destreza",
})
assert(caiPhys.diffMod == 0)

-- 11. Segurança contra nil nas funções públicas
assert(CW.validateCreationRequirements(nil).valid == true)
assert(CW.computeRollModifiers(nil).blocked == false and CW.computeRollModifiers(nil).poolDivisor == 1)
assert(CW.computeSolarExtraDamage(nil, nil, nil) == 0)
assert(CW.endBrujahFrenzyWithWP(nil).ok == false)
assert(CW.recordGangrelFrenzy(nil).newState.gangrel_tracos_qtd == 1)
assert(CW.suppressMalkavianDerangement(nil).ok == false)
assert(CW.recordTremereDrink(nil).step == 1)
assert(CW.checkVentrueFeeding(nil).allowed == true)
assert(CW.computeGiovanniKissDamage(nil).lethalToVessel == 2)
assert(CW.resetTzimisceSoil(nil).tzimisce_dias_sem_terra == 0)
