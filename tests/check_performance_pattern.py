"""Assert retained native control evidence; deliberately makes no audio/listening claim."""
from pathlib import Path
import hashlib,json,subprocess,sys
from check_patch_connections import check
ROOT=Path(__file__).resolve().parents[1];P=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/plugmlr-performance-pattern')
m=json.loads((P/'source.json').read_text())
events=[]
for line in (P/'events.txt').read_text().splitlines():
 a=line.rstrip(';').split()
 if m.get('bank') and float(a[0])>=8900:continue
 if a[1]=='status' and a[2] in ('pattern','count','length') and len(a)==5:
  assert a[3]=='1';a.pop(3) # Slot-labelled status in the eight-slot version.
 events.append((float(a[0]),a[1:]))
def select(tag):return [(t,a[1:]) for t,a in events if a[0]==tag]
def exact(actual,want):
 assert len(actual)==len(want),(len(actual),len(want))
 for (t,a),(wt,wa) in zip(actual,want):assert abs(t-wt)<.05 and a==list(map(str,wa)),((t,a),(wt,wa))
phrase=[(200,[1,'cut',4]),(300,[2,'cut',7]),(400,[1,'speed',3]),(500,[1,'direction',1]),(600,[2,'transport',2]),(800,[2,'transport',1]),(900,[1,'direction',0]),(1000,[2,'transport',0]),(1100,[2,'transport',1])]
want=[]
for base,end in [(1400,3850),(2600,3850),(3800,3850),(4100,4600),(4800,5200)]:
 want.extend([(base,[1,'restore',0,2]),(base,[2,'restore',0,2])])
 want.extend((base+dt,a) for dt,a in phrase if base+dt<end)
for base in [5900,6200,6500,6800]:
 want.append((base,[1,'restore',0,2]))
 for dt,a in [(100,[1,'speed',4]),(200,[1,'direction',1])]:
  if base+dt<6850:want.append((base+dt,a))
rapid=[(50,2),(60,1),(61,2),(70,1),(80,0),(83,0),(100,1)]
for base in [7500,7700,7900,8100]:
 want.append((base,[2,'restore',0,2]))
 want.extend((base+dt,[2,'transport',v]) for dt,v in rapid if base+dt<8200)
want.extend([(8600,[2,'restore',0,2]),(8700,[2,'speed',3]),(8800,[2,'restore',0,2])])
exact(select('replay'),want)
# Independent expected accepted recording: two original players, never raw key downs.
recorded=[(t,[a[1],a[0],*a[2:]]) for t,a in [(200+dt,a) for dt,a in phrase]]
exact([(t,a) for t,a in select('accepted') if 200<t<1400],recorded)
exact([(t,a) for t,a in select('accepted') if 7300<t<7500],[(7300+dt,['transport',2,v]) for dt,v in rapid])
assert not any(a==['cut','1','15'] for t,a in select('accepted')), 'stale quantizer survived replay'
# Every replayed action reached actual player state, not merely the scheduler output.
player=select('player')
def state(track,name,t):
 vals=[a[1] for pt,a in player if pt<=t+.01 and a[0]==f'{900+track}-{name}']
 assert vals,(track,name,t)
 return float(vals[-1])
for t,a in want:
 track,kind,*v=a
 if kind=='restore':
  assert state(track,'playback_direction',t)==v[0]
  assert state(track,'playback_speed_dial',t)==v[1]
 elif kind in ('direction','speed'):
  assert state(track,{'direction':'playback_direction','speed':'playback_speed_dial'}[kind],t)==v[0]
 elif kind=='transport':
  if v[0]==0:assert state(track,'is_playing_flag',t)==0
  if v[0]==1:assert state(track,'is_playing_flag',t)==1 and state(track,'is_paused_flag',t)==0
  if v[0]==2:assert state(track,'is_paused_flag',t)==1
 elif kind=='cut':assert (t,['cut',str(track),str(v[0])]) in select('accepted')
# Controls-only looping moves the existing tape continuously, without transport/key events.
assert not any(5900<=t<6850 and (a[0].endswith('is_playing_flag') or a[0].endswith('is_paused_flag') or a[0].endswith('key_press_pos')) for t,a in player)
positions=[(t,float(a[1])) for t,a in player if a[0]=='901-play-position-frames']
for boundary in [5900,6200,6500,6800]:
 before=[(t,v) for t,v in positions if t<boundary][-1]
 after=[(t,v) for t,v in positions if t>=boundary][0]
 assert 0<abs(after[1]-before[1])<44100*4*(after[0]-before[0])/1000+2,(boundary,before,after)
assert state(2,'is_playing_flag',8700)==0
assert not any(8400<=t<8880 and a[0] in ['902-is_playing_flag','902-is_paused_flag'] for t,a in player)
assert not any(5600<=t<6850 and a[0] in ['902-playback_speed_dial','902-playback_direction'] for t,a in player)
status=select('status')
for t,s in [(200,'recording'),(1400,'playing'),(3850,'stopped'),(4600,'stopped'),(5200,'stopped'),(5500,'empty')]:assert (t,['pattern',s]) in status
assert (1400,['length','1.2']) in status
assert not any(a[0]=='error' for t,a in status)
assert not any(4600<=t<4800 or 5200<=t<5900 for t,a in select('replay'))
leds=[]
for t,a in select('led'):
 assert a[0]=='/monome/grid/led/level/row'
 row=list(map(int,a[3:]));assert len(row)==16 and all(0<=v<=15 for v in row)
 if a[2]=='0':leds.append((t,row))
for t,level in [(100,2),(200,15),(400,2),(600,15),(1400,10),(3850,5),(5500,2)]:
 assert [row for lt,row in leds if lt<=t+.05][-1][4]==level,(t,level)
for name,h in m['production_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
allowed={'grid-cut-control.pd','pattern-player.pd','sample_player_rebuild.pd'}
if m.get('bank') or m.get('pattern_slots')==8:allowed.update({'grid-cut-keys.pd_lua','grid-page-leds.pd_lua'})
if m.get('files'):allowed.add('mlr.pd')
if m.get('grid_buffers'):allowed.add('grid-playback-state.pd')
protected=[]
for name in subprocess.check_output(['git','ls-tree','--name-only',m['base']],cwd=ROOT,text=True).splitlines():
 if name.endswith(('.pd','.pd_lua')) and name not in allowed:
  assert (ROOT/name).read_bytes()==subprocess.check_output(['git','show',m['base']+':'+name],cwd=ROOT),name
  protected.append(name)
old=subprocess.check_output(['git','show',m['base']+':sample_player_rebuild.pd'],cwd=ROOT,text=True)
now=(ROOT/'sample_player_rebuild.pd').read_text()
pause='''#X msg 25 835 2;
#X obj 180 835 s \\$0-pattern-transport;
#X connect 0 0 38 0;
#X connect 38 0 39 0;
'''
tail='''
#X msg 3450 130 0;
#X msg 3570 130 1;
#X obj 3450 175 s \\$0-pattern-transport;
#X connect 44 0 554 0;
#X connect 554 0 556 0;
#X connect 262 0 555 0;
#X connect 548 1 555 0;
#X connect 555 0 556 0;
'''
assert now==old.replace('#X restore 1415 78 pd pause_transition;',pause+'#X restore 1415 78 pd pause_transition;')+tail
for name in ['sample_player_rebuild.pd','grid-cut-control.pd','pattern-player.pd']:assert not check(ROOT/name)['errors'],check(ROOT/name)
r=dict(passed=True,native_replay_commands=len(want),recorded_phrase_actions=len(phrase),rapid_transport_actions=len(rapid),led_frames=len(leds),unchanged_components=protected,checks=['Immediate Record and 1200ms phrase with 200ms lead and 100ms tail','Native original-player cuts, speed, direction, Play/Pause/Resume/Stop','Post-quantizer latest-wins capture and replay bypass; stale input cancellation','Rapid toggles resolved before capture; Stop cancels queued Play','Controls-only lap restoration retains position and transport','Untouched track controls stay unchanged','Live speed change during replay','Disconnect and simulated DSP-off stop scheduling without reconnect restart','Empty / malformed input; native LED status'],limitations=['No new audio capture or listening claim','No physical Grid acceptance yet','DSP-off message simulated on private test bus; global audio DSP left on','4096-event and 300-second limits checked separately with simulated clock'])
(P/('regression-analysis.json' if m.get('bank') else 'analysis.json')).write_text(json.dumps(r,indent=2)+'\n');print('PASS',len(want),'native replay commands;',len(protected),'unchanged components')
