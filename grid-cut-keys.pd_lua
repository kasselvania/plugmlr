-- CUT-page gestures only. Player transport and quantization remain in Pd.
local C = pd.Class:new():register('grid-cut-keys')
local LOOP_HOLD_MS = 40 -- Continuous two-key overlap before release may commit.
function C:initialize()
    self.inlets, self.outlets = 3, 5
    self.connected, self.alt, self.mod, self.focus = false, false, false, 0
    self.held, self.pairs = {}, {}
    return true
end
function C:postinitialize()
    self.hold_clocks = {}
    for row = 1, 6 do
        local method = 'arm_loop_' .. row
        self[method] = function(s)
            local pair = s.pairs[row]
            if pair and pair.second and not pair.done then pair.armed = true end
        end
        -- Pd-Lua owns these clocks and destroys them with this object.
        self.hold_clocks[row] = pd.Clock:new():register(self, method)
    end
end
function C:clear_pair(row)
    self.hold_clocks[row]:unset()
    self.pairs[row] = nil
end
function C:clear_pairs()
    for row = 1, 6 do self:clear_pair(row) end
end
local function integer(v, lo, hi)
    return type(v) == 'number' and v == v and v % 1 == 0 and v >= lo and v <= hi
end
function C:alt_led()
    self:outlet(4, '/monome/grid/led/level/set', {15, 0, self.alt and 15 or 4})
end
function C:mod_led()
    self:outlet(4, '/monome/grid/led/level/set', {13, 0, self.mod and 15 or 4})
end
function C:in_2_float(v)
    local connected = v == 1
    if connected == self.connected then return end
    self:clear_pairs()
    self.connected, self.alt, self.mod, self.held = connected, false, false, {}
    if connected then
        self:outlet(4, '/monome/grid/led/row', {0, 0, 0, 0})
        self:outlet(4, '/monome/grid/led/level/set', {1, 0, 8})
        self:alt_led()
        self:mod_led()
    end
end
function C:row_count(row)
    local n = 0
    for x = 0, 15 do if self.held[row*16+x] then n=n+1 end end
    return n
end
function C:in_3_float(row)
    if integer(row,1,6) then self:clear_pair(row) end
end
function C:in_1_list(a)
    if not self.connected or #a ~= 3 then return end
    local x, y, z = a[1], a[2], a[3]
    if not integer(x,0,15) or not integer(y,0,7) or not integer(z,0,1) then return end
    local key = y * 16 + x
    if z == 0 then
        local was_held = self.held[key]
        self.held[key] = nil
        local pair = self.pairs[y]
        if was_held and pair and pair.second and not pair.done then
            pair.done = true
            self.hold_clocks[y]:unset()
            if pair.armed then
                self:outlet(5, 'list', {y, math.min(pair.first,pair.second), math.max(pair.first,pair.second)+1})
            end
        end
        if y >= 1 and y <= 6 and self:row_count(y) == 0 then self:clear_pair(y) end
        if x == 15 and y == 0 and self.alt then
            self.alt = false
            self:alt_led()
        elseif x == 13 and y == 0 and self.mod then
            self.mod = false
            self:mod_led()
        end
        return
    end
    if self.held[key] then return end
    self.held[key] = true
    if x == 15 and y == 0 then
        self.alt = true
        self:clear_pairs()
        self:alt_led()
    elseif x == 13 and y == 0 then
        self.mod = true
        self:clear_pairs()
        self:mod_led()
    elseif y >= 1 and y <= 6 then
        if self.focus ~= y then
            self.focus = y
            self:outlet(3, 'float', {y})
        end
        if self.alt then
            self:outlet(2, 'float', {y})
        elseif self.mod then
            self:clear_pair(y)
            self:outlet(5, 'list', {y, x, x+1})
        else
            local count = self:row_count(y)
            if count == 1 then
                self:clear_pair(y)
                self.pairs[y] = {first=x}
            elseif count == 2 and self.pairs[y] and not self.pairs[y].done then
                self.pairs[y].second = x
                self.hold_clocks[y]:delay(LOOP_HOLD_MS)
            elseif count > 2 then
                self:clear_pair(y)
            end
            -- Overlapping finger patterns still cut on every fresh key-down.
            -- Pd owns cut quantization; release only adds an intentionally held loop.
            self:outlet(1, 'list', {x,y,z})
        end
    end
end
-- Pd route may present a one-element list instead of a float.
function C:in_2(sel, a)
    if (sel == 'float' or sel == 'list') and #a == 1 then
        self:in_2_float(a[1])
    end
end
function C:in_1(sel, a)
    if sel == 'list' then self:in_1_list(a) end
end

function C:in_3(sel,a)
    if (sel == 'float' or sel == 'list') and #a == 1 then self:in_3_float(a[1]) end
end
