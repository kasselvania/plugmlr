"""Finite original-writer test with private stereo input and an independent stop deadline."""
from pathlib import Path
import runpy,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
b=runpy.run_path(str(ROOT/'tests/build_grid_buffer_check.py'));OUT=Path('/tmp/plugmlr-grid-record');OUT.mkdir(exist_ok=True)
for f in b['OUT'].iterdir():
 if f.suffix in ('.pd','.pd_lua','.lua'):(OUT/f.name).write_text(f.read_text().replace(str(b['OUT']),str(OUT)))
 elif f.name=='source.wav':(OUT/f.name).write_bytes(f.read_bytes())
name='gr'+hashlib.sha256((ROOT/'grid-record-control.pd_lua').read_bytes()).hexdigest()[:8]+'-grid-record-control'
s=(ROOT/'grid-record-control.pd_lua').read_text().replace("register('grid-record-control')",f"register('{name}')").replace("row..'-grid-","(row+900)..'-grid-").replace('n>=1 and n<=16','n>=901 and n<=916').replace('for slot=1,16','for slot=901,916')
(OUT/(name+'.pd_lua')).write_text(s)
f=OUT/'pattern-control.pd';f.write_text(f.read_text().replace(' grid-record-control;',f' {name};'))
Patch=b['Patch'];count=b['count'];f=OUT/'check.pd';s=f.read_text().replace('delay 27000','delay 32000').replace('Pattern check - two isolated players - no DAC or recording - 27 second stop','Grid Record/Finish - private stereo writer - no DAC - 32 second stop').replace('sig~ 0;','osc~ 220;').replace('s~ bcheck-input-record-input;', 's~ bcheck-input-record-input 2;')
s=s.replace('\\; pcheck-connected 0',' '.join('\\; '+str(i)+'_l_b_record stop' for i in range(901,917))+' \\; pcheck-connected 0')
p=Patch(count(s));o,c=p.add,p.wire
# Replace the two equal channels with distinct modest stereo tones; no DAC.
lines=s.splitlines();objects=[l for l in lines if l.startswith(('#X obj','#X msg','#X text'))]
sig=next(i for i,l in enumerate(objects) if 'osc~ 220;' in l);snake=next(i for i,l in enumerate(objects) if '1900 60 snake~ in 2' in l)
s=s.replace(f'#X connect {sig} 0 {snake} 0;','').replace(f'#X connect {sig} 0 {snake} 1;','')
gain=o('obj 1950 20 *~ 0.1');right=o('obj 2050 20 osc~ 330');rg=o('obj 2050 60 *~ 0.2');c(sig,gain);c(gain,snake);c(right,rg);c(rg,snake,0,1)
for slot in range(901,905):
 for field in ('recording','last_index','record_error'):
  r=o(f'obj 2100 100 r {slot}_l_b_{field}');tag=o(f'obj 2100 140 list prepend writer {slot} {field}');send=o('obj 2100 180 s pcheck-log');c(r,tag);c(tag,send)
 r=o(f'obj 2100 220 r {slot}-grid-record');tag=o(f'obj 2100 260 list prepend record-led {slot}');send=o('obj 2100 300 s pcheck-log');c(r,tag);c(tag,send)
 r=o(f'obj 2100 340 r export-{slot}');msg=o(f'msg 2100 380 write -wave -bytes 4 {OUT}/take{slot}.wav 0-live_buffer_{slot} 1-live_buffer_{slot}');writer=o('obj 2100 420 soundfiler');c(r,msg);c(msg,writer)
f.write_text(s+'\n'+p.text())
score=[(t,r,m.replace(str(b['OUT']),str(OUT))) for t,r,m in b['score'] if r!='pcheck-finish']
def at(t,r,m='bang'):score.append((t,r,m))
def key(t,x,y,z):at(t,'pcheck-input',f'{x} {y} {z}')
def tap(t,x,y=0):key(t,x,y,1);key(t+1,x,y,0)
at(18800,'pcheck-command','stop');tap(18810,0)
at(18820,'901-buffer-select','live 901');at(18820,'902-buffer-select','live 901')
at(18820,'901_l_b_length','dynamic');at(18820,'bcheck-input-record-allowed','0')
tap(18900,0,1) # Unarmed: no ownership.
at(19000,'bcheck-input-record-allowed','1');tap(19010,0,1)
tap(19100,0,2) # Another track cannot finish this take.
at(19120,'901-buffer-select','sample 901');tap(19310,0,1) # Finishes remembered Live1.
at(19400,'901-buffer-select','live 901');tap(19440,0,1) # Existing content refuses start.
at(19500,'901-buffer-select','live 902');tap(19501,0,1) # During handoff: refused.
at(19530,'902_l_b_length','seconds 0.2');tap(19550,0,1) # Automatic fixed finish.
at(19800,'901-buffer-select','live 903');at(19800,'903_l_b_length','dynamic');tap(19830,0,1)
at(19900,'903_l_b_record','stop') # External Finish clears remembered take.
at(20000,'901-buffer-select','live 904');at(20000,'904_l_b_length','dynamic');key(20030,0,1,1)
key(20031,0,1,1) # Duplicate cannot finish.
at(20100,'pcheck-connected','0');at(20120,'pcheck-connected','1') # Detach doesn't end audio take.
key(20121,0,1,0);tap(20230,0,1)
for slot in range(901,905):at(20400,'export-'+str(slot))
at(20500,'pcheck-finish')
last=0;lines=[]
for t,r,msg in sorted(score,key=lambda v:v[0]):lines.append(f'{t-last} {r} {msg};');last=t
(OUT/'score.txt').write_text('\n'.join(lines)+'\n')
m=b['m'];m.update(grid_record=True,record_base='4c3caff961680a9207c52022ee2244e4b34bd1c1',score=score)
m['fixture_changes']+=' Record bridge private track/slot IDs901+. Actual original writer records 220Hz L at0.1 and330Hz R at0.2. Native buffer exports after Finish. Independent32s watchdog finishes all private writers. No DAC or user input.'
m['fixture_sha256']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in OUT.iterdir() if f.suffix in ('.pd','.pd_lua','.lua') or f.name=='score.txt'}
(OUT/'source.json').write_text(json.dumps(m,indent=2)+'\n')
print(OUT/'check.pd')
