# Playback and slew: source review and bounded rate repair

2026-09-11. Base: `b85982ab8845ac54e9380b6212314e6f573d3d75`, the unmerged
PR #34 head. Branch: `codex/playback-slew-review`. Remote main was independently
verified as `29ab51e653eded9db9c5aa09850ec4a1352d97e9` before editing.

## What the existing code does

These are the current sources, not the historical functionality table's earlier
revision. All twelve nested player canvases remain byte-identical in this repair.

| Responsibility | Current source and ordering | Disposition |
| --- | --- | --- |
| Requested speed | Player preset index 0..4 selects .25/.5/1/2/4; `tempo-fit.pd` derives the effective target from full-content frames, file Hz, BPM and beats. | Retain as musical policy, separate from motion. Arbitrary free speed is not a current public control. |
| Glide | Root `pack f f f` → `curve~ 1` → 5 ms `cyclone/snapshot~` → `change` → rate publication → position query. Zero ms and completion publish the exact target directly. New targets stop the prior reporter/curve first. | Retain. Add only the report bound described below. Duration/curve edits affect the next target. |
| Time and position | `pd current_position` evaluates the existing start/end/duration tuple at logical elapsed time. `pd calc_duration` uses absolute frame distance divided by rate magnitude × file frames/ms. | Retain one calculation; future extraction should expose explicit units and ownership. Motion during glide is a sequence of audio-rate ramps, not continuous integration of the curve. |
| Transport | Root dispatch, `pd stop_transition` and `pd pause_transition` own flags, saved position, reader envelopes and cleanup. Rate reports can advance while stopped/paused but cannot request motion then. | Retain these state owners. Do not add a competing transport latch for an adapter. |
| Instant Reverse | Toggle original 0/1 direction, update direction-dependent endpoints, query the logical ramp and continue from that position. | Current musical path. Reverse does not negate a GUI rate number or invert the audio waveform. |
| Direction slew | The old second curve/delay section has no hot path into its command pack. Its enabled branch ends without output. Its rate publications would compete with the active glide. | Inactive historical sketch, not a feature to expose. A near-zero divisor guard in `calc_duration` does not define stopped-tape behavior. |
| Slice and loop edits | `pd slice_policy`, `loop-region-control` and `pending-cut-delay` share the pending destination; cuts wait out the prior handoff. Whole-content slicing is the existing explicit policy. | Retain the common owner. The short-loop score includes edits during a glide. |
| Natural wrap | `pd loop_logic` observes signal endpoints with separate directional edges, checks the current logical ramp, then calls the original reader handoff. | Exact-boundary reversal/stale-edge repairs remain. Block-delivered notification still makes nonaligned loops late. |
| Internal readers | `pd tabread_processing` contains two stereo `tabread4~` readers, separate `vline~` ramps and gain envelopes. Loop fades are 6 ms; slice fades are 9 ms; reader shutdown is delayed/cancelled over 12 ms. | Preserve the useful dual-reader design. A return sooner than the fade completion can reuse an audible reader. These are two transition readers inside one musical player. |
| Feedback | The playbar/Grid state follows the logical trajectory; player-panel status reads existing state. | It is not a measurement of both audible reader positions during a crossover. Frontend cleanup should keep requested/actual rate and transport state distinct. |

`sampler_playback_third.pd` retains an earlier curve/snapshot/engage layout;
`sample_playback_new.pd` has older snapshot-based motion. Neither supplies a
validated replacement for these paths. `rate-change.pd` has no outlet and is a
sketch, not a reusable rate utility. No alternative was imported. No recording,
buffer ownership, Grid, mixer, application entry point or installed dependency
was changed. Recording direction/speed remains its separate artistic follow-up.
The root's separate `$0-slew_engaged` send has no receiver; current speed glide
is controlled by its duration, not that leftover engage toggle.

## Small repair

At 44.1 kHz, a 2000 ms glide ending at 4x and immediately replaced at 6.6 seconds
publishes `4.000227451` for 192 captured frames. The baseline report deliberately
fails its rate-range check. This is a small numerical overshoot, not evidence
that the user heard a click.

Three Pd objects fix that publication boundary: `t f f` stores the new interval
before starting the existing curve; a two-output `expr` computes min/max of the
last applied rate and new target; `clip` bounds sampled reports before the
existing ordered rate/position publication. It does not reset or replace the
curve. Final and zero-duration target publication remain unchanged. Fitted rates
are bounded to their actual target interval, not hard-clamped to the free presets.

[source-boundary.json](source-boundary.json) verifies everything outside those
three objects, one comment, two rerouted wires and six added wires is byte-identical
to the base. The final structure check finds 13 canvases, 1061 objects and 1023
connections with no index errors. Native load and audio checks follow separately.

## Native observations and numerical results

Runtime: `/Applications/plugdata.app/Contents/MacOS/plugdata`, **0.9.4 nightly
98ae0f78b / Pd 0.56.3**. Bundle version and binary build/Pd strings were read;
the executable SHA-256 is retained in `source-boundary.json`. Native settings
show CoreAudio **8A**, **512 device frames**, **1×**. Eleven 14-second captures
were run, with an independently armed 16-second watchdog. The patch contains
actual production players/buffers/mixers, no DAC, Grid or hardware input.
The player copy appends only test controls and passive taps.

The native patch title, load messages and console completion were inspected.
The console remains noisy with historical routine DSP prints; seeing no error
in those inspected messages is not proof of correct playback. Samples in the
captures provide the separate audio evidence. All diagnostics were closed and
**48 kHz restored** at the end; plugdata is at Home, DSP On, recording stopped.

| Capture family | What the actual audio establishes |
| --- | --- |
| Repaired standard glides, 48 and 44.1 kHz hosts, 48 kHz files | .1/1/5/400/2000 ms durations, curves 0/-.5/-1, interrupted targets, Pause/Resume, Stop/restart, Reverse and 100 ms loop regions. Rates stay within .25..4; no audible-gain reader resets, non-finite output or exact-zero running dropouts. Running reader gains sum to 1. Loop-period accuracy still fails. |
| Repaired constant stereo, 48 kHz | Stereo amplitude error at most `7.45e-9`, no running dips/boosts. All transition samples are retained; paused/stopped output is zero. |
| Repaired Fit, 44.1 kHz host / 48 kHz file | All 15 checks pass: 1/64x and 16/3x targets, signed motion, interrupted glides, paused changes and restart. This score does not assert exact natural-loop periods. |
| Independent second lane | Paired before/after stereo error is 0 at 48 kHz and at most `3.73e-8` at 44.1 kHz. Actual mixer gain is unchanged outside its known 5 ms opening envelope; opening samples remain in other transition checks. |
| Short loops, before and after | Reader reuse remains a failure: 473 detected resets at 48 kHz and 480 at 44.1 kHz, while the reader still has nonzero gain. The repaired 44.1 kHz waveform exceeds the fixture's derived adjacent-step bound; constant stereo can remain exact despite these position faults. |

The standard repaired waveform's maximum adjacent L/R steps are
`.012604/.011108` at 48 kHz and `.013700/.012084` at 44.1 kHz, below the
fixture-derived slope/envelope limits. The short-loop repaired waveform reaches
`.020650` on L, above its corresponding limit. These are numerical checks,
not universal audibility thresholds. [results.json](results.json) explicitly
reports **rate_repair_passed=true**, **full_playback_acceptance=false**.

Two failures remain. A 100 ms region at 4x nominally repeats every 25 ms, but
measured periods are **25.333 ms at 48 kHz** and **26.122 ms at 44.1 kHz**.
The master ramp reaches its endpoint and waits for the block-delivered wrap.
This affects ordinary non-block-aligned loops too; it is not just a tiny-loop
issue. For 20/12/8 ms regions at 4x, nominal periods 5/3/2 ms become
5.333/4/2.667 ms at 48 kHz and 5.805/4.354/2.902 ms at 44.1 kHz. The same
short returns can overtake the 6 ms fade and reset the outgoing reader while
its gain is still nonzero.
A shorter fade alone would not repair period accuracy.

One analysis correction is retained in [hold-analysis-correction.json](hold-analysis-correction.json).
The first two-block-only position-hold limit incorrectly marked the existing
pending-cut wait as stuck playback. At 10.6 seconds, Apply waits for the prior
handoff; the largest observed hold is about 5.2 ms. The corrected bound includes
the existing 12 ms cut wait plus two audio blocks, with every sample retained.
Reader-reset and exact-period failures remain failures.

## Listening, repeat procedure and next repair

**No new listening report has been collected.** `glide-player.wav` and
`short-loop-player.wav` are stereo 24-bit derivatives of the actual player taps,
without normalization. They are synthetic stress signals, not a musical demo.
The previous [musical handoff capture](../loop-boundary-handoff/listening.wav)
remains available; its pending listening gate is not satisfied by these results.
No Bitwig, acoustic/device-output or full-application acceptance is claimed.

1. With other MLR/test patches closed, run `python3 tests/build_record_session_check.py`
   from the repository and open `/tmp/plugmlr-record-session/check.pd` in native plugdata.
   To reproduce the old player, save `git show b85982a:sample_player_rebuild.pd`
   to a temporary `.pd` file and pass that path with `--player-source`.
2. Read native settings and console. In the console command field enter
   `record-session-check slew`, `slew-constant`, `short`, `short-constant` or
   `fit`. Send one at a time; wait for `capture-stopped` and
   `record-session-finished`. Manual fallback is `record-session-check stop`.
3. Before another run, retain `capture.wav`, `readers1.wav`, `readers2.wav`,
   `events.txt` and `manifest.json` from `/tmp/plugmlr-record-session` under a
   common evidence prefix. Every case's manifest stores the exact score and
   production-player hash. The three float WAVs contain actual input/player/mixer
   signals and both reader positions, gains and DSP flags; see the builder/tap
   channel comments. Native ten-channel WAV headers under-report a few final
   frames; analysis reads declared audio and reports trailing bytes.
4. Run `python3 tests/analyze_playback_slew.py PREFIX` (with NumPy), adding
   `--constant`, `--short` or `--fit` for that score. Ordinary loop-period and
   short-loop failures intentionally return nonzero. The retained cases can be
   rerun with `python3 tests/analyze_playback_slew.py docs/evidence/playback-slew-review --repair-suite`;
   that exit status concerns the small rate repair, not all playback acceptance.
   Each `.wav.xz` restores the exact native WAV bytes; hashes are in
   `audio-archives.json`.

Per-case event logs and manifests are also stored as `.xz` files, with original
hashes in `metadata-archives.json`. This keeps repetitive trace output out of the
code-review diff. Decompress with Python's standard-library `lzma` or `xz -dk`;
the numerical reports and this source map remain directly readable.

The next focused job is **natural-loop scheduling**, preserving current logical
position, direction, cuts and cancellation. Establish exact periods at both host
rates before revising short-loop fades. Then address reader reuse without silently
lengthening a loop or stealing an audible reader. Direction slew through zero
comes after its interruption/zero-speed contract is implemented. The frontend
cleanup should expose these proven parts clearly; reusable abstractions can then
be extracted along the responsibility boundaries above. No new engine, arbitrary
head manager or additional recording mode is justified by this review.
