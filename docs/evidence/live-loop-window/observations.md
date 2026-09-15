# Live loop window: source, native evidence and limits

Base `9aa7b74ab9b43b1c07d34903c05651e28b826590`, PR #41.
The user chose: live Start/End; Move preserves length; edited edges stop at
one another; an ordinary slice returns to the existing 16-way policy.

## Source path

`slice-panel.pd` sends `start`, `end`, or `move` plus seconds to the private
`<player-id>-loop-window` bus. `loop-window-control.pd`, instantiated by
`loop-region-control.pd`, also receives public `<track>-loop-window` messages.
Both paths use the same calculation. No GUI timer, Lua or new DSP is introduced.

The helper snapshots request seconds / operation (0 start, 1 end, 2 move) /
active first / active exclusive end / usable first / usable exclusive end /
file Hz / minimum frames / ready-and-not-switching. The multi-output expr emits
validity, end, then start, so the pair is formed atomically. Frames are rounded
at the input. Minimum = max(1, ceil(abs(current rate) * file Hz / host Hz)); the
existing rate_multiplier feed updates even while stopped. If a later speed
change makes a window too short, Start/End can still widen it. Move does not
silently change its length. Unsupported full sub-host-sample cycles retain the
original player's refusal behavior; this helper does not alter rate-change DSP.

An accepted request cancels the old pending slice, stores its endpoints, then
sends `keep <start_seconds> <end_seconds>` to the existing region validator.
The existing logical-ramp query retains in-range motion. An outside position
uses the existing direction-dependent region cut and handoff. Consecutive
outside-window requests coalesce through that handoff; they are not promised
sample-accurate at every GUI event. Ordinary slice commits refresh full bounds.
Malformed/non-finite requests and empty/switching states do nothing. No buffer
arrays, trim metadata, sample-editor selection or other player's loop is edited.

## Reproduce

1. Run `python3 tests/build_live_loop_check.py` from the repository. It reuses
   `build_sample_editor_check.py` for isolated original players/mixers and the
   stereo test source. It writes `/tmp/plugmlr-live-loop-check/check.pd`.
2. Open that file in standalone plugdata. It uses slots/tracks 900–902, has no
   DAC, and does not replace slots 1–16 or the user's running MLR patch. Only
   fixture selection admits those test slots. Its copied player's ppq receiver
   is renamed to a test bus so scripted ticks cannot affect the user session.
3. Enter `editor-check-run bang` in the native console. The score stops capture
   and playback at 12 seconds; a separate 14-second watchdog also stops both.
   Confirm `editor-check-stopped: bang` in the actual console.
4. Run `python3 tests/analyze_live_loop.py /tmp/plugmlr-live-loop-check` with
   numpy available. Also run `python3 tests/check_ui_overview.py` and the patch
   connection checker on the new helper, region control and slice panel.
5. Close the diagnostic player tab and check.pd. Reopen the ordinary mlr.pd
   when ready to load the new abstractions; the currently loaded session still
   contains the prior panel. Pd patch saves do not preserve sample audio.

The builder copies production code and records hashes in source.json. Unique
fixture Lua class names isolate the unchanged sample-view classes from an open
user session. Test-only probes read existing control buses; audio comes from
actual original players AND original mixers. No mathematical playback model is
substituted. The preserved .pd connections do not establish runtime acceptance
on their own.

## Native observations and numerical results

Runtime: plugdata 0.9.4 nightly **98ae0f78b**, based on **Pd 0.56.3**. The visible
startup console also identified ELSE 1.0-rc14, Cyclone 0.9-4 and pdlua 0.12.23.
The final WAV is 48 kHz; the input stereo file is 44.1 kHz. No device or service
settings were changed. The user's original Player 1 remained paused with its
End Credits sample and was restored to view after closing the test.

`final/capture.wav` is 12 seconds, eight channels: mixer A L/R, mixer B L/R,
pre-mixer A L/R, pre-mixer B L/R. `final/listening.wav` contains only A's stereo
mixer output, with its original level. `final/analysis.json` and `events.txt`
retain the results and actual position/bounds/rate/transport messages.

- 28 bounds checks: live start/end, length-preserving movement, same-timestamp
  composition, crossing both ways, edge clamps, sub-slice loops, and nonzero
  content origin. One-frame clamps and the four-frame minimum at 4x are explicit.
- Quantized cut remains pending before the test tick and restores full content
  after it. The test uses the documented 0=quantized / 1=immediate public modes.
- Forward/reverse position slopes and the expected stereo pitches pass, including
  0.5x and 2x playback. The left/right source tones differ deliberately.
- Pause/Stop/empty silence holds at both player and mixer. No 50 ms silent hole
  in the specified active intervals. This is not a claim to detect every dropout.
- B shares the same buffer; its bounds/transport/speed remain unchanged. Its
  level stays within the expected range while A is manipulated at up to 200
  requests/second. Same-valued metadata refreshes on reselection are allowed.
- Mixer gains are preserved. The known additional startup envelope is accounted
  for only in the exact gain-ratio test; no samples are excluded from global
  peak or adjacent-step measurements. Max A mixer peak: 0.0732414. No non-finite
  output or gain amplification beyond the configured gain.
- Native End field entry changed the loop without Apply. Direct Move dragging
  shifted 2.5–3.0 s to 1.1–1.6 s; the shaded region and both fields followed.
  Earlier automated focus attempts typed into End instead; a fresh focus and
  native drag established the Move result. User usability acceptance is separate.

## Known failures and limits

The first fixture requested absent sample slot 900 as its empty test. The actual
console correctly reported missing arrays/view receivers. This was a fixture
error; adding an empty sample-data 900 fixed the final run. Its raw audio is
retained compressed in `first-pass/capture.wav.gz`, with console and source
manifest. No new errors appeared in the final run or closure.

The analyzer initially mistook same-valued shared metadata notifications for
state changes and omitted the original mixer's startup envelope. These assertions
were corrected to compare actual state values and account for the explicit
startup fade. A too-narrow position window held only one 20 ms report; the check
now spans four reports without a wrap. Audio claims remain tied to final source.

**Extreme crossover gate remains OPEN.** At one-source-frame loop clamps around
3.0023 s and 3.2034 s, the complete recording contains sharp steps; largest A
post-mixer step is **0.0614402**. These are retained in the analysis, not excluded
as harmless transitions. A one-frame repeating waveform may approach DC; short
crossovers can also change RMS/timbre through interference. No universal
click-free or constant-loudness claim is made. The original dual-reader engine
is unchanged and this limit has not been repaired in this control/UI slice.

**Listening:** no new user listening report. The diagnostic tones make the
transition locations reproducible, but are not a substitute for musical audition.
No new 44.1 kHz host, Bitwig, controller hardware, Grid/Arc mapping, session recall,
or full application isolation acceptance. The public control interface is ready
for future adapters; none are added here.
