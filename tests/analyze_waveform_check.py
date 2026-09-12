"""Check native audio, exported take, peak envelopes and message readbacks.
Usage: python tests/analyze_waveform_check.py DIRECTORY
No listening or general real-time performance acceptance is inferred.
"""
from pathlib import Path
import json,shlex,sys
import numpy as np
from analyze_record_session import audio,longest_zero_run
from analyze_handoff import read_pcm

def analyze(d):
 x,info=audio(d/'capture.wav');sr=info['rate'];take,ti=audio(d/'saved take.wav')
 rows=[shlex.split(l.rstrip(';')) for l in (d/'events.txt').read_text().splitlines()]
 tagged=lambda tag:[r for r in rows if r[1]==tag]
 checks={'bounded_capture':13.99<=len(x)/sr<=14.001,'eight_channels':info['channels']==8,
         'finite_all_audio':bool(np.isfinite(x).all() and np.isfinite(take).all()),
         'export_written_length':any(r[2]=='3' and r[-1]=='1' and int(float(r[5]))-int(float(r[4]))==len(take) for r in tagged('l_b_buffer_states')),
         'record_stop_within_one_pd_block':abs(len(take)-round(sr*1.3))<64,'export_stereo_rate':ti['channels']==2 and ti['rate']==sr,
         'refused_playing_no_file':not (d/'rejected-playing.wav').exists(),
         'refused_empty_no_file':not (d/'rejected-empty.wav').exists()}
 statuses=[' '.join(r[3:]) for r in tagged('mlr-save-status')]
 checks['save_feedback']=all(any(term in s for s in statuses) for term in ['Stop all players','Saved Live 3','buffer is empty','Save incomplete'])
 # Match recorded input, not a separately synthesized mathematical source.
 starts=range(round(1.99*sr),round(2.02*sr))
 errors=[np.max(abs(x[n:n+32,6:8]-take[:32])) for n in starts]
 start=list(starts)[int(np.argmin(errors))]
 copy_error=float(np.max(abs(x[start:start+len(take),6:8]-take)))
 checks['export_matches_actual_stereo_input']=copy_error<1e-7
 # Capacity was three seconds; the written take must exclude the unwritten tail.
 checks['retained_capacity_larger_than_export']=any(r[2:]==['3','ready',str(sr*3)] for r in tagged('l_b_storage_events'))
 checks['silence_after_final_stop']=bool(np.all(x[round(12.53*sr):round(13.99*sr),:6]==0))
 bound=.75*(.4*abs(x[:,2:4])+.3*abs(x[:,4:6]))
 checks['whole_capture_gain_bound']=bool(np.all(abs(x[:,:2])<=bound+1e-6))
 residual=[]
 for a,b in [(.4,1.7),(2.05,3.29),(3.56,3.98),(4.25,4.65),(5.2,6.9),(11.1,12.4)]:
  y=x[round(a*sr):round(b*sr)]
  err=float(np.max(abs(y[:,:2]-.75*(.4*y[:,2:4]+.3*y[:,4:6]))))
  residual.append({'start':a,'end':b,'max_error':err})
 checks['expected_mix_during_display_and_recording']=max(r['max_error'] for r in residual)<1e-6
 checks['lane2_continues_through_browsing_recording_and_display']=all(r[2]=='1' for r in tagged('2-grid-playing') if 300<=float(r[0])<7000)
 checks['browse_next_and_previous']=any(float(r[0])==3520 and r[2:]==['set','2'] for r in tagged('1-ui-slot')) and any(float(r[0])==4720 and r[2:]==['set','1'] for r in tagged('1-ui-slot'))
 checks['empty_replacement_clears_identity']=any(float(r[0])==8720 and r[-2:]==['Empty','Empty'] for r in tagged('sample_buffer_2-view-info'))
 checks['replacement_name_and_rate_updated']=any(float(r[0])==10220 and r[-2:]==['input.wav','Loaded'] and r[6]=='44100' for r in tagged('sample_buffer_2-view-info'))
 # Each displayed bin covers every source frame, independently recomputed here.
 peak_checks=[]
 for row in tagged('waveform-peaks-reply'):
  if row[2]!='peaks':continue
  key,first,end=row[3],int(row[4]),int(row[5]);observed=np.array(row[6:],float).reshape(400,4)
  source_path=d/'input.wav'
  if not source_path.exists():source_path=Path(__file__).resolve().parents[1]/'DrumLoop.wav'
  path={'sample_buffer_1':source_path,'sample_buffer_2':d/'short stereo.wav','live_buffer_3':d/'saved take.wav'}[key]
  y = audio(path)[0] if key=='live_buffer_3' else read_pcm(path)[0]
  expected=[]
  for bin in range(400):
   a=first+int(np.ceil(bin*(end-first)/400));b=first+int(np.ceil((bin+1)*(end-first)/400));z=y[a:b]
   expected.append([z[:,0].min(),z[:,0].max(),z[:,1].min(),z[:,1].max()] if len(z) else [0,0,0,0])
  err=float(np.max(abs(observed-np.array(expected))));peak_checks.append({'buffer':key,'max_error':err})
 checks['all_three_stereo_peak_caches_match_source']=len(peak_checks)==3 and max(p['max_error'] for p in peak_checks)<1e-6
 checks['useful_output']=float(np.sqrt(np.mean(x[round(.4*sr):round(6.9*sr),:2]**2)))>.01
 zero=longest_zero_run(x[round(.4*sr):round(6.9*sr),:2])
 checks['no_full_block_exact_zero_dropout_while_lane2_runs']=zero<64
 return {'audio':info,'export':ti,'checks':checks,'save_messages':statuses,'export_input_frame_offset':start,
         'export_max_error_to_actual_input':copy_error,'mix_windows':residual,'peak_cache_checks':peak_checks,
         'longest_running_zero_frames':zero,'max_adjacent_steps':np.max(abs(np.diff(x[:,:2],axis=0)),axis=0).tolist(),
         'listening':'Not performed; user listening remains open.',
         'limits':'A short native fixture; no universal click-free or arbitrary-duration performance claim. Soundfiler save is synchronous and deliberately refused during active instrument playback/recording.'}
if __name__=='__main__':
 result=analyze(Path(sys.argv[1]));print(json.dumps(result,indent=2));sys.exit(not all(result['checks'].values()))
