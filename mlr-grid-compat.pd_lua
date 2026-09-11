-- MLR's legacy message boundary only. No sockets, leases, timing or LED cache.
local C = pd.Class:new():register('mlr-grid-compat')
function C:initialize()
    self.inlets, self.outlets = 3, 3
    self.width, self.height = 0, 0
    return true
end
local function integer(v, lo, hi)
    return type(v) == 'number' and v == v and v % 1 == 0 and v >= lo and v <= hi
end
function C:reject(reason, selector)
    self:outlet(3, 'unsupported_or_invalid', {reason, selector})
end
function C:in_2(sel, a)
    if sel == 'key' and #a >= 3 then
        self:outlet(2, '/monome/grid/key', {a[1], a[2], a[3]})
    end
end
function C:in_3(sel, a)
    if sel == 'attached' then
        self.width, self.height = a[3], a[4]
        self:outlet(2, '/sys/size', {self.width, self.height})
    elseif sel == 'detached' then
        self.width, self.height = 0, 0
    end
end
function C:in_1(sel, a)
    -- One historical Clear message omits the leading slash.
    if sel:sub(1,1) ~= '/' then sel = '/' .. sel end
    local op = sel:match('^/monome/grid/led/(.+)$')
    if not op then return self:reject('not_a_grid_led_command', sel) end
    -- The old panel initializes intensity 15. The package owns level output;
    -- lower hardware-global intensity is deliberately not emulated or bypassed.
    if op == 'intensity' then
        if #a == 1 and a[1] == 15 then return end
        return self:reject('use_per_led_levels', sel)
    end
    if self.width == 0 then return self:reject('grid_not_attached', sel) end
    local level = op:sub(1,6) == 'level/'
    if level then op = op:sub(7) end
    local max = level and 15 or 255
    local function valid(v) return integer(v, 0, max) end
    local function brightness(v) return level and v or (v == 0 and 0 or 15) end
    local out = {}
    local function led(x,y,v)
        if not integer(x,0,self.width-1) or not integer(y,0,self.height-1) or not valid(v) then return false end
        out[#out+1] = {x,y,brightness(v)}; return true
    end
    if op == 'set' then
        if #a ~= 3 or not led(a[1],a[2],a[3]) then return self:reject('set_arguments',sel) end
    elseif op == 'all' then
        if #a ~= 1 or not valid(a[1]) then return self:reject('all_arguments',sel) end
        self:outlet(1,'all',{brightness(a[1])}); return
    elseif op == 'row' or op == 'col' then
        if #a < 3 or not integer(a[1],0,self.width-1) or not integer(a[2],0,self.height-1) then return self:reject('line_arguments',sel) end
        local n = (#a-2) * (level and 1 or 8)
        local limit = op == 'row' and self.width-a[1] or self.height-a[2]
        if n > limit then return self:reject('line_out_of_bounds',sel) end
        for i=3,#a do
            if not valid(a[i]) then return self:reject('line_value',sel) end
            for bit=0,(level and 0 or 7) do
                local offset = (i-3)*(level and 1 or 8)+bit
                local v = level and a[i] or (math.floor(a[i]/2^bit)%2)
                led(a[1]+(op=='row' and offset or 0), a[2]+(op=='col' and offset or 0), v)
            end
        end
    elseif op == 'map' then
        if #a ~= (level and 66 or 10) or not integer(a[1],0,self.width-8) or not integer(a[2],0,self.height-8) then return self:reject('map_arguments',sel) end
        for i=3,#a do if not valid(a[i]) then return self:reject('map_value',sel) end end
        for y=0,7 do for x=0,7 do
            local v = level and a[3+y*8+x] or (math.floor(a[3+y]/2^x)%2)
            led(a[1]+x,a[2]+y,v)
        end end
    else return self:reject('unknown_led_command',sel) end
    -- Validate the whole command before changing any LED.
    for _,v in ipairs(out) do self:outlet(1,'led',v) end
end
