-- Message-only bridge. live-record owns the writer and admission checks.
local C=pd.Class:new():register('grid-record-control')
function C:initialize()
 self.inlets,self.outlets=1,1
 self.rows,self.active,self.receivers={},{},{}
 for row=1,6 do self.rows[row]={} end
 return true
end
function C:postinitialize()
 local function bind(bus,method,fn)
  self[method]=fn
  self.receivers[#self.receivers+1]=pd.Receive:new():register(self,bus,method)
 end
 for row=1,6 do
  bind(row..'-grid-buffer','buffer_'..row,function(s,sel,a)
   if sel~='symbol' or #a~=1 or type(a[1])~='string' then return end
   local n=a[1]:match('^live_buffer_(%d+)$');n=tonumber(n)
   s.rows[row].slot=n and n>=1 and n<=16 and n or nil;s:publish()
  end)
  bind(row..'-grid-switching','switch_'..row,function(s,sel,a)
   if sel=='float' and (a[1]==0 or a[1]==1) then s.rows[row].switching=a[1]==1;s:publish() end
  end)
 end
 for slot=1,16 do
  bind(slot..'_l_b_recording','record_'..slot,function(s,sel,a)
   if sel~='float' or (a[1]~=0 and a[1]~=1) then return end
   s.active[slot]=a[1]==1
   if not s.active[slot] then
    for _,r in ipairs(s.rows) do if r.owned==slot then r.owned=nil end end
   end
   s:publish()
  end)
 end
 self:publish()
end
function C:finalize()for _,r in ipairs(self.receivers) do r:destruct() end end
function C:publish()
 for row,r in ipairs(self.rows) do
  local level=r.owned and self.active[r.owned] and 15 or
   (not r.switching and r.slot and (self.active[r.slot] and 7 or 3) or 0)
  pd.send(row..'-grid-record','float',{level})
 end
end
function C:in_1_float(row)
 if type(row)~='number' or row%1~=0 or not self.rows[row] then return end
 local r=self.rows[row]
 if r.owned and self.active[r.owned] then
  pd.send(r.owned..'_l_b_record','stop',{});return
 end
 local reason=r.switching and 'Buffer_switching' or (not r.slot and 'Select_live_buffer') or
  (self.active[r.slot] and 'Buffer_records_elsewhere')
 if reason then self:outlet(1,'list',{row,reason});return end
 -- The original writer announces admission synchronously, before storage setup.
 -- Failed start (including synchronous storage failure) must not retain ownership.
 local target=r.slot;r.owned=target
 pd.send(target..'_l_b_record','start',{})
 if not self.active[target] then r.owned=nil end
 self:publish()
end
