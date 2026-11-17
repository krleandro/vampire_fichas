# Vampiro: A Máscara V20 (RRPG Firecast SDK 3.7b) — Especificação Técnica do Subprojeto 2

**Data:** 2026-11-17  
**Versão Alvo do Pacote:** `0.6.0` (`Vampiro_V20_Suite.rpk`)  
**Plataforma:** RRPG Firecast SDK 3.7b (`sdkApiVersion="88"`, `sdkMinorApiVersion="2"`, Lua 5.4)  
**Referência Mecânica Exclusiva:** *Vampire: The Masquerade — 20th Anniversary Edition (V20 Corebook)*  
**Base Prévia:** Subprojeto 1 (`v0.2.0`, branch `feat/subproject1-v20-suite`)

---

## 1. Objetivo e Escopo do Subprojeto 2

Expandir o pacote `dist/Vampiro_V20_Suite.rpk` de 2 modelos (`Brujah` e `Mortal`) para o **ecossistema completo de 15 modelos de ficha separados** (13 Clãs Tradicionais + Caitiff + Mortal), acrescentando:
1. **Automação mecânica individual das 14 fraquezas vampíricas** em um módulo dedicado (`Core/clan_weaknesses.lua`) integrado às rolagens, danos solares/letais, alimentação/caça, criação e evolução por XP, além de controles interativos específicos de cada clã na Aba 6;
2. **Subsistema completo de Magia do Sangue e Necromancia (`Data/blood_magic_catalog.lua` + `Core/blood_magic_engine.lua`)** cobrindo as **6 Linhas de Taumaturgia** (Níveis 1–5), as **3 Linhas de Necromancia** (Níveis 1–5) e **20 Rituais Clássicos** (10 Taumatúrgicos + 10 Necromânticos, Níveis 1–5) do Livro Básico V20 + rituais customizados, regras estritas de Linha Primária vs. Linhas Secundárias e integração com a Loja de XP;
3. **8ª Aba Dinâmica (`8. Magia do Sangue & Rituais`)** presente nas 14 fichas vampíricas: visível por padrão em **Tremere** e **Giovanni** e revelada automaticamente via `tab:setVisible(true)` nos demais 12 modelos assim que o personagem possuir pontos em *Taumaturgia*, *Necromancia* ou no Antecedente *Rituais*;
4. **Compilação, auditoria GUI e validação em runtime na `lua54x64.dll` de todas as 15 fichas** dentro de `dist/Vampiro_V20_Suite.rpk` (`v0.6.0`).

---

## 2. Os 15 Modelos de Ficha Registrados (`module.xml`)

| # | Clã / Perfil | `formName` | Arquivo `.lfm` | `dataType` | Título na Mesa do Firecast |
| :-: | :--- | :--- | :--- | :--- | :--- |
| 1 | Brujah | `frmBrujah` | `Sheets/frmBrujah.lfm` | `br.com.v20.Brujah` | `Vampiro V20 - Brujah` |
| 2 | Gangrel | `frmGangrel` | `Sheets/frmGangrel.lfm` | `br.com.v20.Gangrel` | `Vampiro V20 - Gangrel` |
| 3 | Malkaviano | `frmMalkavian` | `Sheets/frmMalkavian.lfm` | `br.com.v20.Malkavian` | `Vampiro V20 - Malkaviano` |
| 4 | Nosferatu | `frmNosferatu` | `Sheets/frmNosferatu.lfm` | `br.com.v20.Nosferatu` | `Vampiro V20 - Nosferatu` |
| 5 | Toreador | `frmToreador` | `Sheets/frmToreador.lfm` | `br.com.v20.Toreador` | `Vampiro V20 - Toreador` |
| 6 | Tremere | `frmTremere` | `Sheets/frmTremere.lfm` | `br.com.v20.Tremere` | `Vampiro V20 - Tremere` |
| 7 | Ventrue | `frmVentrue` | `Sheets/frmVentrue.lfm` | `br.com.v20.Ventrue` | `Vampiro V20 - Ventrue` |
| 8 | Assamita | `frmAssamite` | `Sheets/frmAssamite.lfm` | `br.com.v20.Assamite` | `Vampiro V20 - Assamita` |
| 9 | Seguidores de Set | `frmSetite` | `Sheets/frmSetite.lfm` | `br.com.v20.Setite` | `Vampiro V20 - Seguidores de Set` |
| 10 | Giovanni | `frmGiovanni` | `Sheets/frmGiovanni.lfm` | `br.com.v20.Giovanni` | `Vampiro V20 - Giovanni` |
| 11 | Lasombra | `frmLasombra` | `Sheets/frmLasombra.lfm` | `br.com.v20.Lasombra` | `Vampiro V20 - Lasombra` |
| 12 | Ravnos | `frmRavnos` | `Sheets/frmRavnos.lfm` | `br.com.v20.Ravnos` | `Vampiro V20 - Ravnos` |
| 13 | Tzimisce | `frmTzimisce` | `Sheets/frmTzimisce.lfm` | `br.com.v20.Tzimisce` | `Vampiro V20 - Tzimisce` |
| 14 | Caitiff | `frmCaitiff` | `Sheets/frmCaitiff.lfm` | `br.com.v20.Caitiff` | `Vampiro V20 - Caitiff` |
| 15 | Mortal | `frmMortal` | `Sheets/frmMortal.lfm` | `br.com.v20.Mortal` | `Vampiro V20 - Mortal` |

---

## 3. Especificação das 14 Fraquezas Automatizadas (`Core/clan_weaknesses.lua`)

O módulo `Core/clan_weaknesses.lua` expõe funções puras consumidas por `Adapter/firecast_bridge.lua` sem acoplamento de UI:

1. **Brujah (`passion` — V20, p. 49):**
   * *Mecânica:* `+2` na dificuldade de testes de Frenesi (máx. 10), `canAvoidWithWillpower = false`.
   * *Ação adicional na Aba 6:* Botão `[Encerrar Frenesi Ativo (-1 FdV)]` que gasta `1 FdV` temporária quando `em_frenesi == true`, desliga `em_frenesi` e anuncia no chat.
2. **Gangrel (`animal_features` — V20, p. 53):**
   * *Campos NDB:* `gangrel_tracos_qtd` (`0`), `gangrel_tracos_lista` (`""`), `gangrel_attr_penalizado` (`"attr_carisma"`).
   * *Mecânica:* Botão `[Registrar Frenesi Gangrel (+1 Traço)]` incrementa `gangrel_tracos_qtd`. Sempre que `gangrel_tracos_qtd > 0 and gangrel_tracos_qtd % 5 == 0`, deduz `1` ponto permanente do Atributo Social escolhido em `gangrel_attr_penalizado` (mín. `0` em Aparência ou `1`/`0` conforme regra V20 p. 53 — piso `0` permitido por maldição) e grava entrada automática no Log de Auditoria.
3. **Malkaviano (`derangement` — V20, p. 59):**
   * *Campos NDB:* `malkav_perturbacao` (`""`), `malkav_suprimida_cena` (`false`).
   * *Mecânica:* `validateCreationOnSheet` exige `malkav_perturbacao ~= ""` para Malkavianos. Botão `[Suprimir Perturbação na Cena (-1 FdV)]` desconta `1` de `fdv_temp`, ativa `malkav_suprimida_cena = true` (resetada em `clearSceneBuffs`) e notifica no chat.
4. **Nosferatu (`monstrous_appearance` — V20, p. 61):**
   * *Mecânica na Criação:* `attr_aparencia` inicia em `0` (e não `1`); em `validateCreationOnSheet`, a soma base de Atributos Sociais para Nosferatu subtrai apenas `2` pontos iniciais gratuitos (`(carisma - 1) + (manipulacao - 1) + aparencia`), validando perfeitamente `7/5/3`.
   * *Mecânica em Jogo/Rolagem:* Bloqueia subida de `attr_aparencia` em `adjustResource` e na Loja de XP. Em `rollFromSheet`, se `attrId == "attr_aparencia"` e não houver buff ativo de *Máscara das Mil Faces* (`obf_mask`) nem `narrador_override`, bloqueia/anuncia **Falha Automática pela Maldição Nosferatu**.
5. **Toreador (`aesthetic_fixation` — V20, p. 67):**
   * *Campos NDB:* `toreador_foco_arte` (`""`), `toreador_fascinado_cena` (`false`).
   * *Mecânica:* Botão `[Testar Fascínio Estético (Dif 6)]` rola `Autocontrole/Instinto` (dif. 6); em caso de falha (`totalSuccesses == 0`), marca automaticamente `toreador_fascinado_cena = true` (limpo em `clearSceneBuffs` ou gastando `1 FdV`).
6. **Tremere (`blood_bond_suscept` — V20, p. 69):**
   * *Campos NDB:* `tremere_laco_goles` (`0`), `tremere_regente_nome` (`""`).
   * *Mecânica:* Botão `[Registrar Gole de Vitae (+1)]` avança `0 -> 1 -> 2`, onde **`2 goles` já ativam `Laço de Sangue Completo (2/2 — Maldição Tremere)`** (em vez dos 3 goles padrão), exibindo `tremere_laco_status` derivado e anunciando no chat.
7. **Ventrue (`selective_diet` — V20, p. 71):**
   * *Campos NDB:* `ventrue_presa_restrita` (`""`), `ventrue_presa_compativel` (`true`).
   * *Mecânica:* `validateCreationOnSheet` exige `ventrue_presa_restrita ~= ""`. Em `huntWithHerdDomain`, se `ventrue_presa_compativel == false` (e não for vitae vampírica), bloqueia o ganho de `sangue_atual` e anuncia vômito imediato pela restrição alimentar Ventrue.
8. **Assamita (`vitae_curse` — V20, p. 49 & p. 430):**
   * *Campos NDB:* `assamita_maldicao_modo` (`"ur_shulgi"` | `"tremere_classica"`), `assamita_vitae_qtd` (`1`), `assamita_vicio_ativo` (`false`).
   * *Mecânica:* Botão `[Ingerir Vitae Cainita]` aplica imediatamente `assamita_vitae_qtd` níveis de **dano Letal não absorvível** na trilha de Vitalidade (`Health.applyDamage`) e:
     * Em `"ur_shulgi"` (padrão V20 p. 49): adiciona a vitae à reserva e dispara teste de `Autocontrole` (`dif = math.min(10, 3 + qtd)`); se falhar, marca `assamita_vicio_ativo = true`;
     * Em `"tremere_classica"` (V20 p. 430): nenhum ponto de sangue é ganho (envenenamento cainita puro).
9. **Seguidores de Set (`light_sensitivity` — V20, p. 51):**
   * *Campos NDB:* `setita_luz_forte` (`false`), `dano_fonte_solar` (`false` na Aba 5/6).
   * *Mecânica:* Quando `setita_luz_forte == true`, `rollFromSheet` aplica automaticamente **`-1 dado`** na parada (`bonusDice - 1`, com aviso `"Sensibilidade à Luz Setita (-1 dado)"`). Quando `applyDamage` é acionado com `dano_fonte_solar == true` (`amount >= 1`), soma **`+2` níveis Agravados** adicionais.
10. **Giovanni (`painful_kiss` — V20, p. 55):**
    * *Campos NDB:* `giovanni_beijo_pontos` (`1`).
    * *Mecânica:* Em `huntWithHerdDomain` e no botão `[Aplicar O Beijo Doloroso]`, cada `N` pontos de sangue drenados causam **`2 × N` níveis de dano Letal** no recipiente mortal, anunciando no chat se o recipiente entrou em choque/morte (`2 × N >= 7`).
11. **Lasombra (`no_reflection` — V20, p. 57):**
    * *Campos NDB:* `lasombra_vigiado_espelhos` (`false`), `dano_fonte_solar` (`false`).
    * *Mecânica:* Quando `lasombra_vigiado_espelhos == true`, testes Sociais de disfarce/Lábia ou Furtividade recebem **`+1` na dificuldade**. Quando `applyDamage` é acionado com `dano_fonte_solar == true` (`amount >= 1`), soma **`+1` nível Agravado** adicional.
12. **Ravnos (`specific_vice` — V20, p. 63):**
    * *Campos NDB:* `ravnos_vicio_descricao` (`""`), `ravnos_compulsao_ativa` (`false`).
    * *Mecânica:* `validateCreationOnSheet` exige `ravnos_vicio_descricao ~= ""`. Botão `[Resistir ao Vício Ravnos (Dif 6)]` rola `Autocontrole/Instinto` (dif. 6) e marca `ravnos_compulsao_ativa = true` em caso de falha.
13. **Tzimisce (`native_soil` — V20, p. 71):**
    * *Campos NDB:* `tzimisce_origem_terra` (`""`), `tzimisce_dias_sem_terra` (`0`).
    * *Mecânica:* Quando `tzimisce_dias_sem_terra > 0`, `rollFromSheet` divide a parada final cumulativamente por `2 ^ dias` (`pool = math.max(1, math.floor(pool / (2 ^ dias)))` quando a parada original era `>= 1`), exibindo o alerta `"Fraqueza Tzimisce: X dia(s) sem terra natal"`. Botão `[Repousar com 2 Punhados de Terra Natal]` zera `tzimisce_dias_sem_terra = 0`.
14. **Caitiff (`social_outcast` — V20, p. 73):**
    * *Campos NDB:* `caitiff_estigma_ativo` (`true`).
    * *Mecânica:* Slots de Disciplina 1–3 iniciam em `"— Nenhuma —"` com categoria `"caitiff"` (`XP = Atual × 6` para qualquer disciplina existente, `10` para nova `0->1`). Quando `caitiff_estigma_ativo == true`, qualquer rolagem em `rollFromSheet` usando `attr_carisma`, `attr_manipulacao` ou `attr_aparencia` soma automaticamente **`+2` na dificuldade** (com aviso `"Estigma Social Caitiff (+2 dif)"`).

---

## 4. Subsistema de Magia do Sangue: Linhas e Rituais (`Data/blood_magic_catalog.lua` & `Core/blood_magic_engine.lua`)

### 4.1. Linhas Oficiais da V20 (Níveis 1 a 5 = 45 Poderes Estruturados)
* **Taumaturgia (6 Linhas do Livro Básico V20, p. 213–229):**
  * Sistema unificado V20 (p. 212): custo **`1 Sangue`** (`2` na 15ª Geração via canalização), rolagem de **Força de Vontade Permanente (`attr_fdv_ref`)** contra **`dificuldade = nível_do_poder + 3`** (`4..8`); Falha Crítica consome **`-1 Força de Vontade Permanente`** (sinalizado claramente no relatório do chat para confirmação/aplicação).
  * Linhas incluídas:
    1. `path_of_blood` — *Linha do Sangue* (p. 213)
    2. `lure_of_flames` — *Sedutor das Chamas* (p. 218)
    3. `movement_of_the_mind` — *Movimento da Mente* (p. 220)
    4. `path_of_conjuring` — *Linha da Conjuração* (p. 221)
    5. `hands_of_destruction` — *Mãos da Destruição* (p. 225)
    6. `weather_control` — *Controle do Clima* (p. 228)
* **Necromancia (3 Linhas do Livro Básico V20, p. 159–174):**
  * Cada poder possui seu custo individual de Sangue/FdV e sua parada específica (`Percepção + Ocultismo`, `Manipulação + Ocultismo`, `Destreza + Ocultismo`, `Força de Vontade`, etc.) conforme o Livro Básico V20:
    1. `sepulchre_path` — *Linha do Sepulcro* (p. 160)
    2. `bone_path` — *Linha dos Ossos* (p. 164)
    3. `ash_path` — *Linha das Cinzas* (p. 169)

### 4.2. Regras de Linha Primária vs. Linhas Secundárias (V20, p. 159 & p. 212)
* **Linha Primária de Taumaturgia (`bm_thau_prim_id`) e de Necromancia (`bm_necro_prim_id`):**
  * Seu nível efetivo (`bm_thau_prim_nivel` / `bm_necro_prim_nivel`) é derivado automaticamente como `math.min(5, nivel_disciplina)` a partir dos pontos que o personagem possui em `thaumaturgy` / `necromancy` na Aba 3!
* **4 Slots de Linhas Secundárias (`bm_sec1` .. `bm_sec4`):**
  * Campos por slot: `bm_sec{i}_disc` (`"thaumaturgy"` | `"necromancy"`), `bm_sec{i}_path_id`, `bm_sec{i}_nivel` (`0..5`), `bm_sec{i}_pwr_lvl` (`1..5`), `bm_sec{i}_resumo`.
  * **Validação Estrita (`BloodMagicEngine.validateSecondaryPathUpgrade`):**
    1. Não pode repetir a própria Linha Primária;
    2. Exige `nivel_disciplina_pai >= 2` para adquirir o nível `1` de uma Linha Secundária;
    3. Enquanto `nivel_disciplina_pai < 5`, exige `novo_nivel_secundaria < nivel_disciplina_pai` (somente quando a Primária atinge `5`, as Secundárias podem chegar a `5`);
    4. Evolução na Loja de XP usa `traitKind = "secondary_path"` (`0 -> 1` custa **`7 XP`**; `1+` custa **`Atual × 4 XP`**), incluídos em `cmbXpLojaCampo` (`bm_sec1_nivel`..`bm_sec4_nivel`).

### 4.3. Grimório de 20 Rituais Clássicos V20 + Ritual Customizado
* **10 Rituais Taumatúrgicos (Níveis 1–5, V20 p. 231–240):**
  * Nv 1: *Defesa do Refúgio Sagrado*, *Despertar com o Frescor do Anoitecer*;
  * Nv 2: *Foco Principal de Infusão de Vitae*, *Proteção Contra Carniçais*;
  * Nv 3: *Incorpóreo Passar*, *Pele da Víbora Flamejante / Escudo da Presença Maligna* (*Proteção Contra Membros*, p. 236);
  * Nv 4: *Coração de Pedra*, *Espelho Estilhaçado / Proteção Contra Espíritos*;
  * Nv 5: *Abandonar os Grilhões*, *Contrato de Sangue*.
  * Rolagem padrão V20 (p. 230): **`Inteligência + Ocultismo`**, dificuldade **`math.min(9, 3 + nivel_ritual)`** (`4..8`).
* **10 Rituais Necromânticos (Níveis 1–5, V20 p. 175–183):**
  * Nv 1: *Chamado do Faminto*, *Olhos da Sepultura*;
  * Nv 2: *Mão da Glória*, *Sangue de Osíris / Olhar da Mortalha*;
  * Nv 3: *Ritual da Corrente Desenterrada*, *Cálice de Osso*;
  * Nv 4: *Beijo de Caronte*, *Rasgar a Mortalha*;
  * Nv 5: *Aperto da Morte (Grasp the Ghostly)*, *Trono de Esfinge / Exílio Sombrio*.
  * Rolagem padrão: **`Inteligência + Ocultismo`**, dificuldade específica do ritual (`4..8`).
* **Validação de Conjuração:** `BloodMagicEngine.castRitual` verifica se o personagem possui nível suficiente na disciplina correspondente (`thaumaturgy >= ritual.level` ou `necromancy >= ritual.level`, salvo `storytellerOverride`), desconta eventuais custos de Sangue/FdV do ritual e despacha a rolagem `Inteligência + Ocultismo` no chat.
* **Slot de Ritual Customizado (`ritual_custom_*`):** Permite cadastrar e rolar qualquer ritual de suplemento informando Nome, Tradição, Nível (`1..5+`), Custo de Sangue/FdV e Dificuldade.

---

## 5. Aba 8 Dinâmica (`tabMagiaSangue`) e Integração de Build

1. **Visibilidade Inteligente (`atualizarPermissoesModo` + `V20Bridge.hasBloodMagicAccess`):**
   * Nas fichas `frmTremere` e `frmGiovanni`, `hasBloodMagicAccess` retorna `true` desde a abertura inicial (pois *Taumaturgia* / *Necromancia* fazem parte do trio nativo do clã).
   * Nas outras 12 fichas vampíricas (`Brujah`, `Gangrel`, `Malkavian`, `Nosferatu`, `Toreador`, `Ventrue`, `Assamite`, `Setite`, `Lasombra`, `Ravnos`, `Tzimisce`, `Caitiff`), `tabMagiaSangue` inicia oculta (`visible="false"`) e torna-se automaticamente visível (`self.tabMagiaSangue:setVisible(true)`) assim que qualquer `disc_slot{1..9}` tiver `thaumaturgy` ou `necromancy` com `nivel >= 1` (ou mesmo selecionada com `nivel >= 0` para configuração na criação!) ou `bg_rituals >= 1`. Caso seja ocultada enquanto ativa, o formulário retorna `pgcPrincipal:setTabIndex(0)` antes de ocultá-la.
2. **Escala do Build (`tools/build_v20_suite.py`):**
   * `Templates/generate_vampire_lfm.py` ganha flag `--all-clans` gerando deterministicamente os 14 arquivos `Sheets/frm<Clan>.lfm`.
   * `tools/build_v20_suite.py` compila e valida os **15 arquivos `.lfm.lua`** + todos os módulos Lua/DLua na `lua54x64.dll`, audita os métodos `:setXxx(` contra `sdk/rrpgGUI.lua + sdk/rrpgObjs.lua`, atualiza `<version>0.6.0</version>` em `module.xml` e empacota os 15 `<dataType>` em `dist/Vampiro_V20_Suite.rpk` e `.rdk`.
3. **Plano de Testes Automatizados:**
   * `Tests/test_10_clan_weaknesses.lua`: exercita individualmente as **14 fraquezas vampíricas** (Brujah `+2 Frenesi`, Gangrel perda social a cada 5 traços, Malkaviano perturbação obrigatória + supressão por FdV, Nosferatu criação com Social `-2` + falha automática em Aparência + exceção *Máscara das Mil Faces*, Toreador fascínio, Tremere laço em 2 goles, Ventrue presa incompatível, Assamita dano letal + vício Ur-Shulgi vs Tremere Clássica, Setita `-1 dado` luz forte + `+2 Agravado` solar, Giovanni dobro de dano no Beijo, Lasombra `+1 dif` espelhos + `+1 Agravado` solar, Ravnos vício, Tzimisce divisão cumulativa `2^dias` até mín. 1 dado, Caitiff `×6 XP` + `+2 dif Social`).
   * `Tests/test_11_blood_magic.lua`: valida todas as **9 Linhas (45 poderes)** e **20 Rituais**, sincronia da Linha Primária, travas de Linha Secundária (`primaria >= 2`, `sec < primaria` até 5), custos de XP (`7` / `×4`), conjuração de rituais e bloqueio por nível insuficiente.
   * `Tests/test_08_bridge_and_lfm_gen.py` & `Tests/test_09_rpk_package.py`: atualizados para validar XML/controles únicos das **15 fichas**, auto-boot alfabético VHD e instanciação + eventos + destruição reversa dos **15 formulários compilados** dentro da `lua54x64.dll`.
