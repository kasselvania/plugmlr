# Alpha.1 acceptance record

## Decision

**Not accepted for tagging.** The deterministic archive and bounded clean-package
checks pass. Audible output, the physical Grid lifecycle, live recording/WAV
export, and pattern save/load still require direct observation on the supported
target. Do not create `v0.1.0-alpha.1` until every open item below passes on the
exact proposed tag commit.

## Candidate under rehearsal

- plugmlr commit: `d654c326084573e15edb06f57146d1fac9945c46`
- application-code authority:
  `4c3caff961680a9207c52022ee2244e4b34bd1c1`
- companion package commit:
  `620b22c641003b3dcbca8ec94858839737a495bb`
- companion runtime authority:
  `18b489399d01a9178e4667b849ec4368d72533db`
- SerialOSC candidate:
  `7187832c349202b1a94a9b10080ae57d40069946`
- PlugData nightly: `98ae0f78b`
- PlugData executable SHA-256:
  `86179a37e58e7a0f0436fc555f56ce41892e3f32ed19b4a3ba8f1cfe3c17476e`
- host observed 2026-09-21: Apple silicon, macOS 26.4.1 (`25E253`)
- archive SHA-256:
  `46ee2221f1353b222b0ddac0a81c9dd1b9c43a5aaf4dd31c1f9bcea8553469cb`

The archive digest above identifies the pre-record candidate. Any documentation
commit that incorporates this record changes the archive and must receive a new
digest, clean extraction, hosted gate, and final acceptance pass before tagging.

## Passed in a fresh extraction

- The external archive checksum and every entry in `MANIFEST.sha256` verified.
- The extraction contained 156 files and no Git metadata, `DrumLoop.wav`, or
  root engineering-evidence tree.
- Both project licenses and notice files were present.
- Five packaged Lua suites passed 78 checks covering registry, session, lease,
  Grid, and Arc behavior.
- Nine applicable packaged Python suites passed 68 checks covering fake/live
  OSC tooling, patch structure, and the two macOS SerialOSC service paths. The
  development workbench-bundle test is intentionally inapplicable because it
  requires the Git metadata excluded from the user archive.
- The installed PlugData executable matched the pinned SHA-256 and visibly
  reported 0.9.4 nightly `98ae0f78b`, Pd 0.56.3, and pdlua 0.12.23.
- The installed lease candidate verified at the pinned revision as the sole UDP
  12002 owner; stable and Homebrew SerialOSC services were stopped.
- The extracted `mlr.pd` opened. A generated 48 kHz, 16-bit PCM stereo WAV loaded
  into Sample 1 with a four-second duration. Track 1 entered `Playing`, its
  playhead advanced, and Pause plus hard Stop returned it to `Stopped`.
- Fully quitting and relaunching PlugData reopened the extracted patch with the
  expected empty in-memory buffers and no retained sample-path claim. The console
  reported the exact runtime and a no-Grid diagnostic; no object-creation failure
  was visible.

## Finding resolved in documentation

The first generated fixture used 32-bit signed-integer PCM. This exact runtime
refused it as an unsupported sample format. A 16-bit PCM stereo WAV loaded
successfully, so the release-facing first-sound lane now names that encoding
instead of promising arbitrary stereo WAV support.

## Open manual gates

- [ ] A person confirms the test WAV is audible in stereo through the intended
  output at a safe level; visible transport/playhead movement is not enough.
- [ ] Bitwig and other Monome clients are safely closed before the standalone
  Grid test.
- [ ] Physical Grid `m1000853` is connected and the non-mutating probe reports
  the exact device free at port 0.
- [ ] plugmlr explicitly selects, probes, claims, and reads back `connected` for
  that Grid.
- [ ] A harmless physical press produces matching input and LED feedback.
- [ ] PLAY/CUT slicing and the accepted two-key loop gesture are exercised on
  the physical surface.
- [ ] Explicit release darkens the Grid and direct readback returns it to free
  port 0.
- [ ] A real 48 kHz stereo input moves both meters, records a bounded take, and
  saves a stopped 32-bit-float stereo WAV that is independently inspected.
- [ ] A non-empty performance pattern is recorded, its bank is saved, PlugData
  is fully restarted, the bank is reloaded with explicit replace behavior, and
  the pattern plays against a reloaded test sample.
- [ ] The final console is reviewed after the complete run, with no unexplained
  object, Lua, file, audio, or device errors.
- [ ] The candidate record is updated to the final commit/archive digest, the
  archive is rebuilt from a clean tree, and the hosted release gate passes.

At the 2026-09-21 stop point, the installed candidate service passed but its
non-mutating probe returned `NO_DEVICES`; the physical Grid gates were therefore
not attempted. Bitwig was also running and was deliberately left undisturbed.
