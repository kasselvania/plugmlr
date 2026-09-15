"""Check actual native eight-slot behavior and the preceding single-slot regression."""
from pathlib import Path
import json,hashlib,subprocess,sys,runpy
ROOT=Path(__file__).resolve().parents[1];P=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/plugmlr-pattern-bank')
sys.argv=[str(ROOT/'tests/check_performance_pattern.py'),str(P)]
runpy.run_path(sys.argv[0],run_name='__main__')
m=json.loads((P/'source.json').read_text());events=[]
for line in (P/'events.txt').read_text().splitlines():
 a=line.rstrip(';').split();events.append((float(a[0]),a[1:]))
def select(tag):return [(t,a[1:]) for t,a in events if a[0]==tag]
def exact(actual,want):
 assert len(actual)==len(want),(len(actual),len(want),actual,want)
 for (t,a),(wt,wa) in zip(actual,want):assert abs(t-wt)<.05 and a==list(map(str,wa)),((t,a),(wt,wa))
want=[(9600,[2,'restore',0,2])]
for i in range(3,9):
 start=9650+(i-3)*450;track=1 if i%2 else 2
 want.extend([(start+200,[track,'restore',0,2]),(start+260,[track,'cut',i-1]),(start+400,[track,'restore',0,2])])
 if i==8:want.append((start+460,[track,'cut',i-1]))
want.extend([(12650,[1,'restore',0,2]),(12700,[1,'direction',1]),(12730,[1,'speed',3]),(12760,[1,'cut',8])])
for t,track,cell in [(12800,2,1),(12900,2,3),(13100,1,4),(13200,2,5),(13500,1,6),(14000,2,9),(14400,1,6)]:
 want.extend([(t,[track,'restore',0,2]),(t+60,[track,'cut',cell])])
exact([(t,a) for t,a in select('replay') if t>=9000],want)
status=select('status');states={i:'empty' for i in range(1,9)};seen=set()
for t,a in status:
 if a[0]=='pattern':
  i=int(a[1]);states[i]=a[2]
  assert sum(v in ('recording','playing') for v in states.values())<=1,(t,states.copy())
  if t>=9000 and a[2]=='recording':seen.add(i)
assert seen==set(range(1,9))
for t,a in [(9400,['pattern',1,'stopped']),(9400,['length',1,.2]),(9400,['count',1,1]),(9861,['pattern',1,'empty']),(12811,['pattern',8,'empty']),(12981,['pattern',4,'empty']),(13900,['pattern',8,'stopped']),(13900,['length',8,.1]),(14400,['pattern',6,'empty'])]:
 assert (t,list(map(str,a))) in status,(t,a)
assert not any(a[0]=='error' for t,a in status)
# Replayed cuts reach original players; no event belongs to the newly empty recorder.
accepted=select('accepted')
for t,a in want:
 if a[1]=='cut':assert (t,['cut',str(a[0]),str(a[2])]) in accepted,(t,a)
assert not any(14100<=t<14400 and a[0] in ('cut','direction','speed','transport') for t,a in accepted)
assert not any(13300<=t<13500 or 13600<=t<14000 or 14501<=t for t,a in select('replay'))
buttons=select('button')
assert len([(t,a) for t,a in buttons if 13200<=t<=13210])==1
assert not any(12840<=t<=12843 for t,a in buttons)
for i in range(1,9):assert any(a==['toggle',str(i)] for t,a in buttons)
# Eight statuses, permanent navigation and inactive Clear preserving blink/output.
leds=[]
for t,a in select('led'):
 assert a[0]=='/monome/grid/led/level/row'
 row=list(map(int,a[3:]));assert len(row)==16 and all(0<=v<=15 for v in row)
 if a[2]=='0':leds.append((t,row))
def nav(t):return [r for lt,r in leds if lt<=t+.05][-1]
assert nav(100)[4:12]==[2]*8
for t,i,level in [(9200,1,15),(9400,1,5),(9400,2,15),(9600,2,10),(9650,2,5),(9650,3,15),(9861,1,2),(9861,3,10),(12811,8,2),(12811,2,10),(13200,6,10),(13350,6,5),(13950,8,5),(14000,8,10),(14100,6,15),(14300,6,2),(14400,6,2),(14400,7,10),(14501,7,2)]:
 assert nav(t)[i+3]==level,(t,i,nav(t))
assert nav(13120)[0]==12 and nav(13120)[8]==10 # PLAY switch retains slot5.
# All original audio, player adapters, bank wiring and device dependency files unchanged.
allowed={'performance-pattern.pd_lua','grid-cut-keys.pd_lua','grid-page-leds.pd_lua'}
protected=[]
for name in subprocess.check_output(['git','ls-tree','--name-only',m['bank_base']],cwd=ROOT,text=True).splitlines():
 if name.endswith(('.pd','.pd_lua')) and name not in allowed:
  assert (ROOT/name).read_bytes()==subprocess.check_output(['git','show',m['bank_base']+':'+name],cwd=ROOT),name
  protected.append(name)
for name,h in m['production_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
r=dict(passed=True,native_bank_replay_commands=len(want),single_slot_regression_commands=77,slots_exercised=sorted(seen),unchanged_components=protected,checks=['Eight physical key addresses through native adapter','Finish/retain recording before switching','Only one active slot at every status transition','Outgoing pending events cancelled before another recorder opens','Inactive Clear affects only target slot','Per-slot snapshots and duration retained','Original player accepts all replayed cuts','Page change/reconnect preserve eight LED states','Duplicate key and MOD suppression','Detach/DSP-message stop and recording finish','Empty recording stays empty'],limitations=['No new audio/listening or physical eight-slot Grid acceptance','Synthetic DSP-off messages on private fixture bus; global DSP unchanged','Slot limits and reentrancy tested with simulated logical clock separately'])
(P/'analysis.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS',len(want),'bank replay commands +77 regression;',len(protected),'unchanged components')
