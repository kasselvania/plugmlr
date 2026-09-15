"""Check actual native pattern/accepted-player events, LED feedback, source boundary."""
from pathlib import Path
import json,hashlib,subprocess,sys
from check_patch_connections import check
ROOT=Path(__file__).resolve().parents[1];P=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/plugmlr-cut-pattern')
m=json.loads((P/'source.json').read_text())
events=[]
for line in (P/'events.txt').read_text().splitlines():
 a=line.rstrip(';').split();events.append((float(a[0]),a[1:]))
def select(tag):return [(t,a[1:]) for t,a in events if a[0]==tag]
def exact(actual,want):
 assert len(actual)==len(want),(len(actual),len(want))
 for (t,a),(wt,wa) in zip(actual,want):assert abs(t-wt)<0.05 and a==list(map(str,wa)),((t,a),(wt,wa))
expected=[(t,a) for t,a in [(900,[1,4]),(1000,[2,7]),(1200,[1,10]),(1400,[1,4]),(1500,[2,7]),(1700,[1,10]),(1900,[1,4]),(2200,[1,4]),(2300,[2,7]),(2500,[1,10]),(2700,[1,4]),(3700,[1,1]),(3800,[1,13]),(3950,[1,1]),(4300,[6,3]),(4310,[6,3]),(4320,[6,3])]]
for base in (4630,4750,4870,4990):
 for i in range(12):
  if base+i*7<5001:expected.append((base+i*7,[6,i]))
exact(select('replay'),expected)
accepted=[(t,a) for t,a in select('accepted') if a[0] in ('1','2')]
want=[(400,[1,4]),(500,[2,7]),(700,[1,10])]+expected[:11]+[(3150,[1,1]),(3250,[1,13])]+expected[11:14]
exact(accepted,want)
# Real quantizer latest-wins, bypass on replay, invalid replay cannot cancel pending.
assert not any(a==['1','15'] for t,a in accepted)
assert any(t==3060 and a==['7','2','1'] for t,a in select('key-cut'))
assert not any(3000<t<3150 for t,a in accepted)
status=[(t,a[1]) for t,a in select('status') if a[0]=='pattern']
for t,state in [(150,'armed'),(170,'empty'),(220,'armed'),(400,'recording'),(900,'playing'),(1925,'stopped'),(2780,'empty'),(3000,'armed'),(3150,'recording'),(3400,'stopped'),(3700,'playing'),(4000,'stopped')]:assert (t,state) in status
assert len([1 for t,a in select('button') if t<250])==3 # duplicate and MOD do nothing
assert (2780,['clear']) in select('button')
assert not any(3400<=t<3700 or 4000<=t<4300 for t,a in select('replay'))
# One renderer, actual output row; recording flash, stopped/armed/empty distinguishable.
leds=[]
for t,a in select('led'):
 assert a[0]=='/monome/grid/led/level/row'
 if a[2]=='0':leds.append((t,list(map(int,a[3:]))))
for t,level in [(100,2),(150,15),(170,2),(400,15),(600,2),(800,15),(900,10),(1925,5),(2780,2),(3450,5)]:
 assert [row for lt,row in leds if lt<=t+0.05][-1][4]==level,(t,level)
assert all(len(row)==16 and all(0<=v<=15 for v in row) for t,row in leds)
for name,h in m['production_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
allowed={'grid-cut-keys.pd_lua','grid-cut-control.pd','grid-page-leds.pd_lua','sample_player_rebuild.pd'}
protected=[]
for name in subprocess.check_output(['git','ls-tree','--name-only',m['base']],cwd=ROOT,text=True).splitlines():
 if name.endswith(('.pd','.pd_lua')) and name not in allowed:
  assert (ROOT/name).read_bytes()==subprocess.check_output(['git','show',m['base']+':'+name],cwd=ROOT),name
  protected.append(name)
old=subprocess.check_output(['git','show',m['base']+':sample_player_rebuild.pd'],cwd=ROOT,text=True)
assert (ROOT/'sample_player_rebuild.pd').read_text()==old+'\n#X obj 3450 50 pattern-player \\$0 \\$1;\n#X connect 548 0 553 0;\n#X connect 553 0 142 0;\n'
for name in ['sample_player_rebuild.pd','grid-cut-control.pd','pattern-player.pd']:assert not check(ROOT/name)['errors'],check(ROOT/name)
r=dict(passed=True,replay_events=len(expected),original_player_accepted_events=len(accepted),navigation_led_frames=len(leds),unchanged_components=protected,checks=['quantizer latest-wins before capture','replay without ppq / no second quantization','two-track identity across focus/page change','Stop/restart/Clear','empty buffer does not start capture','invalid replay preserves pending cut','detach finishes stopped / reconnect no launch','DSP-off stops / DSP-on no launch','minimum 10ms loop','7ms event spacing across repeat boundaries','armed / recording flash / playing / stopped / empty LEDs'],limitations=['No audio capture or listening result','No physical Grid playtest','Limit tests use production Lua with a simulated logical clock'])
(P/'analysis.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS',len(expected),'native replay events;',len(accepted),'original-player accepted cuts;',len(protected),'unchanged components')
