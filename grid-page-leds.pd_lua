-- One receive-only renderer for the active Grid page. No musical commands.
local C=pd.Class:new():register('grid-page-leds')
local fields={'position','playing','paused','ready','switching','first','last','loop-start','loop-end','direction','speed'}
local function finite(v) return type(v)=='number' and v==v and math.abs(v)<math.huge end
function C:initialize(_,args)
    self.inlets,self.outlets=1,1
    self.page,self.focus,self.connected,self.alt,self.mod='cut',1,false,0,0
    self.rows,self.frames,self.receivers={},{},{}
    self.patterns,self.recording,self.flash={},nil,false
    for i=1,8 do self.patterns[i]='empty' end
    -- Optional bus prefix allows isolated native fixtures, without a device session.
    self.prefix=type(args[1])=='number' and string.format('%g',args[1]) or (args[1] or '')
    for row=1,6 do self.rows[row]={} end
    return true
end
function C:postinitialize()
    self.blink=pd.Clock:new():register(self,'blink_pattern')
    for row=1,6 do
        for _,field in ipairs(fields) do
            local method='state_'..row..'_'..field
            self[method]=function(s,sel,a)
                if (sel=='float' or sel=='list') and #a==1 and finite(a[1]) then
                    s.rows[row][field]=a[1];s:render()
                end
            end
            self.receivers[#self.receivers+1]=pd.Receive:new():register(self,self.prefix..row..'-grid-'..field,method)
        end
    end
end
function C:in_1(sel,a)
    if sel=='pattern' then
        local i,v=a[1],a[2]
        if #a~=2 or not finite(i) or i%1~=0 or i<1 or i>8 then return end
        if v~='empty' and v~='recording' and v~='playing' and v~='stopped' then return end
        if self.patterns[i]~=v then
            self.patterns[i]=v
            if v=='recording' then
                self.recording=i;self.flash=true;self.blink:unset()
                if self.connected then self.blink:delay(200) end
            elseif self.recording==i then self.recording=nil;self.blink:unset() end
        end
        self:render();return
    end
    if #a~=1 then return end
    local v=a[1]
    if sel=='page' and (v=='cut' or v=='play') then self.page=v
    elseif sel=='focus' and finite(v) and v%1==0 and v>=1 and v<=6 then self.focus=v
    elseif sel=='connected' and (v==0 or v==1) then
        self.connected=v==1;self.frames={};self.blink:unset()
        if self.connected and self.recording~=nil then self.blink:delay(200) end
    elseif (sel=='alt' or sel=='mod') and (v==0 or v==1) then self[sel]=v
    else return end
    self:render()
end
function C:blink_pattern()
    if not self.connected or self.recording==nil then return end
    self.flash=not self.flash;self:render();self.blink:delay(200)
end
local function blank() local r={};for i=1,16 do r[i]=0 end;return r end
local function cuts(s)
    local r=blank()
    if not s.ready or s.ready==0 or s.switching==1 then return r end
    local first,last=s.first or 0,s.last or 0
    local a,b=s['loop-start'] or first,s['loop-end'] or last
    local length=last-first
    local region=length>0 and a>=first and b<=last and b-a>=1 and (a>first or b<last)
    for x=0,15 do
        local overlap=math.min(b,first+length*(x+1)/16)-math.max(a,first+length*x/16)
        if region and overlap>0.5 then r[x+1]=4 end
    end
    if s.playing==1 and s.paused~=1 and s.position and s.position>=0 and s.position<=1 then
        r[math.min(15,math.floor(s.position*16))+1]=12
    end
    return r
end
function C:row(y,r)
    local sig=table.concat(r,',')
    if self.frames[y]==sig then return end
    self.frames[y]=sig
    local a={0,y};for _,v in ipairs(r) do a[#a+1]=v end
    self:outlet(1,'/monome/grid/led/level/row',a)
end
function C:render()
    if not self.connected then return end
    local nav=blank()
    nav[1]=self.page=='play' and 12 or 4;nav[2]=self.page=='cut' and 12 or 4
    nav[14]=self.mod==1 and 15 or 4;nav[16]=self.alt==1 and 15 or 4
    for i=1,8 do
        nav[i+4]=({empty=2,recording=self.flash and 15 or 2,playing=10,stopped=5})[self.patterns[i]]
    end
    self:row(0,nav)
    for row=1,6 do
        local s=self.rows[row]
        if self.page=='cut' then self:row(row,cuts(s))
        else
            local r=blank()
            for x=3,6 do r[x]=self.focus==row and 10 or 3 end
            r[8]=s.direction==1 and 12 or (s.direction==0 and 3 or 0)
            for i=0,4 do r[10+i]=s.speed==i and 12 or 3 end
            if s.ready==1 and s.switching~=1 then
                r[16]=s.playing==1 and s.paused~=1 and 12 or (s.paused==1 and 7 or 3)
            end
            self:row(row,r)
        end
    end
    self:row(7,self.page=='play' and cuts(self.rows[self.focus]) or blank())
end
