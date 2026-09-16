"""Compare actual native buffer exports with the same captured stereo input.

Run: python3 tests/analyze_free_record.py docs/evidence/free-recording/short-48
Requires numpy and ffmpeg. This does not simulate the writer or real-time device I/O.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np


def wave_bytes(path):
    return path.read_bytes() if path.exists() else gzip.decompress(
        Path(str(path) + '.gz').read_bytes())


def read_audio(path):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-f', 'wav', '-i', 'pipe:0',
                                   '-f', 'f32le', '-'], input=wave_bytes(path))
    return np.frombuffer(raw, dtype='<f4').reshape(-1, 2)


def analyze(prefix):
    array_path = Path(str(prefix) + '-array.wav')
    source_path = Path(str(prefix) + '-source.wav')
    events = [line.rstrip(';').split() for line in
              Path(str(prefix) + '-events.txt').read_text().splitlines()]
    completed = [row for row in events if row[1] == 'buffer' and row[-1] == '1']
    if not completed:
        raise ValueError('No completed content bounds in actual buffer events')
    last = completed[-1]
    rate, first, end = float(last[2]) * 1000, int(float(last[3])), int(float(last[4]))
    array, source = read_audio(array_path), read_audio(source_path)
    # One common stereo offset, selected by exact sample identity near Start.
    # Never independently realign channels or omit transition samples.
    possible = np.flatnonzero(np.all(source[:int(rate / 2)] == array[first], axis=1))
    offsets = [int(i) for i in possible if i + end-first <= len(source)
               and np.array_equal(source[i:i+64], array[first:first+64])]
    checks = {'one_stereo_alignment': len(offsets) == 1,
              'finite': bool(np.isfinite(array).all() and np.isfinite(source).all()),
              'content_inside_capacity': 0 <= first < end <= len(array),
              'unwritten_tail_zero': bool(np.all(array[end:] == 0)),
              'writer_reports_loaded': any(r[1:] == ['state', 'Loaded'] for r in events)}
    residual = None
    if len(offsets) == 1:
        reference = source[offsets[0]:offsets[0]+end-first]
        residual = float(np.max(np.abs(array[first:end] - reference)))
        checks['all_recorded_frames_exact'] = residual == 0
    else:
        checks['all_recorded_frames_exact'] = False
    growth = [int(float(r[3])) for r in events if r[1:3] == ['storage', 'grew']]
    scenario = prefix.name.split('-')[0]
    expected_seconds, expected_growth_seconds, busy_count = {
        'short': (3.1, [2, 4], 2),
        'fixed': (2, [], 0),
        'limit': (60, [2, 4, 8, 16, 32, 60], 0),
    }[scenario]
    errors = [row[2:] for row in events if row[1] == 'error']
    checks['expected_frozen_duration'] = end-first == round(expected_seconds*rate)
    checks['expected_growth'] = growth == [round(s*rate) for s in expected_growth_seconds]
    checks['expected_errors_only'] = errors == [['Buffer_busy']] * busy_count
    return {'prefix': prefix.name, 'host_rate': rate, 'written_frames': end-first,
            'content_seconds': (end-first)/rate, 'capacity_frames': len(array),
            'growth_capacities': growth, 'stereo_offset_frames': offsets,
            'maximum_sample_residual': residual, 'checks': checks,
            'sha256': {p.name: hashlib.sha256(wave_bytes(p)).hexdigest()
                       for p in (array_path, source_path)},
            'passed': all(checks.values())}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('prefix', type=Path)
    args = parser.parse_args()
    result = analyze(args.prefix)
    print(json.dumps(result, indent=2))
    raise SystemExit(not result['passed'])
