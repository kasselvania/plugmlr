-- Control-only shared ownership. DSP lives in the .pd abstractions.
_G.plugmlr_r1 = _G.plugmlr_r1 or {instances = {}}
local M = _G.plugmlr_r1
function M.id(x)
    return type(x) == 'number' and string.format('%.9g', x) or tostring(x)
end
function M.finite(x)
    return type(x) == 'number' and x == x and math.abs(x) < math.huge
end
function M.instance(id)
    id = tostring(id)
    M.instances[id] = M.instances[id] or {buffers = {}, heads = {}}
    return M.instances[id]
end
function M.args(a, n)
    if #a ~= n then return false end
    for _, v in ipairs(a) do if not M.finite(v) then return false end end
    return true
end
return M
