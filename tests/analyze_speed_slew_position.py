"""Check actual native speed-slew captures; requires NumPy and ffmpeg.

Usage: python3 tests/analyze_speed_slew_position.py docs/evidence/speed-slew-position
WAV/NPZ are native capture data. Private musical checks are optional.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from analyze_stop_restart import load, audio_case, events, starts, RESTARTS, RATE, GAIN
from analyze_instant_reverse import longest_silence, turn_rows, TURNS, ACTIVE

STRESS_ACTIVE = [(.08, 1.24), (1.28, 2.99), (3.03, 3.64), (3.70, 3.99), (4.39, 5.49)]
# Exclude explicit initial starts, loop-region/slice edits, Stop/Play, empty selection
# and Pause/Resume. Those are separate operations, not speed-position qualification.
EXCLUSIONS = {
    'wave': [(0, 80), (3195, 3280), (3999, 4020), (4399, 4680), (4999, 5290), (5940, 7000)],
    'stress': [(0, 80), (1249, 1268), (3000, 3019), (3650, 3700), (4000, 4390), (5500, 7000)],
}


def reader_steps(r, x, kind):
    rows = []
    times = np.arange(len(r)-1) / 48
    allowed = np.ones(len(times), dtype=bool)
    for a, b in EXCLUSIONS[kind]:
        allowed &= ~((times >= a) & (times <= b))
    sounding = (abs(x[:-1, 4:6]).max(axis=1) > 1e-6) & (abs(x[1:, 4:6]).max(axis=1) > 1e-6)
    for pos, gain, flag in [(4, 5, 8), (6, 7, 9)]:
        eligible = allowed & sounding & (r[:-1, gain] > .01) & (r[1:, gain] > .01) & (r[:-1, flag] > .5) & (r[1:, flag] > .5)
        d = abs(np.diff(r[:, pos]))
        bad = np.flatnonzero(eligible & (d > 4.05))
        rows.append({'reader': (pos-4)//2, 'checked_steps': int(eligible.sum()),
                     'max_frame_step': float(d[eligible].max()),
                     'oversized_step_times_ms': (bad/48).tolist()})
    return rows


def analyze(folder):
    cases, checks = {}, {}
    for name, kind in [('baseline-wave', 'wave'), ('candidate-wave', 'wave'),
                       ('baseline-stress', 'stress'), ('candidate-stress', 'stress'),
                       ('candidate-constant', 'stress')]:
        x = load(folder, name+'-player-mixer-48', 6)
        r = load(folder, name+'-readers-48', 10)
        windows = []
        for a, b in ACTIVE['wave'] if kind == 'wave' else STRESS_ACTIVE:
            w = x[round(a*RATE):round(b*RATE), 2:6]
            windows.append({'seconds': [a, b], 'longest_silence_frames': longest_silence(w[:, :2]),
                            'mixer_gain_error': float(abs(w[:, 2:]-GAIN*w[:, :2]).max())})
        d = abs(np.diff(x[:, 2:4], axis=0))
        rows = reader_steps(r, x, kind)
        cases[name] = {'frames': len(x), 'whole_max_audio_step_LR': d.max(axis=0).tolist(),
                       'active_windows': windows, 'audible_reader_steps': rows}
        checks[name+'_finite_bounded_stopped'] = bool(335000 < len(x) <= 336064 and len(x) == len(r) and np.isfinite(x).all() and np.isfinite(r).all() and np.all(x[-12000:, 2:6] == 0))
        checks[name+'_active_audio_and_mixer_gain'] = all(w['longest_silence_frames'] < 64 and w['mixer_gain_error'] < 2e-6 for w in windows)
        if name.startswith('candidate'):
            checks[name+'_qualified_reader_position_continuity'] = all(row['checked_steps'] > 1000 and not row['oversized_step_times_ms'] for row in rows)
            checks[name+'_rate_range'] = bool(np.all((r[:, 3] >= .25-1e-5) & (r[:, 3] <= 4+1e-5)))
        if kind == 'wave':
            cases[name]['slew_max_audio_step_LR'] = d[120000:152000].max(axis=0).tolist()
        else:
            collisions = []
            for ms in [1250, 3001]:
                a = round(ms*48); b = a+480
                collisions.append({'region_command_ms': ms, 'max_audio_step_LR': d[a:b].max(axis=0).tolist()})
            cases[name]['unrepaired_region_slice_collisions'] = collisions
            if name.startswith('candidate'):
                checks[name+'_empty_and_stopped_mixer_silent'] = bool(np.all(x[round(4.04*RATE):round(4.29*RATE), 4:6] == 0) and np.all(x[round(5.54*RATE):, 4:6] == 0))
        if name == 'candidate-stress':
            settled = []
            for a, b, target in [(0.94,.97,.5),(1.00,1.09,2),(1.13,1.22,4),(3.15,3.20,.25),(3.40,3.45,4),(5.35,5.45,1)]:
                error = float(abs(r[round(a*RATE):round(b*RATE),3]-target).max())
                settled.append({'seconds':[a,b], 'target':target, 'max_rate_error':error})
            cases[name]['settled_rates'] = settled
            checks['stress_final_targets_after_interruptions'] = all(w['max_rate_error'] < 1e-5 for w in settled)
        if name == 'candidate-constant':
            expected = np.array([2621, -1311])/32768
            errors = [float(abs(x[round(a*RATE):round(b*RATE), 2:4]/expected-1).max()) for a,b in STRESS_ACTIVE]
            cases[name]['stereo_gain_errors'] = errors
            checks['constant_stereo_order_and_gain'] = max(errors) < 2e-6
        if name == 'candidate-wave':
            turns = turn_rows(r,x,TURNS); cases[name]['reverse_regression'] = turns
            checks['reverse_position_and_signed_rate_regression'] = all(max(t['master_max_frame_step'],t['audible_reader_max_frame_step']) <= t['rate_magnitude']+.02 and t['before_after_frames_per_sample'][0]*t['before_after_frames_per_sample'][1] < 0 and abs(abs(t['before_after_frames_per_sample'][0])-abs(t['before_after_frames_per_sample'][1])) < .01 for t in turns)
    for kind in ['wave','stress']:
        checks[kind+'_baseline_exposes_position_jumps'] = sum(len(r['oversized_step_times_ms']) for r in cases['baseline-'+kind]['audible_reader_steps']) > 0
    checks['paired_slew_audio_step_reduced'] = max(cases['candidate-wave']['slew_max_audio_step_LR']) < .007 and max(cases['baseline-wave']['slew_max_audio_step_LR']) > .03
    checks['region_collision_is_retained_baseline_failure'] = all(cases[n]['unrepaired_region_slice_collisions'][0]['max_audio_step_LR'][0] > .1 for n in ['baseline-stress','candidate-stress'])
    stop = audio_case(folder,'candidate-stop'); cases['candidate-stop'] = stop
    checks['stop_restart_regression'] = starts(events(folder,'candidate-stop')) == RESTARTS and stop['all_samples_finite'] and stop['final_tail_zero'] and max(stop['max_adjacent_step_player_LR_mixer_LR']) < .001 and all(v['nonzero_gain_before_off'] == 0 for v in stop['reader_shutdowns'])
    local = folder/'local-input'
    if (local/'candidate-music-readers-48.wav').exists():
        r = load(local,'candidate-music-readers-48',10); x = load(local,'candidate-music-player-mixer-48',6)
        rates = []
        for a,b,rate in [(3.55,3.65,.5),(4.40,4.45,-2),(5.15,5.25,1)]:
            delta = np.diff(r[round(a*RATE):round(b*RATE),2])
            # A legitimate whole-file wrap is not a playback slope. Retain its count.
            wrap = abs(delta) > 4.1
            actual = float(delta[~wrap].mean())
            rates.append({'seconds':[a,b],'expected':rate*44100/48000,'actual':actual,'wrap_steps_excluded':int(wrap.sum())})
        boundary = np.diff(r[round(4.35*RATE):round(4.45*RATE),2])
        cases['local-music'] = {'settled_file_host_rates':rates, 'master_boundary_observation': {'seconds':[4.35,4.45], 'whole_file_wraps':int((abs(boundary)>4.1).sum()), 'held_frames':int((abs(boundary)<1e-8).sum()), 'note':'Signed-rate window begins after this wrap; it does not qualify exact full-loop timing.'}}
        checks['local_music_file_host_conversion'] = all(abs(v['actual']-v['expected']) < 1e-4 for v in rates)
        checks['local_music_finite_stopped'] = bool(np.isfinite(x).all() and np.isfinite(r).all() and np.all(x[-12000:,2:6] == 0))
    return {'host_rate':RATE,'checks':checks,'passed':all(checks.values()),'cases':cases,
            'excluded_command_windows_ms':EXCLUSIONS,
            'scope':'Actual stereo player/mixer/readers. Four frames/sample is the largest supported rate at this matching host/file rate; .05 frame is numerical tolerance, not an audibility threshold. Region/slice collisions and Pause remain unaccepted. No universal click-free claim.'}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('folder',type=Path)
    result=analyze(parser.parse_args().folder);print(json.dumps(result,indent=2));raise SystemExit(not result['passed'])
