# Separate stretch compatibility workbench

This is an experiment, not a new sampler or sample-editor page. `mlr.pd`, the
existing editor, playback, buffer owners and recording controls are untouched.
The two-second input is reproducible stereo: 220Hz L at0.1 and330Hz R at0.2.
Both candidates are asked for twice the duration and +12 semitones.

## Run

1. From the repository root: `python3 experiments/offline-stretch/prepare.py`.
   This makes the input and output directory `/tmp/plugmlr-stretch-workbench`.
2. Open `experiments/offline-stretch/workbench.pd` in local plugdata. DSP must
   already be enabled. Opening it does not start recording. No DAC or hardware
   input is present. Only one workbench instance may use the output directory.
3. The optional worker needs an existing `rubberband` executable. Run
   `python3 experiments/offline-stretch/render_worker.py` before the test, or
   immediately after pressing RUN if measuring concurrent execution. The recorded
   experiment launched it after RUN; it completed in0.358s before the6.5s import.
   This is a separate terminal process; no Pd/Bitwig process launcher is implemented.
4. Press **RUN_12s**. It opens a four-channel capture and runs the bundled vocoder.
   At6.5s it loads the worker file into private stereo arrays with `sfload -t`.
   At12s it stops the capture, then exports staged arrays. An independent14s
   watchdog also stops it. **STOP** ends early. Do not change global DSP to run this.
5. Read the actual native console. Expected messages: `pvoc_finished`,
   `loaded 192000 48000 2 ...`, then `completed`.
6. With Python including numpy, run
   `python3 experiments/offline-stretch/analyze.py`.
   Close the experiment after completion. Application tabs remain untouched.

Capture channels1/2 are the bundled vocoder;3/4 are independent997/1499Hz reference
oscillators at0.05. They let analysis detect internal sample discontinuities while
rendering and loading. They do not measure the hardware callback or post-master
application output. No universal no-dropout claim follows from this test.

If Rubber Band is absent, the worker clearly exits; the vocoder is still testable,
but the scheduled loader reports missing input and combined analysis cannot pass.
Nothing is silently installed. The optional process has a30s timeout. A failed
process has no role in the playing application's buffers.

## Findings from this Mac

Native: plugdata0.9.4 nightly98ae0f78b; Pd0.56.3; ELSE1.0-rc14; pdlua0.12.23;
host48kHz. Installed abstractions resolve through Documents/plugdata to0.9.4-test3.
Optional worker: `/opt/homebrew/bin/rubberband`, version4.0.0, R3 engine.
Both bundled objects created without errors. Actual UI/console were inspected;
capture finished and the test was closed. Main's paused Player2 was preserved.

| Candidate/path | Observed fit | Remaining problem |
| --- | --- | --- |
| Bundled pvoc.player~ | Independent speed/pitch; no added dependency | Same Pd scheduler, real-time render; measured438/657.33Hz rather than440/660; elevated level and nonzero residual after completion |
| Existing Rubber Band CLI | 192000 stereo frames =4s; measured440/660Hz; process0.358s | External dependency and launcher/packaging/plugin qualification remain; synthetic tone is not musical-quality acceptance |
| Bundled sfload -t | Actual stereo import exactly matched the worker output | Final resize/copy in inspected source remains in the result callback; no guarantee for larger loads |
| ELSE batch.rec~ / batch.write~ family | Available batch mechanism | batch.rec~ uses global `pd fast-forward`; excluded from the user's playing environment |

Vocoder steady RMS was about0.09975/0.19886 versus source0.07071/0.14142.
After its done bang, residual RMS at5–6s was0.00577/0.01724. The patch deliberately
retains that behavior as evidence rather than hiding it with a gate. It would need
proper boundary/gain handling and pitch investigation before use in an editor.
The analysis reports the failed2Hz pitch criterion; it does not declare all
candidates successful just because they emit audio.

The capture lasted11.9507s (50ms delayed start, Stop at12s). Reference recurrence
errors were1.26e-7/2.88e-8; no internal sample interruption was detected. An initial
whole-capture exact-frequency fit was too strict for float oscillator frequency
rounding (3.94e-5 residual); the local second-order sine recurrence checks sample
continuity without mistaking gradual oscillator phase drift for a dropped sample.
This is a measurement-method correction, not a repaired audio failure.

No hardware/DAW output capture, musical listening, large-file stress, source/host
rate mismatch, full-app live swap, standalone process-launch object, or Bitwig
plugin process invocation was qualified. Optional processor distribution/licensing
is undecided. SoundStretch was not installed or tested. No dependency choice yet.

The next useful experiment is safe staging/import with realistic file sizes while
measuring actual playing application output and device timing. A process-launch
mechanism also needs qualification before a Render button belongs in the existing
sample editor. Do not replace that editor or the playback engine to accommodate
this experiment.

## Source references and retained evidence

Local installed help/source were read for pvoc.player~, sfload and batch.rec~.
Installed abstraction hashes are retained alongside results. The inspected external
source is [ELSE rc14 sfload.c](https://github.com/porres/pd-else/blob/v.1.0-rc14/Source/Control/sfload.c),
particularly `sfload_read_audio_threaded` and `sfload_update_arrays`. This is an
upstream source reference, not proof of every exact compiled plugdata revision.
[Rubber Band command-line documentation](https://www.breakfastquay.com/rubberband/usage.txt)
defines the tested time/pitch options. No upstream implementation was copied.

See `docs/evidence/offline-stretch`: compressed input/output/staged/capture WAVs,
worker result, preparation hashes, numerical checks and native console screenshot.
To re-analyze retained evidence, pass that directory to `analyze.py`; it reads `.xz`
WAVs directly. No export was automatically played through the user's speakers.
