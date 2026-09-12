"""Check actual six-channel UI/mixer capture and its passive message log.

Usage: python tests/analyze_ui_overview.py DIRECTORY
Reads capture.wav or capture.wav.xz, events.txt. Requires NumPy.
This is a UI boundary check, not a new crossover or listening acceptance test.
"""
import json
from pathlib import Path
import sys
import numpy as np
from analyze_record_session import audio, longest_zero_run

def analyze(directory):
    x, info = audio(directory/'capture.wav'); sr = info['rate']
    assert info['channels'] == 6 and sr == 48000
    rows = [r.rstrip(';').split() for r in (directory/'events.txt').read_text().splitlines()]
    checks = {'bounded': 6.99 < len(x)/sr <= 7.001, 'finite_all_samples': bool(np.isfinite(x).all())}
    def window(a,b): return x[round(a*sr):round(b*sr)]
    # Mixer attack envelopes are intentional. These steady windows check the
    # relocated master/track gains; all samples also receive the bounds below.
    windows = [(.4,1.4,.4,.75),(1.55,1.75,.4,.75),(1.85,2.25,.4,.75),
               (2.35,2.55,.4,.75),(2.65,2.95,.4,.75),(3.05,3.45,.2,.75),
               (3.55,3.95,.4,.75),(4.05,4.45,.4,.5),(4.55,6.25,.4,.75),
               (6.35,6.45,.4,.75)]
    residuals = []
    for a,b,gain,master in windows:
        y = window(a,b)
        expected = np.float32(master)*(np.float32(gain)*y[:,2:4]+np.float32(.3)*y[:,4:6])
        residuals.append({'start':a,'end':b,'track1_gain':gain,'master':master,
                          'max_error':float(np.max(abs(y[:,:2]-expected)))})
    checks['expected_stereo_mix_and_initial_master'] = all(r['max_error'] < 1e-6 for r in residuals)
    # Whole recording, including starts/stops/gain commands/navigation: no
    # unexplained amplification beyond the largest requested gains.
    bound = .75*(.4*abs(x[:,2:4])+.3*abs(x[:,4:6]))
    checks['all_sample_gain_bound'] = bool(np.all(abs(x[:,:2]) <= bound + 1e-6))
    checks['pause_silent_at_player1'] = bool(np.all(window(1.52,1.79)[:,2:4] == 0))
    checks['stop_silent_at_player1'] = bool(np.all(window(2.32,2.59)[:,2:4] == 0))
    checks['final_silence_all_taps'] = bool(np.all(window(6.52,6.98) == 0))
    checks['useful_output'] = float(np.sqrt(np.mean(window(.4,6.25)[:,:2]**2))) > .01
    def tagged(tag): return [r for r in rows if r[1] == tag]
    # UI readbacks use set. They must not echo extra gain commands.
    checks['level_readback_no_echo'] = [(float(r[0]),float(r[2])) for r in tagged('audio-1-out')] == [(150,.4),(3000,.2),(3500,.4)] and [(float(r[0]),float(r[2])) for r in tagged('audio-2-out')] == [(150,.3)]
    checks['master_readback_no_echo'] = [(float(r[0]),float(r[2])) for r in tagged('master-level')] == [(4000,.5),(4500,.75)]
    checks['shared_sample1_readback'] = all(any(r[2:] == ['set','1'] and float(r[0]) == 120 for r in tagged(f'{i}-ui-slot')) for i in (1,2))
    checks['lane2_not_stopped_by_lane1_or_navigation'] = all(r[2] == '1' for r in tagged('2-grid-playing') if 300 <= float(r[0]) < 6500)
    for i in (1,2):
        positions = [(float(r[0]),float(r[2])) for r in tagged(f'{i}-grid-position') if 4900 <= float(r[0]) <= 6200]
        differences = np.diff([r[1] for r in positions])
        checks[f'navigation_continues_position_{i}'] = len(positions)>50 and bool(np.all((differences>0)&(differences<.002)))
    ticks = [(float(r[0]),float(r[2])) for r in tagged('ppq')]
    stable_ticks = [(ms,n) for ms,n in ticks if 1200 < ms < 5900]
    checks['internal_clock_120bpm'] = len(stable_ticks)>100 and bool(np.all(abs(np.diff([ms for ms,n in stable_ticks])-31.25)<.01))
    checks['clock_stops_independently'] = not any(ms>=6000 for ms,n in ticks)
    checks['bpm_readback'] = any(r[2:] == ['set','120'] for r in tagged('clock-bpm-ui'))
    checks['opens_player16'] = any(float(r[0]) == 5400 for r in tagged('16-open-player-view'))
    checks['navigation_does_not_finish_recording'] = not tagged('record-finish')
    running = window(.32,6.49)[:,:2]
    result = {'audio':info,'checks':checks,'gain_windows':residuals,
              'peak_stereo':np.max(abs(x[:,:2]),axis=0).tolist(),
              'max_adjacent_step_all_samples':np.max(abs(np.diff(x[:,:2],axis=0)),axis=0).tolist(),
              'longest_running_exact_zero_frames':longest_zero_run(running),
              'listening':'Not performed; no user report for this capture.',
              'limitations':'Steady gain windows exclude intentional mixer attacks. Whole-recording bounds retain every transition sample. No universal click-free or hardware recording claim.'}
    return result

if __name__ == '__main__':
    result = analyze(Path(sys.argv[1])); print(json.dumps(result, indent=2))
    sys.exit(not all(result['checks'].values()))
