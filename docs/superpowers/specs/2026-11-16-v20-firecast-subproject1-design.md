# Vampiro: A Máscara V20 (RRPG Firecast SDK 3.7b) — Especificação Técnica do Subprojeto 1

**Data:** 2026-11-16  
**Versão Alvo do Pacote:** `0.2.0` (`Vampiro_V20_Suite.rpk`)  
**Plataforma:** RRPG Firecast SDK 3.7b (`sdkApiVersion="88"`, `sdkMinorApiVersion="2"`, Lua 5.4)  
**Referência Mecânica Exclusiva:** *Vampire: The Masquerade — 20th Anniversary Edition (V20 Corebook)*  
**Idioma da Interface:** Português Brasileiro (`pt-BR`)

---

## 1. Visão Geral e Escopo no Roteiro Geral

O ecossistema **Vampiro V20 Suite** entrega fichas separadas por clã (13 clãs clássicos + Caitiff) e uma ficha independente para Mortais dentro de **um único pacote instalável `Vampiro_V20_Suite.rpk`** (multi-`dataType`), permitindo que a mesa instale e atualize um único arquivo enquanto cada jogador seleciona o modelo específico de seu clã ou mortal na criação de personagem do Firecast.

O ecossistema divide-se em 3 entregas incrementais:
1. **Subprojeto 1 (`v0.2.0` — Objeto desta Especificação):**
   * Motor Universal V20 completo em Lua 5.4 (`Core/` + `Data/` + `Adapter/`), 100% independente de clã;
   * Automação individual de **todas as 17 Disciplinas Clássicas da V20** (Níveis 1 a 5, tanto de clã quanto fora do clã, incluindo suporte inicial à *Linha do Sangue* de Taumaturgia, *Linha do Sepulcro* de Necromancia e poderes customizados);
   * Automação mecânica de **todos os Antecedentes V20**, **Qualidades e Defeitos com modificadores**, **Sangue/Geração (4ª–15ª)**, **Vitalidade**, **Força de Vontade**, **Moralidade (Humanidade & Trilhas)**, **Criação Validada**, **Evolução por XP Auditada** e **Rotinas de 1 Clique** (Despertar, Caça, Cura, Frenesi, Rötschreck, Absorção, Degeneração);
   * Compilação e entrega operacional dos primeiros dois modelos de ficha: **`Vampiro V20 - Brujah` (`br.com.v20.Brujah`)** (com fraqueza Brujah automatizada) e **`Vampiro V20 - Mortal` (`br.com.v20.Mortal`)** (100% humana por padrão, com chave do Narrador para transição em jogo para **Carniçal / Numina**).
2. **Subprojeto 2 (`v0.6.0`):** Expansão completa de Linhas Secundárias e Grimório de Rituais (Taumaturgia e Necromancia), automação das fraquezas específicas dos outros 12 clãs + Caitiff e compilação das 15 fichas completas no `.rpk`.
3. **Subprojeto 3 (`v1.0.0`):** Sistema avançado de manobras de combate assistido (ações múltiplas com divisão pela menor parada, agarrar, rajada, defesas ativas) e Escudo Acoplável do Narrador (`tablesDock`) para monitoramento da Coterie em tempo real.

---

## 2. Arquitetura de Empacotamento e Estrutura de Diretórios

### 2.1. Solução Multi-DataType em Pacote Único
No SDK 3.7b do Firecast, `.rpk`s distintos executam em *sandboxes* VHD isoladas sem acesso síncrono via `require()`. Para garantir compartilhamento nativo do motor Lua sem duplicar código nem exigir 15 instalações manuais, `Vampiro_V20_Suite.rpk` registra múltiplos `<dataType>` em seu `module.xml` assemblado:
* Subprojeto 1 registra:
  * `br.com.v20.Brujah` → `Sheets/frmBrujah.lfm` (*"Vampiro V20 - Brujah"*)
  * `br.com.v20.Mortal` → `Sheets/frmMortal.lfm` (*"Vampiro V20 - Mortal"*)
* Subprojeto 2 acrescentará no mesmo `module.xml` os outros 13 identificadores (`br.com.v20.Gangrel`, `br.com.v20.Malkavian`, `br.com.v20.Nosferatu`, `br.com.v20.Toreador`, `br.com.v20.Tremere`, `br.com.v20.Ventrue`, `br.com.v20.Assamite`, `br.com.v20.Setite`, `br.com.v20.Giovanni`, `br.com.v20.Lasombra`, `br.com.v20.Ravnos`, `br.com.v20.Tzimisce`, `br.com.v20.Caitiff`).

### 2.2. Árvore do Repositório
```text
vampire/
├── module.xml                        # Manifesto fonte base do projeto
├── Data/
│   ├── attributes_abilities.lua      # 9 Atributos e 30 Habilidades V20 + regras de teste com 0 pontos
│   ├── generations.lua               # Parâmetros oficiais da 4ª à 15ª Geração (Sangue Fraco incluso)
│   ├── clans.lua                     # Metadados dos 13 Clãs + Caitiff (disciplinas, fraqueza, tema visual)
│   ├── disciplines_catalog.lua       # As 17 Disciplinas Clássicas V20 (Níveis 1-5: custos, paradas, dif, buffs)
│   ├── backgrounds_catalog.lua       # Antecedentes V20 com tabelas derivadas e ações automatizadas
│   ├── merits_flaws_catalog.lua      # Qualidades, Defeitos e Numina base com descritores de modificador
│   └── morality_virtues.lua          # Humanidade, Trilhas da Sabedoria, Virtudes, Aura e gatilhos Frenesi/Rötschreck
├── Core/
│   ├── v20_init.lua                  # Registro idempotente do namespace global V20 e carregamento dos módulos
│   ├── dice.lua                      # Avaliador puro de paradas d10 V20 + cálculo de paradas efetivas
│   ├── generation_blood.lua          # Reserva de sangue, gasto/turno, Sangue Fraco (14ª/15ª) e Blood Buff físico
│   ├── health.lua                    # 7 níveis de vitalidade, ordenação (/ X *), upgrade de contundente e penalidades
│   ├── willpower_morality.lua        # Força de Vontade, cálculo de Moralidade/Aura, Frenesi, Rötschreck e Degeneração
│   ├── disciplines_engine.lua        # Validação, ativação de poderes (in-clan/out-of-clan) e aplicação de buffs ativos
│   ├── backgrounds_engine.lua        # Efeitos derivados de Antecedentes (Geração, Rebanho/Caça, Recursos, Fama, Status, Rede)
│   ├── creation.lua                  # Validador de criação Vampiro (7/5/3), Mortal (6/4/3 ou 7/5/3) e Pontos de Bônus (+Defeitos)
│   └── experience.lua                # Calculadora de custos XP V20, fila de aprovação do Narrador e histórico
├── Adapter/
│   └── firecast_bridge.lua           # Integração SDK 3.7b: chat anti-cheat (rolado.ops), detecção isMestre e Log NDB
├── Templates/
│   ├── theme_gothic.py               # Tokens visuais góticos (cores, tipografia, geradores XML de bolinhas e cards)
│   ├── generate_vampire_lfm.py       # Gerador parametrizado de .lfm vampírico por clã (gera Sheets/frmBrujah.lfm)
│   └── generate_mortal_lfm.py        # Gerador de Sheets/frmMortal.lfm (humano puro + painel oculto Carniçal/Numina)
├── Sheets/                           # Artefatos .lfm gerados (versionados para inspeção direta)
│   ├── frmBrujah.lfm
│   └── frmMortal.lfm
├── tools/
│   └── build_v20_suite.py            # Gera LFMs, compila .lfm.lua (regras SDK 3.7b), valida em lua54x64.dll e empacota .rpk
└── Tests/
    ├── run_tests.py                  # Executor Python carregando lua54x64.dll via ctypes para rodar suíte Lua 5.4
    └── suite_v20.lua                 # Testes unitários e de integração cobrindo todo Data/ e Core/
```

---

## 3. Especificação Mecânica Exata (Motor `Core/` & `Data/`)

### 3.1. Sistema de Dados e Paradas (`Core/dice.lua`)
1. **Cálculo da Parada Efetiva:**
   $$\text{Parada} = \text{Atributo Efetivo} + \text{Habilidade/Antecedente} + \text{Modificadores de Buffs/Qualidades} + \text{Dados Extras} - \text{Penalidade de Ferimento}$$
   * **Atributo Efetivo (Físicos):** `Atributo Permanente + Buff de Sangue + Buff de Disciplina/Forma` (ex.: *Forma Horripilante* `+3`). Para *Potência* passiva em testes de Força e *Rapidez* passiva em testes de Destreza, soma-se o nível da disciplina quando não convertida em sucessos/ações ativas no turno.
   * **Regra V20 de Habilidade `0` (Sem Pontos):**
     * *Talento = 0:* penalidade de dificuldade `+0`;
     * *Perícia = 0:* aumenta a dificuldade em **`+1`** automaticamente (com aviso no resumo da rolagem);
     * *Conhecimento = 0:* bloqueia a rolagem por padrão (exibindo aviso *"Conhecimentos sem pontos não podem ser testados na V20"*), salvo se a flag *Exceção do Narrador / Teste Puro de Atributo* estiver marcada.
   * **Penalidade de Ferimento:** Aplicada automaticamente conforme o nível atual de Vitalidade (`0`, `-1`, `-2`, `-5`; `Incapacitado` bloqueia ações físicas), **exceto** quando `ignoreWoundPenalty == true` (automático em rolagens de Absorção, Força de Vontade, Virtudes, Humanidade/Trilha, Despertar, ou quando o personagem estiver em *Frenesi* / gastou *1 FdV para ignorar dor*). Se a parada resultante após ferimentos for `<= 0` e não houver sucesso automático, a ação não pode ser rolada.
2. **Avaliação dos Dados (`Dice.evaluate` — Regra Oficial V20, p. 247–249):**
   * Dificuldade clampada no intervalo `[2, 10]` (padrão `6`).
   * Para cada dado `v` em `results` (`1..10`):
     * Se `v == 1`: `ones = ones + 1`.
     * Se `v >= difficulty`:
       * Se `v == 10` e `hasSpecialty == true`: `rawSuccesses = rawSuccesses + 2` (10 conta como 2 sucessos; não explode).
       * Caso contrário: `rawSuccesses = rawSuccesses + 1`.
   * Sucessos rolados líquidos: `rolledNet = math.max(0, rawSuccesses - ones)`.
   * Sucessos automáticos (`autoSuccesses`: `+1` por gasto de FdV na rolagem + `N` de *Potência Ativa* em testes de Força): **não são cancelados por resultados `1`**.
   * Total final: `totalSuccesses = rolledNet + autoSuccesses`.
   * Classificação do resultado:
     * **`botch` (Falha Crítica):** estritamente quando `rawSuccesses == 0 and autoSuccesses == 0 and ones > 0`;
     * **`failure` (Falha Simples):** quando `totalSuccesses == 0` e não é `botch` (inclui o caso em que `rawSuccesses > 0`, mas `ones >= rawSuccesses`);
     * **`success` (Sucesso):** `totalSuccesses >= 1` (graus descritivos V20: 1 Marginal, 2 Moderado, 3 Completo, 4 Excepcional, 5+ Fenomenal).

### 3.2. Geração, Reserva de Sangue e *Blood Buff* (`Core/generation_blood.lua`)
Tabela integral da **4ª à 15ª Geração** (*V20 Corebook*, p. 270 e p. 487):

| Geração | Atributo Máx. | Disciplina Máx. | Reserva Máx. | Sangue Utilizável | Gasto Máx./Turno | Observação Mecânica |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| 4ª | 9 | 9 | 50 | 50 | 10 | Matusalém |
| 5ª | 8 | 8 | 40 | 40 | 8 | Matusalém / Ancião |
| 6ª | 7 | 7 | 30 | 30 | 6 | Ancião |
| 7ª | 6 | 6 | 20 | 20 | 4 | Ancião / Ancilla |
| 8ª | 5 | 5 | 15 | 15 | 3 | Limite de criação padrão (5 pts Antecedente Geração) |
| 9ª | 5 | 5 | 14 | 14 | 2 | 4 pts Antecedente Geração |
| 10ª | 5 | 5 | 13 | 13 | 1 | 3 pts Antecedente Geração |
| 11ª | 5 | 5 | 12 | 12 | 1 | 2 pts Antecedente Geração |
| 12ª | 5 | 5 | 11 | 11 | 1 | 1 pt Antecedente Geração |
| 13ª | 5 | 5 | 10 | 10 | 1 | Geração base padrão de Neófito (0 pts Antecedente) |
| 14ª | 5 | 4 | 10 | 8 | 1 | *Sangue Fraco*: apenas 8 pts usáveis p/ Disciplinas/cura/buff |
| 15ª | 5 | 3 | 10 | 6 | 1 | *Sangue Fraco*: 6 pts usáveis; custo dobrado p/ Disciplinas e cura |

* **Controle de Gasto no Turno (`sangue_gasto_turno`):** Rastreador por turno com botão `[Novo Turno (Zerar Gasto)]`. Qualquer gasto de sangue (cura, *Blood Buff*, poder de disciplina) soma no acumulador do turno e bloqueia se exceder `gasto_max_turno` — **exceto** na ativação de ações extras de *Rapidez*, que a V20 (p. 142) explicitamente autoriza ignorar o limite de sangue por turno.
* ***Blood Buff* Físico:** Gastar 1 ponto de sangue (2 na 15ª Geração) eleva Força, Destreza ou Vigor em `+1` até `Atributo Máx. da Geração + 1` (exibindo alerta visual quando estiver no `+1` acima do teto, que dura 3 turnos). Botão `[Encerrar Cena (Limpar Buffs)]` zera os buffs temporários.

### 3.3. Vitalidade, Absorção e Cura (`Core/health.lua`)
* **7 Níveis Oficiais:** `Escoriado (0)`, `Machucado (-1)`, `Ferido (-1)`, `Ferido Gravemente (-2)`, `Espancado (-2)`, `Aleijado (-5)`, `Incapacitado (Imóvel)`. Caso a Qualidade *Tamanho Grande* esteja ativa, adiciona-se um 8º nível `Escoriado Extra (0)` no topo.
* **Representação e Empilhamento Oficial:** Armazenado como contadores `dano_contundente`, `dano_letal` e `dano_agravado`. A renderização na trilha ordena sempre **Agravado (`*`) no topo → Letal (`X`) → Contundente (`/`)**.
* **Regras de Transbordo (Upgrade):**
  * Se `contundente + letal + agravado > totalNiveis` ao sofrer novo dano **Contundente**, cada ponto excedente converte 1 Contundente existente em 1 Letal.
  * Para **Vampiros**, quando todos os 7 níveis ficam preenchidos por Letal/Agravado e entra mais dano, a ficha exibe alerta de **Torpor / Morte Final** (se tudo Agravado). Para **Mortais**, preencher `Incapacitado` com Letal/Agravado sinaliza **Morte / Agonia Crítica**.
* **Diferenças Vampiro vs. Mortal:**
  * **Vampiro:** Botão de *Aplicar Dano* possui opção `Arma de Fogo (Normal)` que converte automaticamente para Contundente (salvo *Tiro na Cabeça = Letal*), e opção `Dividir Contundente pós-absorção por 2 (arredondado p/ baixo, mín. 0/1 conforme regra)`. Cura: `-1 Sangue` (2 na 15ª Geração) remove 1 Contundente ou 1 Letal; `-5 Sangue + 1 FdV` (repouso diurno) remove 1 Agravado. Absorção: `Vigor + Fortitude + Armadura` para Contundente e Letal; `Fortitude + Armadura aplicável` para Agravado.
  * **Mortal:** `Arma de Fogo` aplica Letal. Absorção Letal exige `Armadura > 0` (ou Carniçal com *Fortitude*).

### 3.4. Motor Universal de Disciplinas e Poderes (`Data/disciplines_catalog.lua` + `Core/disciplines_engine.lua`)
Todas as **17 Disciplinas Clássicas da V20** possuem catálogo estruturado de Nível 1 a Nível 5 disponível para **qualquer ficha vampírica** (e Nível 1 para Carniçais, ou superior se geração do domitor permitir):
1. `animalism` (Animalismo)
2. `auspex` (Auspícios)
3. `celerity` (Rapidez)
4. `chimerstry` (Quimerismo)
5. `dementation` (Demência)
6. `dominate` (Dominação)
7. `fortitude` (Fortitude)
8. `necromancy` (Necromancia — inclui *Linha do Sepulcro* 1–5 no Subprojeto 1 + slot para Linhas/Rituais extras)
9. `obfuscate` (Ofuscação)
10. `obtenebration` (Tenebrosidade)
11. `potence` (Potência)
12. `presence` (Presença)
13. `protean` (Metamorfose)
14. `quietus` (Quietus)
15. `serpentis` (Serpentis)
16. `thaumaturgy` (Taumaturgia — inclui *Linha do Sangue* 1–5 no Subprojeto 1 + slot para Linhas/Rituais extras)
17. `vicissitude` (Vicissitude)

**Estrutura de cada Poder no Catálogo (e em Poderes Customizados / Anciões 6+):**
```lua
{
  id = "presence_1",
  level = 1,
  name = "Fascínio",
  cost = { blood = 0, willpower = 0 },
  pool = { attr = "attr_carisma", hab = "hab_performance" },
  defaultDiff = 7,
  diffHint = "Dif 7 (afeta espectadores conforme sucessos)",
  toggleEffect = nil, -- ou { id = "buff_garras", label = "Garras da Besta (For+1 Agravado)", mods = {...} }
  summary = "Atrai a atenção e simpatia dos presentes na cena (V20, p. 193)."
}
```
* **Classificação de Custo por Personagem:** Cada entrada em `rclDisciplinas` guarda `disc_id`, `nivel` e `categoria_custo` (`"cla"` → XP `×5`; `"fora_cla"` → XP `×7`; `"caitiff"` → XP `×6`; `"linha_secundaria"` → XP `×4` / nova `7`).
* **Execução de Poder (`[Ativar / Rolar]`):**
  1. Checa `nivel >= power.level`;
  2. Desconta `cost.blood` (aplicando multiplicador de 15ª Geração e limite de turno) e `cost.willpower`;
  3. Se possuir `toggleEffect`, liga/desliga o modificador ativo na cena (atualizando atributos efetivos, dificuldade de percepção, absorção ou armas naturais);
  4. Se possuir `pool`, carrega ou executa imediatamente a rolagem no chat da mesa com cabeçalho temático da Disciplina e Poder.

### 3.5. Motor de Antecedentes (`Data/backgrounds_catalog.lua` + `Core/backgrounds_engine.lua`)
Cada antecedente adicionado ou pré-listado oferece cálculo derivado e botão de ação mecânica:
* **`generation` (Geração):** Define `geracao = geracao_base_cronica - pontos` (padrão `13 - pontos`), atualizando todos os limites vampíricos instantaneamente.
* **`herd` (Rebanho) & `domain` (Domínio):** Calculam `recipientes = {3, 7, 15, 30, 60}` e `reserva_caca_semanal`. Botão **`[Caçar / Alimentar-se]`** rola a parada de caça escolhida (*Percepção/Manipulação/Carisma/Destreza + Manha/Furtividade/Lábia/Intimidação/Sobrevivência*) somando **`+Rebanho` dados** e ajustando a dificuldade por **`-Domínio`** (ou transfere sangue direto da reserva segura do Rebanho).
* **`resources` (Recursos):** Exibe faixa financeira oficial V20 (0 Indigente a 5 Multimilhardário, renda mensal de referência e liquidez) na aba de Antecedentes e Equipamentos.
* **`fame` (Fama) & `status` (Status):** Disponibilizam *checkboxes* rápidos no Montador de Rolagens (`Aplicar Fama: -N dif` e `Aplicar Status: +N dados`).
* **`contacts` (Contatos), `influence` (Influência), `mentor` (Mentor), `allies` (Aliados), `retainers` (Lacaios):** Botão **`[Acionar no Chat]`** rolando `Atributo + Antecedente` (dif. configurável, padrão 6 ou 7 para Contatos secundários) + sub-lista `rclAliadosLacaios` com nome, papel, parada rápida de dados, Vitalidade e Sangue do Lacaio/Aliado.

### 3.6. Moralidade, Virtudes, Fraqueza Brujah e Carniçal/Numina
* **Virtudes Alternáveis:** Virtude 1 selecionável entre `Consciência` e `Convicção`; Virtude 2 entre `Autocontrole` e `Instinto`; Virtude 3 `Coragem`.
* **Moralidade e Modificador de Aura (V20, p. 312):** Seletor `Humanidade` ou `Trilha da Sabedoria` (com campo de nome da Trilha). Calcula automaticamente o **Modificador de Aura** nas interações sociais (`Moralidade 10: -2 dif`, `8–9: -1 dif`, `4–7: 0`, `2–3: +1 dif`, `1: +2 dif`, `0: Bestial/Perdido`).
* **Fraqueza Automatizada do Clã Brujah (`br.com.v20.Brujah`):**
  * Ao rolar **Frenesi** na ficha Brujah, o sistema soma automaticamente **`+2` na dificuldade** (máx. 10) e bloqueia o gasto de Força de Vontade para evitar o Frenesi, exibindo o lembrete mecânico oficial da V20 (p. 49: pode gastar 1 FdV apenas para encerrar um Frenesi já iniciado).
* **Modo Carniçal (Ghoul) / Numina na Ficha Mortal (`br.com.v20.Mortal`):**
  * Invisível por padrão (`sheet.mortal_sobrenatural_modo = "humano"`).
  * Quando o Narrador altera para `"carnical"` ou `"numina"`:
    * `"carnical"`: habilita Reserva de Vitae de Carniçal (`máx. 2 pts`, gasto `1/turno`), concede `Potência 1` automática, permite adicionar Disciplinas Nível 1 (ou teto liberado pelo Narrador conforme geração do domitor), permite absorver Letal com Vigor e habilita teste de Frenesi com penalidade reduzida;
    * `"numina"`: habilita compra e rolagem de **Fé Verdadeira**, **Magia de Cerca** ou **Fenômenos Psíquicos** no mesmo motor universal de poderes.

### 3.7. Criação Validada vs. Evolução por XP e Auditoria (`Core/creation.lua` + `Core/experience.lua`)
1. **Três Modos de Operação da Ficha (`sheet.modo_ficha`):**
   * **`criacao` (Padrão ao criar ficha nova):**
     * *Vampiro Neófito:* Atributos `7 / 5 / 3` (+1 base em cada atributo, exceto Nosferatu `Aparência = 0`); Habilidades `13 / 9 / 5` (teto de `3` pontos na etapa base antes dos Pontos de Bônus!); Disciplinas `3`; Antecedentes `5`; Virtudes `7` (+1 base em cada); Humanidade inicial = `Virtude1 + Virtude2`; FdV inicial = `Coragem`; Sangue inicial = botão `[Rolar 1d10 Inicial]`; Pontos de Bônus = `15 + min(7, total_defeitos)` com custos V20 (`Atributo: 5`, `Habilidade: 2`, `Disciplina: 7`, `Antecedente: 1`, `Virtude: 2`, `Moralidade: 1`, `FdV: 1`, `Qualidade: valor`).
     * *Mortal:* Seletor de perfil da crônica: **Mortal Padrão V20** (`6/4/3`, `11/7/4`, Antecedentes `5`, Virtudes `7`, Bônus `21`) ou **Mortal Heroico** (`7/5/3`, `13/9/5`, Antecedentes `5`, Virtudes `7`, Bônus `15`).
     * Botão **`[Concluir Criação → Entrar em Modo Jogo]`**: valida se não há saldo negativo nem tetos violados (permitindo *override* se `isMestre`) e trava a edição direta de pontos permanentes.
   * **`jogo` (Personagem em Crônica):**
     * Recursos temporários (Sangue, Buffs, FdV Temporária, Vitalidade, Munição, Notas) livres para o jogador.
     * Características permanentes só sobem pela aba **Experiência (XP)**:
       * Custos V20: `Novo ponto em Habilidade (0→1): 3`, `Habilidade: Atual × 2`, `Atributo: Atual × 4`, `Disciplina de Clã: Atual × 5`, `Disciplina Fora do Clã: Atual × 7`, `Disciplina Caitiff: Atual × 6`, `Nova Disciplina (0→1): 10`, `Linha Secundária Nova: 7`, `Linha Secundária Evolução: Atual × 4`, `Virtude: Atual × 2` *(não aumenta Moralidade/FdV retroativamente)*, `Moralidade: Atual × 2`, `Força de Vontade: Atual × 1`.
       * Flag configurável pelo Narrador `sheet.xp_exige_aprovacao` (padrão `true`): quando `true`, clicar em `[Solicitar Evolução]` cria um item pendente em `rclAuditoriaXP` com botões `[Aprovar]` / `[Recusar]` habilitados apenas para `isMestre`; quando `false`, aplica o ponto na hora descontando `sheet.xp_disponivel` e gravando o registro imutável em `rclAuditoriaXP`.
   * **`narrador_livre` (Destravado pelo Mestre ou Fora de Mesa):**
     * Permite ajustar diretamente qualquer característica permanente, geração, clã ou exceção de regra, registrando automaticamente cada alteração manual no `rclAuditoriaXP` com timestamp e login do autor.

---

## 4. Esquema de Dados `NodeDatabase` (`sheet`)

Todos os campos escalares ficam na raiz de `sheet` (garantindo disparo confiável de `<dataLink>` filhos diretos de `<form>`):

* **Identificação & Estado:** `nome`, `jogador`, `cronica`, `conceito`, `natureza`, `comportamento`, `senhor_regente`, `cla_id`, `geracao_base` (`13`), `geracao` (`13`), `modo_ficha` (`"criacao"`), `mortal_perfil` (`"padrao_643"`), `mortal_sobrenatural_modo` (`"humano"`), `xp_total` (`0`), `xp_gasto` (`0`), `xp_exige_aprovacao` (`true`), `narrador_override` (`false`).
* **Atributos & Especialidades:** `attr_forca`, `attr_destreza`, `attr_vigor`, `attr_carisma`, `attr_manipulacao`, `attr_aparencia`, `attr_percepcao`, `attr_inteligencia`, `attr_raciocinio` + `spec_attr_<nome>` + `buff_forca`, `buff_destreza`, `buff_vigor`.
* **Habilidades (30 campos):** `hab_prontidao` ... `hab_tecnologia` + `spec_hab_<nome>`.
* **Recursos, Vitalidade & Moralidade:** `sangue_atual`, `sangue_max`, `sangue_usavel_max`, `sangue_por_turno`, `sangue_gasto_turno`, `fdv_perm`, `fdv_temp`, `virtude1_tipo` (`"consciencia"`), `virtude1_val`, `virtude2_tipo` (`"autocontrole"`), `virtude2_val`, `virtude3_val` (Coragem), `moralidade_tipo` (`"humanidade"`), `moralidade_nome` (`"Humanidade"`), `moralidade_val`, `dano_contundente`, `dano_letal`, `dano_agravado`, `armadura_absorcao`, `armadura_penalidade`, `em_frenesi` (`false`).
* **Montador de Rolagem Persistente:** `roll_attr_id`, `roll_hab_id`, `roll_diff` (`6`), `roll_bonus_dice` (`0`), `roll_usar_espec` (`false`), `roll_gastar_fdv` (`false`), `roll_usar_fama` (`false`), `roll_usar_status` (`false`), `roll_ignorar_ferimento` (`false`).
* **Sub-nós `<recordList>`:**
  * `rclHabilidadesExtras` (`nome`, `categoria`, `valor`, `especialidade`)
  * `rclDisciplinas` (`disc_id`, `nome_custom`, `categoria_custo`, `nivel`, `ativa_turno`, `poderes_custom_json`)
  * `rclBuffsCena` (`buff_id`, `origem`, `label`, `ativo`, `mod_json`)
  * `rclAntecedentes` (`bg_id`, `nome_custom`, `nivel`, `detalhes`, `reserva_atual`)
  * `rclAliadosLacaios` (`nome`, `tipo`, `parada_dados`, `sangue_atual`, `vitalidade_dano`, `notas`)
  * `rclQualidadesDefeitos` (`item_id`, `nome`, `tipo` [`"qualidade"`/`"defeito"`], `pontos`, `mod_tipo`, `mod_valor`, `ativo`)
  * `rclArmasEquipamentos` (`nome`, `tipo_item`, `atributo`, `habilidade`, `dificuldade`, `dano_base`, `tipo_dano`, `cadencia`, `municao_atual`, `municao_max`)
  * `rclAuditoriaXP` (`data_hora`, `autor_login`, `tipo_evento`, `descricao`, `custo_xp`, `status` [`"aprovado"`/`"pendente"`/`"recusado"`], `campo_alvo`, `novo_valor`)

---

## 5. Interface Visual e Fluxo de Interação (SDK 3.7b)

### 5.1. Identidade Visual Gótica Responsiva
* Paleta escura de alto contraste: fundo `#0D0D11`, painéis `#16161E`, bordas `#3A1C24` (vampiros, com acento carmesim `#9E1B24` no Brujah) e `#24303E` (acento âmbar/aço `#C48F36` na ficha Mortal), textos `#ECE8E1` e secundários `#9E9890`.
* Seletor visual de pontos (`1..5` expansível automaticamente até `9` quando `geracao <= 7`) com botões clicáveis estilizados (`●` preenchido vs `○` vazio) que respeitam `modo_ficha` e limites de geração.

### 5.2. Cabeçalho + Barra Montadora de Rolagem Fixos (Topo/Rodapé)
Visíveis em qualquer aba da ficha:
* **Faixa Superior de Status Rápido:** Nome, Clã/Ocupação, Geração (ou Perfil Mortal), controles rápidos `Sangue [-][+] (Atual/Máx | Turno: X/Y)` (oculto no Mortal humano), `FdV Temp [-][+] (Temp/Perm)`, badge de `Vitalidade Atual (ex.: Ferido -1)` e botões de 1 clique `[Despertar]` • `[Curar]` • `[Novo Turno]`.
* **Faixa Inferior — Montador Interativo de Parada:**
  * Clicar no nome de qualquer Atributo seleciona `Atributo Ativo`; clicar no nome de qualquer Habilidade/Antecedente seleciona `Habilidade Ativa`.
  * Exibe a equação viva: ex. `Percepção (4) + Investigação (3) - Ferimento (1) = 6d10 | Dif [6] | [x] Espec. | [ ] +1 FdV | [ROLAR NO CHAT]`.

### 5.3. Organização das Abas
* **Ficha Vampírica (`frmBrujah.lfm`):**
  1. **Personagem & Criação:** Cabeçalho biográfico + Assistente de Criação V20 em tempo real (barras de saldo `7/5/3`, `13/9/5`, Disciplinas `3`, Antecedentes `5`, Virtudes `7`, Defeitos `até +7` e Bônus `15`, com botão de transição para Modo Jogo).
  2. **Atributos & Habilidades:** 3 colunas de Atributos (com *Blood Buff* `+` nos Físicos e especialidades) + 3 colunas das 30 Habilidades oficiais + lista de Habilidades Extras.
  3. **Disciplinas & Poderes:** Disciplinas de Clã pré-carregadas + botão `[+ Adicionar Disciplina Fora do Clã / Custom]` + lista automática dos Poderes Níveis `1..N` desbloqueados com botão `[Ativar / Rolar]`, resumo mecânico e painel de Buffs de Cena ativos.
  4. **Antecedentes, Lacaios & Qualidades:** Antecedentes com cálculos derivados e botões `[Caçar / Acionar no Chat]`, sub-fichas de Aliados/Lacaios e lista de Qualidades & Defeitos com modificadores.
  5. **Combate & Vitalidade:** Atalhos rápidos (`Iniciativa 1d10 + Des + Rac`, `Absorção`, `Briga`, `Esquiva`, `Armas Brancas`, `Armas de Fogo`), lista de Armas/Ataques com rolagem de ataque e parada de dano, e Caixa dos 7 Níveis de Vitalidade com aplicador assistido de dano Contundente/Letal/Agravado.
  6. **Moralidade, Virtudes & Besta:** Virtudes (`Consciência/Convicção`, `Autocontrole/Instinto`, `Coragem`), trilha de Humanidade/Sabedoria (com Aura calculada), card da **Fraqueza Brujah Automatizada** e botões de 1 clique para **Frenesi**, **Rötschreck** e **Degeneração**.
  7. **Experiência & Narrador:** Saldo de XP (`Total - Gasto = Disponível`), loja de evolução com cálculo automático V20, chave `Exigir Aprovação do Narrador`, chave `Modo Edição Livre (Narrador)` e tabela `rclAuditoriaXP`.
* **Ficha Mortal (`frmMortal.lfm`):**
  * Substitui elementos vampíricos na Aba 1 e Aba 3 por **Ocupação, Formação, Vínculos Humanos, Conhecimento Sobrenatural e Equipamentos/Finanças**, aplica regras mortais de Vitalidade/Absorção na Aba 5 e inclui na Aba 7 a chave exclusiva do Narrador **`Modo Sobrenatural: Humano Puro | Carniçal (Ghoul) | Numina`** (que revela uma aba/seção dedicada de Vitae/Disciplinas/Numina apenas quando ativada).

---

## 6. Validação Técnica, Tratamento de Erros e Plano de Testes

1. **Validação Determinística de Compilação SDK 3.7b:**
   * Todo `.lfm` compilado segue as 6 regras estritas do SDK 3.7b (`rawset(obj, "_oldSetNodeObjectFunction", obj.setNodeObject)`, `<dataLink>` na raiz de `<form>`, `cacheMode = "none"`, `TTextAlign` estrito `leading/center/trailing`, destruição reversa completa e zero quebras literais em strings Lua).
   * Validação sintática obrigatória de todos os `.lua` e `.lfm.lua` via `luaL_loadbufferx` na DLL oficial `lua54x64.dll` + auditoria de todos os métodos `:setXxx(` contra `sdk/rrpgGUI.lua`.
2. **Fallback Seguro Fora de Mesa:**
   * Se o jogador testar rolagens com a ficha aberta na Biblioteca fora de uma sala (`Firecast.getMesaDe(sheet) == nil`), `firecast_bridge.lua` executa `rolagem:rolarLocalmente()`, lê `rolagem.ops` exatamente da mesma forma e exibe o resultado completo via `Dialogs.showMessage` sem erro de `nil`.
3. **Suíte Automatizada (`Tests/suite_v20.lua`):**
   * **Rolagens V20:** Sucesso simples, especialidade (`10 = 2`, `[10, 1] = 1`), falha simples quando `rawSuccesses > 0` cancelados por `1`s (`[8, 1] -> failure`, nunca `botch`!), falha crítica real (`[4, 1] -> botch`), `+1 FdV` imune a `1`s, penalidade de Perícia `0` (`+1 dif`) e bloqueio de Conhecimento `0`.
   * **Geração e Sangue:** Todos os degraus da 4ª à 15ª geração, bloqueio de gasto por turno, exceção de *Rapidez*, custo dobrado na 15ª geração e teto de *Blood Buff*.
   * **Vitalidade:** Empilhamento `* > X > /`, conversão Contundente → Letal ao lotar os 7 níveis, penalidades e ignorar penalidade em Absorção/Frenesi.
   * **Disciplinas e Antecedentes:** Ativação de poderes de clã e fora do clã, desconto de recursos, aplicação de *Potência/Rapidez/Fortitude* nas paradas, cálculo de Geração pelo antecedente e parada de Caça com `Rebanho + Domínio`.
   * **Criação e XP:** Validação de `7/5/3` + `13/9/5` (teto 3 pré-bônus) + `15 Bônus` + teto de `+7 Defeitos`; perfil Mortal `6/4/3` e `7/5/3`; custos XP (`Clã ×5`, `Fora ×7`, `Caitiff ×6`, `Habilidade nova 3`, `FdV ×1`); fraqueza Brujah (`+2 dif Frenesi`) e transição Mortal → Carniçal.
