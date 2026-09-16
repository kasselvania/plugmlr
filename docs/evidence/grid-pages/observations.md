# PLAY/CUT Grid controls — 2026-09-15

Base: `ca75d98b77ead7382bc5e330a62249a2f0c8f221` (PR43). This checkpoint adds a
PLAY overview and page navigation to the original application. Pattern recording,
audio recording and browsing improvements are subsequent work, not implemented here.

## Controls

Physical coordinates count from 1. Top-left = PLAY, next key = CUT (startup).
Rows 2–7 correspond to Players 1–6. On PLAY, columns 3–6 focus only; 8 reverses;
10–14 select 0.25/0.5/1/2/4x; 16 is Play/Pause/Resume. The bottom row cuts/loops
the focused track. On CUT each track keeps its own complete 16-key strip.
MOD remains top-row 14; ALT remains 16. They retain their CUT/bottom-strip behavior,
while modified PLAY track controls and other reserved keys are inactive.

Focus and page changes do not open windows. The existing screen Open controls
remain available. PLAY focus and page navigation consume held keys until release
and cancel unfinished loop gestures. CUT row touches still permit simultaneous
independent gestures on several rows. Navigation preserves committed playback and
queued quantized musical cuts. Page/focus persist through detach; key/modifier state
clears. The original per-player slice quantizer and 80 ms loop qualification remain.

PLAY focus keys are dim/bright; Reverse is dim forward/bright reverse; the chosen
speed preset is bright. Transport is dark when empty/switching, dim stopped/ready,
medium paused and bright playing. The focused bottom strip and CUT rows retain dim
committed loop spans and a brighter running marker. Speed LEDs describe the preset,
not instantaneous glide or Fit's resulting speed.

## Source trace / implementation boundary

`mlr.pd` grid input -> existing `grid-cut-control` -> `grid-cut-keys` -> existing
row dispatcher, loop-region path and player controls. The key classifier adds page
routing and PLAY commands; its hold clocks only qualify loops, never drive audio.
`grid-play-controls` bridges `<track>-grid-play`, `<track>-grid-reverse`, and
`<track>-grid-set-speed` into the original private controls. It receives commands
independently of whether a player panel is visible. The original player gains only
one abstraction instance; no pre-existing DSP/control connection is edited.

`grid-playback-state` adds receive-only direction/preset exports. `grid-page-leds`
subscribes to existing state from six tracks and is the one active performance LED
renderer. Only changed complete rows reach the existing Monome adapter/cache. The
old two `grid-playback-row` instances in the root Grid subpatch become comments;
those historical components stay in place. Grid focus no longer sends Open commands.

A source check verifies the exact player addition, the exact two root replacements,
and 67 unchanged existing Pd/Lua components, including the mixer, crossover,
quantizer, buffers, recorder and clock. No Monome dependency/service changes.

## Native runtime and executed checks

Actual Mac plugdata **0.9.4 nightly 98ae0f78b**, **Pd 0.56.3**, **pdlua 0.12.23**,
DSP On. Runtime identity and console were read in the native UI. This is a control
checkpoint: host-rate/audio-quality acceptance is not inferred from these tests.

The isolated native fixture uses six original player components, slots 901–906,
and a generated 44.1 kHz stereo source. It has no DAC, recording object, Monome
session or output to the user's Grid. Control bus names and test Lua class names
are isolated; ordinary source files and their transformations are hashed in
`final/source.json`. The fixture runs for 35.45 seconds, stops its own players and
score, then writes the event log. A separate 55-second watchdog bounds the run.
It starts one second after load because the native console entry could not be
focused reliably. Completion was verified in the actual console, then the test
was closed. The original application and its loaded Funnel_80_Fm.wav remained open;
Player 1 was Paused in the final readback. No diagnostic recorder was started.

Final `check_grid_pages.py` result:

- **68/68 native key cases**, including the preceding 53 CUT hold/release cases.
- PLAY focus, reverse, all five presets and bottom-strip cuts on all six rows.
- Page/focus changes during held loops, old-key duplicate suppression, MOD/ALT
  precedence, short/qualified holds, malformed key data, detach/reconnect and
  reserved inactive controls.
- **Six original-player readbacks**: loaded, slice-launched, direction report,
  preset changed to 2x, paused, and finally stopped through existing controls.
- **299 PLAY row checks** plus complete, bounded LED messages and per-track
  focus/transport/direction/speed/bottom-marker checks against actual player reports.
- Exact source boundary, valid Pd connections and Lua syntax.

`final/analysis.json` contains individual results. `final/events.txt` contains
actual native messages; the screenshot retains final completion and earlier errors.
There is no new rendered-audio/listening claim. Prior playback acceptance remains
scoped to its own revisions and recordings.

## Rejected iterations retained

1. `rejected-command-feedback`: first candidate mistakenly used `grid-speed` for
   both a command and its report, creating a native stack overflow at load. The
   test was closed immediately. `grid-set-speed` now names the command separately;
   the source check protects this distinction. This was our implementation error.
2. That first fixture also omitted live-buffer view metadata, producing optional
   `view-get` errors. Test view-data owners were added for its isolated live arrays.
3. `rejected-fixture-markers`: raw `case`/`smoke` messages reached a list trigger,
   producing 70 trigger errors and omitting case markers. The fixture now sends
   explicit lists. Its numeric renderer prefix also concatenated as a floating
   value, so it did not receive real player reports. Numeric prefixes are now
   formatted without a fractional suffix; LED assertions verify actual readback.
4. The passing run was repeated after removing obsolete, unconnected focus/window
   plumbing from the shell. The retained final run uses the simplified shell.

Earlier console errors were left in history rather than erased. Their counts
remain unchanged in the final run; the completion count advances. No hardware or
DSP problem is blamed for these rejected implementations/fixtures.

## Repeat / physical acceptance

1. Run `python3 tests/build_grid_pages_check.py` from this checkout. It constructs
   `/tmp/plugmlr-grid-pages-check/check.pd` and writes its exact score/source manifest.
   Test IDs 901–906 must not be in use elsewhere. Do not open any other test fixture
   using those IDs at the same time.
2. Open that file in native plugdata with DSP On. It starts after one second and
   automatically stops. Read the actual console and wait for `pages-check-done`.
3. Run `python3 tests/check_grid_pages.py`. Archive results before another run.
   Close the test only after completion. This suite does not establish physical
   LED delivery or audio quality.
4. Save any live takes, fully quit/reopen plugdata to reload Lua, and open the
   original `mlr.pd`. Connect through the existing select/Probe/Claim workflow.
5. Try PLAY -> focus Player 2 -> bottom cuts -> Reverse/speed -> CUT -> PLAY.
   Check LEDs, transport independence and that Grid navigation opens no windows.
   Repeat held-key page changes and the established two-key loop gesture.

Physical six-row PLAY/CUT layout and feel are **open**. The running user application
was not forcibly restarted or saved; until a full restart it retains its earlier
loaded Lua code. Pattern slots, Grid recording controls, Players 7–16 paging,
automatic connection and sample browser improvements remain future work.
