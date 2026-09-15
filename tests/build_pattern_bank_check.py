"""Native bank integration plus the prior 77-command regression. No DAC/recording.
Open /tmp/plugmlr-pattern-bank/check.pd; automatic score stops at14.6s (18s watchdog).
"""
from pathlib import Path
import runpy,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
b=runpy.run_path(str(ROOT/'tests/build_performance_pattern_check.py'))
OUT=Path('/tmp/plugmlr-pattern-bank');OUT.mkdir(exist_ok=True)
for f in b['OUT'].iterdir():
 if f.suffix in ('.pd','.pd_lua','.lua'):
  (OUT/f.name).write_text(f.read_text().replace(str(b['OUT']),str(OUT)))
 elif f.name=='source.wav':(OUT/f.name).write_bytes(f.read_bytes())
f=OUT/'check.pd';f.write_text(f.read_text().replace('delay 9000','delay 18000').replace('9 second stop','18 second stop'))
score=[(t,r,m.replace(str(b['OUT']),str(OUT))) for t,r,m in b['score'] if r!='pcheck-finish']
def at(t,r,m):score.append((t,r,m))
def tap(t,x,y=0):at(t,'pcheck-input',f'{x} {y} 1');at(t+1,'pcheck-input',f'{x} {y} 0')
def clear(t,i):
 at(t,'pcheck-input','15 0 1');tap(t+1,i+3);at(t+2,'pcheck-input','15 0 0')
clear(9000,1);at(9100,'901-quantizer','1');tap(9100,1)
# Switching away from recording1 retains its complete200ms phrase.
tap(9200,4);tap(9260,0,1);tap(9400,5);tap(9460,1,2);tap(9600,5)
# Switch to3 before2's first replayed cut. Inactive Clear must not interrupt3.
for i in range(3,9):
 t=9650+(i-3)*450
 tap(t,i+3);tap(t+60,i-1,1 if i%2 else 2);tap(t+200,i+3)
clear(9860,1)
at(12400,'pcheck-command','stop')
# Slot1 takes a new phrase with its own direction/speed state.
tap(12450,4);at(12500,'901-grid-reverse','bang');at(12530,'901-grid-set-speed','3');tap(12560,8,1);tap(12650,4)
tap(12800,5);clear(12810,8)
# MOD does not act on slots; duplicates/releases do not toggle twice.
at(12840,'pcheck-input','13 0 1');tap(12841,6);at(12843,'pcheck-input','13 0 0')
tap(12900,7);clear(12980,4);clear(13000,2)
tap(13100,8);tap(13120,0) # Page switch preserves bank LED state.
at(13200,'pcheck-input','9 0 1');at(13200.2,'pcheck-input','9 0 1');at(13210,'pcheck-input','9 0 0')
at(13300,'pcheck-connected','0');at(13350,'pcheck-connected','1')
tap(13500,10);at(13600,'pcheck-pd','dsp 0');at(13610,'pcheck-pd','dsp 1')
# Disconnect while recording finishes and retains the take; reconnect stays stopped.
tap(13800,11);tap(13810,1);tap(13860,9,2);at(13900,'pcheck-connected','0');at(13950,'pcheck-connected','1');tap(14000,11)
at(14010,'pcheck-command','toggle 9');at(14011,'pcheck-command','clear 0');clear(14020,6)
tap(14100,9) # Empty6 records nothing: old8's replay must not feed it.
tap(14400,10);clear(14500,7);at(14600,'pcheck-finish','bang')
last=0;lines=[]
for t,r,m in sorted(score,key=lambda v:v[0]):lines.append(f'{t-last} {r} {m};');last=t
(OUT/'score.txt').write_text('\n'.join(lines)+'\n')
manifest=b['manifest'];manifest.update(bank=True,bank_base='d25b266364fc2b52821cf5c6751614b49d90ae85',score=score)
manifest['fixture_sha256']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in OUT.iterdir() if f.suffix in ('.pd','.pd_lua') or f.name in ('source.wav','score.txt')}
(OUT/'source.json').write_text(json.dumps(manifest,indent=2)+'\n')
for name in ['check.pd','pattern-control.pd','sample_player_rebuild.pd']:assert not b['check'](OUT/name)['errors']
print(OUT/'check.pd')
