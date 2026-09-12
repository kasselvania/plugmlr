# Natural-loop deadlines and safe reader reuse

## Scope and source boundary

This continues PR #35 (`b7e64009cf2cf53740bea851ff7da4f6a81169c9`), on
`codex/natural-loop-timing`. Remote main was verified as
`29ab51e653eded9db9c5aa09850ec4a1352d97e9` before editing. The initial worktree
was clean. PRs #34 and #35 remain separate, draft and unmerged.

Two related repairs are needed. The previous signal-edge detector reports an
endpoint only at an audio-block boundary, making a nominal 25 ms loop last
25.333 ms at 48 kHz and 26.122 ms at 44.1 kHz. Removing that delay exposes the
second fault more clearly: cycles shorter than the ordinary fade revisit an
audible reader. Gain can sum to one while a reader jumps incorrectly.

Only `pd loop_logic` and one envelope insertion in each existing voice change.
`source-boundary.json` verifies all remaining player text against the base,
including connection order. The entry point, stereo table readers, crossover
owner, gain `vline~` objects, 12 ms shutdown/cancellation, speed glide, transport,
buffers, recorder, mixer, panels and Grid logic are retained. There is no new
musical head, engine, external, service, dependency or audio-rate Lua timer.

Final production SHA-256:

- Player: `d2b26301ee2fa5eec86f670267606daffe1ad45a14170a8b71eddf1f1b382e49`
- `reader-fade-limit.pd`: `ab4b0c1adfdf006636820d8f20b772e645c2f387b8a5eace933f437cb574dee3`

## Contract and code trace

The preimplementation contract is in STATUS. Public loop positions remain
seconds, converted by the existing loop controller to file frames, with an
exclusive end. Direction stays 0=forward / 1=reverse. The unchanged trajectory
packet is start frame, end frame, duration in milliseconds. File rate converts
rate multipliers into file frames/ms; the host rate supplies the one-sample
fade margin. Free presets remain .25/.5/1/2/4; Fit keeps its existing validation.
This pass tests 1/64..16/3 with both directions, not every Fit value up to 64.

1. `loop_logic` receives that packet, cancels its previous Pd `delay`, and
   schedules the new duration. Stop/Pause, selection cleanup and pending cuts
   cancel the deadline. On expiry it checks the existing playing, paused,
   pending-cut, bounds and positive-rate values. It sends `loop 1`, changes
   reader ownership, then publishes the original direction-appropriate entry.
   `vline~` still produces the audio-rate motion at that logical timestamp.
2. The same duration supplies a gain deadline, one host sample early. Each
   voice's `reader-fade-limit` sits before the existing gain `vline~`. Its first
   inlet accepts target/duration, or an immediate float. The second accepts
   remaining milliseconds; negative disables the bound. The engine initializes
   it through cancellation. A new envelope is capped to the remaining deadline.
   A closer deadline can shorten the ongoing envelope; a later one cannot
   extend it. Two Pd `timer` objects measure elapsed time. The original audio
   envelope determines the current gain; there is no gain snapshot or surrogate.
3. A fast reverse can return to the still-fading outgoing endpoint. Compressing
   that fade into a fraction of a sample creates a gain step. Preserve it until
   handoff only if the preceding handoff was a natural wrap and its outgoing
   endpoint matches the new entry. A cut or changed endpoint clears that policy.
   Sub-sample remaining fragments also retain the ongoing fade. The next handoff
   restores ordinary deadline limiting.

Malformed/non-finite or negative durations cannot schedule. A zero *remaining*
duration can wrap once into a positive full cycle. A *full cycle* shorter than
one host sample emits `Loop_shorter_than_host_sample` through the existing loop
feedback and follows the existing Stop path. Requested bounds are not silently
lengthened. The comparison includes a 1e-6 relative float tolerance at the exact
sample threshold. This is a refusal guard, not certification of one-sample
performance. Stop/restart and silence retain their existing fade semantics;
zero-rate tape behavior is not added.

The helper is a small candidate for reuse: explicit envelope/deadline messages,
no globals, GUI, arrays or audio objects. Its deadline must be initialized;
negative means unbounded. Musical transport and loop policy remain in the
original player, pending deliberate extraction later.

## Native execution

Runtime: `/Applications/plugdata.app/Contents/MacOS/plugdata`, **0.9.4 nightly
98ae0f78b / Pd 0.56.3**, SHA-256
`86179a37e58e7a0f0436fc555f56ce41892e3f32ed19b4a3ba8f1cfe3c17476e`.
CoreAudio, **8A**, **512 device frames**, **1× oversampling**, **64-frame Pd
blocks**. Host settings were read in the actual UI at **48000 and 44100 Hz**;
all fixture files are **48000 Hz**. The latter is a file/host mismatch.

The native `check.pd` instantiates two original players, actual sample/live
buffers and both actual mixers. The observed player is the production source
verbatim plus appended command receivers/passive taps; the manifest checks that
boundary. Production abstractions resolve to this checkout, not an installed
copy. There is no DAC, Grid, hardware input or second full application in this
fixture. Tests cannot disturb speaker playback by emitting their test tones.

Every run arms independent capture termination before starting. Audio ends at
14 seconds, with a separate 16-second watchdog. Native patch-load/console and
capture-stop states were inspected throughout; corresponding images are retained.
The original reader DSP debug prints are noisy. These observations do not mean
the entire console history is error-free or establish foreground/background,
hardware or plugin lifecycle acceptance.

The three native float WAV streams per case are:

| File | Channels, in order |
| --- | --- |
| `capture` | input L/R, player A L/R, player B L/R, actual mixer sum L/R at common .75 gain, master positions A/B |
| `readers1`, `readers2` | player L/R, master file frame, applied rate magnitude, reader 0 frame/gain, reader 1 frame/gain, reader 0/1 DSP flags |

Track mixer gains are .4 and .3. WAV headers underreport a few trailing frames;
original bytes are retained. Analysis uses the declared data, reports trailing
bytes, and keeps every transition sample. Intentional starts/pauses/stops have
explicit windows; those do not disappear from the step, finite or reader-reset
checks. Numerical evidence includes actual component audio, not just a model.

## Final numerical results

`results.json` is the combined report; all **ten final captures** use the same
frozen production sources. Nine synthetic/control cases plus one musical case
pass. The sine-fixture step bounds are the pre-existing 6 ms analytic limits,
not limits fitted to the repaired recordings.

| Test | 48 kHz host | 44.1 kHz host |
| --- | --- | --- |
| 25 / 5 / 3 / 2 ms natural cycles | within one host sample | within one host sample |
| Sustained 2 ms cycle, 8.8 s / 4400 wraps | exactly 96 frames/period | 88/89 frames; accumulated phase error ≤0.8 sample |
| Reader reposition with both adjacent gains >1e-6 | none | none |
| Short-loop maximum adjacent step, L/R | .0126021 / .0111083 | .0137035 / .0120864 |
| Corresponding original fixture limits, L/R | .0131658 / .0114705 | .0143300 / .0124847 |
| Constant stereo error | ≤7.45e-9 | ≤7.45e-9 |
| Sub-sample cycle refusal | once at 1008 ms, safe Stop | once at 1008 ms, safe Stop |
| Four invalid range messages / subsequent recovery | pass | pass |
| Rapid turns, cuts, overlapping glides, pause/resume, Stop/queued Play | pass | pass |
| Non-finite output, unintended zero dropout or gain change in the synthetic checks | none | none |
| Fit 1/64x and 16/3x | not repeated in this slice | pass |

Actual mixer gain and stereo taps agree. Known channel-asymmetric constant and
sine fixtures preserve L/R. The separate musical run passes finite output,
reader continuity, gain, pause/stop and actual mixer checks; it has no arbitrary
music-specific numerical click threshold.

The independent B lane is compared between the `short` and `short-constant`
scores: A's content changes, while all B commands remain the same. At 48 kHz B's
audio is identical. At 44.1 kHz it differs by at most **0.001953125 file frames
(one float32 ULP)** and **0.0000236407 audio amplitude**. Rates and DSP flags are
identical; gain differs by no more than one float32 ULP.

The initial `audio_error < 1e-6` comparison failed and is preserved in
`initial-paired-lane-report.json`. Its replacement checks at most one position
ULP, unchanged rate/DSP, gain, and the audio predicted from the *measured* reader
positions/gains. That reconstructs both full native stereo captures within
**7.92e-8**; the residual of their difference is **5.48e-8** or less. This
explains the difference without widening an unexplained audio tolerance.

The independent cubic lookup follows the formula in
[Pd's `tabread4_tilde_perform`](https://github.com/pure-data/pure-data/blob/master/src/d_array.c).
The fixed source-to-tap alignment is one file frame and is also observed before
the fade repair (`reference-alignment.json`). It is an empirical property of
this existing path, not a new public indexing rule or proof of its origin.
Review that index/guard-cell boundary in a later source audit. This reference
check supplements the native audio; it does not replace runtime validation.

Older assertions expecting bit-identical repeated cycles were tied to the old
block-rounded wrap. Their original results and replacement rationale are kept
in each case report. Current assertions instead measure accumulated phase and
compare the independent lane. Inactive reader positions can differ; audible
reader resets and the entire output remain checked.

## Retained failures and custody

Thirty bounded native runs were executed. Fifteen are retained here as exact,
losslessly compressed native streams: ten final cases and five representative
controls. `capture-inventory.json` records all thirty, their original hashes and
source identities. The other intermediate exploration streams were moved to
`/tmp/plugmlr-loop-exploration`, not deleted; their reports remain here. They are
not required for acceptance or reproduction of the final result.

- `timing48`, `timing441`: duration scheduling before fade limiting. Exact loop
  timing is restored; old bit-identical cycle assertions can still fail.
- `timing-short48`: same timing repair, but **615** audible reader resets and
  failed output-step checks remain. Exact timing alone does not fix crossover.
- `pre-subframe-turns441`: the first limiter compressed a near-zero remaining
  turn into an abrupt gain change. Maximum L/R step **.0388561 / .0270530**.
- `pre-turn-return-short48`: exempting only sub-sample fragments still failed
  just after a 2 ms wrap. The remaining trajectory was about .03018 ms; applying
  the one-sample margin produced an excessively short fade. Maximum L step
  **.0465065**. The final natural-endpoint return policy repairs this case.

The three corresponding production player snapshots and each capture's manifest
are retained; fade-enabled candidates use the final helper unchanged. The suite
requires the three failure controls to continue exposing their stated faults.
PR #35's original block-delay controls remain in its existing evidence folder.
`archives.json` gives raw/archive hashes and verified byte-exact decompression.
No historical evidence or user stash was edited.

## Reproduce and listen

From the repository root, with Python + NumPy and ffmpeg available:

```sh
python3 tests/analyze_natural_loop.py docs/evidence/natural-loop-timing
python3 tests/check_patch_connections.py sample_player_rebuild.pd
python3 tests/check_patch_connections.py reader-fade-limit.pd
python3 tests/build_record_session_check.py
```

For fresh native captures, close other MLR/diagnostic patches first. Open
`/tmp/plugmlr-record-session/check.pd` in the named Mac plugdata build. Inspect
its real console and set host Audio to 48000 Hz, 512 frames, 1×. Enter one of
these messages in plugdata's console (no leading semicolon):

| Console message | Retained prefix at each host rate |
| --- | --- |
| `record-session-check short` | `final-short48`, `final-short441` |
| `record-session-check short-constant` | `final-constant48`, `final-constant441` |
| `record-session-check turns` | `final-turns48`, `final-turns441` |
| `record-session-check deadline` | `final-deadline48`, `final-deadline441` |
| `record-session-check fit` | `final-fit441` only |
| `record-session-check musical` | `final-musical48` only |

Wait for native `capture-stopped` and `record-session-finished` feedback; the
watchdog is independent of UI automation. Preserve `capture.wav`, `readers1.wav`,
`readers2.wav`, `events.txt` and `manifest.json` from that temporary directory
under a new evidence prefix **before** another run. Close/reopen the fixture
between cases to reset state. Repeat at 44100 Hz, then restore 48000 Hz.
`lane.wav` is the deterministic one-second 48 kHz conversion of repository
`DrumLoop.wav`; its exact copy is `lane-source.wav.xz` here. The asymmetric test
signals are the existing `tests/fixtures/stop-{wave,constant}-48.wav` files.

To reproduce a retained negative candidate, pass its saved production player:

```sh
python3 tests/build_record_session_check.py --player-source docs/evidence/natural-loop-timing/timing-player.pd
```

Use the corresponding score/rate above; the other snapshots work the same way.
Do not load two fixtures together or leave diagnostic recording unattended
without its built-in bounded stop.

`listening.wav` is the **actual stereo post-mixer/master stream** from
`final-musical48-capture.wav`, converted to 24-bit PCM without normalization.
Player A uses the longer drum source; B continues its one-second loop. It lasts
about 14 seconds, peak **.509**, running RMS **.100**. Glides occupy 0.3–3.2 s;
rapid speed/Reverse edits occur near 3.2 s; Pause at 3.6–3.9 s and Stop at
4.2–4.3 s are intentional. More glides/Reverse follow; loop edits and turns
occupy 7.6–12.5 s. Both tracks stop at 12.5 s. The short synthetic stress tests
are separate from this listening file.

**Listening observation: pending.** No report from earlier captures is reused
as acceptance of this source. Numerical limits cannot promise universally
click-free arbitrary cuts or short loops. The new fade policy can change tone
at very short periods. Host rates/block sizes outside those above, long-session
float precision, all sub-2 ms loops, direction slew, recorder tape motion,
foreground/background behavior, hardware input, Bitwig lifecycle and isolated
full applications remain unaccepted by this slice.

The native UI ends at Home with all diagnostic patches closed, no recorder
active, DSP On, host **48 kHz**, output **0.8**, limiter Off. `restored48.jpg`
and `final-home.jpg` record that state. Review/listen before another slice;
this does not begin the larger frontend or modularization work.
