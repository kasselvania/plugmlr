"""Bounded native persistence + eight-slot regression. No DAC/recording;23s watchdog."""
from pathlib import Path
import runpy,json,hashlib,sys
ROOT=Path(__file__).resolve().parents[1]
b=runpy.run_path(str(ROOT/'tests/build_pattern_bank_check.py'));OUT=Path('/tmp/plugmlr-pattern-files');OUT.mkdir(exist_ok=True)
for f in b['OUT'].iterdir():
 if f.suffix in ('.pd','.pd_lua','.lua'):(OUT/f.name).write_text(f.read_text().replace(str(b['OUT']),str(OUT)))
 elif f.name=='source.wav':(OUT/f.name).write_bytes(f.read_bytes())
base=b['b'];Patch=base['Patch'];count=base['count'];check=base['check'];prefix=base['prefix']
f=OUT/'check.pd';s=f.read_text().replace('delay 18000','delay 23000').replace('18 second stop','23 second stop').replace('\\; pcheck-command stop','\\; fresh-command stop \\; pcheck-command stop')
p=Patch(count(s));o,c=p.add,p.wire
r=o('obj 1350 20 r pcheck-file-status');tag=o('obj 1350 60 list prepend file-status');log=o('obj 1350 100 s pcheck-log');c(r,tag);c(tag,log)
r=o('obj 1350 150 r fresh-command');core=o('obj 1350 190 '+prefix+'performance-pattern');c(r,core)
for out,label in [(0,'fresh-replay'),(1,'fresh-status'),(3,'fresh-file-status')]:
 t=o('obj 1500 230 list prepend '+label);l=o('obj 1500 270 s pcheck-log');c(core,t,out);c(t,l)
t=o('obj 1350 310 t l l');u=o('obj 1540 350 unpack f');name=o('obj 1540 390 makefilename 90%d-pattern-command');split=o('obj 1350 350 list split 1');trim=o('obj 1350 390 list trim');send=o('obj 1350 430 send')
c(core,t);c(t,u,1);c(u,name);c(name,send,0,1);c(t,split);c(split,trim,1);c(trim,send)
f.write_text(s+'\n'+p.text())
(OUT/'panel-check.pd').write_text('#N canvas 80 60 1080 160 12;\n#X obj 20 20 pattern-bank-panel pcheck-file;\n')
(OUT/'bad.plugmlr-patterns').write_text('plugmlr-pattern-bank 2\nend\n')
score=[(t,r,m.replace(str(b['OUT']),str(OUT))) for t,r,m in b['score'] if r!='pcheck-finish']
def at(t,cmd,target='pcheck-file'):score.append((t,target,cmd))
path=str(OUT/'roundtrip.plugmlr-patterns')
at(14800,'save '+path);at(14810,'load '+str(OUT/'bad.plugmlr-patterns'))
at(14820,'toggle 3','pcheck-command');at(14850,'load '+str(OUT/'bad.plugmlr-patterns'));at(14920,'load '+path)
at(15000,'clear 3','pcheck-command');at(15010,'load '+path);at(15020,'cancel-load');at(15030,'replace')
at(15100,'load '+path);at(15110,'toggle 6','pcheck-command');at(15120,'replace');at(15130,'stop','pcheck-command');at(15140,'replace')
at(15150,'load '+path);at(15160,'replace')
at(15200,'save '+str(OUT/'absent/bank'));at(15210,'load '+str(OUT/'absent-bank'))
at(15250,'load '+path,'fresh-command');at(15300,'toggle 3','fresh-command');at(15400,'stop','fresh-command')
for i in range(1,9):at(15420,f'clear {i}','pcheck-command')
at(15440,'save '+str(OUT/'empty.plugmlr-patterns'));at(15460,'load '+str(OUT/'empty.plugmlr-patterns'),'fresh-command');at(15480,'load '+path,'fresh-command')
at(15500,'toggle 8','fresh-command');at(15600,'stop','fresh-command');at(15610,'load '+path)
at(15700,'toggle 1','pcheck-command');at(15800,'save '+str(OUT/'playing-save.plugmlr-patterns'));at(15810,'load '+str(OUT/'bad.plugmlr-patterns'));at(15880,'stop','pcheck-command')
at(15890,'clear 1','pcheck-command');at(15895,'load '+path);at(15900,'bang','pcheck-finish')
last=0;lines=[]
for t,r,msg in sorted(score,key=lambda v:v[0]):lines.append(f'{t-last} {r} {msg};');last=t
(OUT/'score.txt').write_text('\n'.join(lines)+'\n')
m=b['manifest'];m.update(files=True,files_base='912ec750a157a6d05353ed475d95d8b146cf5755',score=score)
m['production_sha256']['pattern-bank-file.lua']=hashlib.sha256((ROOT/'pattern-bank-file.lua').read_bytes()).hexdigest()
m['fixture_sha256']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in OUT.iterdir() if f.suffix in ('.pd','.pd_lua','.lua') or f.name in ('source.wav','score.txt','bad.plugmlr-patterns')}
(OUT/'source.json').write_text(json.dumps(m,indent=2)+'\n')
for name in ['check.pd','panel-check.pd','pattern-control.pd','pattern-bank-panel.pd']:assert not check(OUT/name)['errors'],check(OUT/name)
print(OUT/'check.pd')
