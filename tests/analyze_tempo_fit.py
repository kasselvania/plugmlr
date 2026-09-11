"""Numerical checks on native component captures, not a playback model.
Run with NumPy/ffmpeg: python3 tests/analyze_tempo_fit.py docs/evidence/tempo-fit
"""
import json,sys,subprocess
from pathlib import Path
import numpy as np
HOST=48000;FILE=44100

def load(p,ch):
 if p.suffix=='.npz':return np.load(p)['samples']
 return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-f','f32le','-']),dtype='<f4').reshape(-1,ch)
def read(folder,name):
 p=folder/(name+'-readers.npz')
 return load(p if p.exists() else p.with_suffix('.wav'),10),load(folder/(name+'-master.wav'),2)
def longest_silent(x):
 z=np.all(abs(x)<1e-7,axis=1);d=np.diff(np.r_[False,z,False].astype(int))
 return int(max(np.flatnonzero(d==-1)-np.flatnonzero(d==1),default=0))
def inspect(r,y,windows,starts):
 jumps=[]
 for pos,gain,dsp in [(4,5,8),(6,7,9)]:
  on=(r[:-1,gain]>.01)&(r[1:,gain]>.01)&(r[:-1,dsp]>.5)&(r[1:,dsp]>.5)
  # At most the adjacent commanded rate plus float frame-index resolution.
  delayed=np.r_[np.repeat(r[0,3],64),r[:-64,3]]
  limit=np.maximum.reduce([abs(r[:-1,3]),abs(r[1:,3]),abs(delayed[:-1]),abs(delayed[1:])])*FILE/HOST+.08
  ix=np.flatnonzero(on&(abs(np.diff(r[:,pos]))>limit))
  jumps += [{'reader':pos,'ms':float(i/HOST*1000),'frames':float(abs(r[i+1,pos]-r[i,pos]))} for i in ix]
 # send~/receive~ paths are recorded by the same host graph; compare fixed alignment.
 n=min(len(r),len(y));x=r[:n,:2];m=y[:n]
 gain=float(np.sum(x[9600:43000]*m[9600:43000])/max(np.sum(x[9600:43000]**2),1e-20))
 expected_fade=np.zeros(n,dtype=bool)
 for t in starts:expected_fade[round(t*HOST):round((t+.007)*HOST)]=True
 residual=abs(m-gain*x)
 settled_error=float(residual[~expected_fade].max())
 return {'frames':[len(r),len(y)],'finite':bool(np.isfinite(r).all() and np.isfinite(y).all()),'mixer_gain':gain,'mixer_residual_peak':float(residual.max()),'mixer_residual_outside_documented_start_fades':settled_error,'mixer_max_amplification_above_gain':float(np.maximum(abs(m)-gain*abs(x),0).max()),'audible_reader_jumps':jumps,'player_peak_lr':abs(x).max(0).tolist(),'player_max_adjacent_step_lr':abs(np.diff(x,axis=0)).max(0).tolist(),'active_longest_silence_frames':[longest_silent(x[round(a*HOST):round(b*HOST)]) for a,b in windows]}
def analyze(folder):
 checks={};results={};r,y=read(folder,'core');a=inspect(r,y,[(.12,9),(10.02,11)],[.1,10])
 results['core']=a
 checks['core_bounded_finite']=a['finite'] and all(575000<=n<=576064 for n in a['frames'])
 checks['core_no_audible_reader_teleports']=not a['audible_reader_jumps']
 checks['core_no_dropouts']=max(a['active_longest_silence_frames'])<=2
 checks['core_stereo_peak_preserved']=bool(np.allclose(a['player_peak_lr'],[.12,.06],atol=.0001))
 checks['core_mixer_preserves_audio']=a['mixer_gain']>.1 and a['mixer_residual_outside_documented_start_fades']<1e-5 and a['mixer_max_amplification_above_gain']<1e-6
 checks['core_pause_and_final_stop_silent']=bool(np.max(abs(r[round(9.03*HOST):round(9.99*HOST),:2]))==0 and np.max(abs(r[round(11.03*HOST):,:2]))==0)
 cases=[]
 for start,rate,direction in [(.2,1,1),(1.2,1,1),(2.2,2,1),(3.2,2,-1),(4.2,1,-1),(5.2,1,-1),(6.2,1,-1),(7.2,.5,-1),(8.2,.5,-1),(10.2,.5,-1)]:
  w=r[round(start*HOST):round((start+.5)*HOST)];slope=float(np.median(np.diff(w[:,2])));expected=direction*rate*FILE/HOST
  cases.append({'at_seconds':start,'rate':float(np.median(w[:,3])),'frame_step':slope,'expected_step':expected})
 checks['core_fit_free_reverse_and_presets']=all(abs(v['frame_step']-v['expected_step'])<.01 for v in cases)
 results['rates']=cases
 w=r[round(5.03*HOST):round(5.99*HOST),2];checks['partial_loop_uses_same_rate_and_requested_bounds']=bool(w.min()>=22049 and w.max()<=66151)
 # Pitch/channel check on a stable non-transition section at fitted 2x.
 w=r[round(2.2*HOST):round(2.7*HOST),:2];freq=np.fft.rfftfreq(len(w),1/HOST);peaks=freq[np.argmax(abs(np.fft.rfft(w*np.hanning(len(w))[:,None],axis=0)),axis=0)]
 results['fitted_stereo_frequencies']=peaks.tolist();checks['file_host_mismatch_and_channel_order']=bool(np.allclose(peaks,[750,1200],atol=2))
 if (folder/'stress-master.wav').exists():
  r,y=read(folder,'stress');a=inspect(r,y,[(.12,6.5),(7.53,8),(9.13,10)],[.1,7.5,9.1])
  results['stress']=a
  checks['stress_bounded_finite']=a['finite'] and all(575000<=n<=576064 for n in a['frames'])
  checks['stress_no_audible_reader_teleports']=not a['audible_reader_jumps']
  checks['stress_no_dropouts']=max(a['active_longest_silence_frames'])<=2
  checks['stress_peak_and_mixer_preserved']=max(a['player_peak_lr'])<.121 and a['mixer_residual_outside_documented_start_fades']<1e-5 and a['mixer_max_amplification_above_gain']<1e-6
  checks['stress_stopped_empty_and_final_silence']=all(np.max(abs(r[round(s*HOST):round(e*HOST),:2]))==0 for s,e in [(6.54,7.49),(8.04,9.08),(10.03,11.99)])
  checks['stress_all_transition_steps_bounded']=max(a['player_max_adjacent_step_lr'])<.025
  rates=[float(r[round(t*HOST),3]) for t in [.9,1.1,1.19,1.3,1.36,1.86]]
  results['interrupted_glide_rates']=rates
  checks['tempo_changes_interrupt_existing_glide']=rates[0]==1 and 1<rates[1]<rates[2]<2 and rates[4]<rates[3]<rates[2] and abs(rates[5]-1.5)<.001
  lines=(folder/'stress-events.txt').read_text().splitlines();errors=[l for l in lines if '1-tempo-fit-error' in l];results['rejected_inputs']=errors
  checks['invalid_mode_and_beats_rejected']=len(errors)==5
  checks['fit_unavailable_reported']=any('tempo-fit-status 2;' in l for l in lines)
  ticks=[float(l.split()[0]) for l in lines if '1-reset-fired' in l];results['reset_request_ms']=ticks
  checks['beat_reset_runs_independently']=len(ticks)>=3 and np.allclose(np.diff(ticks),500,atol=2)
  w=r[round(9.3*HOST):round(9.8*HOST)];checks['four_times_preset_after_empty_recovery']=abs(abs(float(np.median(np.diff(w[:,2]))))-4*FILE/HOST)<.02
 if (folder/'musical-master.wav').exists():
  r,y=read(folder,'musical');n=min(len(r),len(y));results['musical']={'frames':[len(r),len(y)],'rms_by_section':[]}
  checks['musical_finite_bounded_stopped']=bool(np.isfinite(r).all() and np.isfinite(y).all() and 575000<=n<=576064 and np.max(abs(y[round(11.03*HOST):]))==0)
  checks['musical_fit_rates_and_reverse']=True
  for t,bpm,beats,sign in [(1,120,32,1),(4,150,32,1),(7,150,16,1),(10,150,16,-1)]:
   w=r[round(t*HOST):round((t+.5)*HOST)];expected=631881*bpm/(60*beats*HOST)*sign
   checks['musical_fit_rates_and_reverse'] &= abs(float(np.median(np.diff(w[:,2])))-expected)<.05
   results['musical']['rms_by_section'].append(float(np.sqrt(np.mean(y[round(t*HOST):round((t+.5)*HOST)]**2))))
  checks['musical_audible_in_each_section']=min(results['musical']['rms_by_section'])>.003
 return {'host_hz':HOST,'file_hz':FILE,'checks':checks,'passed':all(checks.values()),'results':results,'limits':['Numerical checks are not listening acceptance','Only 48 kHz host tested','No universal click-free or phase-lock claim']}
if __name__=='__main__':
 result=analyze(Path(sys.argv[1]));print(json.dumps(result,indent=2));sys.exit(not result['passed'])
