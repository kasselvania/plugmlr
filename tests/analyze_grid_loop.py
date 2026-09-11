"""Analyze actual player/mixer audio plus actual committed region bounds."""
from pathlib import Path
import subprocess,json
import numpy as np
p=Path('docs/evidence/grid-loop')
def dec(path,extra=[]):return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(path),*extra,'-f','f32le','-']),dtype='<f4')
x=dec(p/'player-master-and-bounds.wav').reshape(-1,8)
s=dec('DrumLoop.wav',['-ar','48000']).reshape(-1,2)[:,0].astype(float)
def window(a,b):return x[int(a*48000):int(b*48000)]
def region(a,b,lo,hi):
 expected=np.array([np.floor(631881*lo/16+.5)/44100,np.floor(631881*hi/16+.5)/44100])
 return bool(np.max(np.abs(window(a,b)[:,6:8]-expected))<1/44100)
def correlation(t,ch,reference,expected=None):
 a=window(t,t+.25)[:,ch].astype(float);n=1<<(len(reference)+len(a)-1).bit_length()
 v=np.fft.irfft(np.fft.rfft(reference,n)*np.conj(np.fft.rfft(a,n)),n)[:len(reference)-len(a)+1]
 e=np.r_[0,np.cumsum(reference*reference)];d=np.sqrt((e[len(a):]-e[:-len(a)])*np.dot(a,a));v=np.divide(v,d,out=np.zeros_like(v),where=d>1e-5)
 if expected is None:i=int(np.argmax(v))
 else:
  lo=int((expected-.005)*48000);hi=int((expected+.005)*48000);i=lo+int(np.argmax(v[lo:hi]))
 return dict(capture_seconds=t,source_seconds=i/48000,correlation=float(v[i]))
b=[correlation(t,2,s,t-.2023) for t in [1,3.2,5.6,8.4,10.5,12.4]]
rev=correlation(4.2,0,s[::-1])
def a_master_residual(a,b):
 y=window(a,b);return float(np.max(np.abs(y[:,4:6]-.225*y[:,2:4])))
checks={
 '16_seconds':len(x)==768000,
 'finite':bool(np.isfinite(x).all()),
 'audio_below_full_scale':bool(np.max(np.abs(x[:,:6]))<1),
 'inclusive_forward_pair':region(1.2,2.9,2,6),
 'reverse_order_pair':region(3.2,4.9,4,8),
 'queued_first_slice_does_not_erase_loop':region(5.3,6.9,0,2),
 'new_loop_in_reverse':region(7.3,7.9,2,4),
 'paused_loop_edit':region(8.3,8.9,4,6),
 'paused_master_silent_for_a':a_master_residual(8.3,8.9)<1e-6,
 'ordinary_slice_restores_full_content':region(10.5,10.9,0,16),
 'stop_cancels_held_pair':region(11.2,11.9,0,16),
 'stopped_loop_edit':region(12.2,12.9,0,3),
 'stopped_master_silent_for_a':a_master_residual(11.2,12.9)<1e-6,
 'reverse_audio_matches_reversed_source':rev['correlation']>.95,
 'b_expected_continuous_audio':all(v['correlation']>.95 for v in b),
 'stereo_master_active':bool((np.max(np.abs(x[:,4:6]),axis=0)>.1).all()),
 'final_master_silent':bool(np.max(np.abs(window(14.2,15.9)[:,4:6]))<1e-6),
}
r=dict(checks=checks,passed=all(checks.values()),host_rate=48000,file_rate=44100,frames=len(x),audio_peaks=np.max(np.abs(x[:,:6]),axis=0).tolist(),b_matches=b,reverse_match=rev,stopped_a_pre_mixer_rms=float(np.sqrt(np.mean(window(12.2,12.9)[:,:2]**2))),stopped_a_master_residual=a_master_residual(12.2,12.9),scope='Scheduled actual Grid input; actual committed bounds and mixer output. B reference comparison is windowed; no universal click-free claim.')
(p/'audio-checks.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));assert r['passed']
