"""Build bounded native waveform/export checks around the complete original application.

Open /tmp/plugmlr-waveform-check/check.pd alone in plugdata; send
`ui-check-run bang`. Capture stops at 14 seconds, independently at 15 seconds.
Only the copied DAC/input and test-only command/audio/message taps differ.
"""
from pathlib import Path
import hashlib,json,runpy,subprocess,sys,struct,math,wave
ROOT=Path(__file__).resolve().parents[1]
OUT=Path('/tmp/plugmlr-waveform-check')
# Reuse the original whole-application mixer fixture builder.
code=(ROOT/'tests/build_ui_overview_check.py').read_text().replace("Path('/tmp/plugmlr-ui-check')",'OUT_OVERRIDE')
ns={'__file__':str(ROOT/'tests/build_ui_overview_check.py'),'OUT_OVERRIDE':OUT,'__name__':'fixture_builder'}
exec(compile(code,'build_ui_overview_check.py','exec'),ns)
Patch,count_root=ns['Patch'],ns['count_root']
# An asymmetric short stereo file, including one-frame peaks, tests peak preservation.
frames=4800;values=[]
for i in range(frames):
 l=.2*math.sin(2*math.pi*331*i/48000);r=.1*math.sin(2*math.pi*727*i/48000)
 if i in (13,2047,4799):l=.9
 if i in (27,3111,4798):r=-.8
 values.extend((round(l*32767),round(r*32767)))
with wave.open(str(OUT/'short stereo.wav'),'wb') as f:
 f.setnchannels(2);f.setsampwidth(2);f.setframerate(48000);f.writeframes(struct.pack('<'+'h'*len(values),*values))
# Symlink-free observed player, no production control edits.
player=(ROOT/'sample_player_rebuild.pd').read_text();p=Patch(count_root(player))
r=p.add('obj 2400 4800 r waveform-player-\\$1');route=p.add('obj 2400 4840 route reverse next previous');p.wire(r,route)
for i,suffix in enumerate(['dir_change']):
 s=p.add(f'obj 2400 4880 s \\$0-{suffix}');p.wire(route,s,i)
# Browse commands exercise the very same production helper as the two UI buttons.
b=p.add('obj 2650 4880 buffer-browse \\$0 \\$1')
for out,value in ((1,1),(2,-1)):
 m=p.add(f'msg {2650+out*100} 4840 {value}');p.wire(route,m,out);p.wire(m,b)
(OUT/'observed-player.pd').write_text(player+'\n'+p.text())
source=(OUT/'check.pd').read_text().replace('sample_player_rebuild ','observed-player ')
source=source.replace('obj 490 97 record-input \\$0 1;','text 490 97 TEST: generated stereo input;')
source=source.replace('writesf~ 6;','writesf~ 8;').replace('delay 8000;','delay 15000;')
p=Patch(count_root(source));o,c=p.add,p.wire
left=o('obj 1350 1350 phasor~ 337');sub=o('obj 1350 1390 -~ 0.5');gain=o('obj 1350 1430 *~ 0.5');c(left,sub);c(sub,gain)
right=o('obj 1530 1350 osc~ 811');rg=o('obj 1530 1430 *~ 0.2');c(right,rg)
join=o('obj 1350 1480 snake~ in 2');c(gain,join);c(rg,join,0,1)
send=o('obj 1350 1520 s~ \\$0-record-input 2');c(join,send)
# Locate the existing root recorder by parsing root object positions.
def root_objects(s):
 depth=0;out=[]
 for line in s.splitlines():
  if line.startswith('#N canvas'):depth+=1
  elif line.startswith('#X restore'):
   depth-=1
   if depth==1:out.append(line)
  elif depth==1 and line.startswith(('#X obj ','#X msg ','#X text ','#X floatatom ','#X symbolatom ','#X listbox ')):out.append(line)
 return out
objects=root_objects(source);rec=next(i for i,l in enumerate(objects) if 'writesf~ 8;' in l)
c(gain,rec,0,6);c(rg,rec,0,7)
load=o('obj 1350 1570 loadbang');one=o('msg 1350 1610 1');allow=o('obj 1350 1650 s \\$0-record-allowed');c(load,one);c(one,allow)
# Watchdog must also stop the original writer, independently of the score.
finish=next(i for i,l in enumerate(objects) if 'obj 650 1560 t b b b b;' in l)
stop=o('msg 1350 1710 \\; 3_l_b_record stop');c(finish,stop)
for j,recv in enumerate(['sample_buffer_1-view-info','sample_buffer_2-view-info','live_buffer_3-view-info','waveform-peaks-reply','mlr-save-status','l_b_buffer_states','l_b_record_errors','l_b_storage_events']):
 r=o(f'obj {1350+j*80} 1780 r {recv}');tag=o(f'obj {1350+j*80} 1820 list prepend {recv}');s=o(f'obj {1350+j*80} 1860 s \\$0-ui-log');c(r,tag);c(tag,s)
# A persistent target for numerical peak readback, no GUI or playback commands.
(OUT/'check.pd').write_text(source+'\n'+p.text())
score=[
 (0,'3_l_b_delete_buffer','bang'),
 (0,'1-sample-path',f'symbol {OUT}/input.wav'),
 (30,'2-sample-path',f'symbol {OUT}/short\\ stereo.wav'),
 (100,'1-buffer-select','sample 1'),(100,'2-buffer-select','sample 1'),
 (150,'audio-1-out','0.4'),(150,'audio-2-out','0.3'),(150,'global-transport','1'),
 (300,'1-press_play','bang'),(300,'2-press_play','bang'),
 (500,'1-open-player-view','bang'),
 (1800,'sample_buffer_1-view-get','peaks waveform-peaks-reply'),
 (1900,'3_l_b_length','seconds 3'),(2000,'3_l_b_record','start'),
 (2500,'mlr-save-take',f'save 3 {OUT}/rejected-playing.wav'),
 (3300,'3_l_b_record','stop'),
 (3500,'waveform-player-1','next'),(4000,'waveform-player-1','reverse'),
 (4200,'1-loop-region','0.02 0.08'),
 (4500,'sample_buffer_2-view-get','peaks waveform-peaks-reply'),
 (4700,'waveform-player-1','previous'),(4900,'waveform-player-1','reverse'),
 (5000,'mlr-debug','1'),(5010,'1-ui-stop','bang'),(5050,'1-press_play','bang'),(5100,'mlr-debug','0'),
 (5500,'1-open-player-view','bang'),
 (6000,'ui-check-sample-bank-open','bang'),(6500,'1-open-player-view','bang'),
 (7000,'1-ui-stop','bang'),(7000,'2-ui-stop','bang'),(7000,'global-transport','0'),
 (7100,'mlr-save-take',f'save 3 {OUT}/saved\\ take.wav'),
 (7300,'1-buffer-select','live 3'),(7400,'1-open-player-view','bang'),
 (7700,'live_buffer_3-view-get','peaks waveform-peaks-reply'),
 (8000,'mlr-save-take',f'save 16 {OUT}/rejected-empty.wav'),
 (8300,'mlr-save-take',f'save 3 {OUT}/missing-parent/file.wav'),
 (8700,'2-sample-path',f'symbol {OUT}/missing.wav'),
 (8800,'1-buffer-select','sample 2'),
 (9300,'2-sample-path',f'symbol {OUT}/short\\ stereo.wav'),
 (9500,'1-open-player-view','bang'),
 (10200,'2-sample-path',f'symbol {OUT}/input.wav'),
 (10400,'1-open-player-view','bang'),
 (10800,'1-buffer-select','sample 1'),
 (11000,'1-press_play','bang'),(11000,'2-press_play','bang'),
 (11500,'1-open-player-view','bang'),
 (12500,'1-ui-stop','bang'),(12500,'2-ui-stop','bang'),
 (13000,'ui-check-record-takes-open','bang'),(14000,'ui-check-stop','bang')]
last=0;lines=[]
for ms,recv,msg in score:lines.append(f'{ms-last} {recv} {msg};');last=ms
(OUT/'score.txt').write_text('\n'.join(lines)+'\n')
from check_patch_connections import check
for name in ['check.pd','observed-player.pd']: assert not check(OUT/name)['errors'],check(OUT/name)
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.iterdir() if p.suffix in ('.pd','.pd_lua')}
(OUT/'source.json').write_text(json.dumps({'base':'ba52e29507aae512f1c429aba87c9d21e3550ac3','production_sha256':hashes,'fixture_sha256':hashlib.sha256((OUT/'check.pd').read_bytes()).hexdigest(),'score':score,'capture_channels':['master L','master R','player1 L','player1 R','player2 L','player2 R','record input L','record input R'],'host_rate':'read from native WAV','changes':'Original full app; copied DAC disconnected, copied hardware input replaced by test signals; passive taps and bounded score.'},indent=2)+'\n')
print('Ready:',OUT/'check.pd')
