-- Adapter for original player controls. Args: internal player ID, musical track.
-- Inlet 1 observes accepted cuts; inlet 2 receives typed replay commands.
-- Outlet 1 clears the original quantizer; outlet 2 publishes events/snapshots.
local C=pd.Class:new():register('performance-player')
local function integer(v,lo,hi)
    return type(v)=='number' and v==v and v%1==0 and v>=lo and v<=hi
end
function C:initialize(_,a)
    self.inlets,self.outlets=2,2
    self.id,self.track=string.format('%g',a[1]),a[2]
    self.direction,self.speed,self.playing,self.paused=0,2,0,0
    self.ready,self.switching=0,0
    self.receivers={}
    return true
end
function C:bind(symbol,method)
    self.receivers[#self.receivers+1]=pd.Receive:new():register(self,symbol,method)
end
function C:postinitialize()
    for _,field in ipairs({'is_playing_flag','is_paused_flag','buffer-ready','buffer-switching'}) do
        local name=({is_playing_flag='playing',is_paused_flag='paused',['buffer-ready']='ready',['buffer-switching']='switching'})[field]
        local method='read_'..name
        self[method]=function(s,sel,a) if sel=='float' and #a==1 then s[name]=a[1] end end
        self:bind(self.id..'-'..field,method)
    end
    self:bind(self.id..'-playback_direction','read_direction')
    self:bind(self.id..'-playback_speed_dial','read_speed')
    self:bind(self.id..'-pattern-transport','read_transport')
    self:bind('mlr-pattern-snapshot','snapshot')
end
function C:finalize()
    for _,r in ipairs(self.receivers) do r:destruct() end
end
function C:event(kind,v) self:outlet(2,kind,{self.track,v}) end
function C:read_direction(sel,a)
    if sel=='float' and #a==1 and integer(a[1],0,1) then
        local changed=self.direction~=a[1];self.direction=a[1]
        if changed then self:event('direction',a[1]) end
    end
end
function C:read_speed(sel,a)
    if sel=='float' and #a==1 and integer(a[1],0,4) then
        local changed=self.speed~=a[1];self.speed=a[1]
        if changed then self:event('speed',a[1]) end
    end
end
function C:read_transport(sel,a)
    if sel=='float' and #a==1 and integer(a[1],0,2) then self:event('transport',a[1]) end
end
function C:snapshot(sel)
    if sel=='bang' then self:outlet(2,'state',{self.track,self.direction,self.speed}) end
end
function C:in_1_float(v) if integer(v,0,15) then self:event('cut',v) end end
function C:send(name,sel,a) pd.send(self.id..'-'..name,sel,a or {}) end
function C:set_direction(v)
    if self.direction~=v then self:send('dir_change','bang') end
end
function C:set_speed(v)
    if self.speed~=v then self:send('playback_speed_dial','float',{v}) end
end
function C:transport(v)
    if v==0 then self:send('stop_button','bang')
    elseif self.ready~=0 and self.switching==0 then
        if v==1 and (self.playing==0 or self.paused~=0) then self:send('play_button','bang')
        elseif v==2 and self.playing~=0 and self.paused==0 then self:send('play_button','bang') end
    end
end
function C:in_2(sel,a)
    if sel=='restore' then
        if #a~=2 or not integer(a[1],0,1) or not integer(a[2],0,4) then return end
        -- Parameter restoration only: no seek or transport command here.
        self:set_speed(a[2]);self:set_direction(a[1])
    elseif #a==1 then
        local v=a[1]
        if sel=='cut' and integer(v,0,15) then
            self:outlet(1,'bang',{});self:send('selected_slice','float',{v})
        elseif sel=='direction' and integer(v,0,1) then self:set_direction(v)
        elseif sel=='speed' and integer(v,0,4) then self:set_speed(v)
        elseif sel=='transport' and integer(v,0,2) then self:transport(v) end
    end
end
