# Working on plugmlr

- Follow the user's current scope. The present task is to understand the original
  `mlr.pd` application and identify small repairs. Additional heads and the rejected
  R1 rewrite are not current implementation goals.
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
  fresh stereo recording is now authorized; growth/trim, pause/resume recording
  and recording quantization remain deferred. The user chose a local Pd stereo bus between standalone patches for this slice;
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
