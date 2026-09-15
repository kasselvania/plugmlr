"""Native PLAY/CUT controller check; isolated players 901..906, no DAC or capture.
Run: pages-check-run bang. A 55s watchdog stops all test players and the score.
"""
from pathlib import Path
import runpy,hashlib,json,sys,re
ROOT=Path(__file__).resolve().parents[1];OUT=Path('/tmp/plugmlr-grid-pages-check');OUT.mkdir(exist_ok=True)
b=runpy.run_path(str(ROOT/'tests/build_sample_editor_check.py'));Patch=b['Patch'];count=b['root_count']
for f in b['OUT'].iterdir():
 if f.suffix in ('.pd','.pd_lua','.lua','.wav'):(OUT/f.name).write_bytes(f.read_bytes())
p=OUT/'buffer-selection.pd';p.write_text(p.read_text().replace('$f2 <= 902','$f2 <= 906'))
# Keep original player with only passive state and test Stop probes; isolate ppq.
p=OUT/'sample_player_rebuild.pd';p.write_text(p.read_text().replace('r ppq;', 'r pages-check-ppq;'))
names=['grid-cut-keys','grid-page-leds']
prefix='pages'+hashlib.sha256(b''.join((ROOT/(n+'.pd_lua')).read_bytes() for n in names)).hexdigest()[:8]+'-'
for n in names:(OUT/(prefix+n+'.pd_lua')).write_text((ROOT/(n+'.pd_lua')).read_text().replace("register('"+n+"')","register('"+prefix+n+"')"))
s=(ROOT/'grid-cut-control.pd').read_text().replace('grid-cut-keys;',prefix+'grid-cut-keys;').replace('grid-page-leds;',prefix+'grid-page-leds 90;').replace('makefilename %d-grid-','makefilename 90%d-grid-').replace('mlr-grid-','pages-check-').replace('s monome_in;','s pages-check-led;')
p=Patch(count(s));o,c=p.add,p.wire
for outlet,name in [(0,'slice'),(1,'play'),(2,'focus'),(4,'loop'),(5,'reverse'),(6,'speed')]:
 tag=o(f'obj 20 {650+outlet*70} list prepend {name}');dst=o(f'obj 350 {650+outlet*70} s pages-check-log');c(2,tag,outlet);c(tag,dst)
(OUT/'pages-control.pd').write_text(s+'\n'+p.text())
p=Patch();o,c=p.add,p.wire
o('text 20 15 PLAY/CUT check - starts 1s after load - no DAC or recording - automatic finish')
auto=o('obj 20 45 loadbang');wait=o('obj 20 80 delay 1000');runout=o('obj 20 115 s pages-check-run');c(auto,wait);c(wait,runout)
for row in range(1,7):
 t=900+row
 o(f'obj {row*180} 60 sample-data {t}');o(f'obj {row*180} 100 sample_player_rebuild {t}')
 for ch in range(2):o(f'obj {row*180} {145+ch*40} array define {ch}-live_buffer_{t} 4')
 o(f'obj {row*180} 205 {b["prefix"]}buffer-view-data live {t}')
 # Capture actual reports from each original player's new read-only exports.
 for j,field in enumerate(['direction','speed','playing','paused','ready']):
  r=o(f'obj {row*180} {240+j*100} r {t}-grid-{field}');tag=o(f'obj {row*180} {270+j*100} list prepend state {row} {field}');dst=o(f'obj {row*180} {300+j*100} s pages-check-log');c(r,tag);c(tag,dst)
r=o('obj 20 800 r pages-check-input');ctl=o('obj 20 840 pages-control');c(r,ctl)
u=o('obj 20 890 unpack f f f');dest=o('obj 200 930 makefilename row_90%d');send=o('obj 20 970 send');c(ctl,u);c(u,dest,1);c(dest,send,0,1);c(u,send)
run=o('obj 20 1050 r pages-check-run');tr=o('obj 20 1090 t b b b b');c(run,tr)
watch=o('obj 500 1090 delay 55000');c(tr,watch,3)
log=o('obj 800 1050 text define \\$0-events');clear=o('msg 500 1130 clear');c(tr,clear,2);c(clear,log)
clock=o('obj 950 1130 timer');c(tr,clock,1)
q=o('obj 20 1180 qlist');m=o(f'msg 20 1130 read {OUT}/score.txt \\, bang');c(tr,m);c(m,q)
r=o('obj 800 1090 r pages-check-log');order=o('obj 800 1130 t l b');tag=o('obj 800 1180 list prepend');ins=o('obj 800 1220 text insert \\$0-events 1e+09');c(r,order);c(order,clock,1,1);c(clock,tag,0,1);c(order,tag);c(tag,ins)
r=o('obj 800 1300 r pages-check-led');tag=o('obj 800 1340 list prepend led');dst=o('obj 800 1380 s pages-check-log');c(r,tag);c(tag,dst)
r=o('obj 500 1180 r pages-check-stop');stop=o('obj 500 1220 t b b b');c(r,stop);c(watch,stop)
m=o('msg 650 1260 stop');c(stop,m,2);c(m,watch)
m=o('msg 500 1260 rewind');c(stop,m,2);c(m,q)
m=o('msg 500 1300 '+ ' '.join(f'\\; editor-test-{t} stop' for t in range(901,907))+' \\; pages-check-connected 0');c(stop,m,1)
delay=o('obj 500 1360 delay 30');c(stop,delay)
tr=o('obj 500 1400 t b b');c(delay,tr)
m=o(f'msg 700 1440 write {OUT}/events.txt');c(tr,m,1);c(m,log)
done=o('obj 500 1440 print pages-check-done');c(tr,done)
(OUT/'check.pd').write_text('#N canvas 100 80 1400 850 12;\n'+p.text())
# Reuse the preceding 53 accepted CUT timing scenarios without changing expected events.
h=runpy.run_path(str(ROOT/'tests/build_grid_hold_check.py'));cases=h['cases']
for case in cases:
 case['commands']=[(t,'pages-check-'+({'key':'input','connected':'connected','cancel':'cancel'}[kind]),v) for t,kind,v in case['commands']]

def keys(t,x,y,z=1):return (t,'pages-check-input',f'{x} {y} {z}')
def tap(t,x,y):return [keys(t,x,y),keys(t+1,x,y,0)]
def ev(t,k,*a):return [t,k,*a]
def add(name,commands,expected):cases.append(dict(name=name,commands=commands,expected=expected))
for row in range(1,7):
 cmds=tap(10,0,0)+tap(20,2,row)+tap(30,7,row)+tap(40,15,row)
 want=[ev(30,'reverse',row),ev(40,'play',row)]
 for i in range(5):cmds+=tap(60+i*15,9+i,row);want+=[ev(60+i*15,'speed',row,i)]
 cmds+=tap(160,11,7);want+=[ev(160,'slice',11,row,1)]
 add(f'play-row-{row}',cmds,want)
add('page-change-cancels-held-loop', [keys(10,2,1),keys(20,7,1)]+tap(110,0,0)+[keys(120,7,1,0),keys(130,2,1,0)], [ev(10,'slice',2,1,1),ev(20,'slice',7,1,1)])
add('held-key-no-new-action-after-page', [keys(10,15,1)]+tap(20,0,0)+[keys(30,15,1),keys(40,15,1,0)]+tap(50,15,1),[ev(10,'slice',15,1,1),ev(50,'play',1)])
add('focus-change-consumes-bottom-hold',tap(5,0,0)+tap(10,2,1)+[keys(20,2,7),keys(30,7,7)]+tap(120,2,2)+[keys(130,7,7,0),keys(140,2,7,0)]+tap(150,7,7),[ev(20,'slice',2,1,1),ev(30,'slice',7,1,1),ev(150,'slice',7,2,1)])
add('play-bottom-loop',tap(5,0,0)+tap(10,2,3)+[keys(20,3,7),keys(30,8,7),keys(110,8,7,0),keys(120,3,7,0)],[ev(20,'slice',3,3,1),ev(30,'slice',8,3,1),ev(110,'loop',3,3,9)])
add('play-modifiers-no-track-command',tap(5,0,0)+tap(10,2,4)+[keys(20,13,0)]+tap(30,7,2)+tap(40,9,2)+tap(50,15,2)+tap(60,5,7)+[keys(70,15,0)]+tap(80,5,7)+[keys(90,15,0,0),keys(100,13,0,0)],[ev(60,'loop',4,5,6),ev(80,'play',4)])
add('page-roundtrip-no-musical-command',tap(10,0,0)+tap(20,1,0)+tap(30,0,0),[])
add('duplicate-speed-and-play',tap(5,0,0)+[keys(10,9,1),keys(20,9,1),keys(30,9,1,0),keys(40,15,2),keys(50,15,2),keys(60,15,2,0)],[ev(10,'speed',1,0),ev(40,'play',2)])
add('unimplemented-controls-inactive',tap(5,0,0)+sum((tap(20+i*3,x,1) for i,x in enumerate([0,1,6,8,14])),[])+tap(50,5,0),[])
add('detach-preserves-page-and-focus',tap(5,0,0)+tap(10,2,6)+[keys(20,2,7),(30,'pages-check-connected','0'),(40,'pages-check-connected','1'),keys(50,2,7,0)]+tap(60,12,7),[ev(20,'slice',2,6,1),ev(60,'slice',12,6,1)])
score=[]
for i,case in enumerate(cases):
 base=i*500;case['base_ms']=base
 score += [(base,'pages-check-connected','0'),(base,'pages-check-connected','1')]+[(base+t,r,m) for t,r,m in tap(0,1,0)]
 score += [(base+2,'pages-check-log','list case '+str(i))]
 score += [(base+t,r,m) for t,r,m in case['commands']]
# A short real-player smoke after silent/empty-state input cases. No new audio file capture.
base=len(cases)*500
score += [(base,'pages-check-log','list smoke 0'),(base,'901-sample-path',f'symbol {OUT}/source.wav')]
for row in range(1,7):
 score += [(base+80,f'{900+row}-buffer-select','sample 901'),(base+120,f'{900+row}-quantizer','1')]
score += [(base+140,'pages-check-connected','0'),(base+140,'pages-check-connected','1')]
score += [(base+150+t,r,m) for t,r,m in tap(0,0,0)]
for row in range(1,7):
 t=base+200+row*150
 score += [(t+dt,r,m) for dt,r,m in tap(0,2,row)+tap(10,4,7)+tap(40,7,row)+tap(70,12,row)+tap(100,15,row)]
score += [(base+1400,'pages-check-log','list smoke-end 0'),(base+1450,'pages-check-stop','bang')]
last=0;lines=[]
for t,r,m in sorted(score,key=lambda v:v[0]):lines.append(f'{t-last} {r} {m};');last=t
(OUT/'score.txt').write_text('\n'.join(lines)+'\n')
manifest=dict(base='ca75d98b77ead7382bc5e330a62249a2f0c8f221',cases=cases,duration_ms=last,production_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in ROOT.iterdir() if f.suffix in ('.pd','.pd_lua')},fixture_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in OUT.iterdir() if f.suffix in ('.pd','.pd_lua','.txt','.wav')},test_changes='Private cached Lua names; track addresses 1..6 mapped to 901..906; connected/cancel/focus/LED buses isolated; ppq isolated; selection test limit 906; passive player probes. No DAC or recording.',smoke_start=base)
(OUT/'source.json').write_text(json.dumps(manifest,indent=2)+'\n')
for f in ['check.pd','pages-control.pd','sample_player_rebuild.pd']:assert not b['check'](OUT/f)['errors'],b['check'](OUT/f)
print(f'{OUT}/check.pd: {len(cases)} key cases + six-player readback; {last/1000}s')
