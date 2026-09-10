"""Check actual original-player and mixer capture from load-isolation-check.pd.

python tests/analyze_load_isolation.py CAPTURE.wav EVENTS.txt
Accepts retained NPZ. Requires NumPy and ffmpeg/ffprobe for WAV input.
A failing pre-repair capture should report slot2_load_muted_track1=true.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from analyze_speed_capture import read


def analyze(path, events_path):
    x, sr = read(path)
    if x.shape[1] != 6:
        raise ValueError('Expected post-mixer L/R, player L/R, master frames, playbar')
    rows = []
    for a,b in [(.3,.9),(1.2,1.8),(2.2,2.7),(3,3.4),(4,4.4)]:
        w=x[round(a*sr):round(b*sr)].astype(float)
        rms=np.sqrt(np.mean(w[:,:4]**2,axis=0))
        rows.append({'seconds':[a,b], 'post_mixer_rms':rms[:2].tolist(),
            'player_rms':rms[2:4].tolist(),
            'mixer_gain':(rms[:2]/np.maximum(rms[2:4],1e-20)).tolist(),
            'master_span_frames':float(np.ptp(w[:,4])),
            'playbar_value_span':float(np.ptp(w[:,5]))})
    events=[line.rstrip(';').split() for line in events_path.read_text().splitlines()]
    closes=[float(e[0]) for e in events if e[1]=='track1_close']
    second=[float(e[0]) for e in events if e[1]=='track2_close']
    valid_gain = min(rows[0]['mixer_gain']) > .01
    gain_stays = all(np.allclose(row['mixer_gain'],rows[0]['mixer_gain'],atol=1e-5) for row in rows)
    result={'capture_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'host_rate':sr, 'frames':len(x),
        'nonfinite_samples':int((~np.isfinite(x)).sum()),
        'windows':rows, 'track1_close_times_ms':closes,'track2_close_times_ms':second,
        'slot2_load_muted_track1': bool(valid_gain and max(rows[1]['post_mixer_rms']) < 1e-7),
        'playbar_updates_after_switches': all(row['playbar_value_span'] > .25 for row in rows[3:]),
        'limits':'Five-second native fixture. Captures the actual mixer, not the physical speaker output. Does not accept every transport transition or diagnose an independently observed GUI freeze.'}
    result['passed']=bool(result['nonfinite_samples']==0 and 4.99<len(x)/sr<=5.01 and valid_gain and gain_stays and
        all(min(row['player_rms']) > .04 and row['master_span_frames']>10000 for row in rows) and
        not any(1000<=t<2000 for t in closes) and 1040 in second and result['playbar_updates_after_switches'])
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('capture',type=Path);p.add_argument('events',type=Path)
    a=p.parse_args();r=analyze(a.capture,a.events)
    print(json.dumps(r,indent=2));raise SystemExit(not r['passed'])
