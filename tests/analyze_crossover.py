"""Check handoff ownership in actual bounded-player-capture recordings.

python tests/analyze_crossover.py CAPTURE.wav --mode speed|cuts|transport
Accepts the retained NPZ format too. Requires NumPy and ffmpeg/ffprobe.
This inspects native reader ramps; it neither synthesizes playback nor establishes
universal audibility. A two-reader burst may reuse an incoming reader above zero.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from analyze_speed_capture import read


def inspect(samples, host, mode):
    x = samples.astype(float)
    if x.shape[1] not in (8, 10):
        raise ValueError('This check requires the reader position/gain channels')
    result = {'sample_rate': host, 'frames': len(x), 'channels': x.shape[1],
              'duration_s': len(x)/host, 'nonfinite_samples': int((~np.isfinite(x)).sum())}
    if result['nonfinite_samples']:
        return result
    limit = 20 if mode == 'speed' else 7
    indices = np.flatnonzero(np.abs(np.diff(x[:, 2])) > 1000) + 1
    events = []
    for n in indices:
        t = n / host
        if not .1 < t < limit:
            continue
        if mode == 'transport' and any(abs(t-stop) < .003 for stop in (1.004, 3, 4.004)):
            continue
        match = [abs(x[n, p]-x[n, 2]) < .1 for p in (4, 6)]
        # An inactive reader may already sit near the new entry boundary.
        # Identify the owner by its match to the master, not by jump size.
        incoming = [v for v in (0, 1) if match[v]]
        event = {'time_s': t, 'master_from_to': x[n-1:n+1, 2].tolist(),
                 'reader_frame_deltas': (x[n, [4, 6]]-x[n-1, [4, 6]]).tolist(),
                 'gain_taps_at_jump': x[n, [5, 7]].tolist(),
                 'audio_step_at_jump': np.abs(x[n, :2]-x[n-1, :2]).tolist(),
                 'only_incoming_retargeted': False}
        if len(incoming) == 1:
            new = incoming[0]
            old = 1-new
            event['incoming_reader'] = new
            event['only_incoming_retargeted'] = abs(event['reader_frame_deltas'][old]) < 16
            event['incoming_above_005'] = bool(x[n, 5+2*new] > .05)
        events.append(event)
    result['handoffs'] = events
    result['ownership_failures'] = sum(not e['only_incoming_retargeted'] for e in events)
    result['incoming_reuse_above_005'] = sum(e.get('incoming_above_005', False) for e in events)
    result['audio_peak'] = np.abs(x[:, :2]).max(axis=0).tolist()
    if x.shape[1] == 10:
        result['dsp_flags_present'] = True
        # Restrict to short handoff windows. Raw gain data remains invalid after
        # switch~ disables a reader; flags allow that held block to be excluded.
        windows = []
        for e in events:
            n = round(e['time_s']*host)
            b = min(len(x), n+round(.015*host))
            effective = x[n:b, 5]*x[n:b, 8] + x[n:b, 7]*x[n:b, 9]
            windows.append({'time_s': e['time_s'],
                            'gain_sum_min': float(effective.min()),
                            'gain_sum_max': float(effective.max())})
        result['gain_windows'] = windows
        result['gain_limit'] = 'DSP flags and raw ramps are block-ordered probes; compare any deficit with actual stereo output before attributing an audible dropout.'
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--mode', choices=('speed', 'cuts', 'transport'), required=True)
    args = parser.parse_args()
    samples, host = read(args.capture)
    print(json.dumps(inspect(samples, host, args.mode), indent=2))
