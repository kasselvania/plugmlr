-- Versioned data only. Never load/execute the contents of a bank file as Lua.
local M={MAX_BYTES=4*1024*1024}
local function number(s,lo,hi,whole)
 local n=tonumber(s)
 if not n or n~=n or n<lo or n>hi or (whole and n%1~=0) then return nil end
 return n
end
local function value(kind,s)
 local max=({cut=15,direction=1,speed=4,transport=2})[kind]
 return max and number(s,0,max,true)
end
local function num(n)return string.format('%.17g',n)end
function M.encode(slots)
 local lines={'plugmlr-pattern-bank 1'}
 for i=1,8 do
  local s=slots[i];local tracks={}
  for t=1,6 do if s.participants[t] then tracks[#tracks+1]=t end end
  lines[#lines+1]=table.concat({'slot',i,num(s.length),#tracks,#s.events},' ')
  for _,t in ipairs(tracks) do lines[#lines+1]=table.concat({'state',t,s.initial[t][1],s.initial[t][2]},' ') end
  for _,e in ipairs(s.events) do lines[#lines+1]=table.concat({'event',num(e[1]),e[2],e[3],e[4]},' ') end
 end
 lines[#lines+1]='end'
 return table.concat(lines,'\n')..'\n'
end
function M.decode(text)
 if type(text)~='string' or #text>M.MAX_BYTES then return nil,'File too large' end
 local lines={}
 for line in text:gmatch('[^\r\n]+') do
  if #line>160 then return nil,'Invalid line' end
  local a={};for word in line:gmatch('%S+') do a[#a+1]=word end
  if #a>0 then lines[#lines+1]=a end
 end
 local pos=0
 local function nextline(tag,n)
  pos=pos+1;local a=lines[pos]
  if not a or a[1]~=tag or #a~=n then return nil end
  return a
 end
 local header=nextline('plugmlr-pattern-bank',2)
 if not header or header[2]~='1' then return nil,'Not a supported pattern bank' end
 local slots={}
 for i=1,8 do
  local a=nextline('slot',5)
  if not a or number(a[2],1,8,true)~=i then return nil,'Invalid slot order' end
  local length,states,count=number(a[3],0,300000),number(a[4],0,6,true),number(a[5],0,4096,true)
  if not length or not states or not count or (count==0 and (length~=0 or states~=0)) or
     (count>0 and (length<10 or states==0)) then return nil,'Invalid slot bounds' end
  local s={state=count==0 and 'empty' or 'stopped',events={},initial={},participants={},length=length}
  for _=1,states do
   a=nextline('state',4)
   if not a then return nil,'Missing starting state' end
   local t,d,v=number(a[2],1,6,true),value('direction',a[3]),value('speed',a[4])
   if not t or not d or not v or s.initial[t] then return nil,'Invalid starting state' end
   s.initial[t]={d,v}
  end
  local last=0
  for _=1,count do
   a=nextline('event',5)
   if not a then return nil,'Missing event' end
   local time,t,v=number(a[2],last,length),number(a[3],1,6,true),value(a[4],a[5])
   if not time or not t or not v or not s.initial[t] then return nil,'Invalid event' end
   last=time;s.events[#s.events+1]={time,t,a[4],v};s.participants[t]=true
  end
  for t in pairs(s.initial) do if not s.participants[t] then return nil,'Unused starting state' end end
  slots[i]=s
 end
 if not nextline('end',1) or pos~=#lines then return nil,'Incomplete or extra data' end
 return slots
end
function M.read(path)
 local f=io.open(path,'rb');if not f then return nil,'Cannot open file' end
 local text,err=f:read(M.MAX_BYTES+1);local closed=f:close()
 if not text or err or not closed then return nil,'Cannot read file' end
 return M.decode(text)
end
local sequence=0
function M.write(path,slots)
 local text=M.encode(slots)
 local valid,err=M.decode(text);if not valid then return nil,err end
 -- Unique sibling keeps rename on the destination filesystem. Never truncate it.
 sequence=sequence+1
 local tmp=path..'.plugmlr-tmp-'..os.time()..'-'..math.random(1,2147483647)..'-'..sequence
 local exists=io.open(tmp,'rb');if exists then exists:close();return nil,'Temporary file exists' end
 local f=io.open(tmp,'wb');if not f then return nil,'Cannot create file' end
 local written=f:write(text);local closed=f:close()
 if not written or not closed then os.remove(tmp);return nil,'Cannot finish file write' end
 if not os.rename(tmp,path) then os.remove(tmp);return nil,'Cannot replace destination' end
 return true
end
return M
