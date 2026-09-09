local C = pd.Class:new():register('r1-head-control')
function C:initialize(_, a)
    self.inlets, self.outlets = 2, 1
    self.M = self:dofile('r1-common.lua')
    if #a ~= 4 then return false end
    self.scope, self.id, self.bid, self.private = self.M.id(a[1]), self.M.id(a[2]), self.M.id(a[3]), self.M.id(a[4])
    self.inst = self.M.instance(self.scope)
    if self.inst.heads[self.id] then self:error('duplicate head ID'); return false end
    self.inst.heads[self.id] = self
    self.d = {started = false, rate = 1, gain = 1, loop = 1, lo = 0, hi = 0}
    self.pos, self.slot, self.version, self.host = {0, 0}, 0, -1, 0
    self.rendered = 0
    return true
end
function C:finalize()
    if self.buffer then self.buffer.users[self.id] = nil end
    if self.inst and self.inst.heads[self.id] == self then self.inst.heads[self.id] = nil end
end
function C:send(suffix, sel, a) pd.send(self.private .. '-' .. suffix, sel, a or {}) end
function C:report(sel, a)
    local out = {self.scope, self.id, self.bid}
    for _, v in ipairs(a or {}) do out[#out+1] = v end
    self:outlet(1, sel, out)
end
function C:refresh()
    local b = self.inst.buffers[self.bid]
    if not b or b.frames == 0 then self:report('error', {'missing-buffer'}); return false end
    if b ~= self.buffer or b.version ~= self.version then
        self.buffer, self.version = b, b.version
        self.d.lo, self.d.hi, self.seek = 0, b.frames/b.sr, 0
        self.pos = {0,0}
        for slot = 0,1 do
            self:send('r'..slot..'-tables', 'list', b.names)
            self:send('r'..slot..'-frames', 'float', {b.frames})
            self:send('r'..slot..'-sr', 'float', {b.sr})
        end
    end
    return true
end
function C:status()
    self:send('snapshot', 'bang')
    local d = self.d
    self:report('state', {d.started and 1 or 0, self.pos[self.slot+1], d.rate,
        d.lo, d.hi, d.loop, d.gain, self.busy and 1 or 0, self.host})
end
function C:in_2(sel, a)
    if sel == 'pos0' or sel == 'pos1' then
        local slot = sel == 'pos0' and 1 or 2
        if self.M.finite(a[1]) then self.pos[slot] = a[1] end
    elseif sel == 'host' then
        self.host = a[1]
        self.rendered = self.rendered + 1
        if self.busy and self.rendered >= self.settleAt then self:settled() end
    elseif sel == 'tick' then
        self:send('snapshot', 'bang')
        if self.d.started and not self.busy and self.applied and self.applied.loop == 0 then
            local p, d = self.pos[self.slot+1], self.applied
            if (d.rate > 0 and p >= d.hi-1/self.buffer.sr) or
               (d.rate < 0 and p <= d.lo) then
                self.d.started = false
                self:apply()
                self:report('ended')
            end
        end
        self:status()
    end
end
function C:in_1(sel, a)
    local d, M = self.d, self.M
    local arity = {start=0, stop=0, seek=1, region=2, loop=1, rate=1, gain=1, status=0}
    if arity[sel] == nil or not M.args(a, arity[sel]) then
        return self:report('error', {'invalid-command', sel})
    end
    if sel == 'status' then return self:status() end
    -- Validate scalar ranges before metadata refresh or any desired-state change.
    if (sel == 'rate' and math.abs(a[1]) > 4) or
       (sel == 'gain' and (a[1] < 0 or a[1] > 1)) or
       (sel == 'loop' and a[1] ~= 0 and a[1] ~= 1) then
        return self:report('error', {'out-of-range', sel})
    end
    if sel == 'stop' then
        if not d.started then return end
        d.started = false
    else
        local b = self.inst.buffers[self.bid]
        if not b or b.frames == 0 then return self:report('error', {'missing-buffer'}) end
        local fresh = b ~= self.buffer or b.version ~= self.version
        local lo, hi = fresh and 0 or d.lo, fresh and b.frames/b.sr or d.hi
        if sel == 'region' and (a[1] < 0 or a[2] > b.frames/b.sr+1e-7 or math.floor((a[2]-a[1])*b.sr+0.5) < math.ceil(0.02*b.sr)) then
            return self:report('error', {'invalid-region'})
        elseif sel == 'seek' and (a[1] < lo or a[1] >= hi) then
            return self:report('error', {'invalid-position'})
        end
        if not self:refresh() then return end
        if sel == 'start' then
            if d.started then return end
            d.started = true
            self.buffer.users[self.id] = true
        elseif sel == 'region' then d.lo, d.hi = math.floor(a[1]*b.sr+0.5)/b.sr, math.min(math.floor(a[2]*b.sr+0.5), b.frames)/b.sr
        elseif sel == 'seek' then self.seek = a[1]
        elseif sel == 'gain' then
            d.gain = a[1]
            self:send('gain', 'list', {d.gain, 5})
            return
        else d[sel] = a[1] end
    end
    self.pending = true
    if not self.busy then self:apply() end
end
function C:apply()
    self.pending = false
    self:send('snapshot', 'bang')
    local d, b = self.d, self.buffer
    if not b then return end
    local p = self.seek or self.pos[self.slot+1]
    self.seek = nil
    if not d.started then
        p = math.min(d.hi, math.max(d.lo, p))
    elseif p < d.lo or p >= d.hi-0.5/b.sr or (d.rate < 0 and p <= d.lo+0.5/b.sr) then
        p = d.rate < 0 and d.hi-1/b.sr or d.lo
    end
    local nextslot = 1-self.slot
    local pre = 'r'..nextslot..'-'
    self:send(pre..'params', 'list', {d.rate, d.lo*b.sr, d.hi*b.sr, d.loop,
        d.started and 1 or 0})
    local frame = p*b.sr
    self:send(pre..'position', 'set', {math.floor(frame), frame-math.floor(frame)})
    self:send('mix', 'list', {nextslot, 5})
    self.slot, self.busy = nextslot, true
    self.applied = {started=d.started, rate=d.rate, loop=d.loop, lo=d.lo, hi=d.hi}
    -- [bang~] confirms rendered 64-frame blocks. Two extra blocks cover
    -- message delivery within a block; DSP-off cannot prematurely unlock storage.
    self.settleAt = self.rendered + math.ceil((self.host > 0 and self.host or 44100)*0.005/64) + 2
end
function C:settled()
    self.busy = false
    self:send('r'..(1-self.slot)..'-active', 'float', {0})
    if not self.d.started and not self.pending then self.buffer.users[self.id] = nil end
    if self.pending then self:apply() end
end
