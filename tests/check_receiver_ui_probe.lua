-- The UI probe must work with only its observer; no deterministic driver exists.
local C
pd={Class={}}
function pd.Class:new()return setmetatable({}, {__index=self})end
function pd.Class:register()C=self;return self end
local events={}
function pd.send(name,kind,a)
 assert(name=='rr-event' or name=='rr-query','UI probe emitted unbound bus '..name)
 events[#events+1]=kind
end
dofile(assert(arg[1],'Pass generated UI sample-stretch.pd_lua'))
local delayed=false
local o=setmetatable({track='1',destination=16,loaded={},clock={delay=function()delayed=true end}},{__index=C})
o:copy_loaded()
assert(o.loaded and o.load_complete and delayed)
assert(#events==2 and events[1]=='callback-enter' and events[2]=='callback-return')
print('PASS: UI completion probe needs no rr-hook listener and preserves deferred callback')
