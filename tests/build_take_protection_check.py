"""Native original-app fixture: take protection, save/reopen, or 70 s UI/record run.

Run CASE in {record,reopen,guards,long}. Open its check.pd alone; ui-check-run bang.
Every case arms an independent watchdog before capture or recording starts.
"""
from pathlib import Path
import sys, json, hashlib, math, struct, wave
ROOT = Path(__file__).resolve().parents[1]
OUT = Path('/tmp/plugmlr-take-check')
case = sys.argv[1] if len(sys.argv)>1 else 'record'
assert case in ('record','reopen','guards','long')
code = (ROOT/'tests/build_waveform_check.py').read_text().replace("Path('/tmp/plugmlr-waveform-check')", 'OUT_OVERRIDE')
ns = {'__file__':str(ROOT/'tests/build_waveform_check.py'), 'OUT_OVERRIDE':OUT, '__name__':'fixture_builder'}
exec(compile(code,'build_waveform_check.py','exec'), ns)
Patch, count_root, root_objects = ns['Patch'],ns['count_root'],ns['root_objects']
player=(OUT/'observed-player.pd').read_text();p=Patch(count_root(player))
r=p.add('obj 2400 4950 r take-player-\\$1');route=p.add('obj 2400 4990 route clear discard');p.wire(r,route)
for outlet,msg in enumerate(['bang','discard']):
 m=p.add(f'msg {2400+outlet*150} 5030 {msg}');s=p.add(f'obj {2400+outlet*150} 5070 s \\$0-delete_buffer');p.wire(route,m,outlet);p.wire(m,s)
if case=='reopen':
 tap=str(ROOT/'tests/bounded-player-capture').replace(' ','\\ ')
 p.add(f'obj 2700 5100 {tap} \\$1 \\$0')
(OUT/'observed-player.pd').write_text(player+'\n'+p.text())
source=(OUT/'check.pd').read_text();duration={'record':8000,'reopen':8000,'guards':18000,'long':70000}[case]
source=source.replace('delay 15000;',f'delay {duration+2000};')
p=Patch(count_root(source));o,c=p.add,p.wire
r=o('obj 2400 1920 r take-check-array-export');w=o('obj 2400 1960 soundfiler');pr=o('obj 2400 2000 print take-array-export');c(r,w);c(w,pr)
for j,recv in enumerate(['mlr-clear-status','live_buffer_4-view-info','sample_buffer_4-view-info']):
 r=o(f'obj {2400+j*120} 2070 r {recv}');tag=o(f'obj {2400+j*120} 2110 list prepend {recv}');s=o(f'obj {2400+j*120} 2150 s \\$0-ui-log');c(r,tag);c(tag,s)
objects=root_objects(source);finish=next(i for i,l in enumerate(objects) if 'obj 650 1560 t b b b b;' in l)
stop=o('msg 2400 2200 \\; 4_l_b_record stop');c(finish,stop)
(OUT/'check.pd').write_text(source+'\n'+p.text())
score=[]
def at(t,receiver,message='bang'):score.append((t,receiver,message))
def bothstop(t):
 at(t,'1-ui-stop');at(t,'2-ui-stop');at(t,'global-transport','0')
def load(t,slot,name):at(t,f'{slot}-sample-path',f'symbol {OUT}/{name}')
def export(t,kind,slot,name,rate):
 at(t,'take-check-array-export',f'write -wave -bytes 4 -rate {rate} {OUT}/{name} 0-{kind}_buffer_{slot} 1-{kind}_buffer_{slot}')
at(0,'audio-1-out','0.4');at(0,'audio-2-out','0.3');at(0,'global-transport','0')
if case=='record':
 at(0,'3_l_b_length','seconds 3');at(400,'3_l_b_record','start');at(1700,'3_l_b_record','stop')
 at(1800,'3_l_b_first_index','64');at(1800,'3_l_b_select_bang')
 at(2000,'mlr-save-take',f'save 3 {OUT}/roundtrip.wav')
 at(2200,'1-buffer-select','live 3');at(2400,'1-open-player-view')
 at(3000,'1-press_play');at(6000,'1-ui-stop')
 at(6200,'3_l_b_delete_buffer');at(6300,'3_l_b_select_bang')
elif case=='reopen':
 at(0,'1-test-capture',f'start {OUT}/readers.wav 8000')
 assert (OUT/'roundtrip.wav').exists(), 'Run record in native plugdata, save its evidence, then close/reopen.'
 load(0,4,'roundtrip.wav');at(2200,'1-buffer-select','sample 4');at(2400,'1-open-player-view')
 at(3000,'1-press_play');at(6000,'1-ui-stop');export(6300,'sample',4,'reimported.wav',48000)
elif case=='guards':
 load(0,1,'input.wav');at(0,'3_l_b_length','seconds 0.3');at(0,'4_l_b_length','seconds 0.3')
 at(100,'3_l_b_record','start');at(100,'4_l_b_record','start')
 at(150,'3_l_b_delete_buffer');at(160,'3_l_b_delete_buffer','discard')
 at(500,'1-buffer-select','live 3');at(600,'1-open-player-view');at(800,'1-press_play')
 at(1000,'take-player-1','clear');at(1100,'take-player-1','clear')
 at(1300,'1-buffer-select','live 4');at(1400,'1-buffer-select','live 3');at(1500,'take-player-1','discard')
 at(1800,'take-player-1','clear');at(1900,'mlr-close-views');at(2000,'take-player-1','discard')
 at(2200,'take-player-1','clear');at(7300,'take-player-1','discard')
 at(7500,'take-player-1','clear');at(7600,'take-player-1','discard');at(7800,'3_l_b_select_bang')
 at(7900,'1-ui-stop');at(8000,'4_l_b_delete_buffer')
 at(8100,'mlr-save-take',f'save 4 {OUT}/guard-saved.wav')
 at(8200,'4_l_b_delete_buffer','discard');at(8400,'4_l_b_select_bang')
 at(8500,'4_l_b_delete_buffer');at(8600,'4_l_b_select_bang')
 at(9000,'4_l_b_record','start');at(9400,'4_l_b_delete_buffer')
 at(9500,'4_l_b_first_index','64');at(9500,'4_l_b_select_bang');at(9600,'4_l_b_delete_buffer','discard')
 at(9800,'4_l_b_delete_buffer');at(9900,'4_l_b_storage_busy','1');at(10000,'4_l_b_delete_buffer','discard')
 at(10100,'4_l_b_storage_busy','0');at(10200,'4_l_b_delete_buffer','discard')
 at(10400,'4_l_b_delete_buffer');at(10500,'4_l_b_delete_buffer','cancel');at(10600,'4_l_b_delete_buffer','discard')
 at(10800,'4_l_b_delete_buffer');at(10900,'4_l_b_delete_buffer','discard');at(11100,'4_l_b_select_bang')
 at(11300,'4_l_b_record','start');at(11700,'4_l_b_delete_buffer','discard');at(11900,'4_l_b_select_bang')
 # End with an unsaved take for a direct native Clear/Discard button observation.
 at(12200,'1-buffer-select','live 4');at(12300,'1-open-player-view')
elif case=='long':
 # Sixty-second stereo file: deterministic bins, useful transients, modest level.
 path=OUT/'long-stereo.wav';sr=48000
 with wave.open(str(path),'wb') as f:
  f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr)
  for second in range(60):
   values=[]
   for i in range(sr):
    # Unequal-channel packet repeats each second; no discontinuity at file wrap.
    env=.5+.5*math.sin(2*math.pi*i/sr)**2
    values.extend((round(8000*env*math.sin(2*math.pi*127*i/sr)),round(6000*env*math.sin(2*math.pi*211*i/sr))))
   f.writeframes(struct.pack('<'+'h'*len(values),*values))
 load(0,1,'long-stereo.wav');load(100,2,'input.wav')
 at(200,'1-buffer-select','sample 1');at(200,'2-buffer-select','sample 2')
 at(400,'1-press_play');at(400,'2-press_play');at(600,'1-open-player-view')
 at(1000,'3_l_b_length','dynamic');at(2000,'3_l_b_record','start')
 for t in [8000,16000,24000,32000,40000,48000,56000]:
  at(t,'ui-check-sample-bank-open');at(t+500,'ui-check-record-takes-open');at(t+1000,'1-open-player-view')
 at(20000,'1-loop-region','2 10');at(26000,'waveform-player-1','reverse')
 at(34000,'waveform-player-1','reverse');at(45000,'1-loop-region','full')
 at(62100,'3_l_b_record','stop');bothstop(62500)
 at(63000,'mlr-save-take',f'save 3 {OUT}/long-take.wav')
 at(64000,'1-buffer-select','live 3');at(64500,'1-open-player-view')
 at(68000,'ui-check-record-takes-open')
at(duration,'ui-check-stop')
score.sort(key=lambda row:row[0]);last=0;lines=[]
for t,r,m in score:lines.append(f'{t-last} {r} {m};');last=t
(OUT/'score.txt').write_text('\n'.join(lines)+'\n')
from check_patch_connections import check
for n in ['check.pd','observed-player.pd']:assert not check(OUT/n)['errors']
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.iterdir() if p.suffix in ('.pd','.pd_lua')}
(OUT/'source.json').write_text(json.dumps({'base':'566c8608e4d3244471db81118ed1939b471c3eca','case':case,'production_sha256':hashes,'fixture_sha256':hashlib.sha256((OUT/'check.pd').read_bytes()).hexdigest(),'score':score,'duration_ms':duration,'watchdog_ms':duration+2000,'channels':['master L','master R','player1 L','player1 R','player2 L','player2 R','input L','input R']},indent=2)+'\n')
print('Ready:',case,OUT/'check.pd')
