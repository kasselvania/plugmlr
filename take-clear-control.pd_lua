-- Per-buffer Clear gate. The original live_buffer patch still owns fade and resize.
local C = pd.Class:new():register('take-clear-control')
function C:initialize(_, a)
    self.slot = math.tointeger(a[1])
    if not self.slot or self.slot < 1 or self.slot > 16 then return false end
    self.key = 'live_buffer_' .. self.slot
    self.inlets, self.outlets = 0, 1
    self.receivers, self.busy = {}, false
    return true
end
function C:postinitialize()
    local function bind(name, method)
        self.receivers[#self.receivers+1] = pd.Receive:new():register(self, name, method)
    end
    self.clock = pd.Clock:new():register(self, 'expired')
    bind(self.slot .. '_l_b_delete_buffer', 'request')
    bind(self.key .. '-view-info', 'info')
    bind(self.key .. '-clear-reply', 'info')
    bind(self.slot .. '_l_b_storage_busy', 'storage')
    bind('mlr-cancel-clear', 'cancel')
    bind('mlr-close-views', 'cancel')
    -- Keep the status bus valid even when this buffer is instantiated without UI.
    bind('mlr-clear-status', 'ignore')
end
function C:finalize()
    self.clock:destruct()
    for _, r in ipairs(self.receivers) do r:destruct() end
end
function C:ignore() end
function C:status(text) pd.send('mlr-clear-status', 'label', {'Live ' .. self.slot .. ': ' .. text}) end
function C:disarm() self.armed = false; self.clock:unset() end
function C:cancel()
    if self.armed then self:disarm(); self:status('discard cancelled') end
end
function C:expired() self:disarm(); self:status('discard expired - press Clear again') end
function C:info(_, a)
    if #a < 8 or a[1] ~= 'live' or a[2] ~= self.slot then return end
    local signature = table.concat(a, '|')
    if self.signature ~= signature then self:cancel() end
    self.signature, self.ready, self.state = signature, a[3] == 1, a[8]
end
function C:storage(_, a)
    self.busy = a[1] ~= 0
    if self.busy then self:cancel() end
end
function C:request(selector)
    if selector == 'cancel' then self:cancel(); return end
    if selector ~= 'bang' and selector ~= 'discard' then return end
    -- Synchronous readback. No destructive decision from a stale panel checkbox.
    pd.send(self.key .. '-view-get', 'info', {self.key .. '-clear-reply'})
    if not self.signature then self:status('state unavailable'); return end
    if self.busy or self.state == 'Recording' then
        self:disarm(); self:status('finish recording or storage changes first'); return
    end
    if selector == 'discard' then
        if not self.armed then self:status('press Clear before Discard'); return end
    elseif self.ready and self.state ~= 'Saved' then
        self.armed = true; self.clock:delay(5000)
        self:status('unsaved - Save WAV or Discard within 5s'); return
    end
    self:disarm()
    self:status(self.ready and 'clearing audio' or 'empty')
    self:outlet(1, 'bang', {})
end
