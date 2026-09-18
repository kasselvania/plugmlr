-- Test-only passive durable observer; no receiver mutation or GUI work in callbacks.
local C=pd.Class:new():register('rr-observer')
local function hex(s) return (tostring(s):gsub('.',function(c)return string.format('%02x',string.byte(c))end)) end
function C:initialize(_,a) self.inlets,self.outlets=0,0;self.seq=0;self.receivers={};return true end
function C:log(kind,a)
 self.seq=self.seq+1
 local f=assert(io.open(self._loadpath..'events.tsv','a'));f:write(self.seq,'\t',kind)
 for _,v in ipairs(a or {})do f:write('\t',hex(v))end
 f:write('\n');f:close()
end
function C:postinitialize()
 self:log('boot',{})
 local function bind(n,fn)local m='r'..(#self.receivers+1);self[m]=fn;self.receivers[#self.receivers+1]=pd.Receive:new():register(self,n,m)end
 bind('rr-event',function(s,sel,a)s:log(sel,a)end)
 bind('rr-track',function(s,_,a)s:log('track',a)end)
 for slot=1,16 do
  bind(slot..'-sample-loaded',function(s)s:log('loaded',{slot});pd.send('rr-query','list',{slot})end)
  local reply='rr-owner-'..slot
  bind(reply,function(s,sel,a)local b={slot};for _,v in ipairs(a)do b[#b+1]=v end;s:log(sel,b)end)
 end
 bind('rr-query',function(s,_,a)
  local value=tonumber(a[1]);local slot=value and math.tointeger(value)
  if not slot or slot<1 or slot>16 then return end
  local key='sample_buffer_'..slot..'-view-get';local reply='rr-owner-'..slot
  pd.send(key,'info',{reply});pd.send(key,'source',{reply});pd.send(key,'tempo',{reply})
 end)
end
function C:finalize() for _,r in ipairs(self.receivers)do r:destruct()end end
