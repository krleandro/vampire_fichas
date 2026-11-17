local V20 = require("Core.v20_init")
local CT = require("Core.coterie_tracker")

assert(V20.CoterieTracker == CT, "V20.CoterieTracker deve apontar para Core.coterie_tracker")

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
assert(decl[1].simultaneous == false and decl[4].simultaneous == false and decl[5].simultaneous == false)
-- Garante que a lista original não foi mutada
assert(raw[1].id == "c1" and raw[1].simultaneous == nil)

local act = CT.sortInitiativeEntries(raw, "acao")
-- Maior total age primeiro (15 antes de 11); no empate em 15, maior initMod (9 antes de 8)
assert(act[1].id == "c3" and act[2].id == "c1")
assert(act[3].simultaneous == true and act[4].simultaneous == true)
assert(act[5].id == "c2" and act[5].simultaneous == false)

-- 1b. upsertInitiativeEntry: atualização in-place por id, limite padrão (20) e customizado
local upList = {}
upList = CT.upsertInitiativeEntry(upList, { id = "u1", name = "[TESTE_E2E] Gangrel #1", d10 = 4, initMod = 5, total = 9, hidden = false }, 3)
upList = CT.upsertInitiativeEntry(upList, { id = "u2", name = "[TESTE_E2E] Ventrue #2", d10 = 8, initMod = 4, total = 12, hidden = "false" }, 3)
upList = CT.upsertInitiativeEntry(upList, { id = "u3", name = "[TESTE_E2E] Lasombra #3", d10 = 9, initMod = 7, total = 16, hidden = "true" }, 3)
assert(#upList == 3)
assert(upList[2].hidden == false and upList[3].hidden == true)

-- Exceder maxEntries com novo id não ultrapassa o teto
local capped = CT.upsertInitiativeEntry(upList, { id = "u4", name = "[TESTE_E2E] Extra #4", d10 = 10, initMod = 8, total = 18, hidden = false }, 3)
assert(#capped == 3 and capped[1].id == "u1" and capped[3].id == "u3")

-- Atualizar id existente mesmo no teto substitui a entrada sem duplicar
local updated = CT.upsertInitiativeEntry(capped, { id = "u2", name = "[TESTE_E2E] Ventrue #2 Reroll", d10 = 10, initMod = 4, total = 14, hidden = "1" }, 3)
assert(#updated == 3 and updated[2].total == 14 and updated[2].hidden == true)
assert(upList[2].total == 12, "upsertInitiativeEntry não deve mutar a tabela de entrada")

-- Limite padrão = 20
local twenty = {}
for i = 1, 25 do
    twenty = CT.upsertInitiativeEntry(twenty, {
        id = "init_" .. i,
        name = "[TESTE_E2E] Combatente #" .. i,
        d10 = 5,
        initMod = 4,
        total = 9,
    })
end
assert(#twenty == 20)

-- 2. Filtragem de Iniciativa Pública oculta NPCs invisíveis para jogadores mas mantém para o Narrador
local pubInit = CT.filterPublicInitiative(act, false)
assert(#pubInit == 4)
for _, e in ipairs(pubInit) do
    assert(e.id ~= "c5")
    assert(not tostring(e.displayName or ""):find("%[Oculto%]"))
    assert(not tostring(e.label or ""):find("%[Oculto%]"))
end
-- Como Gêmeo B (c5) está oculto, Gêmeo A (c4) não vaza flag simultaneous para jogadores!
for _, e in ipairs(pubInit) do
    if e.id == "c4" then
        assert(e.simultaneous == false, "Empate com NPC oculto não deve vazar simultaneous para jogadores")
    end
end

-- PF3-1: isStoryteller como string "false" / 0 vs "true" / 1
assert(#CT.filterPublicInitiative(act, "false") == 4)
assert(#CT.filterPublicInitiative(act, 0) == 4)

local stInit = CT.filterPublicInitiative(act, true)
assert(#stInit == 5)
local foundHiddenSt = false
for _, e in ipairs(stInit) do
    if e.id == "c5" then
        foundHiddenSt = true
        assert(e.displayName:sub(1, 9) == "[Oculto] ", "displayName do Narrador deve iniciar com '[Oculto] '")
        assert(e.label:sub(1, 9) == "[Oculto] ", "label do Narrador deve iniciar com '[Oculto] '")
        assert(e.simultaneous == true)
    end
end
assert(foundHiddenSt == true)
assert(#CT.filterPublicInitiative(act, "true") == 5)
assert(#CT.filterPublicInitiative(act, "1") == 5)

-- Idempotência de "[Oculto] " ao refiltrar
local stInitAgain = CT.filterPublicInitiative(stInit, true)
for _, e in ipairs(stInitAgain) do
    if e.id == "c5" then
        assert(not e.displayName:find("%[Oculto%] %[Oculto%]"), "Não deve duplicar prefixo [Oculto]")
    end
end

-- 3. Condição Física Aparente e Barreira Anti-Metajogo na Camada Pública
assert(CT.computeApparentCondition({ dano_contundente = 0, dano_letal = 0, dano_aggravado = 0 }) == "Saudável")
assert(CT.computeApparentCondition({ dano_contundente = 1, dano_letal = 0, dano_aggravado = 0 }) == "Escoriado")
assert(CT.computeApparentCondition({ dano_contundente = 1, dano_letal = 1, dano_aggravado = 0 }) == "Escoriado")
assert(CT.computeApparentCondition({ dano_contundente = 3, dano_letal = 0, dano_aggravado = 0 }) == "Ferido")
assert(CT.computeApparentCondition({ dano_contundente = 2, dano_letal = 2, dano_aggravado = 0 }) == "Ferido")
assert(CT.computeApparentCondition({ dano_contundente = 2, dano_letal = 3, dano_aggravado = 0 }) == "Gravemente Ferido")
assert(CT.computeApparentCondition({ dano_contundente = 2, dano_letal = 3, dano_aggravado = 1 }) == "Gravemente Ferido")
assert(CT.computeApparentCondition({ dano_contundente = 0, dano_letal = 7, dano_aggravado = 0 }) == "Incapacitado / Torpor")
-- PF3-1: em_torpor como booleano e string NDB ("true" / "1"), e espelho dano_agravado/dano_aggravado sem duplicar
assert(CT.computeApparentCondition({ dano_contundente = 0, dano_letal = 0, dano_aggravado = 0, em_torpor = "true" }) == "Incapacitado / Torpor")
assert(CT.computeApparentCondition({ dano_contundente = 0, dano_letal = 0, dano_aggravado = 2, dano_agravado = 2 }) == "Escoriado")

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
    assert(item.sangue_max == nil and item.fdv_perm == nil and item.geracao == nil and item.xp_pendente_status == nil)
    assert(type(item.nome) == "string" and type(item.condicao_aparente) == "string")
    local keyCount = 0
    for _ in pairs(item) do keyCount = keyCount + 1 end
    assert(keyCount == 3, "Resumo público deve conter estritamente 3 chaves (key, nome, condicao_aparente)")
end
assert(pubList[2].condicao_aparente == "Ferido")

-- PF3-1: Whitelist estrita de visible em buildPublicSummary (nil, "false", 0 e visivelRecursivamente=false excluídos; "true" e 1 aceitos)
local pf3Chars = {
    { key = "v_nil",   visible = nil,    sheet = { nome = "[TESTE_E2E] Sem Visible" } },
    { key = "v_fstr",  visible = "false", sheet = { nome = "[TESTE_E2E] False String" } },
    { key = "v_zero",  visible = 0,      sheet = { nome = "[TESTE_E2E] Zero Visible" } },
    { key = "v_recf",  visible = true,   visivelRecursivamente = false, sheet = { nome = "[TESTE_E2E] Pasta Oculta" } },
    { key = "v_tstr",  visible = "true", sheet = { nome = "[TESTE_E2E] True String" } },
    { key = "v_one",   visible = 1,      sheet = { nome = "[TESTE_E2E] One Visible" } },
}
local pf3Pub = CT.buildPublicSummary(pf3Chars)
assert(#pf3Pub == 2 and pf3Pub[1].key == "v_tstr" and pf3Pub[2].key == "v_one")

-- 4. Cartões Paginados do Narrador (8 por página) incluem NPCs ocultos, medidores completos e flags
local p1 = CT.buildStorytellerCards(libChars, 1, 8)
assert(p1.page == 1 and p1.totalPages == 2 and p1.totalCount == 10 and #p1.cards == 8)
assert(p1.cards[1].sangue_txt:find("12/13") ~= nil)
assert(p1.cards[1].sangue_txt:find("1/2") ~= nil)
assert(p1.cards[1].fdv_txt == "6/7")
assert(p1.cards[1].cla_titulo == "Tremere" and p1.cards[1].geracao == 10 and p1.cards[1].isVampire == true)
assert(p1.cards[1].flags_txt:find("Frenesi") ~= nil)
assert(p1.cards[3].hasPendingXP == true and p1.cards[3].flags_txt:find("XP Pendente") ~= nil)
assert(p1.cards[1].nodeRef == libChars[1].sheet)

local p2 = CT.buildStorytellerCards(libChars, 2, 8)
assert(p2.page == 2 and #p2.cards == 2)
assert(p2.cards[2].flags_txt:find("Oculto") ~= nil)

-- PF3-1 nos cartões do Narrador: flags em string ("true") + ficha Mortal / Carniçal + paginação vazia/clamp
local mixedChars = {
    {
        key = "m_ghoul",
        visible = "false",
        dataType = "br.com.v20.Mortal",
        sheet = {
            nome = "[TESTE_E2E] Carniçal Vigia",
            is_vampire = "false",
            mortal_sobrenatural_modo = "carnical",
            sangue_atual = 2,
            sangue_max = 2,
            sangue_gasto_turno = 0,
            sangue_por_turno = 1,
            fdv_temp = 4,
            fdv_perm = 5,
            em_agarrao = "true",
            em_torpor = "0",
        },
    },
    {
        key = "m_human",
        visible = "1",
        dataType = "br.com.v20.Mortal",
        sheet = {
            nome = "[TESTE_E2E] Detetive Humano",
            is_vampire = false,
            mortal_sobrenatural_modo = "humano",
            fdv_temp = 5,
            fdv_perm = 5,
        },
    },
}
local pm = CT.buildStorytellerCards(mixedChars, 99, 8)
assert(pm.page == 1 and pm.totalPages == 1 and pm.totalCount == 2 and #pm.cards == 2)
assert(pm.cards[1].isVampire == false and pm.cards[1].cla_titulo == "Carniçal")
assert(pm.cards[1].sangue_txt:find("2/2") ~= nil)
assert(pm.cards[1].flags_txt:find("Oculto") ~= nil and pm.cards[1].flags_txt:find("Agarrão") ~= nil)
assert(not pm.cards[1].flags_txt:find("Torpor"))
assert(pm.cards[2].isVampire == false and pm.cards[2].cla_titulo == "Mortal")

local emptyCards = CT.buildStorytellerCards({}, 1, 8)
assert(emptyCards.page == 1 and emptyCards.totalPages == 1 and emptyCards.totalCount == 0 and #emptyCards.cards == 0)
