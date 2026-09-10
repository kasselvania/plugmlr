"""Inspect actual native reverse captures; audio still comes from the Pd player.

python3 tests/analyze_instant_reverse.py docs/evidence/instant-reverse
Requires NumPy and ffmpeg. Accepts WAV or exact decoded float samples in NPZ.
Private musical captures are checked only when available locally.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from analyze_stop_restart import load, audio_case, events, starts, RESTARTS, GAIN, RATE

TURNS = [233, 404, 650, 652, 654, 656, 658, 660, 1133, 1437, 1739,
         2041, 2611, 2817, 3500, 3753, 4004]
EDGE_TURNS = [225, 227, 229, 329, 379, 379.2, 379.4, 379.6, 379.8, 380,
              831.25, 862.5, 893.75, 1204, 1208, 1212, 2500, 4433]
ACTIVE = {
    'wave': [(.08, 3.19), (3.28, 4.39), (4.68, 4.99), (5.28, 5.94)],
    'edges': [(.08, 1.99), (2.48, 2.99), (3.04, 3.39), (3.43, 3.445), (4.29, 4.99)],
}


def longest_silence(samples):
    silent = np.all(abs(samples) < 1e-7, axis=1)
    edges = np.diff(np.r_[False, silent, False].astype(int))
    return int(max(np.flatnonzero(edges == -1) - np.flatnonzero(edges == 1), default=0))


def turn_rows(readers, audio, times):
    rows = []
    for ms in times:
        # Observed passive send~/receive~ capture latency: one 64-frame block.
        # Keep a fixed narrow window; do not search for a better-fitting offset.
        n = round(ms * RATE / 1000) + 64
        w = readers[n-2:n+3]
        before = float(np.median(np.diff(readers[n-8:n-2, 2])))
        after = float(np.median(np.diff(readers[n+2:n+8, 2])))
        audible_steps = []
        for pos, gain, dsp in [(4, 5, 8), (6, 7, 9)]:
            on = (w[:-1, dsp] > .5) & (w[1:, dsp] > .5) & (w[:-1, gain] > .001) & (w[1:, gain] > .001)
            audible_steps.extend(abs(np.diff(w[:, pos]))[on].tolist())
        rows.append({
            'command_ms': ms, 'before_after_frames_per_sample': [before, after],
            'master_max_frame_step': float(abs(np.diff(w[:, 2])).max()),
            'audible_reader_max_frame_step': max(audible_steps, default=0),
            'rate_magnitude': float(w[:, 3].max()),
            'player_max_audio_step_LR': abs(np.diff(audio[n-2:n+3, 2:4], axis=0)).max(axis=0).tolist(),
        })
    return rows


def analyze(folder):
    cases, checks = {}, {}
    for name, kind in [('baseline-wave', 'wave'), ('candidate-wave', 'wave'),
                       ('candidate-edges', 'edges'), ('candidate-constant', 'edges')]:
        x = load(folder, name + '-readers-48', 10)
        y = load(folder, name + '-player-mixer-48', 6)
        turns = turn_rows(x, y, TURNS if kind == 'wave' else EDGE_TURNS)
        windows = []
        for a, b in ACTIVE[kind]:
            w = y[round(a*RATE):round(b*RATE), 2:6]
            windows.append({'seconds': [a, b], 'longest_silent_run_frames': longest_silence(w[:, :2]),
                            'mixer_gain_error': float(abs(w[:, 2:] - GAIN*w[:, :2]).max())})
        cases[name] = {'frames': len(y), 'turns': turns, 'active_windows': windows,
                       'whole_capture_max_step_LR': abs(np.diff(y[:, 2:4], axis=0)).max(axis=0).tolist()}
        checks[name + '_bounded_finite_stopped'] = 335000 < len(y) <= 336064 and 335000 < len(x) <= 336064 and bool(np.isfinite(x).all() and np.isfinite(y).all()) and bool(np.all(y[-12000:, 2:6] == 0))
        checks[name + '_active_audio_and_mixer_gain'] = all(w['longest_silent_run_frames'] < 64 and w['mixer_gain_error'] < 2e-6 for w in windows)
        if name.startswith('candidate'):
            checks[name + '_turn_position_continuity'] = all(max(r['master_max_frame_step'], r['audible_reader_max_frame_step']) <= r['rate_magnitude'] + .02 for r in turns)
            checks[name + '_direction_flips_preserve_speed'] = all(a*b < 0 and abs(abs(a)-abs(b)) < .01 for a, b in (r['before_after_frames_per_sample'] for r in turns))
            # This fixture's steepest ordinary waveform slope is < .0033/frame.
            # This is signal-specific, not a general click/audibility threshold.
            checks[name + '_turn_audio_step_bounded'] = all(max(r['player_max_audio_step_LR']) < .0033*r['rate_magnitude'] + .0001 for r in turns)
        if name == 'candidate-constant':
            expected = np.array([2621, -1311]) / 32768
            errors = [float(abs(y[round(a*RATE):round(b*RATE), 2:4] / expected - 1).max()) for a, b in ACTIVE['edges']]
            cases[name]['constant_gain_errors'] = errors
            checks['constant_stereo_order_and_unity_through_fades'] = max(errors) < 2e-6
        if kind == 'edges':
            silent_windows = [(2.05, 2.39), (3.49, 3.98), (4.05, 4.24)]
            # Play/Pause at 3450 ms pauses the successful automatic buffer start.
            # Legacy paused readers hold DC; the actual mixer must be silent.
            checks[name + '_empty_paused_and_stopped_mixer_silent'] = all(np.all(y[round(a*RATE):round(b*RATE), 4:6] == 0) for a, b in silent_windows)
            checks[name + '_narrow_regions_preserved'] = all(float(x[round(a*RATE):round(b*RATE), 2].min()) >= lo-.01 and float(x[round(a*RATE):round(b*RATE), 2].max()) <= hi+.01 for a, b, lo, hi in [(.13, 1.19, 3000, 9000), (1.24, 1.99, 4500, 7500)])
    checks['baseline_exposes_reverse_jump'] = cases['baseline-wave']['turns'][0]['master_max_frame_step'] > 40
    wave = load(folder, 'candidate-wave-player-mixer-48', 6)
    checks['paused_and_stopped_reverse_do_not_start_mixer'] = all(np.all(wave[round(a*RATE):round(b*RATE), 4:6] == 0) for a, b in [(4.42, 4.64), (5.03, 5.24)])
    stop = audio_case(folder, 'candidate-stop')
    cases['candidate-stop'] = stop
    checks['stop_restart_regression'] = starts(events(folder, 'candidate-stop')) == RESTARTS and stop['all_samples_finite'] and stop['final_tail_zero'] and max(stop['max_adjacent_step_player_LR_mixer_LR']) < .001 and all(r['nonzero_gain_before_off'] == 0 for r in stop['reader_shutdowns'])
    local = folder / 'local-input'
    if (local / 'candidate-music-readers-48.wav').exists():
        x = load(local, 'candidate-music-readers-48', 10)
        y = load(local, 'candidate-music-player-mixer-48', 6)
        rates = []
        for t, multiplier in [(3483, .5), (4237, -2), (5000, 1)]:
            w = x[round((t+40)*48):round((t+80)*48), 2]
            rates.append({'command_ms': t, 'expected_frames_per_host_sample': multiplier*44100/48000,
                          'measured_frames_per_host_sample': float(np.diff(w).mean())})
        cases['local-music'] = {'file_44100_host_48000_rates': rates}
        checks['local_music_mismatch_rates'] = all(abs(r['expected_frames_per_host_sample']-r['measured_frames_per_host_sample']) < 1e-4 for r in rates)
        checks['local_music_finite_and_stopped'] = bool(np.isfinite(x).all() and np.isfinite(y).all() and np.all(y[-12000:, 2:6] == 0))
    return {'host_rate': RATE, 'cases': cases, 'checks': checks, 'passed': all(checks.values()),
            'scope': 'Actual native samples and existing reader ramps. Direction-change windows are qualified; residual speed-slew and Pause edges, 44.1 kHz host and tape slew are not. No universal click-free claim or automated listening judgment.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    result = analyze(parser.parse_args().folder)
    print(json.dumps(result, indent=2))
    raise SystemExit(not result['passed'])
