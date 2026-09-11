"""Extract the production clock verbatim with renamed buses; no audio objects.
Run from repo: python3 tests/build_standalone_clock_check.py
Open /tmp/plugmlr-clock-check.pd in plugdata. Test stops at 2300 ms.
Synthetic host tempo enters the same inlet as playhead tempo (not a DAW test).
"""
from pathlib import Path
import re
s=Path('mlr.pd').read_text(); start=s.index('#N canvas 180 120 1000 700 clock-system 0;'); end=s.index('#X restore 13 359 pd clock-system;',start)
body=s[start:end]
for name in ('global-transport','internal-bpm','clock-switch','clock-source','clock-bpm-ui','clock-run-ui','project_bpm','ppq'):
 body=re.sub(r'(?<![\w-])'+re.escape(name)+r'(?![\w-])','clocktest-'+name,body)
# Add a synthetic host input at the exact production host-tempo destination.
lines=body.splitlines(); n=sum(x.startswith(('#X obj','#X msg','#X floatatom','#X text')) for x in lines)
pos=next(i for i,x in enumerate(lines) if x.startswith('#X connect'))
lines.insert(pos,'#X obj 820 190 r clocktest-host-bpm;');lines.append(f'#X connect {n} 0 41 0;')
body='\n'.join(lines)+'\n#X restore 30 30 pd clock-system;\n'
o=[];c=[]
def obj(t): n=len(o)+1;o.append('#X '+t+';');return n
def link(a,b,out=0,into=0):c.append(f'#X connect {a} {out} {b} {into};')
lb=obj('obj 30 80 loadbang');tr=obj('obj 30 110 t b b b');timer=obj('obj 300 180 timer');delay=obj('obj 30 150 delay 2300');stop=obj('msg 30 190 \\; clocktest-global-transport 0');write=obj('msg 30 230 write /tmp/plugmlr-clock-events.txt');text=obj('obj 30 270 text define clocktest-events');score=obj('msg 150 150 read /tmp/plugmlr-clock-score.txt \\, bang');ql=obj('obj 150 190 qlist');r=obj('obj 300 80 r clocktest-ppq');tag=obj('obj 300 110 list prepend tick');bpm=obj('obj 500 80 r clocktest-project_bpm');btag=obj('obj 500 110 list prepend bpm');order=obj('obj 300 140 t l b');prepend=obj('obj 300 220 list prepend');insert=obj('obj 300 260 text insert clocktest-events 1e+09');done=obj('obj 30 310 print clock-check-stopped');dt=obj('obj 30 170 t b b b');
dummy=obj('obj 600 300 r clocktest-clock-source');
link(lb,tr);link(tr,timer,2);link(tr,delay,1);link(tr,score);link(score,ql);link(delay,dt);link(dt,stop,2);link(dt,write,1);link(write,text);link(dt,done);link(r,tag);link(tag,order);link(bpm,btag);link(btag,order);link(order,timer,1,1);link(timer,prepend,0,1);link(order,prepend);link(prepend,insert)
Path('/tmp/plugmlr-clock-check.pd').write_text('#N canvas 50 50 900 600 12;\n'+body+'\n'.join(o+c)+'\n')
Path('/tmp/plugmlr-clock-score.txt').write_text('''clocktest-internal-bpm 120;
100 clocktest-global-transport 1;
300 clocktest-global-transport 1;
200 clocktest-internal-bpm 240;
100 clocktest-host-bpm 80;
200 clocktest-global-transport 0;
100 clocktest-global-transport 2;
100 clocktest-global-transport 1;
200 clocktest-clock-switch bang;
100 clocktest-host-bpm 90;
100 clocktest-internal-bpm 60;
200 clocktest-clock-switch bang;
200 clocktest-internal-bpm 0;
clocktest-internal-bpm symbol invalid;
200 clocktest-global-transport 0;
''')
print('/tmp/plugmlr-clock-check.pd')
