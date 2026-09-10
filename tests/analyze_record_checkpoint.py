"""Check the bounded 48 kHz hardware recording checkpoint.

Usage: python3 tests/analyze_record_checkpoint.py EVIDENCE_DIRECTORY
Hardware WAVs live in its ignored local-input/ directory. Capture channels are
raw ADC 3/4, original player L/R, and original post-master mixer L/R. The global
plugdata output slider is downstream of these taps. No listening verdict is made.
"""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from analyze_live_record import read


def analyze(root):
    local = root / 'local-input'
    cases = {}
    for case, slot, capacity, windows in [
        ('fixed', 2, 96000, [(2.5, 3.5), (4.5, 5.5)]),
        ('early', 3, 192000, [(1.6, 2.4), (3, 4), (4.5, 5.5)]),
        ('switch', None, None, [(.3, 1.3), (1.7, 2.7), (3.1, 4.1), (4.5, 5.5), (5.8, 6.2)]),
    ]:
        capture = local / f'checkpoint-{case}-48.wav'
        events = root / f'checkpoint-{case}-48-events.txt'
        x = read(capture, 6)
        lines = [line.rstrip(';').split() for line in events.read_text().splitlines()]
        checks = {
            'bounded_capture_length': 335000 < len(x) <= 336064,
            'finite_audio': bool(np.isfinite(x).all()),
            'player_and_mixer_below_full_scale': bool(np.max(abs(x[:, 2:6])) < 1),
            'stopped_player_and_mixer': bool(np.max(abs(x[-12000:, 2:6])) < 1e-7),
            'no_recording_errors': not any(row[1] == 'l_b_record_errors' for row in lines),
        }
        result = {'checks': checks, 'capture_frames': len(x), 'windows': []}
        result['raw_adc_full_scale_events'] = [
            {'channel': channel + 3, 'sample_count': int(np.count_nonzero(abs(x[:, channel]) >= 1)),
             'first_seconds': float(np.flatnonzero(abs(x[:, channel]) >= 1)[0] / 48000)}
            for channel in range(2) if np.any(abs(x[:, channel]) >= 1)
        ]
        for start, finish in windows:
            w = x[int(start * 48000):int(finish * 48000), 2:6]
            result['windows'].append({
                'seconds': [start, finish],
                'rms_player_LR_mixer_LR': np.sqrt(np.mean(w*w, axis=0)).tolist(),
                'maximum_mixer_gain_error': float(np.max(abs(w[:, 2:] - w[:, :2] * .548 * .75))),
            })
        checks['stereo_audio_in_each_window'] = all(min(w['rms_player_LR_mixer_LR']) > 1e-4 for w in result['windows'])
        checks['configured_mixer_gain_in_each_window'] = all(w['maximum_mixer_gain_error'] < 2e-6 for w in result['windows'])
        playing = False
        bad_reports = []
        for row in lines:
            if row[1].endswith('-is_playing_flag'):
                playing = float(row[2]) != 0
            if row[1].endswith('-playbar_data_i') and not np.isfinite(float(row[2])):
                bad_reports.append({'milliseconds': float(row[0]), 'playing': playing})
        result['nonfinite_position_reports'] = bad_reports
        checks['finite_position_while_playing'] = not any(r['playing'] for r in bad_reports)
        files = [capture, events]
        if slot:
            array_path = local / f'checkpoint-live{slot}-48.wav'
            recorded = read(array_path, 2)
            metadata = [r for r in lines if r[1:3] == ['l_b_buffer_states', str(slot)] and r[-1] == '1']
            end = int(float(metadata[-1][5])) if metadata else 0
            checks['content_length'] = end == 96000 if case == 'fixed' else 59936 <= end <= 60064 and end % 64 == 0
            checks['frozen_capacity'] = len(recorded) == capacity
            checks['finite_recorded_array'] = bool(np.isfinite(recorded).all())
            checks['unwritten_tail_is_zero'] = bool(np.all(recorded[end:] == 0))
            checks['recording_and_loaded_states'] = all(any(r[1:] == ['l_b_record_states', str(slot), state] for r in lines) for state in ['Recording', 'Loaded'])
            if end:
                # One common offset for BOTH channels; never independently align
                # channels, which would conceal the stereo skew seen with pdlink.
                _, offset = min((float(np.max(abs(recorded[:3000] - x[i:i+3000, :2] * 1.1))), i) for i in range(2100, 2600))
                error = float(np.max(abs(recorded[:end] - x[offset:offset+end, :2] * 1.1)))
                result['input_to_array'] = {'shared_offset_frames': offset, 'gain': 1.1, 'maximum_error': error}
                checks['stereo_input_preserved_at_requested_gain'] = error < 2e-6
                result['recorded_peak_LR'] = np.max(abs(recorded[:end]), axis=0).tolist()
                result['recorded_rms_LR'] = np.sqrt(np.mean(recorded[:end]**2, axis=0)).tolist()
                checks['recorded_samples_below_full_scale'] = max(result['recorded_peak_LR']) < 1
            else:
                checks['stereo_input_preserved_at_requested_gain'] = False
            result.update(content_frames=end, capacity_frames=len(recorded))
            files.append(array_path)
        else:
            result['selected_buffers'] = [r[2] for r in lines if r[1].endswith('-buffer_ID')]
            checks['expected_buffer_sequence'] = result['selected_buffers'] == ['live_buffer_2', 'sample_buffer_1', 'live_buffer_3', 'sample_buffer_2', 'live_buffer_2']
        result['files_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
        result['named_checks_passed'] = all(checks.values())
        cases[case] = result
    return {
        'host_rate': 48000,
        'input_gain': 1.1,
        'track_gain': .548,
        'master_gain': .75,
        'global_output_gain_not_in_capture': .9,
        'cases': cases,
        'named_checks_passed': all(c['named_checks_passed'] for c in cases.values()),
        'scope': 'Hardware recording and steady playback checks only. Empty-buffer nonfinite position reports are an open UI defect. Raw ADC full-scale events are reported separately, including outside the take. No general transition, input-headroom, listening, 44.1 kHz or DAW acceptance.',
    }


if __name__ == '__main__':
    result = analyze(Path(sys.argv[1]))
    print(json.dumps(result, indent=2))
    raise SystemExit(not result['named_checks_passed'])
