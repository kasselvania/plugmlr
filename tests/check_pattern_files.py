"""Native persistence checks plus strict preservation against PR48 (not historical UI)."""
from pathlib import Path
import json, subprocess, sys, runpy, re, hashlib
from check_patch_connections import check
from check_ui_overview import subpatches
ROOT=Path(__file__).resolve().parents[1]
P=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/plugmlr-pattern-files')
sys.argv=[str(ROOT/'tests/check_pattern_bank.py'),str(P)]
runpy.run_path(sys.argv[0],run_name='__main__')
m=json.loads((P/'source.json').read_text());assert m['files']
rows=[]
for line in (P/'events.txt').read_text().splitlines():
 a=line.rstrip(';').split();rows.append((float(a[0]),a[1:]))
def selected(tag):return [(t,a[1:]) for t,a in rows if a[0]==tag and t>=14800]
def exact(tag,want):
 actual=selected(tag);assert len(actual)==len(want),(tag,actual)
 for (t,a),(wt,wa) in zip(actual,want):assert abs(t-wt)<.05 and a==wa,(tag,t,a,wt,wa)
exact('replay',[(14820,['1','restore','0','2']),(14880,['1','cut','2']),
 (15700,['1','restore','0','2']),(15750,['1','direction','1']),
 (15780,['1','speed','3']),(15810,['1','cut','8'])])
exact('fresh-replay',[(15300,['1','restore','0','2']),(15360,['1','cut','2']),
 (15500,['2','restore','0','2']),(15560,['2','cut','9'])])
for t,track,cell in [(14880,1,2),(15360,1,2),(15560,2,9),(15810,1,8)]:
 assert (t,['accepted','cut',str(track),str(cell)]) in rows
for tag,t in [('status',14920),('status',15160),('fresh-status',15250),('fresh-status',15480),('status',15610)]:
 actual=[a for et,a in selected(tag) if et==t and a[0]=='pattern']
 assert actual==[['pattern',str(i),'stopped' if i in (1,3,5,8) else 'empty'] for i in range(1,9)],(t,actual)
assert [a for t,a in selected('fresh-status') if t==15460 and a[0]=='pattern']==[['pattern',str(i),'empty'] for i in range(1,9)]
labels={t:' '.join(a[1:]).replace('\\ ',' ') for t,a in selected('file-status')}
for t,fragment in [(14800,'Saved | roundtrip'),(14810,'Load failed:'),(14850,'Load failed:'),
 (15010,'Unsaved patterns:'),(15020,'Unsaved |'),(15110,'Patterns changed'),
 (15120,'Finish pattern recording first'),(15150,'Unsaved patterns:'),(15160,'Loaded (stopped)'),
 (15200,'Save failed:'),(15210,'Load failed:'),(15440,'Saved | empty'),(15800,'Saved | playing-save'),
 (15810,'Load failed:'),(15895,'Unsaved patterns:')]:assert fragment in labels[t],(t,labels[t])
assert not any(t in (15030,15140) for t,a in selected('status')) # cancelled/invalidated Replace no-op
raw=(P/'roundtrip.plugmlr-patterns').read_bytes()
assert raw==(P/'playing-save.plugmlr-patterns').read_bytes()
assert (P/'empty.plugmlr-patterns').read_text()=='plugmlr-pattern-bank 1\n'+''.join(f'slot {i} 0 0 0\n' for i in range(1,9))+'end\n'
for f in P.glob('Native *bank.plugmlr-patterns'):assert f.read_bytes()==raw
# Current slice must preserve every pre-existing component except these three.
base=m['files_base'];allowed={'mlr.pd','grid-cut-control.pd','performance-pattern.pd_lua'}
def old(name):return subprocess.check_output(['git','show',base+':'+name],cwd=ROOT,text=True)
protected=[]
for name in subprocess.check_output(['git','ls-tree','--name-only',base],cwd=ROOT,text=True).splitlines():
 if name.endswith(('.pd','.pd_lua','.lua')) and name not in allowed:
  assert (ROOT/name).read_text()==old(name),name
  protected.append(name)
current=(ROOT/'mlr.pd').read_text();prior=old('mlr.pd')
assert subpatches(current)==subpatches(prior),'nested application wiring changed'
# Reverse only the documented footer/layout extension, then compare every byte.
lines=[];depth=0
for line in current.splitlines():
 if line=='#X obj 20 770 pattern-bank-panel mlr-pattern-file;':continue
 if line.startswith('#N canvas'):depth+=1
 elif line.startswith('#X restore'):depth-=1
 if depth==1:
  line=line.replace('cnv 15 1070 890','cnv 15 1070 790')
  match=re.match(r'(#X (?:obj|msg|text|floatatom|symbolatom|restore) \S+ )(\d+)( .*)',line)
  if match and int(match[2])>=950:line=match[1]+str(int(match[2])-100)+match[3]
 lines.append(line)
assert '\n'.join(lines).rstrip()==prior.rstrip()
control=(ROOT/'grid-cut-control.pd').read_text()
assert control.startswith(old('grid-cut-control.pd'))
assert control[len(old('grid-cut-control.pd')):].strip()=='''#X obj 1100 780 r mlr-pattern-file;
#X obj 1100 820 s mlr-pattern-file-status;
#X obj 1100 860 s mlr-pattern-file-chooser;
#X connect 47 0 32 0;
#X connect 32 3 48 0;
#X connect 32 4 49 0;'''
for name in ('mlr.pd','grid-cut-control.pd','pattern-bank-panel.pd'):
 assert not check(ROOT/name)['errors'],check(ROOT/name)
for name,h in m['production_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
r=dict(passed=True,native_replay_commands=125,files_base=base,unchanged_components=protected,
 checks=['77 timeline +38 bank +10 persistence replay commands','Saved all-slot data replays in a fresh recorder',
 'Loaded banks stopped; full slot LED/status refresh','Malformed load leaves current scheduler running',
 'Dirty bank staged; Cancel and edits invalidate Replace','Recording refuses replacement',
 'Missing reads and failed writes preserve bank','Save while playing preserves next cut',
 'Empty bank roundtrip','Exact root layout and nested engine preservation'],
 limitations=['Native file chooser and panel rendering documented separately','No new audio or physical Grid acceptance','Synchronous I/O, no disk-latency audio guarantee'])
(P/'files-analysis.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS persistence and',len(protected),'unchanged components against PR48')
