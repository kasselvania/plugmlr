# Bounded Free recording recovery — 2026-09-11

Base: `29ab51e653eded9db9c5aa09850ec4a1352d97e9`. The preceding branch commit
`02e16520cd99ea89a53fb890f68192b6c1b654f0` contained the recording UI proposal.
This evidence accompanies its replacement scope: source tracing and the first
bounded recovery of the original growth policy. Grid recording design is on hold.

## Native runtime and scope

- Mac `/Applications/plugdata.app`, plugdata **0.9.4 nightly `98ae0f78b`**,
  **Pd 0.56.3**, bundled ELSE v1.0-rc14 / Cyclone v0.9-4.
- Executable SHA-256:
  `86179a37e58e7a0f0436fc555f56ce41892e3f32ed19b4a3ba8f1cfe3c17476e`.
- Native Audio settings: CoreAudio, 8A input/output device, 48,000 Hz,
  512-frame device buffer, oversampling 1×. The fixture's `samplerate~` also
  printed 48000. DSP On; output slider 0.8 and limiter Off were left unchanged.
- UI and console were read through the native application. Startup was Home
  with no patch visible. Only the silent fixture was opened. It owns buffer 901,
  uses the production `live_buffer` → `live-record` → `fixed-record~` path and
  new `record-storage`, and has no `dac~`, hardware input or Grid connection.
- The source is a host-rate `phasor~ 7` with L = 0.1 + 0.2 × phase and
  R = −0.25 − 0.5 × phase. Its distinct channels and nonzero values expose
  gaps, channel swaps, gain changes and lost/repeated recorded samples. These
  are numerical measurement signals with DC and deliberate saw discontinuities.

## Executed results

| Retained run | Usable frames | Capacity frames | Growth capacities (frames) | Maximum stereo residual |
| --- | ---: | ---: | --- | ---: |
| `short-48` | 148800 (3.1 s) | 192000 | 96000, 192000 | 0 |
| `fixed-48` | 96000 (2 s) | 96000 | none | 0 |
| `limit-48` | 2880000 (60 s) | 2880000 | 96000, 192000, 384000, 768000, 1536000, 2880000 | 0 |

Every written sample of both channels equals the captured input, using one
common offset of 4864 frames in each source recording. The analysis does not
align channels separately or exclude growth/Stop windows. Output is finite;
the entire unused tail in the early-stop array export is zero. JSON checks
also enforce the fixture's expected duration, growth events and error sequence.
This offset locates recording within the source capture; it is not a measured
hardware latency or a sample-exact UI scheduling claim.

`short` refuses a second Start at 200 ms and Clear at 250 ms, reporting two
`Buffer_busy` errors. Changing the next length to 0.4 seconds at 1000 ms does
not alter the active Free take; Stop at 3200 ms yields 3.1 seconds of content.
`fixed` starts a two-second take at 100 ms, changes next mode to Free at 200 ms,
and still finishes at its two-second target. `limit` starts at 100 ms and the
writer publishes Loaded at 60103 ms after exactly 60 seconds of input.

The fixed and short scenarios were repeated while developing the native panel;
their retained WAVs/events are the final successful runs of those scenarios.
The 60-second capture precedes the view-only edits and an error-trigger change
from `t s b b` to `t a b b`; its success path is unchanged. The final short run
loads the final production sources. Structural checks pass for all changed
patches; that check does not stand in for a native load or audio test.

## Native UI and rejected iterations

- `native-recording-error-48.png`: **Recording** remains visible while
  **Last error: Buffer_busy** reports a refused command. `Content_empty` refers
  to playable content while the take is still running.
- `native-panel-48.png`: after Stop, **Loaded**, **Content_loaded** and
  **Content_seconds 3.1** are visible, alongside the separate next-take setting
  **sec / 0.4 / Limit_seconds 0.4**. The console shows both growth events and
  `free-check-finished: bang`.
- The fixture initially used `select` on a selector message and printed
  `select: no method for 'Empty'`. It was corrected to `route`.
- `rejected-error-label-48.png` retains a rejected product-label iteration:
  `makefilename: no method for 'Buffer_busy'`. The final version uses the same
  `list prepend label` → `list trim` conversion as the existing state display.
  The subsequent short run/readback has neither of these new errors.
- The panel exposes the 60-second Free cap, identifies Amount as fixed-only,
  and states that Start/Stop are immediate. Its received state clears Last error;
  errors no longer overwrite current recording state.

The final fixture was closed only after automatic completion; the native app
returned to Home with DSP On and its original 48 kHz configuration. No diagnostic
recording remains open. No installed service or adjacent repository was changed.

## Reproduce

1. Use the native Mac plugdata build above at 48 kHz with DSP enabled. Close other
   application/test patches for this isolated check. Do not run this fixture
   beside an application using its test buffer ID or its global test receivers.
2. Open `tests/free-record-check.pd` from this checkout. The component paths are
   relative to the fixture. No sample chooser, companion patch or DAC is needed.
3. In plugdata's console enter `free-record-check short` and press Return.
   Use `fixed` or `limit` for the other scenarios. Do not send another scenario
   until the console prints `free-check-finished: bang`.
4. The sequences finish after 4, 3 and 61.1 seconds respectively. An independent
   62-second watchdog is armed **before** capture starts. Both the fixture and
   production writer have automatic stops. `free-record-check stop` finishes the
   fixture early if needed; an early-aborted scenario is not passing evidence.
5. Copy `/tmp/plugmlr-free-array.wav`, `/tmp/plugmlr-free-source.wav` and
   `/tmp/plugmlr-free-events.txt` to `PREFIX-array.wav`, `PREFIX-source.wav` and
   `PREFIX-events.txt` before starting another scenario. They are overwritten.
   The array WAV contains capacity; event metadata identifies playable bounds.
6. Enter `pd-native-panel vis 1` to inspect the real buffer panel with feedback
   routed from this fixture's live buffer. This is a view test, not a full player
   selection/recording workflow test.
7. Run the analysis from the repository with Python, NumPy and ffmpeg available:

   ```sh
   python3 tests/analyze_free_record.py docs/evidence/free-recording/short-48
   python3 tests/analyze_free_record.py docs/evidence/free-recording/fixed-48
   python3 tests/analyze_free_record.py docs/evidence/free-recording/limit-48
   ```

   The local run used Codex's bundled Python with NumPy and the installed ffmpeg;
   system Python lacked NumPy. No package installation was made. The large limit
   WAVs are stored losslessly as `.wav.gz`; the analyzer reads these directly and
   reports SHA-256 for their original uncompressed WAV bytes. Prefix names begin
   `short-`, `fixed-` or `limit-` to select the corresponding fixture expectations.

## Listening and remaining acceptance

**No listening observation was collected for this recovery.** The user is away;
earlier accepted hardware/playback listening reports do not accept these changes.

The checks establish actual recorded-data continuity and native panel behavior at
48 kHz. They do not measure device xruns/wall-clock delivery during allocation,
another playing lane's output, take playback through the original mixer, or a
hardware source. Those are the next Free-recording acceptance checks. Native
44.1 kHz, allocation failure, zero-frame Stop/rapid restart, longer recording,
recording pause/append, overdub, recording quantization, DAW operation and project
recall remain open. This generated host-rate input test has no file/host mismatch
case and does not add a playback resampling claim.
