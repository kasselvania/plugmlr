"""Check native loop/fade captures, retaining prior failures and all transitions.

Usage: python3 tests/analyze_natural_loop.py docs/evidence/natural-loop-timing
Requires NumPy. Exact native WAVs may be stored losslessly as .wav.xz.
"""
import json
import lzma
from pathlib import Path
import sys

import numpy as np
from analyze_record_session import audio, longest_zero_run
from analyze_playback_slew import analyze as slew
from analyze_loop_boundary import analyze as turns, audible_jumps


def text_file(path):
    return path.read_text() if path.exists() else lzma.decompress(
        Path(str(path)+'.xz').read_bytes()).decode()


def streams(prefix):
    pairs=[audio(Path(str(prefix)+'-'+name+'.wav'))
           for name in ['capture','readers1','readers2']]
    rates=[p[1]['rate'] for p in pairs]
    assert rates[0]==rates[1]==rates[2] and rates[0] in (44100,48000)
    assert all(p[1]['channels']==10 for p in pairs)
    n=min(len(p[0]) for p in pairs)
    return *(p[0][:n] for p in pairs),rates[0]


def periods(position, sr, seconds, period, jump):
    lo,hi=map(lambda t:round(t*sr),seconds)
    wraps=np.flatnonzero(abs(np.diff(position[lo:hi]))>jump)
    if len(wraps)<3:return {'passed':False,'wraps':len(wraps)}
    intervals=np.diff(wraps)
    phase=(wraps-wraps[0])-np.arange(len(wraps))*period*sr
    error=float(abs(phase).max())
    return {'passed':error<=1.00001, 'wraps':len(wraps),
            'seconds':seconds,'nominal_ms':period*1000,
            'interval_frames':np.unique(intervals).tolist(),
            'mean_period_ms':float(intervals.mean()*1000/sr),
            'maximum_accumulated_error_host_samples':error}


def strict_resets(a,sr,max_rate):
    counts=[]
    for pos,gain in [(4,5),(6,7)]:
        active=(a[:-1,gain]>1e-6)&(a[1:,gain]>1e-6)
        counts.append(int(np.count_nonzero(active &
                      (abs(np.diff(a[:,pos]))>max_rate*48000/sr+.05))))
    return counts


def deadline(prefix):
    x,a,b,sr=streams(prefix)
    def span(lo,hi):return slice(round(lo*sr),round(hi*sr))
    running=[(.116,1.008),(1.116,2.2),(2.416,3),(3.025,12.5)]
    held=np.concatenate([a[span(lo,hi)] for lo,hi in running])
    gains=held[:,5]+held[:,7]
    step=abs(np.diff(a[:,:2],axis=0)).max(axis=0)
    limits=2*np.array([.08,.05])/(.006*sr)+2e-6+2*np.pi*4*np.array(
        [.06*360+.02*124,.04*508+.01*92])/sr
    mix=np.float32(.75)*(np.float32(.4)*x[:,2:4]+np.float32(.3)*x[:,4:6])
    opening=np.zeros(len(x),dtype=bool)
    for t in [.1,1.1,2.4,3.009]:opening[span(t,t+.01)]=True
    trace=text_file(Path(str(prefix)+'-events.txt')).splitlines()
    refusal=[float(s.split()[0]) for s in trace if 'Loop_shorter_than_host_sample' in s]
    invalid=[s for s in trace if 'Invalid_range' in s]
    long=periods(a[:,2],sr,[3.6,12.4],.002,200)
    checks={
        'bounded':13.9<len(x)/sr<=14,
        'finite':all(bool(np.isfinite(z).all()) for z in [x,a,b]),
        'player_taps_match':bool(np.array_equal(x[:,2:4],a[:,:2]) and np.array_equal(x[:,4:6],b[:,:2])),
        'no_reader_resets':not any(strict_resets(a,sr,4)+strict_resets(b,sr,1)),
        'all_transition_steps_bounded':bool(np.all(step<limits)),
        'running_gain_unity':float(abs(gains-1).max())<1e-6,
        'no_running_dropouts':max(longest_zero_run(a[span(lo,hi),:2]) for lo,hi in running)<=64,
        'pause_and_refusal_silent':all(bool(np.all(a[span(lo,hi),:2]==0)) for lo,hi in [(1.03,1.09),(2.22,2.39),(12.52,13.9)]),
        'both_lanes_and_mixer_stop':bool(np.all(x[span(12.52,13.9),2:8]==0)),
        'mixer_gain':float(abs(x[:,6:8]-mix)[~opening].max())<1e-6,
        'subsample_cycle_refused_once':len(refusal)==1 and 1000<=refusal[0]<1020,
        'invalid_ranges_reported':len(invalid)>=4,
        'sustained_2ms_periods':long['passed'],
    }
    return {'passed':all(checks.values()),'checks':checks,
            'metrics':{'long_loop':long,'max_step_LR':step.tolist(),
                       'step_limits':limits.tolist(),'refusal_ms':refusal,
                       'gain_min_max':[float(gains.min()),float(gains.max())]}}


def reference_audio(source, readers):
    """Independent interpolation check of measured positions/gains, not a player.

    Cubic formula: pure-data/src/d_array.c, tabread4_tilde_perform.
    The existing native source-to-position mapping has a +1 file-frame offset;
    this fixed alignment also reconstructs the pre-fade-repair captures. It is
    measured, not a new public indexing convention. Never fit it per capture.
    """
    def lookup(position):
        q=np.clip(position+1,1,len(source)-3).astype(float)
        j=q.astype(int);f=(q-j)[:,None]
        a,b,c,d=[source[j+k].astype(float) for k in [-1,0,1,2]]
        delta=c-b
        return b+f*(delta-(1/6)*(1-f)*((d-a-3*delta)*f+d+2*a-3*b))
    return lookup(readers[:,4])*readers[:,5,None]+lookup(readers[:,6])*readers[:,7,None]


def lane_comparison(folder, rate):
    _,_,a,_=streams(folder/('final-short'+rate))
    _,_,b,_=streams(folder/('final-constant'+rate))
    source,_=audio(folder/'lane-source.wav')
    ra,rb=reference_audio(source,a),reference_audio(source,b)
    ulp=np.spacing(np.maximum(abs(a[:,2]),abs(b[:,2]))).clip(1e-20)
    report={
        'audio_max_error':float(abs(a[:,:2]-b[:,:2]).max()),
        'master_frame_max_error':float(abs(a[:,2]-b[:,2]).max()),
        'master_float32_ulp_max_error':float((abs(a[:,2]-b[:,2])/ulp).max()),
        'gain_max_error':float(abs(a[:,[5,7]]-b[:,[5,7]]).max()),
        'rate_and_dsp_flags_identical':bool(np.array_equal(a[:,[3,8,9]],b[:,[3,8,9]])),
        'reference_audio_max_errors':[float(abs(ra-a[:,:2]).max()),float(abs(rb-b[:,:2]).max())],
        'difference_after_measured_interpolation':float(abs((a[:,:2]-b[:,:2])-(ra-rb)).max()),
        'reference_source_sha256':audio(folder/'lane-source.wav')[1]['sha256'],
        'reference_source_offset_frames':1,
    }
    report['passed']=(report['master_float32_ulp_max_error']<=1 and
        report['gain_max_error']<1e-6 and report['rate_and_dsp_flags_identical'] and
        max(report['reference_audio_max_errors'])<1e-6 and
        report['difference_after_measured_interpolation']<1e-6)
    return report


def musical(prefix):
    x,a,b,sr=streams(prefix)
    def span(lo,hi):return slice(round(lo*sr),round(hi*sr))
    running=[(.116,3.6),(3.916,4.2),(4.316,12.5)]
    gain=np.concatenate([a[span(lo,hi),5]+a[span(lo,hi),7] for lo,hi in running])
    mix=np.float32(.75)*(np.float32(.4)*x[:,2:4]+np.float32(.3)*x[:,4:6])
    opening=np.zeros(len(x),bool)
    for t in [.1,3.9,4.3]:opening[span(t,t+.01)]=True
    checks={
        'bounded':13.9<len(x)/sr<=14,
        'finite':all(bool(np.isfinite(z).all()) for z in [x,a,b]),
        'no_reader_resets':not any(strict_resets(a,sr,4)+strict_resets(b,sr,1)),
        'running_gain_unity':float(abs(gain-1).max())<1e-6,
        'pause_stop_silent':all(bool(np.all(a[span(lo,hi),:2]==0)) for lo,hi in [(3.62,3.89),(4.22,4.29),(12.52,13.9)]),
        'mixer_gain':float(abs(x[:,6:8]-mix)[~opening].max())<1e-6,
        'both_lanes_and_mixer_stop':bool(np.all(x[span(12.52,13.9),2:8]==0)),
    }
    return {'passed':all(checks.values()),'checks':checks,
        'post_master_peak':float(abs(x[:,6:8]).max()),
        'post_master_rms':float(np.sqrt(np.mean(x[:round(12.5*sr),6:8]**2))),
        'player_a_rms_by_second':[float(np.sqrt(np.mean(a[span(i,i+1),:2]**2))) for i in range(12)],
        'max_step_LR':abs(np.diff(x[:,6:8],axis=0)).max(axis=0).tolist(),
        'listening':'Pending. Musical sample steps have no sine-fixture click bound.'}


def suite(folder):
    cases={}; phase={}; sources={}
    names=[f'final-{case}{rate}' for rate in ['441','48']
           for case in ['short','constant','turns','deadline']]+['final-fit441']
    for name in names:
        prefix=folder/name
        if 'deadline' in name:r=deadline(prefix)
        elif 'turns' in name:r=turns(prefix)
        else:r=slew(prefix,constant='constant' in name,short='fit' not in name,fit='fit' in name)
        # The old detector snapped wraps to blocks and happened to repeat the
        # 48 kHz drum bit-for-bit. A logical deadline retains fractional frame
        # precision. Replace that assertion with sample-resolution phase and a
        # matched independent-lane control, retaining its value and rationale.
        replaced={k:r['checks'].pop(k) for k in ['lane_b_exact_repeats','lane_b_identical_periods'] if k in r['checks']}
        if replaced:r['replaced_legacy_repeat_assertions']={'values':replaced,
            'reason':'Require measured sample-resolution phase and matched lane control instead of bit-identical interpolation on separate cycles.'}
        x,a,b,sr=streams(prefix)
        counts=strict_resets(a,sr,16/3 if 'fit' in name else 4)+strict_resets(b,sr,1)
        r['checks']['no_reader_reposition_with_gain_above_1e_6']=not any(counts)
        r['strict_reset_counts']=counts
        phase[name]=periods(b[:,2],sr,[1.2,12.4],1,24000)
        r['checks']['lane_b_sample_resolution_phase']=phase[name]['passed']
        r['passed']=all(r['checks'].values());cases[name]=r
        (folder/(name+'-report.json')).write_text(json.dumps(r,indent=2)+'\n')
        m=json.loads(text_file(Path(str(prefix)+'-manifest.json')))
        sources[name]=[m['production_player_sha256'],m['reader_fade_limit_sha256']]
    comparisons={rate:lane_comparison(folder,rate) for rate in ['441','48']}
    musical_report=musical(folder/'final-musical48')
    (folder/'final-musical48-report.json').write_text(json.dumps(musical_report,indent=2)+'\n')
    cases['final-musical48']=musical_report
    m=json.loads(text_file(folder/'final-musical48-manifest.json'))
    sources['final-musical48']=[m['production_player_sha256'],m['reader_fade_limit_sha256']]
    old_short=slew(folder/'timing-short48',short=True)
    old_turn=turns(folder/'pre-subframe-turns441')
    old_return=slew(folder/'pre-turn-return-short48',short=True)
    checks={n:r['passed'] for n,r in cases.items()}
    checks.update({
        'paired_lane_b_independent':all(v['passed'] for v in comparisons.values()),
        'same_final_production_sources':len({tuple(x) for x in sources.values()})==1,
        'timing_only_reader_reuse_failure_retained':not old_short['checks']['no_audible_reader_resets'] and old_short['checks']['natural_loop_periods_within_one_host_sample'],
        'subsample_fade_failure_retained':not old_turn['checks']['all_transition_steps_bounded'],
        'turn_return_fade_failure_retained':not old_return['checks']['all_transition_steps_bounded'],
    })
    return {'native_numerical_suite_passed':all(checks.values()),'checks':checks,
            'case_reports':{n:n+'-report.json' for n in cases},
            'lane_b_comparisons':comparisons,'lane_b_periods':phase,
            'production_hashes':sources,
            'listening_acceptance':'Pending. Numerical bounds are not universal click-free, hardware or DAW acceptance.'}


if __name__=='__main__':
    result=suite(Path(sys.argv[1]));print(json.dumps(result,indent=2))
    raise SystemExit(not result['native_numerical_suite_passed'])
