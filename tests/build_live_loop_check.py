"""Build a no-DAC, two-original-player live-loop check. Console: editor-check-run bang.
Reuses the sample editor fixture's stereo source, original mixers, and isolated
901/902 slots. Capture stops at 12s with a separately scheduled 14s watchdog.
"""
from pathlib import Path
import runpy,shutil,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
base=runpy.run_path(str(ROOT/'tests/build_sample_editor_check.py'))
SRC=base['OUT'];OUT=Path('/tmp/plugmlr-live-loop-check')
OUT.mkdir(exist_ok=True)
for p in SRC.iterdir():
 if p.suffix in ('.pd','.pd_lua','.lua') or p.name=='source.wav':
  if p.suffix=='.wav':shutil.copy2(p,OUT/p.name)
  else:(OUT/p.name).write_text(p.read_text().replace(str(SRC),str(OUT)))
p=OUT/'check.pd';s=p.read_text().replace('10s auto-stop','14s auto-stop').replace('delay 10000','delay 14000');s += '\n#X obj 1000 100 sample-data 900;\n'
p.write_text(s)
# Append test-only private commands and probes, with no engine rewiring.
p=OUT/'sample_player_rebuild.pd';s=p.read_text();q=base['Patch'](base['root_count'](s));o,c=q.add,q.wire
r=o('obj 3000 5000 r live-loop-test-\\$1');rt=o('obj 3000 5040 route speed window');c(r,rt)
for i,suf in enumerate(['rate_multiplier','loop-window']):
 send=o(f'obj {3000+i*220} 5080 s \\$0-{suf}');c(rt,send,i)
for j,suf in enumerate(['loop_target_index','loop-region-feedback','samples_per_ms','is_paused_flag']):
 r=o(f'obj {3000+j*200} 5160 r \\$0-{suf}');tag=o(f'obj {3000+j*200} 5200 list prepend \\$1-{suf}');send=o(f'obj {3000+j*200} 5240 s editor-check-log');c(r,tag);c(tag,send)
p.write_text((s+'\n'+q.text()).replace('r ppq;', 'r live-loop-ppq;'))
score=[]
def at(t,r,m='bang'):score.append((t,r,m))
def win(t,sel,v):at(t,'901-loop-window',f'{sel} {v}')
at(0,'901-sample-path',f'symbol {OUT}/source.wav');at(40,'902-sample-path',f'symbol {OUT}/source.wav')
at(100,'901-buffer-select','sample 901');at(100,'902-buffer-select','sample 901')
at(130,'audio-901-out','0.4');at(130,'audio-902-out','0.3')
at(200,'901-press_play');at(200,'902-press_play')
win(1000,'end',2);win(1000,'start',1);win(1100,'move',1.2)
win(1300,'end',1.45);win(1500,'move',2)
at(1800,'editor-test-901','reverse');win(2000,'move',2.5);win(2200,'start',2.6)
win(2400,'end',2.62);win(2800,'move',2.8)
win(3000,'start',3);win(3030,'end',2.9) # cross-clamp to one frame, then expand
win(3200,'end',1);win(3230,'start',2.7) # opposite crossing, then expand
win(3400,'move',99);win(3600,'move',-1) # preserve length at content edges
at(3800,'row_901','8') # ordinary cut restores full content
at(4000,'editor-test-901','reverse')
# Continuous control burst through the public interface, including overlapping cuts.
win(4200,'end',1);win(4200,'start',0.75)
for n in range(80):win(4300+n*5,'move',0.75+n*.025)
at(4500,'row_901','4')
win(4800,'end',3.2);win(4800,'start',3)
at(4900,'live-loop-test-901','speed 2')
win(5100,'move',2);at(5300,'live-loop-test-901','speed 0.5');win(5500,'move',1.5)
at(5700,'901-press_play') # Pause
win(5800,'move',1.7);win(5850,'start',1.72);at(6000,'901-press_play')
at(6300,'editor-test-901','stop');win(6400,'move',2.3);at(6500,'901-press_play')
win(6750,'bogus',2);at(6755,'901-loop-window','start bad');at(6760,'901-loop-window','start 1 2')
# Buffer switching and empty requests must not mutate the next target.
at(7000,'901-buffer-select','sample 902');win(7001,'move',3)
at(7200,'901-buffer-select','sample 900');win(7250,'move',1)
at(7400,'901-buffer-select','sample 901')
at(7700,'editor-test-901','stop');at(7700,'editor-test-902','stop')
# Nonzero content origin and stopped edits; buffer trimming deliberately stops readers.
at(7800,'901-sample-edit','trim 1 3')
win(7900,'end',2);win(7900,'start',1.5);win(7950,'move',-1)
at(8000,'901-press_play');at(8300,'row_901','8')
at(8700,'editor-test-901','stop')
# Minimum uses current rate even while stopped; allow widening after speed rises.
at(8800,'live-loop-test-901','speed 4')
win(8810,'end',1);win(8820,'start',1.5)
at(8850,'live-loop-test-901','speed 0.5')
win(8900,'end',2.8);win(8900,'start',2.4)
at(8900,'901-quantizer','0');at(9000,'901-press_play')
at(9200,'row_901','0');at(9300,'live-loop-ppq','0')
at(9500,'editor-test-901','stop');at(9550,'901-quantizer','1')
at(9600,'901-open-player-view')
at(12000,'editor-check-stop')
last=0;lines=[]
for t,r,m in sorted(score,key=lambda v:v[0]):lines.append(f'{t-last} {r} {m};');last=t
(OUT/'score.txt').write_text('\n'.join(lines)+'\n')
manifest=json.loads((SRC/'source.json').read_text());manifest.update(base='9aa7b74ab9b43b1c07d34903c05651e28b826590',score=score)
manifest['fixture_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.suffix in ('.pd','.pd_lua')}
(OUT/'source.json').write_text(json.dumps(manifest,indent=2)+'\n')
for p in OUT.glob('*.pd'):
 errors=base['check'](p)['errors']
 assert not errors,(p,errors)
print(OUT/'check.pd')
