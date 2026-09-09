"""Numerical checks on writesf~ captures from the installed Mac plugdata.
Never synthesizes the engine output. Needs NumPy; raw captures are gitignored.
"""
import hashlib, json, struct, wave
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent

def read_float_wav(path):
 b=path.read_bytes(); off=12;fmt=data=None
 while off+8 <= len(b):
  tag,n=struct.unpack_from('<4sI',b,off);chunk=b[off+8:off+8+n]
  if tag==b'fmt ':fmt=chunk
  if tag==b'data':data=chunk
  off+=8+n+(n%2)
 code,ch,sr=struct.unpack_from('<HHI',fmt)
 assert code in (3,65534) and struct.unpack_from('<H',fmt,14)[0]==32
 return sr,np.frombuffer(data,dtype='<f4').reshape(-1,ch).astype(float)

def frequency(x,sr):
 n=len(x);amp=np.abs(np.fft.rfft((x-x.mean())*np.hanning(n)))
 k=int(np.argmax(amp[1:])+1)
 # Parabolic interpolation in log magnitude.
 y=np.log(np.maximum(amp[k-1:k+2],1e-20));delta=.5*(y[0]-y[2])/(y[0]-2*y[1]+y[2])
 return (k+delta)*sr/n

def longest(mask):
 idx=np.flatnonzero(np.diff(np.r_[False,mask,False]));return int(max(idx[1::2]-idx[::2],default=0))

def analyze(label,expected_sr):
 path=ROOT/'evidence'/f'{label}-full.wav';sr,x=read_float_wav(path)
 results={'capture_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'host_rate':sr,'frames':len(x),'channels':x.shape[1]}
 checks={}
 def check(name,ok,detail): checks[name]={'pass':bool(ok),'measurement':detail}
 def segment(a,b,ch=0):return x[round(a*sr):round(b*sr),ch]
 check('host_rate',sr==expected_sr,sr)
 check('duration',abs(len(x)/sr-11)<512/sr,len(x)/sr)
 check('finite',np.isfinite(x).all(),int((~np.isfinite(x)).sum()))
 check('bounded_peak',np.abs(x).max()<=.251,float(np.abs(x).max()))
 difference=float(np.abs(x[:round(9.39*sr),2:4]-x[:round(9.39*sr),6:8]).max())
 check('B_matches_independent_instance_despite_A_commands',difference<1e-7,difference)
 difference=float(np.abs(x[round(.15*sr):round(1.09*sr),:2]-x[round(.15*sr):round(1.09*sr),8:10]).max())
 check('A_matches_other_A_before_changes',difference<1e-7,difference)
 for name,a,b,hz in [('forward',.3,.9,220),('reverse',1.3,1.9,220),('slow',2.3,2.9,110),('fast',3.3,3.7,440),('max_forward',3.82,4.05,880),('max_reverse',4.15,4.35,880)]:
  f=frequency(segment(a,b),sr);check(name+'_frequency',abs(f-hz)/hz<.0002,{'Hz':f,'expected_Hz':hz})
 left=frequency(segment(.3,.9,0),sr);right=frequency(segment(.3,.9,1),sr)
 ratio=float(np.sqrt(np.mean(segment(.3,.9,1)**2)/np.mean(segment(.3,.9,0)**2)))
 check('stereo_order_and_ratio',abs(left-220)<.5 and abs(right-330)<.5 and abs(ratio-.5)<.002,{'L_Hz':left,'R_Hz':right,'R_over_L_rms':ratio})
 cpeak=float(np.abs(segment(.3,.9,4)).max());check('third_head_gain',abs(cpeak-.1)<.001,cpeak)
 bpeak=float(np.abs(segment(.3,9.3,2)).max());check('B_gain_unchanged',abs(bpeak-.15)<.001,bpeak)
 check('independent_gain_change',abs(float(np.abs(segment(5.15,5.25)).max())-.125)<.001,float(np.abs(segment(5.15,5.25)).max()))
 check('rate_zero_silent',np.abs(segment(4.43,4.88)).max()<1e-7,float(np.abs(segment(4.43,4.88)).max()))
 check('explicit_stop_silent',np.abs(segment(7.12,7.29)).max()<1e-7,float(np.abs(segment(7.12,7.29)).max()))
 check('one_shot_forward_ends',np.abs(segment(8.02,8.35)).max()<1e-7,float(np.abs(segment(8.02,8.35)).max()))
 check('one_shot_reverse_ends',np.abs(segment(8.52,8.60)).max()<1e-7,float(np.abs(segment(8.52,8.60)).max()))
 check('audio_survives_failed_replacements',np.abs(segment(9.78,9.84)).max()>.22,float(np.abs(segment(9.78,9.84)).max()))
 check('final_stop_silent',np.abs(x[round(10.62*sr):]).max()<1e-7,float(np.abs(x[round(10.62*sr):]).max()))
 stress=x[round(6.49*sr):round(6.63*sr),:2]
 delta=float(np.abs(np.diff(stress,axis=0)).max())
 check('rapid_transition_step_bound',delta<.06,delta)
 check('rapid_commands_recover_audio',np.sqrt(np.mean(segment(6.65,7.05)**2))>.1,float(np.sqrt(np.mean(segment(6.65,7.05)**2))))
 # Untouched B must never acquire a multi-sample hole during any A transition.
 quiet=np.max(np.abs(x[round(.15*sr):round(9.39*sr),2:4]),axis=1)<1e-5
 hole=longest(quiet);check('untouched_B_no_dropout',hole<=4,{'longest_near_zero_frames':hole})
 transition_checks={}
 for ms in [2100,3100,4100,4800,5100,6100,6300,6400,6700,8800,8820]:
  t=ms/1000-1;xx=x[round((t-.005)*sr):round((t+.02)*sr),:2]
  step=float(np.abs(np.diff(xx,axis=0)).max());hole=longest(np.max(np.abs(xx),axis=1)<1e-5)
  transition_checks[str(ms)]={'max_sample_step':step,'near_zero_frames':hole}
 check('individual_transition_steps_and_dropouts',all(v['max_sample_step']<.06 and v['near_zero_frames']<=4 for v in transition_checks.values()),transition_checks)
 results['global_max_sample_step']=float(np.abs(np.diff(x,axis=0)).max())
 results['checks']=checks
 lines=(ROOT/'evidence'/f'{label}-states.txt').read_text().splitlines()
 errors=[l for l in lines if ' error ' in l];loads=[l for l in lines if ' loaded ' in l];ended=[l for l in lines if ' ended ' in l]
 check('sole_rate_zero_user_blocks_replacement',any(l.startswith('11450 error') and 'buffer-in-use' in l for l in errors),[l for l in errors if l.startswith('11450')])
 results['errors']=errors;results['loads']=loads;results['ended']=ended
 check('DSP_paused_stop_keeps_buffer_locked',any(l.startswith('12014 error') and 'buffer-in-use' in l for l in errors),[l for l in errors if l.startswith('12014')])
 check('DSP_resumed_stop_releases_buffer',any(l.startswith('12100 loaded') for l in loads),[l for l in loads if l.startswith('12100')])
 check('expected_loads',len(loads)==4,loads)
 check('replacement_locked_during_use_and_stop_fade',any(l.startswith('5450 error') and 'buffer-in-use' in l for l in errors) and any(l.startswith('10401 error') and 'buffer-in-use' in l for l in errors),errors)
 check('invalid_commands_rejected',sum(7000<=float(l.split()[0])<=7100 for l in errors)==12,[l for l in errors if 7000<=float(l.split()[0])<=7100])
 check('missing_and_empty_rejected',any(l.startswith('200 error') for l in errors) and any(l.startswith('210 error') for l in errors) and any(l.startswith('250 error') for l in errors),errors[:3])
 check('failed_replacements_leave_version_one',any(l.startswith('10800 buffer') and ' 1 1;' in l for l in lines),[l for l in lines if l.startswith('10800 buffer')])
 # Reports establish direction and region independently of spectral magnitude.
 states=[]
 for l in lines:
  a=l.rstrip(';').split()
  if len(a)==14 and a[1]=='state' and a[3]=='A' and a[2].endswith('-main'):
   states.append([float(a[0]),*[float(v) for v in a[5:]]])
 for name,a,b,sign in [('forward',1400,1800,1),('reverse',2400,2800,-1)]:
  ss=[s for s in states if a<=s[0]<=b]
  slopes=np.diff([s[2] for s in ss]);check(name+'_position_direction',len(slopes)>5 and (slopes*sign>0).all(),[s[2] for s in ss])
 for name,t,boundary in [('forward',9100,.8),('reverse',9550,.3)]:
  ss=[s for s in states if t<=s[0]<=t+40]
  check(name+'_holds_completed_boundary',bool(ss) and all(s[1]==0 and abs(s[2]-boundary)<1e-5 for s in ss),ss)
 ss=[s for s in states if 9660<=s[0]<=9700]
 check('reverse_restart_from_completed_boundary',bool(ss) and all(s[1]==1 and .65<s[2]<.8 for s in ss),ss)
 ss=[s for s in states if 7150<=s[0]<=7400]
 check('invalid_inputs_preserve_controls',bool(ss) and all(s[1]==1 and s[3]==1 and abs(s[4]-.3)<1e-6 and abs(s[5]-.8)<1e-6 and s[6]==1 and s[7]==1 for s in ss),ss)
 ss=[s for s in states if 10020<=s[0]<=10380]
 check('short_loop_bounds',bool(ss) and all(.5<=s[2]<=.52 for s in ss),[s[2] for s in ss])
 results['all_pass']=all(c['pass'] for c in checks.values())
 # Representative component audio retained as PCM16; full float capture hash above.
 for name,a,b,pair in [('A-transitions',6.45,7.05,0),('B-independent',6.45,7.05,1),('C-reverse',.25,1.0,2)]:
  samples=x[round(a*sr):round(b*sr),2*pair:2*pair+2]
  with wave.open(str(ROOT/'evidence'/f'{label}-{name}.wav'),'wb') as w:
   w.setparams((2,2,sr,0,'NONE','not compressed'));w.writeframes(np.round(np.clip(samples,-1,1)*32767).astype('<i2').tobytes())
 out=ROOT/'evidence'/f'{label}-checks.json';out.write_text(json.dumps(results,indent=2)+'\n')
 print(label, 'PASS' if results['all_pass'] else 'FAIL', {k:v['measurement'] for k,v in checks.items() if not v['pass']})
 return results['all_pass']
def analyze_precision():
 path=ROOT/'evidence/precision-full.wav';sr,x=read_float_wav(path)
 segment=x[round(.4*sr):round(1.8*sr)]
 hz=[frequency(segment[:,i],sr) for i in (0,1)]
 checks={'host_48000':sr==48000,'finite':bool(np.isfinite(x).all()),
         'left_110_Hz':bool(abs(hz[0]-110)/110<.0002),
         'right_165_Hz':bool(abs(hz[1]-165)/165<.0002),
         'audible':bool(np.max(np.abs(segment))>.24)}
 result={'checks':checks,'all_pass':all(checks.values()),'host_rate':sr,
         'file_rate':44100,'region_seconds':[9,11],'seek_seconds':10,
         'rate':.5,'measured_Hz':hz,
         'capture_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 (ROOT/'evidence/precision-checks.json').write_text(json.dumps(result,indent=2)+'\n')
 with wave.open(str(ROOT/'evidence/precision-excerpt.wav'),'wb') as w:
  w.setparams((2,2,sr,0,'NONE','not compressed'))
  w.writeframes(np.round(np.clip(segment,-1,1)*32767).astype('<i2').tobytes())
 print('precision', 'PASS' if result['all_pass'] else 'FAIL', hz)
 return result['all_pass']

if __name__=='__main__':
 import sys
 labels=sys.argv[1:] or ['48k','44k','mismatch','precision']
 ok=[analyze_precision() if l=='precision' else analyze(l,44100 if l=='44k' else 48000) for l in labels]
 raise SystemExit(0 if all(ok) else 1)
