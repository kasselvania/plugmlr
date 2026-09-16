"""Finite native pattern + two-original-player check. No DAC, device or recording.
Open /tmp/plugmlr-performance-pattern/check.pd; starts automatically and stops after 9s.
"""
from pathlib import Path
import runpy,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];OUT=Path('/tmp/plugmlr-performance-pattern');OUT.mkdir(exist_ok=True)
b=runpy.run_path(str(ROOT/'tests/build_sample_editor_check.py'));Patch=b['Patch'];count=b['root_count'];check=b['check']
for f in b['OUT'].iterdir():
 if f.suffix in ('.pd','.pd_lua','.lua') or f.name=='source.wav':(OUT/f.name).write_bytes(f.read_bytes())
# Reuse the original player fixture's isolated slots, passive probes and stop control.
f=OUT/'sample_player_rebuild.pd';f.write_text(f.read_text().replace('r ppq;','r pcheck-ppq;'))
names=['performance-pattern','performance-player','grid-cut-keys','grid-page-leds'];prefix='pt'+hashlib.sha256(b''.join((ROOT/(n+'.pd_lua')).read_bytes() for n in names)).hexdigest()[:8]+'-'
for n in names:
 text=(ROOT/(n+'.pd_lua')).read_text().replace("register('"+n+"')","register('"+prefix+n+"')")
 if n=='performance-player':text=text.replace('a[2]','a[2]-900',1).replace('mlr-pattern-snapshot','pcheck-snapshot')
 (OUT/(prefix+n+'.pd_lua')).write_text(text)
f=OUT/'pattern-player.pd';f.write_text(f.read_text().replace('performance-player ',prefix+'performance-player ').replace('mlr-pattern-file','pcheck-file').replace('mlr-pattern-event','pcheck-event'))
# Extra passive original-player state and target-speed probes, no control rewiring.
f=OUT/'sample_player_rebuild.pd';s=f.read_text();p=Patch(count(s));o,c=p.add,p.wire
for name in ['is_paused_flag','playback_speed_dial','pattern-transport']:
 r=o('obj 20 5500 r \\$0-'+name);t=o('obj 20 5540 list prepend \\$1-'+name);v=o('obj 20 5580 s editor-check-log');c(r,t);c(t,v)
f.write_text(s+'\n'+p.text())
s=(ROOT/'grid-cut-control.pd').read_text()
for n in names:s=s.replace(n+';',prefix+n+(' 90;' if n=='grid-page-leds' else ';'))
s=s.replace('mlr-pattern-file','pcheck-file').replace('mlr-pattern-event','pcheck-event').replace('mlr-pattern-snapshot','pcheck-snapshot').replace('mlr-grid-','pcheck-').replace('s monome_in;','s pcheck-led;').replace('makefilename %d-','makefilename 90%d-').replace('mlr-close-views','pcheck-close-views').replace('r pd;','r pcheck-pd;').replace('90%d-open-player-view','unused-%d-view')
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
for bus,label in [('pcheck-event','accepted'),('pcheck-led','led'),('editor-check-log','player')]:
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
at(120,'901-grid-set-speed','2');at(120,'902-grid-set-speed','2')
# Immediate Record; two original players and both gaps. Quantized Track 1 cut at400.
tap(200,4,0)
at(250,'901-quantizer','0');at(250,'902-quantizer','1')
tap(300,2,1);tap(330,4,1);at(400,'pcheck-ppq','0');tap(500,7,2)
at(600,'901-grid-set-speed','3');at(700,'901-grid-reverse','bang')
at(800,'902-grid-play','bang');at(1000,'902-grid-play','bang')
at(1100,'901-grid-reverse','bang');at(1200,'editor-test-902','stop')
at(1300,'902-grid-play','bang')
tap(1400,4,0) # 1200ms phrase; 200ms lead /100ms tail
# Live action on Track 2 and stale quantized cut coexist with replay.
at(1550,'row_901','15');at(1800,'902-grid-set-speed','1');at(1850,'pcheck-ppq','4')
at(3850,'pcheck-command','stop')
# Stop schedules no tape command; restart and detach stop only timeline.
at(4100,'pcheck-command','toggle');at(4600,'pcheck-connected','0');at(4650,'pcheck-connected','1')
at(4800,'pcheck-command','toggle');at(5200,'pcheck-pd','dsp 0');at(5210,'pcheck-pd','dsp 1')
# Empty recording creates no phrase. Invalid input ignored.
at(5400,'pcheck-command','clear');at(5410,'pcheck-command','toggle')
at(5420,'pcheck-event','cut 1 -1');at(5430,'pcheck-event','speed 2 99')
at(5500,'pcheck-command','toggle')
# Track1-only direction/speed phrase, no cuts: lap restore must never seek/start.
at(5600,'pcheck-command','toggle');at(5700,'901-grid-set-speed','4');at(5800,'901-grid-reverse','bang');at(5900,'pcheck-command','toggle')
at(6850,'pcheck-command','stop');at(6900,'pcheck-command','clear')
# Capture accepted rapid transport, including queued/cancelled resumes and plays.
at(7300,'pcheck-command','toggle')
at(7350,'902-grid-play','bang');at(7351,'902-grid-play','bang');at(7352,'902-grid-play','bang')
at(7360,'902-grid-play','bang');at(7361,'902-grid-play','bang');at(7362,'902-grid-play','bang')
at(7380,'editor-test-902','stop');at(7381,'902-grid-play','bang');at(7383,'editor-test-902','stop')
at(7400,'902-grid-play','bang');at(7500,'pcheck-command','toggle');at(8200,'pcheck-command','stop')
# Controls-only phrase on a stopped player must keep it stopped at every lap.
at(8250,'editor-test-902','stop');at(8300,'pcheck-command','clear');at(8400,'pcheck-command','toggle')
at(8500,'902-grid-set-speed','3');at(8600,'pcheck-command','toggle');at(8880,'pcheck-command','stop')
at(8900,'pcheck-finish','bang')
last=0;lines=[]
for t,r,m in sorted(score,key=lambda v:v[0]):lines.append(f'{t-last} {r} {m};');last=t
(OUT/'score.txt').write_text('\n'.join(lines)+'\n')
for f in ['check.pd','pattern-control.pd','sample_player_rebuild.pd','pattern-player.pd']:assert not check(OUT/f)['errors'],check(OUT/f)
manifest=dict(pattern_slots=8,score=score,base='fe0a5d49027a0eb0cb75f20d87063e34ca0f9810',production_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in ROOT.iterdir() if f.suffix in ('.pd','.pd_lua')},fixture_changes='Unique Lua classes; original players/slots 901/902 mapped to musical tracks 1/2; private ppq/Grid/pattern/snapshot/LED buses; screen requests redirected to unused bus; passive accepted-action and state probes. No DAC, writesf, device or global DSP command.',fixture_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in OUT.iterdir() if f.suffix in ('.pd','.pd_lua') or f.name in ('source.wav','score.txt')})
(OUT/'source.json').write_text(json.dumps(manifest,indent=2)+'\n');print(OUT/'check.pd')
