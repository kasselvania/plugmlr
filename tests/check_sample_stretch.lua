-- Production bridge with synchronous Pd shim; never launches audio or a process.
local class, sent, receivers, launches={}, {}, {}, {}
local dispatching=false
pd={Class={},Receive={},Clock={}}
function pd.Class:new() return setmetatable({}, {__index=self}) end
function pd.Class:register(n) class[n]=self;return self end
function pd.Receive:new() return setmetatable({}, {__index=self}) end
function pd.Receive:register(o,n,m) self.name=n;receivers[n]={o,m};return self end
function pd.Receive:destruct() assert(not dispatching,'Receiver freed during message delivery');receivers[self.name]=nil end
function pd.Clock:new() return setmetatable({}, {__index=self}) end
function pd.Clock:register() return self end
function pd.Clock:delay() self.pending=true end
function pd.Clock:unset() self.pending=false end
function pd.Clock:destruct() end
local vacant,source=16,"/tmp/source with 'quote' $(literal).wav"
function pd.send(n,s,a)
 if n=='1-buffer-select' then assert(not dispatching,'Buffer handoff nested inside message delivery') end
 sent[#sent+1]={n,s,a}
 if s=='source' and n:match('view%-get$') then pd.send(a[1],'source',{source})
 elseif s=='vacant' and n:match('view%-get$') then local slot=tonumber(n:match('sample_buffer_(%d+)'));pd.send(a[1],'vacant',{slot*1.0,slot==vacant and 1 or 0})
 else local r=receivers[n];if r then local previous=dispatching;dispatching=true;r[1][r[2]](r[1],s,a);dispatching=previous end end
end
local original=os.execute
os.execute=function(command) launches[#launches+1]=command;return true end
dofile('sample-stretch.pd_lua')
local c=setmetatable({_loadpath='./'},{__index=class['sample-stretch']});assert(c:initialize('',{100,1,300}));c:postinitialize()
c:command('render',{});assert(#launches==0)
c:selection('list',{'sample_buffer_1',1,24000.0,72000.0,48000.0})
c:command('ratio',{0});assert(c.ratio==1)
c:command('pitch',{math.huge});assert(c.pitch==0)
c:command('render',{});assert(#launches==1 and launches[1]:find("'24000' '72000' '48000'",1,true))
assert(launches[1]:find("'\\''",1,true) and launches[1]:find('$(literal)',1,true))
local base=c.job;c:command('render',{});assert(#launches==1)
c:command('cancel',{});assert(c.job==nil and io.open(base..'.cancel'))
local f=assert(io.open('/tmp/editor-test-result.wav','w'));f:write('fixture');f:close()
c.result='/tmp/editor-test-result.wav';c.origin=1;c:command('load',{});assert(c.destination==16 and c.loaded)
-- While its copy loads, a manual selection wins over delayed adoption.
c:selection('list',{'sample_buffer_2',2,0,100,48000});local count=#sent;pd.send('16-sample-loaded','bang',{});assert(c.loaded);c:poll()
for i=count+1,#sent do assert(sent[i][1]~='1-buffer-select') end
c:command('load',{});assert(c.loaded);pd.send('16-sample-loaded','bang',{});pd.send('16-sample-loaded','bang',{});assert(c.loaded);local before_handoff=#sent;c:poll();assert(sent[#sent-1][1]=='1-buffer-select');assert(#sent==before_handoff+2)
vacant=nil;c:command('load',{});assert(not c.loaded)
vacant=15;c:command('load',{});for _=1,50 do c:poll() end;assert(not c.loaded)
c:finalize();os.execute=original
print('PASS: invalid input, integer argv, shell quoting, duplicate render, cancellation, occupied slots, deferred receiver teardown/adoption, duplicate completion, manual selection wins, load timeout')
