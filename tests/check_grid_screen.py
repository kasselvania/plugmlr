"""Native page-message check and exact production-source boundary."""
from pathlib import Path
import hashlib,json,subprocess,sys
from check_patch_connections import check
ROOT=Path(__file__).resolve().parents[1];P=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/plugmlr-grid-screen-check')
m=json.loads((P/'source.json').read_text())
actual=[]
for line in (P/'events.txt').read_text().splitlines():
 a=line.rstrip(';').split();actual.append([int(x) if x.isdigit() else x for x in a])
assert actual==m['expected'],(actual,m['expected'])
for n,h in m['production_sha256'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h,n
allowed={'grid-cut-keys.pd_lua','grid-cut-control.pd'}
protected=[]
for name in subprocess.check_output(['git','ls-tree','--name-only',m['base']],cwd=ROOT,text=True).splitlines():
 if name.endswith(('.pd','.pd_lua')) and name not in allowed:
  assert (ROOT/name).read_bytes()==subprocess.check_output(['git','show',m['base']+':'+name],cwd=ROOT),name
  protected.append(name)
assert not check(ROOT/'grid-cut-control.pd')['errors']
report=dict(passed=True,expected_events=len(actual),screen_requests=sum(a[0]=='screen' for a in actual),unchanged_components=protected,native_visual_acceptance='Record actual CUT and PLAY screenshots separately; messages alone do not prove visible navigation.')
(P/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');print(f'PASS {len(actual)} native events; {len(protected)} components unchanged')
