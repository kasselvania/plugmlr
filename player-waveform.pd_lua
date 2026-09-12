-- Receive-only stereo view. Content peaks belong to the buffer; cursor/loop to the player.
local C=pd.Class:new():register('player-waveform')
local function finite(x) return type(x)=='number' and x==x and math.abs(x)<math.huge end
local function clamp(x) return math.max(0,math.min(1,x)) end
function C:initialize(_,a)
    self.player,self.track=string.format('%d',a[1]),string.format('%d',a[2])
    self.reply=self.player..'-waveform-reply';self.inlets,self.outlets=0,0
    self:set_size(640,130)
    self.position,self.loopstart,self.loopend,self.first,self.last=0,0,0,0,0
    self.ready,self.show,self.dirty=0,false,true
    self.name,self.status='Select a buffer','Empty'
    self.receivers={};return true
end
function C:postinitialize()
    local function bind(name,fn)
        local method='receive_'..(#self.receivers+1);self[method]=fn
        self.receivers[#self.receivers+1]=pd.Receive:new():register(self,name,method)
    end
    bind(self.player..'-wave-visible',function(s,_,a) s:in_1_float(a[1]) end)
    bind(self.player..'-buffer_ID',function(s,_,a) s:select(a[1]) end)
    bind(self.reply,function(s,sel,a) s:reply_message(sel,a) end)
    bind(self.player..'-is_playing_flag',function(s,_,a)
        s.playing=a[1]~=0
        if s.show and not s.playing then s:repaint(3) end
    end)
    bind(self.player..'-playbar_data_i',function(s,_,a) s:position_report(a[1]) end)
    bind(self.player..'-set_active_loop_start',function(s,_,a) if finite(a[1]) then s.loopstart=a[1];s:overlay() end end)
    bind(self.player..'-set_active_loop_end',function(s,_,a) if finite(a[1]) then s.loopend=a[1];s:overlay() end end)
    bind(self.player..'-buffer-switching',function(s,_,a) s.switching=a[1]~=0;s:overlay() end)
end
function C:finalize()
    if self.changed then self.changed:destruct() end
    for _,r in ipairs(self.receivers) do r:destruct() end
end
function C:select(key)
    if self.key then pd.send(self.key..'-view-get','cancel',{self.reply}) end
    if type(key)~='string' then return end
    if self.changed then self.changed:destruct() end
    self.key,self.peaks,self.name,self.ready=key,nil,'Loading...',0
    self.changed=pd.Receive:new():register(self,key..'-view-changed','refresh')
    self:refresh();self:repaint()
end
function C:refresh()
    if self.key then pd.send(self.key..'-view-get',self.show and 'peaks' or 'info',{self.reply}) end
end
function C:reply_message(sel,a)
    if sel=='info' then
        self.kind,self.slot,self.ready,self.rate,self.first,self.last,self.name,self.status=table.unpack(a)
        if self.ready~=1 or self.status=='Recording' then self.peaks=nil end
        if self.show then self:repaint() end
    elseif sel=='peaks' and a[1]==self.key and a[2]==self.first and a[3]==self.last then
        self.peaks=a;if self.show then self:repaint(1) end
    end
end
function C:in_1_float(x)
    self.show=x~=0
    if self.show then self:refresh();self:repaint()
    elseif self.key then pd.send(self.key..'-view-get','cancel',{self.reply}) end
end
function C:overlay() if self.show then self:repaint(2) end end
function C:position_report(value)
    if not finite(value) then return end
    self.position=clamp(value)
    -- Reuse the original 20 ms playbar feed. No independent GUI clock.
    self.report=(self.report or 0)+1
    local pixel=math.floor(self.position*608)
    if self.show and (not self.playing or self.report%2==0) and pixel~=self.pixel then
        self.pixel=pixel;self:repaint(3)
    end
end
function C:paint(g)
    g:set_color(250,248,242);g:fill_all()
    g:set_color(40,61,58)
    local name=self.name or 'Empty'
    if #name>68 then name=name:sub(1,32)..'...'..name:sub(-32) end
    g:draw_text((self.kind=='live' and 'Live ' or 'Sample ')..(self.slot and string.format('%d',self.slot) or '')..'  |  '..name,12,6,618,12)
    local duration=(self.rate or 0)>0 and math.max(0,self.last-self.first)/self.rate or 0
    local label=string.format('%.3f s  |  %s',duration,self.status)
    if self.ready==1 and not self.peaks then label=label..'  |  Building waveform...' end
    if self.status=='Recording' then label='Recording - waveform available after Finish' end
    g:draw_text(label,12,25,618,11)
    for channel=0,1 do
        local mid=channel==0 and 65 or 101
        g:set_color(210,217,207);g:draw_line(24,mid,632,mid,1)
        g:set_color(90,111,106);g:draw_text(channel==0 and 'L' or 'R',8,mid-7,14,10)
        if self.peaks then
            g:set_color(channel==0 and 52 or 78,124,114)
            for i=0,399 do
                local low,high=self.peaks[4+i*4+channel*2],self.peaks[5+i*4+channel*2]
                local x=24+i*608/400
                g:draw_line(x,mid-math.max(-1,math.min(1,high))*16,x,mid-math.max(-1,math.min(1,low))*16,1.6)
            end
        end
    end
end
function C:paint_layer_2(g)
    if self.ready~=1 or self.switching then return end
    local length=self.last-self.first
    if length<=0 then return end
    local a,b=clamp((self.loopstart-self.first)/length),clamp((self.loopend-self.first)/length)
    if b>a and (a>0.000001 or b<0.999999) then
        g:set_color(183,94,73,0.18);g:fill_rect(24+608*a,44,608*(b-a),73)
        g:set_color(183,94,73);g:draw_line(24+608*a,44,24+608*a,117,2);g:draw_line(24+608*b,44,24+608*b,117,2)
    end
    g:set_color(110,129,120,0.45)
    for i=0,16 do g:draw_line(24+608*i/16,44,24+608*i/16,117,1) end
    g:set_color(80,99,91)
    for i=0,15 do g:draw_text(tostring(i+1),26+608*i/16,117,35,9) end
end
function C:paint_layer_3(g)
    if self.ready~=1 or self.switching then return end
    local x=24+608*self.position
    g:set_color(183,94,73);g:draw_line(x,44,x,117,2)
end
