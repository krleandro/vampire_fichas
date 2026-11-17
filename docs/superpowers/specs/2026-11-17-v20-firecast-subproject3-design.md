# Vampiro: A Máscara V20 (RRPG Firecast SDK 3.7b) — Especificação Técnica do Subprojeto 3 (`v1.0.0`)

**Data:** 2026-11-17  
**Versão Alvo do Pacote:** `1.0.0` (`Vampiro_V20_Suite.rpk`)  
**Plataforma:** RRPG Firecast SDK 3.7b (`sdkApiVersion="88"`, `sdkMinorApiVersion="2"`, Lua 5.4)  
**Referência Mecânica Exclusiva:** *Vampire: The Masquerade — 20th Anniversary Edition (V20 Corebook)*  
**Base Prévia:** Subprojeto 2 (`v0.6.0`, commit `216af58` em `feat/subproject1-v20-suite`)

---

## 1. Objetivo e Escopo do Subprojeto 3 (`v1.0.0`)

Concluir a edição `v1.0.0` do ecossistema `dist/Vampiro_V20_Suite.rpk`, adicionando os dois subsistemas finais planejados no roadmap original e incorporando os polimentos de coesão levantados na revisão do Subprojeto 2:

1. **Catálogo e Motor Puro de Manobras de Combate Assistido V20 (`Data/combat_maneuvers_catalog.lua` + `Core/combat_maneuvers.lua`):**
   - **Divisão de Paradas pela Menor Parada (V20, p. 248)** separada das **Ações Extras de Rapidez (V20, p. 142)**;
   - **20 Manobras Oficiais V20 (pp. 274–281)** cobrindo *Briga/Desarmado*, *Armas Brancas/Especiais*, *Armas de Fogo/Rajadas* e *Defesas Ativas* (*Esquiva, Bloqueio, Aparar*), além de modificadores táticos de *Mira*, *Golpe Localizado* e *Cobertura*;
   - **Fluxo Encadeado Ataque → Sucessos Líquidos → Parada Exata de Dano** na Aba 5 das 15 fichas (`frmBrujah`..`frmMortal`), integrando automaticamente *Potência* (dados passivos ou sucessos automáticos quando ativada por sangue), *Metamorfose 2* (garras agravadas), *Mordida Vampírica* (agravada em agarrão) e *Estaca no Coração* (dif. `9`, paralisia com `>= 3` níveis pós-absorção).
2. **Painel Lateral Acoplável `tablesDock` de Coterie & Iniciativa (`Sheets/frmV20CoterieDock.lfm` + `Core/coterie_tracker.lua` + `Adapter/coterie_dock_bridge.lua`):**
   - Registrado como o **16º `dataType`** (`id="br.com.v20.CoterieDock"`, `formType="tablesDock"`) dentro do mesmo `Vampiro_V20_Suite.rpk` com chamada obrigatória a `Firecast.registrarSpecialForm(...)`;
   - **Segurança em Duas Camadas (Zero Metajogo):**
     - **Aba 1 Pública (`v20_coterie_dock_v1` via `mesa:abrirNDBDeMesa`):** Ordem de Iniciativa V20 sincronizada com as 15 fichas (Fase de Declaração ascendente vs. Fase de Ação descendente com desempate por modificador `Destreza + Raciocínio`, V20 p. 271) e Resumo Aparente apenas dos personagens visíveis (*Nome* + *Condição Física Aparente*, sem jamais expor Sangue, FdV, Clã real, Moralidade, XP ou NPCs ocultos);
     - **Aba 2 Exclusiva do Narrador (`isMestre == true`, via `mesa.biblioteca` → `loadSheetNDB` + `NDB.newObserver`):** 8 cartões paginados sem `<recordList>` monitorando ao vivo PJs e NPCs (`br.com.v20.*`), ajustes rápidos de Vitae, aprovação de XP pendente e comandos globais em lote (*Despertar Noturno da Coterie*, *Novo Turno Global* e *Encerrar Cena*).
3. **Polimentos Arquiteturais & Higiene de Build (`v1.0.0`):**
   - Suporte a `--output-dir` em `tools/build_v20_suite.py` para que `Tests/test_09_rpk_package.py` compile em diretório temporário de sandbox sem mutar `dist/Vampiro_V20_Suite.{rpk,rdk}`;
   - Coesão Aba 3 ↔ Aba 8 para `thaumaturgy` e `necromancy` (delegando ativação e resumo da Aba 3 para a Linha Primária configurada na Aba 8, incluindo o alerta de falha crítica de Taumaturgia) e liberação dos combos `cmbBmThauPrimId` / `cmbBmNecroPrimId` em `modo_ficha == "jogo"` enquanto o nível da disciplina for `0`.

---

## 2. Os 16 Formulários Registrados em `module.xml` (`v1.0.0`)

- **Modelos 1 a 15 (`formType="sheetTemplate"`):** Os 14 modelos vampíricos (`br.com.v20.Brujah`..`br.com.v20.Caitiff`) + `br.com.v20.Mortal` (`Sheets/frmMortal.lfm`), idênticos à tabela do Subprojeto 2 e enriquecidos na Aba 5 com o Estúdio de Manobras V20.
- **Modelo 16 (`formType="tablesDock"`):**

| # | Componente | `formName` | Arquivo `.lfm` | `dataType` | `formType` | Título na Mesa do Firecast |
| :-: | :--- | :--- | :--- | :--- | :--- | :--- |
| 16 | Painel da Coterie & Iniciativa | `frmV20CoterieDock` | `Sheets/frmV20CoterieDock.lfm` | `br.com.v20.CoterieDock` | `tablesDock` | `Vampiro V20 - Painel da Coterie & Iniciativa` |

> **Regra Crítica SDK 3.7b para `tablesDock`:** Ao compilar um `.lfm` cujo `formType` seja `"tablesDock"`, `tools/build_v20_suite.py` DEVE injetar `Firecast.registrarSpecialForm(_frmV20CoterieDock);` imediatamente após `Firecast.registrarDataType(_frmV20CoterieDock);` no `.lfm.lua` gerado, além de emitir `formType="tablesDock"` em `<assembledFeatures><dataTypes><dataType .../>` no `module.xml` assemblado.

---

## 3. Subsistema de Manobras de Combate Assistido (`Data/combat_maneuvers_catalog.lua` & `Core/combat_maneuvers.lua`)

### 3.1. Divisão de Paradas V20 vs. Ações Extras de Rapidez
1. **Ações Normais Múltiplas (`CombatManeuvers.computeSplitPool` — V20, p. 248):**
   - Entradas: `ownPool` (parada base `Atributo + Habilidade + precisão/bônus da manobra`, antes de penalidade de ferimento ou com ferimento aplicado apenas uma vez conforme abaixo), `totalNormalActions` (`1..5`), `actionNumber` (`1..totalNormalActions`), `lowestBasePool` (`0` = usar `ownPool`; se `> 0`, a base da divisão passa a ser `math.min(ownPool, lowestBasePool)`).
   - Quando `totalNormalActions <= 1`: não há penalidade de divisão (`poolAfterSplit = ownPool`, `splitPenalty = 0`).
   - Quando `totalNormalActions >= 2`:
     - `base = (lowestBasePool and lowestBasePool > 0) and math.min(ownPool, lowestBasePool) or ownPool`
     - `idx = clamp(actionNumber, 1, totalNormalActions)`
     - `splitPenalty = totalNormalActions + (idx - 1)` (ex.: 2 ações → `-2` na 1ª, `-3` na 2ª; 3 ações → `-3`, `-4`, `-5`).
     - `poolAfterSplit = base - splitPenalty`.
   - **Ordem exata de modificadores de parada no turno:**
     1. Calcula `ownPool` (`Atributo efetivo + Habilidade + bônus de precisão da manobra + dados de Mira + bônus manual`).
     2. Aplica Divisão de Parada (`computeSplitPool`, exceto quando `isCelerityAction == true`).
     3. Subtrai Penalidade de Ferimento (`penalidade_ferimento`, ignorada se `em_frenesi == true` ou `roll_ignorar_ferimento == true`) e Penalidade de Destreza de Armadura (`armadura_penalidade`, quando a manobra usa `attr_destreza`) e penalidades de fraqueza de clã em dados (ex.: `-1` dado Setita sob luz forte).
     4. Se a parada resultante nesta etapa for `<= 0`, a ação **não pode ser rolada** (`canRoll = false`, retornando motivo explícito em `pt-BR`, conforme V20 p. 248).
     5. Se a parada for `>= 1` e o personagem for Tzimisce com `tzimisce_dias_sem_terra > 0`, aplica a divisão cumulativa `math.max(1, math.floor(pool / (2 ^ dias)))` já existente em `rollFromSheet`.
2. **Ações Extras de Rapidez (`isCelerityAction == true` — V20, p. 142):**
   - Exige `rapidez_acoes_extras >= 1` (salvo `storytellerOverride == true`).
   - Ignora integralmente `computeSplitPool` (sem penalidade de múltiplas ações!) e consome `1` ponto de `rapidez_acoes_extras` ao executar a rolagem.

### 3.2. Catálogo Oficial das 20 Manobras V20 (`Data/combat_maneuvers_catalog.lua`)

Todas as 20 manobras possuem IDs ASCII estáveis, nomes em `pt-BR`, categoria (`"brawl"`, `"melee"`, `"ranged"`, `"defense"`), referência de página V20 e regras determinísticas:

| # | ID | Nome (`pt-BR`) | Cat. | Parada Base | Mod. Ataque | Mod. Dif. | Dano Base & Tipo | Regras Especiais V20 |
| :-: | :--- | :--- | :---: | :--- | :---: | :---: | :--- | :--- |
| 1 | `strike` | Soco | `brawl` | `Des + Briga` | `+0` | `+0` (6) | `Força` Contundente | Manobra padrão desarmada (p. 276) |
| 2 | `kick` | Chute | `brawl` | `Des + Briga` | `+0` | `+1` (7) | `Força + 1` Contundente | Falha crítica derruba atacante (p. 276) |
| 3 | `bite` | Mordida Vampírica | `brawl` | `Des + Briga` | `+1` (vamp) | `+0` (6) | `Força + 1` **Agravado** (vamp) | Exige `em_agarrao == true` (salvo override); mortal causa Letal s/ `+1` dado (p. 276) |
| 4 | `claw` | Garras | `brawl` | `Des + Briga` | `+0` | `+0` (6) | `Força + 1` **Agravado** (`pro_2`) / Letal | Agravado quando *Garras da Besta* (`natural_aggravated`) ativo; senão Letal (p. 276) |
| 5 | `clinch` | Agarrão (*Clinch*) | `brawl` | `For + Briga` | `+0` | `+0` (6) | `Força` Contundente | Em acerto, ativa `em_agarrao = true` (p. 276) |
| 6 | `hold` | Segurar (*Hold*) | `brawl` | `For + Briga` | `+0` | `+0` (6) | Sem dano (`noDamage`) | Em acerto, ativa `em_agarrao = true` e imobiliza alvo até próx. ação (p. 276) |
| 7 | `tackle` | Encontrão (*Tackle*) | `brawl` | `For + Briga` | `+0` | `+1` (7) | `Força + 1` Contundente | Alvo e atacante testam Destreza+Esportes p/ não cair (p. 277) |
| 8 | `sweep_brawl` | Rasteira (Briga) | `brawl` | `Des + Briga` | `+0` | `+1` (7) | `Força` Contundente | Derruba o alvo (`+2` dif. p/ ações dele no chão, p. 277) |
| 9 | `disarm_brawl` | Desarmar (Desarmado) | `brawl` | `Des + Briga` | `+0` | `+1` (7) | Sem dano (`noDamage`) | Exige `sucessos líquidos > Força do alvo`; botch fere atacante (p. 276) |
| 10 | `weapon_strike` | Golpe com Arma Equipada | `melee` | Slot `arma{1..4}` | `+0` | Dif. Arma | `Força + Dano Arma` (Tipo Arma) | Usa o slot `cmb_arma_slot` (`1..4`, p. 276) |
| 11 | `stake_heart` | Estacar Coração | `melee` | `Des + Armas Brancas` | `+0` | Fixa `9` | `Força + Dano Arma/1` Letal | Se causar `>= 3` níveis efetivos pós-absorção, paralisa vampiro! (p. 279) |
| 12 | `disarm_melee` | Desarmar com Arma | `melee` | `Des + Armas Brancas` | `+0` | `Dif Arma + 1` | Sem dano (`noDamage`) | Exige `sucessos líquidos > Força do alvo`; botch perde a própria arma (p. 276) |
| 13 | `sweep_melee` | Rasteira com Haste/Arma | `melee` | `Des + Armas Brancas` | `+0` | `Dif Arma + 1` | `Força` Contundente | Derruba o alvo em acerto (p. 277) |
| 14 | `single_shot` | Tiro Único | `ranged` | Slot `arma{1..4}` (`Des + Fogo`) | `+0` | Dif. Arma | `Dano Arma` (Cont./Letal) | Armas de fogo não somam Força; Contundente em vampiro exceto cabeça (p. 277, 280) |
| 15 | `double_tap` | Tiro Duplo Rápido | `ranged` | Slot `arma{1..4}` | `+1` | `Dif Arma + 1` | `Dano Arma` | `+1` dado, `+1` dif. de recuo; consome 2 munições (p. 278) |
| 16 | `three_round_burst` | Rajada Curta (3 Tiros) | `ranged` | Slot `arma{1..4}` | `+2` | `Dif Arma + 1` | `Dano Arma` | `+2` dados de ataque, `+1` dificuldade; gasta 3 balas (p. 277) |
| 17 | `full_auto` | Rajada Completa (*Full-Auto*) | `ranged` | Slot `arma{1..4}` | `+10` | `Dif Arma + 2` | `Dano Arma` | `+10` dados de ataque, `+2` dif.; esvazia carregador e exige recarga (p. 277) |
| 18 | `dodge` | Esquiva Ativa | `defense` | `Des + Esportes` | `-defExtra` | `6` | Reativa (`isDefense`) | Cada defesa extra no mesmo turno sofre `-1` dado cumulativo (p. 274) |
| 19 | `block` | Bloqueio (Briga) | `defense` | `Des + Briga` | `-defExtra` | `6` | Reativa (`isDefense`) | Apenas contra ataques desarmados/contundentes corpo a corpo (p. 274) |
| 20 | `parry` | Aparar (Armas Brancas) | `defense` | `Des + Armas Brancas` | `-defExtra` | `6` | Reativa (`isDefense`) | Aparar com arma branca; contra ataque desarmado pode ferir agressor (p. 275) |

### 3.3. Modificadores Táticos e Encadeamento Ataque → Dano
1. **Modificadores Táticos cumulativos (`CombatManeuvers.prepareManeuverRoll`):**
   - **Mira (`cmb_mira_turnos`, `0..6`):** soma `math.min(miraTurnos, percepcao + (temLuneta and 1 or 0))` dados na parada do 1º tiro (`single_shot` / `weapon_strike` arremessado — V20 p. 274).
   - **Golpe Localizado (`cmb_alvo_localizado`):**
     - `"nenhum"`: `+0` dif, `+0` dano;
     - `"membro"` (Braço/Perna/Mão): `+1` dif, `+0` dano;
     - `"cabeca"` (Cabeça/Vital): `+2` dif, `+1` dado de dano base (e ativa `isHeadshot = true`, tornando armas de fogo **Letais** até contra vampiros, V20 p. 274 & p. 280!).
   - **Cobertura do Alvo (`cmb_cobertura`):** `"nenhuma"` (`+0`), `"leve"` (`+1` dif), `"boa"` (`+2` dif), `"superior"` (`+3` dif — V20 p. 274).
   - **Flanco / Retaguarda (`cmb_posicao`):** `"frontal"` (`+0` dif), `"flanco"` (`-1` dif no ataque — V20 p. 278), `"retaguarda"` (`-2` dif no ataque — V20 p. 278). *Nota:* a dificuldade final é sempre limitada ao intervalo `[3, 10]` (exceto `stake_heart`, cuja dificuldade mínima permanece `9`).
2. **Cálculo Encadeado da Parada de Dano (`CombatManeuvers.computePostAttackDamage` — V20, p. 272):**
   - Entradas: resultado de avaliação do ataque (`totalSuccesses`, `outcome`), `defenseSuccesses` (`cmb_defesa_alvo_sucessos`, `>= 0`), manobra resolvida, estado de *Potência* (`passivePotenceDice`, `autoPotenceSuccesses` quando ativada por sangue no turno) e `targetStrength` (para `disarm_*`).
   - `netHits = totalSuccesses - defenseSuccesses`.
   - Se `netHits <= 0`: ataque evitado/sem efeito (`hit = false`).
   - Se `netHits >= 1`: `hit = true`, `carryOverDice = netHits - 1` (V20 p. 272: cada sucesso no ataque além do primeiro adiciona `+1` dado à parada de dano, inclusive para armas de fogo!).
   - Para manobras com dano (`not noDamage`):
     - Em ataques corpo a corpo (`brawl` / `melee`): quando *Potência* está apenas passiva, soma `meleePotenceDice = passivePotenceDice` aos dados rolados de dano (`autoSuccesses = 0`); quando *Potência* foi ativada com `1 Sangue` no turno (V20, p. 192), `meleePotenceDice = 0` e seus pontos entram como `autoSuccesses = autoPotenceSuccesses` somados aos dados rolados de `Força + Arma + Sucessos Extras`. Armas de fogo (`ranged`) **não** recebem Potência.
     - `damageDicePool = math.max(0, baseDamage + extraTargetedDice + carryOverDice + meleePotenceDice)` (garantindo ao menos `1` dado rolado quando `autoSuccesses == 0` e a manobra causa dano).
     - Dificuldade da rolagem de dano: sempre **`6`** (V20 p. 272), `ignoreWoundPenalty = true`, `forbidWillpower = true`.
   - Na ficha (`Adapter/firecast_bridge.lua`), acertar um ataque preenche `cmb_dano_pendente_parada`, `cmb_dano_pendente_auto`, `cmb_dano_pendente_tipo`, `cmb_dano_pendente_manobra`, `cmb_dano_pendente_resumo` e habilita o botão **`[Rolar Dano Encadeado]`** em 1 clique!

---

## 4. Painel `tablesDock` de Coterie & Iniciativa (`Core/coterie_tracker.lua`, `Adapter/coterie_dock_bridge.lua` & `Sheets/frmV20CoterieDock.lfm`)

### 4.1. Motor Puro do Rastreador (`Core/coterie_tracker.lua`)
1. **Ordenação Oficial de Iniciativa V20 (p. 271):**
   - `CoterieTracker.sortInitiativeEntries(entries, phase)`:
     - **`phase == "declaracao"` (Fase de Declaração):** ordena do **menor** `total` para o **maior** `total` (os mais lentos declaram suas ações primeiro, permitindo que os mais rápidos reajam!). Em empate de `total`, o **menor** `initMod` declara primeiro; persistindo empate, ordem alfabética determinística por `name` / `id` com flag `simultaneous = true`.
     - **`phase == "acao"` (Fase de Resolução/Ação):** ordena do **maior** `total` para o **menor** `total` (os mais rápidos resolvem primeiro!). Em empate de `total`, o **maior** `initMod` age primeiro; persistindo empate, marca `simultaneous = true`.
2. **Filtro de Privacidade em Duas Camadas (`CoterieTracker.buildPublicSummary` vs. `CoterieTracker.buildStorytellerCards`):**
   - **`computeApparentCondition(sheet)`:** mapeia o dano total e `isTorpor` apenas para rótulos visuais públicos sem números internos:
     - `0` níveis → `"Saudável"`
     - `1..2` níveis → `"Escoriado"`
     - `3..4` níveis → `"Ferido"`
     - `5..6` níveis → `"Gravemente Ferido"`
     - `>= 7` níveis ou `em_torpor` → `"Incapacitado / Torpor"`
   - **`buildPublicSummary(libraryCharacters)`:**
     - Filtra estritamente `char.visible == true` (descarta qualquer item com `visivel == false` ou `visivelRecursivamente == false`).
     - Retorna apenas `{ key, nome, condicao_aparente }`. **Proibido** incluir `sangue_atual`, `sangue_max`, `fdv_temp`, `fdv_perm`, `cla_id`, `geracao`, `moralidade_val`, `xp_*` ou notas.
   - **`filterPublicInitiative(entries, isStoryteller)`:**
     - Se `isStoryteller == true`: retorna todos os combatentes (exibindo tag `[Oculto]` nos invisíveis).
     - Se `isStoryteller == false`: omite combatentes marcados com `hidden == true` até que o Narrador desmarque sua ocultação.
   - **`buildStorytellerCards(libraryCharacters, page, pageSize)`:**
     - Paginação determinística (`pageSize = 8`, `totalPages = math.max(1, math.ceil(#all / 8))`).
     - Retorna para cada um dos até 8 slots da página: `nome`, `cla_titulo`, `geracao`, `sangue_txt` (`"X/Y (Turno: Z/Max)"`), `fdv_txt` (`"Temp/Perm"`), `vitalidade_txt`, `moralidade_txt`, `flags_txt` (`[Oculto]`, `[Frenesi]`, `[Agarrão]`, `[XP Pendente]`), `hasPendingXP`, `isVampire`, `nodeRef`.

### 4.2. Integração com a Sala do Firecast (`Adapter/coterie_dock_bridge.lua`)
1. **Conexão Segura ao NDB Público da Sala (`v20_coterie_dock_v1`):**
   - Em `OnShow` de `frmV20CoterieDock`, `CoterieDockBridge.connectDock(formObj, firecastApi, ndbApi)` obtém `mesa = Firecast.getMesaDe(formObj)` e chama `mesa:abrirNDBDeMesa("v20_coterie_dock_v1", callback, { criar = true })` (com fallback em memória `NDB.newMemNodeDatabase()` ou tabela Lua quando fora de sala/em testes).
   - Registra `formObj` em um conjunto fraco/controlado e cria `NDB.newObserver(roomNode)` para atualizar o HUD em tempo real.
   - Em `OnHide` (e antes de `destroy()`), `CoterieDockBridge.disconnectDock(formObj)` desativa todos os `NDB.newObserver` (tanto do `roomNode` quanto dos `charNode`s abertos pelo Narrador) evitando qualquer vazamento de memória ou callbacks órfãos.
2. **Alimentação Automática da Iniciativa a partir de `Bridge.rollInitiative`:**
   - Quando qualquer ficha rola `Bridge.rollInitiative(sheet, fc, dlg)`, após obter `d10 + mod = total`, se `mesa ~= nil and mesa.abrirNDBDeMesa ~= nil`, grava/atualiza a entrada do personagem em `v20_coterie_dock_v1` (`id` baseado em `bibItem.codigoInterno` ou `sheet.nome`, `name`, `d10`, `initMod`, `total`, `hidden = (bibItem and bibItem.visivelRecursivamente == false) or false`) e reordena os 10 slots públicos visíveis.
   - O Narrador também dispõe na Aba 1 do Dock de campos rápidos (`npc_init_nome`, `npc_init_mod`, `npc_init_oculto`) + botão **`[+ Rolar NPC]`**, além de **`[Alternar Declaração / Ação]`** e **`[Limpar Iniciativa]`**.
3. **Inspeção da Biblioteca e Comandos em Lote do Narrador (`isMestre == true`):**
   - `CoterieDockBridge.scanLibrarySheets(mesa, onUpdated)` percorre recursivamente `mesa.biblioteca.filhos` procurando itens com `tipo == "personagem"` e `tostring(item.dataType):sub(1, 11) == "br.com.v20."` (excluindo `br.com.v20.CoterieDock`).
   - Para cada personagem encontrado, chama `item:loadSheetNDB(callback)` e registra um `NDB.newObserver` leve enquanto o Dock do Narrador estiver visível.
   - **Ações Individuais nos 8 Cartões do Narrador (`st_card1..8`):**
     - `[-1🩸]` / `[+1🩸]`: chama `V20Bridge.adjustResource(charNode, "sangue_atual", delta)` (apenas em vampiros/carniçais);
     - `[Aprovar XP]`: visível quando `charNode.xp_pendente_status == "pendente"`, executando `V20Bridge.submitOrApproveXP(charNode, "approve")` diretamente pelo Dock!
   - **Ações Globais em Lote do Narrador (apenas sobre fichas com `isMestre == true`):**
     - **`[🌙 Despertar Noturno da Coterie]`:** executa `V20.WillpowerMorality.awakenNightly` + sincronia em todos os personagens vampiros visíveis (ou todos os PJs vampiros carregados), registrando um único boletim consolidado no chat da sala;
     - **`[🔄 Novo Turno (+1 Rodada)]`:** executa `V20Bridge.newTurn(charNode)` em todas as fichas carregadas, incrementa `rodada_atual` em `v20_coterie_dock_v1` e muda `combate_fase = "declaracao"`;
     - **`[🧹 Encerrar Cena]`:** limpa buffs de cena (`clearSceneBuffs` silencioso + 1 mensagem única da Coterie no chat), zera `em_agarrao` e reseta o contador de rodada.

---

## 5. Polimentos Incorporados & Plano de Testes (`v1.0.0`)

1. **Polimentos da Revisão do Subprojeto 2:**
   - `tools/build_v20_suite.py`: adiciona argumento opcional `--output-dir <path>` (padrão `dist/`). `Tests/test_09_rpk_package.py` passa um diretório temporário `[TESTE_E2E]` limpo no `finally:`, garantindo que `python Tests/run_tests.py` jamais altere os timestamps de `dist/Vampiro_V20_Suite.{rpk,rdk}`.
   - `Adapter/firecast_bridge.lua`: `updateDisciplineSummaries` e `Bridge.activateDisciplineSlot` delegam `thaumaturgy` e `necromancy` em fichas vampíricas para `V20.BloodMagicEngine.getPathTable` / `Bridge.activatePrimaryBloodMagic`, unificando Aba 3 e Aba 8 (incluindo o aviso de `-1 FdV Permanente` em falha crítica de Taumaturgia).
   - `Templates/theme_gothic.py`: `cmbBmThauPrimId` e `cmbBmNecroPrimId` saem do bloqueio fixo e só travam em `modo_ficha == "jogo"` quando `bm_thau_prim_nivel > 0` (respectivamente `bm_necro_prim_nivel > 0`).
2. **Suítes Automatizadas (`13/13` em `Tests/run_tests.py` com isolamento `[TESTE_E2E]`):**
   - `Tests/test_12_combat_maneuvers.lua`: exercita divisão de paradas pela menor parada (2, 3+ ações, bloqueio em parada `<= 0`), isenção das ações extras de *Rapidez*, as 20 manobras do catálogo (Mordida Agravada com trava de Agarrão, Garras Agravadas com Metamorfose 2 vs Letal, Agarrão/Segurar, Desarmar vs Força, Estaca dif. 9 com alerta de paralisia em `>= 3` níveis, Rajada Curta `+2d/+1 dif`, Rajada Completa `+10d/+2 dif`, Mira limitada à Percepção, Cabeça tornando arma de fogo Letal, Cobertura/Flanco, Defesas Ativas cumulativas `-1`) e encadeamento *Ataque → Sucessos Líquidos → Dano + Potência*.
   - `Tests/test_13_coterie_tracker.lua`: valida ordenação V20 de Iniciativa (`declaracao` ascendente vs `acao` descendente + desempate por `initMod`), ocultação estrita de dados privados e NPCs invisíveis na camada pública de jogadores, cartões paginados do Narrador e operações em lote (*Despertar Noturno*, *Novo Turno*, *Encerrar Cena* e *Aprovar XP*).
   - `Tests/test_08_bridge_and_lfm_gen.py` & `Tests/test_09_rpk_package.py`: atualizados para validar os **16 formulários** (`15 sheetTemplate + 1 tablesDock`), presença de `Firecast.registrarSpecialForm` apenas no `tablesDock`, ciclo `OnShow`/`OnHide`/`destroy()` sem vazamento de `NDB.newObserver` ou listeners, e empacotamento final de `dist/Vampiro_V20_Suite.rpk` (`v1.0.0`).
