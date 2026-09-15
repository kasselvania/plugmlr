-- Grid input only. Existing Pd players own transport, quantization and audio.
local C = pd.Class:new():register('grid-cut-keys')
local LOOP_HOLD_MS = 80 -- Continuous overlap; first release commits a qualified loop.
local function integer(v, lo, hi)
    return type(v)=='number' and v==v and v%1==0 and v>=lo and v<=hi
end
function C:initialize()
    self.inlets, self.outlets = 3, 8
    self.connected, self.alt, self.mod = false, false, false
    self.page, self.focus = 'cut', 1
    self.down, self.routes, self.held, self.pairs = {}, {}, {}, {}
    return true
end
function C:postinitialize()
    self.hold_clocks = {}
    for row=1,6 do
        local method='arm_loop_'..row
        self[method]=function(s)
            local p=s.pairs[row]
            if p and p.second and not p.done then p.armed=true end
        end
        -- Pd-Lua owns and destroys these clocks.
        self.hold_clocks[row]=pd.Clock:new():register(self,method)
    end
end
function C:clear_pair(row)
    self.hold_clocks[row]:unset()
    self.pairs[row]=nil
end
function C:clear_pairs()
    for row=1,6 do self:clear_pair(row) end
end
function C:cancel_gestures()
    self:clear_pairs()
    self.routes,self.held={},{}
    -- Physical downs survive navigation: old keys must come up before acting again.
end
function C:display(sel,value) self:outlet(4,sel,{value}) end
function C:in_2_float(v)
    local connected=v==1
    if connected==self.connected then return end
    self:cancel_gestures()
    self.connected,self.alt,self.mod,self.down=connected,false,false,{}
    self:display('page',self.page)
    self:display('focus',self.focus)
    self:display('alt',0);self:display('mod',0)
    self:display('connected',connected and 1 or 0)
end
function C:in_3_float(row)
    if integer(row,1,6) then self:clear_pair(row) end
end
function C:set_focus(row, cancel)
    if self.focus==row then return end
    if cancel then self:cancel_gestures() end
    self.focus=row
    self:outlet(3,'float',{row})
    self:display('focus',row)
end
function C:row_count(row)
    local n=0
    for x=0,15 do if self.held[row*16+x] then n=n+1 end end
    return n
end
function C:cut(x,row,z)
    local key=row*16+x
    if z==0 then
        self.held[key]=nil
        local p=self.pairs[row]
        if p and p.second and not p.done then
            p.done=true;self.hold_clocks[row]:unset()
            if p.armed then
                self:outlet(5,'list',{row,math.min(p.first,p.second),math.max(p.first,p.second)+1})
            end
        end
        if self:row_count(row)==0 then self:clear_pair(row) end
        return
    end
    self.held[key]=true
    if self.alt then self:outlet(2,'float',{row})
    elseif self.mod then
        self:clear_pair(row)
        self:outlet(5,'list',{row,x,x+1})
    else
        local count=self:row_count(row)
        if count==1 then
            self:clear_pair(row);self.pairs[row]={first=x}
        elseif count==2 and self.pairs[row] and not self.pairs[row].done then
            self.pairs[row].second=x;self.hold_clocks[row]:delay(LOOP_HOLD_MS)
        elseif count>2 then self:clear_pair(row) end
        self:outlet(1,'list',{x,row,z}) -- Every fresh ordinary key cuts immediately.
    end
end
function C:in_1_list(a)
    if not self.connected or #a~=3 then return end
    local x,y,z=a[1],a[2],a[3]
    if not integer(x,0,15) or not integer(y,0,7) or not integer(z,0,1) then return end
    local key=y*16+x
    if z==0 then
        if not self.down[key] then return end
        self.down[key]=nil
        local row=self.routes[key];self.routes[key]=nil
        if row then self:cut(x,row,0) end
        if y==0 and x==15 then self.alt=false;self:display('alt',0)
        elseif y==0 and x==13 then self.mod=false;self:display('mod',0) end
        return
    end
    if self.down[key] then return end
    self.down[key]=true
    if y==0 then
        if x==15 then self.alt=true;self:clear_pairs();self:display('alt',1)
        elseif x==13 then self.mod=true;self:clear_pairs();self:display('mod',1)
        elseif (x==0 or x==1) and not self.alt and not self.mod then
            local page=x==0 and 'play' or 'cut'
            if page~=self.page then
                self:cancel_gestures();self.page=page;self:display('page',page)
            end
            self:outlet(8,page,{self.focus}) -- Explicit page press also selects the screen.
        end
    elseif self.page=='cut' and y<=6 then
        -- Simultaneous CUT gestures on different rows remain independent.
        self:set_focus(y,false);self.routes[key]=y;self:cut(x,y,1)
    elseif self.page=='play' and y==7 then
        self.routes[key]=self.focus;self:cut(x,self.focus,1)
    elseif self.page=='play' and y<=6 and not self.alt and not self.mod then
        if x>=2 and x<=5 then self:set_focus(y,true)
        elseif x==7 then self:outlet(6,'float',{y})
        elseif x>=9 and x<=13 then self:outlet(7,'list',{y,x-9})
        elseif x==15 then self:outlet(2,'float',{y}) end
    end
end
function C:in_1(sel,a) if sel=='list' then self:in_1_list(a) end end
function C:in_2(sel,a)
    if (sel=='float' or sel=='list') and #a==1 then self:in_2_float(a[1]) end
end
function C:in_3(sel,a)
    if (sel=='float' or sel=='list') and #a==1 then self:in_3_float(a[1]) end
end
