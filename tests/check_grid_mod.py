from pathlib import Path
import subprocess
base='d8f843d78863887bbad2f628bf7bfeafaf7490e9'
for p in ['mlr.pd','sample_player_rebuild.pd','grid-loop-region.pd','loop-region-control.pd','loop-region-live.pd','grid-cut-control.pd','grid-playback-state.pd','grid-playback-row.pd','grid-row-leds.pd_lua','mlr-grid-compat.pd_lua']:
 assert Path(p).read_bytes()==subprocess.check_output(['git','show',f'{base}:{p}']),p
print('PASS: MOD adds input handling only; exact accepted player, loop, display and device paths')
