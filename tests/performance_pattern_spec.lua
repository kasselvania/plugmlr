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
dofile('performance-pattern.pd_lua')
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
 local c=setmetatable({out={}}, {__index=classes['performance-pattern']})
 function c:outlet(n,s,a)
 self.out[#self.out+1]={now,n,s,a}
 if n==3 then for t=1,6 do self:in_2('state',{t,0,2,0}) end end
 if self.callback then self:callback(n,s,a) end
 end
 c:initialize();c:postinitialize();return c
end
local function control(c,s)c:in_1(s,{}) end
local function count(c,n)local k=0;for _,e in ipairs(c.out)do if e[2]==n then k=k+1 end end;return k end
local c=instance();control(c,'toggle');assert(c.state=='recording')
c:in_2('cut',{0,1});c:in_2('cut',{1,16});c:in_2('speed',{1,0/0});assert(#c.events==0)
control(c,'toggle');assert(c.state=='empty')
control(c,'toggle');advance(200);c:in_2('cut',{1,2});advance(500);c:in_2('direction',{1,1})
advance(700);c:in_2('speed',{2,4});advance(800);c:in_2('transport',{1,0});advance(1000);control(c,'toggle')
assert(c.length==1000 and c.events[1][1]==200 and c.events[4][1]==800)
advance(2400)
local out={};for _,e in ipairs(c.out)do if e[2]==1 then out[#out+1]=e end end
assert(#out==9,#out)
assert(out[1][1]==1000 and out[1][4][2]=='restore' and out[1][4][1]==1)
assert(out[2][1]==1000 and out[2][4][1]==2) -- Untouched tracks never restored.
assert(out[3][1]==1200 and out[3][4][2]=='cut')
assert(out[6][1]==1800 and out[6][4][2]=='transport')
assert(out[7][1]==2000 and out[7][4][2]=='restore')
assert(out[9][1]==2200) -- 200 ms tail + 200 ms lead between actions.
control(c,'stop');local n=count(c,1);advance(2600);assert(count(c,1)==n)
control(c,'toggle');advance(2800);assert(c.out[#c.out][4][2]=='cut')
c.callback=function(self,n)if n==1 then control(self,'clear') end end
advance(3100);assert(c.state=='empty');n=count(c,1);advance(3200);assert(count(c,1)==n)
local d=instance();control(d,'toggle');d:in_2('cut',{6,0});advance(now+300000);assert(d.state=='stopped' and d.length==300000)
assert(d.out[#d.out][3]=='error' and d.out[#d.out][4][1]=='duration_limit')
local e=instance();control(e,'toggle');for i=1,4096 do e:in_2('cut',{1,i%16}) end
assert(e.state=='stopped' and #e.events==4096 and e.length==10)
e:in_2('cut',{1,1});assert(#e.events==4096)
control(e,'clear');control(e,'toggle');control(e,'stop');assert(e.state=='empty')
print('PASS immediate timing, leading/trailing gaps, typed events, participant restore, Stop/restart/Clear and limits')
