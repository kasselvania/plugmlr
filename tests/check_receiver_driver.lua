-- Actual observer+driver subscriptions, with native-style multireceiver dispatch.
local classes,bindings={},{}
pd={Class={},Receive={},Clock={}}
function pd.Class:new()return setmetatable({}, {__index=self})end
function pd.Class:register(n)classes[n]=self;return self end
function pd.Receive:new()return setmetatable({}, {__index=self})end
function pd.Receive:register(o,n,m)bindings[n]=bindings[n]or {};table.insert(bindings[n],{o,m});return self end
function pd.Receive:destruct()end
function pd.Clock:new()return setmetatable({}, {__index=self})end
function pd.Clock:register()return self end
function pd.Clock:delay()end
function pd.Clock:unset()end
function pd.Clock:destruct()end
local depth=0
function pd.send(n,sel,a)
 depth=depth+1;assert(depth<10,'Recursive observation delivery')
 for _,r in ipairs(assert(bindings[n],'Unbound '..n))do r[1][r[2]](r[1],sel,a)end
 depth=depth-1
end
dofile('tests/receiver_lifetime/observer.pd_lua');dofile('tests/receiver_lifetime/driver.pd_lua');dofile('buffer-view-data.pd_lua')
local observer=setmetatable({},{__index=classes['rr-observer']});observer:initialize('',{1})
local logs={};observer.log=function(_,kind)logs[kind]=(logs[kind]or 0)+1 end;observer:postinitialize()
local driver=setmetatable({},{__index=classes['rr-driver']});driver:initialize('',{5,'lifecycle'});driver:postinitialize()
local owner=setmetatable({},{__index=classes['buffer-view-data']});owner:initialize('',{'sample',16.0});owner:postinitialize()
owner.ready,owner.rate,owner.first,owner.last,owner.name=1,48000,0,36000,'render.wav';owner.source_path='/tmp/render.wav';owner.tempo_bpm,owner.tempo_authority=120,'rendered'
pd.send('rr-track','list',{1.0,'sample_buffer_16'})
pd.send('16-sample-loaded','bang',{})
pd.send('rr-event','callback-return',{1.0,16.0,1.0,1.0})
pd.send('rr-event','deferred-return',{1.0,16.0,0.0,0.0})
assert(driver.actual=='sample_buffer_16','Missing committed-track delivery')
assert(driver.bounds and driver.output=='/tmp/render.wav','Missing owner readback')
assert(driver.loaded_count==1 and driver.callbacks==1 and driver.done and driver.cancelled==0)
for _,k in ipairs({'track','loaded','info','source','tempo','callback-return','deferred-return'})do assert(logs[k]==1,'Duplicate/missing log '..k)end
print('PASS: actual observer->driver delivery, owner query roundtrip, no recursion or double logging')
