local VersionUpdater = {}

local function trim(s)
    if type(s) ~= "string" then return "" end
    return (s:gsub("^%s+", ""):gsub("%s+$", ""))
end

function VersionUpdater.parseVersionParts(verStr)
    local clean = trim(tostring(verStr or "")):gsub("^[vV]", "")
    if clean == "" then return {} end
    local parts = {}
    for numStr in clean:gmatch("(%d+)") do
        table.insert(parts, tonumber(numStr) or 0)
    end
    return parts
end

function VersionUpdater.isNewVersion(installedVer, availableVer)
    local cur = VersionUpdater.parseVersionParts(installedVer)
    local rem = VersionUpdater.parseVersionParts(availableVer)
    if #rem == 0 then return false end
    local maxLen = math.max(#cur, #rem)
    for i = 1, maxLen do
        local cVal = cur[i] or 0
        local rVal = rem[i] or 0
        if rVal > cVal then
            return true
        elseif rVal < cVal then
            return false
        end
    end
    return false
end

function VersionUpdater.parseManifestXml(xmlText)
    if type(xmlText) ~= "string" or xmlText == "" then
        return nil
    end
    local ver = xmlText:match("<version>%s*([^<%s]+)%s*</version>")
    if not ver or ver == "" then
        return nil
    end
    local modId = xmlText:match("<id>%s*([^<%s]+)%s*</id>")
    return {
        id = modId and trim(modId) or nil,
        version = trim(ver),
    }
end

return VersionUpdater
