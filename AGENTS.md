# plugmlr implementation rules

- Product: expandable shared-buffer playback/recording toolkit for plugdata.
  MLR is one application. Keep buffer, musical-head and instrument-track IDs
  separate; internal fade readers are not musical heads.
- Existing code has no authority by default. Follow the user contract. If a
  term or boundary is unclear, ask; classify conflicting code rather than
  converting it into architecture. Do not use fusion for reviews.
- Preserve user work and historical patches, including `mlr.pd`. Inspect Git
  state and remote authority before editing. Work on a dedicated branch.
  Adjacent repositories and installed services are read-only for R1.
- Keep GUI/mapping outside DSP; keep sample processing in the signal path.
  No new compiled external, recording, clock, recall, Grid/Arc or SerialOSC
  work in R1. No broad dependency or formatting pass.
- Validate actual Mac plugdata audio at 44.1/48 kHz including file-rate mismatch,
  stereo, independent heads and two instances. Record runtime build and retain
  evidence. Separate numerical checks, listening and DAW acceptance.
- Keep README and docs/STATUS.md accurate about contracts and open gates.
  Commit and push completed work; open a focused PR and leave it unmerged.
