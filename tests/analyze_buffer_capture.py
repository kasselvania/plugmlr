"""Check native buffer-checks audio and metadata; requires NumPy and ffmpeg.

python tests/analyze_buffer_capture.py CAPTURE.wav EVENTS.txt CONFIG.txt
The live buffer is seeded test content, not evidence of a working recorder.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from analyze_speed_capture import read, longest_run

WINDOWS = [(.3,1,48000,1,220,440), (1.3,2,44100,1,330,660),
 (2.3,3,48000,1,550,770), (3.7,4.1,48000,-1,220,440),
 (4.4,5,48000,-1,220,440), (5.3,5.5,0,0,0,0),
 (5.8,6,44100,-1,330,660), (6.3,6.5,0,0,0,0),
 (6.7,7,48000,1,220,440), (7.2,7.3,48000,1,220,440),
 (7.7,8,44100,1,330,660), (8.4,8.6,0,0,0,0),
 (9,9.4,48000,1,220,440), (9.7,10,0,0,0,0)]


def analyze(path, events_path, config_path):
    x, host = read(path)
    x = x.astype(float)
    result = {'capture_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'host_rate': host, 'frames': len(x), 'duration_s': len(x)/host,
        'nonfinite_samples': int((~np.isfinite(x)).sum()),
        'peak': np.abs(x[:,:2]).max(axis=0).tolist(), 'windows': []}
    checks = [result['nonfinite_samples'] == 0, 10.49 < len(x)/host <= 10.51,
              max(result['peak']) < 3500/32768*1.05]
    for start, end, source_rate, direction, left, right in WINDOWS:
        if left == 550:
            source_rate = host  # seeded recording fixture matches the host
        w = x[round(start*host):round(end*host)]
        delta = np.diff(w[:,2])
        rms = np.sqrt(np.mean(w[:,:2]**2, axis=0))
        moving = (abs(delta) > 1e-7) & (abs(delta) < 3)
        rate = float(np.median(delta[moving])*host/source_rate) if moving.any() and source_rate else 0
        frequencies = [float(np.argmax(abs(np.fft.rfft(w[:,c]*np.hanning(len(w)))))*host/len(w)) for c in range(2)]
        _, held = longest_run(delta == 0)
        if direction:
            expected = np.array([3500,2500])/32768/np.sqrt(2)
            passed = (abs(rate-direction) < .002 and
                      np.all(abs(rms/expected-1) < .025) and
                      np.all(abs(np.array(frequencies)-[left,right]) <= host/len(w)) and
                      held/host < .003)
        else:
            passed = float(np.max(abs(w[:,:2]))) < 1e-7 and np.all(delta == 0)
        checks.append(bool(passed))
        result['windows'].append({'seconds':[start,end], 'signed_rate':rate,
            'channel_hz':frequencies, 'rms':rms.tolist(),
            'longest_position_hold_ms':held/host*1000, 'passed':bool(passed)})
    result['transitions'] = []
    for t in (1.1,2.1,3.1,3.6,4.2,5.1,6.1,7.4,8.1,8.3,9.5):
        w = x[round((t-.01)*host):round((t+.06)*host),:2]
        _, quiet = longest_run(np.max(abs(w),axis=1) < 1e-5)
        result['transitions'].append({'command_s':t,
            'max_sample_step':np.max(abs(np.diff(w,axis=0)),axis=0).tolist(),
            'longest_near_silence_ms':quiet/host*1000})
    result['switch_steps_below_fixture_limit'] = all(max(t['max_sample_step']) < .025 for t in result['transitions'] if t['command_s'] in (1.1,2.1,3.6,4.2,7.4,8.1))
    checks.append(result['switch_steps_below_fixture_limit'])
    events = [line.rstrip(';').split() for line in events_path.read_text().splitlines()]
    selections = [(float(e[0]),e[2]) for e in events if e[1]=='buffer']
    expected = [(120,'sample_buffer_1'),(1120,'sample_buffer_2'),(2120,'live_buffer_1'),
        (3620,'sample_buffer_1'),(4224,'sample_buffer_1'),(5120,'live_buffer_2'),
        (5520,'sample_buffer_2'),(6120,'sample_buffer_1'),(7420,'sample_buffer_2'),
        (8120,'live_buffer_1'),(8620,'sample_buffer_1')]
    result['selection_events_match'] = selections == expected
    result['other_kind_update_ignored'] = not any(7100 <= float(e[0]) < 7400 and e[1] in ('end','rate_khz','ready','buffer') for e in events)
    result['stop_cancels_resume'] = not any(6105 < float(e[0]) < 6500 and e[1]=='playing' and e[2]=='1' for e in events)
    config = [line.rstrip(';').split() for line in config_path.read_text().splitlines()]
    states = {int(float(e[0])):list(map(float,e[3:])) for e in config if e[1:3]==['length','1']}
    config_expected = {20:[2,8,16,1],80:[2,8,12,1],100:[1,3,3,1],140:[1,3,3,1],
        180:[2,2,16/3,1],220:[2,2,0,0],260:[2,2,4,1],380:[2,2,4,1],440:[0,2,0,0]}
    result['length_configuration_matches'] = all(t in states and np.allclose(states[t],v,atol=1e-5) for t,v in config_expected.items())
    content = next(e for e in config if e[1:3]==['live_state','1'])
    result['recorded_duration_unchanged'] = abs((float(content[5])-float(content[4]))/(float(content[3])*1000)-.8) < 1e-6
    checks += [result[k] for k in ('selection_events_match','other_kind_update_ignored','stop_cancels_resume','length_configuration_matches','recorded_duration_unchanged')]
    result['passed'] = all(checks)
    result['limits'] = 'Short native fixtures; a deliberate fade gap is expected on buffer change. Sample-step and silence measurements are not universal click-free or listening acceptance.'
    return result

def analyze_replacement(path):
    x, host = read(path)
    quiet = [(0, .1), (.24, .49), (.53, .99)]
    quiet_peaks = [float(abs(x[round(a*host):round(b*host), :2]).max()) for a,b in quiet]
    w = x[round(.15*host):round(.19*host), :2].astype(float)
    rms = np.sqrt(np.mean(w*w, axis=0))
    expected = np.array([3500,2500])/32768/np.sqrt(2)
    result = {'capture_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'host_rate': host, 'frames': len(x),
        'nonfinite_samples': int((~np.isfinite(x)).sum()),
        'quiet_windows_s': quiet, 'quiet_peaks': quiet_peaks,
        'normal_live_start_rms': rms.tolist()}
    result['passed'] = bool(result['nonfinite_samples'] == 0 and
        .99 < len(x)/host <= 1.01 and max(quiet_peaks) < 1e-7 and
        np.all(abs(rms/expected-1) < .025))
    return result


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('capture',type=Path);p.add_argument('events',type=Path);p.add_argument('config',type=Path)
    p.add_argument('--replacement', type=Path, help='Optional one-second replacement race capture')
    a=p.parse_args();r=analyze(a.capture,a.events,a.config)
    if a.replacement:
        r['replacement_checks'] = analyze_replacement(a.replacement)
        r['passed'] = r['passed'] and r['replacement_checks']['passed']
    print(json.dumps(r,indent=2));raise SystemExit(not r['passed'])
