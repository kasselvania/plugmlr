"""Numerical checks of native original-player/mixer output, not a DSP model.
Run with a Python environment containing numpy. Input: fixture output directory.
"""
from pathlib import Path
import sys,json,struct,hashlib,wave
import numpy as np
P=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/plugmlr-sample-editor')
def wav(path):
 data=path.read_bytes();i=12;chunks={}
 while i+8<=len(data):
  k,n=struct.unpack_from('<4sI',data,i);chunks[k]=data[i+8:i+8+n];i+=8+n+(n%2)
 fmt=chunks[b'fmt '];channels,rate=struct.unpack_from('<HI',fmt,2);bits=struct.unpack_from('<H',fmt,14)[0]
 dtype='<f4' if bits==32 else '<i2';x=np.frombuffer(chunks[b'data'],dtype=dtype).astype(float).reshape(-1,channels)
 if bits==16:x/=32768
 return x,rate
x,rate=wav(P/'capture.wav');assert x.shape==(9*rate,8) and np.isfinite(x).all()
source,sr=wav(P/'source.wav');unchanged,ur=wav(P/'unchanged.wav');assert sr==ur==44100 and np.array_equal(source,unchanged)
windows=[]
for start,end,freq in [(.3,.9,220),(1.2,1.45,440),(1.6,1.8,440),(2.5,2.7,440),(3.45,3.7,220),(4.95,5.25,440),(6.15,6.4,440)]:
 a=x[int(start*rate):int(end*rate)]; rms=np.sqrt(np.mean(a*a,axis=0));want=[freq,freq*1.5,freq,freq*1.5]
 if start==3.45:want[:2]=[880,1320]
 observed=[float(np.argmax(abs(np.fft.rfft(a[:,i])))*rate/len(a)) for i in range(4)]
 active=2 if start>6 else 4
 assert all(abs(observed[i]-want[i])<=5 for i in range(active)),(start,observed)
 assert .045<rms[0]<.06 and .020<rms[1]<.03,(start,rms)
 if active==4: assert .033<rms[2]<.045 and .015<rms[3]<.022
 windows.append(dict(start=start,end=end,dominant_hz=observed,rms=rms.tolist()))
# Intentional Stop windows must be silent in the actual mixers AND reader taps.
for start,end in [(1.02,1.09),(3.32,3.39),(3.93,3.99),(5.43,5.95),(6.63,8.99)]:
 assert np.max(abs(x[int(start*rate):int(end*rate)]))<1e-6,(start,end)
# Trimming A's buffer must leave B, now reading a different slot, audible.
isolated=x[int(4.63*rate):int(4.69*rate)]
assert np.max(abs(isolated[:,:2]))<1e-6 and np.sqrt(np.mean(isolated[:,2]**2))>.03
# Retain every transition sample for global peak and step measurements.
peaks=np.max(abs(x),axis=0);steps=np.max(abs(np.diff(x,axis=0)),axis=0)
assert max(peaks[:4])<.081 and max(steps[:4])<.081,(peaks,steps)
events=[]
for l in (P/'events.txt').read_text().splitlines():
 v=l.rstrip(';').split();events.append((float(v[0]),v[1],list(map(float,v[2:]))))
metadata=[e for e in events if e[1]=='metadata-901']
def bounds_at(ms):
 return [e for e in metadata if e[0]<=ms and e[2][0]==1][-1][2][-2:]
assert bounds_at(1200)==[44100,88200]
assert bounds_at(3200)==[44100,88200] # invalid trim did not commit
assert bounds_at(3450)==[0,176400]
assert bounds_at(4050)==[0,176400] # new load cancelled pending trim
assert bounds_at(4850)==[44100,88200] # reselection retained trim
for t,key,v in events:
 if key.endswith('play-position-frames') and (1200<t<3000 or 4950<t<5300):
  assert 44100-64<=v[0]<=88200+64,(t,key,v)
assert not any(k=='901-playback_direction' and 2300<t<5400 and v[0]==0 for t,k,v in events), 'Content change reset reverse'
assert any(k=='901-playback_direction' and t>=5400 and v[0]==0 for t,k,v in events), 'Normal Stop no longer resets direction'
for track,sign in [(901,-1),(902,1)]:
 values=[v[0] for t,k,v in events if k==f'{track}-play-position-frames' and 2510<t<2590]
 assert len(values)>=2 and all(sign*(b-a)>0 for a,b in zip(values,values[1:])),(track,values)
result={'host_rate':rate,'file_rate':sr,'duration_s':len(x)/rate,'all_finite':True,'direction_retained_during_content_changes':True,'different_buffer_unaffected':True,'original_stereo_arrays_unchanged':True,'trim_restore_reload_race_reselection_bounds_pass':True,'post_mixer_and_reader_stop_windows_silent':True,'global_channel_peaks':peaks.tolist(),'global_max_adjacent_sample_steps':steps.tolist(),'windows':windows,'listening_acceptance':'Open; numerical checks do not establish universally click-free behavior.','capture_sha256':hashlib.sha256((P/'capture.wav').read_bytes()).hexdigest()}
(P/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
# A compact stereo copy of both actual mixer outputs is retained for listening.
y=np.clip(x[:,:2]+x[:,2:4],-1,1)
with wave.open(str(P/'listening.wav'),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(rate);w.writeframes((y*32767).astype('<i2').tobytes())
