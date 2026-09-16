# Grid slice launch and 80 ms loop grace period

Base: `62b7b4a30c5717a63db6d842b2194178051d1763` on PR43.
Production changes: `grid-cut-keys.pd_lua`, `sample_player_rebuild.pd`,
`pending-cut-delay.pd`. The existing player and crossover remain the audio engine.

## Current control map

| Gesture | Result |
| --- | --- |
| Ordinary slice press | Starts/resumes at that cell, or cuts there while playing. Respects that player's quantization. |
| Second ordinary key while first is held | Cuts immediately and starts the 80 ms overlap timer. |
| Either release before 80 ms | No loop and no release-triggered slice. |
| Both held at least 80 ms, then either released | Commits the inclusive range once; preserves position inside it, wraps if outside. |
| Third held key | Cuts and cancels the possible two-key loop. |
| ALT + row | Play/Pause/Resume. The accompanying cell is not a launch position. |
| MOD + row cell | Immediate one-cell loop. Does not independently start stopped playback. |
| Ordinary cut from a smaller loop | Restores whole-content bounds and launches the selected cell. |
| Stop/Pause, selection/mode changes, loop commit | Cancel relevant pending cuts through the existing paths. |

An immediate second-key cut and a later loop selection share the same gesture.
Reducing the hold time does not prevent that initial jump. Suppression, delayed
cuts or an explicit loop modifier would be different musical policies and are
not silently substituted. Queued-cut LEDs, lane 3–6 feedback and focus/navigation
synchronization remain recorded UI gaps. No new Grid layout is claimed here.

## Source shape

Gesture interpretation stays in grid-cut-keys. The original row dispatcher and
player quantizer still schedule slices. slice_input validates the dispatched
index, and stop_transition retains one pending entry (bang for Play, float for
slice) until its existing cleanup completes. Readiness is checked again after
that wait. slice_policy distinguishes ordinary slices from explicit regions,
sets transport only on a committed ordinary slice, and selects the existing
Play fade for launch from silence or Slice fade for a running cut. The typed
message is trimmed before the existing selector-based crossover interface.

This avoids Play-at-loop-start followed by a corrective slice. A newer entry
replaces the old queued entry; another Stop cancels it. The pending-cut wait also
observes Stop/Pause fades to avoid recycling a reader before its shutdown.

## Native observations and numerical results

Observed runtime: plugdata **0.9.4 nightly 98ae0f78b**, Pd **0.56.3**, pdlua
**0.12.23**. Host rate was **48000 Hz**, confirmed by the native rendered WAV;
the generated stereo source is **44100 Hz**. No device claim, DAC connection,
host-clock setting change or speaker-producing test was introduced.

Baseline capture reproduces silent first/stopped launches. Final capture passes
all 16 analyzer checks: 41 correct trajectory entries; all 16 slice cells in
both directions have the expected L/R frequency and level; first launch,
Pause launch, Stop cleanup and replacement/cancellation; quantized launch at a
controlled tick; invalid/empty/switching requests; a second uninterrupted player
sharing the buffer; loop release continuity and return to full content.

All samples are finite. Intentional stopped spans are exactly silent. Tested
active spans have no zero runs of 64 frames or longer and mixer gain error below
1e-6. Maximum adjacent post-mixer L/R step is **0.0073065 / 0.0047275**; these are
fixture-specific numbers, not universal click-free acceptance. The second lane
retains its own single trajectory while the first reverses, stops and cuts.

The separate hold-80ms native fixture passes **53 cases**, including 79/80/81 ms
boundaries, duplicate downs, independent rows, modifiers and stale-deadline
cancellation. Source checks retain **69 other components** and **10 unchanged
player subpatches**, including reader/crossover DSP, Pause, natural-loop timing,
duration conversion and current-position calculation.

## Retained failures

- `first-candidate/`: slice launch worked, but using the running Slice fade from
  silence produced a 0.026558 post-mixer step at 2252.3 ms, after a natural wrap.
  The final candidate uses the existing Play initialization for stopped/paused
  launches. Its loop-position assertion also originally counted 80 rather than
  79 ms since the actual 5801 ms trajectory; the corrected assertion uses that
  measured start. No failing audio window was excluded.
- `untrimmed-command/`: a stored list was not converted to the crossover's
  selector interface; first launch audio failed. The final path uses list trim.
- Console screenshots retain malformed-comment and invalid list-constructor
  errors encountered during development. Those source errors were corrected.
  Old errors remain visible in the console history; final runs added completion
  messages without new errors. The pre-existing Grid-not-attached warning is
  separate from these test failures.

## Repeat

1. Run `python3 tests/build_grid_launch_check.py --baseline` for the original
   implementation or omit `--baseline` for current production.
2. Open `/tmp/plugmlr-grid-launch-before/check.pd` or
   `/tmp/plugmlr-grid-launch-after/check.pd` in standalone plugdata.
3. Enter `editor-check-run bang` in the native console. Capture ends at 15 seconds;
   an independent 16-second watchdog also stops the writer and both players.
   Verify `editor-check-stopped: bang`, then close that test patch.
4. With NumPy and ffmpeg/ffprobe available, run
   `python3 tests/analyze_grid_launch.py /tmp/plugmlr-grid-launch-after` and
   `python3 tests/check_grid_launch_source.py`.
5. Run `python3 tests/build_grid_hold_check.py`, open its printed patch, and send
   `grid-hold-check-run bang`. It finishes at 26.505 seconds. Run
   `python3 tests/check_grid_hold.py`; close the silent fixture.

The builders copy source into isolated test folders, use sample/player IDs
900–902, separate controlled clock ticks and a uniquely named actual gesture
class. They retain the original player/mixer audio path. The fixture's selection
validator alone accepts these high test IDs. Passive probes and direct row
mapping are documented test instrumentation, not hardware/Grid integration.

Raw eight-channel float captures are retained as `capture.wav.gz`; decompress
to `capture.wav` to rerun the analyzer on retained results. Channels are mixer A
L/R, mixer B L/R, pre-mixer A L/R, pre-mixer B L/R. `listen-player-1.wav` is a
24-bit stereo listening extract from final mixer A. SHA-256 files bind each raw
capture; manifests bind source and fixture files. Baseline manifest production
hashes were corrected to name the three explicitly restored baseline sources.

## Listening and physical acceptance

The user accepted the earlier immediate-cut interaction at 40 ms, then rejected
160 ms as too long and requested 80 ms. New physical feel and listening reports
for this slice-launch revision are **open**. 44.1 kHz host, full DAW lifecycle,
and the remaining Grid UI gaps are not accepted by these checks.

Tests are closed and recording is stopped. The user's paused Player 1 with
Strategy_107_G.wav was left open. Fully quit/reopen plugdata and reopen mlr.pd
to test the new behavior. Quantized cuts still require a running clock.
