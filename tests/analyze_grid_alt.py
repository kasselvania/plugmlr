"""Bounded actual-player evidence; NumPy + ffmpeg. No universal click claim."""
from pathlib import Path
import numpy as np
import subprocess,json
root=Path('docs/evidence/grid-alt')
def decode(path,extra=[]):
 return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(path),*extra,'-f','f32le','-']),dtype='<f4')
x=decode(root/'player-and-master.wav').reshape(-1,6)
s=decode('DrumLoop.wav',['-ar','48000']).reshape(-1,2)[:,0].astype(float)
def rms(a,b,c):return float(np.sqrt(np.mean(x[int(a*48000):int(b*48000),c]**2)))
def match(sec,ch,expected=None):
 a=x[int(sec*48000):int((sec+.4)*48000),ch].astype(float)
 n=1<<(len(s)+len(a)-1).bit_length()
 v=np.fft.irfft(np.fft.rfft(s,n)*np.conj(np.fft.rfft(a,n)),n)[:len(s)-len(a)+1]
 e=np.r_[0,np.cumsum(s*s)];d=np.sqrt((e[len(a):]-e[:-len(a)])*np.dot(a,a))
 v=np.divide(v,d,out=np.zeros_like(v),where=d>1e-5)
 # Repeated drum phrases can have nearly identical global matches. For B,
 # test the expected continuous source window rather than selecting another bar.
 if expected is None: i=int(np.argmax(v))
 else:
  lo=max(0,int((expected-.005)*48000));hi=min(len(v),int((expected+.005)*48000))
  i=lo+int(np.argmax(v[lo:hi]))
 return {'capture_seconds':sec,'source_seconds':i/48000,'correlation':float(v[i])}
b=[match(t,2,t-.2023) for t in [1,3.2,6.2,8.3,10]]
a=match(9.2,0)
offsets=[v['capture_seconds']-v['source_seconds'] for v in b]
checks={
 'duration_within_one_device_block_of_12s':abs(len(x)-576000)<=512,
 'finite_and_below_full_scale':bool(np.isfinite(x).all() and np.max(np.abs(x))<1),
 'a_pause_silent':rms(2.1,2.9,slice(0,2))<1e-6,
 'a_queued_cut_cancelled_pause_silent':rms(8.3,8.9,slice(0,2))<1e-6,
 'a_resumes_after_rapid_toggles':rms(6.2,7,slice(0,2))>.01,
 'a_resumes_saved_position_not_pending_slice':a['correlation']>.95 and 7<a['source_seconds']<8,
 'b_continuous_source_progression':min(v['correlation'] for v in b)>.95 and max(offsets)-min(offsets)<.002,
 'master_both_channels_active':bool((np.max(np.abs(x[:,4:]),axis=0)>.1).all()),
 'final_pause_silent':rms(11.1,11.9,slice(0,6))<1e-6,
}
r={'checks':checks,'passed':all(checks.values()),'frames':len(x),'host_rate':48000,'file_rate':44100,'peaks':np.max(np.abs(x),axis=0).tolist(),'b_source_matches':b,'a_after_cancelled_cut':a,'scope':'Scheduled gestures through actual MLR input. Correlation windows do not exclude all brief artifacts. Physical gestures and listening remain separate.'}
(root/'audio-checks.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));assert r['passed']
