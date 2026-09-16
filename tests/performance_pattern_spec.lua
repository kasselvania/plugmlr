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
 if n==3 then for t=1,6 do self:in_2('state',{t,0,2}) end end
 if self.callback then self:callback(n,s,a) end
 end
 c:initialize();c:postinitialize();return c
end
local function control(c,s)c:in_1(s,{}) end
local function count(c,n)local k=0;for _,e in ipairs(c.out)do if e[2]==n then k=k+1 end end;return k end
local c=instance();control(c,'toggle');assert(c.slots[c.slot].state=='recording')
c:in_2('cut',{0,1});c:in_2('cut',{1,16});c:in_2('speed',{1,0/0});assert(#c.slots[c.slot].events==0)
control(c,'toggle');assert(c.slots[c.slot].state=='empty')
control(c,'toggle');advance(200);c:in_2('cut',{1,2});advance(500);c:in_2('direction',{1,1})
advance(700);c:in_2('speed',{2,4});advance(800);c:in_2('transport',{1,0});advance(1000);control(c,'toggle')
assert(c.slots[c.slot].length==1000 and c.slots[c.slot].events[1][1]==200 and c.slots[c.slot].events[4][1]==800)
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
advance(3100);assert(c.slots[c.slot].state=='empty');n=count(c,1);advance(3200);assert(count(c,1)==n)
local d=instance();control(d,'toggle');d:in_2('cut',{6,0});advance(now+300000);assert(d.slots[d.slot].state=='stopped' and d.slots[d.slot].length==300000)
assert(d.out[#d.out][3]=='error' and d.out[#d.out][4][1]=='duration_limit')
local e=instance();control(e,'toggle');for i=1,4096 do e:in_2('cut',{1,i%16}) end
assert(e.slots[e.slot].state=='stopped' and #e.slots[e.slot].events==4096 and e.slots[e.slot].length==10)
e:in_2('cut',{1,1});assert(#e.slots[e.slot].events==4096)
control(e,'clear');control(e,'toggle');control(e,'stop');assert(e.slots[e.slot].state=='empty')
print('PASS immediate timing, leading/trailing gaps, typed events, participant restore, Stop/restart/Clear and limits')

-- Bank behavior uses the same timeline: independent stores and one pending clock.
local bank=instance();local base=now
local function slot(i) return bank.slots[i] end
local function cmd(s,i)bank:in_1(s,i and {i} or {}) end
cmd('toggle',2);advance(base+50);bank:in_2('cut',{1,3})
advance(base+100);cmd('toggle',3) -- Finish slot 2, retain its leading/trailing 50ms.
assert(slot(2).state=='stopped' and slot(2).length==100 and slot(2).events[1][1]==50)
assert(slot(3).state=='recording' and #slot(3).events==0)
bank:in_2('direction',{2,1});advance(base+200);cmd('toggle',3)
assert(slot(3).state=='playing' and slot(2).state=='stopped')
local deadline=bank.clock.due;cmd('clear',2)
assert(bank.slot==3 and bank.clock.due==deadline and slot(2).state=='empty')
advance(base+225);cmd('toggle',8) -- Stop replay before opening the next recorder.
assert(slot(3).state=='stopped' and slot(8).state=='recording')
advance(base+500);assert(#slot(8).events==0,'outgoing replay contaminated new recording')
cmd('clear',3);assert(slot(8).state=='recording')
bank:in_2('speed',{6,4});advance(base+550);cmd('toggle',8)
assert(slot(8).length==325 and slot(8).events[1][1]==275)
for _,bad in ipairs({0,9,1.5,-1,math.huge}) do
 cmd('toggle',bad);cmd('clear',bad);assert(bank.slot==8 and slot(8).state=='playing')
end
cmd('stop');assert(slot(8).state=='stopped')
-- Fill every slot with distinct actions and snapshots; switching keeps others intact.
for i=1,8 do
 cmd('clear',i)
 bank.callback=function(self,n) if n==3 then self:in_2('state',{1,i%2,(i-1)%5}) end end
 cmd('toggle',i);advance(now+20);bank:in_2('cut',{1,i-1});advance(now+30);cmd('stop')
end
bank.callback=nil
for i=1,8 do
 assert(slot(i).state=='stopped' and slot(i).length==50)
 assert(slot(i).events[1][4]==i-1 and slot(i).initial[1][1]==i%2 and slot(i).initial[1][2]==(i-1)%5)
end
local t=now;cmd('toggle',1);advance(t+10);cmd('toggle',8);advance(t+31)
local emitted={};for _,e in ipairs(bank.out) do if e[1]>=t and e[2]==1 then emitted[#emitted+1]=e end end
assert(#emitted==3 and emitted[1][4][2]=='restore' and emitted[2][4][2]=='restore' and emitted[3][4][3]==7)
-- A reentrant slot switch during restore must not leave an outgoing tick scheduled.
bank.callback=function(self,n)
 if n==1 then self.callback=nil;cmd('toggle',4) end
end
cmd('toggle',2);assert(bank.slot==4 and slot(2).state=='stopped' and slot(4).state=='playing')
advance(now+21);assert(bank.out[#bank.out][4][3]==3)
cmd('stop')
-- Independent caps, and cancelling during snapshot cannot resurrect Record.
cmd('clear',7);cmd('toggle',7)
for i=1,4096 do bank:in_2('cut',{1,i%16}) end
assert(slot(7).state=='stopped' and #slot(7).events==4096 and #slot(8).events==1)
cmd('clear',6);cmd('toggle',6);bank:in_2('cut',{1,0});advance(now+300000)
assert(slot(6).length==300000 and slot(6).state=='stopped' and #slot(7).events==4096)
bank.callback=function(self,n)if n==3 then cmd('clear') end end
cmd('clear',5);cmd('toggle',5);assert(slot(5).state=='empty' and not bank.clock.due)
print('PASS eight independent slots, finish/switch, inactive Clear, exclusive replay, snapshots, bounds and reentrant cancellation')
