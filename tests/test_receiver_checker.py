import tempfile,unittest,json,wave
from pathlib import Path
from check_receiver_lifetime import inspect,digest,cycle,read_events
class Checks(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.p=Path(self.t.name);(self.p/'source.wav').write_bytes(b'source');(self.p/'receipt.json').write_text(json.dumps({'candidate_commit':'test','expected':1,'input_hashes':{},'source_sha256':digest(self.p/'source.wav')}));self.events=[]
 def tearDown(self):self.t.cleanup()
 def event(self,k,*a):
  self.events.append(str(len(self.events)+1)+'\t'+k+''.join('\t'+str(v).encode().hex()for v in a));(self.p/'events.tsv').write_text('\n'.join(self.events)+'\n')
 def complete(self):
  self.event('boot');self.event('attempt',1,'job');self.event('callback-enter',1,16);self.event('callback-return',1,16,1,1);self.event('loaded',16);self.event('deferred-enter',1,16);self.event('deferred-return',1,16,0,0)
  (self.p/'renders').mkdir();f=self.p/'renders/out.wav'
  with wave.open(str(f),'wb')as w:w.setparams((2,2,48000,0,'NONE','not compressed'));w.writeframes(b'\x00'*144000)
  f.with_suffix('.json').write_text(json.dumps({'source':{'path':str(self.p/'source.wav'),'first':24000,'end':72000},'tempo':{'source_bpm':90,'target_bpm':120},'duration_multiplier':.75,'pitch_semitones':0}))
  self.event('source',16,f);self.event('info',16,'sample',16,1,48000,0,36000,'out.wav','Loaded');self.event('tempo',16,120,'rendered')
 def test_empty(self):self.assertEqual(inspect(self.p)['status'],'PENDING')
 def test_render_without_adoption(self):self.complete();self.assertEqual(inspect(self.p)['status'],'PENDING')
 def test_complete(self):self.complete();self.event('track',1,'sample_buffer_16');r=inspect(self.p);self.assertEqual(r['status'],'PASS',r);self.assertTrue(all(type(v)is bool and v for v in r['checks'].values()))
 def test_stale_boot(self):self.complete();self.event('track',1,'sample_buffer_16');self.event('boot');self.assertEqual(inspect(self.p)['status'],'FAIL')
 def test_old_process(self):self.complete();self.event('track',1,'sample_buffer_16');self.assertEqual(inspect(self.p,(self.p/'events.tsv').stat().st_birthtime+1)['status'],'FAIL')
 def test_source_changed(self):self.complete();(self.p/'source.wav').write_bytes(b'changed');self.assertEqual(inspect(self.p)['status'],'FAIL')
 def test_callback_freed(self):self.complete();self.events=[x.rsplit('\t',2)[0]+'\t30\t31' if '\tcallback-return\t'in x else x for x in self.events];(self.p/'events.tsv').write_text('\n'.join(self.events)+'\n');self.assertEqual(inspect(self.p)['status'],'FAIL')
 def test_cancel_suppresses_adoption(self):
  self.complete();self.event('track',1,'sample_buffer_1');ev=read_events(self.p/'events.tsv')
  ev=[(i,k,[*a[:3],'1'] if k=='deferred-return'else a)for i,k,a in ev]
  self.assertIsNotNone(cycle(self.p,ev,'cancel',0))
  ev.append((100,'track',['1','sample_buffer_16']))
  with self.assertRaisesRegex(AssertionError,'Unexpected adoption'):cycle(self.p,ev,'cancel',0)
 def test_destroy_no_deferred_callback(self):
  self.complete();self.event('track',1,'sample_buffer_1');ev=[e for e in read_events(self.p/'events.tsv')if not e[1].startswith('deferred-')]
  ev += [(100,'finalize-enter',['1','1','1']),(101,'finalize-return',['1'])]
  self.assertIsNotNone(cycle(self.p,ev,'destroy',0))
  ev.append((102,'deferred-enter',['1','16']))
  with self.assertRaisesRegex(AssertionError,'survived destruction'):cycle(self.p,ev,'destroy',0)
 def test_campaign_requires_cycle_receipts(self):
  self.complete();self.event('track',1,'sample_buffer_16');m=json.loads((self.p/'receipt.json').read_text());m.update(mode='campaign',expected=300);(self.p/'receipt.json').write_text(json.dumps(m));r=inspect(self.p);self.assertEqual(r['completed'],0);self.assertEqual(r['status'],'PENDING')
 def test_native_failure(self):
  self.event('boot');self.event('failure',1,'deadline');self.assertEqual(inspect(self.p)['status'],'FAIL')
if __name__=='__main__':unittest.main()
