"""Compare a native four-channel capture: direct L/R, received L/R.

Per-channel fidelity and stereo alignment are separate assertions. A link that
preserves every sample but delays one channel more than the other fails stereo.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np


def analyze(path, rate):
    raw = subprocess.check_output([
        'ffmpeg', '-v', 'error', '-i', str(path), '-f', 'f32le', '-'])
    audio = np.frombuffer(raw, dtype='<f4').reshape(-1, 4)
    windows = []
    for second in (1, 2, 3, 4):
        for channel in (0, 1):
            start, count = second * rate, rate // 2
            x = audio[start:start + count, channel]
            y = audio[start:start + count, channel + 2]
            size = 1 << (2 * count - 1).bit_length()
            correlation = np.fft.irfft(
                np.fft.rfft(y, size) * np.conj(np.fft.rfft(x, size)), size)
            lag = int(np.argmax(correlation[:8192]))
            y = audio[start + lag:start + lag + count, channel + 2]
            windows.append({
                'second': second, 'channel': channel, 'lag_frames': lag,
                'raw_rms': float(np.sqrt(np.mean(x * x))),
                'gain': float(x @ y / (x @ x)) if x @ x else None,
                'maximum_sample_error': float(np.max(np.abs(y - x))),
            })
    lags = [w['lag_frames'] for w in windows]
    checks = {
        'finite': bool(np.isfinite(audio).all()),
        'signal_present_in_each_window': all(w['raw_rms'] > 1e-5 for w in windows),
        'window_samples_match_after_independent_alignment': all(
            w['maximum_sample_error'] == 0 for w in windows),
        'one_shared_stereo_delay': len(set(lags)) == 1,
    }
    return {
        'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'host_rate': rate, 'captured_frames': len(audio), 'windows': windows,
        'checks': checks, 'passed': all(checks.values()),
        'scope': 'Measured windows only; no listening or DAW lifecycle claim.',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('wav', type=Path)
    parser.add_argument('--rate', type=int, required=True)
    args = parser.parse_args()
    result = analyze(args.wav, args.rate)
    print(json.dumps(result, indent=2))
    raise SystemExit(not result['passed'])
