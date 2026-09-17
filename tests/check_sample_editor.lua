-- Execute production control/cache classes against a small Pd message/clock shim.
-- This checks edge cases; native rendering and audio are separate evidence.
local classes,receivers,sent={}, {}, {}
pd={Class={},Receive={},Clock={},Table={}}
function pd.Class:new() return setmetatable({}, {__index=self}) end
function pd.Class:register(n) classes[n]=self;return self end
function pd.Class:set_size() end
function pd.Class:repaint() end
function pd.Class:destruct() self:finalize() end
function pd.Receive:new() return setmetatable({}, {__index=self}) end
function pd.Receive:register(owner,n,m) self.name=n;receivers[n]={owner,m};return self end
function pd.Receive:destruct() receivers[self.name]=nil end
function pd.Clock:new() return setmetatable({}, {__index=self}) end
function pd.Clock:register(o,m) self.owner,self.method=o,m;return self end
function pd.Clock:delay() self.pending=true end
function pd.Clock:unset() self.pending=false end
function pd.Clock:destruct() self:unset() end
function pd.Clock:fire() if self.pending then self.pending=false;self.owner[self.method](self.owner) end end
function pd.send(n,s,a)
 sent[#sent+1]={n,s,a};local r=receivers[n];if r then r[1][r[2]](r[1],s,a) end
end
function pd.Table:new() return setmetatable({}, {__index=self}) end
function pd.Table:sync(n) self.name=n;return self end
function pd.Table:length() return 10000 end
function pd.Table:get(i) return (self.name:sub(1,1)=='0' and 1 or -1)*i/10000 end
local function object(n,args)
 local o=setmetatable({packets={}}, {__index=classes[n]})
 function o:outlet(_,s,a) self.packets[#self.packets+1]=a end
 function o:error(s) error(s) end
 assert(o:initialize(n,args));o:postinitialize();return o
end
dofile('sample-trim.pd_lua')
local t=object('sample-trim',{7});local source={7,1,1,625,0,10000}
t:command('trim',{0,1});assert(not t.pending)
t:in_1_list(source);assert(t.packets[#t.packets][6]==10000)
t:command('trim',{1,3});assert(t.pending and t.packets[#t.packets][2]==0)
t:in_1_list(source);assert(t.packets[#t.packets][2]==0)
t.clock:fire();assert(t.first==1000 and t.last==3000)
t:in_1_list(source);assert(t.packets[#t.packets][4]==125 and t.packets[#t.packets][5]==1000)
for _,a in ipairs({{0,4},{2,1},{0/0,2},{1,math.huge},{1,1.001},{'x',2},{1}}) do
 t:command('trim',a);assert(not t.pending and t.first==1000)
end
t:command('restore',{});t.clock:fire();assert(t.first==0 and t.last==10000)
t:command('trim',{2,5});t:in_1_list({7,0,1,625,0,10000});t.clock:fire()
assert(t.source==nil and not t.pending)
t:in_1_list(source);assert(t.first==0 and t.last==10000)
t:command('trim',{0.0006,0.0051});t.clock:fire();assert(t.first==1 and t.last==5)
t:finalize()
dofile('buffer-view-data.pd_lua')
local b=object('buffer-view-data',{'sample',7})
b:request('vacant',{'vacancy'});assert(sent[#sent][3][2]==1)
b:in_1_symbol('/test/original.wav');b:request('vacant',{'vacancy'});assert(sent[#sent][3][2]==0)
b:metadata('list',source);assert(b.name=='original.wav')
b:request('source',{'source-reply'});assert(sent[#sent][3][1]=='/test/original.wav')
b:request('vacant',{'vacancy'});assert(sent[#sent][3][2]==0)
b:metadata('list',{7,0,1,625,0,10000});b:metadata('list',{7,1,1,125,1000,3000});assert(b.name=='original.wav')
b:request('range',{'detail1',1100,1250});b:request('range',{'detail2',2000,2500});b:request('peaks',{'whole'})
for i=1,30 do b.clock:fire() end
local got={}
for _,e in ipairs(sent) do if e[2]=='peaks' then got[e[1]]=e[3] end end
assert(got.detail1[2]==1100 and got.detail1[3]==1250)
assert(got.detail2[2]==2000 and got.detail2[3]==2500)
assert(got.whole[2]==1000 and got.whole[3]==3000)
assert(got.whole[4]>=0 and got.whole[6]<=0)
b:request('range',{'cancelled',1200,2000});b:request('cancel',{'cancelled'});assert(not b.job)
b:request('range',{'invalid',0,99999});assert(not b.job)
b:request('range',{'stale',1100,2500});b:metadata('list',{7,0,1,125,1000,3000});assert(not b.job)
dofile('sample-editor.pd_lua')
local editor=object('sample-editor',{100,2,300})
editor:select('sample_buffer_7');assert(editor.key=='sample_buffer_7')
b:destruct();assert(editor.key==nil and not editor.ready)
local count=#sent;editor:destruct();assert(#sent==count)
print('PASS: reversible bounds, invalid input, selection persistence, load cancellation, stereo range cache, cancellation, filename retention')
