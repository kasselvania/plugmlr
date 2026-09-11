"""Check native original-player Beat Reset captures; NumPy required.
Usage: python3 tests/analyze_beat_reset.py docs/evidence/beat-reset
"""
import json,sys
from pathlib import Path
import numpy as np
from analyze_cut_handoff import jumps
from analyze_instant_reverse import longest_silence
from analyze_stop_restart import GAIN
EXPECTED=[(250,16),(450,32),(700,48),(1200,96),(1500,128),(1800,192),(2100,256),(2400,512),(2700,1024),(2900,1536),(3300,16),(3350,32),(3352,48),(3356,64),(3900,112)]
ACTIVE=[(.08,.79),(.97,.99),(1.18,2.99),(3.28,3.49),(3.63,4.29)]
SILENT=[(.83,.94),(1.03,1.14),(3.04,3.24),(3.53,3.59),(4.33,6.95)]
def span(x,a,b):return x[round(a*48000):round(b*48000)]
def events(folder,name,label):
 rows=[l.rstrip(';').split() for l in (folder/(name+'-events.txt')).read_text().splitlines()]
 return [(float(r[0]),r[2:]) for r in rows if r[1]==label]
def analyze(folder):
 checks={};cases={}
 for name in ['wave','constant']:
  x=np.load(folder/(name+'-player-mixer-48.npz'))['samples'];r=np.load(folder/(name+'-readers-48.npz'))['samples'];d=np.diff(r[:,2])
  fired=[(t,int(v[0])) for t,v in events(folder,name,'1-reset-fired')]
  checks[name+'_exact_reset_requests_and_suppression']=fired==EXPECTED
  checks[name+'_invalid_intervals_rejected']=events(folder,name,'1-reset-error')==[(2800,['Invalid_interval'])]*3
  checks[name+'_other_track_stays_silent']=events(folder,name,'2-reset-fired')==[]
  checks[name+'_finite_bounded']=bool(335000<len(x)<=336064 and len(x)==len(r) and np.isfinite(x).all() and np.isfinite(r).all())
  checks[name+'_no_nonzero_gain_reader_teleports']=not jumps(r)
  checks[name+'_active_audio_and_mixer_gain']=all(longest_silence(span(x,a,b)[:,2:4])<64 and abs(span(x,a,b)[:,4:6]-GAIN*span(x,a,b)[:,2:4]).max()<2e-6 for a,b in ACTIVE)
  checks[name+'_stopped_paused_empty_silence']=all(np.all(span(x,a,b)[:,2:6]==0) for a,b in SILENT)
  steps=abs(np.diff(x[:,2:6],axis=0)).max(0);checks[name+'_all_transition_steps_bounded']=bool(max(steps)<(.001 if name=='constant' else .004))
  entry=[]
  for t,tick in EXPECTED:
   if t in (3350,3352):continue # replaced within the shared pending fade; final request checked at 3356
   before=float(np.median(d[(t-8)*48:(t-2)*48]));after=float(np.median(d[(t+14)*48:(t+20)*48]));target=11999 if before<0 else 1
   error=float(abs(r[t*48:(t+14)*48,2]-target).min());entry.append({'ms':t,'entry_error_frames':error,'speed_before':before,'speed_after':after})
  checks[name+'_full_start_or_end_entry']=all(z['entry_error_frames']<1.1 for z in entry)
  checks[name+'_signed_speed_preserved']=all(abs(z['speed_before']-z['speed_after'])<.02 for z in entry)
  checks[name+'_full_bounds_restored']=bool(r[450*48:650*48,2].max()>7200 and r[3356*48:3490*48,2].max()>5760)
  if name=='constant':checks['stereo_order_unity_reader_gain']=all(abs(span(x,a,b)[:,2:4]-np.array([2621,-1311])/32768).max()<2e-6 for a,b in ACTIVE)
  cases[name]={'reset_requests':fired,'entries':entry,'maximum_adjacent_steps_player_mixer':steps.tolist(),'reader_jumps':jumps(r)}
 initial=[t for t,_ in events(folder,'initial-wave','1-reset-fired')];checks['initial_candidate_failure_retained']=700 in initial and 1200 not in initial and 2900 not in initial
 if (folder/'musical-player-mixer-48.npz').exists():
  x=np.load(folder/'musical-player-mixer-48.npz')['samples'];r=np.load(folder/'musical-readers-48.npz')['samples'];fired=events(folder,'musical','1-reset-fired')
  checks['musical_autonomous_resets_occur']=len(fired)>=4
  checks['musical_finite_and_automatically_stopped']=bool(np.isfinite(x).all() and np.isfinite(r).all() and np.all(x[-12000:,2:6]==0))
  checks['musical_no_reader_teleports']=not jumps(r)
  cases['musical']={'reset_requests':fired,'reader_jumps':jumps(r),'maximum_adjacent_steps_player_mixer':abs(np.diff(x[:,2:6],axis=0)).max(0).tolist()}
 return {'checks':checks,'passed':all(checks.values()),'cases':cases,'limits':['Listening pending','48 kHz host only','Shared clock does not provide DAW-sync acceptance','Fired reports a request; crossover can defer or replace its audio commit','Malformed text on global ppq still errors in the legacy slice modulo objects']}
if __name__=='__main__':
 result=analyze(Path(sys.argv[1]));print(json.dumps(result,indent=2));sys.exit(0 if result['passed'] else 1)
