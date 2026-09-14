-- Editing view/control only. Buffer owns cached peaks and reversible trim;
-- the original player owns audition, looping, transport and all audio.
local C=pd.Class:new():register('sample-editor')
local function finite(x) return type(x)=='number' and x==x and math.abs(x)<math.huge end
local function clamp(x,a,b) return math.max(a,math.min(b,x)) end
function C:initialize(_,a)
 self.player,self.track,self.ui=string.format('%d',a[1]),string.format('%d',a[2]),string.format('%d',a[3])
 self.reply=self.ui..'-editor-reply';self.receivers={};self.inlets,self.outlets=1,0
 self.first,self.last,self.rate,self.a,self.b,self.left,self.right=0,0,1,0,0,0,1
 self.ready,self.show=false,false;self:set_size(920,290);return true
end
function C:postinitialize()
 local function bind(n,fn)
  local m='receive_'..(#self.receivers+1);self[m]=fn
  self.receivers[#self.receivers+1]=pd.Receive:new():register(self,n,m)
 end
 bind(self.player..'-buffer_ID',function(s,_,a) s:select(a[1]) end)
 bind(self.player..'-buffer-switching',function(s,_,a) s.switching=a[1]~=0;s.drag=nil end)
 bind(self.reply,function(s,sel,a) s:reply_message(sel,a) end)
 bind(self.track..'-sample-editor',function(s,sel,a) s:in_1(sel,a) end)
 bind(self.ui..'-editor-command',function(s,sel,a) s:in_1(sel,a) end)
 bind(self.player..'-is_playing_flag',function(s,_,a) s.playing=a[1]~=0 end)
 bind(self.player..'-is_paused_flag',function(s,_,a) s.paused=a[1]~=0 end)
 bind(self.player..'-play-position-frames',function(s,_,a)
  s.position=a[1];s.report=(s.report or 0)+1
  if s.show and s.report%2==0 then s:repaint(3) end
 end)
end
function C:destruct()
 -- Cancel while our reply receiver is still bound, before Pd-Lua teardown.
 if self.key then pd.send(self.key..'-view-get','cancel',{self.reply}) end
 pd.Class.destruct(self)
end
function C:finalize()
 if self.changed then self.changed:destruct() end
 if self.closing then self.closing:destruct() end
 for _,r in ipairs(self.receivers) do r:destruct() end
end
function C:status(message)
 pd.send(self.ui..'-editor-status','label',{message})
end
function C:fields()
 for name,v in pairs({start=self.a/self.rate,finish=self.b/self.rate,length=(self.b-self.a)/self.rate}) do
  if name=='length' then pd.send(self.ui..'-editor-length','label',{string.format('Length %.6f s',v)})
  else pd.send(self.ui..'-editor-'..name,'set',{v}) end
 end
 self:repaint(2)
end
function C:select(key)
 if self.key then pd.send(self.key..'-view-get','cancel',{self.reply}) end
 if self.changed then self.changed:destruct();self.changed=nil end
 if self.closing then self.closing:destruct();self.closing=nil end
 self.key,self.slot,self.ready,self.peaks,self.drag=nil,nil,false,nil,nil
 if type(key)=='string' then self.slot=key:match('^sample_buffer_(%d+)$') end
 if not self.slot then self:status('Select an imported Sample buffer');self:repaint();return end
 self.key=key
 self.changed=pd.Receive:new():register(self,key..'-view-changed','refresh')
 self.closing=pd.Receive:new():register(self,key..'-view-closing','buffer_closed')
 self:refresh()
end
function C:buffer_closed()
 self.key,self.ready,self.drag=nil,false,nil
end
function C:refresh()
 if self.key then pd.send(self.key..'-view-get','info',{self.reply}) end
end
function C:reply_message(sel,a)
 if sel=='info' then
  local changed=self.first~=a[5] or self.last~=a[6] or self.name~=a[7] or self.ready~=(a[3]==1)
  self.ready,self.rate,self.first,self.last,self.name=a[3]==1,a[4]>0 and a[4] or 1,a[5],a[6],a[7]
  if changed then
   self.drag=nil;self.a,self.b=self.first,self.last
   self.left,self.right=self.first,math.max(self.first+1,self.last);self.peaks=nil
   self:fields();self:status(self.ready and 'Drag either edge; seconds refer to the original file' or 'Buffer empty or changing')
   if self.show and self.ready then self:scan() end
   self:repaint()
  end
 elseif sel=='peaks' and a[1]==self.key and a[2]==self.left and a[3]==self.right then
  self.peaks=a;self:repaint(1)
 end
end
function C:scan()
 if not self.key or not self.show or not self.ready then return end
 pd.send(self.key..'-view-get','cancel',{self.reply})
 pd.send(self.key..'-view-get','range',{self.reply,self.left,self.right})
end
function C:range(left,right)
 local width=clamp(math.floor(right-left+0.5),math.min(16,self.last-self.first),self.last-self.first)
 self.left=clamp(math.floor(left+0.5),self.first,self.last-width);self.right=self.left+width
 self.peaks=nil;self:scan();self:repaint()
end
function C:valid()
 return self.ready and not self.switching and finite(self.a) and finite(self.b)
    and self.a>=self.first and self.b<=self.last and self.b-self.a>=4
end
function C:in_1(sel,a)
 if sel=='visible' then
  self.show=a[1]~=0
  if self.show then self:refresh();self:scan();self:repaint()
  elseif self.key then pd.send(self.key..'-view-get','cancel',{self.reply}) end
  return
 end
 if not self.ready or self.switching then self:status('Select a ready Sample buffer');return end
 if sel=='start' or sel=='finish' then
  if not finite(a[1]) then self:status('Invalid seconds');return end
  local v=math.floor(a[1]*self.rate+0.5)
  if sel=='start' then self.a=v else self.b=v end
  self:fields();self:status(self:valid() and 'Selection staged' or 'Invalid selection; adjust Start / End');return
 end
 if sel=='zoom-in' or sel=='zoom-out' then
  local mid=(self.left+self.right)/2;local width=(self.right-self.left)*(sel=='zoom-in' and 0.5 or 2)
  self:range(mid-width/2,mid+width/2);return
 elseif sel=='left' or sel=='right' then
  local shift=(self.right-self.left)*0.5*(sel=='left' and -1 or 1)
  self:range(self.left+shift,self.right+shift);return
 elseif sel=='all' then self:range(self.first,self.last);return
 elseif sel=='restore' then pd.send(self.slot..'-sample-edit','restore',{});return
 elseif sel=='stop' then pd.send(self.player..'-stop_button','bang',{});return
 end
 if not self:valid() then self:status('Selection needs four frames within the usable sample');return end
 if sel=='selection' then self:range(self.a,self.b)
 elseif sel=='trim' then pd.send(self.slot..'-sample-edit','trim',{self.a/self.rate,self.b/self.rate})
 elseif sel=='loop' or sel=='audition' then
  pd.send(self.player..'-loop-region-request','list',{self.a/self.rate,self.b/self.rate})
  if sel=='audition' and (not self.playing or self.paused) then pd.send(self.player..'-play_button','bang',{}) end
  self:status('Player '..self.track..' loops the selection; Stop ends audition')
 end
end
function C:frame(x) return math.floor(self.left+clamp((x-30)/860,0,1)*(self.right-self.left)+0.5) end
function C:mouse_down(x,y)
 if not self.ready or self.switching or y<40 or y>242 then return end
 local at=self:frame(x);self.drag=math.abs(at-self.a)<=math.abs(at-self.b) and 'start' or 'finish'
 self:mouse_drag(x,y)
end
function C:mouse_drag(x,y)
 if not self.drag or not self.ready or self.switching then return end
 local at=self:frame(x)
 if self.drag=='start' then self.a=clamp(at,self.first,self.b-4)
 else self.b=clamp(at,self.a+4,self.last) end
 self:fields();self:status('Selection staged; no audio or loop change until an action')
end
function C:mouse_up() self.drag=nil end
function C:paint(g)
 g:set_color(250,248,242);g:fill_all();g:set_color(40,61,58)
 local name=self.name or 'No sample selected'
 g:draw_text('Sample '..(self.slot or '-')..'  |  '..name,14,8,890,14)
 if not self.ready then return end
 for channel=0,1 do
  local mid=channel==0 and 95 or 195
  g:set_color(170,185,175);g:draw_line(30,mid,890,mid,1)
  g:draw_text(channel==0 and 'L' or 'R',10,mid-8,18,12)
  if self.peaks then
   g:set_color(channel==0 and 52 or 78,124,114)
   for i=0,399 do
    local low,high=self.peaks[4+i*4+channel*2],self.peaks[5+i*4+channel*2]
    local x=30+i*860/400
    g:draw_line(x,mid-clamp(high,-1,1)*42,x,mid-clamp(low,-1,1)*42,2.2)
   end
  end
 end
 g:set_color(70,95,90)
 for i=0,8 do
  local f=self.left+(self.right-self.left)*i/8;local x=30+860*i/8
  g:draw_line(x,242,x,248,1)
  g:draw_text(string.format('%.3fs',f/self.rate),math.min(832,x),253,72,11)
 end
 if not self.peaks then g:draw_text('Building detail...',32,274,200,11) end
end
function C:paint_layer_2(g)
 if not self.ready then return end
 local function x(f) return 30+860*clamp((f-self.left)/(self.right-self.left),0,1) end
 local a,b=x(self.a),x(self.b)
 if b>a then g:set_color(183,94,73,0.15);g:fill_rect(a,40,b-a,202) end
 g:set_color(183,94,73)
 for _,f in ipairs({self.a,self.b}) do
  if f>=self.left and f<=self.right then g:fill_rect(x(f)-2,40,4,202);g:fill_rect(x(f)-5,32,10,10) end
 end
end
function C:paint_layer_3(g)
 if not self.ready or not finite(self.position) or self.position<self.left or self.position>self.right then return end
 local x=30+860*(self.position-self.left)/(self.right-self.left)
 g:set_color(40,61,58);g:draw_line(x,44,x,240,2)
end
