local C = pd.Class:new():register('r1-buffer-control')
function C:initialize(_, a)
    self.inlets, self.outlets = 2, 2
    self.M = self:dofile('r1-common.lua')
    if #a ~= 3 then return false end
    self.scope, self.id, self.private = self.M.id(a[1]), self.M.id(a[2]), self.M.id(a[3])
    self.inst = self.M.instance(self.scope)
    if self.inst.buffers[self.id] then self:error('duplicate buffer ID'); return false end
    self.buffer = {users = {}, version = 0, frames = 0, sr = 0}
    self.inst.buffers[self.id] = self.buffer
    self.bank = 0
    return true
end
function C:finalize()
    if self.inst and self.inst.buffers[self.id] == self.buffer then
        self.inst.buffers[self.id] = nil
    end
end
function C:report(sel, a)
    local out = {self.scope, self.id}
    for _, x in ipairs(a or {}) do out[#out+1] = x end
    self:outlet(2, sel, out)
end
function C:in_1(sel, a)
    if sel == 'status' and #a == 0 then
        self:report('buffer', {self.buffer.frames, self.buffer.sr, self.buffer.version,
            next(self.buffer.users) and 1 or 0})
    elseif sel == 'load' and #a == 1 and type(a[1]) == 'string' then
        if next(self.buffer.users) then return self:report('error', {'buffer-in-use'}) end
        self.pending, self.meta = true, nil
        local prefix = self.private .. '-bank' .. (1-self.bank)
        self.names = {prefix .. '-L', prefix .. '-R'}
        self:outlet(1, 'read', {'-resize', '-maxsize', 8388608, a[1], self.names[1], self.names[2]})
    else self:report('error', {'invalid-buffer-command', sel}) end
end
function C:in_2(sel, a)
    if not self.pending then return end
    if sel == 'meta' then self.meta = a; return end
    if sel ~= 'float' then return end
    self.pending = false
    local n, m = a[1], self.meta
    if not m or not self.M.finite(n) or n < 4 or n >= 8388608 or
       not self.M.finite(m[1]) or m[1] < 8000 or m[1] > 384000 or
       m[3] ~= 2 or n / m[1] < 0.02 then
        return self:report('error', {'invalid-stereo-file'})
    end
    -- File loading is synchronous and permitted only without started readers.
    -- Validate both staging tables before making their names visible to heads.
    for _, name in ipairs(self.names) do
        local t = pd.Table:new():sync(name)
        if not t or t:length() ~= n then return self:report('error', {'invalid-table'}) end
        for i = 0, n-1 do
            if not self.M.finite(t:get(i)) then return self:report('error', {'nonfinite-file'}) end
        end
    end
    self.bank = 1-self.bank
    local b = self.buffer
    b.frames, b.sr, b.names, b.version = n, m[1], self.names, b.version+1
    self:report('loaded', {n, m[1], n/m[1], b.version})
end
