"""Generate the deterministic two-second stereo source used by tempo-fit tests."""
import math,struct,wave
from pathlib import Path
p=Path(__file__).parent/'fixtures/tempo-stereo-441.wav'
with wave.open(str(p),'wb') as w:
    w.setparams((2,2,44100,0,'NONE','not compressed'))
    w.writeframes(b''.join(struct.pack('<hh',round(32767*.12*math.sin(2*math.pi*375*n/44100)),round(32767*.06*math.sin(2*math.pi*600*n/44100))) for n in range(88200)))
print(p)
