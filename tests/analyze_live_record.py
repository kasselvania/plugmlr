"""Check native application recordings and the actual player/post-master capture.

Capture channels: generated input L/R, player L/R, post-master mixer L/R.
Array export includes capacity. The event log independently supplies content end.
No listening judgment or general click-free claim is made by this analysis.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np


def read(path, channels):
    data = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'f32le', '-'])
    return np.frombuffer(data, dtype='<f4').reshape(-1, channels)


def analyze(capture, array, events, case):
    x, recorded = read(capture, 6), read(array, 2)
    lines = events.read_text().splitlines()
    metadata = [l.rstrip(';').split() for l in lines if ' l_b_buffer_states 1 ' in l]
    loaded = [l for l in metadata if l[-1] == '1']
    end = int(float(loaded[-1][5])) if loaded else 0
    expected = {'fixed': 48000, 'bars': 96000, 'guards': 0, 'gap':48000}.get(case)
    # Recorder begins 50 ms into the score. Early stop is block-quantized.
    if case == 'early': expected = end
    errors = [l for l in lines if ' l_b_record_errors ' in l]
    checks = {
        'capture_present': 335000 < len(x) <= 336064,
        'all_samples_finite': bool(np.isfinite(x).all() and np.isfinite(recorded).all()),
        'expected_content_frames': end == expected,
        'capacity_matches_frozen_length': len(recorded) == {'fixed':48000,'early':96000,'bars':96000,'guards':48000,'gap':48000}[case],
    }
    if case == 'early': checks['early_stop_block_resolution'] = 15400 <= end <= 15700 and end % 64 == 0
    result = {'case': case, 'host_rate': 48000, 'captured_frames': len(x),
              'capacity_frames': len(recorded), 'content_frames': end,
              'errors_reported': errors, 'checks': checks}
    if end:
        # Match actual written samples to the actual input tap near the scheduled
        # start, allowing one local signal block of latency. Both channels must
        # match at one offset; independent channel realignment would hide skew.
        n = 10000 if case == 'gap' else end
        candidates = [(float(np.max(np.abs(recorded[:n]-x[i:i+n,:2]))), i)
                      for i in range(2200, 2500)]
        error, offset = min(candidates)
        result['input_to_array'] = {'shared_offset_frames': offset, 'maximum_sample_error':error}
        checks['stereo_input_samples_preserved'] = error < 2e-6
        if case == 'gap':
            checks['disconnected_interval_is_silence'] = bool(np.all(recorded[14000:24000] == 0))
            checks['reconnected_input_resumes_exactly'] = bool(np.max(np.abs(recorded[-9600:]-x[offset+end-9600:offset+end,:2])) < 2e-6)
        checks['unwritten_capacity_zero'] = bool(np.all(recorded[end:] == 0))
        active = np.sqrt(np.mean(x[:,2:4]**2,axis=1)) > .01
        checks['player_has_audio'] = bool(np.count_nonzero(active) > 24000)
        # Ignore existing mixer start/stop envelope edges. Check steady windows
        # selected from actual player activity, with both channels evaluated.
        blocks=[]
        for start in range(0,len(x)-4800,4800):
            a=x[start:start+4800,2:4]; b=x[start:start+4800,4:6]
            if np.sqrt(np.mean(a*a)) > .02:
                err=float(np.max(np.abs(b-.15*a)))
                blocks.append({'start_frame':start,'maximum_gain_error':err})
        result['active_mixer_windows']=blocks
        checks['mixer_unity_relative_to_configured_gain'] = len(blocks)>5 and sum(b['maximum_gain_error'] < 2e-6 for b in blocks) >= len(blocks)-2
        result['player_maximum_adjacent_step'] = np.max(np.abs(np.diff(x[:,2:4],axis=0)),axis=0).tolist()
        result['mixer_maximum_adjacent_step'] = np.max(np.abs(np.diff(x[:,4:6],axis=0)),axis=0).tolist()
        if case != 'gap':
            begin,finish={'fixed':(1.3,5.7),'early':(.525,2.3),'bars':(2.45,4.7)}[case]
            active_audio=x[int(begin*48000):int(finish*48000),2:4]
            silent=np.all(np.abs(active_audio)<1e-8,axis=1)
            edges=np.diff(np.r_[False,silent,False].astype(int))
            runs=np.flatnonzero(edges==-1)-np.flatnonzero(edges==1)
            result['longest_silent_run_during_playback_frames']=int(max(runs,default=0))
            checks['no_block_length_dropout_in_playback']=result['longest_silent_run_during_playback_frames'] < 64
        checks['stopped_audio'] = bool(np.max(np.abs(x[-12000:,2:6])) < 1e-7)
    else:
        checks['empty_arrays_untouched'] = bool(np.all(recorded == 0))
        checks['no_playback'] = bool(np.max(np.abs(x[:,2:6])) < 1e-7)
    if case == 'fixed':
        checks['busy_and_overwrite_rejected'] = sum('Buffer_busy' in l for l in errors)==2 and any('Clear_live_buffer_first' in l for l in errors)
    if case == 'bars':
        checks['changed_preview_and_selected_elsewhere'] = any('l_b_length_states 1 2 4 4 1' in l for l in lines) and any('live_buffer_2' in l for l in lines)
    if case == 'guards':
        checks['clear_and_invalid_lengths_rejected'] = any('Buffer_busy' in l for l in errors) and sum('Set_fixed_length' in l for l in errors)==3
    result['files']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (capture,array,events)}
    result['passed']=all(checks.values())
    result['scope']='Actual recorded arrays and player/mixer samples. No listening, general transition or DAW acceptance.'
    return result

def playback(capture, case):
    x=read(capture,6)
    ranges = {
        'switch': [('live_1',.5,1.3),('sample_1',1.7,2.7),('live_1_return',3.1,4.1),('sample_2',4.5,5.5)],
        'hardware': [('first_direction',1,2),('second_direction',4,5)],
        'hardware-take': [('recorded_hardware',2.5,3.5),('recorded_hardware_loop',4,5)],
    }[case]
    windows=[]
    for label,start,end in ranges:
        a=x[int(start*48000):int(end*48000),2:6]
        windows.append({'buffer':label,'seconds':[start,end],
                        'rms_player_LR_mixer_LR':np.sqrt(np.mean(a*a,axis=0)).tolist(),
                        'maximum_mixer_gain_error':float(np.max(abs(a[:,2:4]-.15*a[:,:2])))})
    checks={'finite':bool(np.isfinite(x).all()),
            'audio_in_all_windows':all(min(w['rms_player_LR_mixer_LR'])>1e-4 for w in windows),
            'configured_mixer_gain':all(w['maximum_mixer_gain_error']<2e-6 for w in windows),
            'stopped':bool(np.max(abs(x[-12000:,2:6]))<1e-7)}
    return {'windows':windows,'checks':checks,'passed':all(checks.values()),
            'sha256':hashlib.sha256(capture.read_bytes()).hexdigest(),
            'scope':'Steady playback through the original player/mixer. Transition-edge quality and listening acceptance remain separate.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('case',choices=['fixed','early','bars','guards','gap','switch','hardware','hardware-take'])
    p.add_argument('capture',type=Path);p.add_argument('array',type=Path,nargs='?');p.add_argument('events',type=Path,nargs='?')
    args=p.parse_args()
    if args.case in ('switch','hardware','hardware-take'):
        r=playback(args.capture,args.case)
    else:
        if args.array is None or args.events is None:p.error('This check needs an array export and event log.')
        r=analyze(args.capture,args.array,args.events,args.case)
    print(json.dumps(r,indent=2));raise SystemExit(not r['passed'])
