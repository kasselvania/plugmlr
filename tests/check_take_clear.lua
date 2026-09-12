-- Behavioral control test only; not Pd/audio acceptance.
local buses, now, timers, cleared, labels = {}, 0, {}, 0, {}
pd = {Class={},Receive={},Clock={}}
function pd.Class:new() return self end
function pd.Class:register() return self end
function pd.Receive:new() return setmetatable({}, {__index=self}) end
function pd.Receive:register(owner,name,method)
    self.owner,self.name,self.method=owner,name,method
    buses[name]=buses[name] or {};table.insert(buses[name],self);return self
end
function pd.Receive:destruct() end
function pd.Clock:new() return setmetatable({}, {__index=self}) end
function pd.Clock:register(owner,method) self.owner,self.method=owner,method;timers[#timers+1]=self;return self end
function pd.Clock:delay(ms) self.deadline=now+ms end
function pd.Clock:unset() self.deadline=nil end
function pd.Clock:destruct() self:unset() end
function pd.send(name,selector,atoms)
    for _,r in ipairs(buses[name] or {}) do r.owner[r.method](r.owner,selector,atoms or {}) end
end
local state
pd.Receive:new():register({query=function(_,_,a)
    if state then pd.send(a[1],'info',state) end
end},'live_buffer_3-view-get','query')
pd.Receive:new():register({label=function(_,_,a) labels[#labels+1]=a[1] end},'mlr-clear-status','label')
dofile('take-clear-control.pd_lua')
local c=setmetatable({}, {__index=pd.Class});assert(c:initialize('',{3}));c.outlet=function() cleared=cleared+1 end;c:postinitialize()
local checks=0
local function request(s) pd.send('3_l_b_delete_buffer',s or 'bang',{}) end
local function expect(n,why) checks=checks+1;assert(cleared==n,why..': '..cleared) end
local function setstate(ready,status,first)
    state={'live',3,ready,48000,first or 0,14400,'Live 3',status}
    pd.send('live_buffer_3-view-info','info',state)
end
request();expect(0,'unknown state refuses')
setstate(0,'Empty');request();expect(1,'empty Clear passes')
setstate(1,'Unsaved');request('discard');expect(1,'unarmed Discard refuses')
request();request();expect(1,'repeated Clear cannot confirm')
request('discard');expect(2,'separate armed Discard passes once')
request('discard');expect(2,'duplicate Discard refuses')
for _,cancel in ipairs({'mlr-close-views','mlr-cancel-clear'}) do
    request();pd.send(cancel,'bang',{});request('discard');expect(2,cancel)
end
request();now=5001
for _,t in ipairs(timers) do if t.deadline and t.deadline<=now then t.deadline=nil;t.owner[t.method](t.owner) end end
request('discard');expect(2,'expiry refuses')
request();setstate(1,'Unsaved',64);request('discard');expect(2,'new content bounds cancel')
request();setstate(1,'Saved',64);request('discard');expect(2,'save completion cancels')
request();expect(3,'saved Clear passes')
setstate(1,'Unsaved');request();pd.send('3_l_b_storage_busy','float',{1});request('discard');request();expect(3,'busy blocks both')
pd.send('3_l_b_storage_busy','float',{0});request('discard');expect(3,'busy cancellation persists')
request();setstate(1,'Recording');request('discard');request();expect(3,'recording blocks both')
setstate(1,'Unsaved');request('discard');expect(3,'record completion does not rearm')
request();request('cancel');request('discard');expect(3,'explicit cancellation')
request();request('discard');expect(4,'fresh deliberate request succeeds')
c:finalize()
print(string.format('PASS: %d take-clear behavioral checks; native/audio acceptance separate',checks))
