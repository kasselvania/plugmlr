"""Original player/mixer + actual Grid gesture class; no DAC or device claim.
Run with --baseline for PR43 before slice launch; console: editor-check-run bang.
The capture stops at 15s; an independent 16s watchdog stops recording and players.
"""
from pathlib import Path
import runpy,shutil,json,hashlib,sys,subprocess,math,struct,wave,re
ROOT=Path(__file__).resolve().parents[1]
base=runpy.run_path(str(ROOT/'tests/build_sample_editor_check.py'))
SRC=base['OUT'];baseline='--baseline' in sys.argv
OUT=Path('/tmp/plugmlr-grid-launch-'+('before' if baseline else 'after'));OUT.mkdir(exist_ok=True)
for f in SRC.iterdir():
 if f.suffix in ('.pd','.pd_lua','.lua'):
  (OUT/f.name).write_text(f.read_text().replace(str(SRC),str(OUT)))
# Baseline uses the same test-only probes; production source is replaced before appending them.
p=OUT/'sample_player_rebuild.pd'
if baseline:
 old=subprocess.check_output(['git','show','62b7b4a:sample_player_rebuild.pd'],cwd=ROOT,text=True)
 new=(ROOT/'sample_player_rebuild.pd').read_text()
 # Builder appended probes by root object index. Rebuild them against the old root.
 suffix=p.read_text()[len(new):]
 delta=base['root_count'](new)-base['root_count'](old)
 suffix=re.sub(r'(#X connect )(\d+)( \d+ )(\d+)',lambda m:m[1]+str(int(m[2])-delta)+m[3]+str(int(m[4])-delta),suffix)
 p.write_text(old+suffix)
 (OUT/'pending-cut-delay.pd').write_text(subprocess.check_output(['git','show','62b7b4a:pending-cut-delay.pd'],cwd=ROOT,text=True))
# Passive trajectory and transport probes; ppq remains local to this fixture.
s=p.read_text();q=base['Patch'](base['root_count'](s));o,c=q.add,q.wire
for j,key in enumerate(['loop_target_index','is_paused_flag','selected_slice','slice-loop-allowed','mixer_env_open']):
 r=o(f'obj {3000+j*200} 5100 r \\$0-{key}');tag=o(f'obj {3000+j*200} 5140 list prepend \\$1-{key}');send=o(f'obj {3000+j*200} 5180 s editor-check-log');c(r,tag);c(tag,send)
p.write_text((s+'\n'+q.text()).replace('r ppq;','r launch-check-ppq;'))
vals=[]
for i in range(4*44100):
 t=i/44100;cell=min(15,int(t*4));f=160+40*cell
 vals.extend((int(6000*math.sin(2*math.pi*f*t)),int(3000*math.sin(2*math.pi*(f*1.25)*t))))
with wave.open(str(OUT/'source.wav'),'wb') as w:
 w.setnchannels(2);w.setsampwidth(2);w.setframerate(44100);w.writeframes(struct.pack('<'+'h'*len(vals),*vals))
# Add the actual Grid classifier, map its two test rows onto isolated players.
s=(OUT/'check.pd').read_text().replace('10s auto-stop','16s watchdog').replace('delay 10000','delay 16000')
q=base['Patch'](base['root_count'](s));o,c=q.add,q.wire
o('obj 900 100 sample-data 900')
source=subprocess.check_output(['git','show','62b7b4a:grid-cut-keys.pd_lua'],cwd=ROOT) if baseline else (ROOT/'grid-cut-keys.pd_lua').read_bytes()
name='launch-keys-'+hashlib.sha256(source).hexdigest()[:10]
(OUT/(name+'.pd_lua')).write_text(source.decode().replace("register('grid-cut-keys')",f"register('{name}')"))
r=o('obj 20 760 r launch-key');keys=o(f'obj 20 800 {name}');c(r,keys)
r=o('obj 220 760 loadbang');m=o('msg 220 800 1');c(r,m);c(m,keys,0,1)
a=o('obj 20 845 unpack f f f');store=o('obj 20 890 f');row=o('obj 150 890 sel 1 2');c(keys,a);c(a,store,0,1);c(a,row,1)
# unpack fires y before x: reorder with the same y/x packing as the original root row route.
t=o('obj 20 825 t l l');c(keys,t);c(t,a,1)
# Right copy sets row, then left copy extracts x and sends it to that row.
rt=o('obj 20 940 list split 1');trim=o('obj 20 980 list trim');dest=o('obj 180 980 send');c(t,rt);c(rt,trim);c(trim,dest)
for i,n in enumerate((901,902)):
 m=o(f'msg {180+i*200} 940 symbol row_{n}');c(row,m,i);c(m,dest,0,1)
r=o('obj 600 845 sel 1 2');c(keys,r,1)
for i,n in enumerate((901,902)):
 send=o(f'obj {600+i*200} 890 s {n}-press_play');c(r,send,i)
r=o('obj 500 940 route 1 2');c(keys,r,4)
for i,n in enumerate((901,902)):
 send=o(f'obj {500+i*200} 980 s {n}-grid-loop-cells');c(r,send,i)
# Cancellation messages from isolated players only. No attachment or hardware traffic.
r=o('obj 900 760 r mlr-grid-cancel');rt=o('obj 900 800 sel 901 902');c(r,rt)
for i in range(2):
 m=o(f'msg {900+i*70} 840 {i+1}');c(rt,m,i);c(m,keys,0,2)
(OUT/'check.pd').write_text(s+'\n'+q.text())
score=[]
def at(t,r,m='bang'):score.append((t,r,m))
def key(t,x,y,z):at(t,'launch-key',f'{x} {y} {z}')
def cut(t,x,y=1):key(t,x,y,1);key(t+3,x,y,0)
def alt(t,y=1):key(t,15,0,1);key(t+1,0,y,1);key(t+2,0,y,0);key(t+3,15,0,0)
def stop(t,y=901):at(t,f'editor-test-{y}','stop')
at(0,'901-sample-path',f'symbol {OUT}/source.wav')
at(100,'901-buffer-select','sample 901');at(100,'902-buffer-select','sample 901')
at(130,'audio-901-out','0.4');at(130,'audio-902-out','0.3')
cut(200,4);alt(700);cut(750,8)
stop(1100);cut(1101,12)
stop(1600);cut(1601,7);stop(1604)
cut(2000,15);stop(2400);at(2450,'editor-test-901','reverse');cut(2500,4)
alt(2900);cut(2950,8);stop(3300)
at(3500,'901-quantizer','0');cut(3550,6);at(3650,'launch-check-ppq','0');alt(3900)
cut(4000,2);stop(4010);at(4100,'launch-check-ppq','0');at(4200,'901-quantizer','1')
at(4250,'901-buffer-select','sample 900');cut(4300,5)
at(4400,'901-buffer-select','sample 901');cut(4401,10);alt(4500)
at(4600,'editor-test-901','reverse');cut(4700,0);stop(4900)
cut(5000,1);key(5200,2,1,1);key(5205,7,1,1);key(5210,7,1,0);key(5215,2,1,0)
cut(5300,9);key(5400,3,1,1);key(5480,7,1,1);key(5520,7,1,0);key(5530,3,1,0)
key(5700,4,1,1);key(5800,10,1,1);key(5880,10,1,0);key(5890,4,1,0)
key(6100,13,0,1);cut(6101,5);key(6110,13,0,0);cut(6200,12)
stop(6400);cut(6500,3,2);cut(6600,1);at(7000,'editor-test-901','reverse');stop(7400);cut(7450,9)
stop(8000);stop(8000,902)
stop(8100);alt(8101);cut(8105,6) # queued Play replaced by slice
stop(8300);cut(8301,10);alt(8305) # queued slice replaced by Play
stop(8500)
for i,value in enumerate(['-1','16','1.5','symbol bad','1 2']):at(8600+i*20,'row_901',value)
for i in range(16):cut(9000+i*150,i)
stop(11500);at(11700,'editor-test-901','reverse')
for i in range(16):cut(11800+i*150,i)
stop(14400);stop(14400,902);at(15000,'editor-check-stop')
last=0;lines=[]
for t,r,m in sorted(score,key=lambda v:v[0]):lines.append(f'{t-last} {r} {m};');last=t
(OUT/'score.txt').write_text('\n'.join(lines)+'\n')
manifest=json.loads((SRC/'source.json').read_text());manifest.update(baseline=baseline,base='62b7b4a30c5717a63db6d842b2194178051d1763',score=score,grid_source_sha256=hashlib.sha256(source).hexdigest())
if baseline:
 for name in ['sample_player_rebuild.pd','pending-cut-delay.pd','grid-cut-keys.pd_lua']:
  manifest['production_sha256'][name]=hashlib.sha256(subprocess.check_output(['git','show','62b7b4a:'+name],cwd=ROOT)).hexdigest()
 manifest['production_source_overrides']='These three baseline files came from 62b7b4a; passive probes and isolated row mapping are fixture-only.'
manifest['fixture_sha256']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in OUT.iterdir() if f.suffix in ('.pd','.pd_lua')}
(OUT/'source.json').write_text(json.dumps(manifest,indent=2)+'\n')
for f in ['check.pd','sample_player_rebuild.pd','pending-cut-delay.pd']:assert not base['check'](OUT/f)['errors'],base['check'](OUT/f)
print(OUT/'check.pd')
