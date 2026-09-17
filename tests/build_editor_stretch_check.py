"""Native integration fixture: production editor/players, isolated IDs, no DAC.
Run bang starts an 8s capture with independent 10s stop. No live session changes.
"""
from pathlib import Path
import hashlib, json, re, shutil, sys, wave, struct, math
ROOT=Path(__file__).resolve().parents[1]
OUT=Path('/tmp/plugmlr-editor-handoff');OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'tests'))
from check_patch_connections import check
changed=['sample-editor','sample-stretch','buffer-view-data']
prefix='stretch'+hashlib.sha256(b''.join((ROOT/(n+'.pd_lua')).read_bytes() for n in changed)).hexdigest()[:8]+'-'
for path in ROOT.iterdir():
 if path.suffix not in ('.pd','.pd_lua','.lua'):continue
 text=path.read_text()
 if path.name=='buffer-selection.pd':text=text.replace('$f2 <= 16','$f2 <= 916')
 if path.name=='sample-stretch.pd_lua':text=text.replace('for slot=16,1,-1','for slot=916,901,-1')
 for n in changed:
  text=text.replace("register('"+n+"')","register('"+prefix+n+"')")
  text=re.sub(r'(?m)^(#X obj \S+ \S+ )'+re.escape(n)+r'(?= |;)',r'\g<1>'+prefix+n,text)
 dest=OUT/(prefix+path.name if path.stem in changed else path.name);dest.write_text(text)
(OUT/'scripts').mkdir(exist_ok=True);shutil.copy2(ROOT/'scripts/render_sample.py',OUT/'scripts/render_sample.py')
with wave.open(str(OUT/'source.wav'),'wb') as w:
 w.setnchannels(2);w.setsampwidth(2);w.setframerate(48000)
 w.writeframes(b''.join(struct.pack('<hh',int(3200*math.sin(2*math.pi*220*i/48000)),int(6400*math.sin(2*math.pi*330*i/48000))) for i in range(192000)))
objects=[];edges=[]
def o(s):objects.append('#X '+s+';');return len(objects)-1
def c(a,b,ao=0,bi=0):edges.append(f'#X connect {a} {ao} {b} {bi};')
o('text 20 10 Production sample editor test / isolated slots 901–916 / NO DAC / automatic 8s stop')
for slot in range(901,917):o(f'obj {20+(slot-901)%8*130} {60+(slot-901)//8*40} sample-data {slot}')
for slot in range(901,917):
 o(f'obj 20 {140+(slot-901)*40} sample_player_rebuild {slot}')
 o(f'obj 400 {140+(slot-901)*40} {prefix}buffer-view-data live {slot}')
 o(f'obj 650 {140+(slot-901)*40} array define 0-live_buffer_{slot} 4');o(f'obj 950 {140+(slot-901)*40} array define 1-live_buffer_{slot} 4')
rec=o('obj 20 360 writesf~ 4')
for j,slot in enumerate([901,902]):
 m=o(f'obj {20+j*250} 290 mixer {slot}');c(m,rec,0,2*j);c(m,rec,1,2*j+1)
b=o('obj 20 230 bng 25 250 50 0 empty empty RUN 30 12 0 14 #faf8f2 #347c72 #283d3a')
t=o('obj 20 420 t b b b');c(b,t)
run=o('obj 850 430 r editor-stretch-run');c(run,t)
auto=o('obj 850 550 loadbang');wait=o('obj 850 580 delay 1000');c(auto,wait);c(wait,t)
fallback=o('obj 650 430 delay 10000');c(t,fallback,2)
msg=o(f'msg 300 420 open -bytes 4 {OUT}/capture.wav \\, start');c(t,msg,1);c(msg,rec)
q=o('obj 20 520 qlist');m=o(f'msg 20 470 read {OUT}/score.txt \\, bang');c(t,m);c(m,q)
r=o('obj 650 390 r editor-stretch-stop');stop=o('msg 650 470 stop');c(r,stop);c(fallback,stop);c(stop,rec);c(stop,fallback)
done=o('obj 650 510 print editor-stretch-capture-stopped');c(stop,done)
# Open the existing editor via its public internal request, exposed only in fixture.
s=(OUT/'sample_player_rebuild.pd').read_text();depth=count=0
for line in s.splitlines():
 if line.startswith('#N canvas'):depth+=1
 elif line.startswith('#X restore'):
  depth-=1
  if depth==1:count+=1
 elif depth==1 and line.startswith(('#X obj ','#X msg ','#X text ','#X floatatom ','#X symbolatom ')):count+=1
s+=f'\n#X obj 2900 5100 r stretch-open-\\$1;\n#X obj 2900 5140 s \\$0-open-sample-editor;\n#X connect {count} 0 {count+1} 0;\n'
(OUT/'sample_player_rebuild.pd').write_text(s)
# Commands enter the very same editor command bus as the UI buttons.
s=(OUT/'sample-editor-panel.pd').read_text();count=sum(l.startswith(('#X obj ','#X msg ','#X text ','#X floatatom ')) for l in s.splitlines())
s+=f'\n#X obj 100 2100 r stretch-test-\\$2;\n#X obj 100 2140 s \\$0-stretch-command;\n#X connect {count} 0 {count+1} 0;\n';(OUT/'sample-editor-panel.pd').write_text(s)
(OUT/'check.pd').write_text('#N canvas 100 80 1150 620 12;\n'+'\n'.join(objects+edges)+'\n')
events=[(0,'901-sample-path',f'symbol {OUT}/source.wav'),(30,'902-sample-path',f'symbol {OUT}/source.wav'),(80,'901-buffer-select','sample 901'),(80,'902-buffer-select','sample 902'),(120,'audio-901-out','0.4'),(120,'audio-902-out','0.4'),(150,'901-press_play','bang'),(150,'902-press_play','bang'),(250,'stretch-open-901','bang'),(300,'901-sample-editor','start 0.5'),(300,'901-sample-editor','finish 1.5'),(400,'stretch-test-901','ratio 2'),(400,'stretch-test-901','pitch 12'),(500,'stretch-test-901','render'),(3000,'stretch-test-901','load'),(3400,'901-sample-editor','audition'),(4200,'stretch-test-901','load'),(4800,'stretch-test-901','load'),(5400,'stretch-test-901','load'),(6000,'stretch-test-901','load'),(6600,'stretch-test-901','load'),(7600,'901-sample-editor','stop'),(7600,'902-sample-editor','stop'),(8000,'editor-stretch-stop','bang')]
events.sort(key=lambda e:e[0])
last=0;score=[]
for time,receiver,message in events:score.append(f'{time-last} {receiver} {message};');last=time
(OUT/'score.txt').write_text('\n'.join(score)+'\n')
for file in ['check.pd','sample-editor-panel.pd','sample_player_rebuild.pd']:assert not check(OUT/file)['errors'],check(OUT/file)
(OUT/'manifest.json').write_text(json.dumps(dict(prefix=prefix,changes='Unique Lua names, 16 original players and sample owners IDs901–916, six imports with multiple listeners, public command probes, no DAC, bounded capture',production={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*(ROOT/(n+'.pd_lua') for n in changed),ROOT/'sample-editor-panel.pd',ROOT/'scripts/render_sample.py']}),indent=2))
print(OUT/'check.pd')
