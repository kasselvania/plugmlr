"""Compare actual two-player captures, including all transition samples."""
import json
from pathlib import Path
import sys
import numpy as np
import analyze_tempo_fit as audio

audio.HOST = audio.FILE = 48000
folder = Path(sys.argv[1])
checks, results, readers, mixers = {}, {}, {}, {}
for run in ('baseline', 'changes'):
    mixers[run] = audio.load(folder / f'{run}-mixers.wav', 4)
    for channel, track in enumerate((17, 18)):
        path = folder / f'{run}-{track}.npz'
        r = audio.load(path if path.exists() else path.with_suffix('.wav'), 10)
        readers[run, track] = r
        y = mixers[run][:, channel * 2:channel * 2 + 2]
        result = audio.inspect(r, y, [(.12, 8.99)], [.1])
        key = f'{run}_{track}'
        results[key] = result
        checks[key + '_bounded_finite'] = result['finite'] and all(479000 <= n <= 480064 for n in result['frames'])
        checks[key + '_reader_continuity'] = not result['audible_reader_jumps']
        checks[key + '_active_stereo'] = max(result['active_longest_silence_frames']) <= 2 and bool(np.allclose(result['player_peak_lr'], [.12, .06], atol=.0001))
        checks[key + '_mixer_gain'] = abs(result['mixer_gain'] - (.4 if track == 17 else .3)) < 1e-6 and result['mixer_residual_outside_documented_start_fades'] < 1e-6 and result['mixer_max_amplification_above_gain'] < 1e-6
        checks[key + '_stop_silent'] = bool(np.max(abs(r[round(9.03*48000):, :2])) == 0 and np.max(abs(y[round(9.03*48000):])) == 0)
        checks[key + '_transition_audio_steps'] = max(result['player_max_adjacent_step_lr']) < .012

b, c = readers['baseline', 18], readers['changes', 18]
results['player_b_max_sample_difference'] = abs(b-c).max(0).tolist()
checks['player_b_audio_position_rate_unchanged'] = bool(np.array_equal(b[:, :5], c[:, :5]) and np.array_equal(b[:, 6], c[:, 6]))
checks['player_b_fades_unchanged_within_float_precision'] = bool(np.max(abs(b-c)) < 1e-8)
checks['player_b_post_mixer_unchanged'] = bool(np.array_equal(mixers['baseline'][:, 2:], mixers['changes'][:, 2:]))
for track, cases in [(17, [(.2,1), (1.2,1), (2.2,-1), (3.2,-2), (4.2,2), (5.2,2), (7.2,2), (8.2,2)]), (18, [(.2,1), (3.2,1), (6.2,1), (7.2,1.5), (8.2,.75)])]:
    r = readers['changes', track]
    rates = [float(np.median(np.diff(r[round(t*48000):round((t+.4)*48000), 2]))) for t, _ in cases]
    results[f'{track}_signed_frame_steps'] = rates
    checks[f'{track}_independent_motion_and_fit'] = all(abs(observed-expected) < .01 for observed, (_,expected) in zip(rates,cases))
r = readers['changes',17]
w = r[round(1.03*48000):round(4.99*48000),2]
checks['player_a_partial_loop_bounds'] = bool(w.min() >= 12000-1 and w.max() <= 60000+1)
checks['player_a_slice_restores_full_content'] = bool(r[round(5.1*48000):round(5.8*48000),2].max() > 60001)
output = {'host_hz':48000,'file_hz':48000,'checks':checks,'passed':all(checks.values()),'results':results,'limits':['Two original player/mixer components sharing Sample16; not two complete instruments','No human listening acceptance for these generated-signal captures','No Bitwig acceptance']}
print(json.dumps(output, indent=2))
sys.exit(not output['passed'])
