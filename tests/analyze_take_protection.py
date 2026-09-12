"""Analyze retained native take-protection captures; no listening acceptance implied."""
from pathlib import Path
import json, shlex, sys
import numpy as np
from analyze_record_session import audio, longest_zero_run

def analyze(d):
    manifest=json.loads((d/'source.json').read_text());case=manifest['case']
    x,info=audio(d/'capture.wav');sr=info['rate']
    rows=[shlex.split(l.rstrip(';')) for l in (d/'events.txt').read_text().splitlines()]
    tagged=lambda name:[r for r in rows if r[1]==name]
    statuses=[(float(r[0]),' '.join(r[3:])) for r in tagged('mlr-clear-status')]
    def says(t,text):return any(abs(time-t)<1 and text in s for time,s in statuses)
    def ready(slot,t):
        r=[r for r in tagged('l_b_buffer_states') if r[2]==str(slot) and float(r[0])<=t]
        return bool(r and r[-1][-1]=='1')
    checks={'bounded_capture':abs(len(x)/sr-manifest['duration_ms']/1000)<.003,
            'eight_native_channels':info['channels']==8,'finite_all_samples':bool(np.isfinite(x).all())}
    # Includes transitions: actual master cannot exceed original weighted lane magnitudes.
    bound=.75*(.4*abs(x[:,2:4])+.3*abs(x[:,4:6]))
    checks['whole_capture_master_gain_bound']=bool(np.all(abs(x[:,:2])<=bound+1e-6))
    metrics={}
    if case=='guards':
        checks.update({
            'busy_Clear_and_Discard_refused':says(150,'finish recording') and says(160,'finish recording'),
            'repeated_Clear_never_confirms':says(1000,'unsaved') and says(1100,'unsaved') and ready(3,1200),
            'selection_cancels_discard':says(1500,'press Clear before Discard') and ready(3,1500),
            'navigation_cancels_discard':says(2000,'press Clear before Discard') and ready(3,2000),
            'expiry_cancels_discard':says(7200,'discard expired') and says(7300,'press Clear before Discard') and ready(3,7300),
            'deliberate_discard_clears_only_its_buffer':says(7600,'clearing audio') and not ready(3,7800) and ready(4,7800),
            'save_cancels_pending_discard':says(8200,'press Clear before Discard') and ready(4,8400),
            'saved_Clear_succeeds':says(8500,'clearing audio') and not ready(4,8600),
            'changed_bounds_cancel_discard':says(9600,'press Clear before Discard') and ready(4,9700),
            'storage_change_cancels_discard':says(10000,'finish recording') and says(10200,'press Clear before Discard') and ready(4,10300),
            'explicit_cancel':says(10600,'press Clear before Discard') and ready(4,10700),
            'later_fresh_discard_succeeds':says(10900,'clearing audio') and not ready(4,11100),
            'old_discard_cannot_clear_new_take':says(11700,'press Clear before Discard') and ready(4,11900),
        })
        # Each refused command leaves active playback running until a deliberate switch/clear.
        for a,b in [(1,1.29),(1.56,1.79),(1.81,2.19),(2.21,7.49)]:
            y=x[round(a*sr):round(b*sr),:2]
            checks[f'protected_audio_continues_{a}_{b}']=float(np.sqrt(np.mean(y*y)))>.01 and longest_zero_run(y)<64 and longest_zero_run(np.diff(y,axis=0))<64
        checks['protected_audio_keeps_advancing']=longest_zero_run(np.diff(x[round(2.21*sr):round(7.49*sr),:2],axis=0))<64
        checks['deliberate_Clear_stops_affected_playback']=bool(np.all(x[round(7.64*sr):,:6]==0))
    elif case in ('record','long'):
        name='roundtrip.wav' if case=='record' else 'long-take.wav'
        y,yi=audio(d/name);first=64 if case=='record' else 0
        startseconds=.4 if case=='record' else 2
        candidates=range(round(startseconds*sr)+first-128,round(startseconds*sr)+first+129)
        errors=[np.max(abs(x[n:n+64,6:8]-y[:64])) for n in candidates]
        start=list(candidates)[int(np.argmin(errors))]
        residual=float(np.max(abs(x[start:start+len(y),6:8]-y)))
        checks['exact_recorded_stereo_export']=residual==0
        checks['export_uses_written_bounds']=any(r[2]=='3' and r[-1]=='1' and int(float(r[4]))==first and int(float(r[5]))-first==len(y) for r in tagged('l_b_buffer_states'))
        checks['export_rate_matches_recording']=yi['rate']==sr and yi['channels']==2
        metrics.update({'export':yi,'export_input_frame_offset':start,'export_error':residual})
        if case=='record':
            checks['saved_take_clears']=says(6200,'clearing audio') and not ready(3,6300)
            checks['nonzero_first_index_preserved']=first==64 and abs(len(y)+64-1.3*sr)<64
        else:
            checks['sixty_second_written_take']=len(y)==sr*60
            growth=[int(float(r[4])) for r in tagged('l_b_storage_events') if r[2:4]==['3','grew']]
            checks['growth_to_sixty_seconds']=growth==[sr*n for n in [2,4,8,16,32,60]]
            metrics['growth_frames']=growth
            for a,b in [(1,7.9),(8.1,15.9),(16.1,23.9),(24.1,31.9),(32.1,39.9),(40.1,47.9),(48.1,55.9),(56.1,62.4)]:
                y=x[round(a*sr):round(b*sr)]
                checks[f'continuous_actual_mix_{a}_{b}']=float(np.max(abs(y[:,:2]-.75*(.4*y[:,2:4]+.3*y[:,4:6]))))<1e-6 and longest_zero_run(y[:,:2])<64
            checks['both_lanes_keep_changing_in_every_two_second_window']=all(float(np.std(x[round(t*sr):round((t+2)*sr),c]))>0.001 for t in range(1,60,2) for c in (2,4))
            checks['continuous_mix_including_every_view_and_audio_transition']=longest_zero_run(x[round(sr):round(62.4*sr),:2])<64
            checks['final_silence']=bool(np.all(x[round(62.55*sr):,:6]==0))
    elif case=='reopen':
        saved,si=audio(d/'roundtrip.wav');imported,ii=audio(d/'reimported.wav')
        checks['reimported_arrays_exact']=saved.shape==imported.shape and bool(np.array_equal(saved,imported))
        checks['imported_rate_and_duration_correct']=any(r[2]=='4' and r[3]=='1' and float(r[4])*1000==si['rate'] and int(float(r[7]))==len(saved) for r in tagged('s_b_buffer_states'))
        metrics.update({'saved':si,'array_readback':ii,'file_host_mismatch':si['rate']!=sr})
    if case in ('record','reopen'):
        y=x[round(3.04*sr):round(5.95*sr)]
        checks['recovered_audio_reaches_actual_master']=float(np.sqrt(np.mean(y[:,:2]**2)))>.01
        checks['no_held_sample_during_play']=longest_zero_run(np.diff(y[:,:2],axis=0))<64
        checks['actual_stereo_master_matches_player']=float(np.max(abs(y[:,:2]-.3*y[:,2:4])))<1e-6
        checks['no_block_zero_dropout_during_play']=longest_zero_run(y[:,:2])<64
        window=np.hanning(len(y))
        peaks=[float(np.fft.rfftfreq(len(y),1/sr)[np.argmax(abs(np.fft.rfft(y[:,c]*window)))]) for c in (0,1)]
        metrics['playback_peak_hz']=peaks
        checks['playback_pitch_preserves_file_rate']=all(abs(a-b)<2 for a,b in zip(peaks,[337,811]))
        checks['stereo_channels_remain_distinct']=float(np.sqrt(np.mean((y[:,0]-y[:,1])**2)))>.01
        checks['stopped_output_zero']=bool(np.all(x[round(6.04*sr):,:6]==0))
    return {'case':case,'audio':info,'checks':checks,'metrics':metrics,'clear_messages':statuses,
            'max_adjacent_steps':np.max(abs(np.diff(x[:,:2],axis=0)),axis=0).tolist(),
            'listening':'Pending; numerical results do not establish audibility or general background reliability.'}
if __name__=='__main__':
    r=analyze(Path(sys.argv[1]));print(json.dumps(r,indent=2));sys.exit(not all(r['checks'].values()))
