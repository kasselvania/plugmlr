"""Recheck preceding speed and pause contracts against this checkpoint's captures."""
import json,sys
from pathlib import Path
import numpy as np
from analyze_stop_restart import load,GAIN
from analyze_pause_resume import ACTIVE,PAUSED,SILENT,span
from analyze_instant_reverse import longest_silence

def analyze(p):
 checks={};out={}
 x=load(p,'candidate-speed-player-mixer-48',6);r=load(p,'candidate-speed-readers-48',10)
 times=np.arange(len(r)-1)/48;allowed=np.ones(len(times),dtype=bool)
 for a,b in [(0,80),(3650,3700),(4000,4390),(5500,7000)]:allowed&=~((times>=a)&(times<=b))
 sounding=(abs(x[:-1,4:6]).max(1)>1e-6)&(abs(x[1:,4:6]).max(1)>1e-6)
 readers=[]
 for pos,gain,flag in [(4,5,8),(6,7,9)]:
  eligible=allowed&sounding&(r[:-1,gain]>.01)&(r[1:,gain]>.01)&(r[:-1,flag]>.5)&(r[1:,flag]>.5)
  d=abs(np.diff(r[:,pos]));bad=np.flatnonzero(eligible&(d>4.05))
  readers.append({'checked_steps':int(eligible.sum()),'max_step':float(d[eligible].max()),'bad_times_ms':(bad/48).tolist()})
 checks['speed_reader_continuity_including_boundary_collisions']=all(q['checked_steps']>1000 and not q['bad_times_ms'] for q in readers)
 checks['speed_rate_range']=bool(np.all((r[:,3]>=.25-1e-5)&(r[:,3]<=4+1e-5)))
 out['speed_readers']=readers
 x=load(p,'candidate-pause-player-mixer-48',6);r=load(p,'candidate-pause-readers-48',10)
 checks['pause_stop_empty_silent']=all(np.all(span(x,a,b)[:,2:6]==0) for a,b in SILENT)
 checks['paused_position_held_readers_off']=all(np.ptp(span(r,a,b)[:,2])==0 and np.max(span(r,a,b)[:,8:10])==0 for a,b in PAUSED)
 checks['resume_audio_and_gain']=all(longest_silence(span(x,a,b)[:,2:4])<64 and abs(span(x,a,b)[:,4:6]-GAIN*span(x,a,b)[:,2:4]).max()<2e-6 for a,b in ACTIVE)
 resumes=[]
 for a,ms,rate in [(.26,533,1),(.81,1033,-2),(2.19,2350,-2),(4.80,5150,-.25)]:
  saved=r[round(a*48000),2];lo=round((ms-4)*48);hi=round((ms+8)*48);ix=np.flatnonzero(abs(r[lo:hi,2]-saved)>1e-3);first=lo+int(ix[0]) if len(ix) else lo
  resumes.append({'ms':ms,'step':float(r[first,2]-saved),'slope':float(np.median(np.diff(r[first:first+32,2]))),'expected':rate})
 checks['resume_saved_position_and_rate']=all(abs(q['step'])<=abs(q['expected'])+.01 and abs(q['slope']-q['expected'])<.01 for q in resumes)
 out['resumes']=resumes
 for name in ['candidate-speed','candidate-pause']:
  x=load(p,name+'-player-mixer-48',6);r=load(p,name+'-readers-48',10)
  checks[name+'_finite_bounded_stopped']=bool(len(x)==len(r) and 335000<len(x)<=336064 and np.isfinite(x).all() and np.isfinite(r).all() and np.all(x[-12000:,2:6]==0))
 return {'checks':checks,'passed':all(checks.values()),'measurements':out}
if __name__=='__main__':
 result=analyze(Path(sys.argv[1]));print(json.dumps(result,indent=2));sys.exit(0 if result['passed'] else 1)
