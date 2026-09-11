"""This slice can only change read-only display components, not the player."""
from pathlib import Path
import subprocess
from check_patch_connections import check
base='19245a00b974c0e48ed79157f1c9ef542392377b'
for p in ['mlr.pd','sample_player_rebuild.pd','loop-region-control.pd','loop-region-live.pd','grid-loop-region.pd','grid-cut-keys.pd_lua','grid-cut-control.pd','mlr-grid-compat.pd_lua']:
 assert Path(p).read_bytes()==subprocess.check_output(['git','show',f'{base}:{p}']),p
for p in ['grid-playback-state.pd','grid-playback-row.pd','tests/grid-feedback-check.pd']:
 assert not check(Path(p))['errors'],p
for p in ['grid-playback-state.pd','grid-playback-row.pd','grid-row-leds.pd_lua']:
 s=Path(p).read_text()
 assert not any(v in s for v in ['-play_button','-stop_button','-selected_slice','-loop-region-request','pd.Clock','metro ']),p
print('PASS: exact original playback, gestures and device boundary; read-only display changes only')
