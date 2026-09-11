# Two-row playback feedback check

2026-09-11, native Mac plugdata 0.9.4 nightly, build 98ae0f78b, Pd 0.56.3.
Executable SHA-256: `86179a37e58e7a0f0436fc555f56ce41892e3f32ed19b4a3ba8f1cfe3c17476e`.
Musical capture: 48 kHz host, 512-frame device buffer, bundled DrumLoop.wav.
This is not new 44.1 kHz or Bitwig acceptance. Installed SerialOSC unchanged.

## Observed results

- `native-message-checks.json`: 29 command sequences through actual Pd row
  helpers. Forward/reverse positions, endpoint 1, repeated columns, Pause,
  Stop, readiness/switching, independent second row, invalid positions and
  reconnect redraw passed. This silent fixture does not claim hardware output.
- `player-and-master.wav`: 16 seconds, four float channels: player L/R then
  post-master L/R. `listening.wav` is its post-master stereo pair.
- `audio-checks.json`: six checks passed. Master peaks 0.4392/0.4412;
  finite output, no clipping, active stereo throughout each playing second,
  and silence after 15.1 seconds. Per-second RMS cannot exclude brief dropouts.
- Maximum master adjacent step is 0.4143/0.4142. Percussive source transients
  make this an unsuitable universal click detector. No claim of click-free
  playback follows from these numbers.
- Live physical slicing acceptance: user reported, “yup! visible and I was able
  to play it! it works great!” after the hands-on setup below. This accepts the
  visible feedback and playable immediate slicing in that session. It does not
  establish separate quantized, two-player, or exhaustive transition acceptance.
- Retained capture listening: no explicit report for that file yet; the live
  playing report above is separate evidence.
- Physical moving marker: user confirmed, “I saw the LED moving.” This accepts
  observed movement, not every reverse/pause/reconnect behavior. Earlier connector
  acceptance covers corner LEDs and a physical row_1 key event.
- Hands-on follow-up: reselected m1000853, probed free and claimed; native panel
  showed connected. Sample 1 DrumLoop was left Playing, Forward, 1x, immediate
  slicing, Beat Reset Off, internal clock stopped; track gain 0.6, master 0.75.
  Native output meters were active. No recorder is open. This supersedes the
  earlier stopped/released cleanup state for the user’s personal slicing trial.
- Native completion printed `grid-musical-stopped: bang`; player showed Stopped.
  Release reported `verified_lease_free`. The recording wrapper and temporary
  mixer taps were discarded, then saved MLR was reopened. Native UI shows
  loaded Sample 1, Stopped, Forward, 1x, Free and no clock ticks.

## Repeat the silent native check

Close MLR first to avoid shared test symbols affecting the application. Open
`tests/grid-feedback-check.pd` in native plugdata, then run from repo root:

```
python3 tests/check_grid_feedback_native.py
```

The fixture receives localhost UDP 17930 and reports on 17931. Close it afterward.
Run source guards separately:

```
python3 tests/check_grid_feedback.py
python3 tests/check_grid_adapter.py
python3 tests/check_tempo_fit.py
lua tests/mlr_grid_compat_spec.lua
```

## Repeat the musical/physical check

1. Open only this checkout's MLR. Load bundled DrumLoop.wav into Sample 1.
   Choose immediate slices, free speed 1x, Forward, reset Off and internal
   clock stopped. Raise track gain to 0.6 and master to 0.75, starting quietly.
2. Open Grid_connection, select the 128, Probe then Claim when free. Press Play.
   The second physical row should track whole-content position. Try its slice
   keys, reverse, Pause/Resume and Stop. Slice keys alone do not start playback.
   A second loaded player uses the third row independently. Release when done.
3. To reproduce the retained recording, add temporary passive `s~` taps from
   the two final master multipliers (objects 20/21 in `pd mixer`) to
   `plugmlr-record-check-left` and `plugmlr-record-check-right`. These taps are
   deliberately absent from the saved application. Inspect native `ls` first
   rather than assuming object indices after future edits.
4. Read the current player dollar-zero from its opened player-panel title.
   Instantiate `tests/grid-musical-check CURRENT_PLAYER_ID` in a temporary
   wrapper; qualify the abstraction path to this checkout. The ID changes on
   reload. Send `grid-musical-check bang` once. Its fixed stop timer is armed
   before recording starts; wait for `grid-musical-stopped: bang` at 16 seconds.
   Play begins at 0.1s, cuts 8/3/12 occur at 4/8/12s, reverse at 10s, Stop at15s.
   The output is `/tmp/grid-musical.wav`. Do not close or disable DSP mid-capture.
5. Close the wrapper, release the Grid and reload MLR without saving the
   temporary mixer taps. Recording completion must not depend on another turn.
6. Copy the capture to `player-and-master.wav` in this folder, then run
   `python3 tests/analyze_grid_musical.py` with NumPy and ffmpeg available.
   Preserve earlier evidence before overwriting when testing another revision.

## Rejected fixture evidence

`rejected-fixture-no-monitor.json` records a missing connection from the fixture's
connect message into netsend. No events were received. The fixture wire was
corrected before the 29 passing sequences.

`rejected-stopped-transport.wav` records the first musical attempt: slices were
sent while transport was Stopped; no explicit Play was issued. The post-master
pair is silent despite pre-mixer activity. The corrected fixture explicitly
presses Play. Master gain was also explicitly sent to 0.75 and the DSP graph
refreshed while stopped before the successful capture. Those setup changes mean
this is not evidence attributing the failed capture to a unique mixer fault.

No additional DSP fix was made in this slice. Physical gestures, listening,
other Grid rows, hotplug, Arc and Bitwig remain separate acceptance work.

## Quantized two-row hands-on setup (acceptance pending)

After immediate physical slicing acceptance, both original players were prepared
in native plugdata with bundled DrumLoop.wav in separate sample slots 1 and 2.
Player 1 runs at 1x, player 2 at 0.5x; track gains are 0.4 and 0.3, master 0.75.
Both panels visibly show Playing, Forward, Quantize enabled, slice grid 1/4,
Fit off, Reset Off. The shared internal clock shows Ticking at 110 BPM.
The output meter is active. No recorder or additional audio-producing fixture
was opened. No patch implementation was changed for this setup.

Physical second/third rows target players 1/2 respectively. Try alternating
rows and pressing several keys before a beat: each player's last pending slice
should commit on its next quarter-note tick. Its marker should continue showing
actual playback until that commit, and the other row should remain independent.
Clock-quantized cuts do not tempo-fit the free-running sample or synchronize its
drum transients. Both loops are intentionally left playing for the user.
Physical quantized timing and two-row independence await the user's report.
