# Suite de plugins para Vampiro - A máscara V 20

**Desenvolvida por Mestre Carlos (`krmirim`)**  
Plataforma: **RRPG Firecast (SDK 3.7b / API 88.2 / Lua 5.4)**  
Versão Atual: **`1.0.2`**

---

## 📥 Download e Instalação Direta

- **[Baixar `Vampiro_V20_Suite.rpk` (Clique aqui)](https://github.com/krleandro/vampire_fichas/raw/main/dist/Vampiro_V20_Suite.rpk)**

1. Baixe o arquivo `Vampiro_V20_Suite.rpk` acima e dê **duplo clique** nele com o RRPG Firecast aberto (ou vá em *Plugins → Instalar Plugin*).
2. As futuras atualizações serão detectadas **automaticamente** ao abrir qualquer ficha ou pelo botão **`Verificar / Atualizar`** na aba **`Sobre`**.

---

## 🦇 O que está incluído na Suíte (16 Formulários)

- **15 Modelos de Ficha dedicados** na criação de personagem da mesa:
  - **13 Clãs Tradicionais:** Brujah, Gangrel, Malkaviano, Nosferatu, Toreador, Tremere, Ventrue, Assamita, Seguidores de Set, Giovanni, Lasombra, Ravnos e Tzimisce;
  - **Caitiff** (Sem Clã);
  - **Mortal** (Humano padrão/heroico, Carniçal e Numina).
- **Painel Lateral Acoplável (`TablesDock`):** `Vampiro V20 - Painel da Coterie & Iniciativa` com separação anti-metajogo em duas camadas (Visão Pública segura para jogadores + Painel Exclusivo do Narrador com cartões paginados e comandos em lote).
- **Automação Mecânica V20 Completa:**
  - **17 Disciplinas Clássicas** (Níveis 1–5 = 85 poderes), **9 Linhas de Taumaturgia/Necromancia** (45 poderes) e **20 Rituais Clássicos** + customizados;
  - **14 Fraquezas Vampíricas** automatizadas;
  - **20 Manobras de Combate Assistido V20**, divisão de paradas pela menor parada vs. ações extras de *Rapidez* e rolagem encadeada de dano;
  - **Gerações 4ª à 15ª** (incluindo Sangue-Fraco), Antecedentes interativos, Qualidades/Defeitos, Virtudes/Trilhas de Moralidade, Assistente de Criação e Loja de XP auditada pelo Narrador.

---

## 🔄 Como Publicar uma Nova Versão (Auto-Updater)

Sempre que alterar as fichas ou regras:

1. Incremente `<version>` em `module.xml` (ex.: `1.0.2` → `1.0.3`);
2. Gere o novo pacote e rode as 14 suítes de validação:
   ```powershell
   python tools/build_v20_suite.py
   python Tests/run_tests.py
   ```
3. Faça commit e envie para o GitHub:
   ```powershell
   git add -A
   git commit -m "chore(release): bump suite to v1.0.3"
   git push
   ```
Todos os jogadores e narradores receberão o aviso de atualização automaticamente no Firecast!
