"""Inspect actual bounded-player-capture output; not a playback model.

python tests/analyze_speed_capture.py DrumLoop.wav CAPTURE.wav [--cuts]
Requires NumPy and ffmpeg/ffprobe. --retain PREFIX saves lossless float samples
as PREFIX.npz and stereo listening audio as PREFIX.flac. NPZ can be reanalyzed.
Timing windows correspond to speed-sequence.pd or cut-sequence.pd.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np


def read(path):
    if path.suffix == '.npz':
        with np.load(path, allow_pickle=False) as z:
            return z['samples'], int(z['sample_rate'])
    meta = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries', 'stream=sample_rate,channels',
        '-of', 'json', str(path)]))['streams'][0]
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path),
                                   '-f', 'f32le', '-'])
    return np.frombuffer(raw, '<f4').reshape(-1, meta['channels']), int(meta['sample_rate'])


def longest_run(mask):
    edges = np.flatnonzero(np.diff(np.r_[False, mask, False]))
    if not len(edges):
        return 0, 0
    runs = edges.reshape(-1, 2)
    start, end = runs[np.argmax(runs[:, 1] - runs[:, 0])]
    return int(start), int(end - start)


def analyze(source, sr, x, host, cuts):
    if x.shape[1] not in (4, 8) or source.shape[1] != 2:
        raise ValueError('Expected stereo source and 4/8-channel native capture')
    result = {'sample_rate': host, 'channels': x.shape[1], 'frames': len(x),
              'duration_s': len(x) / host,
              'nonfinite_samples': int((~np.isfinite(x)).sum())}
    if result['nonfinite_samples']:
        return result
    x = x.astype(float)
    result['audio_peak'] = np.abs(x[:, :2]).max(axis=0).tolist()
    active = [(0.1, 7)] if cuts else [(0.1, 20), (22.1, 23)]
    result['constant_position_runs'] = []
    for lo, hi in active:
        a, b = round(lo * host), min(len(x), round(hi * host))
        start, count = longest_run(np.diff(x[a:b, 2]) == 0)
        result['constant_position_runs'].append({
            'interval_s': [lo, hi], 'start_s': (a + start) / host,
            'duration_s': count / host})
    times = [.5, 2.5, 4.5, 6.5, 7.3] if cuts else [
        .5, 2.5, 4.5, 6.5, 10.5, 12.5, 15.2, 16.5, 18.5, 20.5, 21.5, 22.3, 23.3]
    result['windows'] = []
    source_frames = np.arange(len(source))
    for start in times:
        a, b = round(start * host), round((start + .2) * host)
        w = x[a:b]
        if not len(w):
            continue
        delta = np.diff(w[:, 2])
        moving = (np.abs(delta) > 1e-6) & (np.abs(delta) < 16)
        row = {'start_s': start, 'rate_control_median': float(np.median(w[:, 3])),
               'moving_rate_mean': float(delta[moving].mean() * host / sr) if moving.any() else 0.,
               'position_hold_fraction': float(np.mean(delta == 0)),
               'audio_rms': np.sqrt(np.mean(w[:, :2] ** 2, axis=0)).tolist(),
               'audio_step_max': np.abs(np.diff(w[:, :2], axis=0)).max(axis=0).tolist()}
        # Lag search accounts for Pd block ordering. Match original channel-swapped
        # playback path. Linear interpolation is a reference, not a tabread4 oracle.
        if np.std(w[:, 0]) > 1e-6:
            best = None
            for lag in range(-128, 129):
                pos = x[a + lag:b + lag, 2]
                pred = np.interp(pos, source_frames, source[:, 1])
                if np.std(pred) < 1e-9:
                    continue
                corr = float(np.corrcoef(pred, w[:, 0])[0, 1])
                if best is None or corr > best[0]:
                    best = corr, lag, pred
            if best:
                corr, lag, pred = best
                right = np.interp(x[a + lag:b + lag, 2], source_frames, source[:, 0])
                row['source_match'] = {
                    'channel_mapping': ['source_right', 'source_left'],
                    'correlation': [corr, float(np.corrcoef(right, w[:, 1])[0, 1])],
                    'lag_samples': lag,
                    'gain': [float(np.dot(pred, w[:, 0]) / np.dot(pred, pred)),
                             float(np.dot(right, w[:, 1]) / np.dot(right, right))]}
        result['windows'].append(row)
    if not cuts:
        result['slew_control_medians'] = {
            str(t): float(np.median(x[round(t*host):round((t+.02)*host), 3]))
            for t in (14.1, 14.2, 14.3, 14.9)}
    if x.shape[1] == 8:
        d0, d1 = np.diff(x[:, 4]), np.diff(x[:, 6])
        # The large same-frame jumps at nonzero gains expose common trajectory
        # retargeting. Raw s~ taps repeat their last block while switch~ is off;
        # do not sum these gains across disabled readers as an audio level test.
        indices = np.flatnonzero((np.abs(d0) > 1000) & (np.abs(d1) > 1000)
                                 & (np.abs(d0-d1) < 1) & (x[1:, 5] > .05)
                                 & (x[1:, 7] > .05))
        result['simultaneous_reader_jumps'] = [
            {'time_s': (int(n)+1)/host, 'frame_delta': [d0[n], d1[n]],
             'gain_taps': x[n+1, [5, 7]].tolist(),
             'audio_step': np.abs(x[n+1, :2]-x[n, :2]).tolist()}
            for n in indices]
        result['gain_tap_limit'] = 'Disabled switch~ readers repeat their final s~ block; raw gain sum is not output gain.'
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('capture', type=Path)
    p.add_argument('--cuts', action='store_true')
    p.add_argument('--retain', type=Path)
    args = p.parse_args()
    source, sr = read(args.source)
    x, host = read(args.capture)
    result = analyze(source, sr, x, host, args.cuts)
    result.update(source_sample_rate=sr, source_sha256=hashlib.sha256(args.source.read_bytes()).hexdigest(),
                  input_sha256=hashlib.sha256(args.capture.read_bytes()).hexdigest(),
                  sequence='cut-sequence.pd' if args.cuts else 'speed-sequence.pd')
    if args.retain:
        args.retain.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(args.retain.with_suffix('.npz'), samples=x, sample_rate=host)
        subprocess.run(['ffmpeg', '-v', 'error', '-n', '-f', 'f32le', '-ar', str(host),
                        '-ac', '2', '-i', '-', '-c:a', 'flac', '-sample_fmt', 's32',
                        str(args.retain.with_suffix('.flac'))],
                       input=x[:, :2].astype('<f4').tobytes(), check=True)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
