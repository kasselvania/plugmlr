"""Inspect actual native captures from the slew/short scores, including transitions.

Usage: python3 tests/analyze_playback_slew.py EVIDENCE_PREFIX [--constant]
Requires NumPy. WAV, WAV.gz and WAV.xz inputs are supported. No simulated DSP.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from analyze_record_session import audio, longest_zero_run
from analyze_loop_boundary import audible_jumps


def analyze(prefix, constant=False, short=False, fit=False):
    x, info = audio(Path(str(prefix)+'-capture.wav'))
    a, ai = audio(Path(str(prefix)+'-readers1.wav'))
    b, bi = audio(Path(str(prefix)+'-readers2.wav'))
    sr = info['rate']
    assert sr == ai['rate'] == bi['rate']
    assert info['channels'] == ai['channels'] == bi['channels'] == 10
    n = min(map(len, (x,a,b)))
    x,a,b = x[:n],a[:n],b[:n]
    def span(lo,hi):return slice(round(lo*sr),round(hi*sr))
    running=[(.116,4),(4.616,9),(9.216,12.5)] if fit else [(.116,3.6),(3.916,4.2),(4.316,12.5)]
    held=np.concatenate([a[span(lo,hi)] for lo,hi in running])
    gains=held[:,5]+held[:,7]
    maximum_rate=16/3 if fit else 4
    jumps=audible_jumps(a,sr,maximum_rate)
    step=abs(np.diff(a[:,:2],axis=0)).max(axis=0)
    peaks=np.array([.08,.04] if constant else [.08,.05])
    limit=2*peaks/(.006*sr)+2e-6
    if not constant:
        limit+=2*np.pi*maximum_rate*np.array([.06*360+.02*124,.04*508+.01*92])/sr
    expected=np.round(np.array([.08,-.04])*32767)/32768
    constant_error=float(abs(held[:,:2]-expected).max()) if constant else None
    zero=max(longest_zero_run(a[span(lo,hi),:2]) for lo,hi in running)
    expected_mix=np.float32(.75)*(np.float32(.4)*x[:,2:4]+np.float32(.3)*x[:,4:6])
    residual=abs(x[:,6:8]-expected_mix).max(axis=1)
    opening=np.zeros(n,dtype=bool)
    for t in ((.1,4.6,9.2) if fit else (.1,3.9,4.3)):opening[span(t,t+.01)]=True
    checks={
        'bounded':13.9<n/sr<=14,
        'finite':all(bool(np.isfinite(z).all()) for z in (x,a,b)),
        'player_taps_match':bool(np.array_equal(x[:,2:4],a[:,:2]) and np.array_equal(x[:,4:6],b[:,:2])),
        'supported_rate_range':bool(a[:,3].min()>=(.015625 if fit else .25)-1e-6 and a[:,3].max()<=maximum_rate+1e-6),
        'no_audible_reader_resets':not jumps,
        'all_transition_steps_bounded':bool(np.all(step<limit)),
        'unity_running_reader_gain':bool(abs(gains-1).max()<1e-6),
        'no_running_dropouts':zero<=64,
        'pause_stop_silence':all(bool(np.all(a[span(lo,hi),:2]==0)) for lo,hi in ([(4.02,4.59),(9.02,9.19),(12.52,13.9)] if fit else [(3.62,3.89),(4.22,4.29),(12.52,13.9)])),
        'both_players_and_mixer_stop':bool(np.all(x[span(12.52,13.9),2:8]==0)),
        'mixer_preserves_gain':bool(residual[~opening].max()<1e-6),
        'lane_b_no_reader_resets':not audible_jumps(b,sr,1),
    }
    if constant:checks['constant_stereo_no_dips_or_boosts']=constant_error<1e-6
    repeats=None
    if sr==48000:
        repeats=max(float(abs(x[i*sr:(i+1)*sr,4:6]-x[sr:2*sr,4:6]).max()) for i in range(2,12))
        checks['lane_b_identical_periods']=repeats==0
    rates=[]
    targets=[(.85,1.1,16/3),(3.55,3.9,.015625),(6.3,6.4,4),(6.6,7.4,16/3),(7.6,7.9,4),(8.1,8.9,1),(9.3,12.4,1)] if fit else [(3.12,3.19,2),(3.3,3.49,1),(4.1,4.19,4),(7.3,7.59,1)]
    for lo,hi,target in targets:
        error=float(abs(a[span(lo,hi),3]-target).max())
        rates.append({'seconds':[lo,hi],'expected':target,'error':error})
    checks['glides_reach_final_targets']=all(r['error']<1e-5 for r in rates)
    motion=[]
    motions=[(lo,hi,-target if 1.2<lo<9 else target) for lo,hi,target in targets] if fit else [(3.12,3.19,2),(3.3,3.49,-1),(4.1,4.19,4),(7.3,7.59,-1)]
    for lo,hi,target in motions:
        delta=np.diff(a[span(lo,hi),2])
        # Wraps are excluded only from this slope estimate, never from reader
        # continuity, output-step, gain or finite-output checks.
        delta=delta[(abs(delta)<maximum_rate*48000/sr+.05)&(delta!=0)]
        rate=float(np.mean(delta))*sr/48000
        motion.append({'seconds':[lo,hi],'expected':target,'measured':rate})
    checks['signed_reader_motion_and_file_host_conversion']=all(abs(m['measured']-m['expected'])<.02 for m in motion)
    holds=[]
    for lo,hi in running:
        delta=np.diff(a[span(lo,hi),2])
        holds.append(longest_zero_run(delta[:,None]))
    # A queued region/slice deliberately waits for the previous 12 ms handoff.
    # Include that interval and two blocks of boundary notification latency;
    # a stricter two-block-only limit incorrectly labels this wait as stuck.
    hold_limit_frames=int(np.ceil(.012*sr))+128
    checks['no_running_hold_beyond_cut_wait_budget']=max(holds)<=hold_limit_frames
    periods=[]
    for lo,hi,region in ([] if fit else [(8.18,8.28,.1),(9.18,9.28,.02),(10.18,10.28,.012),(11.18,11.28,.008)]):
        expected_ms=(region if short else .1)*1000/4
        position=a[span(lo,hi),2]
        wraps=np.flatnonzero(abs(np.diff(position))>10)
        actual=np.diff(wraps)*1000/sr
        periods.append({'seconds':[lo,hi],'nominal_period_ms':expected_ms,
                        'measured_periods_ms':actual.tolist(),
                        'maximum_error_ms':float(abs(actual-expected_ms).max()) if len(actual) else None})
    if periods:
        checks['natural_loop_periods_within_one_host_sample']=all(
            p['maximum_error_ms'] is not None and p['maximum_error_ms']<=1000/sr for p in periods)
    chapters=[]
    for lo,hi in [(0,3.2),(3.2,3.5),(3.5,4.3),(4.3,7.6),(7.6,8.6),(8.6,9.6),(9.6,10.6),(10.6,12.5)]:
        w=a[span(lo,hi)]
        chapters.append({'seconds':[lo,hi],
                         'max_step_LR':abs(np.diff(w[:,:2],axis=0)).max(axis=0).tolist(),
                         'audible_reader_reset_count':sum(lo<=j['seconds']<hi for j in jumps),
                         'reader_gain_min_max':[float((w[:,5]+w[:,7]).min()),float((w[:,5]+w[:,7]).max())]})
    return {'passed':all(checks.values()),'checks':checks,'capture':info,
            'file_rate':48000,'reader_captures':[ai,bi],
            'metrics':{'max_step_LR':step.tolist(),'fixture_step_limits':limit.tolist(),
                       'audible_reader_resets':jumps,'constant_stereo_error':constant_error,
                       'running_gain_min_max':[float(gains.min()),float(gains.max())],
                       'longest_running_zero_frames':zero,'lane_b_repeat_residual':repeats,
                       'mixer_residual_all':float(residual.max()),
                       'mixer_residual_outside_open':float(residual[~opening].max()),
                       'rate_min_max':[float(a[:,3].min()),float(a[:,3].max())],
                       'rates':rates,'motion':motion,'longest_position_hold_frames':max(holds),
                       'position_hold_limit_frames':hold_limit_frames,
                       'loop_periods':periods,'chapters':chapters},
            'listening':'Not collected. These numerical bounds do not establish universal click-free playback.'}


def repair_suite(folder):
    names=['baseline48','constant48','short48','short-constant48','baseline441',
           'short441','repaired441','repaired-short441','fit441','repaired48',
           'repaired-constant48']
    cases={}
    for name in names:
        result=analyze(folder/name,'constant' in name,'short' in name,name=='fit441')
        cases[name]=result
        (folder/(name+'-report.json')).write_text(json.dumps(result,indent=2)+'\n')
    comparisons={}
    for before,after in [('baseline48','repaired48'),('baseline441','repaired441'),
                         ('short441','repaired-short441')]:
        a,_=audio(folder/(before+'-readers2.wav'))
        b,_=audio(folder/(after+'-readers2.wav'))
        n=min(len(a),len(b))
        comparisons[after]={'reference':before,
            'lane_b_audio_max_error':float(abs(a[:n,:2]-b[:n,:2]).max()),
            'lane_b_master_position_max_error':float(abs(a[:n,2]-b[:n,2]).max())}
    checks={
        'baseline_reproduces_rate_overshoot':not cases['baseline441']['checks']['supported_rate_range'],
        'repaired_441_rate_bounded':cases['repaired441']['checks']['supported_rate_range'],
        'fit_including_1_over_64_and_16_over_3_passes':cases['fit441']['passed'],
        'normal_repaired_scores_fail_only_known_loop_timing':all(
            [k for k,v in cases[n]['checks'].items() if not v]==['natural_loop_periods_within_one_host_sample']
            for n in ['repaired48','repaired441','repaired-constant48']),
        'short_loop_failure_retained':not cases['repaired-short441']['checks']['no_audible_reader_resets']
            and not cases['repaired-short441']['checks']['all_transition_steps_bounded'],
        'other_lane_unchanged':all(v['lane_b_audio_max_error']<1e-6 and
            v['lane_b_master_position_max_error']<.001 for v in comparisons.values()),
    }
    return {'rate_repair_passed':all(checks.values()),'full_playback_acceptance':False,
        'repair_checks':checks,'other_lane_comparisons':comparisons,
        'open_failures':['Natural loops wait for block-boundary notification, extending nominal periods.',
                         'Short loops reuse a reader before its outgoing fade completes.'],
        'case_reports':{n:n+'-report.json' for n in names},
        'listening':'Not collected for these new captures.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('prefix',type=Path)
    parser.add_argument('--constant',action='store_true')
    parser.add_argument('--short',action='store_true')
    parser.add_argument('--fit',action='store_true')
    parser.add_argument('--repair-suite',action='store_true',
                        help='Check the bounded rate repair and retain explicit broader playback failures.')
    args=parser.parse_args()
    result=repair_suite(args.prefix) if args.repair_suite else analyze(args.prefix,args.constant,args.short,args.fit)
    print(json.dumps(result,indent=2))
    raise SystemExit(not result['rate_repair_passed' if args.repair_suite else 'passed'])
