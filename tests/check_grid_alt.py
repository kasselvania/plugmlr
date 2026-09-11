from grid_loop_boundary import without_region_query
from pathlib import Path
import subprocess
from check_patch_connections import check
base='a46451003d5b7bf2a6104d2896266f0e53169f8c'
def old(p):return subprocess.check_output(['git','show',f'{base}:{p}'],text=True)
s=Path('mlr.pd').read_text().replace('#X obj -20 1500 grid-cut-control;\n','').replace('#X connect 7 0 83 0;\n#X connect 83 0 67 0;','#X connect 7 0 67 0;')
assert s==old('mlr.pd')
for p in ['sample_player_rebuild.pd','mlr-grid.pd']:
    assert without_region_query(Path(p).read_text()).replace('#X obj 1700 4350 grid-loop-region \\$0 \\$1;\n','').replace('\n#X connect 525 0 142 0;\n','')==old(p),p
for p in ['mlr.pd','grid-cut-control.pd','tests/grid-cut-keys-check.pd']:
    assert not check(Path(p))['errors'],p
print('PASS: ALT baseline preserved after removing the explicit Grid-loop helper and queued-cut cancellation wire')

# The later display-only slice is guarded separately by check_grid_loop_feedback.py.
