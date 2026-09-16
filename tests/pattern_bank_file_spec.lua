local F=dofile('pattern-bank-file.lua')
local function bank()
 local b={};for i=1,8 do b[i]={state='empty',length=0,events={},initial={},participants={}} end
 b[1]={state='playing',length=1234.567890123,events={{0,1,'cut',0},{250.123456789,2,'direction',1},{250.123456789,2,'speed',4},{1200,1,'transport',2}},initial={[1]={0,2},[2]={1,4}},participants={[1]=true,[2]=true}}
 return b
end
local b=bank();local text=F.encode(b);local loaded=assert(F.decode(text))
assert(F.encode(loaded)==text and loaded[1].state=='stopped' and loaded[8].state=='empty')
assert(loaded[1].events[2][1]==b[1].events[2][1] and loaded[1].length==b[1].length)
local bad={text:gsub('bank 1','bank 2',1), text:sub(1,-6),text..'extra\n',text:gsub('slot 2','slot 1',1),text:gsub('slot 1 [^\n]+','slot 1 1 2 4',1),text:gsub('slot 1 [^\n]+','slot 1 300001 2 4',1),text:gsub('slot 1 [^\n]+','slot 1 2000 2 4097',1),text:gsub('event 0 1 cut 0','event nan 1 cut 0',1),text:gsub('event 0 1 cut 0','event inf 1 cut 0',1),text:gsub('event 0 1 cut 0','event 0 7 cut 0',1),text:gsub('event 0 1 cut 0','event 0 1 cut 16',1),text:gsub('event 0 1 cut 0','event 0 1 exec 0',1),text:gsub('event 1200','event 2400',1),text:gsub('event 1200','event 1',1),text:gsub('state 2 1 4','state 1 1 4',1),text:gsub('state 2 1 4','state 3 1 4',1),text:gsub('state 2 1 4','state 2 1 5',1),'return os.execute("false")',string.rep('a',F.MAX_BYTES+1)}
for i,v in ipairs(bad) do assert(not F.decode(v),'accepted malformed case '..i) end
-- Eight maximum-sized slots remain within the bounded text format.
for i=1,8 do
 b[i]={length=300000,events={},initial={[6]={1,0}},participants={[6]=true}}
 for n=1,4096 do b[i].events[n]={n*300000/4096,6,'cut',n%16} end
end
local max=F.encode(b);assert(#max<F.MAX_BYTES);assert(#assert(F.decode(max))[8].events==4096)
local path='/tmp/plugmlr-pattern bank ü test.plugmlr-patterns'
assert(F.write(path,bank()));local read=assert(F.read(path));assert(F.encode(read)==text)
local rename=os.rename;os.rename=function()return nil,'injected rename failure'end
assert(not F.write(path,b));os.rename=rename
assert(F.encode(assert(F.read(path)))==text,'failed replace changed destination')
assert(not F.read('/tmp/no-such-plugmlr-pattern-file'))
assert(not F.write('/tmp/no-such-plugmlr-pattern-directory/bank',b))
os.remove(path)
print('PASS lossless all-slot round trip, bounded maximum, malformed/truncated/version rejection, Unicode path and failed replacement preservation')
