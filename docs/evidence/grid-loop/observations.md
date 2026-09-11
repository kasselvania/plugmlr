# Two-key CUT loops

Native Mac plugdata 0.9.4 nightly 98ae0f78b / Pd 0.56.3. Executable SHA-256
`86179a37e58e7a0f0436fc555f56ce41892e3f32ed19b4a3ba8f1cfe3c17476e`.
Host 48 kHz, device block 512; stereo DrumLoop.wav is 44.1 kHz, 631881 frames.
No installed service or dependency changes. Physical two-key testing and listening
acceptance remain pending; scheduled keys do not establish physical usability.

## Executed checks

- `native-keys.json`: 78 native Pd-Lua sequences pass, including the original ALT
  checks, pair release/press orders, endpoints, third-key cancellation, separate
  rows, ALT/external cancellation and detach with held keys.
- `native-regions.json`: 20 actual Pd bridge cases pass. Nonzero content start,
  sample-rate conversion, invalid lengths/types/bounds, and cancellation events.
- `player-master-and-bounds.wav`: 16 seconds, 768000 frames, eight float channels.
  Channels 1/2 are Player 1, 3/4 Player 2, 5/6 actual master stereo. Channels 7/8
  are committed loop bounds in seconds, NOT audio. `listening.wav` contains only
  the master pair. Do not audition the eight-channel file as ordinary audio.
- `audio-checks.json`: 17 checks pass. Actual bounds include both selected cells;
  reverse press order is equivalent. A queued first slice does not erase the new
  loop. Reverse playback correlates with reversed source above 0.99997. Player B
  continues at its expected source timeline in six windows (minimum 0.9966).
  Paused/stopped edits preserve master silence; ordinary slices restore full
  content. All output is finite, audio peaks below full scale, final master silent.
- The original stopped-slice path has pre-mixer activity (A RMS 0.210807 during
  12.2–12.9 seconds). Its contribution at master is below 2.99e-8 after subtracting
  B at its known gain. Do not describe this as universal internal silence.
- Correlation windows do not prove every transition free from clicks/dropouts.
  Repeated drum phrases make a global reverse match unsuitable for proving exact
  source position. No universal click-free, DAW or 44.1 kHz host acceptance here.
- Native panel showed Empty buffer / Invalid_range for the empty-track request.
  The fixture printed `grid-loop-capture-stopped` after automatically stopping
  writesf and DSP. It was closed; Grid released (verified_lease_free), MLR and
  detached views closed. Clean saved MLR was reopened without diagnostic taps.
  During final setup an incorrectly addressed console selection command produced
  `canvas: no method for 'sel'`; using the console's local selection command fixed
  setup. This was not a playback error. Grid then connected with verified_lease.

## Repeat procedure

From repo root run `python3 tests/check_grid_loop.py` and the existing ALT,
feedback, adapter and tempo-fit source guards plus `lua tests/mlr_grid_compat_spec.lua`.
Open a fresh `tests/grid-cut-keys-check.pd` in native plugdata and run
`python3 tests/check_grid_loop_native.py` (localhost UDP 17932/17933). Close it.
Open `tests/grid-loop-region-check.pd`, run `python3 tests/check_grid_region_native.py`
(17934/17935), then close it. These fixtures have no audio or device claim.
After editing Lua in a running session, explicitly reload the class with
`pdluax reload grid-cut-keys` before creating fresh objects.

For audio, load DrumLoop into slots 1/2. Stop both players; Forward, 1x, Fit/Reset
off, immediate cuts, internal clock stopped. Track gains 0.4/0.3, master 0.75.
Claim the Grid; do not press physical keys during the schedule. In the native
`pd grid-input-output` temporarily connect `r grid-loop-check-key` to its actual
`grid-cut-control` (observed objects 84 -> 83). In mixer temporarily tap final
master multipliers 20/21 with `s~ plugmlr-record-check-left/right`. Inspect native
object listing before relying on indices. These connections must not be saved.

Determine Player 1's current dollar-zero from its native panel/canvas. Create a
wrapper instantiating `tests/grid-loop-audio <player-dollar-zero>` with the test
path resolved to this checkout. The capture used 27345; this changes on reopen.
Send `grid-loop-capture bang` once. The fixture arms a 16-second stop BEFORE
recording and is one-shot. It writes `/tmp/grid-loop.wav`; completion stops the
writer, clock and DSP without relying on a later UI command. Retained schedule
is `audio-schedule.json`: pairs in both orders, reverse, quantized first cut with
clock stopped then running, paused/stopped edits, Stop cancellation, ordinary
slice restoration, final pauses and empty-track refusal.

After completion, retain the capture, close the wrapper, release Grid, and reopen
saved MLR to discard taps. Restore DSP and user controls. Analyze the retained
file with `tests/analyze_grid_loop.py` using Python with NumPy and ffmpeg. The
analysis resamples the reference only; playback remains actual plugdata audio.
Extract channels 5/6 as a separate stereo listening file.

## Rejected analysis

`rejected-python-rounding.json` retains an analysis failure: Python's ties-to-even
rounding expected frame 315940 where Pd's positive half-up conversion produces
315941. The analyzer now uses floor(x + 0.5), matching the existing region
validator. This corrected the analysis of the same capture, not the audio.
