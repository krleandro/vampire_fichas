local V20 = require("Core.v20_init")

local Bridge = {}

local function safeNum(val, default)
    local n = tonumber(val)
    if n == nil or n ~= n or n == math.huge or n == -math.huge then
        return default
    end
    return n
end

local function safeInt(val, default)
    return math.floor(safeNum(val, default or 0))
end

local function safeNonNegInt(val, default)
    return math.max(0, safeInt(val, default or 0))
end

local GEN15_CHANNEL_NOTE = "(15ª Geração: 2 pts de vitae canalizados em 2 turnos)"

local function isTrue(val)
    return val == true or val == "true" or val == 1 or val == "1"
end

local function isFalse(val)
    return val == false or val == "false"
end

local function normalizeOptsAndApis(opts, firecastApi, dialogsApi)
    if type(opts) == "table" and (opts.getMesaDe ~= nil or opts.interpretarRolagem ~= nil) then
        dialogsApi = firecastApi
        firecastApi = opts
        opts = {}
    end
    return opts or {}, firecastApi, dialogsApi
end

local function getFirecastAndDialogs(firecastApi, dialogsApi)
    local fc = firecastApi or _G.Firecast
    local dlg = dialogsApi or _G.Dialogs or { showMessage = _G.showMessage or function() end }
    if type(dlg.showMessage) ~= "function" then
        dlg = { showMessage = _G.showMessage or function() end }
    end
    return fc, dlg
end

local function buildKnownBuffLookup()
    local map = {}
    for _, discId in ipairs(V20.DisciplinesCatalog.ORDER) do
        local cat = V20.DisciplinesCatalog.DISCIPLINES[discId]
        if cat and cat.powers then
            for _, pw in ipairs(cat.powers) do
                if pw.toggleBuff and pw.toggleBuff.id then
                    map[pw.toggleBuff.id] = pw.toggleBuff
                end
            end
        end
    end
    return map
end

local KNOWN_BUFFS = buildKnownBuffLookup()
local BUFF_CACHE = setmetatable({}, { __mode = "k" })

function Bridge.deserializeBuffs(sheet)
    local out = {}
    if type(sheet) ~= "table" then return out end
    local cached = BUFF_CACHE[sheet] or (not rawget(sheet, "__nodeFacadeFlag") and rawget(sheet, "_active_buffs_tbl") or nil)
    if type(cached) == "table" then
        for k, v in pairs(cached) do
            if v then out[k] = (type(v) == "table") and v or (KNOWN_BUFFS[k] or { id = k }) end
        end
    end
    if type(sheet.buffs_ativos_csv) == "string" and sheet.buffs_ativos_csv ~= "" then
        for token in sheet.buffs_ativos_csv:gmatch("[^,%s]+") do
            if KNOWN_BUFFS[token] then
                out[token] = KNOWN_BUFFS[token]
            elseif out[token] == nil then
                out[token] = { id = token }
            end
        end
    end
    for bid, bdef in pairs(KNOWN_BUFFS) do
        if isTrue(sheet["buff_toggle_" .. bid]) then
            out[bid] = bdef
        end
    end
    return out
end

function Bridge.serializeBuffs(sheet, activeBuffs)
    if type(sheet) ~= "table" then return end
    local copy = {}
    local ids = {}
    for k, v in pairs(activeBuffs or {}) do
        if v then
            copy[k] = v
            table.insert(ids, tostring(k))
        end
    end
    table.sort(ids)
    BUFF_CACHE[sheet] = copy
    if not rawget(sheet, "__nodeFacadeFlag") then
        rawset(sheet, "_active_buffs_tbl", copy)
    end
    sheet.buffs_ativos_csv = table.concat(ids, ",")
    for bid, _ in pairs(KNOWN_BUFFS) do
        if sheet["buff_toggle_" .. bid] ~= nil then
            sheet["buff_toggle_" .. bid] = (copy[bid] ~= nil)
        end
    end
end

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
    local facesStr = table.concat(faces or {}, ", ")
    local statusTag = "FALHA SIMPLES"
    if evalRes.outcome == "botch" then
        statusTag = "💀 FALHA CRÍTICA (BOTCH)!"
    elseif evalRes.outcome == "success" then
        statusTag = string.format("🩸 %d Sucesso(s) — %s!", evalRes.totalSuccesses, evalRes.degree)
    end
    local msg = string.format(
        "[%s] %s | Dif %d | Dados [%s] -> %s",
        actorName or "Personagem",
        label or "Teste V20",
        evalRes.difficulty,
        facesStr,
        statusTag
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

function Bridge.getCurrentLogin(sheet, firecastApi)
    local fc = firecastApi or _G.Firecast
    if fc and fc.getMesaDe then
        local mesa = fc.getMesaDe(sheet)
        if mesa and mesa.meuJogador and mesa.meuJogador.login and mesa.meuJogador.login ~= "" then
            return tostring(mesa.meuJogador.login)
        end
    end
    if type(sheet) == "table" and type(sheet.jogador) == "string" and sheet.jogador ~= "" then
        return sheet.jogador
    end
    return "Local"
end

function Bridge.notify(sheet, msg, firecastApi, dialogsApi)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    local mesa = (fc and fc.getMesaDe) and fc.getMesaDe(sheet) or nil
    if mesa ~= nil and mesa.activeChat ~= nil and mesa.activeChat.enviarMensagem ~= nil then
        mesa.activeChat:enviarMensagem(msg)
    else
        dlg.showMessage(msg)
    end
    return msg
end

function Bridge.isVampireSheet(sheet)
    if type(sheet) ~= "table" then return true end
    if isFalse(sheet.is_vampire) then return false end
    if sheet.mortal_sobrenatural_modo ~= nil and sheet.mortal_sobrenatural_modo ~= "" then
        return false
    end
    return true
end

function Bridge.collectBackgrounds(sheet, ndbApi)
    local list = {}
    if type(sheet) ~= "table" then return list end
    local ndb = ndbApi or _G.NDB

    for _, bgId in ipairs(V20.BackgroundsCatalog.ORDER) do
        local dots = safeInt(sheet["bg_" .. bgId], 0)
        if dots > 0 then
            table.insert(list, { bg_id = bgId, nivel = dots, ativo = true })
        end
    end

    if ndb and ndb.getChildNodes and sheet.rclAntecedentes_node then
        local children = ndb.getChildNodes(sheet.rclAntecedentes_node) or {}
        for _, ch in ipairs(children) do
            if type(ch) == "table" then
                table.insert(list, ch)
            end
        end
    end

    if type(sheet.backgrounds_list) == "table" then
        for _, ch in ipairs(sheet.backgrounds_list) do
            if type(ch) == "table" then
                table.insert(list, ch)
            end
        end
    end

    return list
end

function Bridge.collectDisciplines(sheet, ndbApi)
    local byId = {}
    local ordered = {}
    if type(sheet) ~= "table" then return ordered end
    local ndb = ndbApi or _G.NDB

    local function upsert(discId, lvl, cat, activeAuto)
        if type(discId) ~= "string" or discId == "" then return end
        local n = math.max(0, safeInt(lvl, 0))
        if n <= 0 then return end
        local existing = byId[discId]
        if not existing then
            existing = {
                disc_id = discId,
                nivel = n,
                categoria_custo = cat,
                activeAuto = isTrue(activeAuto),
            }
            byId[discId] = existing
            table.insert(ordered, existing)
        else
            if n > existing.nivel then existing.nivel = n end
            if cat and not existing.categoria_custo then existing.categoria_custo = cat end
            if isTrue(activeAuto) then existing.activeAuto = true end
        end
    end

    for i = 1, 9 do
        local sid = sheet["disc_slot" .. i .. "_id"]
        local slvl = safeInt(sheet["disc_slot" .. i .. "_nivel"], 0)
        if isTrue(sheet.isGhoul) and sid == "potence" then
            slvl = math.max(slvl, safeInt(sheet.ghoulPotence, 0))
        end
        local scat = sheet["disc_slot" .. i .. "_cat"]
        local sauto = sheet["disc_slot" .. i .. "_auto"]
        upsert(sid, slvl, scat, sauto)
    end

    for _, discId in ipairs(V20.DisciplinesCatalog.ORDER) do
        local directLvl = sheet["disc_" .. discId]
        if directLvl ~= nil then
            upsert(discId, directLvl, nil, false)
        end
    end

    if ndb and ndb.getChildNodes and sheet.rclDisciplinas_node then
        local children = ndb.getChildNodes(sheet.rclDisciplinas_node) or {}
        for _, ch in ipairs(children) do
            if type(ch) == "table" then
                upsert(ch.disc_id, ch.nivel, ch.categoria_custo, ch.ativa_turno or ch.activeAuto)
            end
        end
    end

    if type(sheet.disciplines_list) == "table" then
        for _, ch in ipairs(sheet.disciplines_list) do
            if type(ch) == "table" then
                upsert(ch.disc_id, ch.nivel, ch.categoria_custo, ch.ativa_turno or ch.activeAuto)
            end
        end
    end

    return ordered
end

local function getDisciplineDots(sheet, discId, ndbApi)
    local best = 0
    for _, d in ipairs(Bridge.collectDisciplines(sheet, ndbApi)) do
        if d.disc_id == discId and safeNonNegInt(d.nivel, 0) > best then
            best = safeNonNegInt(d.nivel, 0)
        end
    end
    return best
end

local function resolveSecondaryTradition(sheet, idx)
    local rawTrad = (type(sheet) == "table") and sheet["bm_sec" .. idx .. "_disc"] or nil
    local pid = (type(sheet) == "table") and (sheet["bm_sec" .. idx .. "_path_id"] or "") or ""
    if pid ~= "" then
        if V20.BloodMagicCatalog.THAUMATURGY_PATHS[pid] ~= nil then
            return "thaumaturgy"
        elseif V20.BloodMagicCatalog.NECROMANCY_PATHS[pid] ~= nil then
            return "necromancy"
        end
    end
    if rawTrad == "necromancy" or rawTrad == "thaumaturgy" then
        return rawTrad
    end
    return (type(sheet) == "table" and sheet.cla_id == "giovanni") and "necromancy" or "thaumaturgy"
end

function Bridge.hasBloodMagicAccess(sheet, ndbApi)
    if type(sheet) ~= "table" or not Bridge.isVampireSheet(sheet) then
        return false
    end
    local discList = {}
    for _, d in ipairs(Bridge.collectDisciplines(sheet, ndbApi)) do
        table.insert(discList, d)
    end
    for i = 1, 9 do
        local sid = sheet["disc_slot" .. i .. "_id"]
        if sid == "thaumaturgy" or sid == "necromancy" then
            table.insert(discList, {
                disc_id = sid,
                nivel = safeNonNegInt(sheet["disc_slot" .. i .. "_nivel"], 0),
                selected = true,
            })
        end
    end
    local ritualsDots = safeNonNegInt(sheet.bg_rituals, 0)
    for _, b in ipairs(Bridge.collectBackgrounds(sheet, ndbApi)) do
        if b.bg_id == "rituals" and safeNonNegInt(b.nivel, 0) > ritualsDots then
            ritualsDots = safeNonNegInt(b.nivel, 0)
        end
    end
    return V20.BloodMagicEngine.hasBloodMagicAccess(sheet.cla_id, discList, ritualsDots)
end

function Bridge.collectMeritsFlaws(sheet, ndbApi)
    local list = {}
    local seenIds = {}
    if type(sheet) ~= "table" then return list end
    local ndb = ndbApi or _G.NDB

    for i = 1, 6 do
        local itemId = sheet["mf_slot" .. i .. "_id"]
        local customName = sheet["mf_slot" .. i .. "_nome"]
        local pts = sheet["mf_slot" .. i .. "_pontos"]
        local ativo = sheet["mf_slot" .. i .. "_ativo"]
        if not isFalse(ativo) then
            local cat = (type(itemId) == "string" and itemId ~= "" and itemId ~= "custom")
                and V20.MeritsFlawsCatalog.ITEMS[itemId] or nil
            if cat ~= nil then
                seenIds[itemId] = true
                local overridePts = safeInt(pts, 0)
                table.insert(list, {
                    item_id = itemId,
                    tipo = cat.tipo,
                    pontos = (overridePts > 0) and overridePts or cat.pontos,
                    mod_tipo = sheet["mf_slot" .. i .. "_mod"],
                    ativo = true,
                })
            elseif type(itemId) == "string" and itemId ~= "" and itemId ~= "custom" then
                seenIds[itemId] = true
                local overridePts = safeInt(pts, 0)
                table.insert(list, {
                    item_id = itemId,
                    tipo = sheet["mf_slot" .. i .. "_tipo"],
                    pontos = (overridePts > 0) and overridePts or nil,
                    mod_tipo = sheet["mf_slot" .. i .. "_mod"],
                    ativo = true,
                })
            elseif (itemId == "custom" or (type(customName) == "string" and customName ~= "")) and safeInt(pts, 0) > 0 then
                table.insert(list, {
                    nome = (type(customName) == "string" and customName ~= "") and customName or "Custom",
                    tipo = sheet["mf_slot" .. i .. "_tipo"] or "qualidade",
                    pontos = safeInt(pts, 0),
                    mod_tipo = sheet["mf_slot" .. i .. "_mod"],
                    ativo = true,
                })
            end
        end
    end

    for _, mfId in ipairs(V20.MeritsFlawsCatalog.ORDER) do
        if isTrue(sheet["mf_" .. mfId]) and not seenIds[mfId] then
            seenIds[mfId] = true
            table.insert(list, { item_id = mfId, ativo = true })
        end
    end

    if ndb and ndb.getChildNodes and sheet.rclQualidadesDefeitos_node then
        local children = ndb.getChildNodes(sheet.rclQualidadesDefeitos_node) or {}
        for _, ch in ipairs(children) do
            if type(ch) == "table" then
                table.insert(list, ch)
            end
        end
    end

    if type(sheet.merits_flaws_list) == "table" then
        for _, ch in ipairs(sheet.merits_flaws_list) do
            if type(ch) == "table" then
                table.insert(list, ch)
            end
        end
    end

    return list
end

function Bridge.sheetToEngineState(sheet)
    sheet = sheet or {}
    return {
        isVampire = Bridge.isVampireSheet(sheet),
        isGhoul = isTrue(sheet.isGhoul) or (sheet.mortal_sobrenatural_modo == "carnical"),
        cla_id = sheet.cla_id,
        generation = safeInt(sheet.geracao, 13),
        currentBlood = safeInt(sheet.sangue_atual, 0),
        spentThisTurn = safeInt(sheet.sangue_gasto_turno, 0),
        thinBloodUsed = safeInt(sheet.sangue_fraco_usado, 0),
        fdv_perm = safeInt(sheet.fdv_perm, 1),
        fdv_temp = safeInt(sheet.fdv_temp, 0),
        attr_forca = safeInt(sheet.attr_forca, 1),
        attr_destreza = safeInt(sheet.attr_destreza, 1),
        attr_vigor = safeInt(sheet.attr_vigor, 1),
        buff_forca = safeInt(sheet.buff_forca, 0),
        buff_destreza = safeInt(sheet.buff_destreza, 0),
        buff_vigor = safeInt(sheet.buff_vigor, 0),
        ghoulPotence = safeInt(sheet.ghoulPotence, 0),
        activePotenceAuto = isTrue(sheet.potencia_ativa_turno),
        activeCelerityActions = safeInt(sheet.rapidez_acoes_ativas, 0),
        activeBuffs = Bridge.deserializeBuffs(sheet),
    }
end

function Bridge.resolvePoolTrait(sheet, traitId, combatMods)
    if type(traitId) ~= "string" or traitId == "" or traitId == "none" then
        return { val = 0, label = nil, category = nil, isVirtual = false }
    end

    -- Referências virtuais exigidas pelo catálogo de Disciplinas / Numina (PF-3)
    if traitId == "attr_fdv_ref" then
        return {
            val = safeInt(sheet.fdv_perm, 1),
            label = "Força de Vontade",
            category = nil,
            isVirtual = true,
        }
    elseif traitId == "hab_autocontrole_ref" then
        return {
            val = safeInt(sheet.virtude2_val, 1),
            label = (sheet.virtude2_tipo == "instinto") and "Instinto" or "Autocontrole",
            category = nil,
            isVirtual = true,
        }
    elseif traitId == "hab_coragem_ref" then
        return {
            val = safeInt(sheet.virtude3_val, 1),
            label = "Coragem",
            category = nil,
            isVirtual = true,
        }
    elseif traitId == "hab_consciencia_ref" then
        return {
            val = safeInt(sheet.virtude1_val, 1),
            label = (sheet.virtude1_tipo == "conviccao") and "Convicção" or "Consciência",
            category = nil,
            isVirtual = true,
        }
    end

    local attrMeta = V20.Traits.ATTRIBUTES[traitId]
    if attrMeta then
        local defaultBase = (sheet.cla_id == "nosferatu" and traitId == "attr_aparencia") and 0 or 1
        local val = (sheet[traitId] ~= nil) and safeInt(sheet[traitId], defaultBase) or defaultBase
        local sceneMods = (combatMods and combatMods.sceneAttrMods) or {}
        if traitId == "attr_forca" then
            val = val + safeInt(sheet.buff_forca, 0) + safeInt(sceneMods.forca, 0)
        elseif traitId == "attr_destreza" then
            val = val + safeInt(sheet.buff_destreza, 0) + safeInt(sceneMods.destreza, 0)
        elseif traitId == "attr_vigor" then
            val = val + safeInt(sheet.buff_vigor, 0) + safeInt(sceneMods.vigor, 0)
        end
        if sheet.cla_id == "nosferatu" and traitId == "attr_aparencia" then
            local activeBuffs = Bridge.deserializeBuffs(sheet)
            val = (activeBuffs.obf_mask ~= nil) and math.max(1, val) or 0
        end
        return { val = val, label = attrMeta.name, category = nil, isVirtual = false }
    end

    local habMeta = V20.Traits.ABILITIES[traitId]
    if habMeta then
        return {
            val = safeInt(sheet[traitId], 0),
            label = habMeta.name,
            category = habMeta.category,
            isVirtual = false,
        }
    end

    local bgKey = traitId:match("^bg_(.+)$") or traitId
    local bgMeta = V20.BackgroundsCatalog.BACKGROUNDS[bgKey]
    if bgMeta then
        return {
            val = safeInt(sheet["bg_" .. bgKey], 0),
            label = bgMeta.name,
            category = nil,
            isVirtual = false,
        }
    end

    return {
        val = safeInt(sheet[traitId], 0),
        label = traitId,
        category = nil,
        isVirtual = false,
    }
end

local SYNC_IN_PROGRESS = setmetatable({}, { __mode = "k" })
local HUGE_FROM_MF = setmetatable({}, { __mode = "k" })
local LAST_AGG_MIRROR = setmetatable({}, { __mode = "k" })

local function setIfChanged(sheet, key, val)
    if sheet[key] ~= val then
        sheet[key] = val
    end
end

local function resolveMirroredAggravated(sheet)
    local prevAgg = LAST_AGG_MIRROR[sheet]
    local rawAggrav = (sheet.dano_aggravado ~= nil) and safeNonNegInt(sheet.dano_aggravado, 0) or nil
    local rawAgrav = (sheet.dano_agravado ~= nil) and safeNonNegInt(sheet.dano_agravado, 0) or nil
    local agg = 0
    if rawAggrav ~= nil and rawAgrav ~= nil then
        if prevAgg ~= nil then
            if rawAggrav ~= prevAgg then
                agg = rawAggrav
            elseif rawAgrav ~= prevAgg then
                agg = rawAgrav
            else
                agg = rawAggrav
            end
        else
            agg = (rawAggrav ~= 0) and rawAggrav or rawAgrav
        end
    elseif rawAggrav ~= nil then
        agg = rawAggrav
    elseif rawAgrav ~= nil then
        agg = rawAgrav
    end
    LAST_AGG_MIRROR[sheet] = agg
    setIfChanged(sheet, "dano_aggravado", agg)
    setIfChanged(sheet, "dano_agravado", agg)
    return agg
end

local function updateDisciplineSummaries(sheet)
    local isVamp = Bridge.isVampireSheet(sheet)
    for i = 1, 9 do
        local did = sheet["disc_slot" .. i .. "_id"]
        local dots = safeInt(sheet["disc_slot" .. i .. "_nivel"], 0)
        if isTrue(sheet.isGhoul) and did == "potence" then
            dots = math.max(dots, safeInt(sheet.ghoulPotence, 0))
        end
        local pwrLvl = math.max(1, math.min(5, safeInt(sheet["disc_slot" .. i .. "_pwr_lvl"], 1)))
        if isVamp and (did == "thaumaturgy" or did == "necromancy") then
            local primId = (did == "necromancy")
                and ((type(sheet.bm_necro_prim_id) == "string" and sheet.bm_necro_prim_id ~= "") and sheet.bm_necro_prim_id or "sepulchre_path")
                or ((type(sheet.bm_thau_prim_id) == "string" and sheet.bm_thau_prim_id ~= "") and sheet.bm_thau_prim_id or "path_of_blood")
            local effDots = math.max(dots, V20.BloodMagicEngine.derivePrimaryPathLevel(getDisciplineDots(sheet, did)))
            local pathTbl = V20.BloodMagicEngine.getPathTable(did, primId)
            if pathTbl and pathTbl.powers and pathTbl.powers[pwrLvl] then
                local pw = pathTbl.powers[pwrLvl]
                local lockPrefix = (effDots < pw.level) and string.format("[Requer Nv %d] ", pw.level) or ""
                setIfChanged(sheet, "disc_slot" .. i .. "_resumo", string.format(
                    "%s%s — %s (Nv %d) — %s | %s",
                    lockPrefix, pathTbl.name, pw.name, pw.level, pw.diffHint or "Dif 6", pw.summary or ""
                ))
            else
                setIfChanged(sheet, "disc_slot" .. i .. "_resumo", "Selecione uma Disciplina V20 para inspecionar e ativar poderes.")
            end
        else
            local cat = (type(did) == "string") and V20.DisciplinesCatalog.DISCIPLINES[did] or nil
            if cat and cat.powers and cat.powers[pwrLvl] then
                local pw = cat.powers[pwrLvl]
                local lockPrefix = (dots < pw.level) and string.format("[Requer Nv %d] ", pw.level) or ""
                setIfChanged(sheet, "disc_slot" .. i .. "_resumo", string.format(
                    "%s%s (Nv %d) — %s | %s",
                    lockPrefix, pw.name, pw.level, pw.diffHint or "Dif 6", pw.summary or ""
                ))
            else
                setIfChanged(sheet, "disc_slot" .. i .. "_resumo", "Selecione uma Disciplina V20 para inspecionar e ativar poderes.")
            end
        end
    end

    local inspectId = sheet.disc_catalogo_id
    if type(inspectId) == "string" and V20.DisciplinesCatalog.DISCIPLINES[inspectId] then
        local cat = V20.DisciplinesCatalog.DISCIPLINES[inspectId]
        local lines = { cat.name .. ":" }
        for _, pw in ipairs(cat.powers) do
            table.insert(lines, string.format("Nv %d - %s (%s): %s", pw.level, pw.name, pw.diffHint or "Dif 6", pw.summary or ""))
        end
        setIfChanged(sheet, "disc_catalogo_resumo", table.concat(lines, " || "))
    end
end

local function updateBloodMagicSummaries(sheet, ndb)
    if not Bridge.isVampireSheet(sheet) then return end

    local thauDots = getDisciplineDots(sheet, "thaumaturgy", ndb)
    local necroDots = getDisciplineDots(sheet, "necromancy", ndb)
    local thauPrimLvl = V20.BloodMagicEngine.derivePrimaryPathLevel(thauDots)
    local necroPrimLvl = V20.BloodMagicEngine.derivePrimaryPathLevel(necroDots)
    setIfChanged(sheet, "bm_thau_prim_nivel", thauPrimLvl)
    setIfChanged(sheet, "bm_necro_prim_nivel", necroPrimLvl)

    local thauPrimId = (type(sheet.bm_thau_prim_id) == "string" and sheet.bm_thau_prim_id ~= "") and sheet.bm_thau_prim_id or "path_of_blood"
    local thauPwrLvl = math.max(1, math.min(5, safeInt(sheet.bm_thau_prim_pwr_lvl, 1)))
    local thauPath = V20.BloodMagicEngine.getPathTable("thaumaturgy", thauPrimId)
    if thauPath and thauPath.powers and thauPath.powers[thauPwrLvl] then
        local pw = thauPath.powers[thauPwrLvl]
        local lockPfx = (thauPrimLvl < pw.level) and string.format("[Requer Nv %d] ", pw.level) or ""
        setIfChanged(sheet, "bm_thau_prim_resumo", string.format("%s%s — %s (Nv %d) | %s | %s", lockPfx, thauPath.name, pw.name, pw.level, pw.diffHint or "", pw.summary or ""))
    else
        setIfChanged(sheet, "bm_thau_prim_resumo", "Selecione a Linha Primária de Taumaturgia.")
    end

    local necroPrimId = (type(sheet.bm_necro_prim_id) == "string" and sheet.bm_necro_prim_id ~= "") and sheet.bm_necro_prim_id or "sepulchre_path"
    local necroPwrLvl = math.max(1, math.min(5, safeInt(sheet.bm_necro_prim_pwr_lvl, 1)))
    local necroPath = V20.BloodMagicEngine.getPathTable("necromancy", necroPrimId)
    if necroPath and necroPath.powers and necroPath.powers[necroPwrLvl] then
        local pw = necroPath.powers[necroPwrLvl]
        local lockPfx = (necroPrimLvl < pw.level) and string.format("[Requer Nv %d] ", pw.level) or ""
        setIfChanged(sheet, "bm_necro_prim_resumo", string.format("%s%s — %s (Nv %d) | %s | %s", lockPfx, necroPath.name, pw.name, pw.level, pw.diffHint or "", pw.summary or ""))
    else
        setIfChanged(sheet, "bm_necro_prim_resumo", "Selecione a Linha Primária de Necromancia.")
    end

    for i = 1, 4 do
        local trad = resolveSecondaryTradition(sheet, i)
        local pid = sheet["bm_sec" .. i .. "_path_id"] or ""
        local dots = safeNonNegInt(sheet["bm_sec" .. i .. "_nivel"], 0)
        local pwrLvl = math.max(1, math.min(5, safeInt(sheet["bm_sec" .. i .. "_pwr_lvl"], 1)))
        local pTable = (pid ~= "") and V20.BloodMagicEngine.getPathTable(trad, pid) or nil
        if pTable and pTable.powers and pTable.powers[pwrLvl] then
            local pw = pTable.powers[pwrLvl]
            local lockPfx = (dots < pw.level) and string.format("[Requer Nv %d] ", pw.level) or ""
            setIfChanged(sheet, "bm_sec" .. i .. "_resumo", string.format("%s%s (Nv %d) — %s | %s", lockPfx, pw.name, pw.level, pw.diffHint or "", pw.summary or ""))
        else
            setIfChanged(sheet, "bm_sec" .. i .. "_resumo", "Selecione uma Linha Secundária V20 (Nova: 7 XP | Evolução: Atual x4 XP).")
        end
    end

    local ritId = (type(sheet.bm_ritual_id) == "string" and sheet.bm_ritual_id ~= "") and sheet.bm_ritual_id or "thau_rit_1_sacred_haven"
    local rit = V20.BloodMagicCatalog.RITUALS[ritId]
    if rit then
        local tradName = (rit.tradition == "necromancy") and "Necromancia" or "Taumaturgia"
        setIfChanged(sheet, "bm_ritual_catalogo_resumo", string.format(
            "[%s Nv %d | Dif %d | Sangue: %d, FdV: %d] %s — %s",
            tradName, rit.level, rit.defaultDiff, safeNonNegInt(rit.cost and rit.cost.blood, 0), safeNonNegInt(rit.cost and rit.cost.willpower, 0), rit.name, rit.summary or ""
        ))
    else
        setIfChanged(sheet, "bm_ritual_catalogo_resumo", "Selecione um ritual oficial do catálogo V20.")
    end
end

local function syncDerivedFieldsImpl(sheet, ndbApi)
    local ndb = ndbApi or _G.NDB

    local bgList = Bridge.collectBackgrounds(sheet, ndb)
    local mfList = Bridge.collectMeritsFlaws(sheet, ndb)
    local mfAgg = V20.BackgroundsEngine.aggregateMeritsFlaws(mfList)
    local fx = V20.BackgroundsEngine.deriveSheetEffects(sheet.geracao_base or 13, bgList)

    local isVamp = Bridge.isVampireSheet(sheet)
    if isVamp then
        local gen = tonumber(sheet.geracao_override) or mfAgg.thinBloodGenOverride or fx.effectiveGeneration
        setIfChanged(sheet, "geracao", gen)
        local stats = V20.Blood.deriveStats(gen)
        setIfChanged(sheet, "sangue_max", stats.bloodMax)
        setIfChanged(sheet, "sangue_usavel_max", stats.usableBlood)
        setIfChanged(sheet, "sangue_por_turno", stats.perTurn)
        setIfChanged(sheet, "atributo_max_geracao", stats.traitMax)
        setIfChanged(sheet, "disciplina_max_geracao", stats.discMax)
        setIfChanged(sheet, "isGhoul", false)
        setIfChanged(sheet, "hasNumina", false)
        setIfChanged(sheet, "ghoulPotence", 0)
    else
        local mSt = V20.Creation.applyMortalSupernaturalMode({}, sheet.mortal_sobrenatural_modo or "humano")
        setIfChanged(sheet, "mortal_sobrenatural_modo", mSt.mortal_sobrenatural_modo)
        setIfChanged(sheet, "isGhoul", mSt.isGhoul)
        setIfChanged(sheet, "hasNumina", mSt.hasNumina)
        setIfChanged(sheet, "sangue_max", mSt.sangue_max or 0)
        setIfChanged(sheet, "sangue_usavel_max", mSt.sangue_max or 0)
        setIfChanged(sheet, "sangue_por_turno", mSt.sangue_por_turno or 0)
        setIfChanged(sheet, "ghoulPotence", mSt.ghoulPotence or 0)
        setIfChanged(sheet, "atributo_max_geracao", 5)
        setIfChanged(sheet, "disciplina_max_geracao", mSt.isGhoul and math.max(1, safeInt(sheet.carnical_disc_max, 1)) or 0)
    end

    setIfChanged(sheet, "rebanho_recipientes", fx.herdVessels)
    setIfChanged(sheet, "caca_bonus_dados", fx.huntingBonusDice)
    setIfChanged(sheet, "caca_mod_dif", fx.huntingDiffMod)
    setIfChanged(sheet, "recursos_faixa", fx.resourcesLabel)
    setIfChanged(sheet, "fama_mod_dif", fx.fameSocialDiffMod)
    setIfChanged(sheet, "status_bonus_dados", fx.statusSocialBonusDice)
    setIfChanged(sheet, "qualidades_total", mfAgg.totalMeritCost)
    setIfChanged(sheet, "defeitos_bonus", mfAgg.effectiveFlawBonus)
    setIfChanged(sheet, "percepcao_mod_qualidades", mfAgg.perceptionDiffMod)
    setIfChanged(sheet, "tem_disc_adicional", mfAgg.hasAdditionalDisc)

    if mfAgg.hugeSize then
        if not isTrue(sheet.tem_tamanho_grande) then
            HUGE_FROM_MF[sheet] = true
        end
        setIfChanged(sheet, "tem_tamanho_grande", true)
    elseif HUGE_FROM_MF[sheet] then
        HUGE_FROM_MF[sheet] = nil
        setIfChanged(sheet, "tem_tamanho_grande", false)
    end

    local huge = isTrue(sheet.tem_tamanho_grande) or mfAgg.hugeSize
    local aggMirrored = resolveMirroredAggravated(sheet)
    local hStatus = V20.Health.getStatus({
        isVampire = isVamp,
        hugeSize = huge,
        bashing = sheet.dano_contundente,
        lethal = sheet.dano_letal,
        aggravated = aggMirrored,
    })
    setIfChanged(sheet, "vitalidade_resumo", hStatus.currentLevelName)
    setIfChanged(sheet, "vitalidade_label", hStatus.currentLevelName)
    setIfChanged(sheet, "penalidade_ferimento", hStatus.penalty)
    setIfChanged(sheet, "incapacitado", hStatus.incapacitated)
    setIfChanged(sheet, "vitalidade_alerta", hStatus.torporOrDeath or "")

    local function fmtBox(sym)
        if sym == nil then return "-" end
        if sym == "" then return "[ ]" end
        return "[" .. sym .. "]"
    end

    local boxTokens = {}
    if huge then
        local b0 = fmtBox(hStatus.boxes[1])
        setIfChanged(sheet, "health_box_0", b0)
        table.insert(boxTokens, b0)
        for i = 1, 7 do
            local bi = fmtBox(hStatus.boxes[i + 1])
            setIfChanged(sheet, "health_box_" .. i, bi)
            table.insert(boxTokens, bi)
        end
    else
        setIfChanged(sheet, "health_box_0", "-")
        for i = 1, 7 do
            local bi = fmtBox(hStatus.boxes[i])
            setIfChanged(sheet, "health_box_" .. i, bi)
            table.insert(boxTokens, bi)
        end
    end
    setIfChanged(sheet, "vitalidade_trilha_visual", table.concat(boxTokens, " "))

    if type(sheet.moralidade_tipo) == "string" then
        for _, p in ipairs(V20.MoralityCatalog.PATHS) do
            if p.id == sheet.moralidade_tipo then
                setIfChanged(sheet, "moralidade_nome", p.name)
                break
            end
        end
    end

    local aura = V20.WillpowerMorality.getAuraModifier(sheet.moralidade_val or 7)
    setIfChanged(sheet, "aura_resumo", aura.label)
    setIfChanged(sheet, "aura_label", aura.label)
    setIfChanged(sheet, "aura_mod_dif", aura.diffMod)

    setIfChanged(sheet, "xp_disponivel", safeNonNegInt(sheet.xp_total, 0) - safeNonNegInt(sheet.xp_gasto, 0))

    local discList = Bridge.collectDisciplines(sheet, ndb)
    local cMods = V20.DisciplinesEngine.computeCombatModifiers(Bridge.sheetToEngineState(sheet), discList)
    setIfChanged(sheet, "fortitude_absorcao_dados", cMods.fortitudeSoak)
    setIfChanged(sheet, "potencia_dados_passivos", cMods.passivePotenceDice)
    setIfChanged(sheet, "potencia_sucessos_ativos", cMods.activePotenceAuto)
    setIfChanged(sheet, "rapidez_dados_passivos", cMods.passiveCelerityDice)
    if sheet.rapidez_acoes_extras == nil then
        setIfChanged(sheet, "rapidez_acoes_extras", cMods.activeCelerityActions)
    else
        setIfChanged(sheet, "rapidez_acoes_extras", safeNonNegInt(sheet.rapidez_acoes_extras, 0))
    end

    local mId = (type(sheet.cmb_manobra_id) == "string" and sheet.cmb_manobra_id ~= "") and sheet.cmb_manobra_id or "strike"
    local mSpec = V20.CombatManeuversCatalog.MANEUVERS[mId]
    if mSpec then
        setIfChanged(sheet, "cmb_manobra_resumo", string.format("%s (%s) — %s", mSpec.name, mSpec.page, mSpec.summary))
    end

    local activeIds = {}
    for k, _ in pairs(Bridge.deserializeBuffs(sheet)) do
        table.insert(activeIds, k)
    end
    table.sort(activeIds)
    if isTrue(sheet.potencia_ativa_turno) then
        table.insert(activeIds, 1, "potence_auto")
    end
    if safeInt(sheet.rapidez_acoes_ativas, 0) > 0 then
        table.insert(activeIds, 1, "celerity_x" .. tostring(safeInt(sheet.rapidez_acoes_ativas, 0)))
    end
    setIfChanged(sheet, "buffs_cena_resumo", (#activeIds > 0) and table.concat(activeIds, ", ") or "Nenhum buff ativo")

    updateDisciplineSummaries(sheet)
    updateBloodMagicSummaries(sheet, ndb)

    if isVamp then
        local trGoles = math.min(2, safeNonNegInt(sheet.tremere_laco_goles, 0))
        local regente = (type(sheet.tremere_regente_nome) == "string" and sheet.tremere_regente_nome ~= "")
            and (" [" .. sheet.tremere_regente_nome .. "]") or ""
        local trStatus = "Sem Laço (0/2 goles)"
        if trGoles >= 2 then
            trStatus = "Laço de Sangue Completo (2/2 — Maldição Tremere)" .. regente
        elseif trGoles == 1 then
            trStatus = "1º Gole (1/2 — Início de Laço)" .. regente
        end
        setIfChanged(sheet, "tremere_laco_status", trStatus)
    end

    -- Atualiza resumo vivo do montador de rolagem no rodapé (incluindo modificadores de fraqueza de clã)
    local rAttrId = sheet.roll_attr_id or "attr_percepcao"
    local rHabId = (sheet.roll_hab_id ~= "" and sheet.roll_hab_id ~= "none") and sheet.roll_hab_id or nil
    local rAttr = Bridge.resolvePoolTrait(sheet, rAttrId, cMods)
    local rHab = Bridge.resolvePoolTrait(sheet, rHabId, cMods)
    local wPen = (isTrue(sheet.roll_ignorar_ferimento) or isTrue(sheet.em_frenesi)) and 0 or math.abs(safeInt(sheet.penalidade_ferimento, 0))
    local extra = safeInt(sheet.roll_bonus_dice, 0)
    if (rAttrId == "attr_forca") then extra = extra + cMods.passivePotenceDice end
    if (rAttrId == "attr_destreza") then extra = extra + cMods.passiveCelerityDice end
    if isTrue(sheet.roll_usar_status) then extra = extra + safeInt(sheet.status_bonus_dados, 0) end

    local stOverridePreview = isTrue(sheet.narrador_override) and Bridge.isStoryteller(sheet)
    local cwPreview = isVamp and V20.ClanWeaknesses.computeRollModifiers({
        cla_id = sheet.cla_id,
        attrId = rAttrId,
        habId = rHabId,
        activeBuffs = Bridge.deserializeBuffs(sheet),
        setita_luz_forte = sheet.setita_luz_forte,
        lasombra_vigiado_espelhos = sheet.lasombra_vigiado_espelhos,
        caitiff_estigma_ativo = sheet.caitiff_estigma_ativo,
        tzimisce_dias_sem_terra = sheet.tzimisce_dias_sem_terra,
        storytellerOverride = stOverridePreview,
    }) or { blocked = false, bonusDiceMod = 0, diffMod = 0, poolDivisor = 1 }

    extra = extra + safeInt(cwPreview.bonusDiceMod, 0)
    local previewDiffMod = safeInt(cwPreview.diffMod, 0)
    if rAttrId == "attr_percepcao" then
        previewDiffMod = previewDiffMod + cMods.perceptionDiffMod + safeInt(sheet.percepcao_mod_qualidades, 0)
    end
    if isTrue(sheet.roll_usar_fama) then
        previewDiffMod = previewDiffMod + safeInt(sheet.fama_mod_dif, 0)
    end
    local previewDiff = math.max(2, math.min(10, safeInt(sheet.roll_diff, 6) + previewDiffMod))
    local previewPool = math.max(0, rAttr.val + rHab.val + extra - wPen)
    if cwPreview.blocked then
        previewPool = 0
    elseif cwPreview.poolDivisor and cwPreview.poolDivisor > 1 and previewPool >= 1 then
        previewPool = math.max(1, math.floor(previewPool / cwPreview.poolDivisor))
    end
    local habPart = rHab.label and string.format(" + %s (%d)", rHab.label, rHab.val) or ""
    setIfChanged(sheet, "roll_equacao_resumo", string.format(
        "%s (%d)%s + Bônus (%d) - Ferim. (%d) = %dd10 | Dif %d",
        rAttr.label or "Atributo",
        rAttr.val,
        habPart,
        extra,
        wPen,
        previewPool,
        previewDiff
    ))
end

function Bridge.syncDerivedFields(sheet, ndbApi)
    if type(sheet) ~= "table" then return end
    if SYNC_IN_PROGRESS[sheet] then return end
    SYNC_IN_PROGRESS[sheet] = true
    local ok, err = pcall(syncDerivedFieldsImpl, sheet, ndbApi)
    SYNC_IN_PROGRESS[sheet] = nil
    if not ok then
        error(err, 0)
    end
end

function Bridge.selectRollTrait(sheet, kind, traitId)
    if type(sheet) ~= "table" then return end
    if kind == "attr" then
        sheet.roll_attr_id = traitId
    elseif kind == "hab" then
        sheet.roll_hab_id = traitId
    end
    Bridge.syncDerivedFields(sheet)
end

local TEMP_RESOURCE_FIELDS = {
    sangue_atual = true,
    fdv_temp = true,
    dano_contundente = true,
    dano_letal = true,
    dano_aggravado = true,
    dano_agravado = true,
}

local function isTemporaryResourceField(field)
    if type(field) ~= "string" then return false end
    if TEMP_RESOURCE_FIELDS[field] then return true end
    if field:match("^municao_") or field:match("_municao$") then return true end
    return false
end

function Bridge.adjustResource(sheet, field, delta, minVal, maxFieldOrVal, firecastApi, dialogsApi, ndbApi)
    if type(sheet) ~= "table" or type(field) ~= "string" then return { ok = false } end
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet, ndbApi)

    local isTemp = isTemporaryResourceField(field)
    local modo = sheet.modo_ficha or "criacao"
    local isMaster = Bridge.isStoryteller(sheet, fc)
    local stOverride = isTrue(sheet.narrador_override) and isMaster

    if not isTemp then
        if modo == "jogo" and not stOverride then
            local err = "Ficha em Modo Jogo: características permanentes estão bloqueadas. Utilize a Aba 7 (Experiência / XP) para evoluir o personagem."
            dlg.showMessage(err)
            return { ok = false, blocked = true, error = err }
        elseif modo == "narrador_livre" and not isMaster then
            local err = "Apenas o Narrador pode alterar características permanentes no modo Edição Livre."
            dlg.showMessage(err)
            return { ok = false, blocked = true, error = err }
        end
    end

    local cur = safeInt(sheet[field], 0)
    local lo = safeInt(minVal, 0)
    local hi = 99
    if type(maxFieldOrVal) == "string" then
        hi = safeInt(sheet[maxFieldOrVal], 10)
    elseif type(maxFieldOrVal) == "number" then
        hi = safeInt(maxFieldOrVal, 99)
    end
    local nextVal = math.max(lo, math.min(hi, cur + safeInt(delta, 0)))
    if not isTemp and sheet.cla_id == "nosferatu" and field == "attr_aparencia" and not stOverride then
        nextVal = 0
    end
    sheet[field] = nextVal
    if field == "dano_agravado" then
        sheet.dano_aggravado = nextVal
        LAST_AGG_MIRROR[sheet] = nextVal
    elseif field == "dano_aggravado" then
        sheet.dano_agravado = nextVal
        LAST_AGG_MIRROR[sheet] = nextVal
    end
    Bridge.syncDerivedFields(sheet, ndbApi)

    if not isTemp and nextVal ~= cur then
        if modo == "narrador_livre" then
            Bridge.logAudit(
                sheet,
                ndbApi,
                fc,
                "edicao_narrador",
                string.format("Edição Livre (%s): %d -> %d", field, cur, nextVal),
                0,
                "aprovado",
                field,
                nextVal
            )
        elseif modo == "jogo" and stOverride then
            Bridge.logAudit(
                sheet,
                ndbApi,
                fc,
                "override_narrador",
                string.format("Ajuste com Override (%s): %d -> %d", field, cur, nextVal),
                0,
                "aprovado",
                field,
                nextVal
            )
        end
    end
    return { ok = true, before = cur, after = nextVal }
end

local VALID_SHEET_MODES = { criacao = true, jogo = true, narrador_livre = true }

function Bridge.setSheetMode(sheet, newMode, firecastApi, dialogsApi, ndbApi)
    if type(sheet) ~= "table" then return { ok = false, error = "Ficha inválida." } end
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    if not VALID_SHEET_MODES[newMode] then
        local err = "Modo de ficha inválido: " .. tostring(newMode)
        dlg.showMessage(err)
        return { ok = false, error = err }
    end
    if not Bridge.isStoryteller(sheet, fc) then
        local err = "Apenas o Narrador pode alterar manualmente o Modo da Ficha."
        dlg.showMessage(err)
        return { ok = false, error = err }
    end
    local prevMode = sheet.modo_ficha or "criacao"
    if prevMode ~= newMode then
        sheet.modo_ficha = newMode
        Bridge.syncDerivedFields(sheet, ndbApi)
        Bridge.logAudit(
            sheet,
            ndbApi,
            fc,
            "modo_ficha",
            string.format("Modo da ficha alterado: %s -> %s", tostring(prevMode), tostring(newMode)),
            0,
            "aprovado",
            "modo_ficha",
            newMode
        )
    else
        Bridge.syncDerivedFields(sheet, ndbApi)
    end
    return { ok = true, mode = newMode }
end

local VALID_MORTAL_MODES = { humano = true, carnical = true, numina = true }

function Bridge.setMortalSupernaturalMode(sheet, newMode, firecastApi, dialogsApi, ndbApi)
    if type(sheet) ~= "table" then return { ok = false, error = "Ficha inválida." } end
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    if not VALID_MORTAL_MODES[newMode] then
        local err = "Condição sobrenatural mortal inválida: " .. tostring(newMode)
        dlg.showMessage(err)
        return { ok = false, error = err }
    end
    if not Bridge.isStoryteller(sheet, fc) then
        local err = "Apenas o Narrador pode alterar a Condição Sobrenatural (Humano / Carniçal / Numina)."
        dlg.showMessage(err)
        return { ok = false, error = err }
    end
    local prevMode = sheet.mortal_sobrenatural_modo or "humano"
    sheet.mortal_sobrenatural_modo = newMode
    Bridge.syncDerivedFields(sheet, ndbApi)
    if prevMode ~= newMode then
        Bridge.logAudit(
            sheet,
            ndbApi,
            fc,
            "transicao_sobrenatural",
            string.format("Condição sobrenatural mortal: %s -> %s", tostring(prevMode), tostring(newMode)),
            0,
            "aprovado",
            "mortal_sobrenatural_modo",
            newMode
        )
    end
    return { ok = true, mode = newMode }
end

function Bridge.rollInitialBlood(sheet, firecastApi, dialogsApi)
    if type(sheet) ~= "table" then return end
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)
    local rolObj = (fc and fc.interpretarRolagem) and fc.interpretarRolagem("1d10") or nil
    local mesa = (fc and fc.getMesaDe) and fc.getMesaDe(sheet) or nil

    local function applyFace(val)
        local cap = math.max(1, safeInt(sheet.sangue_max, 10))
        sheet.sangue_atual = math.min(cap, math.max(1, safeInt(val, 5)))
        Bridge.syncDerivedFields(sheet)
        return string.format("[%s] Reserva Inicial de Vitae (1d10): %d ponto(s).", sheet.nome or "Personagem", safeInt(sheet.sangue_atual, 0))
    end

    if mesa ~= nil and mesa.activeChat ~= nil and rolObj ~= nil then
        mesa.activeChat:rolarDados(rolObj, "🩸 [" .. (sheet.nome or "Personagem") .. "] Vitae Inicial (1d10)", function(rolado)
            local faces = Bridge.extractRollFaces(rolado)
            mesa.activeChat:enviarMensagem(applyFace(faces[1] or 5))
        end)
    else
        local v = 5
        if rolObj and rolObj.rolarLocalmente then
            rolObj:rolarLocalmente()
            local faces = Bridge.extractRollFaces(rolObj)
            v = faces[1] or 5
        else
            v = math.random(1, 10)
        end
        dlg.showMessage(applyFace(v))
    end
end

function Bridge.rollFromSheet(sheet, opts, firecastApi, dialogsApi)
    opts, firecastApi, dialogsApi = normalizeOptsAndApis(opts, firecastApi, dialogsApi)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)

    local discList = Bridge.collectDisciplines(sheet)
    local cMods = V20.DisciplinesEngine.computeCombatModifiers(Bridge.sheetToEngineState(sheet), discList)

    local attrVal = 0
    local habVal = 0
    local habCat = nil
    local label = opts.label
    local bonusDice = safeInt(opts.bonusDice ~= nil and opts.bonusDice or sheet.roll_bonus_dice, 0)
    local diffMod = safeInt(opts.difficultyMod, 0)
    local extraAuto = 0
    local isVirtualPool = false
    local resolvedAttrId = nil
    local resolvedHabId = nil

    if opts.rawPool ~= nil then
        attrVal = safeInt(opts.rawPool, 0)
        habVal = 0
        bonusDice = safeInt(opts.bonusDice, 0)
        label = label or "Teste V20"
        resolvedAttrId = opts.resolvedAttrId or opts.attrId
        resolvedHabId = opts.resolvedHabId or opts.habId
        if resolvedHabId == "" or resolvedHabId == "none" then resolvedHabId = nil end
    else
        local attrId = opts.attrId or sheet.roll_attr_id or "attr_percepcao"
        local habId = (opts.habId ~= nil) and opts.habId or (opts.attrId == nil and sheet.roll_hab_id or nil)
        if habId == "" or habId == "none" then habId = nil end
        resolvedAttrId = attrId
        resolvedHabId = habId

        local attrInfo = Bridge.resolvePoolTrait(sheet, attrId, cMods)
        local habInfo = habId and Bridge.resolvePoolTrait(sheet, habId, cMods) or { val = 0, label = nil, category = nil, isVirtual = false }

        attrVal = attrInfo.val
        habVal = habInfo.val
        habCat = habInfo.category
        isVirtualPool = attrInfo.isVirtual

        if attrId == "attr_forca" and not opts.noPassiveDiscipline then
            bonusDice = bonusDice + cMods.passivePotenceDice
            extraAuto = extraAuto + cMods.activePotenceAuto
        elseif attrId == "attr_destreza" and not opts.noPassiveDiscipline then
            bonusDice = bonusDice + cMods.passiveCelerityDice
        elseif attrId == "attr_percepcao" then
            diffMod = diffMod + cMods.perceptionDiffMod + safeInt(sheet.percepcao_mod_qualidades, 0)
        end

        if isTrue(opts.useFame) or (opts.attrId == nil and isTrue(sheet.roll_usar_fama)) then
            diffMod = diffMod + safeInt(sheet.fama_mod_dif, 0)
        end
        if isTrue(opts.useStatus) or (opts.attrId == nil and isTrue(sheet.roll_usar_status)) then
            bonusDice = bonusDice + safeInt(sheet.status_bonus_dados, 0)
        end

        if not label then
            label = (attrInfo.label or attrId) .. (habInfo.label and (" + " .. habInfo.label) or "")
        end
    end

    local spendWP = false
    if not isTrue(opts.forbidWillpower) then
        if opts.spendWillpower ~= nil then
            spendWP = isTrue(opts.spendWillpower)
        elseif opts.rawPool == nil and opts.attrId == nil then
            spendWP = isTrue(sheet.roll_gastar_fdv)
        end
    end

    local ignoreWound = isVirtualPool
        or isTrue(opts.ignoreWoundPenalty)
        or (opts.rawPool == nil and isTrue(sheet.roll_ignorar_ferimento))
        or isTrue(sheet.em_frenesi)

    local stOverride = isTrue(sheet.narrador_override) and Bridge.isStoryteller(sheet, fc)

    local cwMods = nil
    if Bridge.isVampireSheet(sheet) and not isTrue(opts.skipClanWeakness) then
        cwMods = V20.ClanWeaknesses.computeRollModifiers({
            cla_id = sheet.cla_id,
            attrId = resolvedAttrId,
            habId = resolvedHabId,
            activeBuffs = Bridge.deserializeBuffs(sheet),
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
        bonusDice = bonusDice + safeInt(cwMods.bonusDiceMod, 0)
        diffMod = diffMod + safeInt(cwMods.diffMod, 0)
    end

    local poolInfo = V20.Dice.buildPool({
        actorName = sheet.nome,
        attrVal = attrVal,
        abilityVal = habVal,
        abilityCategory = habCat,
        bonusDice = bonusDice,
        difficulty = safeInt(opts.difficulty ~= nil and opts.difficulty or sheet.roll_diff, 6),
        difficultyMod = diffMod,
        woundPenalty = isTrue(opts.woundPenaltyAlreadyApplied) and 0 or (sheet.penalidade_ferimento or 0),
        incapacitated = isTrue(sheet.incapacitado),
        ignoreWoundPenalty = ignoreWound,
        spendWillpower = spendWP,
        autoSuccesses = safeInt(opts.autoSuccesses, 0) + extraAuto,
        storytellerOverride = stOverride,
    })

    if not poolInfo.canRoll then
        dlg.showMessage(poolInfo.blockReason or "Rolagem bloqueada pelas regras V20.")
        return { ok = false, error = poolInfo.blockReason }
    end

    if isTrue(opts.forbidZeroPool) and poolInfo.pool <= 0 and not stOverride then
        local zeroMsg = "Parada reduzida a zero ou menos pelas penalidades."
        dlg.showMessage(zeroMsg)
        return { ok = false, error = zeroMsg }
    end

    if cwMods ~= nil then
        if cwMods.poolDivisor and cwMods.poolDivisor > 1 and poolInfo.pool >= 1 then
            poolInfo.pool = math.max(1, math.floor(poolInfo.pool / cwMods.poolDivisor))
        end
        for _, w in ipairs(cwMods.warnings or {}) do
            table.insert(poolInfo.warnings, w)
        end
    end

    if spendWP then
        if safeInt(sheet.fdv_temp, 0) < 1 and not stOverride then
            dlg.showMessage("Força de Vontade temporária insuficiente para sucesso automático.")
            return { ok = false, error = "Força de Vontade temporária insuficiente." }
        end
        sheet.fdv_temp = math.max(0, safeInt(sheet.fdv_temp, 1) - 1)
    end

    if type(opts.extraNotes) == "table" then
        for _, n in ipairs(opts.extraNotes) do
            table.insert(poolInfo.warnings, n)
        end
    end

    local useSpec = false
    if opts.specialty ~= nil then
        useSpec = isTrue(opts.specialty)
    elseif opts.rawPool == nil and opts.attrId == nil then
        useSpec = isTrue(sheet.roll_usar_espec)
    end

    -- PF-3: poolInfo.autoSuccesses JÁ inclui +1 de spendWillpower; NÃO passar spendWillpower p/ evaluate!
    local function finishEvaluation(faces)
        local evalRes = V20.Dice.evaluate(faces, poolInfo.effectiveDifficulty, {
            specialty = useSpec,
            autoSuccesses = poolInfo.autoSuccesses,
        })
        if type(opts.onEvaluated) == "function" then
            local extraNote = opts.onEvaluated(evalRes)
            if type(extraNote) == "string" and extraNote ~= "" then
                table.insert(poolInfo.warnings, extraNote)
            end
        end
        local msg = Bridge.formatChatReport(sheet.nome, label, evalRes, faces, poolInfo.warnings)
        return evalRes, msg
    end

    local diceToRoll = poolInfo.pool
    local mesa = (fc and fc.getMesaDe) and fc.getMesaDe(sheet) or nil

    if diceToRoll <= 0 then
        local evalRes, msg = finishEvaluation({})
        if mesa ~= nil and mesa.activeChat ~= nil then
            mesa.activeChat:enviarMensagem(msg)
        else
            dlg.showMessage(msg)
        end
        return { ok = true, eval = evalRes, message = msg }
    end

    local expr = tostring(diceToRoll) .. "d10"
    local rolObj = (fc and fc.interpretarRolagem) and fc.interpretarRolagem(expr) or nil

    if mesa ~= nil and mesa.activeChat ~= nil and rolObj ~= nil then
        local lastEval = nil
        mesa.activeChat:rolarDados(rolObj, "🎲 [" .. (sheet.nome or "Personagem") .. "] " .. label, function(rolado)
            local faces = Bridge.extractRollFaces(rolado)
            local evalRes, msg = finishEvaluation(faces)
            lastEval = evalRes
            mesa.activeChat:enviarMensagem(msg)
        end)
        return { ok = true, eval = lastEval }
    else
        local faces = {}
        if rolObj and rolObj.rolarLocalmente then
            rolObj:rolarLocalmente()
            faces = Bridge.extractRollFaces(rolObj)
        else
            for i = 1, diceToRoll do
                faces[i] = math.random(1, 10)
            end
        end
        local evalRes, msg = finishEvaluation(faces)
        dlg.showMessage(msg)
        return { ok = true, eval = evalRes, message = msg }
    end
end

local function applyEngineStateToSheet(sheet, st)
    sheet.sangue_atual = st.currentBlood
    sheet.sangue_gasto_turno = st.spentThisTurn
    sheet.sangue_fraco_usado = st.thinBloodUsed
    sheet.fdv_temp = st.fdv_temp
    sheet.potencia_ativa_turno = (st.activePotenceAuto == true)
    local prevAtivas = safeNonNegInt(sheet.rapidez_acoes_ativas, 0)
    local newAtivas = safeNonNegInt(st.activeCelerityActions, 0)
    sheet.rapidez_acoes_ativas = newAtivas
    if newAtivas == 0 and prevAtivas > 0 then
        sheet.rapidez_acoes_extras = 0
    elseif newAtivas > prevAtivas then
        sheet.rapidez_acoes_extras = safeNonNegInt(sheet.rapidez_acoes_extras, 0) + (newAtivas - prevAtivas)
    end
    sheet.buff_forca = safeInt(st.buff_forca, safeInt(sheet.buff_forca, 0))
    sheet.buff_destreza = safeInt(st.buff_destreza, safeInt(sheet.buff_destreza, 0))
    sheet.buff_vigor = safeInt(st.buff_vigor, safeInt(sheet.buff_vigor, 0))
    Bridge.serializeBuffs(sheet, st.activeBuffs)
    Bridge.syncDerivedFields(sheet)
end

function Bridge.activateDisciplinePower(sheet, discNode, powerId, firecastApi, dialogsApi)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)

    local resolvedEntry = nil
    if type(discNode) == "number" then
        local sid = sheet["disc_slot" .. discNode .. "_id"]
        local slvl = safeInt(sheet["disc_slot" .. discNode .. "_nivel"], 0)
        if isTrue(sheet.isGhoul) and sid == "potence" then
            slvl = math.max(slvl, safeInt(sheet.ghoulPotence, 0))
        end
        resolvedEntry = { disc_id = sid, nivel = slvl }
    elseif type(discNode) == "string" then
        for _, d in ipairs(Bridge.collectDisciplines(sheet)) do
            if d.disc_id == discNode then
                resolvedEntry = d
                break
            end
        end
        local fallbackLvl = safeInt(sheet["disc_" .. discNode], 0)
        if isTrue(sheet.isGhoul) and discNode == "potence" then
            fallbackLvl = math.max(fallbackLvl, safeInt(sheet.ghoulPotence, 0))
        end
        resolvedEntry = resolvedEntry or { disc_id = discNode, nivel = fallbackLvl }
    elseif type(discNode) == "table" then
        resolvedEntry = discNode
    end

    local resolvedPower = powerId
    if type(powerId) == "number" and resolvedEntry and resolvedEntry.disc_id then
        local cat = V20.DisciplinesCatalog.DISCIPLINES[resolvedEntry.disc_id]
        if cat and cat.powers and cat.powers[powerId] then
            resolvedPower = cat.powers[powerId].id
        end
    end

    local pwObj = nil
    if type(resolvedPower) == "table" then
        pwObj = resolvedPower
    elseif type(resolvedPower) == "string" and resolvedEntry and resolvedEntry.disc_id then
        local cat = V20.DisciplinesCatalog.DISCIPLINES[resolvedEntry.disc_id]
        if cat and cat.powers then
            for _, pw in ipairs(cat.powers) do
                if pw.id == resolvedPower then
                    pwObj = pw
                    break
                end
            end
        end
    end

    local baseBloodCost = 0
    if resolvedEntry and resolvedEntry.disc_id == "potence" then
        baseBloodCost = isTrue(sheet.potencia_ativa_turno) and 0 or 1
    elseif resolvedEntry and resolvedEntry.disc_id == "celerity" then
        baseBloodCost = 1
    elseif pwObj ~= nil then
        local curBuffs = Bridge.deserializeBuffs(sheet)
        local isDeactivating = (pwObj.toggleBuff ~= nil) and (curBuffs[pwObj.toggleBuff.id] ~= nil)
        baseBloodCost = isDeactivating and 0 or math.max(0, safeInt(pwObj.cost and pwObj.cost.blood, 0))
    end

    local isGen15Channel = Bridge.isVampireSheet(sheet)
        and (baseBloodCost == 1)
        and (safeInt(sheet.geracao, 13) == 15)
        and (safeInt(sheet.sangue_gasto_turno, 0) == 0)

    local stOverride = isTrue(sheet.narrador_override) and Bridge.isStoryteller(sheet, fc)
    local engState = Bridge.sheetToEngineState(sheet)
    local res = V20.DisciplinesEngine.activatePower(engState, resolvedEntry, resolvedPower, {
        storytellerOverride = stOverride,
        bypassTurnLimit = isGen15Channel,
    })

    if not res.ok then
        dlg.showMessage(res.error or "Não foi possível ativar o poder.")
        return res
    end

    applyEngineStateToSheet(sheet, res.newState)

    if res.rollSpec then
        local notes = {}
        if res.rollSpec.diffHint and res.rollSpec.diffHint ~= "" then
            table.insert(notes, res.rollSpec.diffHint)
        end
        if isGen15Channel then
            table.insert(notes, GEN15_CHANNEL_NOTE)
        end
        Bridge.rollFromSheet(sheet, {
            attrId = res.rollSpec.attr,
            habId = res.rollSpec.hab,
            difficulty = res.rollSpec.defaultDiff,
            label = res.rollSpec.powerName,
            spendWillpower = false,
            extraNotes = (#notes > 0) and notes or nil,
        }, fc, dlg)
    else
        local statusTxt = "ativado"
        if res.buffToggled and res.buffToggled.active == false then
            statusTxt = "desativado"
        end
        local discMeta = resolvedEntry and V20.DisciplinesCatalog.DISCIPLINES[resolvedEntry.disc_id]
        local title = (discMeta and discMeta.name) or tostring(powerId)
        local gen15Note = isGen15Channel and (" " .. GEN15_CHANNEL_NOTE) or ""
        Bridge.notify(
            sheet,
            string.format("🦇 [%s] %s %s (Sangue: %d/%d | Turno: %d/%d).%s",
                sheet.nome or "Personagem",
                title,
                statusTxt,
                safeInt(sheet.sangue_atual, 0),
                safeInt(sheet.sangue_max, 10),
                safeInt(sheet.sangue_gasto_turno, 0),
                safeInt(sheet.sangue_por_turno, 1),
                gen15Note
            ),
            fc,
            dlg
        )
    end

    return res
end

function Bridge.activateDisciplineSlot(sheet, slotIndex, firecastApi, dialogsApi)
    local pwrLvl = math.max(1, math.min(5, safeInt(sheet and sheet["disc_slot" .. slotIndex .. "_pwr_lvl"], 1)))
    local discId = (type(sheet) == "table") and sheet["disc_slot" .. slotIndex .. "_id"] or nil
    if Bridge.isVampireSheet(sheet) and (discId == "thaumaturgy" or discId == "necromancy") then
        return Bridge.activatePrimaryBloodMagic(sheet, discId, pwrLvl, firecastApi, dialogsApi)
    end
    return Bridge.activateDisciplinePower(sheet, slotIndex, pwrLvl, firecastApi, dialogsApi)
end

function Bridge.activateCustomPower(sheet, firecastApi, dialogsApi)
    if type(sheet) ~= "table" then return { ok = false } end
    local customPower = {
        id = "custom_power",
        level = math.max(1, safeInt(sheet.custom_pwr_nivel, 1)),
        name = (type(sheet.custom_pwr_nome) == "string" and sheet.custom_pwr_nome ~= "") and sheet.custom_pwr_nome or "Poder Customizado",
        cost = {
            blood = math.max(0, safeInt(sheet.custom_pwr_sangue, 0)),
            willpower = math.max(0, safeInt(sheet.custom_pwr_fdv, 0)),
        },
        pool = (type(sheet.custom_pwr_attr) == "string" and sheet.custom_pwr_attr ~= "" and sheet.custom_pwr_attr ~= "none")
            and { attr = sheet.custom_pwr_attr, hab = (sheet.custom_pwr_hab ~= "none" and sheet.custom_pwr_hab or nil) }
            or nil,
        defaultDiff = safeInt(sheet.custom_pwr_dif, 6),
        diffHint = "Poder Customizado / Linha Secundária",
    }
    local maxLvl = math.max(customPower.level, safeInt(sheet.disciplina_max_geracao, 5))
    return Bridge.activateDisciplinePower(sheet, { disc_id = "custom", nivel = maxLvl }, customPower, firecastApi, dialogsApi)
end

function Bridge.awakenNightly(sheet, firecastApi, dialogsApi)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)
    local res = V20.WillpowerMorality.awakenNightly({
        isVampire = Bridge.isVampireSheet(sheet),
        currentBlood = sheet.sangue_atual,
        spentThisTurn = sheet.sangue_gasto_turno,
        virtude2_val = sheet.virtude2_val,
    })
    sheet.sangue_atual = res.newState.currentBlood
    sheet.sangue_gasto_turno = 0
    Bridge.syncDerivedFields(sheet)
    local warn = res.warning and (" ⚠️ " .. res.warning) or ""
    Bridge.notify(
        sheet,
        string.format("🌙 [%s] Despertar Noturno — Vitae: %d/%d.%s",
            sheet.nome or "Personagem",
            safeInt(sheet.sangue_atual, 0),
            safeInt(sheet.sangue_max, 10),
            warn
        ),
        fc,
        dlg
    )
    return res
end

function Bridge.healDamage(sheet, damageType, opts, firecastApi, dialogsApi)
    opts, firecastApi, dialogsApi = normalizeOptsAndApis(opts, firecastApi, dialogsApi)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)

    local dtype = damageType or sheet.cura_tipo or "bashing"
    local isGen15Channel = Bridge.isVampireSheet(sheet)
        and (dtype ~= "aggravated")
        and (safeInt(sheet.geracao, 13) == 15)
        and (safeInt(sheet.sangue_gasto_turno, 0) == 0)
    local stOverride = isTrue(sheet.narrador_override) and Bridge.isStoryteller(sheet, fc)
    local st = Bridge.sheetToEngineState(sheet)
    st.bashing = safeInt(sheet.dano_contundente, 0)
    st.lethal = safeInt(sheet.dano_letal, 0)
    st.aggravated = safeInt(sheet.dano_aggravado, 0)

    local res = V20.Health.healWithBlood(st, dtype, {
        useWillpowerForExtra = isTrue(opts.useWillpowerForExtra) or isTrue(sheet.cura_agravado_extra_fdv),
        bypassTurnLimit = isTrue(opts.bypassTurnLimit) or isGen15Channel,
        storytellerOverride = stOverride,
    })
    if not res.ok then
        dlg.showMessage(res.error or "Não foi possível curar ferimento.")
        return res
    end

    sheet.sangue_atual = res.newState.currentBlood
    sheet.sangue_gasto_turno = res.newState.spentThisTurn
    sheet.sangue_fraco_usado = res.newState.thinBloodUsed
    sheet.fdv_temp = res.newState.fdv_temp
    sheet.dano_contundente = res.newState.bashing
    sheet.dano_letal = res.newState.lethal
    sheet.dano_aggravado = res.newState.aggravated
    sheet.dano_agravado = res.newState.aggravated
    LAST_AGG_MIRROR[sheet] = res.newState.aggravated
    Bridge.syncDerivedFields(sheet)

    local gen15Note = isGen15Channel and (" " .. GEN15_CHANNEL_NOTE) or ""
    Bridge.notify(
        sheet,
        string.format("🩸 [%s] Curou 1 nível (%s) | Vitalidade: %s | Sangue: %d/%d%s",
            sheet.nome or "Personagem",
            dtype,
            sheet.vitalidade_resumo or "Saudável",
            safeInt(sheet.sangue_atual, 0),
            safeInt(sheet.sangue_max, 10),
            gen15Note
        ),
        fc,
        dlg
    )
    return res
end

function Bridge.applyDamage(sheet, amount, damageType, opts, firecastApi, dialogsApi)
    opts, firecastApi, dialogsApi = normalizeOptsAndApis(opts, firecastApi, dialogsApi)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)

    local qty = math.max(0, safeInt(amount ~= nil and amount or sheet.dano_aplicar_qtd, 1))
    local dtype = damageType or sheet.dano_aplicar_tipo or "bashing"
    local isVamp = Bridge.isVampireSheet(sheet)
    local isSolar = (opts.isSolar ~= nil) and isTrue(opts.isSolar) or isTrue(sheet.dano_fonte_solar)
    local solarExtra = 0
    if isVamp and qty > 0 and isSolar then
        dtype = "aggravated"
        solarExtra = V20.ClanWeaknesses.computeSolarExtraDamage(sheet.cla_id, qty, true)
    end
    local totalQty = qty + solarExtra
    local huge = isTrue(sheet.tem_tamanho_grande) or V20.BackgroundsEngine.aggregateMeritsFlaws(Bridge.collectMeritsFlaws(sheet)).hugeSize

    local nextH = V20.Health.applyDamage({
        isVampire = isVamp,
        hugeSize = huge,
        bashing = safeInt(sheet.dano_contundente, 0),
        lethal = safeInt(sheet.dano_letal, 0),
        aggravated = safeInt(sheet.dano_aggravado, 0),
    }, totalQty, dtype, {
        isVampire = isVamp,
        isFirearm = (not isSolar) and ((opts.isFirearm ~= nil) and isTrue(opts.isFirearm) or isTrue(sheet.dano_arma_fogo)),
        headshot = (not isSolar) and ((opts.headshot ~= nil) and isTrue(opts.headshot) or isTrue(sheet.dano_tiro_cabeca)),
        halveBashing = (not isSolar) and ((opts.halveBashing ~= nil) and isTrue(opts.halveBashing) or isTrue(sheet.dano_dividir_contundente)),
    })

    sheet.dano_contundente = nextH.bashing
    sheet.dano_letal = nextH.lethal
    sheet.dano_aggravado = nextH.aggravated
    sheet.dano_agravado = nextH.aggravated
    LAST_AGG_MIRROR[sheet] = nextH.aggravated
    Bridge.syncDerivedFields(sheet)

    local solarNote = (solarExtra > 0) and string.format(" [Luz Solar +%d Agravado da fraqueza]", solarExtra) or ""
    local alert = (sheet.vitalidade_alerta and sheet.vitalidade_alerta ~= "") and (" ⚠️ " .. sheet.vitalidade_alerta) or ""
    Bridge.notify(
        sheet,
        string.format("⚔️ [%s] Dano aplicado (%d %s)%s -> %s (%s)%s",
            sheet.nome or "Personagem",
            totalQty,
            dtype,
            solarNote,
            sheet.vitalidade_resumo or "Saudável",
            sheet.vitalidade_trilha_visual or "",
            alert
        ),
        fc,
        dlg
    )
    return nextH
end

function Bridge.newTurn(sheet, firecastApi, dialogsApi)
    if type(sheet) ~= "table" then return end
    local st = V20.DisciplinesEngine.clearTurnEffects(Bridge.sheetToEngineState(sheet))
    st = V20.Blood.newTurn(st)
    setIfChanged(sheet, "cmb_defesas_feitas_turno", 0)
    setIfChanged(sheet, "rapidez_acoes_extras", 0)
    applyEngineStateToSheet(sheet, st)
    return st
end

function Bridge.applyBloodBuff(sheet, attrKey, firecastApi, dialogsApi)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)
    if not Bridge.isVampireSheet(sheet) and not isTrue(sheet.isGhoul) then
        dlg.showMessage("Apenas vampiros e carniçais podem realizar Blood Buff físico.")
        return { ok = false, error = "Mortal humano não possui vitae para Blood Buff." }
    end

    local isGen15Channel = Bridge.isVampireSheet(sheet)
        and (safeInt(sheet.geracao, 13) == 15)
        and (safeInt(sheet.sangue_gasto_turno, 0) == 0)
    local stOverride = isTrue(sheet.narrador_override) and Bridge.isStoryteller(sheet, fc)
    local res = V20.Blood.applyPhysicalBuff(Bridge.sheetToEngineState(sheet), attrKey, {
        bypassTurnLimit = isGen15Channel,
        storytellerOverride = stOverride,
    })
    if not res.ok then
        dlg.showMessage(res.error or "Falha no Blood Buff.")
        return res
    end

    applyEngineStateToSheet(sheet, res.newState)
    local durNote = res.temporaryAboveMax and " (Acima do teto da geração: dura 3 turnos)" or " (Dura toda a cena)"
    local gen15Note = isGen15Channel and (" " .. GEN15_CHANNEL_NOTE) or ""
    Bridge.notify(
        sheet,
        string.format("🩸 [%s] Blood Buff em %s -> Efetivo %d%s | Sangue: %d/%d%s",
            sheet.nome or "Personagem",
            attrKey,
            res.effectiveAttr,
            durNote,
            safeInt(sheet.sangue_atual, 0),
            safeInt(sheet.sangue_max, 10),
            gen15Note
        ),
        fc,
        dlg
    )
    return res
end

function Bridge.clearSceneBuffs(sheet, firecastApi, dialogsApi)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    local st = V20.Blood.clearSceneBuffs(Bridge.sheetToEngineState(sheet))
    st = V20.DisciplinesEngine.clearSceneBuffs(st)
    setIfChanged(sheet, "malkav_suprimida_cena", false)
    setIfChanged(sheet, "toreador_fascinado_cena", false)
    setIfChanged(sheet, "em_agarrao", false)
    setIfChanged(sheet, "cmb_defesas_feitas_turno", 0)
    setIfChanged(sheet, "cmb_dano_pendente_ativo", false)
    setIfChanged(sheet, "rapidez_acoes_extras", 0)
    applyEngineStateToSheet(sheet, st)
    Bridge.notify(sheet, string.format("🧹 [%s] Buffs de cena encerrados.", sheet.nome or "Personagem"), fc, dlg)
    return st
end

function Bridge.rollFrenzy(sheet, stimulusDiff, firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)
    local diff = safeInt(stimulusDiff ~= nil and stimulusDiff or sheet.frenesi_dif, 6)
    local check = V20.WillpowerMorality.prepareFrenzyCheck(sheet, diff)
    local vLabel = (sheet.virtude2_tipo == "instinto") and "Instinto" or "Autocontrole"
    return Bridge.rollFromSheet(sheet, {
        rawPool = check.pool,
        difficulty = check.difficulty,
        ignoreWoundPenalty = true,
        forbidWillpower = (not check.canAvoidWithWillpower),
        extraNotes = check.notes,
        label = "Frenesi (" .. vLabel .. ")",
    }, firecastApi, dialogsApi)
end

function Bridge.rollRotschreck(sheet, stimulusDiff, firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)
    local diff = safeInt(stimulusDiff ~= nil and stimulusDiff or sheet.rotschreck_dif, 6)
    local check = V20.WillpowerMorality.prepareRotschreckCheck(sheet, diff)
    return Bridge.rollFromSheet(sheet, {
        rawPool = check.pool,
        difficulty = check.difficulty,
        ignoreWoundPenalty = true,
        label = "Rötschreck (Coragem)",
    }, firecastApi, dialogsApi)
end

function Bridge.rollDegeneration(sheet, firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)
    local check = V20.WillpowerMorality.prepareDegenerationCheck(sheet)
    return Bridge.rollFromSheet(sheet, {
        rawPool = check.pool,
        difficulty = check.difficulty,
        ignoreWoundPenalty = true,
        forbidWillpower = true,
        label = "Degeneração (" .. check.virtueUsed .. ")",
    }, firecastApi, dialogsApi)
end

function Bridge.rollSoak(sheet, damageType, firecastApi, dialogsApi)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)
    local dtype = damageType or sheet.absorcao_tipo or "bashing"
    local cMods = V20.DisciplinesEngine.computeCombatModifiers(Bridge.sheetToEngineState(sheet), Bridge.collectDisciplines(sheet))
    local soak = V20.Health.buildSoakPool({
        isVampire = Bridge.isVampireSheet(sheet),
        isGhoul = isTrue(sheet.isGhoul),
        attr_vigor = safeInt(sheet.attr_vigor, 1),
        buff_vigor = safeInt(sheet.buff_vigor, 0) + safeInt(cMods.sceneAttrMods.vigor, 0),
        fortitude = cMods.fortitudeSoak,
        armor = safeInt(sheet.armadura_absorcao, 0),
        soakDifficulty = cMods.soakDiffOverride or 6,
    }, dtype)

    if not soak.canSoak then
        dlg.showMessage(soak.reason or "Não é possível absorver este tipo de dano.")
        return { ok = false, error = soak.reason }
    end

    return Bridge.rollFromSheet(sheet, {
        rawPool = soak.pool,
        difficulty = soak.difficulty,
        ignoreWoundPenalty = true,
        forbidWillpower = true,
        label = "Absorção (" .. dtype .. ")",
    }, fc, dlg)
end

function Bridge.rollInitiative(sheet, firecastApi, dialogsApi)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)
    local cMods = V20.DisciplinesEngine.computeCombatModifiers(Bridge.sheetToEngineState(sheet), Bridge.collectDisciplines(sheet))
    local dex = Bridge.resolvePoolTrait(sheet, "attr_destreza", cMods).val + cMods.passiveCelerityDice
    local wits = Bridge.resolvePoolTrait(sheet, "attr_raciocinio", cMods).val
    local wPen = (isTrue(sheet.em_frenesi) or isTrue(sheet.roll_ignorar_ferimento)) and 0 or math.abs(safeInt(sheet.penalidade_ferimento, 0))
    local armorPen = math.abs(safeInt(sheet.armadura_penalidade, 0))
    local mod = dex + wits - wPen - armorPen

    local rolObj = (fc and fc.interpretarRolagem) and fc.interpretarRolagem("1d10") or nil
    local mesa = (fc and fc.getMesaDe) and fc.getMesaDe(sheet) or nil

    local function formatInit(d10Val)
        local faceInt = safeInt(d10Val, 1)
        local total = faceInt + mod
        local dockBridge = rawget(_G, "V20CoterieDockBridge")
        if dockBridge == nil then
            local okDock, modDock = pcall(require, "Adapter.coterie_dock_bridge")
            if okDock and type(modDock) == "table" then dockBridge = modDock end
        end
        if dockBridge and type(dockBridge.recordSheetInitiative) == "function" then
            dockBridge.recordSheetInitiative(sheet, faceInt, mod, faceInt + mod, fc)
        end
        return string.format("⚡ [%s] Iniciativa V20: 1d10 (%d) + Mod (%d) = %d", sheet.nome or "Personagem", faceInt, mod, total)
    end

    if mesa ~= nil and mesa.activeChat ~= nil and rolObj ~= nil then
        mesa.activeChat:rolarDados(rolObj, "⚡ [" .. (sheet.nome or "Personagem") .. "] Iniciativa", function(rolado)
            local faces = Bridge.extractRollFaces(rolado)
            mesa.activeChat:enviarMensagem(formatInit(faces[1] or 1))
        end)
    else
        local d10Val = 5
        if rolObj and rolObj.rolarLocalmente then
            rolObj:rolarLocalmente()
            local faces = Bridge.extractRollFaces(rolObj)
            d10Val = faces[1] or 5
        else
            d10Val = math.random(1, 10)
        end
        dlg.showMessage(formatInit(d10Val))
    end
end

function Bridge.huntWithHerdDomain(sheet, opts, firecastApi, dialogsApi)
    opts, firecastApi, dialogsApi = normalizeOptsAndApis(opts, firecastApi, dialogsApi)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)

    if Bridge.isVampireSheet(sheet) and not isTrue(opts.isCainiteVitae) then
        local vCheck = V20.ClanWeaknesses.checkVentrueFeeding(sheet)
        if not vCheck.allowed then
            Bridge.notify(sheet, "🩸 [" .. (sheet.nome or "Personagem") .. "] " .. vCheck.reason, fc, dlg)
            return { ok = false, blocked = true, error = vCheck.reason }
        end
    end

    local attrId = opts.attrId or sheet.caca_attr_id or "attr_percepcao"
    local habId = opts.habId or sheet.caca_hab_id or "hab_manha"
    local baseDiff = safeInt(opts.difficulty ~= nil and opts.difficulty or sheet.caca_dif_base, 6)
    local gainBlood = not isFalse(opts.gainBloodOnSuccess)

    return Bridge.rollFromSheet(sheet, {
        attrId = attrId,
        habId = habId,
        bonusDice = safeInt(sheet.caca_bonus_dados, 0),
        difficulty = baseDiff,
        difficultyMod = safeInt(sheet.caca_mod_dif, 0),
        label = "Caça / Alimentação",
        onEvaluated = function(evalRes)
            if gainBlood and evalRes.totalSuccesses > 0 and Bridge.isVampireSheet(sheet) then
                local g = V20.Blood.gain(Bridge.sheetToEngineState(sheet), evalRes.totalSuccesses)
                sheet.sangue_atual = g.newState.currentBlood
                sheet.sangue_fraco_usado = g.newState.thinBloodUsed
                Bridge.syncDerivedFields(sheet)
                local note = string.format("+%d Vitae absorvida -> %d/%d", safeInt(g.added, 0), safeInt(sheet.sangue_atual, 0), safeInt(sheet.sangue_max, 10))
                if sheet.cla_id == "giovanni" then
                    local kiss = V20.ClanWeaknesses.computeGiovanniKissDamage(evalRes.totalSuccesses)
                    local fatalTxt = kiss.fatalRisk and " — CHOQUE/MORTE DO RECIPIENTE!" or ""
                    note = note .. string.format(" | Beijo Doloroso Giovanni: %d níveis Letais no recipiente%s", kiss.lethalToVessel, fatalTxt)
                end
                return note
            end
            return nil
        end,
    }, fc, dlg)
end

function Bridge.rollBackgroundAction(sheet, bgId, attrId, firecastApi, dialogsApi)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)
    if bgId == "herd" or bgId == "domain" then
        return Bridge.huntWithHerdDomain(sheet, {}, fc, dlg)
    end
    local useAttr = attrId or sheet.bg_acao_attr_id or "attr_carisma"
    local attrInfo = Bridge.resolvePoolTrait(sheet, useAttr)
    local dots = safeInt(sheet["bg_" .. tostring(bgId)], 0)
    local act = V20.BackgroundsEngine.buildActionRoll(bgId, dots, attrInfo.val)
    if not act.canRoll then
        dlg.showMessage(act.title or "Antecedente sem pontos ou sem ação rolável.")
        return { ok = false, error = act.title }
    end
    return Bridge.rollFromSheet(sheet, {
        rawPool = act.pool,
        difficulty = act.defaultDiff,
        label = act.title .. " (" .. (attrInfo.label or useAttr) .. ")",
    }, fc, dlg)
end

function Bridge.rollNuminaAction(sheet, numinaId, firecastApi, dialogsApi)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)
    local nid = numinaId or sheet.numina_id or "true_faith"
    local dots = safeInt(sheet["numina_" .. nid] or sheet.numina_nivel, 0)
    local entry = V20.MeritsFlawsCatalog.NUMINA[nid]
    local attrInfo = Bridge.resolvePoolTrait(sheet, entry and entry.poolAttr or "attr_fdv_ref")
    local act = V20.BackgroundsEngine.buildNuminaRoll(nid, dots, attrInfo.val)
    if not act.canRoll then
        dlg.showMessage(act.title or "Numina sem pontos para rolar.")
        return { ok = false, error = act.title }
    end
    return Bridge.rollFromSheet(sheet, {
        rawPool = act.pool,
        difficulty = act.defaultDiff,
        ignoreWoundPenalty = (nid == "true_faith"),
        label = "Numina: " .. act.title,
    }, fc, dlg)
end

function Bridge.rollAllyOrRetainer(sheet, slotIdx, firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)
    local name = sheet["lacaio" .. slotIdx .. "_nome"] or ("Aliado/Lacaio #" .. tostring(slotIdx))
    local pool = math.max(1, safeInt(sheet["lacaio" .. slotIdx .. "_parada"], 3))
    return Bridge.rollFromSheet(sheet, {
        rawPool = pool,
        difficulty = 6,
        ignoreWoundPenalty = true,
        skipClanWeakness = true,
        label = "Ação de " .. name,
    }, firecastApi, dialogsApi)
end

function Bridge.rollWeaponAttack(sheet, slotIdx, firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)
    local wName = sheet["arma" .. slotIdx .. "_nome"]
    if type(wName) ~= "string" or wName == "" then wName = "Ataque #" .. tostring(slotIdx) end
    local attrId = sheet["arma" .. slotIdx .. "_attr"] or "attr_destreza"
    local habId = sheet["arma" .. slotIdx .. "_hab"] or "hab_briga"
    local diff = safeInt(sheet["arma" .. slotIdx .. "_dif"], 6)
    local dmg = safeInt(sheet["arma" .. slotIdx .. "_dano"], 2)
    local dtype = sheet["arma" .. slotIdx .. "_tipo"] or "bashing"
    return Bridge.rollFromSheet(sheet, {
        attrId = attrId,
        habId = habId,
        difficulty = diff,
        label = string.format("Ataque: %s (Dano base %d %s)", wName, dmg, dtype),
    }, firecastApi, dialogsApi)
end

function Bridge.executeCombatManeuver(sheet, opts, firecastApi, dialogsApi)
    if type(sheet) ~= "table" then return { ok = false, error = "Ficha inválida." } end
    opts, firecastApi, dialogsApi = normalizeOptsAndApis(opts, firecastApi, dialogsApi)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)

    local discList = Bridge.collectDisciplines(sheet)
    local cMods = V20.DisciplinesEngine.computeCombatModifiers(Bridge.sheetToEngineState(sheet), discList)
    local activeBuffs = Bridge.deserializeBuffs(sheet)

    local rawManId = opts.maneuverId or opts.cmb_manobra_id or sheet.cmb_manobra_id
    local maneuverId = (type(rawManId) == "string" and rawManId:match("%S")) and rawManId or "strike"
    local weaponSlot = math.max(1, math.min(4, safeInt(opts.weaponSlot or opts.cmb_arma_slot or sheet.cmb_arma_slot, 1)))
    local totalNormalActions = math.max(1, math.min(5, safeInt(opts.totalNormalActions or opts.cmb_acoes_normais or sheet.cmb_acoes_normais, 1)))
    local actionNumber = math.max(1, math.min(5, safeInt(opts.actionNumber or opts.cmb_acao_ordem or sheet.cmb_acao_ordem, 1)))
    local rawLowest = (opts.lowestBasePool ~= nil) and opts.lowestBasePool
        or ((opts.cmb_menor_parada ~= nil) and opts.cmb_menor_parada or sheet.cmb_menor_parada)
    local lowestBasePool = safeNonNegInt(rawLowest, 0)
    local isCelerityAction = (opts.isCelerityAction ~= nil) and isTrue(opts.isCelerityAction)
        or ((opts.cmb_acao_rapidez ~= nil) and isTrue(opts.cmb_acao_rapidez) or isTrue(sheet.cmb_acao_rapidez))
    local rawAim = (opts.aimTurns ~= nil) and opts.aimTurns
        or ((opts.cmb_mira_turnos ~= nil) and opts.cmb_mira_turnos or sheet.cmb_mira_turnos)
    local aimTurns = safeNonNegInt(rawAim, 0)
    local hasScope = (opts.hasScope ~= nil) and isTrue(opts.hasScope)
        or ((opts.cmb_tem_luneta ~= nil) and isTrue(opts.cmb_tem_luneta) or isTrue(sheet.cmb_tem_luneta))
    local rawLoc = opts.targetLocation or opts.cmb_alvo_localizado or sheet.cmb_alvo_localizado
    local targetLocation = (type(rawLoc) == "string" and rawLoc:match("%S")) and rawLoc or "nenhum"
    local rawCover = opts.coverLevel or opts.cmb_cobertura or sheet.cmb_cobertura
    local coverLevel = (type(rawCover) == "string" and rawCover:match("%S")) and rawCover or "nenhuma"
    local rawFlank = opts.flankMode or opts.cmb_posicao or sheet.cmb_posicao
    local flankMode = (type(rawFlank) == "string" and rawFlank:match("%S")) and rawFlank or "frontal"
    local rawDefSucc = (opts.defenseSuccesses ~= nil) and opts.defenseSuccesses
        or ((opts.cmb_defesa_alvo_sucessos ~= nil) and opts.cmb_defesa_alvo_sucessos or sheet.cmb_defesa_alvo_sucessos)
    local defenseSuccesses = safeNonNegInt(rawDefSucc, 0)
    local rawTgtStr = (opts.targetStrength ~= nil) and opts.targetStrength
        or ((opts.cmb_forca_alvo ~= nil) and opts.cmb_forca_alvo or sheet.cmb_forca_alvo)
    local targetStrength = safeNonNegInt(rawTgtStr, 2)
    local rawPriorDef = (opts.priorDefensesThisTurn ~= nil) and opts.priorDefensesThisTurn
        or ((opts.cmb_defesas_feitas_turno ~= nil) and opts.cmb_defesas_feitas_turno or sheet.cmb_defesas_feitas_turno)
    local priorDefensesThisTurn = safeNonNegInt(rawPriorDef, 0)
    local inGrapple = (opts.inGrapple ~= nil) and isTrue(opts.inGrapple)
        or ((opts.em_agarrao ~= nil) and isTrue(opts.em_agarrao) or isTrue(sheet.em_agarrao))

    local weapon = opts.weapon
    if type(weapon) ~= "table" then
        weapon = {
            nome = sheet["arma" .. weaponSlot .. "_nome"],
            attr = sheet["arma" .. weaponSlot .. "_attr"],
            hab = sheet["arma" .. weaponSlot .. "_hab"],
            dif = tonumber(sheet["arma" .. weaponSlot .. "_dif"]),
            dano = tonumber(sheet["arma" .. weaponSlot .. "_dano"]),
            tipo = sheet["arma" .. weaponSlot .. "_tipo"],
            municao = sheet["arma" .. weaponSlot .. "_municao"],
        }
    end

    local attrs = {}
    for _, aid in ipairs(V20.Traits.ATTRIBUTE_ORDER) do
        attrs[aid] = Bridge.resolvePoolTrait(sheet, aid, cMods).val
    end
    attrs.attr_destreza = safeNonNegInt(attrs.attr_destreza, 0) + safeNonNegInt(cMods.passiveCelerityDice, 0)

    local habs = {}
    for _, hid in ipairs(V20.Traits.ABILITY_ORDER) do
        habs[hid] = Bridge.resolvePoolTrait(sheet, hid, cMods).val
    end
    for i = 1, 4 do
        habs["hab_extra" .. i .. "_val"] = safeNonNegInt(sheet["hab_extra" .. i .. "_val"], 0)
    end

    local mSpec = V20.CombatManeuversCatalog.MANEUVERS[maneuverId]
    local previewAttrId = mSpec and mSpec.defaultAttr or "attr_destreza"
    if mSpec and mSpec.usesSlotTraits and type(weapon.attr) == "string" and weapon.attr:match("%S") then
        previewAttrId = weapon.attr
    end
    if type(opts.attrId) == "string" and opts.attrId:match("%S") then
        previewAttrId = opts.attrId
    end
    local potenceAttackBonus = (previewAttrId == "attr_forca") and safeNonNegInt(cMods.passivePotenceDice, 0) or 0

    local naturalAgg = (opts.naturalAggravated ~= nil)
        and isTrue(opts.naturalAggravated)
        or ((activeBuffs.prot_claws ~= nil) or (activeBuffs.prot_beast ~= nil) or (activeBuffs.serp_tongue ~= nil))
    local weaponAgg = (opts.weaponAggravated ~= nil)
        and isTrue(opts.weaponAggravated)
        or (activeBuffs.quie_baal ~= nil)

    local stOverride = (opts.storytellerOverride ~= nil and isTrue(opts.storytellerOverride))
        or (isTrue(sheet.narrador_override) and Bridge.isStoryteller(sheet, fc))
    local ignoreWound = (opts.ignoreWoundPenalty ~= nil and isTrue(opts.ignoreWoundPenalty))
        or isTrue(sheet.roll_ignorar_ferimento)
        or isTrue(sheet.em_frenesi)
    local celerityLeft = safeNonNegInt(
        opts.celerityActionsLeft ~= nil and opts.celerityActionsLeft or sheet.rapidez_acoes_extras,
        0
    )

    local prep = V20.CombatManeuvers.prepareManeuverRoll({
        actorName = sheet.nome,
        isVampire = Bridge.isVampireSheet(sheet),
        maneuverId = maneuverId,
        attrId = opts.attrId,
        habId = opts.habId,
        attrs = attrs,
        habs = habs,
        weapon = weapon,
        inGrapple = inGrapple,
        isCelerityAction = isCelerityAction,
        celerityActionsLeft = celerityLeft,
        totalNormalActions = totalNormalActions,
        actionNumber = actionNumber,
        lowestBasePool = lowestBasePool,
        aimTurns = aimTurns,
        hasScope = hasScope,
        targetLocation = targetLocation,
        coverLevel = coverLevel,
        flankMode = flankMode,
        priorDefensesThisTurn = priorDefensesThisTurn,
        bonusDice = safeInt(opts.bonusDice ~= nil and opts.bonusDice or sheet.cmb_bonus_dados, 0) + potenceAttackBonus,
        extraDiffMod = safeInt(opts.extraDiffMod, 0),
        woundPenalty = safeInt(sheet.penalidade_ferimento, 0),
        armorDexPenalty = safeInt(opts.armorDexPenalty ~= nil and opts.armorDexPenalty or sheet.armadura_penalidade, 0),
        clanDiceMod = 0,
        naturalAggravated = naturalAgg,
        weaponAggravated = weaponAgg,
        emFrenesi = isTrue(sheet.em_frenesi),
        ignoreWoundPenalty = ignoreWound,
        storytellerOverride = stOverride,
    })

    if not prep.canRoll then
        dlg.showMessage(prep.reason or "Manobra bloqueada pelas regras V20.")
        return { ok = false, error = prep.reason, prep = prep }
    end

    local atkAutoPot = (prep.attrUsed == "attr_forca" and safeNonNegInt(cMods.activePotenceAuto, 0) > 0)
        and safeNonNegInt(cMods.activePotenceAuto, 0) or 0
    local lastPost = nil

    local res = Bridge.rollFromSheet(sheet, {
        rawPool = prep.poolBeforeClanDivisor,
        difficulty = prep.difficulty,
        resolvedAttrId = prep.attrUsed,
        resolvedHabId = prep.habUsed,
        woundPenaltyAlreadyApplied = true,
        ignoreWoundPenalty = ignoreWound,
        forbidZeroPool = (not isTrue(opts.spendWillpower)),
        autoSuccesses = atkAutoPot,
        spendWillpower = opts.spendWillpower,
        specialty = opts.specialty,
        extraNotes = prep.notes,
        label = opts.label or ("Manobra: " .. tostring(prep.maneuverName)),
        onEvaluated = function(evalRes)
            if prep.isDefense then
                return nil
            end
            local post = V20.CombatManeuvers.computePostAttackDamage({
                maneuver = prep,
                attackSuccesses = evalRes.totalSuccesses,
                attackOutcome = evalRes.outcome,
                defenseSuccesses = defenseSuccesses,
                targetStrength = targetStrength,
                passivePotenceDice = safeNonNegInt(cMods.passivePotenceDice, 0),
                autoPotenceSuccesses = safeNonNegInt(cMods.activePotenceAuto, 0),
            })
            lastPost = post
            if post.setsGrapple then
                sheet.em_agarrao = true
            end
            if post.hit and not post.noDamage then
                sheet.cmb_dano_pendente_ativo = true
                sheet.cmb_dano_pendente_parada = post.damageDicePool
                sheet.cmb_dano_pendente_auto = post.autoSuccesses
                sheet.cmb_dano_pendente_tipo = post.damageType
                sheet.cmb_dano_pendente_estaca = post.isStaking
                sheet.cmb_dano_pendente_cabeca = post.isHeadshot
                sheet.cmb_dano_pendente_manobra = prep.maneuverName
                sheet.cmb_dano_pendente_resumo = post.summary
            else
                sheet.cmb_dano_pendente_ativo = false
                sheet.cmb_dano_pendente_resumo = post.summary
            end
            return post.summary
        end,
    }, fc, dlg)

    if res and res.ok ~= false then
        if prep.consumeCelerityAction then
            sheet.rapidez_acoes_extras = math.max(0, safeNonNegInt(sheet.rapidez_acoes_extras, 0) - 1)
        end
        if prep.isDefense then
            sheet.cmb_defesas_feitas_turno = safeNonNegInt(sheet.cmb_defesas_feitas_turno, 0) + 1
        end
        res.prep = prep
        res.post = lastPost
    end

    return res
end

function Bridge.rollPendingCombatDamage(sheet, firecastApi, dialogsApi)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    if type(sheet) ~= "table" or not isTrue(sheet.cmb_dano_pendente_ativo) then
        local err = "Não há parada de dano encadeado pendente. Execute e acerte uma manobra de ataque primeiro."
        dlg.showMessage(err)
        return { ok = false, error = err }
    end

    Bridge.syncDerivedFields(sheet)
    local dmgPool = safeNonNegInt(sheet.cmb_dano_pendente_parada, 0)
    local dmgAuto = safeNonNegInt(sheet.cmb_dano_pendente_auto, 0)
    local dtype = (type(sheet.cmb_dano_pendente_tipo) == "string" and sheet.cmb_dano_pendente_tipo ~= "")
        and sheet.cmb_dano_pendente_tipo or "bashing"
    local isStaking = isTrue(sheet.cmb_dano_pendente_estaca)
    local mName = (type(sheet.cmb_dano_pendente_manobra) == "string" and sheet.cmb_dano_pendente_manobra ~= "")
        and sheet.cmb_dano_pendente_manobra or "Ataque"

    return Bridge.rollFromSheet(sheet, {
        rawPool = dmgPool,
        autoSuccesses = dmgAuto,
        difficulty = 6,
        ignoreWoundPenalty = true,
        forbidWillpower = true,
        skipClanWeakness = true,
        allowZeroPoolWithAuto = true,
        label = string.format("Dano Encadeado (%s — %s)", mName, dtype),
        onEvaluated = function(evalRes)
            sheet.cmb_dano_pendente_ativo = false
            local out = "Dano Bruto (" .. tostring(dtype) .. "): " .. tostring(evalRes.totalSuccesses) .. " nível(is)"
            if isStaking and evalRes.totalSuccesses >= 3 then
                out = out .. " | 🪵 ESTACA NO CORAÇÃO: 3+ níveis (se restarem >= 3 após Absorção, vampiro entra em Paralisia/Torpor!)"
            end
            sheet.cmb_dano_pendente_resumo = out
            return out
        end,
    }, fc, dlg)
end

local AUDIT_CACHE = setmetatable({}, { __mode = "k" })

function Bridge.logAudit(sheet, ndbApi, firecastApi, eventType, description, costXp, status, targetField, newVal)
    if type(sheet) ~= "table" then return nil end
    local ndb = ndbApi or _G.NDB
    local stamp = os.date("%Y-%m-%d %H:%M:%S")
    local author = Bridge.getCurrentLogin(sheet, firecastApi)
    local st = status or "aprovado"
    local cost = safeInt(costXp, 0)

    local entry = {
        data_hora = stamp,
        autor_login = author,
        tipo_evento = eventType or "registro",
        descricao = description or "",
        custo_xp = cost,
        status = st,
        campo_alvo = targetField,
        novo_valor = newVal,
    }

    if type(AUDIT_CACHE[sheet]) ~= "table" then
        AUDIT_CACHE[sheet] = {}
    end
    table.insert(AUDIT_CACHE[sheet], entry)
    if not rawget(sheet, "__nodeFacadeFlag") then
        rawset(sheet, "_audit_entries", AUDIT_CACHE[sheet])
    end

    if ndb and ndb.createChildNode and sheet.rclAuditoriaXP_node then
        local ch = ndb.createChildNode(sheet.rclAuditoriaXP_node)
        if type(ch) == "table" then
            for k, v in pairs(entry) do ch[k] = v end
        end
    end

    local line = string.format(
        "[%s] (%s) %s — %s | XP: %d | Status: %s",
        stamp, author, entry.tipo_evento, entry.descricao, cost, string.upper(st)
    )
    local prev = (type(sheet.auditoria_xp_log) == "string" and sheet.auditoria_xp_log ~= "") and (sheet.auditoria_xp_log .. "\n") or ""
    sheet.auditoria_xp_log = prev .. line
    return entry
end

local function peelFreebiesFromGroups(groups, targets, freebieDots)
    local s = { groups[1] or 0, groups[2] or 0, groups[3] or 0 }
    table.sort(s, function(a, b) return a > b end)
    local rem = math.max(0, safeInt(freebieDots, 0))
    for i = 1, 3 do
        local tgt = targets[i] or 0
        local excess = math.max(0, s[i] - tgt)
        local take = math.min(rem, excess)
        s[i] = s[i] - take
        rem = rem - take
    end
    if rem > 0 then
        s[3] = s[3] - rem
    end
    return s
end

function Bridge.validateCreationOnSheet(sheet, ndbApi, firecastApi, dialogsApi, lockIfValid)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet, ndbApi)

    local isVamp = Bridge.isVampireSheet(sheet)
    local profile = "vampire_neonate"
    if not isVamp then
        profile = (sheet.mortal_perfil == "heroico_753") and "mortal_heroic_753" or "mortal_standard_643"
    end
    local profSpec = V20.Creation.PROFILES[profile] or V20.Creation.PROFILES.vampire_neonate

    local phys = math.max(0, safeInt(sheet.attr_forca, 1) - 1)
        + math.max(0, safeInt(sheet.attr_destreza, 1) - 1)
        + math.max(0, safeInt(sheet.attr_vigor, 1) - 1)

    local socialFreeBase = isVamp and V20.ClanWeaknesses.getSocialBaseFreeDots(sheet.cla_id) or 3
    local rawCar = math.max(1, safeInt(sheet.attr_carisma, 1))
    local rawMan = math.max(1, safeInt(sheet.attr_manipulacao, 1))
    local rawApp = (isVamp and sheet.cla_id == "nosferatu")
        and math.max(0, safeInt(sheet.attr_aparencia, 0))
        or math.max(1, safeInt(sheet.attr_aparencia, 1))
    local soc = math.max(0, (rawCar + rawMan + rawApp) - socialFreeBase)

    local ment = math.max(0, safeInt(sheet.attr_percepcao, 1) - 1)
        + math.max(0, safeInt(sheet.attr_inteligencia, 1) - 1)
        + math.max(0, safeInt(sheet.attr_raciocinio, 1) - 1)

    local talents, skills, knowledges, maxHab, excessAbove3 = 0, 0, 0, 0, 0
    for _, hid in ipairs(V20.Traits.ABILITY_ORDER) do
        local meta = V20.Traits.ABILITIES[hid]
        local v = math.max(0, safeInt(sheet[hid], 0))
        if v > maxHab then maxHab = v end
        if v > 3 then excessAbove3 = excessAbove3 + (v - 3) end
        if meta.category == "talents" then
            talents = talents + v
        elseif meta.category == "skills" then
            skills = skills + v
        else
            knowledges = knowledges + v
        end
    end

    local freebieAttr = safeInt(sheet.freebie_attributes, 0)
    local freebieHab = safeInt(sheet.freebie_abilities, 0)
    local baseAttrGroups = peelFreebiesFromGroups({ phys, soc, ment }, profSpec.attr, freebieAttr)
    local baseHabGroups = peelFreebiesFromGroups({ talents, skills, knowledges }, profSpec.abilities, freebieHab)
    local effMaxBaseHab = (excessAbove3 <= math.max(0, freebieHab)) and math.min(maxHab, 3) or maxHab

    local discDots = 0
    local freeGhoulPotence = (not isVamp and isTrue(sheet.isGhoul)) and safeNonNegInt(sheet.ghoulPotence, 0) or 0
    for _, d in ipairs(Bridge.collectDisciplines(sheet, ndbApi)) do
        local n = math.max(0, safeInt(d.nivel, 0))
        if d.disc_id == "potence" and freeGhoulPotence > 0 then
            n = math.max(0, n - freeGhoulPotence)
        end
        discDots = discDots + n
    end
    if isVamp then
        for secIdx = 1, 4 do
            discDots = discDots + safeNonNegInt(sheet["bm_sec" .. secIdx .. "_nivel"], 0)
        end
    end

    local bgDots = 0
    for _, b in ipairs(Bridge.collectBackgrounds(sheet, ndbApi)) do
        bgDots = bgDots + math.max(0, safeInt(b.nivel, 0))
    end

    local virtDots = math.max(0, safeInt(sheet.virtude1_val, 1) - 1)
        + math.max(0, safeInt(sheet.virtude2_val, 1) - 1)
        + math.max(0, safeInt(sheet.virtude3_val, 1) - 1)

    local mfAgg = V20.BackgroundsEngine.aggregateMeritsFlaws(Bridge.collectMeritsFlaws(sheet, ndbApi))

    local res = V20.Creation.validate({
        profile = profile,
        cla_id = sheet.cla_id,
        attr_aparencia = (sheet.cla_id == "nosferatu") and safeInt(sheet.attr_aparencia, 0) or safeInt(sheet.attr_aparencia, 1),
        attrGroups = baseAttrGroups,
        abilityGroups = baseHabGroups,
        maxBaseAbility = effMaxBaseHab,
        baseDisciplines = discDots - safeInt(sheet.freebie_disciplines, 0),
        baseBackgrounds = bgDots - safeInt(sheet.freebie_backgrounds, 0),
        baseVirtues = virtDots - safeInt(sheet.freebie_virtues, 0),
        flawsBonus = mfAgg.effectiveFlawBonus,
        freebiePurchases = {
            attributes = freebieAttr,
            abilities = freebieHab,
            disciplines = safeInt(sheet.freebie_disciplines, 0),
            backgrounds = safeInt(sheet.freebie_backgrounds, 0),
            virtues = safeInt(sheet.freebie_virtues, 0),
            morality = safeInt(sheet.freebie_morality, 0),
            willpower = safeInt(sheet.freebie_willpower, 0),
            merits = mfAgg.totalMeritCost,
        },
    })

    if isVamp then
        local cwReq = V20.ClanWeaknesses.validateCreationRequirements({
            cla_id = sheet.cla_id,
            attr_aparencia = (sheet.cla_id == "nosferatu") and safeInt(sheet.attr_aparencia, 0) or safeInt(sheet.attr_aparencia, 1),
            malkav_perturbacao = sheet.malkav_perturbacao,
            ventrue_presa_restrita = sheet.ventrue_presa_restrita,
            ravnos_vicio_descricao = sheet.ravnos_vicio_descricao,
        })
        if not cwReq.valid then
            for _, errMsg in ipairs(cwReq.errors) do
                if not (sheet.cla_id == "nosferatu" and errMsg:find("Nosferatu") and (#res.errors > 0 and table.concat(res.errors, " "):find("Nosferatu"))) then
                    table.insert(res.errors, errMsg)
                end
            end
            res.valid = false
        end

        local seenSecPaths = {}
        for secIdx = 1, 4 do
            local secLvl = safeNonNegInt(sheet["bm_sec" .. secIdx .. "_nivel"], 0)
            if secLvl > 0 then
                local trad = resolveSecondaryTradition(sheet, secIdx)
                local secPathId = sheet["bm_sec" .. secIdx .. "_path_id"] or ""
                if secPathId ~= "" and seenSecPaths[secPathId] ~= nil then
                    table.insert(res.errors, string.format("Linha Secundária '%s' duplicada nos slots #%d e #%d.", secPathId, seenSecPaths[secPathId], secIdx))
                    res.valid = false
                elseif secPathId ~= "" then
                    seenSecPaths[secPathId] = secIdx
                end
                if secPathId ~= "" and V20.BloodMagicEngine.getPathTable(trad, secPathId) == nil then
                    table.insert(res.errors, string.format("Linha Secundária #%d incompatível com a tradição escolhida.", secIdx))
                    res.valid = false
                else
                    local parentDots = getDisciplineDots(sheet, trad, ndbApi)
                    local primId = (trad == "necromancy")
                        and ((type(sheet.bm_necro_prim_id) == "string" and sheet.bm_necro_prim_id ~= "") and sheet.bm_necro_prim_id or "sepulchre_path")
                        or ((type(sheet.bm_thau_prim_id) == "string" and sheet.bm_thau_prim_id ~= "") and sheet.bm_thau_prim_id or "path_of_blood")
                    local vSec = V20.BloodMagicEngine.validateSecondaryPathUpgrade({
                        parentDiscDots = parentDots,
                        primaryPathId = primId,
                        secondaryPathId = secPathId,
                        targetLevel = secLvl,
                    })
                    if not vSec.ok then
                        table.insert(res.errors, vSec.error)
                        res.valid = false
                    end
                end
            end
        end
    end

    if res.valid then
        sheet.criacao_resumo_status = string.format(
            "✅ Criação V20 válida! Bônus gastos: %d/%d (Restante: %d).",
            res.freebiesSpent, res.freebiesAvailable, res.freebiesRemaining
        )
        if isTrue(lockIfValid) then
            sheet.modo_ficha = "jogo"
            Bridge.logAudit(sheet, ndbApi, fc, "modo_jogo", "Criação validada e concluída -> Modo Jogo", 0, "aprovado", "modo_ficha", "jogo")
        end
    else
        sheet.criacao_resumo_status = "⚠️ Pendências V20: " .. table.concat(res.errors, " | ")
        if isTrue(lockIfValid) then
            if isTrue(sheet.narrador_override) and Bridge.isStoryteller(sheet, fc) then
                sheet.modo_ficha = "jogo"
                Bridge.logAudit(sheet, ndbApi, fc, "override_narrador", "Transição p/ Modo Jogo com Exceção do Narrador", 0, "aprovado", "modo_ficha", "jogo")
            else
                dlg.showMessage(sheet.criacao_resumo_status)
            end
        end
    end

    return res
end

local function inferTraitKindFromField(sheet, campo)
    if type(campo) ~= "string" or campo == "" then
        return nil, nil, nil
    end
    if V20.Traits.ATTRIBUTES[campo] ~= nil then
        return "attribute", nil, nil
    end
    if V20.Traits.ABILITIES[campo] ~= nil or campo:match("^hab_extra[1-4]_val$") then
        return "ability", nil, nil
    end
    local slotIdx = campo:match("^disc_slot([1-9])_nivel$")
    if slotIdx then
        local discId = (type(sheet) == "table") and sheet["disc_slot" .. slotIdx .. "_id"] or nil
        return "discipline", tonumber(slotIdx), discId
    end
    local directDisc = campo:match("^disc_([a-z_]+)$")
    if directDisc and V20.DisciplinesCatalog.DISCIPLINES[directDisc] ~= nil then
        return "discipline", nil, directDisc
    end
    if campo:match("^bm_sec[1-4]_nivel$") or campo:match("^trilha_sec_%d+$") or campo:match("^sec_path_[a-z0-9_]+$") then
        return "secondary_path", nil, nil
    end
    if campo == "virtude1_val" or campo == "virtude2_val" or campo == "virtude3_val" then
        return "virtue", nil, nil
    end
    if campo == "moralidade_val" then
        return "morality", nil, nil
    end
    if campo == "fdv_perm" then
        return "willpower", nil, nil
    end
    return nil, nil, nil
end

local function getEffectiveFieldRatingForXP(sheet, campo, traitKind, discId)
    if type(sheet) ~= "table" or type(campo) ~= "string" then
        return 0
    end
    if traitKind == "discipline" and isTrue(sheet.isGhoul) and discId == "potence" then
        return math.max(safeNonNegInt(sheet[campo], 0), safeNonNegInt(sheet.ghoulPotence, 0))
    end
    if sheet[campo] == nil then
        if traitKind == "attribute" then
            return (sheet.cla_id == "nosferatu" and campo == "attr_aparencia") and 0 or 1
        elseif traitKind == "virtue" or traitKind == "willpower" then
            return 1
        end
    end
    return safeNonNegInt(sheet[campo], 0)
end

local function checkV20TraitCeiling(sheet, traitKind, campo, targetVal)
    if traitKind == "attribute" then
        if sheet.cla_id == "nosferatu" and campo == "attr_aparencia" and targetVal > 0 then
            return false, "Nosferatu não pode aumentar Aparência acima de 0 (V20, p. 60)."
        end
        local cap = safeInt(sheet.atributo_max_geracao, 5)
        if targetVal > cap then
            return false, string.format("Teto máximo de Atributo atingido para a geração (%d).", cap)
        end
    elseif traitKind == "ability" then
        local cap = math.max(5, safeInt(sheet.atributo_max_geracao, 5))
        if targetVal > cap then
            return false, string.format("Teto máximo de Habilidade atingido (%d).", cap)
        end
    elseif traitKind == "discipline" then
        local cap = safeInt(sheet.disciplina_max_geracao, 5)
        if cap <= 0 then
            return false, "Mortal humano sem vitae vampírica não pode adquirir Disciplinas (teto 0)."
        end
        if targetVal > cap then
            return false, string.format("Teto máximo de Disciplina atingido (%d).", cap)
        end
    elseif traitKind == "secondary_path" then
        local cap = math.min(5, safeInt(sheet.disciplina_max_geracao, 5))
        if cap <= 0 or targetVal > cap then
            return false, string.format("Teto máximo de Linha Secundária atingido (%d).", math.max(0, cap))
        end
    elseif traitKind == "virtue" then
        if targetVal > 5 then
            return false, "Virtudes possuem teto máximo igual a 5 na V20."
        end
    elseif traitKind == "morality" then
        if targetVal > 10 then
            return false, "Moralidade possui teto máximo igual a 10 na V20."
        end
    elseif traitKind == "willpower" then
        if targetVal > 10 then
            return false, "Força de Vontade permanente possui teto máximo igual a 10 na V20."
        end
    end
    return true, nil
end

local function validateBmSecFieldUpgrade(sheet, campo, targetVal, ndbApi)
    local secIdx = (type(campo) == "string") and tonumber(campo:match("^bm_sec([1-4])_nivel$")) or nil
    if not secIdx then return true, nil end
    local trad = resolveSecondaryTradition(sheet, secIdx)
    local secPathId = sheet["bm_sec" .. secIdx .. "_path_id"] or ""
    if secPathId ~= "" then
        for otherIdx = 1, 4 do
            if otherIdx ~= secIdx
                and safeNonNegInt(sheet["bm_sec" .. otherIdx .. "_nivel"], 0) > 0
                and (sheet["bm_sec" .. otherIdx .. "_path_id"] or "") == secPathId
            then
                return false, string.format("A Linha Secundária '%s' já está adquirida no slot secundário #%d.", secPathId, otherIdx)
            end
        end
    end
    if secPathId ~= "" and V20.BloodMagicEngine.getPathTable(trad, secPathId) == nil then
        return false, "A Linha Secundária selecionada não pertence à tradição escolhida."
    end
    local parentDots = getDisciplineDots(sheet, trad, ndbApi)
    local primId = (trad == "necromancy")
        and ((type(sheet.bm_necro_prim_id) == "string" and sheet.bm_necro_prim_id ~= "") and sheet.bm_necro_prim_id or "sepulchre_path")
        or ((type(sheet.bm_thau_prim_id) == "string" and sheet.bm_thau_prim_id ~= "") and sheet.bm_thau_prim_id or "path_of_blood")
    local vRes = V20.BloodMagicEngine.validateSecondaryPathUpgrade({
        parentDiscDots = parentDots,
        primaryPathId = primId,
        secondaryPathId = secPathId,
        targetLevel = targetVal,
    })
    if not vRes.ok then
        return false, vRes.error
    end
    return true, nil
end

function Bridge.submitOrApproveXP(sheet, action, payload, ndbApi, firecastApi, dialogsApi)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet, ndbApi)

    local act = action or "submit"
    local isMaster = Bridge.isStoryteller(sheet, fc)
    local stOverride = isTrue(sheet.narrador_override) and isMaster
    local login = Bridge.getCurrentLogin(sheet, fc)

    local function makeXpSnapshot(targetField, overrideRating)
        local snap = {
            cla_id = sheet.cla_id,
            xp_total = safeNonNegInt(sheet.xp_total, 0),
            xp_gasto = safeNonNegInt(sheet.xp_gasto, 0),
            xp_exige_aprovacao = sheet.xp_exige_aprovacao,
        }
        if type(targetField) == "string" and targetField ~= "" then
            if overrideRating ~= nil then
                snap[targetField] = overrideRating
            else
                snap[targetField] = sheet[targetField]
            end
        end
        return snap
    end

    if act == "submit" then
        if sheet.xp_pendente_status == "pendente" then
            local err = "Já existe uma solicitação de XP pendente aguardando o Narrador."
            dlg.showMessage(err)
            return { ok = false, error = err }
        end

        local campo = (type(payload) == "table") and payload.field or sheet.xp_loja_campo
        local rawKind = (type(payload) == "table") and payload.traitKind or sheet.xp_loja_tipo
        local rawCat = (type(payload) == "table") and payload.costCategory or sheet.xp_loja_cat_custo
        local rawLabel = (type(payload) == "table") and payload.label
            or ((type(sheet.xp_loja_descricao) == "string" and sheet.xp_loja_descricao ~= "") and sheet.xp_loja_descricao or campo)
        local author = ((type(payload) == "table") and payload.author) or login

        local inferredKind, slotIdx, discId = inferTraitKindFromField(sheet, campo)
        if inferredKind == nil then
            local err = "Campo alvo inválido para evolução por XP: " .. tostring(campo)
            dlg.showMessage(err)
            return { ok = false, error = err }
        end

        local finalKind = inferredKind
        if rawKind ~= nil and rawKind ~= "" and rawKind ~= "auto" then
            local compatibleSecPath = (rawKind == "secondary_path" and inferredKind == "discipline")
            if rawKind ~= inferredKind and not compatibleSecPath then
                local err = string.format(
                    "Tipo de característica '%s' incompatível com o campo '%s' (esperado '%s').",
                    tostring(rawKind), tostring(campo), inferredKind
                )
                dlg.showMessage(err)
                return { ok = false, error = err }
            end
            finalKind = rawKind
        elseif slotIdx and sheet["disc_slot" .. slotIdx .. "_cat"] == "linha_secundaria" then
            finalKind = "secondary_path"
        end

        local finalCat = rawCat
        if finalKind == "discipline" and (finalCat == nil or finalCat == "" or finalCat == "auto") then
            local slotCat = slotIdx and sheet["disc_slot" .. slotIdx .. "_cat"] or nil
            local hasAddDisc = isTrue(sheet.tem_disc_adicional)
            local clanForClass = Bridge.isVampireSheet(sheet) and (sheet.cla_id or "brujah") or (sheet.cla_id or "none")
            if type(discId) == "string" and discId ~= "" then
                local classified = V20.DisciplinesEngine.classifyCostCategory(clanForClass, discId, hasAddDisc)
                if sheet.cla_id == "caitiff" then
                    finalCat = "caitiff"
                elseif classified == "cla" or slotCat == "cla" then
                    finalCat = "cla"
                elseif slotCat == "caitiff" then
                    finalCat = "caitiff"
                else
                    finalCat = classified
                end
            elseif slotCat == "cla" or slotCat == "caitiff" or slotCat == "fora_cla" then
                finalCat = slotCat
            else
                finalCat = V20.DisciplinesEngine.classifyCostCategory(clanForClass, discId, hasAddDisc)
            end
        end

        local curRating
        if type(payload) == "table" and payload.currentRating ~= nil then
            curRating = safeNonNegInt(payload.currentRating, 0)
        else
            curRating = getEffectiveFieldRatingForXP(sheet, campo, finalKind, discId)
        end

        if not stOverride then
            local okCeil, ceilErr = checkV20TraitCeiling(sheet, finalKind, campo, curRating + 1)
            if not okCeil then
                dlg.showMessage(ceilErr)
                return { ok = false, error = ceilErr }
            end
            local okSec, secErr = validateBmSecFieldUpgrade(sheet, campo, curRating + 1, ndbApi)
            if not okSec then
                dlg.showMessage(secErr)
                return { ok = false, error = secErr }
            end
        end

        local req = {
            traitKind = finalKind,
            field = campo,
            currentRating = curRating,
            costCategory = finalCat,
            label = rawLabel,
            author = author,
        }

        local res = V20.Experience.submitUpgrade(makeXpSnapshot(req.field, curRating), req, {
            isMestre = isMaster,
            storytellerOverride = stOverride,
        })
        if not res.ok then
            dlg.showMessage(res.error or "Falha na compra de XP.")
            return res
        end

        sheet.xp_gasto = res.newState.xp_gasto
        if req.field and res.newState[req.field] ~= nil then
            sheet[req.field] = res.newState[req.field]
        end

        local e = res.auditEntry
        if e.status == "pendente" then
            sheet.xp_pendente_campo = e.campo_alvo
            sheet.xp_pendente_novo_val = e.novo_valor
            sheet.xp_pendente_custo = e.custo_xp
            sheet.xp_pendente_desc = e.descricao
            sheet.xp_pendente_autor = e.autor_login
            sheet.xp_pendente_status = "pendente"
        else
            sheet.xp_pendente_status = "nenhum"
        end

        Bridge.syncDerivedFields(sheet, ndbApi)
        Bridge.logAudit(sheet, ndbApi, fc, e.tipo_evento, tostring(e.descricao) .. " -> " .. tostring(e.novo_valor), e.custo_xp, e.status, e.campo_alvo, e.novo_valor)
        return res
    elseif act == "approve" or act == "reject" then
        if not isMaster then
            local err = "Apenas o Narrador pode aprovar ou recusar evoluções de XP pendentes."
            dlg.showMessage(err)
            return { ok = false, error = err }
        end

        local pendingEntry = type(payload) == "table" and payload or {
            autor_login = sheet.xp_pendente_autor or "Jogador",
            tipo_evento = "evolucao_xp",
            descricao = sheet.xp_pendente_desc or sheet.xp_pendente_campo or "Evolução",
            custo_xp = safeNonNegInt(sheet.xp_pendente_custo, 0),
            campo_alvo = sheet.xp_pendente_campo,
            novo_valor = safeNonNegInt(sheet.xp_pendente_novo_val, 1),
            status = sheet.xp_pendente_status or "nenhum",
        }

        local effCur = nil
        if act == "approve" and pendingEntry.campo_alvo ~= nil and pendingEntry.campo_alvo ~= "" then
            local inferredKind, slotIdx, discId = inferTraitKindFromField(sheet, pendingEntry.campo_alvo)
            if inferredKind == nil then
                local err = "Campo alvo inválido na solicitação pendente: " .. tostring(pendingEntry.campo_alvo)
                dlg.showMessage(err)
                return { ok = false, error = err }
            end
            local kindForCeil = (slotIdx and sheet["disc_slot" .. slotIdx .. "_cat"] == "linha_secundaria") and "secondary_path" or inferredKind
            effCur = getEffectiveFieldRatingForXP(sheet, pendingEntry.campo_alvo, kindForCeil, discId)
            if not stOverride then
                local tgtPending = safeNonNegInt(pendingEntry.novo_valor, 1)
                local okCeil, ceilErr = checkV20TraitCeiling(sheet, kindForCeil, pendingEntry.campo_alvo, tgtPending)
                if not okCeil then
                    dlg.showMessage(ceilErr)
                    return { ok = false, error = ceilErr }
                end
                local okSec, secErr = validateBmSecFieldUpgrade(sheet, pendingEntry.campo_alvo, tgtPending, ndbApi)
                if not okSec then
                    dlg.showMessage(secErr)
                    return { ok = false, error = secErr }
                end
            end
        end

        local res = V20.Experience.resolvePending(makeXpSnapshot(pendingEntry.campo_alvo, effCur), pendingEntry, act == "approve", login)
        if not res.ok then
            dlg.showMessage(res.error or "Não há evolução pendente válida.")
            return res
        end

        sheet.xp_gasto = res.newState.xp_gasto
        if pendingEntry.campo_alvo and res.newState[pendingEntry.campo_alvo] ~= nil then
            sheet[pendingEntry.campo_alvo] = res.newState[pendingEntry.campo_alvo]
        end
        sheet.xp_pendente_status = res.updatedEntry.status
        Bridge.syncDerivedFields(sheet, ndbApi)
        Bridge.logAudit(
            sheet,
            ndbApi,
            fc,
            "resolucao_xp",
            tostring(res.updatedEntry.descricao) .. " (" .. tostring(res.updatedEntry.status) .. ")",
            res.updatedEntry.custo_xp,
            res.updatedEntry.status,
            res.updatedEntry.campo_alvo,
            res.updatedEntry.novo_valor
        )
        return res
    end

    return { ok = false, error = "Ação de XP desconhecida." }
end

function Bridge.endBrujahFrenzy(sheet, firecastApi, dialogsApi)
    if type(sheet) ~= "table" then return { ok = false } end
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)
    local stOverride = isTrue(sheet.narrador_override) and Bridge.isStoryteller(sheet, fc)
    local res = V20.ClanWeaknesses.endBrujahFrenzyWithWP({
        em_frenesi = sheet.em_frenesi,
        fdv_temp = safeInt(sheet.fdv_temp, 0),
        storytellerOverride = stOverride,
    })
    if not res.ok then
        dlg.showMessage(res.error or "Não foi possível encerrar o Frenesi.")
        return res
    end
    sheet.em_frenesi = false
    sheet.fdv_temp = res.newState.fdv_temp
    Bridge.syncDerivedFields(sheet)
    Bridge.notify(
        sheet,
        string.format("🔥 [%s] Encerrou o Frenesi ativo gastando 1 FdV (FdV Temp: %d/%d).",
            sheet.nome or "Personagem", safeInt(sheet.fdv_temp, 0), safeInt(sheet.fdv_perm, 5)),
        fc,
        dlg
    )
    return res
end

function Bridge.recordGangrelFrenzy(sheet, firecastApi, dialogsApi, ndbApi)
    if type(sheet) ~= "table" then return { ok = false } end
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet, ndbApi)
    local targetAttr = sheet.gangrel_attr_penalizado
    if targetAttr ~= "attr_carisma" and targetAttr ~= "attr_manipulacao" and targetAttr ~= "attr_aparencia" then
        targetAttr = "attr_carisma"
    end
    local prevAttrVal = safeNonNegInt(sheet[targetAttr], 1)
    local res = V20.ClanWeaknesses.recordGangrelFrenzy({
        gangrel_tracos_qtd = safeNonNegInt(sheet.gangrel_tracos_qtd, 0),
        gangrel_attr_penalizado = targetAttr,
        attr_carisma = safeNonNegInt(sheet.attr_carisma, 1),
        attr_manipulacao = safeNonNegInt(sheet.attr_manipulacao, 1),
        attr_aparencia = safeNonNegInt(sheet.attr_aparencia, 1),
    })
    sheet.gangrel_tracos_qtd = res.newState.gangrel_tracos_qtd
    if res.penalizedAttr ~= nil then
        sheet[res.penalizedAttr] = res.newAttrVal
        Bridge.syncDerivedFields(sheet, ndbApi)
        local attrMeta = V20.Traits.ATTRIBUTES[res.penalizedAttr]
        local attrLabel = (attrMeta and attrMeta.name) or res.penalizedAttr
        Bridge.logAudit(
            sheet,
            ndbApi,
            fc,
            "maldicao_gangrel",
            string.format("Fraqueza Gangrel (%d traços animais): %s %d -> %d", res.newState.gangrel_tracos_qtd, attrLabel, prevAttrVal, res.newAttrVal),
            0,
            "aprovado",
            res.penalizedAttr,
            res.newAttrVal
        )
        Bridge.notify(
            sheet,
            string.format("🐺 [%s] Frenesi Gangrel (%d traços animais) — Perda permanente em %s (%d -> %d)!",
                sheet.nome or "Personagem", res.newState.gangrel_tracos_qtd, attrLabel, prevAttrVal, res.newAttrVal),
            fc,
            dlg
        )
    else
        Bridge.syncDerivedFields(sheet, ndbApi)
        Bridge.notify(
            sheet,
            string.format("🐺 [%s] Frenesi Gangrel registrado: %d traço(s) animal(is) acumulado(s).",
                sheet.nome or "Personagem", res.newState.gangrel_tracos_qtd),
            fc,
            dlg
        )
    end
    return {
        ok = true,
        count = res.newState.gangrel_tracos_qtd,
        penalizedAttr = res.penalizedAttr,
        newAttrVal = res.newAttrVal,
    }
end

function Bridge.suppressMalkavianDerangement(sheet, firecastApi, dialogsApi)
    if type(sheet) ~= "table" then return { ok = false } end
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)
    local stOverride = isTrue(sheet.narrador_override) and Bridge.isStoryteller(sheet, fc)
    local res = V20.ClanWeaknesses.suppressMalkavianDerangement({
        fdv_temp = safeInt(sheet.fdv_temp, 0),
        storytellerOverride = stOverride,
    })
    if not res.ok then
        dlg.showMessage(res.error or "Força de Vontade insuficiente para suprimir Perturbação.")
        return res
    end
    sheet.fdv_temp = res.newState.fdv_temp
    sheet.malkav_suprimida_cena = true
    Bridge.syncDerivedFields(sheet)
    local pert = (type(sheet.malkav_perturbacao) == "string" and sheet.malkav_perturbacao ~= "") and sheet.malkav_perturbacao or "Perturbação"
    Bridge.notify(
        sheet,
        string.format("🌀 [%s] %s suprimida pela cena (-1 FdV | FdV Temp: %d/%d).",
            sheet.nome or "Personagem", pert, safeInt(sheet.fdv_temp, 0), safeInt(sheet.fdv_perm, 5)),
        fc,
        dlg
    )
    return res
end

function Bridge.rollToreadorFascination(sheet, firecastApi, dialogsApi)
    if type(sheet) ~= "table" then return { ok = false } end
    Bridge.syncDerivedFields(sheet)
    local vLabel = (sheet.virtude2_tipo == "instinto") and "Instinto" or "Autocontrole"
    local pool = math.max(1, safeInt(sheet.virtude2_val, 1))
    local foco = (type(sheet.toreador_foco_arte) == "string" and sheet.toreador_foco_arte ~= "") and (" — " .. sheet.toreador_foco_arte) or ""
    return Bridge.rollFromSheet(sheet, {
        rawPool = pool,
        difficulty = 6,
        ignoreWoundPenalty = true,
        skipClanWeakness = true,
        label = "Fascínio Estético Toreador (" .. vLabel .. ")" .. foco,
        onEvaluated = function(evalRes)
            if evalRes.totalSuccesses <= 0 then
                sheet.toreador_fascinado_cena = true
                return "Fraqueza Toreador: FASCINADO pela cena (gaste 1 FdV ou encerre a cena)!"
            else
                sheet.toreador_fascinado_cena = false
                return "Resistiu ao Fascínio Estético."
            end
        end,
    }, firecastApi, dialogsApi)
end

function Bridge.recordTremereDrink(sheet, firecastApi, dialogsApi)
    if type(sheet) ~= "table" then return { ok = false } end
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)
    local res = V20.ClanWeaknesses.recordTremereDrink({
        tremere_laco_goles = safeNonNegInt(sheet.tremere_laco_goles, 0),
    })
    sheet.tremere_laco_goles = res.step
    Bridge.syncDerivedFields(sheet)
    local regente = (type(sheet.tremere_regente_nome) == "string" and sheet.tremere_regente_nome ~= "")
        and (" com " .. sheet.tremere_regente_nome) or ""
    local statusMsg = res.fullBond
        and ("Laço de Sangue Completo (2/2 — Maldição Tremere)" .. regente .. "!")
        or string.format("1º Gole de Vitae (%d/2)%s.", res.step, regente)
    Bridge.notify(sheet, string.format("🍷 [%s] %s", sheet.nome or "Personagem", statusMsg), fc, dlg)
    return { ok = true, step = res.step, fullBond = res.fullBond }
end

function Bridge.ingestAssamiteVitae(sheet, points, firecastApi, dialogsApi)
    if type(sheet) ~= "table" then return { ok = false } end
    if type(points) == "table" then
        dialogsApi = firecastApi
        firecastApi = points
        points = nil
    end
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)

    local pts = math.max(1, safeInt(points ~= nil and points or sheet.assamita_vitae_qtd, 1))
    local huge = isTrue(sheet.tem_tamanho_grande) or V20.BackgroundsEngine.aggregateMeritsFlaws(Bridge.collectMeritsFlaws(sheet)).hugeSize
    local st = Bridge.sheetToEngineState(sheet)
    st.hugeSize = huge
    st.bashing = safeNonNegInt(sheet.dano_contundente, 0)
    st.lethal = safeNonNegInt(sheet.dano_letal, 0)
    st.aggravated = safeNonNegInt(sheet.dano_aggravado, 0)
    st.assamita_maldicao_modo = sheet.assamita_maldicao_modo or "ur_shulgi"

    local res = V20.ClanWeaknesses.ingestAssamiteVitae(st, pts)
    sheet.dano_contundente = res.newState.bashing
    sheet.dano_letal = res.newState.lethal
    sheet.dano_aggravado = res.newState.aggravated
    sheet.dano_agravado = res.newState.aggravated
    LAST_AGG_MIRROR[sheet] = res.newState.aggravated
    sheet.sangue_atual = res.newState.currentBlood
    sheet.sangue_fraco_usado = res.newState.thinBloodUsed or safeInt(sheet.sangue_fraco_usado, 0)
    Bridge.syncDerivedFields(sheet)

    if res.addictionDiff == nil then
        Bridge.notify(
            sheet,
            string.format("🗡️ [%s] Maldição Tremere Clássica: ingeriu %d vitae cainita -> +%d dano Letal não absorvível e 0 sangue ganho!",
                sheet.nome or "Personagem", pts, res.lethalApplied),
            fc,
            dlg
        )
        return { ok = true, lethalApplied = res.lethalApplied, bloodAdded = 0, addictionDiff = nil }
    end

    local rollRes = Bridge.rollFromSheet(sheet, {
        rawPool = math.max(1, safeInt(sheet.virtude2_val, 1)),
        difficulty = res.addictionDiff,
        ignoreWoundPenalty = true,
        skipClanWeakness = true,
        extraNotes = { string.format("Maldição de Ur-Shulgi: +%d dano Letal não absorvível, +%d Vitae absorvida", res.lethalApplied, res.bloodAdded) },
        label = "Vício Assamita (Autocontrole)",
        onEvaluated = function(evalRes)
            if evalRes.totalSuccesses <= 0 then
                sheet.assamita_vicio_ativo = true
                return "VÍCIO EM VITAE CAINITA ATIVADO!"
            end
            return "Resistiu ao vício em vitae cainita."
        end,
    }, fc, dlg)

    return {
        ok = true,
        lethalApplied = res.lethalApplied,
        bloodAdded = res.bloodAdded,
        addictionDiff = res.addictionDiff,
        roll = rollRes,
    }
end

function Bridge.applyGiovanniKiss(sheet, points, firecastApi, dialogsApi)
    if type(sheet) ~= "table" then return { ok = false } end
    if type(points) == "table" then
        dialogsApi = firecastApi
        firecastApi = points
        points = nil
    end
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)

    local pts = math.max(1, safeInt(points ~= nil and points or sheet.giovanni_beijo_pontos, 1))
    local kiss = V20.ClanWeaknesses.computeGiovanniKissDamage(pts)
    local added = 0
    if Bridge.isVampireSheet(sheet) then
        local g = V20.Blood.gain(Bridge.sheetToEngineState(sheet), pts)
        sheet.sangue_atual = g.newState.currentBlood
        sheet.sangue_fraco_usado = g.newState.thinBloodUsed
        added = safeInt(g.added, 0)
        Bridge.syncDerivedFields(sheet)
    end

    Bridge.notify(
        sheet,
        string.format("💀 [%s] O Beijo Doloroso Giovanni (%d vitae drenada -> +%d Sangue): recipiente mortal sofre %d níveis de dano Letal%s",
            sheet.nome or "Personagem",
            pts,
            added,
            kiss.lethalToVessel,
            kiss.fatalRisk and " — CHOQUE / MORTE DO RECIPIENTE!" or "."
        ),
        fc,
        dlg
    )
    return {
        ok = true,
        bloodDrained = pts,
        bloodAdded = added,
        lethalToVessel = kiss.lethalToVessel,
        fatalRisk = kiss.fatalRisk,
    }
end

function Bridge.rollRavnosVice(sheet, firecastApi, dialogsApi)
    if type(sheet) ~= "table" then return { ok = false } end
    Bridge.syncDerivedFields(sheet)
    local vLabel = (sheet.virtude2_tipo == "instinto") and "Instinto" or "Autocontrole"
    local pool = math.max(1, safeInt(sheet.virtude2_val, 1))
    local vicio = (type(sheet.ravnos_vicio_descricao) == "string" and sheet.ravnos_vicio_descricao ~= "") and (" — " .. sheet.ravnos_vicio_descricao) or ""
    return Bridge.rollFromSheet(sheet, {
        rawPool = pool,
        difficulty = 6,
        ignoreWoundPenalty = true,
        skipClanWeakness = true,
        label = "Resistir ao Vício Ravnos (" .. vLabel .. ")" .. vicio,
        onEvaluated = function(evalRes)
            if evalRes.totalSuccesses <= 0 then
                sheet.ravnos_compulsao_ativa = true
                return "Fraqueza Ravnos: COMPULSÃO ATIVA (cedeu ao vício)!"
            else
                sheet.ravnos_compulsao_ativa = false
                return "Resistiu à tentação do vício."
            end
        end,
    }, firecastApi, dialogsApi)
end

function Bridge.resetTzimisceSoil(sheet, firecastApi, dialogsApi)
    if type(sheet) ~= "table" then return { ok = false } end
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    local nextSt = V20.ClanWeaknesses.resetTzimisceSoil({
        tzimisce_dias_sem_terra = sheet.tzimisce_dias_sem_terra,
    })
    sheet.tzimisce_dias_sem_terra = nextSt.tzimisce_dias_sem_terra
    Bridge.syncDerivedFields(sheet)
    local origem = (type(sheet.tzimisce_origem_terra) == "string" and sheet.tzimisce_origem_terra ~= "")
        and (" (" .. sheet.tzimisce_origem_terra .. ")") or ""
    Bridge.notify(
        sheet,
        string.format("⚰️ [%s] Repousou com 2 punhados de terra natal%s — penalidade Tzimisce zerada.",
            sheet.nome or "Personagem", origem),
        fc,
        dlg
    )
    return { ok = true, tzimisce_dias_sem_terra = 0 }
end

local function dispatchBloodMagicRoll(sheet, rollSpec, tradition, isGen15Channel, fc, dlg)
    if not rollSpec then return nil end
    local notes = {}
    if rollSpec.diffHint and rollSpec.diffHint ~= "" then
        table.insert(notes, rollSpec.diffHint)
    end
    if isGen15Channel then
        table.insert(notes, GEN15_CHANNEL_NOTE)
    end
    return Bridge.rollFromSheet(sheet, {
        attrId = rollSpec.attr,
        habId = rollSpec.hab,
        difficulty = rollSpec.defaultDiff,
        label = rollSpec.powerName,
        spendWillpower = false,
        extraNotes = (#notes > 0) and notes or nil,
        onEvaluated = function(evalRes)
            if tradition == "thaumaturgy" and evalRes.outcome == "botch" then
                return "⚠️ Falha Crítica Taumatúrgica: perde 1 ponto de Força de Vontade Permanente (V20, p. 212)!"
            end
            return nil
        end,
    }, fc, dlg)
end

function Bridge.activatePrimaryBloodMagic(sheet, tradition, level, firecastApi, dialogsApi)
    if type(sheet) ~= "table" then return { ok = false } end
    if type(level) == "table" then
        dialogsApi = firecastApi
        firecastApi = level
        level = nil
    end
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)

    local trad = (tradition == "necromancy") and "necromancy" or "thaumaturgy"
    local pathId = (trad == "necromancy")
        and ((type(sheet.bm_necro_prim_id) == "string" and sheet.bm_necro_prim_id ~= "") and sheet.bm_necro_prim_id or "sepulchre_path")
        or ((type(sheet.bm_thau_prim_id) == "string" and sheet.bm_thau_prim_id ~= "") and sheet.bm_thau_prim_id or "path_of_blood")
    local pathDots = (trad == "necromancy")
        and safeNonNegInt(sheet.bm_necro_prim_nivel, 0)
        or safeNonNegInt(sheet.bm_thau_prim_nivel, 0)
    local pwrLvl = (level ~= nil)
        and math.max(1, math.min(5, safeInt(level, 1)))
        or math.max(1, math.min(5, safeInt((trad == "necromancy") and sheet.bm_necro_prim_pwr_lvl or sheet.bm_thau_prim_pwr_lvl, 1)))

    local pTable = V20.BloodMagicEngine.getPathTable(trad, pathId)
    local pw = pTable and pTable.powers and pTable.powers[pwrLvl] or nil
    local baseBloodCost = math.max(0, safeInt(pw and pw.cost and pw.cost.blood, 0))
    local isGen15Channel = Bridge.isVampireSheet(sheet)
        and (baseBloodCost == 1)
        and (safeInt(sheet.geracao, 13) == 15)
        and (safeInt(sheet.sangue_gasto_turno, 0) == 0)

    local stOverride = isTrue(sheet.narrador_override) and Bridge.isStoryteller(sheet, fc)
    local res = V20.BloodMagicEngine.activatePathPower(
        Bridge.sheetToEngineState(sheet),
        trad,
        pathId,
        pathDots,
        pwrLvl,
        { storytellerOverride = stOverride, bypassTurnLimit = isGen15Channel }
    )
    if not res.ok then
        dlg.showMessage(res.error or "Não foi possível ativar o poder de Magia do Sangue.")
        return res
    end

    applyEngineStateToSheet(sheet, res.newState)
    dispatchBloodMagicRoll(sheet, res.rollSpec, trad, isGen15Channel, fc, dlg)
    return res
end

function Bridge.activateSecondaryBloodMagic(sheet, slotIndex, level, firecastApi, dialogsApi)
    if type(sheet) ~= "table" then return { ok = false } end
    if type(level) == "table" then
        dialogsApi = firecastApi
        firecastApi = level
        level = nil
    end
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)

    local idx = math.max(1, math.min(4, safeInt(slotIndex, 1)))
    local trad = resolveSecondaryTradition(sheet, idx)
    local pathId = sheet["bm_sec" .. idx .. "_path_id"] or ""
    local pathDots = safeNonNegInt(sheet["bm_sec" .. idx .. "_nivel"], 0)
    local pwrLvl = (level ~= nil)
        and math.max(1, math.min(5, safeInt(level, 1)))
        or math.max(1, math.min(5, safeInt(sheet["bm_sec" .. idx .. "_pwr_lvl"], 1)))

    local pTable = V20.BloodMagicEngine.getPathTable(trad, pathId)
    local pw = pTable and pTable.powers and pTable.powers[pwrLvl] or nil
    local baseBloodCost = math.max(0, safeInt(pw and pw.cost and pw.cost.blood, 0))
    local isGen15Channel = Bridge.isVampireSheet(sheet)
        and (baseBloodCost == 1)
        and (safeInt(sheet.geracao, 13) == 15)
        and (safeInt(sheet.sangue_gasto_turno, 0) == 0)

    local stOverride = isTrue(sheet.narrador_override) and Bridge.isStoryteller(sheet, fc)
    local res = V20.BloodMagicEngine.activatePathPower(
        Bridge.sheetToEngineState(sheet),
        trad,
        pathId,
        pathDots,
        pwrLvl,
        { storytellerOverride = stOverride, bypassTurnLimit = isGen15Channel }
    )
    if not res.ok then
        dlg.showMessage(res.error or "Não foi possível ativar a Linha Secundária.")
        return res
    end

    applyEngineStateToSheet(sheet, res.newState)
    dispatchBloodMagicRoll(sheet, res.rollSpec, trad, isGen15Channel, fc, dlg)
    return res
end

function Bridge.castCatalogRitual(sheet, ritualId, firecastApi, dialogsApi)
    if type(sheet) ~= "table" then return { ok = false } end
    if type(ritualId) == "table" then
        dialogsApi = firecastApi
        firecastApi = ritualId
        ritualId = nil
    end
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)

    local rid = (type(ritualId) == "string" and ritualId ~= "")
        and ritualId
        or ((type(sheet.bm_ritual_id) == "string" and sheet.bm_ritual_id ~= "") and sheet.bm_ritual_id or "thau_rit_1_sacred_haven")
    local rit = V20.BloodMagicCatalog.RITUALS[rid]
    local parentDots = rit and getDisciplineDots(sheet, rit.tradition, nil) or 0
    local stOverride = isTrue(sheet.narrador_override) and Bridge.isStoryteller(sheet, fc)

    local res = V20.BloodMagicEngine.castRitual(
        Bridge.sheetToEngineState(sheet),
        rid,
        parentDots,
        { storytellerOverride = stOverride }
    )
    if not res.ok then
        dlg.showMessage(res.error or "Não foi possível conjurar o ritual.")
        return res
    end

    applyEngineStateToSheet(sheet, res.newState)
    if res.rollSpec then
        Bridge.rollFromSheet(sheet, {
            attrId = res.rollSpec.attr,
            habId = res.rollSpec.hab,
            difficulty = res.rollSpec.defaultDiff,
            label = res.rollSpec.powerName,
            spendWillpower = false,
            extraNotes = (res.rollSpec.diffHint and res.rollSpec.diffHint ~= "") and { res.rollSpec.diffHint } or nil,
        }, fc, dlg)
    end
    return res
end

function Bridge.castCustomRitual(sheet, firecastApi, dialogsApi)
    if type(sheet) ~= "table" then return { ok = false } end
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi)
    Bridge.syncDerivedFields(sheet)

    local trad = (sheet.ritual_custom_trad == "necromancy") and "necromancy" or "thaumaturgy"
    local lvl = math.max(1, safeInt(sheet.ritual_custom_nivel, 1))
    local customRit = {
        id = "ritual_custom",
        name = (type(sheet.ritual_custom_nome) == "string" and sheet.ritual_custom_nome ~= "") and sheet.ritual_custom_nome or "Ritual Customizado",
        tradition = trad,
        level = lvl,
        cost = {
            blood = math.max(0, safeInt(sheet.ritual_custom_sangue, 0)),
            willpower = math.max(0, safeInt(sheet.ritual_custom_fdv, 0)),
        },
        defaultDiff = safeInt(sheet.ritual_custom_dif, math.min(9, 3 + lvl)),
        summary = string.format("Ritual Customizado (%s Nv %d)", (trad == "necromancy") and "Necromancia" or "Taumaturgia", lvl),
    }
    local parentDots = getDisciplineDots(sheet, trad, nil)
    local stOverride = isTrue(sheet.narrador_override) and Bridge.isStoryteller(sheet, fc)

    local res = V20.BloodMagicEngine.castRitual(
        Bridge.sheetToEngineState(sheet),
        customRit,
        parentDots,
        { storytellerOverride = stOverride }
    )
    if not res.ok then
        dlg.showMessage(res.error or "Não foi possível conjurar o ritual customizado.")
        return res
    end

    applyEngineStateToSheet(sheet, res.newState)
    if res.rollSpec then
        Bridge.rollFromSheet(sheet, {
            attrId = res.rollSpec.attr,
            habId = res.rollSpec.hab,
            difficulty = res.rollSpec.defaultDiff,
            label = res.rollSpec.powerName,
            spendWillpower = false,
            extraNotes = (res.rollSpec.diffHint and res.rollSpec.diffHint ~= "") and { res.rollSpec.diffHint } or nil,
        }, fc, dlg)
    end
    return res
end

_G.V20Bridge = Bridge
return Bridge
