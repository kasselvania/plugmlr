"""Source-file crop and validation checks; native rendering is a separate test."""
from pathlib import Path
import importlib.util, struct, tempfile, unittest, wave
spec=importlib.util.spec_from_file_location('worker',Path(__file__).resolve().parents[1]/'scripts/render_sample.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Crop(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.p=Path(self.temp.name)
  self.source=self.p/"audio ' $literal.wav"
  with wave.open(str(self.source),'wb') as w:
   w.setnchannels(2);w.setsampwidth(2);w.setframerate(44100)
   w.writeframes(b''.join(struct.pack('<hh',i,-i) for i in range(100)))
 def tearDown(self):self.temp.cleanup()
 def test_exact_stereo_exclusive_bounds(self):
  before=self.source.read_bytes();m.wav_region(self.source,self.p/'out.wav',20,50,44100)
  with wave.open(str(self.p/'out.wav')) as w:
   self.assertEqual(w.getnframes(),30);self.assertEqual(w.readframes(30),before[44+20*4:44+50*4])
  self.assertEqual(self.source.read_bytes(),before)
 def test_invalid_bounds_rate_and_missing_file(self):
  for first,end,rate in [(-1,20,44100),(20,21,44100),(0,101,44100),(0,100,48000),(50,20,44100)]:
   with self.assertRaises(ValueError):m.wav_region(self.source,self.p/'out.wav',first,end,rate)
  with self.assertRaises(FileNotFoundError):m.wav_region(self.p/'missing',self.p/'out.wav',0,100,44100)
 def test_float_wav(self):
  fmt=struct.pack('<HHIIHH',3,2,48000,384000,8,32);data=struct.pack('<8f',.1,.2,.3,.4,.5,.6,.7,.8)
  self.source.write_bytes(b'RIFF'+struct.pack('<I',36+len(data))+b'WAVEfmt '+struct.pack('<I',16)+fmt+b'data'+struct.pack('<I',len(data))+data)
  m.wav_region(self.source,self.p/'out.wav',0,4,48000)
  self.assertEqual((self.p/'out.wav').read_bytes(),self.source.read_bytes())
 def test_invalid_render_parameters(self):
  for ratio,pitch in [(0,0),(5,0),(1,float('nan')),(1,25)]:
   with self.assertRaises(ValueError):m.render(self.p/'job',self.source,0,100,44100,ratio,pitch,self.p/'renders')
 def test_never_overwrites_crop(self):
  p=self.p/'out.wav';p.write_bytes(b'keep')
  with self.assertRaises(FileExistsError):m.wav_region(self.source,p,0,100,44100)
  self.assertEqual(p.read_bytes(),b'keep')
if __name__=='__main__':unittest.main()
