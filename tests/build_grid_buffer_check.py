"""Finite native BUFFER page check, retaining 115 timeline/bank replay cases.
Private players/slots901..916; no DAC, capture, Grid ownership or global DSP change.
"""
from pathlib import Path
import runpy,json,hashlib,re
ROOT=Path(__file__).resolve().parents[1]
b=runpy.run_path(str(ROOT/'tests/build_pattern_bank_check.py'));base=b['b'];Patch=base['Patch'];count=base['count'];check=base['check'];prefix=base['prefix']
OUT=Path('/tmp/plugmlr-grid-buffer');OUT.mkdir(exist_ok=True)
for f in b['OUT'].iterdir():
 if f.suffix in ('.pd','.pd_lua','.lua'):(OUT/f.name).write_text(f.read_text().replace(str(b['OUT']),str(OUT)))
 elif f.name=='source.wav':(OUT/f.name).write_bytes(f.read_bytes())
# Fixture slots retain original metadata formats, normalized only at LED observer.
f=OUT/(prefix+'grid-page-leds.pd_lua');s=f.read_text().replace('local slot=a[1]','local slot=a[1]-900').replace('local slot=tonumber(n)','local slot=n and tonumber(n)-900')
f.write_text(s)
f=OUT/'buffer-selection.pd';f.write_text(f.read_text().replace('$f2 <= 902','$f2 <= 916'))
# Private-ID copy of the Clear guard; production slot bounds stay 1..16.
s=(ROOT/'take-clear-control.pd_lua').read_text().replace("register('take-clear-control')","register('bcheck-take-clear-control')").replace('self.slot < 1 or self.slot > 16','self.slot < 901 or self.slot > 916')
(OUT/'bcheck-take-clear-control.pd_lua').write_text(s)
f=OUT/'live_buffer.pd';f.write_text(f.read_text().replace(' take-clear-control ', ' bcheck-take-clear-control '))
f=OUT/'sample-data.pd';f.write_text(f.read_text().replace('364966','4')) # Tiny empty storage; loads still resize normally.
f=OUT/'pattern-control.pd';s=f.read_text().replace('makefilename 90%d-buffer-select;', 'makefilename 90%d-grid-buffer-test;');p=Patch(count(s));o,c=p.add,p.wire
for out,label in [(9,'assignment'),(3,'display'),(7,'screen'),(4,'loop'),(1,'play')]:
 t=o('obj 1500 20 list prepend '+label);l=o('obj 1500 60 s pcheck-log');c(2,t,out);c(t,l)
f.write_text(s+'\n'+p.text())
f=OUT/'check.pd';s=f.read_text().replace('delay 18000','delay 27000').replace('18 second stop','27 second stop')
# Replace placeholder live arrays/views with the actual buffer components below.
s=re.sub(r'#X obj ([^;]+) array define [01]-live_buffer_90[12] 4;',r'#X text 20 1800 ;',s)
s=re.sub(r'#X obj [^;]+buffer-view-data live 90[12];',r'#X text 20 1800 ;',s)
s=s.replace('\\; pcheck-connected 0',' '.join('\\; editor-test-'+str(i)+' stop' for i in range(903,907))+' \\; pcheck-connected 0')
p=Patch(count(s));o,c=p.add,p.wire
sig=o('obj 1900 20 sig~ 0');stereo=o('obj 1900 60 snake~ in 2');send=o('obj 1900 100 s~ bcheck-input-record-input');c(sig,stereo,0,0);c(sig,stereo,0,1);c(stereo,send)
for slot in range(901,917):
 o(f'obj 1400 {20+(slot-901)*30} live_buffer {slot} bcheck-input')
 if slot>902:o(f'obj 1600 {20+(slot-901)*30} sample-data {slot}')
for row in range(1,7):
 track=900+row
 if row>2:o(f'obj 1400 {550+row*30} sample_player_rebuild {track}')
 r=o(f'obj 1400 780 r {track}-grid-buffer-test');route=o('obj 1400 820 route sample live');c(r,route)
 for port,kind in enumerate(('sample','live')):
  add=o('obj 1400 860 + 900');pre=o('obj 1400 900 list prepend '+kind);trim=o('obj 1400 940 list trim');dst=o(f'obj 1400 980 s {track}-buffer-select')
  c(route,add,port);c(add,pre);c(pre,trim);c(trim,dst)
 for field in ('buffer','switching','playing','paused','ready'):
  r=o(f'obj 1700 780 r {track}-grid-{field}');t=o(f'obj 1700 820 list prepend selected {row} {field}');d=o('obj 1700 860 s pcheck-log');c(r,t);c(t,d)
f.write_text(s+'\n'+p.text())
score=[(t,r,m.replace(str(b['OUT']),str(OUT))) for t,r,m in b['score'] if r!='pcheck-finish']
def at(t,r,m='bang'):score.append((t,r,m))
def key(t,x,y,z):at(t,'pcheck-input',f'{x} {y} {z}')
def tap(t,x,y=0):key(t,x,y,1);key(t+1,x,y,0)
def enter(t):key(t,15,0,1);tap(t+1,14);key(t+2,15,0,0)
at(14600,'pcheck-command','stop');enter(14700)
# Bank browse while player2 is running must not touch either player.
tap(14800,15,7);tap(14850,0,7)
# Every track uses actual buffer-selection and committed ID readback.
for row in range(1,7):tap(15000+row*80,1,row)
# Explicit external/on-screen-path selection updates LEDs, not just Grid request.
at(15600,'901-buffer-select','sample 901')
# Rapid latest-wins requests; at15725 only the last slot may be installed.
tap(15700,1,1);tap(15705,15,1);tap(15710,0,1)
# Empty slots can be assigned; populated live metadata from original buffer publication.
tap(15900,15,7);tap(16000,15,1)
at(16100,'916_l_b_first_index','0');at(16100,'916_l_b_last_index','4');at(16100,'916_l_b_first_record_complete','1');at(16101,'916_l_b_select_bang')
tap(16200,15,2)
# Reselect then switch while paused; no implicit launch from paused.
at(16300,'902-grid-play');tap(16400,0,7);tap(16450,0,2)
# Clear live metadata via existing owner (no live user buffer touched).
at(16600,'916_l_b_last_index','0');at(16600,'916_l_b_first_record_complete','0');at(16601,'916_l_b_select_bang')
# Modifiers suppress assignment/bank toggle, unknown keys and duplicates inert.
key(16700,13,0,1);tap(16710,5,3);tap(16720,15,7);key(16730,13,0,0)
key(16800,15,0,1);tap(16810,6,3);tap(16820,15,7);key(16830,15,0,0)
key(16900,2,3,1);key(16901,2,3,1);tap(16910,15,7);key(16920,2,3,1);key(16930,2,3,0);tap(16950,2,3)
# Hold a buffer key across navigation: release must never become a slice.
key(17100,6,4,1);tap(17110,1);key(17120,6,4,1);key(17130,6,4,0)
# CUT pair cancelled entering BUFFER, no late loop commit.
key(17200,2,1,1);key(17210,7,1,1);enter(17300);key(17320,7,1,0);key(17330,2,1,0)
# Bank retained on re-entry; pattern slots available while BUFFER is displayed.
tap(17500,6);at(17750,'pcheck-command','stop')
at(17800,'pcheck-connected','0');key(17810,8,5,1);at(17820,'pcheck-connected','1');key(17830,8,5,0)
tap(17900,15,6);tap(18000,0);tap(18050,1);enter(18100)
# Final state change from original buffer load/trim metadata, independent of assignment.
at(18200,'916-sample-path',f'symbol {OUT}/source.wav');tap(18300,0,7);tap(18400,15,5)
at(18600,'editor-test-901','stop');at(18600,'editor-test-902','stop')
at(18700,'pcheck-finish')
last=0;lines=[]
for t,r,msg in sorted(score,key=lambda v:v[0]):lines.append(f'{t-last} {r} {msg};');last=t
(OUT/'score.txt').write_text('\n'.join(lines)+'\n')
m=b['manifest'];m.update(grid_buffers=True,files=True,buffer_base='42c4754d8e8bc2e6a26d4f35891a4d6653497c58',score=score)
m['fixture_changes']='Private musical/player buses and unique Lua classes inherited from pattern suite. Actual players901..906; actual sample/live slots901..916. Grid assignment fixture adds900 to slot; LED observer subtracts900 from metadata/IDs and rejects ordinary session slots. Empty sample allocation starts4 frames. Fixture-only Clear guard accepts901..916; explicit silent stereo input bus. Seeded live content metadata tests selection, not recording. No DAC/capture or device commands.'
m['fixture_sha256']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in OUT.iterdir() if f.suffix in ('.pd','.pd_lua','.lua') or f.name in ('source.wav','score.txt')}
(OUT/'source.json').write_text(json.dumps(m,indent=2)+'\n')
for name in ('check.pd','pattern-control.pd','grid-playback-state.pd'):assert not check(OUT/name)['errors'],check(OUT/name)
print(OUT/'check.pd')
