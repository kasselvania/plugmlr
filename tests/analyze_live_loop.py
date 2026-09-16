"""Numerical checks of actual native original-player AND mixer captures.
One-frame transitions are measured and retained as an open click gate, not
excluded from global measurements or described as click-free.
"""
from pathlib import Path
import json,struct,sys,wave,hashlib
import numpy as np
P=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/plugmlr-live-loop-check')
def readwav(path):
 data=path.read_bytes();i=12;chunks={}
 while i+8<=len(data):
  key,n=struct.unpack_from('<4sI',data,i);chunks[key]=data[i+8:i+8+n];i+=8+n+(n%2)
 channels,rate=struct.unpack_from('<HI',chunks[b'fmt '],2)
 return np.frombuffer(chunks[b'data'],'<f4').reshape(-1,channels).astype(float),rate
x,rate=readwav(P/'capture.wav');assert x.shape==(12*rate,8) and np.isfinite(x).all()
events=[]
for line in (P/'events.txt').read_text().splitlines():
 a=line.rstrip(';').split();events.append((float(a[0]),a[1],a[2:]))
def last(ms,suffix,track=901):
 return float([v for t,k,v in events if t<=ms and k==f'{track}-{suffix}'][-1][0])
def bounds(ms):return [last(ms,'set_active_loop_start'),last(ms,'set_active_loop_end')]
checks={1050:[1,2],1150:[1.2,2.2],1350:[1.2,1.45],1550:[2,2.25],2050:[2.5,2.75],2250:[2.6,2.75],2450:[2.6,2.62],2850:[2.8,2.82],3450:[3.88,4],3650:[0,.12],3850:[0,4],4250:[.75,1],4850:[3,3.2],5150:[2,2.2],5550:[1.5,1.7],5890:[1.72,1.9],6450:[2.3,2.48],6790:[2.3,2.48],7050:[0,4],7280:[0,0],7955:[1,1.5],8350:[1,3],8815:[1,1+4/44100],8940:[2.4,2.8],9250:[2.4,2.8],9350:[1,3]}
for t,expected in checks.items():assert np.max(abs(np.array(bounds(t))-np.array(expected)*44100))<=1,(t,bounds(t),expected)
for t in [3010,3210]:assert bounds(t)[1]-bounds(t)[0]==1,(t,bounds(t))
# B's state and speed must remain unchanged while A is manipulated, even with a shared buffer.
for t,k,v in events:
 if 201<t<7700 and k in ['902-set_active_loop_start','902-set_active_loop_end','902-is_playing_flag','902-is_paused_flag']:
  expected={'902-set_active_loop_start':0,'902-set_active_loop_end':176400,'902-is_playing_flag':1,'902-is_paused_flag':0}[k]
  assert float(v[0])==expected,(t,k,v)
for t in [500,2000,3500,5000,6500]:assert abs(last(t,'samples_per_ms',902)-44.1)<.001
assert not [e for e in events if e[1].endswith('loop-region-feedback')], 'Unexpected invalid/short-loop refusal'
# Both intended channels pass through the original mixer with unchanged level.
for track,gain in [(0,.4),(1,.3)]:
 mixer=x[:,track*2:track*2+2];reader=x[:,4+track*2:6+track*2]
 assert np.max(abs(mixer)-abs(reader)*gain)<1e-6
 # The original mixer has an additional startup envelope; outside those
 # explicit starts, require the exact constant gain (including all loop edits).
 mask=np.ones(len(x),dtype=bool)
 for t in ([.2,6,6.5,7.02,8,9] if track==0 else [.2]):mask[int(t*rate):int((t+.006)*rate)]=False
 assert np.max(abs(mixer[mask]-reader[mask]*gain))<1e-6
silence=[(5.73,5.99),(6.33,6.49),(7.24,7.39),(8.73,8.99),(9.53,11.99)]
for a,b in silence:assert np.max(abs(x[int(a*rate):int(b*rate),[0,1,4,5]]))<1e-6,(a,b)
assert np.max(abs(x[int(7.73*rate):, [2,3,6,7]]))<1e-6
# No 50-ms silent hole during intended active sections; not a claim about every
# short transient. Tiny periodic loops may deliberately approach DC.
for a,b in [(.24,5.69),(6.04,6.29),(6.54,6.99),(8.04,8.69),(9.04,9.49)]:
 for start in np.arange(a,b-.05,.025):
  w=x[int(start*rate):int((start+.05)*rate),0]
  assert np.sqrt(np.mean(w*w))>.002,('silent hole',start)
for start in np.arange(.24,7.68,.025):
 w=x[int(start*rate):int((start+.05)*rate),2];assert np.sqrt(np.mean(w*w))>.025,('B dropout',start)
windows=[]
for a,b,freq in [(.3,.9,220),(1.15,1.28,440),(1.6,1.75,880),(5.12,5.28,1760),(5.52,5.68,220),(6.55,6.69,440),(8.05,8.25,220),(8.4,8.6,440)]:
 w=x[round(a*rate):round(b*rate),:2]
 hz=[np.argmax(abs(np.fft.rfft(w[:,i])))*rate/len(w) for i in range(2)]
 assert abs(hz[0]-freq)<10 and abs(hz[1]-freq*1.5)<10,(a,hz)
 rms=np.sqrt(np.mean(w*w,axis=0));assert .045<rms[0]<.06 and .020<rms[1]<.03,(a,rms)
 windows.append(dict(start=a,end=b,dominant_hz=hz,rms=rms.tolist()))
# Position slope verifies direction separately from a sine wave's spectrum.
for a,b,sign in [(1550,1650,1),(2060,2160,-1),(5110,5190,1)]:
 pos=[float(v[0]) for t,k,v in events if a<t<b and k=='901-play-position-frames']
 assert len(pos)>1 and all(sign*(b-a)>0 for a,b in zip(pos,pos[1:])),(a,b,pos)
peak=np.max(abs(x),axis=0);steps=np.max(abs(np.diff(x,axis=0)),axis=0)
assert max(peak[:2])<.074 and max(peak[2:4])<.056, 'Unexpected amplification'
sharp=np.where(np.max(abs(np.diff(x[:,:2],axis=0)),axis=1)>.025)[0]
result={'host_rate':rate,'file_rate':44100,'duration_s':12,'all_finite':True,'bounds_checks':len(checks)+2,'same_timestamp_edits_compose':True,'slice_restores_whole_content':True,'quantized_slice_waits_for_tick':True,'move_preserves_length_and_clamps':True,'other_shared_buffer_player_unaffected_in_state_and_level':True,'original_mixer_gains_preserved':True,'paused_stopped_empty_silence':True,'expected_pitch_and_stereo':windows,'global_peaks':peak.tolist(),'global_adjacent_steps':steps.tolist(),'sharp_step_times_s':(sharp/rate).tolist(),'extreme_loop_click_gate':'OPEN: one-source-frame clamp produces sharp transitions; retained, not excluded. Short loops can change timbre and RMS through crossover interference.','listening':'Not yet user reviewed.','capture_sha256':hashlib.sha256((P/'capture.wav').read_bytes()).hexdigest()}
(P/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
y=x[:,:2] # isolate the manipulated player for listening
with wave.open(str(P/'listening.wav'),'wb') as w:
 w.setnchannels(2);w.setsampwidth(2);w.setframerate(rate);w.writeframes((np.clip(y,-1,1)*32767).astype('<i2').tobytes())
