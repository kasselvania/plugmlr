-- Previous/next loaded slot in the current bank. Selection still belongs to the player.
local C=pd.Class:new():register('buffer-browse')
function C:initialize(_,a)
 self.player,self.track=string.format('%d',a[1]),string.format('%d',a[2])
 self.inlets,self.outlets=1,0;self.kind,self.slot='live',1
 self.loaded={sample={},live={}};self.receivers={};return true
end
function C:postinitialize()
 local function bind(n,m) self.receivers[#self.receivers+1]=pd.Receive:new():register(self,n,m) end
 bind('s_b_buffer_states','samples');bind('l_b_buffer_states','live');bind(self.player..'-buffer_ID','selected')
end
function C:finalize() for _,r in ipairs(self.receivers) do r:destruct() end end
function C:samples(_,a) self.loaded.sample[a[1]]=a[2]~=0 and a[6]>a[5] end
function C:live(_,a) self.loaded.live[a[1]]=a[6]~=0 and a[4]>a[3] end
function C:selected(_,a)
 local k,n=tostring(a[1]):match('^(%a+)_buffer_(%d+)$')
 if self.loaded[k] then self.kind,self.slot=k,tonumber(n) end
end
function C:in_1_float(direction)
 if direction~=1 and direction~=-1 then return end
 for step=1,16 do
  local n=(self.slot-1+direction*step)%16+1
  if self.loaded[self.kind][n] then
   if n~=self.slot then self.slot=n;pd.send(self.track..'-buffer-select',self.kind,{n}) end
   return
  end
 end
end
