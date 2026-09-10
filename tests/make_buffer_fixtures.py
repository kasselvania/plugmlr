"""Reproducible quiet stereo fixtures; no input devices or audio runtime needed."""
from pathlib import Path
import math
import struct
import wave

ROOT = Path(__file__).parent / 'fixtures'
ROOT.mkdir(exist_ok=True)
for name, rate, seconds, left, right in [
    ('buffer-a', 48000, 1, 220, 440),
    ('buffer-b', 44100, .75, 330, 660),
    ('buffer-live-48', 48000, .8, 550, 770),
    ('buffer-live-44', 44100, .8, 550, 770),
]:
    with wave.open(str(ROOT / (name + '.wav')), 'wb') as out:
        out.setparams((2, 2, rate, 0, 'NONE', 'not compressed'))
        out.writeframes(b''.join(struct.pack('<hh',
            round(3500 * math.sin(2 * math.pi * left * i / rate)),
            round(2500 * math.sin(2 * math.pi * right * i / rate)))
            for i in range(round(rate * seconds))))
