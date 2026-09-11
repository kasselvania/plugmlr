# Release continuity correction

User rejected the initial two-key behavior: release restarted the first slice.
This was the Apply path's explicit entry jump, not another key-down. User chose
immediate wrap if already beyond the new boundary. Previous evidence remains
retained but does not accept that rejected musical behavior.

Native Mac plugdata 0.9.4 nightly 98ae0f78b / Pd 0.56.3, same runtime as parent
checkpoint. 48 kHz host / 512 device block, 44.1 kHz stereo DrumLoop.wav.
`player-master-position.wav` contains 575859 frames (11.9971 seconds, within one
device block of the 12-second timer). Channels 1–6: A stereo, B stereo, master
stereo; 7/8: committed bounds in seconds; 9: actual logical vline signal in
seconds; 10: queried current position in seconds. Only `listening.wav` is for
ordinary stereo audition. Numerical results are not a user listening report.

Twelve checks pass in `checks.json`. The whole 200 ms windows spanning releases
at 1.8 and 6.8 seconds have continuous forward/reverse position steps, not an
entry restart. Both actual audio channels match the native source sampled at
that measured position (correlations >0.9985 forward, >0.9996 reverse). At 5.4s,
position was outside the new range; it wraps immediately to the entry. Bounds,
finite output, headroom, active master and final silence pass. This is a targeted
regression check, not universal artifact-free or DAW acceptance.

`rejected-source-reference.json` records the first analysis attempt using an
ffmpeg band-limited 48 kHz reference, which correlated only 0.9627 in the forward
window. The source's high-frequency content and the native table interpolation
are different from that resampler. The corrected check uses the native 44.1 kHz
file at measured positions with the original reader's +1 table offset and a
linear interpolation reference; no audio was changed. It covers the entire
release window and both stereo channels. It is an approximate interpolation
reference, not an assertion of bit-exact tabread4 output.

`native-regions.json`: 20 actual native bridge checks pass with the new `keep`
selector, including malformed input and cancellation. Gesture Lua is unchanged
from the prior 78-sequence run; it was not rerun for this correction.

Repeat the parent's temporary tap setup and clean reload procedure. Use
`tests/grid-loop-continuity-audio.pd <current-player-dollar-zero>` instead of the
older fixture. The capture used 28353, which changes on reload. It adds two
position taps, arms a 12-second stop before recording, and writes
`/tmp/grid-loop-continuity.wav`. Schedule is in `audio-schedule.json`. Set both
players Stopped, Forward, 1x, immediate slicing, Fit/Reset off; gains .4/.3,
master .75. Run `grid-loop-capture bang` once. Completion printed
`grid-loop-capture-stopped`; DSP was visibly Off. The recorder and isolated
fixture were closed, Grid released under verified_lease_free, and saved MLR
reopened to discard all temporary wires. DSP/clock/quantized cuts restored.

Run `tests/analyze_grid_loop_continuity.py` with NumPy and ffmpeg. Run
`tests/check_grid_region_native.py` against a fresh native converter fixture.
Source guards explicitly account for the new logical query and keep dispatch;
the original reader DSP and plain/full Apply path are preserved.

During setup, untyped numeric console messages produced knob selector errors;
explicit `float` messages corrected them before capture. These setup errors were
read in the native console, not treated as DSP failures. No new patch-load error
was observed. Physical retest passed: the user answered “yes” when asked whether releasing
the second key now continues playback rather than restarting the first slice.
Listening acceptance of the separate retained capture remains unreported.
