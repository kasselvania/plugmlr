"""Analyze actual native player/mixer WAV and logical trajectory events.
Usage: python3 tests/analyze_grid_launch.py /tmp/plugmlr-grid-launch-after
Requires NumPy and ffmpeg/ffprobe. Listening and physical Grid acceptance are separate.
"""
from pathlib import Path
import json,subprocess,sys
import numpy as np
P=Path(sys.argv[1]);audio=P/'capture.wav'
info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(audio)]))['streams'][0]
sr=int(info['sample_rate']);channels=int(info['channels'])
x=np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(audio),'-f','f32le','-']),dtype='<f4').reshape(-1,channels)
rows=[l.rstrip(';').split() for l in (P/'events.txt').read_text().splitlines()]
traj=[(float(r[0]),*[float(v) for v in r[2:]]) for r in rows if r[1]=='901-loop_target_index']
checks={};detail={}
def span(a,b):return x[round(a*sr):round(b*sr)]
def silent(a,b):return float(np.max(np.abs(span(a,b)[:,:4])))==0
checks['48k_host_44k1_file_15s_finite']=sr==48000 and len(x)==15*sr and channels==8 and bool(np.isfinite(x).all())
checks['first_loaded_slice_reaches_mixer']=bool(np.max(np.abs(span(.25,.65)[:,:2]))>.05)
checks['stop_cancels_pending_launch']=silent(1.63,1.99)
checks['quantized_launch_waits_for_tick']=silent(3.52,3.649)
checks['pause_stop_cancel_quantized_launch']=silent(3.92,4.449)
checks['invalid_slice_requests_stay_silent']=silent(8.53,8.99)
checks['final_stop_silence']=silent(14.45,14.999)
entries=[(200,4,1),(750,8,1),(1101,12,1),(2000,15,1),(2500,4,-1),(2950,8,-1),(3650,6,1),(4700,0,-1),(8112,6,1)]
entries += [(9000+i*150,i,1) for i in range(16)]+[(11800+i*150,i,-1) for i in range(16)]
entry_results=[]
for ms,index,direction in entries:
 target=(index+(direction<0))*44100/4
 matching=[r for r in traj if ms<=r[0]<=ms+13 and abs(r[1]-target)<.01 and (r[2]-r[1])*direction>0]
 entry_results.append(dict(request_ms=ms,cell=index,direction=direction,expected_frame=target,matching_trajectories=matching))
checks['all_41_requested_entries_correct']=all(r['matching_trajectories'] for r in entry_results)
detail['entries']=entry_results
checks['queued_play_replaces_slice']=any(8309<=r[0]<=8310 and r[1]==0 for r in traj)
# Frequency/order checks of all 16 cells in both directions, from rendered mixer audio.
frequency=[]
for start,direction in [(9000,1),(11800,-1)]:
 for i in range(16):
  ms=start+i*150;z=span((ms+30)/1000,(ms+120)/1000)[:,:2]
  f=[]
  for ch in range(2):
   spectrum=np.abs(np.fft.rfft(z[:,ch]*np.hanning(len(z)),n=65536));f.append(float(np.argmax(spectrum)*sr/65536))
  expected=[160+40*i,(160+40*i)*1.25]
  frequency.append(dict(cell=i,direction=direction,actual_hz=f,expected_hz=expected,lr_rms=np.sqrt(np.mean(z*z,axis=0)).tolist()))
checks['all_32_stereo_cells_audible_correct_pitch']=all(max(abs(a-b) for a,b in zip(w['actual_hz'],w['expected_hz']))<1 and .050<w['lr_rms'][0]<.054 and .024<w['lr_rms'][1]<.028 for w in frequency)
detail['stereo_frequency_checks']=frequency
active=[(.25,.65),(.78,1.05),(1.13,1.5),(2.05,2.23),(2.55,2.8),(2.98,3.28),(3.68,3.88),(5.02,5.18),(6.22,6.38),(6.68,6.95),(7.5,7.95),(8.13,8.28),(8.35,8.48)]
gain=[]
for a,b in active:
 z=span(a,b);quiet=np.max(np.abs(z[:,:2]),axis=1)<1e-8
 padded=np.r_[False,quiet,False];edges=np.flatnonzero(padded[1:]!=padded[:-1]);longest=int(max(edges[1::2]-edges[::2],default=0))
 gain.append(dict(seconds=[a,b],mixer_gain_error=float(np.max(np.abs(z[:,:2]-.4*z[:,4:6]))),longest_zero_frames=longest))
checks['active_audio_no_dropouts_or_mixer_gain_error']=all(w['longest_zero_frames']<64 and w['mixer_gain_error']<1e-6 for w in gain)
detail['active_windows']=gain
# B shares A's buffer but runs uninterrupted across A's reverse, Stop and cut.
z=span(6.55,7.98);checks['second_lane_independent_gain_continuity']=bool(np.max(np.abs(z[:,2:4]-.3*z[:,6:8]))<1e-6 and np.sqrt(np.mean(z[:,2]**2))>.035)
btraj=[(float(r[0]),*[float(v) for v in r[2:]]) for r in rows if r[1]=='902-loop_target_index']
checks['second_lane_single_uninterrupted_trajectory']=len(btraj)==1 and btraj[0][0]==6501 and btraj[0][1]==33075
# Loop release preserves position inside range and ordinary cuts restore full content.
loop=[r for r in traj if 5880<=r[0]<=5895]
checks['qualified_loop_release_preserves_running_position']=len(loop)==1 and abs(loop[0][1]-(110250+79*44.1))<1 and loop[0][2]==121275
checks['ordinary_slice_restores_full_content']=any(6200<=r[0]<=6213 and r[1]==132300 and r[2]==176400 for r in traj)
detail['max_adjacent_step_all_audio_channels']=np.max(np.abs(np.diff(x,axis=0)),axis=0).tolist()
detail['global_peak_all_channels']=np.max(np.abs(x),axis=0).tolist()
# Fixture-specific ceiling above the largest expected one-sample sine change.
checks['all_transition_samples_bounded']=max(detail['max_adjacent_step_all_audio_channels'][:4])<.02 and max(detail['global_peak_all_channels'])<.19
result=dict(host_rate=sr,file_rate=44100,checks=checks,passed=all(checks.values()),detail=detail,limitations='No new listening or physical Grid acceptance. Bounds are fixture-specific, not universal click-free proof.')
(P/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':result['passed'],'checks':checks,'max_steps':detail['max_adjacent_step_all_audio_channels']},indent=2))
raise SystemExit(not result['passed'])
