"""Bounded native Clear routing check; original app, disposable generated takes.

Open /tmp/plugmlr-clear-route-check/check.pd ALONE. ui-check-run bang.
2 s score, independent 4 s auto-stop. No DAC output. Never run on user takes.
The earlier protection fixture supplies original buffers, players, mixer and probes.
"""
from pathlib import Path
import hashlib, json, sys
ROOT = Path(__file__).resolve().parents[1]
OUT = Path('/tmp/plugmlr-clear-route-check')
sys.path.insert(0, str(ROOT/'tests'))
code = (ROOT/'tests/build_take_protection_check.py').read_text().replace(
    "Path('/tmp/plugmlr-take-check')", "Path('/tmp/plugmlr-clear-route-check')")
old_args = sys.argv
sys.argv = ['build', 'guards']
ns = {'__file__':str(ROOT/'tests/build_take_protection_check.py'), '__name__':'fixture_builder'}
try:
    exec(compile(code, 'take_fixture', 'exec'), ns)
finally:
    sys.argv = old_args
source = (OUT/'check.pd').read_text().replace('delay 20000;', 'delay 4000;')
Patch = ns['Patch']; p = Patch(ns['count_root'](source))
# Query responses are retained in the existing timestamped event log.
for symbol in ['clear-route-reply', '3_l_b_delete_buffer', '4_l_b_delete_buffer']:
    r=p.add(f'obj 2400 2700 r {symbol}')
    tag=p.add(f'obj 2400 2740 list prepend {symbol}')
    send=p.add('obj 2400 2780 s \\$0-ui-log')
    pr=p.add(f'obj 2700 2780 print {symbol}')
    p.wire(r,tag);p.wire(tag,send);p.wire(r,pr)
(OUT/'check.pd').write_text(source+'\n'+p.text())
# Passive probes on the real panel's ordinary symbols; no alternate action path.
panel=(ROOT/'player-panel.pd').read_text();p=Patch(ns['count_root'](panel))
for symbol in ['\\$1-delete_buffer','\\$0-discard']:
    r=p.add(f'obj 30 1600 r {symbol}')
    pr=p.add(f'obj 30 1640 print UI-{symbol}')
    p.wire(r,pr)
(OUT/'observed-panel.pd').write_text(panel+'\n'+p.text())
f=OUT/'observed-player.pd'
f.write_text(f.read_text().replace('player-panel \\$0 \\$1;', 'observed-panel \\$0 \\$1;'))
score=[]
def at(t,r,m='bang'):score.append((t,r,m))
def query(t,slot):at(t,f'live_buffer_{slot}-view-get','info clear-route-reply')
at(0,'global-transport','0')
for slot in (3,4):
    at(0,f'{slot}_l_b_length','seconds 0.1');at(100,f'{slot}_l_b_record','start')
at(300,'1-buffer-select','live 3');query(400,3);query(400,4)
# Previously both commands reached Live 3 while the UI requested Live 4.
at(500,'1-buffer-select','live 4');at(501,'take-player-1','clear');at(502,'take-player-1','discard')
query(550,3);query(550,4)
# Switching to an imported slot must not erase the former live slot either.
at(600,'1-buffer-select','sample 1');at(601,'take-player-1','clear');at(602,'take-player-1','discard')
query(650,3);query(650,4)
# Settled live selection still uses the original Clear/Discard guard.
at(700,'1-buffer-select','live 3');at(750,'take-player-1','clear');query(760,3)
at(800,'take-player-1','discard');query(850,3);query(850,4)
at(900,'take-player-1','discard');query(950,3)
at(1000,'1-buffer-select','live 4');at(1100,'1-open-player-view')
at(2000,'ui-check-stop')
score.sort(key=lambda x:x[0]);lines=[];last=0
for t,r,m in score:lines.append(f'{t-last} {r} {m};');last=t
(OUT/'score.txt').write_text('\n'.join(lines)+'\n')
manifest=json.loads((OUT/'source.json').read_text())
manifest.update(case='clear-route', duration_ms=2000,watchdog_ms=4000,score=score)
manifest['fixture_sha256']=hashlib.sha256((OUT/'check.pd').read_bytes()).hexdigest()
manifest['fixture_files_sha256']={n:hashlib.sha256((OUT/n).read_bytes()).hexdigest() for n in ['check.pd','observed-player.pd','observed-panel.pd','score.txt']}
(OUT/'source.json').write_text(json.dumps(manifest,indent=2)+'\n')
from check_patch_connections import check
for name in ['check.pd','observed-player.pd','observed-panel.pd']:
    assert not check(OUT/name)['errors']
print('Ready:',OUT/'check.pd')
