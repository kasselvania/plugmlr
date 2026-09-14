# Sample editor and reversible bounds

2026-09-14. Base `544f8b4d8373cdc305ce4310856e8f00cea25cd0` (PR #40).

## User workflow

After restarting plugdata with this checkout, open `mlr.pd`, select an imported
Sample in a focused player, then click **Edit sample** in the waveform header.
The original loaded file is retained. The editor follows the player's selected
sample; entering Live disables sample edits. Drag the nearest selection edge,
or enter source-file seconds in Start/End. Length is a readout. Zoom +/−,
Scroll left/right, Fit selection and Show all request cached waveform detail.

**Set player loop** commits the staged selection to that player. **Audition
loop** also starts/resumes it at its existing speed and direction; Stop is the
ordinary hard Stop. Back to player does not stop audition. **Trim sample**
changes the shared usable range, stopping matching readers first. Every slice
then divides this usable range. **Restore original** restores full loaded bounds.
Times stay in source-file coordinates: trimming 3–11 s gives an 8 s usable sample
with ruler endpoints 3 and 11. No source file or array sample is overwritten.

Trim/Restore changes apply to every player reading that shared buffer. Edits
are not persisted by saving the Pd patch. Replacing the file or closing the
application loses the trim state. Saving an edited imported copy and offline
stretching/tuning remain follow-up work, not implemented controls.

## Source map

- `player-waveform`: separate seconds ruler and explicitly prefixed S1–S16 IDs.
- `player-sample-edit`, `sample-editor-panel`: Sample-only entry and native widgets.
- `sample-editor`: staged selection, mouse handling, view range, and ordinary
  messages to existing loop/transport and buffer APIs. No audio processing.
- `sample-trim`: one owner per imported slot, original/effective bounds, 20 ms
  commit, invalidation and new-load cancellation. No copying/resizing of arrays.
- `buffer-view-data`: existing 1024-frame/2 ms bounded scans, extended with
  cancellable range requests and a shared queue. Full-content cache is retained;
  painting never reads arrays. Stereo channel extrema remain separate.
- Original player: one first_index addition to slice positions; no reader or
  fade algorithm rewrite. Content-change Stop uses the same 6/9 ms sequence but
  preserves direction. Normal Stop still resets direction.

Interfaces: `<slot>-sample-edit trim <start_seconds> <end_seconds>` or `restore`.
Editor actions are on `<track>-sample-editor` (`start`, `finish`, `loop`,
`audition`, `stop`, `trim`, `restore`, `zoom-in`, `zoom-out`, `left`, `right`,
`selection`, `all`). The editor validates ready/type/switching and bounds. The
buffer independently rounds to source frames and validates the trim. Minimum
four frames; reversed, non-finite or out-of-range requests are rejected.

## Native observations

Runtime: plugdata **0.9.4 nightly 98ae0f78b**, Pd **0.56.3**, ELSE 1.0-rc14,
Cyclone 0.9-4, pdlua 0.12.23. Capture host rate is 48 kHz; input file is 44.1 kHz.
The user's normal MLR and loaded samples stayed open. The test had no DAC and
used isolated slots/tracks 901/902, actual players and actual track mixers.
Only the test selector's slot limit was extended; production remains 1–16.
Test copies have unique Lua class names to avoid cached definitions from the
user's existing patch. Their source hashes are retained in `final/source.json`.

The visible editor mouse drag changed the numeric selection without a loop
command. Visible Trim and Restore buttons updated the usable/full bounds.
Back to player showed the two distinct rulers and the Edit sample entry.
Zoom and Scroll changed the displayed seconds range and rebuilt detail.
The ordinary numeric command path staged and auditioned 1.2–1.8 seconds.

All captures stop at nine seconds, with an independent ten-second watchdog.
No recording depended on the next agent turn. The test tabs were closed after
verification. A full restart and user usability/listening review of the ordinary
application remain open; this is not Bitwig or project-save acceptance.

## Numerical checks

`final/analysis.json` is produced by `tests/analyze_sample_editor.py` from the
native eight-channel recording: mixer 901 L/R, mixer 902 L/R, player 901 L/R,
player 902 L/R. `final/listening.wav` sums the two actual mixer stereo outputs
without normalization. It is a diagnostic tone sequence, not a musical demo.
`final/capture.wav` retains every sample, including all transition windows.

Checks cover nonzero trim start, full Restore, invalid bounds, reverse and
forward slicing, both players sharing a buffer, another buffer remaining
audible during trim, load cancelling a pending trim, selection/reselection,
editor audition and Stop. Frequency and RMS checks distinguish actual advancing
playback from held endpoints/DC. Position traces verify signed motion and bounds.
Stop gaps are checked in the actual mixer outputs as well as reader taps.
Original RAM exports are compared exactly with the source stereo samples.
Global peaks and adjacent-sample steps include all transitions; they do not
establish universally click-free playback. No listening acceptance is claimed.

## Failures retained and repaired

The first pass had fixture-only missing live arrays, cached old Lua classes,
editor patch cords visible on the page, and filename loss on trim readiness
invalidation. `first-pass/` retains the source manifest, events, raw audio and
native screenshot. Those results do not accept the final UI or zoom behavior.

Shutdown initially sent cancellation after its buffer disappeared. A first
notification attempt in finalize also failed: the actual Pd-Lua implementation
removes receive bindings before finalize. `native/failed-shutdown.png` retains
that error. Notification/cancellation now happens before base-class teardown.

The final state trace found Reverse reset by content-change Stop. This was
repaired in the existing Stop path, with direction-retention assertions added
rather than accepting the earlier source-only claim from PR #40.

A regression fixture initially pressed Play after player 902 had automatically
resumed on buffer selection, inadvertently pausing it. `fixture-toggle/` retains
that failed run and cause. The duplicate Play was removed; the audible-other-
buffer assertion was retained. This was a fixture correction, not an audio fix.

Final checks passed: 48 kHz host / 44.1 kHz file, nine seconds, all finite,
unchanged original stereo samples, expected pitches and levels, correct signed
motion, retained Reverse through content changes, preserved trim on reselection,
new-load cancellation, and a different buffer remaining audible during trim.
Peak/step numbers and all windows are in `final/analysis.json`. The actual
console was clean after final load/run/close. No listening report was supplied.

[Editor](native/editor-final.png) · [Drag](native/drag-selection.png) ·
[Trim](native/trim-applied.png) · [Zoom/pan](native/zoom-pan.png) ·
[Player rulers](native/player-rulers.png) · [Shutdown](native/clean-shutdown.png) ·
[Listening WAV](final/listening.wav)

## Repeat

1. `python3 tests/build_sample_editor_check.py` prepares
   `/tmp/plugmlr-sample-editor/check.pd`, its deterministic stereo file and score.
2. Open that fixture in the Mac runtime and send `editor-check-run bang` from
   its native console. It is silent at speakers. Wait for `editor-check-stopped`.
3. Run `python3 tests/analyze_sample_editor.py` with numpy available. It reads
   actual captured samples and events, writes analysis JSON and a listening WAV.
4. Run `lua tests/check_sample_editor.lua` for control/cache edge cases. It
   executes production Lua with a Pd message/clock shim; it is not native audio
   evidence. Run `python3 tests/check_ui_overview.py` and Pd connection checks
   on all changed patches. These preserve unrelated engine wiring explicitly.
5. Inspect and operate the native editor, then close editor and fixture and read
   the console. Preserve actual runtime failures separately from unit outcomes.

Remaining limits: no 44.1 kHz host run in this slice (the active user session's
audio configuration was left alone), no extreme-short-loop performance claim,
no spectrum/tuning/stretch tool, no edited-copy export/persistence, and no new
physical Grid/Arc validation. Source trim keeps full original RAM allocation.
