"""Historical PR22 extraction check plus current display-only/index checks.
Run from the repo root: python3 tests/check_player_panel.py
Native interaction and user usability remain separate from this check.
"""
from pathlib import Path
import subprocess
BASE='3d349dc8527de4598fd11f2c99c3805465528590'

def parse(text):
 stack=[];canvases=[]
 for line in text.splitlines():
  if line.startswith('#N canvas'): stack.append({'objects':[], 'connections':[]})
  elif line.startswith('#X restore'):
   canvases.append(stack.pop());stack[-1]['objects'].append(line)
  elif line.startswith('#X connect'):stack[-1]['connections'].append(line)
  elif line.startswith(('#X obj','#X msg','#X text','#X floatatom','#X symbolatom','#X array')):stack[-1]['objects'].append(line)
 canvases.extend(stack)
 for canvas in canvases:
  for line in canvas['connections']:
   t=line.split();assert max(int(t[2]),int(t[4]))<len(canvas['objects']),line
 return canvases

for name in ['sample_player_rebuild.pd','mlr.pd','player-panel.pd','player-panel-state.pd','clock-display-state.pd']:
 text=Path(name).read_text();parse(text)
 if name in ['sample_player_rebuild.pd','mlr.pd']:
  text=subprocess.check_output(['git','show','610098f:'+name],text=True)
 if name in ['sample_player_rebuild.pd','mlr.pd']:
  old=subprocess.check_output(['git','show',BASE+':'+name],text=True)
  assert [l for l in old.splitlines() if l.startswith('#X connect')]==[l for l in text.splitlines() if l.startswith('#X connect')],name
  if name=='sample_player_rebuild.pd':
   before=parse(old);after=parse(text)
   assert len(before)==len(after)
   # All existing nested DSP/control canvases retain their objects. One malformed
   # comment delimiter is repaired, without changing an object or connection.
   for a,b in zip(before[:-1],after[:-1]):
    assert [l for l in a['objects'] if not l.startswith('#X text')]==[l for l in b['objects'] if not l.startswith('#X text')]
   allowed={0,1,2,3,4,5,6,7,10,11,12,13,14,15,16,17,18,21,22,25,452,453,454,455,526,541,550}
   changed={i for i,(a,b) in enumerate(zip(before[-1]['objects'],after[-1]['objects'])) if a!=b}
   assert changed==allowed,changed^allowed
   assert len(after[-1]['objects'])==len(before[-1]['objects'])+1
   assert 'beat-reset' in after[-1]['objects'][19] # still one original reset engine
 else:
  assert not any('~' in l for l in text.splitlines() if l.startswith('#X obj')),name
  if name=='player-panel-state.pd':
   assert not any(('s \\$1-' in l or 's \\$2-' in l) for l in text.splitlines()),'display must not command engine'
assert 'beat-reset ' not in Path('player-panel.pd').read_text(),'view must not duplicate reset engine'
print('PASS: historical PR22 extraction preserved DSP/control wiring; current views have valid indexes and no engine sends (current engine: check_tempo_fit.py)')
