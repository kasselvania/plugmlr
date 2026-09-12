"""Analyze captured original-player audio/state, not a substitute playback model."""
from pathlib import Path
import gzip,json,subprocess
import numpy as np
p=Path('docs/evidence/two-lane-cut')
raw=p/'lanes-master-state.wav'
data=raw.read_bytes() if raw.exists() else gzip.decompress((p/'lanes-master-state.wav.gz').read_bytes())
x=np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i','pipe:0','-f','f32le','-'],input=data),dtype='<f4').reshape(-1,16)
def source(path):return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-f','f32le','-']),dtype='<f4').reshape(-1,2)
sources={1:source('DrumLoop.wav'),2:source(p/'buffer-b.wav')}
def w(a,b):return x[int(a*48000):int(b*48000)]
def match(lane,t):
 y=w(t,t+.2);buf=int(y[0,14+lane]);s=sources[buf];pos=y[:,6+lane].astype(float)+1
 ref=np.stack([np.interp(pos,np.arange(len(s)),s[:,k]) for k in [0,1]],axis=1);actual=y[:,lane*2:lane*2+2]
 return dict(lane=lane+1,time=t,buffer=buf,correlation=[float(np.corrcoef(actual[:,k],ref[:,k])[0,1]) for k in [0,1]],gain=[float(np.dot(actual[:,k],ref[:,k])/np.dot(ref[:,k],ref[:,k])) for k in [0,1]])
b=[match(1,t) for t in [2.3,3.5,6.8,8.7,10.5]]
a=[match(0,t) for t in [12.3,14.3,16.8,18.4]]
other=[match(0,6.75),match(0,7.65),match(1,16.8),match(1,25.1)]
def timing(lane,a,b):
 y=w(a,b)[:,6+lane].astype(float);expected=np.arange(len(y))*44100/48000;err=y-expected
 return float(np.ptp(err))
def bounds(a,b,lane,start,end):return bool(np.max(abs(w(a,b)[:,8+lane*2:10+lane*2]-[start,end]))<1)
# Full-run 10ms blocks: report suspicious silence only where the measured
# source reference has energy and the actual lane is stably active.
dropouts=[]
for lane in [0,1]:
 for i in range(0,len(x)-480,480):
  y=x[i:i+480];flag=y[:,12+lane];buf=y[:,14+lane]
  if not (np.all(flag==3) and buf[0] in sources and np.all(buf==buf[0])):continue
  # Keep crossfade/cut command windows; exclude only 50ms after transport/buffer changes.
  history=x[max(0,i-2400):i+480]
  if not (np.all(history[:,12+lane]==3) and np.all(history[:,14+lane]==buf[0])):continue
  s=sources[int(buf[0])];pos=y[:,6+lane].astype(float)+1
  ref=np.stack([np.interp(pos,np.arange(len(s)),s[:,k]) for k in [0,1]],axis=1)
  expected=float(np.sqrt(np.mean(ref**2)));actual=float(np.sqrt(np.mean(y[:,lane*2:lane*2+2]**2)))
  if expected>.02 and actual<expected*.05:dropouts.append(dict(lane=lane+1,time=i/48000,expected_rms=expected,actual_rms=actual))
# Compare actual native audio at the same source trajectory, not interpolation.
# A's steady pass starts 9.8s after B's; every sample in this 8.8s span can compare.
steady_a_audio=w(11,19.8)[:,:2]
steady_b_audio=w(1.2,10)[:,2:4]
steady_difference=float(np.max(abs(steady_a_audio-steady_b_audio)))
master_residual=0.0
for i in range(2400,len(x)-480,480):
 history=x[i-2400:i+480]
 if np.all(history[:,12:14]==3) and np.all(history[:,14:16]==history[0,14:16]):
  y=x[i:i+480];master_residual=max(master_residual,float(np.max(abs(y[:,4:6]-.3*y[:,:2]-.225*y[:,2:4]))))
def solo_master(a,b,lane):
 y=w(a,b);expected=(.3*y[:,:2]) if lane==0 else (.225*y[:,2:4])
 return float(np.max(abs(y[:,4:6]-expected)))<1e-6
checks={
 '30_seconds':abs(len(x)/48000-30)<512/48000,
 'all_channels_finite':bool(np.isfinite(x).all()),
 'audio_below_full_scale':bool(np.max(abs(x[:,:6]))<1),
 'solo_b_silent':bool(np.max(abs(w(.2,.9)[:,2:4]))<1e-7),
 'shared_buffer_initially':bool(np.all(w(1.2,6.4)[:,14:16]==1)),
 'steady_b_position_preserved':timing(1,1.2,11.8)<2,
 'steady_a_position_preserved':timing(0,11,19.8)<2,
 'steady_b_stereo_matches':all(min(v['correlation'])>.99 for v in b),
 'steady_a_stereo_matches':all(min(v['correlation'])>.99 for v in a),
 'steady_lanes_audio_bit_identical':steady_difference==0,
 'active_master_mix_preserved':master_residual<1e-6,
 'a_pause_leaves_b_master_unchanged':solo_master(5.6,5.9,1),
 'b_pause_leaves_a_master_unchanged':solo_master(15.6,15.9,0),
 'empty_b_leaves_a_master_unchanged':solo_master(24.1,24.4,0),
 'a_stop_leaves_b_master_unchanged':solo_master(25.8,26,1),
 'different_buffer_stereo_matches':all(min(v['correlation'])>.99 for v in other),
 'a_two_key_loop':bounds(3.5,5.4,0,118478,276448),
 'a_mod_on_buffer2':bounds(7.5,8.1,0,171941,214926),
 'b_mod_loop':bounds(13.2,16.4,1,236955,276448),
 'overlapping_rows_keep_independent_bounds':bounds(20.6,20.9,0,78985,276448) and bounds(20.6,20.9,1,157970,355433),
 'rapid_mod_cells':bounds(21.9,22.2,0,78985,118478) and bounds(21.9,22.2,1,197463,236955),
 'alt_cancels_unfinished_pair':bounds(23.5,23.7,0,0,631881),
 'empty_b_refused':bool(np.all(w(24.1,24.4)[:,13]==0) and np.max(abs(w(24.1,24.4)[:,2:4]))<1e-7),
 'stop_cancels_unfinished_pair':bounds(26.3,26.7,0,0,631881),
 'final_full_content_cuts':bounds(27.6,27.9,0,0,631881) and bounds(27.6,27.9,1,0,687762),
 'no_detected_unexpected_silent_blocks':not dropouts,
 'final_master_silent':bool(np.max(abs(w(28.3,29.9)[:,4:6]))<1e-6),
}
r=dict(passed=all(checks.values()),checks=checks,frames=len(x),host_rate=48000,file_rates=[44100,48000],audio_peaks=np.max(abs(x[:,:6]),axis=0).tolist(),steady_b_frame_error=timing(1,1.2,11.8),steady_a_frame_error=timing(0,11,19.8),steady_b=b,steady_a=a,steady_audio_max_difference=steady_difference,active_master_max_residual=master_residual,different_buffer=other,suspicious_silent_blocks=dropouts,max_master_sample_step=float(np.max(abs(np.diff(x[:,4:6],axis=0)))),limits='Correlation/reference uses linear interpolation approximating native table playback. Silence check excludes 50ms after state/buffer changes, not cut/fade events. No universal click-free or physical gesture acceptance.')
(p/'checks.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));assert r['passed']
