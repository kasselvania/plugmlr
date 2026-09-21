# Alpha release boundary

## Status

`v0.1.0-alpha.1` is a preparation target, not a published release. This document
is the authority for what that alpha is allowed to claim. Historical notes in
`STATUS.md` remain evidence and design history; they do not expand this boundary.

The alpha is intended for curious early testers who are comfortable with
PlugData, visible console diagnostics, explicit device ownership, incomplete
session persistence, and reporting exact reproduction details. It is not a
general-purpose or production-ready looper.

## Newcomer path

The release-facing route is now:

1. [Installation](INSTALLATION.md) for the exact source and runtime;
2. [First sound](FIRST_SOUND.md) for the smallest sample-playback check;
3. [User guide](USER_GUIDE.md) for the included instrument workflows;
4. [Grid guide](GRID_GUIDE.md) for select, probe, claim, performance, and release;
5. [Troubleshooting](TROUBLESHOOTING.md) for symptom-based recovery and reports.

The root README is the landing page for that route. `STATUS.md` remains the
engineering evidence history in the full repository and is intentionally absent
from the curated user archive. Until a tag exists, Installation truthfully names
the preparation branch and exact-runtime acquisition gap.

## Source authority

- Application-code checkpoint: `4c3caff961680a9207c52022ee2244e4b34bd1c1`.
- Preparation branch: `codex/alpha-boundary-and-licensing`.
- The quarantine commits after `4c3caff` add documentation only; they do not
  change playback, recording, Grid, pattern, buffer, or editor code.
- The later stretch integration merged to remote main at
  `b8cd65d9d882374dfb7230589c539fdf92e21594` is not part of alpha.1.
- The final release tag must point to a reviewed descendant of the application
  checkpoint containing only release documentation, packaging, and validation
  changes. It must not silently acquire later feature commits.
- The packaged companion commit is
  `620b22c641003b3dcbca8ec94858839737a495bb`. It adds an MIT license, notices,
  and documentation only; its runtime source is the tested parent
  `18b489399d01a9178e4667b849ec4368d72533db`.

This split is deliberate. The receiver-lifetime repair closes one identified
synchronous callback defect, but it does not close the broader stretch, teardown,
audio-quality, alternate-host, or dependency-packaging gates. Stretch may return
in a separately identified experimental build after those gates are exercised.

## Supported target

The first alpha supports one deliberately narrow lane:

- Apple-silicon macOS;
- PlugData standalone 0.9.4 nightly `98ae0f78b`;
- Pd 0.56.3 and pdlua 0.12.23 as carried by that tested PlugData runtime;
- one open plugmlr application instance;
- 48 kHz as the primary playback/recording lane;
- the licensed `PlugData-Monome-Devices` package revision
  `620b22c641003b3dcbca8ec94858839737a495bb`, whose runtime source is the tested
  parent `18b489399d01a9178e4667b849ec4368d72533db`;
- the lease-aware `kasselvania/serialosc` candidate at
  `7187832c349202b1a94a9b10080ae57d40069946`; and
- legacy Grid `m1000853` (16-by-8) as the instrument's physically exercised
  controller surface.

There is bounded 44.1 kHz and file/host-rate-mismatch playback evidence, but the
alpha does not promote that to complete 44.1 kHz recording or host acceptance.
The device layer has broader Grid/Arc and SteamOS evidence; that does not make
those devices and platforms supported plugmlr instrument targets.

## Alpha claims

Within the supported target, the alpha may be described as an MLR-style stereo
instrument with:

- imported and live buffer selection;
- forward/reverse playback, five speed presets, speed glide, Pause, and hard Stop;
- sixteen whole-content slices, quantized slice dispatch, and editable loop windows;
- internal clock, Beat Reset, and tempo-fit controls;
- fixed-length and bounded Free stereo recording;
- finished-take WAV export and explicit unsaved-take protection;
- a sixteen-track overview and focused player/sample/live-take views;
- eight free-time performance-pattern slots with manual bank save/load; and
- explicit Grid selection, probe, lease claim, playback control, LED feedback,
  and release.

Each claim is bounded by `FEATURE_STATUS.md` and `KNOWN_ISSUES.md`. “Included”
means the named path has retained source/native evidence appropriate to an alpha;
it is not a universal artifact-free, crash-free, or all-host guarantee.

## Explicit non-claims

Alpha.1 does not claim:

- vanilla Pure Data compatibility;
- Intel macOS, Windows, Linux, or SteamOS support;
- AU, VST3, CLAP, LV2, Bitwig, or any other DAW lifecycle support;
- safe multiple instances in one Pd environment;
- complete project/audio/pattern recall from the Pd patch;
- automatic save, quit veto, or crash recovery;
- DAW or MIDI clock synchronization;
- record pause/resume, overdub, record quantization, or recording speed/direction;
- Arc control, 16-by-16 instrument layout acceptance, or arbitrary Monome devices;
- arbitrary-source click-free behavior at every loop length or transition; or
- Rubber Band rendering, pitch shifting, or time stretching.

## Publication gates

Project-owned plugmlr source is MIT licensed. The maintainer confirmed on
2026-09-21 that the six files in the initial upload are wholly their own work and
may be shared.

The curated package builder now materializes the exact companion revision,
excludes private media and engineering evidence, records source authorities,
generates per-file and whole-archive SHA-256 manifests, enforces a bounded
payload, and is exercised twice by CI to prove deterministic output.

Do not tag or publish alpha.1 until all of the following are true:

1. The removed `DrumLoop.wav` and any derived captures remain excluded from the
   release archive; any replacement demo receives documented redistribution terms.
2. Third-party notices remain complete for the exact distributed payload.
3. The automated release gate passes on the exact commit selected for tagging.
4. The manual clean-install, first-sound with a tester-supplied 16-bit PCM stereo
   WAV, Grid claim/input/LED/release, WAV-save, pattern-save/load, restart, and
   console-inspection checklist in [ALPHA_ACCEPTANCE.md](ALPHA_ACCEPTANCE.md)
   passes on the supported target.

The project license now grants community use, modification, and redistribution
of project-owned plugmlr and companion source. It does not grant rights to
private sample-pack audio, derived captures, runtime prerequisites, or other
third-party material. The remaining gates control what the alpha may claim.
