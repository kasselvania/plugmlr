# Receiver-dispatch defect review — 2026-09-17

The evidence supports closing the specific completion-receiver lifetime defect
on candidate `c56ee2174f17fee6188a68f8af74116465d17bdd`. This is an engineering
conclusion, not a PR merge, production restoration or GitHub issue-closing action.
No linked issue is known. Production remains quarantined at `574d9cd`.

Before `ee1252a`, copy_loaded destructed its own Pd receiver during synchronous
message delivery. The retained native comparison reproduced a bindlist_bang crash
after rendering completed. The candidate instead marks completion and schedules
cleanup/adoption on a Pd clock; duplicate callbacks are guarded. Probe wrappers
preserve these bodies and observe retention at callback return and later release.
The deterministic intervention hook only schedules a later clock. UI excludes it.

Exact final runtime receipts copied here establish:
- Full-MLR UI render/adoption: PASS1/1, PID60324; one Jev action. Runtime owner
  observed Sample16, .750 seconds, 120BPM and no observer/hook console error.
- Lifecycle: PASS5/5, PID37830: normal, duplicate, cancel, manual selection,
  parent destruction after callback and before deferred completion. Suppressed
  adoption is the expected result for the latter cases, not a selected copy.
- Campaign: PASS300/300, PID40444, 464.1seconds; fresh sessions, distinct render
  paths, actual loads, source/fixture hashes, callback order and native readbacks.
- Normal quit accepted and process exits observed. Delayed external checks at
  118.9seconds after final exit found no matching crash reports. Numeric process
  exit status was unavailable; no zero exit code is claimed.

Runtime: plugdata0.9.4 nightly98ae0f78b, Pd0.56.3, macOS ARM64. Source90 to
120BPM, selected1second rendered to36000 stereo PCM16 frames at48kHz, pitch0.
The deterministic Pd driver performed the300 cycles, not300 Jev GUI interactions.
Prior UI success with an unbound test hook warning remains separate historical
 evidence; the final clean rerun replaces it for the clean-console gate.

## Limits and retained evidence

The operator subsequently requested deletion of disposable test audio. The cleanup
manifest preserves paths, sizes and SHA256 hashes for368 removed temporary audio
files, including campaign outputs. Their contents were checked during the native
runs; rechecking those WAVs now requires regeneration. Receipts are historical
results, not a claim that every referenced output still exists. Source and logs
remain. The active UI fixture was excluded from that cleanup.

No broad PR52 acceptance: concurrent audible continuity, clicks/dropouts, musical
stretch quality, other rates/hosts, bank-full, missing completion/timeouts, worker
errors, cancellation during rendering and late worker publication remain separate
gates. Repeated destination16 tests do not prove all slots or every uninstrumented
schedule. No new architecture or implementation is proposed for this narrow fix.

External detailed report: local Jev harness RECEIVER_JOBS.md, with compressed event
logs and fixture/job manifests under validation/receiver-jobs. Earlier before/fixed
comparison is in RUBBER_BAND_REPRO.md and validation/stretch-before-crash.json.
