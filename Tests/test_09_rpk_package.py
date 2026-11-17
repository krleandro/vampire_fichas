#!/usr/bin/env python3
"""Auditoria E2E do pacote compilado dist/Vampiro_V20_Suite.rpk (v1.0.0, 16 formulários) segundo SDK 3.7b e PF-4."""
import ctypes
import glob
import hashlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BUILD_SCRIPT = os.path.join(ROOT, "tools", "build_v20_suite.py")
DLL_PATH = r"C:\Users\Cliente\AppData\Local\Firecast\lua54x64.dll"

EXPECTED_VERSION = "1.0.0"

EXPECTED_SHEETS: list[tuple[str, str, str, str, str]] = [
    ("brujah", "Sheets/frmBrujah.lfm", "br.com.v20.Brujah", "frmBrujah", "Vampiro V20 - Brujah"),
    ("gangrel", "Sheets/frmGangrel.lfm", "br.com.v20.Gangrel", "frmGangrel", "Vampiro V20 - Gangrel"),
    ("malkavian", "Sheets/frmMalkavian.lfm", "br.com.v20.Malkavian", "frmMalkavian", "Vampiro V20 - Malkaviano"),
    ("nosferatu", "Sheets/frmNosferatu.lfm", "br.com.v20.Nosferatu", "frmNosferatu", "Vampiro V20 - Nosferatu"),
    ("toreador", "Sheets/frmToreador.lfm", "br.com.v20.Toreador", "frmToreador", "Vampiro V20 - Toreador"),
    ("tremere", "Sheets/frmTremere.lfm", "br.com.v20.Tremere", "frmTremere", "Vampiro V20 - Tremere"),
    ("ventrue", "Sheets/frmVentrue.lfm", "br.com.v20.Ventrue", "frmVentrue", "Vampiro V20 - Ventrue"),
    ("assamite", "Sheets/frmAssamite.lfm", "br.com.v20.Assamite", "frmAssamite", "Vampiro V20 - Assamita"),
    ("setite", "Sheets/frmSetite.lfm", "br.com.v20.Setite", "frmSetite", "Vampiro V20 - Seguidores de Set"),
    ("giovanni", "Sheets/frmGiovanni.lfm", "br.com.v20.Giovanni", "frmGiovanni", "Vampiro V20 - Giovanni"),
    ("lasombra", "Sheets/frmLasombra.lfm", "br.com.v20.Lasombra", "frmLasombra", "Vampiro V20 - Lasombra"),
    ("ravnos", "Sheets/frmRavnos.lfm", "br.com.v20.Ravnos", "frmRavnos", "Vampiro V20 - Ravnos"),
    ("tzimisce", "Sheets/frmTzimisce.lfm", "br.com.v20.Tzimisce", "frmTzimisce", "Vampiro V20 - Tzimisce"),
    ("caitiff", "Sheets/frmCaitiff.lfm", "br.com.v20.Caitiff", "frmCaitiff", "Vampiro V20 - Caitiff"),
    ("mortal", "Sheets/frmMortal.lfm", "br.com.v20.Mortal", "frmMortal", "Vampiro V20 - Mortal"),
]

DOCK_SPEC: tuple[str, str, str, str, str, str] = (
    "coterie_dock",
    "Sheets/frmV20CoterieDock.lfm",
    "br.com.v20.CoterieDock",
    "frmV20CoterieDock",
    "Vampiro V20 - Painel da Coterie & Iniciativa",
    "tablesDock",
)

EXPECTED_ALL_FORMS: list[tuple[str, str, str, str, str, str]] = [
    (cid, lfm, dt, fn, title, "sheetTemplate")
    for cid, lfm, dt, fn, title in EXPECTED_SHEETS
] + [DOCK_SPEC]


def _lua_forms_table() -> str:
    rows = [
        f'    {{ cid = "{cid}", lfmLua = "{lfm}.lua", dataType = "{dt}", formName = "{fn}", formType = "{ft}" }}'
        for cid, lfm, dt, fn, _, ft in EXPECTED_ALL_FORMS
    ]
    return "{\n" + ",\n".join(rows) + "\n}"


def validate_lua_buffer(dll: ctypes.CDLL, lua_bytes: bytes, chunk_name: str, allow_bom: bool = False) -> None:
    if lua_bytes.startswith(b"\xef\xbb\xbf"):
        assert allow_bom, f"BOM UTF-8 inesperado em script do projeto: {chunk_name}"
        lua_bytes = lua_bytes[3:]
    L = dll.luaL_newstate()
    try:
        rc = dll.luaL_loadbufferx(L, lua_bytes, len(lua_bytes), chunk_name.encode("utf-8"), b"t")
        if rc != 0:
            ln = ctypes.c_size_t(0)
            msg = dll.lua_tolstring(L, -1, ctypes.byref(ln)).decode("utf-8", errors="replace")
            raise AssertionError(f"Erro de sintaxe Lua 5.4 em {chunk_name}: {msg}")
    finally:
        dll.lua_close(L)


def run_lua_in_isolated_state(dll: ctypes.CDLL, lua_code: str, chunk_name: str = "@test_09_runtime") -> None:
    L = dll.luaL_newstate()
    try:
        dll.luaL_openlibs(L)
        payload = lua_code.encode("utf-8")
        rc = dll.luaL_loadbufferx(L, payload, len(payload), chunk_name.encode("utf-8"), b"t")
        if rc != 0:
            ln = ctypes.c_size_t(0)
            msg = dll.lua_tolstring(L, -1, ctypes.byref(ln)).decode("utf-8", errors="replace")
            raise AssertionError(f"Erro de compilação em {chunk_name}: {msg}")
        rc = dll.lua_pcallk(L, 0, 0, 0, 0, None)
        if rc != 0:
            ln = ctypes.c_size_t(0)
            msg = dll.lua_tolstring(L, -1, ctypes.byref(ln)).decode("utf-8", errors="replace")
            raise AssertionError(f"Erro de runtime em {chunk_name}:\n{msg}")
    finally:
        dll.lua_close(L)


def setup_lua_dll() -> ctypes.CDLL:
    assert os.path.exists(DLL_PATH), f"lua54x64.dll não encontrada em {DLL_PATH}"
    dll = ctypes.CDLL(DLL_PATH)
    dll.luaL_newstate.restype = ctypes.c_void_p
    dll.luaL_openlibs.argtypes = [ctypes.c_void_p]
    dll.luaL_loadbufferx.argtypes = [
        ctypes.c_void_p,
        ctypes.c_char_p,
        ctypes.c_size_t,
        ctypes.c_char_p,
        ctypes.c_char_p,
    ]
    dll.luaL_loadbufferx.restype = ctypes.c_int
    dll.lua_pcallk.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_ssize_t,
        ctypes.c_void_p,
    ]
    dll.lua_pcallk.restype = ctypes.c_int
    dll.lua_tolstring.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_size_t)]
    dll.lua_tolstring.restype = ctypes.c_char_p
    dll.lua_close.argtypes = [ctypes.c_void_p]
    return dll


def verify_xml_escaping_pf4() -> None:
    """PF-4: Garante que build_multi_assembled_xml escapa &, \", <, > em atributos e textos XML."""
    spec = importlib.util.spec_from_file_location("build_v20_suite", BUILD_SCRIPT)
    assert spec is not None and spec.loader is not None, "Não foi possível carregar tools/build_v20_suite.py"
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)

    sandbox_dir = tempfile.mkdtemp(prefix="test_e2e_xml_escape_sandbox_")
    os.makedirs(os.path.join(sandbox_dir, "Sheets"), exist_ok=True)
    orig_root = builder.ROOT
    try:
        mod_xml_src = os.path.join(sandbox_dir, "module.xml")
        with open(mod_xml_src, "w", encoding="utf-8") as f:
            f.write(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<module sdkVersion="3.7b">\n'
                "    <id>br.com.v20.test_e2e</id>\n"
                "    <version>0.6.0</version>\n"
                '    <info lang="pt-BR">\n'
                "        <name>[TESTE_E2E] Vampiro &amp; Máscara \"V20\" &lt;Suíte&gt;</name>\n"
                "        <description>[TESTE_E2E] Criação &amp; XP (\"Clã\" &lt;4ª-15ª&gt;)</description>\n"
                "        <author>[TESTE_E2E] Carlos &amp; Equipe</author>\n"
                "        <site>https://firecast.app/?a=1&amp;b=2</site>\n"
                "        <contact>[TESTE_E2E] Mestre \"V20\" &amp; Cia</contact>\n"
                "    </info>\n"
                "</module>\n"
            )
        lfm_src = os.path.join(sandbox_dir, "Sheets", "frmTesteE2E.lfm")
        with open(lfm_src, "w", encoding="utf-8") as f:
            f.write(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<form name="frmTesteE2E" formType="sheetTemplate" dataType="br.com.v20.TesteE2E" '
                'title="[TESTE_E2E] Ficha &amp; Clã &quot;Especial&quot; &lt;V20&gt;" align="client" theme="dark"/>\n'
            )

        builder.ROOT = sandbox_dir
        assembled = builder.build_multi_assembled_xml(
            mod_xml_src, ["Sheets/frmTesteE2E.lfm"], 'Vampiro_"Suite"&Test.rpk'
        )
        parsed = ET.fromstring(assembled)
        assert parsed.attrib["originalPluginFileName"] == 'Vampiro_"Suite"&Test.rpk'
        assert parsed.findtext("version") == "0.6.0"
        assert parsed.findtext("name") == '[TESTE_E2E] Vampiro & Máscara "V20" <Suíte>'
        assert parsed.findtext("description") == '[TESTE_E2E] Criação & XP ("Clã" <4ª-15ª>)'
        dt_el = parsed.find("./dataTypes/dataType")
        assert dt_el is not None
        assert dt_el.attrib["title"] == '[TESTE_E2E] Ficha & Clã "Especial" <V20>'
        asm_info = parsed.find("./assembledFeatures/dataTypes/dataType/info")
        assert asm_info is not None
        assert asm_info.attrib["title"] == '[TESTE_E2E] Ficha & Clã "Especial" <V20>'
    finally:
        builder.ROOT = orig_root
        shutil.rmtree(sandbox_dir, ignore_errors=True)


def verify_tablesdock_compiler_enhancements(dll: ctypes.CDLL) -> None:
    """
    Valida que compile_v20_lfm em tools/build_v20_suite.py emite:
    - obj._e_form_event{k} + liberação reversa em obj:_releaseEvents() para <event> filhos diretos de <form>;
    - hook self:_onBeforeDestroy() no início de obj:destroy();
    - Firecast.registrarSpecialForm(_{form_name}) para formType="tablesDock", sem injetá-lo em sheetTemplate.
    """
    spec = importlib.util.spec_from_file_location("build_v20_suite", BUILD_SCRIPT)
    assert spec is not None and spec.loader is not None, "Não foi possível carregar tools/build_v20_suite.py"
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    assert hasattr(builder, "compile_v20_lfm"), "build_v20_suite.py deve expor compile_v20_lfm"
    help_res = subprocess.run([sys.executable, BUILD_SCRIPT, "--help"], capture_output=True, text=True, check=True)
    assert "--output-dir" in help_res.stdout and "--skip-regenerate" in help_res.stdout
    base_compiler = builder.load_base_compiler()

    sandbox_dir = tempfile.mkdtemp(prefix="test_e2e_dock_compiler_")
    try:
        dock_lfm = os.path.join(sandbox_dir, "frmTesteE2EDock.lfm")
        with open(dock_lfm, "w", encoding="utf-8", newline="\n") as f:
            f.write(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<form name="frmTesteE2EDock" formType="tablesDock" dataType="br.com.v20.test_e2e.Dock" '
                'title="[TESTE_E2E] Painel Coterie Dock" width="340" height="580" theme="dark">\n'
                '    <script><![CDATA[\n'
                '        self._onBeforeDestroy = function(fObj) fObj._beforeDestroyFired = true end\n'
                '    ]]></script>\n'
                '    <button name="btnPing" text="[TESTE_E2E] Ping" width="80" height="24">\n'
                '        <event name="onClick">self._pingClicked = true</event>\n'
                '    </button>\n'
                '    <event name="OnShow">self._onShowFired = true</event>\n'
                '    <event name="OnHide">self._onHideFired = true</event>\n'
                '</form>\n'
            )

        sheet_lfm = os.path.join(sandbox_dir, "frmTesteE2ESheet.lfm")
        with open(sheet_lfm, "w", encoding="utf-8", newline="\n") as f:
            f.write(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<form name="frmTesteE2ESheet" formType="sheetTemplate" dataType="br.com.v20.test_e2e.Sheet" '
                'title="[TESTE_E2E] Ficha Padrão" align="client" theme="dark"/>\n'
            )

        dock_lua = builder.compile_v20_lfm(base_compiler, dock_lfm)
        sheet_lua = builder.compile_v20_lfm(base_compiler, sheet_lfm)

        validate_lua_buffer(dll, dock_lua.encode("utf-8"), "@frmTesteE2EDock.lfm.lua")
        validate_lua_buffer(dll, sheet_lua.encode("utf-8"), "@frmTesteE2ESheet.lfm.lua")

        assert 'require("v20_loader.lua");' in dock_lua
        assert 'obj._e_form_event0 = obj:addEventListener("OnShow",' in dock_lua
        assert 'obj._e_form_event1 = obj:addEventListener("OnHide",' in dock_lua
        assert "__o_rrpgObjs.removeEventListenerById(self._e_form_event1);" in dock_lua
        assert "__o_rrpgObjs.removeEventListenerById(self._e_form_event0);" in dock_lua
        assert (
            dock_lua.index("__o_rrpgObjs.removeEventListenerById(self._e_form_event1);")
            < dock_lua.index("__o_rrpgObjs.removeEventListenerById(self._e_form_event0);")
        ), "Eventos diretos do <form> devem ser liberados em ordem reversa"
        assert "if self._onBeforeDestroy ~= nil then self:_onBeforeDestroy(); end;" in dock_lua
        assert "Firecast.registrarSpecialForm(_frmTesteE2EDock);" in dock_lua
        assert (
            dock_lua.index("Firecast.registrarDataType(_frmTesteE2EDock);")
            < dock_lua.index("Firecast.registrarSpecialForm(_frmTesteE2EDock);")
        )

        assert "if self._onBeforeDestroy ~= nil then self:_onBeforeDestroy(); end;" in sheet_lua
        assert "registrarSpecialForm" not in sheet_lua, "sheetTemplate NÃO deve chamar registrarSpecialForm"

        dock_lua_path = os.path.join(sandbox_dir, "frmTesteE2EDock.lfm.lua")
        with open(dock_lua_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(dock_lua)
        dock_lua_escaped = dock_lua_path.replace("\\", "/")

        runtime_probe = f"""
local specialForms = {{}}
local activeListeners = {{}}
local allControls = {{}}
local nextHandle = 10
local nextListenerId = 1

local ctrlProto = {{}}
local ctrlMeta = {{ __index = ctrlProto }}
for _, mName in ipairs({{
    "setAlign", "setWidth", "setHeight", "setName", "setFormType",
    "setDataType", "setTitle", "setTheme", "setText"
}}) do
    ctrlProto[mName] = function(self, val) self._props[mName] = val end
end
function ctrlProto:beginUpdate() end
function ctrlProto:endUpdate() end
function ctrlProto:setParent(p) table.insert(p._children, self) end
function ctrlProto:setNodeObject(n) self._nodeObject = n end
function ctrlProto:setNodeDatabase(n) self:setNodeObject(n) end
function ctrlProto:addEventListener(evName, fn, ctx)
    local id = nextListenerId
    nextListenerId = nextListenerId + 1
    activeListeners[id] = {{ id = id, ctrl = self, evName = evName, fn = fn, ctx = ctx }}
    return id
end
function ctrlProto:destroy()
    assert(not self._destroyed)
    for _, ch in ipairs(self._children) do assert(ch._destroyed == true) end
    self._destroyed = true
end

_G._obj_newObject = function(tag)
    nextHandle = nextHandle + 1
    local h = nextHandle
    allControls[h] = setmetatable({{ handle = h, _tag = tag, _props = {{}}, _children = {{}}, _destroyed = false }}, ctrlMeta)
    return h
end
_G.GUI = {{ fromHandle = function(h) return assert(allControls[h]) end }}
_G._gui_assignInitialParentForForm = function(_) end
_G.Firecast = {{
    registrarForm = function(_) end,
    registrarDataType = function(_) end,
    registrarSpecialForm = function(spec) specialForms[spec.name] = spec end,
}}
package.preload["firecast.lua"] = function() return _G.Firecast end
package.preload["rrpgObjs.lua"] = function()
    return {{
        beginObjectsLoading = function() end,
        endObjectsLoading = function() end,
        removeEventListenerById = function(id)
            assert(activeListeners[id] ~= nil, "Listener inválido: " .. tostring(id))
            activeListeners[id] = nil
        end,
    }}
end
package.preload["rrpgGUI.lua"] = function() return _G.GUI end
package.preload["rrpgDialogs.lua"] = function() return {{ showMessage = function() end }} end
package.preload["rrpgLFM.lua"] = function() return true end
package.preload["ndb.lua"] = function() return {{}} end
package.preload["locale.lua"] = function() return true end
package.preload["utils.lua"] = function()
    return {{ tryFinally = function(t, f) local ok, e = pcall(t); f(); if not ok then error(e, 0) end end }}
end
package.preload["v20_loader.lua"] = function() return true end

local spec = dofile("{dock_lua_escaped}")
assert(specialForms["frmTesteE2EDock"] == spec, "tablesDock deve registrar via Firecast.registrarSpecialForm")
local inst = spec.new()
for _, rec in pairs(activeListeners) do
    rec.fn(rec.ctrl)
end
assert(inst._onShowFired == true and inst._onHideFired == true and inst._pingClicked == true)
assert(inst._beforeDestroyFired == nil)
inst:destroy()
assert(inst._beforeDestroyFired == true, "_onBeforeDestroy deve disparar em inst:destroy()")
assert(inst._destroyed == true)
local rem = 0
for _, _ in pairs(activeListeners) do rem = rem + 1 end
assert(rem == 0, "Todos os listeners (incluindo _e_form_event) devem ser removidos em destroy()")
"""
        run_lua_in_isolated_state(dll, runtime_probe, "@test_09_tablesdock_compiler_probe")
    finally:
        shutil.rmtree(sandbox_dir, ignore_errors=True)


def verify_rpk_forms_runtime_pf4(dll: ctypes.CDLL, rpk_path: str) -> None:
    """
    PF-4: Extrai Vampiro_V20_Suite.rpk para sandbox isolada, carrega v20_loader.lua e
    TODOS os 15 Sheets/frm*.lfm.lua dentro da lua54x64.dll (sem acesso ao workspace externo),
    instancia newfrmBrujah() .. newfrmMortal(), vincula mockSheet [TESTE_E2E] via :setNodeObject(),
    aciona todos os eventos compilados e executa :destroy() em ordem reversa provando 0 erros.
    """
    extract_dir = tempfile.mkdtemp(prefix="test_e2e_rpk_runtime_")
    try:
        with zipfile.ZipFile(rpk_path, "r") as zf:
            zf.extractall(extract_dir)

        rpk_dir_lua = extract_dir.replace("\\", "/")
        forms_lua = _lua_forms_table()
        lua_harness = f"""
local RPK_ROOT = "{rpk_dir_lua}"
local EXPECTED_FORMS = {forms_lua}

-- Bloqueia acesso acidental ao workspace fora do .rpk extraído
package.path = ""
package.cpath = ""

local vhdSearchPaths = {{ "" }}
local registeredForms = {{}}
local registeredDataTypes = {{}}
local registeredSpecialForms = {{}}
local createdObservers = {{}}
local runtimeIsMestre = false
local runtimeRoomNode = {{}}
local runtimeCharNode = {{
    nome = "[TESTE_E2E] Neófito RPK Dock",
    cla_id = "tremere",
    is_vampire = true,
    geracao_base = 12,
    sangue_atual = 9,
    fdv_perm = 6,
    fdv_temp = 6,
}}
local dialogLog = {{}}
local chatLog = {{}}
local allControls = {{}}
local createdHandles = {{}}
local destroyedHandles = {{}}
local activeListeners = {{}}
local nextHandle = 100
local nextListenerId = 1

-- Simula SDK mocks leves do Firecast SDK 3.7b
local ctrlProto = {{}}
local ctrlMeta = {{ __index = ctrlProto }}

local ALLOWED_SETTERS = {{
    "setAlign", "setWidth", "setHeight", "setLeft", "setTop",
    "setColor", "setStrokeColor", "setStrokeSize", "setXradius", "setYradius",
    "setMargins", "setPadding", "setText", "setFontColor", "setFontSize",
    "setHorzTextAlign", "setVertTextAlign", "setWordWrap", "setField", "setType",
    "setTransparent", "setTextPrompt", "setItems", "setValues", "setValue",
    "setTitle", "setSRC", "setStyle", "setOptimize", "setFields", "setDefaultValues",
    "setReadOnly", "setHitTest", "setCursor", "setHint", "setVisible", "setEnabled",
    "setName", "setFormType", "setDataType", "setTheme"
}}

for _, mName in ipairs(ALLOWED_SETTERS) do
    ctrlProto[mName] = function(self, val)
        self._props[mName] = val
    end
end

function ctrlProto:getTabIndex() return self._tabIdx or 0 end
function ctrlProto:setTabIndex(idx) self._tabIdx = idx end
function ctrlProto:beginUpdate() self._updating = true end
function ctrlProto:endUpdate() self._updating = false end

function ctrlProto:setParent(parentObj)
    assert(type(parentObj) == "table" and parentObj.handle ~= nil, "setParent exige objeto válido")
    self._parent = parentObj
    table.insert(parentObj._children, self)
end

function ctrlProto:addEventListener(evName, fn, ctx)
    assert(type(evName) == "string" and type(fn) == "function", "addEventListener inválido")
    local id = nextListenerId
    nextListenerId = nextListenerId + 1
    local rec = {{ id = id, ctrl = self, evName = evName, fn = fn, ctx = ctx }}
    activeListeners[id] = rec
    table.insert(self._listeners, rec)
    return id
end

-- Regra 1 SDK 3.7b: setNodeObject vive na metatable (ctrlProto), NÃO via rawset na instância!
function ctrlProto:setNodeObject(nodeObject)
    self._nodeObject = nodeObject
    if nodeObject ~= nil then
        -- Propaga defaultValues e dispara onChange dos <dataLink> filhos diretos do <form>
        for _, child in ipairs(self._children) do
            if child._tag == "dataLink" then
                local fields = child._props.setFields
                local defaults = child._props.setDefaultValues
                if type(fields) == "table" and type(defaults) == "table" then
                    for i, fName in ipairs(fields) do
                        if nodeObject[fName] == nil and defaults[i] ~= nil then
                            nodeObject[fName] = defaults[i]
                        end
                    end
                end
                for _, lRec in ipairs(child._listeners) do
                    if lRec.evName == "onChange" and activeListeners[lRec.id] ~= nil then
                        lRec.fn(child)
                    end
                end
            end
        end
    end
end

function ctrlProto:setNodeDatabase(nodeObject)
    self:setNodeObject(nodeObject)
end

function ctrlProto:destroy()
    assert(not self._destroyed, "Controle destruído em duplicidade: " .. tostring(self._props.setName or self._tag))
    for _, ch in ipairs(self._children) do
        assert(ch._destroyed == true,
            "Ordem reversa violada: filho " .. tostring(ch._props.setName or ch._tag) ..
            " ainda vivo ao destruir pai " .. tostring(self._props.setName or self._tag))
    end
    self._destroyed = true
    table.insert(destroyedHandles, self.handle)
end

_G._obj_newObject = function(tag)
    nextHandle = nextHandle + 1
    local h = nextHandle
    allControls[h] = {{
        handle = h,
        _tag = tag,
        _props = {{}},
        _children = {{}},
        _listeners = {{}},
        _destroyed = false,
        _tabIdx = 0,
    }}
    setmetatable(allControls[h], ctrlMeta)
    table.insert(createdHandles, h)
    return h
end

_G.GUI = {{
    fromHandle = function(h)
        local obj = allControls[h]
        assert(obj ~= nil, "GUI.fromHandle chamado para handle inexistente: " .. tostring(h))
        return obj
    end
}}
_G.gui = _G.GUI

_G._gui_assignInitialParentForForm = function(h)
    assert(allControls[h] ~= nil and allControls[h]._tag == "form", "Handle de form inválido")
end

_G.lfm_setPropAsString = function(ctrl, prop, val)
    assert(type(ctrl) == "table" and type(prop) == "string", "lfm_setPropAsString inválido")
    ctrl._props[prop] = tostring(val)
end

_G.showMessage = function(msg)
    table.insert(dialogLog, tostring(msg))
end

_G.Dialogs = {{ showMessage = _G.showMessage }}

_G.Firecast = {{
    registrarForm = function(spec)
        assert(type(spec) == "table" and spec.name ~= nil, "registrarForm inválido")
        registeredForms[spec.name] = spec
    end,
    registrarDataType = function(spec)
        assert(type(spec) == "table" and spec.dataType ~= nil, "registrarDataType inválido")
        registeredDataTypes[spec.dataType] = spec
    end,
    registrarSpecialForm = function(spec)
        assert(type(spec) == "table" and spec.name ~= nil, "registrarSpecialForm inválido")
        registeredSpecialForms[spec.name] = spec
    end,
    interpretarRolagem = function(expr)
        return {{
            expr = expr,
            ops = {{ {{ tipo = "dado", resultados = {{ 9, 8, 7 }} }} }},
            rolarLocalmente = function() end,
        }}
    end,
    getMesaDe = function(_)
        return {{
            meuJogador = {{ isMestre = runtimeIsMestre, login = "test_e2e_rpk_runner" }},
            biblioteca = {{
                filhos = {{
                    {{
                        codigoInterno = 501,
                        tipo = "personagem",
                        nome = "[TESTE_E2E] Neófito RPK Dock",
                        dataType = "br.com.v20.Tremere",
                        visivel = true,
                        visivelRecursivamente = true,
                        loadSheetNDB = function(_, cb) cb(runtimeCharNode) end,
                    }},
                }},
            }},
            abrirNDBDeMesa = function(_, _, cb, _)
                cb(runtimeRoomNode)
            end,
            activeChat = {{
                rolarDados = function(_, _, _, cb)
                    cb({{ ops = {{ {{ tipo = "dado", resultados = {{ 9, 8, 7 }} }} }} }})
                end,
                enviarMensagem = function(_, msg)
                    table.insert(chatLog, tostring(msg))
                end,
            }},
        }}
    end,
}}
_G.RRPG = _G.Firecast
_G.rrpg = _G.Firecast

_G.NDB = {{
    getChildNodes = function(_) return {{}} end,
    newObserver = function(nodeObj)
        local obs = {{ node = nodeObj, enabled = true, onChanged = nil }}
        table.insert(createdObservers, obs)
        return obs
    end,
}}

local mockRrpgObjs = {{
    beginObjectsLoading = function() end,
    endObjectsLoading = function() end,
    removeEventListenerById = function(id)
        assert(activeListeners[id] ~= nil, "Tentativa de remover listener inexistente/duplicado: " .. tostring(id))
        activeListeners[id] = nil
    end,
}}

local mockUtils = {{
    tryFinally = function(tryFn, finallyFn)
        local ok, err = pcall(tryFn)
        finallyFn()
        if not ok then error(err, 0) end
    end,
}}

local mockVhd = {{
    addSearchPath = function(p)
        table.insert(vhdSearchPaths, tostring(p))
    end,
}}

local sdkPreloads = {{
    ["firecast.lua"] = function() return _G.Firecast end,
    ["rrpgObjs.lua"] = function() return mockRrpgObjs end,
    ["rrpgGUI.lua"] = function() return _G.GUI end,
    ["rrpgDialogs.lua"] = function() return _G.Dialogs end,
    ["rrpgLFM.lua"] = function() return true end,
    ["ndb.lua"] = function() return _G.NDB end,
    ["locale.lua"] = function() return true end,
    ["utils.lua"] = function() return mockUtils end,
    ["vhd.lua"] = function() return mockVhd end,
}}

-- Simula fielmente o require VHD do Firecast: exige extensão .lua/.dlua nos arquivos do pacote,
-- forçando o v20_loader.lua / v20_shim.dlua a traduzir require("Core.v20_init") -> "/Core/v20_init.lua"!
local vhdLoaded = {{}}
_G.require = function(modName)
    if vhdLoaded[modName] ~= nil then
        return vhdLoaded[modName]
    end
    if sdkPreloads[modName] ~= nil then
        local res = sdkPreloads[modName]()
        vhdLoaded[modName] = (res == nil) and true or res
        return vhdLoaded[modName]
    end
    if type(modName) == "string" and (modName:match("%.lua$") or modName:match("%.dlua$")) then
        local rel = modName:gsub("^/+", "")
        local fullPath = RPK_ROOT .. "/" .. rel
        local f = io.open(fullPath, "rb")
        if f ~= nil then
            local src = f:read("*a")
            f:close()
            local chunk, loadErr = load(src, "@" .. rel)
            if not chunk then error(loadErr, 0) end
            local res = chunk()
            vhdLoaded[modName] = (res == nil) and true or res
            return vhdLoaded[modName]
        end
    end
    error("VHD module not found: " .. tostring(modName), 0)
end

-- 1. Carregar v20_loader.lua diretamente do pacote .rpk extraído
require("v20_loader.lua")
assert(_G.__v20_loader_ready == true, "v20_loader.lua deveria marcar __v20_loader_ready")
assert(type(_G.V20) == "table" and type(_G.V20Bridge) == "table", "V20 e V20Bridge devem estar carregados")
assert(type(_G.V20.ClanWeaknesses) == "table", "V20.ClanWeaknesses deve estar carregado")
assert(type(_G.V20.BloodMagicCatalog) == "table", "V20.BloodMagicCatalog deve estar carregado")
assert(type(_G.V20.BloodMagicEngine) == "table", "V20.BloodMagicEngine deve estar carregado")
assert(type(_G.V20.CombatManeuvers) == "table", "V20.CombatManeuvers deve estar carregado")
assert(type(_G.V20.CoterieTracker) == "table", "V20.CoterieTracker deve estar carregado")
assert(type(_G.V20CoterieDockBridge) == "table", "V20CoterieDockBridge deve estar carregado")
assert(#vhdSearchPaths >= 4, "vhd.addSearchPath deve registrar /Data, /Core, /Adapter")

-- 2. Carregar, instanciar, vincular [TESTE_E2E], exercitar eventos e destruir TODOS os 16 formulários
assert(#EXPECTED_FORMS == 16, "Devem existir exatamente 16 formulários configurados")
for _, fInfo in ipairs(EXPECTED_FORMS) do
    local spec = require(fInfo.lfmLua)
    assert(registeredForms[fInfo.formName] == spec, "Form não registrado: " .. fInfo.formName)
    assert(registeredDataTypes[fInfo.dataType] == spec, "DataType não registrado: " .. fInfo.dataType)
    if fInfo.formType == "tablesDock" then
        assert(registeredSpecialForms[fInfo.formName] == spec, "tablesDock deve registrar registrarSpecialForm: " .. fInfo.formName)
    else
        assert(registeredSpecialForms[fInfo.formName] == nil, "sheetTemplate NÃO deve registrar registrarSpecialForm: " .. fInfo.formName)
    end
    assert(spec.cacheMode == "none", "cacheMode deve ser 'none' em " .. fInfo.formName)

    local ctor = _G["new" .. fInfo.formName]
    assert(type(ctor) == "function", "Construtor global ausente: new" .. fInfo.formName)

    local inst = ctor()
    assert(inst ~= nil and inst._props.setName == fInfo.formName)
    assert(rawget(inst, "_oldSetNodeObjectFunction") == ctrlProto.setNodeObject,
        "Regra 1 SDK 3.7b deve preservar setNodeObject em " .. fInfo.formName)

    if fInfo.cid == "coterie_dock" then
        -- Testa ciclo completo OnShow -> observadores ativos -> OnHide -> 0 observadores -> OnShow -> destroy() -> 0 observadores!
        runtimeIsMestre = true
        createdObservers = {{}}
        local onShowFn, onHideFn = nil, nil
        for _, lRec in pairs(activeListeners) do
            if lRec.ctx == inst and lRec.ctrl == inst then
                if lRec.evName == "OnShow" then onShowFn = lRec.fn end
                if lRec.evName == "OnHide" then onHideFn = lRec.fn end
            end
        end
        assert(type(onShowFn) == "function" and type(onHideFn) == "function", "OnShow/OnHide devem estar compilados em frmV20CoterieDock")
        onShowFn(inst)
        local activeObsAfterShow = 0
        for _, obs in ipairs(createdObservers) do
            if obs.enabled then activeObsAfterShow = activeObsAfterShow + 1 end
        end
        assert(activeObsAfterShow >= 2, "OnShow do Narrador deve criar observers ativos p/ roomNode e charNode, obteve: " .. activeObsAfterShow)
        assert(inst.tabNarradorCoterie._props.setVisible == true)

        -- Aciona todos os botões onClick/onChange do Dock como Narrador
        local dockListenerIds = {{}}
        for id, lRec in pairs(activeListeners) do
            if lRec.ctx == inst and lRec.ctrl ~= inst then
                table.insert(dockListenerIds, id)
            end
        end
        table.sort(dockListenerIds)
        assert(#dockListenerIds >= 25, "Dock deve possuir controles interativos compilados, obteve: " .. #dockListenerIds)
        for _, id in ipairs(dockListenerIds) do
            local lRec = activeListeners[id]
            if lRec ~= nil then lRec.fn(lRec.ctrl) end
        end

        onHideFn(inst)
        for _, obs in ipairs(createdObservers) do
            assert(obs.enabled == false, "OnHide deve desativar 100% dos observers")
        end

        -- Reabre com OnShow e destrói direto (sem OnHide) para provar que _onBeforeDestroy limpa tudo
        onShowFn(inst)
        local activeBeforeDestroy = 0
        for _, obs in ipairs(createdObservers) do
            if obs.enabled then activeBeforeDestroy = activeBeforeDestroy + 1 end
        end
        assert(activeBeforeDestroy >= 2)
        runtimeIsMestre = false
        inst:destroy()
        assert(inst._destroyed == true)
        for _, obs in ipairs(createdObservers) do
            assert(obs.enabled == false, "destroy() deve desativar 100% dos observers via _onBeforeDestroy")
        end
    else
        if fInfo.cid ~= "mortal" then
        local vampSheet = {{
            nome = "[TESTE_E2E] Personagem RPK " .. fInfo.formName,
            geracao_base = 9,
            attr_forca = 4,
            attr_destreza = 4,
            hab_briga = 4,
            sangue_atual = 12,
            fdv_perm = 7,
            fdv_temp = 7,
        }}
        inst:setNodeObject(vampSheet)
        assert(inst.sheet == vampSheet)
        assert(vampSheet.cla_id == fInfo.cid, "cla_id incorreto em " .. fInfo.formName .. ": " .. tostring(vampSheet.cla_id))
        assert(vampSheet.geracao == 9 and vampSheet.sangue_max == 14 and vampSheet.sangue_por_turno == 2)
        assert(vampSheet.vitalidade_resumo == "Saudável")
        assert(inst.cmbModoFicha._props.setEnabled == false, "Controles do Narrador devem ficar desabilitados para não-Mestre")
        assert(inst.edtXpTotal._props.setReadOnly == true, "xp_total deve ficar readOnly para não-Mestre")
        assert(inst.edt_attr_forca._props.setReadOnly == false, "Em modo criacao, atributos ficam editáveis")

        if fInfo.cid == "nosferatu" then
            assert(tonumber(vampSheet.attr_aparencia) == 0, "Nosferatu deve ter Aparência 0")
            assert(inst.edt_attr_aparencia._props.setReadOnly == true, "Nosferatu deve bloquear edt_attr_aparencia")
        end

        local expectedBM = (fInfo.cid == "tremere" or fInfo.cid == "giovanni")
        assert(inst.tabMagiaSangue ~= nil, "tabMagiaSangue deve existir em " .. fInfo.formName)
        assert(inst.tabMagiaSangue._props.setVisible == expectedBM,
            "Visibilidade inicial de tabMagiaSangue incorreta em " .. fInfo.formName)
        if not expectedBM then
            vampSheet.bg_rituals = 1
            inst:setNodeObject(vampSheet)
            assert(inst.tabMagiaSangue._props.setVisible == true)
            inst.pgcPrincipal:setTabIndex(7)
            vampSheet.bg_rituals = 0
            inst:setNodeObject(vampSheet)
            assert(inst.tabMagiaSangue._props.setVisible == false)
            assert(inst.pgcPrincipal:getTabIndex() == 0)
        end

        vampSheet.modo_ficha = "jogo"
        inst:setNodeObject(vampSheet)
        assert(inst.edt_attr_forca._props.setReadOnly == true, "Em modo jogo, edt_attr_forca deve ficar readOnly")
        assert(inst.btnPlus_attr_forca._props.setEnabled == false, "Em modo jogo, btnPlus_attr_forca deve ficar desabilitado")
        vampSheet.modo_ficha = "criacao"
        inst:setNodeObject(vampSheet)
    else
        local mortalSheet = {{
            nome = "[TESTE_E2E] Padre Sullivan RPK",
            is_vampire = false,
            mortal_perfil = "padrao_643",
            mortal_sobrenatural_modo = "carnical",
        }}
        inst:setNodeObject(mortalSheet)
        assert(inst.sheet == mortalSheet)
        assert(mortalSheet.isGhoul == true and mortalSheet.sangue_max == 2 and mortalSheet.ghoulPotence == 1)
        assert(inst.pnlHeaderBlood._props.setVisible == true, "Modo carniçal deve exibir pnlHeaderBlood")
        assert(inst.pnlCarnical._props.setVisible == true, "Modo carniçal deve exibir pnlCarnical")
        assert(inst.pnlNumina._props.setVisible == false, "Modo carniçal deve ocultar pnlNumina")
        assert(inst.btnFrenesiCarnical._props.setVisible == true, "Modo carniçal deve exibir btnFrenesiCarnical")

        mortalSheet.mortal_sobrenatural_modo = "humano"
        inst:setNodeObject(mortalSheet)
        assert(inst.btnFrenesiCarnical._props.setVisible == false, "Modo humano deve ocultar btnFrenesiCarnical")

        mortalSheet.mortal_sobrenatural_modo = "numina"
        inst:setNodeObject(mortalSheet)
        assert(mortalSheet.hasNumina == true and mortalSheet.isGhoul == false)
        assert(inst.pnlHeaderBlood._props.setVisible == false)
        assert(inst.pnlCarnical._props.setVisible == false)
        assert(inst.pnlNumina._props.setVisible == true, "Modo numina deve exibir pnlNumina")
        assert(inst.btnFrenesiCarnical._props.setVisible == false, "Modo numina deve ocultar btnFrenesiCarnical")
    end

    -- Acionar TODOS os listeners onClick e onChange compilados no formulário
    local chatBefore = #chatLog
    local eventsFired = 0
    local listenerIds = {{}}
    for id, lRec in pairs(activeListeners) do
        if lRec.ctx == inst then
            table.insert(listenerIds, id)
        end
    end
    table.sort(listenerIds)
    for _, id in ipairs(listenerIds) do
        local lRec = activeListeners[id]
        if lRec ~= nil then
            lRec.fn(lRec.ctrl)
            eventsFired = eventsFired + 1
        end
    end
    assert(eventsFired > 100, "Deveria executar >100 eventos em " .. fInfo.formName .. ", executou: " .. tostring(eventsFired))
    assert(#chatLog > chatBefore, "Eventos de rolagem em " .. fInfo.formName .. " devem publicar diagnóstico V20 no chat")

        inst:destroy()
        assert(inst._destroyed == true, fInfo.formName .. " deve ser destruído completamente")
        assert(inst.barHeaderTop == nil and inst.pgcPrincipal == nil,
            "Controles filhos devem ser limpos para nil em " .. fInfo.formName .. ":destroy()")
    end
end

-- Todos os listeners dos 16 forms foram removidos em _releaseEvents()
local remainingListeners = 0
for _, _ in pairs(activeListeners) do remainingListeners = remainingListeners + 1 end
assert(remainingListeners == 0, "Nenhum listener deve sobrar ativo após destroy() dos 16 forms, restaram: " .. tostring(remainingListeners))
assert(#createdHandles == #destroyedHandles, "Todos os handles criados devem ser destruídos: " .. #createdHandles .. " vs " .. #destroyedHandles)
"""
        run_lua_in_isolated_state(dll, lua_harness, "@test_09_rpk_forms_runtime_16")
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)


def verify_rpk_vhd_sorted_autoboot_round1(dll: ctypes.CDLL, rpk_path: str) -> None:
    """
    Reproduz fielmente o auto-boot VHD do Firecast SDK 3.7b, que executa todos os arquivos .lua
    (exceto sdk/, *.lfm.lua e *.dlua) em ordem alfabética de caminho — executando
    Adapter/firecast_bridge.lua ANTES de Core/* e ANTES de v20_loader.lua — seguido da instanciação,
    binding [TESTE_E2E], disparo de todos os listeners e destruição reversa de TODOS os 15
    formulários (newfrmBrujah() .. newfrmMortal()).
    """
    extract_dir = tempfile.mkdtemp(prefix="test_e2e_rpk_autoboot_")
    try:
        with zipfile.ZipFile(rpk_path, "r") as zf:
            names = zf.namelist()
            zf.extractall(extract_dir)

        boot_entries = sorted(
            n
            for n in names
            if n.endswith(".lua") and not n.startswith("sdk/") and not n.endswith(".lfm.lua")
        )
        assert boot_entries[0] == "Adapter/coterie_dock_bridge.lua", (
            f"Adapter/coterie_dock_bridge.lua deve ser o 1º script no auto-boot alfabético, obteve: {boot_entries[0]}"
        )
        assert boot_entries[1] == "Adapter/firecast_bridge.lua", (
            f"Adapter/firecast_bridge.lua deve ser o 2º script no auto-boot alfabético, obteve: {boot_entries[1]}"
        )
        assert boot_entries[-1] == "v20_loader.lua", (
            f"v20_loader.lua deve ser o último script no auto-boot alfabético, obteve: {boot_entries[-1]}"
        )
        for req_boot in (
            "Core/blood_magic_engine.lua",
            "Core/clan_weaknesses.lua",
            "Core/combat_maneuvers.lua",
            "Core/coterie_tracker.lua",
            "Data/blood_magic_catalog.lua",
            "Data/combat_maneuvers_catalog.lua",
        ):
            assert req_boot in boot_entries, f"{req_boot} deve participar do auto-boot VHD"
        assert all(not n.endswith(".dlua") for n in boot_entries), (
            "Arquivos .dlua JAMAIS devem entrar no auto-boot do VHD"
        )

        rpk_dir_lua = extract_dir.replace("\\", "/")
        boot_lua_list = ", ".join(f'"{e}"' for e in boot_entries)
        forms_lua = _lua_forms_table()

        lua_autoboot = f"""
local RPK_ROOT = "{rpk_dir_lua}"
local BOOT_ENTRIES = {{ {boot_lua_list} }}
local EXPECTED_FORMS = {forms_lua}

package.path = ""
package.cpath = ""

local vhdSearchPaths = {{ "" }}
local vhdLoaded = {{}}
local registeredForms = {{}}
local registeredDataTypes = {{}}
local registeredSpecialForms = {{}}
local allControls = {{}}
local createdHandles = {{}}
local destroyedHandles = {{}}
local activeListeners = {{}}
local nextHandle = 500
local nextListenerId = 1

local ctrlProto = {{}}
local ctrlMeta = {{ __index = ctrlProto }}
local ALLOWED_SETTERS = {{
    "setAlign", "setWidth", "setHeight", "setLeft", "setTop",
    "setColor", "setStrokeColor", "setStrokeSize", "setXradius", "setYradius",
    "setMargins", "setPadding", "setText", "setFontColor", "setFontSize",
    "setHorzTextAlign", "setVertTextAlign", "setWordWrap", "setField", "setType",
    "setTransparent", "setTextPrompt", "setItems", "setValues", "setValue",
    "setTitle", "setSRC", "setStyle", "setOptimize", "setFields", "setDefaultValues",
    "setReadOnly", "setHitTest", "setCursor", "setHint", "setVisible", "setEnabled",
    "setName", "setFormType", "setDataType", "setTheme"
}}
for _, mName in ipairs(ALLOWED_SETTERS) do
    ctrlProto[mName] = function(self, val) self._props[mName] = val end
end
function ctrlProto:getTabIndex() return self._tabIdx or 0 end
function ctrlProto:setTabIndex(idx) self._tabIdx = idx end
function ctrlProto:beginUpdate() end
function ctrlProto:endUpdate() end
function ctrlProto:setParent(p) table.insert(p._children, self) end
function ctrlProto:addEventListener(evName, fn, ctx)
    local id = nextListenerId
    nextListenerId = nextListenerId + 1
    local rec = {{ id = id, ctrl = self, evName = evName, fn = fn, ctx = ctx }}
    activeListeners[id] = rec
    table.insert(self._listeners, rec)
    return id
end
function ctrlProto:setNodeObject(nodeObject)
    self._nodeObject = nodeObject
    if nodeObject ~= nil then
        for _, child in ipairs(self._children) do
            if child._tag == "dataLink" then
                local fields = child._props.setFields
                local defaults = child._props.setDefaultValues
                if type(fields) == "table" and type(defaults) == "table" then
                    for i, fName in ipairs(fields) do
                        if nodeObject[fName] == nil and defaults[i] ~= nil then
                            nodeObject[fName] = defaults[i]
                        end
                    end
                end
                for _, lRec in ipairs(child._listeners) do
                    if lRec.evName == "onChange" and activeListeners[lRec.id] ~= nil then
                        lRec.fn(child)
                    end
                end
            end
        end
    end
end
function ctrlProto:setNodeDatabase(nodeObject) self:setNodeObject(nodeObject) end
function ctrlProto:destroy()
    assert(not self._destroyed, "Controle destruído duas vezes")
    for _, ch in ipairs(self._children) do assert(ch._destroyed == true, "Ordem reversa violada") end
    self._destroyed = true
    table.insert(destroyedHandles, self.handle)
end

_G._obj_newObject = function(tag)
    nextHandle = nextHandle + 1
    local h = nextHandle
    allControls[h] = setmetatable(
        {{ handle = h, _tag = tag, _props = {{}}, _children = {{}}, _listeners = {{}}, _destroyed = false, _tabIdx = 0 }},
        ctrlMeta
    )
    table.insert(createdHandles, h)
    return h
end
_G.GUI = {{ fromHandle = function(h) return assert(allControls[h]) end }}
_G.gui = _G.GUI
_G._gui_assignInitialParentForForm = function(_) end
_G.lfm_setPropAsString = function(ctrl, prop, val) ctrl._props[prop] = tostring(val) end
_G.showMessage = function(_) end
_G.Dialogs = {{ showMessage = _G.showMessage }}
_G.Firecast = {{
    registrarForm = function(spec) registeredForms[spec.name] = spec end,
    registrarDataType = function(spec) registeredDataTypes[spec.dataType] = spec end,
    registrarSpecialForm = function(spec) registeredSpecialForms[spec.name] = spec end,
    interpretarRolagem = function(expr)
        return {{ expr = expr, ops = {{ {{ tipo = "dado", resultados = {{ 10, 8 }} }} }}, rolarLocalmente = function() end }}
    end,
    getMesaDe = function(_) return nil end,
}}
_G.RRPG = _G.Firecast
_G.rrpg = _G.Firecast
_G.NDB = {{ getChildNodes = function(_) return {{}} end }}

local mockRrpgObjs = {{
    beginObjectsLoading = function() end,
    endObjectsLoading = function() end,
    removeEventListenerById = function(id)
        assert(activeListeners[id] ~= nil, "Listener inexistente/duplicado: " .. tostring(id))
        activeListeners[id] = nil
    end,
}}
local mockUtils = {{
    tryFinally = function(tryFn, finallyFn)
        local ok, err = pcall(tryFn)
        finallyFn()
        if not ok then error(err, 0) end
    end,
}}
local mockVhd = {{
    addSearchPath = function(p) table.insert(vhdSearchPaths, tostring(p)) end,
}}
local sdkPreloads = {{
    ["firecast.lua"] = function() return _G.Firecast end,
    ["rrpgObjs.lua"] = function() return mockRrpgObjs end,
    ["rrpgGUI.lua"] = function() return _G.GUI end,
    ["rrpgDialogs.lua"] = function() return _G.Dialogs end,
    ["rrpgLFM.lua"] = function() return true end,
    ["ndb.lua"] = function() return _G.NDB end,
    ["locale.lua"] = function() return true end,
    ["utils.lua"] = function() return mockUtils end,
    ["vhd.lua"] = function() return mockVhd end,
}}

-- Mock VHD require: aceita APENAS .lua e .dlua (como o VHD real do Firecast SDK 3.7b)
_G.require = function(modName)
    if vhdLoaded[modName] ~= nil then
        return vhdLoaded[modName]
    end
    if sdkPreloads[modName] ~= nil then
        local res = sdkPreloads[modName]()
        vhdLoaded[modName] = (res == nil) and true or res
        return vhdLoaded[modName]
    end
    if type(modName) == "string" and (modName:match("%.lua$") or modName:match("%.dlua$")) then
        local rel = modName:gsub("^/+", "")
        local f = io.open(RPK_ROOT .. "/" .. rel, "rb")
        if f ~= nil then
            local src = f:read("*a")
            f:close()
            local chunk, loadErr = load(src, "@" .. rel)
            if not chunk then error(loadErr, 0) end
            local res = chunk()
            vhdLoaded[modName] = (res == nil) and true or res
            return vhdLoaded[modName]
        end
    end
    error("VHD module not found: " .. tostring(modName), 0)
end

-- Confirma que v20_shim.dlua NÃO foi auto-executado antes do boot
assert(vhdLoaded["v20_shim.dlua"] == nil and _G.__v20_loader_ready == nil)

-- Auto-boot estrito em ordem alfabética (Adapter/coterie_dock_bridge.lua é o #1!)
for idx, relEntry in ipairs(BOOT_ENTRIES) do
    assert(not relEntry:match("%.dlua$"), ".dlua proibido no auto-boot: " .. relEntry)
    local f = assert(io.open(RPK_ROOT .. "/" .. relEntry, "rb"), "Arquivo ausente: " .. relEntry)
    local src = f:read("*a")
    f:close()
    local chunk, loadErr = load(src, "@" .. relEntry)
    if not chunk then error(loadErr, 0) end
    chunk()
    if idx == 1 then
        -- Logo após Adapter/coterie_dock_bridge.lua (#1), v20_shim.dlua, V20, V20Bridge e V20CoterieDockBridge já devem estar carregados!
        assert(vhdLoaded["v20_shim.dlua"] ~= nil, "v20_shim.dlua deve ser carregado sob demanda via require no 1º script!")
        assert(_G.__v20_loader_ready == true, "__v20_loader_ready deve estar ativo já no 1º script do boot!")
        assert(type(_G.V20) == "table" and type(_G.V20Bridge) == "table" and type(_G.V20CoterieDockBridge) == "table")
        assert(type(_G.V20.ClanWeaknesses) == "table" and type(_G.V20.BloodMagicEngine) == "table")
        assert(type(_G.V20.CombatManeuvers) == "table" and type(_G.V20.CoterieTracker) == "table")
    end
end

-- Agora carrega, instancia, vincula [TESTE_E2E], dispara eventos e destrói em ordem reversa TODOS os 16 forms!
assert(#EXPECTED_FORMS == 16)
for _, fInfo in ipairs(EXPECTED_FORMS) do
    local spec = require(fInfo.lfmLua)
    assert(registeredForms[fInfo.formName] == spec and registeredDataTypes[fInfo.dataType] == spec)
    if fInfo.formType == "tablesDock" then
        assert(registeredSpecialForms[fInfo.formName] == spec)
    else
        assert(registeredSpecialForms[fInfo.formName] == nil)
    end
    local ctor = assert(_G["new" .. fInfo.formName], "Construtor ausente: new" .. fInfo.formName)
    local inst = ctor()
    if fInfo.cid == "coterie_dock" then
        local sd = {{ npc_init_nome = "[TESTE_E2E] NPC Boot", npc_init_mod = 3 }}
        inst:setNodeObject(sd)
    elseif fInfo.cid ~= "mortal" then
        local sb = {{ nome = "[TESTE_E2E] Boot " .. fInfo.formName, geracao_base = 12 }}
        inst:setNodeObject(sb)
        assert(sb.cla_id == fInfo.cid and sb.geracao == 12 and sb.sangue_max == 11)
    else
        local sm = {{ nome = "[TESTE_E2E] Boot Mortal", is_vampire = false, mortal_sobrenatural_modo = "carnical" }}
        inst:setNodeObject(sm)
        assert(sm.isGhoul == true and sm.sangue_max == 2)
    end

    local ids = {{}}
    for id, lRec in pairs(activeListeners) do
        if lRec.ctx == inst then table.insert(ids, id) end
    end
    table.sort(ids)
    if fInfo.cid == "coterie_dock" then
        assert(#ids >= 25, "Esperados >=25 listeners em " .. fInfo.formName)
    else
        assert(#ids > 100, "Esperados >100 listeners em " .. fInfo.formName)
    end
    for _, id in ipairs(ids) do
        local lRec = activeListeners[id]
        if lRec ~= nil then lRec.fn(lRec.ctrl) end
    end

    inst:destroy()
    assert(inst._destroyed == true)
end

local rem = 0
for _, _ in pairs(activeListeners) do rem = rem + 1 end
assert(rem == 0, "Listeners residuais após destroy dos 16 forms no auto-boot: " .. tostring(rem))
assert(#createdHandles == #destroyedHandles, "Handles vazados no auto-boot: " .. #createdHandles .. " vs " .. #destroyedHandles)
"""
        run_lua_in_isolated_state(dll, lua_autoboot, "@test_09_vhd_sorted_autoboot_16")
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)


def main() -> None:
    assert os.path.exists(BUILD_SCRIPT), f"Script compilador não encontrado: {BUILD_SCRIPT}"
    dll = setup_lua_dll()
    verify_tablesdock_compiler_enhancements(dll)

    tmp_out_dir = tempfile.mkdtemp(prefix="test_e2e_rpk_out_")
    try:
        subprocess.run([sys.executable, BUILD_SCRIPT, "--output-dir", tmp_out_dir], check=True)
        rpk_path = os.path.join(tmp_out_dir, "Vampiro_V20_Suite.rpk")
        rdk_path = os.path.join(tmp_out_dir, "Vampiro_V20_Suite.rdk")
        assert os.path.exists(rpk_path), "Vampiro_V20_Suite.rpk não foi gerado no --output-dir temporário"
        assert os.path.exists(rdk_path), "Vampiro_V20_Suite.rdk não foi gerado no --output-dir temporário"

        with open(rpk_path, "rb") as f1, open(rdk_path, "rb") as f2:
            assert hashlib.sha256(f1.read()).hexdigest() == hashlib.sha256(f2.read()).hexdigest(), (
                "Vampiro_V20_Suite.rdk deve ser cópia idêntica do .rpk"
            )

        expected_dt_ids = [s[2] for s in EXPECTED_ALL_FORMS]

        with zipfile.ZipFile(rpk_path, "r") as zf:
            names = set(zf.namelist())
            assert "module.xml" in names
            assert "v20_loader.lua" in names, "v20_loader.lua obrigatório na raiz do ZIP"
            assert "v20_shim.dlua" in names, "v20_shim.dlua obrigatório na raiz do ZIP"
            assert "_rdkCompiledLang.cln" in names, "_rdkCompiledLang.cln obrigatório na raiz do ZIP"
            assert "sdk/firecast.lua" in names and "sdk/rrpgGUI.lua" in names and "sdk/rrpgObjs.lua" in names, (
                "sdk/ obrigatório no ZIP"
            )
            assert "firecast.lua" not in names, "Arquivos do SDK não devem ficar soltos na raiz do ZIP"

            mod_xml = zf.read("module.xml").decode("utf-8")
            mod_root = ET.fromstring(mod_xml)
            assert mod_root.attrib.get("sdkVersion") == "3.7b"
            assert mod_root.attrib.get("sdkApiVersion") == "88"
            assert mod_root.attrib.get("sdkMinorApiVersion") == "2"
            assert mod_root.attrib.get("originalPluginFileName") == "Vampiro_V20_Suite.rpk"
            assert mod_root.findtext("id") == "br.com.v20.suite"

            dt_els = mod_root.findall("./dataTypes/dataType")
            asm_els = mod_root.findall("./assembledFeatures/dataTypes/dataType")
            dt_ids = [(el.text or "").strip() for el in dt_els]
            assembled_ids = [el.attrib.get("id") for el in asm_els]

            actual_version = mod_root.findtext("version")
            assert actual_version == EXPECTED_VERSION, (
                f"Versão esperada {EXPECTED_VERSION!r} em module.xml, obteve {actual_version!r} "
                f"(dataTypes empacotados: {len(dt_ids)}/16 -> {dt_ids})"
            )
            assert dt_ids == expected_dt_ids, f"Lista ./dataTypes/dataType inesperada ({len(dt_ids)}/16): {dt_ids}"
            assert assembled_ids == expected_dt_ids, (
                f"Lista ./assembledFeatures/dataTypes/dataType inesperada ({len(assembled_ids)}/16): {assembled_ids}"
            )

            for idx, (_, exp_lfm, exp_dt, exp_form, exp_title, exp_ftype) in enumerate(EXPECTED_ALL_FORMS):
                dt_node = dt_els[idx]
                asm_node = asm_els[idx]
                assert dt_node.attrib.get("name") == exp_form
                assert dt_node.attrib.get("lfmFile") == exp_lfm
                assert dt_node.attrib.get("title") == exp_title
                assert asm_node.attrib.get("id") == exp_dt
                assert asm_node.attrib.get("formType") == exp_ftype, (
                    f"formType inesperado para {exp_dt}: {asm_node.attrib.get('formType')} vs {exp_ftype}"
                )
                assert asm_node.attrib.get("lfmFile") == exp_lfm
                assert asm_node.attrib.get("formName") == exp_form
                asm_info = asm_node.find("info")
                assert asm_info is not None and asm_info.attrib.get("title") == exp_title

            info_el = mod_root.find("info")
            assert info_el is not None and info_el.attrib.get("lang") == "pt-BR"
            for meta_tag in ("name", "description", "author", "site", "contact"):
                info_val = (info_el.findtext(meta_tag) or "").strip()
                root_val = (mod_root.findtext(meta_tag) or "").strip()
                assert info_val and info_val == root_val, f"Tag <{meta_tag}> inconsistente no module.xml assemblado"

            # Garante presença de todas as 32 entradas de formulários (16 .lfm + 16 .lfm.lua)
            for _, exp_lfm, _, _, _, _ in EXPECTED_ALL_FORMS:
                assert exp_lfm in names, f"LFM ausente no .rpk: {exp_lfm}"
                assert f"{exp_lfm}.lua" in names, f"LFM compilado ausente no .rpk: {exp_lfm}.lua"

            # Garante presença explícita dos catálogos e motores Subprojeto 1 + Subprojeto 2 + Subprojeto 3
            for req_mod in (
                "Data/blood_magic_catalog.lua",
                "Data/combat_maneuvers_catalog.lua",
                "Core/clan_weaknesses.lua",
                "Core/blood_magic_engine.lua",
                "Core/combat_maneuvers.lua",
                "Core/coterie_tracker.lua",
                "Core/v20_init.lua",
                "Adapter/firecast_bridge.lua",
                "Adapter/coterie_dock_bridge.lua",
            ):
                assert req_mod in names, f"Módulo obrigatório ausente no .rpk: {req_mod}"

            for folder in ("Data", "Core", "Adapter"):
                for ws_file in sorted(glob.glob(os.path.join(ROOT, folder, "*.lua"))):
                    rel_mod = f"{folder}/{os.path.basename(ws_file)}"
                    assert rel_mod in names, f"Arquivo do workspace não empacotado no .rpk: {rel_mod}"

            sdk_concat = (
                zf.read("sdk/rrpgGUI.lua").decode("utf-8", errors="ignore")
                + "\n"
                + zf.read("sdk/rrpgObjs.lua").decode("utf-8", errors="ignore")
            )

            for _, exp_lfm, exp_dt, exp_form, _, exp_ftype in EXPECTED_ALL_FORMS:
                compiled_lfm = f"{exp_lfm}.lua"
                code = zf.read(compiled_lfm).decode("utf-8")
                assert 'require("v20_loader.lua");' in code
                assert 'rawset(obj, "_oldSetNodeObjectFunction", obj.setNodeObject);' in code
                assert 'rawget(obj, "setNodeObject")' not in code
                assert 'cacheMode = "none"' in code
                assert "if self._onBeforeDestroy ~= nil then self:_onBeforeDestroy(); end;" in code
                if exp_ftype == "tablesDock":
                    assert f"Firecast.registrarSpecialForm(_{exp_form});" in code, (
                        f"tablesDock {compiled_lfm} deve conter Firecast.registrarSpecialForm(_{exp_form});"
                    )
                else:
                    assert "registrarSpecialForm" not in code
                assert f'obj:setDataType("{exp_dt}");' in code
                assert f'obj:setName("{exp_form}");' in code

                methods = set(re.findall(r":(set[A-Za-z0-9_]+)\(", code))
                missing = [
                    m
                    for m in sorted(methods)
                    if m not in ("setNodeObject", "setNodeDatabase") and m not in sdk_concat
                ]
                assert not missing, f"Métodos inválidos em {compiled_lfm} frente a rrpgGUI+rrpgObjs: {missing}"

            # Valida sintaxe Lua 5.4 via lua54x64.dll para todos os scripts Lua e DLua empacotados no .rpk
            for entry in sorted(names):
                if entry.endswith((".lua", ".dlua")):
                    validate_lua_buffer(dll, zf.read(entry), f"@{entry}", allow_bom=entry.startswith("sdk/"))

            # Verifica prefixo require("v20_shim.dlua"); na linha 1 de todos os módulos Core/ e Adapter/
            assert 'require("v20_shim.dlua")' in zf.read("v20_loader.lua").decode("utf-8")
            for entry in sorted(names):
                if entry.startswith(("Core/", "Adapter/")) and entry.endswith(".lua"):
                    first_line = zf.read(entry).decode("utf-8").splitlines()[0]
                    assert first_line.startswith('require("v20_shim.dlua"); '), (
                        f'{entry} no .rpk deve iniciar com require("v20_shim.dlua"); na linha 1'
                    )

        # Inspeciona em modo somente-leitura os binários rastreados em dist/ (sem mutá-los!)
        dist_rpk = os.path.join(ROOT, "dist", "Vampiro_V20_Suite.rpk")
        dist_rdk = os.path.join(ROOT, "dist", "Vampiro_V20_Suite.rdk")
        assert os.path.exists(dist_rpk) and os.path.exists(dist_rdk), "Binários dist/Vampiro_V20_Suite.{rpk,rdk} ausentes"
        with open(dist_rpk, "rb") as df1, open(dist_rdk, "rb") as df2:
            assert hashlib.sha256(df1.read()).hexdigest() == hashlib.sha256(df2.read()).hexdigest(), (
                "dist/Vampiro_V20_Suite.rdk deve ser idêntico ao dist/Vampiro_V20_Suite.rpk"
            )
        with zipfile.ZipFile(dist_rpk, "r") as dzf:
            d_mod_root = ET.fromstring(dzf.read("module.xml").decode("utf-8"))
            assert d_mod_root.findtext("version") == EXPECTED_VERSION, (
                f"dist/Vampiro_V20_Suite.rpk desatualizado: versão {d_mod_root.findtext('version')!r} != {EXPECTED_VERSION!r}"
            )
            d_dt_ids = [(el.text or "").strip() for el in d_mod_root.findall("./dataTypes/dataType")]
            assert d_dt_ids == expected_dt_ids, f"dist/Vampiro_V20_Suite.rpk com dataTypes inesperados: {d_dt_ids}"

        verify_rpk_vhd_sorted_autoboot_round1(dll, rpk_path)
        verify_xml_escaping_pf4()
        verify_rpk_forms_runtime_pf4(dll, rpk_path)
    finally:
        shutil.rmtree(tmp_out_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
