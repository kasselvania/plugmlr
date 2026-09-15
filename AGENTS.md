# Working on plugmlr

- Follow the user's current scope. The present task is to understand the original
  `mlr.pd` application and identify small repairs. Additional heads and the rejected
  R1 rewrite are not current implementation goals.
- Reusable transport, buffers, recording, playback and manipulation utilities are
  the community-facing destination. Extract traced and validated behavior with
  explicit ownership, identities and units; do not begin another engine rewrite.
- Start with the actual plugdata UI and console. Trace the corresponding `.pd`
  objects, connections, trigger order, and send/receive symbols. Existing code
  establishes what is wired, not that it is correct.
- Catalogue the whole musical path before choosing the next repair: loading,
  buffer selection, slicing, quantization, transport, loops, speed/direction and
  their slew, readers/fades, recording, mixer, and visual/controller feedback.
  Trace each part's state and timing dependencies; do not stop at the first bug.
- Separate direct UI/console observations, user listening reports, source
  findings, and untested hypotheses in `docs/STATUS.md`. An empty error view is
  not proof of correct playback. A model or log is not an audio test.
  For output-loss or cross-track claims, capture the actual mixer as well as
  the player; a pre-mixer tap cannot detect a wrongly closed mixer envelope.
- Keep changes small and within the authorized scope. Do not replace the entry
  point, bulk-format patches, or import an alternative player wholesale. Read
  alternatives where they contain useful behavior; names are not authority.
- Preserve user work, the failed-experiment stash, and historical patches. The
  installed `mlr-lite` copy and adjacent repositories are read-only references.
  Do not launch additional audio-producing test patches into the user's session
  as an incidental diagnostic.
- Use a dedicated `codex/` branch. Verify the final changed paths, commit and
  push completed work, and leave any PR unmerged unless the user asks to merge.
  The accepted checkpoint includes the original playback, crossover, buffer
  selection and mixer-isolation repairs (PRs #6–#10).
  Keep recording-length settings separate from content bounds and capacity:
  tempo changes affect the next recording, never existing audio. Test early Stop
  with retained capacity: reader lookups must not enter the unwritten tail. Fixed-length
  fresh stereo recording is authorized. Free recording now recovers the original
  90%-capacity/doubling policy through record-storage and the existing stereo writer,
  with a provisional 60-second ceiling. Keep written bounds separate from capacity;
  validate resize continuity in actual audio and other playing lanes separately.
  Physical shrink, recording pause/resume, overdub and record quantization remain open.
  Finish the recording source recovery and native UI before Grid recording design.
  Recording progress is display-only and instrument-scoped. Finish addresses the
  live buffer, not current player selection. DSP Off finishes written content;
  DSP On never resumes a take. Input capture currently stays forward at 1x.
  Recording direction/speed/slew are authorized artistic follow-up, not implemented
  by the playback controls. Retain the recording-continuity exact-boundary Reverse
  failure until its player handoff is repaired and checked in actual audio.
  Natural wraps now schedule from the original frame-ramp duration, replacing
  audio-block edge detection. New trajectories replace the deadline; transport
  and pending cuts cancel it. Keep the original handoff order and 0=forward /
  1=reverse convention. Preserve the recorded-boundary and stale-edge controls.
  The user chose a local Pd stereo bus between standalone patches for this slice;
  cross-instance pdlink transport fails stereo timing and remains separate.
  Validate type AND number selection, reselection, empty buffers, interrupted
  switches, stereo ordering and safe load/clear in the native original player.
  Keep the 6/9 ms fade defaults and shutdown cancellation. reader-fade-limit may
  shorten an envelope before reuse, never extend it. A turn back to the preceding
  natural loop's outgoing endpoint preserves that fade until handoff; cuts and
  changed endpoints do not get this exception. Refuse full sub-sample cycles.
  Retain the failed fade candidates and test all transition audio/reader gains.
  Playback Stop must finish its fade/cleanup before a queued Play rechecks buffer
  readiness. Another Stop cancels that Play. Keep recording Stop's direct timing
  separate from playback shutdown, and check empty-buffer playbar output is finite.
  At a speed-boundary collision, the loop handler owns the jump; query the current
  ramp position after the boundary retry. Keep failing recordings bound to their source.
  First-pass crossover evidence does not accept later untested edits. Direction
  slew remains out of scope. Preserve the original playback path.
  Instant Reverse and speed updates query the existing ramp's logical-time position; do not
  replace it with a stale block snapshot. Check actual reader continuity and
  signed speed during rapid turns and loop/slice fades, separately from tape slew.
  Pause saves the logical position before its 6 ms reader fade and 9 ms cleanup.
  Resume restores reader gates/gain before motion; Stop, buffer switching and
  leaving paused state cancel pending cleanup. Test slices during and after Pause,
  exact loop-end pauses, rapid toggle parity and pre-mixer silence.
- Slice mapping is an explicit musical choice: fixed 16-way whole-content cuts,
  and any committed cut restores full-content bounds. Keep this choice visible in
  `pd slice_policy` and the linked slice-position calculation; future modes must
  change both deliberately. A pending slice owns the next jump until commit or
  Stop cancellation. Test boundary/cut collisions without excluding those windows.
- The visible loop panel edits Start/End live; Move preserves window length.
  loop-window-control clamps crossing edges at the current one-host-sample limit,
  keeps seconds/file frames explicit, and routes through the existing keep path.
  Same-timestamp edits must compose before a deferred handoff. A new committed
  slice refreshes the window and restores the whole-content policy.
  Sample-editor selection remains staged; it is separate from live loop controls.
  Validation belongs in
  `loop-region-control`; region and slice requests share `pd slice_policy` and
  its pending jump. Preserve paused/stopped silence and whole-content feedback.
  The original visible-loop capture exposed nonzero-gain reader reuse and
  premature mixer closure on paused Apply. Preserve the pending-cut handoff wait
  and separate pause reposition from cleanup; retain whole-transition checks in
  `analyze_cut_handoff.py` rather than excluding these failure windows.
- Quantized slice input writes the stored index without output; only matching
  ppq ticks dispatch it. Stop/Pause, selection and mode/grid messages clear pending.
  Public mode remains 1=immediate. slice-mode-control inverts the visible
  Quantize checkbox and mirrors public messages with set (no feedback command).
  Default mode is immediate; the visible grid and scheduler both initialize to 1/16.
  Controlled tick tests are not autonomous-clock or DAW-sync acceptance.
- Internal clock Run controls ticks independently of playback. Keep its tempo
  separate from host tempo and retain the tick count on Stop. BPM must store into
  calc_duration without retriggering a stale start position. Validate autonomous
  ticks through the actual player/mixer, not only an isolated clock.
- Beat Reset uses quarter-note intervals on shared ppq, with 4/4 bar labels.
  Preserve full-content start-forward/end-reverse entry through loop-region-control.
  Never wake paused/stopped tracks; read existing transport flags rather than
  maintaining a second playing latch. Same-tick reset supersedes quantized slice
  through the shared pending-cut path; test all transition samples.
- Establish an automatic capture stop before starting any diagnostic recording.
  Do not leave recording dependent on another agent turn, context compression,
  UI automation, or the user noticing it. Keep capture setup separate from DSP
  changes and never treat an abandoned capture as acceptance evidence.
- The agreed tape direction is free-form: instant reverse at the current position
  or tape slew with permitted drift. Automatic catch-up and clock locking are
  deferred. Keep the reference effect catalogue separate from implementation.
- The community device layer is `kasselvania/PlugData-Monome-Devices`, using the
  lease-aware `kasselvania/serialosc` fork. Follow the pinned suite map in STATUS;
  their default branches do not identify the lease candidates. Musical mapping
  belongs here; session ownership, renewal, release and platform installation
  stay with those projects. Do not claim integration from a documentation link.

- The main UI is a 16-track overview, with focused player, imported-bank and
  live-take views. Keep buffer slots distinct from tracks and status receive-only.
  ui-open-view changes canvas visibility only; it must not stop audio or finish a
  take. Preserve the original nested clock/Grid/array wiring when editing the
  root layout. Run tests/check_ui_overview.py and inspect native rendering; Pd
  index validation alone misses valid-but-wrong wires and overlapping widgets.
  Any change to relocated gain controls needs an actual post-master check.

- Player-panel is a view onto the original player, not another engine. Keep status
  receive-only, preserve public control symbols, and show selected speed separately
  from any claim about instantaneous slew. Clock activity and reset request feedback
  must not imply tempo fitting or sample-exact synchronization. Validate the actual
  panel with the user; structural/message checks alone do not accept usability.

- Tempo fit derives the effective target before the original speed glide. Full
  content frames and file sample rate define its duration; loop bounds and storage
  capacity do not. Keep preset multiplier, fitted target and current slew distinct.
  Do not reconnect the obsolete calc_duration tempo branch. Mode/tempo/beat edits
  must preserve current position and stopped/paused silence. Test the actual reader
  signals and post-master output, including file/host rate mismatch and cut collisions.
  Bound sampled glide reports to the last applied rate/new-target interval;
  preserve fitted rates outside the five free presets. The playback-slew-review
  evidence retains the original natural-loop timing and reader-reuse failures;
  natural-loop-timing contains their repair and final native regression suite.
  Neither checkpoint is full playback acceptance or direction-slew acceptance.

- Host validation must name host and file rates separately. Passive message-to-signal
  rate reporting and reader taps can span two 64-frame blocks at command boundaries;
  retain all transition samples and the rejected narrower-analysis evidence.
  Qualify test component paths relative to this checkout; installed abstractions may
  shadow unqualified names. Two original player components sharing a buffer are not
  two isolated full applications. Bitwig's visible editor currently cannot be read
  by the UI tool; do not turn that access gap into an audio failure or acceptance claim.

- Grid migration uses the pinned dependencies/monome submodule. Keep leases,
  discovery and LED cache in that package; mlr-grid-compat only translates the
  original message boundary. Do not bypass session ownership with raw OSC.
  Preserve original row mapping; a connector test does not accept playback LEDs
  or audible Grid slicing. Run tests/check_grid_adapter.py and the Lua boundary
  checks, then inspect actual native session and physical input/output separately.

- Playback Grid feedback is receive-only: export existing player state, render
  whole-content columns on the two existing display rows, and gate output on
  attachment. Keep tests/check_grid_feedback.py as the current source boundary;
  check_grid_adapter.py retains the earlier connector-only checkpoint comparison.
  Scheduled row commands and numerical audio checks do not prove physical key
  gestures or physical moving LEDs.

- For new Grid gestures, consult the pinned mlre manual/source map in STATUS.
  Distinguish upstream behavior, current plugmlr behavior and proposed changes.
  Preserve stereo and the original player; do not equate tape splices with buffer
  slots or mlre Stop/Start names with our hard Stop. Define gesture/release
  semantics before editing, and keep unsupported page controls inactive.

- CUT ALT routing sits before the old press filter. Release and duplicate-down
  handling belong there; never emit a slice alongside an ALT transport command.
  Disconnect clears held input state. Keep transport immediate and slice timing
  in the existing player. Run check_grid_alt.py for the exact input-only boundary.

- Two-key CUT loops include both cells and commit once on first release after
  at least 160 ms continuous overlap. Every fresh ordinary key-down still sends
  its slice through the existing quantizer, including overlapping keys. Keep
  LOOP_HOLD_MS in grid-cut-keys as the single feel setting. Per-row clocks only
  arm gestures; release owns commit. Short releases, cancellation, modifiers,
  third keys and detach unset the clocks. Preserve immediate MOD single-cell loops.
  The user accepted the immediate-cut interaction at 40 ms and requested 160 ms;
  do not claim physical acceptance of a changed threshold from timed tests alone.
  Run build_grid_hold_check.py / check_grid_hold.py in native plugdata; old
  checkpoint gesture fixtures predate the new overlapping-key slice behavior.
  Keep gesture state in grid-cut-keys and seconds conversion in grid-loop-region;
  original loop-region-control owns validation and transitions. Loop commit must
  cancel the queued quantized slice as well as the pending trajectory. Stop,
  Pause, buffer changes, ALT and detach cancel unfinished gestures. Validate
  master silence separately from the known stopped-slice pre-mixer activity.
  check_grid_loop.py guards the exact helper and cancellation-wire boundary.

- Grid loop release is a boundary edit, not Apply's entry retrigger. For running
  playback inside the new range, query the existing logical ramp and recalculate
  from that position without a slice; outside, wrap immediately. Keep plain/full
  Apply unchanged. Test long holds in both directions and inspect actual position
  AND audio across release; an emitted loop message alone misses this regression.

- Grid loop feedback is receive-only. Dim level 4 means committed smaller loop;
  bright 12 means current running column. Pause/Stop retain the dim range;
  full content has no background. Ready/switching and attachment gate display.
  Never render held gestures as committed bounds. Keep package LED ownership,
  and use check_grid_loop_feedback.py to preserve exact player/gesture sources.

- MOD is top-row column 14, committing one cell on fresh key-down through the
  existing loop path. Releases never retrigger. ALT wins if both are held; no
  upstream ALT+MOD chop behavior is implied. Modifier presses cancel pending
  two-key gestures, not already committed loops. Keep check_grid_mod.py and the
  native gesture suite as this input-only slice's preservation boundary.

- Waveforms are receive-only views. Keep stereo min/max caches buffer-owned, scan
  written content in bounded chunks, and drive cursor paint from the existing
  playbar feed. Never scan arrays in paint or use a GUI timer to advance audio.
  Save WAV uses soundfiler synchronously after rechecking all instrument players,
  recorders and storage activity. Preserve written bounds and recorded rate; do
  not claim background I/O or switch playback to disk. Routine Debug gates must
  leave actionable errors visible. Repeat tests/build_waveform_check.py in the
  native runtime and analyze the actual mixer/export before audio claims.

- Clear protection belongs to the live buffer, before the existing fade/resize.
  Unsaved Clear arms a five-second request; only separate Discard confirms.
  Content/save/storage changes, selection and view navigation cancel it. Never
  describe this as a close/quit guard or patch-based audio persistence.
- Validate first Play from a fresh native launch before any Stop or slice.
  slice_policy must initialize no-pending-slice state explicitly. A nonzero
  capture can be a held endpoint/DC: check advancing audio and expected pitch,
  not only silence/RMS, and retain failures with their exact source manifests.

- Clear/Discard must stay blocked throughout buffer selection, until its new live
  target is installed. Drop transient requests; never replay them against another slot.
  Pd connections must follow both object declarations; inspect native console too.

- Sample trim is buffer-owned, non-destructive first/exclusive-end metadata over
  retained stereo arrays. Stop shared readers before committing; new loads cancel
  pending trim. Reselection keeps trim and Restore returns original bounds.
  Keep source-file seconds explicit and add first_index to whole-content slices.
  Editor gestures stage selection; original loop/transport paths own audition.
  Zoom uses cancellable buffer-owned peak jobs, never audio work inside paint.
  Test nonzero starts, both directions, shared readers, reload races and native
  UI separately. Isolate native test Lua class names from already loaded user code.
