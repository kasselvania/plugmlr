"""Check retained audio from build_record_session_check.py in native plugdata.

python3 tests/analyze_record_session.py docs/evidence/recording-continuity/run
Requires numpy. Reads raw WAV or its lossless .gz archive. No DSP simulation.
The boundary scenario must fail until the separately recorded playback defect is fixed.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct

import numpy as np


def audio(path):
    raw = path.read_bytes() if path.exists() else gzip.decompress(
        Path(str(path) + '.gz').read_bytes())
    assert raw[:4] == b'RIFF' and raw[8:12] == b'WAVE'
    offset = 12
    while offset + 8 <= len(raw):
        tag, size = struct.unpack_from('<4sI', raw, offset)
        start = offset + 8
        payload = raw[start:start + size]
        offset = start + size + size % 2
        if tag == b'fmt ':
            fmt, channels, rate, _, alignment, bits = struct.unpack_from(
                '<HHIIHH', payload)
            assert bits == 32 and alignment == 4 * channels
            assert fmt == 3 or (fmt == 65534 and payload[24:28] == b'\x03\0\0\0')
        elif tag == b'data':
            data = np.frombuffer(payload, '<f4').reshape(-1, channels)
            # Native writesf~ 10 headers under-report a few final frames here.
            # Preserve originals; analyze the declared audio, report trailing bytes.
            return data, {'rate': rate, 'channels': channels,
                          'declared_frames': len(data),
                          'trailing_bytes': len(raw) - (start + size),
                          'sha256': hashlib.sha256(raw).hexdigest()}
    raise ValueError(f'No audio data: {path}')


def longest_zero_run(data):
    zero = np.all(data == 0, axis=1)
    edges = np.diff(np.r_[False, zero, False].astype(int))
    starts, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    return int(max(ends - starts, default=0))


def analyze(prefix):
    scenario = 'boundary' if prefix.name.startswith('boundary') else prefix.name
    capture, capture_info = audio(Path(str(prefix) + '-capture.wav'))
    rate = capture_info['rate']
    assert capture_info['channels'] == 10 and rate == 48000
    rows = [line.rstrip(';').split() for line in
            Path(str(prefix) + '-events.txt').read_text().splitlines()]
    specs = {'run': [(1, 1.3, 3.1, 4), (2, 1.8, 2.8, 4)],
             'boundary': [(1, 1.3, 3.1, 4), (2, 1.8, 2.8, 4)],
             'dsp': [(1, 1.3, 1.2, 2)],
             'zero': [(1, 1.32, 1.1, 2)]}[scenario]
    checks = {'finite_capture': bool(np.isfinite(capture).all()),
              'capture_bounded': 13.49 < len(capture) / rate <= 14.0}
    buffers = {}
    for number, start_seconds, duration, capacity in specs:
        arr, info = audio(Path(str(prefix) + f'-live{number}.wav'))
        completed = [r for r in rows if r[1:3] == ['buffer', str(number)]
                     and r[-1] == '1' and float(r[0]) >= start_seconds * 1000]
        assert completed, f'Missing completed buffer {number}'
        last = completed[-1]
        first, end = int(float(last[4])), int(float(last[5]))
        low, high = round(start_seconds * rate) - 128, round(start_seconds * rate) + 129
        offsets = [i for i in range(low, high)
                   if np.array_equal(capture[i:i+64, :2], arr[first:first+64])]
        residual = None
        if len(offsets) == 1:
            reference = capture[offsets[0]:offsets[0] + end-first, :2]
            residual = float(np.max(np.abs(arr[first:end] - reference)))
        active = [r for r in rows if r[1:3] == ['progress', str(number)] and r[-1] == '1']
        expected_limit = 60 if number == 1 else 4
        checks.update({
            f'buffer{number}_finite': bool(np.isfinite(arr).all()),
            f'buffer{number}_written_bounds': first == 0 and end == round(duration * rate),
            f'buffer{number}_capacity': len(arr) == round(capacity * rate),
            f'buffer{number}_one_stereo_alignment': len(offsets) == 1,
            f'buffer{number}_all_recorded_samples_exact': residual == 0,
            f'buffer{number}_unused_tail_zero': bool(np.all(arr[end:] == 0)),
            f'buffer{number}_frozen_limit_visible': bool(active) and
                all(float(r[4]) == expected_limit for r in active),
            f'buffer{number}_finish_visible': any(r[1:] ==
                ['progress', str(number), '0', '0', '0'] for r in rows),
        })
        buffers[number] = {'written_frames': end-first, 'capacity_frames': len(arr),
                           'common_stereo_offsets': offsets,
                           'maximum_sample_residual': residual, **info}
    errors = [r[2:] for r in rows if r[1] == 'error']
    checks['expected_errors_only'] = errors == ([['1', 'Buffer_busy']] if scenario == 'zero' else [])
    if scenario in ('run', 'boundary'):
        growth = [int(float(r[4])) for r in rows if r[1:4] == ['storage', '1', 'grew']]
        checks['free_growth_2_then_4_seconds'] = growth == [96000, 192000]
        checks['other_take_still_active_after_finish1'] = any(
            4403 < float(r[0]) < 4600 and r[1:3] == ['progress', '2'] and r[-1] == '1'
            for r in rows)
    if scenario == 'dsp':
        checks['dsp_off_finishes_without_restart'] = (
            [r for r in rows if r[1:] == ['record', '1', 'Recording']] ==
            [['1300', 'record', '1', 'Recording']] and
            any(r == ['2503', 'record', '1', 'Loaded'] for r in rows) and
            any(r == ['3200', 'record', '1', 'Loaded'] for r in rows))
    if scenario == 'zero':
        checks['zero_frame_take_stays_empty'] = ['1303', 'record', '1', 'Empty'] in rows
        checks['later_start_succeeds'] = ['1320', 'record', '1', 'Recording'] in rows

    playback = {}
    metrics = {}
    if scenario in ('run', 'boundary'):
        b_reference = capture[rate:2*rate, 4:6]
        residuals = [float(np.max(np.abs(capture[s*rate:(s+1)*rate, 4:6] - b_reference)))
                     for s in range(2, 12)]
        playback['other_lane_exact_repeats_during_and_after_growth'] = max(residuals) == 0
        expected_mix = np.float32(.75) * (np.float32(.4) * capture[:, 2:4] +
                                         np.float32(.3) * capture[:, 4:6])
        residual = np.max(np.abs(capture[:, 6:8] - expected_mix), axis=1)
        # The production mixers intentionally ramp open over 5 ms at each Play.
        # Report those samples too; only the unity-envelope equality check uses this mask.
        time = np.arange(len(capture)) / rate
        opening = ((time >= .1) & (time < .107)) | ((time >= 4.9) & (time < 4.907))
        playback['mixer_gain_outside_intentional_open'] = bool(np.max(residual[~opening]) < 1e-6)
        playback['mixer_open_bounded_difference'] = bool(np.max(residual) < .001)
        playback['players_and_mix_silent_after_stop'] = bool(np.all(capture[round(12.52*rate):, 2:8] == 0))
        moving = capture[round(4.92*rate):round(12.49*rate)]
        playback['reader_stays_inside_written_content'] = bool(
            moving[:, 8].min() >= 0 and moving[:, 8].max() <= 148800)
        zero_run = longest_zero_run(moving[:, 2:4])
        playback['no_long_exact_silent_dropout'] = zero_run <= 64
        motions = [(5, 7.9, 1), (8.34, 8.9, -1), (9.04, 9.9, -.5), (10.04, 12.4, -2)]
        for lo, hi, speed in motions:
            step = np.diff(capture[round(lo*rate):round(hi*rate), 8])
            # Natural loop wraps are reported separately by bounds; not per-frame rates.
            step = step[np.abs(step) < 10]
            median = float(np.median(step))
            playback[f'actual_motion_{lo}s'] = abs(median-speed) < .02
            metrics[f'median_frame_step_{lo}s'] = median
        metrics.update({'other_lane_max_repeat_residual': max(residuals),
                        'mixer_max_residual_all_samples': float(np.max(residual)),
                        'mixer_max_residual_outside_open': float(np.max(residual[~opening])),
                        'longest_exact_zero_run_playing_frames': zero_run,
                        'post_mixer_peak': float(np.max(np.abs(capture[:, 6:8]))),
                        'post_mixer_max_adjacent_step': float(np.max(np.abs(np.diff(capture[:, 6:8], axis=0))))})
    return {'scenario': prefix.name, 'capture': capture_info, 'buffers': buffers,
            'recorder_checks': checks, 'playback_checks': playback,
            'metrics': metrics, 'recorder_passed': all(checks.values()),
            'passed': all(checks.values()) and all(playback.values()),
            'listening': 'Not collected. Adjacent-step metrics are not a click-free claim.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('prefix', type=Path)
    args = parser.parse_args()
    result = analyze(args.prefix)
    print(json.dumps(result, indent=2))
    raise SystemExit(not result['passed'])
