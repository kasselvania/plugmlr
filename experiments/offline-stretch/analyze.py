"""Inspect actual native samples. This does not measure audio-device underruns."""
from pathlib import Path
import struct,json,hashlib,sys,lzma
import numpy as np
P=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/plugmlr-stretch-workbench')
def read(path):
 b=path.read_bytes() if path.exists() else lzma.decompress(path.with_suffix(path.suffix+'.xz').read_bytes());p=12
 while p+8<=len(b):
  tag=b[p:p+4];n=struct.unpack_from('<I',b,p+4)[0];d=b[p+8:p+8+n];p+=8+n+(n%2)
  if tag==b'fmt ':fmt,ch,sr,_,_,bits=struct.unpack_from('<HHIIHH',d)
  if tag==b'data':data=d
 if fmt in (3,65534) and bits==32:a=np.frombuffer(data,dtype='<f4')
 elif fmt==1 and bits==16:a=np.frombuffer(data,dtype='<i2')/32768
 else:raise ValueError((fmt,bits))
 return sr,a.reshape(-1,ch)
r,cap=read(P/'capture.wav');rr,rb=read(P/'rubberband.wav');rs,stage=read(P/'staged.wav')
assert r==rr==rs==48000 and cap.shape[1]==4
assert np.isfinite(cap).all() and np.isfinite(rb).all()
assert rb.shape==stage.shape==(192000,2)
assert np.max(abs(rb-stage))<1e-7 # Threaded load preserved both channels exactly.
def peaks(a,sr):
 w=a[int(.5*sr):int(3.5*sr)];return np.fft.rfftfreq(len(w),1/sr)[np.argmax(abs(np.fft.rfft(w*np.hanning(len(w))[:,None],axis=0)),axis=0)].tolist()
refs=[]
for ch,hz in [(2,997),(3,1499)]:
 z=cap[:,ch].astype(float)
 # Local oscillator recurrence detects sample discontinuities without treating
 # float oscillator frequency rounding over 12 seconds as an interruption.
 err=float(np.max(abs(z[2:]-2*np.cos(2*np.pi*hz/r)*z[1:-1]+z[:-2])))
 refs.append(err);assert err<1e-6,(ch,err)
 assert abs(float(np.sqrt(np.mean(z*z)))-.05/np.sqrt(2))<1e-4
pv=peaks(cap[:,:2],r);rbfreq=peaks(rb,r)
pv_pitch_ok=all(abs(v-w)<2 for v,w in zip(pv,[440,660])) # Report the candidate's failure; do not loosen tolerance.
assert all(abs(v-w)<2 for v,w in zip(rbfreq,[440,660])),rbfreq
rms=[np.sqrt(np.mean(cap[i:i+480,:2]**2,axis=0)).tolist() for i in range(0,len(cap),480)]
result=dict(native_capture_seconds=len(cap)/r,pvoc_peak_hz=pv,pvoc_pitch_within_2hz=pv_pitch_ok,rubberband_peak_hz=rbfreq,rubberband_seconds=len(rb)/r,threaded_load_max_error=float(np.max(abs(rb-stage))),reference_max_recurrence_error=refs,pvoc_middle_rms=np.sqrt(np.mean(cap[48000:144000,:2]**2,axis=0)).tolist(),pvoc_after_end_rms=np.sqrt(np.mean(cap[240000:288000,:2]**2,axis=0)).tolist(),pvoc_rms_10ms=rms,limitations=['Reference continuity is inside Pd, not device/DAW underrun proof','Two-second synthetic source; not musical quality or large-file safety','pvoc renders in real time, not background','Worker launched from terminal; no in-patch or plugin process launcher qualified'])
(P/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print({k:v for k,v in result.items() if k!='pvoc_rms_10ms'})
