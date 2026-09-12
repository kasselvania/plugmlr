# Combined two-lane CUT checkpoint

Base `ac40fc85d3f4d02ffeb3087d7c0904bcad94e379` (accepted MOD workflow, PR #31
still unmerged). No production patch, Lua, dependency or installed service was
changed. This is a validation/evidence slice.

Native Mac plugdata 0.9.4 nightly 98ae0f78b / Pd 0.56.3; executable SHA-256
`86179a37e58e7a0f0436fc555f56ce41892e3f32ed19b4a3ba8f1cfe3c17476e`.
Host 48 kHz, device block 512. Sample 1 is the repository's stereo DrumLoop.wav,
44100 Hz / 631881 frames. Sample 2 is its reversed, channel-swapped version at
48000 Hz / 687762 frames and gain 0.65, retained as buffer-b.wav. It is generated
with ffmpeg `areverse,pan=stereo|c0=c1|c1=c0,volume=0.65`, resampled to 48000 Hz.

## Results

The single native capture contains exactly 1440000 frames (30 seconds).
`checks.json` records 27 passing checks:

- A alone first; then both read the same logical sample buffer. B stays steady
  while A cuts, loops, reverses, changes speed, pauses/resumes and switches buffer.
  Roles then swap. Each steady trajectory deviates by at most 0.0375 file frames
  from its expected linear progression (floating-point representation).
- The steady A passage at 11–19.8 seconds and the corresponding steady B passage
  at 1.2–10 seconds are **bit-identical in both audio channels**, with zero sample
  difference. This is actual captured audio, not a numerical sampler model.
- Master output matches the expected .3*A + .225*B mix within 5.97e-8 while both
  lanes are stably active. A Pause/Stop leaves B's master contribution unchanged;
  B Pause/empty-buffer refusal leaves A's unchanged.
- Same-buffer and different-buffer operation, stereo source matching after swaps,
  independent two-key and MOD ranges, overlapping cross-row focus/held gestures,
  ALT cancellation, Stop cancellation and full-content restoration all pass.
- Both lanes run rapid cuts and modifier gestures in the final section. Empty
  sample 3 refuses playback and remains silent; selecting sample 2 recovers.
  Quantized cuts run against the internal clock at the end. Final master is silent.
- All 16 recorded channels finite. Audio channel peaks are below full scale;
  maximum master peak 0.503901. No unexpected silent 10 ms block was detected
  where the measured source reference was energetic and the lane stably active.

The silence check excludes 50 ms after transport/buffer-state changes; it does
not exclude cut/crossfade command windows. Correlation uses linear interpolation
as an approximate reference for table playback. These checks do not establish
universally click-free transitions. Maximum master adjacent-sample step is
0.303174; the source contains sharp drums, so this is reported rather than
mislabelled as a click. The user listened to the master capture and reported: “nope. it sounds great.”
This is listening acceptance of this capture, separate from the numerical checks.

This run uses scheduled keys through the actual Grid input handler with a verified
lease, not physical key presses. Native console/panel showed the resulting state
changes and final Paused state. Physical combined-gesture/LED acceptance remains
separate. No DAW, 44.1 kHz host, nonzero speed slew, Beat Reset/tempo-fit collision,
maximum-lane or separate full-application instance acceptance is claimed.

## Retained files and correction to analysis

`lanes-master-state.wav.gz` is the losslessly gzip-compressed original 16-channel
float WAV. Channels (one-based): 1/2 A stereo, 3/4 B stereo, 5/6 master stereo,
7/8 actual logical vline positions in file frames, 9/10 A loop start/end, 11/12 B
loop start/end, 13/14 A/B state bits, 15/16 A/B selected buffer IDs. State bits:
ready=1, playing=2, paused=4, switching=8. IDs 1/2 identify the test sample slots;
0 means another/empty slot. Metadata channels must NOT be auditioned as audio.
`listening.wav` contains only master L/R converted to PCM16 for audition.

`rejected-linear-gain-reference.json` retains an initial failed gain check. A
linear interpolation reference differed from native table interpolation by up
to 6.35% fitted gain on high-frequency material, despite high correlation.
The corrected gain/independence test compares the actual steady passages directly:
they are bit-identical for 8.8 seconds, so no interpolator assumption is needed.
The initial gain estimates remain in checks.json as reference diagnostics, not
claims of gain modulation. The recorded audio was not changed; the interpolation-based gain test was
replaced with a direct actual-audio identity test.

## Repeat and safe capture lifecycle

Generate the fixture with `python3 tests/build_two_lane_cut.py`; schedule.json
records the absolute-millisecond messages. Load DrumLoop into sample 1 and the
retained buffer-b.wav into sample 2. Keep sample 3 empty. Start both players
Stopped, Forward, 1x, zero speed glide, Fit/Reset off, immediate cuts and internal
clock stopped. Gains are .4/.3 and master .75. Claim the Grid; do not play physical
keys during the scheduled capture.

Use a wrapper with `tests/two-lane-cut-audio <A-dollar-zero> <B-dollar-zero>`.
Read IDs from the actual native panels; this run used 30437 and 30466. Temporary
native connections: grid-input-output object 84 `r two-lane-check-key` -> existing
83 grid-cut-control; mixer final multipliers 20/21 -> temporary 47/48 sends
`plugmlr-record-check-left/right`. Inspect object listings before using indices.
A temporary receiver 49 `r two-lane-master-level` -> master knob 19 sets .75 via
an explicit float. Do not save these diagnostic connections.

After opening the wrapper, select buffer 2 then 1 on both stopped lanes so the
new state taps receive complete metadata. Trigger `two-lane-capture bang` once.
The one-shot fixture arms its 30-second stop BEFORE starting writesf. Completion
stops writing, disables DSP and stops the clock, independently of future UI or
agent actions. It writes /tmp/two-lane-cut.wav.

Completion was observed in the native console as `two-lane-capture-stopped`, with
DSP Off. The recorder was closed, Grid released (verified_lease_free), MLR and
detached views closed, then saved MLR reopened to discard all diagnostic taps.
DSP, internal clock and 1/16 quantization were restored. Both distinct buffers
remain loaded for hands-on use; Player 2 is returned to half speed. Both players
initially stopped, Grid connected verified_lease, no recorder open.

Analyze with `tests/analyze_two_lane_cut.py` using Python + NumPy and ffmpeg. It
reads either the raw WAV or its gzip archive. Existing source guards pass and
production sources compare exactly to the base. A listening report should be
recorded separately, preserving both this capture and the rejected analysis.
