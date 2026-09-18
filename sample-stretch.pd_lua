-- Optional editor process bridge. Heavy work runs outside Pd; original loader/player
-- own adoption and audition. This object never reads/writes an audio table.
local C=pd.Class:new():register('sample-stretch')
local function finite(x) return type(x)=='number' and x==x and math.abs(x)<math.huge end
local function quote(s) return "'"..tostring(s):gsub("'", "'\\''").."'" end
local function exists(p) local f=io.open(p,'rb');if f then f:close();return true end end
function C:initialize(_,a)
 self.player,self.track,self.ui=string.format('%d',a[1]),string.format('%d',a[2]),string.format('%d',a[3])
 self.reply=self.ui..'-stretch-reply';self.receivers={};self.ratio,self.pitch=1,0
 self.mode,self.source_bpm,self.target_bpm,self.target_seconds,self.authority='bpm',0,120,0,'unknown'
 self.inlets,self.outlets=1,0;return true
end
function C:postinitialize()
 local function bind(n,m) self.receivers[#self.receivers+1]=pd.Receive:new():register(self,n,m) end
 bind(self.ui..'-stretch-command','command');bind(self.ui..'-editor-selection','selection')
 bind(self.reply,'reply_message')
 self.clock=pd.Clock:new():register(self,'poll')
end
function C:finalize()
 self:cancel();self.clock:destruct()
 if self.loaded then self.loaded:destruct() end
 for _,r in ipairs(self.receivers) do r:destruct() end
end
function C:status(s) pd.send(self.ui..'-stretch-status','label',{s}) end
function C:selection(_,a)
 if (self.job or self.loaded) and self.selected then
  for i=1,5 do if self.selected[i]~=a[i] then self.adopt=false;self.load_cancelled=true;break end end
 end
 self.selected=a
 if a[1]~='none' then
  self.source_bpm,self.authority=0,'unknown'
  pd.send(a[1]..'-view-get','tempo',{self.reply})
 end
 self:fields()
end
function C:duration()
 local s=self.selected
 return s and s[1]~='none' and finite(s[5]) and s[5]>0 and (s[4]-s[3])/s[5] or 0
end
function C:calculate()
 local d=self:duration();if d<=0 then return nil,'Select a ready Sample and valid region' end
 local ratio=self.ratio
 if self.mode=='bpm' then
  if self.source_bpm<=0 then return nil,'Source tempo unknown: enter BPM or beats in selection' end
  ratio=self.source_bpm/self.target_bpm
 elseif self.mode=='seconds' then ratio=self.target_seconds/d end
 if not finite(ratio) or ratio<.25 or ratio>4 then return nil,'Stretch range is 0.25–4x the selection length' end
 local bpm=self.source_bpm>0 and self.source_bpm/ratio or 0
 if bpm>0 and (bpm<1 or bpm>999) then return nil,'Result BPM must stay within 1–999' end
 if d*ratio>600 then return nil,'Rendered duration is limited to 600 seconds' end
 return {duration=d,ratio=ratio,seconds=d*ratio,bpm=self.source_bpm>0 and self.source_bpm/ratio or 0,
  source_bpm=self.source_bpm,authority=self.authority,beats=self.source_bpm*d/60,mode=self.mode}
end
function C:fields()
 local d=self:duration();local spec=self:calculate()
 local values={['source-bpm']=self.source_bpm,beats=self.source_bpm*d/60,mode=({bpm=0,seconds=1,ratio=2})[self.mode],
  ['target-bpm']=self.mode=='bpm' and self.target_bpm or (spec and spec.bpm or 0),
  seconds=self.mode=='seconds' and self.target_seconds or (spec and spec.seconds or d),ratio=spec and spec.ratio or self.ratio,pitch=self.pitch}
 for n,v in pairs(values) do pd.send(self.ui..'-stretch-'..n..'-set','set',{v}) end
 pd.send(self.ui..'-stretch-source','label',{string.format('Selection %.4f s | %s',d,
  self.source_bpm>0 and ('Confirmed '..string.format('%.3f',self.source_bpm)..' BPM ('..self.authority..')') or 'Tempo unknown')})
end
function C:confirm(bpm,authority)
 if not finite(bpm) or bpm<1 or bpm>999 or self:duration()<=0 then self:status('Source BPM must be 1–999; select a region first');return end
 pd.send(self.selected[1]..'-view-get','tempo-set',{self.reply,bpm,authority})
 self:fields();local _,err=self:calculate();self:status(err or 'Ready to render and use a copy')
end
function C:cancel()
 self.adopt=false;self.load_cancelled=true
 if self.job then
  local f=io.open(self.job..'.cancel','w');if f then f:close() end
  self.job=nil;self.clock:unset()
 end
end
function C:reply_message(sel,a)
 if sel=='tempo' then if self.setting_copy_tempo then return end;self.source_bpm,self.authority=a[1],a[2];self:fields()
 elseif sel=='source' then self.source=a[1]
 elseif sel=='vacant' and self.finding and a[2]==1 then self.empty=math.tointeger(a[1]) end
end
function C:command(sel,a)
 if sel~='render' and sel~='load' and sel~='cancel' and (self.job or self.loaded) then self.adopt=false;self.load_cancelled=true end
 if sel=='source-bpm' then self:confirm(a[1],'manual');return
 elseif sel=='beats' then
  if not finite(a[1]) or a[1]<=0 or self:duration()<=0 then self:status('Enter positive beats for the selected region');return end
  self:confirm(a[1]*60/self:duration(),'beats');return
 elseif sel=='half' or sel=='double' then self:confirm(self.source_bpm*(sel=='half' and .5 or 2),'manual');return
 elseif sel=='mode' then
  local mode=({[0]='bpm',[1]='seconds',[2]='ratio'})[a[1]]
  if not mode then return end
  local old=self:calculate()
  self.mode=mode
  if old then self.target_seconds,self.ratio=old.seconds,old.ratio;if old.bpm>0 then self.target_bpm=old.bpm end
  elseif self.target_seconds<=0 then self.target_seconds=self:duration() end
 elseif sel=='target-bpm' then
  if not finite(a[1]) or a[1]<1 or a[1]>999 then self:status('Target BPM must be 1–999');return end
  self.target_bpm,self.mode=a[1],'bpm'
 elseif sel=='seconds' then
  if not finite(a[1]) or a[1]<=0 or a[1]>600 then self:status('Target seconds must be above zero and at most 600');return end
  self.target_seconds,self.mode=a[1],'seconds'
 elseif sel=='ratio' or sel=='pitch' then
  if not finite(a[1]) or (sel=='ratio' and (a[1]<.25 or a[1]>4)) or (sel=='pitch' and math.abs(a[1])>24) then
   self:status('Duration 0.25–4x; pitch -24–24 semitones');return
  end
  self[sel]=a[1];if sel=='ratio' then self.mode='ratio' end
 elseif sel=='cancel' then self:cancel();self:status('Cancelled; original unchanged');return
 elseif sel=='load' then self:load_copy();return
 elseif sel~='render' then return end
 if sel~='render' then self:fields();local _,err=self:calculate();self:status(err or 'Ready to render and use a copy');return end
 if self.job or self.loaded then self:status('Wait for the current render/load, or Cancel');return end
 local s=self.selected
 if not s or s[1]=='none' or not finite(s[3]) or not finite(s[4]) or s[4]-s[3]<4 or s[5]<=0 then
  self:status('Select a ready Sample and valid Start / End');return
 end
 local spec,err=self:calculate();if not spec then self:status(err);return end
 self.source=nil;pd.send(s[1]..'-view-get','source',{self.reply})
 if not self.source or self.source=='' then self:status('Reload this sample once to expose its source file');return end
 local python
 for _,p in ipairs({'/opt/homebrew/bin/python3','/usr/local/bin/python3','/usr/bin/python3'}) do if exists(p) then python=p;break end end
 if not python then self:status('Python 3 is required for the render worker');return end
 local base=os.tmpname();local worker=self._loadpath..'scripts/render_sample.py'
 if not exists(worker) then self:status('Render worker is missing beside the patch');os.remove(base);return end
 local args={python,worker,base,self.source,string.format('%d',s[3]),string.format('%d',s[4]),string.format('%d',s[5]),spec.ratio,self.pitch,self._loadpath..'renders',spec.source_bpm,spec.bpm,spec.beats,spec.authority,spec.mode}
 for i,v in ipairs(args) do args[i]=quote(v) end
 -- Shell only detaches the worker. All variable arguments are single-quoted;
 -- Python invokes Rubber Band with an argv list, never a shell command.
 local ok=os.execute(table.concat(args,' ')..' >'..quote(base..'.log')..' 2>&1 < /dev/null &')
 if not ok then self:status('Unable to start render worker');return end
 self.job,self.polls,self.result,self.origin=base,0,nil,math.tointeger(s[2])
 self.adopt,self.render_spec=true,spec
 self:status('Starting render; original stays unchanged');self.clock:delay(100)
end
function C:poll()
 if self.loaded then
  if self.load_complete then
   -- This clock runs after the entire Pd send/bindlist traversal has returned.
   local slot=self.destination
   self.loaded:destruct();self.loaded=nil;self.load_complete=false
   if self.render_spec and self.render_spec.bpm>=1 and self.render_spec.bpm<=999 then
    self.setting_copy_tempo=true
    pd.send('sample_buffer_'..slot..'-view-get','tempo-set',{self.reply,self.render_spec.bpm,'rendered'})
    self.setting_copy_tempo=false
   end
   if self.load_cancelled or (self.selected and self.selected[1]~=self.load_key) then self:status('Copy loaded in Sample '..slot..'; current selection kept');return end
   pd.send(self.track..'-buffer-select','sample',{slot})
   self:status('Sample '..slot..' selected — use Audition loop above. Original: Sample '..tostring(self.origin))
   return
  end
  self.load_polls=self.load_polls+1
  if self.load_polls>=50 then
   self.loaded:destruct();self.loaded=nil;self:status('Copy load did not complete; rendered file preserved')
  else self.clock:delay(100) end
  return
 end
 if not self.job then return end
 self.polls=self.polls+1
 local f=io.open(self.job..'.status','r')
 if f then
  local state,message,path=f:read('*l'),f:read('*l'),f:read('*l');f:close()
  self:status(message or 'Worker status unavailable')
  if state=='ready' or state=='error' or state=='cancelled' then
   self.result=state=='ready' and path or nil;self.job=nil
   if self.result then
    if self.adopt then self:load_copy() else self:status('Copy saved; selection/settings changed, so player was not switched') end
   end
   return
  end
 end
 if self.polls>1300 then self:cancel();self:status('Worker did not finish; see render log');return end
 self.clock:delay(100)
end
function C:load_copy()
 if self.job or self.loaded then self:status('Wait for the current render/load');return end
 if not self.result or not exists(self.result) then self:status('Render a copy first');return end
 -- Query owners now, not a stale population cache. No delayed overwrite.
 self.empty=nil;self.finding=true
 for slot=16,1,-1 do
  pd.send('sample_buffer_'..slot..'-view-get','vacant',{self.reply})
  if self.empty then break end
 end
 self.finding=false
 if not self.empty then self:status('Sample bank full; original and rendered file are preserved');return end
 local slot=self.empty
 self.loaded=pd.Receive:new():register(self,tostring(slot)..'-sample-loaded','copy_loaded')
 self.destination=slot;self.load_polls=0;self.load_complete=false;self.load_cancelled=false;self.load_key=self.selected and self.selected[1]
 self:status('Loading copy into Sample '..slot..'; original remains in Sample '..tostring(self.origin))
 pd.send(tostring(slot)..'-sample-path','symbol',{self.result})
 self.clock:delay(100)
end
function C:copy_loaded()
 -- Never free this receiver or switch buffers within its own callback. The
 -- shared completion bus also has the ordinary player's buffer-selection receiver.
 if not self.loaded or self.load_complete then return end
 self.load_complete=true;self.clock:delay(0)
end
