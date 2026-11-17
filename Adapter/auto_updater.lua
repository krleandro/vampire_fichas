local V20 = require("Core.v20_init")

local AutoUpdater = {
    MODULE_ID = "br.com.v20.suite",
    BUNDLED_VERSION = "1.0.2",
    REPO_URL = "https://github.com/krleandro/vampire_fichas",
    MANIFEST_URL = "https://raw.githubusercontent.com/krleandro/vampire_fichas/HEAD/module.xml",
    RPK_URL = "https://github.com/krleandro/vampire_fichas/raw/HEAD/dist/Vampiro_V20_Suite.rpk",
}

local function tryRequire(modName)
    local ok, mod = pcall(require, modName)
    if ok and type(mod) == "table" then
        return mod
    end
    return nil
end

local function resolveApis(overrides)
    overrides = (type(overrides) == "table") and overrides or {}

    local internetApi = nil
    if overrides.internet == false then
        internetApi = nil
    elseif type(overrides.internet) == "table" then
        internetApi = overrides.internet
    else
        internetApi = rawget(_G, "Internet") or rawget(_G, "internet") or tryRequire("internet.lua")
    end

    local pluginsApi = nil
    if overrides.plugins == false then
        pluginsApi = nil
    elseif type(overrides.plugins) == "table" then
        pluginsApi = overrides.plugins
    else
        local fc = rawget(_G, "Firecast") or rawget(_G, "rrpg")
        pluginsApi = (fc and (fc.Plugins or fc.plugins)) or tryRequire("plugins.lua")
    end

    local dialogsApi = nil
    if overrides.dialogs == false then
        dialogsApi = nil
    elseif type(overrides.dialogs) == "table" then
        dialogsApi = overrides.dialogs
    else
        dialogsApi = rawget(_G, "Dialogs") or tryRequire("dialogs.lua")
    end

    local guiApi = nil
    if overrides.gui == false then
        guiApi = nil
    elseif type(overrides.gui) == "table" then
        guiApi = overrides.gui
    else
        guiApi = rawget(_G, "GUI") or rawget(_G, "gui") or tryRequire("gui.lua")
    end

    return {
        internet = internetApi,
        plugins = pluginsApi,
        dialogs = dialogsApi,
        gui = guiApi,
    }
end

local function setStatusLabel(formObj, text)
    if type(formObj) == "table" and formObj.lblUpdateStatus ~= nil and type(formObj.lblUpdateStatus.setText) == "function" then
        formObj.lblUpdateStatus:setText(tostring(text or ""))
    end
end

local function setUpdateBtnEnabled(formObj, enabled)
    if type(formObj) == "table" and formObj.btnVerificarAtualizacao ~= nil and type(formObj.btnVerificarAtualizacao.setEnabled) == "function" then
        formObj.btnVerificarAtualizacao:setEnabled(enabled == true)
    end
end

function AutoUpdater.resetSessionState()
    rawset(_G, "__V20_SUITE_UPDATE_CHECKED", false)
    rawset(_G, "__V20_SUITE_MUTE_UPDATE_SESSION", false)
end

function AutoUpdater.getInstalledVersion(pluginsApi)
    if type(pluginsApi) == "table" and type(pluginsApi.getInstalledPlugins) == "function" then
        local ok, list = pcall(pluginsApi.getInstalledPlugins)
        if ok and type(list) == "table" then
            for i = 1, #list do
                local item = list[i]
                if type(item) == "table" and item.moduleId == AutoUpdater.MODULE_ID and type(item.version) == "string" and item.version ~= "" then
                    return item.version
                end
            end
        end
    end
    return AutoUpdater.BUNDLED_VERSION
end

local function openBrowserUrl(guiApi, url)
    if type(guiApi) == "table" and type(guiApi.openInBrowser) == "function" then
        pcall(guiApi.openInBrowser, url)
        return true
    end
    return false
end

function AutoUpdater.openRepository(apiOverrides)
    local apis = resolveApis(apiOverrides)
    return openBrowserUrl(apis.gui, AutoUpdater.REPO_URL)
end

local function fetchManifestXml(internetApi, onSuccess, onError)
    if type(internetApi) ~= "table" then
        if onError then onError("API Internet indisponível.") end
        return false
    end

    if type(internetApi.newHTTPRequest) == "function" then
        local req = internetApi.newHTTPRequest("GET", AutoUpdater.MANIFEST_URL)
        if type(req) == "table" then
            if type(req.setRequestHeader) == "function" then
                pcall(req.setRequestHeader, req, "Cache-Control", "no-cache")
            end
            if type(req.addEventListener) == "function" then
                req:addEventListener("onResponse", function()
                    local st = tonumber(req.status) or 200
                    local body = req.responseText
                    if (st == 200 or st == 0) and type(body) == "string" and body ~= "" then
                        onSuccess(body)
                    elseif onError then
                        onError("HTTP " .. tostring(st))
                    end
                end)
                req:addEventListener("onError", function(errMsg)
                    if onError then onError(tostring(errMsg or "Falha de rede")) end
                end)
            end
            if type(req.send) == "function" then
                req:send()
                return true
            end
        end
    end

    if type(internetApi.download) == "function" then
        internetApi.download(
            AutoUpdater.MANIFEST_URL,
            function(stream)
                local txt = nil
                if type(stream) == "table" and type(stream.readBinary) == "function" then
                    local ok, decoded = pcall(stream.readBinary, stream, "utf8")
                    if ok then txt = decoded end
                end
                if type(txt) == "string" and txt ~= "" then
                    onSuccess(txt)
                elseif onError then
                    onError("Manifesto vazio.")
                end
            end,
            function(errMsg)
                if onError then onError(tostring(errMsg or "Falha no download do manifesto")) end
            end,
            nil,
            "checkForModification"
        )
        return true
    end

    if onError then onError("Nenhum método HTTP disponível.") end
    return false
end

local function downloadAndInstallRpk(formObj, remoteVer, apis)
    if type(apis.internet) ~= "table" or type(apis.internet.download) ~= "function" then
        openBrowserUrl(apis.gui, AutoUpdater.RPK_URL)
        return
    end

    setUpdateBtnEnabled(formObj, false)
    setStatusLabel(formObj, string.format("Baixando atualização v%s...", tostring(remoteVer)))

    apis.internet.download(
        AutoUpdater.RPK_URL,
        function(stream)
            setUpdateBtnEnabled(formObj, true)
            local installedOk = false
            if type(apis.plugins) == "table" and type(apis.plugins.installPlugin) == "function" and stream ~= nil then
                local okCall, resInstall = pcall(apis.plugins.installPlugin, stream, true)
                installedOk = (okCall and resInstall == true)
            end

            if installedOk then
                setStatusLabel(formObj, string.format("Suíte atualizada para v%s! Reabra a ficha se necessário.", tostring(remoteVer)))
                if type(apis.dialogs) == "table" and type(apis.dialogs.showMessage) == "function" then
                    apis.dialogs.showMessage(
                        string.format("Suíte Vampiro V20 atualizada com sucesso para a versão v%s!", tostring(remoteVer))
                    )
                end
            else
                setStatusLabel(formObj, string.format("Abrindo download direto v%s no navegador...", tostring(remoteVer)))
                openBrowserUrl(apis.gui, AutoUpdater.RPK_URL)
            end
        end,
        function(errMsg)
            setUpdateBtnEnabled(formObj, true)
            setStatusLabel(formObj, "Falha ao baixar .rpk: " .. tostring(errMsg or "erro desconhecido"))
            openBrowserUrl(apis.gui, AutoUpdater.RPK_URL)
        end,
        function(downloaded, total)
            local tot = tonumber(total) or 0
            local dl = tonumber(downloaded) or 0
            if tot > 0 then
                local pct = math.min(100, math.max(0, math.floor((dl / tot) * 100)))
                setStatusLabel(formObj, string.format("Baixando v%s (%d%%)...", tostring(remoteVer), pct))
            end
        end,
        "alwaysDownload"
    )
end

function AutoUpdater.checkAndInstall(formObj, opts, apiOverrides)
    opts = (type(opts) == "table") and opts or {}
    local manual = (opts.manual == true)
    local apis = resolveApis(apiOverrides)

    if type(apis.internet) ~= "table" or (type(apis.internet.newHTTPRequest) ~= "function" and type(apis.internet.download) ~= "function") then
        return { ok = false, skipped = true, reason = "Sem API Internet ativa." }
    end

    local installedVer = AutoUpdater.getInstalledVersion(apis.plugins)
    setStatusLabel(formObj, string.format("Verificando atualizações no GitHub (instalada: v%s)...", installedVer))

    fetchManifestXml(
        apis.internet,
        function(xmlBody)
            local manifest = V20.VersionUpdater.parseManifestXml(xmlBody)
            if type(manifest) ~= "table" or type(manifest.version) ~= "string" then
                setStatusLabel(formObj, string.format("Versão instalada: v%s (manifesto indisponível)", installedVer))
                if manual and type(apis.dialogs) == "table" and type(apis.dialogs.showMessage) == "function" then
                    apis.dialogs.showMessage("Não foi possível ler a versão remota no GitHub no momento.")
                end
                return
            end

            if manifest.id ~= nil and manifest.id ~= AutoUpdater.MODULE_ID then
                setStatusLabel(formObj, string.format("Versão instalada: v%s", installedVer))
                return
            end

            local remoteVer = manifest.version
            if V20.VersionUpdater.isNewVersion(installedVer, remoteVer) then
                setStatusLabel(formObj, string.format("Nova versão disponível: v%s (Instalada: v%s)", remoteVer, installedVer))
                if (not manual) and rawget(_G, "__V20_SUITE_MUTE_UPDATE_SESSION") == true then
                    return
                end

                local prompt = string.format(
                    "Nova versão v%s da Suíte Vampiro V20 disponível (instalada: v%s). Deseja instalar agora?",
                    remoteVer,
                    installedVer
                )
                if type(apis.dialogs) == "table" and type(apis.dialogs.choose) == "function" then
                    apis.dialogs.choose(
                        prompt,
                        { "Instalar Agora", "Depois", "Silenciar nesta Sessão" },
                        function(selected, selectedIndex)
                            if selected and selectedIndex == 1 then
                                downloadAndInstallRpk(formObj, remoteVer, apis)
                            elseif selected and selectedIndex == 3 then
                                rawset(_G, "__V20_SUITE_MUTE_UPDATE_SESSION", true)
                            end
                        end,
                        1
                    )
                elseif type(apis.dialogs) == "table" and type(apis.dialogs.confirmYesNo) == "function" then
                    apis.dialogs.confirmYesNo(prompt, function(yes)
                        if yes then
                            downloadAndInstallRpk(formObj, remoteVer, apis)
                        end
                    end)
                elseif manual then
                    downloadAndInstallRpk(formObj, remoteVer, apis)
                end
            else
                setStatusLabel(formObj, string.format("Suíte atualizada (v%s)", installedVer))
                if manual and type(apis.dialogs) == "table" and type(apis.dialogs.showMessage) == "function" then
                    apis.dialogs.showMessage(string.format("Sua Suíte Vampiro V20 já está na versão mais recente (v%s)!", installedVer))
                end
            end
        end,
        function(errMsg)
            setStatusLabel(formObj, string.format("Versão instalada: v%s (repositório ainda sem release ou offline)", installedVer))
            if manual and type(apis.dialogs) == "table" and type(apis.dialogs.showMessage) == "function" then
                apis.dialogs.showMessage("Não foi possível consultar atualizações no GitHub (" .. tostring(errMsg or "offline") .. ").")
            end
        end
    )

    return { ok = true, checked = true, installedVersion = installedVer }
end

function AutoUpdater.checkOnOpen(formObj, apiOverrides)
    local apis = resolveApis(apiOverrides)
    if type(apis.internet) ~= "table" or (type(apis.internet.newHTTPRequest) ~= "function" and type(apis.internet.download) ~= "function") then
        return { ok = false, skipped = true }
    end
    if rawget(_G, "__V20_SUITE_UPDATE_CHECKED") == true then
        local instVer = AutoUpdater.getInstalledVersion(apis.plugins)
        setStatusLabel(formObj, string.format("Versão instalada: v%s", instVer))
        return { ok = true, alreadyChecked = true }
    end
    rawset(_G, "__V20_SUITE_UPDATE_CHECKED", true)
    return AutoUpdater.checkAndInstall(formObj, { manual = false }, apis)
end

_G.V20AutoUpdater = AutoUpdater
return AutoUpdater
