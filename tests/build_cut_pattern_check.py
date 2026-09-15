"""Finite native pattern + two-original-player check. No DAC, device or recording.
Open /tmp/plugmlr-cut-pattern/check.pd; starts automatically and stops after 9s.
"""
from pathlib import Path
import runpy,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];OUT=Path('/tmp/plugmlr-cut-pattern');OUT.mkdir(exist_ok=True)
b=runpy.run_path(str(ROOT/'tests/build_sample_editor_check.py'));Patch=b['Patch'];count=b['root_count'];check=b['check']
for f in b['OUT'].iterdir():
 if f.suffix in ('.pd','.pd_lua','.lua','.wav'):(OUT/f.name).write_bytes(f.read_bytes())
# Reuse the original player fixture's isolated slots, passive probes and stop control.
f=OUT/'sample_player_rebuild.pd';f.write_text(f.read_text().replace('r ppq;','r pcheck-ppq;'))
f=OUT/'pattern-player.pd';s=f.read_text().replace('mlr-pattern-cut','pcheck-cut').replace('list prepend \\$2;','list prepend;')
s+='\n#X obj 20 350 loadbang;\n#X obj 20 390 f \\$2;\n#X obj 20 430 - 900;\n#X connect 13 0 14 0;\n#X connect 14 0 15 0;\n#X connect 15 0 2 1;\n';f.write_text(s)
names=['cut-pattern','grid-cut-keys','grid-page-leds'];prefix='pc'+hashlib.sha256(b''.join((ROOT/(n+'.pd_lua')).read_bytes() for n in names)).hexdigest()[:8]+'-'
for n in names:(OUT/(prefix+n+'.pd_lua')).write_text((ROOT/(n+'.pd_lua')).read_text().replace("register('"+n+"')","register('"+prefix+n+"')"))
s=(ROOT/'grid-cut-control.pd').read_text()
for n in names:s=s.replace(n+';',prefix+n+(' 90;' if n=='grid-page-leds' else ';'))
s=s.replace('mlr-pattern-cut','pcheck-cut').replace('mlr-grid-','pcheck-').replace('s monome_in;','s pcheck-led;').replace('makefilename %d-','makefilename 90%d-').replace('mlr-close-views','pcheck-close-views').replace('r pd;','r pcheck-pd;')
p=Patch(count(s));o,c=p.add,p.wire
for src,out,label in [(32,0,'replay'),(32,1,'status'),(2,8,'button'),(2,0,'key-cut')]:
 t=o(f'obj 20 {900+len(p.objects)*30} list prepend {label}');r=o('obj 250 920 s pcheck-log');c(src,t,out);c(t,r)
r=o('obj 450 900 r pcheck-command');c(r,32)
(OUT/'pattern-control.pd').write_text(s+'\n'+p.text())
p=Patch();o,c=p.add,p.wire
o('text 20 15 Pattern check - two isolated players - no DAC or recording - 9 second stop')
lb=o('obj 20 55 loadbang');d=o('obj 20 95 delay 1000');tr=o('obj 20 135 t b b b');c(lb,d);c(d,tr)
clock=o('obj 950 100 timer');c(tr,clock,2)
log=o('obj 900 380 text define \\$0-events');clear=o('msg 350 175 clear');c(tr,clear,1);c(clear,log)
q=o('obj 20 220 qlist');m=o(f'msg 20 180 read {OUT}/score.txt \\, bang');c(tr,m);c(m,q)
for i in (901,902):
 o(f'obj {20+(i-901)*350} 260 sample-data {i}');o(f'obj {20+(i-901)*350} 300 sample_player_rebuild {i}')
 for ch in (0,1):o(f'obj {20+(i-901)*350} {340+ch*35} array define {ch}-live_buffer_{i} 4')
 o(f'obj {20+(i-901)*350} 420 {b["prefix"]}buffer-view-data live {i}')
r=o('obj 20 500 r pcheck-input');ctl=o('obj 20 540 pattern-control');c(r,ctl)
u=o('obj 20 580 unpack f f f');dest=o('obj 180 620 makefilename row_90%d');send=o('obj 20 660 send');c(ctl,u);c(u,dest,1);c(dest,send,0,1);c(u,send)
for bus,label in [('pcheck-cut','accepted'),('pcheck-led','led')]:
 r=o('obj 550 500 r '+bus);t=o('obj 550 540 list prepend '+label);s=o('obj 550 580 s pcheck-log');c(r,t);c(t,s)
r=o('obj 900 55 r pcheck-log');order=o('obj 900 140 t l b');tag=o('obj 900 185 list prepend');ins=o('obj 900 230 text insert \\$0-events 1e+09');c(r,order);c(order,clock,1,1);c(clock,tag,0,1);c(order,tag);c(tag,ins)
r=o('obj 900 430 r pcheck-finish');stop=o('obj 900 470 t b b');c(r,stop)
watch=o('obj 700 140 delay 9000');c(tr,watch,2);c(watch,stop)
unset=o('msg 700 185 stop');rewind=o('msg 700 230 rewind');c(stop,unset,1);c(unset,watch);c(stop,rewind,1);c(rewind,q)
m=o('msg 1050 510 \\; pcheck-command stop \\; editor-test-901 stop \\; editor-test-902 stop \\; pcheck-connected 0');c(stop,m,1)
w=o(f'msg 900 550 write {OUT}/events.txt');c(stop,w);c(w,log);done=o('obj 900 590 print pattern-check-done');c(stop,done)
(OUT/'check.pd').write_text('#N canvas 100 80 1200 800 12;\n'+p.text())
score=[]
def at(t,r,m):score.append((t,r,m))
def tap(t,x,y):at(t,'pcheck-input',f'{x} {y} 1');at(t+1,'pcheck-input',f'{x} {y} 0')
at(0,'901-sample-path',f'symbol {OUT}/source.wav');at(30,'902-sample-path',f'symbol {OUT}/source.wav')
at(80,'901-buffer-select','sample 901');at(80,'902-buffer-select','sample 901');at(100,'pcheck-connected','1')
# Arm/cancel, MOD suppression, duplicate down, clear, malformed event.
tap(150,4,0);tap(170,4,0);at(180,'pcheck-input','13 0 1');tap(190,4,0);at(200,'pcheck-input','13 0 0')
tap(220,4,0);at(220.5,'pcheck-input','4 0 1');at(230,'pcheck-cut','0 99')
# Record quantized latest-wins Track 1 and free Track 2, first commit at 400.
at(250,'901-quantizer','0');at(250,'902-quantizer','1')
tap(300,2,1);tap(330,4,1);at(400,'pcheck-ppq','0');tap(500,7,2);tap(580,10,1);at(700,'pcheck-ppq','4')
# Finish length 500 ms. Replay must advance even with no further ppq ticks.
tap(900,4,0)
# Switch page/focus: pattern identity remains Tracks 1/2. Screen requests address only the isolated test player numbers.
tap(1000,0,0);tap(1020,2,6)
# Stale quantized manual request must not appear at next tick after replay.
at(1050,'row_901','15');at(1500,'pcheck-ppq','8')
# Stop / silence of EVENTS, restart original phrase, clear while playing.
tap(1925,4,0);tap(2200,4,0)
at(2775,'pcheck-input','15 0 1');tap(2780,4,0);at(2790,'pcheck-input','15 0 0')
# Empty player's cut must not begin recording.
tap(2990,1,0);tap(3000,4,0);at(3010,'901-buffer-select','sample 902');at(3040,'902-buffer-select','live 902');tap(3060,7,2)
# Page back to CUT; valid first event then detach must retain stopped phrase.
tap(3100,1,0);at(3110,'901-quantizer','1');tap(3150,1,1);at(3400,'pcheck-connected','0');at(3450,'pcheck-connected','1')
at(3200,'901-quantizer','0');at(3210,'row_901','13');at(3220,'901-pattern-slice','-1');at(3250,'pcheck-ppq','12')
tap(3700,4,0);at(4000,'pcheck-pd','dsp 0');at(4010,'pcheck-pd','dsp 1')
# Single-event minimum duration and explicit stop clear cancellation (no real players).
at(4300,'pcheck-command','clear');at(4300,'pcheck-command','toggle');at(4300,'pcheck-cut','6 3');at(4300,'pcheck-command','toggle');at(4325,'pcheck-command','stop');at(4350,'pcheck-command','clear')
# Timing/stress on component input, using Track 6 (no instantiated player).
at(4500,'pcheck-command','toggle')
for i in range(12):at(4510+i*7,'pcheck-cut',f'6 {i}')
at(4630,'pcheck-command','toggle');at(5001,'pcheck-command','stop');at(5010,'pcheck-command','clear')
at(5200,'pcheck-finish','bang')
last=0;lines=[]
for t,r,m in sorted(score,key=lambda v:v[0]):lines.append(f'{t-last} {r} {m};');last=t
(OUT/'score.txt').write_text('\n'.join(lines)+'\n')
for f in ['check.pd','pattern-control.pd','sample_player_rebuild.pd','pattern-player.pd']:assert not check(OUT/f)['errors'],check(OUT/f)
manifest=dict(base='06e8bc64787fcbb4df46837eed37677edddad1c7',production_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in ROOT.iterdir() if f.suffix in ('.pd','.pd_lua')},fixture_changes='Cached Lua class isolation; players/slots 901/902 and capture/replay track mapping; private ppq/Grid/pattern/LED buses; isolated test-player screen addresses; passive accepted-cut probes. No DAC, writesf, device or global DSP command.',fixture_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in OUT.iterdir() if f.suffix in ('.pd','.pd_lua','.wav','.txt')})
(OUT/'source.json').write_text(json.dumps(manifest,indent=2)+'\n');print(OUT/'check.pd')
