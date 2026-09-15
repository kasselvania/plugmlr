"""Native key/page-message check plus optional real screen navigation. No audio.
Open /tmp/plugmlr-grid-screen-check/check.pd; auto-start/finish within 20 seconds.
"""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];OUT=Path('/tmp/plugmlr-grid-screen-check');OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'tests'));from check_patch_connections import check
src=(ROOT/'grid-cut-keys.pd_lua').read_text();name='screen-keys-'+hashlib.sha256(src.encode()).hexdigest()[:10]
(OUT/(name+'.pd_lua')).write_text(src.replace("register('grid-cut-keys')",f"register('{name}')"))
objects=[];edges=[]
def o(s):objects.append('#X '+s+';');return len(objects)-1
def c(a,b,x=0,y=0):edges.append(f'#X connect {a} {x} {b} {y};')
o('text 20 15 Grid page screen check - no audio - opens Player 2 then Overview')
lb=o('obj 20 60 loadbang');d=o('obj 20 100 delay 1000');tr=o('obj 20 140 t b b');c(lb,d);c(d,tr)
log=o('obj 700 400 text define \\$0-events');clear=o('msg 500 180 clear');c(tr,clear,1);c(clear,log)
q=o('obj 20 230 qlist');r=o(f'msg 20 190 read {OUT}/score.txt \\, bang');c(tr,r);c(r,q)
r=o('obj 20 280 r screen-check-input');rt=o('obj 20 320 route key connected');k=o(f'obj 20 360 {name}');c(r,rt);c(rt,k);c(rt,k,1,1)
for outlet,label in [(0,'slice'),(1,'play'),(2,'focus'),(4,'loop'),(5,'reverse'),(6,'speed'),(7,'screen')]:
 p=o(f'obj {20+outlet*120} 430 list prepend {label}');send=o(f'obj {20+outlet*120} 470 s screen-check-log');c(k,p,outlet);c(p,send)
r=o('obj 700 300 r screen-check-log');ins=o('obj 700 350 text insert \\$0-events 1e+09');c(r,ins)
r=o('obj 20 550 r screen-check-finish');tr=o('obj 20 590 t b b');c(r,tr)
w=o(f'msg 250 630 write {OUT}/events.txt');c(tr,w,1);c(w,log);done=o('obj 20 630 print screen-check-done');c(tr,done)
# Real UI navigation uses the exact new route/send tail of grid-cut-control.
r=o('obj 20 700 r screen-check-live');gate=o('obj 300 700 spigot');c(r,gate,0,1);c(k,gate,7)
s=(ROOT/'grid-cut-control.pd').read_text().splitlines();prod=[l for l in s if l.startswith('#X ') and not l.startswith('#X connect')];mapping={}
for old in range(26,len(prod)):mapping[old]=o(prod[old][3:-1])
c(gate,mapping[26])
for l in s:
 if l.startswith('#X connect'):
  a,x,b,y=map(int,l.rstrip(';').split()[2:])
  if a in mapping and b in mapping:c(mapping[a],mapping[b],x,y)
(OUT/'check.pd').write_text('#N canvas 100 80 1050 800 12;\n'+'\n'.join(objects+edges)+'\n')
score=[];expected=[]
def at(t,r,m):score.append((t,r,m))
def key(t,x,y,z=1):at(t,'screen-check-input',f'key {x} {y} {z}')
def tap(t,x,y):key(t,x,y);key(t+1,x,y,0)
at(0,'screen-check-input','connected 1')
# Every track: focus only, CUT, CUT again, PLAY. No audio commands on PLAY focus.
for row in range(1,7):
 t=100*row;tap(t,0,0);expected.append(['screen','play',row-1 if row>1 else 1])
 tap(t+10,2,row)
 if row>1:expected.append(['focus',row])
 tap(t+20,1,0);expected.append(['screen','cut',row])
 tap(t+30,1,0);expected.append(['screen','cut',row])
# Duplicate down/release do not reopen; modified page buttons do nothing.
key(800,0,0);expected.append(['screen','play',6]);key(805,0,0);key(810,0,0,0)
key(820,15,0);tap(830,1,0);key(840,15,0,0)
key(850,13,0);tap(860,1,0);key(870,13,0,0)
at(900,'screen-check-input','connected 0');at(910,'screen-check-input','connected 1')
# Focus follows ordinary CUT interaction, but only a subsequent page press opens.
tap(920,1,0);expected.append(['screen','cut',6]);tap(930,4,3);expected += [['focus',3],['slice',4,3,1]]
tap(940,1,0);expected.append(['screen','cut',3])
# UI phase: page dispatcher into the user's real empty original application.
tap(1000,0,0);expected.append(['screen','play',3]);tap(1010,2,2);expected.append(['focus',2])
at(1100,'screen-check-live','1');tap(1200,1,0);expected.append(['screen','cut',2])
tap(12000,0,0);expected.append(['screen','play',2])
at(13000,'screen-check-finish','bang')
last=0;lines=[]
for t,r,m in sorted(score):lines.append(f'{t-last} {r} {m};');last=t
(OUT/'score.txt').write_text('\n'.join(lines)+'\n')
(OUT/'source.json').write_text(json.dumps(dict(expected=expected,base='4da7e6d364fa0c70e3bfd447de37cde89a5c1a76',production_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['grid-cut-keys.pd_lua','grid-cut-control.pd']},fixture_sha256={n:hashlib.sha256((OUT/n).read_bytes()).hexdigest() for n in ['check.pd','score.txt',name+'.pd_lua']}),indent=2)+'\n')
assert not check(OUT/'check.pd')['errors'],check(OUT/'check.pd');print(OUT/'check.pd')
