"""Build isolated full-MLR UI receiver regression; never launches Pd or a worker."""
from pathlib import Path
import argparse,hashlib,json,math,struct,subprocess,wave
from check_patch_connections import check
ROOT=Path(__file__).resolve().parents[1]
CANDIDATE='c56ee2174f17fee6188a68f8af74116465d17bdd'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def append(s,objects,edges):
 depth=count=0
 for l in s.splitlines():
  if l.startswith('#N canvas'):depth+=1
  elif l.startswith('#X restore'):
   depth-=1
   if depth==1:count+=1
  elif depth==1 and l.startswith(('#X obj ','#X msg ','#X text ','#X floatatom ','#X symbolatom ','#X listbox ')):count+=1
 return s+'\n'+'\n'.join('#X '+o+';' for o in objects)+'\n'+'\n'.join(f'#X connect {count+a} {ao} {count+b} {bi};' for a,ao,b,bi in edges)+'\n'
def build(out,mode="ui",monome=None):
 monome=Path(monome or ROOT.parent/'plugmlr/dependencies/monome').resolve()
 dep_commit='18b489399d01a9178e4667b849ec4368d72533db'
 subprocess.run(['git','cat-file','-e',dep_commit+'^{commit}'],cwd=monome,check=True)
 out=out.resolve();out.mkdir(parents=True,exist_ok=False)
 originals={}
 for f in ROOT.iterdir():
  if f.suffix in ('.pd','.pd_lua','.lua'):
   data=subprocess.check_output(['git','show',f'{CANDIDATE}:{f.name}'],cwd=ROOT)
   (out/f.name).write_bytes(data);originals[f.name]=hashlib.sha256(data).hexdigest()
 for name in subprocess.check_output(['git','ls-tree','-r','--name-only',dep_commit],cwd=monome,text=True).splitlines():
  target=out/'dependencies/monome'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(subprocess.check_output(['git','show',dep_commit+':'+name],cwd=monome))
 (out/'scripts').mkdir();(out/'scripts/render_sample.py').write_bytes(subprocess.check_output(['git','show',f'{CANDIDATE}:scripts/render_sample.py'],cwd=ROOT))
 (out/'rr-observer.pd_lua').write_bytes((ROOT/'tests/receiver_lifetime/observer.pd_lua').read_bytes())
 f=out/'sample-stretch.pd_lua';f.write_text(f.read_text()+'\n'+(ROOT/'tests/receiver_lifetime/bridge_probe.lua').read_text())
 f=out/'sample_player_rebuild.pd';f.write_text(append(f.read_text(),['obj 2900 5100 r \\$0-buffer_ID','obj 2900 5140 list prepend \\$1','obj 2900 5180 s rr-track','obj 3100 5100 r rr-open-\\$1','obj 3100 5140 s \\$0-open-sample-editor'],[(0,0,1,0),(1,0,2,0),(3,0,4,0)]))
 f=out/'sample-editor-panel.pd';f.write_text(append(f.read_text(),['obj 100 2300 r rr-command-\\$2','obj 100 2340 s \\$0-stretch-command'],[(0,0,1,0)]))
 with wave.open(str(out/'source.wav'),'wb')as w:
  w.setparams((2,2,48000,0,'NONE','not compressed'));w.writeframes(b''.join(struct.pack('<hh',int(3200*math.sin(2*math.pi*220*i/48000)),int(6400*math.sin(2*math.pi*330*i/48000)))for i in range(192000)))
 # Observer instantiated first; actual mlr contains all16 owners, players, original GUI/DAC/Grid.
 source=str(out/'source.wav').replace(' ','\\ ')
 objects=['obj 20 20 rr-observer','obj 20 60 mlr','obj 20 100 loadbang','obj 20 140 delay 1000',f'msg 20 180 \\; 1-sample-path symbol {source}','obj 300 140 delay 1500','msg 300 180 \\; 1-buffer-select sample 1 \\; rr-open-1 bang','obj 20 240 delay 2000','msg 20 280 \\; 1-sample-editor start 0.5 \\; 1-sample-editor finish 1.5 \\; rr-command-1 source-bpm 90 \\; rr-command-1 target-bpm 120 \\; rr-command-1 pitch 0']
 (out/'check.pd').write_text(append('#N canvas 100 100 900 450 12;\n',objects,[(2,0,3,0),(3,0,4,0),(2,0,5,0),(5,0,6,0),(2,0,7,0),(7,0,8,0)]))
 if mode!='ui':
  (out/'rr-driver.pd_lua').write_bytes((ROOT/'tests/receiver_lifetime/driver.pd_lua').read_bytes())
  parts=[]
  for slot in range(1,17):
   parts += [f'obj 20 {slot*30} sample-data {slot}',f'obj 250 {slot*30} sample_player_rebuild {slot}',f'obj 550 {slot*30} array define 0-live_buffer_{slot} 4',f'obj 800 {slot*30} array define 1-live_buffer_{slot} 4',f'obj 1050 {slot*30} buffer-view-data live {slot}']
  (out/'rr-session.pd').write_text(append('#N canvas 100 100 1300 600 12;\n',parts,[]))
  count=300 if mode=='campaign' else 5
  (out/'check.pd').write_text('#N canvas 100 100 900 400 12;\n#X obj 20 20 rr-observer 1;\n#N canvas 100 100 400 300 rr-session-container 0;\n#X restore 20 60 pd rr-session-container;\n'+f'#X obj 20 100 rr-driver {count} {mode};\n')
 for name in ['check.pd','sample_player_rebuild.pd','sample-editor-panel.pd']:assert not check(out/name)['errors'],check(out/name)
 manifest={'candidate_commit':CANDIDATE,'dependency_commit':dep_commit,'mode':mode,'expected':(1 if mode=='ui' else 300 if mode=='campaign' else 5),'source_sha256':sha(out/'source.wav'),'original_source_hashes':originals,'input_hashes':{str(f.relative_to(out)):sha(f)for f in out.rglob('*')if f.is_file()},'instrumentation':['passive file observer + additional completion listeners','method wrappers log return order without modifying candidate bodies','private test command and track readback taps','setup-only wrapper; actual mlr DAC/Grid retained; no playback commands'],'native_qualified':False}
 (out/'receipt.json').write_text(json.dumps(manifest,indent=2)+'\n');return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--fixture',type=Path,required=True);p.add_argument('--monome-source',type=Path);p.add_argument('--mode',choices=['ui','lifecycle','campaign'],default='ui');a=p.parse_args();print(build(a.fixture,a.mode,a.monome_source))
