-- Label adapter; the buffer owns file identity and content metadata.
local C=pd.Class:new():register('buffer-name')
function C:initialize(_,a)
    self.mode=a[3];self.key=a[1]..'_buffer_'..math.tointeger(a[2]); self.inlets,self.outlets=0,1;return true
end
function C:postinitialize()
    self.rx=pd.Receive:new():register(self,self.key..'-view-info','receive')
    self.clock=pd.Clock:new():register(self,'refresh');self.clock:delay(10)
end
function C:refresh() pd.send(self.key..'-view-get','info',{self.key..'-view-info'}) end
function C:receive(_,a)
    local name=self.mode=='status' and a[8] or a[7] or 'Empty'
    if #name>47 then name=name:sub(1,22)..'...'..name:sub(-22) end
    self:outlet(1,'label',{name})
end
function C:finalize() self.rx:destruct();self.clock:destruct() end
