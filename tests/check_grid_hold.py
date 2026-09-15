"""Check real Pd-Lua event output and ensure this change is confined to gestures."""
from pathlib import Path
import json,sys,subprocess,hashlib
ROOT=Path(__file__).resolve().parents[1];P=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/plugmlr-grid-hold-check')
m=json.loads((P/'source.json').read_text());assert hashlib.sha256((ROOT/'grid-cut-keys.pd_lua').read_bytes()).hexdigest()==m['production_sha256']
# The three current production changes are separately exercised by the launch audio suite.
# All other .pd and Lua files must be byte-for-byte the recorded base.
protected=[]
for name in subprocess.check_output(['git','ls-tree','--name-only',m['base']],cwd=ROOT,text=True).splitlines():
 if name.endswith(('.pd','.pd_lua')) and name not in ('grid-cut-keys.pd_lua','sample_player_rebuild.pd','pending-cut-delay.pd'):
  assert (ROOT/name).read_bytes()==subprocess.check_output(['git','show',m['base']+':'+name],cwd=ROOT),name
  protected.append(name)
actual=[[] for _ in m['cases']];case=None
for line in (P/'events.txt').read_text().splitlines():
 a=line.rstrip(';').split();t=float(a[0]);kind=a[1]
 if kind=='case':case=int(a[2]);continue
 assert case is not None
 actual[case].append([round(t-m['cases'][case]['base_ms'],6),kind]+[int(v) for v in a[2:]])
results=[]
for i,case in enumerate(m['cases']):
 result=dict(name=case['name'],expected=case['expected'],actual=actual[i],passed=case['expected']==actual[i]);results.append(result)
report=dict(production_sha256=m['production_sha256'],cases=results,passed=sum(r['passed'] for r in results),total=len(results),protected_sources=protected,native_runtime='plugdata 0.9.4 nightly 98ae0f78b / Pd 0.56.3 (verify in console)',physical_grid_acceptance='Open; timed native messages do not establish human feel.')
(P/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
assert all(r['passed'] for r in results),[r for r in results if not r['passed']]
print(f"PASS {len(results)} native cases; {len(protected)} existing patch/Lua files unchanged")
