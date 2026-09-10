"""Summarize actual plugdata output captures; requires Python + NumPy.

Usage: python analyze_handoff.py DrumLoop.wav capture.wav [capture.wav ...]
Outputs JSON. Quiet regions are measurements, not automatic dropout verdicts:
compare the source's own silence and the recorded control sequence.
PCM export cannot establish whether an internal DSP signal was ever non-finite.
"""

import json
import sys
import wave
from pathlib import Path

import numpy as np


def read_pcm(path):
    with wave.open(str(path)) as wav:
        rate = wav.getframerate()
        channels = wav.getnchannels()
        width = wav.getsampwidth()
        raw = wav.readframes(wav.getnframes())
    if width == 3:
        b = np.frombuffer(raw, np.uint8).reshape(-1, 3)
        v = (b[:, 0].astype(np.int32)
             | (b[:, 1].astype(np.int32) << 8)
             | (b[:, 2].astype(np.int32) << 16))
        x = ((v ^ 0x800000) - 0x800000) / 8388608.0
    elif width in (2, 4):
        x = np.frombuffer(raw, '<i' + str(width)).astype(float)
        x /= float(2 ** (8 * width - 1))
    else:
        raise ValueError(f'Unsupported PCM width: {width}')
    return x.reshape(-1, channels), rate, width


def describe(path):
    x, rate, width = read_pcm(path)
    size = rate // 10
    count = len(x) // size
    bins = x[:count * size].reshape(count, size, x.shape[1])
    rms = np.sqrt(np.mean(bins * bins, axis=(1, 2)))
    quiet = rms < 1e-6
    edges = np.flatnonzero(np.diff(np.r_[False, quiet, False]))
    regions = [[round(a * size / rate, 4), round(b * size / rate, 4)]
               for a, b in edges.reshape(-1, 2) if b - a >= 4]
    step = np.abs(np.diff(x, axis=0))
    return {
        'file': str(path), 'frames': len(x), 'rate_hz': rate,
        'channels': x.shape[1], 'pcm_bits': width * 8,
        'duration_s': len(x) / rate,
        'peak_by_channel': np.max(np.abs(x), axis=0).tolist(),
        'rms_by_channel': np.sqrt(np.mean(x * x, axis=0)).tolist(),
        'mean_by_channel': np.mean(x, axis=0).tolist(),
        'full_scale_samples': int(np.sum(np.abs(x) >= 1 - 2 ** (1 - 8 * width))),
        'largest_adjacent_step_by_channel': np.max(step, axis=0).tolist(),
        'adjacent_step_p9999_by_channel': np.quantile(step, .9999, axis=0).tolist(),
        'quiet_regions_at_least_0_4s': regions,
        'rms_0_1s_bins': rms.tolist(),
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    print(json.dumps([describe(Path(p)) for p in sys.argv[1:]], indent=2))
