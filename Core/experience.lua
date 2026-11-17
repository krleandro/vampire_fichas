local Experience = {}

local function safeNum(val, default)
    local n = tonumber(val)
    if n == nil or n ~= n or n == math.huge or n == -math.huge then
        return default
    end
    return n
end

local function safeNonNegInt(val, default)
    return math.max(0, math.floor(safeNum(val, default or 0)))
end

local VALID_TRAIT_KINDS = {
    attribute = true,
    ability = true,
    discipline = true,
    secondary_path = true,
    virtue = true,
    morality = true,
    willpower = true,
}

function Experience.calculateUpgradeCost(traitKind, currentRating, opts)
    opts = type(opts) == "table" and opts or {}
    local cur = safeNonNegInt(currentRating, 0)

    if traitKind == "attribute" then
        return cur * 4
    elseif traitKind == "ability" then
        return (cur == 0) and 3 or (cur * 2)
    elseif traitKind == "discipline" then
        if cur == 0 then return 10 end
        local cat = opts.costCategory or "fora_cla"
        if cat == "cla" then return cur * 5 end
        if cat == "caitiff" then return cur * 6 end
        return cur * 7
    elseif traitKind == "secondary_path" then
        return (cur == 0) and 7 or (cur * 4)
    elseif traitKind == "virtue" then
        return cur * 2
    elseif traitKind == "morality" then
        return cur * 2
    elseif traitKind == "willpower" then
        return math.max(1, cur)
    end
    return 0
end

function Experience.submitUpgrade(state, request, opts)
    opts = type(opts) == "table" and opts or {}
    local nextSt = {}
    if type(state) == "table" then
        for k, v in pairs(state) do
            nextSt[k] = v
        end
    end

    if type(request) ~= "table" or not VALID_TRAIT_KINDS[request.traitKind] then
        return {
            ok = false,
            newState = nextSt,
            auditEntry = nil,
            error = "Solicitação de evolução por XP inválida.",
        }
    end

    if nextSt.cla_id == "nosferatu" and request.field == "attr_aparencia" then
        return {
            ok = false,
            newState = nextSt,
            auditEntry = nil,
            error = "Nosferatu não pode aumentar Aparência acima de 0 (V20, p. 60).",
        }
    end

    local cur
    if request.currentRating ~= nil then
        cur = safeNonNegInt(request.currentRating, 0)
    elseif request.field then
        cur = safeNonNegInt(nextSt[request.field], 0)
    else
        cur = 0
    end

    local cost = Experience.calculateUpgradeCost(request.traitKind, cur, { costCategory = request.costCategory })
    local avail = safeNum(nextSt.xp_total, 0) - safeNum(nextSt.xp_gasto, 0)
    local hasOverride = (opts.storytellerOverride == true or opts.storytellerOverride == "true")

    if cost > avail and not hasOverride then
        return {
            ok = false,
            newState = nextSt,
            auditEntry = nil,
            error = string.format("XP insuficiente (custo %d, disponível %d).", cost, avail),
        }
    end

    local exigeAprovacao = (nextSt.xp_exige_aprovacao ~= false and nextSt.xp_exige_aprovacao ~= "false")
    local isMestre = (opts.isMestre == true or opts.isMestre == "true")
    local requiresApproval = exigeAprovacao and (not isMestre)

    local entry = {
        autor_login = request.author or "Jogador",
        tipo_evento = "evolucao_xp",
        descricao = request.label or request.field,
        custo_xp = cost,
        campo_alvo = request.field,
        novo_valor = cur + 1,
        status = requiresApproval and "pendente" or "aprovado",
    }

    if not requiresApproval then
        nextSt.xp_gasto = safeNum(nextSt.xp_gasto, 0) + cost
        if request.field then
            nextSt[request.field] = cur + 1
        end
    end

    return { ok = true, newState = nextSt, auditEntry = entry, error = nil }
end

function Experience.resolvePending(state, auditEntry, approve, masterLogin)
    local nextSt = {}
    if type(state) == "table" then
        for k, v in pairs(state) do
            nextSt[k] = v
        end
    end

    local updated = {}
    if type(auditEntry) == "table" then
        for k, v in pairs(auditEntry) do
            updated[k] = v
        end
    end

    if updated.status ~= "pendente" then
        return {
            ok = false,
            newState = nextSt,
            updatedEntry = updated,
            error = "Solicitação já foi processada.",
        }
    end

    local approved = (approve == true or approve == "true")
    if not approved then
        updated.aprovador_login = masterLogin or "Narrador"
        updated.status = "recusado"
        return { ok = true, newState = nextSt, updatedEntry = updated, error = nil }
    end

    local avail = safeNum(nextSt.xp_total, 0) - safeNum(nextSt.xp_gasto, 0)
    local cost = safeNonNegInt(updated.custo_xp, 0)
    if cost > avail then
        return {
            ok = false,
            newState = nextSt,
            updatedEntry = updated,
            error = "Saldo de XP tornou-se insuficiente antes da aprovação.",
        }
    end

    updated.aprovador_login = masterLogin or "Narrador"
    updated.status = "aprovado"
    nextSt.xp_gasto = safeNum(nextSt.xp_gasto, 0) + cost
    if updated.campo_alvo then
        nextSt[updated.campo_alvo] = safeNum(updated.novo_valor, 1)
    end
    return { ok = true, newState = nextSt, updatedEntry = updated, error = nil }
end

return Experience
