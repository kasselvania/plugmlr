"""Actual original-player position and stereo audio across long-held Grid loops."""
from pathlib import Path
import json,subprocess
import numpy as np
p=Path('docs/evidence/grid-loop/continuity')
x=np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(p/'player-master-position.wav'),'-f','f32le','-']),dtype='<f4').reshape(-1,10)
s=np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i','DrumLoop.wav','-f','f32le','-']),dtype='<f4').reshape(-1,2)
def win(a,b):return x[int(a*48000):int(b*48000)]
def match(t):
 y=win(t,t+.2);pos=y[:,8].astype(float)*44100+1
 # Compare native file samples at the measured reader position. The original
 # reader has a +1 table offset; linear reference approximates tabread4~.
 return [float(np.corrcoef(y[:,ch],np.interp(pos,np.arange(len(s)),s[:,ch]))[0,1]) for ch in [0,1]]
f=match(1.7);r=match(6.7)
checks={
 'bounded_12_seconds':abs(len(x)/48000-12)<512/48000,
 'finite':bool(np.isfinite(x).all()),
 'audio_below_full_scale':bool(np.max(abs(x[:,:6]))<1),
 'forward_no_position_restart':bool(np.max(abs(np.diff(win(1.7,1.9)[:,8])-1/48000))<2/44100),
 'reverse_no_position_restart':bool(np.max(abs(np.diff(win(6.7,6.9)[:,8])+1/48000))<2/44100),
 'forward_audio_tracks_continuous_position':min(f)>.99,
 'reverse_audio_tracks_continuous_position':min(r)>.99,
 'outside_wraps_immediately':bool(.0<float(x[int(5.42*48000),8])<.04),
 'new_bounds_forward':bool(np.max(abs(win(1.9,2.8)[:,6:8]-[78985/44100,236955/44100]))<1/44100),
 'new_bounds_reverse':bool(np.max(abs(win(6.9,7.8)[:,6:8]-[78985/44100,236955/44100]))<1/44100),
 'master_active':bool(np.max(abs(x[:,4:6]))>.1),
 'final_master_silent':bool(np.max(abs(win(10.2,11.8)[:,4:6]))<1e-6),
}
r=dict(passed=all(checks.values()),checks=checks,frames=len(x),host_rate=48000,file_rate=44100,forward_stereo_correlations=f,reverse_stereo_correlations=r)
(p/'checks.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));assert r['passed']
