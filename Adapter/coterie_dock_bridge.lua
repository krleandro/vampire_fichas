local V20 = require("Core.v20_init")
local Bridge = require("Adapter.firecast_bridge")

local CoterieDockBridge = {
    ROOM_NDB_NAME = "v20_coterie_dock_v1",
    MAX_INIT_ENTRIES = 20,
    MAX_INIT_ROWS = 10,
    MAX_PUB_SLOTS = 8,
    ST_PAGE_SIZE = 8,
}

local ACTIVE_DOCKS = setmetatable({}, { __mode = "k" })
local REFRESH_IN_PROGRESS = setmetatable({}, { __mode = "k" })
local FALLBACK_ROOM_NODES = setmetatable({}, { __mode = "k" })
local SHEET_TO_BIB_CACHE = setmetatable({}, { __mode = "k" })

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

local function setAttrIfChanged(node, key, val)
    if type(node) ~= "table" then return end
    if node[key] ~= val then
        node[key] = val
    end
end

local function getFirecastAndDialogs(firecastApi, dialogsApi, formObj)
    local fc = firecastApi or (type(formObj) == "table" and rawget(formObj, "_dockFc")) or _G.Firecast
    local dlg = dialogsApi or _G.Dialogs or { showMessage = _G.showMessage or function() end }
    if type(dlg.showMessage) ~= "function" then
        dlg = { showMessage = _G.showMessage or function() end }
    end
    return fc, dlg
end

local function getNdbApi(ndbApi, formObj)
    return ndbApi or (type(formObj) == "table" and rawget(formObj, "_dockNdb")) or _G.NDB
end

local function resolveMesa(formObj, firecastApi)
    local fc = firecastApi or (type(formObj) == "table" and rawget(formObj, "_dockFc")) or _G.Firecast
    if fc ~= nil and type(fc.getMesaDe) == "function" then
        if type(formObj) == "table" then
            local m = fc.getMesaDe(formObj)
            if m ~= nil then return m end
            if formObj.sheet ~= nil then
                local ms = fc.getMesaDe(formObj.sheet)
                if ms ~= nil then return ms end
            end
        end
    end
    if type(formObj) == "table" and rawget(formObj, "_mesa") ~= nil then
        return rawget(formObj, "_mesa")
    end
    return nil
end

local function isRoomStoryteller(mesa)
    if mesa == nil then
        return true
    end
    return (mesa.meuJogador ~= nil and isTrue(mesa.meuJogador.isMestre))
end

local function sendRoomBulletin(mesa, dlg, msg)
    if mesa ~= nil and mesa.activeChat ~= nil and type(mesa.activeChat.enviarMensagem) == "function" then
        mesa.activeChat:enviarMensagem(msg)
    elseif dlg ~= nil and type(dlg.showMessage) == "function" then
        dlg.showMessage(msg)
    end
    return msg
end

local function disableObserver(obs)
    if type(obs) ~= "table" then return end
    obs.onChanged = nil
    obs.onDeepChanged = nil
    obs.onChildAdded = nil
    obs.onChildRemoved = nil
    obs.enabled = false
    local setEn = rawget(obs, "setEnabled")
    if type(setEn) == "function" then
        setEn(obs, false)
    end
end

local function getFallbackRoomNode(mesa, formObj, ndb)
    local key = mesa or formObj
    if key ~= nil and FALLBACK_ROOM_NODES[key] ~= nil then
        return FALLBACK_ROOM_NODES[key]
    end
    local node = nil
    if ndb ~= nil and type(ndb.newMemNodeDatabase) == "function" then
        local ok, mem = pcall(ndb.newMemNodeDatabase)
        if ok and type(mem) == "table" then
            node = mem
        end
    end
    if type(node) ~= "table" then
        node = {}
    end
    if key ~= nil then
        FALLBACK_ROOM_NODES[key] = node
    end
    return node
end

local function withRoomNode(formObj, mesa, fc, ndb, callback)
    if type(formObj) == "table" and rawget(formObj, "_roomNode") ~= nil then
        callback(rawget(formObj, "_roomNode"))
        return
    end
    local resolvedMesa = mesa or resolveMesa(formObj, fc)
    if resolvedMesa ~= nil and type(resolvedMesa.abrirNDBDeMesa) == "function" then
        resolvedMesa:abrirNDBDeMesa(CoterieDockBridge.ROOM_NDB_NAME, function(loadedNode)
            local rNode = loadedNode or getFallbackRoomNode(resolvedMesa, formObj, ndb)
            if type(formObj) == "table" then
                rawset(formObj, "_roomNode", rNode)
            end
            callback(rNode)
        end, { criar = true })
    else
        local rNode = getFallbackRoomNode(resolvedMesa, formObj, ndb)
        if type(formObj) == "table" then
            rawset(formObj, "_roomNode", rNode)
        end
        callback(rNode)
    end
end

local function isBibItemOwnVisible(item)
    if type(item) ~= "table" then
        return false
    end
    if isFalse(item.visivel) or isFalse(item.visible) or isFalse(item.visivelRecursivamente) then
        return false
    end
    if type(item.getVisivel) == "function" then
        local okV, resV = pcall(item.getVisivel, item)
        if okV and isFalse(resV) then return false end
    end
    if type(item.getVisivelRecursivamente) == "function" then
        local okR, resR = pcall(item.getVisivelRecursivamente, item)
        if okR and isFalse(resR) then return false end
    end
    return true
end

local function collectV20BibItems(bibRoot, onlyVisible)
    local out = {}
    if type(bibRoot) ~= "table" then
        return out
    end
    local seen = {}

    local function walk(node, parentVisible)
        if type(node) ~= "table" or seen[node] then return end
        seen[node] = true
        local ownVis = isBibItemOwnVisible(node)
        local effVis = parentVisible and ownVis
        if onlyVisible and not effVis then
            return
        end

        local tipo = tostring(node.tipo or "")
        local dt = tostring(node.dataType or "")
        if tipo == "personagem" and dt:sub(1, 11) == "br.com.v20." and dt ~= "br.com.v20.CoterieDock" then
            table.insert(out, {
                bibItem = node,
                visible = effVis,
                dataType = dt,
            })
        end

        local filhos = node.filhos or node.children
        if type(filhos) == "table" then
            for _, ch in ipairs(filhos) do
                walk(ch, effVis)
            end
        end
    end

    walk(bibRoot, true)
    return out
end

local function makeCharKey(bibItem, fallbackIdx)
    if type(bibItem) == "table" then
        if bibItem.codigoInterno ~= nil and tostring(bibItem.codigoInterno) ~= "" then
            return "char_" .. tostring(bibItem.codigoInterno)
        end
        if nonEmpty(bibItem.key) then
            return tostring(bibItem.key)
        end
        if nonEmpty(bibItem.id) then
            return tostring(bibItem.id)
        end
        if nonEmpty(bibItem.nome) then
            return tostring(bibItem.nome)
        end
    end
    return "char_" .. tostring(fallbackIdx or 1)
end

local function isAncestorChainVisible(bibItem)
    local cur = bibItem
    local seen = {}
    while type(cur) == "table" and not seen[cur] do
        seen[cur] = true
        if not isBibItemOwnVisible(cur) then
            return false
        end
        local nextParent = cur.pai
        if nextParent == nil and type(cur.getPai) == "function" then
            local okP, resP = pcall(cur.getPai, cur)
            if okP then nextParent = resP end
        end
        if nextParent == nil then
            nextParent = rawget(cur, "parent")
        end
        cur = nextParent
    end
    return type(bibItem) == "table"
end

local function findBibMetaForSheet(mesa, sheet, fc)
    local directBib = nil
    if fc ~= nil then
        if type(fc.getPersonagemDe) == "function" then
            directBib = fc.getPersonagemDe(sheet)
        end
        if directBib == nil and type(fc.getBibliotecaItemDe) == "function" then
            directBib = fc.getBibliotecaItemDe(sheet)
        end
    end

    if directBib == nil then
        local cached = SHEET_TO_BIB_CACHE[sheet]
        if type(cached) == "table" and cached.bibItem ~= nil then
            directBib = cached.bibItem
        end
    end

    if mesa ~= nil and type(mesa.biblioteca) == "table" then
        local allItems = collectV20BibItems(mesa.biblioteca, false)
        for _, entry in ipairs(allItems) do
            if (directBib ~= nil and entry.bibItem == directBib) or (rawget(entry.bibItem, "sheet") == sheet) then
                SHEET_TO_BIB_CACHE[sheet] = { bibItem = entry.bibItem }
                local liveVis = (entry.visible == true) and isAncestorChainVisible(entry.bibItem)
                return entry.bibItem, liveVis
            end
        end
    end

    if directBib ~= nil then
        SHEET_TO_BIB_CACHE[sheet] = { bibItem = directBib }
        return directBib, isAncestorChainVisible(directBib)
    end

    return nil, true
end

local function readInitiativeEntries(roomNode)
    local list = {}
    if type(roomNode) ~= "table" then
        return list
    end
    local count = clamp(safeNonNegInt(roomNode.init_count, 0), 0, CoterieDockBridge.MAX_INIT_ENTRIES)
    for i = 1, count do
        local name = roomNode["init_e" .. i .. "_name"]
        if nonEmpty(name) then
            local id = roomNode["init_e" .. i .. "_id"]
            table.insert(list, {
                id = nonEmpty(id) and tostring(id) or tostring(name),
                name = tostring(name),
                d10 = safeInt(roomNode["init_e" .. i .. "_d10"], 0),
                initMod = safeInt(roomNode["init_e" .. i .. "_mod"], 0),
                total = safeInt(roomNode["init_e" .. i .. "_total"], 0),
                hidden = isTrue(roomNode["init_e" .. i .. "_hidden"]),
            })
        end
    end
    return list
end

local function syncPublicInitiativeSlots(roomNode, sortedEntries)
    if type(roomNode) ~= "table" then return end
    local publicOnly = V20.CoterieTracker.filterPublicInitiative(sortedEntries, false)
    for i = 1, CoterieDockBridge.MAX_INIT_ROWS do
        local txt = (publicOnly[i] ~= nil) and tostring(publicOnly[i].label) or ""
        setAttrIfChanged(roomNode, "init_row" .. i .. "_txt", txt)
    end
end

local function writeInitiativeEntries(roomNode, entries, phase)
    if type(roomNode) ~= "table" then return {} end
    local sorted = V20.CoterieTracker.sortInitiativeEntries(entries, phase or roomNode.combate_fase or "declaracao")
    local count = math.min(#sorted, CoterieDockBridge.MAX_INIT_ENTRIES)
    local prevCount = clamp(safeNonNegInt(roomNode.init_count, 0), 0, CoterieDockBridge.MAX_INIT_ENTRIES)

    setAttrIfChanged(roomNode, "init_count", count)
    for i = 1, math.max(count, prevCount) do
        local e = (i <= count) and sorted[i] or nil
        if e ~= nil then
            setAttrIfChanged(roomNode, "init_e" .. i .. "_id", tostring(e.id))
            setAttrIfChanged(roomNode, "init_e" .. i .. "_name", tostring(e.name))
            setAttrIfChanged(roomNode, "init_e" .. i .. "_d10", safeInt(e.d10, 0))
            setAttrIfChanged(roomNode, "init_e" .. i .. "_mod", safeInt(e.initMod, 0))
            setAttrIfChanged(roomNode, "init_e" .. i .. "_total", safeInt(e.total, 0))
            setAttrIfChanged(roomNode, "init_e" .. i .. "_hidden", e.hidden == true)
        else
            setAttrIfChanged(roomNode, "init_e" .. i .. "_id", nil)
            setAttrIfChanged(roomNode, "init_e" .. i .. "_name", nil)
            setAttrIfChanged(roomNode, "init_e" .. i .. "_d10", nil)
            setAttrIfChanged(roomNode, "init_e" .. i .. "_mod", nil)
            setAttrIfChanged(roomNode, "init_e" .. i .. "_total", nil)
            setAttrIfChanged(roomNode, "init_e" .. i .. "_hidden", nil)
        end
    end

    syncPublicInitiativeSlots(roomNode, sorted)
    return sorted
end

local function notifyActiveDocks()
    local docks = {}
    for dockForm, info in pairs(ACTIVE_DOCKS) do
        table.insert(docks, { form = dockForm, fc = info.fc, ndb = info.ndb })
    end
    for _, item in ipairs(docks) do
        if ACTIVE_DOCKS[item.form] ~= nil then
            CoterieDockBridge.refreshDock(item.form, item.fc, item.ndb)
        end
    end
end

function CoterieDockBridge.scanLibrarySheets(mesa, onUpdated, opts)
    opts = opts or {}
    local onlyVisible = (opts.onlyVisible == true)
    if type(mesa) ~= "table" or type(mesa.biblioteca) ~= "table" then
        if type(onUpdated) == "function" then
            onUpdated({})
        end
        return {}
    end

    local found = collectV20BibItems(mesa.biblioteca, onlyVisible)
    if #found == 0 then
        if type(onUpdated) == "function" then
            onUpdated({})
        end
        return {}
    end

    local slots = {}
    local inInitialPass = true

    local function buildOrderedList()
        local list = {}
        for idx = 1, #found do
            if slots[idx] ~= nil then
                table.insert(list, slots[idx])
            end
        end
        return list
    end

    for idx, entry in ipairs(found) do
        local bibItem = entry.bibItem
        local key = makeCharKey(bibItem, idx)

        local function acceptCharNode(charNode)
            if type(charNode) ~= "table" then return end
            SHEET_TO_BIB_CACHE[charNode] = { bibItem = bibItem }
            slots[idx] = {
                key = key,
                id = key,
                nome = bibItem.nome,
                dataType = entry.dataType,
                visible = entry.visible,
                visivel = entry.visible,
                visivelRecursivamente = entry.visible,
                bibItem = bibItem,
                sheet = charNode,
                nodeRef = charNode,
            }
            if not inInitialPass and type(onUpdated) == "function" then
                onUpdated(buildOrderedList())
            end
        end

        if type(bibItem.loadSheetNDB) == "function" then
            bibItem:loadSheetNDB(acceptCharNode)
        elseif type(rawget(bibItem, "sheet")) == "table" then
            acceptCharNode(rawget(bibItem, "sheet"))
        end
    end

    inInitialPass = false
    local initialOrdered = buildOrderedList()
    if type(onUpdated) == "function" then
        onUpdated(initialOrdered)
    end
    return initialOrdered
end

local function setCtrlText(formObj, ctrlName, text)
    if type(formObj) ~= "table" then return end
    local ctrl = formObj[ctrlName]
    if type(ctrl) == "table" and type(ctrl.setText) == "function" then
        ctrl:setText(tostring(text or ""))
    end
end

local function setCtrlVisible(formObj, ctrlName, vis)
    if type(formObj) ~= "table" then return end
    local ctrl = formObj[ctrlName]
    if type(ctrl) == "table" and type(ctrl.setVisible) == "function" then
        ctrl:setVisible(vis == true)
    end
end

local function setCtrlEnabled(formObj, ctrlName, en)
    if type(formObj) ~= "table" then return end
    local ctrl = formObj[ctrlName]
    if type(ctrl) == "table" and type(ctrl.setEnabled) == "function" then
        ctrl:setEnabled(en == true)
    end
end

local function clearStorytellerCardsUI(formObj)
    if type(formObj) ~= "table" then return end
    rawset(formObj, "_currentCards", {})
    rawset(formObj, "_loadedChars", {})
    setCtrlText(formObj, "lblStPageInfo", "Página 1/1 (0 fichas)")
    setCtrlEnabled(formObj, "btnStPrevPage", false)
    setCtrlEnabled(formObj, "btnStNextPage", false)
    for i = 1, CoterieDockBridge.ST_PAGE_SIZE do
        setCtrlVisible(formObj, "rectStCard" .. i, false)
        setCtrlText(formObj, "lblStCardTitle" .. i, "—")
        setCtrlText(formObj, "lblStCardStats" .. i, "")
        setCtrlText(formObj, "lblStCardFlags" .. i, "")
        setCtrlEnabled(formObj, "btnStBloodMinus" .. i, false)
        setCtrlEnabled(formObj, "btnStBloodPlus" .. i, false)
        setCtrlVisible(formObj, "btnStApproveXp" .. i, false)
        setCtrlEnabled(formObj, "btnStApproveXp" .. i, false)
    end
end

local function syncCharObserversForDock(formObj, chars, fc, ndb)
    if type(formObj) ~= "table" or ACTIVE_DOCKS[formObj] == nil then
        return
    end
    local obsMap = rawget(formObj, "_charObservers")
    if type(obsMap) ~= "table" then
        obsMap = {}
        rawset(formObj, "_charObservers", obsMap)
    end

    local activeNodes = {}
    for _, ch in ipairs(chars or {}) do
        local cNode = ch and ch.nodeRef
        if type(cNode) == "table" then
            activeNodes[cNode] = true
            if obsMap[cNode] == nil and ndb ~= nil and type(ndb.newObserver) == "function" then
                local obs = ndb.newObserver(cNode)
                if obs ~= nil then
                    obs.enabled = true
                    obs.onChanged = function()
                        if ACTIVE_DOCKS[formObj] ~= nil then
                            CoterieDockBridge.refreshDock(formObj, fc, ndb)
                        end
                    end
                    obsMap[cNode] = obs
                end
            end
        end
    end

    for nodeKey, oldObs in pairs(obsMap) do
        if not activeNodes[nodeKey] then
            disableObserver(oldObs)
            obsMap[nodeKey] = nil
        end
    end
end

local function syncPublicSlotsToRoomNode(roomNode, pubSummary)
    if type(roomNode) ~= "table" then return end
    local count = math.min(#pubSummary, CoterieDockBridge.MAX_PUB_SLOTS)
    setAttrIfChanged(roomNode, "pub_slot_count", count)
    for i = 1, CoterieDockBridge.MAX_PUB_SLOTS do
        local item = pubSummary[i]
        local txt = (item ~= nil) and string.format("%s — %s", item.nome, item.condicao_aparente) or ""
        setAttrIfChanged(roomNode, "pub_slot" .. i .. "_txt", txt)
    end
end

local function renderPublicSummaryControls(formObj, slotStrings)
    for i = 1, CoterieDockBridge.MAX_PUB_SLOTS do
        local s = slotStrings[i]
        if nonEmpty(s) then
            setCtrlText(formObj, "lblPubSlot" .. i, "• " .. tostring(s))
        else
            setCtrlText(formObj, "lblPubSlot" .. i, "• —")
        end
    end
end

local function refreshDockImpl(formObj, firecastApi, ndbApi)
    local fc = firecastApi or rawget(formObj, "_dockFc") or _G.Firecast
    local ndb = getNdbApi(ndbApi, formObj)
    local mesa = resolveMesa(formObj, fc)
    if mesa ~= nil then
        rawset(formObj, "_mesa", mesa)
    end

    local isMestre = isRoomStoryteller(mesa)

    if not isMestre then
        if formObj.pgcDock ~= nil and type(formObj.pgcDock.getTabIndex) == "function" and formObj.pgcDock:getTabIndex() == 1 then
            if type(formObj.pgcDock.setTabIndex) == "function" then
                formObj.pgcDock:setTabIndex(0)
            end
        end
        setCtrlVisible(formObj, "tabNarradorCoterie", false)
        local charObs = rawget(formObj, "_charObservers")
        if type(charObs) == "table" then
            for k, obs in pairs(charObs) do
                disableObserver(obs)
                charObs[k] = nil
            end
        end
        clearStorytellerCardsUI(formObj)
    else
        setCtrlVisible(formObj, "tabNarradorCoterie", true)
    end

    setCtrlVisible(formObj, "layNpcQuickControls", isMestre)
    setCtrlEnabled(formObj, "btnAddNpcInit", isMestre)
    setCtrlEnabled(formObj, "btnTogglePhase", isMestre)
    setCtrlEnabled(formObj, "btnClearInit", isMestre)

    local roomNode = rawget(formObj, "_roomNode")
    local cenaTitulo = (roomNode and nonEmpty(roomNode.cena_titulo)) and tostring(roomNode.cena_titulo) or "Cena Noturna"
    local rodada = (roomNode and tonumber(roomNode.rodada_atual) ~= nil) and math.max(1, safeInt(roomNode.rodada_atual, 1)) or 1
    local fase = (roomNode and tostring(roomNode.combate_fase or "declaracao"):lower() == "acao") and "acao" or "declaracao"
    local faseLabel = (fase == "acao")
        and "AÇÃO (Maior -> Menor)"
        or "DECLARAÇÃO (Menor -> Maior)"

    setCtrlText(formObj, "lblCenaTitulo", cenaTitulo)
    setCtrlText(formObj, "lblRodadaInfo", string.format("Rodada %d • %s", rodada, faseLabel))

    local rawEntries = readInitiativeEntries(roomNode)
    local sortedEntries = V20.CoterieTracker.sortInitiativeEntries(rawEntries, fase)
    local visibleEntries = V20.CoterieTracker.filterPublicInitiative(sortedEntries, isMestre)
    for i = 1, CoterieDockBridge.MAX_INIT_ROWS do
        if visibleEntries[i] ~= nil then
            setCtrlText(formObj, "lblInitRow" .. i, string.format("%d. %s", i, visibleEntries[i].label))
        else
            setCtrlText(formObj, "lblInitRow" .. i, string.format("%d. —", i))
        end
    end

    if isMestre then
        if mesa ~= nil and type(mesa.biblioteca) == "table" then
            CoterieDockBridge.scanLibrarySheets(mesa, function(chars)
                rawset(formObj, "_loadedChars", chars)
                syncCharObserversForDock(formObj, chars, fc, ndb)

                local pubSummary = V20.CoterieTracker.buildPublicSummary(chars)
                if roomNode ~= nil then
                    syncPublicSlotsToRoomNode(roomNode, pubSummary)
                end

                local pubStrings = {}
                for idxP = 1, CoterieDockBridge.MAX_PUB_SLOTS do
                    if pubSummary[idxP] ~= nil then
                        pubStrings[idxP] = string.format("%s — %s", pubSummary[idxP].nome, pubSummary[idxP].condicao_aparente)
                    end
                end
                renderPublicSummaryControls(formObj, pubStrings)

                local pageInfo = V20.CoterieTracker.buildStorytellerCards(
                    chars,
                    rawget(formObj, "_stPage") or 1,
                    CoterieDockBridge.ST_PAGE_SIZE
                )
                rawset(formObj, "_stPage", pageInfo.page)
                rawset(formObj, "_stTotalPages", pageInfo.totalPages)
                rawset(formObj, "_currentCards", pageInfo.cards)

                setCtrlText(
                    formObj,
                    "lblStPageInfo",
                    string.format("Página %d/%d (%d fichas)", pageInfo.page, pageInfo.totalPages, pageInfo.totalCount)
                )
                setCtrlEnabled(formObj, "btnStPrevPage", pageInfo.page > 1)
                setCtrlEnabled(formObj, "btnStNextPage", pageInfo.page < pageInfo.totalPages)

                for i = 1, CoterieDockBridge.ST_PAGE_SIZE do
                    local card = pageInfo.cards[i]
                    if card ~= nil then
                        setCtrlVisible(formObj, "rectStCard" .. i, true)
                        local titleTxt = card.isVampire
                            and string.format("%s • %s (%dª Ger.)", card.nome, card.cla_titulo, card.geracao)
                            or string.format("%s • %s", card.nome, card.cla_titulo)
                        local statsTxt = string.format(
                            "Sangue: %s | FdV: %s | Vit: %s | %s",
                            card.sangue_txt,
                            card.fdv_txt,
                            card.vitalidade_txt,
                            card.moralidade_txt
                        )
                        local flagsTxt = nonEmpty(card.flags_txt) and card.flags_txt or "Sem alertas ativos"
                        local hasVitae = (card.isVampire == true) or (card.isGhoul == true)

                        setCtrlText(formObj, "lblStCardTitle" .. i, titleTxt)
                        setCtrlText(formObj, "lblStCardStats" .. i, statsTxt)
                        setCtrlText(formObj, "lblStCardFlags" .. i, flagsTxt)
                        setCtrlVisible(formObj, "btnStBloodMinus" .. i, hasVitae)
                        setCtrlEnabled(formObj, "btnStBloodMinus" .. i, hasVitae)
                        setCtrlVisible(formObj, "btnStBloodPlus" .. i, hasVitae)
                        setCtrlEnabled(formObj, "btnStBloodPlus" .. i, hasVitae)
                        setCtrlVisible(formObj, "btnStApproveXp" .. i, card.hasPendingXP == true)
                        setCtrlEnabled(formObj, "btnStApproveXp" .. i, card.hasPendingXP == true)
                    else
                        setCtrlVisible(formObj, "rectStCard" .. i, false)
                        setCtrlText(formObj, "lblStCardTitle" .. i, "—")
                        setCtrlText(formObj, "lblStCardStats" .. i, "")
                        setCtrlText(formObj, "lblStCardFlags" .. i, "")
                        setCtrlEnabled(formObj, "btnStBloodMinus" .. i, false)
                        setCtrlEnabled(formObj, "btnStBloodPlus" .. i, false)
                        setCtrlVisible(formObj, "btnStApproveXp" .. i, false)
                        setCtrlEnabled(formObj, "btnStApproveXp" .. i, false)
                    end
                end
            end, { onlyVisible = false })
        else
            clearStorytellerCardsUI(formObj)
            renderPublicSummaryControls(formObj, {})
        end
    else
        local pubStrings = {}
        if roomNode ~= nil and roomNode.pub_slot_count ~= nil then
            local cnt = clamp(safeNonNegInt(roomNode.pub_slot_count, 0), 0, CoterieDockBridge.MAX_PUB_SLOTS)
            for i = 1, cnt do
                pubStrings[i] = roomNode["pub_slot" .. i .. "_txt"]
            end
            renderPublicSummaryControls(formObj, pubStrings)
        elseif mesa ~= nil and type(mesa.biblioteca) == "table" then
            CoterieDockBridge.scanLibrarySheets(mesa, function(visChars)
                local pubSummary = V20.CoterieTracker.buildPublicSummary(visChars)
                local localStrings = {}
                for i = 1, math.min(#pubSummary, CoterieDockBridge.MAX_PUB_SLOTS) do
                    localStrings[i] = string.format("%s — %s", pubSummary[i].nome, pubSummary[i].condicao_aparente)
                end
                renderPublicSummaryControls(formObj, localStrings)
            end, { onlyVisible = true })
        else
            renderPublicSummaryControls(formObj, {})
        end
    end
end

function CoterieDockBridge.refreshDock(formObj, firecastApi, ndbApi)
    if type(formObj) ~= "table" then return { ok = false } end
    if REFRESH_IN_PROGRESS[formObj] then return { ok = true, reentrant = true } end
    REFRESH_IN_PROGRESS[formObj] = true
    local ok, err = pcall(refreshDockImpl, formObj, firecastApi, ndbApi)
    REFRESH_IN_PROGRESS[formObj] = nil
    if not ok then
        error(err, 0)
    end
    return { ok = true }
end

local function seedLocalUiDefaults(node)
    if type(node) ~= "table" then return end
    if node.npc_init_nome == nil then
        node.npc_init_nome = "NPC"
    end
    if node.npc_init_mod == nil then
        node.npc_init_mod = 4
    end
    if node.npc_init_oculto == nil then
        node.npc_init_oculto = false
    end
end

local function ensureLocalUiNode(formObj, ndbApi)
    if type(formObj) ~= "table" then return {} end
    local ndb = getNdbApi(ndbApi, formObj)
    local existing = rawget(formObj, "_localUiNode")
    local canUpgradeToMemNdb = (existing == nil or not rawget(existing, "__nodeFacadeFlag"))
        and ndb ~= nil and type(ndb.newMemNodeDatabase) == "function"
    if canUpgradeToMemNdb then
        local ok, memNode = pcall(ndb.newMemNodeDatabase)
        if ok and type(memNode) == "table" then
            if type(existing) == "table" then
                if existing.npc_init_nome ~= nil then memNode.npc_init_nome = existing.npc_init_nome end
                if existing.npc_init_mod ~= nil then memNode.npc_init_mod = existing.npc_init_mod end
                if existing.npc_init_oculto ~= nil then memNode.npc_init_oculto = existing.npc_init_oculto end
            end
            existing = memNode
        end
    end
    if type(existing) ~= "table" then
        existing = {}
    end
    seedLocalUiDefaults(existing)
    rawset(formObj, "_localUiNode", existing)
    return existing
end

local function isRoomBoundNode(nodeObj, formObj, firecastApi)
    if type(nodeObj) ~= "table" then return false end
    if type(formObj) == "table" and nodeObj == rawget(formObj, "_localUiNode") then
        return false
    end
    local fc = firecastApi or (type(formObj) == "table" and rawget(formObj, "_dockFc")) or _G.Firecast
    if fc ~= nil and type(fc.getMesaDe) == "function" then
        local okM, m = pcall(fc.getMesaDe, nodeObj)
        if okM and m ~= nil then
            if type(formObj) == "table" and rawget(formObj, "_mesa") == nil then
                rawset(formObj, "_mesa", m)
            end
            return true
        end
    end
    return false
end

function CoterieDockBridge.installLocalUiGuard(formObj, firecastApi, ndbApi)
    if type(formObj) ~= "table" then return end
    if firecastApi ~= nil then rawset(formObj, "_dockFc", firecastApi) end
    if ndbApi ~= nil then rawset(formObj, "_dockNdb", ndbApi) end

    if not rawget(formObj, "_v20LocalGuardInstalled") and type(formObj.setNodeObject) == "function" then
        local baseSetNodeObject = formObj.setNodeObject
        rawset(formObj, "_v20BaseSetNodeObject", baseSetNodeObject)
        rawset(formObj, "_v20LocalGuardInstalled", true)

        formObj.setNodeObject = function(self, nodeObject)
            if nodeObject == nil then
                return baseSetNodeObject(self, nil)
            end
            local ndb = getNdbApi(nil, self)
            local localUi = ensureLocalUiNode(self, ndb)
            if nodeObject == localUi then
                return baseSetNodeObject(self, localUi)
            end
            if isRoomBoundNode(nodeObject, self, nil) then
                return baseSetNodeObject(self, localUi)
            end
            return baseSetNodeObject(self, nodeObject)
        end
    end
end

function CoterieDockBridge.ensureIsolatedSheet(formObj, firecastApi, ndbApi)
    if type(formObj) ~= "table" then return nil end
    CoterieDockBridge.installLocalUiGuard(formObj, firecastApi, ndbApi)
    local localUi = ensureLocalUiNode(formObj, ndbApi)
    local curSheet = formObj.sheet
    local needsRebind = (curSheet == nil)
        or isRoomBoundNode(curSheet, formObj, firecastApi)
        or (curSheet ~= localUi and not rawget(curSheet, "__nodeFacadeFlag") and rawget(localUi, "__nodeFacadeFlag") == true)
    if needsRebind then
        if type(formObj.setNodeObject) == "function" then
            formObj:setNodeObject(localUi)
        else
            formObj.sheet = localUi
        end
    end
    return formObj.sheet
end

function CoterieDockBridge.connectDock(formObj, firecastApi, ndbApi)
    if type(formObj) ~= "table" then return { ok = false } end
    CoterieDockBridge.disconnectDock(formObj)

    local fc, _ = getFirecastAndDialogs(firecastApi, nil, formObj)
    local ndb = getNdbApi(ndbApi, formObj)

    rawset(formObj, "_dockFc", fc)
    rawset(formObj, "_dockNdb", ndb)
    rawset(formObj, "_stPage", safeInt(rawget(formObj, "_stPage"), 1))
    rawset(formObj, "_charObservers", {})
    rawset(formObj, "_loadedChars", {})
    rawset(formObj, "_currentCards", {})

    CoterieDockBridge.ensureIsolatedSheet(formObj, fc, ndb)

    ACTIVE_DOCKS[formObj] = { fc = fc, ndb = ndb }
    local mesa = resolveMesa(formObj, fc)
    rawset(formObj, "_mesa", mesa)

    local function attachRoom(roomNode)
        if ACTIVE_DOCKS[formObj] == nil then return end
        rawset(formObj, "_roomNode", roomNode)

        if isRoomStoryteller(mesa) and type(roomNode) == "table" then
            if not nonEmpty(roomNode.cena_titulo) then
                setAttrIfChanged(roomNode, "cena_titulo", "Cena Noturna")
            end
            if tonumber(roomNode.rodada_atual) == nil then
                setAttrIfChanged(roomNode, "rodada_atual", 1)
            end
            if not nonEmpty(roomNode.combate_fase) then
                setAttrIfChanged(roomNode, "combate_fase", "declaracao")
            end
        end

        if ndb ~= nil and type(ndb.newObserver) == "function" and type(roomNode) == "table" then
            local obs = ndb.newObserver(roomNode)
            if obs ~= nil then
                obs.enabled = true
                obs.onChanged = function()
                    if ACTIVE_DOCKS[formObj] ~= nil then
                        CoterieDockBridge.refreshDock(formObj, fc, ndb)
                    end
                end
                rawset(formObj, "_roomObserver", obs)
            end
        end

        CoterieDockBridge.refreshDock(formObj, fc, ndb)
    end

    if mesa ~= nil and type(mesa.abrirNDBDeMesa) == "function" then
        mesa:abrirNDBDeMesa(CoterieDockBridge.ROOM_NDB_NAME, function(loadedNode)
            attachRoom(loadedNode or getFallbackRoomNode(mesa, formObj, ndb))
        end, { criar = true })
    else
        attachRoom(getFallbackRoomNode(mesa, formObj, ndb))
    end

    return { ok = true, roomNode = rawget(formObj, "_roomNode") }
end

function CoterieDockBridge.disconnectDock(formObj)
    if type(formObj) ~= "table" then return { ok = false } end
    ACTIVE_DOCKS[formObj] = nil

    local rObs = rawget(formObj, "_roomObserver")
    if rObs ~= nil then
        disableObserver(rObs)
        rawset(formObj, "_roomObserver", nil)
    end

    local cObsMap = rawget(formObj, "_charObservers")
    if type(cObsMap) == "table" then
        for k, obs in pairs(cObsMap) do
            disableObserver(obs)
            cObsMap[k] = nil
        end
        rawset(formObj, "_charObservers", nil)
    end

    rawset(formObj, "_loadedChars", nil)
    rawset(formObj, "_currentCards", nil)
    return { ok = true }
end

function CoterieDockBridge.recordSheetInitiative(sheet, d10, initMod, total, firecastApi)
    if type(sheet) ~= "table" then return { ok = false } end
    local fc = firecastApi or _G.Firecast
    local mesa = (fc ~= nil and type(fc.getMesaDe) == "function") and fc.getMesaDe(sheet) or nil
    if mesa == nil or type(mesa.abrirNDBDeMesa) ~= "function" then
        return { ok = false }
    end

    local bibItem, effVis = findBibMetaForSheet(mesa, sheet, fc)
    local charId
    if bibItem ~= nil and bibItem.codigoInterno ~= nil and tostring(bibItem.codigoInterno) ~= "" then
        charId = "char_" .. tostring(bibItem.codigoInterno)
    elseif bibItem ~= nil and nonEmpty(bibItem.key) then
        charId = tostring(bibItem.key)
    else
        charId = nonEmpty(sheet.nome) and tostring(sheet.nome) or "Combatente"
    end

    local charName = nonEmpty(sheet.nome) and tostring(sheet.nome)
        or ((bibItem ~= nil and nonEmpty(bibItem.nome)) and tostring(bibItem.nome) or "Personagem")
    local isHidden = (bibItem ~= nil) and (not effVis) or isTrue(sheet.init_oculto)

    local d10Int = safeInt(d10, 1)
    local modInt = safeInt(initMod, 0)
    local totInt = (total ~= nil) and safeInt(total, d10Int + modInt) or (d10Int + modInt)

    mesa:abrirNDBDeMesa(CoterieDockBridge.ROOM_NDB_NAME, function(roomNode)
        if type(roomNode) ~= "table" then return end
        local current = readInitiativeEntries(roomNode)
        local updated = V20.CoterieTracker.upsertInitiativeEntry(current, {
            id = charId,
            name = charName,
            d10 = d10Int,
            initMod = modInt,
            total = totInt,
            hidden = isHidden,
        }, CoterieDockBridge.MAX_INIT_ENTRIES)
        local phase = nonEmpty(roomNode.combate_fase) and tostring(roomNode.combate_fase) or "declaracao"
        writeInitiativeEntries(roomNode, updated, phase)
        notifyActiveDocks()
    end, { criar = true })

    return { ok = true, id = charId, hidden = isHidden, total = totInt }
end

function CoterieDockBridge.addQuickNpcInitiative(formObj, firecastApi, dialogsApi)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi, formObj)
    local mesa = resolveMesa(formObj, fc)
    if not isRoomStoryteller(mesa) then
        local err = "Apenas o Narrador pode adicionar NPCs rápidos na lista de Iniciativa."
        dlg.showMessage(err)
        return { ok = false, blocked = true, error = err }
    end

    local ui = (type(formObj) == "table" and type(formObj.sheet) == "table") and formObj.sheet or (formObj or {})
    local npcName = nonEmpty(ui.npc_init_nome) and tostring(ui.npc_init_nome) or "NPC"
    local npcMod = safeInt(ui.npc_init_mod, 0)
    local npcHidden = isTrue(ui.npc_init_oculto)
    local npcId = "npc_" .. npcName:lower():gsub("%s+", "_")
    local ndb = getNdbApi(nil, formObj)

    local rolObj = (fc ~= nil and type(fc.interpretarRolagem) == "function") and fc.interpretarRolagem("1d10") or nil

    local function commitNpcRoll(faceVal)
        local d10Val = safeInt(faceVal, 5)
        local total = d10Val + npcMod
        withRoomNode(formObj, mesa, fc, ndb, function(roomNode)
            local current = readInitiativeEntries(roomNode)
            local updated = V20.CoterieTracker.upsertInitiativeEntry(current, {
                id = npcId,
                name = npcName,
                d10 = d10Val,
                initMod = npcMod,
                total = total,
                hidden = npcHidden,
            }, CoterieDockBridge.MAX_INIT_ENTRIES)
            local phase = nonEmpty(roomNode.combate_fase) and tostring(roomNode.combate_fase) or "declaracao"
            writeInitiativeEntries(roomNode, updated, phase)
            notifyActiveDocks()
            if type(formObj) == "table" and ACTIVE_DOCKS[formObj] == nil then
                CoterieDockBridge.refreshDock(formObj, fc, ndb)
            end
        end)
        return d10Val, total
    end

    if (not npcHidden) and mesa ~= nil and mesa.activeChat ~= nil and rolObj ~= nil and type(mesa.activeChat.rolarDados) == "function" then
        mesa.activeChat:rolarDados(rolObj, "⚡ [" .. npcName .. "] Iniciativa (NPC)", function(rolado)
            local faces = Bridge.extractRollFaces(rolado)
            local d10Val, total = commitNpcRoll(faces[1] or 1)
            sendRoomBulletin(
                mesa,
                dlg,
                string.format("⚡ [%s] Iniciativa V20 (NPC): 1d10 (%d) + Mod (%d) = %d", npcName, d10Val, npcMod, total)
            )
        end)
        return { ok = true, hidden = false }
    else
        local face = 5
        if rolObj ~= nil and type(rolObj.rolarLocalmente) == "function" then
            rolObj:rolarLocalmente()
            local faces = Bridge.extractRollFaces(rolObj)
            face = faces[1] or 5
        else
            face = math.random(1, 10)
        end
        local d10Val, total = commitNpcRoll(face)
        return { ok = true, hidden = npcHidden, d10 = d10Val, total = total }
    end
end

function CoterieDockBridge.toggleCombatPhase(formObj, firecastApi, dialogsApi)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi, formObj)
    local mesa = resolveMesa(formObj, fc)
    if not isRoomStoryteller(mesa) then
        local err = "Apenas o Narrador pode alternar entre Fase de Declaração e Fase de Ação."
        dlg.showMessage(err)
        return { ok = false, blocked = true, error = err }
    end

    local ndb = getNdbApi(nil, formObj)
    local nextPhase = "acao"
    withRoomNode(formObj, mesa, fc, ndb, function(roomNode)
        local cur = tostring(roomNode.combate_fase or "declaracao"):lower()
        nextPhase = (cur == "acao") and "declaracao" or "acao"
        setAttrIfChanged(roomNode, "combate_fase", nextPhase)
        local entries = readInitiativeEntries(roomNode)
        writeInitiativeEntries(roomNode, entries, nextPhase)
        notifyActiveDocks()
        if type(formObj) == "table" and ACTIVE_DOCKS[formObj] == nil then
            CoterieDockBridge.refreshDock(formObj, fc, ndb)
        end
    end)

    return { ok = true, phase = nextPhase }
end

function CoterieDockBridge.clearInitiative(formObj, firecastApi, dialogsApi)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi, formObj)
    local mesa = resolveMesa(formObj, fc)
    if not isRoomStoryteller(mesa) then
        local err = "Apenas o Narrador pode limpar a Iniciativa da cena."
        dlg.showMessage(err)
        return { ok = false, blocked = true, error = err }
    end

    local ndb = getNdbApi(nil, formObj)
    withRoomNode(formObj, mesa, fc, ndb, function(roomNode)
        setAttrIfChanged(roomNode, "combate_fase", "declaracao")
        setAttrIfChanged(roomNode, "rodada_atual", 1)
        writeInitiativeEntries(roomNode, {}, "declaracao")
        notifyActiveDocks()
        if type(formObj) == "table" and ACTIVE_DOCKS[formObj] == nil then
            CoterieDockBridge.refreshDock(formObj, fc, ndb)
        end
    end)

    return { ok = true }
end

function CoterieDockBridge.changePage(formObj, delta, firecastApi, ndbApi)
    if type(formObj) ~= "table" then return { ok = false } end
    local cur = safeInt(rawget(formObj, "_stPage"), 1)
    local requested = math.max(1, cur + safeInt(delta, 0))
    rawset(formObj, "_stPage", requested)
    CoterieDockBridge.refreshDock(formObj, firecastApi, ndbApi)
    local maxP = math.max(1, safeInt(rawget(formObj, "_stTotalPages"), 1))
    local finalPage = clamp(safeInt(rawget(formObj, "_stPage"), 1), 1, maxP)
    rawset(formObj, "_stPage", finalPage)
    return { ok = true, page = finalPage, totalPages = maxP }
end

function CoterieDockBridge.adjustCardBlood(formObj, cardIdx, delta, firecastApi, dialogsApi)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi, formObj)
    local mesa = resolveMesa(formObj, fc)
    if not isRoomStoryteller(mesa) then
        local err = "Apenas o Narrador pode ajustar Vitae pelos cartões da Coterie."
        dlg.showMessage(err)
        return { ok = false, blocked = true, error = err }
    end

    if type(formObj) ~= "table" then
        return { ok = false, error = "Painel inválido." }
    end

    local cards = rawget(formObj, "_currentCards")
    if type(cards) ~= "table" or #cards == 0 then
        CoterieDockBridge.refreshDock(formObj, fc)
        cards = rawget(formObj, "_currentCards") or {}
    end

    local card = cards[safeInt(cardIdx, 1)]
    if type(card) ~= "table" or type(card.nodeRef) ~= "table" then
        return { ok = false, error = "Cartão sem personagem vinculado." }
    end

    if not card.isVampire and not card.isGhoul then
        local err = "Mortal humano não possui reserva de Vitae."
        dlg.showMessage(err)
        return { ok = false, error = err }
    end

    local ndb = getNdbApi(nil, formObj)
    local res = Bridge.adjustResource(card.nodeRef, "sangue_atual", safeInt(delta, 0), 0, "sangue_max", fc, dlg, ndb)
    notifyActiveDocks()
    if ACTIVE_DOCKS[formObj] == nil then
        CoterieDockBridge.refreshDock(formObj, fc, ndb)
    end
    return res
end

function CoterieDockBridge.approveCardXP(formObj, cardIdx, firecastApi, ndbApi, dialogsApi)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi, formObj)
    local mesa = resolveMesa(formObj, fc)
    if not isRoomStoryteller(mesa) then
        local err = "Apenas o Narrador pode aprovar solicitações de XP da Coterie."
        dlg.showMessage(err)
        return { ok = false, blocked = true, error = err }
    end

    if type(formObj) ~= "table" then
        return { ok = false, error = "Painel inválido." }
    end

    local ndb = getNdbApi(ndbApi, formObj)
    local cards = rawget(formObj, "_currentCards")
    if type(cards) ~= "table" or #cards == 0 then
        CoterieDockBridge.refreshDock(formObj, fc, ndb)
        cards = rawget(formObj, "_currentCards") or {}
    end

    local card = cards[safeInt(cardIdx, 1)]
    if type(card) ~= "table" or type(card.nodeRef) ~= "table" then
        return { ok = false, error = "Cartão sem personagem vinculado." }
    end

    local res = Bridge.submitOrApproveXP(card.nodeRef, "approve", nil, ndb, fc, dlg)
    if res and res.ok then
        local e = res.updatedEntry or {}
        sendRoomBulletin(
            mesa,
            dlg,
            string.format(
                "✨ [Coterie • XP Aprovado] %s: %s -> %s (-%d XP).",
                tostring(card.nome or "Personagem"),
                tostring(e.descricao or e.campo_alvo or "Característica"),
                tostring(e.novo_valor or ""),
                safeNonNegInt(e.custo_xp, 0)
            )
        )
    end
    notifyActiveDocks()
    if ACTIVE_DOCKS[formObj] == nil then
        CoterieDockBridge.refreshDock(formObj, fc, ndb)
    end
    return res
end

local function resolveBatchCharacters(formObj, mesa)
    if mesa ~= nil and type(mesa.biblioteca) == "table" then
        local loaded = nil
        CoterieDockBridge.scanLibrarySheets(mesa, function(chars)
            loaded = chars
        end, { onlyVisible = false })
        if type(loaded) == "table" then
            return loaded
        end
    end
    if type(formObj) == "table" and type(rawget(formObj, "_loadedChars")) == "table" then
        return rawget(formObj, "_loadedChars")
    end
    return {}
end

function CoterieDockBridge.batchAwakenNightly(formObj, firecastApi, dialogsApi)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi, formObj)
    local mesa = resolveMesa(formObj, fc)
    if not isRoomStoryteller(mesa) then
        local err = "Apenas o Narrador pode executar o Despertar Noturno em lote."
        dlg.showMessage(err)
        return { ok = false, blocked = true, error = err }
    end

    local ndb = getNdbApi(nil, formObj)
    local chars = resolveBatchCharacters(formObj, mesa)
    local visibleNames = {}
    local visibleWarnings = {}
    local hiddenCount = 0
    local hiddenTorporCount = 0
    local totalAwakened = 0

    for _, ch in ipairs(chars) do
        local sheet = ch and ch.nodeRef
        if type(sheet) == "table" and Bridge.isVampireSheet(sheet) then
            Bridge.syncDerivedFields(sheet, ndb)
            local awk = V20.WillpowerMorality.awakenNightly({
                isVampire = true,
                currentBlood = sheet.sangue_atual,
                spentThisTurn = sheet.sangue_gasto_turno,
                virtude2_val = sheet.virtude2_val,
            })
            sheet.sangue_atual = awk.newState.currentBlood
            sheet.sangue_gasto_turno = 0
            if not awk.ok then
                sheet.em_torpor = true
            end
            Bridge.syncDerivedFields(sheet, ndb)
            totalAwakened = totalAwakened + 1

            local cName = nonEmpty(sheet.nome) and tostring(sheet.nome) or tostring(ch.nome or "Vampiro")
            if ch.visible then
                table.insert(visibleNames, cName)
                if nonEmpty(awk.warning) then
                    table.insert(visibleWarnings, string.format("%s (%s)", cName, awk.warning))
                end
            else
                hiddenCount = hiddenCount + 1
                if not awk.ok then
                    hiddenTorporCount = hiddenTorporCount + 1
                end
            end
        end
    end

    local whoPart = (#visibleNames > 0) and table.concat(visibleNames, ", ") or "Nenhum PJ visível"
    local hiddenPart = (hiddenCount > 0) and string.format(" (+%d oculto(s))", hiddenCount) or ""
    if hiddenTorporCount > 0 then
        table.insert(visibleWarnings, string.format("%d vampiro(s) oculto(s) entrou(aram) em Torpor por inanição!", hiddenTorporCount))
    end
    local warnPart = (#visibleWarnings > 0) and (" ⚠️ " .. table.concat(visibleWarnings, " | ")) or ""
    local msg = string.format(
        "🌙 [Coterie • Despertar Noturno] Vitae matinal consumida (-1): %s%s.%s",
        whoPart,
        hiddenPart,
        warnPart
    )
    sendRoomBulletin(mesa, dlg, msg)

    notifyActiveDocks()
    if type(formObj) == "table" and ACTIVE_DOCKS[formObj] == nil then
        CoterieDockBridge.refreshDock(formObj, fc, ndb)
    end
    return { ok = true, awakenedCount = totalAwakened, message = msg }
end

function CoterieDockBridge.batchNewTurn(formObj, firecastApi, dialogsApi)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi, formObj)
    local mesa = resolveMesa(formObj, fc)
    if not isRoomStoryteller(mesa) then
        local err = "Apenas o Narrador pode avançar o Novo Turno global da Coterie."
        dlg.showMessage(err)
        return { ok = false, blocked = true, error = err }
    end

    local ndb = getNdbApi(nil, formObj)
    local chars = resolveBatchCharacters(formObj, mesa)
    local updatedCount = 0
    for _, ch in ipairs(chars) do
        local sheet = ch and ch.nodeRef
        if type(sheet) == "table" then
            Bridge.newTurn(sheet, fc, dlg)
            updatedCount = updatedCount + 1
        end
    end

    local nextRound = nil
    local sentMsg = nil
    withRoomNode(formObj, mesa, fc, ndb, function(roomNode)
        nextRound = math.max(1, safeInt(roomNode.rodada_atual, 1)) + 1
        setAttrIfChanged(roomNode, "rodada_atual", nextRound)
        setAttrIfChanged(roomNode, "combate_fase", "declaracao")
        local entries = readInitiativeEntries(roomNode)
        writeInitiativeEntries(roomNode, entries, "declaracao")

        sentMsg = string.format(
            "🔄 [Coterie • Novo Turno] Rodada %d iniciada — Fase de Declaração (Menor -> Maior Iniciativa) | %d ficha(s) sincronizada(s).",
            nextRound,
            updatedCount
        )
        sendRoomBulletin(mesa, dlg, sentMsg)

        notifyActiveDocks()
        if type(formObj) == "table" and ACTIVE_DOCKS[formObj] == nil then
            CoterieDockBridge.refreshDock(formObj, fc, ndb)
        end
    end)

    return { ok = true, round = nextRound, phase = "declaracao", updatedCount = updatedCount, message = sentMsg }
end

function CoterieDockBridge.batchEndScene(formObj, firecastApi, dialogsApi)
    local fc, dlg = getFirecastAndDialogs(firecastApi, dialogsApi, formObj)
    local mesa = resolveMesa(formObj, fc)
    if not isRoomStoryteller(mesa) then
        local err = "Apenas o Narrador pode encerrar a cena em lote."
        dlg.showMessage(err)
        return { ok = false, blocked = true, error = err }
    end

    local ndb = getNdbApi(nil, formObj)
    local chars = resolveBatchCharacters(formObj, mesa)
    local updatedCount = 0

    for _, ch in ipairs(chars) do
        local sheet = ch and ch.nodeRef
        if type(sheet) == "table" then
            local st = V20.Blood.clearSceneBuffs(Bridge.sheetToEngineState(sheet))
            st = V20.DisciplinesEngine.clearSceneBuffs(st)
            st = V20.Blood.newTurn(st)

            setAttrIfChanged(sheet, "sangue_atual", st.currentBlood)
            setAttrIfChanged(sheet, "sangue_gasto_turno", 0)
            setAttrIfChanged(sheet, "sangue_fraco_usado", st.thinBloodUsed)
            setAttrIfChanged(sheet, "fdv_temp", st.fdv_temp)
            setAttrIfChanged(sheet, "potencia_ativa_turno", false)
            setAttrIfChanged(sheet, "rapidez_acoes_ativas", 0)
            setAttrIfChanged(sheet, "rapidez_acoes_extras", 0)
            setAttrIfChanged(sheet, "buff_forca", 0)
            setAttrIfChanged(sheet, "buff_destreza", 0)
            setAttrIfChanged(sheet, "buff_vigor", 0)
            setAttrIfChanged(sheet, "malkav_suprimida_cena", false)
            setAttrIfChanged(sheet, "toreador_fascinado_cena", false)
            setAttrIfChanged(sheet, "em_agarrao", false)
            setAttrIfChanged(sheet, "cmb_defesas_feitas_turno", 0)
            setAttrIfChanged(sheet, "cmb_dano_pendente_ativo", false)

            Bridge.serializeBuffs(sheet, st.activeBuffs or {})
            Bridge.syncDerivedFields(sheet, ndb)
            updatedCount = updatedCount + 1
        end
    end

    local sentMsg = nil
    withRoomNode(formObj, mesa, fc, ndb, function(roomNode)
        setAttrIfChanged(roomNode, "rodada_atual", 1)
        setAttrIfChanged(roomNode, "combate_fase", "declaracao")
        local entries = readInitiativeEntries(roomNode)
        writeInitiativeEntries(roomNode, entries, "declaracao")

        sentMsg = string.format(
            "🧹 [Coterie • Fim de Cena] Buffs físicos, poderes de cena e agarrões encerrados (%d ficha(s)); Rodada reiniciada para 1.",
            updatedCount
        )
        sendRoomBulletin(mesa, dlg, sentMsg)

        notifyActiveDocks()
        if type(formObj) == "table" and ACTIVE_DOCKS[formObj] == nil then
            CoterieDockBridge.refreshDock(formObj, fc, ndb)
        end
    end)

    return { ok = true, round = 1, updatedCount = updatedCount, message = sentMsg }
end

_G.V20CoterieDockBridge = CoterieDockBridge
return CoterieDockBridge
