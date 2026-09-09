"""Generate actual-component render scenarios. Run make_fixture.py first."""
from pd_patch import Patch
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
for label,sr in [('48k',48000),('44k',44100),('mismatch',44100)]:
 p=Patch(1300,950)
 lb=p.obj(20,40,'loadbang')
 log=p.obj(880,500,r'text define \$0-log')
 insert=p.obj(880,460,r'text insert \$0-log 1e+09')
 receive=p.obj(880,300,r'r \$0-log-in');tr=p.obj(880,335,'t a b');p.c(receive,tr)
 timer=p.obj(1030,375,'timer');p.c(lb,timer);p.c(tr,timer,1,1)
 prefix=p.obj(880,415,'list prepend');p.c(tr,prefix);p.c(timer,prefix,0,1);p.c(prefix,insert)
 sink=p.obj(1040,250,r's \$0-log-in')
 def logger(obj,out=0):
  norm=p.obj(1000,210,'list prepend');p.c(obj,norm,out);p.c(norm,sink)
 buf=p.obj(20,210,r'../engine/r1-buffer \$0-main shared');logger(buf)
 buf2=p.obj(20,260,r'../engine/r1-buffer \$0-other shared');logger(buf2)
 empty=p.obj(20,310,r'../engine/r1-buffer \$0-main empty');logger(empty)
 heads=[]
 for j,(scope,h,bid) in enumerate([('main','A','shared'),('main','B','shared'),('main','C','shared'),('other','B','shared'),('other','A','shared'),('main','missing','absent'),('main','empty','empty')]):
  a=p.obj(370,140+j*70,rf'../engine/r1-head~ \$0-{scope} {h} {bid}');heads.append(a);logger(a,2)
 w=p.obj(370,700,'writesf~ 10')
 for j,h in enumerate(heads[:5]):p.c(h,w,0,j*2);p.c(h,w,1,j*2+1)
 events=[]
 def event(t,target,msg,label_target=None):
  if target in (buf,buf2,empty) and msg.startswith('load '): msg='load ../tests/'+msg[5:]
  j=len(events);d=p.obj(20+(j%8)*150,1050+(j//8)*100,f'delay {t}');m=p.msg(20+(j%8)*150,1085+(j//8)*100,msg)
  p.c(lb,d);p.c(d,m);p.c(m,target)
  if label_target:
   cm=p.msg(20+(j%8)*150,1120+(j//8)*100,f'command {label_target} {msg}');p.c(d,cm);p.c(cm,sink)
  events.append({'ms':t,'target':label_target,'message':msg})
 A,B,C,Bref,Aref,missing,eh=heads
 def cmd(t,h,msg):event(t,h,msg,{A:'A',B:'B',C:'C',Bref:'other-B',Aref:'other-A',missing:'missing',eh:'empty'}[h])
 event(200,missing,'start','missing');event(210,eh,'start','empty')
 event(250,empty,'load empty.wav','empty-buffer')
 event(500,buf,f'load stereo-{sr}.wav','buffer')
 event(600,buf2,f'load stereo-{sr}.wav','other-buffer')
 for h in [A,Aref]:cmd(750,h,'region 0.2 1.8')
 for h in [B,Bref]:
  cmd(750,h,'region 0.4 1.4');cmd(770,h,'rate 0.5');cmd(790,h,'gain 0.6')
 cmd(750,C,'region 0.6 1.6');cmd(770,C,'rate -1');cmd(790,C,'seek 1.5');cmd(810,C,'gain 0.4')
 event(900,w,f'open -bytes 4 evidence/{label}-full.wav')
 event(1000,w,'start')
 for h in heads[:5]:cmd(1100,h,'start')
 cmd(2100,A,'rate -1');cmd(3100,A,'rate 0.5');cmd(4100,A,'rate 2');cmd(4800,A,'rate 4')
 cmd(5100,A,'rate -4');cmd(5400,A,'rate 0');event(5450,buf,'load stereo-48000.wav','buffer')
 cmd(5900,A,'rate 1');cmd(6100,A,'gain 0.5');cmd(6300,A,'gain 1');cmd(6400,A,'seek 1.25');cmd(6700,A,'region 0.3 0.8')
 for t,msg in [(7000,'rate 9'),(7005,'rate 1e+40'),(7010,'rate nan'),(7020,'rate 1 2'),(7030,'seek -1'),(7040,'seek 0.8'),(7050,'region 1 0'),(7060,'region 0 9'),(7070,'region 0.1 0.101'),(7080,'loop 2'),(7090,'gain -1'),(7100,'unknown 5')]:cmd(t,A,msg)
 # Alternating seeks/rates/start-stop during active fades. The final command must win.
 for j in range(30):
  cmd(7500+j,A,['seek 0.35','rate -2','stop','start','seek 0.65','rate 2'][j%6])
 cmd(7540,A,'rate 1');cmd(7550,A,'start');cmd(7570,A,'seek 0.4')
 cmd(8100,A,'stop');cmd(8110,A,'stop');cmd(8300,A,'start');cmd(8310,A,'start')
 cmd(8800,A,'loop 0');cmd(8820,A,'seek 0.7');cmd(9400,A,'rate -1');cmd(9420,A,'seek 0.35');cmd(9440,A,'start');cmd(9620,A,'start')
 cmd(9900,A,'loop 1');cmd(9920,A,'region 0.5 0.52');cmd(9940,A,'rate 4');cmd(9960,A,'start')
 for h in heads[:5]:cmd(10400,h,'stop')
 # Replacement while all three users stop-fade must still be refused.
 event(10401,buf,'load stereo-48000.wav','buffer')
 event(10500,buf,'load does-not-exist.wav','buffer');event(10600,buf,'load mono.wav','buffer');event(10700,buf,'load empty.wav','buffer')
 event(10800,buf,'status','buffer')
 cmd(10750,A,'start');cmd(10850,A,'stop')
 # Refresh stopped head after valid replacement and resume against new file metadata.
 event(10900,buf,'load stereo-48000.wav','buffer');cmd(11200,A,'start');cmd(11400,A,'rate 0');event(11450,buf,'load stereo-44100.wav','buffer');cmd(11520,A,'rate 1');cmd(11600,A,'stop')
 event(12000,w,'stop')
 # Exercise a stop while DSP is paused after the audio capture has closed.
 cmd(12010,A,'start')
 off=p.msg(880,660,r'\; pd dsp 0');on=p.msg(1030,660,r'\; pd dsp 1')
 event(12012,off,'bang');cmd(12013,A,'stop')
 event(12014,buf,'load stereo-48000.wav','buffer')
 event(12060,on,'bang');event(12100,buf,'load stereo-48000.wav','buffer')
 event(12200,log,f'write evidence/{label}-states.txt')
 done=p.obj(880,600,'print R1-DONE');event(12300,done,label)
 p.text(20,850,f'Actual plugdata render: {label}. File rate {sr} Hz. Set host rate before opening.')
 p.text(20,890,'No dac~. 10 channels = main A/B/C then other B/A. All controls below are ordinary messages.')
 p.save(f'tests/render-{label}.pd')
 (ROOT/f'tests/{label}-events.json').write_text(json.dumps(events,indent=2)+'\n')
# A second actual-audio regression at large absolute file positions.
p=Patch(1000,680)
lb=p.obj(25,30,'loadbang')
b=p.obj(25,240,r'../engine/r1-buffer \$0 shared')
a=p.obj(350,240,r'../engine/r1-head~ \$0 A shared')
w=p.obj(350,350,'writesf~ 2');p.c(a,w);p.c(a,w,1,1)
log=p.obj(700,400,r'text define \$0-log');ins=p.obj(700,350,r'text insert \$0-log 1e+09')
pre=p.obj(700,290,'list prepend');p.c(a,pre,2);p.c(b,pre);p.c(pre,ins)
for j,(ms,target,msg) in enumerate([(500,b,'load ../tests/precision-44100.wav'),(700,a,'region 9 11'),(720,a,'rate 0.5'),(740,a,'seek 10'),(900,w,'open -bytes 4 evidence/precision-full.wav'),(1000,w,'start'),(1100,a,'start'),(3000,a,'stop'),(3100,w,'stop'),(3200,log,'write evidence/precision-states.txt')]):
 d=p.obj(25+(j%5)*180,480+(j//5)*100,f'delay {ms}');m=p.msg(25+(j%5)*180,520+(j//5)*100,msg);p.c(lb,d);p.c(d,m);p.c(m,target)
p.text(25,100,'Precision regression: 48 kHz host / 44.1 kHz file / seek 10 seconds / rate 0.5')
p.text(25,145,'Records actual component stereo audio for 2.1 seconds. No DAC. Done after 3.3 seconds.')
p.save('tests/render-precision.pd')
