"""Build a small, silent-by-default native workbench and its reproducible input."""
from pathlib import Path
import wave,math,struct,json,hashlib
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;OUT=Path('/tmp/plugmlr-stretch-workbench');OUT.mkdir(exist_ok=True)
with wave.open(str(OUT/'source.wav'),'wb') as w:
 w.setparams((2,2,48000,0,'NONE','not compressed'))
 w.writeframes(b''.join(struct.pack('<hh',round(32767*.1*math.sin(2*math.pi*220*i/48000)),round(32767*.2*math.sin(2*math.pi*330*i/48000))) for i in range(96000)))
class Patch:
 def __init__(self):self.objs=[];self.edges=[]
 def add(self,line):i=len(self.objs);self.objs.append('#X '+line+';');return i
 def wire(self,a,b,out=0,inp=0):self.edges.append(f'#X connect {a} {out} {b} {inp};')
p=Patch();o,c=p.add,p.wire
o('text 25 15 OFFLINE STRETCH WORKBENCH - isolated compatibility experiment - no mlr.pd dependency')
o('text 25 45 No DAC or hardware input. RUN captures 12 seconds then stops. DSP must already be on.')
run=o('obj 30 100 bng 30 250 50 0 empty empty RUN_12s 36 15 0 14 #faf8f2 #347c72 #283d3a')
abort=o('obj 270 100 bng 30 250 50 0 empty empty STOP 36 15 0 14 #faf8f2 #b75e49 #283d3a')
start=o('obj 30 150 t b b b');c(run,start)
o('text 25 200 A / bundled phase vocoder - signal-rate render at wall-clock speed (not background/offline)')
openpv=o(f'msg 30 240 open {OUT}/source.wav');pv=o('obj 30 300 else/pvoc.player~ -speed 50 -transp 1200 2');c(openpv,pv)
o('text 430 250 Input 2 seconds / 220 Hz L / 330 Hz R. Speed 50 percent / pitch +1200 cents.')
o('text 430 280 Expected rendered length about 4 seconds / 440 Hz L / 660 Hz R.')
stoppv=o('msg 30 345 stop');c(stoppv,pv)
o('text 25 395 B / optional external Rubber Band worker - invoke render_worker.py separately')
o('text 25 420 Threaded import into private arrays. No active application buffer is changed.')
load=o(f'msg 30 455 load {OUT}/rubberband.wav');sf=o('obj 30 495 else/sfload -t \\$0-stage');c(load,sf)
arr0=o('obj 460 455 array define 0-\\$0-stage 4');arr1=o('obj 460 490 array define 1-\\$0-stage 4')
info=o('obj 30 535 list prepend loaded');log=o('obj 30 570 s \\$0-log');c(sf,info);c(info,log)
o('text 25 620 C / reference continuity - independent oscillators run through both processing and loading')
refs=[]
for x,hz in [(30,997),(270,1499)]:
 osc=o(f'obj {x} 655 osc~ {hz}');gain=o(f'obj {x} 690 *~ 0.05');c(osc,gain);refs.append(gain)
rec=o('obj 720 690 writesf~ 4');c(pv,rec,0,0);c(pv,rec,1,1);c(refs[0],rec,0,2);c(refs[1],rec,0,3)
capopen=o(f'msg 720 610 open -bytes 4 {OUT}/capture.wav');c(start,capopen,2);c(capopen,rec)
go=o('obj 720 150 delay 50');c(start,go,0);got=o('obj 720 185 t b b');c(go,got)
msg=o('msg 875 220 start');c(got,msg,1);c(msg,rec);c(got,openpv)
finish=o('obj 950 150 delay 12000');c(start,finish,0)
# Independent Stop is armed before any load/processing command.
watch=o('obj 1080 150 delay 14000');c(start,watch,1)
stop=o('obj 950 300 t b b b');c(finish,stop);c(watch,stop);c(abort,stop)
st=o('msg 1010 345 stop');c(stop,st,2);c(st,rec);c(stop,stoppv,2)
for d in (go,finish,watch):c(st,d)
ld=o('obj 830 255 delay 6500');c(start,ld);c(ld,load);c(st,ld)
# Export staged arrays only after capture stops (outside the continuity window).
export=o('obj 950 390 delay 100');c(stop,export)
id=o('obj 950 425 f \\$0');c(export,id)
save=o(f'msg 750 465 write -wave -bytes 4 {OUT}/staged.wav 0-\\$1-stage 1-\\$1-stage');c(id,save)
writer=o('obj 750 500 soundfiler');c(save,writer)
done=o('msg 950 535 completed');c(export,done);c(done,log)
pvdone=o('msg 350 345 pvoc_finished');c(pv,pvdone,2);c(pvdone,log)
r=o('obj 750 740 r \\$0-log');pr=o('obj 750 775 print stretch-workbench');c(r,pr)
(HERE/'workbench.pd').write_text('#N canvas 40 40 1240 850 12;\n'+'\n'.join(p.objs+p.edges)+'\n')
(OUT/'prepare.json').write_text(json.dumps({'source_rate':48000,'source_frames':96000,'source_sha256':hashlib.sha256((OUT/'source.wav').read_bytes()).hexdigest(),'patch_sha256':hashlib.sha256((HERE/'workbench.pd').read_bytes()).hexdigest()},indent=2)+'\n')
print(HERE/'workbench.pd')
