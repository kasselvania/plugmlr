"""Check retained original-player audio for the MLR slice policy and handoff.

Run: python3 tests/analyze_slice_region.py docs/evidence/slice-region
Requires NumPy and ffmpeg. Measures native WAV/NPZ, never a substitute DSP model.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from analyze_stop_restart import load, RATE, GAIN
from analyze_instant_reverse import longest_silence
from analyze_pause_resume import ACTIVE as PAUSE_ACTIVE, SILENT as PAUSE_SILENT

CUTS = [(200,6,1),(700,1,1),(1200,14,1),(2000,6,-1),(2500,1,-1),(3000,14,-1)]
ACTIVE = [(.08,3.75),(3.97,4.29),(4.73,4.98)]
SILENT = [(3.82,3.94),(4.32,4.69),(5.02,5.28),(5.52,6.95)]
# Only transport/empty-selection spans are excluded from SPEED reader continuity.
# Crucially, both loop-bound + slice collision windows are included.
SPEED_TRANSPORT = [(0,80),(3650,3700),(4000,4390),(5500,7000)]


def span(x,a,b):
    return x[round(a*RATE):round(b*RATE)]


def analyze(folder):
    checks, cases = {}, {}
    for name in ['baseline-wave','baseline-speed','policy-only-speed',
                 'candidate-wave','candidate-constant','candidate-speed','candidate-pause']:
        x=load(folder,name+'-player-mixer-48',6)
        r=load(folder,name+'-readers-48',10)
        checks[name+'_finite_bounded_stopped']=bool(335000<len(x)<=336064 and len(x)==len(r)
            and np.isfinite(x).all() and np.isfinite(r).all() and np.all(x[-12000:,2:6]==0))
        row={'frames':len(x),'max_audio_steps_player_mixer':abs(np.diff(x[:,2:6],axis=0)).max(axis=0).tolist()}
        if name in ['baseline-wave','candidate-wave','candidate-constant']:
            cuts=[]
            for ms,index,direction in CUTS:
                a=ms*48;b=(ms+8)*48
                ix=np.flatnonzero(abs(np.diff(r[a:b,2]))>100)
                target=(index+(direction<0))*750
                destinations=[float(r[a+i+1,2]) for i in ix]
                z=span(r,(ms+10)/1000,(ms+260)/1000)[:,2]
                cuts.append({'command_ms':ms,'index':index,'direction':direction,
                    'target_file_frame':target,'observed_destinations':destinations,
                    'later_range':[float(z.min()),float(z.max())]})
            row['cuts']=cuts
            if name.startswith('candidate'):
                checks[name+'_six_forward_reverse_cut_entries']=all(len(c['observed_destinations'])==1
                    and abs(c['observed_destinations'][0]-(c['target_file_frame']+c['direction']))<.02 for c in cuts)
                checks[name+'_six_cuts_restore_full_content_loop']=all(c['later_range'][0]<2 and c['later_range'][1]>11998 for c in cuts)
            else:
                checks['baseline_retains_smaller_loop']=all(c['later_range'][0]>=2999 and c['later_range'][1]<=9001 for c in [cuts[0],cuts[3]])
        if name in ['candidate-wave','candidate-constant','candidate-pause']:
            active=PAUSE_ACTIVE if name=='candidate-pause' else ACTIVE
            silent=PAUSE_SILENT if name=='candidate-pause' else SILENT
            windows=[]
            for a,b in active:
                z=span(x,a,b)[:,2:6]
                windows.append({'seconds':[a,b],'longest_silent_run_frames':longest_silence(z[:,:2]),
                    'max_mixer_gain_error':float(abs(z[:,2:]-GAIN*z[:,:2]).max())})
            row['active_windows']=windows
            checks[name+'_no_block_dropout_or_mixer_gain_change']=all(w['longest_silent_run_frames']<64 and w['max_mixer_gain_error']<2e-6 for w in windows)
            checks[name+'_pause_stop_empty_silent']=all(np.all(span(x,a,b)[:,2:6]==0) for a,b in silent)
            off=[]
            for gain,flag in [(5,8),(7,9)]:
                ix=np.flatnonzero((r[:-1,flag]>.5)&(r[1:,flag]<.5))
                nonzero=ix[abs(r[ix,gain])>1e-4]
                off.append({'count':len(ix),'nonzero_gain_before_off':len(nonzero),
                    'nonzero_gain_off_ms':(nonzero/48).tolist(),
                    'audible_nonzero_gain_shutdowns':sum(bool(np.any(x[max(0,t-240):t+240,2:6])) for t in nonzero)})
            row['reader_shutdowns']=off
            checks[name+'_no_audible_shutdown_before_fade']=all(w['count']>0 and w['audible_nonzero_gain_shutdowns']==0 for w in off)
        if name=='candidate-constant':
            expected=np.array([2621,-1311])/32768
            error=max(float(abs(span(x,a,b)[:,2:4]-expected).max()) for a,b in ACTIVE)
            row['stereo_constant_max_error']=error
            checks['constant_stereo_order_unity_gain_and_fade_steps']=error<2e-6 and max(row['max_audio_steps_player_mixer'])<.001
        if name.endswith('speed'):
            times=np.arange(len(r)-1)/48;allowed=np.ones(len(times),dtype=bool)
            for a,b in SPEED_TRANSPORT:allowed &= ~((times>=a)&(times<=b))
            sounding=(abs(x[:-1,4:6]).max(axis=1)>1e-6)&(abs(x[1:,4:6]).max(axis=1)>1e-6)
            readers=[]
            for pos,gain,flag in [(4,5,8),(6,7,9)]:
                eligible=allowed&sounding&(r[:-1,gain]>.01)&(r[1:,gain]>.01)&(r[:-1,flag]>.5)&(r[1:,flag]>.5)
                d=abs(np.diff(r[:,pos]));bad=np.flatnonzero(eligible&(d>4.05))
                readers.append({'checked_steps':int(eligible.sum()),'max_step':float(d[eligible].max()),'oversized_step_times_ms':(bad/48).tolist()})
            row['audible_readers']=readers
            row['collision_audio_steps']=[{'command_ms':ms,'max_step_LR':abs(np.diff(x[ms*48:(ms+12)*48,2:4],axis=0)).max(axis=0).tolist()} for ms in [1250,3001]]
            if name=='candidate-speed':
                checks['speed_includes_collisions_without_reader_jumps']=all(w['checked_steps']>1000 and not w['oversized_step_times_ms'] for w in readers)
                checks['speed_rate_range']=bool(np.all((r[:,3]>=.25-1e-5)&(r[:,3]<=4+1e-5)))
            else:
                checks[name+'_reproduces_two_collisions']=sum(len(w['oversized_step_times_ms']) for w in readers)==2
        cases[name]=row
    # Retain the existing silent buffer-selection gain/flag mismatch, not a fade pass.
    baseline=load(folder,'baseline-wave-readers-48',10)
    candidate=load(folder,'candidate-wave-readers-48',10)
    def nonzero_off(r):
        return [(g, int(i)) for g,k in [(5,8),(7,9)] for i in
            np.flatnonzero((r[:-1,k]>.5)&(r[1:,k]<.5)&(r[:-1,g]>1e-4))]
    checks['silent_selection_shutdown_state_unchanged']=nonzero_off(baseline)==nonzero_off(candidate)
    return {'host_sample_rate':RATE,'checks':checks,'passed':all(checks.values()),'cases':cases,
        'speed_transport_exclusions_ms':SPEED_TRANSPORT,
        'limits':'Fixture-specific numerical evidence. Rapid arbitrary-source cuts can reuse an audible reader; no universal click-free claim or human listening acceptance.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path)
    result=analyze(p.parse_args().folder);print(json.dumps(result,indent=2));raise SystemExit(not result['passed'])
