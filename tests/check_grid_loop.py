from grid_loop_boundary import without_region_query
from pathlib import Path
import subprocess
from check_patch_connections import check
base='bf3f628121437f9c05edee2531141f8a9a2f1ca9'
def old(p):return subprocess.check_output(['git','show',f'{base}:{p}'],text=True)
s=without_region_query(Path('sample_player_rebuild.pd').read_text()).replace('#X obj 1700 4350 grid-loop-region \\$0 \\$1;\n','').replace('\n#X connect 525 0 142 0;\n','')
assert s==old('sample_player_rebuild.pd')
for p in ['mlr.pd']:
 assert Path(p).read_text()==old(p),p
for p in ['sample_player_rebuild.pd','grid-loop-region.pd','loop-region-control.pd','loop-region-live.pd','grid-cut-control.pd','tests/grid-cut-keys-check.pd','tests/grid-loop-region-check.pd']:
 assert not check(Path(p))['errors'],p
print('PASS: original DSP preserved; explicit logical-position query, loop bridge and queued-cut cancellation wire only')
# Plain/full Apply and its validator remain exact; keep only adds a dispatch.
legacy=old('loop-region-control.pd')
added='''#X obj 20 75 route keep;
#X obj 200 95 t a b;
#X msg 330 95 1;
#X obj 20 115 t a b;
#X msg 130 115 0;
#X obj 280 805 list prepend 0;
#X obj 280 825 route 0 1;
#X obj 720 805 loop-region-live \\$1;
'''
wires='''#X connect 65 0 66 0;
#X connect 66 1 67 0;
#X connect 67 0 70 1;
#X connect 66 0 3 0;
#X connect 65 1 68 0;
#X connect 68 1 69 0;
#X connect 69 0 70 1;
#X connect 68 0 3 0;
#X connect 70 0 71 0;
#X connect 71 0 39 0;
#X connect 71 1 72 0;
#X connect 72 0 39 0;
'''
i=legacy.index('#X connect')
expected=legacy[:i]+added+legacy[i:]
expected=expected.replace('#X connect 1 0 3 0;','#X connect 1 0 65 0;').replace('#X connect 2 0 3 0;','#X connect 2 0 65 0;').replace('#X connect 35 0 39 0;','#X connect 35 0 70 0;')+wires
assert Path('loop-region-control.pd').read_text()==expected
print('PASS: existing plain/full validation and Apply preserved behind explicit keep dispatch')

# The later display-only slice is guarded separately by check_grid_loop_feedback.py.
