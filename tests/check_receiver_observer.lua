-- Exercise the actual observer and file:write varargs without a Pd runtime.
local captured
pd={Class={}}
function pd.Class:new() return setmetatable({}, {__index=self})end
function pd.Class:register() captured=self;return self end
dofile('tests/receiver_lifetime/observer.pd_lua')
local original=io.open
local file=assert(io.tmpfile())
io.open=function(_,mode)assert(mode=='a');return {write=function(_,...)file:write(...)end,close=function()file:flush()end}end
local obj=setmetatable({_loadpath='unused/',seq=0},{__index=captured})
obj:log('test',{'a',1.0,'sample_buffer_16','path with spaces.wav','', 'line\nbreak'})
io.open=original
file:seek('set',0)
local line=file:read('*a');file:close()
assert(line=='1\ttest\t61\t312e30\t73616d706c655f6275666665725f3136\t706174682077697468207370616365732e776176\t\t6c696e650a627265616b\n',line)
print('PASS: actual observer file:write varargs emit only hex fields, including native float atoms')
