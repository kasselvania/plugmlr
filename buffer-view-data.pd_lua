-- One owner per existing stereo buffer. Cached display data, never an audio reader.
local C = pd.Class:new():register('buffer-view-data')
local N, CHUNK = 400, 1024
local function finite(x) return type(x)=='number' and x==x and math.abs(x)<math.huge end
function C:initialize(_,a)
    self.kind,self.slot=a[1],math.tointeger(a[2])
    if (self.kind~='sample' and self.kind~='live') or not finite(self.slot) then return false end
    self.key=self.kind..'_buffer_'..self.slot
    self.inlets,self.outlets=1,0
    self.ready,self.rate,self.first,self.last=0,0,0,0
    self.name,self.pending,self.status='Empty',nil,'Empty'
    self.waiters,self.receivers={},{}
    return true
end
function C:postinitialize()
    self.clock=pd.Clock:new():register(self,'step')
    local function bind(name,method) self.receivers[#self.receivers+1]=pd.Receive:new():register(self,name,method) end
    bind(self.kind=='sample' and 's_b_buffer_states' or 'l_b_buffer_states','metadata')
    bind(self.key..'-view-get','request')
    -- Pd-Lua reports unbound sends as errors. These buses always have an owner.
    bind(self.key..'-view-info','ignore')
    bind(self.key..'-view-changed','ignore')
    if self.kind=='live' then
        bind(self.slot..'_l_b_recording','recording')
        bind(self.key..'-view-saved','saved')
    end
end
function C:ignore() end
function C:finalize()
    self.clock:destruct()
    for _,r in ipairs(self.receivers) do r:destruct() end
end
function C:in_1_symbol(path) self.pending=path end
function C:saved(_,a)
    self.saved_path=a[1];self:publish()
end
function C:recording(_,a)
    self.busy=a[1]~=0
    self:invalidate()
    self:publish()
end
function C:metadata(_,a)
    if a[1]~=self.slot then return end
    local ready,rate,first,last
    if self.kind=='sample' then ready,rate,first,last=a[2],a[3],a[5],a[6]
    else ready,rate,first,last=a[6],a[2],a[3],a[4] end
    if not (finite(rate) and finite(first) and finite(last)) then return end
    rate=rate*1000
    ready=(ready~=0 and rate>0 and last>first and first>=0) and 1 or 0
    local changed=ready~=self.ready or rate~=self.rate or first~=self.first or last~=self.last
    self.ready,self.rate,self.first,self.last=ready,rate,first,last
    if self.kind=='sample' and ready==1 and self.pending then
        self.name=self.pending:match('([^/]+)$') or self.pending
        self.pending=nil; changed=true
    elseif self.kind=='live' then self.name='Live '..self.slot end
    if ready==0 then self.name=self.kind=='sample' and 'Empty' or self.name end
    if changed then self:invalidate() end
    self:publish()
end
function C:invalidate()
    self.saved_path=nil;self.clock:unset(); self.job=nil; self.peaks=nil; self.waiters={}
end
function C:info(reply)
    local status=self.busy and 'Recording' or (self.ready==1 and (self.kind=='sample' and 'Loaded' or (self.saved_path and 'Saved' or 'Unsaved')) or 'Empty')
    pd.send(reply,'info',{self.kind,self.slot,self.ready,self.rate,self.first,self.last,self.name,status})
end
function C:publish()
    self:info(self.key..'-view-info')
    pd.send(self.key..'-view-changed','bang',{})
end
function C:request(sel,a)
    if type(a[1])~='string' then return end
    if sel=='cancel' then
        self.waiters[a[1]]=nil
        if not next(self.waiters) and self.job then self.clock:unset();self.job=nil end
        return
    end
    self:info(a[1])
    if sel~='peaks' or self.ready~=1 or self.busy then return end
    if self.peaks then pd.send(a[1],'peaks',self.peaks); return end
    self.waiters[a[1]]=true
    if self.job then return end
    self.job={at=math.floor(self.first), first=math.floor(self.first), last=math.floor(self.last), values={}}
    for i=1,N do self.job.values[i]={math.huge,-math.huge,math.huge,-math.huge} end
    self.clock:delay(2)
end
function C:step()
    local j=self.job
    if not j then return end
    -- Table pointers are reacquired on every callback; never retained across resize.
    local l=pd.Table:new():sync('0-'..self.key)
    local r=pd.Table:new():sync('1-'..self.key)
    if not l or not r or l:length()<j.last or r:length()<j.last then
        self:invalidate(); self:error('Preview storage does not match content bounds'); return
    end
    local stop=math.min(j.last,j.at+CHUNK)
    for frame=j.at,stop-1 do
        local bin=math.min(N,math.floor((frame-j.first)*N/(j.last-j.first))+1)
        local v=j.values[bin]; local a,b=l:get(frame),r:get(frame)
        if finite(a) then v[1]=math.min(v[1],a);v[2]=math.max(v[2],a) end
        if finite(b) then v[3]=math.min(v[3],b);v[4]=math.max(v[4],b) end
    end
    j.at=stop
    if stop<j.last then self.clock:delay(2); return end
    local result={self.key,j.first,j.last}
    for _,v in ipairs(j.values) do for k=1,4 do result[#result+1]=finite(v[k]) and v[k] or 0 end end
    self.peaks,self.job=result,nil
    local waiters=self.waiters;self.waiters={}
    for reply in pairs(waiters) do pd.send(reply,'peaks',result) end
end
