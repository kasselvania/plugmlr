"""Generate the deterministic two-second stereo source used by tempo-fit tests."""
import argparse,math,struct,wave
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--rate',type=int,choices=[44100,48000],default=44100)
rate=parser.parse_args().rate
p=Path(__file__).parent/f'fixtures/tempo-stereo-{rate//100}.wav'
with wave.open(str(p),'wb') as w:
    w.setparams((2,2,rate,0,'NONE','not compressed'))
    w.writeframes(b''.join(struct.pack('<hh',round(32767*.12*math.sin(2*math.pi*375*n/rate)),round(32767*.06*math.sin(2*math.pi*600*n/rate))) for n in range(rate*2)))
print(p)
