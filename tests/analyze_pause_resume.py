"""Numerical checks of actual native Pause/Resume captures, not a DSP model.

Usage: python3 tests/analyze_pause_resume.py docs/evidence/pause-resume
Requires NumPy and ffmpeg. Private musical capture checks are optional.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from analyze_stop_restart import load, audio_case, events, starts, RESTARTS, RATE, GAIN
from analyze_instant_reverse import longest_silence

# Relative to bounded recording start, leaving margin around command transitions.
ACTIVE = [(.08,.20),(.56,.70),(1.08,1.20),(1.29,1.50),(1.59,1.80),
          (1.89,2.10),(2.38,2.48),(2.54,2.75),(3.14,3.28),
          (3.65,3.85),(4.49,4.58),(5.20,5.45)]
PAUSED = [(.26,.50),(.81,1.02),(2.19,2.32),(4.80,5.10)]
SILENT = PAUSED + [(2.83,3.05),(3.39,3.55),(3.95,4.28),(5.74,6.95)]


def span(x,a,b):
    return x[round(a*RATE):round(b*RATE)]


def analyze(folder):
    cases, checks = {}, {}
    for name in ['baseline-constant','baseline-wave','candidate-constant','candidate-wave']:
        x=load(folder,name+'-player-mixer-48',6)
        r=load(folder,name+'-readers-48',10)
        windows=[]
        for a,b in ACTIVE:
            z=span(x,a,b)[:,2:6]
            windows.append({'seconds':[a,b], 'longest_silent_run_frames':longest_silence(z[:,:2]),
                            'mixer_gain_error':float(abs(z[:,2:]-GAIN*z[:,:2]).max())})
        silent=[{'seconds':[a,b], 'max_player_mixer':abs(span(x,a,b)[:,2:6]).max(axis=0).tolist()} for a,b in SILENT]
        holds=[{'seconds':[a,b], 'master_range_frames':float(np.ptp(span(r,a,b)[:,2])),
                'master_position':float(span(r,a,b)[0,2]),
                'dsp_flag_max':span(r,a,b)[:,8:10].max(axis=0).tolist()} for a,b in PAUSED]
        off=[]
        for g,flag in [(5,8),(7,9)]:
            ix=np.flatnonzero((r[:-1,flag]>.5)&(r[1:,flag]<.5))
            off.append({'count':len(ix),'nonzero_gain_before_off':int((abs(r[ix,g])>1e-4).sum())})
        resumes=[]
        for pause_a,resume_ms,rate in [(.26,533,1),(.81,1033,-2),(2.19,2350,-2),(4.80,5150,-.25)]:
            saved=r[round(pause_a*RATE),2]
            a=round((resume_ms-4)*48);b=round((resume_ms+8)*48)
            ix=np.flatnonzero(abs(r[a:b,2]-saved)>1e-3)
            first=a+int(ix[0]) if len(ix) else a
            resumes.append({'command_ms':resume_ms,'saved_frame':float(saved),'first_moving_frame':float(r[first,2]),
                            'first_move_ms':first/48,'first_step_frames':float(r[first,2]-saved),
                            'signed_slope':float(np.median(np.diff(r[first:first+32,2]))),'expected_slope':rate})
        cases[name]={'frames':len(x),'max_step_player_mixer_LR':abs(np.diff(x[:,2:6],axis=0)).max(axis=0).tolist(),
                     'active_windows':windows,'silent_windows':silent,'pause_holds':holds,'reader_shutdowns':off,'resumes':resumes}
        checks[name+'_finite_bounded_capture']=bool(335000<len(x)<=336064 and len(x)==len(r) and np.isfinite(x).all() and np.isfinite(r).all())
        if name.startswith('candidate'):
            checks[name+'_silence_including_stop_selection_cancellation']=all(max(w['max_player_mixer'])==0 for w in silent)
            checks[name+'_paused_master_held_readers_off']=all(w['master_range_frames']==0 and max(w['dsp_flag_max'])==0 for w in holds)
            checks[name+'_active_playback_gain']=all(w['longest_silent_run_frames']<64 and w['mixer_gain_error']<2e-6 for w in windows)
            checks[name+'_fade_before_every_shutdown']=all(w['count']>0 and w['nonzero_gain_before_off']==0 for w in off)
            checks[name+'_resume_saved_position_and_current_rate']=all(abs(w['first_step_frames'])<=abs(w['expected_slope'])+0.01 and abs(w['signed_slope']-w['expected_slope'])<.01 for w in resumes)
            checks[name+'_audio_steps_bounded']=max(cases[name]['max_step_player_mixer_LR']) < (.001 if 'constant' in name else .015)
        else:
            checks[name+'_baseline_held_reader_output']=max(silent[0]['max_player_mixer'][:2])>.01
    expected=np.array([2621,-1311])/32768
    x=load(folder,'candidate-constant-player-mixer-48',6)
    gain_errors=[float(abs(span(x,a,b)[:,2:4]-expected).max()) for a,b in ACTIVE]
    cases['constant_stereo_gain_error']=max(gain_errors)
    checks['constant_stereo_order_and_gain']=max(gain_errors)<2e-6
    for name in ['candidate-boundaries']:
        x=load(folder,name+'-player-mixer-48',6);r=load(folder,name+'-readers-48',10)
        active=[(.55,.65),(1.05,1.15),(1.65,1.69),(1.80,2.0),(2.45,2.60),(2.85,3.05),(3.55,3.75),(4.0,4.15)]
        ws=[{'seconds':[a,b],'longest_silent_frames':longest_silence(span(x,a,b)[:,2:4]),
             'gain_error':float(abs(span(x,a,b)[:,2:4]-expected).max())} for a,b in active]
        cases[name]={'active_windows':ws,'paused_boundary_frames':[float(r[round(t*RATE),2]) for t in [.4,.9,1.52]],'max_steps':abs(np.diff(x[:,2:6],axis=0)).max(axis=0).tolist()}
        checks['boundary_resume_and_slice_after_pause']=all(w['longest_silent_frames']<64 and w['gain_error']<2e-6 for w in ws)
        checks['boundary_finite_stopped']=bool(335000<len(x)<=336064 and len(x)==len(r) and np.isfinite(x).all() and np.isfinite(r).all() and np.all(x[-12000:,2:6]==0))
        checks['boundary_constant_steps_bounded']=max(cases[name]['max_steps'])<.001
    stop=audio_case(folder,'candidate-stop');cases['stop_regression']=stop
    checks['stop_regression']=starts(events(folder,'candidate-stop'))==RESTARTS and stop['all_samples_finite'] and stop['final_tail_zero'] and max(stop['max_adjacent_step_player_LR_mixer_LR'])<.001 and all(w['nonzero_gain_before_off']==0 for w in stop['reader_shutdowns'])
    from analyze_speed_slew_position import reader_steps
    from analyze_instant_reverse import turn_rows, TURNS
    x=load(folder,'candidate-reverse-player-mixer-48',6);r=load(folder,'candidate-reverse-readers-48',10)
    rows=reader_steps(r,x,'wave');turns=turn_rows(r,x,TURNS)
    cases['reverse_speed_regression']={'reader_steps':rows,'turns':turns}
    checks['reverse_speed_position_regression']=all(w['checked_steps']>1000 and not w['oversized_step_times_ms'] for w in rows) and all(max(w['master_max_frame_step'],w['audible_reader_max_frame_step'])<=w['rate_magnitude']+.02 and w['before_after_frames_per_sample'][0]*w['before_after_frames_per_sample'][1]<0 for w in turns)
    checks['reverse_speed_finite_stopped']=bool(np.isfinite(x).all() and np.isfinite(r).all() and np.all(x[-12000:,2:6]==0))
    local=folder/'local-input'
    if (local/'candidate-music-player-mixer-48.wav').exists():
        x=load(local,'candidate-music-player-mixer-48',6);r=load(local,'candidate-music-readers-48',10)
        delta=np.diff(span(r,3.65,3.85)[:,2]);actual=float(delta.mean());expected_rate=2*44100/48000
        cases['local_music']={'drum_resume_signed_rate':actual,'expected_rate':expected_rate,
                              'player_peak_LR':abs(x[:,2:4]).max(axis=0).tolist()}
        checks['local_music_file_host_rate_conversion']=abs(actual-expected_rate)<1e-4
        checks['local_music_finite_silent_pauses_stopped']=bool(np.isfinite(x).all() and np.isfinite(r).all() and all(np.all(span(x,a,b)[:,2:6]==0) for a,b in SILENT))
    return {'host_rate':RATE,'checks':checks,'passed':all(checks.values()),'cases':cases,
            'scope':'Actual native stereo player/mixer/readers. Amplitude bounds are fixture-specific numerical checks, not a universal audibility guarantee.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('folder',type=Path)
    result=analyze(parser.parse_args().folder);print(json.dumps(result,indent=2));raise SystemExit(not result['passed'])
