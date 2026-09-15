-- Control-state/limits test against production Lua; native timing is checked separately.
local now, clocks, classes=0,{},{}
pd={Class={},Clock={}}
function pd.Class:new() local c={};function c:register(n) classes[n]=self;return self end;return c end
function pd.Clock:new()
 local c={};function c:register(o,m)self.o=o;self.m=m;clocks[#clocks+1]=self;return self end
 function c:delay(t)self.due=now+t end
 function c:unset()self.due=nil end
 return c
end
function pd.systime()return now end
function pd.timesince(t)return now-t end
dofile('cut-pattern.pd_lua')
local function advance(t)
 local count=0
 while true do
  local nextc
  for _,c in ipairs(clocks) do if c.due and c.due<=t and (not nextc or c.due<nextc.due) then nextc=c end end
  if not nextc then break end
  now=nextc.due;nextc.due=nil;nextc.o[nextc.m](nextc.o);count=count+1;assert(count<100000,'unbounded scheduling')
 end
 now=t
end
local function instance()
 local c=setmetatable({out={}}, {__index=classes['cut-pattern']})
 function c:outlet(n,s,a)self.out[#self.out+1]={now,n,s,a};if self.callback then self:callback(n,s,a) end end
 c:initialize();c:postinitialize();return c
end
local function control(c,s)c:in_1(s,{}) end
local function count(c,n)local k=0;for _,e in ipairs(c.out)do if e[2]==n then k=k+1 end end;return k end
local c=instance();control(c,'toggle');c:in_2_list({0,1});c:in_2_list({1,16});c:in_2_list({1,0/0});assert(c.state=='armed')
control(c,'toggle');assert(c.state=='empty')
control(c,'toggle');c:in_2_list({1,2});advance(25);c:in_2_list({2,9});advance(100);control(c,'toggle')
advance(1100);assert(count(c,1)==21);assert(c.length==100)
control(c,'stop');local n=count(c,1);advance(1300);assert(count(c,1)==n)
control(c,'toggle');assert(c.out[#c.out][4][1]==1)
-- Clear during downstream callback must leave no future event scheduled.
c.callback=function(self,n)if n==1 then control(self,'clear') end end
advance(1325);assert(c.state=='empty');n=count(c,1);advance(1400);assert(count(c,1)==n)
local d=instance();control(d,'toggle');d:in_2_list({6,0});advance(now+300000);assert(d.state=='stopped' and d.length==300000)
assert(d.out[#d.out][3]=='error' and d.out[#d.out][4][1]=='duration_limit')
local e=instance();control(e,'toggle');for i=1,4096 do e:in_2_list({1,i%16}) end
assert(e.state=='stopped' and #e.events==4096 and e.length==10)
e:in_2_list({1,1});assert(#e.events==4096)
control(e,'clear');control(e,'toggle');e:in_2_list({1,1});control(e,'stop');assert(e.state=='stopped' and e.length==10)
print('PASS pattern validation, exact cycles, Stop/restart, reentrant Clear, 300s and 4096-event limits')
