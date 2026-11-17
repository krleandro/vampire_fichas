-- v20_loader.lua (executado automaticamente no boot do plugin e requerido pelos .lfm.lua)
if not _G.__v20_loader_ready then
    _G.__v20_loader_ready = true
    local okVhd, vhdMod = pcall(require, "vhd.lua")
    if okVhd and vhdMod and vhdMod.addSearchPath then
        pcall(vhdMod.addSearchPath, "/Data")
        pcall(vhdMod.addSearchPath, "/Core")
        pcall(vhdMod.addSearchPath, "/Adapter")
    end
    local origRequire = require
    _G.require = function(modName)
        local ok, res = pcall(origRequire, modName)
        if ok then return res end
        if type(modName) == "string" and not modName:match("%.lua$") and not modName:match("%.dlua$") then
            local slashPath = "/" .. modName:gsub("%.", "/") .. ".lua"
            local ok2, res2 = pcall(origRequire, slashPath)
            if ok2 then return res2 end
            local relPath = modName:gsub("%.", "/") .. ".lua"
            local ok3, res3 = pcall(origRequire, relPath)
            if ok3 then return res3 end
        end
        error(res)
    end
end
require("Core.v20_init")
require("Adapter.firecast_bridge")
