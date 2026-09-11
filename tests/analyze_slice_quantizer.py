"""Compare original-player scheduling and rendered audio against controlled ticks.
Run: python3 tests/analyze_slice_quantizer.py docs/evidence/slice-quantizer
NumPy/ffmpeg required. This exercises Pd's actual scheduler and audio path.
"""
import json,sys
from pathlib import Path
import numpy as np
from analyze_stop_restart import load, GAIN
from analyze_instant_reverse import longest_silence
from analyze_visible_regressions import analyze as regressions
from analyze_visible_loop import analyze as loop_checks
EXPECTED=[(250,6),(2100,9),(2300,10),(2350,11),(2570,12),(2800,13),(3500,14),(3850,3),(4100,4)]
ACTIVE=[(.08,.54),(.83,.91),(1.13,1.21),(1.25,4.29)]
SILENT=[(.58,.79),(.95,1.09),(4.33,6.95)]
def span(x,a,b):return x[round(a*48000):round(b*48000)]
def selected(folder,name):
 rows=[l.rstrip(';').split() for l in (folder/(name+'-events.txt')).read_text().splitlines()]
 return [(float(r[0]),int(r[2])) for r in rows if r[1]=='selected_slice']
def analyze(folder):
 checks={};cases={}
 for name in ['baseline-wave','candidate-wave','candidate-constant','candidate-grids']:
  x=load(folder,name+'-player-mixer-48',6);r=load(folder,name+'-readers-48',10)
  events=selected(folder,name);jumps=[]
  for p,g,k in [(4,5,8),(6,7,9)]:
   d=abs(np.diff(r[:,p]));eligible=(r[:-1,g]>.01)&(r[1:,g]>.01)&(r[:-1,k]>.5)&(r[1:,k]>.5)
   ix=np.flatnonzero(eligible&(d>1.05));jumps.extend((ix/48).tolist())
  cases[name]={'selected_slice_events':events,'max_steps_player_mixer':abs(np.diff(x[:,2:6],axis=0)).max(0).tolist(),'audible_reader_jump_ms':jumps}
  checks[name+'_finite_bounded_stopped']=bool(335000<len(x)<=336064 and len(x)==len(r) and np.isfinite(x).all() and np.isfinite(r).all() and np.all(x[-12000:,2:6]==0))
  if name=='baseline-wave':
   checks['baseline_reproduces_early_duplicate_and_stale_cuts']=all(e in events for e in [(150,6),(250,6),(600,8),(950,3),(1250,4),(1550,5),(1850,7)])
   continue
  expected=[(350+500*g,g) for g in range(7)] if name=='candidate-grids' else EXPECTED
  checks[name+'_exact_dispatch_times_and_no_extra_cuts']=events==expected
  checks[name+'_no_audible_reader_teleports']=not jumps
  active=[(.08,3.99)] if name=='candidate-grids' else ACTIVE
  silent=[(4.03,6.95)] if name=='candidate-grids' else SILENT
  checks[name+'_continuous_audio_and_gain']=all(longest_silence(span(x,a,b)[:,2:4])<64 and abs(span(x,a,b)[:,4:6]-GAIN*span(x,a,b)[:,2:4]).max()<2e-6 for a,b in active)
  checks[name+'_transport_silence']=all(np.all(span(x,a,b)[:,2:6]==0) for a,b in silent)
  checks[name+'_all_transition_steps_bounded']=max(cases[name]['max_steps_player_mixer'])<(.001 if name=='candidate-constant' else .004)
  entries=[]
  for ms,index in expected:
   direction=-1 if name!='candidate-grids' and ms>=3850 else 1;target=(index+(direction<0))*750
   z=r[ms*48:(ms+16)*48,2];dist=abs(z-(target+direction)).min()
   entries.append({'tick_or_press_ms':ms,'target_frames':target,'nearest_entry_error_frames':float(dist)})
  cases[name]['actual_master_entries']=entries
  checks[name+'_actual_master_enters_requested_slices']=all(q['nearest_entry_error_frames']<1.1 for q in entries)
  if name=='candidate-constant':
   err=max(float(abs(span(x,a,b)[:,2:4]-np.array([2621,-1311])/32768).max()) for a,b in active)
   cases[name]['stereo_constant_error']=err;checks['constant_stereo_order_and_unity_reader_sum']=err<2e-6
 reg=regressions(folder);checks.update(reg['checks'])
 # Existing loop/Apply score retained under distinct names in this folder.
 loops=loop_checks(folder/'loop-regression');checks['loop_apply_functional_regression']=loops['functional_checks_pass'];checks['loop_apply_reader_handoff_regression']=loops['transition_acceptance_complete']
 return {'checks':checks,'passed':all(checks.values()),'cases':cases,'regressions':reg,'loop_regression':loops,'scope':'Controlled ppq messages into original native player; not autonomous clock or DAW transport acceptance.'}
if __name__=='__main__':
 result=analyze(Path(sys.argv[1]));print(json.dumps(result,indent=2));sys.exit(0 if result['passed'] else 1)
