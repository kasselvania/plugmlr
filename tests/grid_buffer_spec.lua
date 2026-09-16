-- Production classifier/renderer with a deterministic Pd logical clock.
local classes,clocks,now={},{},0
pd={Class={},Clock={},Receive={}}
function pd.Class:new()local c={};function c:register(n)classes[n]=self;return self end;return c end
function pd.Clock:new()local c={};function c:register(o,m)self.o=o;self.m=m;clocks[#clocks+1]=self;return self end;function c:unset()self.due=nil end;function c:delay(t)self.due=now+t end;return c end
function pd.Receive:new()local r={};function r:register()return self end;return r end
local function advance(t)for _,c in ipairs(clocks)do if c.due and c.due<=t then c.due=nil;c.o[c.m](c.o)end end;now=t end
local function new(name)
 local c=setmetatable({events={}}, {__index=classes[name]})
 function c:outlet(n,s,a)local copy={};for i,v in ipairs(a)do copy[i]=v end;self.events[#self.events+1]={n,s,copy}end
 c:initialize(nil,{});c:postinitialize();return c
end
dofile('grid-cut-keys.pd_lua');dofile('grid-page-leds.pd_lua')
local k=new('grid-cut-keys');k:in_2_float(1)
local function key(x,y,z)k:in_1_list({x,y,z})end
local function tap(x,y)key(x,y,1);key(x,y,0)end
local function enter()key(15,0,1);tap(14,0);key(15,0,0)end
local function count(n)local t={};for _,e in ipairs(k.events)do if e[1]==n then t[#t+1]=e[3]end end;return t end
enter();assert(k.page=='buffer' and k.bank=='sample');assert(#count(10)==0)
for row=1,6 do for slot=1,16 do tap(slot-1,row) end end
assert(#count(10)==96)
for i,a in ipairs(count(10))do assert(a[1]==math.floor((i-1)/16)+1 and a[2]=='sample' and a[3]==(i-1)%16+1)end
local n=#count(10);tap(15,7);assert(k.bank=='live' and #count(10)==n)
for row=1,6 do tap(15,row)end
assert(#count(10)==102 and count(10)[102][2]=='live')
key(3,2,1);key(3,2,1);tap(0,7);key(3,2,1);key(3,2,0);assert(#count(10)==103)
tap(3,2);assert(#count(10)==104)
for _,mod in ipairs({13,15})do key(mod,0,1);tap(6,4);tap(15,7);key(mod,0,0)end
assert(#count(10)==104 and k.bank=='sample')
for _,x in ipairs({1,2,7,14})do tap(x,7)end;assert(#count(10)==104)
-- Page entry and bank switches never launch cuts or transport; patterns stay usable.
assert(#count(1)==0 and #count(2)==0 and #count(5)==0)
tap(4,0);assert(count(9)[1][1]==1)
key(3,1,1);tap(1,0);key(3,1,1);key(3,1,0);assert(#count(1)==0)
tap(3,1);assert(#count(1)==1)
-- Preserve the 80ms loop threshold; entering BUFFER cancels a held pair.
key(2,2,1);key(7,2,1);advance(79);key(7,2,0);key(2,2,0);assert(#count(5)==0)
key(2,2,1);key(7,2,1);advance(159);key(7,2,0);key(2,2,0);assert(#count(5)==1)
key(2,2,1);key(7,2,1);enter();advance(300);key(7,2,0);key(2,2,0);assert(#count(5)==1)
n=#count(10);k:in_2_float(0);tap(0,1);k:in_2_float(1);assert(k.page=='buffer' and #count(10)==n)
key(0,1,0);tap(0,1);assert(#count(10)==n+1)
-- Only actual committed selection drives the highlighted cell.
local l=new('grid-page-leds');l:in_1('connected',{1});l:in_1('page',{'buffer'})
local function row(y)for i=#l.events,1,-1 do local e=l.events[i];if e[3][2]==y then return e[3]end end end
l:metadata_sample('list',{2,1,44.1,100,0,1600});assert(row(1)[4]==5)
l:buffer_1('symbol',{'sample_buffer_2'});assert(row(1)[4]==15)
l['state_1_switching'](l,'float',{1});assert(row(1)[4]==8)
l:buffer_1('symbol',{'live_buffer_16'});assert(row(1)[4]==5)
l:in_1('bank',{'live'});assert(row(1)[18]==8)
l['state_1_switching'](l,'float',{0});assert(row(1)[18]==15)
l:metadata_live('list',{16,48,0,48000,3000,1});assert(row(2)[18]==5)
l:metadata_live('list',{16,48,0,0,0,0});assert(row(2)[18]==1)
l:metadata_sample('list',{2,0,44.1,0,0,0});l:in_1('bank',{'sample'});assert(row(1)[4]==1)
local events=#l.events;l:metadata_sample('list',{99,1,48,0,0,16});l:buffer_1('symbol',{'sample_buffer_99'});assert(#l.events==events)
assert(row(7)[3]==15 and row(7)[18]==5)
l:in_1('connected',{0});l:in_1('bank',{'live'});assert(#l.events==events);l:in_1('connected',{1});assert(row(7)[18]==15)
print('PASS 96 sample assignments, live destinations, bank/page/modifier/duplicate cancellation, patterns, 80ms loop regression and readback-only LEDs')
