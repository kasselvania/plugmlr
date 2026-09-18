"""Bounded read-only receiver checker. No Pd/API/process launch; native log required."""
import argparse,hashlib,json,wave
from pathlib import Path
MAX=16*1024*1024
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def num(x):return int(float(x))
def read_events(path):
 assert path.stat().st_size<=MAX,'Event log exceeds bound'
 b=path.read_bytes();lines=b.splitlines()
 if b and not b.endswith(b'\n'):lines=lines[:-1]
 events=[]
 for i,l in enumerate(lines,1):
  v=l.decode().split('\t');assert int(v[0])==i,'Noncontiguous event sequence';events.append((i,v[1],[bytes.fromhex(x).decode()for x in v[2:]]))
 return events

def cycle(root,ev,case,birth):
 def rows(k):return [e for e in ev if e[1]==k]
 attempts=rows('attempt');assert len(attempts)<=1,'Extra render attempts in cycle'
 if not attempts:return None
 callbacks=[e for e in rows('callback-return')if num(e[2][0])==1]
 loaded=[e for e in rows('loaded')if num(e[2][0])>=3]
 if not(callbacks and loaded):return None
 slot=num(callbacks[0][2][1]);assert slot==16,'Unexpected fresh destination'
 assert all(e[2][2:]==['1','1']for e in callbacks),'Receiver freed or incomplete inside callback'
 entered=[e for e in rows('callback-enter')if num(e[2][0])==1]
 assert len(entered)==len(callbacks),'Unreturned callback'
 if case=='duplicate':assert len(callbacks)==3,'Duplicate completion not exercised'
 elif len(callbacks)!=1:raise AssertionError('Unexpected duplicate completion')
 later=[e for e in rows('deferred-return')if num(e[2][0])==1]
 if case=='destroy':
  finals=[e for e in rows('finalize-enter')if num(e[2][0])==1]
  exits=[e for e in rows('finalize-return')if num(e[2][0])==1]
  if not(finals and exits):return None
  assert len(finals)==len(exits)==1 and finals[0][0]>callbacks[-1][0] and finals[0][2][1:]==['1','1'],'Wrong pending destruction order'
  assert not later and not [e for e in rows('deferred-enter')if num(e[2][0])==1],'Deferred callback survived destruction'
 else:
  if not later:return None
  assert len(later)==1 and later[0][0]>callbacks[-1][0] and later[0][2][2]=='0','Nondeferred or duplicate cleanup'
  assert later[0][2][3]==('1'if case in ('cancel','manual')else '0'),'Wrong cancellation state'
 # Independently observed track ID comes from original player committed buffer_ID.
 tracks=[e for e in rows('track')if num(e[2][0])==1]
 if not tracks:return None
 if case in ('normal','duplicate'):
  if tracks[-1][2][1]!='sample_buffer_16':return None
  assert tracks[-1][0]>callbacks[0][0],'Adoption predates load'
 else:
  assert not any(e[2][1]=='sample_buffer_16'for e in tracks),'Unexpected adoption after cancel/destroy'
  if case=='manual' and tracks[-1][2][1]!='sample_buffer_2':return None
 sources=[e for e in rows('source')if num(e[2][0])==slot and e[2][1]]
 infos=[e for e in rows('info')if num(e[2][0])==slot]
 if not(sources and infos):return None
 f=Path(sources[-1][2][1]);assert f.parent.resolve()==(root/'renders').resolve(),'Foreign output'
 if not f.exists() or not f.with_suffix('.json').exists():return None
 assert f.stat().st_mtime>=birth,'Output predates runtime'
 with wave.open(str(f),'rb')as w:
  assert(w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes())==(2,2,48000,36000),'Wrong rendered WAV'
  assert len(w.readframes(36000))==144000,'Partial WAV'
 meta=json.loads(f.with_suffix('.json').read_text())
 assert Path(meta['source']['path']).resolve()==(root/'source.wav').resolve() and meta['source']['first']==24000 and meta['source']['end']==72000,'Wrong source region'
 assert meta['tempo']['source_bpm']==90 and meta['tempo']['target_bpm']==120 and meta['pitch_semitones']==0 and meta['duration_multiplier']==.75,'Wrong render metadata'
 a=infos[-1][2];assert a[1]=='sample' and num(a[3])==1 and float(a[4])==48000 and float(a[6])-float(a[5])==36000,'Wrong native loaded bounds'
 if case!='destroy':
  tempos=[e for e in rows('tempo')if num(e[2][0])==slot]
  if not tempos:return None
  assert float(tempos[-1][2][1])==120 and tempos[-1][2][2]=='rendered','Wrong native tempo'
 return {'destination':slot,'file':str(f),'sha256':digest(f),'case':case}

def inspect(root,not_before=None):
 r=dict(status='PENDING',candidate_commit='',attempted=0,completed=0,expected=0,destinations=[],checks={},evidence={'fixture':str(root),'events':str(root/'events.tsv')})
 try:
  m=json.loads((root/'receipt.json').read_text());r.update(candidate_commit=m['candidate_commit'],expected=m['expected'])
  for n,h in m['input_hashes'].items():assert digest(root/n)==h,'Changed input: '+n
  assert digest(root/'source.wav')==m['source_sha256'],'Source mutated'
  p=root/'events.tsv'
  if not p.exists():return r
  if not_before is not None:assert p.stat().st_birthtime>=not_before,'Events predate launched process'
  ev=read_events(p);assert sum(k=='boot'for _,k,a in ev)==1,'Multiple/stale runtime starts'
  assert not any(k=='failure'for _,k,a in ev),'Native driver reported failure'
  r['attempted']=sum(k=='attempt'for _,k,a in ev);assert r['attempted']<=r['expected'],'Extra attempts'
  mode=m.get('mode','ui');results=[]
  if mode=='ui':
   one=cycle(root,ev,'normal',p.stat().st_birthtime)
   if one:results.append(one)
  else:
   starts=[e for e in ev if e[1]=='cycle'];ends=[e for e in ev if e[1]=='cycle-end']
   assert len(starts)<=r['expected'],'Excess fresh sessions'
   for ix,start in enumerate(starts,1):
    assert num(start[2][0])==ix,'Skipped cycle'
    matches=[e for e in ends if num(e[2][0])==ix];assert len(matches)<=1,'Duplicate cycle end'
    if not matches:break
    end=matches[0];case=start[2][1];want='normal'if mode=='campaign'else ['normal','duplicate','cancel','manual','destroy'][ix-1]
    assert case==want and end[2][1]==case,'Wrong lifecycle case'
    segment=[e for e in ev if start[0]<e[0]<end[0]]
    one=cycle(root,segment,case,p.stat().st_birthtime)
    assert one is not None,'Driver ended cycle without independent completed load/lifetime evidence'
    results.append(one)
   if len(results)==r['expected']:
    if not any(k=='campaign-done' and num(a[0])==r['expected']for _,k,a in ev):return r
  paths=[x['file']for x in results];assert len(paths)==len(set(paths)),'Reused output/no-op load'
  r['completed']=len(results);r['destinations']=[x['destination']for x in results];assert r['completed']<=r['attempted'],'Load without render'
  r['evidence']['outputs']=results;r['checks']={'source_and_fixture_unchanged':True,'actual_native_load':bool(results),'lifetime_order':bool(results),'expected_adoption_or_suppression':bool(results),'unique_render_per_completion':True}
  if r['completed']==r['expected']:r['status']='PASS'
 except Exception as e:r['status']='FAIL';r['reason']=str(e)
 return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fixture',type=Path,required=True);p.add_argument('--not-before',type=float);a=p.parse_args();r=inspect(a.fixture.resolve(),a.not_before);print(json.dumps(r));raise SystemExit(1 if r['status']=='FAIL'else 0)
