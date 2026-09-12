-- Control only. Pd soundfiler owns the file write; this is NOT background I/O.
local C=pd.Class:new():register('take-save-control')
function C:initialize()
 self.inlets,self.outlets=2,3;self.receivers={};self.buffers={};self.busy={};self.playing={}
 self.reply='mlr-save-status';return true
end
function C:postinitialize()
 local function bind(n,fn)
  local m='receive_'..(#self.receivers+1);self[m]=fn
  self.receivers[#self.receivers+1]=pd.Receive:new():register(self,n,m)
 end
 bind('l_b_buffer_states',function(s,_,a) s.buffers[a[1]]=a end)
 bind('mlr-save-take',function(s,sel,a) s:in_1(sel,a) end)
 for i=1,16 do
  bind(i..'-grid-playing',function(s,_,a) s.playing[i]=a[1]~=0 end)
  for _,suffix in ipairs({'_l_b_recording','_l_b_storage_busy'}) do
   local key=i..suffix;bind(key,function(s,_,a) s.busy[key]=a[1]~=0 end)
  end
 end
 self.clock=pd.Clock:new():register(self,'execute')
end
function C:finalize() self.clock:destruct();for _,r in ipairs(self.receivers) do r:destruct() end end
function C:status(text) self:outlet(3,'label',{text}) end
function C:check(slot)
 for _,v in pairs(self.playing) do if v then return 'Stop all players before saving' end end
 for _,v in pairs(self.busy) do if v then return 'Finish recording or buffer changes before saving' end end
 local b=self.buffers[slot]
 if not b or b[6]==0 or b[2]<=0 or b[4]<=b[3] then return 'That live buffer is empty' end
 if b[3]%1~=0 or b[4]%1~=0 then return 'Invalid recorded frame bounds' end
 local l=pd.Table:new():sync('0-live_buffer_'..slot)
 local r=pd.Table:new():sync('1-live_buffer_'..slot)
 if not l or not r or b[3]<0 or b[4]>math.min(l:length(),r:length()) then return 'Recorded bounds exceed storage' end
end
function C:in_1(sel,a)
 if sel=='path' then
  if self.pending and type(a[1])=='string' then self:queue(self.pending,a[1]) end
  self.pending=nil;return
 end
 if sel~='choose' and sel~='save' then return end
 local slot=math.tointeger(a[1])
 if not slot or slot<1 or slot>16 then self:status('Choose a live slot 1 to 16');return end
 local err=self:check(slot)
 if err then self:status(err);return end
 if sel=='choose' then
  self.pending=slot;self:status('Choose a WAV destination');self:outlet(2,'bang',{})
 elseif type(a[2])=='string' then self:queue(slot,a[2]) end
end
function C:queue(slot,path)
 if path=='' then return end
 if path:sub(-4):lower()~='.wav' then path=path..'.wav' end
 self.job={slot=slot,path=path};self:status('Saving live '..slot..'...')
 -- Let any just-stopped reader fade/cleanup finish. Recheck after the chooser.
 self.clock:delay(30)
end
function C:execute()
 local j=self.job;self.job=nil
 if not j then return end
 local err=self:check(j.slot)
 if err then self:status(err);return end
 local b=self.buffers[j.slot];j.frames=b[4]-b[3];self.writing=j
 self:outlet(1,'write',{'-wave','-bytes',4,'-rate',b[2]*1000,'-skip',b[3],'-nframes',j.frames,
                       j.path,'0-live_buffer_'..j.slot,'1-live_buffer_'..j.slot})
 -- soundfiler reports synchronously. A missing reply is not success.
 if self.writing then self.writing=nil;self:status('Save failed - see console') end
end
function C:in_2_float(frames)
 local j=self.writing;self.writing=nil
 if not j then return end
 if frames~=j.frames then self:status('Save incomplete - see console');return end
 self:status('Saved Live '..j.slot..': '..(j.path:match('([^/]+)$') or j.path))
 pd.send('live_buffer_'..j.slot..'-view-saved','symbol',{j.path})
end
