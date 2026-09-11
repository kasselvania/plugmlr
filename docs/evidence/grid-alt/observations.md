# CUT-page ALT transport checkpoint

Native Mac plugdata 0.9.4 nightly 98ae0f78b / Pd 0.56.3, executable SHA-256
`86179a37e58e7a0f0436fc555f56ce41892e3f32ed19b4a3ba8f1cfe3c17476e`.
Executable hash and bundle version rechecked. Host 48 kHz, device block 512;
DrumLoop.wav is stereo 44.1 kHz. No service or dependency changes.

## Results and limits

- `native-keys.json`: 35 actual native Pd-Lua sequences pass. Covers duplicate
  downs, key-before-ALT, both release orders, separate players, disconnect with
  held keys, reconnect, inactive rows and malformed coordinates/messages.
- Actual MLR native UI: scheduled ALT opened Player 1 and showed Playing;
  bounded capture ended with Player 2 Paused. An ALT attempt on empty player 3
  left the panel at Empty buffer. No new transport state machine exists.
- `player-and-master.wav`: 575860 frames, six float channels: Player 1 L/R,
  Player 2 L/R, master L/R. Duration 11.9971 seconds, within one device block
  of the 12-second timer. `listening.wav` is the master pair.
- `audio-checks.json`: nine checks pass. Player 1 is silent in its scheduled
  pauses, resumes after rapid toggles, and resumes at the saved position rather
  than the queued slice after Pause cancellation. Player 2 matches the expected
  advancing source in five windows (correlations >0.998). Finite stereo master,
  peak <0.503, final paused tail silent. No universal click/dropout guarantee:
  correlation windows do not test every transition sample perceptually.
- Physical ALT/row acceptance: user answered “yes. this works” when asked
  whether ALT+row toggles once without slicing and changing rows shows the
  correct player view. Listening to the separate retained file remains unreported;
  the physical report is kept distinct from file-based listening acceptance.
- Recorder completion was observed as `grid-alt-capture-stopped: bang`. The
  fixture stopped writing and disabled DSP automatically. It was then closed.
  Grid release reported verified_lease_free; MLR and detached views were closed
  without saving temporary taps. Saved MLR reopened and DSP restored.
- Ready for user: both drum slots loaded, player 1 1x and player 2 0.5x, gains
  0.4/0.3, master 0.75, 1/16 quantization, internal clock running at 110 BPM.
  Both players initially Stopped so ALT can start them. Grid connected under a
  verified lease. No recorder, injected-key receiver or mixer tap remains open.

## Repeat

Run source guards from the repository root:

```
python3 tests/check_grid_alt.py
python3 tests/check_grid_feedback.py
python3 tests/check_grid_adapter.py
python3 tests/check_tempo_fit.py
lua tests/mlr_grid_compat_spec.lua
```

Open a fresh `tests/grid-cut-keys-check.pd` in native plugdata, then run
`python3 tests/check_grid_cut_native.py`. It uses isolated localhost UDP ports
17932/17933, no global musical messages, audio, or device ownership. Close the
fixture after the check. When editing the Lua class during a session, Pd-Lua
caches definitions: native `pdluax reload grid-cut-keys` reloads only this class.
See the [upstream Pd-Lua reload documentation](https://agraef.github.io/pd-lua/tutorial/pd-lua-intro.html).

For the bounded audio test, stop other playback and load DrumLoop into slots
1/2. Both players must be Stopped, Forward, 1x, Fit/Reset off, immediate cuts,
internal clock stopped. Use gains 0.4/0.3 and master 0.75. Claim the Grid so the
actual gesture layer is enabled. This capture uses scheduled keys, not physical
key gestures; do not press keys during it.

Temporarily add `r grid-alt-check-key` to `pd grid-input-output`, connecting to
`grid-cut-control` (current objects 84 to 83). Inspect native `ls` before relying
on indices. In `pd mixer`, add `s~ plugmlr-record-check-left/right` fed by final
master multipliers 20/21 (temporary sends 47/48). Open `tests/grid-alt-audio.pd`.
Refresh DSP while stopped and send `grid-alt-capture bang` once. It arms its
12-second completion timer before starting writesf. Completion stops the writer
and switches DSP off independently of any later UI/agent action.

The schedule is retained in `audio-schedule.json`: ALT starts players at 0.1/
0.2s; pauses/resumes A at 2/3s; attempts empty track 3 at 4s; sends four rapid
A toggles at 6s; queues a quantized slice with the clock stopped at 8s, then
pauses A before starting the clock; resumes A at 9s; pauses both at 11s.

Retain `/tmp/grid-alt.wav`, close the fixture, release the Grid, and reopen
saved MLR without saving diagnostic connections. Restore DSP and desired user
settings. Copy the capture to this folder's `player-and-master.wav` and run
`tests/analyze_grid_alt.py` with NumPy and ffmpeg. Preserve earlier captures when
validating a later revision. Source-matching uses ffmpeg resampling as an analysis
reference, not as a substitute playback implementation.

## Rejected diagnostics

`rejected-list-connection.json` retains the initial no-output test. Native console
reported a missing list handler at the connection inlet. A one-element list is
now accepted alongside float. Reopening alone retained the cached class; explicit
class reload was required. The next console read exposed a separate fixture
error: netsend lacked its `send` prefix. The monitor was fixed before the passing
run. Neither diagnostic is audio-engine failure evidence.

`rejected-silent-reference-correlation.json` retains an invalid analysis that
normalized numerical FFT residue against the source's silent tail. Near-zero
reference energy is now excluded. `rejected-repeated-source-match.json` retains
the subsequent global-match ambiguity: repeated drum phrases selected other bars.
The final B check measures correlation at its expected continuously advancing
source window, allowing ±5 ms alignment; matching another bar cannot pass it.
These are analysis corrections on the same retained recording, not audio edits.
