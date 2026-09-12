"""Build a bounded native fixture. Args: actual Player 1/2 dollar-zero values."""
from pathlib import Path
import json
nodes=[];w=[]
def o(s):nodes.append('#X '+s+';');return len(nodes)-1
def c(a,b,out=0,inn=0):w.append(f'#X connect {a} {out} {b} {inn};')
r=o('obj 20 20 r two-lane-capture');g=o('obj 20 50 spigot 1');t=o('obj 20 90 t b b b b');c(r,g);c(g,t)
z=o('msg 480 90 0');c(t,z,3);c(z,g,0,1)
end=o('obj 650 90 delay 30000');c(t,end,2)
op=o('msg 200 130 open -bytes 4 /tmp/two-lane-cut.wav');st=o('msg 20 130 start');wr=o('obj 20 480 writesf~ 16');c(t,op,1);c(op,wr);c(t,st);c(st,wr)
for n in [1,2]:
 a=o(f'obj {n*180} 190 r~ {n}-voice_audio');b=o(f'obj {n*180} 225 snake~ out 2');c(a,b);c(b,wr,0,(n-1)*2);c(b,wr,1,(n-1)*2+1)
for ch,n in [('left',4),('right',5)]:a=o(f'obj {n*150} 190 r~ plugmlr-record-check-{ch}');c(a,wr,0,n)
for n in [1,2]:
 x=30+(n-1)*550
 a=o(f'obj {x} 280 r~ \\${n}-vline_output_sig');c(a,wr,0,5+n)
 for k,edge in enumerate(['start','end']):
  a=o(f'obj {x+k*250} 320 r \\${n}-set_active_loop_{edge}');b=o(f'obj {x+k*250} 350 sig~');c(a,b);c(b,wr,0,8+(n-1)*2+k)
 # Each flag contributes a separate signal, summed without message ordering ambiguity.
 sm=o(f'obj {x} 420 +~');sm2=o(f'obj {x+120} 420 +~');sm3=o(f'obj {x+240} 420 +~');c(sm,sm2);c(sm2,sm3);c(sm3,wr,0,11+n)
 for k,key in enumerate(['buffer-ready','is_playing_flag','is_paused_flag','buffer-switching']):
  a=o(f'obj {x+k*130} 540 r \\${n}-{key}');b=o(f'obj {x+k*130} 570 * {2**k}');d=o(f'obj {x+k*130} 600 sig~');c(a,b);c(b,d)
  target=[sm,sm,sm2,sm3][k];c(d,target,0,0 if k==0 else 1)
 a=o(f'obj {x} 660 r \\${n}-buffer_ID');b=o(f'obj {x} 690 select sample_buffer_1 sample_buffer_2');sg=o(f'obj {x} 760 sig~');c(a,b)
 for k,v in enumerate([1,2,0]):
  m=o(f'msg {x+k*100} 725 {v}');c(b,m,k);c(m,sg)
 c(sg,wr,0,13+n)
f=o('obj 700 800 t b b b b');c(end,f)
s=o('msg 800 840 stop');c(f,s,3);c(s,wr)
m=o('msg 800 880 dsp 0');p=o('obj 800 915 s pd');c(f,m,2);c(m,p)
m=o('msg 500 880 0');p=o('obj 500 915 s global-transport');c(f,m,1);c(m,p)
p=o('obj 700 955 print two-lane-capture-stopped');c(f,p)
schedule=[]
def send(ms,rc,msg):schedule.append((ms,rc,msg))
def key(ms,x,y,z):send(ms,'two-lane-check-key',f'{x} {y} {z}')
def tog(ms,y):
 key(ms,15,0,1);key(ms+1,0,y,1);key(ms+2,0,y,0);key(ms+3,15,0,0)
def cut(ms,x,y):key(ms,x,y,1);key(ms+20,x,y,0)
def mod(ms,x,y):
 key(ms,13,0,1);key(ms+1,x,y,1);key(ms+80,x,y,0);key(ms+100,13,0,0)
def pair(ms,a,b,y):
 key(ms,a,y,1);key(ms+100,b,y,1);key(ms+350,b,y,0);key(ms+400,a,y,0)
def local(ms,y,key,msg):send(ms,f'\\${y}-{key}',msg)
# Solo baseline, then shared-buffer independence: B steady while A changes.
tog(100,1);tog(1000,2)
cut(2000,2,1);pair(3000,3,6,1);local(4000,1,'dir_change','bang');local(4500,1,'playback_speed_dial','1')
tog(5500,1);tog(6000,1);send(6500,'1-buffer-select','sample 2');mod(7300,4,1)
send(8200,'1-buffer-select','sample 1');local(9000,1,'dir_change','bang');local(9200,1,'playback_speed_dial','2')
# A restarts steady; B changes, including a different-rate buffer.
local(10500,1,'stop_button','bang');send(10600,'1-loop-region','full');tog(10800,1)
cut(12000,5,2);mod(13000,6,2);local(14000,2,'dir_change','bang');local(14500,2,'playback_speed_dial','3')
tog(15500,2);tog(16000,2);send(16500,'2-buffer-select','sample 2');send(17800,'2-buffer-select','sample 1')
local(18500,2,'dir_change','bang');local(18700,2,'playback_speed_dial','2')
# Both: hold across focus changes, modifiers, rapid cuts, empty selection and Stop.
key(20000,2,1,1);key(20050,4,2,1);key(20100,6,1,1);key(20150,8,2,1)
key(20400,6,1,0);key(20450,4,2,0);key(20500,2,1,0);key(20550,8,2,0)
for j in range(8):cut(21000+j*40,j%6,1+j%2)
mod(21500,2,1);mod(21700,5,2)
local(22300,1,'dir_change','bang');local(22400,2,'playback_speed_dial','1')
key(23000,1,1,1);key(23100,3,1,1);tog(23200,2);key(23300,3,1,0);key(23400,1,1,0)
send(23800,'2-buffer-select','sample 3');tog(24000,2)
send(24500,'2-buffer-select','sample 2');local(24700,2,'stop_button','bang');tog(24900,2)
key(25500,1,1,1);key(25600,3,1,1);local(25700,1,'stop_button','bang');key(25800,3,1,0);key(25900,1,1,0);tog(26100,1)
send(26800,'1-quantizer','0');send(26800,'2-quantizer','0');send(26800,'global-transport','1')
cut(27000,4,1);cut(27020,2,2);tog(28000,1);tog(28100,2)
for ix,(ms,rc,msg) in enumerate(schedule):
 a=o(f'obj 20 {1000+ix*28} delay {ms}');b=o(f'msg 220 {1000+ix*28} {msg}');d=o(f'obj 460 {1000+ix*28} s {rc}');c(t,a,2);c(a,b);c(b,d)
Path('tests/two-lane-cut-audio.pd').write_text('#N canvas 100 100 1200 1100 12;\n'+'\n'.join(nodes+w)+'\n')
p=Path('docs/evidence/two-lane-cut');p.mkdir(exist_ok=True);(p/'schedule.json').write_text(json.dumps(schedule,indent=2)+'\n')
