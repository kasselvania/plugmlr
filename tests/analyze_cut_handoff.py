"""Matched native audio checks for pending-cut reader reuse and paused Apply.
Run: python3 tests/analyze_cut_handoff.py docs/evidence/cut-handoff
Requires NumPy and ffmpeg. Every transition sample remains in the step checks.
"""
import json,sys
from pathlib import Path
import numpy as np
from analyze_stop_restart import load
from analyze_visible_loop import analyze as functional
from analyze_visible_regressions import analyze as regressions

def jumps(r):
 out=[]
 for p,g,k in [(4,5,8),(6,7,9)]:
  eligible=(r[:-1,g]>.01)&(r[1:,g]>.01)&(r[:-1,k]>.5)&(r[1:,k]>.5)
  delta=abs(np.diff(r[:,p]));ix=np.flatnonzero(eligible&(delta>1.05))
  out.extend({'reader':(p-4)//2,'ms':float(i/48),'frames':float(delta[i])} for i in ix)
 return out

def analyze(folder):
 f=functional(folder);checks=dict(f['checks']);cases={}
 for name in ['baseline-wave','guard-only-constant','candidate-wave','candidate-constant']:
  x=load(folder,name+'-player-mixer-48',6);r=load(folder,name+'-readers-48',10)
  cases[name]={'audible_reader_jumps':jumps(r),'maximum_adjacent_steps_player_mixer':abs(np.diff(x[:,2:6],axis=0)).max(0).tolist()}
 checks['baseline_reproduces_three_reader_teleports']=len(cases['baseline-wave']['audible_reader_jumps'])==3
 checks['candidate_has_no_audible_reader_teleports']=not cases['candidate-wave']['audible_reader_jumps']
 checks['guard_only_exposes_paused_apply_mixer_cut']=max(cases['guard-only-constant']['maximum_adjacent_steps_player_mixer'][2:])>.02
 checks['candidate_constant_all_transitions_bounded']=max(cases['candidate-constant']['maximum_adjacent_steps_player_mixer'])<.001
 checks['candidate_wave_all_transitions_bounded']=max(cases['candidate-wave']['maximum_adjacent_steps_player_mixer'])<.004
 # The newest request at 3054 ms must win, but neither 2 ms replacement may
 # toggle another still-audible reader. Final range is also checked above.
 r=load(folder,'candidate-wave-readers-48',10);d=np.diff(r[:,2]);ix=np.flatnonzero(abs(d[3050*48:3075*48])>100)+3050*48
 cases['rapid_burst_master_jumps_ms']=(ix/48).tolist()
 checks['rapid_burst_coalesces_to_two_safe_handoffs']=bool(len(ix)==2 and ix[-1]/48>=3062)
 reg=regressions(folder);checks.update(reg['checks'])
 return {'checks':checks,'passed':all(checks.values()),'cases':cases,'functional':f,'regressions':reg,'limits':['No universal click-free guarantee','Natural loops shorter than fade not qualified','Host rates other than 48 kHz not exercised in this repair']}
if __name__=='__main__':
 result=analyze(Path(sys.argv[1]));print(json.dumps(result,indent=2));sys.exit(0 if result['passed'] else 1)
