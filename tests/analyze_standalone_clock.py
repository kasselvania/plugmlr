"""Native clock event checks and original player/mixer integration; requires NumPy.
Usage: python3 tests/analyze_standalone_clock.py docs/evidence/standalone-clock
No listening or DAW-transport inference is made from these checks.
"""
import json, sys
from pathlib import Path
import numpy as np
from analyze_cut_handoff import jumps
from analyze_instant_reverse import longest_silence
from analyze_stop_restart import GAIN

def rows(path):
 return [line.rstrip(';').split() for line in path.read_text().splitlines()]
def analyze(folder):
 events=rows(folder/'clock-events.txt'); ticks=np.array([(float(r[0]),int(r[2])) for r in events if r[1]=='tick']); bpms=[(float(r[0]),float(r[2])) for r in events if r[1]=='bpm']
 checks={}
 checks['default_110_then_requested_120']=bpms[:2]==[(0,110),(0,120)]
 checks['host_tempo_isolated_and_internal_tempo_restored']=bpms==[(0,110),(0,120),(600,240),(1300,80),(1400,90),(1700,60)]
 checks['monotonic_ticks_across_stop_and_source_switch']=np.array_equal(ticks[:,1],np.arange(56))
 checks['no_ticks_when_stopped_or_DAW_selected']=not any(900<=t<1100 or 1300<=t<1700 or t>=2100 for t in ticks[:,0])
 checks['run_resume_immediate']=all(t in ticks[:,0] for t in [100,1100,1700])
 for a,b,dt in [(100,600,31.25),(600,900,15.625),(1100,1300,15.625),(1700,2100,62.5)]:
  t=ticks[(ticks[:,0]>=a)&(ticks[:,0]<b),0]
  checks[f'tick_spacing_{a}_{b}_ms']=bool(len(t)>2 and np.max(abs(np.diff(t)-dt))<.011)
 ev=rows(folder/'musical-events.txt'); pt=[(float(r[0]),int(r[2])) for r in ev if r[1]=='ppq'];cuts=[(float(r[0]),int(r[2])) for r in ev if r[1]=='selected_slice']
 checks['autonomous_cuts_only_on_matching_ticks']=all(any(abs(t-ct)<.01 and n%4==0 for t,n in pt) for ct,_ in cuts)
 checks['latest_keys_and_held_pending_keys_dispatched']=cuts==[(300,6),(1087.5,9),(2515.62,11),(4015.62,13),(4140.62,4),(5140.62,7)]
 checks['application_clock_stops_and_source_gates']=not any(2000<=t<2500 or 3500<=t<4000 or t>=6000 for t,_ in pt)
 x=np.load(folder/'musical-player-mixer-48.npz')['samples'];r=np.load(folder/'musical-readers-48.npz')['samples']
 checks['bounded_finite_capture']=bool(335000<len(x)<=336064 and len(x)==len(r) and np.isfinite(x).all() and np.isfinite(r).all())
 checks['final_stop_is_silent']=bool(np.all(x[6020*48:,2:6]==0))
 checks['no_nonzero_gain_reader_teleports']=not jumps(r)
 clock_stopped=x[2010*48:2490*48,2:6]
 checks['clock_stop_leaves_audio_running']=bool(longest_silence(clock_stopped[:,:2])<64 and np.max(abs(clock_stopped[:,2:]-GAIN*clock_stopped[:,:2]))<2e-6)
 active=x[80*48:5990*48,2:6]
 checks['continuous_player_and_expected_mixer_gain']=bool(longest_silence(active[:,:2])<64 and np.max(abs(active[:,2:]-GAIN*active[:,:2]))<2e-6)
 synthetic={}
 for name,limit in [('wave',.004),('constant',.001)]:
  sx=np.load(folder/(name+'-player-mixer-48.npz'))['samples'];sr=np.load(folder/(name+'-readers-48.npz'))['samples']
  steps=abs(np.diff(sx[:,2:6],axis=0)).max(0)
  synthetic[name]={'maximum_adjacent_steps_player_mixer':steps.tolist(),'reader_jumps':jumps(sr)}
  checks[name+'_finite_bounded_silent_after_stop']=bool(335000<len(sx)<=336064 and np.isfinite(sx).all() and np.isfinite(sr).all() and np.all(sx[6020*48:,2:6]==0))
  checks[name+'_no_audible_reader_teleports']=not jumps(sr)
  checks[name+'_all_transition_steps_bounded']=bool(max(steps)<limit)
  z=sx[80*48:5990*48,2:6]
  checks[name+'_continuous_with_expected_mixer_gain']=bool(longest_silence(z[:,:2])<64 and abs(z[:,2:]-GAIN*z[:,:2]).max()<2e-6)
  if name=='constant': checks['constant_stereo_order_and_unity_reader_sum']=bool(abs(z[:,:2]-np.array([2621,-1311])/32768).max()<2e-6)
 baseline=np.load(folder/'before-tempo-repair-musical-readers-48.npz')['samples']
 checks['retained_before_capture_reproduces_tempo_teleport']=bool(len(jumps(baseline))==1 and abs(jumps(baseline)[0]['ms']-1001.3125)<.001)
 result={'checks':checks,'passed':all(checks.values()),'selected_slices':cuts,'synthetic':synthetic,'maximum_adjacent_steps_player_mixer':abs(np.diff(x[:,2:6],axis=0)).max(0).tolist(),'audible_reader_jumps':jumps(r),'limitations':['Musical maximum steps are measurements, not a universal click criterion','Listening deferred by user','Synthetic host tempo injection is not DAW transport acceptance','48 kHz host only; DrumLoop is 44.1 kHz','Clock Stop retains a queued key; playback Stop/Pause cancels it']}
 return result
if __name__=='__main__':
 result=analyze(Path(sys.argv[1]));print(json.dumps(result,indent=2));sys.exit(0 if result['passed'] else 1)
