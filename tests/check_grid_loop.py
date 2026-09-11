from pathlib import Path
import subprocess
from check_patch_connections import check
base='bf3f628121437f9c05edee2531141f8a9a2f1ca9'
def old(p):return subprocess.check_output(['git','show',f'{base}:{p}'],text=True)
s=Path('sample_player_rebuild.pd').read_text().replace('#X obj 1700 4350 grid-loop-region \\$0 \\$1;\n','').replace('\n#X connect 525 0 142 0;\n','')
assert s==old('sample_player_rebuild.pd')
for p in ['mlr.pd','loop-region-control.pd','grid-playback-row.pd','grid-playback-state.pd']:
 assert Path(p).read_text()==old(p),p
for p in ['sample_player_rebuild.pd','grid-loop-region.pd','grid-cut-control.pd','tests/grid-cut-keys-check.pd','tests/grid-loop-region-check.pd']:
 assert not check(Path(p))['errors'],p
print('PASS: original DSP/region transitions unchanged; only loop bridge and queued-cut cancellation wire added')
