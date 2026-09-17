"""Numerical checks of native editor -> worker -> loader -> original player audio."""
from pathlib import Path
import json, struct, sys
import numpy as np
P=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/plugmlr-editor-stretch')
def read(path):
 b=path.read_bytes();p=12
 while p+8<=len(b):
  tag=b[p:p+4];n=struct.unpack_from('<I',b,p+4)[0];d=b[p+8:p+8+n];p+=8+n+(n%2)
  if tag==b'fmt ':fmt,ch,sr,_,_,bits=struct.unpack_from('<HHIIHH',d)
  if tag==b'data':data=d
 if fmt in (3,65534) and bits==32:a=np.frombuffer(data,dtype='<f4')
 elif fmt==1 and bits==16:a=np.frombuffer(data,dtype='<i2')/32768
 else:raise ValueError((fmt,bits))
 return sr,a.reshape(-1,ch)
def peak(a,sr):
 return np.fft.rfftfreq(len(a),1/sr)[np.argmax(abs(np.fft.rfft(a*np.hanning(len(a))[:,None],axis=0)),axis=0)].tolist()
r,cap=read(P/'capture.wav');result=max((P/'renders').glob('*.wav'),key=lambda p:p.stat().st_mtime)
musical='--musical' in sys.argv
rr,a=read(result);assert r==rr==48000 and len(cap)==8*r and cap.shape[1]==4
assert np.isfinite(cap).all() and np.isfinite(a).all()
assert len(a)==(36000 if musical else 96000) and a.shape[1]==2
expected=[220,330] if musical else [440,660]
render_pitch=peak(a[int(.1*r):int(.65*r)] if musical else a[24000:72000],r)
player_pitch=peak(cap[2*r:3*r,:2] if musical else cap[4*r:5*r,:2],r)
assert all(abs(x-y)<2 for x,y in zip(render_pitch,expected)),render_pitch
assert all(abs(x-y)<2 for x,y in zip(player_pitch,expected)),player_pitch
if musical:
 manifests=[json.loads(p.read_text()) for p in (P/'renders').glob('*.json')]
 assert len(manifests)==4
 first=next(m for m in manifests if m['tempo']['source_bpm']==90)
 assert first['tempo']['target_bpm']==120 and first['duration_multiplier']==.75 and first['pitch_semitones']==0
 assert all(m['tempo']['target_bpm']==120 and m['target_duration_seconds']==.75 for m in manifests)
# The second ORIGINAL playback engine runs across render and adoption. 10ms RMS
# bins and local recurrence detect dropouts or jumps; exclude its loop edge at 4.15s.
ref=cap[int(.4*r):int(7.4*r),2:].astype(float)
rms=np.array([np.sqrt(np.mean(ref[i:i+480]**2,axis=0)) for i in range(0,len(ref)-480,480)])
assert np.min(rms)>0.02,(np.min(rms),np.max(rms))
# Compare the renderer/load window against pre-render level, not absolute mixer gain.
baseline=np.sqrt(np.mean(cap[int(.2*r):int(.4*r),2:].astype(float)**2,axis=0))
window=np.sqrt(np.mean(cap[int(.6*r):int(3.6*r),2:].astype(float)**2,axis=0))
assert np.max(abs(window/baseline-1))<.01
record=dict(capture_seconds=len(cap)/r,render_seconds=len(a)/r,render_pitch_hz=render_pitch,adopted_player_pitch_hz=player_pitch,
 finite=True,other_original_player_min_10ms_rms=rms.min(axis=0).tolist(),other_original_player_relative_rms=(window/baseline).tolist(),
 output_file=result.name,limitations=['Internal original mixer output, not device/DAW underrun proof','Synthetic stereo source, not musical listening acceptance','Copy import uses the synchronous loader','Native control sequence, physical mouse activation not established'])
(P/'analysis.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
