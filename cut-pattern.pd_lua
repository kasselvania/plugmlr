-- One reusable event pattern. No audio work and no device ownership.
-- inlet 1: toggle/stop/clear; inlet 2: committed track/cell.
-- outlet 1: timed track/cell; outlet 2: pattern state / length seconds / count / error.
local C=pd.Class:new():register('cut-pattern')
local MAX_EVENTS, MAX_MS, MIN_MS=4096,300000,10
local function integer(v,lo,hi)
    return type(v)=='number' and v==v and v%1==0 and v>=lo and v<=hi
end
function C:initialize()
    self.inlets,self.outlets=2,2
    self.state,self.events,self.length='empty',{},0
    return true
end
function C:postinitialize()
    self.clock=pd.Clock:new():register(self,'tick')
    self:report()
end
function C:report()
    self:outlet(2,'pattern',{self.state})
    self:outlet(2,'count',{#self.events})
    self:outlet(2,'length',{self.length/1000})
end
function C:finish(play)
    self.clock:unset()
    self.length=math.max(MIN_MS,pd.timesince(self.origin))
    self.state='stopped'
    if play then self:start() else self:report() end
end
function C:start()
    if #self.events==0 then return end
    self.clock:unset()
    self.state,self.origin,self.index,self.cycle='playing',pd.systime(),1,0
    self:report();self:tick()
end
function C:stop()
    self.clock:unset()
    if self.state=='recording' then self:finish(false)
    else self.state=#self.events>0 and 'stopped' or 'empty';self:report() end
end
function C:in_1(sel,a)
    if #a~=0 then return end
    if sel=='clear' then
        self.clock:unset();self.events,self.length,self.state={},0,'empty';self:report()
    elseif sel=='stop' then self:stop()
    elseif sel=='toggle' then
        if self.state=='empty' then self.state='armed';self:report()
        elseif self.state=='armed' then self:stop()
        elseif self.state=='recording' then self:finish(true)
        elseif self.state=='playing' then self:stop()
        elseif self.state=='stopped' then self:start() end
    end
end
function C:in_2_list(a)
    if #a~=2 or not integer(a[1],1,6) or not integer(a[2],0,15) then return end
    if self.state=='armed' then
        self.origin=pd.systime();self.state='recording';self.clock:delay(MAX_MS)
    elseif self.state~='recording' then return end
    self.events[#self.events+1]={pd.timesince(self.origin),a[1],a[2]}
    self:report()
    if #self.events>=MAX_EVENTS then
        self:finish(false);self:outlet(2,'error',{'event_limit'})
    end
end
function C:tick()
    if self.state=='recording' then
        self:finish(false);self:outlet(2,'error',{'duration_limit'});return
    end
    if self.state~='playing' then return end
    local e=self.events[self.index]
    local due=self.cycle*self.length+e[1]
    local wait=due-pd.timesince(self.origin)
    if wait>0.001 then self.clock:delay(wait);return end
    -- Advance before output: downstream Stop/Clear may synchronously cancel us.
    self.index=self.index+1
    if self.index>#self.events then self.index=1;self.cycle=self.cycle+1 end
    self:outlet(1,'list',{e[2],e[3]})
    if self.state~='playing' then return end
    e=self.events[self.index]
    self.clock:delay(math.max(0,self.cycle*self.length+e[1]-pd.timesince(self.origin)))
end
