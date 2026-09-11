"""Measure actual original-player captures, including retained transition failures.
Run: python3 tests/analyze_visible_loop.py docs/evidence/visible-loop
Requires NumPy and ffmpeg. No simulated playback is used as acceptance evidence.
"""
import json
import sys
from pathlib import Path
import numpy as np
from analyze_stop_restart import load, RATE, GAIN
from analyze_instant_reverse import longest_silence

# Seconds in visible-loop.txt, with margins only around intentional transport fades.
REGIONS = [(.08,.54,2400,7200),(.58,1.04,4800,9600),
 (1.08,1.54,4800,9600),(1.58,2.04,1200,6000),(2.08,2.44,0,12000),
 (2.48,2.74,0,12000),(2.78,3.04,2400,7200),(3.08,3.34,2880,7680),
 (3.68,4.04,1200,6000),(4.38,4.64,2400,7200),(4.68,4.94,2400,7200),
 (5.6,6.04,0,12000)]
ACTIVE=[(.08,3.34),(3.68,4.04),(4.38,4.94),(5.6,6.04)]
SILENT=[(3.38,3.64),(4.08,4.34),(4.98,5.54),(6.1,6.95)]
def span(x,a,b):return x[round(a*RATE):round(b*RATE)]
def analyze(folder):
 checks={}; cases={}
 for name in ['candidate-wave','candidate-constant']:
  x=load(folder,name+'-player-mixer-48',6);r=load(folder,name+'-readers-48',10)
  checks[name+'_finite_bounded_stop']=bool(len(x)==len(r) and 335000<len(x)<=336064 and np.isfinite(x).all() and np.isfinite(r).all() and np.all(x[-12000:,2:6]==0))
  ranges=[]
  for a,b,lo,hi in REGIONS:
   z=span(r,a,b)[:,2]
   ranges.append({'seconds':[a,b],'expected':[lo,hi],'observed':[float(z.min()),float(z.max())]})
  checks[name+'_region_bounds_and_full_sample']=all(lo-.02<=w['observed'][0]<=lo+1.02 and hi-1.02<=w['observed'][1]<=hi+.02 for w,(_,_,lo,hi) in zip(ranges,REGIONS))
  checks[name+'_pause_holds_new_reverse_entry']=bool(np.all(span(r,3.38,3.64)[:,2]==6000))
  checks[name+'_transport_and_empty_silent']=all(np.all(span(x,a,b)[:,2:6]==0) for a,b in SILENT)
  windows=[]
  for a,b in ACTIVE:
   z=span(x,a,b)[:,2:6]
   windows.append({'seconds':[a,b],'longest_silence_frames':longest_silence(z[:,:2]),'mixer_gain_error':float(abs(z[:,2:]-GAIN*z[:,:2]).max())})
  checks[name+'_no_block_dropout_or_mixer_gain_change']=all(w['longest_silence_frames']<64 and w['mixer_gain_error']<2e-6 for w in windows)
  jumps=[]
  for p,g,k in [(4,5,8),(6,7,9)]:
   eligible=(r[:-1,g]>.01)&(r[1:,g]>.01)&(r[:-1,k]>.5)&(r[1:,k]>.5)
   d=abs(np.diff(r[:,p]));ix=np.flatnonzero(eligible&(d>1.05))
   jumps.extend({'reader':(p-4)//2,'time_ms':float(i/48),'step_frames':float(d[i]),'gain':float(r[i,g])} for i in ix)
  cases[name]={'frames':len(x),'regions':ranges,'active_windows':windows,'max_audio_steps_player_mixer':abs(np.diff(x[:,2:6],axis=0)).max(0).tolist(),'audible_reader_reuse':jumps}
  if name.endswith('constant'):
   error=max(float(abs(span(x,a,b)[:,2:4]-np.array([2621,-1311])/32768).max()) for a,b in ACTIVE)
   checks['stereo_order_and_unity_reader_sum']=error<2e-6
   cases[name]['constant_stereo_error']=error
 wave=cases['candidate-wave']; failures={'overlapping_handoffs_have_no_audible_reader_teleports':not wave['audible_reader_reuse']}
 return {'checks':checks,'functional_checks_pass':all(checks.values()),'transition_acceptance_gates':failures,'transition_acceptance_complete':all(failures.values()),'cases':cases}
if __name__=='__main__':
 result=analyze(Path(sys.argv[1]));print(json.dumps(result,indent=2));sys.exit(0 if result['functional_checks_pass'] else 1)
