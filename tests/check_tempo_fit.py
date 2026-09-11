"""Verify localized changes against the accepted player, including every wire.
No claim about native audio: that has separate retained captures.
"""
from pathlib import Path
import subprocess
from check_patch_connections import check
BASE='610098f6f70c598c991d4ee59f351912e8397107'
def parse(s):
 stack=[];result={}
 for l in s.splitlines():
  if l.startswith('#N canvas'):stack.append([l,[],[]])
  elif l.startswith('#X restore'):
   inner=stack.pop();result[l]=inner;stack[-1][1].append(l)
  elif l.startswith('#X connect'):stack[-1][2].append(tuple(map(int,l.rstrip(';').split()[2:6])))
  elif l.startswith(('#X obj','#X msg','#X text','#X floatatom','#X symbolatom')):stack[-1][1].append(l)
 result['root']=stack[0];return result
old=parse(subprocess.check_output(['git','show',BASE+':sample_player_rebuild.pd'],text=True));new=parse(Path('sample_player_rebuild.pd').read_text())
for key in old:
 if key!='root' and 'pd calc_duration' not in key:assert old[key]==new[key],key
removed={208,209,210,212,213,214}|set(range(353,365))
a=old['root'];b=new['root'];mapping={i:i-sum(r<i for r in removed) for i in range(len(a[1])) if i not in removed};n=len(mapping)
assert b[1][:-1]==[obj for i,obj in enumerate(a[1]) if i not in removed]
assert b[1][-1]=='#X obj -580 900 tempo-fit \\$0 \\$1;'
wires=[]
for src,out,dst,port in a[2]:
 if src in removed or dst in removed:continue
 if src in range(276,281) and dst==326:continue
 wires.append((mapping[src],out,n if src in range(276,281) and dst==318 else mapping[dst],port))
wires += [(n,0,mapping[326],0),(n,0,mapping[318],0)]
assert wires==b[2],'unexpected wire change'
assert any('s \\$0-vline_message;'==l.split(' ',4)[-1] for l in b[1]),'motion send must survive'
for name in ['sample_player_rebuild.pd','tempo-fit.pd','player-panel.pd','player-panel-state.pd','tests/tempo-fit-check.pd']:
 r=check(Path(name));assert not r['errors'],r
assert not any('s \\$1-' in l or 's \\$2-' in l for l in Path('player-panel-state.pd').read_text().splitlines())
print('PASS: all unaffected subpatches and root wires preserved; motion send retained; indexes valid; status display receive-only')
