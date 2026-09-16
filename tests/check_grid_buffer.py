"""Check native BUFFER assignments/readback and preserve the original player engine."""
from pathlib import Path
import hashlib,json,runpy,subprocess,sys
from check_patch_connections import check
ROOT=Path(__file__).resolve().parents[1]
P=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/plugmlr-grid-buffer')
sys.argv=[str(ROOT/'tests/check_pattern_bank.py'),str(P)]
runpy.run_path(sys.argv[0],run_name='__main__')
m=json.loads((P/'source.json').read_text());E=[]
for line in (P/'events.txt').read_text().splitlines():
 a=line.rstrip(';').split();E.append((float(a[0]),a[1:]))
def select(tag):return [(t,a[1:]) for t,a in E if a[0]==tag and t>=14600]
def state(row,field,t):
 return [a[2] for tt,a in select('selected') if tt<=t+.01 and a[:2]==[str(row),field]][-1]
def led(row,t):
 return [list(map(int,a[3:])) for tt,a in select('led') if tt<=t+.01 and a[2]==str(row)][-1]
want=[(15000+row*80,[row,'sample',2]) for row in range(1,7)]
want += [(15700,[1,'sample',2]),(15705,[1,'sample',16]),(15710,[1,'sample',1]),
 (16000,[1,'live',16]),(16200,[2,'live',16]),(16450,[2,'sample',1]),
 (16900,[3,'sample',3]),(16950,[3,'live',3]),(17100,[4,'live',7]),
 (17900,[6,'live',16]),(18400,[5,'sample',16])]
assert select('assignment')==[(t,list(map(str,a))) for t,a in want],select('assignment')
# Actual committed targets (not optimistic Grid state). Superseded requests never install.
committed=[(t,a) for t,a in select('selected') if a[1]=='buffer']
expected=[(15020+row*80,[row,'buffer','sample_buffer_902']) for row in range(1,7)]
expected += [(15620,[1,'buffer','sample_buffer_901']),(15730,[1,'buffer','sample_buffer_901']),
 (16020,[1,'buffer','live_buffer_916']),(16220,[2,'buffer','live_buffer_916']),
 (16470,[2,'buffer','sample_buffer_901']),(16920,[3,'buffer','sample_buffer_903']),
 (16970,[3,'buffer','live_buffer_903']),(17120,[4,'buffer','live_buffer_907']),
 (17920,[6,'buffer','live_buffer_916']),(18420,[5,'buffer','sample_buffer_916'])]
assert committed==[(t,list(map(str,a))) for t,a in expected],committed
# Browse is receive-only; switching one lane does not command another lane.
assert not any(14700<=t<15080 for t,a in select('selected'))
assert not any(15080<=t<=15120 and a[0]=='2' for t,a in select('selected'))
assert not any(15600<=t<15900 and a[0]!='1' for t,a in select('selected'))
for row in (1,2):assert state(row,'playing',15501)=='1' and state(row,'paused',15501)=='0'
for row in range(3,7):assert state(row,'playing',15501)=='0'
assert state(1,'ready',16021)=='0' and state(1,'playing',16021)=='0'
assert state(2,'playing',16221)=='1' and state(2,'ready',16221)=='1'
assert state(2,'paused',16301)=='1'
assert state(2,'playing',16471)=='0' # Existing selection ends paused transport; never auto-starts.
assert state(3,'ready',16921)=='0' and state(3,'playing',16921)=='0'
assert state(5,'ready',18421)=='1' and state(5,'playing',18421)=='0'
assert not select('loop') and not select('play')
assert select('screen')==[(17110,['cut','4']),(18000,['play','6']),(18050,['cut','6'])]
assert not any(17100<=t<17200 or 17300<=t<17500 for t,a in select('key-cut'))
assert (17500,['toggle','3']) in select('button')
assert (17500,['pattern','3','playing']) in select('status')
assert not any(17800<=t<17820 for t,a in select('led'))
assert (17820,['bank','live']) in select('display')
for t,a in select('led'):
 assert a[:2]==['/monome/grid/led/level/row','0'] and 0<=int(a[2])<8
 assert len(a[3:])==16 and all(0<=int(v)<=15 for v in a[3:])
assert led(0,14703)[14]==12 and led(0,17501)[6]==10
assert led(7,14703)==[15]+[0]*14+[5]
assert led(7,14801)==[5]+[0]*14+[15]
assert led(1,14703)==[15,5]+[1]*14
assert led(1,14801)==[1]*16 # No false selection in the other bank.
assert led(1,15080)==[8,5]+[1]*14
for row in range(1,7):assert led(row,15501)==[5,15]+[1]*14
assert led(1,15620)==[15,5]+[1]*14 # External/on-screen path reflected.
assert led(1,15705)==[8,5]+[1]*14
assert led(1,15730)==[15,5]+[1]*14
assert led(1,16021)==[1]*15+[15] # Empty, but selected.
assert led(2,16102)==[1]*15+[5] # Original live owner metadata publication.
assert led(2,16221)==[1]*15+[15]
assert led(2,16911)==[1]*16 # Live content cleared while viewing Sample.
assert led(3,16971)==[1,1,15]+[1]*13
assert led(7,17821)==[5]+[0]*14+[15]
assert led(6,17921)==[1]*15+[15]
assert led(1,18301)==[5,5]+[1]*13+[5] # Actual soundfiler load of Sample16.
assert led(5,18421)==[5,5]+[1]*13+[15]
# Strict current-slice boundary, independently of older regression allowances.
allowed={'grid-cut-control.pd','grid-cut-keys.pd_lua','grid-page-leds.pd_lua','grid-playback-state.pd'}
protected=[]
for name in subprocess.check_output(['git','ls-tree','--name-only',m['buffer_base']],cwd=ROOT,text=True).splitlines():
 if name.endswith(('.pd','.pd_lua')) and name not in allowed:
  assert (ROOT/name).read_bytes()==subprocess.check_output(['git','show',m['buffer_base']+':'+name],cwd=ROOT),name
  protected.append(name)
for name in ('grid-cut-control.pd','grid-playback-state.pd'):
 old=subprocess.check_output(['git','show',m['buffer_base']+':'+name],cwd=ROOT,text=True)
 assert (ROOT/name).read_text().startswith(old),name
 assert not check(ROOT/name)['errors'],check(ROOT/name)
for name,h in m['production_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
r=dict(passed=True,native_buffer_requests=len(want),native_committed_targets=len(expected),native_pattern_regression_commands=115,
 unchanged_components=protected,checks=['Six original player routes','Empty and populated Sample/Live, slot16','Rapid latest-wins selection','External selection readback','No transport commands from bank browsing','Held keys and page/modifier cancellation','80ms CUT regression in Lua suite','Metadata population/clear and actual soundfiler load','Committed versus switching LED states','Stopped/paused selection does not launch','Pattern control and LEDs on BUFFER','Reconnect retains viewed bank'],
 limitations=['No new audio capture or listening claim','Physical BUFFER usability pending','Live content metadata seeded; no recording or Clear action tested','Original paused selection becomes stopped rather than preserving pause position','Global buffer identity remains inherited; not full application instance isolation'])
(P/'analysis.json').write_text(json.dumps(r,indent=2)+'\n')
print('PASS',len(want),'native BUFFER requests;',len(expected),'committed targets;',len(protected),'unchanged components')
