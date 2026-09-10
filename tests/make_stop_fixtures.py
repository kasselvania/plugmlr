"""Reproduce the short stereo Stop fixtures. Keep the DC fixture off speakers."""
from pathlib import Path
import wave
import numpy as np

target = Path(__file__).parent / 'fixtures'
t = np.arange(12000) / 48000
signals = {
    'constant': np.tile([.08, -.04], (len(t), 1)),
    'wave': np.column_stack([
        .06 * np.sin(2*np.pi*360*t) + .02 * np.sin(2*np.pi*124*t),
        .04 * np.sin(2*np.pi*508*t) + .01 * np.cos(2*np.pi*92*t),
    ]),
}
for name, samples in signals.items():
    with wave.open(str(target / f'stop-{name}-48.wav'), 'wb') as output:
        output.setparams((2, 2, 48000, len(t), 'NONE', 'not compressed'))
        output.writeframes(np.round(samples * 32767).astype('<i2').tobytes())
