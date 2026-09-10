"""Match recorded application audio to forward/reversed source audio.

Usage: python analyze_reverse.py SOURCE.wav CAPTURE.wav START_SECONDS [...]
Optional: --window SECONDS --region START_SECONDS END_SECONDS --period SECONDS
Requires NumPy. Default window is 0.5 s. This is offline analysis of native captures,
not a playback implementation or a substitute runtime. Source channel order is
reversed to account for the separately documented loader/reader ordering gap.
Linear interpolation supplies a matching reference, not an exact DSP oracle.
"""
import argparse
import json

import numpy as np

from analyze_handoff import read_pcm


def match(reference, recorded):
    y = recorded - recorded.mean()
    n = len(y)
    size = 1 << (len(reference) + n - 1).bit_length()
    dot = np.fft.irfft(np.fft.rfft(reference, size)
                      * np.conj(np.fft.rfft(y, size)), size)[:len(reference)-n+1]
    sums = np.r_[0., np.cumsum(reference)]
    squares = np.r_[0., np.cumsum(reference * reference)]
    energy = squares[n:] - squares[:-n] - (sums[n:] - sums[:-n])**2 / n
    denom = np.sqrt(np.maximum(energy, 0) * np.dot(y, y))
    score = np.divide(dot, denom, out=np.zeros_like(dot), where=denom > 1e-12)
    i = int(np.argmax(score))
    gain = dot[i] / energy[i] if energy[i] > 1e-12 else None
    return i, float(score[i]), gain


def cycle_match(capture, host, start, window, period):
    """Compare native audio with its next cycle within +/- two Pd blocks."""
    first = round(start*host)
    count = round(window*host)
    expected = round(period*host)
    margin = 128
    lo = first+expected-margin
    hi = first+expected+margin+count
    if lo < 0 or hi > len(capture):
        raise ValueError('Cycle comparison is outside the capture')
    target = capture[first:first+count]
    i, score, gain = match(capture[lo:hi, 0], target[:, 0])
    return {'expected_period_s': period, 'measured_period_s': (expected-margin+i)/host,
            'correlation_channel_1': score,
            'correlation_channel_2': float(np.corrcoef(
                capture[lo+i:lo+i+count, 1], target[:, 1])[0, 1]),
            'gain_channel_1': gain}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('capture')
    parser.add_argument('starts', type=float, nargs='+')
    parser.add_argument('--window', type=float, default=.5)
    parser.add_argument('--region', type=float, nargs=2)
    parser.add_argument('--period', type=float)
    args = parser.parse_args()
    source, sr, _ = read_pcm(args.source)
    capture, host, _ = read_pcm(args.capture)
    source_offset = 0
    if args.region:
        first, last = [round(t*sr) for t in args.region]
        if not 0 <= first < last <= len(source):
            parser.error('Region must be inside the source file')
        source = source[first:last]
        source_offset = first/sr
    if args.window <= 0 or min(args.starts) < 0:
        parser.error('Use a positive window and nonnegative capture times')
    assert source.shape[1] == capture.shape[1] == 2
    references = {}
    for speed in (.5, 1., 2.):
        for direction in (1, -1):
            positions = np.arange(0, len(source)-1, speed*sr/host)
            if direction == -1:
                positions = len(source)-1-positions
            references[speed*direction] = (
                np.interp(positions, np.arange(len(source)), source[:, 1]),
                np.interp(positions, np.arange(len(source)), source[:, 0]))
    results = []
    for start in args.starts:
        window = capture[round(start*host):round(start*host)+round(args.window*host)]
        assert len(window) == round(args.window*host)
        candidates = []
        for rate, (left, right) in references.items():
            if len(left) < len(window):
                continue
            i, correlation, gain = match(left, window[:, 0])
            right_correlation = float(np.corrcoef(right[i:i+len(window)], window[:, 1])[0, 1])
            frame = i*abs(rate)*sr/host
            if rate < 0:
                frame = len(source)-1-frame
            candidates.append({'signed_rate': rate, 'correlation_channel_1': correlation,
                               'correlation_channel_2_same_alignment': right_correlation,
                               'gain_channel_1': gain, 'source_position_s': source_offset+frame/sr})
        candidates.sort(key=lambda r: r['correlation_channel_1'], reverse=True)
        result = {'capture_start_s': start, 'duration_s': args.window,
                  'reference_region_s': args.region, 'matches': candidates}
        if args.period:
            result['next_cycle'] = cycle_match(capture, host, start, args.window, args.period)
        results.append(result)
    print(json.dumps(results, indent=2))
