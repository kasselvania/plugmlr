-- Free-time performance timeline. Pd logical clocks schedule messages, never audio.
-- Controls: toggle/stop/clear. Event inlet: cut/direction/speed/transport track value,
-- or state track direction speed (snapshot response, not an action).
-- Outputs: list track command values; status; snapshot request.
local C=pd.Class:new():register('performance-pattern')
local MAX_EVENTS,MAX_MS,MIN_MS=4096,300000,10
local function integer(v,lo,hi)
    return type(v)=='number' and v==v and v%1==0 and v>=lo and v<=hi
end
local function valid(kind,v)
    return (kind=='cut' and integer(v,0,15)) or
        (kind=='direction' and integer(v,0,1)) or
        (kind=='speed' and integer(v,0,4)) or
        (kind=='transport' and integer(v,0,2))
end
function C:initialize()
    self.inlets,self.outlets=2,3
    self.state,self.events,self.length='empty',{},0
    self.initial,self.participants={},{}
    return true
end
function C:postinitialize()
    self.clock=pd.Clock:new():register(self,'tick');self:report()
end
function C:finalize()
    if self.clock then self.clock:destruct() end
end
function C:report()
    self:outlet(2,'pattern',{self.state})
    self:outlet(2,'count',{#self.events})
    self:outlet(2,'length',{self.length/1000})
end
function C:record()
    self.clock:unset()
    self.events,self.initial,self.participants,self.length={},{},{},0
    self.origin=pd.systime();self.state='snapshot'
    self:outlet(3,'bang',{}) -- Synchronous read-only snapshot from the player adapters.
    self.state='recording';self.clock:delay(MAX_MS);self:report()
end
function C:finish(play)
    self.clock:unset();self.length=math.max(MIN_MS,pd.timesince(self.origin))
    self.state=#self.events>0 and 'stopped' or 'empty'
    if self.state=='empty' then self.length=0 end
    if play and self.state=='stopped' then self:start() else self:report() end
end
function C:start()
    if #self.events==0 then return end
    self.clock:unset()
    self.state,self.origin,self.index,self.cycle='playing',pd.systime(),0,0
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
        self.clock:unset();self.events,self.initial,self.participants,self.length,self.state={},{},{},0,'empty';self:report()
    elseif sel=='stop' then self:stop()
    elseif sel=='toggle' then
        if self.state=='empty' then self:record()
        elseif self.state=='recording' then self:finish(true)
        elseif self.state=='playing' then self:stop()
        elseif self.state=='stopped' then self:start() end
    end
end
function C:in_2(sel,a)
    if sel=='state' then
        if self.state=='snapshot' and #a==3 and integer(a[1],1,6) and
            valid('direction',a[2]) and valid('speed',a[3]) then
            self.initial[a[1]]={a[2],a[3]}
        end
        return
    end
    if self.state~='recording' or #a~=2 or not integer(a[1],1,6) or not valid(sel,a[2]) then return end
    if not self.initial[a[1]] then self:outlet(2,'error',{'missing_track_snapshot',a[1]});return end
    self.participants[a[1]]=true
    self.events[#self.events+1]={pd.timesince(self.origin),a[1],sel,a[2]}
    self:report()
    if #self.events>=MAX_EVENTS then self:finish(false);self:outlet(2,'error',{'event_limit'}) end
end
function C:tick()
    if self.state=='recording' then self:finish(false);self:outlet(2,'error',{'duration_limit'});return end
    if self.state~='playing' then return end
    local e=self.events[self.index]
    local due=self.cycle*self.length+(e and e[1] or 0)
    local wait=due-pd.timesince(self.origin)
    if wait>0.001 then self.clock:delay(wait);return end
    if self.index==0 then
        self.index=1
        for track=1,6 do
            if self.participants[track] then
                local a={track,'restore',table.unpack(self.initial[track])}
                self:outlet(1,'list',a)
                if self.state~='playing' then return end
            end
        end
    else
        self.index=self.index+1
        if self.index>#self.events then self.index=0;self.cycle=self.cycle+1 end
        self:outlet(1,'list',{e[2],e[3],e[4]})
    end
    if self.state~='playing' then return end
    e=self.events[self.index]
    self.clock:delay(math.max(0,self.cycle*self.length+(e and e[1] or 0)-pd.timesince(self.origin)))
end
