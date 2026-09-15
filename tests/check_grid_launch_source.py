"""Guard the bounded Grid launch change against its PR43 base."""
from pathlib import Path
import hashlib,json,re,subprocess
from check_patch_connections import check
ROOT=Path(__file__).resolve().parents[1];BASE='62b7b4a30c5717a63db6d842b2194178051d1763'
def old(p):return subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT,text=True)
changed={'grid-cut-keys.pd_lua','sample_player_rebuild.pd','pending-cut-delay.pd'}
protected=[]
for name in subprocess.check_output(['git','ls-tree','--name-only',BASE],cwd=ROOT,text=True).splitlines():
 if name.endswith(('.pd','.pd_lua')) and name not in changed:
  assert (ROOT/name).read_text()==old(name),name
  protected.append(name)
def canvases(s):
 stack=[];out={}
 for line in s.splitlines(keepends=True):
  if line.startswith('#N canvas'):stack.append([line,[]])
  if line.startswith('#X restore'):
   head,lines=stack.pop();out[head]=''.join(lines)
  for _,lines in stack:lines.append(line)
 return out
before=canvases(old('sample_player_rebuild.pd'));after=canvases((ROOT/'sample_player_rebuild.pd').read_text())
untouched=[]
for head,body in before.items():
 if any(' '+name+' ' in head for name in ['stop_transition','slice_policy']):continue
 assert after[head]==body,head
 untouched.append(head.strip())
for name in ['sample_player_rebuild.pd','pending-cut-delay.pd']:
 assert not check(ROOT/name)['errors'],check(ROOT/name)
m=json.loads(Path('/tmp/plugmlr-grid-launch-after/source.json').read_text())
for name in changed:
 assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==m['production_sha256'][name],name+' changed since capture'
result={'base':BASE,'unchanged_components':protected,'unchanged_player_subpatches':untouched,'capture_matches_current_production':True}
print(json.dumps(result,indent=2))
