# Vampiro V20 Firecast Suite (Subproject 3 — Assisted Combat Maneuvers & Storyteller Coterie TablesDock `v1.0.0`) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Concluir a versão `1.0.0` de `dist/Vampiro_V20_Suite.rpk` adicionando o subsistema completo de **Manobras Avançadas de Combate Assistido V20** (Divisão de Paradas pela menor parada vs. Rapidez, 20 manobras oficiais, cobertura/mira/localizado e encadeamento *Ataque → Sucessos Líquidos → Parada Exata de Dano*) nas 15 fichas e o **16º formulário `formType="tablesDock"` (`frmV20CoterieDock`)** de Coterie & Iniciativa em duas camadas (Visão Pública segura na sala + Painel Exclusivo do Narrador com cartões paginados e ações em lote), além dos polimentos finais de `v0.6.0`.

**Architecture:** Dois novos motores puros desacoplados de UI em `Core/` (`Core/combat_maneuvers.lua` apoiado por `Data/combat_maneuvers_catalog.lua`, e `Core/coterie_tracker.lua`), integrados em `Core/v20_init.lua`; expansão de `Adapter/firecast_bridge.lua` e `Templates/` para o Estúdio de Manobras na Aba 5 das 15 fichas e unificação Aba 3 ↔ Aba 8 de Magia do Sangue; novo adaptador `Adapter/coterie_dock_bridge.lua` e gerador `Templates/generate_coterie_dock_lfm.py` produzindo `Sheets/frmV20CoterieDock.lfm`; e atualização de `tools/build_v20_suite.py` com `--output-dir`, compilação de `<event>` raiz em `<form>`, gancho `_onBeforeDestroy` e registro `Firecast.registrarSpecialForm` para `tablesDock`.

**Tech Stack:** Lua 5.4 (`C:\Users\Cliente\AppData\Local\Firecast\lua54x64.dll`), RRPG Firecast SDK 3.7b (`sdkApiVersion="88"`, `sdkMinorApiVersion="2"`), Python 3.x.

**Spec:** `docs/superpowers/specs/2026-11-17-v20-firecast-subproject3-design.md`

## Global Constraints

- **Referência Mecânica Exclusiva:** *Vampire: The Masquerade — 20th Anniversary Edition (V20 Corebook)*.
- **Idioma:** Português Brasileiro (`pt-BR`) na interface e mensagens; IDs internos em ASCII.
- **Isolamento de Sandbox em Testes (`[TESTE_E2E]`):** Qualquer personagem, combatente, sala, arquivo temporário ou registro criado em `Tests/` DEVE conter obrigatoriamente o prefixo `[TESTE_E2E]` em seu nome/título e limpar diretórios/arquivos temporários em blocos `finally:`.
- **Regras Estritas Firecast SDK 3.7b:**
  1. Usar apenas tags nativas suportadas pelo compilador (`form`, `script`, `tabControl`, `tab`, `scrollBox`, `layout`, `rectangle`, `label`, `edit`, `comboBox`, `checkBox`, `button`, `textEditor`, `dataLink`, `event`), **sem** `<recordList>` ou `<template>`;
  2. Todos os `<dataLink>` filhos diretos de `<form>`;
  3. `horzTextAlign` e `vertTextAlign` estritamente `"leading"`, `"center"` ou `"trailing"`;
  4. `rawset(obj, "_oldSetNodeObjectFunction", obj.setNodeObject);` e `cacheMode = "none"`;
  5. Em formulários `formType="tablesDock"`, o `.lfm.lua` compilado DEVE chamar `Firecast.registrarForm(...)`, `Firecast.registrarDataType(...)` **e** `Firecast.registrarSpecialForm(...)`;
  6. Nomes (`name="..."`) únicos por formulário `.lfm`;
  7. Prefixar `require("v20_shim.dlua"); ` na linha 1 de todos os arquivos `Core/*.lua` e `Adapter/*.lua` empacotados no `.rpk` para garantir boot alfabético VHD seguro (atenção: `/Adapter/coterie_dock_bridge.lua` ordena alfabeticamente antes de `/Adapter/firecast_bridge.lua`, portanto não criar `require` circular no topo de módulo entre os dois adaptadores);
  8. Direitos autorais: resumos mecânicos próprios concisos + citação de página V20, sem cópia literal.

---

## Mapa de Arquivos do Subprojeto 3

- Create: `Data/combat_maneuvers_catalog.lua` — catálogo declarativo das 20 manobras V20 (`brawl`, `melee`, `ranged`, `defense`), localizações de golpe (`TARGET_LOCATIONS`), níveis de cobertura (`COVER_LEVELS`) e flanco (`FLANK_MODES`).
- Create: `Core/combat_maneuvers.lua` — cálculo puro de divisão de paradas pela menor parada (V20 p. 248) vs. Rapidez (p. 142), montagem de ataque/defesa tática, cálculo encadeado de dano pós-ataque com *Potência* passiva/automática, desarme e paralisia por estaca.
- Create: `Core/coterie_tracker.lua` — ordenação oficial de Iniciativa V20 (`declaracao` ascendente vs. `acao` descendente com desempate por modificador), filtro estrito anti-metajogo para visão pública vs. cartões paginados do Narrador (`8` por página).
- Modify: `Core/v20_init.lua` — expor `CombatManeuversCatalog`, `CombatManeuvers` e `CoterieTracker` idempotentemente em `_G.V20`.
- Modify: `Adapter/firecast_bridge.lua` — adicionar `executeCombatManeuver`, `rollPendingCombatDamage`, reset de defesas/agarrão em `newTurn`/`clearSceneBuffs`, hook de publicação de Iniciativa para o Dock e delegação Aba 3 ↔ Aba 8 para `thaumaturgy`/`necromancy`.
- Create: `Adapter/coterie_dock_bridge.lua` — ciclo de vida `connectDock`/`disconnectDock` com limpeza total de `NDB.newObserver`, sincronização `v20_coterie_dock_v1`, inspeção recursiva de `mesa.biblioteca` (`br.com.v20.*`), ações rápidas por cartão e comandos em lote do Narrador.
- Modify: `v20_loader.lua` — carregar `Adapter.coterie_dock_bridge` no boot padrão.
- Modify: `Templates/theme_gothic.py`, `Templates/generate_vampire_lfm.py`, `Templates/generate_mortal_lfm.py` & regerar as 15 fichas `Sheets/frm*.lfm` — Estúdio de Manobras V20 + barra de Dano Encadeado na Aba 5 e destravamento inteligente de `cmbBmThauPrimId`/`cmbBmNecroPrimId` em nível `0`.
- Create: `Templates/generate_coterie_dock_lfm.py` & `Sheets/frmV20CoterieDock.lfm` — 16º formulário acoplável `tablesDock`.
- Modify: `module.xml` (`1.0.0`) & `tools/build_v20_suite.py` — flag `--output-dir`, suporte a `<event>` raiz em `<form>`, `_onBeforeDestroy`, `Firecast.registrarSpecialForm` para `tablesDock` e build dos 16 formulários.
- Create/Modify Tests: `Tests/test_12_combat_maneuvers.lua`, `Tests/test_13_coterie_tracker.lua`, `Tests/test_08_bridge_and_lfm_gen.py`, `Tests/test_09_rpk_package.py`.

---

### Task 1: Catálogo e Motor Puro de Manobras de Combate Assistido V20 (`Data/combat_maneuvers_catalog.lua` + `Core/combat_maneuvers.lua`)

**Files:**
- Create: `Data/combat_maneuvers_catalog.lua`
- Create: `Core/combat_maneuvers.lua`
- Modify: `Core/v20_init.lua`
- Test: `Tests/test_12_combat_maneuvers.lua`

**Interfaces:**
- Consumes: nenhum módulo de UI (100% Lua puro).
- Produces:
  - `Data/combat_maneuvers_catalog.lua`:
    - `MANEUVERS[id]` com todas as **20 manobras** exatas da Spec (`strike`, `kick`, `bite`, `claw`, `clinch`, `hold`, `tackle`, `sweep_brawl`, `disarm_brawl`, `weapon_strike`, `stake_heart`, `disarm_melee`, `sweep_melee`, `single_shot`, `double_tap`, `three_round_burst`, `full_auto`, `dodge`, `block`, `parry`);
    - `MANEUVER_ORDER` (lista ordenada dos 20 IDs);
    - `TARGET_LOCATIONS` (`nenhum`, `membro`, `cabeca`), `COVER_LEVELS` (`nenhuma`, `leve`, `boa`, `superior`), `FLANK_MODES` (`frontal`, `flanco`, `retaguarda`).
  - `Core/combat_maneuvers.lua`:
    - `CombatManeuvers.computeSplitPool(ownPool, totalNormalActions, actionNumber, lowestBasePool, isCelerityAction)` -> `{ poolAfterSplit = number, splitPenalty = number, usedBase = number, bypassedByCelerity = boolean }`
    - `CombatManeuvers.prepareManeuverRoll(ctx)` -> `{ canRoll = boolean, reason = string|nil, maneuverId = string, maneuverName = string, category = string, isDefense = boolean, noDamage = boolean, poolBeforeClanDivisor = number, difficulty = number, splitPenalty = number, consumeCelerityAction = boolean, setsGrappleOnHit = boolean, isDisarm = boolean, isStaking = boolean, isHeadshot = boolean, baseDamage = number, extraTargetedDice = number, damageType = string, notes = string[] }`
    - `CombatManeuvers.computePostAttackDamage(params)` -> `{ hit = boolean, netHits = number, carryOverDice = number, noDamage = boolean, damageDicePool = number, autoSuccesses = number, damageDifficulty = 6, damageType = string, isHeadshot = boolean, isStaking = boolean, setsGrapple = boolean, disarm = { attempted = boolean, disarmed = boolean, botchedSelf = boolean }|nil, summary = string }`
    - `CombatManeuvers.checkStakingParalyze(finalDamageLevels, isVampireTarget)` -> `{ paralyzed = boolean, message = string|nil }`
  - `Core/v20_init.lua`: registra `V20.CombatManeuversCatalog` e `V20.CombatManeuvers`.

- [ ] **Step 1: Escrever o teste falho `Tests/test_12_combat_maneuvers.lua`**

```lua
local V20 = require("Core.v20_init")
local Cat = require("Data.combat_maneuvers_catalog")
local CM = require("Core.combat_maneuvers")

assert(V20.CombatManeuversCatalog == Cat)
assert(V20.CombatManeuvers == CM)
assert(#Cat.MANEUVER_ORDER == 20, "Esperadas 20 manobras oficiais V20")
for _, id in ipairs(Cat.MANEUVER_ORDER) do
    local m = Cat.MANEUVERS[id]
    assert(m ~= nil and m.id == id and type(m.name) == "string" and type(m.page) == "string", "Manobra inválida: " .. tostring(id))
end

-- 1. Divisão de paradas pela menor parada (V20, p. 248) vs Ação de Rapidez (p. 142)
local sp1 = CM.computeSplitPool(7, 2, 1, 5, false)
assert(sp1.usedBase == 5 and sp1.splitPenalty == 2 and sp1.poolAfterSplit == 3 and sp1.bypassedByCelerity == false)
local sp2 = CM.computeSplitPool(7, 2, 2, 5, false)
assert(sp2.usedBase == 5 and sp2.splitPenalty == 3 and sp2.poolAfterSplit == 2)
local spCel = CM.computeSplitPool(7, 3, 2, 4, true)
assert(spCel.poolAfterSplit == 7 and spCel.splitPenalty == 0 and spCel.bypassedByCelerity == true)

-- Quando a divisão zera ou negativa a parada, V20 p. 248 bloqueia a ação
local zeroSplit = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Neófito Lento",
    isVampire = true,
    maneuverId = "strike",
    attrs = { attr_destreza = 2, attr_forca = 2, attr_percepcao = 2 },
    habs = { hab_briga = 1 },
    totalNormalActions = 3,
    actionNumber = 1,
    lowestBasePool = 3,
})
assert(zeroSplit.canRoll == false and type(zeroSplit.reason) == "string")

-- 2. Mordida vampírica exige Agarrão prévio (salvo storytellerOverride), +1 precisão e dano Força+1 Agravado
local biteBlocked = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Brujah",
    isVampire = true,
    maneuverId = "bite",
    inGrapple = false,
    attrs = { attr_destreza = 3, attr_forca = 3 },
    habs = { hab_briga = 3 },
})
assert(biteBlocked.canRoll == false)

local biteOk = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Brujah",
    isVampire = true,
    maneuverId = "bite",
    inGrapple = true,
    attrs = { attr_destreza = 3, attr_forca = 3 },
    habs = { hab_briga = 3 },
})
assert(biteOk.canRoll == true and biteOk.poolBeforeClanDivisor == 7 and biteOk.difficulty == 6)
assert(biteOk.baseDamage == 4 and biteOk.damageType == "aggravated")

-- Mortal usando bite não ganha +1 dado vampírico nem dano agravado
local biteMortal = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Mortal",
    isVampire = false,
    maneuverId = "bite",
    inGrapple = true,
    attrs = { attr_destreza = 3, attr_forca = 2 },
    habs = { hab_briga = 2 },
})
assert(biteMortal.canRoll == true and biteMortal.poolBeforeClanDivisor == 5 and biteMortal.damageType == "lethal")

-- 3. Garras: Agravado com Metamorfose 2 (naturalAggravated), Letal caso contrário
local clawAgg = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Gangrel",
    isVampire = true,
    maneuverId = "claw",
    naturalAggravated = true,
    attrs = { attr_destreza = 4, attr_forca = 3 },
    habs = { hab_briga = 3 },
})
assert(clawAgg.canRoll == true and clawAgg.damageType == "aggravated" and clawAgg.baseDamage == 4)

local clawLethal = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Gangrel Sem Garras",
    isVampire = true,
    maneuverId = "claw",
    naturalAggravated = false,
    attrs = { attr_destreza = 4, attr_forca = 3 },
    habs = { hab_briga = 3 },
})
assert(clawLethal.canRoll == true and clawLethal.damageType == "lethal")

-- 4. Estaca no Coração: dificuldade mínima fixa 9 mesmo com flanco/retaguarda, e paralisia em >= 3 níveis
local stake = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Caçador",
    isVampire = true,
    maneuverId = "stake_heart",
    flankMode = "retaguarda",
    attrs = { attr_destreza = 4, attr_forca = 3 },
    habs = { hab_armas_brancas = 3 },
    weapon = { dano = 1, dif = 6, tipo = "lethal", hab = "hab_armas_brancas" },
})
assert(stake.canRoll == true and stake.difficulty == 9 and stake.isStaking == true and stake.baseDamage == 4)
assert(CM.checkStakingParalyze(2, true).paralyzed == false)
assert(CM.checkStakingParalyze(3, true).paralyzed == true)
assert(CM.checkStakingParalyze(4, false).paralyzed == false)

-- 5. Armas de fogo: Rajada Curta (+2d, +1 dif), Rajada Completa (+10d, +2 dif), Mira limitada à Percepção (+1 luneta), Cabeça Letal
local burst = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Toreador Atirador",
    isVampire = true,
    maneuverId = "three_round_burst",
    coverLevel = "boa",
    attrs = { attr_destreza = 3, attr_forca = 4, attr_percepcao = 2 },
    habs = { hab_armas_fogo = 3 },
    weapon = { nome = "[TESTE_E2E] Submetralhadora", attr = "attr_destreza", hab = "hab_armas_fogo", dif = 6, dano = 4, tipo = "lethal" },
})
-- pool: 3 + 3 + 2 (rajada) = 8; dif: 6 + 1 (rajada) + 2 (cobertura boa) = 9; dano base arma de fogo NÃO soma Força (= 4)
assert(burst.canRoll == true and burst.poolBeforeClanDivisor == 8 and burst.difficulty == 9 and burst.baseDamage == 4)

local aimedHead = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Sniper",
    isVampire = true,
    maneuverId = "single_shot",
    aimTurns = 5,
    hasScope = true,
    targetLocation = "cabeca",
    attrs = { attr_destreza = 3, attr_forca = 2, attr_percepcao = 3 },
    habs = { hab_armas_fogo = 2 },
    weapon = { nome = "[TESTE_E2E] Rifle", attr = "attr_destreza", hab = "hab_armas_fogo", dif = 6, dano = 8, tipo = "bashing" },
})
-- Mira limitada a Percepção (3) + 1 (luneta) = +4 dados -> 3 + 2 + 4 = 9; Cabeça: +2 dif (8), +1 dado dano extra, Letal
assert(aimedHead.poolBeforeClanDivisor == 9 and aimedHead.difficulty == 8 and aimedHead.isHeadshot == true)
assert(aimedHead.extraTargetedDice == 1 and aimedHead.damageType == "lethal")

local fullAuto = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Brujah Metralhadora",
    isVampire = true,
    maneuverId = "full_auto",
    attrs = { attr_destreza = 3, attr_forca = 3 },
    habs = { hab_armas_fogo = 2 },
    weapon = { dif = 6, dano = 5, tipo = "bashing", hab = "hab_armas_fogo" },
})
assert(fullAuto.poolBeforeClanDivisor == 15 and fullAuto.difficulty == 8)

-- 6. Defesas ativas cumulativas (-1 dado por defesa prévia no turno)
local def2 = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Defensor",
    isVampire = true,
    maneuverId = "dodge",
    priorDefensesThisTurn = 2,
    attrs = { attr_destreza = 4 },
    habs = { hab_esportes = 3 },
})
assert(def2.canRoll == true and def2.isDefense == true and def2.poolBeforeClanDivisor == 5)

-- 7. Encadeamento Ataque -> Sucessos Líquidos -> Parada de Dano (Potência passiva vs Potência automática por sangue)
local postPassive = CM.computePostAttackDamage({
    maneuver = biteOk,
    attackSuccesses = 4,
    attackOutcome = "success",
    defenseSuccesses = 1,
    passivePotenceDice = 2,
    autoPotenceSuccesses = 0,
})
-- netHits = 3 -> carryOver = 2; baseDamage(4) + carryOver(2) + passivePotence(2) = 8 dados, 0 auto
assert(postPassive.hit == true and postPassive.netHits == 3 and postPassive.carryOverDice == 2)
assert(postPassive.damageDicePool == 8 and postPassive.autoSuccesses == 0 and postPassive.damageType == "aggravated")

local postAuto = CM.computePostAttackDamage({
    maneuver = biteOk,
    attackSuccesses = 4,
    attackOutcome = "success",
    defenseSuccesses = 1,
    passivePotenceDice = 2,
    autoPotenceSuccesses = 2,
})
-- Potência ativada com sangue: 2 sucessos automáticos + 6 dados rolados (base 4 + carryOver 2)
assert(postAuto.hit == true and postAuto.damageDicePool == 6 and postAuto.autoSuccesses == 2)

-- Armas de fogo não somam Potência no dano
local postRanged = CM.computePostAttackDamage({
    maneuver = burst,
    attackSuccesses = 3,
    attackOutcome = "success",
    defenseSuccesses = 0,
    passivePotenceDice = 3,
    autoPotenceSuccesses = 3,
})
assert(postRanged.hit == true and postRanged.damageDicePool == 6 and postRanged.autoSuccesses == 0)

-- Desarme compara netHits > Força do oponente; botch marca botchedSelf
local disarmPrep = CM.prepareManeuverRoll({
    actorName = "[TESTE_E2E] Esgrimista",
    isVampire = true,
    maneuverId = "disarm_melee",
    attrs = { attr_destreza = 4, attr_forca = 3 },
    habs = { hab_armas_brancas = 4 },
    weapon = { dif = 6, dano = 2, tipo = "lethal", hab = "hab_armas_brancas" },
})
assert(disarmPrep.difficulty == 7 and disarmPrep.noDamage == true and disarmPrep.isDisarm == true)
local disarmWin = CM.computePostAttackDamage({
    maneuver = disarmPrep,
    attackSuccesses = 4,
    attackOutcome = "success",
    defenseSuccesses = 0,
    targetStrength = 3,
})
assert(disarmWin.hit == true and disarmWin.noDamage == true and disarmWin.disarm.disarmed == true)
local disarmBotch = CM.computePostAttackDamage({
    maneuver = disarmPrep,
    attackSuccesses = 0,
    attackOutcome = "botch",
    defenseSuccesses = 0,
    targetStrength = 3,
})
assert(disarmBotch.hit == false and disarmBotch.disarm.botchedSelf == true)
```

- [ ] **Step 2: Rodar `Tests/test_12_combat_maneuvers.lua` e verificar RED**

Run: `python Tests/run_tests.py Tests/test_12_combat_maneuvers.lua`
Expected: FAIL (`module 'Data.combat_maneuvers_catalog' not found`)

- [ ] **Step 3: Implementar `Data/combat_maneuvers_catalog.lua`, `Core/combat_maneuvers.lua` e atualizar `Core/v20_init.lua`**

Regras exatas de implementação:
- `Data/combat_maneuvers_catalog.lua`: declarar as 20 manobras com `id`, `name`, `category` (`"brawl"|"melee"|"ranged"|"defense"`), `defaultAttr`, `defaultHab`, `usesWeaponSlot` (`true` em `weapon_strike`, `stake_heart` p/ bônus de dano opcional mín. `1`, `disarm_melee`, `sweep_melee`, `single_shot`, `double_tap`, `three_round_burst`, `full_auto`), `accBonus`, `diffMod` (ou `fixedDiff = 9` em `stake_heart`), `strDamageBonus` (ex.: `0` Soco/Agarrão/Rasteira, `+1` Chute/Mordida/Garras/Encontrão), `damageType`, `noDamage`, `setsGrapple`, `requiresGrapple` (`bite`), `isDisarm`, `isStaking`, `isDefense`, `allowAim` (`single_shot`, `weapon_strike`), `page` (`"V20, p. 274"` etc.) e `summary`.
- `Core/combat_maneuvers.lua`:
  - `computeSplitPool(ownPool, totalNormalActions, actionNumber, lowestBasePool, isCelerityAction)`: implementar exatamente a Seção 3.1 da Spec.
  - `prepareManeuverRoll(ctx)`:
    - Verificar `requiresGrapple` (`bite` exige `ctx.inGrapple == true` ou `ctx.storytellerOverride == true`).
    - Se `ctx.isCelerityAction == true` e `(tonumber(ctx.celerityActionsLeft) or 0) < 1` (quando `ctx.celerityActionsLeft ~= nil`) e não `ctx.storytellerOverride`: retornar `canRoll = false` com mensagem clara.
    - Calcular `ownPool = attrVal + habVal + accBonus + aimBonus + bonusDice - defenseExtraPenalty` (em `bite`, `accBonus = +1` apenas se `isVampire == true`; em `single_shot` / arremesso com `aimTurns > 0`, `aimBonus = math.min(aimTurns, percepcao + (hasScope and 1 or 0))`; em `defense`, `defenseExtraPenalty = math.max(0, priorDefensesThisTurn)`).
    - Aplicar `computeSplitPool` sobre `ownPool` (se não `isDefense` ou mesmo em `isDefense` quando o personagem divide o turno normal; se `isCelerityAction`, sem split).
    - Subtrair penalidade de ferimento (`woundPenalty`, zerada se `ignoreWoundPenalty` ou `emFrenesi`), penalidade de armadura (`armorDexPenalty` quando o atributo usado é `attr_destreza`) e `clanDiceMod` opcional.
    - Se `poolBeforeClanDivisor <= 0`, retornar `canRoll = false` com motivo explícito em `pt-BR`.
    - Calcular `difficulty`: base (`fixedDiff` ou `weapon.dif` ou `6`) + `maneuver.diffMod` + `targetLocation.diffMod` + `coverLevel.diffMod` + `flankMode.diffMod` + `extraDiffMod`, limitado a `[3, 10]` (e para `stake_heart`, `math.max(9, math.min(10, diff))`).
    - Calcular `baseDamage` e `damageType`:
      - `bite`: `forca + 1`, `"aggravated"` se `isVampire` senão `"lethal"`;
      - `claw`: `forca + 1`, `"aggravated"` se `naturalAggravated` senão `"lethal"`;
      - `stake_heart`: `forca + math.max(1, weaponDmg)`, `"lethal"`;
      - `weapon_strike`: se `weapon.hab == "hab_armas_fogo"` então `weaponDmg` senão `forca + weaponDmg`;
      - `ranged` (`single_shot`, `double_tap`, `three_round_burst`, `full_auto`): `weaponDmg` (nunca soma Força!); se `isHeadshot` (`targetLocation == "cabeca"`), `damageType = "lethal"` mesmo em arma contundente/fogo contra vampiros;
      - Demais `brawl`/`melee` com dano: `forca + (maneuver.strDamageBonus or 0)`.
  - `computePostAttackDamage(params)`: implementar exatamente a Seção 3.3.2 da Spec (incluindo `clinch`/`hold` marcando `setsGrapple = true` em acerto, `disarm_*` avaliando `netHits > targetStrength` e `botchedSelf` quando `attackOutcome == "botch"`).
- `Core/v20_init.lua`: registrar `CombatManeuversCatalog` e `CombatManeuvers` tanto na tabela literal quanto com `V20.X = V20.X or require(...)`.

- [ ] **Step 4: Rodar suíte focada e suíte completa**

Run: `python Tests/run_tests.py Tests/test_12_combat_maneuvers.lua`
Expected: `[PASS] Tests\test_12_combat_maneuvers.lua`

- [ ] **Step 5: Commit**

```bash
git add Data/combat_maneuvers_catalog.lua Core/combat_maneuvers.lua Core/v20_init.lua Tests/test_12_combat_maneuvers.lua
git commit -m "feat(combat): add V20 assisted combat maneuvers catalog and pure engine"
```

---

### Task 2: Motor Puro do Rastreador de Coterie & Iniciativa (`Core/coterie_tracker.lua`) + Isolamento de Build `--output-dir`

**Files:**
- Create: `Core/coterie_tracker.lua`
- Modify: `Core/v20_init.lua`
- Modify: `tools/build_v20_suite.py`
- Modify: `Tests/test_09_rpk_package.py`
- Test: `Tests/test_13_coterie_tracker.lua`

**Interfaces:**
- Consumes: `Core/health.lua` (opcional) ou cálculo direto dos campos NDB das fichas V20.
- Produces:
  - `Core/coterie_tracker.lua`:
    - `CoterieTracker.sortInitiativeEntries(entries, phase)` -> lista ordenada (`phase == "declaracao"` menor `total` -> maior `total`, desempate menor `initMod`; `phase == "acao"` maior `total` -> menor `total`, desempate maior `initMod`; empates exatos de `total` e `initMod` recebem `simultaneous = true`)
    - `CoterieTracker.upsertInitiativeEntry(entries, newEntry, maxEntries)` -> nova lista atualizando por `id` (ou anexando até `maxEntries`, padrão `20`)
    - `CoterieTracker.filterPublicInitiative(entries, isStoryteller)` -> lista filtrada (remove `hidden == true` quando `not isStoryteller`; adiciona prefixo `"[Oculto] "` no rótulo de exibição para `isStoryteller`)
    - `CoterieTracker.computeApparentCondition(sheet)` -> `"Saudável" | "Escoriado" | "Ferido" | "Gravemente Ferido" | "Incapacitado / Torpor"`
    - `CoterieTracker.buildPublicSummary(libraryCharacters)` -> lista de `{ key, nome, condicao_aparente }` contendo **apenas** personagens com `visible == true` e **nenhum** campo privado (`sangue_atual`, `fdv_temp`, `cla_id`, `moralidade_val`, `xp_*`)
    - `CoterieTracker.buildStorytellerCards(libraryCharacters, page, pageSize)` -> `{ cards = table[], page = number, totalPages = number, totalCount = number }` (`pageSize` padrão `8`)
  - `tools/build_v20_suite.py`:
    - CLI `--output-dir <path>` (padrão `<ROOT>/dist`) e `--skip-regenerate` opcional (ou regeneração padrão idempotente);
    - Compilação de `<event>` filhos diretos de `<form>` (`obj._e_form_event{idx} = obj:addEventListener(...)` liberados em `obj:_releaseEvents()`);
    - Chamada `if self._onBeforeDestroy ~= nil then self:_onBeforeDestroy(); end;` no início de `obj:destroy()`;
    - Injeção automática de `Firecast.registrarSpecialForm(_{form_name});` logo após `Firecast.registrarDataType(_{form_name});` quando `formType == "tablesDock"`.

- [ ] **Step 1: Escrever o teste falho `Tests/test_13_coterie_tracker.lua`**

```lua
local V20 = require("Core.v20_init")
local CT = require("Core.coterie_tracker")

assert(V20.CoterieTracker == CT)

-- 1. Ordenação V20 p. 271: Declaração ascendente vs Ação descendente + desempate por initMod e flag simultaneous
local raw = {
    { id = "c1", name = "[TESTE_E2E] Brujah Rápido", d10 = 7, initMod = 8, total = 15, hidden = false },
    { id = "c2", name = "[TESTE_E2E] Nosferatu", d10 = 6, initMod = 5, total = 11, hidden = false },
    { id = "c3", name = "[TESTE_E2E] Toreador", d10 = 6, initMod = 9, total = 15, hidden = false },
    { id = "c4", name = "[TESTE_E2E] Gêmeo A", d10 = 5, initMod = 6, total = 11, hidden = false },
    { id = "c5", name = "[TESTE_E2E] Gêmeo B", d10 = 5, initMod = 6, total = 11, hidden = true },
}

local decl = CT.sortInitiativeEntries(raw, "declaracao")
-- Menor total declara primeiro (11 antes de 15); no empate em 11, menor initMod (5 antes de 6); em 15, menor initMod (8 antes de 9)
assert(decl[1].id == "c2")
assert(decl[4].id == "c1" and decl[5].id == "c3")
assert(decl[2].simultaneous == true and decl[3].simultaneous == true)

local act = CT.sortInitiativeEntries(raw, "acao")
-- Maior total age primeiro (15 antes de 11); no empate em 15, maior initMod (9 antes de 8)
assert(act[1].id == "c3" and act[2].id == "c1")
assert(act[5].id == "c2")

-- 2. Filtragem de Iniciativa Pública oculta NPCs invisíveis para jogadores mas mantém para o Narrador
local pubInit = CT.filterPublicInitiative(act, false)
assert(#pubInit == 4)
for _, e in ipairs(pubInit) do assert(e.id ~= "c5") end
local stInit = CT.filterPublicInitiative(act, true)
assert(#stInit == 5)

-- 3. Condição Física Aparente e Barreira Anti-Metajogo na Camada Pública
assert(CT.computeApparentCondition({ dano_contundente = 0, dano_letal = 0, dano_aggravado = 0 }) == "Saudável")
assert(CT.computeApparentCondition({ dano_contundente = 1, dano_letal = 1, dano_aggravado = 0 }) == "Escoriado")
assert(CT.computeApparentCondition({ dano_contundente = 2, dano_letal = 2, dano_aggravado = 0 }) == "Ferido")
assert(CT.computeApparentCondition({ dano_contundente = 2, dano_letal = 3, dano_aggravado = 1 }) == "Gravemente Ferido")
assert(CT.computeApparentCondition({ dano_contundente = 0, dano_letal = 7, dano_aggravado = 0 }) == "Incapacitado / Torpor")

local libChars = {}
for i = 1, 10 do
    libChars[i] = {
        key = "char_" .. i,
        visible = (i <= 9), -- 10º é NPC oculto
        dataType = "br.com.v20.Tremere",
        sheet = {
            nome = "[TESTE_E2E] Membro #" .. i,
            cla_id = "tremere",
            geracao = 10,
            sangue_atual = 12,
            sangue_max = 13,
            sangue_gasto_turno = 1,
            sangue_por_turno = 2,
            fdv_temp = 6,
            fdv_perm = 7,
            dano_contundente = (i == 2) and 3 or 0,
            dano_letal = 0,
            dano_aggravado = 0,
            moralidade_val = 7,
            em_frenesi = (i == 1),
            xp_pendente_status = (i == 3) and "pendente" or "nenhum",
        },
    }
end

local pubList = CT.buildPublicSummary(libChars)
assert(#pubList == 9, "NPC oculto jamais deve aparecer no resumo público")
for _, item in ipairs(pubList) do
    assert(item.sangue_atual == nil and item.fdv_temp == nil and item.cla_id == nil and item.moralidade_val == nil)
    assert(type(item.nome) == "string" and type(item.condicao_aparente) == "string")
end
assert(pubList[2].condicao_aparente == "Ferido")

-- 4. Cartões Paginados do Narrador (8 por página) incluem NPCs ocultos, medidores completos e flags
local p1 = CT.buildStorytellerCards(libChars, 1, 8)
assert(p1.page == 1 and p1.totalPages == 2 and p1.totalCount == 10 and #p1.cards == 8)
assert(p1.cards[1].sangue_txt:find("12/13") ~= nil)
assert(p1.cards[1].flags_txt:find("Frenesi") ~= nil)
assert(p1.cards[3].hasPendingXP == true)

local p2 = CT.buildStorytellerCards(libChars, 2, 8)
assert(p2.page == 2 and #p2.cards == 2)
assert(p2.cards[2].flags_txt:find("Oculto") ~= nil)
```

- [ ] **Step 2: Rodar `Tests/test_13_coterie_tracker.lua` e verificar RED**

Run: `python Tests/run_tests.py Tests/test_13_coterie_tracker.lua`
Expected: FAIL (`module 'Core.coterie_tracker' not found`)

- [ ] **Step 3: Implementar `Core/coterie_tracker.lua`, atualizar `Core/v20_init.lua`, `tools/build_v20_suite.py` e `Tests/test_09_rpk_package.py`**

Detalhes exatos de `tools/build_v20_suite.py` e `Tests/test_09_rpk_package.py`:
- Em `tools/build_v20_suite.py`:
  - Adicionar `argparse` com `--output-dir` (padrão `os.path.join(ROOT, "dist")`).
  - Na compilação de cada `.lfm` (`LFM_ENTRIES`):
    1. Extrair quaisquer tags `<event name="...">...</event>` filhas diretas de `<form>` (`root`), injetando antes de `function obj:_releaseEvents()` os listeners `obj._e_form_event{k} = obj:addEventListener("{ev_name}", function(_) {ev_code} end, obj);` e dentro de `function obj:_releaseEvents()` a liberação `__o_rrpgObjs.removeEventListenerById(self._e_form_event{k});`;
    2. Injetar no início de `function obj:destroy()` (antes de `self:_releaseEvents();`): `if self._onBeforeDestroy ~= nil then self:_onBeforeDestroy(); end;`;
    3. Quando `root.attrib.get("formType") == "tablesDock"`, injetar `Firecast.registrarSpecialForm(_{form_name});` imediatamente após `Firecast.registrarDataType(_{form_name});`.
- Em `Tests/test_09_rpk_package.py`:
  - Em `main()` / verificações de build, criar um diretório temporário com prefixo `test_e2e_rpk_out_` via `tempfile.mkdtemp(prefix="test_e2e_rpk_out_")`, passar `--output-dir <tmp_dir>` ao executar `tools/build_v20_suite.py`, auditar o `.rpk`/`.rdk` gerado nesse diretório temporário e removê-lo em `finally:` com `shutil.rmtree(..., ignore_errors=True)`. Assim `git status` em `dist/` permanece 100% intacto ao rodar `python Tests/run_tests.py`!

- [ ] **Step 4: Rodar testes focados e verificar árvore `dist/` intacta**

Run: `python Tests/run_tests.py Tests/test_13_coterie_tracker.lua Tests/test_09_rpk_package.py`
Expected: `[PASS]` em ambos e `git diff --name-only dist/` vazio.

- [ ] **Step 5: Commit**

```bash
git add Core/coterie_tracker.lua Core/v20_init.lua tools/build_v20_suite.py Tests/test_09_rpk_package.py Tests/test_13_coterie_tracker.lua
git commit -m "feat(tracker): add pure coterie/initiative engine and sandboxed build output-dir"
```

---

### Task 3: Estúdio de Manobras V20 na Aba 5 das 15 Fichas + Coesão Aba 3 ↔ Aba 8 (`Adapter/firecast_bridge.lua` + `Templates/`)

**Files:**
- Modify: `Adapter/firecast_bridge.lua`
- Modify: `Templates/theme_gothic.py`
- Modify: `Templates/generate_vampire_lfm.py`
- Modify: `Templates/generate_mortal_lfm.py`
- Modify: `Sheets/frmBrujah.lfm` .. `Sheets/frmCaitiff.lfm` e `Sheets/frmMortal.lfm` (15 arquivos gerados)
- Test: `Tests/test_08_bridge_and_lfm_gen.py`

**Interfaces:**
- Consumes: `Core/combat_maneuvers.lua`, `Data/combat_maneuvers_catalog.lua`, `Core/blood_magic_engine.lua`.
- Produces:
  - `Bridge.executeCombatManeuver(sheet, opts, firecastApi, dialogsApi)`:
    - Lê os campos NDB da Aba 5 (com override via `opts`):
      - `cmb_manobra_id` (padrão `"strike"`), `cmb_arma_slot` (`1..4`, padrão `1`), `cmb_acoes_normais` (`1..5`, padrão `1`), `cmb_acao_ordem` (`1..5`, padrão `1`), `cmb_menor_parada` (`0` = usar parada da própria manobra), `cmb_acao_rapidez` (`false`), `cmb_mira_turnos` (`0`), `cmb_tem_luneta` (`false`), `cmb_alvo_localizado` (`"nenhum"`), `cmb_cobertura` (`"nenhuma"`), `cmb_posicao` (`"frontal"`), `cmb_defesa_alvo_sucessos` (`0`), `cmb_forca_alvo` (`2`), `cmb_defesas_feitas_turno` (`0`), `em_agarrao` (`false`).
    - Prepara a manobra via `V20.CombatManeuvers.prepareManeuverRoll(...)` (passando `naturalAggravated = cMods.naturalAggravated`, `celerityActionsLeft = safeInt(sheet.rapidez_acoes_extras, 0)`, `storytellerOverride = stOverride`, `woundPenalty`, `armorDexPenalty`).
    - Se `not prep.canRoll`: exibe `dlg.showMessage(prep.reason)` e retorna `{ ok = false, error = prep.reason }`.
    - Se `prep.consumeCelerityAction`: decrementa `sheet.rapidez_acoes_extras = math.max(0, safeInt(sheet.rapidez_acoes_extras, 0) - 1)`.
    - Se `prep.isDefense`: incrementa `sheet.cmb_defesas_feitas_turno = safeInt(sheet.cmb_defesas_feitas_turno, 0) + 1`.
    - Rola via `Bridge.rollFromSheet` usando `rawPool = prep.poolBeforeClanDivisor`, `difficulty = prep.difficulty`, `ignoreWoundPenalty = true` (já descontada uma única vez em `prep.poolBeforeClanDivisor`!), `attrId = prep.attrUsed` (para preservar modificadores/avisos de fraqueza de clã aplicáveis sem duplicar ferimento; passe flag `preAppliedSetitePenalty = true` ou deixe `clanDiceMod = 0` em `prep` para que `rollFromSheet` aplique Setita `-1` e Tzimisce `2^dias` uma única vez!).
    - No callback `onEvaluated(evalRes)` de ataques (`not prep.isDefense`): chama `V20.CombatManeuvers.computePostAttackDamage(...)` (usando `passivePotenceDice = cMods.passivePotenceDice`, `autoPotenceSuccesses = cMods.autoPotenceSuccesses`, `defenseSuccesses = safeInt(sheet.cmb_defesa_alvo_sucessos, 0)`, `targetStrength = safeInt(sheet.cmb_forca_alvo, 2)`):
      - Se `post.setsGrapple`: marca `sheet.em_agarrao = true`;
      - Se `post.hit and not post.noDamage`: preenche `sheet.cmb_dano_pendente_ativo = true`, `sheet.cmb_dano_pendente_parada = post.damageDicePool`, `sheet.cmb_dano_pendente_auto = post.autoSuccesses`, `sheet.cmb_dano_pendente_tipo = post.damageType`, `sheet.cmb_dano_pendente_estaca = post.isStaking`, `sheet.cmb_dano_pendente_cabeca = post.isHeadshot`, `sheet.cmb_dano_pendente_manobra = prep.maneuverName`, `sheet.cmb_dano_pendente_resumo = post.summary`; caso contrário limpa `sheet.cmb_dano_pendente_ativo = false` e grava `sheet.cmb_dano_pendente_resumo = post.summary`;
      - Retorna `post.summary` para sair na mesma mensagem de resultado do chat!
  - `Bridge.rollPendingCombatDamage(sheet, firecastApi, dialogsApi)`:
    - Valida `isTrue(sheet.cmb_dano_pendente_ativo)` (se falso, avisa via `dlg.showMessage`).
    - Rola `Bridge.rollFromSheet` com `rawPool = safeInt(sheet.cmb_dano_pendente_parada, 0)`, `autoSuccesses = safeInt(sheet.cmb_dano_pendente_auto, 0)`, `difficulty = 6`, `ignoreWoundPenalty = true`, `forbidWillpower = true`, `skipClanWeakness = true` (rolagens de dano em V20 não sofrem penalidade de luz/ferimento/divisão de parada!), `allowZeroPoolWithAuto = true`, e em `onEvaluated(evalRes)`:
      - Limpa `sheet.cmb_dano_pendente_ativo = false`;
      - Se `isTrue(sheet.cmb_dano_pendente_estaca)` e `evalRes.totalSuccesses >= 3`: anexa alerta `"🪵 ESTACA NO CORAÇÃO: 3+ níveis (se restarem >= 3 após Absorção, vampiro entra em Paralisia/Torpor!)"`;
      - Retorna resumo `"Dano Bruto (" .. dtype .. "): " .. tostring(evalRes.totalSuccesses) .. " nível(is)"`.
  - `Bridge.rollInitiative`: adiciona chamada opcional segura (`pcall(require, "Adapter.coterie_dock_bridge")`) para `dockBridge.recordSheetInitiative(sheet, faceInt, mod, faceInt + mod, fc)` quando disponível.
  - Unificação Aba 3 ↔ Aba 8:
    - Em `Bridge.activateDisciplineSlot(sheet, slotIndex, firecastApi, dialogsApi)`: quando `Bridge.isVampireSheet(sheet)` e `disc_id` for `"thaumaturgy"` ou `"necromancy"`, delega diretamente para `Bridge.activatePrimaryBloodMagic(sheet, disc_id, pwrLvl, firecastApi, dialogsApi)`.
    - Em `updateDisciplineSummaries(sheet)`: quando `Bridge.isVampireSheet(sheet)` e `disc_id` for `"thaumaturgy"` ou `"necromancy"`, busca o poder na Linha Primária ativa (`V20.BloodMagicEngine.getPathTable`) em vez da tabela estática padrão.
    - Em `Templates/theme_gothic.py`: remove `cmbBmThauPrimId` e `cmbBmNecroPrimId` de `PERM_CTRLS` incondicional e trava cada um apenas quando `lockPerm and (tonumber(sheet.bm_thau_prim_nivel) or 0) > 0` (respectivamente `bm_necro_prim_nivel`).

- [ ] **Step 1: Adicionar os testes falhos em `Tests/test_08_bridge_and_lfm_gen.py`**

Adicionar casos de teste cobrindo:
1. `V20Bridge.executeCombatManeuver` com divisão de parada (`2` ações, menor parada `5`), consumo de `rapidez_acoes_extras` sem divisão, `clinch` ligando `em_agarrao = true` -> `bite` causando dano `aggravated` encadeado -> `V20Bridge.rollPendingCombatDamage` somando `autoPotenceSuccesses` e limpando `cmb_dano_pendente_ativo`;
2. `stake_heart` emitindo alerta de paralisia com `>= 3` sucessos de dano;
3. Unificação Aba 3 ↔ Aba 8: mudar `bm_thau_prim_id = "lure_of_flames"` na Aba 8 faz `disc_slot_resumo` e `activateDisciplineSlot` na Aba 3 ativarem *Sedutor das Chamas* (com alerta de falha crítica de Taumaturgia);
4. Verificação dos novos controles da Aba 5 nas **15 fichas** geradas (`Sheets/frm*.lfm`).

- [ ] **Step 2: Rodar `Tests/test_08_bridge_and_lfm_gen.py` e verificar RED**

Run: `python Tests/run_tests.py Tests/test_08_bridge_and_lfm_gen.py`
Expected: FAIL (`executeCombatManeuver` ausente)

- [ ] **Step 3: Implementar os métodos em `Adapter/firecast_bridge.lua`, atualizar `Templates/` e regerar as 15 fichas**

Atenção especial:
- Em `Bridge.rollFromSheet`, garantir suporte a `opts.skipClanWeakness == true` e `opts.autoSuccesses` com `rawPool == 0` (para o caso extremo em que apenas sucessos automáticos de Potência componham o dano, ou quando `rawPool >= 1` somado a `autoSuccesses`).
- Em `Bridge.newTurn`, zerar `sheet.cmb_defesas_feitas_turno = 0`. Em `Bridge.clearSceneBuffs`, zerar `sheet.em_agarrao = false`, `sheet.cmb_defesas_feitas_turno = 0` e `sheet.cmb_dano_pendente_ativo = false`.
- Em `Templates/generate_vampire_lfm.py` e `Templates/generate_mortal_lfm.py`, adicionar na Aba 5 (`build_tab5_combat`) o card **"ESTÚDIO DE MANOBRAS V20, DIVISÃO DE PARADAS & DANO ENCADEADO"** (com todos os `name="..."` únicos e `<dataLink>`s padrão na raiz do `<form>`) e regerar todas as 15 fichas (`python Templates/generate_vampire_lfm.py --all-clans` e `python Templates/generate_mortal_lfm.py`).

- [ ] **Step 4: Rodar `Tests/test_08_bridge_and_lfm_gen.py` e toda a suíte atual**

Run: `python Tests/run_tests.py`
Expected: 12/12 suítes `[PASS]`.

- [ ] **Step 5: Commit**

```bash
git add Adapter/firecast_bridge.lua Templates/theme_gothic.py Templates/generate_vampire_lfm.py Templates/generate_mortal_lfm.py Sheets/ Tests/test_08_bridge_and_lfm_gen.py
git commit -m "feat(sheets): add Tab 5 V20 combat maneuver studio and Tab 3/8 blood magic cohesion"
```

---

### Task 4: Painel Acoplável `frmV20CoterieDock` (`tablesDock`), `Adapter/coterie_dock_bridge.lua` e Pacote Final `v1.0.0` (16 Formulários)

**Files:**
- Create: `Adapter/coterie_dock_bridge.lua`
- Modify: `v20_loader.lua`
- Create: `Templates/generate_coterie_dock_lfm.py`
- Create: `Sheets/frmV20CoterieDock.lfm`
- Modify: `module.xml`
- Modify: `tools/build_v20_suite.py`
- Modify: `dist/Vampiro_V20_Suite.rpk` & `dist/Vampiro_V20_Suite.rdk`
- Test: `Tests/test_08_bridge_and_lfm_gen.py` & `Tests/test_09_rpk_package.py`

**Interfaces:**
- Consumes: `Core/coterie_tracker.lua`, `Core/v20_init.lua`, `Adapter/firecast_bridge.lua`.
- Produces:
  - `Adapter/coterie_dock_bridge.lua` (exposto como `_G.V20CoterieDockBridge`):
    - `CoterieDockBridge.ROOM_NDB_NAME = "v20_coterie_dock_v1"`
    - `CoterieDockBridge.connectDock(formObj, firecastApi, ndbApi)`
    - `CoterieDockBridge.disconnectDock(formObj)` (desabilita `formObj._roomObserver` e todos os `formObj._charObservers`, removendo `formObj` do registro ativo)
    - `CoterieDockBridge.recordSheetInitiative(sheet, d10, initMod, total, firecastApi)`
    - `CoterieDockBridge.addQuickNpcInitiative(formObj, firecastApi, dialogsApi)`
    - `CoterieDockBridge.toggleCombatPhase(formObj, firecastApi, dialogsApi)` (alterna `"declaracao"` ↔ `"acao"` e reordena os 10 slots públicos `init_row1_txt..init_row10_txt`)
    - `CoterieDockBridge.clearInitiative(formObj, firecastApi, dialogsApi)`
    - `CoterieDockBridge.refreshDock(formObj, firecastApi, ndbApi)` (aplica visibilidade de `tabNarradorCoterie:setVisible(isMestre)`, atualiza Aba 1 pública apenas com dados permitidos e, se `isMestre`, varre `mesa.biblioteca` recursivamente, conecta observers e preenche os 8 cartões paginados `st_card1..st_card8`)
    - `CoterieDockBridge.changePage(formObj, delta, firecastApi, ndbApi)`
    - `CoterieDockBridge.adjustCardBlood(formObj, cardIdx, delta, firecastApi, dialogsApi)` (exclusivo `isMestre`)
    - `CoterieDockBridge.approveCardXP(formObj, cardIdx, firecastApi, ndbApi, dialogsApi)` (exclusivo `isMestre`)
    - `CoterieDockBridge.batchAwakenNightly(formObj, firecastApi, dialogsApi)` (exclusivo `isMestre`)
    - `CoterieDockBridge.batchNewTurn(formObj, firecastApi, dialogsApi)` (exclusivo `isMestre`)
    - `CoterieDockBridge.batchEndScene(formObj, firecastApi, dialogsApi)` (exclusivo `isMestre`)
  - `Sheets/frmV20CoterieDock.lfm`: `<form name="frmV20CoterieDock" formType="tablesDock" dataType="br.com.v20.CoterieDock" title="Vampiro V20 - Painel da Coterie &amp; Iniciativa" width="340" height="580" theme="dark">` com `<event name="OnShow">`, `<event name="OnHide">`, `self._onBeforeDestroy`, Aba 1 (`tabCenaIniciativa`) e Aba 2 (`tabNarradorCoterie`).
  - `module.xml` atualizado para `<version>1.0.0</version>` e `tools/build_v20_suite.py` empacotando os **16 formulários** (`15 sheetTemplate + 1 tablesDock`).

- [ ] **Step 1: Escrever os testes falhos E2E em `Tests/test_08_bridge_and_lfm_gen.py` e `Tests/test_09_rpk_package.py`**

Adicionar verificações falhas exigindo:
1. Em `test_08_bridge_and_lfm_gen.py`:
   - Geração e validação XML de `Sheets/frmV20CoterieDock.lfm` (`formType == "tablesDock"`, `dataType == "br.com.v20.CoterieDock"`, zero `<recordList>`, todos os nomes únicos);
   - Teste E2E de `CoterieDockBridge` com sala simulada (`[TESTE_E2E] Sala Crônica Noturna`), biblioteca contendo PJs visíveis (`[TESTE_E2E] Tremere`, `[TESTE_E2E] Brujah`) + NPC oculto (`[TESTE_E2E] Ancião Nosferatu Oculto`, `visivelRecursivamente = false`):
     - `V20Bridge.rollInitiative` nos PJs e NPC alimenta automaticamente `v20_coterie_dock_v1`;
     - Quando aberto por **Jogador (`isMestre = false`)**: `tabNarradorCoterie` fica oculta (`visible == false`), NPC oculto **não** aparece nem na Iniciativa nem no Resumo Aparente, `roomNode` não contém Sangue/FdV/Moralidade, e qualquer tentativa de chamar `batchAwakenNightly`/`adjustCardBlood`/`approveCardXP` é bloqueada por permissão;
     - Quando aberto pelo **Narrador (`isMestre = true`)**: `tabNarradorCoterie` fica visível, os 3 personagens aparecem nos cartões (com `[Oculto]` no NPC), `toggleCombatPhase` alterna Declaração (ascendente) ↔ Ação (descendente), `adjustCardBlood`, `approveCardXP`, `batchAwakenNightly`, `batchNewTurn` e `batchEndScene` atualizam as fichas reais e postam boletim único no chat, e `disconnectDock` desativa 100% dos `NDB.newObserver` criados!
2. Em `test_09_rpk_package.py`:
   - Verificar `<version>1.0.0</version>` e os **16 `<dataType>`** no `module.xml` assemblado (`15` com `formType="sheetTemplate"` + `br.com.v20.CoterieDock` com `formType="tablesDock"`);
   - Verificar que `Sheets/frmV20CoterieDock.lfm.lua` contém `Firecast.registrarSpecialForm(_frmV20CoterieDock);`;
   - Instanciar os **16 formulários** no runtime `lua54x64.dll` (incluindo disparo de `OnShow` -> observadores ativos -> `OnHide` -> `destroy()` em `frmV20CoterieDock` verificando `0` listeners órfãos e `0` observers ativos) e validar auto-boot VHD em ordem alfabética estrita (`/Adapter/coterie_dock_bridge.lua` antes de `/Adapter/firecast_bridge.lua` e antes de `/v20_loader.lua`!).

- [ ] **Step 2: Rodar `test_08` e `test_09` para confirmar RED**

Run: `python Tests/run_tests.py Tests/test_08_bridge_and_lfm_gen.py Tests/test_09_rpk_package.py`
Expected: FAIL (`Adapter.coterie_dock_bridge` / `frmV20CoterieDock.lfm` ausentes)

- [ ] **Step 3: Implementar `Adapter/coterie_dock_bridge.lua`, `Templates/generate_coterie_dock_lfm.py`, `v20_loader.lua`, `module.xml`, `tools/build_v20_suite.py` e construir `dist/Vampiro_V20_Suite.{rpk,rdk}` (`v1.0.0`)**

Pontos críticos de implementação:
- Em `Adapter/coterie_dock_bridge.lua`:
  - Não fazer `require("Adapter.firecast_bridge")` criando dependência circular com topo de módulo: `firecast_bridge.lua` não requer `coterie_dock_bridge` no topo, então `coterie_dock_bridge.lua` pode requerer `Core.v20_init` e `Adapter.firecast_bridge` com total segurança no boot alfabético VHD (desde que `tools/build_v20_suite.py` injete `require("v20_shim.dlua"); ` na linha 1, o que já faz para todo `Adapter/*.lua`).
  - Todas as mutações do Narrador (`toggleCombatPhase`, `addQuickNpcInitiative`, `clearInitiative`, `adjustCardBlood`, `approveCardXP`, `batchAwakenNightly`, `batchNewTurn`, `batchEndScene`) DEVEM checar `isRoomStoryteller(mesa)` no backend antes de executar qualquer alteração.
  - Em `roomNode` (`v20_coterie_dock_v1`), gravar **apenas** campos da camada pública (`cena_titulo`, `rodada_atual`, `combate_fase`, entradas serializadas/indexadas de iniciativa com flag `hidden`, e até 8 slots públicos `pub_slot{1..8}_txt` contendo somente `Nome — Condição Aparente`). Dados privados dos cartões do Narrador vivem apenas nos controles visuais locais `self.lblStCard*` alimentados diretamente dos `charNode`s lidos via `loadSheetNDB` quando `isMestre == true`!
- Rodar `python tools/build_v20_suite.py` uma vez para gerar os binários finais `v1.0.0` em `dist/Vampiro_V20_Suite.rpk` e `dist/Vampiro_V20_Suite.rdk`.

- [ ] **Step 4: Rodar todas as 13 suítes de teste e confirmar árvore limpa**

Run: `python Tests/run_tests.py`
Expected: **13/13 suítes `[PASS]`** com `exit code 0` e sem arquivos sujos não rastreados.

- [ ] **Step 5: Commit**

```bash
git add Adapter/coterie_dock_bridge.lua v20_loader.lua Templates/generate_coterie_dock_lfm.py Sheets/frmV20CoterieDock.lfm module.xml tools/build_v20_suite.py dist/Vampiro_V20_Suite.rpk dist/Vampiro_V20_Suite.rdk Tests/test_08_bridge_and_lfm_gen.py Tests/test_09_rpk_package.py
git commit -m "feat(dock): add Storyteller Coterie tablesDock and package v1.0.0 suite (16 forms)"
```
