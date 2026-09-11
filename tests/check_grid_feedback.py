"""Exact feedback-only source boundary and Pd graph validation."""
from pathlib import Path
import subprocess
from check_patch_connections import check
BASE='fa6812cc02e829153c65a20bf036c83172d218da'
def old(name):return subprocess.check_output(['git','show',f'{BASE}:{name}'],text=True)
def parse(s):
 stack=[];out={}
 for l in s.splitlines():
  if l.startswith('#N canvas'):stack.append([[],[]])
  elif l.startswith('#X restore'):
   out[l]=stack.pop();stack[-1][0].append(l)
  elif l.startswith('#X connect'):stack[-1][1].append(tuple(map(int,l.rstrip(';').split()[2:6])))
  elif l.startswith(('#X obj ','#X msg ','#X text ','#X floatatom ','#X symbolatom ')):stack[-1][0].append(l)
 out['root']=stack[0];return out
player=Path('sample_player_rebuild.pd').read_text().replace('#X obj 1700 4350 grid-loop-region \\$0 \\$1;\n','').replace('\n#X connect 525 0 142 0;\n','')
assert player.replace('#X obj 1700 4300 grid-playback-state \\$0 \\$1;\n','')==old('sample_player_rebuild.pd')
current=Path('mlr.pd').read_text().replace('#X obj -20 1500 grid-cut-control;\n','').replace('#X connect 7 0 83 0;\n#X connect 83 0 67 0;','#X connect 7 0 67 0;')
a,b=parse(old('mlr.pd')),parse(current);key='#X restore 13 458 pd grid-input-output;'
for k in a:
 if k!=key:assert a[k]==b[k],k
removed=set(range(46,65))-{51,59};mapping=lambda n:n-sum(i<n for i in removed)
objs=[]
for i,l in enumerate(a[key][0]):
 if i in removed:continue
 if i==51:l='#X obj 326 1487 grid-playback-row 1 1;'
 if i==59:l='#X obj 704 1471 grid-playback-row 2 2;'
 objs.append(l)
assert b[key][0]==objs
assert b[key][1]==[(mapping(s),o,mapping(t),i) for s,o,t,i in a[key][1] if not (46<=s<=64 or 46<=t<=64)]
for name in ['grid-playback-state.pd','grid-playback-row.pd','mlr-grid.pd','mlr.pd','sample_player_rebuild.pd','tests/grid-feedback-check.pd','tests/grid-musical-check.pd']:
 assert not check(Path(name))['errors'],name
for name in ['grid-playback-state.pd','grid-playback-row.pd']:
 s=Path(name).read_text();assert not any('~' in l or 'metro ' in l for l in s.splitlines() if l.startswith('#X obj'))
 assert not any(x in s for x in ['-play_button','-stop_button','-dir_change','-selected_slice'])
print('PASS: feedback baseline preserved after removing the explicit Grid-loop additions; original audio and musical row routing retained')
