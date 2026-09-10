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
- Keep changes small and within the authorized scope. Do not replace the entry
  point, bulk-format patches, or import an alternative player wholesale. Read
  alternatives where they contain useful behavior; names are not authority.
- Preserve user work, the failed-experiment stash, and historical patches. The
  installed `mlr-lite` copy and adjacent repositories are read-only references.
  Do not launch additional audio-producing test patches into the user's session
  as an incidental diagnostic.
- Use a dedicated `codex/` branch. Verify the final changed paths, commit and
  push completed work, and leave any PR unmerged unless the user asks to merge.
  The current candidate repairs speed-control ordering. Direction slew and
  the two-reader crossover have identified gaps recorded in STATUS; they are
  not accepted repairs. Preserve the original playback path and validate actual
  native output before claiming an audio fix.
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
