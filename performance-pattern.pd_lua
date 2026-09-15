-- Eight free-time performances, one active timeline/clock. Messages, never audio.
-- Controls: toggle [slot], clear [slot], stop. Slots are 1..8; omitted = selected.
-- Event inlet: cut/direction/speed/transport track value, or snapshot state
-- track direction speed. Outputs: track command values; slot status; snapshot bang.
local C=pd.Class:new():register('performance-pattern')
local SLOTS,MAX_EVENTS,MAX_MS,MIN_MS=8,4096,300000,10
local function integer(v,lo,hi)
    return type(v)=='number' and v==v and v%1==0 and v>=lo and v<=hi
end
local function valid(kind,v)
    return (kind=='cut' and integer(v,0,15)) or
        (kind=='direction' and integer(v,0,1)) or
        (kind=='speed' and integer(v,0,4)) or
        (kind=='transport' and integer(v,0,2))
end
local function empty() return {state='empty',events={},length=0,initial={},participants={}} end
function C:initialize()
    self.inlets,self.outlets=2,3
    self.slot,self.slots,self.epoch=1,{},0
    for i=1,SLOTS do self.slots[i]=empty() end
    return true
end
function C:postinitialize()
    self.clock=pd.Clock:new():register(self,'tick')
    for i=1,SLOTS do self:report(i) end
end
function C:finalize()
    if self.clock then self.clock:destruct() end
end
function C:cancel()
    self.clock:unset();self.epoch=self.epoch+1
end
function C:report(i)
    i=i or self.slot;local s=self.slots[i]
    self:outlet(2,'pattern',{i,s.state})
    self:outlet(2,'count',{i,#s.events})
    self:outlet(2,'length',{i,s.length/1000})
end
function C:record()
    self:cancel();local epoch=self.epoch
    local s=empty();self.slots[self.slot]=s
    self.origin=pd.systime();s.state='snapshot'
    self:outlet(3,'bang',{}) -- Synchronous read-only snapshot from player adapters.
    if self.epoch~=epoch then return end
    s.state='recording';self.clock:delay(MAX_MS);self:report()
end
function C:finish(play)
    self:cancel();local s=self.slots[self.slot]
    s.length=math.max(MIN_MS,pd.timesince(self.origin))
    s.state=#s.events>0 and 'stopped' or 'empty'
    if s.state=='empty' then s.length=0 end
    if play and s.state=='stopped' then self:start() else self:report() end
end
function C:start()
    local s=self.slots[self.slot]
    if #s.events==0 then return end
    self:cancel()
    s.state='playing';self.origin,self.index,self.cycle=pd.systime(),0,0
    self:report();self:tick()
end
function C:stop()
    if self.slots[self.slot].state=='recording' then self:finish(false)
    else
        self:cancel();local s=self.slots[self.slot]
        s.state=#s.events>0 and 'stopped' or 'empty';self:report()
    end
end
function C:in_1(sel,a)
    if sel=='stop' then if #a==0 then self:stop() end;return end
    if sel~='toggle' and sel~='clear' then return end
    if #a>1 or (#a==1 and not integer(a[1],1,SLOTS)) then return end
    local i=a[1] or self.slot
    if sel=='clear' then
        if i==self.slot then self:cancel() end
        self.slots[i]=empty();self:report(i)
    else
        -- Finish/store the outgoing recording before selecting the destination.
        if i~=self.slot then self:stop();self.slot=i end
        local state=self.slots[i].state
        if state=='empty' then self:record()
        elseif state=='recording' then self:finish(true)
        elseif state=='playing' then self:stop()
        elseif state=='stopped' then self:start() end
    end
end
function C:in_2(sel,a)
    local s=self.slots[self.slot]
    if sel=='state' then
        if s.state=='snapshot' and #a==3 and integer(a[1],1,6) and
            valid('direction',a[2]) and valid('speed',a[3]) then
            s.initial[a[1]]={a[2],a[3]}
        end
        return
    end
    if s.state~='recording' or #a~=2 or not integer(a[1],1,6) or not valid(sel,a[2]) then return end
    if not s.initial[a[1]] then self:outlet(2,'error',{'missing_track_snapshot',a[1]});return end
    s.participants[a[1]]=true
    s.events[#s.events+1]={pd.timesince(self.origin),a[1],sel,a[2]}
    self:report()
    if #s.events>=MAX_EVENTS then self:finish(false);self:outlet(2,'error',{'event_limit',self.slot}) end
end
function C:tick()
    local s=self.slots[self.slot];local epoch=self.epoch
    if s.state=='recording' then self:finish(false);self:outlet(2,'error',{'duration_limit',self.slot});return end
    if s.state~='playing' then return end
    local e=s.events[self.index]
    local due=self.cycle*s.length+(e and e[1] or 0)
    local wait=due-pd.timesince(self.origin)
    if wait>0.001 then self.clock:delay(wait);return end
    if self.index==0 then
        self.index=1
        for track=1,6 do
            if s.participants[track] then
                self:outlet(1,'list',{track,'restore',table.unpack(s.initial[track])})
                if self.epoch~=epoch then return end
            end
        end
    else
        self.index=self.index+1
        if self.index>#s.events then self.index=0;self.cycle=self.cycle+1 end
        self:outlet(1,'list',{e[2],e[3],e[4]})
    end
    if self.epoch~=epoch then return end
    e=s.events[self.index]
    self.clock:delay(math.max(0,self.cycle*s.length+(e and e[1] or 0)-pd.timesince(self.origin)))
end
