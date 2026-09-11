from pathlib import Path
import subprocess
from check_patch_connections import check
base='a46451003d5b7bf2a6104d2896266f0e53169f8c'
def old(p):return subprocess.check_output(['git','show',f'{base}:{p}'],text=True)
s=Path('mlr.pd').read_text().replace('#X obj -20 1500 grid-cut-control;\n','').replace('#X connect 7 0 83 0;\n#X connect 83 0 67 0;','#X connect 7 0 67 0;')
assert s==old('mlr.pd')
for p in ['sample_player_rebuild.pd','grid-playback-row.pd','grid-playback-state.pd','mlr-grid.pd']:
    assert Path(p).read_text()==old(p),p
for p in ['mlr.pd','grid-cut-control.pd','tests/grid-cut-keys-check.pd']:
    assert not check(Path(p))['errors'],p
print('PASS: single input interception; original DSP, quantizer, transport and row renderers unchanged')
