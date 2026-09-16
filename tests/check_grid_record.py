"""Native writer/readback and retained stereo sample checks. Requires numpy."""
from pathlib import Path
import json,runpy,sys,struct,subprocess,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];P=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/plugmlr-grid-record')
sys.argv=[str(ROOT/'tests/check_grid_buffer.py'),str(P)]
runpy.run_path(sys.argv[0],run_name='__main__')
m=json.loads((P/'source.json').read_text());E=[]
for line in (P/'events.txt').read_text().splitlines():
 a=line.rstrip(';').split();E.append((float(a[0]),a[1:]))
def wr(slot,field):return [(t,a[3]) for t,a in E if t>=18800 and a[:3]==['writer',str(slot),field]]
def led(row,t):return int([a[2] for tt,a in E if tt<=t and a[:2]==['record-led',str(row)]][-1])
results=[]
for slot,start,finish,duration in [(901,19010,19310,.3),(902,19550,19750,.2),(903,19830,19900,.07),(904,20030,20230,.2)]:
 flags=wr(slot,'recording');assert len(flags)==2 and flags[0]==(start,'1') and flags[1][1]=='0' and finish<=flags[1][0]<=finish+6,flags
 frames=int(wr(slot,'last_index')[-1][1]);raw=(P/f'take{slot}.wav').read_bytes();pos=12
 while pos+8<=len(raw):
  tag=raw[pos:pos+4];size=struct.unpack_from('<I',raw,pos+4)[0];data=raw[pos+8:pos+8+size];pos+=8+size+(size%2)
  if tag==b'fmt ':fmt=struct.unpack_from('<HHIIHH',data)
  if tag==b'data':audio=np.frombuffer(data,dtype='<f4').reshape(-1,2)
 _,channels,rate,_,_,bits=fmt;assert channels==2 and bits==32 and rate==48000
 assert abs(frames-duration*rate)<=64 and np.isfinite(audio).all()
 if slot==902:assert frames==9600 and len(audio)==9600
 assert np.max(abs(audio[frames:]),initial=0)==0 # Unwritten capacity stays silent.
 residual=[];amplitudes=[]
 for ch,(hz,amp) in enumerate([(220,.1),(330,.2)]):
  x=np.arange(frames)*2*np.pi*hz/rate;basis=np.column_stack([np.cos(x),np.sin(x)])
  fit=np.linalg.lstsq(basis,audio[:frames,ch],rcond=None)[0];error=np.max(abs(audio[:frames,ch]-basis@fit));amplitude=float(np.linalg.norm(fit))
  assert abs(amplitude-amp)<2e-5 and error<2e-5,(slot,ch,amplitude,error)
  residual.append(float(error));amplitudes.append(amplitude)
 results.append(dict(slot=slot,rate=rate,frames=frames,capacity=len(audio),amplitude=amplitudes,max_sine_residual=residual))
assert wr(901,'record_error')==[(18900,'Arm_recording_input_first'),(19440,'Clear_live_buffer_first')]
for t,level in [(18901,3),(19011,15),(19141,15),(19320,0),(19551,15),(19760,3),(19831,15),(19910,3),(20101,15),(20240,3)]:assert led(901,t)==level,(t,led(901,t))
assert led(902,19011)==7 and led(902,19320)==3
# Actual page renderer shows owned take even after selecting an imported sample.
for t,want in [(19011,15),(19141,15),(19320,0),(19760,3),(20121,15)]:
 rows=[a for tt,a in E if tt<=t and a[:4]==['led','/monome/grid/led/level/row','0','1']]
 assert int(rows[-1][4])==want,(t,rows[-1])
allowed={'grid-cut-control.pd','grid-cut-keys.pd_lua','grid-page-leds.pd_lua'};protected=[]
for name in subprocess.check_output(['git','ls-tree','--name-only',m['record_base']],cwd=ROOT,text=True).splitlines():
 if name.endswith(('.pd','.pd_lua')) and name not in allowed:
  assert (ROOT/name).read_bytes()==subprocess.check_output(['git','show',m['record_base']+':'+name],cwd=ROOT),name
  protected.append(name)
for name,h in m['production_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
r=dict(passed=True,takes=results,unchanged_components=protected,checks=['Remembered target after sample selection','Shared buffer refusal','Input/content refusal','Selection handoff refusal','Automatic fixed completion','External Finish releases ownership','Duplicate held key does not stop','Detach/reconnect preserves active take','Actual stereo writer audio, order, level, continuity and unwritten tail','115 pattern and 17 buffer request regressions'],limitations=['48k standalone only in this slice','No physical Grid or hardware-input listening acceptance','No overdub, resampling, record quantization or new save workflow'])
(P/'record-analysis.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS four actual stereo takes; ownership/readback; original engine unchanged')
