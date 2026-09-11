local C
pd={Class={new=function() return {register=function(self) C=self;return self end} end}}
dofile('mlr-grid-compat.pd_lua')
local c=setmetatable({}, {__index=C});c:initialize()
local events={}
function c:outlet(o,s,a) events[#events+1]={o,s,a} end
local function send(s,a) events={};c:in_1(s,a);return events end
local function eq(a,b) assert(a==b,tostring(a)..' ~= '..tostring(b)) end
send('/monome/grid/led/all',{1});eq(events[1][1],3)
c:in_3('attached',{'test','/monome',16,8})
eq(events[#events][2],'/sys/size')
send('/monome/grid/led/set',{15,7,1});eq(events[1][3][3],15)
send('/monome/grid/led/level/set',{0,0,6});eq(events[1][3][3],6)
send('/monome/grid/led/row',{0,1,1,128});eq(#events,16);eq(events[1][3][3],15);eq(events[16][3][1],15);eq(events[16][3][3],15)
send('/monome/grid/led/col',{0,0,128});eq(#events,8);eq(events[8][3][2],7);eq(events[8][3][3],15)
send('/monome/grid/led/level/row',{0,2,0,4,10,15});eq(#events,4);eq(events[3][3][3],10)
local map={8,0};for i=1,64 do map[#map+1]=i%16 end
send('/monome/grid/led/level/map',map);eq(#events,64);eq(events[64][3][1],15);eq(events[64][3][2],7)
send('monome/grid/led/all',{0});eq(events[1][2],'all');eq(events[1][3][1],0)
for _,pair in ipairs({{'set',{16,0,1}},{'set',{-1,0,1}},{'level/set',{0,0,16}},{'level/set',{0/0,0,1}},{'row',{0,0,255,999}},{'col',{0,0,255,255}},{'level/map',{0,0,1}},{'intensity',{2}}}) do
 send('/monome/grid/led/'..pair[1],pair[2]);eq(#events,1);eq(events[1][1],3)
end
send('/sys/port',{9999});eq(events[1][1],3)
events={};c:in_2('key',{4,3,0,'synthetic','release'});eq(events[1][2],'/monome/grid/key');eq(#events[1][3],3)
c:in_3('detached',{});send('/monome/grid/led/all',{1});eq(events[1][1],3)
print('PASS: legacy LED translations, complete-command rejection, key/size projection, detach and ownership bypass refusal')
