"""Isolated original players 901/902, original mixers, no DAC. 10s hard auto-stop.
Only the test selection validator allows slots 901/902; production limit stays 16.
Open /tmp/plugmlr-sample-editor/check.pd. Console: editor-check-run bang.
"""
from pathlib import Path
import sys, json, hashlib, math, struct, wave
ROOT=Path(__file__).resolve().parents[1]; OUT=Path('/tmp/plugmlr-sample-editor');OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'tests'))
from check_patch_connections import check
class Patch:
 def __init__(self,n=0):self.n=n;self.objects=[];self.edges=[]
 def add(self,line):self.objects.append('#X '+line+';');return self.n+len(self.objects)-1
 def wire(self,a,b,o=0,i=0):self.edges.append(f'#X connect {a} {o} {b} {i};')
 def text(self):return '\n'.join(self.objects+self.edges)+'\n'
def root_count(s):
 d=n=0
 for l in s.splitlines():
  if l.startswith('#N canvas'):d+=1
  elif l.startswith('#X restore'):
   d-=1
   if d==1:n+=1
  elif d==1 and l.startswith(('#X obj ','#X msg ','#X text ','#X floatatom ','#X symbolatom ')):n+=1
 return n
for f in ROOT.iterdir():
 if f.suffix in ('.pd','.pd_lua','.lua'):
  (OUT/f.name).write_bytes(f.read_bytes())
s=(OUT/'buffer-selection.pd').read_text();assert '$f2 <= 16' in s
(OUT/'buffer-selection.pd').write_text(s.replace('$f2 <= 16','$f2 <= 902'))
s=(ROOT/'sample_player_rebuild.pd').read_text();p=Patch(root_count(s));o,c=p.add,p.wire
r=o('obj 2700 4600 r editor-test-\\$1');route=o('obj 2700 4640 route stop reverse editor');c(r,route)
for k,suffix in enumerate(['stop_button','dir_change','open-sample-editor']):
 q=o(f'obj {2700+180*k} 4680 s \\$0-{suffix}');c(route,q,k)
for j,suffix in enumerate(['play-position-frames','first_index','last_index','set_active_loop_start','set_active_loop_end','slice_size_val','playback_direction','key_press_pos','buffer-ready','is_playing_flag']):
 r=o(f'obj {2700+j*100} 4800 r \\$0-{suffix}');tag=o(f'obj {2700+j*100} 4840 list prepend \\$1-{suffix}');send=o(f'obj {2700+j*100} 4880 s editor-check-log');c(r,tag);c(tag,send)
(OUT/'sample_player_rebuild.pd').write_text(s+'\n'+p.text())
# Test tone identifies wrong source segments and swapped channels unambiguously.
vals=[]
for i in range(4*44100):
 t=i/44100;freq=220 if t<1 else (440 if t<2 else 880)
 vals.extend((int(6000*math.sin(2*math.pi*freq*t)),int(3000*math.sin(2*math.pi*(freq*1.5)*t))))
with wave.open(str(OUT/'source.wav'),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(44100);w.writeframes(struct.pack('<'+'h'*len(vals),*vals))
p=Patch();o,c=p.add,p.wire
o('text 20 10 Sample editor check - isolated slots 901/902 - no speaker output - 10s auto-stop')
for i in (901,902):
 o(f'obj 700 {60+(i-901)*100} array define 0-live_buffer_{i} 4');o(f'obj 700 {90+(i-901)*100} array define 1-live_buffer_{i} 4');o(f'obj 700 {120+(i-901)*100} buffer-view-data live {i}')
 o(f'obj {20+(i-901)*300} 60 sample-data {i}');o(f'obj {20+(i-901)*300} 100 sample_player_rebuild {i}')
rec=o('obj 20 330 writesf~ 8')
for j,t in enumerate((901,902)):
 mix=o(f'obj {20+j*300} 170 mixer {t}');c(mix,rec,0,j*2);c(mix,rec,1,j*2+1)
 sig=o(f'obj {20+j*300} 220 r~ {t}-voice_audio');split=o(f'obj {20+j*300} 255 snake~ out 2');c(sig,split);c(split,rec,0,4+j*2);c(split,rec,1,5+j*2)
run=o('obj 20 380 r editor-check-run');tr=o('obj 20 420 t b b b b');c(run,tr)
watch=o('obj 550 450 delay 10000');c(tr,watch,3)
log=o('obj 700 550 text define \\$0-events');clear=o('msg 700 420 clear');c(tr,clear,2);c(clear,log)
op=o(f'msg 300 420 open -bytes 4 {OUT}/capture.wav \\, start');c(tr,op,1);c(op,rec)
q=o('obj 20 500 qlist');m=o(f'msg 20 460 read {OUT}/score.txt \\, bang');c(tr,m);c(m,q)
stoprecv=o('obj 550 380 r editor-check-stop');stop=o('obj 550 500 t b b b b');c(stoprecv,stop);c(watch,stop)
msg=o('msg 550 540 stop');c(stop,msg,3);c(msg,rec);c(msg,watch)
m=o('msg 450 580 rewind');c(stop,m,2);c(m,q)
m=o('msg 350 620 \\; editor-test-901 stop \\; editor-test-902 stop');c(stop,m,1)
m=o(f'msg 700 620 write {OUT}/events.txt');c(stop,m);c(m,log)
done=o('obj 550 660 print editor-check-stopped');c(stop,done)
r=o('obj 700 380 r editor-check-log');ins=o('obj 700 470 text insert \\$0-events 1e+09');order=o('obj 1050 380 t l b');clock=o('obj 1050 420 timer');tag=o('obj 1050 460 list prepend');c(tr,clock,3);c(r,order);c(order,clock,1,1);c(clock,tag,0,1);c(order,tag);c(tag,ins)
r=o('obj 850 380 r s_b_buffer_states');route=o('obj 850 420 route 901 902');c(r,route)
for i in range(2):
 tag=o(f'obj {850+i*150} 470 list prepend metadata-{901+i}');send=o(f'obj {850+i*150} 510 s editor-check-log');c(route,tag,i);c(tag,send)
# Export original RAM to verify trim never changed storage.
r=o('obj 900 580 r editor-check-export');sf=o('obj 900 620 soundfiler');c(r,sf)
(OUT/'check.pd').write_text('#N canvas 100 80 1100 760 12;\n'+p.text())
score=[]
def at(t,r,m='bang'):score.append((t,r,m))
at(0,'901-sample-path',f'symbol {OUT}/source.wav');at(40,'902-sample-path',f'symbol {OUT}/source.wav')
at(100,'901-buffer-select','sample 901');at(100,'902-buffer-select','sample 901')
at(130,'audio-901-out','0.4');at(130,'audio-902-out','0.3')
at(200,'901-press_play');at(200,'902-press_play')
at(1000,'901-sample-edit','trim 1 2')
at(1100,'901-press_play');at(1100,'902-press_play')
at(1500,'row_901','0');at(1900,'row_901','15')
at(2300,'editor-test-901','reverse');at(2400,'row_901','0');at(2800,'row_901','15')
at(3100,'901-sample-edit','trim 1.5 1.4') # invalid, no changes
at(3300,'901-sample-edit','restore')
at(3400,'901-press_play');at(3400,'902-press_play')
at(3900,'901-sample-edit','trim 1 2');at(3905,'901-sample-path',f'symbol {OUT}/source.wav') # cancel pending trim
at(4000,'901-press_play');at(4000,'902-press_play')
at(4400,'902-buffer-select','sample 902')
at(4800,'902-buffer-select','sample 901')
at(4600,'901-sample-edit','trim 1 2');at(4700,'901-buffer-select','sample 902');at(4800,'901-buffer-select','sample 901')
at(4900,'901-press_play') # 902 already resumed through buffer selection
at(5400,'editor-test-901','stop');at(5400,'editor-test-902','stop')
at(5600,'editor-check-export',f'write -wave -bytes 4 -rate 44100 {OUT}/unchanged.wav 0-sample_buffer_901 1-sample_buffer_901')
at(5800,'editor-test-901','editor')
at(5900,'901-sample-editor','start 1.2');at(5900,'901-sample-editor','finish 1.8')
at(6000,'901-sample-editor','audition');at(6600,'901-sample-editor','stop')
at(7000,'901-sample-editor','selection')
at(9000,'editor-check-stop')
last=0;lines=[]
for t,r,m in sorted(score,key=lambda v:v[0]):lines.append(f'{t-last} {r} {m};');last=t
(OUT/'score.txt').write_text('\n'.join(lines)+'\n')
# Lua classes are cached across open patches. Give test copies unique class names,
# keeping the user's loaded classes/session intact and executing this exact source.
names=['sample-editor','sample-trim','buffer-view-data','player-waveform']
prefix='se'+hashlib.sha256(b''.join((ROOT/(n+'.pd_lua')).read_bytes() for n in names)).hexdigest()[:8]+'-'
for path in list(OUT.iterdir()):
 if path.suffix not in ('.pd','.pd_lua'):continue
 text=path.read_text()
 for name in names:
  text=text.replace("register('"+name+"')","register('"+prefix+name+"')")
  # Replace Pd object names only, not control symbols or sample-editor-panel.
  import re
  text=re.sub(r'(?m)^(#X obj \S+ \S+ )'+re.escape(name)+r'(?= |;)',r'\g<1>'+prefix+name,text)
 dest=OUT/(prefix+path.name) if path.stem in names else path
 dest.write_text(text)
for f in ['check.pd','sample_player_rebuild.pd','sample-editor-panel.pd','sample-data.pd']:assert not check(OUT/f)['errors'],check(OUT/f)
(OUT/'source.json').write_text(json.dumps({'base':'544f8b4d8373cdc305ce4310856e8f00cea25cd0','production_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in ROOT.iterdir() if f.suffix in ('.pd','.pd_lua')},'score':score,'lua_test_class_prefix':prefix,'fixture_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in OUT.iterdir() if f.name in ['check.pd','sample_player_rebuild.pd','buffer-selection.pd'] or f.name.startswith(prefix)},'fixture_changes':'Unique test Lua class names avoid cached user classes. Selection accepts isolated slots <=902; passive private state probes; original mixer outputs recorded without DAC; watchdog 10 seconds. Production selection limit is unchanged.'},indent=2)+'\n')
print(OUT/'check.pd')
