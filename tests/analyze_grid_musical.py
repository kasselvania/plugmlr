from pathlib import Path
import subprocess,json
import numpy as np
p=Path('docs/evidence/grid-feedback');x=np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(p/'player-and-master.wav'),'-f','f32le','-']),dtype='<f4').reshape(-1,4)
rms=[float(np.sqrt(np.mean(x[i*48000:(i+1)*48000,2:]**2))) for i in range(16)]
checks={'exact_16_seconds_at_48k':len(x)==768000,'finite':bool(np.isfinite(x).all()),'master_stereo_active':bool((np.max(np.abs(x[:,2:]),axis=0)>.1).all()),'no_clipping':bool(np.max(np.abs(x))<1),'all_playing_seconds_active':all(v>.01 for v in rms[:15]),'stopped_tail_silent':bool(np.max(np.abs(x[int(15.1*48000):]))<1e-6)}
r={'checks':checks,'passed':all(checks.values()),'master_rms_by_second':rms,'channel_peaks':np.max(np.abs(x),axis=0).tolist(),'maximum_adjacent_steps':np.max(np.abs(np.diff(x,axis=0)),axis=0).tolist(),'scope':'Actual original player and post-master taps. Scheduled original row_1 cuts at 4/8/12 seconds; reverse at 10; Stop at 15. Not a claim of universally click-free playback or a recording of physical key gestures.'}
(p/'audio-checks.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));assert r['passed']
