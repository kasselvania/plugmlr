-- Exercise the actual observer and file:write varargs without a Pd runtime.
local captured
pd={Class={}}
function pd.Class:new() return setmetatable({}, {__index=self})end
function pd.Class:register() captured=self;return self end
dofile('tests/receiver_lifetime/observer.pd_lua')
local original=io.open
local file=assert(io.tmpfile())
io.open=function(_,mode)assert(mode=='a');return {write=function(_,...)file:write(...)end,close=function()file:flush()end}end
local obj=setmetatable({_loadpath='unused/',seq=0},{__index=captured})
obj:log('test',{'a',1.0,'sample_buffer_16','path with spaces.wav','', 'line\nbreak'})
io.open=original
file:seek('set',0)
local line=file:read('*a');file:close()
assert(line=='1\ttest\t61\t312e30\t73616d706c655f6275666665725f3136\t706174682077697468207370616365732e776176\t\t6c696e650a627265616b\n',line)
print('PASS: actual observer file:write varargs emit only hex fields, including native float atoms')
-- Exercise real observer -> real buffer-view-data protocol with Pd float atoms.
local classes,bindings={},{}
function pd.Class:register(name) classes[name]=self;return self end
pd.Receive={};pd.Clock={}
function pd.Receive:new()return setmetatable({}, {__index=self})end
function pd.Receive:register(o,name,m)assert(not bindings[name]);bindings[name]={o,m};return self end
function pd.Receive:destruct()end
function pd.Clock:new()return setmetatable({}, {__index=self})end
function pd.Clock:register()return self end
function pd.Clock:destruct()end
local sends={}
function pd.send(name,sel,atoms)
 assert(type(name)=='string' and type(sel)=='string' and type(atoms)=='table')
 for k,v in pairs(atoms)do assert(type(k)=='number' and (type(v)=='number' or type(v)=='string'),'Invalid atom argument')end
 local receiver=assert(bindings[name],'Unbound receiver: '..name)
 sends[#sends+1]={name,sel,atoms}
 receiver[1][receiver[2]](receiver[1],sel,atoms)
end
dofile('tests/receiver_lifetime/observer.pd_lua')
dofile('buffer-view-data.pd_lua')
local observer=setmetatable({_loadpath='unused/'},{__index=classes['rr-observer']});assert(observer:initialize('',{}))
local received={};observer.log=function(_,kind,a)received[kind]=a end;observer:postinitialize()
local owner=setmetatable({},{__index=classes['buffer-view-data']});assert(owner:initialize('',{'sample',1.0}));owner:postinitialize()
owner.ready,owner.rate,owner.first,owner.last,owner.name=1,48000,0,36000,'sample.wav';owner.source_path='/tmp/sample.wav';owner.tempo_bpm,owner.tempo_authority=120,'rendered'
pd.send('rr-query','list',{1.0})
assert(received.info[1]==1 and received.info[2]=='sample' and received.info[4]==1)
assert(received.source[2]=='/tmp/sample.wav' and received.tempo[2]==120)
for _,v in ipairs(sends)do assert(not v[1]:find('1.0',1,true));if v[1]=='sample_buffer_1-view-get'then assert(#v[3]==1 and v[3][1]=='rr-owner-1')end end
local n=#sends
observer[bindings['rr-query'][2]](observer,'list',{1.5})
observer[bindings['rr-query'][2]](observer,'list',{17.0})
assert(#sends==n,'Invalid slot emitted owner query')
print('PASS: float slot canonicalization and real owner info/source/tempo roundtrip; valid one-string atoms tables')
