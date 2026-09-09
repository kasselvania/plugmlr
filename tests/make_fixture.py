"""Deterministic stereo PCM16 test files; Python standard library only."""
import math, struct, wave
from pathlib import Path
ROOT = Path(__file__).resolve().parent
for sr in (44100, 48000):
    with wave.open(str(ROOT / f'stereo-{sr}.wav'), 'wb') as f:
        f.setparams((2, 2, sr, 0, 'NONE', 'not compressed'))
        f.writeframes(b''.join(struct.pack('<hh', round(8192*math.sin(2*math.pi*220*i/sr)),
            round(4096*math.sin(2*math.pi*330*i/sr))) for i in range(sr*2)))
with wave.open(str(ROOT/'mono.wav'), 'wb') as f:
    f.setparams((1, 2, 48000, 0, 'NONE', 'not compressed')); f.writeframes(b'\0\0'*4800)
with wave.open(str(ROOT/'empty.wav'), 'wb') as f:
    f.setparams((2, 2, 48000, 0, 'NONE', 'not compressed')); f.writeframes(b'')
# A longer periodic file exposes loss of fractional increments at large indices.
with wave.open(str(ROOT/'precision-44100.wav'), 'wb') as f:
    f.setparams((2, 2, 44100, 0, 'NONE', 'not compressed'))
    period=b''.join(struct.pack('<hh', round(8192*math.sin(2*math.pi*220*i/44100)),
        round(4096*math.sin(2*math.pi*330*i/44100))) for i in range(44100))
    f.writeframes(period*12)
