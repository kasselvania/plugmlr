"""Silent native Pd-Lua timing test; no device claim, global player messages or audio.
Open /tmp/plugmlr-grid-hold-check/check.pd; console: grid-hold-check-run bang.
"""
from pathlib import Path
import json,hashlib,sys
ROOT=Path(__file__).resolve().parents[1];OUT=Path('/tmp/plugmlr-grid-hold-check');OUT.mkdir(exist_ok=True)
source=(ROOT/'grid-cut-keys.pd_lua').read_bytes();digest=hashlib.sha256(source).hexdigest();name='grid-hold-'+digest[:10]
(OUT/(name+'.pd_lua')).write_text(source.decode().replace("register('grid-cut-keys')",f"register('{name}')"))
cases=[]
def add(name,commands,expected):cases.append(dict(name=name,commands=commands,expected=expected))
def key(t,x,y,z):return [t,'key',f'{x} {y} {z}']
def event(t,kind,*a):return [t,kind,*a]
# A slice on each fresh down; no event at all on an unqualified release.
for row in (1,2,6):
 for overlap in (0,5,39,40,41,100):
  for first_up in (2,7):
   second_up=7 if first_up==2 else 2
   cmd=[key(10,2,row,1),key(20,7,row,1),key(20+overlap,first_up,row,0),key(150,second_up,row,0)]
   want=[event(10,'slice',2,row,1),event(20,'slice',7,row,1)]
   if overlap>=40:want+=[event(20+overlap,'loop',row,2,8)]
   add(f'row{row}-overlap{overlap}-release{first_up}',cmd,want)
add('long-first-short-overlap',[key(10,1,1,1),key(160,8,1,1),key(165,8,1,0),key(200,1,1,0)],
    [event(10,'slice',1,1,1),event(160,'slice',8,1,1)])
add('duplicate-does-not-restart',[key(10,1,1,1),key(20,8,1,1),key(50,8,1,1),key(61,8,1,0),key(100,1,1,0)],
    [event(10,'slice',1,1,1),event(20,'slice',8,1,1),event(61,'loop',1,1,9)])
add('timer-alone-never-loops',[key(10,1,1,1),key(20,8,1,1)],
    [event(10,'slice',1,1,1),event(20,'slice',8,1,1)])
add('three-keys-still-cut-cancel-loop',[key(10,1,1,1),key(20,5,1,1),key(70,9,1,1),key(100,5,1,0),key(110,9,1,0),key(120,1,1,0)],
    [event(10,'slice',1,1,1),event(20,'slice',5,1,1),event(70,'slice',9,1,1)])
for delay in (30,70):
 add(f'cancel-at-{delay}',[key(10,1,1,1),key(20,5,1,1),[delay,'cancel','1'],key(100,5,1,0),key(110,1,1,0)],
     [event(10,'slice',1,1,1),event(20,'slice',5,1,1)])
add('old-deadline-cannot-arm-new-pair',[key(10,1,1,1),key(20,5,1,1),key(30,5,1,0),key(31,1,1,0),key(40,2,1,1),key(50,6,1,1),key(65,6,1,0),key(110,2,1,0)],
    [event(10,'slice',1,1,1),event(20,'slice',5,1,1),event(40,'slice',2,1,1),event(50,'slice',6,1,1)])
add('independent-rows',[key(10,1,1,1),key(20,5,1,1),key(30,3,2,1),key(40,9,2,1),key(65,1,1,0),key(70,3,2,0),key(100,5,1,0),key(110,9,2,0)],
    [event(10,'slice',1,1,1),event(20,'slice',5,1,1),event(30,'slice',3,2,1),event(40,'slice',9,2,1),event(65,'loop',1,1,6)])
add('ALT-cancels-armed-pair',[key(10,1,1,1),key(20,5,1,1),key(70,15,0,1),key(80,5,1,0),key(90,1,1,0),key(100,8,1,1),key(105,8,1,1),key(110,8,1,0),key(120,15,0,0)],
    [event(10,'slice',1,1,1),event(20,'slice',5,1,1),event(100,'play',1)])
add('MOD-still-immediate',[key(10,13,0,1),key(11,4,1,1),key(12,4,1,1),key(13,4,1,0),key(14,13,0,0)],
    [event(11,'loop',1,4,5)])
add('ALT-wins-over-MOD',[key(10,13,0,1),key(20,15,0,1),key(30,4,1,1),key(35,4,1,0),key(40,15,0,0),key(50,5,1,1),key(55,5,1,0),key(60,13,0,0)],
    [event(30,'play',1),event(50,'loop',1,5,6)])
add('MOD-cancels-unarmed-pair',[key(10,1,1,1),key(20,5,1,1),key(30,13,0,1),key(80,5,1,0),key(90,1,1,0),key(100,13,0,0)],
    [event(10,'slice',1,1,1),event(20,'slice',5,1,1)])
for delay in (30,70):
 add(f'detach-at-{delay}',[key(10,1,1,1),key(20,5,1,1),[delay,'connected','0'],[80,'connected','1'],key(100,5,1,0),key(110,1,1,0)],
     [event(10,'slice',1,1,1),event(20,'slice',5,1,1)])
add('repeat-taps-with-first-held',[key(10,1,1,1),key(20,5,1,1),key(25,5,1,0),key(40,7,1,1),key(45,7,1,0),key(60,5,1,1),key(65,5,1,0),key(100,1,1,0)],
    [event(10,'slice',1,1,1),event(20,'slice',5,1,1),event(40,'slice',7,1,1),event(60,'slice',5,1,1)])
add('malformed-duplicate-release',[[10,'key','-1 1 1'],[15,'key','0 9 1'],[20,'key','x 1 1'],[25,'key','1 1'],key(30,0,7,1),key(40,1,1,0)],[])
add('both-rows-qualified',[key(10,15,1,1),key(20,0,1,1),key(30,3,2,1),key(40,9,2,1),key(90,15,1,0),key(100,9,2,0),key(110,0,1,0),key(120,3,2,0)],
    [event(10,'slice',15,1,1),event(20,'slice',0,1,1),event(30,'slice',3,2,1),event(40,'slice',9,2,1),event(90,'loop',1,0,16),event(100,'loop',2,3,10)])
class Patch:
 def __init__(s):s.objects=[];s.edges=[]
 def add(s,l):s.objects.append('#X '+l+';');return len(s.objects)-1
 def wire(s,a,b,o=0,i=0):s.edges.append(f'#X connect {a} {o} {b} {i};')
p=Patch();o,c=p.add,p.wire
o('text 20 15 Grid hold timing check - silent - no device session - automatic finish')
r=o('obj 20 60 r grid-hold-check-run');tr=o('obj 20 100 t b b b');c(r,tr)
log=o('obj 650 500 text define \\$0-events');cl=o('msg 350 100 clear');c(tr,cl,2);c(cl,log)
timer=o('obj 650 350 timer');c(tr,timer,1)
ql=o('obj 20 190 qlist');read=o(f'msg 20 145 read {OUT}/score.txt \\, bang');c(tr,read);c(read,ql)
r=o('obj 20 240 r grid-hold-input');rt=o('obj 20 280 route key connected cancel');c(r,rt)
obj=o(f'obj 20 330 {name}');c(rt,obj);c(rt,obj,1,1);c(rt,obj,2,2)
for i,label in [(0,'slice'),(1,'play'),(4,'loop')]:
 tag=o(f'obj {20+i*120} 390 list prepend {label}');send=o(f'obj {20+i*120} 430 s grid-hold-log');c(obj,tag,i);c(tag,send)
r=o('obj 650 240 r grid-hold-log');tr=o('obj 650 280 t l b');pre=o('obj 650 390 list prepend');ins=o('obj 650 435 text insert \\$0-events 1e+09');c(r,tr);c(tr,timer,1,1);c(timer,pre,0,1);c(tr,pre);c(pre,ins)
r=o('obj 20 500 r grid-hold-finish');tr=o('obj 20 540 t b b');c(r,tr)
write=o(f'msg 220 580 write {OUT}/events.txt');c(tr,write,1);c(write,log)
pr=o('obj 20 580 print grid-hold-check-done');c(tr,pr)
(OUT/'check.pd').write_text('#N canvas 100 80 1000 650 12;\n'+'\n'.join(p.objects+p.edges)+'\n')
score=[]
for index,case in enumerate(cases):
 base=250*index;case['base_ms']=base
 score += [(base,'grid-hold-input','connected 0'),(base,'grid-hold-input','connected 1'),(base,'grid-hold-log','list case '+str(index))]
 score += [(base+t,'grid-hold-input',typ+' '+value) for t,typ,value in case['commands']]
score += [(250*len(cases),'grid-hold-input','connected 0'),(250*len(cases)+5,'grid-hold-finish','bang')]
last=0;lines=[]
for t,dst,msg in sorted(score,key=lambda v:v[0]):lines.append(f'{t-last} {dst} {msg};');last=t
(OUT/'score.txt').write_text('\n'.join(lines)+'\n')
manifest=dict(base='a09c10b5a2a653862d648564f93a9ac3586656d3',production_sha256=digest,test_class=name,cases=cases,duration_ms=last)
manifest['fixture_sha256']={n:hashlib.sha256((OUT/n).read_bytes()).hexdigest() for n in ['check.pd','score.txt',name+'.pd_lua']}
(OUT/'source.json').write_text(json.dumps(manifest,indent=2)+'\n')
sys.path.insert(0,str(ROOT/'tests'));from check_patch_connections import check
assert not check(OUT/'check.pd')['errors'];print(OUT/'check.pd');print(f'{len(cases)} cases; {last/1000}s; no audio capture')
