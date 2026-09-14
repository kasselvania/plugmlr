-- Buffer-owned reversible bounds. Arrays and source file are never modified.
local C=pd.Class:new():register('sample-trim')
local function finite(x) return type(x)=='number' and x==x and math.abs(x)<math.huge end
function C:initialize(_,a)
 self.slot=math.tointeger(a[1]);self.inlets,self.outlets=1,1;return self.slot~=nil
end
function C:postinitialize()
 self.clock=pd.Clock:new():register(self,'commit')
 self.receiver=pd.Receive:new():register(self,self.slot..'-sample-edit','command')
end
function C:finalize() self.clock:destruct();self.receiver:destruct() end
function C:status(s)
 -- This outlet exists even without an editor window.
 self.message=s
end
function C:packet(ready)
 local b=self.source
 if not b then return end
 self:outlet(1,'list',{self.slot,ready,b[3],(self.last-self.first)/16,self.first,self.last})
end
function C:in_1_list(a)
 if #a~=6 or a[1]~=self.slot then return end
 if a[2]==0 then
  self.clock:unset();self.pending=nil;self.source=nil;self.first,self.last=0,0
  self:outlet(1,'list',a);return
 end
 if not self.source then self.source={table.unpack(a)};self.first,self.last=a[5],a[6] end
 self:packet(self.pending and 0 or 1)
end
function C:command(sel,a)
 if sel=='info' and type(a[1])=='string' then
  local b=self.source
  pd.send(a[1],'trim-info',{self.slot,b and b[5] or 0,b and b[6] or 0,self.message or 'Ready'})
  return
 end
 if sel~='trim' and sel~='restore' then return end
 local b=self.source
 if not b or self.pending then self:status('Buffer empty or changing');return end
 local first,last=b[5],b[6]
 if sel=='trim' then
  if #a~=2 or not finite(a[1]) or not finite(a[2]) then self:status('Invalid selection');return end
  first,last=math.floor(a[1]*b[3]*1000+0.5),math.floor(a[2]*b[3]*1000+0.5)
  if first<self.first or last>self.last then self:status('Selection outside usable sample');return end
 end
 if first<b[5] or last>b[6] or last-first<4 then self:status('Selection needs at least four frames');return end
 if first==self.first and last==self.last then self:status('Bounds unchanged');return end
 self.pending={first,last}
 pd.send('buffer-will-change','symbol',{self.slot..'_s_b'})
 self:packet(0)
 self:status('Stopping shared readers before trim')
 self.clock:delay(20)
end
function C:commit()
 local p=self.pending;self.pending=nil
 if not p or not self.source then return end
 self.first,self.last=p[1],p[2]
 self:status('Usable bounds updated; original retained')
 self:packet(1)
end
