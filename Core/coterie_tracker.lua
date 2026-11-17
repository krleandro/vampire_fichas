local Health = require("Core.health")
local Clans = require("Data.clans")
local MoralityCatalog = require("Data.morality_virtues")

local CoterieTracker = {}

local function isTrue(v)
    return v == true or v == "true" or v == 1 or v == "1"
end

local function isFalse(v)
    return v == false or v == "false" or v == 0 or v == "0"
end

local function nonEmpty(s)
    return type(s) == "string" and s:match("%S") ~= nil
end

local function safeInt(v, default)
    local n = tonumber(v)
    if n == nil or n ~= n or n == math.huge or n == -math.huge then
        return default or 0
    end
    return math.floor(n)
end

local function safeNonNegInt(v, default)
    local n = safeInt(v, default)
    return n < 0 and 0 or n
end

local function clamp(val, minV, maxV)
    if val < minV then return minV end
    if val > maxV then return maxV end
    return val
end

local function stripHiddenPrefix(s)
    if type(s) ~= "string" then return "Combatente" end
    local stripped = s:gsub("^(%[Oculto%]%s*)+", "")
    return nonEmpty(stripped) and stripped or "Combatente"
end

local function copyEntry(e)
    local out = {}
    if type(e) == "table" then
        for k, v in pairs(e) do
            out[k] = v
        end
    end
    return out
end

local function normalizeInitEntry(e, fallbackIdx)
    local out = copyEntry(e)
    local rawName = nonEmpty(e and e.name) and tostring(e.name)
        or (nonEmpty(e and e.nome) and tostring(e.nome) or "Combatente")
    local cleanName = stripHiddenPrefix(rawName)
    local rawId = (e and e.id ~= nil and tostring(e.id) ~= "") and tostring(e.id)
        or ((e and e.key ~= nil and tostring(e.key) ~= "") and tostring(e.key) or cleanName)

    local d10 = safeInt(e and e.d10, 0)
    local initMod = safeInt(e and e.initMod, 0)
    local total = (e and e.total ~= nil) and safeInt(e.total, d10 + initMod) or (d10 + initMod)

    out.id = rawId
    out.name = cleanName
    out.d10 = d10
    out.initMod = initMod
    out.total = total
    out.hidden = isTrue(e and e.hidden)
    out._origIdx = fallbackIdx or 0
    return out
end

local function markSimultaneous(list)
    local counts = {}
    for _, item in ipairs(list) do
        local key = tostring(item.total) .. ":" .. tostring(item.initMod)
        counts[key] = (counts[key] or 0) + 1
    end
    for _, item in ipairs(list) do
        local key = tostring(item.total) .. ":" .. tostring(item.initMod)
        item.simultaneous = (counts[key] or 0) > 1
    end
end

local function buildClanByDataTypeLookup()
    local map = {}
    for _, cid in ipairs(Clans.ORDER or {}) do
        local c = Clans.CLANS and Clans.CLANS[cid]
        if c and c.dataType then
            map[c.dataType] = c
        end
    end
    return map
end

local CLAN_BY_DATATYPE = buildClanByDataTypeLookup()

local function buildMoralityNameLookup()
    local map = {}
    for _, p in ipairs(MoralityCatalog.PATHS or {}) do
        if p.id and p.name then
            map[p.id] = p.name
        end
    end
    return map
end

local MORALITY_NAMES = buildMoralityNameLookup()

local function isCharacterVisible(char)
    if type(char) ~= "table" then
        return false
    end
    return isTrue(char.visible)
        and not isFalse(char.visivel)
        and not isFalse(char.visivelRecursivamente)
end

local function isVampireCharacter(char, sheet)
    if type(sheet) == "table" then
        if isFalse(sheet.is_vampire) then
            return false
        end
        if nonEmpty(sheet.mortal_sobrenatural_modo) then
            return false
        end
    end
    if type(char) == "table" and char.dataType == "br.com.v20.Mortal" then
        return false
    end
    return true
end

function CoterieTracker.sortInitiativeEntries(entries, phase)
    local list = {}
    if type(entries) == "table" then
        for i, e in ipairs(entries) do
            if type(e) == "table" then
                table.insert(list, normalizeInitEntry(e, i))
            end
        end
    end

    local isActionPhase = (tostring(phase or "declaracao"):lower() == "acao")

    table.sort(list, function(a, b)
        if a.total ~= b.total then
            if isActionPhase then
                return a.total > b.total
            else
                return a.total < b.total
            end
        end
        if a.initMod ~= b.initMod then
            if isActionPhase then
                return a.initMod > b.initMod
            else
                return a.initMod < b.initMod
            end
        end
        if a.name ~= b.name then
            return a.name < b.name
        end
        if a.id ~= b.id then
            return a.id < b.id
        end
        return a._origIdx < b._origIdx
    end)

    for _, item in ipairs(list) do
        item._origIdx = nil
    end

    markSimultaneous(list)
    return list
end

function CoterieTracker.upsertInitiativeEntry(entries, newEntry, maxEntries)
    local limit = math.max(1, safeInt(maxEntries, 20))
    local out = {}
    if type(entries) == "table" then
        for i, e in ipairs(entries) do
            if type(e) == "table" and #out < limit then
                local norm = normalizeInitEntry(e, i)
                norm._origIdx = nil
                table.insert(out, norm)
            end
        end
    end

    if type(newEntry) ~= "table" then
        markSimultaneous(out)
        return out
    end

    local candidate = normalizeInitEntry(newEntry, #out + 1)
    candidate._origIdx = nil

    local updated = false
    for idx, existing in ipairs(out) do
        if existing.id == candidate.id then
            out[idx] = candidate
            updated = true
            break
        end
    end

    if not updated and #out < limit then
        table.insert(out, candidate)
    end

    markSimultaneous(out)
    return out
end

function CoterieTracker.filterPublicInitiative(entries, isStoryteller)
    local st = isTrue(isStoryteller)
    local out = {}
    if type(entries) == "table" then
        for i, e in ipairs(entries) do
            if type(e) == "table" then
                local norm = normalizeInitEntry(e, i)
                norm._origIdx = nil
                if st or not norm.hidden then
                    table.insert(out, norm)
                end
            end
        end
    end

    markSimultaneous(out)

    for _, item in ipairs(out) do
        local prefix = (st and item.hidden) and "[Oculto] " or ""
        local simSuffix = item.simultaneous and " [Simultâneo]" or ""
        item.displayName = prefix .. item.name
        item.label = string.format(
            "%s%s — %d (%d + %d)%s",
            prefix, item.name, item.total, item.d10, item.initMod, simSuffix
        )
    end

    return out
end

function CoterieTracker.computeApparentCondition(sheet)
    if type(sheet) ~= "table" then
        return "Saudável"
    end
    if isTrue(sheet.em_torpor) or isTrue(sheet.torpor) or isTrue(sheet.incapacitado) then
        return "Incapacitado / Torpor"
    end

    local bas = (sheet.dano_contundente ~= nil)
        and safeNonNegInt(sheet.dano_contundente, 0)
        or safeNonNegInt(sheet.bashing, 0)
    local let = (sheet.dano_letal ~= nil)
        and safeNonNegInt(sheet.dano_letal, 0)
        or safeNonNegInt(sheet.lethal, 0)
    local agg = math.max(
        safeNonNegInt(sheet.dano_aggravado, 0),
        safeNonNegInt(sheet.dano_agravado, 0),
        safeNonNegInt(sheet.aggravated, 0)
    )

    local totalDmg = bas + let + agg
    if totalDmg >= 7 then
        return "Incapacitado / Torpor"
    elseif totalDmg >= 5 then
        return "Gravemente Ferido"
    elseif totalDmg >= 3 then
        return "Ferido"
    elseif totalDmg >= 1 then
        return "Escoriado"
    end
    return "Saudável"
end

function CoterieTracker.buildPublicSummary(libraryCharacters)
    local out = {}
    if type(libraryCharacters) ~= "table" then
        return out
    end

    for i, char in ipairs(libraryCharacters) do
        if isCharacterVisible(char) then
            local sheet = type(char.sheet) == "table" and char.sheet or {}
            local nome = nonEmpty(sheet.nome) and tostring(sheet.nome)
                or (nonEmpty(char.nome) and tostring(char.nome) or "Personagem")
            table.insert(out, {
                key               = tostring(char.key or char.id or ("char_" .. i)),
                nome              = nome,
                condicao_aparente = CoterieTracker.computeApparentCondition(sheet),
            })
        end
    end

    return out
end

function CoterieTracker.buildStorytellerCards(libraryCharacters, page, pageSize)
    local all = {}
    if type(libraryCharacters) == "table" then
        for _, char in ipairs(libraryCharacters) do
            if type(char) == "table" then
                table.insert(all, char)
            end
        end
    end

    local totalCount = #all
    local pSize = math.max(1, safeInt(pageSize, 8))
    local totalPages = (totalCount == 0) and 1 or math.floor((totalCount + pSize - 1) / pSize)
    local curPage = clamp(safeInt(page, 1), 1, totalPages)

    local startIdx = (curPage - 1) * pSize + 1
    local endIdx = math.min(totalCount, curPage * pSize)
    local cards = {}

    for i = startIdx, endIdx do
        local char = all[i]
        local sheet = type(char.sheet) == "table" and char.sheet or {}
        local isVamp = isVampireCharacter(char, sheet)
        local isGhoul = (not isVamp) and (isTrue(sheet.isGhoul) or sheet.mortal_sobrenatural_modo == "carnical")
        local isNumina = (not isVamp) and (isTrue(sheet.hasNumina) or sheet.mortal_sobrenatural_modo == "numina")
        local visible = isCharacterVisible(char)

        local nome = nonEmpty(sheet.nome) and tostring(sheet.nome)
            or (nonEmpty(char.nome) and tostring(char.nome) or "Personagem")

        local claTitulo
        if isVamp then
            local cid = type(sheet.cla_id) == "string" and sheet.cla_id:lower() or ""
            local clanEntry = (Clans.CLANS and Clans.CLANS[cid]) or CLAN_BY_DATATYPE[char.dataType or ""]
            claTitulo = (clanEntry and clanEntry.name)
                or (nonEmpty(sheet.cla_nome) and tostring(sheet.cla_nome))
                or "Vampiro"
        elseif isGhoul then
            claTitulo = "Carniçal"
        elseif isNumina then
            claTitulo = "Mortal (Numina)"
        else
            claTitulo = "Mortal"
        end

        local geracao = isVamp and safeInt(sheet.geracao or sheet.geracao_base, 13) or 0

        local sangueTxt
        if isVamp or isGhoul or safeNonNegInt(sheet.sangue_max, 0) > 0 then
            local curBlood = safeNonNegInt(sheet.sangue_atual, 0)
            local maxBlood = safeNonNegInt(sheet.sangue_max, isVamp and 10 or 2)
            local spentTurn = safeNonNegInt(sheet.sangue_gasto_turno, 0)
            local perTurn = safeNonNegInt(sheet.sangue_por_turno, 1)
            sangueTxt = string.format("%d/%d (Turno: %d/%d)", curBlood, maxBlood, spentTurn, perTurn)
        else
            sangueTxt = "N/A (Mortal)"
        end

        local fdvTemp = safeNonNegInt(sheet.fdv_temp, 0)
        local fdvPerm = safeNonNegInt(sheet.fdv_perm, 1)
        local fdvTxt = string.format("%d/%d", fdvTemp, fdvPerm)

        local bas = (sheet.dano_contundente ~= nil)
            and safeNonNegInt(sheet.dano_contundente, 0)
            or safeNonNegInt(sheet.bashing, 0)
        local let = (sheet.dano_letal ~= nil)
            and safeNonNegInt(sheet.dano_letal, 0)
            or safeNonNegInt(sheet.lethal, 0)
        local agg = math.max(
            safeNonNegInt(sheet.dano_aggravado, 0),
            safeNonNegInt(sheet.dano_agravado, 0),
            safeNonNegInt(sheet.aggravated, 0)
        )
        local hStatus = Health.getStatus({
            isVampire  = isVamp,
            hugeSize   = isTrue(sheet.tem_tamanho_grande),
            bashing    = bas,
            lethal     = let,
            aggravated = agg,
        })
        local vitLabel = isTrue(sheet.em_torpor) and "Torpor" or hStatus.currentLevelName
        local penPart = (hStatus.penalty < 0) and string.format("%d | ", hStatus.penalty) or ""
        local vitalidadeTxt = string.format("%s (%sC:%d L:%d A:%d)", vitLabel, penPart, bas, let, agg)

        local moralName = nonEmpty(sheet.moralidade_nome) and tostring(sheet.moralidade_nome)
            or (nonEmpty(sheet.moralidade_tipo) and MORALITY_NAMES[sheet.moralidade_tipo])
            or "Humanidade"
        local moralVal = safeNonNegInt(sheet.moralidade_val, 7)
        local moralidadeTxt = string.format("%s %d", moralName, moralVal)

        local hasPendingXP = (sheet.xp_pendente_status == "pendente") or isTrue(sheet.xp_pendente)

        local flags = {}
        if not visible then
            table.insert(flags, "[Oculto]")
        end
        if isTrue(sheet.em_frenesi) then
            table.insert(flags, "[Frenesi]")
        end
        if isTrue(sheet.em_torpor) then
            table.insert(flags, "[Torpor]")
        end
        if isTrue(sheet.em_agarrao) then
            table.insert(flags, "[Agarrão]")
        end
        if hasPendingXP then
            table.insert(flags, "[XP Pendente]")
        end

        table.insert(cards, {
            key            = tostring(char.key or char.id or ("char_" .. i)),
            nome           = nome,
            cla_titulo     = claTitulo,
            geracao        = geracao,
            sangue_txt     = sangueTxt,
            fdv_txt        = fdvTxt,
            vitalidade_txt = vitalidadeTxt,
            moralidade_txt = moralidadeTxt,
            flags_txt      = table.concat(flags, " "),
            hasPendingXP   = hasPendingXP,
            isVampire      = isVamp,
            isGhoul        = isGhoul,
            visible        = visible,
            nodeRef        = char.nodeRef or char.sheet,
        })
    end

    return {
        cards      = cards,
        page       = curPage,
        totalPages = totalPages,
        totalCount = totalCount,
    }
end

return CoterieTracker
