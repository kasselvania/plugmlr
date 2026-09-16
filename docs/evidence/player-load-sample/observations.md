# Player-local sample loading

2026-09-14. Base: `a66b9c08f7f95e7319f6cadd6b21ac41833b738f`.

## Native observations

Runtime console: plugdata 0.9.4 nightly `98ae0f78b`, Pd 0.56.3,
ELSE 1.0-rc14, Cyclone 0.9-4, pdlua 0.12.23.

The silent fixture uses real `sample-data` slots 901/902 and the production
`player-sample-load` and `player-panel` abstractions. It has no player engine,
audio output or recording. Its layout screenshot therefore has placeholder
state and Player 901, not a claim that a real musical player was exercised.

- Message-triggered load opened each slot's own chooser. Selecting the repository
  `DrumLoop.wav` reported ready=1, 44.1 samples/ms, 39492.6 frames/slice,
  start=0, end=631881 for both slots. The existing invalidation preceded readiness.
- Before/after-cancel exports from slot 901 were byte-identical. Decoded stereo
  samples matched the original 24-bit WAV exactly: maximum absolute error 0.
  Source/export hashes and counts: [array-check.json](array-check.json).
- `live` hid the button and label; a subsequent `click` command emitted no load
  and opened no chooser. `sample`, `switching 1`, `click` also emitted no load.
  `switching 0`, `slot 902`, `click` opened the second slot's chooser.
- The coordinate mouse tool initially failed to activate the standalone helper
  at the fixture's upper-left. Its cause remains unknown. The same tool DID open
  the chooser by clicking Load sample in the production player-panel view. That
  chooser was cancelled. This clears the new button's mouse check, not the older
  Clear/Discard mouse issue or general UI acceptance.
- Revised panel fits Load sample beside Slot, shifts Prev/Next to its right and
  moves Overview one row up. Live leaves an empty GOP outline where Load sample
  was; no actionable widget/label remains there.
- Console showed no new object/connection errors. Existing `grid_not_attached`
  output remained visible; this is not a Grid validation slice.
- Both test tabs were closed. Normal MLR stayed open: Player 1 paused on Sample 1,
  Player 2 stopped on Sample 1. No production sample was overwritten or reloaded.

[Loader console](native-load-console.png) ·
[Sample layout](native-player-layout.png) ·
[Mouse-triggered load console](native-button-console.png) ·
[Live layout](native-live-layout.png)

## Source findings and limits

The new helper only sends the existing load command. `sample-data.pd` receives
the chosen path, broadcasts `buffer-will-change`, invalidates readiness, waits
20 ms and uses its existing stereo `soundfiler read -resize`. The matching
`buffer-selection` sends Stop before resize. Ready metadata then updates the
original player's full-content bounds. Cancel never reaches that path.
No speed, direction, glide, quantize, tempo-fit or Beat Reset reset was added.
Control retention and reset are source-traced here, not newly tested in audio.

Inherited behavior remains: loading slot N also emits `N-sample-loaded`, which
can select Sample N in player N. Failed reads can invalidate existing content;
this is not transactional rollback. These were not expanded into an unrelated
loader/selection rewrite. Shared-slot users stop before replacement.

No audio playback, host-rate, Bitwig or listening test was performed for this
UI-only change. User review on the ordinary player remains open. Reopen MLR to
load the edited abstractions; its currently open instance retains the old view.

## Repeat procedure

1. Open `tests/player-load-sample-check.pd` in native plugdata; its declare points
   at the repository root. For the recorded run, this fixture was copied to a
   temporary directory containing symlinks to the repository `.pd`/`.pd_lua`
   abstractions. Do not run two copies of this fixture together.
2. In plugdata's console send `901-open-player-view bang`, click **Load sample**,
   select repository `DrumLoop.wav`, and inspect the console. Close the view to
   return to the fixture. Use `load-button-check slot 902` for the other slot.
3. Console commands `load-button-check live`, `sample`, `switching 1`,
   `switching 0`, and `click` exercise the documented guards. Each is a separate
   console command with the `load-button-check` prefix.
4. Export slot 901 with `load-button-export write -wave -bytes 4 /tmp/before.wav
   0-sample_buffer_901 1-sample_buffer_901` (one line). Open and cancel the chooser;
   repeat export to `/tmp/after.wav`. Compare bytes and decoded samples against
   `DrumLoop.wav`. The retained JSON describes this run, not synthetic audio.
5. Run `python3 tests/check_ui_overview.py` and
   `python3 tests/check_patch_connections.py player-sample-load.pd`, then repeat
   the index check for `tests/player-load-sample-check.pd`. All passed, as did
   `git diff --check`. These are structural checks, separate from native results.
6. Ordinary-session follow-up: reopen MLR when its current unsaved audio/state
   can be discarded; select Sample/Slot from Player 2 and use Load sample. Apply
   a partial loop and non-default player controls, then replace the file. Check
   full-content position/loop and retained controls, cancellation, and another
   player sharing the same slot. This step is not recorded as executed here.
