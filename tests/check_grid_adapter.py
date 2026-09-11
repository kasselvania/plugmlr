"""Historical connector-only boundary. Current feedback: check_grid_feedback.py."""
from pathlib import Path
import subprocess
base = subprocess.check_output(['git', 'show', 'ac8956e291ab6aa1c8d7f5ab4c84334d4eec3c4a:mlr.pd'], text=True)
current = subprocess.check_output(['git', 'show', 'fa6812cc02e829153c65a20bf036c83172d218da:mlr.pd'], text=True)
current = current.replace('mlr-grid 17879 17880 12002;', 'monome-object;')
current = '\n'.join(l for l in current.splitlines() if 'bng 30 250 50 0 mlr-grid-open ' not in l) + '\n'
assert current == base, 'Unrelated MLR objects or wires changed'
assert not Path('monome-object.pd').exists()
assert 'dependencies/monome/monome-grid-live-slot' in Path('mlr-grid.pd').read_text()
assert subprocess.check_output(['git', '-C', 'dependencies/monome', 'rev-parse', 'HEAD'], text=True).strip() == '18b489399d01a9178e4667b849ec4368d72533db'
print('PASS: only connector and open-panel button changed; original musical/DSP wiring exact; dependency pinned')
