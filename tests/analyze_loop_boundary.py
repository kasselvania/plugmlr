"""Analyze actual native player/reader/mixer captures; no simulated DSP.

Usage: python3 tests/analyze_loop_boundary.py EVIDENCE_PREFIX [--constant]
Requires NumPy. Reads float WAV or lossless WAV.gz via analyze_record_session.
The score is the turns/constant scenario in build_record_session_check.py.
Every sample, including every transition, remains in the discontinuity checks.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from analyze_record_session import audio, longest_zero_run
from analyze_record_session import analyze as recording_session


def audible_jumps(reader, host_rate, maximum_rate):
    result = []
    # Fixture file rate is 48 kHz; the reader position is in file frames.
    maximum_step = maximum_rate * 48000 / host_rate + .05
    for position, gain, dsp in ((4, 5, 8), (6, 7, 9)):
        active = ((reader[:-1, gain] > .01) & (reader[1:, gain] > .01) &
                  (reader[:-1, dsp] > .5) & (reader[1:, dsp] > .5))
        delta = abs(np.diff(reader[:, position]))
        for i in np.flatnonzero(active & (delta > maximum_step)):
            result.append({'reader': (position-4)//2, 'seconds': float(i/host_rate),
                           'jump_frames': float(delta[i]),
                           'gain_before': float(reader[i, gain]),
                           'gain_after': float(reader[i+1, gain])})
    return result


def analyze(prefix, constant=False):
    x, info = audio(Path(str(prefix)+'-capture.wav'))
    a, ai = audio(Path(str(prefix)+'-readers1.wav'))
    b, bi = audio(Path(str(prefix)+'-readers2.wav'))
    sr = info['rate']
    assert sr in (44100, 48000)
    assert info['channels'] == ai['channels'] == bi['channels'] == 10
    assert info['rate'] == ai['rate'] == bi['rate']
    n = min(len(x), len(a), len(b))
    x, a, b = x[:n], a[:n], b[:n]
    def span(lo, hi): return slice(round(lo*sr), round(hi*sr))
    checks = {'finite_all_signals': bool(all(np.isfinite(v).all() for v in (x,a,b))),
              'bounded_capture': 13.9 < n/sr <= 14.0,
              'player_taps_match_capture': bool(np.array_equal(a[:,:2], x[:,2:4]) and
                                                np.array_equal(b[:,:2], x[:,4:6])),
              'master_inside_file': bool(a[:,2].min() >= 0 and a[:,2].max() <= 12000)}
    jumps_a, jumps_b = audible_jumps(a, sr, 4), audible_jumps(b, sr, 1)
    checks['no_audible_reader_resets'] = not jumps_a and not jumps_b
    for second in range(1,12):
        delta = np.diff(b[span(second,second+1),2])
        delta = delta[abs(delta) < 2]
        checks[f'lane_b_keeps_moving_{second}s'] = abs(float(np.median(delta))*sr/48000-1) < .02

    # Stops/opening envelopes are deliberate. These intervals include all turns,
    # natural wraps, loop edits, pending cuts and speed glides while running.
    running = [(.116,1), (1.116,2), (2.116,3), (3.116,4), (4.116,5),
               (5.116,6), (6.116,6.35), (6.616,7), (7.116,8),
               (8.116,8.3502), (8.38,9), (9.116,10), (10.616,12.5)]
    held = np.concatenate([a[span(lo,hi)] for lo,hi in running])
    gains = held[:,5] + held[:,7]
    checks['unity_combined_gain_while_running'] = bool(np.max(abs(gains-1)) < 1e-6)
    zero_run = max(longest_zero_run(a[span(lo,hi),:2]) for lo,hi in running)
    checks['no_silent_dropouts_while_running'] = zero_run <= 64
    silent = [(t+.02,t+.09) for t in range(1,10)] + [(6.37,6.59),(10.05,10.48),(12.52,13.9)]
    # Chapter 8 has another intentional Stop followed by a queued Play.
    checks['stopped_paused_empty_player_silent'] = all(
        np.all(a[span(lo,hi),:2] == 0) for lo,hi in silent)
    checks['both_players_and_mixer_stop'] = bool(np.all(x[span(12.52,13.9),2:8] == 0))

    motions = [(.15,.3,1), (.38,.98,-1), (1.12,1.34,-1), (1.38,1.98,1),
               (2.38,2.98,-1), (3.3,3.98,-2), (4.2,4.98,-4), (5.38,5.98,-1),
               (6.62,6.78,1), (6.82,6.98,-1), (7.88,7.98,-.25),
               (8.38,8.98,1), (9.5,9.98,-1), (10.62,12.48,-1)]
    motion = []
    for lo, hi, speed in motions:
        delta = np.diff(a[span(lo,hi),2])
        delta = delta[abs(delta) < 5] # exclude wraps only for measuring rate
        measured = float(np.median(delta))*sr/48000
        checks[f'motion_{lo}s'] = abs(measured-speed) < .02
        motion.append({'from':lo,'to':hi,'expected_multiplier':speed,
                       'measured_multiplier':measured})

    # Exact periodic comparison is meaningful at matched file/host rate.
    # At 44.1 kHz, block-scheduled wraps have different fractional alignment;
    # compare the entire B stream with the matched constant-probe run separately.
    repeats = None
    if sr == 48000:
        reference = x[sr:2*sr,4:6]
        repeats = max(float(np.max(abs(x[i*sr:(i+1)*sr,4:6]-reference))) for i in range(2,12))
        checks['lane_b_exact_repeats'] = repeats == 0
    expected_mix = np.float32(.75)*(np.float32(.4)*x[:,2:4] + np.float32(.3)*x[:,4:6])
    mix_residual = np.max(abs(x[:,6:8]-expected_mix),axis=1)
    time = np.arange(n)/sr
    opening = np.zeros(n,dtype=bool)
    for start in [.1,1.1,2.1,3.1,4.1,5.1,6.1,6.6,7.1,8.1,8.3592,9.1,10.6]:
        opening |= (time >= start) & (time < start+.01)
    checks['mixer_preserves_gain_outside_open'] = bool(mix_residual[~opening].max() < 1e-6)
    player_step = np.max(abs(np.diff(a[:,:2],axis=0)),axis=0)
    # The fixture's maximum sine slopes at 4x plus two simultaneous 6 ms
    # unit-range reader fades. Scale per host sample; do not fit to a capture.
    peaks = np.array([.08,.04] if constant else [.08,.05])
    step_limit = 2*peaks/(.006*sr)+2e-6
    if not constant:
        step_limit += 2*np.pi*4*np.array([.06*360+.02*124, .04*508+.01*92])/sr
    checks['all_transition_steps_bounded'] = bool(np.all(player_step < step_limit))
    constant_error = None
    if constant:
        expected = np.round(np.array([.08,-.04])*32767)/32768
        constant_error = float(np.max(abs(held[:,:2]-expected)))
        checks['stereo_constant_no_dips_or_boosts'] = constant_error < 1e-6
    return {'passed':all(checks.values()),'checks':checks,'capture':info,
            'reader_captures':[ai,bi], 'file_rate':48000,
            'metrics':{'audible_reader_jumps_a':jumps_a,'audible_reader_jumps_b':jumps_b,
                       'player_max_adjacent_step_all_samples':player_step.tolist(),
                       'fixture_step_limits':step_limit.tolist(),
                       'running_gain_min_max':[float(gains.min()),float(gains.max())],
                       'longest_zero_run_running_frames':zero_run,
                       'lane_b_repeat_residual':repeats,'constant_stereo_error':constant_error,
                       'mixer_max_residual_all_samples':float(mix_residual.max()),
                       'mixer_max_residual_outside_open':float(mix_residual[~opening].max()),
                       'motion':motion},
            'listening':'Not collected. No universal click-free or DAW acceptance claim.'}


def analyze_recorded(prefix):
    result = recording_session(prefix)
    for lane in (1,2):
        a, info = audio(Path(str(prefix)+f'-readers{lane}.wav'))
        sr = info['rate']
        jumps = audible_jumps(a, sr, 2 if lane == 1 else 1)
        result['playback_checks'][f'no_audible_resets_{lane}'] = not jumps
        result['metrics'][f'audible_resets_{lane}'] = jumps
        playing = a[round((4.92 if lane == 1 else .12)*sr):round(12.49*sr)]
        gains = playing[:,5]+playing[:,7]
        result['playback_checks'][f'unity_reader_gain_{lane}'] = bool(abs(gains-1).max() < 1e-6)
    result['passed'] = all(result['recorder_checks'].values()) and all(result['playback_checks'].values())
    return result


def suite(folder):
    cases = {name: analyze(folder/name, name.startswith('constant')) for name in
             ('final48','constant48','final441','constant441')}
    cases['boundary-final'] = analyze_recorded(folder/'boundary-final')
    checks = {name: result['passed'] for name,result in cases.items()}
    baseline = analyze(folder/'baseline48')
    checks['prior_player_reproduces_audible_reset'] = not baseline['checks']['no_audible_reader_resets']
    old = recording_session(folder.parent/'recording-continuity'/'boundary')
    checks['prior_recorded_boundary_reproduces_stuck_reverse'] = (
        old['recorder_passed'] and not old['playback_checks']['actual_motion_8.34s'])
    comparisons = {}
    for rate in ('48','441'):
        a, _ = audio(folder/f'final{rate}-readers2.wav')
        b, _ = audio(folder/f'constant{rate}-readers2.wav')
        audio_error = float(np.max(abs(a[:,:2]-b[:,:2])))
        position_error = float(np.max(abs(a[:,2]-b[:,2])))
        checks[f'lane_b_matches_control_{rate}'] = audio_error < 1e-6 and position_error < .001
        comparisons[rate] = {'all_stereo_samples_max_residual':audio_error,
                             'logical_frame_max_residual':position_error}
    return {'passed':all(checks.values()),'checks':checks,'cases':cases,
            'lane_b_comparisons':comparisons,'prior_player':baseline,
            'prior_recorded_boundary':old}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('prefix',type=Path)
    parser.add_argument('--constant',action='store_true')
    parser.add_argument('--recorded',action='store_true',help='Original recorded-buffer boundary score.')
    parser.add_argument('--suite',action='store_true',help='Analyze the retained evidence folder and failure controls.')
    args=parser.parse_args()
    result=(suite(args.prefix) if args.suite else analyze_recorded(args.prefix) if args.recorded
            else analyze(args.prefix,args.constant))
    print(json.dumps(result,indent=2))
    raise SystemExit(not result['passed'])
