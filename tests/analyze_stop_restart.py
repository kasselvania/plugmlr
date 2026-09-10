"""Check retained native Stop/restart captures; no separate playback simulation.

Usage: python3 tests/analyze_stop_restart.py docs/evidence/stop-restart
Requires NumPy and ffmpeg. Private hardware captures are checked only when present.
NPZ files retain exact decoded float samples and sample rate from the original WAV.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np
from analyze_live_record import read

RATE = 48000
GAIN = .548 * .75
RESTARTS = [50, 500, 909, 1309, 1709, 2115, 2613, 3500, 4009, 4412, 5050]
CANCEL_STARTS = [50, 1000, 2050, 2509, 3550, 4200]
WINDOWS = [.08, .54, .94, 1.35, 1.75, 2.16, 2.66, 3.56, 4.06, 4.46, 5.10]


def load(folder, stem, channels):
    path = folder / (stem + '.wav')
    if path.exists():
        info = json.loads(subprocess.check_output([
            'ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(path)]))['streams'][0]
        assert int(info['sample_rate']) == RATE and info['channels'] == channels
        return read(path, channels)
    with np.load(folder / (stem + '.npz')) as data:
        assert int(data['sample_rate']) == RATE and data['samples'].shape[1] == channels
        return data['samples']


def events(folder, case):
    return [line.rstrip(';').split() for line in
            (folder / (case + '-events.txt')).read_text().splitlines()]


def starts(rows):
    return [float(r[0]) for r in rows if r[1].endswith('-is_playing_flag') and r[2] == '1']


def nonfinite_positions(rows):
    return [float(r[0]) for r in rows if r[1].endswith('-playbar_data_i')
            and not np.isfinite(float(r[2]))]


def audio_case(folder, name, windows=WINDOWS):
    x = load(folder, name + '-player-mixer-48', 6)
    readers = load(folder, name + '-readers-48', 10)
    result = {
        'frames': len(x), 'reader_frames': len(readers),
        'all_samples_finite': bool(np.isfinite(x).all() and np.isfinite(readers).all()),
        'peak_player_LR_mixer_LR': np.max(abs(x[:, 2:6]), axis=0).tolist(),
        'max_adjacent_step_player_LR_mixer_LR': np.max(abs(np.diff(x[:, 2:6], axis=0)), axis=0).tolist(),
        'final_tail_zero': bool(np.all(x[-12000:, 2:6] == 0)),
    }
    result['steady_windows'] = []
    for start in windows:
        a = x[round(start*RATE):round((start+.1)*RATE), 2:6]
        silent = np.all(abs(a[:, :2]) < 1e-8, axis=1)
        edges = np.diff(np.r_[False, silent, False].astype(int))
        lengths = np.flatnonzero(edges == -1) - np.flatnonzero(edges == 1)
        result['steady_windows'].append({
            'seconds': [start, start+.1],
            'rms_LR': np.sqrt(np.mean(a[:, :2]**2, axis=0)).tolist(),
            'mixer_gain_error': float(np.max(abs(a[:, 2:4] - GAIN*a[:, :2]))),
            'longest_silent_run_frames': int(max(lengths, default=0)),
        })
    result['reader_shutdowns'] = []
    for gain, flag in [(5, 8), (7, 9)]:
        off = np.flatnonzero((readers[:-1, flag] > .5) & (readers[1:, flag] < .5))
        # Passive taps can retain stale values after switch~ stops. Inspect the
        # sample immediately BEFORE shutdown, not the inactive reader afterwards.
        result['reader_shutdowns'].append({
            'count': len(off), 'nonzero_gain_before_off': int(np.count_nonzero(abs(readers[off, gain]) > 1e-4)),
            'maximum_gain_before_off': float(max(abs(readers[off, gain]), default=0)),
        })
    return result


def analyze(folder):
    cases = {name: audio_case(folder, name) for name in [
        'baseline-constant', 'candidate-constant', 'baseline-wave', 'candidate-wave']}
    cases['candidate-cancel'] = audio_case(folder, 'candidate-cancel', [.08, 1.04, 2.09, 2.55, 3.60, 4.25])
    checks = {}
    for signal, max_step in [('constant', .001), ('wave', .004)]:
        baseline, candidate = (cases[prefix + '-' + signal] for prefix in ['baseline', 'candidate'])
        checks[signal + '_baseline_exposes_hard_cut'] = max(baseline['max_adjacent_step_player_LR_mixer_LR'][:2]) > .07
        checks[signal + '_candidate_step_bounded'] = max(candidate['max_adjacent_step_player_LR_mixer_LR'][:2]) < max_step
        checks[signal + '_peak_unchanged'] = bool(np.allclose(baseline['peak_player_LR_mixer_LR'], candidate['peak_player_LR_mixer_LR'], rtol=0, atol=2e-6))
        actual = starts(events(folder, 'candidate-' + signal))
        candidate['start_times_ms'] = actual
        checks[signal + '_queued_restart_timing'] = actual == RESTARTS
    for name, case in cases.items():
        checks[name + '_finite_bounded_capture'] = case['all_samples_finite'] and 335000 < case['frames'] <= 336064 and 335000 < case['reader_frames'] <= 336064
        checks[name + '_stopped_tail'] = case['final_tail_zero']
        checks[name + '_steady_audio_and_gain'] = all(min(w['rms_LR']) > .01 and w['mixer_gain_error'] < 2e-6 and w['longest_silent_run_frames'] < 64 for w in case['steady_windows'])
        if name.startswith('candidate'):
            checks[name + '_readers_fade_before_off'] = all(r['count'] > 0 and r['nonzero_gain_before_off'] == 0 for r in case['reader_shutdowns'])
    checks['baseline_reader_shutdown_exposes_nonzero_gain'] = sum(r['nonzero_gain_before_off'] for r in cases['baseline-constant']['reader_shutdowns']) > 0
    cases['candidate-cancel']['start_times_ms'] = starts(events(folder, 'candidate-cancel'))
    checks['pending_play_cancelled_coalesced_and_reload_stops'] = cases['candidate-cancel']['start_times_ms'] == CANCEL_STARTS
    cancel = load(folder, 'candidate-cancel-player-mixer-48', 6)
    cases['candidate-cancel']['stopped_windows'] = [
        {'seconds': [a, b], 'exact_zero': bool(np.all(cancel[round(a*RATE):round(b*RATE), 2:6] == 0))}
        for a, b in [(.53, .99), (1.33, 2.04), (3.03, 3.54), (4.03, 4.19), (4.53, 6.99)]]
    checks['cancelled_starts_remain_silent'] = all(w['exact_zero'] for w in cases['candidate-cancel']['stopped_windows'])
    recording = {}
    for prefix in ['baseline', 'candidate']:
        rows = events(folder, prefix + '-record')
        loaded = [r for r in rows if r[1:3] == ['l_b_buffer_states', '4'] and r[-1] == '1']
        recording[prefix] = {'content_frames': int(loaded[0][5]), 'loaded_ms': float(loaded[0][0]),
                             'nonfinite_position_times_ms': nonfinite_positions(rows)}
        checks[prefix + '_record_stop_direct'] = recording[prefix]['content_frames'] == 15616 and recording[prefix]['loaded_ms'] == 378
        local = folder / 'local-input'
        array = local / (prefix + '-record-live4-48.wav')
        if array.exists():
            samples = load(local, prefix + '-record-live4-48', 2)
            checks[prefix + '_retained_record_capacity'] = len(samples) == 96000 and bool(np.isfinite(samples).all()) and bool(np.all(samples[15616:] == 0))
            recording[prefix]['local_array_sha256'] = hashlib.sha256(array.read_bytes()).hexdigest()
    checks['baseline_exposes_empty_position_nan'] = bool(recording['baseline']['nonfinite_position_times_ms'])
    checks['candidate_empty_positions_finite'] = not recording['candidate']['nonfinite_position_times_ms'] and all(not nonfinite_positions(events(folder, n)) for n in cases if n.startswith('candidate'))
    return {'host_rate': RATE, 'configured_mixer_gain': GAIN, 'cases': cases, 'recording': recording,
            'checks': checks, 'passed': all(checks.values()),
            'scope': 'Actual native 48 kHz captures. Baseline defects are expected controls. No listening judgment, universal click-free claim, pause, reverse-slew, 44.1 kHz host or DAW acceptance.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    result = analyze(parser.parse_args().folder)
    print(json.dumps(result, indent=2))
    raise SystemExit(not result['passed'])
