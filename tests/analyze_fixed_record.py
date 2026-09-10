"""Check actual native array exports from fixed-record-check.pd (no model)."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np


def analyze(path, frames):
    raw = subprocess.check_output([
        'ffmpeg', '-v', 'error', '-i', str(path), '-f', 'f32le', '-'])
    audio = np.frombuffer(raw, dtype='<f4').reshape(-1, 2)
    checks = {
        'exported_frames': len(audio) == 4864,
        'finite': bool(np.isfinite(audio).all()),
        'written_range': bool(np.all(audio[:frames] == [0.125, 0.25])),
        'unwritten_range': bool(np.all(audio[frames:] == -0.5)),
    }
    return {
        'file': path.name,
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'console_reported_frames': frames,
        'checks': checks,
        'passed': all(checks.values()),
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('wav', type=Path)
    parser.add_argument('--frames', type=int, required=True)
    args = parser.parse_args()
    result = analyze(args.wav, args.frames)
    print(json.dumps(result, indent=2))
    raise SystemExit(not result['passed'])
