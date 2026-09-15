"""Check native Grid events/readback and the bounded source change, not audio quality."""
from pathlib import Path
import json,hashlib,subprocess,sys
from check_patch_connections import check
ROOT=Path(__file__).resolve().parents[1];P=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/plugmlr-grid-pages-check')
m=json.loads((P/'source.json').read_text());rows=[]
for line in (P/'events.txt').read_text().splitlines():
 a=line.rstrip(';').split();rows.append((float(a[0]),a[1],a[2:]))
music={'slice','play','loop','reverse','speed'};actual=[[] for _ in m['cases']];case=None;smoke=False
for t,k,a in rows:
 if k=='case':case=int(a[0]);continue
 if k=='smoke':smoke=True
 if not smoke and k in music:
  assert case is not None
  actual[case].append([round(t-m['cases'][case]['base_ms'],6),k]+[int(v) for v in a])
results=[]
for i,case in enumerate(m['cases']):results.append(dict(name=case['name'],expected=case['expected'],actual=actual[i],passed=case['expected']==actual[i]))
# Actual existing players must acknowledge the routed controls on all six lanes.
smoke_results=[]
for row in range(1,7):
 events=[(t,a[1],float(a[2])) for t,k,a in rows if k=='state' and int(a[0])==row and t>=m['smoke_start']]
 # Each row: loaded, slice launch, direction change, 2x preset, Pause, final Stop.
 t=m['smoke_start']+200+row*150
 def values(field,lo,hi):return [v for et,f,v in events if f==field and lo<=et<=hi]
 # Direction before the smoke depends on preceding gestures, so require a report.
 checks={'loaded':1 in values('ready',m['smoke_start'],t),
         'slice_started':1 in values('playing',t+10,t+35),
         'reverse_report':bool(values('direction',t+40,t+45)),
         'speed_2x_report':3 in values('speed',t+70,t+75),
         'paused':1 in values('paused',t+100,t+115),
         'final_stopped':0 in values('playing',m['smoke_start']+1450,m['smoke_start']+1480)}
 smoke_results.append(dict(row=row,checks=checks,passed=all(checks.values())))
# Every page frame must be a complete bounded 16-key row. Unknown rows can't leak.
leds=[]
for t,k,a in rows:
 if k!='led':continue
 assert a[0]=='/monome/grid/led/level/row' and len(a)==19,a
 x,y,*v=map(int,a[1:]);assert x==0 and 0<=y<=7 and all(0<=i<=15 for i in v)
 leds.append((t,y,v))
assert leds
# Readback-driven PLAY feedback, including bottom-row focus, must follow real players.
def frame_at(t,y):
 v=None
 for et,ey,ev in leds:
  if et<=t and ey==y:v=ev
 return v
led_smoke=[]
for row in range(1,7):
 t=m['smoke_start']+200+row*150
 direction=[int(a[2]) for et,k,a in rows if k=='state' and a[:2]==[str(row),'direction'] and t+40<=et<=t+45][-1]
 checks={'focus':frame_at(t+5,row)[2:6]==[10]*4,
         'playing':frame_at(t+20,row)[15]==12,
         'direction':frame_at(t+45,row)[7]==(12 if direction==1 else 3),
         'preset':frame_at(t+75,row)[9:14]==[3,3,3,12,3],
         'paused':frame_at(t+115,row)[15]==7,
         'bottom_playhead':12 in frame_at(t+30,7),
         'bottom_paused':12 not in frame_at(t+115,7)}
 led_smoke.append(dict(row=row,checks=checks,passed=all(checks.values())))
# On every PLAY top-row transition, subsequent track rows use PLAY columns, never CUT markers.
page='cut';frames={};page_checks=0
for t,y,v in leds:
 if y==0:page='play' if v[0]==12 else 'cut'
 if page=='play' and 1<=y<=6:
  assert all(v[i]==0 for i in [0,1,6,8,14]),(t,y,v)
  assert all(v[i] in [3,10] for i in range(2,6)),(t,y,v)
  page_checks+=1
 frames[y]=v
assert page_checks>100
allowed={'grid-cut-keys.pd_lua','grid-cut-control.pd','grid-playback-state.pd','mlr.pd','sample_player_rebuild.pd'}
protected=[]
for name in subprocess.check_output(['git','ls-tree','--name-only',m['base']],cwd=ROOT,text=True).splitlines():
 if name.endswith(('.pd','.pd_lua')) and name not in allowed:
  assert (ROOT/name).read_bytes()==subprocess.check_output(['git','show',m['base']+':'+name],cwd=ROOT),name
  protected.append(name)
old=subprocess.check_output(['git','show',m['base']+':sample_player_rebuild.pd'],cwd=ROOT,text=True)
assert (ROOT/'sample_player_rebuild.pd').read_text()==old+'\n#X obj 2200 4450 grid-play-controls \\$0 \\$1;\n'
old_mlr=subprocess.check_output(['git','show',m['base']+':mlr.pd'],cwd=ROOT,text=True)
expected_mlr=old_mlr.replace('#X obj 326 1487 grid-playback-row 1 1;','#X text 326 1487 Page LEDs now belong to grid-cut-control;').replace('#X obj 704 1471 grid-playback-row 2 2;','#X text 704 1471 Historical row renderer retained as a reference;')
assert (ROOT/'mlr.pd').read_text()==expected_mlr
# Command and report must never share a receive/send name (native rejected first candidate).
assert 'r \\$2-grid-set-speed;' in (ROOT/'grid-play-controls.pd').read_text()
assert 'r \\$2-grid-speed;' not in (ROOT/'grid-play-controls.pd').read_text()
assert '%d-open-player-view' not in (ROOT/'grid-cut-control.pd').read_text()
for name,h in m['production_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
for name in allowed|{'grid-play-controls.pd'}:
 if name.endswith('.pd'):assert not check(ROOT/name)['errors'],check(ROOT/name)
report=dict(cases=results,passed=sum(r['passed'] for r in results),total=len(results),player_readback=smoke_results,led_readback=led_smoke,led_frames=len(leds),play_row_checks=page_checks,protected_sources=protected,original_player_only_adds_control_bridge=True,audio_acceptance='Not measured in this control-only checkpoint',physical_acceptance='Open')
(P/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
assert all(r['passed'] for r in results),[r for r in results if not r['passed']]
assert all(r['passed'] for r in smoke_results),smoke_results
assert all(r['passed'] for r in led_smoke),led_smoke
print(f'PASS {len(results)} native gesture cases, six original player readbacks, {page_checks} PLAY LED rows; {len(protected)} components unchanged')
