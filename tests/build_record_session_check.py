"""Build a silent, bounded native recording/playback check from production sources.

Run from the repo, then open /tmp/plugmlr-record-session/check.pd in plugdata.
The player copy is the production file verbatim plus message/tap instrumentation;
audio logic is unchanged. Actual production sample/live buffers and mixers load
from this checkout. No DAC, Grid, hardware input, installed files, or services.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--player-source',type=Path,default=ROOT/'sample_player_rebuild.pd',
                    help='Optional saved production revision for matched failure reproduction.')
args=parser.parse_args()
OUT=Path('/tmp/plugmlr-record-session')
OUT.mkdir(exist_ok=True)
# Pd resolves abstractions as it creates them. A late declare in the copied
# player cannot supply earlier objects; local symlinks resolve the real sources.
for dependency in ROOT.iterdir():
    if dependency.suffix in ('.pd', '.pd_lua', '.lua') and dependency.is_file():
        link=OUT/dependency.name
        if not link.exists():link.symlink_to(dependency)
        assert link.resolve()==dependency.resolve(),link
sys.path.insert(0,str(ROOT/'tests'))
from check_patch_connections import check

class Pd:
    def __init__(self): self.o=[]; self.c=[]
    def add(self,body): i=len(self.o);self.o.append('#X '+body+';');return i
    def link(self,a,b,out=0,into=0):self.c.append(f'#X connect {a} {out} {b} {into};')
    def text(self):return '\n'.join(self.o+self.c)+'\n'

# Append test controls/taps without changing any production object or connection.
source=args.player_source.read_text()
depth=0;count=0
for line in source.splitlines():
    if line.startswith('#N canvas'): depth+=1
    elif line.startswith('#X restore'):
        depth-=1
        if depth==1:count+=1
    elif depth==1 and line.startswith(('#X obj ','#X msg ','#X text ','#X floatatom ','#X symbolatom ','#X listbox ')):count+=1
p=Pd();o=p.add
r=o('obj 2100 4550 r record-session-player-\\$1')
route=o('obj 2100 4590 route play stop reverse speed slew record')
p.link(r,route)
for j,name in enumerate(['play_button','stop_button','dir_change','playback_speed_dial','rate_slew-duration-i','record_button_bang']):
    dest=o(f'obj {2100+j*180} 4640 s \\$0-{name}');p.link(route,dest,j)
rp=o('obj 2100 4700 r~ \\$0-vline_output_sig');sp=o('obj 2100 4740 s~ record-session-position-\\$1');p.link(rp,sp)
lb=o('obj 2100 4800 loadbang');f=o('obj 2100 4840 f \\$0');pr=o('obj 2100 4880 print record-session-player-id-\\$1');p.link(lb,f);p.link(f,pr)
tap_path=str(ROOT/'tests'/'bounded-player-capture').replace(' ','\\ ')
o(f'obj 2100 5100 {tap_path} \\$1 \\$0')
# Message taps expose the original boundary/direction handoff; they drive nothing.
for j,(tag,suffix) in enumerate([('target','-loop_target_index'),('direction','-playback_direction'),('detector-direction','_direction_for_expr_sig'),('entry','-loop_entry'),('rate','-samples_per_ms'),('boundary-entry','-buffer_and_playhead_update_and_exe'),('boundary-position','-boundary-current-position')]):
    r=o(f'obj {2100+j*220} 4950 r \\$0{suffix}')
    lp=o(f'obj {2100+j*220} 4990 list prepend {tag}')
    send=o(f'obj {2100+j*220} 5030 s record-session-trace-\\$1')
    if tag == 'boundary-position':
        precision=o(f'obj {2100+j*220} 4970 makefilename %.9f')
        p.link(r,precision);p.link(precision,lp)
    else:
        p.link(r,lp)
    p.link(lp,send)

extra='\n'.join(p.o)+'\n'
for line in p.c:
    f=line.rstrip(';').split(); extra+=f'#X connect {int(f[2])+count} {f[3]} {int(f[4])+count} {f[5]};\n'
(OUT/'observed-player.pd').write_text(source+'\n'+extra)
assert (OUT/'observed-player.pd').read_text().startswith(source+'\n')

# Known musical input at the tested host rate, and a one-second repeating lane.
for name,seconds in [('input',14.5),('lane',1)]:
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(ROOT/'DrumLoop.wav'),
                    '-t',str(seconds),'-ar','48000','-c:a','pcm_f32le',str(OUT/f'{name}.wav')],check=True)
for name in ('wave', 'constant'):
    shutil.copy2(ROOT/'tests'/'fixtures'/f'stop-{name}-48.wav', OUT/f'{name}.wav')

p=Pd();o=p.add;c=p.link
root= str(ROOT).replace(' ','\\ ')
o(f'obj 25 45 declare -path {root}')
o('text 25 15 Recording/session check. No DAC or Grid. Only run with other MLR/test patches closed.')
o(f'obj 25 85 {root}/sample-data 1');o(f'obj 25 125 {root}/sample-data 2')
o(f'obj 300 325 {root}/sample-data 3') # Present but empty, like the original app.
o(f'obj 25 165 {root}/live_buffer 1 \\$0');o(f'obj 25 205 {root}/live_buffer 2 \\$0')
o('obj 25 245 observed-player 1');o('obj 25 285 observed-player 2')
o(f'obj 25 325 {root}/record-takes-panel \\$0')
input_reader=o('obj 25 390 readsf~ 2');join=o('obj 25 435 snake~ in 2');inp=o('obj 25 475 s~ \\$0-record-input 2');c(input_reader,join);c(input_reader,join,1,1);c(join,inp)
lb=o('obj 510 40 loadbang');init=o('obj 510 80 f \\$0')
initmsg=o(f'msg 510 120 \\; \\$1-record-allowed 1 \\; 1-sample-path symbol {OUT}/lane.wav \\; 2-sample-path symbol {OUT}/lane.wav \\; audio-1-out 0.4 \\; audio-2-out 0.3 \\; project_bpm 120')
c(lb,init);c(init,initmsg)
# Named relay uses the actual production take-row Finish path.
fr=o('obj 510 175 r record-session-finish');fs=o('obj 510 215 s \\$0-record-finish');c(fr,fs)
vr=o('obj 820 175 r record-session-view');vs=o('obj 820 215 s \\$0-record-takes-open');c(vr,vs)
# Captures: actual input LR, actual players 1/2 LR, actual mixers summed at .75, logical positions.
cap=o('obj 25 760 writesf~ 10')
r=o('obj 25 520 r~ \\$0-record-input');un=o('obj 25 560 snake~ out 2');c(r,un);c(un,cap);c(un,cap,1,1)
for i in (1,2):
 r=o(f'obj {230*i} 390 r~ {i}-voice_audio');un=o(f'obj {230*i} 430 snake~ out 2');c(r,un);c(un,cap,0,i*2);c(un,cap,1,i*2+1)
mx1=o(f'obj 700 390 {root}/mixer 1');mx2=o(f'obj 920 390 {root}/mixer 2')
left=o('obj 700 440 *~ 0.75');right=o('obj 920 440 *~ 0.75')
for m in (mx1,mx2):c(m,left);c(m,right,1)
c(left,cap,0,6);c(right,cap,0,7)
for i in (1,2):
 r=o(f'obj {650+i*180} 500 r~ record-session-position-{i}');c(r,cap,0,7+i)
# Capture start always arms its independent watchdog before opening any file.
r=o('obj 510 275 r record-session-check');route=o('obj 510 315 route run dsp zero boundary turns constant stop');c(r,route)
start=o('obj 510 610 t s b b b b');timer=o('obj 1050 840 timer');clear=o('msg 920 650 clear');events=o('obj 1050 1080 text define \\$0-events');watch=o('obj 820 700 delay 16000')
c(start,clear,4);c(clear,events);c(start,timer,3);c(start,watch,2)
sourceplay=o(f'msg 650 740 open {OUT}/input.wav \\, 1');c(start,sourceplay,1);c(sourceplay,input_reader)
openwrite=o(f'msg 650 780 open -bytes 4 {OUT}/capture.wav \\, start');c(start,openwrite,1);c(openwrite,cap)
readertaps=o(f'msg 1050 610 \\; 1-test-capture start {OUT}/readers1.wav 14000 \\; 2-test-capture start {OUT}/readers2.wav 14000');c(start,readertaps,1)
read=o('msg 510 830 read \\$1 \\, bang');ql=o('obj 510 870 qlist');c(start,read);c(read,ql)
for j,name in enumerate(['run','dsp','zero','boundary','turns','constant']):
 msg=o(f'msg {510+j*175} 550 symbol {OUT}/{name}.txt');c(route,msg,j);c(msg,start)
finishr=o('obj 25 820 r record-session-done');fin=o('obj 25 860 t b b b b');c(finishr,fin);c(watch,fin);c(route,fin,6)
stop=o('msg 360 900 stop');c(fin,stop,3);c(stop,cap);c(stop,input_reader);c(stop,watch)
rewind=o('msg 250 900 rewind');c(fin,rewind,2);c(rewind,ql)
allstop=o('msg 150 940 \\; 1_l_b_record stop \\; 2_l_b_record stop \\; record-session-player-1 stop \\; record-session-player-2 stop \\; 1-test-capture stop \\; 2-test-capture stop');c(fin,allstop,1)
d=o('obj 25 900 delay 20');c(fin,d)
for i in (1,2):
 msg=o(f'msg {25+(i-1)*450} 990 write -wave -bytes 4 {OUT}/live{i}.wav 0-live_buffer_{i} 1-live_buffer_{i}');sf=o(f'obj {25+(i-1)*450} 1030 soundfiler');pr=o(f'obj {25+(i-1)*450} 1070 print record-session-export-{i}');c(d,msg);c(msg,sf);c(sf,pr)
write=o(f'msg 25 1120 write {OUT}/events.txt');done=o('obj 25 1160 print record-session-finished');c(d,write);c(write,events);c(d,done)
log=o('obj 1050 800 r \\$0-log');t=o('obj 1050 880 t l b');prepend=o('obj 1050 920 list prepend');insert=o('obj 1050 960 text insert \\$0-events 1e+09');c(log,t);c(t,timer,1,1);c(timer,prepend,0,1);c(t,prepend);c(prepend,insert)
# Full progress is logged; the console prints only discrete state/storage/error messages.
for j,(receiver,tag) in enumerate([('l_b_record_states','record'),('l_b_record_errors','error'),('l_b_buffer_states','buffer'),('l_b_storage_events','storage'),('\\$0-record-progress','progress'),('1-grid-position','position1'),('2-grid-position','position2'),('1-grid-playing','playing1'),('2-grid-playing','playing2'),('1-grid-last','end1'),('record-session-trace-1','trace1'),('record-session-trace-2','trace2')]):
 r=o(f'obj {25+(j%3)*360} {1250+(j//3)*125} r {receiver}');lp=o(f'obj {25+(j%3)*360} {1290+(j//3)*125} list prepend {tag}');ls=o(f'obj {25+(j%3)*360} {1330+(j//3)*125} s \\$0-log');c(r,lp);c(lp,ls)
 if tag in ['record','error','storage']:
  pr=o(f'obj {25+(j%3)*360} {1350+(j//3)*125} print record-session-{tag}');c(r,pr)
(OUT/'check.pd').write_text('#N canvas 50 50 1250 900 12;\n'+p.text())

def score(events,path):
    last=0;lines=[]
    for ms,recv,msg in sorted(events,key=lambda e:e[0]):
        lines.append(f'{ms-last:.6f} {recv} {msg};');last=ms
    path.write_text('\n'.join(lines)+'\n')
setup=[(0,'record-session-player-1','stop'),(0,'record-session-player-2','stop'),(0,'1_l_b_delete_buffer','bang'),(0,'2_l_b_delete_buffer','bang'),(0,'record-session-player-1','speed 2'),(0,'record-session-player-2','speed 2'),(0,'1-buffer-select','live 1'),(0,'2-buffer-select','sample 2'),(30,'1_l_b_length','dynamic'),(30,'2_l_b_length','seconds 4'),(100,'record-session-player-2','play'),(14000,'record-session-done','bang')]
run=setup+[(1300,'record-session-player-1','record'),(1500,'1-buffer-select','sample 1'),(1600,'record-session-player-1','reverse'),(1700,'record-session-player-1','speed 1'),(1800,'2_l_b_record','start'),(2200,'1_l_b_length','seconds 0.4'),(4400,'record-session-finish','1'),(4600,'record-session-finish','2'),(4700,'record-session-player-1','reverse'),(4700,'record-session-player-1','speed 2'),(4800,'1-buffer-select','live 1'),(4900,'record-session-player-1','play'),(8000,'record-session-player-1','reverse'),(9000,'record-session-player-1','speed 1'),(10000,'record-session-player-1','speed 3'),(12500,'record-session-player-1','stop'),(12500,'record-session-player-2','stop')]
boundary=run
run=[(8300 if ms==8000 else ms,recv,msg) for ms,recv,msg in run]
dsp=setup+[(1300,'1_l_b_record','start'),(2500,'pd','dsp 0'),(3000,'pd','dsp 1'),(3200,'1_l_b_record','get'),(12500,'record-session-player-2','stop')]
zero=setup+[(1300,'1_l_b_record','start'),(1300,'1_l_b_record','stop'),(1301,'1_l_b_record','start'),(1320,'1_l_b_record','start'),(2420,'record-session-finish','1'),(12500,'record-session-player-2','stop')]
# Boundary regression score. The existing quarter-second stereo fixtures let
# commanded turns coincide with both ends, including rapid turns within a block.
# Every chapter starts from a completed Stop; lane B stays a steady reference.
def turn_score(signal):
    events=[(0,'record-session-player-1','stop'),(0,'record-session-player-2','stop'),
            (20,'1-sample-path',f'symbol {OUT}/{signal}.wav'),
            (20,'2-sample-path',f'symbol {OUT}/lane.wav'),
            (30,'1-buffer-select','sample 1'),(30,'2-buffer-select','sample 2'),
            (30,'1-quantizer','1'),(30,'record-session-player-2','speed 2'),
            (100,'record-session-player-2','play'),
            (12500,'record-session-player-1','stop'),
            (12500,'record-session-player-2','stop'),(14000,'record-session-done','bang')]
    def send(t,msg):events.append((t,'record-session-player-1',msg))
    def begin(t,rate=2,reverse=False):
        send(t,'stop');send(t+20,'slew 0');send(t+20,f'speed {rate}')
        events.append((t+30,'1-loop-region','full'))
        if reverse:send(t+40,'reverse')
        send(t+100,'play')
    begin(0);send(350,'reverse')                       # end -> reverse
    begin(1000,reverse=True);send(1350,'reverse')      # start -> forward
    begin(2000)
    for offset in (0,.2,.4,.6,.8):send(2350+offset,'reverse')
    begin(3000,3);send(3225,'reverse')                 # 2x endpoint
    begin(4000,4);send(4162.5,'reverse')               # 4x endpoint
    begin(5000)
    events.append((5350,'row_1','9'));send(5350,'reverse') # pending cut owns jump
    begin(6000);send(6350,'play');send(6600,'play')     # endpoint Pause / Resume
    send(6800,'reverse')
    begin(7000);send(7200,'slew 400');send(7200,'speed 4')
    send(7350,'reverse');send(7450,'speed 0')           # interrupt speed glide
    begin(8000);send(8350,'reverse');send(8350.2,'stop');send(8351,'play')
    begin(9000)
    events.append((9300,'1-loop-region','0.05 0.175'))
    send(9426,'reverse');send(9426.2,'reverse');send(9426.4,'reverse')
    send(10000,'stop');events.append((10020,'1-buffer-select','sample 3'))
    send(10100,'play');send(10200,'reverse')           # empty stays silent
    events.append((10500,'1-buffer-select','sample 1'))
    send(10600,'play')
    return events
turns=turn_score('wave');constant=turn_score('constant')
scores={'run':run,'dsp':dsp,'zero':zero,'boundary':boundary,'turns':turns,'constant':constant}
for name,data in scores.items():score(data,OUT/f'{name}.txt')
checks=[check(OUT/f) for f in ('observed-player.pd','check.pd')]
assert not any(c['errors'] for c in checks),checks
manifest={'production_player_sha256':hashlib.sha256(source.encode()).hexdigest(),'production_root_objects':count,'instrumentation_added_only':True,'files':checks,'scores':scores,'fixture':'check.pd','scope':'Actual two player/mixer components with common .75 master multiplier. No DAC, full application, Grid or device-loopback acceptance.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(OUT/'check.pd')
