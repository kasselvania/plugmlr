# Working on plugmlr

- Follow the user's current scope. The present task is to understand the original
  `mlr.pd` application and identify small repairs. Additional heads and the rejected
  R1 rewrite are not current implementation goals.
- Start with the actual plugdata UI and console. Trace the corresponding `.pd`
  objects, connections, trigger order, and send/receive symbols. Existing code
  establishes what is wired, not that it is correct.
- Work through one part of the musical path at a time: loader, buffer metadata
  and selection, transport/looping, then the two internal readers and their fades.
  Preserve and understand connected musical controls while doing so.
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
  push completed work, and leave any PR unmerged. For this observation update,
  only documentation changes are authorized; Pd/Lua/audio files stay unchanged.
