-- Finite native control scheduler. No audio processing, no worker substitute.
local C=pd.Class:new():register('rr-driver')
function C:initialize(_,a)
 self.inlets,self.outlets=0,0;self.index=0;self.limit=tonumber(a[1]);self.mode=tostring(a[2]);self.stage='begin';return true
end
function C:event(kind,a) pd.send('rr-event',kind,a or {})end
function C:postinitialize()
 self.alarm=pd.Clock:new():register(self,'deadline');self.alarm:delay(self.mode=='campaign' and 900000 or 120000)
 self.timer=pd.Clock:new():register(self,'step');self.turn=pd.Clock:new():register(self,'intervene')
 self.hook=pd.Receive:new():register(self,'rr-hook','completion')
 self.events=pd.Receive:new():register(self,'rr-event','observe')
 self.timer:delay(1000)
end
function C:observe(sel,a)
 if sel=='track' and tonumber(a[1])==1 then self.actual=a[2];return end
 if sel=='info' and tonumber(a[1])==16 then self.bounds=(a[2]=='sample' and tonumber(a[4])==1 and tonumber(a[5])==48000 and tonumber(a[7])-tonumber(a[6])==36000);return end
 if sel=='loaded' and tonumber(a[1])==16 then self.loaded_count=(self.loaded_count or 0)+1;return end
 if sel=='source' and tonumber(a[1])==16 then self.output=a[2];return end
 if tonumber(a[1])~=1 then return end
 if sel=='callback-return' then self.callbacks=(self.callbacks or 0)+1;if tonumber(a[3])~=1 or tonumber(a[4])~=1 then self.problem='Receiver did not survive callback'end
 elseif sel=='deferred-return' then self.done=true;self.cancelled=tonumber(a[4]);if tonumber(a[3])~=0 then self.problem='Receiver not released by clock'end
 elseif sel=='finalize-return' then self.finalized=true end
end
function C:deadline() self:fail('Overall finite deadline exceeded')end
function C:completion(_,a)
 if tonumber(a[1])~=1 or self.hooked then return end
 self.hooked=true;self.destination=math.tointeger(a[2]);self.turn:delay(0)
end
function C:intervene()
 self:event('intervention',{self.index,self.case})
 if self.case=='duplicate' then pd.send(self.destination..'-sample-loaded','bang',{});pd.send(self.destination..'-sample-loaded','bang',{})
 elseif self.case=='cancel' then pd.send('rr-command-1','cancel',{})
 elseif self.case=='manual' then pd.send('1-buffer-select','sample',{2})
 elseif self.case=='destroy' then pd.send('pd-rr-session-container','clear',{});self.destroyed=true end
end
function C:fail(s)
 self.stage='failed';self:event('failure',{self.index,s});self.timer:unset();self.turn:unset();self.alarm:unset()
 -- Destruction from a driver clock, never a receiver callback.
 pd.send('pd-rr-session-container','clear',{})
end
function C:step()
 if self.stage=='begin' then
  self.index=self.index+1
  if self.index>self.limit then self:event('campaign-done',{self.limit});self.alarm:unset();return end
  self.case=self.mode=='campaign' and 'normal' or ({'normal','duplicate','cancel','manual','destroy'})[self.index]
  self.hooked,self.done,self.finalized,self.destroyed=false,false,false,false;self.ticks=0;self.callbacks=0;self.loaded_count=0;self.problem=nil;self.actual=nil;self.bounds=false;self.output=nil;self.cancelled=nil
  self:event('cycle',{self.index,self.case})
  pd.send('pd-rr-session-container','obj',{20,20,'rr-session'})
  pd.send('pd-rr-session-container','loadbang',{})
  self.stage='seed';self.timer:delay(200)
 elseif self.stage=='seed' then
  pd.send('1-sample-path','symbol',{self._loadpath..'source.wav'})
  pd.send('2-sample-path','symbol',{self._loadpath..'source.wav'})
  self.stage='select';self.timer:delay(150)
 elseif self.stage=='select' then
  pd.send('1-buffer-select','sample',{1})
  self.stage='render';self.timer:delay(150)
 elseif self.stage=='render' then
  pd.send('1-sample-editor','start',{.5});pd.send('1-sample-editor','finish',{1.5})
  pd.send('rr-command-1','source-bpm',{90});pd.send('rr-command-1','target-bpm',{120});pd.send('rr-command-1','pitch',{0})
  pd.send('rr-command-1','render',{});self.stage='wait';self.timer:delay(100)
 elseif self.stage=='wait' then
  if self.problem then self:fail(self.problem);return end
  self.ticks=self.ticks+1
  if self.done or self.destroyed then self.stage='settle';self.timer:delay(250)
  elseif self.ticks>=150 then self:fail('No completed handoff within 15 seconds')
  else self.timer:delay(100) end
 elseif self.stage=='settle' then
  if self.case=='destroy' and (not self.finalized or self.done) then self:fail('Destruction ordering failed');return end
  if not self.destroyed then pd.send('rr-query','list',{16}) end
  local expected_callbacks=self.case=='duplicate' and 3 or 1
  local want=self.case=='manual' and 'sample_buffer_2' or ((self.case=='cancel' or self.case=='destroy') and 'sample_buffer_1' or 'sample_buffer_16')
  if self.problem or self.callbacks~=expected_callbacks or self.loaded_count<1 or not self.bounds or not self.output or self.output=='' or self.actual~=want then self:fail(self.problem or 'Native completion/state assertion failed');return end
  if self.case~='destroy' and self.cancelled~=((self.case=='cancel' or self.case=='manual') and 1 or 0)then self:fail('Wrong cancellation state');return end
  self:event('cycle-end',{self.index,self.case})
  if not self.destroyed then pd.send('pd-rr-session-container','clear',{}) end
  self.stage='begin';self.timer:delay(100)
 end
end
function C:finalize()
 self.alarm:destruct();self.timer:destruct();self.turn:destruct();self.hook:destruct();self.events:destruct()
end
