-- CUT-page gestures only. Player transport and quantization remain in Pd.
local C = pd.Class:new():register('grid-cut-keys')
function C:initialize()
    self.inlets, self.outlets = 2, 4
    self.connected, self.alt, self.focus = false, false, 0
    self.held = {}
    return true
end
local function integer(v, lo, hi)
    return type(v) == 'number' and v == v and v % 1 == 0 and v >= lo and v <= hi
end
function C:alt_led()
    self:outlet(4, '/monome/grid/led/level/set', {15, 0, self.alt and 15 or 4})
end
function C:in_2_float(v)
    local connected = v == 1
    if connected == self.connected then return end
    self.connected, self.alt, self.held = connected, false, {}
    if connected then
        self:outlet(4, '/monome/grid/led/row', {0, 0, 0, 0})
        self:outlet(4, '/monome/grid/led/level/set', {1, 0, 8})
        self:alt_led()
    end
end
function C:in_1_list(a)
    if not self.connected or #a ~= 3 then return end
    local x, y, z = a[1], a[2], a[3]
    if not integer(x,0,15) or not integer(y,0,7) or not integer(z,0,1) then return end
    local key = y * 16 + x
    if z == 0 then
        self.held[key] = nil
        if x == 15 and y == 0 and self.alt then
            self.alt = false
            self:alt_led()
        end
        return
    end
    if self.held[key] then return end
    self.held[key] = true
    if x == 15 and y == 0 then
        self.alt = true
        self:alt_led()
    elseif y >= 1 and y <= 6 then
        if self.focus ~= y then
            self.focus = y
            self:outlet(3, 'float', {y})
        end
        if self.alt then
            self:outlet(2, 'float', {y})
        else
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
