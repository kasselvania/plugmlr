# Loop-boundary handoff: native evidence, 2026-09-11

Follow-up on PR #34. Starting head `1e708b7316810afc233daeeaa20829a3ee7cdcb6`;
base main `29ab51e653eded9db9c5aa09850ec4a1352d97e9`.
The only production changes are the original player's `loop_logic` and
`current_position` subpatches. [Source boundary](source-boundary.json) records
their hashes and verifies that the remainder of the player is byte-identical.

## What was repaired

1. The retained [recording boundary failure](../recording-continuity/boundary-results.json)
   stopped at frame zero after Reverse coincided with the first 3.1-second loop
   endpoint. A combined forward/reverse condition stayed high through the turn;
   the single edge detector could not deliver another rising edge. Each direction
   now has its own detector, feeding the original crossover and loop entry.
2. A new range from 0.05 to 0.175 seconds committed at 9.301 seconds in the probe.
   A stale signal edge arrived at 9.30133 seconds and repeated the handoff.
   The old player moved an audible reader by **7,262.995 file frames at gain 0.963**.
   A boundary notification now queries the existing logical ramp and verifies that
   the current position still reaches the current boundary in the current direction.

This is an event check of the existing audio ramp, not message-rate playback.
Public loop positions remain seconds; the internal ramp and check use file frames.
End remains exclusive. Pending cuts retain ownership. The existing 6/9 ms fades,
reader shutdown cancellation and playback/recording Stop distinction are untouched.
No new musical head or transport latch is introduced. An unused early-boundary
diagnostic branch was removed from `loop_logic`.

## Runtime and capture

Actual Mac **plugdata 0.9.4 nightly `98ae0f78b` / Pd 0.56.3**, CoreAudio **8A**,
**512 device frames**, **1× oversampling**, output 0.8, limiter Off. The current
[About view](runtime-about.png) shows 0.9.4. The executable SHA-256 is
`86179a37e58e7a0f0436fc555f56ce41892e3f32ed19b4a3ba8f1cfe3c17476e`, identical
to the runtime previously identified from the native startup console.
[48 kHz](audio48.png) and [44.1 kHz](audio441.png) settings were read in the UI.
Settings were changed only with all patches/captures closed, then
[restored to 48 kHz](restored-audio48.png).

The builder appends controls and passive taps to a verbatim production player.
It loads actual sample/live buffers and both production mixers. Signal processing
inside the player is unchanged by instrumentation. The common post-mixer gain is
0.75; this fixture does not load the complete MLR master path or use DAC, hardware
input, Grid, Bitwig, or a second full application.

`capture.wav`: input L/R, player A L/R, player B L/R, combined post-mixer L/R,
logical position A/B. Each `readersN.wav`: player L/R, master position, direction
sign, reader 0 position/gain, reader 1 position/gain, reader 0/1 DSP flags.
The direction-sign channel is not the complete speed multiplier; motion is
measured from actual reader positions with explicit file/host-rate conversion.
**Do not audition these 10-channel files.** Frame-number channels are not audio.
Use [listening.wav](listening.wav), the actual final musical post-mixer channels
converted to stereo 24-bit PCM without normalization.

Every capture has a 14-second automatic Stop plus a 16-second independent
watchdog armed before starting writesf. Each reader tap has its own bounded Stop.
Native console completion was read after every retained run. The final fixture
was closed. No recording was left dependent on this conversation continuing.

Native writesf's 10-channel header under-reports 164 final frames at 48 kHz and
151 at 44.1 kHz. The analyzer reads declared frames, reports trailing bytes, and
keeps original file bytes in lossless `.wav.gz` archives. Tests finish at 12.5 s;
this final 3.4 ms discrepancy does not overlap their transitions. Its cause remains
unisolated; this is not a claim of missing samples in the production buffer writer.
[Archive hashes](audio-archives.json) bind retained audio to the raw native files.

## Final numerical results

The repeatable [suite report](results.json) includes five successful final cases
and the unchanged historical failures. Every transition sample remains in the
reader-reset and waveform-step checks. Slope bounds derive from the known stereo
frequencies, maximum 4x motion and original 6 ms envelopes, not a listening claim.

| Case | Result |
| --- | --- |
| [boundary-final](boundary-final-report.json) | 21/21 recorder + 14/14 playback/reader checks. Actual stereo input remains exact through growth to 2/4-second capacity. Written bounds are 148,800 frames, not the 192,000-frame allocation. Exact-end Reverse, -.5x and -2x continue. Both reader gains sum to one; no audible reader reset. |
| [final48](final48-report.json) | 37/37. Both direction boundaries, repeated 0.2 ms turns, 2x/4x endpoints, pending cut, endpoint Pause/Resume, interrupted speed glide, Stop/queued Play, loop-range change and empty-buffer recovery. No audible reader reset; maximum stereo steps 0.012604 / 0.011079. |
| [constant48](constant48-report.json) | 38/38. Same controls with distinct signed constant L/R values. Maximum error while running `7.45e-9`; maximum all-sample steps 0.000493 / 0.000247, including intentional Stop/Start fades. |
| [final441](final441-report.json) | 36/36 at 44.1 kHz host with the same 48 kHz files. Correct signed motion after rate conversion; no audible reader reset. Maximum steps 0.013707 / 0.012085. |
| [constant441](constant441-report.json) | 37/37. Constant stereo error `7.45e-9`; maximum steps 0.000590 / 0.000295. |

All final captures are finite. Running reader gains sum to exactly one; no exact
stereo-zero dropout occurs. Pause, Stop and the empty-buffer interval are silent.
Both players and the combined mixer are silent after 12.52 s. Mixer output equals
`0.75 * (0.4*A + 0.3*B)` outside its intentional opening envelopes, with zero
residual. All opening samples are retained and reported separately.

The second lane's actual stereo repeats exactly at 48 kHz while A changes.
Between waveform/constant runs its maximum stereo difference is zero at 48 kHz
and `3.73e-8` at 44.1 kHz; logical-position difference is at most `1.53e-5` file
frames. This is a two-player component comparison, not global namespace isolation.

## Rejected attempts and native UI observations

- `baseline48` uses the unchanged starting player and reproduces the audible
  range-handoff reset. Its source hash is in its manifest; use `--player-source`
  to repeat that exact production revision.
- `boundary` is the first edge-only repair's recorded case; `turns48` then exposes
  the still-unfixed stale range event. Its successful motion alone was not accepted.
- `candidate48`, `strict48`, `constant48-strict` and `initial-direction` retain
  intermediate failures in my logical validator. It read the signal selector's
  1/2 messages, but that selector initializes only its signal to 1. The control
  check stayed at zero on a lane with no direction changes. A rounding hypothesis
  was disproved: the passive trace returned `48000.000000000`; adding a tolerance
  did not repair it. The final version reads the existing 0/1 direction state and
  contains no added epsilon or timing delay.
- The initial extended fixture selected Sample 3 without instantiating its arrays.
  The actual console reported `no such array`. Sample-data 3 is now instantiated
  but empty, matching the application's empty-slot test. Final captures use that
  corrected fixture. No missing-array warning is treated as an accepted load.
- During rate setup the chooser opened `buffer-panel.pd` instead of the fixture.
  The visible title exposed this immediately; it was closed unmodified and the
  absolute fixture path reopened before the retained 44.1 kHz runs. Console
  commands issued to that lone panel produced no capture and supply no evidence.
- `*-console.png` shows native completion, not a complete export of historic
  console contents. Existing voice/debug printouts remain. Timed `*-events.txt`
  and the actual audio carry the numerical evidence.

## Listening, scope and repeat

**No new user listening report.** In `listening.wav`, lane B starts at 0.1 s;
the newly recorded take joins at 4.9 s; exact-end Reverse is at 8 s, half speed
at 9 s and double speed at 10 s. Both intentionally stop at 12.5 s.

Not qualified here: natural loops shorter than the crossover duration, arbitrary
maximum tempo-fit speeds, full-application/device delivery, Bitwig lifecycle,
hardware/Grid interaction, 44.1 kHz Free growth, or changing rate during an active
recording. No universal click-free behavior is claimed. Broader playback/slew
work is next, followed by frontend organization and later reusable utilities;
this repair does not implement that architectural end goal.

1. Close MLR and other fixtures. Run `python3 tests/build_record_session_check.py`
   from the repo (Python and ffmpeg required). Open the exact path
   `/tmp/plugmlr-record-session/check.pd` in native plugdata; inspect the console.
2. With DSP On at 48 kHz / 1×, enter `record-session-check boundary` in the console,
   without a leading semicolon. Wait for `record-session-finished: bang` (~14 s).
   Copy capture/readers1/readers2/live1/live2 WAVs, events.txt and manifest.json
   from that directory to a new evidence prefix before another run.
3. Repeat `record-session-check turns` and `record-session-check constant` at
   48 kHz, then with the host at 44.1 kHz and the same 48 kHz fixture files.
   A manual `record-session-check stop` is available; the watchdog is already armed.
4. Run `python3 tests/analyze_loop_boundary.py PREFIX` (NumPy required), adding
   `--constant` for constant probes or `--recorded` for the original recorded case.
   The full retained report repeats with
   `python3 tests/analyze_loop_boundary.py docs/evidence/loop-boundary-handoff --suite`.
5. For the prior-player comparison, export
   `git show 1e708b7316810afc233daeeaa20829a3ee7cdcb6:sample_player_rebuild.pd`
   to a temporary file and pass it to the builder's `--player-source` option.
   Keep other source files at this PR's version; run `turns` at 48 kHz.
6. Close the stopped fixture and restore host settings. For ordinary use, open
   the original `mlr.pd`, load a sample, raise its mixer, and use **Open player 1**.
   This repair adds no new product entry point or controls.
