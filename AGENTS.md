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
  Loop endpoints now use separate directional edges and validate against the
  existing logical ramp before handing off. The control check reads the original
  0=forward / 1=reverse state, not the signal selector's 1/2 convention. Preserve
  the recorded-boundary and stale-edge failure controls in loop-boundary-handoff.
  The user chose a local Pd stereo bus between standalone patches for this slice;
  cross-instance pdlink transport fails stereo timing and remains separate.
  Validate type AND number selection, reselection, empty buffers, interrupted
  switches, stereo ordering and safe load/clear in the native original player.
  Keep the 6/9 ms fades and shutdown cancellation; test loops, cuts and interrupted transport in the actual player.
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
- The visible loop panel stages seconds until Apply. Validation belongs in
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

- Two-key CUT loops include both cells and commit once on first release. Keep
  gesture state in grid-cut-keys and seconds conversion in grid-loop-region;
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
