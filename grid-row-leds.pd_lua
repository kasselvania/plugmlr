-- Receive-only rendering. The Monome package still owns transport and LED cache.
local C = pd.Class:new():register('grid-row-leds')
local function finite(v)
    return type(v) == 'number' and v == v and math.abs(v) < math.huge
end
function C:initialize(_, args)
    self.inlets, self.outlets = 1, 1
    self.row = args[1]
    if not finite(self.row) or self.row % 1 ~= 0 or self.row < 0 or self.row > 7 then return false end
    self.state = {position=0, playing=0, paused=0, ready=0, switching=0,
                  first=0, last=0, ['loop-start']=0, ['loop-end']=0, connected=0}
    return true
end
function C:in_1(sel, a)
    if self.state[sel] == nil or #a ~= 1 or not finite(a[1]) then return end
    local before = self.state.connected
    self.state[sel] = a[1]
    local s = self.state
    if s.connected ~= 1 then self.last_frame = nil; return end
    if before ~= 1 then self.last_frame = nil end
    local usable = s.ready ~= 0 and s.switching == 0
    local start, finish, length = s['loop-start'], s['loop-end'], s.last-s.first
    local region = usable and length > 0 and start >= s.first and finish <= s.last
        and finish-start >= 1 and (start > s.first or finish < s.last)
    local column = -1
    if usable and s.playing ~= 0 and s.paused == 0 and s.position >= 0 and s.position <= 1 then
        column = math.min(15, math.floor(s.position*16))
    end
    local frame = {0, self.row}
    for x=0,15 do
        local overlap = math.min(finish,s.first+length*(x+1)/16)-math.max(start,s.first+length*x/16)
        frame[#frame+1] = x == column and 12 or (region and overlap > 0.5 and 4 or 0)
    end
    local signature = table.concat(frame, ',')
    if signature == self.last_frame then return end
    self.last_frame = signature
    self:outlet(1, '/monome/grid/led/level/row', frame)
end
