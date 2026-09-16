local C,receivers,sends={}, {},{}
pd={Class={},Receive={}}
function pd.Class:new()local c={};function c:register()C=self;return self end;return c end
function pd.Receive:new()local r={};function r:register(o,b,m)receivers[b]=function(s,a)o[m](o,s,a)end;return self end;function r:destruct()end;return r end
local admit=true
function pd.send(b,s,a)
 sends[#sends+1]={b,s,a}
 local slot=b:match('^(%d+)_l_b_record$')
 if slot and (s=='stop' or admit) then receivers[slot..'_l_b_recording']('float',{s=='start' and 1 or 0}) end
end
dofile('grid-record-control.pd_lua');local c=setmetatable({errors={}}, {__index=C})
function c:outlet(_,_,a)self.errors[#self.errors+1]=a end
c:initialize();c:postinitialize()
local function set(row,slot)receivers[row..'-grid-buffer']('symbol',{slot})end
local function active(slot,v)receivers[slot..'_l_b_recording']('float',{v})end
local function level(row)for i=#sends,1,-1 do if sends[i][1]==row..'-grid-record' then return sends[i][3][1]end end end
set(1,'sample_buffer_1');c:in_1_float(1);assert(c.errors[#c.errors][2]=='Select_live_buffer')
set(1,'live_buffer_1');admit=false;c:in_1_float(1);assert(not c.rows[1].owned)
admit=true;c:in_1_float(1);assert(c.rows[1].owned==1 and level(1)==15)
set(2,'live_buffer_1');c:in_1_float(2);assert(c.errors[#c.errors][2]=='Buffer_records_elsewhere' and level(2)==7)
set(1,'sample_buffer_2');assert(level(1)==15);c:in_1_float(1);assert(not c.rows[1].owned and not c.active[1] and level(1)==0)
set(1,'live_buffer_2');receivers['1-grid-switching']('float',{1});c:in_1_float(1);assert(not c.active[2]);receivers['1-grid-switching']('float',{0})
c:in_1_float(1);active(2,0);assert(not c.rows[1].owned and level(1)==3)
for row=1,6 do set(row,'live_buffer_'..row);c:in_1_float(row);assert(c.rows[row].owned==row)end
for row=1,6 do set(row,'live_buffer_16');c:in_1_float(row);assert(not c.rows[row].owned and not c.active[row])end
active(16,1);c:in_1_float(1);assert(not c.rows[1].owned and c.active[16]);active(16,0)
set(1,'live_buffer_99');assert(not c.rows[1].slot);c:in_1_float(0);c:in_1_float(7);c:in_1_float(1.5)
print('PASS remembered targets, six owners, shared/external refusal, synchronous rejection, completion, switching and lights')
