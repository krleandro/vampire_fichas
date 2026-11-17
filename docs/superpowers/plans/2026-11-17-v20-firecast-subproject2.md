# Vampiro V20 Firecast Suite (Subproject 2 — 15 Sheets, Clan Weaknesses & Blood Magic) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expandir `dist/Vampiro_V20_Suite.rpk` para a versão `0.6.0` contendo os **15 modelos de ficha separados** (13 Clãs Tradicionais + Caitiff + Mortal), automação mecânica das **14 fraquezas vampíricas** e o subsistema completo de **Magia do Sangue & Rituais** (6 Linhas de Taumaturgia, 3 Linhas de Necromancia e 20 Rituais Clássicos V20 + aba dinâmica `tabMagiaSangue`).

**Architecture:** Dois novos módulos puros em `Core/` (`Core/clan_weaknesses.lua` e `Core/blood_magic_engine.lua`) apoiados pelo catálogo declarativo `Data/blood_magic_catalog.lua`, integrados em `Core/v20_init.lua` e `Adapter/firecast_bridge.lua`; extensão parametrizada de `Templates/theme_gothic.py` e `Templates/generate_vampire_lfm.py` (`--all-clans`) gerando os 14 `.lfm` vampíricos com painéis específicos de fraqueza na Aba 6 e a 8ª aba condicional `tabMagiaSangue`; e empacotamento multi-`dataType` dos 15 formulários em `tools/build_v20_suite.py` validado na `lua54x64.dll`.

**Tech Stack:** Lua 5.4 (`C:\Users\Cliente\AppData\Local\Firecast\lua54x64.dll`), RRPG Firecast SDK 3.7b (`sdkApiVersion="88"`, `sdkMinorApiVersion="2"`), Python 3.x.

**Spec:** `docs/superpowers/specs/2026-11-17-v20-firecast-subproject2-design.md`

## Global Constraints

- **Referência Mecânica Exclusiva:** *Vampire: The Masquerade — 20th Anniversary Edition (V20 Corebook)*.
- **Idioma:** Português Brasileiro (`pt-BR`) na interface e mensagens; IDs internos em ASCII.
- **Isolamento de Sandbox em Testes (`[TESTE_E2E]`):** Todos os personagens simulados em `Tests/` DEVEM usar o prefixo `[TESTE_E2E]` em `nome`/`titulo` e limpar recursos temporários em blocos `finally:`.
- **Regras Estritas Firecast SDK 3.7b:**
  1. Usar apenas tags nativas suportadas pelo compilador (`form`, `script`, `tabControl`, `tab`, `scrollBox`, `layout`, `rectangle`, `label`, `edit`, `comboBox`, `checkBox`, `button`, `textEditor`, `dataLink`, `event`), sem `<recordList>` ou `<template>`;
  2. Todos os `<dataLink>` filhos diretos de `<form>`;
  3. `horzTextAlign` e `vertTextAlign` estritamente `"leading"`, `"center"` ou `"trailing"`;
  4. `rawset(obj, "_oldSetNodeObjectFunction", obj.setNodeObject);` e `cacheMode = "none"`;
  5. Nomes (`name="..."`) únicos por formulário `.lfm`;
  6. Prefixar `require("v20_shim.dlua"); ` na linha 1 de todos os arquivos `Core/*.lua` e `Adapter/*.lua` empacotados no `.rpk` para garantir boot alfabético VHD seguro;
  7. Direitos autorais: resumos mecânicos próprios concisos + citação de página V20, sem cópia literal.

---

## Mapa de Arquivos do Subprojeto 2

- Modify: `Data/disciplines_catalog.lua` — adicionar `toggleBuff = { id = "obf_mask", maskThousandFaces = true }` em `obf_3` (*Máscara das Mil Faces*) para destravar testes de Aparência Nosferatu sob disfarce ilusório.
- Create: `Core/clan_weaknesses.lua` — regras puras das 14 fraquezas vampíricas.
- Create: `Data/blood_magic_catalog.lua` — 6 Linhas de Taumaturgia (30 poderes), 3 Linhas de Necromancia (15 poderes) e 20 Rituais Clássicos V20 (10 Taumatúrgicos + 10 Necromânticos).
- Create: `Core/blood_magic_engine.lua` — derivação de Linha Primária, validação de Linhas Secundárias, ativação de poderes de linha, conjuração de rituais e checagem de visibilidade `hasBloodMagicAccess`.
- Modify: `Core/v20_init.lua` — registrar `BloodMagicCatalog`, `ClanWeaknesses` e `BloodMagicEngine` (suportando recarga limpa se novos campos forem adicionados).
- Modify: `Adapter/firecast_bridge.lua` — integrar as 14 fraquezas, Linhas Primária/Secundárias, Rituais e evolução XP de `bm_sec1_nivel..bm_sec4_nivel`.
- Modify: `Templates/theme_gothic.py` & `Templates/generate_vampire_lfm.py` — controles específicos de fraqueza na Aba 6 por clã, flag `dano_fonte_solar` na Aba 5, Aba 8 dinâmica (`tabMagiaSangue`) e geração `--all-clans` dos 14 `.lfm` vampíricos (`Sheets/frmBrujah.lfm` .. `Sheets/frmCaitiff.lfm`).
- Modify: `module.xml` & `tools/build_v20_suite.py` — versão `0.6.0` e empacotamento das 15 fichas (`14 clãs + 1 mortal`).
- Create/Modify Tests: `Tests/test_10_clan_weaknesses.lua`, `Tests/test_11_blood_magic.lua`, `Tests/test_08_bridge_and_lfm_gen.py`, `Tests/test_09_rpk_package.py`.

---

### Task 1: Motor Puro das 14 Fraquezas Vampíricas (`Core/clan_weaknesses.lua`)

**Files:**
- Modify: `Data/disciplines_catalog.lua:98-100`
- Create: `Core/clan_weaknesses.lua`
- Modify: `Core/v20_init.lua`
- Test: `Tests/test_10_clan_weaknesses.lua`

**Interfaces:**
- Consumes: `Core/willpower_morality.lua`, `Core/health.lua`, `Core/generation_blood.lua`
- Produces:
  - `ClanWeaknesses.getSocialBaseFreeDots(clanId)` -> `2` para `"nosferatu"`, `3` para os demais
  - `ClanWeaknesses.validateCreationRequirements(state)` -> `{ valid = boolean, errors = string[] }` (valida `malkav_perturbacao`, `ventrue_presa_restrita`, `ravnos_vicio_descricao` e `attr_aparencia == 0` para Nosferatu)
  - `ClanWeaknesses.computeRollModifiers(state)` -> `{ blocked = boolean, blockReason = string|nil, bonusDiceMod = number, diffMod = number, poolDivisor = number, warnings = string[] }`
  - `ClanWeaknesses.computeSolarExtraDamage(clanId, amount, isSolar)` -> `number` (`+2` Setita, `+1` Lasombra quando `isSolar == true and amount > 0`)
  - `ClanWeaknesses.endBrujahFrenzyWithWP(state)` -> `{ ok, newState, error }`
  - `ClanWeaknesses.recordGangrelFrenzy(state)` -> `{ newState, penalizedAttr = string|nil, newAttrVal = number|nil }`
  - `ClanWeaknesses.suppressMalkavianDerangement(state)` -> `{ ok, newState, error }`
  - `ClanWeaknesses.recordTremereDrink(state)` -> `{ newState, fullBond = boolean, step = number }`
  - `ClanWeaknesses.checkVentrueFeeding(state)` -> `{ allowed = boolean, reason = string|nil }`
  - `ClanWeaknesses.ingestAssamiteVitae(state, points)` -> `{ newState, lethalApplied = number, addictionDiff = number|nil, bloodAdded = number }`
  - `ClanWeaknesses.computeGiovanniKissDamage(bloodPoints)` -> `{ lethalToVessel = number, fatalRisk = boolean }`
  - `ClanWeaknesses.resetTzimisceSoil(state)` -> `newState`

- [ ] **Step 1: Escrever o teste falho `Tests/test_10_clan_weaknesses.lua`**

```lua
local CW = require("Core.clan_weaknesses")
local DiscCatalog = require("Data.disciplines_catalog")

-- 0. Máscara das Mil Faces tem toggleBuff obf_mask
assert(DiscCatalog.DISCIPLINES.obfuscate.powers[3].toggleBuff ~= nil)
assert(DiscCatalog.DISCIPLINES.obfuscate.powers[3].toggleBuff.id == "obf_mask")

-- 1. Brujah: encerrar frenesi ativo gasta 1 FdV
local b = CW.endBrujahFrenzyWithWP({ nome = "[TESTE_E2E] Brujah", cla_id = "brujah", em_frenesi = true, fdv_temp = 4 })
assert(b.ok == true and b.newState.em_frenesi == false and b.newState.fdv_temp == 3)

-- 2. Gangrel: a cada 5 traços animais reduz 1 ponto do atributo social alvo
local g = { nome = "[TESTE_E2E] Gangrel", cla_id = "gangrel", gangrel_tracos_qtd = 4, gangrel_attr_penalizado = "attr_carisma", attr_carisma = 3 }
local g5 = CW.recordGangrelFrenzy(g)
assert(g5.newState.gangrel_tracos_qtd == 5 and g5.penalizedAttr == "attr_carisma" and g5.newState.attr_carisma == 2)

-- 3. Malkaviano: perturbação obrigatória na criação + supressão por 1 FdV
assert(CW.validateCreationRequirements({ cla_id = "malkavian", malkav_perturbacao = "" }).valid == false)
assert(CW.validateCreationRequirements({ cla_id = "malkavian", malkav_perturbacao = "Paranoia" }).valid == true)
local mk = CW.suppressMalkavianDerangement({ nome = "[TESTE_E2E] Malkav", cla_id = "malkavian", fdv_temp = 3 })
assert(mk.ok == true and mk.newState.malkav_suprimida_cena == true and mk.newState.fdv_temp == 2)

-- 4. Nosferatu: 2 pontos sociais grátis na base; falha automática em Aparência salvo obf_mask ou storytellerOverride
assert(CW.getSocialBaseFreeDots("nosferatu") == 2)
assert(CW.getSocialBaseFreeDots("toreador") == 3)
local nFail = CW.computeRollModifiers({ cla_id = "nosferatu", attrId = "attr_aparencia", activeBuffs = {} })
assert(nFail.blocked == true)
local nMask = CW.computeRollModifiers({ cla_id = "nosferatu", attrId = "attr_aparencia", activeBuffs = { obf_mask = { id = "obf_mask" } } })
assert(nMask.blocked == false)

-- 5. Tremere: 2 goles já completam Laço de Sangue (2/2)
local t1 = CW.recordTremereDrink({ nome = "[TESTE_E2E] Tremere", cla_id = "tremere", tremere_laco_goles = 0 })
assert(t1.step == 1 and t1.fullBond == false)
local t2 = CW.recordTremereDrink(t1.newState)
assert(t2.step == 2 and t2.fullBond == true)

-- 6. Ventrue: restrição obrigatória na criação + bloqueio de presa incompatível
assert(CW.validateCreationRequirements({ cla_id = "ventrue", ventrue_presa_restrita = "" }).valid == false)
assert(CW.checkVentrueFeeding({ cla_id = "ventrue", ventrue_presa_compativel = false }).allowed == false)
assert(CW.checkVentrueFeeding({ cla_id = "ventrue", ventrue_presa_compativel = true }).allowed == true)

-- 7. Assamita: Ur-Shulgi (letal não absorvível + sangue ganho + dif vício) vs Tremere Clássica (letal + 0 sangue)
local aUr = CW.ingestAssamiteVitae({
    nome = "[TESTE_E2E] Assamita", isVampire = true, cla_id = "assamite", generation = 12,
    currentBlood = 5, bashing = 0, lethal = 0, aggravated = 0, assamita_maldicao_modo = "ur_shulgi"
}, 2)
assert(aUr.lethalApplied == 2 and aUr.newState.lethal == 2 and aUr.bloodAdded == 2 and aUr.addictionDiff == 5)

local aTr = CW.ingestAssamiteVitae({
    nome = "[TESTE_E2E] Assamita Antigo", isVampire = true, cla_id = "assamite", generation = 12,
    currentBlood = 5, bashing = 0, lethal = 0, aggravated = 0, assamita_maldicao_modo = "tremere_classica"
}, 2)
assert(aTr.lethalApplied == 2 and aTr.newState.lethal == 2 and aTr.bloodAdded == 0 and aTr.addictionDiff == nil)

-- 8. Setita (-1 dado sob luz forte, +2 agravado solar) e Lasombra (+1 dif espelhos, +1 agravado solar)
local sMod = CW.computeRollModifiers({ cla_id = "setite", setita_luz_forte = true })
assert(sMod.bonusDiceMod == -1)
assert(CW.computeSolarExtraDamage("setite", 2, true) == 2)
assert(CW.computeSolarExtraDamage("lasombra", 2, true) == 1)
local lMod = CW.computeRollModifiers({ cla_id = "lasombra", lasombra_vigiado_espelhos = true, habId = "hab_furtividade" })
assert(lMod.diffMod == 1)

-- 9. Giovanni: dobro de dano letal no recipiente
local gio = CW.computeGiovanniKissDamage(4)
assert(gio.lethalToVessel == 8 and gio.fatalRisk == true)

-- 10. Ravnos (vício obrigatório), Tzimisce (divisor 2^dias) e Caitiff (+2 dif Social)
assert(CW.validateCreationRequirements({ cla_id = "ravnos", ravnos_vicio_descricao = "" }).valid == false)
local tzMod = CW.computeRollModifiers({ cla_id = "tzimisce", tzimisce_dias_sem_terra = 2 })
assert(tzMod.poolDivisor == 4)
local tzReset = CW.resetTzimisceSoil({ tzimisce_dias_sem_terra = 3 })
assert(tzReset.tzimisce_dias_sem_terra == 0)
local caiMod = CW.computeRollModifiers({ cla_id = "caitiff", caitiff_estigma_ativo = true, attrId = "attr_carisma" })
assert(caiMod.diffMod == 2)
```

- [ ] **Step 2: Rodar o teste para confirmar falha**

Executar: `python Tests/run_tests.py Tests/test_10_clan_weaknesses.lua`  
Resultado esperado: `FAIL` com `module 'Core.clan_weaknesses' not found`.

- [ ] **Step 3: Implementar `Core/clan_weaknesses.lua` e atualizar `Data/disciplines_catalog.lua` e `Core/v20_init.lua`**

Atualizar `obf_3` em `Data/disciplines_catalog.lua`:
```lua
p(3, "obf_3", "Máscara das Mil Faces", 0, 0, "attr_manipulacao", "hab_performance", 7, "Dif 7", { id = "obf_mask", maskThousandFaces = true }, "Projeta feições ilusórias escolhidas na mente de quem o observa (V20, p. 186)."),
```

Criar `Core/clan_weaknesses.lua`:
```lua
local WM = require("Core.willpower_morality")
local Health = require("Core.health")
local Blood = require("Core.generation_blood")

local CW = {}

local SOCIAL_ATTRS = { attr_carisma = true, attr_manipulacao = true, attr_aparencia = true }

local function copyState(s)
    local o = {}
    for k, v in pairs(s or {}) do o[k] = v end
    return o
end

local function isTrue(v)
    return v == true or v == "true" or v == 1 or v == "1"
end

local function nonEmpty(s)
    return type(s) == "string" and s:match("%S") ~= nil
end

local function safeNonNegInt(v, default)
    local n = tonumber(v)
    if n == nil or n ~= n or n == math.huge or n == -math.huge then return default or 0 end
    n = math.floor(n)
    return n < 0 and 0 or n
end

function CW.getSocialBaseFreeDots(clanId)
    return (clanId == "nosferatu") and 2 or 3
end

function CW.validateCreationRequirements(state)
    state = state or {}
    local errors = {}
    local cid = state.cla_id

    if cid == "nosferatu" and safeNonNegInt(state.attr_aparencia, 0) ~= 0 then
        table.insert(errors, "Nosferatu possui Aparência permanentemente igual a 0 (V20, p. 61).")
    elseif cid == "malkavian" and not nonEmpty(state.malkav_perturbacao) then
        table.insert(errors, "Malkaviano exige definir a Perturbação incurável inicial (V20, p. 59).")
    elseif cid == "ventrue" and not nonEmpty(state.ventrue_presa_restrita) then
        table.insert(errors, "Ventrue exige definir o tipo exclusivo de recipiente mortal da alimentação (V20, p. 71).")
    elseif cid == "ravnos" and not nonEmpty(state.ravnos_vicio_descricao) then
        table.insert(errors, "Ravnos exige definir o Vício específico da fraqueza de clã (V20, p. 63).")
    end

    return { valid = (#errors == 0), errors = errors }
end

function CW.computeRollModifiers(state)
    state = state or {}
    local cid = state.cla_id
    local attrId = state.attrId
    local habId = state.habId
    local buffs = state.activeBuffs or {}
    local warnings = {}
    local bonusDiceMod = 0
    local diffMod = 0
    local poolDivisor = 1

    if cid == "nosferatu" and attrId == "attr_aparencia" and not state.storytellerOverride then
        if not buffs.obf_mask then
            return {
                blocked = true,
                blockReason = "Maldição Nosferatu: Aparência 0 causa falha automática sem Máscara das Mil Faces (V20, p. 61).",
                bonusDiceMod = 0,
                diffMod = 0,
                poolDivisor = 1,
                warnings = warnings,
            }
        end
    end

    if cid == "setite" and isTrue(state.setita_luz_forte) then
        bonusDiceMod = bonusDiceMod - 1
        table.insert(warnings, "Fraqueza Setita: -1 dado sob luz forte.")
    end

    if cid == "lasombra" and isTrue(state.lasombra_vigiado_espelhos) then
        if SOCIAL_ATTRS[attrId or ""] or habId == "hab_furtividade" or habId == "hab_labia" then
            diffMod = diffMod + 1
            table.insert(warnings, "Fraqueza Lasombra: +1 dif perante espelhos/câmeras.")
        end
    end

    if cid == "caitiff" and isTrue(state.caitiff_estigma_ativo) and SOCIAL_ATTRS[attrId or ""] then
        diffMod = diffMod + 2
        table.insert(warnings, "Estigma Social Caitiff: +2 dif com Membros estabelecidos.")
    end

    if cid == "tzimisce" then
        local days = math.min(10, safeNonNegInt(state.tzimisce_dias_sem_terra, 0))
        if days > 0 then
            poolDivisor = math.floor(2 ^ days)
            table.insert(warnings, string.format("Fraqueza Tzimisce: %d dia(s) sem terra natal (parada / %d, mín. 1).", days, poolDivisor))
        end
    end

    return {
        blocked = false,
        blockReason = nil,
        bonusDiceMod = bonusDiceMod,
        diffMod = diffMod,
        poolDivisor = poolDivisor,
        warnings = warnings,
    }
end

function CW.computeSolarExtraDamage(clanId, amount, isSolar)
    local amt = safeNonNegInt(amount, 0)
    if not isTrue(isSolar) or amt <= 0 then return 0 end
    if clanId == "setite" then return 2 end
    if clanId == "lasombra" then return 1 end
    return 0
end

function CW.endBrujahFrenzyWithWP(state)
    state = state or {}
    if not isTrue(state.em_frenesi) then
        return { ok = false, newState = copyState(state), error = "O personagem não está em Frenesi ativo no momento." }
    end
    local wRes = WM.spendWillpower(state, 1)
    if not wRes.ok then
        return { ok = false, newState = wRes.newState, error = wRes.error }
    end
    local nextSt = wRes.newState
    nextSt.em_frenesi = false
    return { ok = true, newState = nextSt, error = nil }
end

function CW.recordGangrelFrenzy(state)
    local nextSt = copyState(state)
    local count = safeNonNegInt(nextSt.gangrel_tracos_qtd, 0) + 1
    nextSt.gangrel_tracos_qtd = count
    local target = nextSt.gangrel_attr_penalizado
    if not SOCIAL_ATTRS[target or ""] then
        target = "attr_carisma"
    end
    if count > 0 and (count % 5 == 0) then
        local cur = safeNonNegInt(nextSt[target], 1)
        local nextVal = math.max(0, cur - 1)
        nextSt[target] = nextVal
        return { newState = nextSt, penalizedAttr = target, newAttrVal = nextVal }
    end
    return { newState = nextSt, penalizedAttr = nil, newAttrVal = nil }
end

function CW.suppressMalkavianDerangement(state)
    local wRes = WM.spendWillpower(state, 1)
    if not wRes.ok then
        return { ok = false, newState = wRes.newState, error = wRes.error }
    end
    local nextSt = wRes.newState
    nextSt.malkav_suprimida_cena = true
    return { ok = true, newState = nextSt, error = nil }
end

function CW.recordTremereDrink(state)
    local nextSt = copyState(state)
    local cur = safeNonNegInt(nextSt.tremere_laco_goles, 0)
    local step = math.min(2, cur + 1)
    nextSt.tremere_laco_goles = step
    return { newState = nextSt, fullBond = (step >= 2), step = step }
end

function CW.checkVentrueFeeding(state)
    state = state or {}
    if state.cla_id == "ventrue" and state.ventrue_presa_compativel == false then
        return {
            allowed = false,
            reason = "Restrição Ventrue: sangue fora da preferência alimentar é vomitado imediatamente (0 vitae ganha; V20, p. 71).",
        }
    end
    return { allowed = true, reason = nil }
end

function CW.ingestAssamiteVitae(state, points)
    local pts = math.max(1, safeNonNegInt(points, 1))
    local damaged = Health.applyDamage(state, pts, "lethal", { isVampire = true, isFirearm = false, halveBashing = false })
    local mode = (state and state.assamita_maldicao_modo) or "ur_shulgi"
    if mode == "tremere_classica" then
        return { newState = damaged, lethalApplied = pts, addictionDiff = nil, bloodAdded = 0 }
    end
    local gained = Blood.gain(damaged, pts)
    local diff = math.min(10, 3 + pts)
    return { newState = gained.newState, lethalApplied = pts, addictionDiff = diff, bloodAdded = gained.added }
end

function CW.computeGiovanniKissDamage(bloodPoints)
    local pts = math.max(1, safeNonNegInt(bloodPoints, 1))
    local let = pts * 2
    return { lethalToVessel = let, fatalRisk = (let >= 7) }
end

function CW.resetTzimisceSoil(state)
    local nextSt = copyState(state)
    nextSt.tzimisce_dias_sem_terra = 0
    return nextSt
end

return CW
```

Atualizar `Core/v20_init.lua` para incluir `ClanWeaknesses = require("Core.clan_weaknesses")` (atribuindo `V20.ClanWeaknesses = V20.ClanWeaknesses or require("Core.clan_weaknesses")` para ser seguro mesmo quando `V20` já existir).

- [ ] **Step 4: Rodar os testes e confirmar aprovação**

Executar: `python Tests/run_tests.py Tests/test_10_clan_weaknesses.lua` e `python Tests/run_tests.py`  
Resultado esperado: `[PASS] Tests\test_10_clan_weaknesses.lua` e todas as suítes aprovadas.

- [ ] **Step 5: Commit**

```bash
git add Data/disciplines_catalog.lua Core/clan_weaknesses.lua Core/v20_init.lua Tests/test_10_clan_weaknesses.lua
git commit -m "feat(core): add mechanical automation engine for all 14 V20 clan weaknesses"
```

---

### Task 2: Catálogo e Motor de Magia do Sangue — 9 Linhas (45 Poderes) & 20 Rituais V20 (`Data/blood_magic_catalog.lua`, `Core/blood_magic_engine.lua`)

**Files:**
- Create: `Data/blood_magic_catalog.lua`
- Create: `Core/blood_magic_engine.lua`
- Modify: `Core/v20_init.lua`
- Test: `Tests/test_11_blood_magic.lua`

**Interfaces:**
- Consumes: `Core/generation_blood.lua`, `Core/willpower_morality.lua`
- Produces:
  - `BloodMagicCatalog.THAUMATURGY_PATHS` (6 linhas × 5 poderes = 30 poderes) & `BloodMagicCatalog.NECROMANCY_PATHS` (3 linhas × 5 poderes = 15 poderes)
  - `BloodMagicCatalog.RITUALS` (10 Taumatúrgicos + 10 Necromânticos = 20 rituais estruturados)
  - `BloodMagicEngine.derivePrimaryPathLevel(discDots)` -> `math.min(5, math.max(0, discDots))`
  - `BloodMagicEngine.validateSecondaryPathUpgrade(params)` -> `{ ok = boolean, error = string|nil }` (`params = { parentDiscDots, primaryPathId, secondaryPathId, targetLevel }`)
  - `BloodMagicEngine.activatePathPower(state, tradition, pathId, pathDots, level, opts)` -> `{ ok, newState, rollSpec, error }`
  - `BloodMagicEngine.castRitual(state, ritualIdOrCustom, parentDiscDots, opts)` -> `{ ok, newState, rollSpec, error }`
  - `BloodMagicEngine.hasBloodMagicAccess(clanId, disciplinesList, ritualsBgDots)` -> `boolean`

- [ ] **Step 1: Escrever o teste falho `Tests/test_11_blood_magic.lua`**

```lua
local V20 = require("Core.v20_init")
local BMCat = V20.BloodMagicCatalog
local BMEng = V20.BloodMagicEngine

-- 1. Catálogo completo: 6 linhas Taumaturgia (30 poderes), 3 linhas Necromancia (15 poderes) e 20 rituais
assert(#BMCat.THAUMATURGY_ORDER == 6)
assert(#BMCat.NECROMANCY_ORDER == 3)
assert(#BMCat.RITUAL_ORDER == 20)
for _, pid in ipairs(BMCat.THAUMATURGY_ORDER) do
    assert(#BMCat.THAUMATURGY_PATHS[pid].powers == 5)
end
for _, pid in ipairs(BMCat.NECROMANCY_ORDER) do
    assert(#BMCat.NECROMANCY_PATHS[pid].powers == 5)
end

-- 2. Regras V20 de Linha Primária vs Linha Secundária (p. 159 e p. 212)
assert(BMEng.derivePrimaryPathLevel(6) == 5)
assert(BMEng.validateSecondaryPathUpgrade({
    parentDiscDots = 1, primaryPathId = "path_of_blood", secondaryPathId = "lure_of_flames", targetLevel = 1
}).ok == false, "Primária precisa estar em >= 2 para iniciar Secundária")

assert(BMEng.validateSecondaryPathUpgrade({
    parentDiscDots = 3, primaryPathId = "path_of_blood", secondaryPathId = "lure_of_flames", targetLevel = 3
}).ok == false, "Secundária não pode igualar Primária antes de Primária atingir 5")

assert(BMEng.validateSecondaryPathUpgrade({
    parentDiscDots = 5, primaryPathId = "path_of_blood", secondaryPathId = "lure_of_flames", targetLevel = 5
}).ok == true, "Quando Primária está em 5, Secundária pode chegar a 5")

assert(BMEng.validateSecondaryPathUpgrade({
    parentDiscDots = 5, primaryPathId = "path_of_blood", secondaryPathId = "path_of_blood", targetLevel = 1
}).ok == false, "Secundária não pode duplicar a Linha Primária")

-- 3. Ativação de poder de Linha de Taumaturgia (Sedutor das Chamas 3: gasta 1 sangue, rola FdV dif 6)
local st = { nome = "[TESTE_E2E] Tremere", isVampire = true, generation = 12, currentBlood = 8, spentThisTurn = 0, fdv_temp = 6 }
local pRes = BMEng.activatePathPower(st, "thaumaturgy", "lure_of_flames", 3, 3, {})
assert(pRes.ok == true and pRes.newState.currentBlood == 7 and pRes.rollSpec.attr == "attr_fdv_ref" and pRes.rollSpec.defaultDiff == 6)

-- 4. Conjuração de Ritual Taumatúrgico Nv 4 (Coração de Pedra): exige Taumaturgia >= 4 e rola Inteligência + Ocultismo dif 7
local rFail = BMEng.castRitual(st, "thau_rit_4_heart_stone", 3, {})
assert(rFail.ok == false)
local rOk = BMEng.castRitual(st, "thau_rit_4_heart_stone", 4, {})
assert(rOk.ok == true and rOk.rollSpec.attr == "attr_inteligencia" and rOk.rollSpec.hab == "hab_ocultismo" and rOk.rollSpec.defaultDiff == 7)

-- 5. Visibilidade dinâmica da aba Magia do Sangue
assert(BMEng.hasBloodMagicAccess("tremere", {}, 0) == true)
assert(BMEng.hasBloodMagicAccess("giovanni", {}, 0) == true)
assert(BMEng.hasBloodMagicAccess("brujah", {}, 0) == false)
assert(BMEng.hasBloodMagicAccess("brujah", { { disc_id = "thaumaturgy", nivel = 1 } }, 0) == true)
assert(BMEng.hasBloodMagicAccess("toreador", {}, 1) == true)
```

- [ ] **Step 2: Rodar o teste para confirmar falha**

Executar: `python Tests/run_tests.py Tests/test_11_blood_magic.lua`  
Resultado esperado: `FAIL` (`BloodMagicCatalog` ausente).

- [ ] **Step 3: Implementar `Data/blood_magic_catalog.lua`, `Core/blood_magic_engine.lua` e atualizar `Core/v20_init.lua`**

Criar `Data/blood_magic_catalog.lua`:
```lua
local BMCatalog = {}

local function tp(lvl, id, name, summary)
    return {
        id = id, level = lvl, name = name,
        cost = { blood = 1, willpower = 0 },
        pool = { attr = "attr_fdv_ref", hab = nil },
        defaultDiff = lvl + 3,
        diffHint = string.format("1 Sangue; testa FdV dif %d (botch perde 1 FdV perm.)", lvl + 3),
        summary = summary,
    }
end

local function np(lvl, id, name, blood, wp, attr, hab, diff, hint, summary)
    return {
        id = id, level = lvl, name = name,
        cost = { blood = blood or 0, willpower = wp or 0 },
        pool = attr and { attr = attr, hab = hab } or nil,
        defaultDiff = diff or 6,
        diffHint = hint or "Dif 6",
        summary = summary,
    }
end

BMCatalog.THAUMATURGY_ORDER = {
    "path_of_blood", "lure_of_flames", "movement_of_the_mind",
    "path_of_conjuring", "hands_of_destruction", "weather_control",
}

BMCatalog.THAUMATURGY_PATHS = {
    path_of_blood = {
        id = "path_of_blood", name = "Linha do Sangue",
        powers = {
            tp(1, "pob_1", "Um Gosto por Sangue", "Analisa geração, vitae restante e diablerie por uma gota (V20, p. 214)."),
            tp(2, "pob_2", "Fúria do Sangue", "Força outro vampiro a gastar sangue contra sua vontade ao toque (V20, p. 214)."),
            tp(3, "pob_3", "Sangue de Potência", "Reduz temporariamente a Geração efetiva por 1 hora (V20, p. 215)."),
            tp(4, "pob_4", "Furto de Vitae", "Drena sangue de alvo até 15m pelo ar sem contato físico (V20, p. 215)."),
            tp(5, "pob_5", "Caldeirão de Sangue", "Ferve o sangue nas veias causando dano Agravado ao toque (V20, p. 216)."),
        },
    },
    lure_of_flames = {
        id = "lure_of_flames", name = "Sedutor das Chamas",
        powers = {
            tp(1, "lof_1", "Vela", "Conjura pequena chama na palma (1 dado Agravado/turno, dif absorção 3; V20, p. 219)."),
            tp(2, "lof_2", "Punhado de Chamas", "Chama equivalente a tocha (1 dado Agravado/turno, dif absorção 4; V20, p. 219)."),
            tp(3, "lof_3", "Fogueira", "Labaredas intensas à vista (2 dados Agravados/turno, dif absorção 5; V20, p. 219)."),
            tp(4, "lof_4", "Pira", "Coluna ardente de fogo (2 dados Agravados/turno, dif absorção 7; V20, p. 219)."),
            tp(5, "lof_5", "Inferno", "Conflagração devastadora (3 dados Agravados/turno, dif absorção 9; V20, p. 219)."),
        },
    },
    movement_of_the_mind = {
        id = "movement_of_the_mind", name = "Movimento da Mente",
        powers = {
            tp(1, "mom_1", "Meio Quilo", "Move telecineticamente objetos de até 0,5 kg (V20, p. 220)."),
            tp(2, "mom_2", "Dez Quilos", "Ergue e arremessa objetos de até 10 kg mentalmente (V20, p. 220)."),
            tp(3, "mom_3", "Cem Quilos", "Ergue até 100 kg ou permite voo telecinético próprio lento (V20, p. 221)."),
            tp(4, "mom_4", "Meia Tonelada", "Ergue e arremessa massas de até 250–500 kg (V20, p. 221)."),
            tp(5, "mom_5", "Uma Tonelada", "Manipula até 500–1000 kg e arremessa seres vivos com impacto letal (V20, p. 221)."),
        },
    },
    path_of_conjuring = {
        id = "path_of_conjuring", name = "Linha da Conjuração",
        powers = {
            tp(1, "poc_1", "Invocar a Forma Simples", "Materializa objeto inanimado homogêneo simples por turnos (V20, p. 222)."),
            tp(2, "poc_2", "Permanência", "Gasta +3 Sangue para tornar permanente uma forma simples conjurada (V20, p. 222)."),
            tp(3, "poc_3", "Magia do Ferreiro", "Conjura objetos complexos com múltiplos materiais e peças móveis (V20, p. 223)."),
            tp(4, "poc_4", "Reverter Conjuração", "Dissolve instantaneamente criações conjuradas anteriores (V20, p. 223)."),
            tp(5, "poc_5", "Poder Sobre a Vida", "Conjura criatura ou simulacro biológico temporário obediente (V20, p. 223)."),
        },
    },
    hands_of_destruction = {
        id = "hands_of_destruction", name = "Mãos da Destruição",
        powers = {
            tp(1, "hod_1", "Decomposição", "Envelhece e apodrece matéria inanimada ao toque (V20, p. 225)."),
            tp(2, "hod_2", "Retorcer Madeira", "Deforma e estilhaça estruturas de madeira à vista (V20, p. 225)."),
            tp(3, "hod_3", "Toque Ácido", "Secreta fluido corrosivo que causa dano Agravado em carne/metal (V20, p. 226)."),
            tp(4, "hod_4", "Atrofia", "Murcha permanentemente ou pela noite um membro da vítima ao toque (V20, p. 226)."),
            tp(5, "hod_5", "Transformar em Pó", "Envelhece mortais até a morte ou inflige dano Agravado severo (V20, p. 226)."),
        },
    },
    weather_control = {
        id = "weather_control", name = "Controle do Clima",
        powers = {
            tp(1, "wc_1", "Névoa", "Conjura banco denso de neblina ocultando visão local (V20, p. 228)."),
            tp(2, "wc_2", "Chuva ou Neve", "Desencadeia precipitação intensa prejudicando percepção e tráfego (V20, p. 229)."),
            tp(3, "wc_3", "Vendaval", "Levanta ventos violentos que dificultam disparos e movimentação (V20, p. 229)."),
            tp(4, "wc_4", "Tempestade", "Invoca tormenta completa sobre a região em minutos (V20, p. 229)."),
            tp(5, "wc_5", "Ataque de Relâmpago", "Descarrega raio direto causando 10 dados de dano Letal/Agravado (V20, p. 229)."),
        },
    },
}

BMCatalog.NECROMANCY_ORDER = { "sepulchre_path", "bone_path", "ash_path" }

BMCatalog.NECROMANCY_PATHS = {
    sepulchre_path = {
        id = "sepulchre_path", name = "Linha do Sepulcro",
        powers = {
            np(1, "sep_1", "Visão do Cadáver", 0, 0, "attr_percepcao", "hab_consciencia", 6, "Dif 6", "Vê a última imagem registrada pelos olhos de um cadáver (V20, p. 160)."),
            np(2, "sep_2", "Invocar a Alma", 0, 1, "attr_percepcao", "hab_ocultismo", 7, "1 FdV; Dif = FdV do fantasma", "Chama o espectro de um falecido através da Mortalha (V20, p. 161)."),
            np(3, "sep_3", "Compelir a Alma", 0, 1, "attr_manipulacao", "hab_ocultismo", 6, "1 FdV; Dif = FdV da aparição", "Comanda um fantasma invocado por uma cena ou hora (V20, p. 162)."),
            np(4, "sep_4", "Assombração", 1, 0, "attr_manipulacao", "hab_ocultismo", 7, "1 Sangue; Dif = FdV da aparição", "Ancora uma aparição a um local ou objeto específico (V20, p. 162)."),
            np(5, "sep_5", "Tormento", 0, 0, "attr_vigor", "hab_empatia", 6, "Dif = FdV da aparição", "Inflige dano direto ao corpus espiritual de um fantasma (V20, p. 163)."),
        },
    },
    bone_path = {
        id = "bone_path", name = "Linha dos Ossos",
        powers = {
            np(1, "bon_1", "Tremor", 1, 0, "attr_destreza", "hab_ocultismo", 6, "1 Sangue; Dif 6", "Move repentinamente um membro de um cadáver próximo (V20, p. 164)."),
            np(2, "bon_2", "Passo do Aprendiz", 1, 1, "attr_inteligencia", "hab_ocultismo", 7, "1 Sangue + 1 FdV; Dif 7", "Reanima cadáveres como zumbis lentos para tarefas simples (V20, p. 165)."),
            np(3, "bon_3", "Trôpego", 1, 1, "attr_raciocinio", "hab_ocultismo", 6, "1 Sangue/cadáver + 1 FdV; Dif 6", "Ergue guardiões mortos-vivos agressivos capazes de combater (V20, p. 165)."),
            np(4, "bon_4", "Roubar a Vida", 0, 1, "attr_manipulacao", "hab_medicina", 7, "1 FdV; Dif 7", "Extrai temporariamente a alma de um ser vivo do próprio corpo (V20, p. 166)."),
            np(5, "bon_5", "Infusão Daemônica", 2, 1, "attr_inteligencia", "hab_ocultismo", 6, "2 Sangue + 1 FdV; Dif 6", "Prende um espectro num cadáver fresco criando servo inteligente (V20, p. 167)."),
        },
    },
    ash_path = {
        id = "ash_path", name = "Linha das Cinzas",
        powers = {
            np(1, "ash_1", "Visão da Mortalha", 0, 0, "attr_percepcao", "hab_consciencia", 7, "Dif 7", "Enxerga fantasmas e estruturas das Terras Sombrias pela cena (V20, p. 169)."),
            np(2, "ash_2", "Línguas Sem Vida", 0, 1, "attr_percepcao", "hab_ocultismo", 6, "1 FdV; Dif 6", "Conversa claramente com aparições sem atravessar a Mortalha (V20, p. 170)."),
            np(3, "ash_3", "Mão Morta", 0, 1, "attr_raciocinio", "hab_ocultismo", 7, "1 FdV (+1 Sangue/cena extra); Dif 7", "Toca objetos e espíritos nas Terras Sombrias a partir do mundo físico (V20, p. 170)."),
            np(4, "ash_4", "Exumação", 1, 1, "attr_destreza", "hab_ocultismo", 7, "1 Sangue + 1 FdV; Dif 7/8", "Cruza fisicamente a Mortalha para adentrar ou sair das Terras Sombrias (V20, p. 170)."),
            np(5, "ash_5", "Domínio da Mortalha", 0, 2, "attr_fdv_ref", nil, 6, "2 FdV; testa FdV dif 6", "Ergue ou rebaixa a densidade local da Mortalha drasticamente (V20, p. 171)."),
        },
    },
}

local function rit(id, tradition, lvl, name, blood, wp, diff, summary)
    return {
        id = id,
        tradition = tradition,
        level = lvl,
        name = name,
        cost = { blood = blood or 0, willpower = wp or 0 },
        defaultDiff = diff or math.min(9, 3 + lvl),
        summary = summary,
    }
end

BMCatalog.RITUAL_ORDER = {
    "thau_rit_1_sacred_haven", "thau_rit_1_wake_fresheness",
    "thau_rit_2_vitae_infusion", "thau_rit_2_ward_ghouls",
    "thau_rit_3_incorporeal_passage", "thau_rit_3_ward_kindred",
    "thau_rit_4_heart_stone", "thau_rit_4_ward_spirits",
    "thau_rit_5_abandon_fetters", "thau_rit_5_blood_contract",
    "necro_rit_1_call_hungry", "necro_rit_1_eyes_grave",
    "necro_rit_2_hand_glory", "necro_rit_2_sight_shroud",
    "necro_rit_3_unearthly_chain", "necro_rit_3_skull_chalice",
    "necro_rit_4_charon_kiss", "necro_rit_4_rend_shroud",
    "necro_rit_5_grasp_ghostly", "necro_rit_5_dark_exile",
}

BMCatalog.RITUALS = {
    thau_rit_1_sacred_haven        = rit("thau_rit_1_sacred_haven",        "thaumaturgy", 1, "Defesa do Refúgio Sagrado",          1, 0, 4, "Veda aposento contra a luz solar enquanto o conjurador permanecer dentro (V20, p. 231)."),
    thau_rit_1_wake_fresheness     = rit("thau_rit_1_wake_fresheness",     "thaumaturgy", 1, "Despertar com o Frescor da Tarde",   0, 0, 4, "Permite despertar imediatamente diante de perigo diurno sem teto de Humanidade (V20, p. 233)."),
    thau_rit_2_vitae_infusion      = rit("thau_rit_2_vitae_infusion",      "thaumaturgy", 2, "Foco Principal de Infusão de Vitae", 1, 0, 5, "Condensa 1 ponto de sangue num pequeno objeto para consumo futuro (V20, p. 235)."),
    thau_rit_2_ward_ghouls         = rit("thau_rit_2_ward_ghouls",         "thaumaturgy", 2, "Proteção Contra Carniçais",          1, 0, 5, "Glifo protetor que causa 3 dados Letais a carniçais que tocarem o objeto (V20, p. 235)."),
    thau_rit_3_incorporeal_passage = rit("thau_rit_3_incorporeal_passage", "thaumaturgy", 3, "Passagem Incorpórea",                0, 0, 6, "Torna o taumaturgo imaterial por horas mediante espelho estilhaçado (V20, p. 236)."),
    thau_rit_3_ward_kindred        = rit("thau_rit_3_ward_kindred",        "thaumaturgy", 3, "Proteção Contra Membros",            1, 0, 6, "Glifo com vitae que inflige 3 dados Agravados a outros vampiros ao toque (V20, p. 237)."),
    thau_rit_4_heart_stone         = rit("thau_rit_4_heart_stone",         "thaumaturgy", 4, "Coração de Pedra",                   0, 0, 7, "Petrifica o coração conferindo proteção contra estacas (-Empatia/Consciência; V20, p. 238)."),
    thau_rit_4_ward_spirits        = rit("thau_rit_4_ward_spirits",        "thaumaturgy", 4, "Proteção Contra Espíritos",          0, 0, 7, "Selo hermético que bloqueia e fere espíritos/aparições (V20, p. 239)."),
    thau_rit_5_abandon_fetters     = rit("thau_rit_5_abandon_fetters",     "thaumaturgy", 5, "Abandonar os Grilhões",              2, 1, 8, "Rompe de forma dolorosa um Laço de Sangue existente (V20, p. 239)."),
    thau_rit_5_blood_contract      = rit("thau_rit_5_blood_contract",      "thaumaturgy", 5, "Contrato de Sangue",                 1, 0, 8, "Pacto indissolúvel escrito em vitae que pune fisicamente quem violá-lo (V20, p. 240)."),

    necro_rit_1_call_hungry        = rit("necro_rit_1_call_hungry",        "necromancy",  1, "Chamado dos Mortos Famintos",        0, 0, 4, "Permite ouvir sussurros e lamúrias através da Mortalha local (V20, p. 176)."),
    necro_rit_1_eyes_grave         = rit("necro_rit_1_eyes_grave",         "necromancy",  1, "Olhos da Sepultura",                 0, 0, 4, "Inflige visões súbitas da própria morte à vítima escolhida (V20, p. 176)."),
    necro_rit_2_hand_glory         = rit("necro_rit_2_hand_glory",         "necromancy",  2, "Mão da Glória",                      1, 0, 5, "Mão mumificada acesa que paralisa moradores adormecidos de um local (V20, p. 177)."),
    necro_rit_2_sight_shroud       = rit("necro_rit_2_sight_shroud",       "necromancy",  2, "Olhar Além da Mortalha",             0, 0, 5, "Revela se objetos ou pessoas possuem grilhões espectrais ativos (V20, p. 177)."),
    necro_rit_3_unearthly_chain    = rit("necro_rit_3_unearthly_chain",    "necromancy",  3, "Ritual da Corrente Desenterrada",    0, 0, 6, "Sintoniza osso falange para rastrear infalivelmente o grilhão de um espírito (V20, p. 178)."),
    necro_rit_3_skull_chalice      = rit("necro_rit_3_skull_chalice",      "necromancy",  3, "Cálice de Crânio",                   1, 0, 6, "Compartilha percepção sensorial ou absorve maldições via crânio preparado (V20, p. 179)."),
    necro_rit_4_charon_kiss        = rit("necro_rit_4_charon_kiss",        "necromancy",  4, "Ósculo de Caronte",                  1, 0, 7, "Garante que um mortal prestes a morrer se torne uma aparição após o óbito (V20, p. 180)."),
    necro_rit_4_rend_shroud        = rit("necro_rit_4_rend_shroud",        "necromancy",  4, "Rasgar a Mortalha",                  1, 1, 7, "Reduz temporariamente a barreira da Mortalha facilitando travessias e invocações (V20, p. 181)."),
    necro_rit_5_grasp_ghostly      = rit("necro_rit_5_grasp_ghostly",      "necromancy",  5, "Aperto Fantasmagórico",              0, 1, 8, "Traz um objeto das Terras Sombrias como relíquia sólida para o mundo material (V20, p. 182)."),
    necro_rit_5_dark_exile         = rit("necro_rit_5_dark_exile",         "necromancy",  5, "Exílio Sombrio",                     2, 1, 8, "Arremessa temporariamente uma vítima para as Terras Sombrias (V20, p. 183)."),
}

return BMCatalog
```

Criar `Core/blood_magic_engine.lua`:
```lua
local BMCat = require("Data.blood_magic_catalog")
local Blood = require("Core.generation_blood")
local WM = require("Core.willpower_morality")

local BMEngine = {}

local function copyState(s)
    local o = {}
    for k, v in pairs(s or {}) do o[k] = v end
    return o
end

local function safeNonNegInt(v, default)
    local n = tonumber(v)
    if n == nil or n ~= n or n == math.huge or n == -math.huge then return default or 0 end
    n = math.floor(n)
    return n < 0 and 0 or n
end

function BMEngine.derivePrimaryPathLevel(discDots)
    return math.min(5, safeNonNegInt(discDots, 0))
end

function BMEngine.validateSecondaryPathUpgrade(params)
    params = params or {}
    local parentDots = safeNonNegInt(params.parentDiscDots, 0)
    local target = safeNonNegInt(params.targetLevel, 1)
    local primId = params.primaryPathId or ""
    local secId = params.secondaryPathId or ""

    if secId == "" then
        return { ok = false, error = "Selecione uma Linha Secundária válida antes de evoluir." }
    end
    if primId ~= "" and primId == secId then
        return { ok = false, error = "A Linha Secundária não pode ser idêntica à Linha Primária." }
    end
    if target > 5 then
        return { ok = false, error = "Linhas de Taumaturgia/Necromancia têm nível máximo 5." }
    end
    if target >= 1 and parentDots < 2 then
        return { ok = false, error = "Exige nível mínimo 2 na Linha Primária/Disciplina para iniciar Linha Secundária (V20, p. 212)." }
    end
    local primLvl = BMEngine.derivePrimaryPathLevel(parentDots)
    if primLvl < 5 and target >= primLvl then
        return { ok = false, error = string.format("Linha Secundária (%d) deve permanecer inferior à Linha Primária (%d) até que a Primária atinja 5 (V20, p. 212).", target, primLvl) }
    end
    return { ok = true, error = nil }
end

function BMEngine.getPathTable(tradition, pathId)
    if tradition == "necromancy" then
        return BMCat.NECROMANCY_PATHS[pathId]
    end
    return BMCat.THAUMATURGY_PATHS[pathId]
end

function BMEngine.activatePathPower(state, tradition, pathId, pathDots, level, opts)
    opts = opts or {}
    local pTable = BMEngine.getPathTable(tradition, pathId)
    if not pTable then
        return { ok = false, newState = copyState(state), rollSpec = nil, error = "Linha de Magia do Sangue não encontrada." }
    end
    local lvl = math.max(1, math.min(5, safeNonNegInt(level, 1)))
    local dots = safeNonNegInt(pathDots, 0)
    if dots < lvl and not opts.storytellerOverride then
        return { ok = false, newState = copyState(state), rollSpec = nil, error = string.format("Nível insuficiente na %s (possui %d, requer %d).", pTable.name, dots, lvl) }
    end

    local power = pTable.powers[lvl]
    local nextSt = copyState(state)
    local bCost = safeNonNegInt(power.cost and power.cost.blood, 0)
    local wCost = safeNonNegInt(power.cost and power.cost.willpower, 0)

    if bCost > 0 then
        local bRes = Blood.spend(nextSt, bCost, {
            forDisciplineOrHeal = true,
            bypassTurnLimit = (opts.bypassTurnLimit == true),
            storytellerOverride = opts.storytellerOverride,
        })
        if not bRes.ok then
            return { ok = false, newState = copyState(state), rollSpec = nil, error = bRes.error }
        end
        nextSt = bRes.newState
    end

    if wCost > 0 then
        local wRes = WM.spendWillpower(nextSt, wCost, { storytellerOverride = opts.storytellerOverride })
        if not wRes.ok then
            return { ok = false, newState = copyState(state), rollSpec = nil, error = wRes.error }
        end
        nextSt = wRes.newState
    end

    return {
        ok = true,
        newState = nextSt,
        rollSpec = power.pool and {
            powerName = pTable.name .. " — " .. power.name,
            attr = power.pool.attr,
            hab = power.pool.hab,
            defaultDiff = power.defaultDiff or 6,
            diffHint = power.diffHint or "",
        } or nil,
        error = nil,
    }
end

function BMEngine.castRitual(state, ritualIdOrCustom, parentDiscDots, opts)
    opts = opts or {}
    local rit = type(ritualIdOrCustom) == "table" and ritualIdOrCustom or BMCat.RITUALS[ritualIdOrCustom]
    if not rit then
        return { ok = false, newState = copyState(state), rollSpec = nil, error = "Ritual não encontrado no grimório." }
    end
    local reqLvl = math.max(1, safeNonNegInt(rit.level, 1))
    local haveDots = safeNonNegInt(parentDiscDots, 0)
    if haveDots < reqLvl and not opts.storytellerOverride then
        return {
            ok = false,
            newState = copyState(state),
            rollSpec = nil,
            error = string.format("Conhecimento insuficiente na disciplina para conjurar '%s' (requer nível %d, possui %d).", rit.name or "Ritual", reqLvl, haveDots),
        }
    end

    local nextSt = copyState(state)
    local bCost = safeNonNegInt(rit.cost and rit.cost.blood, 0)
    local wCost = safeNonNegInt(rit.cost and rit.cost.willpower, 0)

    if bCost > 0 then
        local bRes = Blood.spend(nextSt, bCost, {
            forDisciplineOrHeal = true,
            bypassTurnLimit = true,
            storytellerOverride = opts.storytellerOverride,
        })
        if not bRes.ok then
            return { ok = false, newState = copyState(state), rollSpec = nil, error = bRes.error }
        end
        nextSt = bRes.newState
    end

    if wCost > 0 then
        local wRes = WM.spendWillpower(nextSt, wCost, { storytellerOverride = opts.storytellerOverride })
        if not wRes.ok then
            return { ok = false, newState = copyState(state), rollSpec = nil, error = wRes.error }
        end
        nextSt = wRes.newState
    end

    return {
        ok = true,
        newState = nextSt,
        rollSpec = {
            powerName = "Ritual: " .. (rit.name or "Customizado"),
            attr = "attr_inteligencia",
            hab = "hab_ocultismo",
            defaultDiff = safeNonNegInt(rit.defaultDiff, math.min(9, 3 + reqLvl)),
            diffHint = rit.summary or "",
        },
        error = nil,
    }
end

function BMEngine.hasBloodMagicAccess(clanId, disciplinesList, ritualsBgDots)
    if clanId == "tremere" or clanId == "giovanni" then
        return true
    end
    if safeNonNegInt(ritualsBgDots, 0) >= 1 then
        return true
    end
    for _, d in ipairs(disciplinesList or {}) do
        if (d.disc_id == "thaumaturgy" or d.disc_id == "necromancy") and safeNonNegInt(d.nivel, 0) >= 1 then
            return true
        end
    end
    return false
end

return BMEngine
```

Atualizar `Core/v20_init.lua` atribuindo `V20.BloodMagicCatalog` e `V20.BloodMagicEngine`.

- [ ] **Step 4: Rodar os testes e confirmar aprovação**

Executar: `python Tests/run_tests.py Tests/test_11_blood_magic.lua` e `python Tests/run_tests.py`  
Resultado esperado: `[PASS] Tests\test_11_blood_magic.lua` e todas as suítes aprovadas.

- [ ] **Step 5: Commit**

```bash
git add Data/blood_magic_catalog.lua Core/blood_magic_engine.lua Core/v20_init.lua Tests/test_11_blood_magic.lua
git commit -m "feat(core): add V20 Thaumaturgy/Necromancy 9 paths, 20 rituals and secondary path engine"
```

---

### Task 3: Integração `Adapter/firecast_bridge.lua` e Gerador LFM dos 14 Clãs + Aba 8 Dinâmica

**Files:**
- Modify: `Adapter/firecast_bridge.lua`
- Modify: `Templates/theme_gothic.py`
- Modify: `Templates/generate_vampire_lfm.py`
- Modify: `Templates/generate_mortal_lfm.py` (se `all_xp_upgradable_field_options` for estendido)
- Create/Update (generated): `Sheets/frmBrujah.lfm` .. `Sheets/frmCaitiff.lfm` (14 arquivos) + `Sheets/frmMortal.lfm`
- Modify Test: `Tests/test_08_bridge_and_lfm_gen.py`

**Interfaces:**
- Consumes: `Core/clan_weaknesses.lua`, `Core/blood_magic_engine.lua`, `Data/blood_magic_catalog.lua`
- Produces:
  - Integração automática de `ClanWeaknesses` em `Bridge.rollFromSheet` (`blocked`, `bonusDiceMod`, `diffMod`, `poolDivisor`), `Bridge.applyDamage` (`dano_fonte_solar`), `Bridge.huntWithHerdDomain` (Ventrue & Giovanni), `Bridge.validateCreationOnSheet` (Nosferatu Social `-2`, campos obrigatórios Malkavian/Ventrue/Ravnos e Linhas Secundárias) e `Bridge.clearSceneBuffs` (limpa `malkav_suprimida_cena` e `toreador_fascinado_cena`);
  - Handlers de 1 clique na `Bridge`: `endBrujahFrenzy`, `recordGangrelFrenzy`, `suppressMalkavianDerangement`, `rollToreadorFascination`, `recordTremereDrink`, `ingestAssamiteVitae`, `applyGiovanniKiss`, `rollRavnosVice`, `resetTzimisceSoil`, `activatePrimaryBloodMagic`, `activateSecondaryBloodMagic`, `castCatalogRitual`, `castCustomRitual`, `hasBloodMagicAccess`;
  - Evolução por XP suportando `bm_sec1_nivel..bm_sec4_nivel` (`traitKind = "secondary_path"`, validado via `BloodMagicEngine.validateSecondaryPathUpgrade`);
  - `Templates/generate_vampire_lfm.py --all-clans` gerando os 14 arquivos `Sheets/frm<Clan>.lfm`, cada um com:
    - Painel específico da fraqueza do seu clã na Aba 6;
    - Checkbox `dano_fonte_solar` (`Luz Solar`) na Aba 5;
    - Aba 8 `tabMagiaSangue` (`name="tabMagiaSangue"`, `visible="true"` em Tremere/Giovanni e `visible="false"` inicial nos demais, alternada dinamicamente em `atualizarPermissoesModo(self)` via `V20Bridge.hasBloodMagicAccess(sheet)`, voltando `self.pgcPrincipal:setTabIndex(0)` caso ocultada enquanto ativa).

- [ ] **Step 1: Atualizar `Tests/test_08_bridge_and_lfm_gen.py` com testes falhos das 15 fichas, fraquezas e Magia do Sangue**

Adicionar em `Tests/test_08_bridge_and_lfm_gen.py`:
- Execução de `generate_vampire_lfm.py --all-clans` verificando existência, `dataType`, `formName`, nomes únicos de controles, compilação `.lfm.lua` e validação `lua54x64.dll` de **todos os 15 arquivos `.lfm`**;
- Verificação de que `frmTremere.lfm` e `frmGiovanni.lfm` têm `tabMagiaSangue` visível por padrão e as outras 12 fichas iniciam `visible="false"` com controle dinâmico em `atualizarPermissoesModo`;
- Testes Lua em `lua54x64.dll` exercitando via `V20Bridge`:
  1. Criação válida de Nosferatu `7/5/3` com `attr_aparencia = 0` + falha automática em `rollFromSheet` de Aparência + sucesso quando `obf_mask` está ativo;
  2. Tzimisce com `tzimisce_dias_sem_terra = 2` dividindo parada de 8 dados para 2 dados (`8 / 4 = 2`) em `rollFromSheet`;
  3. Setita recebendo `+2` níveis Agravados com `dano_fonte_solar = true` em `applyDamage` e `-1 dado` com `setita_luz_forte = true`;
  4. Caitiff pagando `Atual × 6` XP em qualquer disciplina e sofrendo `+2 dif` social com `caitiff_estigma_ativo = true`;
  5. Brujah adquirindo `thaumaturgy` Nv 2 -> `hasBloodMagicAccess(sheet) == true`, comprando `bm_sec1_nivel` (`0 -> 1` por `7 XP`) via `submitOrApproveXP` e bloqueando compra `1 -> 2` enquanto Taumaturgia primária estiver em `2`!

- [ ] **Step 2: Rodar o teste para confirmar falha**

Executar: `python Tests/run_tests.py Tests/test_08_bridge_and_lfm_gen.py`  
Resultado esperado: `FAIL` (`--all-clans` e métodos de fraqueza/magia ainda ausentes).

- [ ] **Step 3: Implementar as extensões em `Adapter/firecast_bridge.lua`, `Templates/theme_gothic.py` e `Templates/generate_vampire_lfm.py` e gerar as 15 fichas**

Pontos-chave de implementação em `Adapter/firecast_bridge.lua`:
```lua
-- Em Bridge.rollFromSheet: consultar ClanWeaknesses.computeRollModifiers
local cwMods = V20.ClanWeaknesses.computeRollModifiers({
    cla_id = sheet.cla_id,
    attrId = attrId,
    habId = habId,
    activeBuffs = getBuffTable(sheet),
    setita_luz_forte = sheet.setita_luz_forte,
    lasombra_vigiado_espelhos = sheet.lasombra_vigiado_espelhos,
    caitiff_estigma_ativo = sheet.caitiff_estigma_ativo,
    tzimisce_dias_sem_terra = sheet.tzimisce_dias_sem_terra,
    storytellerOverride = stOverride,
})
if cwMods.blocked then
    dlg.showMessage(cwMods.blockReason)
    return { ok = false, error = cwMods.blockReason }
end
-- Aplicar cwMods.bonusDiceMod e cwMods.diffMod em Dice.buildPool;
-- e se cwMods.poolDivisor > 1 e poolInfo.pool >= 1:
-- poolInfo.pool = math.max(1, math.floor(poolInfo.pool / cwMods.poolDivisor))
```

Pontos-chave em `Templates/theme_gothic.py` (`build_mode_permissions_lua`):
```lua
-- Controle dinâmico da 8ª aba nas fichas vampíricas:
if self.tabMagiaSangue ~= nil then
    local mostrarBM = (V20Bridge ~= nil and V20Bridge.hasBloodMagicAccess ~= nil and V20Bridge.hasBloodMagicAccess(s)) or false
    if (not mostrarBM) and self.pgcPrincipal ~= nil and self.pgcPrincipal.getTabIndex ~= nil and self.pgcPrincipal:getTabIndex() == 7 then
        self.pgcPrincipal:setTabIndex(0)
    end
    self.tabMagiaSangue:setVisible(mostrarBM)
end
```

Executar `python Templates/generate_vampire_lfm.py --all-clans` e `python Templates/generate_mortal_lfm.py` para gravar todas as 15 fichas em `Sheets/`.

- [ ] **Step 4: Rodar os testes e confirmar aprovação**

Executar: `python Tests/run_tests.py Tests/test_08_bridge_and_lfm_gen.py` e `python Tests/run_tests.py`  
Resultado esperado: `[PASS] Tests\test_08_bridge_and_lfm_gen.py` com as 15 fichas compilando na `lua54x64.dll`.

- [ ] **Step 5: Commit**

```bash
git add Adapter/firecast_bridge.lua Templates/ Sheets/ Tests/test_08_bridge_and_lfm_gen.py
git commit -m "feat(ui): integrate 14 clan weaknesses, dynamic Blood Magic tab and generate all 15 LFM sheets"
```

---

### Task 4: Empacotamento `v0.6.0` das 15 Fichas (`module.xml`, `tools/build_v20_suite.py`) e Auditoria E2E Completa

**Files:**
- Modify: `module.xml`
- Modify: `tools/build_v20_suite.py`
- Modify: `Tests/test_09_rpk_package.py`
- Update (generated): `dist/Vampiro_V20_Suite.rpk`, `dist/Vampiro_V20_Suite.rdk`

**Interfaces:**
- Consumes: `Data/*.lua`, `Core/*.lua`, `Adapter/*.lua`, `Sheets/frm*.lfm` (15 formulários)
- Produces:
  - `dist/Vampiro_V20_Suite.rpk` (`v0.6.0`) registrando exatamente os **15 `<dataType>`** na ordem oficial (`br.com.v20.Brujah` .. `br.com.v20.Caitiff` + `br.com.v20.Mortal`), validados sintaticamente e em execução dentro da `lua54x64.dll`.

- [ ] **Step 1: Atualizar `Tests/test_09_rpk_package.py` para exigir versão `0.6.0` e as 15 fichas completas no `.rpk`**

Atualizar `Tests/test_09_rpk_package.py`:
- Exigir `<version>0.6.0</version>` em `module.xml` assemblado;
- Exigir os 15 IDs `dataType` (`br.com.v20.Brujah`, `br.com.v20.Gangrel`, `br.com.v20.Malkavian`, `br.com.v20.Nosferatu`, `br.com.v20.Toreador`, `br.com.v20.Tremere`, `br.com.v20.Ventrue`, `br.com.v20.Assamite`, `br.com.v20.Setite`, `br.com.v20.Giovanni`, `br.com.v20.Lasombra`, `br.com.v20.Ravnos`, `br.com.v20.Tzimisce`, `br.com.v20.Caitiff`, `br.com.v20.Mortal`) tanto em `./dataTypes/dataType` quanto em `./assembledFeatures/dataTypes/dataType`;
- Exigir `Data/blood_magic_catalog.lua`, `Core/clan_weaknesses.lua` e `Core/blood_magic_engine.lua` (com prefixo `require("v20_shim.dlua"); ` nos módulos `Core/`) dentro do `.rpk`;
- Executar o auto-boot alfabético VHD e instanciar, vincular ficha `[TESTE_E2E]`, disparar eventos e destruir em ordem reversa **todos os 15 formulários (`newfrmBrujah()` .. `newfrmMortal()`)** dentro da `lua54x64.dll`!

- [ ] **Step 2: Rodar o teste para confirmar falha**

Executar: `python Tests/run_tests.py Tests/test_09_rpk_package.py`  
Resultado esperado: `FAIL` (`module.xml` ainda em `0.2.0` e apenas 2 `dataTypes` empacotados).

- [ ] **Step 3: Atualizar `module.xml` e `tools/build_v20_suite.py` e construir `dist/Vampiro_V20_Suite.rpk`**

Atualizar `module.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<module sdkVersion="3.7b">
    <id>br.com.v20.suite</id>
    <version>0.6.0</version>
    <info lang="pt-BR">
        <name>Vampiro: A Máscara V20 — Suíte Oficial Completa (15 Modelos)</name>
        <description>Ecossistema automatizado completo para Vampiro: A Máscara Edição de 20º Aniversário (V20): 13 Clãs Tradicionais + Caitiff + Ficha Mortal (Carniçal/Numina), fraquezas de clã automatizadas, 17 Disciplinas (de clã e fora do clã), 9 Linhas e 20 Rituais de Taumaturgia/Necromancia, Antecedentes interativos, Gerações 4ª-15ª e XP auditado.</description>
        <author>Carlos Leandro</author>
        <site>https://firecast.app</site>
        <contact>Mestre Carlos</contact>
    </info>
</module>
```

Atualizar `tools/build_v20_suite.py`:
```python
CLAN_FORM_FILES = [
    "Sheets/frmBrujah.lfm",
    "Sheets/frmGangrel.lfm",
    "Sheets/frmMalkavian.lfm",
    "Sheets/frmNosferatu.lfm",
    "Sheets/frmToreador.lfm",
    "Sheets/frmTremere.lfm",
    "Sheets/frmVentrue.lfm",
    "Sheets/frmAssamite.lfm",
    "Sheets/frmSetite.lfm",
    "Sheets/frmGiovanni.lfm",
    "Sheets/frmLasombra.lfm",
    "Sheets/frmRavnos.lfm",
    "Sheets/frmTzimisce.lfm",
    "Sheets/frmCaitiff.lfm",
]
LFM_ENTRIES = CLAN_FORM_FILES + ["Sheets/frmMortal.lfm"]
```
E invocar `generate_vampire_lfm.py --all-clans` antes da compilação e auditoria dos 15 `.lfm.lua`.

- [ ] **Step 4: Executar toda a suíte de testes (`test_01` a `test_11`)**

Executar: `python Tests/run_tests.py`  
Resultado esperado: Todas as **11 suítes** reportando `[PASS]` e `dist/Vampiro_V20_Suite.rpk` (`v0.6.0`) pronto!

- [ ] **Step 5: Commit**

```bash
git add module.xml tools/build_v20_suite.py Tests/test_09_rpk_package.py dist/Vampiro_V20_Suite.rpk dist/Vampiro_V20_Suite.rdk
git commit -m "build(rpk): package all 15 V20 sheet models into Vampiro_V20_Suite v0.6.0"
```
