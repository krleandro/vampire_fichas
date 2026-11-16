# Vampiro V20 Firecast Suite (Subproject 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir o pacote instalável `dist/Vampiro_V20_Suite.rpk` (`v0.2.0`, SDK 3.7b / Lua 5.4) contendo o Motor Universal completo de Vampiro: A Máscara V20 (17 Disciplinas Níveis 1–5 in-clan e out-of-clan, todos os Antecedentes, Geração 4ª–15ª, Vitalidade, Moralidade, Criação e XP auditado) e as fichas automatizadas `Vampiro V20 - Brujah` (`br.com.v20.Brujah`) e `Vampiro V20 - Mortal` (`br.com.v20.Mortal`, com evolução oculta para Carniçal/Numina).

**Architecture:** Camada pura de regras e catálogos declarativos em Lua 5.4 (`Data/` e `Core/`) desacoplada da UI e executada/testada diretamente na DLL oficial `lua54x64.dll` do Firecast; camada de adaptação (`Adapter/firecast_bridge.lua`) integrando `NodeDatabase`, detecção de Narrador (`isMestre`) e rolagens anti-cheat via `rolado.ops`; e geradores parametrizados em Python (`Templates/` + `tools/build_v20_suite.py`) produzindo os `.lfm`, `.lfm.lua` e `module.xml` assemblado multi-`dataType`.

**Tech Stack:** Lua 5.4 (validado e executado via `C:\Users\Cliente\AppData\Local\Firecast\lua54x64.dll` com `ctypes`), RRPG Firecast SDK 3.7b (`sdkApiVersion="88"`, `sdkMinorApiVersion="2"`), Python 3.x (geração LFM, compilador `.lfm.lua`, suíte de testes e empacotador `.rpk`).

**Spec:** `docs/superpowers/specs/2026-11-16-v20-firecast-subproject1-design.md`

## Global Constraints

- **Referência Mecânica Exclusiva:** *Vampire: The Masquerade — 20th Anniversary Edition (V20 Corebook)* sem misturar regras da 1ª/2ª Edição ou Revised (ex.: Falha Crítica estritamente quando `rawSuccesses == 0 and autoSuccesses == 0 and ones > 0`; Especialidade `10 = 2 sucessos` sem explosão).
- **Idioma da Interface:** Português Brasileiro (`pt-BR`) em todos os rótulos, mensagens de chat e diagnósticos, mantendo IDs internos estáveis em ASCII/inglês (`potence`, `celerity`, `attr_forca`, etc.).
- **Isolamento de Sandbox em Testes (`[TESTE_E2E]`):** Todos os personagens, fichas simuladas e registros criados nas suítes `Tests/` DEVEM obrigatoriamente usar o prefixo `[TESTE_E2E]` em `nome`/`titulo` (ex.: `"[TESTE_E2E] Jack Brujah"`) e encerrar o estado Lua (`lua_close`) ao término de cada execução sem deixar resíduos em disco.
- **Regras Estritas de Compilação Firecast SDK 3.7b:**
  1. Usar `rawset(obj, "_oldSetNodeObjectFunction", obj.setNodeObject);` (jamais `rawget`);
  2. Posicionar todos os `<dataLink>` como filhos diretos da raiz `<form>`;
  3. Definir `cacheMode = "none"` no registro de cada formulário;
  4. Usar exclusivamente `"leading"`, `"center"` ou `"trailing"` em `horzTextAlign` e `vertTextAlign` (jamais `"left"` ou `"right"`);
  5. Destruir controles e listeners em ordem estritamente reversa em `obj:destroy()`;
  6. Jamais quebrar linhas literais dentro de strings Lua `"..."` em blocos `<script>` ou `<event>`;
  7. Incluir `_rdkCompiledLang.cln` na raiz do `.rpk` e os binários/scripts do SDK 3.7b dentro da subpasta `sdk/` copiados de `c:\Users\Cliente\OneDrive\Documentos\event\firecast_event_ficha\`.
- **Direitos Autorais:** Usar resumos mecânicos próprios concisos + referência de página do livro V20, nunca copiando parágrafos literais do livro.

---

## Mapa de Arquivos do Subprojeto 1

- `Tests/run_tests.py`: Executor de testes em Python que carrega `lua54x64.dll` via `ctypes`, abre as bibliotecas padrão Lua 5.4 (`luaL_openlibs`), configura `package.path` para a raiz do repositório e executa todos os arquivos `Tests/test_*.lua` e `Tests/test_*.py`.
- `Data/attributes_abilities.lua`: Catálogo imutável dos 9 Atributos e 30 Habilidades V20 + regras de dificuldade para Habilidade `0` (`talents = 0`, `skills = +1 diff`, `knowledges = bloqueado`).
- `Core/dice.lua`: Construção de paradas efetivas (`Dice.buildPool`) e avaliação oficial V20 (`Dice.evaluate`).
- `Data/generations.lua`: Tabela oficial da 4ª à 15ª Geração (`traitMax`, `discMax`, `bloodMax`, `usableBlood`, `perTurn`, `doubleDisciplineHealingCost`).
- `Core/generation_blood.lua`: Derivação de status sanguíneos, gasto por turno (com exceção de *Rapidez*), ganho de sangue e *Blood Buff* físico.
- `Core/health.lua`: Trilha de 7 (+1) níveis de Vitalidade, ordenação `* > X > /`, conversão de transbordo Contundente → Letal, penalidades, regras Vampiro vs Mortal e cura vampírica.
- `Data/clans.lua`: Configuração dos 13 Clãs + Caitiff (nome PT-BR, 3 disciplinas de clã, ID e regra de fraqueza, paleta gótica).
- `Data/morality_virtues.lua`: Virtudes, Humanidade/Trilhas da Sabedoria, tabela de Aura Social e estímulos oficiais de Frenesi e Rötschreck.
- `Core/willpower_morality.lua`: Operações de Força de Vontade, Aura, Despertar Noturno, Frenesi (incluindo fraqueza Brujah `+2 dif` sem esquiva por FdV), Rötschreck e Degeneração.
- `Data/disciplines_catalog.lua`: Catálogo estruturado das 17 Disciplinas Clássicas da V20 (Níveis 1 a 5 = 85 poderes com custos, paradas, dificuldades e *buffs* de cena).
- `Core/disciplines_engine.lua`: Validação de compra/nível (in-clan, out-of-clan, Caitiff, Carniçal), ativação de poderes, aplicação de *Potência*, *Rapidez*, *Fortitude* e *buffs* ativos.
- `Data/backgrounds_catalog.lua` & `Data/merits_flaws_catalog.lua`: Catálogo dos Antecedentes V20, Qualidades, Defeitos e Numina.
- `Core/backgrounds_engine.lua`: Derivação de Geração por Antecedente, parada de Caça (`Rebanho + Domínio`), renda de `Recursos`, modificadores de `Fama`/`Status`, rolagens de rede e agregador de modificadores de Qualidades/Defeitos.
- `Core/creation.lua` & `Core/experience.lua` & `Core/v20_init.lua`: Validador de criação Vampiro (`7/5/3`) e Mortal (`6/4/3` ou `7/5/3`), transição Mortal → Carniçal/Numina, calculadora de XP V20, fila de aprovação do Narrador e inicializador global `V20`.
- `Adapter/firecast_bridge.lua`: Ponte com `Firecast`, `NDB` e `Dialogs` para rolagens no chat (`rolado.ops`), sincronização reativa do nó `sheet`, permissões `isMestre` e gravação de auditoria.
- `Templates/theme_gothic.py`, `Templates/generate_vampire_lfm.py`, `Templates/generate_mortal_lfm.py`: Geradores determinísticos de `Sheets/frmBrujah.lfm` e `Sheets/frmMortal.lfm`.
- `module.xml` & `tools/build_v20_suite.py`: Manifesto base e construtor multi-`dataType` que gera `dist/Vampiro_V20_Suite.rpk` e `.rdk`.

---

### Task 1: Executor Lua 5.4 Nativo (`lua54x64.dll`), Catálogo de Características e Motor de Dados V20

**Files:**
- Create: `Tests/run_tests.py`
- Create: `Data/attributes_abilities.lua`
- Create: `Core/dice.lua`
- Test: `Tests/test_01_dice.lua`

**Interfaces:**
- Consumes: `C:\Users\Cliente\AppData\Local\Firecast\lua54x64.dll`
- Produces:
  - `AttributesAbilities.ATTRIBUTES`: tabela mapeando IDs (`attr_forca`..`attr_raciocinio`) para `{ id, name, category }`
  - `AttributesAbilities.ABILITIES`: tabela mapeando IDs (`hab_prontidao`..`hab_tecnologia`) para `{ id, name, category }` (`"talents" | "skills" | "knowledges"`)
  - `AttributesAbilities.getZeroRankRule(category)` -> `{ allowed = boolean, diffMod = number, reason = string|nil }`
  - `Dice.buildPool(params)` -> `{ canRoll = boolean, pool = number, effectiveDifficulty = number, autoSuccesses = number, warnings = string[], blockReason = string|nil }`
  - `Dice.evaluate(results, difficulty, options)` -> `{ rawSuccesses = number, ones = number, rolledNet = number, autoSuccesses = number, totalSuccesses = number, outcome = "botch"|"failure"|"success", degree = string, difficulty = number, diceCount = number }`

- [ ] **Step 1: Criar o executor `Tests/run_tests.py` e o teste falho `Tests/test_01_dice.lua`**

Criar `Tests/run_tests.py`:
```python
#!/usr/bin/env python3
"""Executa suítes Lua 5.4 diretamente na lua54x64.dll do Firecast e testes Python."""
import ctypes
import glob
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

DLL_PATH = r"C:\Users\Cliente\AppData\Local\Firecast\lua54x64.dll"
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def run_lua_file(lua_file: str) -> None:
    if not os.path.exists(DLL_PATH):
        raise RuntimeError(f"lua54x64.dll não encontrada em {DLL_PATH}")

    dll = ctypes.CDLL(DLL_PATH)
    dll.luaL_newstate.restype = ctypes.c_void_p
    dll.luaL_openlibs.argtypes = [ctypes.c_void_p]
    dll.luaL_loadbufferx.argtypes = [
        ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p, ctypes.c_char_p
    ]
    dll.luaL_loadbufferx.restype = ctypes.c_int
    dll.lua_pcallk.argtypes = [
        ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ssize_t, ctypes.c_void_p
    ]
    dll.lua_pcallk.restype = ctypes.c_int
    dll.lua_tolstring.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_size_t)]
    dll.lua_tolstring.restype = ctypes.c_char_p
    dll.lua_close.argtypes = [ctypes.c_void_p]

    L = dll.luaL_newstate()
    try:
        dll.luaL_openlibs(L)
        root_escaped = ROOT_DIR.replace("\\", "/")
        bootstrap = (
            f'package.path = "{root_escaped}/?.lua;{root_escaped}/?/init.lua;" .. package.path\n'
            f'dofile("{os.path.abspath(lua_file).replace(chr(92), "/")}")\n'
        ).encode("utf-8")

        rc = dll.luaL_loadbufferx(L, bootstrap, len(bootstrap), b"@bootstrap", b"t")
        if rc != 0:
            ln = ctypes.c_size_t(0)
            msg = dll.lua_tolstring(L, -1, ctypes.byref(ln)).decode("utf-8", errors="replace")
            raise AssertionError(f"Erro de compilação em {lua_file}: {msg}")

        rc = dll.lua_pcallk(L, 0, 0, 0, 0, None)
        if rc != 0:
            ln = ctypes.c_size_t(0)
            msg = dll.lua_tolstring(L, -1, ctypes.byref(ln)).decode("utf-8", errors="replace")
            raise AssertionError(f"Falha em {lua_file}:\n{msg}")
        print(f"[PASS] {os.path.relpath(lua_file, ROOT_DIR)}")
    finally:
        dll.lua_close(L)


def main() -> int:
    targets = sys.argv[1:] if len(sys.argv) > 1 else sorted(
        glob.glob(os.path.join(ROOT_DIR, "Tests", "test_*.lua"))
        + glob.glob(os.path.join(ROOT_DIR, "Tests", "test_*.py"))
    )
    if not targets:
        print("Nenhum teste encontrado.")
        return 1

    for target in targets:
        if target.endswith(".lua"):
            run_lua_file(target)
        elif target.endswith(".py") and os.path.abspath(target) != os.path.abspath(__file__):
            res = subprocess.run([sys.executable, target], cwd=ROOT_DIR)
            if res.returncode != 0:
                return res.returncode
            print(f"[PASS] {os.path.relpath(target, ROOT_DIR)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Criar `Tests/test_01_dice.lua`:
```lua
local Traits = require("Data.attributes_abilities")
local Dice = require("Core.dice")

-- 1. Catálogo completo: 9 atributos e 30 habilidades
assert(#Traits.ATTRIBUTE_ORDER == 9, "Esperado 9 atributos")
assert(#Traits.ABILITY_ORDER == 30, "Esperado 30 habilidades")
assert(Traits.ATTRIBUTES.attr_forca.name == "Força")
assert(Traits.ABILITIES.hab_investigacao.category == "knowledges")

-- 2. Regra V20 crítica: [8, 1] na dif 6 é FALHA SIMPLES, nunca Botch!
local r1 = Dice.evaluate({8, 1}, 6, {})
assert(r1.rawSuccesses == 1, "rawSuccesses deveria ser 1")
assert(r1.totalSuccesses == 0, "totalSuccesses deveria ser 0")
assert(r1.outcome == "failure", "Em V20, ter sucesso cancelado por 1 é falha simples, não botch!")

-- 3. Falha Crítica (Botch) real: zero sucessos brutos e pelo menos um 1
local r2 = Dice.evaluate({4, 5, 1}, 6, {})
assert(r2.outcome == "botch", "Zero sucessos brutos com 1 deve ser botch")

-- 4. Especialidade: 10 vale 2 sucessos, e um 1 cancela apenas 1 deles
local r3 = Dice.evaluate({10, 1}, 6, { specialty = true })
assert(r3.rawSuccesses == 2)
assert(r3.totalSuccesses == 1)
assert(r3.outcome == "success")

-- 5. Gasto de Força de Vontade (+1 sucesso automático imune a 1s e imune a botch)
local r4 = Dice.evaluate({1, 1, 2}, 6, { spendWillpower = true })
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

local pKnow0 = Dice.buildPool({
    actorName = "[TESTE_E2E] Jack Brujah",
    attrVal = 4,
    abilityVal = 0,
    abilityCategory = "knowledges",
    difficulty = 6,
})
assert(pKnow0.canRoll == false, "Conhecimento 0 não pode testar sem autorização do Narrador")

local pAbsorb = Dice.buildPool({
    actorName = "[TESTE_E2E] Jack Brujah",
    attrVal = 4,
    abilityVal = 2,
    difficulty = 6,
    woundPenalty = -5,
    ignoreWoundPenalty = true,
})
assert(pAbsorb.pool == 6, "Absorção deve ignorar penalidade de ferimento")
```

- [ ] **Step 2: Rodar o teste para confirmar falha inicial**

Executar: `python Tests/run_tests.py Tests/test_01_dice.lua`  
Resultado esperado: `FAIL` com `module 'Data.attributes_abilities' not found`.

- [ ] **Step 3: Implementar `Data/attributes_abilities.lua` e `Core/dice.lua`**

Criar `Data/attributes_abilities.lua`:
```lua
local AttributesAbilities = {}

AttributesAbilities.ATTRIBUTE_ORDER = {
    "attr_forca", "attr_destreza", "attr_vigor",
    "attr_carisma", "attr_manipulacao", "attr_aparencia",
    "attr_percepcao", "attr_inteligencia", "attr_raciocinio",
}

AttributesAbilities.ATTRIBUTES = {
    attr_forca        = { id = "attr_forca",        name = "Força",        category = "physical" },
    attr_destreza     = { id = "attr_destreza",     name = "Destreza",     category = "physical" },
    attr_vigor        = { id = "attr_vigor",        name = "Vigor",        category = "physical" },
    attr_carisma      = { id = "attr_carisma",      name = "Carisma",      category = "social" },
    attr_manipulacao  = { id = "attr_manipulacao",  name = "Manipulação",  category = "social" },
    attr_aparencia    = { id = "attr_aparencia",    name = "Aparência",    category = "social" },
    attr_percepcao    = { id = "attr_percepcao",    name = "Percepção",    category = "mental" },
    attr_inteligencia = { id = "attr_inteligencia", name = "Inteligência", category = "mental" },
    attr_raciocinio   = { id = "attr_raciocinio",   name = "Raciocínio",   category = "mental" },
}

AttributesAbilities.ABILITY_ORDER = {
    -- Talentos (10)
    "hab_prontidao", "hab_esportes", "hab_consciencia", "hab_briga", "hab_empatia",
    "hab_expressao", "hab_intimidacao", "hab_lideranca", "hab_manha", "hab_labia",
    -- Perícias (10)
    "hab_empatia_animais", "hab_oficios", "hab_conducao", "hab_etiqueta", "hab_armas_fogo",
    "hab_arrombamento", "hab_armas_brancas", "hab_performance", "hab_furtividade", "hab_sobrevivencia",
    -- Conhecimentos (10)
    "hab_academicos", "hab_computador", "hab_financas", "hab_investigacao", "hab_direito",
    "hab_medicina", "hab_ocultismo", "hab_politica", "hab_ciencias", "hab_tecnologia",
}

AttributesAbilities.ABILITIES = {
    hab_prontidao       = { id = "hab_prontidao",       name = "Prontidão",           category = "talents" },
    hab_esportes        = { id = "hab_esportes",        name = "Esportes",            category = "talents" },
    hab_consciencia     = { id = "hab_consciencia",     name = "Consciência",         category = "talents" },
    hab_briga           = { id = "hab_briga",           name = "Briga",               category = "talents" },
    hab_empatia         = { id = "hab_empatia",         name = "Empatia",             category = "talents" },
    hab_expressao       = { id = "hab_expressao",       name = "Expressão",           category = "talents" },
    hab_intimidacao     = { id = "hab_intimidacao",     name = "Intimidação",         category = "talents" },
    hab_lideranca       = { id = "hab_lideranca",       name = "Liderança",           category = "talents" },
    hab_manha           = { id = "hab_manha",           name = "Manha",               category = "talents" },
    hab_labia           = { id = "hab_labia",           name = "Lábia",               category = "talents" },

    hab_empatia_animais = { id = "hab_empatia_animais", name = "Empatia com Animais", category = "skills" },
    hab_oficios         = { id = "hab_oficios",         name = "Ofícios",             category = "skills" },
    hab_conducao        = { id = "hab_conducao",        name = "Condução",            category = "skills" },
    hab_etiqueta        = { id = "hab_etiqueta",        name = "Etiqueta",            category = "skills" },
    hab_armas_fogo      = { id = "hab_armas_fogo",      name = "Armas de Fogo",       category = "skills" },
    hab_arrombamento    = { id = "hab_arrombamento",    name = "Arrombamento",        category = "skills" },
    hab_armas_brancas   = { id = "hab_armas_brancas",   name = "Armas Brancas",       category = "skills" },
    hab_performance     = { id = "hab_performance",     name = "Performance",         category = "skills" },
    hab_furtividade     = { id = "hab_furtividade",     name = "Furtividade",         category = "skills" },
    hab_sobrevivencia   = { id = "hab_sobrevivencia",   name = "Sobrevivência",       category = "skills" },

    hab_academicos      = { id = "hab_academicos",      name = "Acadêmicos",          category = "knowledges" },
    hab_computador      = { id = "hab_computador",      name = "Computador",          category = "knowledges" },
    hab_financas        = { id = "hab_financas",        name = "Finanças",            category = "knowledges" },
    hab_investigacao    = { id = "hab_investigacao",    name = "Investigação",        category = "knowledges" },
    hab_direito         = { id = "hab_direito",         name = "Direito",             category = "knowledges" },
    hab_medicina        = { id = "hab_medicina",        name = "Medicina",            category = "knowledges" },
    hab_ocultismo       = { id = "hab_ocultismo",       name = "Ocultismo",           category = "knowledges" },
    hab_politica        = { id = "hab_politica",        name = "Política",            category = "knowledges" },
    hab_ciencias        = { id = "hab_ciencias",        name = "Ciências",            category = "knowledges" },
    hab_tecnologia      = { id = "hab_tecnologia",      name = "Tecnologia",          category = "knowledges" },
}

function AttributesAbilities.getZeroRankRule(category)
    if category == "skills" then
        return { allowed = true, diffMod = 1, reason = "Perícia sem pontos: +1 na dificuldade (V20, p. 253)." }
    elseif category == "knowledges" then
        return { allowed = false, diffMod = 0, reason = "Conhecimento sem pontos não pode ser testado sem autorização do Narrador (V20, p. 253)." }
    end
    return { allowed = true, diffMod = 0, reason = nil }
end

return AttributesAbilities
```

Criar `Core/dice.lua`:
```lua
local Traits = require("Data.attributes_abilities")

local Dice = {}

local function clamp(val, minV, maxV)
    if val < minV then return minV end
    if val > maxV then return maxV end
    return val
end

local function degreeLabel(total)
    if total <= 0 then return "Nenhum" end
    if total == 1 then return "Marginal" end
    if total == 2 then return "Moderado" end
    if total == 3 then return "Completo" end
    if total == 4 then return "Excepcional" end
    return "Fenomenal"
end

function Dice.buildPool(params)
    params = params or {}
    local warnings = {}
    local attrVal = tonumber(params.attrVal) or 0
    local abilityVal = tonumber(params.abilityVal) or 0
    local bonusDice = tonumber(params.bonusDice) or 0
    local diff = tonumber(params.difficulty) or 6
    local diffMod = tonumber(params.difficultyMod) or 0
    local autoSuccesses = tonumber(params.autoSuccesses) or 0
    if params.spendWillpower then
        autoSuccesses = autoSuccesses + 1
    end

    if params.incapacitated and not params.ignoreWoundPenalty and not params.storytellerOverride then
        return {
            canRoll = false,
            pool = 0,
            effectiveDifficulty = clamp(diff, 2, 10),
            autoSuccesses = autoSuccesses,
            warnings = warnings,
            blockReason = "Personagem Incapacitado não pode realizar ações físicas.",
        }
    end

    if params.abilityCategory and abilityVal <= 0 then
        local rule = Traits.getZeroRankRule(params.abilityCategory)
        if not rule.allowed and not params.storytellerOverride then
            return {
                canRoll = false,
                pool = 0,
                effectiveDifficulty = clamp(diff, 2, 10),
                autoSuccesses = autoSuccesses,
                warnings = warnings,
                blockReason = rule.reason,
            }
        end
        if rule.diffMod ~= 0 then
            diffMod = diffMod + rule.diffMod
            table.insert(warnings, rule.reason)
        end
    end

    local woundPen = 0
    if not params.ignoreWoundPenalty then
        woundPen = math.abs(tonumber(params.woundPenalty) or 0)
    end

    local pool = attrVal + abilityVal + bonusDice - woundPen
    local effectiveDiff = clamp(diff + diffMod, 2, 10)

    if pool <= 0 and autoSuccesses <= 0 and not params.storytellerOverride then
        return {
            canRoll = false,
            pool = 0,
            effectiveDifficulty = effectiveDiff,
            autoSuccesses = 0,
            warnings = warnings,
            blockReason = "Parada reduzida a zero ou menos pelas penalidades.",
        }
    end

    return {
        canRoll = true,
        pool = math.max(0, pool),
        effectiveDifficulty = effectiveDiff,
        autoSuccesses = autoSuccesses,
        warnings = warnings,
        blockReason = nil,
    }
end

function Dice.evaluate(results, difficulty, options)
    options = options or {}
    local diff = clamp(tonumber(difficulty) or 6, 2, 10)
    local specialty = options.specialty == true
    local autoSuccesses = tonumber(options.autoSuccesses) or 0
    if options.spendWillpower then
        autoSuccesses = autoSuccesses + 1
    end

    local rawSuccesses = 0
    local ones = 0
    results = results or {}

    for _, v in ipairs(results) do
        local face = tonumber(v) or 0
        if face == 1 then
            ones = ones + 1
        elseif face >= diff then
            if face == 10 and specialty then
                rawSuccesses = rawSuccesses + 2
            else
                rawSuccesses = rawSuccesses + 1
            end
        end
    end

    local rolledNet = math.max(0, rawSuccesses - ones)
    local totalSuccesses = rolledNet + autoSuccesses

    local outcome = "failure"
    if totalSuccesses > 0 then
        outcome = "success"
    elseif rawSuccesses == 0 and autoSuccesses == 0 and ones > 0 then
        outcome = "botch"
    end

    return {
        rawSuccesses = rawSuccesses,
        ones = ones,
        rolledNet = rolledNet,
        autoSuccesses = autoSuccesses,
        totalSuccesses = totalSuccesses,
        outcome = outcome,
        degree = degreeLabel(totalSuccesses),
        difficulty = diff,
        diceCount = #results,
    }
end

return Dice
```

- [ ] **Step 4: Rodar o teste e confirmar aprovação**

Executar: `python Tests/run_tests.py Tests/test_01_dice.lua`  
Resultado esperado: `[PASS] Tests\test_01_dice.lua` (exit code 0).

- [ ] **Step 5: Commit**

```bash
git add Tests/run_tests.py Data/attributes_abilities.lua Core/dice.lua Tests/test_01_dice.lua
git commit -m "feat(core): add native lua54x64 test runner, V20 traits catalog and dice engine"
```

---

### Task 2: Gerações (4ª–15ª), Reserva de Sangue, Limite por Turno e *Blood Buff* Físico

**Files:**
- Create: `Data/generations.lua`
- Create: `Core/generation_blood.lua`
- Test: `Tests/test_02_generation_blood.lua`

**Interfaces:**
- Produces:
  - `Generations.get(genNumber)` -> `{ generation, traitMax, discMax, bloodMax, usableBlood, perTurn, doubleCost }`
  - `Blood.deriveStats(genNumber)` -> mesma tabela com fallback seguro para `13ª`
  - `Blood.spend(state, amount, opts)` -> `{ ok = boolean, newState = table, costApplied = number, error = string|nil }` (`opts.bypassTurnLimit` true para *Rapidez*; `opts.forDisciplineOrHeal` aplica teto `usableBlood` e custo dobrado na 15ª)
  - `Blood.gain(state, amount)` -> `{ newState = table, added = number }`
  - `Blood.newTurn(state)` -> `newState` (zera `spentThisTurn`)
  - `Blood.applyPhysicalBuff(state, attrKey)` -> `{ ok = boolean, newState = table, effectiveAttr = number, temporaryAboveMax = boolean, error = string|nil }`
  - `Blood.clearSceneBuffs(state)` -> `newState`

- [ ] **Step 1: Escrever o teste falho `Tests/test_02_generation_blood.lua`**

```lua
local Blood = require("Core.generation_blood")

-- 1. Derivação de 13ª, 8ª, 4ª e 15ª Geração
local g13 = Blood.deriveStats(13)
assert(g13.bloodMax == 10 and g13.perTurn == 1 and g13.traitMax == 5)

local g4 = Blood.deriveStats(4)
assert(g4.bloodMax == 50 and g4.perTurn == 10 and g4.traitMax == 9)

local g15 = Blood.deriveStats(15)
assert(g15.bloodMax == 10 and g15.usableBlood == 6 and g15.discMax == 3 and g15.doubleCost == true)

-- 2. Gasto respeitando limite por turno e exceção de Rapidez
local st = { generation = 13, currentBlood = 10, spentThisTurn = 0, attr_forca = 3, buff_forca = 0 }
local res1 = Blood.spend(st, 1, { forDisciplineOrHeal = true })
assert(res1.ok == true and res1.newState.currentBlood == 9 and res1.newState.spentThisTurn == 1)

local res2 = Blood.spend(res1.newState, 1, { forDisciplineOrHeal = true })
assert(res2.ok == false, "13ª geração não pode gastar 2 pontos normais no mesmo turno")

local resCel = Blood.spend(res1.newState, 2, { bypassTurnLimit = true, forDisciplineOrHeal = true })
assert(resCel.ok == true and resCel.newState.currentBlood == 7, "Rapidez pode exceder limite por turno na V20")

-- 3. 15ª Geração (Sangue Fraco): custo dobrado e teto utilizável
local st15 = { generation = 15, currentBlood = 10, spentThisTurn = 0 }
local r15 = Blood.spend(st15, 1, { forDisciplineOrHeal = true, bypassTurnLimit = true })
assert(r15.ok == true and r15.costApplied == 2 and r15.newState.currentBlood == 8)

-- 4. Blood Buff Físico até traitMax + 1
local stBuff = { generation = 13, currentBlood = 10, spentThisTurn = 0, attr_forca = 5, buff_forca = 0 }
local b1 = Blood.applyPhysicalBuff(stBuff, "forca")
assert(b1.ok == true and b1.effectiveAttr == 6 and b1.temporaryAboveMax == true)

local b2 = Blood.newTurn(b1.newState)
local b3 = Blood.applyPhysicalBuff(b2, "forca")
assert(b3.ok == false, "Não pode ultrapassar traitMax + 1 com Blood Buff")
```

- [ ] **Step 2: Rodar o teste para confirmar falha**

Executar: `python Tests/run_tests.py Tests/test_02_generation_blood.lua`  
Resultado esperado: `FAIL` com `module 'Core.generation_blood' not found`.

- [ ] **Step 3: Implementar `Data/generations.lua` e `Core/generation_blood.lua`**

Criar `Data/generations.lua`:
```lua
local Generations = {}

Generations.TABLE = {
    [4]  = { generation = 4,  traitMax = 9, discMax = 9, bloodMax = 50, usableBlood = 50, perTurn = 10, doubleCost = false },
    [5]  = { generation = 5,  traitMax = 8, discMax = 8, bloodMax = 40, usableBlood = 40, perTurn = 8,  doubleCost = false },
    [6]  = { generation = 6,  traitMax = 7, discMax = 7, bloodMax = 30, usableBlood = 30, perTurn = 6,  doubleCost = false },
    [7]  = { generation = 7,  traitMax = 6, discMax = 6, bloodMax = 20, usableBlood = 20, perTurn = 4,  doubleCost = false },
    [8]  = { generation = 8,  traitMax = 5, discMax = 5, bloodMax = 15, usableBlood = 15, perTurn = 3,  doubleCost = false },
    [9]  = { generation = 9,  traitMax = 5, discMax = 5, bloodMax = 14, usableBlood = 14, perTurn = 2,  doubleCost = false },
    [10] = { generation = 10, traitMax = 5, discMax = 5, bloodMax = 13, usableBlood = 13, perTurn = 1,  doubleCost = false },
    [11] = { generation = 11, traitMax = 5, discMax = 5, bloodMax = 12, usableBlood = 12, perTurn = 1,  doubleCost = false },
    [12] = { generation = 12, traitMax = 5, discMax = 5, bloodMax = 11, usableBlood = 11, perTurn = 1,  doubleCost = false },
    [13] = { generation = 13, traitMax = 5, discMax = 5, bloodMax = 10, usableBlood = 10, perTurn = 1,  doubleCost = false },
    [14] = { generation = 14, traitMax = 5, discMax = 4, bloodMax = 10, usableBlood = 8,  perTurn = 1,  doubleCost = false },
    [15] = { generation = 15, traitMax = 5, discMax = 3, bloodMax = 10, usableBlood = 6,  perTurn = 1,  doubleCost = true  },
}

function Generations.get(genNumber)
    local g = tonumber(genNumber) or 13
    if g < 4 then g = 4 end
    if g > 15 then g = 15 end
    return Generations.TABLE[g]
end

return Generations
```

Criar `Core/generation_blood.lua`:
```lua
local Generations = require("Data.generations")

local Blood = {}

local function shallowCopy(t)
    local out = {}
    for k, v in pairs(t or {}) do out[k] = v end
    return out
end

function Blood.deriveStats(genNumber)
    return Generations.get(genNumber)
end

function Blood.spend(state, amount, opts)
    opts = opts or {}
    local baseAmount = tonumber(amount) or 0
    if baseAmount <= 0 then
        return { ok = true, newState = shallowCopy(state), costApplied = 0, error = nil }
    end

    local stats = Blood.deriveStats(state.generation)
    local cost = baseAmount
    if opts.forDisciplineOrHeal and stats.doubleCost then
        cost = cost * 2
    end

    local cur = tonumber(state.currentBlood) or 0
    local spentTurn = tonumber(state.spentThisTurn) or 0

    if cur < cost and not opts.storytellerOverride then
        return { ok = false, newState = shallowCopy(state), costApplied = 0, error = "Reserva de sangue insuficiente." }
    end

    if opts.forDisciplineOrHeal and stats.usableBlood < stats.bloodMax and not opts.storytellerOverride then
        local unusableFloor = stats.bloodMax - stats.usableBlood
        if (cur - cost) < unusableFloor and cur > unusableFloor then
            -- Na 14ª/15ª geração, apenas `usableBlood` da reserva máxima pode ativar poderes/cura
        end
        local usedSoFar = tonumber(state.thinBloodUsed) or 0
        if (usedSoFar + cost) > stats.usableBlood then
            return {
                ok = false,
                newState = shallowCopy(state),
                costApplied = 0,
                error = "Sangue Fraco atingiu o limite de vitae utilizável para poderes/cura.",
            }
        end
    end

    if not opts.bypassTurnLimit and not opts.storytellerOverride then
        if (spentTurn + cost) > stats.perTurn then
            return {
                ok = false,
                newState = shallowCopy(state),
                costApplied = 0,
                error = string.format("Limite de gasto de sangue por turno excedido (%d/%d).", spentTurn + cost, stats.perTurn),
            }
        end
    end

    local nextSt = shallowCopy(state)
    nextSt.currentBlood = math.max(0, cur - cost)
    nextSt.spentThisTurn = spentTurn + cost
    if opts.forDisciplineOrHeal and stats.usableBlood < stats.bloodMax then
        nextSt.thinBloodUsed = (tonumber(state.thinBloodUsed) or 0) + cost
    end
    return { ok = true, newState = nextSt, costApplied = cost, error = nil }
end

function Blood.gain(state, amount)
    local stats = Blood.deriveStats(state.generation)
    local cur = tonumber(state.currentBlood) or 0
    local add = math.max(0, tonumber(amount) or 0)
    local nextSt = shallowCopy(state)
    nextSt.currentBlood = math.min(stats.bloodMax, cur + add)
    nextSt.thinBloodUsed = 0
    return { newState = nextSt, added = nextSt.currentBlood - cur }
end

function Blood.newTurn(state)
    local nextSt = shallowCopy(state)
    nextSt.spentThisTurn = 0
    return nextSt
end

function Blood.applyPhysicalBuff(state, attrKey, opts)
    opts = opts or {}
    local valid = { forca = true, destreza = true, vigor = true }
    if not valid[attrKey] then
        return { ok = false, newState = shallowCopy(state), effectiveAttr = 0, temporaryAboveMax = false, error = "Apenas Atributos Físicos recebem Blood Buff." }
    end

    local stats = Blood.deriveStats(state.generation)
    local baseVal = tonumber(state["attr_" .. attrKey]) or 1
    local curBuff = tonumber(state["buff_" .. attrKey]) or 0
    local maxAllowed = stats.traitMax + 1

    if (baseVal + curBuff + 1) > maxAllowed and not opts.storytellerOverride then
        return {
            ok = false,
            newState = shallowCopy(state),
            effectiveAttr = baseVal + curBuff,
            temporaryAboveMax = (baseVal + curBuff) > stats.traitMax,
            error = string.format("Blood Buff limitado a %d (máx. da geração + 1; V20 p. 268).", maxAllowed),
        }
    end

    local spendRes = Blood.spend(state, 1, {
        forDisciplineOrHeal = true,
        storytellerOverride = opts.storytellerOverride,
    })
    if not spendRes.ok then
        return {
            ok = false,
            newState = spendRes.newState,
            effectiveAttr = baseVal + curBuff,
            temporaryAboveMax = (baseVal + curBuff) > stats.traitMax,
            error = spendRes.error,
        }
    end

    local nextSt = spendRes.newState
    nextSt["buff_" .. attrKey] = curBuff + 1
    local eff = baseVal + nextSt["buff_" .. attrKey]
    return {
        ok = true,
        newState = nextSt,
        effectiveAttr = eff,
        temporaryAboveMax = eff > stats.traitMax,
        error = nil,
    }
end

function Blood.clearSceneBuffs(state)
    local nextSt = shallowCopy(state)
    nextSt.buff_forca = 0
    nextSt.buff_destreza = 0
    nextSt.buff_vigor = 0
    nextSt.spentThisTurn = 0
    return nextSt
end

return Blood
```

- [ ] **Step 4: Rodar o teste e confirmar aprovação**

Executar: `python Tests/run_tests.py Tests/test_02_generation_blood.lua`  
Resultado esperado: `[PASS] Tests\test_02_generation_blood.lua`.

- [ ] **Step 5: Commit**

```bash
git add Data/generations.lua Core/generation_blood.lua Tests/test_02_generation_blood.lua
git commit -m "feat(core): add 4th-15th generation table, blood spending rules and physical blood buff"
```

---

### Task 3: Trilha de Vitalidade, Empilhamento, Transbordo, Absorção e Cura

**Files:**
- Create: `Core/health.lua`
- Test: `Tests/test_03_health.lua`

**Interfaces:**
- Consumes: `Core/generation_blood.lua`
- Produces:
  - `Health.getStatus(state)` -> `{ totalBoxes = number, boxes = string[], currentLevelName = string, penalty = number, incapacitated = boolean, torporOrDeath = string|nil }`
  - `Health.applyDamage(state, amount, damageType, opts)` -> `newState` (`damageType` = `"bashing"|"lethal"|"aggravated"`; `opts.isVampire`, `opts.isFirearm`, `opts.headshot`, `opts.halveBashing`)
  - `Health.buildSoakPool(state, damageType)` -> `{ canSoak = boolean, pool = number, difficulty = number, reason = string|nil }`
  - `Health.healWithBlood(state, damageType, opts)` -> `{ ok = boolean, newState = table, error = string|nil }`

- [ ] **Step 1: Escrever o teste falho `Tests/test_03_health.lua`**

```lua
local Health = require("Core.health")

-- 1. Empilhamento (* > X > /) e penalidade de ferimento
local st = { bashing = 2, lethal = 1, aggravated = 1, hugeSize = false, isVampire = true }
local info = Health.getStatus(st)
assert(info.totalBoxes == 7)
assert(info.boxes[1] == "*" and info.boxes[2] == "X" and info.boxes[3] == "/" and info.boxes[4] == "/")
assert(info.currentLevelName == "Ferido Gravemente" and info.penalty == -2)

-- 2. Upgrade de Contundente para Letal quando estoura 7 níveis
local stFull = { bashing = 7, lethal = 0, aggravated = 0, isVampire = true }
local after = Health.applyDamage(stFull, 2, "bashing", { isVampire = true })
assert(after.lethal == 2 and after.bashing == 5, "Excedente contundente deve virar letal")

-- 3. Arma de fogo em Vampiro vira Contundente e divide pela metade após absorção; em Mortal é Letal
local vShot = Health.applyDamage({ bashing = 0, lethal = 0, aggravated = 0 }, 5, "lethal", {
    isVampire = true, isFirearm = true, halveBashing = true
})
assert(vShot.bashing == 2 and vShot.lethal == 0, "5 contundente pós-absorção / 2 = 2 contundente")

local mShot = Health.applyDamage({ bashing = 0, lethal = 0, aggravated = 0 }, 3, "lethal", {
    isVampire = false, isFirearm = true
})
assert(mShot.lethal == 3, "Arma de fogo em mortal permanece letal")

-- 4. Absorção: Mortal não absorve Letal sem armadura; Vampiro absorve Letal com Vigor + Fortitude
local mSoak = Health.buildSoakPool({ isVampire = false, attr_vigor = 3, armor = 0 }, "lethal")
assert(mSoak.canSoak == false)

local vSoak = Health.buildSoakPool({ isVampire = true, attr_vigor = 3, fortitude = 2, armor = 1 }, "lethal")
assert(vSoak.canSoak == true and vSoak.pool == 6)

local vAgg = Health.buildSoakPool({ isVampire = true, attr_vigor = 4, fortitude = 2, armor = 0 }, "aggravated")
assert(vAgg.canSoak == true and vAgg.pool == 2, "Agravado só usa Fortitude (+ armadura aplicável)")

-- 5. Cura pelo sangue
local vHeal = Health.healWithBlood({
    isVampire = true, generation = 13, currentBlood = 8, spentThisTurn = 0,
    bashing = 1, lethal = 1, aggravated = 0
}, "lethal", {})
assert(vHeal.ok == true and vHeal.newState.lethal == 0 and vHeal.newState.currentBlood == 7)
```

- [ ] **Step 2: Rodar o teste para confirmar falha**

Executar: `python Tests/run_tests.py Tests/test_03_health.lua`  
Resultado esperado: `FAIL` com `module 'Core.health' not found`.

- [ ] **Step 3: Implementar `Core/health.lua`**

```lua
local Blood = require("Core.generation_blood")

local Health = {}

Health.STANDARD_LEVELS = {
    { name = "Escoriado",         penalty = 0,  incapacitated = false },
    { name = "Machucado",         penalty = -1, incapacitated = false },
    { name = "Ferido",            penalty = -1, incapacitated = false },
    { name = "Ferido Gravemente", penalty = -2, incapacitated = false },
    { name = "Espancado",         penalty = -2, incapacitated = false },
    { name = "Aleijado",          penalty = -5, incapacitated = false },
    { name = "Incapacitado",      penalty = 0,  incapacitated = true  },
}

local function copyState(s)
    local o = {}
    for k, v in pairs(s or {}) do o[k] = v end
    return o
end

local function buildLevels(hugeSize)
    local levels = {}
    if hugeSize then
        table.insert(levels, { name = "Escoriado (Extra)", penalty = 0, incapacitated = false })
    end
    for _, lv in ipairs(Health.STANDARD_LEVELS) do
        table.insert(levels, lv)
    end
    return levels
end

function Health.getStatus(state)
    state = state or {}
    local levels = buildLevels(state.hugeSize == true)
    local totalBoxes = #levels
    local agg = math.max(0, tonumber(state.aggravated) or 0)
    local let = math.max(0, tonumber(state.lethal) or 0)
    local bas = math.max(0, tonumber(state.bashing) or 0)

    local boxes = {}
    for i = 1, totalBoxes do
        if i <= agg then
            boxes[i] = "*"
        elseif i <= (agg + let) then
            boxes[i] = "X"
        elseif i <= (agg + let + bas) then
            boxes[i] = "/"
        else
            boxes[i] = ""
        end
    end

    local filled = math.min(totalBoxes, agg + let + bas)
    local currentLevelName = "Saudável"
    local penalty = 0
    local incapacitated = false

    if filled > 0 then
        local lv = levels[filled]
        currentLevelName = lv.name
        penalty = lv.penalty
        incapacitated = lv.incapacitated
    end

    local torporOrDeath = nil
    if agg >= totalBoxes then
        torporOrDeath = state.isVampire and "Morte Final" or "Morte"
    elseif (agg + let) >= totalBoxes then
        torporOrDeath = state.isVampire and "Torpor (ou Morte se sem sangue)" or "Agonia Crítica / Morte"
    end

    return {
        totalBoxes = totalBoxes,
        boxes = boxes,
        currentLevelName = currentLevelName,
        penalty = penalty,
        incapacitated = incapacitated,
        torporOrDeath = torporOrDeath,
    }
end

function Health.applyDamage(state, amount, damageType, opts)
    opts = opts or {}
    local nextSt = copyState(state)
    local dmg = math.max(0, tonumber(amount) or 0)
    local dtype = damageType or "bashing"

    if opts.isVampire and opts.isFirearm and not opts.headshot and dtype == "lethal" then
        dtype = "bashing"
    end

    if opts.isVampire and dtype == "bashing" and opts.halveBashing then
        dmg = math.floor(dmg / 2)
    end

    local levels = buildLevels(nextSt.hugeSize == true)
    local cap = #levels
    local agg = math.max(0, tonumber(nextSt.aggravated) or 0)
    local let = math.max(0, tonumber(nextSt.lethal) or 0)
    local bas = math.max(0, tonumber(nextSt.bashing) or 0)

    for _ = 1, dmg do
        if dtype == "aggravated" then
            if (agg + let + bas) < cap then
                agg = agg + 1
            elseif bas > 0 then
                bas = bas - 1
                agg = agg + 1
            elseif let > 0 then
                let = let - 1
                agg = agg + 1
            end
        elseif dtype == "lethal" then
            if (agg + let + bas) < cap then
                let = let + 1
            elseif bas > 0 then
                bas = bas - 1
                let = let + 1
            elseif (agg + let) < cap then
                let = let + 1
            end
        else -- bashing
            if (agg + let + bas) < cap then
                bas = bas + 1
            elseif bas > 0 then
                bas = bas - 1
                let = let + 1
            end
        end
    end

    nextSt.aggravated = math.min(cap, agg)
    nextSt.lethal = math.min(cap - nextSt.aggravated, let)
    nextSt.bashing = math.min(cap - nextSt.aggravated - nextSt.lethal, bas)
    return nextSt
end

function Health.buildSoakPool(state, damageType)
    state = state or {}
    local vigor = (tonumber(state.attr_vigor) or 1) + (tonumber(state.buff_vigor) or 0)
    local fort = tonumber(state.fortitude) or 0
    local armor = tonumber(state.armor) or 0
    local diff = tonumber(state.soakDifficulty) or 6
    local isVampOrGhoul = (state.isVampire == true) or (state.isGhoul == true)

    if damageType == "aggravated" then
        if fort <= 0 then
            return { canSoak = false, pool = 0, difficulty = diff, reason = "Dano Agravado exige Fortitude para absorção." }
        end
        return { canSoak = true, pool = fort, difficulty = diff, reason = nil }
    elseif damageType == "lethal" then
        if not isVampOrGhoul and armor <= 0 and fort <= 0 then
            return { canSoak = false, pool = 0, difficulty = diff, reason = "Mortais não absorvem dano Letal sem armadura." }
        end
        local base = isVampOrGhoul and vigor or 0
        return { canSoak = true, pool = base + fort + armor, difficulty = diff, reason = nil }
    end

    return { canSoak = true, pool = vigor + fort + armor, difficulty = diff, reason = nil }
end

function Health.healWithBlood(state, damageType, opts)
    opts = opts or {}
    if not state.isVampire and not state.isGhoul then
        return { ok = false, newState = copyState(state), error = "Apenas vampiros e carniçais curam ferimentos com sangue." }
    end

    if damageType == "aggravated" then
        if (tonumber(state.aggravated) or 0) <= 0 then
            return { ok = false, newState = copyState(state), error = "Nenhum nível de dano Agravado para curar." }
        end
        local wp = tonumber(state.fdv_temp) or 0
        local sp = Blood.spend(state, 5, { forDisciplineOrHeal = true, bypassTurnLimit = true, storytellerOverride = opts.storytellerOverride })
        if not sp.ok then
            return { ok = false, newState = sp.newState, error = sp.error }
        end
        local nextSt = sp.newState
        nextSt.aggravated = math.max(0, (tonumber(nextSt.aggravated) or 0) - 1)
        if opts.useWillpowerForExtra and wp >= 1 then
            nextSt.fdv_temp = wp - 1
        end
        return { ok = true, newState = nextSt, error = nil }
    end

    local field = (damageType == "lethal") and "lethal" or "bashing"
    if (tonumber(state[field]) or 0) <= 0 then
        return { ok = false, newState = copyState(state), error = "Nenhum dano desse tipo para curar." }
    end

    local sp = Blood.spend(state, 1, { forDisciplineOrHeal = true, storytellerOverride = opts.storytellerOverride })
    if not sp.ok then
        return { ok = false, newState = sp.newState, error = sp.error }
    end
    local nextSt = sp.newState
    nextSt[field] = math.max(0, (tonumber(nextSt[field]) or 0) - 1)
    return { ok = true, newState = nextSt, error = nil }
end

return Health
```

- [ ] **Step 4: Rodar o teste e confirmar aprovação**

Executar: `python Tests/run_tests.py Tests/test_03_health.lua`  
Resultado esperado: `[PASS] Tests\test_03_health.lua`.

- [ ] **Step 5: Commit**

```bash
git add Core/health.lua Tests/test_03_health.lua
git commit -m "feat(core): add V20 health track, bashing overflow, soak and blood healing"
```

---

### Task 4: Clãs, Moralidade, Virtudes, Força de Vontade, Frenesi (Fraqueza Brujah) e Rötschreck

**Files:**
- Create: `Data/clans.lua`
- Create: `Data/morality_virtues.lua`
- Create: `Core/willpower_morality.lua`
- Test: `Tests/test_04_willpower_morality.lua`

**Interfaces:**
- Produces:
  - `Clans.CLANS`: tabela com os 14 perfis vampíricos (`brujah`..`caitiff`) contendo `{ id, name, disciplines, weaknessId, weaknessSummary, accentColor, appearanceZero }`
  - `MoralityVirtues.getAuraModifier(score)` -> `{ diffMod = number, label = string }`
  - `WillpowerMorality.spendWillpower(state, amount)` -> `{ ok, newState, error }`
  - `WillpowerMorality.awakenNightly(state)` -> `{ ok, newState, hungerFrenzyRisk = boolean, warning = string|nil }`
  - `WillpowerMorality.prepareFrenzyCheck(state, stimulusDiff)` -> `{ pool = number, difficulty = number, canAvoidWithWillpower = boolean, notes = string[] }`
  - `WillpowerMorality.prepareRotschreckCheck(state, stimulusDiff)` -> `{ pool = number, difficulty = number }`
  - `WillpowerMorality.prepareDegenerationCheck(state)` -> `{ pool = number, difficulty = 8, virtueUsed = string }`

- [ ] **Step 1: Escrever o teste falho `Tests/test_04_willpower_morality.lua`**

```lua
local Clans = require("Data.clans")
local MoralityVirtues = require("Data.morality_virtues")
local WM = require("Core.willpower_morality")

-- 1. Todos os 13 clãs + Caitiff presentes, Nosferatu com appearanceZero
assert(Clans.CLANS.brujah.disciplines[1] == "celerity")
assert(Clans.CLANS.nosferatu.appearanceZero == true)
assert(#Clans.CLANS.caitiff.disciplines == 0)

-- 2. Modificador de Aura V20 (p. 312)
assert(MoralityVirtues.getAuraModifier(10).diffMod == -2)
assert(MoralityVirtues.getAuraModifier(8).diffMod == -1)
assert(MoralityVirtues.getAuraModifier(6).diffMod == 0)
assert(MoralityVirtues.getAuraModifier(2).diffMod == 1)
assert(MoralityVirtues.getAuraModifier(1).diffMod == 2)

-- 3. Fraqueza Brujah no Frenesi: +2 de dificuldade (teto 10) e bloqueia evitar com FdV
local fBrujah = WM.prepareFrenzyCheck({
    cla_id = "brujah", virtude2_tipo = "autocontrole", virtude2_val = 3
}, 6)
assert(fBrujah.pool == 3)
assert(fBrujah.difficulty == 8, "Brujah soma +2 na dificuldade de Frenesi")
assert(fBrujah.canAvoidWithWillpower == false, "Brujah não pode gastar FdV para evitar entrar em Frenesi")

-- 4. Despertar Noturno desconta 1 de sangue e alerta risco de fome quando reserva baixa
local awk = WM.awakenNightly({
    isVampire = true, generation = 13, currentBlood = 3, virtude2_val = 3
})
assert(awk.ok == true and awk.newState.currentBlood == 2 and awk.hungerFrenzyRisk == true)
```

- [ ] **Step 2: Rodar o teste para confirmar falha**

Executar: `python Tests/run_tests.py Tests/test_04_willpower_morality.lua`  
Resultado esperado: `FAIL` com `module 'Data.clans' not found`.

- [ ] **Step 3: Implementar `Data/clans.lua`, `Data/morality_virtues.lua` e `Core/willpower_morality.lua`**

Criar `Data/clans.lua`:
```lua
local Clans = {}

Clans.ORDER = {
    "brujah", "gangrel", "malkavian", "nosferatu", "toreador", "tremere", "ventrue",
    "assamite", "setite", "giovanni", "lasombra", "ravnos", "tzimisce", "caitiff",
}

Clans.CLANS = {
    brujah    = { id = "brujah",    dataType = "br.com.v20.Brujah",    name = "Brujah",            accentColor = "#9E1B24", appearanceZero = false, disciplines = { "celerity", "potence", "presence" },        weaknessId = "passion",              weaknessSummary = "+2 na dificuldade para resistir ao Frenesi (máx. 10); não pode gastar FdV para evitar o Frenesi, apenas 1 FdV para encerrá-lo após começar (V20, p. 49)." },
    gangrel   = { id = "gangrel",   dataType = "br.com.v20.Gangrel",   name = "Gangrel",           accentColor = "#4F6D3A", appearanceZero = false, disciplines = { "animalism", "fortitude", "protean" },      weaknessId = "animal_features",      weaknessSummary = "Adquire 1 característica animal a cada Frenesi; a cada 5 características, perde 1 ponto permanente de Atributo Social (V20, p. 53)." },
    malkavian = { id = "malkavian", dataType = "br.com.v20.Malkavian", name = "Malkaviano",        accentColor = "#6B3FA0", appearanceZero = false, disciplines = { "auspex", "dementation", "obfuscate" },     weaknessId = "derangement",          weaknessSummary = "Possui ao menos 1 Perturbação incurável desde o Abraço; pode gastar 1 FdV para suprimi-la por 1 cena (V20, p. 59)." },
    nosferatu = { id = "nosferatu", dataType = "br.com.v20.Nosferatu", name = "Nosferatu",         accentColor = "#5C5346", appearanceZero = true,  disciplines = { "animalism", "obfuscate", "potence" },      weaknessId = "monstrous_appearance", weaknessSummary = "Aparência permanentemente 0; falha automática na maioria dos testes baseados em Aparência (V20, p. 61)." },
    toreador  = { id = "toreador",  dataType = "br.com.v20.Toreador",  name = "Toreador",          accentColor = "#B8336A", appearanceZero = false, disciplines = { "auspex", "celerity", "presence" },         weaknessId = "aesthetic_fixation",   weaknessSummary = "Diante de grande beleza, testa Autocontrole/Instinto (dif. 6) ou fica fascinado pela cena (V20, p. 67)." },
    tremere   = { id = "tremere",   dataType = "br.com.v20.Tremere",   name = "Tremere",           accentColor = "#8C1D40", appearanceZero = false, disciplines = { "auspex", "dominate", "thaumaturgy" },      weaknessId = "blood_bond_suscept",   weaknessSummary = "Bastam 2 goles (em vez de 3) de sangue de outro vampiro para formar Laço de Sangue completo (V20, p. 69)." },
    ventrue   = { id = "ventrue",   dataType = "br.com.v20.Ventrue",   name = "Ventrue",           accentColor = "#2E5A88", appearanceZero = false, disciplines = { "dominate", "fortitude", "presence" },      weaknessId = "selective_diet",       weaknessSummary = "Alimenta-se apenas de um tipo específico de recipiente mortal; vomita qualquer outro sangue humano (V20, p. 71)." },
    assamite  = { id = "assamite",  dataType = "br.com.v20.Assamite",  name = "Assamita",          accentColor = "#7A4419", appearanceZero = false, disciplines = { "celerity", "obfuscate", "quietus" },       weaknessId = "vitae_curse",          weaknessSummary = "Sofre 1 nível Letal não absorvível por ponto de vitae vampírica ingerida e vício em sangue cainita (V20, p. 49)." },
    setite    = { id = "setite",    dataType = "br.com.v20.Setite",    name = "Seguidores de Set", accentColor = "#A67C1E", appearanceZero = false, disciplines = { "obfuscate", "presence", "serpentis" },     weaknessId = "light_sensitivity",    weaknessSummary = "Recebe +2 níveis de dano por luz solar e perde 1 dado em todas as paradas sob luz forte (V20, p. 51)." },
    giovanni  = { id = "giovanni",  dataType = "br.com.v20.Giovanni",  name = "Giovanni",          accentColor = "#3B5949", appearanceZero = false, disciplines = { "dominate", "necromancy", "potence" },      weaknessId = "painful_kiss",         weaknessSummary = "O Beijo causa dor excruciante e causa o dobro de dano letal no recipiente humano (V20, p. 55)." },
    lasombra  = { id = "lasombra",  dataType = "br.com.v20.Lasombra",  name = "Lasombra",          accentColor = "#3A3F5E", appearanceZero = false, disciplines = { "dominate", "obtenebration", "potence" },   weaknessId = "no_reflection",        weaknessSummary = "Não possui reflexo em espelhos/câmeras e sofre +1 nível de dano agravado pela luz solar (V20, p. 57)." },
    ravnos    = { id = "ravnos",    dataType = "br.com.v20.Ravnos",    name = "Ravnos",            accentColor = "#9C4A1A", appearanceZero = false, disciplines = { "animalism", "chimerstry", "fortitude" },   weaknessId = "specific_vice",        weaknessSummary = "Possui um vício específico; quando tem oportunidade de praticá-lo, testa Autocontrole/Instinto dif. 6 para resistir (V20, p. 63)." },
    tzimisce  = { id = "tzimisce",  dataType = "br.com.v20.Tzimisce",  name = "Tzimisce",          accentColor = "#731928", appearanceZero = false, disciplines = { "animalism", "auspex", "vicissitude" },     weaknessId = "native_soil",          weaknessSummary = "Deve repousar com 2 punhados de terra natal/importante; a cada 24h sem ela, paradas divididas pela metade até mín. 1 dado (V20, p. 71)." },
    caitiff   = { id = "caitiff",   dataType = "br.com.v20.Caitiff",   name = "Caitiff",           accentColor = "#5A5A66", appearanceZero = false, disciplines = {},                                            weaknessId = "social_outcast",       weaknessSummary = "Sem disciplinas de clã (evolui qualquer disciplina por Atual x 6 XP); +2 dif. em testes Sociais com Membros estabelecidos até ser aceito (V20, p. 73)." },
}

return Clans
```

Criar `Data/morality_virtues.lua`:
```lua
local MoralityVirtues = {}

MoralityVirtues.PATHS = {
    { id = "humanidade",   name = "Humanidade",                v1 = "consciencia", v2 = "autocontrole" },
    { id = "metamorfose",  name = "Trilha da Metamorfose",     v1 = "conviccao",   v2 = "instinto" },
    { id = "noite",        name = "Trilha da Noite",           v1 = "conviccao",   v2 = "instinto" },
    { id = "ossos",        name = "Trilha dos Ossos",          v1 = "conviccao",   v2 = "autocontrole" },
    { id = "sangue",       name = "Trilha do Sangue",          v1 = "conviccao",   v2 = "autocontrole" },
    { id = "tifao",        name = "Trilha de Tifão",           v1 = "conviccao",   v2 = "autocontrole" },
    { id = "paradoxo",     name = "Trilha do Paradoxo",        v1 = "conviccao",   v2 = "autocontrole" },
    { id = "reis",         name = "Trilha dos Reis / Honra",   v1 = "conviccao",   v2 = "autocontrole" },
}

MoralityVirtues.FRENZY_STIMULI = {
    { label = "Cheiro de sangue (faminto)", diff = 4 },
    { label = "Visão de sangue (faminto)",  diff = 6 },
    { label = "Humilhação / Provocação",    diff = 4 },
    { label = "Ameaça à vida / Amado ferido", diff = 6 },
    { label = "Gosto de sangue (faminto)",  diff = 8 },
}

MoralityVirtues.ROTSCHRECK_STIMULI = {
    { label = "Acender isqueiro / vela",    diff = 3 },
    { label = "Tocha / Fogueira pequena",   diff = 5 },
    { label = "Fogo próximo / Incêndio",    diff = 7 },
    { label = "Queimadura / Luz solar velada", diff = 8 },
    { label = "Luz solar direta",           diff = 9 },
}

function MoralityVirtues.getAuraModifier(score)
    local s = tonumber(score) or 7
    if s >= 10 then return { diffMod = -2, label = "Radiante (-2 dif Social)" } end
    if s >= 8  then return { diffMod = -1, label = "Calorosa (-1 dif Social)" } end
    if s >= 4  then return { diffMod = 0,  label = "Neutra (0 dif Social)" } end
    if s >= 2  then return { diffMod = 1,  label = "Fria / Predatória (+1 dif Social)" } end
    if s == 1  then return { diffMod = 2,  label = "Monstruosa (+2 dif Social)" } end
    return { diffMod = 5, label = "Perdido para a Besta" }
end

return MoralityVirtues
```

Criar `Core/willpower_morality.lua`:
```lua
local MoralityVirtues = require("Data.morality_virtues")

local WM = {}

local function copyState(s)
    local o = {}
    for k, v in pairs(s or {}) do o[k] = v end
    return o
end

function WM.spendWillpower(state, amount)
    local cost = math.max(1, tonumber(amount) or 1)
    local cur = tonumber(state.fdv_temp) or 0
    if cur < cost and not state.storytellerOverride then
        return { ok = false, newState = copyState(state), error = "Força de Vontade temporária insuficiente." }
    end
    local nextSt = copyState(state)
    nextSt.fdv_temp = math.max(0, cur - cost)
    return { ok = true, newState = nextSt, error = nil }
end

function WM.awakenNightly(state)
    local nextSt = copyState(state)
    if not state.isVampire then
        return { ok = true, newState = nextSt, hungerFrenzyRisk = false, warning = nil }
    end
    local cur = tonumber(state.currentBlood) or 0
    if cur <= 0 then
        return {
            ok = false,
            newState = nextSt,
            hungerFrenzyRisk = true,
            warning = "Sem sangue ao despertar: personagem entra em Torpor por inanição!",
        }
    end
    nextSt.currentBlood = cur - 1
    nextSt.spentThisTurn = 0
    local selfControl = tonumber(state.virtude2_val) or 1
    local threshold = math.max(2, 7 - selfControl)
    local hungry = nextSt.currentBlood <= threshold
    return {
        ok = true,
        newState = nextSt,
        hungerFrenzyRisk = hungry,
        warning = hungry and string.format("Fome intensa (%d pts restantes): risco de Frenesi diante de sangue!", nextSt.currentBlood) or nil,
    }
end

function WM.prepareFrenzyCheck(state, stimulusDiff)
    local baseDiff = tonumber(stimulusDiff) or 6
    local v2 = tonumber(state.virtude2_val) or 1
    local notes = { "Acumule 5 sucessos em testes estendidos para conter a Besta totalmente." }
    local canAvoidWP = true

    if state.virtude2_tipo == "instinto" then
        table.insert(notes, "Instinto: controla e cavalga o Frenesi em vez de resistir passivamente (V20, p. 313).")
    end

    if state.cla_id == "brujah" then
        baseDiff = math.min(10, baseDiff + 2)
        canAvoidWP = false
        table.insert(notes, "Fraqueza Brujah: +2 na dificuldade (máx. 10) e proibido gastar FdV para evitar o Frenesi (V20, p. 49).")
    end

    return {
        pool = v2,
        difficulty = math.max(2, math.min(10, baseDiff)),
        canAvoidWithWillpower = canAvoidWP,
        notes = notes,
    }
end

function WM.prepareRotschreckCheck(state, stimulusDiff)
    local baseDiff = tonumber(stimulusDiff) or 6
    local courage = tonumber(state.virtude3_val) or 1
    return {
        pool = courage,
        difficulty = math.max(2, math.min(10, baseDiff)),
    }
end

function WM.prepareDegenerationCheck(state)
    local v1 = tonumber(state.virtude1_val) or 1
    local vName = (state.virtude1_tipo == "conviccao") and "Convicção" or "Consciência"
    return {
        pool = v1,
        difficulty = 8,
        virtueUsed = vName,
    }
end

WM.getAuraModifier = MoralityVirtues.getAuraModifier

return WM
```

- [ ] **Step 4: Rodar o teste e confirmar aprovação**

Executar: `python Tests/run_tests.py Tests/test_04_willpower_morality.lua`  
Resultado esperado: `[PASS] Tests\test_04_willpower_morality.lua`.

- [ ] **Step 5: Commit**

```bash
git add Data/clans.lua Data/morality_virtues.lua Core/willpower_morality.lua Tests/test_04_willpower_morality.lua
git commit -m "feat(core): add 14 clans config, aura modifiers, awakening and Brujah frenzy automation"
```

---

### Task 5: Catálogo Universal das 17 Disciplinas Clássicas (Níveis 1–5) e Motor de Poderes

**Files:**
- Create: `Data/disciplines_catalog.lua`
- Create: `Core/disciplines_engine.lua`
- Test: `Tests/test_05_disciplines.lua`

**Interfaces:**
- Consumes: `Core/generation_blood.lua`, `Core/willpower_morality.lua`, `Data/clans.lua`
- Produces:
  - `DisciplinesCatalog.DISCIPLINES`: todas as 17 disciplinas V20 (`animalism`..`vicissitude`), cada uma com 5 poderes (`level 1..5`) contendo `{ id, level, name, cost = { blood, willpower }, pool = { attr, hab }, defaultDiff, diffHint, toggleBuff, summary }`
  - `DisciplinesEngine.classifyCostCategory(clanId, discId, hasAdditionalDiscMerit)` -> `"cla"|"fora_cla"|"caitiff"`
  - `DisciplinesEngine.getUnlockedPowers(discId, dots, customPowers)` -> lista ordenada de poderes `1..dots`
  - `DisciplinesEngine.activatePower(state, discEntry, power, opts)` -> `{ ok, newState, rollSpec = table|nil, buffToggled = table|nil, error = string|nil }`
  - `DisciplinesEngine.computeCombatModifiers(state, disciplinesList)` -> `{ passivePotenceDice, activePotenceAuto, passiveCelerityDice, activeCelerityActions, fortitudeSoak, sceneAttrMods, perceptionDiffMod }`

- [ ] **Step 1: Escrever o teste falho `Tests/test_05_disciplines.lua`**

```lua
local Catalog = require("Data.disciplines_catalog")
local Engine = require("Core.disciplines_engine")

-- 1. Todas as 17 disciplinas clássicas cadastradas com 5 poderes cada (85 poderes oficiais)
local count = 0
for _, id in ipairs(Catalog.ORDER) do
    local d = Catalog.DISCIPLINES[id]
    assert(d ~= nil and #d.powers == 5, "Disciplina inválida ou sem 5 poderes: " .. tostring(id))
    count = count + 1
end
assert(count == 17, "Esperado 17 disciplinas clássicas da V20")

-- 2. Classificação automática de custo: Brujah comprando Dominação = fora_cla; com Qualidade = cla; Caitiff = caitiff
assert(Engine.classifyCostCategory("brujah", "potence", false) == "cla")
assert(Engine.classifyCostCategory("brujah", "dominate", false) == "fora_cla")
assert(Engine.classifyCostCategory("brujah", "dominate", true) == "cla")
assert(Engine.classifyCostCategory("caitiff", "dominate", false) == "caitiff")

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
assert(act.rollSpec.attr == "attr_manipulacao" and act.rollSpec.hab == "hab_ocultismo" and act.rollSpec.defaultDiff == 7)

-- 4. Modificadores de Potência ativa (sucessos automáticos), Rapidez ativa (ações extras ignorando limite/turno) e Fortitude
local st2 = {
    isVampire = true, generation = 13, currentBlood = 8, spentThisTurn = 1, fdv_temp = 5, activeBuffs = {}
}
local celRes = Engine.activateCelerityActions(st2, 2)
assert(celRes.ok == true and celRes.newState.currentBlood == 6 and celRes.newState.activeCelerityActions == 2)

local mods = Engine.computeCombatModifiers(celRes.newState, {
    { disc_id = "potence", nivel = 3, activeAuto = true },
    { disc_id = "celerity", nivel = 2 },
    { disc_id = "fortitude", nivel = 2 },
})
assert(mods.activePotenceAuto == 3 and mods.passivePotenceDice == 0)
assert(mods.activeCelerityActions == 2 and mods.passiveCelerityDice == 0)
assert(mods.fortitudeSoak == 2)
```

- [ ] **Step 2: Rodar o teste para confirmar falha**

Executar: `python Tests/run_tests.py Tests/test_05_disciplines.lua`  
Resultado esperado: `FAIL` com `module 'Data.disciplines_catalog' not found`.

- [ ] **Step 3: Implementar `Data/disciplines_catalog.lua` e `Core/disciplines_engine.lua`**

Criar `Data/disciplines_catalog.lua`:
```lua
local Catalog = {}

Catalog.ORDER = {
    "animalism", "auspex", "celerity", "chimerstry", "dementation", "dominate",
    "fortitude", "necromancy", "obfuscate", "obtenebration", "potence", "presence",
    "protean", "quietus", "serpentis", "thaumaturgy", "vicissitude",
}

local function p(lvl, id, name, blood, wp, attr, hab, diff, hint, buff, summary)
    return {
        id = id, level = lvl, name = name,
        cost = { blood = blood or 0, willpower = wp or 0 },
        pool = attr and { attr = attr, hab = hab } or nil,
        defaultDiff = diff or 6, diffHint = hint or "Dif 6",
        toggleBuff = buff, summary = summary,
    }
end

Catalog.DISCIPLINES = {
    animalism = {
        id = "animalism", name = "Animalismo", hasPaths = false,
        powers = {
            p(1, "anim_1", "Sussurros Fera", 0, 0, "attr_manipulacao", "hab_empatia_animais", 6, "Dif 6 (mamíferos predadores) a 8", nil, "Comunica-se mentalmente e impõe comandos simples a animais (V20, p. 128)."),
            p(2, "anim_2", "O Chamado", 0, 0, "attr_carisma", "hab_sobrevivencia", 6, "Dif 6; convoca animais da espécie escolhida", nil, "Convoca animais da vizinhança conforme número de sucessos (V20, p. 129)."),
            p(3, "anim_3", "Acalmar a Besta", 0, 0, "attr_manipulacao", "hab_intimidacao", 7, "Dif 7 (ou Empatia p/ tirar do Frenesi)", nil, "Subjuga a Besta em mortais ou retira vampiros do Frenesi (V20, p. 130)."),
            p(4, "anim_4", "Subjugar o Espírito", 0, 1, "attr_manipulacao", "hab_empatia_animais", 8, "Dif 8 (possui corpo do animal)", nil, "Transfere a consciência vampírica para o corpo de um animal (V20, p. 131)."),
            p(5, "anim_5", "Expulsar a Besta", 0, 0, "attr_manipulacao", "hab_autocontrole_ref", 8, "Dif 8 ao beirar Frenesi", nil, "Transfere o próprio Frenesi iminente para outro alvo próximo (V20, p. 132)."),
        },
    },
    auspex = {
        id = "auspex", name = "Auspícios", hasPaths = false,
        powers = {
            p(1, "ausp_1", "Sentidos Aguçados", 0, 0, nil, nil, 6, "Ativação livre (-N dif Percepção)", { id = "auspex_senses", perceptionDiffMod = -1 }, "Dobra o alcance sensorial e reduz dificuldade de Percepção pelo nível de Auspícios (V20, p. 134)."),
            p(2, "ausp_2", "Percepção da Aura", 0, 0, "attr_percepcao", "hab_empatia", 8, "Dif 8", nil, "Lê emoções, natureza vampírica, magia e diablerie na aura do alvo (V20, p. 135)."),
            p(3, "ausp_3", "O Toque do Espírito", 0, 0, "attr_percepcao", "hab_empatia", 8, "Dif 5 a 9 conforme idade da impressão", nil, "Extrai visões psicométricas do último possuidor de um objeto ou local (V20, p. 136)."),
            p(4, "ausp_4", "Telepatia", 0, 0, "attr_inteligencia", "hab_labia", 6, "Dif = FdV permanente do alvo (1 FdV contra vampiros)", nil, "Projeta pensamentos e lê a mente superficial ou profunda (V20, p. 137)."),
            p(5, "ausp_5", "Projeção Psíquica", 0, 1, "attr_percepcao", "hab_consciencia", 7, "Dif 7 a 9 conforme distância", nil, "Separa a consciência em corpo astral invisível e veloz (V20, p. 138)."),
        },
    },
    celerity = {
        id = "celerity", name = "Rapidez", hasPaths = false,
        powers = {
            p(1, "cel_1", "Rapidez 1", 1, 0, nil, nil, 6, "+1 dado Destreza passivo OU 1 Sangue = +1 ação extra", nil, "Velocidade sobrenatural: +1 Destreza passivo ou +1 ação física extra no turno (V20, p. 142)."),
            p(2, "cel_2", "Rapidez 2", 1, 0, nil, nil, 6, "Até 2 ações físicas extras por 1 Sangue cada", nil, "Eleva bônus passivo de Destreza para +2 ou até 2 ações extras (V20, p. 142)."),
            p(3, "cel_3", "Rapidez 3", 1, 0, nil, nil, 6, "Até 3 ações físicas extras por 1 Sangue cada", nil, "Eleva bônus passivo de Destreza para +3 ou até 3 ações extras (V20, p. 142)."),
            p(4, "cel_4", "Rapidez 4", 1, 0, nil, nil, 6, "Até 4 ações físicas extras por 1 Sangue cada", nil, "Eleva bônus passivo de Destreza para +4 ou até 4 ações extras (V20, p. 142)."),
            p(5, "cel_5", "Rapidez 5", 1, 0, nil, nil, 6, "Até 5 ações físicas extras por 1 Sangue cada", nil, "Eleva bônus passivo de Destreza para +5 ou até 5 ações extras (V20, p. 142)."),
        },
    },
    chimerstry = {
        id = "chimerstry", name = "Quimerismo", hasPaths = false,
        powers = {
            p(1, "chim_1", "Ignis Fatuus", 0, 1, nil, nil, 6, "1 FdV; ilusão estática de 1 sentido", nil, "Cria miragem menor perceptível por um único sentido (V20, p. 143)."),
            p(2, "chim_2", "Fata Morgana", 1, 1, nil, nil, 6, "1 Sangue + 1 FdV; ilusão multissensorial estática", nil, "Cria ilusão completa que afeta todos os sentidos sem causar dano físico (V20, p. 144)."),
            p(3, "chim_3", "Aparição", 1, 0, nil, nil, 6, "+1 Sangue para dar movimento à ilusão", nil, "Concede movimento, som contínuo e comportamento verossímil à ilusão (V20, p. 144)."),
            p(4, "chim_4", "Permanência", 1, 0, nil, nil, 6, "1 Sangue torna a ilusão persistente", nil, "Mantém ilusões de Ignis Fatuus ou Fata Morgana mesmo sem presença do criador (V20, p. 144)."),
            p(5, "chim_5", "Realidade Horrível", 0, 1, "attr_manipulacao", "hab_labia", 6, "Dif = Percepção + Autocontrole da vítima", nil, "Alucinação psicossomática capaz de ferir diretamente uma vítima (V20, p. 145)."),
        },
    },
    dementation = {
        id = "dementation", name = "Demência", hasPaths = false,
        powers = {
            p(1, "dem_1", "Paixão", 0, 0, "attr_carisma", "hab_empatia", 6, "Dif = Humanidade/Trilha do alvo", nil, "Amplifica ou embota radicalmente as emoções atuais do alvo (V20, p. 146)."),
            p(2, "dem_2", "Assombrar a Alma", 1, 0, "attr_manipulacao", "hab_ocultismo", 6, "Dif = Percepção + Autocontrole do alvo", nil, "Assombra a vítima com visões fugazes nos cantos da percepção (V20, p. 147)."),
            p(3, "dem_3", "Olhos do Caos", 0, 0, "attr_percepcao", "hab_ocultismo", 6, "Dif variável (6 a 9 conforme obscuridade)", nil, "Decifra padrões ocultos, naturezas reais e mensagens cifradas na loucura (V20, p. 148)."),
            p(4, "dem_4", "A Voz da Loucura", 1, 0, "attr_manipulacao", "hab_empatia", 7, "Dif 7; induz Frenesi/Rötschreck coletivo", nil, "Conduz ouvintes ao pânico cego ou fúria irracional (V20, p. 148)."),
            p(5, "dem_5", "Insanidade Total", 1, 0, "attr_manipulacao", "hab_intimidacao", 6, "Dif = FdV atual da vítima", nil, "Desperta cinco perturbações graves simultâneas na mente do alvo (V20, p. 149)."),
        },
    },
    dominate = {
        id = "dominate", name = "Dominação", hasPaths = false,
        powers = {
            p(1, "dom_1", "Comando", 0, 0, "attr_manipulacao", "hab_intimidacao", 6, "Dif = FdV permanente do alvo; 1 palavra", nil, "Impõe ordem imediata de uma única palavra via contato visual (V20, p. 152)."),
            p(2, "dom_2", "Hipnotizar", 0, 0, "attr_manipulacao", "hab_lideranca", 6, "Dif = FdV permanente do alvo", nil, "Implanta diretriz complexa imediata ou ativada por gatilho no subconsciente (V20, p. 152)."),
            p(3, "dom_3", "A Mente Esquecida", 0, 0, "attr_raciocinio", "hab_labia", 6, "Dif = FdV permanente do alvo", nil, "Apaga, vasculha ou reescreve memórias da vítima sob olhar fixo (V20, p. 154)."),
            p(4, "dom_4", "Condicionamento", 0, 0, "attr_carisma", "hab_lideranca", 6, "Dif = FdV permanente; teste estendido ao longo do tempo", nil, "Quebra gradualmente a autonomia do servo, facilitando dominações futuras sem olhar (V20, p. 155)."),
            p(5, "dom_5", "Possessão", 0, 1, "attr_carisma", "hab_intimidacao", 7, "Disputa de FdV e domina corpo mortal", nil, "Assume controle absoluto do corpo físico de um mortal (V20, p. 155)."),
        },
    },
    fortitude = {
        id = "fortitude", name = "Fortitude", hasPaths = false,
        powers = {
            p(1, "fort_1", "Fortitude 1", 0, 0, nil, nil, 6, "Passivo: +1 dado Absorção Contundente/Letal/Agravado", nil, "Resistência sobrenatural a danos normais, fogo e luz solar (V20, p. 157)."),
            p(2, "fort_2", "Fortitude 2", 0, 0, nil, nil, 6, "Passivo: +2 dados de Absorção", nil, "Concede +2 dados em paradas de Absorção inclusive contra Agravado (V20, p. 157)."),
            p(3, "fort_3", "Fortitude 3", 0, 0, nil, nil, 6, "Passivo: +3 dados de Absorção", nil, "Concede +3 dados em paradas de Absorção inclusive contra Agravado (V20, p. 157)."),
            p(4, "fort_4", "Fortitude 4", 0, 0, nil, nil, 6, "Passivo: +4 dados de Absorção", nil, "Concede +4 dados em paradas de Absorção inclusive contra Agravado (V20, p. 157)."),
            p(5, "fort_5", "Fortitude 5", 0, 0, nil, nil, 6, "Passivo: +5 dados de Absorção", nil, "Concede +5 dados em paradas de Absorção inclusive contra Agravado (V20, p. 157)."),
        },
    },
    necromancy = {
        id = "necromancy", name = "Necromancia (Linha do Sepulcro)", hasPaths = true,
        powers = {
            p(1, "necro_1", "Visão do Cadáver", 0, 0, "attr_percepcao", "hab_consciencia", 6, "Dif 6 (enxerga últimos momentos nos olhos do morto)", nil, "Contempla a última cena presenciada por um cadáver (V20, p. 160)."),
            p(2, "necro_2", "Invocar a Alma", 0, 1, "attr_percepcao", "hab_ocultismo", 7, "Dif = FdV do espectro (ou 7)", nil, "Chama o fantasma de um falecido de volta através da Mortalha (V20, p. 161)."),
            p(3, "necro_3", "Compelir a Alma", 0, 1, "attr_manipulacao", "hab_ocultismo", 6, "Dif = FdV atual da aparição", nil, "Obriga uma aparição invocada a obedecer ordens por uma cena/hora (V20, p. 162)."),
            p(4, "necro_4", "Assombração", 1, 0, "attr_manipulacao", "hab_ocultismo", 7, "Dif = FdV da aparição; prende a local/objeto", nil, "Atrela um espírito a um objeto ou aposento específico (V20, p. 162)."),
            p(5, "necro_5", "Tormento", 0, 0, "attr_vigor", "hab_empatia", 6, "Dif = FdV da aparição (causa dano letal espiritual)", nil, "Golpeia diretamente o corpus de uma aparição com energia entrópica (V20, p. 163)."),
        },
    },
    obfuscate = {
        id = "obfuscate", name = "Ofuscação", hasPaths = false,
        powers = {
            p(1, "obf_1", "Manto das Sombras", 0, 0, nil, nil, 6, "Automático se imóvel e em cobertura", { id = "obf_cloak", stealthActive = true }, "Oculta-se das vistas enquanto permanecer imóvel na penumbra (V20, p. 184)."),
            p(2, "obf_2", "Presença Invisível", 0, 0, "attr_raciocinio", "hab_furtividade", 6, "Automático, ou Raciocínio + Furtividade se arriscar ruído", { id = "obf_unseen", stealthActive = true }, "Move-se pelo ambiente sem ser notado por observadores comuns (V20, p. 185)."),
            p(3, "obf_3", "Máscara das Mil Faces", 0, 0, "attr_manipulacao", "hab_performance", 7, "Dif 7", nil, "Projeta feições ilusórias escolhidas na mente de quem o observa (V20, p. 186)."),
            p(4, "obf_4", "Desaparecer do Olho da Mente", 0, 0, "attr_carisma", "hab_furtividade", 6, "Dif = Raciocínio + Prontidão das testemunhas", nil, "Desaparece abruptamente mesmo diante de olhares diretos (V20, p. 187)."),
            p(5, "obf_5", "Cobrir o Grupo", 0, 0, nil, nil, 6, "Estende poderes de Ofuscação a 1 aliado por ponto de Furtividade", nil, "Oculta ou disfarça companheiros próximos sob o mesmo véu mental (V20, p. 187)."),
        },
    },
    obtenebration = {
        id = "obtenebration", name = "Tenebrosidade", hasPaths = false,
        powers = {
            p(1, "obt_1", "Jogo de Sombras", 1, 0, nil, nil, 6, "1 Sangue/cena: +1 Furtividade/Intimidação, sufoca inimigos (-1 Vigor)", { id = "obt_shadowplay", bonusIntimidation = 1 }, "Dobra sombras naturais ao redor para intimidar e sufocar (V20, p. 189)."),
            p(2, "obt_2", "Mortalha das Trevas", 1, 0, "attr_manipulacao", "hab_ocultismo", 7, "Dif 7; nuvem cega e tira -2 Vigor dos mortais dentro", nil, "Cria esfera de escuridão abissal impenetrável até por visão aguçada (V20, p. 189)."),
            p(3, "obt_3", "Braços do Abismo", 1, 0, "attr_manipulacao", "hab_ocultismo", 7, "Dif 7; 1 tentáculo por sucesso (For/Des = nível Tenebrosidade)", nil, "Invoca tentáculos sólidos do Abismo para agarrar e esmagar (V20, p. 190)."),
            p(4, "obt_4", "Metamorfose Sombria", 2, 0, "attr_manipulacao", "hab_coragem_ref", 7, "2 Sangue; +1 ataque tentacular e -2 dados em inimigos adjacentes", { id = "obt_blackmeta", extraShadowAttack = true }, "Funde o corpo às trevas abissais ganhando tentáculos e terror (V20, p. 190)."),
            p(5, "obt_5", "Forma Tenebrosa", 3, 0, nil, nil, 6, "3 Sangue (3 turnos); imune a ataques físicos, vulnerável a fogo/sol", { id = "obt_tenebrous", shadowForm = true }, "Transforma o corpo inteiro em mancha fluida de escuridão pura (V20, p. 191)."),
        },
    },
    potence = {
        id = "potence", name = "Potência", hasPaths = false,
        powers = {
            p(1, "pot_1", "Potência 1", 0, 0, nil, nil, 6, "+1 dado Força passivo OU 1 Sangue = 1 sucesso automático no turno", nil, "Força vampírica sobre-humana em paradas de Força e dano corpo a corpo (V20, p. 192)."),
            p(2, "pot_2", "Potência 2", 0, 0, nil, nil, 6, "+2 dados Força passivos OU 1 Sangue = 2 sucessos automáticos", nil, "Eleva Potência para 2 dados ou 2 sucessos automáticos por 1 Sangue (V20, p. 192)."),
            p(3, "pot_3", "Potência 3", 0, 0, nil, nil, 6, "+3 dados Força passivos OU 1 Sangue = 3 sucessos automáticos", nil, "Eleva Potência para 3 dados ou 3 sucessos automáticos por 1 Sangue (V20, p. 192)."),
            p(4, "pot_4", "Potência 4", 0, 0, nil, nil, 6, "+4 dados Força passivos OU 1 Sangue = 4 sucessos automáticos", nil, "Eleva Potência para 4 dados ou 4 sucessos automáticos por 1 Sangue (V20, p. 192)."),
            p(5, "pot_5", "Potência 5", 0, 0, nil, nil, 6, "+5 dados Força passivos OU 1 Sangue = 5 sucessos automáticos", nil, "Eleva Potência para 5 dados ou 5 sucessos automáticos por 1 Sangue (V20, p. 192)."),
        },
    },
    presence = {
        id = "presence", name = "Presença", hasPaths = false,
        powers = {
            p(1, "pres_1", "Fascínio", 0, 0, "attr_carisma", "hab_performance", 7, "Dif 7 (afeta quantidade de pessoas conforme sucessos)", nil, "Desperta admiração magnética nos presentes ao redor (V20, p. 193)."),
            p(2, "pres_2", "Olhar Aterrorizante", 0, 0, "attr_carisma", "hab_intimidacao", 6, "Dif = Raciocínio + Coragem do alvo", nil, "Revela a face predatória vampírica causando medo paralisante ou fuga (V20, p. 194)."),
            p(3, "pres_3", "Transe", 0, 0, "attr_aparencia", "hab_empatia", 6, "Dif = FdV permanente do alvo", nil, "Inspira devoção emocional profunda no alvo por horas a semanas (V20, p. 195)."),
            p(4, "pres_4", "Convocação", 1, 0, "attr_carisma", "hab_labia", 5, "Dif 5 (conhecidos) ou 7 (encontro breve)", nil, "Chama psiquicamente um indivíduo conhecido para vir até você (V20, p. 195)."),
            p(5, "pres_5", "Majestade", 0, 1, nil, nil, 6, "1 FdV; alvos testam Coragem (dif = Carisma + Intimidação) p/ agir contra", { id = "pres_majesty", majestyActive = true }, "Aura soberana esmagadora que impede hostilidade direta na cena (V20, p. 196)."),
        },
    },
    protean = {
        id = "protean", name = "Metamorfose", hasPaths = false,
        powers = {
            p(1, "prot_1", "Olhos da Besta", 0, 0, nil, nil, 6, "Ativação livre (olhos vermelhos, visão total no escuro; +1 dif Social c/ mortais)", { id = "prot_eyes", nightVision = true }, "Enxerga perfeitamente na escuridão absoluta sem fonte de luz (V20, p. 197)."),
            p(2, "prot_2", "Garras da Besta", 1, 0, nil, nil, 6, "1 Sangue: garras causam Força + 1 de dano Agravado e -2 dif escalar", { id = "prot_claws", naturalAggravatedBonus = 1 }, "Transforma as unhas em garras letais que infligem dano Agravado (V20, p. 197)."),
            p(3, "prot_3", "Fusão com a Terra", 1, 0, nil, nil, 6, "1 Sangue: afunda no solo natural para proteção diurna", nil, "Funde o corpo à terra nua para abrigar-se do sol durante o dia (V20, p. 198)."),
            p(4, "prot_4", "Forma da Besta", 1, 0, nil, nil, 6, "1 Sangue (3 turnos): Forma de Lobo (For+1 Agrav, mov x2) ou Morcego (voo)", { id = "prot_beast", perceptionDiffMod = -2 }, "Assume a forma física de predador (lobo) ou fuga (morcego) (V20, p. 199)."),
            p(5, "prot_5", "Forma de Névoa", 1, 0, nil, nil, 6, "1 Sangue (3 turnos): imune a ataques físicos, -1 dado fogo/sol", { id = "prot_mist", mistForm = true }, "Dissolve o corpo em nuvem incorpórea de névoa (V20, p. 199)."),
        },
    },
    quietus = {
        id = "quietus", name = "Quietus", hasPaths = false,
        powers = {
            p(1, "quie_1", "Silêncio Mortal", 1, 0, nil, nil, 6, "1 Sangue (1 hora): anula todos os sons em raio de 6m", { id = "quie_silence", silenceAura = true }, "Cria zona de silêncio absoluto ao redor do Assamita (V20, p. 201)."),
            p(2, "quie_2", "Toque do Escorpião", 1, 0, "attr_fdv_ref", nil, 6, "Gasta Sangue + rola FdV (dif = Vigor + Fortitude do alvo) p/ reduzir Vigor", nil, "Converte vitae em veneno de contato que corrói o Vigor da vítima (V20, p. 201)."),
            p(3, "quie_3", "Chamado de Dagon", 0, 1, "attr_vigor", nil, 6, "Após tocar alvo, disputa estendida de Vigor contra Vigor da vítima (1 FdV)", nil, "Rompe os vasos internos do alvo à distância causando dano letal (V20, p. 202)."),
            p(4, "quie_4", "Carícia de Baal", 1, 0, nil, nil, 6, "1 Sangue por ataque na lâmina: converte dano da arma em Agravado", { id = "quie_baal", weaponAggravated = true }, "Ungir lâmina com vitae torna seu corte letalmente Agravado (V20, p. 202)."),
            p(5, "quie_5", "Gosto da Morte", 1, 0, "attr_vigor", "hab_esportes", 6, "Cospe sangue cáustico à distância (2 dados de dano Agravado por Sangue gasto)", nil, "Projeta jato ácido de vitae causando queimaduras Agravadas (V20, p. 203)."),
        },
    },
    serpentis = {
        id = "serpentis", name = "Serpentis", hasPaths = false,
        powers = {
            p(1, "serp_1", "Os Olhos da Serpente", 0, 0, nil, nil, 9, "Imobiliza mortais em contato visual; sobrenaturais resistem com FdV dif 9", nil, "Olhar dourado hipnótico que congela vítimas no lugar (V20, p. 208)."),
            p(2, "serp_2", "A Língua da Áspide", 0, 0, nil, nil, 6, "Língua bifurcada causa Força de dano Agravado e bebe sangue em combate", { id = "serp_tongue", naturalAggravatedBonus = 0 }, "Alonga a língua em ferrão cortante que causa feridas Agravadas (V20, p. 208)."),
            p(3, "serp_3", "A Pele da Víbora", 1, 1, nil, nil, 5, "1 Sangue + 1 FdV: dificuldade de Absorção cai para 5, mordida Agravada", { id = "serp_skin", soakDiffOverride = 5 }, "Escamas flexíveis reduzem dificuldade de Absorção para 5 e facilitam escapulir (V20, p. 209)."),
            p(4, "serp_4", "A Forma da Cobra", 1, 0, nil, nil, 6, "1 Sangue: transforma-se em naja negra gigante com mordida venenosa fatal", { id = "serp_cobra", cobraForm = true }, "Assume corpo ofídico letal a mortais e esguio em frestas (V20, p. 209)."),
            p(5, "serp_5", "O Coração das Trevas", 0, 0, nil, nil, 8, "Noite de lua nova: remove o próprio coração (-2 dif resistir Frenesi, imune a estaca)", nil, "Extrai e esconde o próprio coração em urna, impedindo paralisia por estaca (V20, p. 210)."),
        },
    },
    thaumaturgy = {
        id = "thaumaturgy", name = "Taumaturgia (Linha do Sangue)", hasPaths = true,
        powers = {
            p(1, "thau_1", "Um Gosto por Sangue", 0, 1, "attr_fdv_ref", nil, 4, "Testa FdV (dif = nível do poder + 3 = 4)", nil, "Identifica geração, sangue restante, natureza vampírica e diablerie por 1 gota (V20, p. 214)."),
            p(2, "thau_2", "Fúria do Sangue", 0, 1, "attr_fdv_ref", nil, 5, "Testa FdV dif 5 ao tocar alvo; força gasto de sangue da vítima", nil, "Obriga outro vampiro a queimar vitae involuntariamente e amplia dif. de Frenesi (V20, p. 214)."),
            p(3, "thau_3", "Sangue de Potência", 0, 1, "attr_fdv_ref", nil, 6, "Testa FdV dif 6; reduz efetivamente a Geração por 1 hora", nil, "Concentra temporariamente o próprio sangue para operar em Geração mais baixa (V20, p. 215)."),
            p(4, "thau_4", "Furto de Vitae", 0, 1, "attr_fdv_ref", nil, 7, "Testa FdV dif 7; drena sangue à distância (até 15m) sem Laço completo imediato", nil, "Arranca torrente de sangue da vítima pelo ar direto para o taumaturgo (V20, p. 215)."),
            p(5, "thau_5", "Caldeirão de Sangue", 0, 1, "attr_fdv_ref", nil, 8, "Testa FdV dif 8 ao toque; ferve 1 ponto de sangue por sucesso (1 Agravado cada)", nil, "Ferve o sangue nas veias do alvo, matando mortais e causando dano Agravado a Membros (V20, p. 216)."),
        },
    },
    vicissitude = {
        id = "vicissitude", name = "Vicissitude", hasPaths = false,
        powers = {
            p(1, "vici_1", "Aspecto Maleável", 1, 0, "attr_inteligencia", "hab_medicina", 6, "1 Sangue por parte alterada; Inteligência + Moldar Corpo/Medicina", nil, "Altera feições, voz, altura e tom de pele do próprio corpo (V20, p. 241)."),
            p(2, "vici_2", "Moldar Carne", 1, 0, "attr_destreza", "hab_medicina", 6, "1 Sangue; esculpe carne e gordura própria ou de terceiros", nil, "Deforma, desloca ou aprimora tecidos moles em si ou num alvo agarrado (V20, p. 242)."),
            p(3, "vici_3", "Moldar Ossos", 1, 0, "attr_forca", "hab_medicina", 7, "1 Sangue; esculpe ossos em espinhos ou armas (causa Letal sem anestesia)", nil, "Torce, funde e afia estruturas ósseas como armamento ou suplício (V20, p. 242)."),
            p(4, "vici_4", "Forma Horripilante", 2, 0, nil, nil, 6, "2 Sangue: +3 Força, +3 Destreza, +3 Vigor, Aparência 0, Briga +1 dano", { id = "vici_zulo", attrModPhysical = 3 }, "Assume a monstruosa forma guerreira Zulo com +3 em todos os Físicos (V20, p. 243)."),
            p(5, "vici_5", "Forma Sanguínea", 0, 0, nil, nil, 6, "Converte membros ou todo o corpo em vitae senciente imune a estacas/golpes", { id = "vici_bloodform", bloodForm = true }, "Liquefaz o próprio corpo em poça consciente de sangue vampírico (V20, p. 243)."),
        },
    },
}

return Catalog
```

Criar `Core/disciplines_engine.lua`:
```lua
local Clans = require("Data.clans")
local Catalog = require("Data.disciplines_catalog")
local Blood = require("Core.generation_blood")
local WM = require("Core.willpower_morality")

local Engine = {}

local function copyState(s)
    local o = {}
    for k, v in pairs(s or {}) do o[k] = v end
    local buffs = {}
    for k, v in pairs((s and s.activeBuffs) or {}) do buffs[k] = v end
    o.activeBuffs = buffs
    return o
end

function Engine.classifyCostCategory(clanId, discId, hasAdditionalDiscMerit)
    if clanId == "caitiff" then
        return "caitiff"
    end
    if hasAdditionalDiscMerit then
        return "cla"
    end
    local clan = Clans.CLANS[clanId or "brujah"]
    if clan then
        for _, cid in ipairs(clan.disciplines) do
            if cid == discId then
                return "cla"
            end
        end
    end
    return "fora_cla"
end

function Engine.getUnlockedPowers(discId, dots, customPowers)
    local lvl = tonumber(dots) or 0
    local out = {}
    local cat = Catalog.DISCIPLINES[discId]
    if cat then
        for _, pw in ipairs(cat.powers) do
            if pw.level <= lvl then
                table.insert(out, pw)
            end
        end
    end
    for _, cp in ipairs(customPowers or {}) do
        if (tonumber(cp.level) or 1) <= lvl then
            table.insert(out, cp)
        end
    end
    return out
end

function Engine.activatePower(state, discEntry, power, opts)
    opts = opts or {}
    local dots = tonumber(discEntry and discEntry.nivel) or 0
    if dots < (tonumber(power.level) or 1) and not opts.storytellerOverride then
        return { ok = false, newState = copyState(state), rollSpec = nil, buffToggled = nil, error = "Nível insuficiente na Disciplina para este poder." }
    end

    local nextSt = copyState(state)
    local bCost = tonumber(power.cost and power.cost.blood) or 0
    local wCost = tonumber(power.cost and power.cost.willpower) or 0

    if bCost > 0 then
        local bypass = (discEntry and discEntry.disc_id == "celerity")
        local bRes = Blood.spend(nextSt, bCost, {
            forDisciplineOrHeal = true,
            bypassTurnLimit = bypass,
            storytellerOverride = opts.storytellerOverride,
        })
        if not bRes.ok then
            return { ok = false, newState = copyState(state), rollSpec = nil, buffToggled = nil, error = bRes.error }
        end
        nextSt = bRes.newState
    end

    if wCost > 0 then
        nextSt.storytellerOverride = opts.storytellerOverride
        local wRes = WM.spendWillpower(nextSt, wCost)
        nextSt.storytellerOverride = nil
        if not wRes.ok then
            return { ok = false, newState = copyState(state), rollSpec = nil, buffToggled = nil, error = wRes.error }
        end
        nextSt = wRes.newState
    end

    local buffToggled = nil
    if power.toggleBuff then
        local bid = power.toggleBuff.id
        if nextSt.activeBuffs[bid] then
            nextSt.activeBuffs[bid] = nil
            buffToggled = { id = bid, active = false }
        else
            nextSt.activeBuffs[bid] = power.toggleBuff
            buffToggled = { id = bid, active = true }
        end
    end

    local rollSpec = nil
    if power.pool then
        rollSpec = {
            powerName = power.name,
            attr = power.pool.attr,
            hab = power.pool.hab,
            defaultDiff = power.defaultDiff or 6,
            diffHint = power.diffHint or "",
        }
    end

    return {
        ok = true,
        newState = nextSt,
        rollSpec = rollSpec,
        buffToggled = buffToggled,
        error = nil,
    }
end

function Engine.activateCelerityActions(state, pointsToActivate, opts)
    opts = opts or {}
    local pts = math.max(1, tonumber(pointsToActivate) or 1)
    local bRes = Blood.spend(state, pts, {
        forDisciplineOrHeal = true,
        bypassTurnLimit = true,
        storytellerOverride = opts.storytellerOverride,
    })
    if not bRes.ok then
        return { ok = false, newState = bRes.newState, error = bRes.error }
    end
    local nextSt = bRes.newState
    nextSt.activeCelerityActions = pts
    return { ok = true, newState = nextSt, error = nil }
end

function Engine.computeCombatModifiers(state, disciplinesList)
    state = state or {}
    local out = {
        passivePotenceDice = 0,
        activePotenceAuto = 0,
        passiveCelerityDice = 0,
        activeCelerityActions = tonumber(state.activeCelerityActions) or 0,
        fortitudeSoak = 0,
        sceneAttrMods = { forca = 0, destreza = 0, vigor = 0 },
        perceptionDiffMod = 0,
        soakDiffOverride = nil,
    }

    local auspexDots = 0
    for _, d in ipairs(disciplinesList or {}) do
        local n = tonumber(d.nivel) or 0
        if d.disc_id == "potence" and n > 0 then
            if d.activeAuto then
                out.activePotenceAuto = n
            else
                out.passivePotenceDice = n
            end
        elseif d.disc_id == "celerity" and n > 0 then
            if out.activeCelerityActions > 0 then
                out.passiveCelerityDice = math.max(0, n - out.activeCelerityActions)
            else
                out.passiveCelerityDice = n
            end
        elseif d.disc_id == "fortitude" and n > 0 then
            out.fortitudeSoak = n
        elseif d.disc_id == "auspex" and n > 0 then
            auspexDots = n
        end
    end

    local buffs = state.activeBuffs or {}
    if buffs.vici_zulo then
        out.sceneAttrMods.forca = out.sceneAttrMods.forca + 3
        out.sceneAttrMods.destreza = out.sceneAttrMods.destreza + 3
        out.sceneAttrMods.vigor = out.sceneAttrMods.vigor + 3
    end
    if buffs.auspex_senses and auspexDots > 0 then
        out.perceptionDiffMod = out.perceptionDiffMod - auspexDots
    end
    if buffs.prot_beast then
        out.perceptionDiffMod = out.perceptionDiffMod - 2
    end
    if buffs.serp_skin then
        out.soakDiffOverride = 5
    end

    return out
end

return Engine
```

- [ ] **Step 4: Rodar o teste e confirmar aprovação**

Executar: `python Tests/run_tests.py Tests/test_05_disciplines.lua`  
Resultado esperado: `[PASS] Tests\test_05_disciplines.lua`.

- [ ] **Step 5: Commit**

```bash
git add Data/disciplines_catalog.lua Core/disciplines_engine.lua Tests/test_05_disciplines.lua
git commit -m "feat(core): add universal 17 V20 disciplines catalog (85 powers) and automation engine"
```

---

### Task 6: Catálogo e Motor de Antecedentes V20, Qualidades, Defeitos e Numina

**Files:**
- Create: `Data/backgrounds_catalog.lua`
- Create: `Data/merits_flaws_catalog.lua`
- Create: `Core/backgrounds_engine.lua`
- Test: `Tests/test_06_backgrounds_merits.lua`

**Interfaces:**
- Produces:
  - `BackgroundsCatalog.BACKGROUNDS`: 13 antecedentes oficiais (`allies`, `alternate_identity`, `contacts`, `domain`, `fame`, `generation`, `herd`, `influence`, `mentor`, `resources`, `retainers`, `rituals`, `status`)
  - `MeritsFlawsCatalog.ITEMS` & `MeritsFlawsCatalog.NUMINA`
  - `BackgroundsEngine.deriveSheetEffects(baseGeneration, backgroundsList)` -> `{ effectiveGeneration, herdVessels, huntingBonusDice, huntingDiffMod, resourcesLabel, fameSocialDiffMod, statusSocialBonusDice }`
  - `BackgroundsEngine.buildActionRoll(bgId, dots, attrVal)` -> `{ canRoll, pool, defaultDiff, title }`
  - `BackgroundsEngine.aggregateMeritsFlaws(itemsList)` -> `{ totalMeritCost, totalFlawGainRaw, effectiveFlawBonus, hugeSize, perceptionDiffMod, hasAdditionalDisc, thinBloodGenOverride }`

- [ ] **Step 1: Escrever o teste falho `Tests/test_06_backgrounds_merits.lua`**

```lua
local BgEngine = require("Core.backgrounds_engine")

-- 1. Geração derivada (13 - 3 = 10ª), Rebanho (+2 dados caça, 7 recipientes), Domínio (-2 dif caça), Recursos 3, Fama 2, Status 1
local fx = BgEngine.deriveSheetEffects(13, {
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
assert(fx.resourcesLabel:find("Classe Média Alta") ~= nil or fx.resourcesLabel ~= "")

-- 2. Rolagem de rede de Contatos Secundários (Carisma + Contatos, dif 7)
local roll = BgEngine.buildActionRoll("contacts", 3, 4)
assert(roll.canRoll == true and roll.pool == 7 and roll.defaultDiff == 7)

-- 3. Qualidades e Defeitos: teto oficial de +7 pontos de bônus oriundos de Defeitos + Tamanho Grande
local mf = BgEngine.aggregateMeritsFlaws({
    { item_id = "huge_size", tipo = "qualidade", pontos = 4, ativo = true },
    { item_id = "flaw_1",    tipo = "defeito",   pontos = 5, ativo = true },
    { item_id = "flaw_2",    tipo = "defeito",   pontos = 4, ativo = true },
})
assert(mf.totalMeritCost == 4)
assert(mf.totalFlawGainRaw == 9 and mf.effectiveFlawBonus == 7, "Defeitos só concedem até +7 pontos de bônus na V20")
assert(mf.hugeSize == true)
```

- [ ] **Step 2: Rodar o teste para confirmar falha**

Executar: `python Tests/run_tests.py Tests/test_06_backgrounds_merits.lua`  
Resultado esperado: `FAIL` com `module 'Core.backgrounds_engine' not found`.

- [ ] **Step 3: Implementar `Data/backgrounds_catalog.lua`, `Data/merits_flaws_catalog.lua` e `Core/backgrounds_engine.lua`**

Criar `Data/backgrounds_catalog.lua`:
```lua
local BgCatalog = {}

BgCatalog.ORDER = {
    "allies", "alternate_identity", "contacts", "domain", "fame", "generation",
    "herd", "influence", "mentor", "resources", "retainers", "rituals", "status",
}

BgCatalog.HERD_VESSELS = { [0] = 0, [1] = 3, [2] = 7, [3] = 15, [4] = 30, [5] = 60 }

BgCatalog.RESOURCES_TIERS = {
    [0] = "Indigente (Sem renda fixa)",
    [1] = "Economias Modestas (~R$ 2.500/mês)",
    [2] = "Classe Média (~R$ 6.000/mês)",
    [3] = "Classe Média Alta / Confortável (~R$ 20.000/mês)",
    [4] = "Rico / Abastado (~R$ 80.000/mês)",
    [5] = "Multimilionário (~R$ 350.000+/mês)",
}

BgCatalog.BACKGROUNDS = {
    allies             = { id = "allies",             name = "Aliados",                vampireOnly = false, defaultDiff = 6, actionTitle = "Acionar Aliados" },
    alternate_identity = { id = "alternate_identity", name = "Identidade Alternativa", vampireOnly = false, defaultDiff = 6, actionTitle = "Sustentar Disfarce Documental" },
    contacts           = { id = "contacts",           name = "Contatos",               vampireOnly = false, defaultDiff = 7, actionTitle = "Sondar Rede de Contatos" },
    domain             = { id = "domain",             name = "Domínio",                vampireOnly = true,  defaultDiff = 6, actionTitle = "Patrulhar / Caçar no Domínio" },
    fame               = { id = "fame",               name = "Fama",                   vampireOnly = false, defaultDiff = 6, actionTitle = "Usar Reconhecimento Público" },
    generation         = { id = "generation",         name = "Geração",                vampireOnly = true,  defaultDiff = 6, actionTitle = nil },
    herd               = { id = "herd",               name = "Rebanho",                vampireOnly = true,  defaultDiff = 6, actionTitle = "Alimentar-se do Rebanho" },
    influence          = { id = "influence",          name = "Influência",             vampireOnly = false, defaultDiff = 6, actionTitle = "Exercer Influência Institucional" },
    mentor             = { id = "mentor",             name = "Mentor",                 vampireOnly = false, defaultDiff = 6, actionTitle = "Solicitar Conselho/Auxílio do Mentor" },
    resources          = { id = "resources",          name = "Recursos",               vampireOnly = false, defaultDiff = 6, actionTitle = "Liquidar Recursos / Aquisição" },
    retainers          = { id = "retainers",          name = "Lacaios",                vampireOnly = false, defaultDiff = 6, actionTitle = "Comandar Lacaio" },
    rituals            = { id = "rituals",            name = "Rituais",                vampireOnly = true,  defaultDiff = 6, actionTitle = "Consultar Grimório de Rituais" },
    status             = { id = "status",             name = "Status",                 vampireOnly = false, defaultDiff = 6, actionTitle = "Invocar Prestígio de Status" },
}

return BgCatalog
```

Criar `Data/merits_flaws_catalog.lua`:
```lua
local MFCatalog = {}

MFCatalog.ITEMS = {
    acute_senses    = { id = "acute_senses",    name = "Sentidos Aguçados",     tipo = "qualidade", pontos = 1, effect = "perception_diff_-2" },
    ambidextrous    = { id = "ambidextrous",    name = "Ambidestro",            tipo = "qualidade", pontos = 1, effect = "no_offhand_penalty" },
    iron_will       = { id = "iron_will",       name = "Vontade de Ferro",      tipo = "qualidade", pontos = 3, effect = "resist_dominate_+3" },
    huge_size       = { id = "huge_size",       name = "Tamanho Grande",        tipo = "qualidade", pontos = 4, effect = "extra_bruised_box" },
    additional_disc = { id = "additional_disc", name = "Disciplina Adicional",  tipo = "qualidade", pontos = 5, effect = "additional_in_clan_disc" },
    gen_14th        = { id = "gen_14th",        name = "Décima Quarta Geração", tipo = "defeito",   pontos = 2, effect = "force_gen_14" },
    gen_15th        = { id = "gen_15th",        name = "Décima Quinta Geração", tipo = "defeito",   pontos = 4, effect = "force_gen_15" },
    bad_sight       = { id = "bad_sight",       name = "Deficiência Visual",    tipo = "defeito",   pontos = 1, effect = "perception_diff_+2" },
}

MFCatalog.NUMINA = {
    true_faith  = { id = "true_faith",  name = "Fé Verdadeira",       poolAttr = "attr_fdv_ref",      defaultDiff = 7, summary = "Repele vampiros (teste de Fé vs FdV/Autocontrole) e protege contra Dominação (V20, p. 372)." },
    hedge_magic = { id = "hedge_magic", name = "Magia de Cerca",      poolAttr = "attr_inteligencia", defaultDiff = 7, summary = "Trilhas lineares de feitiçaria mortal ritualística e encantamentos." },
    psychic     = { id = "psychic",     name = "Fenômeno Psíquico",   poolAttr = "attr_percepcao",    defaultDiff = 7, summary = "Aptidão psíquica humana como telepatia, pirocinese ou clarividência." },
}

return MFCatalog
```

Criar `Core/backgrounds_engine.lua`:
```lua
local BgCatalog = require("Data.backgrounds_catalog")
local MFCatalog = require("Data.merits_flaws_catalog")

local BgEngine = {}

function BgEngine.deriveSheetEffects(baseGeneration, backgroundsList)
    local baseGen = tonumber(baseGeneration) or 13
    local genDots = 0
    local herdDots = 0
    local domainDots = 0
    local resDots = 0
    local fameDots = 0
    local statusDots = 0

    for _, bg in ipairs(backgroundsList or {}) do
        local n = math.max(0, tonumber(bg.nivel) or 0)
        if bg.bg_id == "generation" then genDots = genDots + n
        elseif bg.bg_id == "herd" then herdDots = math.min(5, herdDots + n)
        elseif bg.bg_id == "domain" then domainDots = math.min(5, domainDots + n)
        elseif bg.bg_id == "resources" then resDots = math.min(5, resDots + n)
        elseif bg.bg_id == "fame" then fameDots = math.min(5, fameDots + n)
        elseif bg.bg_id == "status" then statusDots = math.min(5, statusDots + n)
        end
    end

    local effGen = math.max(4, baseGen - genDots)
    return {
        effectiveGeneration = effGen,
        herdVessels = BgCatalog.HERD_VESSELS[herdDots] or 0,
        huntingBonusDice = herdDots,
        huntingDiffMod = -domainDots,
        resourcesLabel = BgCatalog.RESOURCES_TIERS[resDots] or BgCatalog.RESOURCES_TIERS[0],
        fameSocialDiffMod = -fameDots,
        statusSocialBonusDice = statusDots,
    }
end

function BgEngine.buildActionRoll(bgId, dots, attrVal)
    local entry = BgCatalog.BACKGROUNDS[bgId]
    local n = math.max(0, tonumber(dots) or 0)
    local a = math.max(0, tonumber(attrVal) or 0)
    if not entry or not entry.actionTitle or n <= 0 then
        return { canRoll = false, pool = 0, defaultDiff = 6, title = "Antecedente sem ação rolável" }
    end
    return {
        canRoll = true,
        pool = a + n,
        defaultDiff = entry.defaultDiff or 6,
        title = entry.actionTitle,
    }
end

function BgEngine.aggregateMeritsFlaws(itemsList)
    local meritCost = 0
    local flawGain = 0
    local hugeSize = false
    local percDiffMod = 0
    local hasAddDisc = false
    local thinGen = nil

    for _, it in ipairs(itemsList or {}) do
        if it.ativo ~= false then
            local pts = math.max(0, tonumber(it.pontos) or 0)
            if it.tipo == "defeito" then
                flawGain = flawGain + pts
            else
                meritCost = meritCost + pts
            end

            local cat = MFCatalog.ITEMS[it.item_id]
            local eff = (cat and cat.effect) or it.mod_tipo
            if eff == "extra_bruised_box" then hugeSize = true
            elseif eff == "perception_diff_-2" then percDiffMod = percDiffMod - 2
            elseif eff == "perception_diff_+2" then percDiffMod = percDiffMod + 2
            elseif eff == "additional_in_clan_disc" then hasAddDisc = true
            elseif eff == "force_gen_14" then thinGen = 14
            elseif eff == "force_gen_15" then thinGen = 15
            end
        end
    end

    return {
        totalMeritCost = meritCost,
        totalFlawGainRaw = flawGain,
        effectiveFlawBonus = math.min(7, flawGain),
        hugeSize = hugeSize,
        perceptionDiffMod = percDiffMod,
        hasAdditionalDisc = hasAddDisc,
        thinBloodGenOverride = thinGen,
    }
end

return BgEngine
```

- [ ] **Step 4: Rodar o teste e confirmar aprovação**

Executar: `python Tests/run_tests.py Tests/test_06_backgrounds_merits.lua`  
Resultado esperado: `[PASS] Tests\test_06_backgrounds_merits.lua`.

- [ ] **Step 5: Commit**

```bash
git add Data/backgrounds_catalog.lua Data/merits_flaws_catalog.lua Core/backgrounds_engine.lua Tests/test_06_backgrounds_merits.lua
git commit -m "feat(core): add automated V20 backgrounds, merits/flaws cap and numina catalog"
```

---

### Task 7: Validador de Criação (Vampiro e Mortal), Evolução por XP Auditada e Inicializador `V20`

**Files:**
- Create: `Core/creation.lua`
- Create: `Core/experience.lua`
- Create: `Core/v20_init.lua`
- Test: `Tests/test_07_creation_xp.lua`

**Interfaces:**
- Produces:
  - `Creation.PROFILES`: `vampire_neonate`, `mortal_standard_643`, `mortal_heroic_753`
  - `Creation.validate(state)` -> `{ valid = boolean, freebiesAvailable = number, freebiesSpent = number, freebiesRemaining = number, errors = string[] }`
  - `Creation.applyMortalSupernaturalMode(state, mode)` -> `newState` (`"humano"|"carnical"|"numina"`)
  - `Experience.calculateUpgradeCost(traitKind, currentRating, opts)` -> `number`
  - `Experience.submitUpgrade(state, request, opts)` -> `{ ok, newState, auditEntry, error }`
  - `Experience.resolvePending(state, auditEntry, approve, masterLogin)` -> `{ ok, newState, updatedEntry, error }`
  - `V20` global table bundling all `Data/` and `Core/` modules idempotently

- [ ] **Step 1: Escrever o teste falho `Tests/test_07_creation_xp.lua`**

```lua
local V20 = require("Core.v20_init")

-- 1. Custos oficiais de XP V20 (incluindo Caitiff x6, Nova Disciplina 10, Nova Habilidade 3, Fora do Clã x7, Clã x5)
assert(V20.Experience.calculateUpgradeCost("ability", 0, {}) == 3)
assert(V20.Experience.calculateUpgradeCost("ability", 2, {}) == 4)
assert(V20.Experience.calculateUpgradeCost("attribute", 3, {}) == 12)
assert(V20.Experience.calculateUpgradeCost("discipline", 0, { costCategory = "fora_cla" }) == 10)
assert(V20.Experience.calculateUpgradeCost("discipline", 2, { costCategory = "cla" }) == 10)
assert(V20.Experience.calculateUpgradeCost("discipline", 2, { costCategory = "fora_cla" }) == 14)
assert(V20.Experience.calculateUpgradeCost("discipline", 2, { costCategory = "caitiff" }) == 12)
assert(V20.Experience.calculateUpgradeCost("willpower", 5, {}) == 5)

-- 2. Validação de criação Vampiro Neófito (7/5/3, 13/9/5, 15 Bônus + Defeitos até +7)
local validVamp = {
    nome = "[TESTE_E2E] Jack Brujah",
    profile = "vampire_neonate",
    cla_id = "brujah",
    attrGroups = { 7, 5, 3 },
    abilityGroups = { 13, 9, 5 },
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
assert(cv.valid == true and cv.freebiesRemaining == 0)

-- Habilidade base > 3 antes de bônus deve invalidar criação
validVamp.maxBaseAbility = 4
assert(V20.Creation.validate(validVamp).valid == false)

-- 3. Fluxo de XP com aprovação do Narrador vs compra direta
local ch = { nome = "[TESTE_E2E] Jack Brujah", xp_total = 20, xp_gasto = 0, xp_exige_aprovacao = true, attr_forca = 3 }
local sub = V20.Experience.submitUpgrade(ch, {
    traitKind = "attribute", field = "attr_forca", currentRating = 3, label = "Força 3 -> 4", author = "jogador1"
}, { isMestre = false })
assert(sub.ok == true and sub.auditEntry.status == "pendente" and sub.newState.attr_forca == 3)

local app = V20.Experience.resolvePending(sub.newState, sub.auditEntry, true, "NarradorMestre")
assert(app.ok == true and app.updatedEntry.status == "aprovado" and app.newState.attr_forca == 4 and app.newState.xp_gasto == 12)

-- 4. Transição Mortal -> Carniçal concede Potência 1 e Vitae máx 2
local mortal = { nome = "[TESTE_E2E] Helena Mortal", isVampire = false, mortal_sobrenatural_modo = "humano" }
local ghoul = V20.Creation.applyMortalSupernaturalMode(mortal, "carnical")
assert(ghoul.isGhoul == true and ghoul.sangue_max == 2 and ghoul.ghoulPotence == 1)
```

- [ ] **Step 2: Rodar o teste para confirmar falha**

Executar: `python Tests/run_tests.py Tests/test_07_creation_xp.lua`  
Resultado esperado: `FAIL` com `module 'Core.v20_init' not found`.

- [ ] **Step 3: Implementar `Core/creation.lua`, `Core/experience.lua` e `Core/v20_init.lua`**

Criar `Core/creation.lua`:
```lua
local Creation = {}

Creation.FREEBIE_COSTS = {
    attributes = 5,
    abilities = 2,
    disciplines = 7,
    backgrounds = 1,
    virtues = 2,
    morality = 1,
    willpower = 1,
    merits = 1, -- multiplicado pelos pontos da qualidade
}

Creation.PROFILES = {
    vampire_neonate = {
        attr = { 7, 5, 3 }, abilities = { 13, 9, 5 }, disciplines = 3, backgrounds = 5, virtues = 7, freebies = 15,
    },
    mortal_standard_643 = {
        attr = { 6, 4, 3 }, abilities = { 11, 7, 4 }, disciplines = 0, backgrounds = 5, virtues = 7, freebies = 21,
    },
    mortal_heroic_753 = {
        attr = { 7, 5, 3 }, abilities = { 13, 9, 5 }, disciplines = 0, backgrounds = 5, virtues = 7, freebies = 15,
    },
}

local function sortedDesc(list)
    local copy = {}
    for i, v in ipairs(list or {}) do copy[i] = tonumber(v) or 0 end
    table.sort(copy, function(a, b) return a > b end)
    return copy
end

local function matchesTargets(given, targets, errors, label)
    local s = sortedDesc(given)
    for i = 1, #targets do
        if (s[i] or 0) > targets[i] then
            table.insert(errors, string.format("%s excede o limite do grupo %d (%d > %d).", label, i, s[i] or 0, targets[i]))
        elseif (s[i] or 0) < targets[i] then
            table.insert(errors, string.format("%s possui pontos não distribuídos no grupo %d (%d < %d).", label, i, s[i] or 0, targets[i]))
        end
    end
end

function Creation.validate(state)
    state = state or {}
    local prof = Creation.PROFILES[state.profile or "vampire_neonate"] or Creation.PROFILES.vampire_neonate
    local errors = {}

    matchesTargets(state.attrGroups or {0, 0, 0}, prof.attr, errors, "Atributos")
    matchesTargets(state.abilityGroups or {0, 0, 0}, prof.abilities, errors, "Habilidades")

    if (tonumber(state.maxBaseAbility) or 0) > 3 then
        table.insert(errors, "Nenhuma Habilidade pode ultrapassar 3 pontos antes dos Pontos de Bônus (V20, p. 80).")
    end

    if state.cla_id == "nosferatu" and (tonumber(state.attr_aparencia) or 0) ~= 0 then
        table.insert(errors, "Nosferatu possui Aparência obrigatoriamente igual a 0.")
    end

    if (tonumber(state.baseDisciplines) or 0) ~= prof.disciplines then
        table.insert(errors, string.format("Disciplinas iniciais devem somar %d pontos.", prof.disciplines))
    end
    if (tonumber(state.baseBackgrounds) or 0) ~= prof.backgrounds then
        table.insert(errors, string.format("Antecedentes iniciais devem somar %d pontos.", prof.backgrounds))
    end
    if (tonumber(state.baseVirtues) or 0) ~= prof.virtues then
        table.insert(errors, string.format("Virtudes iniciais devem somar %d pontos.", prof.virtues))
    end

    local flawBonus = math.min(7, math.max(0, tonumber(state.flawsBonus) or 0))
    local available = prof.freebies + flawBonus
    local fp = state.freebiePurchases or {}
    local spent = 0
    for k, cost in pairs(Creation.FREEBIE_COSTS) do
        spent = spent + ((tonumber(fp[k]) or 0) * cost)
    end

    if spent > available then
        table.insert(errors, string.format("Pontos de Bônus excedidos (%d gastos de %d disponíveis).", spent, available))
    end

    return {
        valid = (#errors == 0),
        freebiesAvailable = available,
        freebiesSpent = spent,
        freebiesRemaining = available - spent,
        errors = errors,
    }
end

function Creation.applyMortalSupernaturalMode(state, mode)
    local nextSt = {}
    for k, v in pairs(state or {}) do nextSt[k] = v end
    nextSt.mortal_sobrenatural_modo = mode or "humano"
    if mode == "carnical" then
        nextSt.isGhoul = true
        nextSt.sangue_max = 2
        nextSt.sangue_por_turno = 1
        nextSt.ghoulPotence = 1
    elseif mode == "numina" then
        nextSt.isGhoul = false
        nextSt.hasNumina = true
    else
        nextSt.isGhoul = false
        nextSt.hasNumina = false
        nextSt.sangue_max = 0
        nextSt.sangue_por_turno = 0
        nextSt.ghoulPotence = 0
    end
    return nextSt
end

return Creation
```

Criar `Core/experience.lua`:
```lua
local Experience = {}

function Experience.calculateUpgradeCost(traitKind, currentRating, opts)
    opts = opts or {}
    local cur = math.max(0, tonumber(currentRating) or 0)

    if traitKind == "attribute" then
        return cur * 4
    elseif traitKind == "ability" then
        return (cur == 0) and 3 or (cur * 2)
    elseif traitKind == "discipline" then
        if cur == 0 then return 10 end
        local cat = opts.costCategory or "fora_cla"
        if cat == "cla" then return cur * 5 end
        if cat == "caitiff" then return cur * 6 end
        return cur * 7
    elseif traitKind == "secondary_path" then
        return (cur == 0) and 7 or (cur * 4)
    elseif traitKind == "virtue" then
        return cur * 2
    elseif traitKind == "morality" then
        return cur * 2
    elseif traitKind == "willpower" then
        return math.max(1, cur)
    end
    return 0
end

function Experience.submitUpgrade(state, request, opts)
    opts = opts or {}
    local nextSt = {}
    for k, v in pairs(state or {}) do nextSt[k] = v end

    local cur = tonumber(request.currentRating) or 0
    local cost = Experience.calculateUpgradeCost(request.traitKind, cur, { costCategory = request.costCategory })
    local avail = (tonumber(nextSt.xp_total) or 0) - (tonumber(nextSt.xp_gasto) or 0)

    if cost > avail and not opts.storytellerOverride then
        return { ok = false, newState = nextSt, auditEntry = nil, error = string.format("XP insuficiente (custo %d, disponível %d).", cost, avail) }
    end

    local requiresApproval = (nextSt.xp_exige_aprovacao ~= false) and (not opts.isMestre)
    local entry = {
        autor_login = request.author or "Jogador",
        tipo_evento = "evolucao_xp",
        descricao = request.label or request.field,
        custo_xp = cost,
        campo_alvo = request.field,
        novo_valor = cur + 1,
        status = requiresApproval and "pendente" or "aprovado",
    }

    if not requiresApproval then
        nextSt.xp_gasto = (tonumber(nextSt.xp_gasto) or 0) + cost
        if request.field then
            nextSt[request.field] = cur + 1
        end
    end

    return { ok = true, newState = nextSt, auditEntry = entry, error = nil }
end

function Experience.resolvePending(state, auditEntry, approve, masterLogin)
    local nextSt = {}
    for k, v in pairs(state or {}) do nextSt[k] = v end
    local updated = {}
    for k, v in pairs(auditEntry or {}) do updated[k] = v end

    if updated.status ~= "pendente" then
        return { ok = false, newState = nextSt, updatedEntry = updated, error = "Solicitação já foi processada." }
    end

    updated.aprovador_login = masterLogin or "Narrador"
    if not approve then
        updated.status = "recusado"
        return { ok = true, newState = nextSt, updatedEntry = updated, error = nil }
    end

    local avail = (tonumber(nextSt.xp_total) or 0) - (tonumber(nextSt.xp_gasto) or 0)
    local cost = tonumber(updated.custo_xp) or 0
    if cost > avail then
        return { ok = false, newState = nextSt, updatedEntry = updated, error = "Saldo de XP tornou-se insuficiente antes da aprovação." }
    end

    updated.status = "aprovado"
    nextSt.xp_gasto = (tonumber(nextSt.xp_gasto) or 0) + cost
    if updated.campo_alvo then
        nextSt[updated.campo_alvo] = tonumber(updated.novo_valor) or 1
    end
    return { ok = true, newState = nextSt, updatedEntry = updated, error = nil }
end

return Experience
```

Criar `Core/v20_init.lua`:
```lua
V20 = V20 or {
    Traits             = require("Data.attributes_abilities"),
    Generations        = require("Data.generations"),
    Clans              = require("Data.clans"),
    MoralityCatalog    = require("Data.morality_virtues"),
    DisciplinesCatalog = require("Data.disciplines_catalog"),
    BackgroundsCatalog = require("Data.backgrounds_catalog"),
    MeritsFlawsCatalog = require("Data.merits_flaws_catalog"),

    Dice               = require("Core.dice"),
    Blood              = require("Core.generation_blood"),
    Health             = require("Core.health"),
    WillpowerMorality  = require("Core.willpower_morality"),
    DisciplinesEngine  = require("Core.disciplines_engine"),
    BackgroundsEngine  = require("Core.backgrounds_engine"),
    Creation           = require("Core.creation"),
    Experience         = require("Core.experience"),
}

return V20
```

- [ ] **Step 4: Rodar o teste e confirmar aprovação**

Executar: `python Tests/run_tests.py Tests/test_07_creation_xp.lua`  
Resultado esperado: `[PASS] Tests\test_07_creation_xp.lua`.

- [ ] **Step 5: Commit**

```bash
git add Core/creation.lua Core/experience.lua Core/v20_init.lua Tests/test_07_creation_xp.lua
git commit -m "feat(core): add creation validator, audited XP engine, ghoul toggle and V20 bundle"
```

---

### Task 8: Ponte `Adapter/firecast_bridge.lua` e Geradores Parametrizados LFM (`Brujah` & `Mortal`)

**Files:**
- Create: `Adapter/firecast_bridge.lua`
- Create: `Templates/theme_gothic.py`
- Create: `Templates/generate_vampire_lfm.py`
- Create: `Templates/generate_mortal_lfm.py`
- Create (generated): `Sheets/frmBrujah.lfm`, `Sheets/frmMortal.lfm`
- Test: `Tests/test_08_bridge_and_lfm_gen.py`

**Interfaces:**
- Consumes: `Core/v20_init.lua`
- Produces:
  - `V20Bridge.syncDerivedFields(sheet)`: recalcula automaticamente `geracao`, `sangue_max`, `sangue_por_turno`, `aura_label`, `vitalidade_label` e `penalidade_ferimento` no nó `sheet`
  - `V20Bridge.rollFromSheet(sheet, opts, firecastApi, dialogsApi)`: executa a rolagem oficial d10 no chat (lendo `rolado.ops` do servidor Firecast) ou localmente quando fora de sala, aplicando `Dice.buildPool` + `Dice.evaluate` + gasto de `FdV`
  - `V20Bridge.activateDisciplinePower(sheet, discNode, powerId, firecastApi, dialogsApi)`
  - `V20Bridge.logAudit(sheet, ndbApi, firecastApi, eventType, description, costXp, status, targetField, newVal)`
  - `Sheets/frmBrujah.lfm` (`dataType="br.com.v20.Brujah"`, `name="frmBrujah"`) e `Sheets/frmMortal.lfm` (`dataType="br.com.v20.Mortal"`, `name="frmMortal"`)

- [ ] **Step 1: Escrever o teste falho `Tests/test_08_bridge_and_lfm_gen.py`**

```python
#!/usr/bin/env python3
"""Valida a ponte Firecast em Lua 5.4 (com mock de sala/rolado.ops) e a geração XML dos LFMs."""
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from Tests.run_tests import run_lua_file  # noqa: E402


def main() -> None:
    # 1. Gerar os LFMs Brujah e Mortal
    subprocess.run([sys.executable, os.path.join(ROOT, "Templates", "generate_vampire_lfm.py"), "--clan", "brujah"], check=True)
    subprocess.run([sys.executable, os.path.join(ROOT, "Templates", "generate_mortal_lfm.py")], check=True)

    for rel, expected_dt, expected_name in [
        ("Sheets/frmBrujah.lfm", "br.com.v20.Brujah", "frmBrujah"),
        ("Sheets/frmMortal.lfm", "br.com.v20.Mortal", "frmMortal"),
    ]:
        full = os.path.join(ROOT, rel)
        assert os.path.exists(full), f"Arquivo {rel} não gerado"
        root = ET.parse(full).getroot()
        assert root.attrib.get("dataType") == expected_dt
        assert root.attrib.get("name") == expected_name
        # Regra 2 SDK 3.7b: nenhum <dataLink> aninhado fora da raiz <form>
        direct_datalinks = [c for c in root if c.tag == "dataLink"]
        all_datalinks = list(root.iter("dataLink"))
        assert len(direct_datalinks) == len(all_datalinks) and len(direct_datalinks) >= 1, (
            f"Todos os <dataLink> em {rel} devem ser filhos diretos de <form>"
        )
        # Regra 4 SDK 3.7b: proibido left/right em horzTextAlign
        for el in root.iter():
            for attr in ("horzTextAlign", "vertTextAlign"):
                if attr in el.attrib:
                    assert el.attrib[attr] in ("leading", "center", "trailing"), f"{attr} inválido em {rel}"

    # 2. Testar V20Bridge com mock de chat e rolado.ops dentro da lua54x64.dll
    lua_probe = os.path.join(ROOT, "output", "probe_bridge.lua")
    os.makedirs(os.path.dirname(lua_probe), exist_ok=True)
    with open(lua_probe, "w", encoding="utf-8") as f:
        f.write('''
local Bridge = require("Adapter.firecast_bridge")
local sentMessages = {}
local mockFirecast = {
    interpretarRolagem = function(expr) return { expr = expr } end,
    getMesaDe = function(_)
        return {
            meuJogador = { isMestre = false, login = "tester_e2e" },
            activeChat = {
                rolarDados = function(_, rol, title, cb)
                    cb({ ops = { { tipo = "dado", resultados = { 10, 8, 1 } } } })
                end,
                enviarMensagem = function(_, msg)
                    table.insert(sentMessages, msg)
                end,
            }
        }
    end
}
local mockSheet = {
    nome = "[TESTE_E2E] Jack Brujah",
    cla_id = "brujah",
    is_vampire = true,
    geracao_base = 13,
    attr_percepcao = 2,
    hab_investigacao = 1,
    roll_attr_id = "attr_percepcao",
    roll_hab_id = "hab_investigacao",
    roll_diff = 6,
    roll_usar_espec = true,
    roll_gastar_fdv = false,
    fdv_temp = 5,
    sangue_atual = 8,
}
Bridge.syncDerivedFields(mockSheet)
assert(mockSheet.sangue_max == 10 and mockSheet.sangue_por_turno == 1)
Bridge.rollFromSheet(mockSheet, {}, mockFirecast, { showMessage = function() end })
assert(#sentMessages == 1, "Deveria ter enviado diagnóstico V20 no chat")
assert(sentMessages[1]:find("2 Sucesso") ~= nil, "10 com espec (2) + 8 (1) - dado 1 (1) = 2 sucessos! Msg: " .. sentMessages[1])
''')
    run_lua_file(lua_probe)
    os.remove(lua_probe)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Rodar o teste para confirmar falha**

Executar: `python Tests/run_tests.py Tests/test_08_bridge_and_lfm_gen.py`  
Resultado esperado: `FAIL` (arquivos `Templates/generate_vampire_lfm.py` e `Adapter/firecast_bridge.lua` ainda não existem).

- [ ] **Step 3: Implementar `Adapter/firecast_bridge.lua`, `Templates/theme_gothic.py`, `Templates/generate_vampire_lfm.py` e `Templates/generate_mortal_lfm.py`**

Criar `Adapter/firecast_bridge.lua`:
```lua
local V20 = require("Core.v20_init")

local Bridge = {}

function Bridge.extractRollFaces(rolado)
    local faces = {}
    if type(rolado) == "table" and type(rolado.ops) == "table" then
        for _, op in ipairs(rolado.ops) do
            if op.tipo == "dado" and type(op.resultados) == "table" then
                for _, v in ipairs(op.resultados) do
                    table.insert(faces, tonumber(v) or 0)
                end
            end
        end
    end
    return faces
end

function Bridge.formatChatReport(actorName, label, evalRes, faces, warnings)
    local facesStr = table.concat(faces, ", ")
    local statusTag = "FALHA SIMPLES"
    if evalRes.outcome == "botch" then
        statusTag = "💀 FALHA CRÍTICA (BOTCH)!"
    elseif evalRes.outcome == "success" then
        statusTag = string.format("🩸 %d Sucesso(s) — %s!", evalRes.totalSuccesses, evalRes.degree)
    end
    local msg = string.format(
        "[%s] %s | Dif %d | Dados [%s] -> %s",
        actorName or "Personagem", label or "Teste V20", evalRes.difficulty, facesStr, statusTag
    )
    if warnings and #warnings > 0 then
        msg = msg .. " (" .. table.concat(warnings, " ") .. ")"
    end
    return msg
end

function Bridge.isStoryteller(sheet, firecastApi)
    local fc = firecastApi or _G.Firecast
    if not fc or not fc.getMesaDe then return true end
    local mesa = fc.getMesaDe(sheet)
    if mesa == nil then return true end
    return (mesa.meuJogador ~= nil and mesa.meuJogador.isMestre == true)
end

function Bridge.syncDerivedFields(sheet, ndbApi)
    if type(sheet) ~= "table" then return end
    local ndb = ndbApi or _G.NDB
    local bgList = {}
    if ndb and ndb.getChildNodes and sheet.rclAntecedentes_node then
        bgList = ndb.getChildNodes(sheet.rclAntecedentes_node) or {}
    end

    local isVamp = (sheet.is_vampire ~= false) and (sheet.mortal_sobrenatural_modo == nil or sheet.mortal_sobrenatural_modo == "")
    if isVamp then
        local fx = V20.BackgroundsEngine.deriveSheetEffects(sheet.geracao_base or 13, bgList)
        local gen = tonumber(sheet.geracao_override) or fx.effectiveGeneration
        sheet.geracao = gen
        local stats = V20.Blood.deriveStats(gen)
        sheet.sangue_max = stats.bloodMax
        sheet.sangue_usavel_max = stats.usableBlood
        sheet.sangue_por_turno = stats.perTurn
        sheet.atributo_max_geracao = stats.traitMax
        sheet.disciplina_max_geracao = stats.discMax
    else
        local mSt = V20.Creation.applyMortalSupernaturalMode(sheet, sheet.mortal_sobrenatural_modo or "humano")
        sheet.sangue_max = mSt.sangue_max or 0
        sheet.sangue_por_turno = mSt.sangue_por_turno or 0
    end

    local hStatus = V20.Health.getStatus({
        isVampire = isVamp,
        hugeSize = (sheet.tem_tamanho_grande == true),
        bashing = sheet.dano_contundente,
        lethal = sheet.dano_letal,
        aggravated = sheet.dano_agravado,
    })
    sheet.vitalidade_resumo = hStatus.currentLevelName
    sheet.penalidade_ferimento = hStatus.penalty
    sheet.vitalidade_alerta = hStatus.torporOrDeath or ""

    local aura = V20.WillpowerMorality.getAuraModifier(sheet.moralidade_val or 7)
    sheet.aura_resumo = aura.label
end

function Bridge.rollFromSheet(sheet, opts, firecastApi, dialogsApi)
    opts = opts or {}
    local fc = firecastApi or _G.Firecast
    local dlg = dialogsApi or _G.Dialogs or { showMessage = _G.showMessage or function() end }
    Bridge.syncDerivedFields(sheet)

    local attrId = opts.attrId or sheet.roll_attr_id or "attr_percepcao"
    local habId = opts.habId or sheet.roll_hab_id
    local attrMeta = V20.Traits.ATTRIBUTES[attrId]
    local habMeta = habId and V20.Traits.ABILITIES[habId] or nil

    local attrVal = tonumber(sheet[attrId]) or 1
    if attrId == "attr_forca" then attrVal = attrVal + (tonumber(sheet.buff_forca) or 0) end
    if attrId == "attr_destreza" then attrVal = attrVal + (tonumber(sheet.buff_destreza) or 0) end
    if attrId == "attr_vigor" then attrVal = attrVal + (tonumber(sheet.buff_vigor) or 0) end

    local habVal = habId and (tonumber(sheet[habId]) or 0) or 0
    local spendWP = (opts.spendWillpower ~= nil) and opts.spendWillpower or (sheet.roll_gastar_fdv == true)

    if spendWP then
        if (tonumber(sheet.fdv_temp) or 0) < 1 then
            dlg.showMessage("Força de Vontade temporária insuficiente para sucesso automático.")
            return
        end
        sheet.fdv_temp = (tonumber(sheet.fdv_temp) or 1) - 1
    end

    local poolInfo = V20.Dice.buildPool({
        actorName = sheet.nome,
        attrVal = attrVal,
        abilityVal = habVal,
        abilityCategory = habMeta and habMeta.category or nil,
        bonusDice = (tonumber(opts.bonusDice) or tonumber(sheet.roll_bonus_dice) or 0),
        difficulty = tonumber(opts.difficulty) or tonumber(sheet.roll_diff) or 6,
        difficultyMod = tonumber(opts.difficultyMod) or 0,
        woundPenalty = sheet.penalidade_ferimento or 0,
        ignoreWoundPenalty = (opts.ignoreWoundPenalty == true) or (sheet.roll_ignorar_ferimento == true) or (sheet.em_frenesi == true),
        spendWillpower = spendWP,
        autoSuccesses = tonumber(opts.autoSuccesses) or 0,
        storytellerOverride = (sheet.narrador_override == true) and Bridge.isStoryteller(sheet, fc),
    })

    if not poolInfo.canRoll then
        dlg.showMessage(poolInfo.blockReason or "Rolagem bloqueada pelas regras V20.")
        return
    end

    local label = opts.label or ((attrMeta and attrMeta.name or attrId) .. (habMeta and (" + " .. habMeta.name) or ""))
    local expr = tostring(math.max(1, poolInfo.pool)) .. "d10"
    local rolObj = fc.interpretarRolagem(expr)
    local mesa = fc.getMesaDe and fc.getMesaDe(sheet) or nil
    local useSpec = (opts.specialty ~= nil) and opts.specialty or (sheet.roll_usar_espec == true)

    if mesa ~= nil and mesa.activeChat ~= nil then
        mesa.activeChat:rolarDados(rolObj, "🎲 [" .. (sheet.nome or "Personagem") .. "] " .. label, function(rolado)
            local faces = Bridge.extractRollFaces(rolado)
            local evalRes = V20.Dice.evaluate(faces, poolInfo.effectiveDifficulty, {
                specialty = useSpec,
                spendWillpower = spendWP,
                autoSuccesses = tonumber(opts.autoSuccesses) or 0,
            })
            mesa.activeChat:enviarMensagem(Bridge.formatChatReport(sheet.nome, label, evalRes, faces, poolInfo.warnings))
        end)
    else
        if rolObj.rolarLocalmente then rolObj:rolarLocalmente() end
        local faces = Bridge.extractRollFaces(rolObj)
        local evalRes = V20.Dice.evaluate(faces, poolInfo.effectiveDifficulty, {
            specialty = useSpec,
            spendWillpower = spendWP,
            autoSuccesses = tonumber(opts.autoSuccesses) or 0,
        })
        dlg.showMessage(Bridge.formatChatReport(sheet.nome, label, evalRes, faces, poolInfo.warnings))
    end
end

_G.V20Bridge = Bridge
return Bridge
```

Criar `Templates/theme_gothic.py`, `Templates/generate_vampire_lfm.py` e `Templates/generate_mortal_lfm.py`:
- `Templates/theme_gothic.py`: define tokens visuais (`BG_MAIN="#0D0D11"`, `BG_PANEL="#16161E"`, `TEXT_MAIN="#ECE8E1"`, `TEXT_MUTED="#9E9890"`) e funções construtoras XML (`header_bar_xml`, `dice_roller_footer_xml`, `trait_row_xml`, `health_track_xml`, `root_datalinks_xml`) garantindo `horzTextAlign` apenas em `("leading", "center", "trailing")` e `<dataLink>` apenas na raiz `<form>`:
```python
# Trecho central de Templates/theme_gothic.py
VALID_ALIGNS = {"leading", "center", "trailing"}

def make_root_datalink(fields: list[str], defaults: list[str], on_change_lua: str = "") -> str:
    f_lua = "{" + ", ".join(f"'{f}'" for f in fields) + "}"
    d_lua = "{" + ", ".join(f"'{d}'" for d in defaults) + "}"
    ev = f'<event name="onChange">{on_change_lua}</event>' if on_change_lua else ""
    return f'    <dataLink fields="{f_lua}" defaultValues="{d_lua}">{ev}</dataLink>'
```
- `Templates/generate_vampire_lfm.py`: recebe `--clan brujah`, lê a cor `#9E1B24` e as 3 disciplinas iniciais (`celerity`, `potence`, `presence`), monta as 7 abas completas V20 (com botões de ativação de todas as 17 disciplinas, todos os antecedentes, *Blood Buff*, Vitalidade, Fraqueza Brujah e loja/auditoria de XP) e grava `Sheets/frmBrujah.lfm`.
- `Templates/generate_mortal_lfm.py`: gera `Sheets/frmMortal.lfm` com o perfil humano independente (`6/4/3` ou `7/5/3`), Ocupação/Equipamentos, regras mortais de Vitalidade e painel condicional `Humano Puro | Carniçal | Numina`.

- [ ] **Step 4: Rodar o teste e confirmar aprovação**

Executar: `python Tests/run_tests.py Tests/test_08_bridge_and_lfm_gen.py`  
Resultado esperado: `[PASS] Tests\test_08_bridge_and_lfm_gen.py`.

- [ ] **Step 5: Commit**

```bash
git add Adapter/firecast_bridge.lua Templates/ Sheets/frmBrujah.lfm Sheets/frmMortal.lfm Tests/test_08_bridge_and_lfm_gen.py
git commit -m "feat(ui): add Firecast SDK3 bridge and parameterized Brujah and Mortal LFM sheets"
```

---

### Task 9: Manifesto `module.xml`, Loader VHD, Compilador Multi-DataType SDK 3.7b e Empacotamento `Vampiro_V20_Suite.rpk`

**Files:**
- Create: `module.xml`
- Create: `v20_loader.lua`
- Create: `tools/build_v20_suite.py`
- Create (generated): `dist/Vampiro_V20_Suite.rpk`, `dist/Vampiro_V20_Suite.rdk`
- Test: `Tests/test_09_rpk_package.py`

**Interfaces:**
- Consumes: `Data/*.lua`, `Core/*.lua`, `Adapter/*.lua`, `Sheets/*.lfm`, `c:\Users\Cliente\OneDrive\Documentos\event\firecast_event_ficha\sdk\*`, `c:\Users\Cliente\OneDrive\Documentos\event\firecast_event_ficha\output\rdkObjs\_rdkCompiledLang.cln`, `C:\Users\Cliente\AppData\Local\Firecast\lua54x64.dll`
- Produces:
  - `dist/Vampiro_V20_Suite.rpk` e `dist/Vampiro_V20_Suite.rdk` prontos para instalação direta no RRPG Firecast

- [ ] **Step 1: Escrever o teste falho `Tests/test_09_rpk_package.py`**

```python
#!/usr/bin/env python3
"""Auditoria E2E do pacote compilado dist/Vampiro_V20_Suite.rpk segundo o protocolo SDK 3.7b."""
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RPK_PATH = os.path.join(ROOT, "dist", "Vampiro_V20_Suite.rpk")


def main() -> None:
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_v20_suite.py")], check=True)
    assert os.path.exists(RPK_PATH), "Vampiro_V20_Suite.rpk não foi gerado em dist/"

    with zipfile.ZipFile(RPK_PATH, "r") as zf:
        names = set(zf.namelist())
        assert "module.xml" in names
        assert "_rdkCompiledLang.cln" in names, "_rdkCompiledLang.cln obrigatório na raiz do ZIP"
        assert "sdk/firecast.lua" in names and "sdk/rrpgGUI.lua" in names, "sdk/ obrigatório no ZIP"
        assert "Sheets/frmBrujah.lfm" in names and "Sheets/frmBrujah.lfm.lua" in names
        assert "Sheets/frmMortal.lfm" in names and "Sheets/frmMortal.lfm.lua" in names
        assert "Core/v20_init.lua" in names and "Adapter/firecast_bridge.lua" in names

        mod_xml = zf.read("module.xml").decode("utf-8")
        mod_root = ET.fromstring(mod_xml)
        assert mod_root.attrib.get("sdkVersion") == "3.7b"
        assert mod_root.attrib.get("sdkApiVersion") == "88"

        dt_ids = [el.text.strip() for el in mod_root.findall("./dataTypes/dataType")]
        assembled_ids = [el.attrib.get("id") for el in mod_root.findall("./assembledFeatures/dataTypes/dataType")]
        assert dt_ids == ["br.com.v20.Brujah", "br.com.v20.Mortal"]
        assert assembled_ids == ["br.com.v20.Brujah", "br.com.v20.Mortal"]

        for compiled_lfm in ("Sheets/frmBrujah.lfm.lua", "Sheets/frmMortal.lfm.lua"):
            code = zf.read(compiled_lfm).decode("utf-8")
            assert 'rawset(obj, "_oldSetNodeObjectFunction", obj.setNodeObject);' in code
            assert 'rawget(obj, "setNodeObject")' not in code
            assert 'cacheMode = "none"' in code


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Rodar o teste para confirmar falha**

Executar: `python Tests/run_tests.py Tests/test_09_rpk_package.py`  
Resultado esperado: `FAIL` (`tools/build_v20_suite.py` não existe).

- [ ] **Step 3: Implementar `module.xml` e `tools/build_v20_suite.py`**

Criar `module.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<module sdkVersion="3.7b">
    <id>br.com.v20.suite</id>
    <version>0.2.0</version>
    <info lang="pt-BR">
        <name>Vampiro: A Máscara V20 — Suíte Oficial Automatizada</name>
        <description>Ecossistema automatizado para Vampiro: A Máscara Edição de 20º Aniversário (V20): Motor Universal das 17 Disciplinas (de clã e fora do clã), Antecedentes interativos, Gerações 4ª-15ª, Vitalidade, Criação validada, XP auditado, Ficha Brujah e Ficha Mortal (com evolução Carniçal/Numina).</description>
        <author>Carlos Leandro</author>
        <site>https://firecast.app</site>
        <contact>Mestre Carlos</contact>
    </info>
</module>
```

Criar `v20_loader.lua` (shim de compatibilidade VHD Firecast + Lua padrão na raiz do `.rpk`) e `tools/build_v20_suite.py`:
```lua
-- v20_loader.lua (executado automaticamente no boot do plugin e requerido pelos .lfm.lua)
if not _G.__v20_loader_ready then
    _G.__v20_loader_ready = true
    local okVhd, vhdMod = pcall(require, "vhd.lua")
    if okVhd and vhdMod and vhdMod.addSearchPath then
        pcall(vhdMod.addSearchPath, "/Data")
        pcall(vhdMod.addSearchPath, "/Core")
        pcall(vhdMod.addSearchPath, "/Adapter")
    end
    local origRequire = require
    _G.require = function(modName)
        local ok, res = pcall(origRequire, modName)
        if ok then return res end
        if type(modName) == "string" and not modName:match("%.lua$") and not modName:match("%.dlua$") then
            local slashPath = "/" .. modName:gsub("%.", "/") .. ".lua"
            local ok2, res2 = pcall(origRequire, slashPath)
            if ok2 then return res2 end
            local relPath = modName:gsub("%.", "/") .. ".lua"
            local ok3, res3 = pcall(origRequire, relPath)
            if ok3 then return res3 end
        end
        error(res)
    end
end
require("Core.v20_init")
require("Adapter.firecast_bridge")
```

```python
#!/usr/bin/env python3
"""tools/build_v20_suite.py — Compilador Multi-DataType e Empacotador SDK 3.7b para Vampiro_V20_Suite.rpk."""
import datetime
import glob
import hashlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SKILL_COMPILER = r"C:\Users\Cliente\.gemini\config\skills\firecast-ficha\scripts\compile_firecast_rpk.py"
REF_SDK_DIR = r"c:\Users\Cliente\OneDrive\Documentos\event\firecast_event_ficha\sdk"
REF_CLN = r"c:\Users\Cliente\OneDrive\Documentos\event\firecast_event_ficha\output\rdkObjs\_rdkCompiledLang.cln"


def load_base_compiler():
    spec = importlib.util.spec_from_file_location("compile_firecast_rpk", SKILL_COMPILER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_multi_assembled_xml(mod_path: str, lfm_entries: list[str], rpk_filename: str) -> str:
    mod_root = ET.parse(mod_path).getroot()
    mod_id = mod_root.findtext("id").strip()
    version = mod_root.findtext("version").strip()
    info = mod_root.find("info")
    name = info.findtext("name").strip()
    desc = info.findtext("description").strip()
    author = info.findtext("author").strip()
    site = info.findtext("site").strip()
    contact = info.findtext("contact").strip()

    dt_lines, asm_lines = [], []
    for rel in lfm_entries:
        r = ET.parse(os.path.join(ROOT, rel)).getroot()
        f_name = r.attrib["name"]
        f_type = r.attrib.get("formType", "sheetTemplate")
        d_type = r.attrib["dataType"]
        f_title = r.attrib["title"]
        dt_lines.append(f'        <dataType title="{f_title}" name="{f_name}" lfmFile="{rel}">{d_type}</dataType>')
        asm_lines.append(
            f'            <dataType id="{d_type}" formType="{f_type}" lfmFile="{rel}" formName="{f_name}">\n'
            f'                <info title="{f_title}"/>\n'
            f'            </dataType>'
        )

    now_str = datetime.datetime.now().strftime("%d%m%Y%H%M%S")
    digest = hashlib.sha1(f"{mod_id}:{version}:{now_str}".encode("utf-8")).hexdigest()
    uid = hashlib.md5(f"{mod_id}:{now_str}".encode("utf-8")).hexdigest()[:24]

    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<module sdkVersion="3.7b" originalPluginFileName="{rpk_filename}" compilationDate="{now_str}" '
        f'sdkApiVersion="88" sdkMinorApiVersion="2" compilationDigest="{digest}" compilationUniqueID="{uid}">\n'
        f'    <id>{mod_id}</id>\n'
        f'    <version>{version}</version>\n'
        f'    <info lang="pt-BR">\n'
        f'        <name>{name}</name>\n'
        f'        <description>{desc}</description>\n'
        f'        <author>{author}</author>\n'
        f'        <site>{site}</site>\n'
        f'        <contact>{contact}</contact>\n'
        f'    </info>\n'
        f'    <dataTypes>\n' + "\n".join(dt_lines) + "\n    </dataTypes>\n"
        f'    <assembledFeatures>\n        <dataTypes>\n' + "\n".join(asm_lines) + "\n        </dataTypes>\n    </assembledFeatures>\n"
        f'    <name>{name}</name>\n'
        f'    <description>{desc}</description>\n'
        f'    <author>{author}</author>\n'
        f'    <site>{site}</site>\n'
        f'    <contact>{contact}</contact>\n'
        f'</module>\n'
    )


def main() -> None:
    compiler = load_base_compiler()
    subprocess.run([sys.executable, os.path.join(ROOT, "Templates", "generate_vampire_lfm.py"), "--clan", "brujah"], check=True)
    subprocess.run([sys.executable, os.path.join(ROOT, "Templates", "generate_mortal_lfm.py")], check=True)

    with open(os.path.join(REF_SDK_DIR, "rrpgGUI.lua"), "r", encoding="utf-8", errors="ignore") as f:
        gui_sdk = f.read()

    for lua_src in sorted(
        glob.glob(os.path.join(ROOT, "Data", "*.lua"))
        + glob.glob(os.path.join(ROOT, "Core", "*.lua"))
        + glob.glob(os.path.join(ROOT, "Adapter", "*.lua"))
        + [os.path.join(ROOT, "v20_loader.lua")]
    ):
        with open(lua_src, "r", encoding="utf-8") as f:
            compiler.validate_lua_syntax(f.read(), "@" + os.path.relpath(lua_src, ROOT))

    lfm_entries = ["Sheets/frmBrujah.lfm", "Sheets/frmMortal.lfm"]
    compiled_map = {}
    for rel in lfm_entries:
        raw_lua = compiler.compile_lfm_to_lua(os.path.join(ROOT, rel))
        injected = raw_lua.replace(
            'local __o_Utils = require("utils.lua");',
            'local __o_Utils = require("utils.lua");\nrequire("v20_loader.lua");',
            1,
        )
        compiler.validate_lua_syntax(injected, f"@{rel}.lua")
        methods = set(re.findall(r":(set[A-Za-z0-9_]+)\(", injected))
        missing = [m for m in sorted(methods) if m not in ("setNodeObject", "setNodeDatabase", "setName") and m not in gui_sdk]
        if missing:
            raise RuntimeError(f"Métodos inválidos em {rel}: {missing}")
        compiled_map[rel] = injected

    dist_dir = os.path.join(ROOT, "dist")
    os.makedirs(dist_dir, exist_ok=True)
    out_rpk = os.path.join(dist_dir, "Vampiro_V20_Suite.rpk")
    assembled_xml = build_multi_assembled_xml(os.path.join(ROOT, "module.xml"), lfm_entries, "Vampiro_V20_Suite.rpk")

    with zipfile.ZipFile(out_rpk, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("module.xml", assembled_xml)
        zf.write(REF_CLN, "_rdkCompiledLang.cln")
        zf.write(os.path.join(ROOT, "v20_loader.lua"), "v20_loader.lua")
        for folder in ("Data", "Core", "Adapter"):
            for p in sorted(glob.glob(os.path.join(ROOT, folder, "*.lua"))):
                zf.write(p, f"{folder}/{os.path.basename(p)}")
        for rel, lua_txt in compiled_map.items():
            zf.write(os.path.join(ROOT, rel), rel)
            zf.writestr(rel + ".lua", lua_txt)
        for item in sorted(os.listdir(REF_SDK_DIR)):
            s = os.path.join(REF_SDK_DIR, item)
            if os.path.isfile(s):
                zf.write(s, f"sdk/{item}")

    shutil.copy2(out_rpk, os.path.join(dist_dir, "Vampiro_V20_Suite.rdk"))
    print(f"[OK] Gerado {out_rpk}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Executar toda a suíte de testes (`test_01` a `test_09`)**

Executar: `python Tests/run_tests.py`  
Resultado esperado: Todos os 9 arquivos de teste reportando `[PASS]` e `dist/Vampiro_V20_Suite.rpk` gerado com zero erros.

- [ ] **Step 5: Commit**

```bash
git add module.xml v20_loader.lua tools/build_v20_suite.py Tests/test_09_rpk_package.py dist/Vampiro_V20_Suite.rpk dist/Vampiro_V20_Suite.rdk
git commit -m "build(rpk): add multi-dataType SDK 3.7b packager and build Vampiro_V20_Suite v0.2.0"
```
