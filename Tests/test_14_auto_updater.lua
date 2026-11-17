local V20 = require("Core.v20_init")
local VU = require("Core.version_updater")
local AU = require("Adapter.auto_updater")

assert(V20.VersionUpdater == VU, "V20.VersionUpdater deve estar registrado em Core/v20_init.lua")
assert(_G.V20AutoUpdater == AU, "_G.V20AutoUpdater deve estar exposto globalmente")

-- 1. Constantes oficiais apontando para krleandro/vampire_fichas
assert(AU.MODULE_ID == "br.com.v20.suite")
assert(AU.REPO_URL == "https://github.com/krleandro/vampire_fichas")
assert(AU.MANIFEST_URL == "https://raw.githubusercontent.com/krleandro/vampire_fichas/main/module.xml")
assert(AU.RPK_URL == "https://github.com/krleandro/vampire_fichas/raw/main/dist/Vampiro_V20_Suite.rpk")

-- 2. Comparação semântica de versões (Core/version_updater.lua)
assert(VU.isNewVersion("1.0.2", "1.0.3") == true)
assert(VU.isNewVersion("1.0.2", "1.1.0") == true)
assert(VU.isNewVersion("1.0.9", "1.0.10") == true)
assert(VU.isNewVersion("1.0.2", "1.0.2") == false)
assert(VU.isNewVersion("1.2.0", "1.1.9") == false)
assert(VU.isNewVersion("v1.0.2", "v2.0.0") == true)
assert(VU.isNewVersion("1.0", "1.0.1") == true)
assert(VU.isNewVersion("1.0.1", "1.0") == false)

-- 3. Extração de <version> e <id> de module.xml remoto
local sampleXml = [[<?xml version="1.0" encoding="UTF-8"?>
<module sdkVersion="3.7b">
    <id>br.com.v20.suite</id>
    <version>1.2.4</version>
</module>]]
local parsed = VU.parseManifestXml(sampleXml)
assert(parsed ~= nil and parsed.id == "br.com.v20.suite" and parsed.version == "1.2.4")
assert(VU.parseManifestXml("invalido sem tags") == nil)

-- Helper para criar formulário mockado com controles da aba Sobre ([TESTE_E2E])
local function makeMockForm(name)
    local texts = {}
    local enabled = {}
    local function mkLabel(initTxt)
        local lbl = { _txt = initTxt or "" }
        function lbl:setText(t) self._txt = tostring(t or "") end
        function lbl:getText() return self._txt end
        return lbl
    end
    local function mkBtn()
        local b = { _en = true, _txt = "" }
        function b:setEnabled(v) self._en = (v == true) end
        function b:setText(t) self._txt = tostring(t or "") end
        return b
    end
    local f = {
        _testName = "[TESTE_E2E] " .. tostring(name),
        lblUpdateStatus = mkLabel("Versão instalada: 1.0.2"),
        btnVerificarAtualizacao = mkBtn(),
        btnAbrirGithub = mkBtn(),
    }
    return f, texts, enabled
end

-- 4. Offline / sem API Internet: checkOnOpen faz no-op gracioso sem travar
AU.resetSessionState()
local offlineForm = makeMockForm("OfflineForm")
local offRes = AU.checkOnOpen(offlineForm, { internet = false, plugins = false, dialogs = false, gui = false })
assert(offRes.ok == false and offRes.skipped == true)

-- 5. Checagem automática 1x por sessão: versão igual não abre diálogo, 2ª chamada é ignorada na sessão
AU.resetSessionState()
local httpCalls = 0
local dialogPrompts = 0
local mockApisUpToDate = {
    plugins = {
        getInstalledPlugins = function()
            return { { moduleId = "br.com.v20.suite", version = "1.0.2", name = "[TESTE_E2E] Suite V20" } }
        end,
    },
    internet = {
        newHTTPRequest = function(method, url)
            httpCalls = httpCalls + 1
            assert(method == "GET" and url == AU.MANIFEST_URL)
            local listeners = {}
            local req = {
                status = 200,
                responseText = "<module><id>br.com.v20.suite</id><version>1.0.2</version></module>",
            }
            function req:addEventListener(ev, fn) listeners[ev] = fn; return 1 end
            function req:send()
                if listeners.onResponse then listeners.onResponse() end
            end
            return req
        end,
    },
    dialogs = {
        choose = function() dialogPrompts = dialogPrompts + 1 end,
        showMessage = function() end,
    },
}

local f1 = makeMockForm("BrujahSession1")
AU.checkOnOpen(f1, mockApisUpToDate)
assert(httpCalls == 1 and dialogPrompts == 0)
assert(f1.lblUpdateStatus:getText():find("atualizada") ~= nil or f1.lblUpdateStatus:getText():find("1.0.2") ~= nil)

local f2 = makeMockForm("TremereSession2")
local secondCheck = AU.checkOnOpen(f2, mockApisUpToDate)
assert(secondCheck.alreadyChecked == true and httpCalls == 1, "Não deve repetir requisição automática na mesma sessão")

-- 6. Nova versão disponível -> aceita atualizar -> baixa .rpk e instala via installPlugin(stream, true)
AU.resetSessionState()
local installedStreams = {}
local shownMessages = {}
local openedUrls = {}

local function makeUpdateApis(installSucceeds, userChoiceIdx)
    return {
        plugins = {
            getInstalledPlugins = function()
                return { { moduleId = "br.com.v20.suite", version = "1.0.2" } }
            end,
            getRPKDetails = function(stream)
                return { moduleId = "br.com.v20.suite", version = "1.1.0" }
            end,
            installPlugin = function(stream, ignoreIfOlder)
                table.insert(installedStreams, { stream = stream, ignoreIfOlder = ignoreIfOlder })
                return installSucceeds
            end,
        },
        internet = {
            newHTTPRequest = function(method, url)
                local listeners = {}
                local req = {
                    status = 200,
                    responseText = "<module><id>br.com.v20.suite</id><version>1.1.0</version></module>",
                }
                function req:addEventListener(ev, fn) listeners[ev] = fn; return 1 end
                function req:send()
                    if listeners.onResponse then listeners.onResponse() end
                end
                return req
            end,
            download = function(url, onFinish, onError, onProgress, cacheMode)
                assert(url == AU.RPK_URL)
                if onProgress then onProgress(512, 1024) end
                onFinish({ handle = 999, tag = "[TESTE_E2E]_RPK_STREAM" }, "application/octet-stream")
                return 1
            end,
        },
        dialogs = {
            choose = function(prompt, options, cb)
                dialogPrompts = dialogPrompts + 1
                cb(true, userChoiceIdx, options[userChoiceIdx])
            end,
            showMessage = function(msg)
                table.insert(shownMessages, msg)
            end,
        },
        gui = {
            openInBrowser = function(url)
                table.insert(openedUrls, url)
            end,
        },
    }
end

local fUpd = makeMockForm("GiovanniUpdate")
AU.checkAndInstall(fUpd, { manual = true }, makeUpdateApis(true, 1))
assert(#installedStreams == 1 and installedStreams[1].ignoreIfOlder == true)
assert(#openedUrls == 0)
assert(fUpd.lblUpdateStatus:getText():find("1.1.0") ~= nil)

-- 7. Fallback automático para GUI.openInBrowser(RPK_URL) quando installPlugin retornar false
local fFallback = makeMockForm("NosferatuFallback")
AU.checkAndInstall(fFallback, { manual = true }, makeUpdateApis(false, 1))
assert(#installedStreams == 2)
assert(#openedUrls == 1 and openedUrls[1] == AU.RPK_URL)

-- 8. Botão abrir GitHub chama GUI.openInBrowser(REPO_URL)
AU.openRepository({ gui = { openInBrowser = function(u) table.insert(openedUrls, u) end } })
assert(openedUrls[#openedUrls] == AU.REPO_URL)
