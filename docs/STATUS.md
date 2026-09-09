# R1: reusable shared-buffer playback

## Authority and source recovery

Base: remote main `5f4b801fea36a33599b2a6bb8b2e34eaeeb527a6`, resolved
before edits on 2026-09-09. Work is on `codex/r1-shared-buffer-playback`.
The supplied parent directory was an empty Git repository; this is a fresh
child clone. No previous files in either checkout were overwritten.

`mlr.pd` instantiates `sample-data`, `live_buffer`, and
`sample_player_rebuild` for IDs 1–16. Its embedded mixer uses `mixer` for
2–16 and a separate track-1 path. `sample-data` owns two arrays and reads
file sample-rate metadata with `soundfiler`; its symbol ordering routes the
first file channel into the array prefixed `1-`, despite reader construction
using `0-` first. R1 uses explicit L/R ordering. `live_buffer` owns two
recording arrays and resizes them through global messages; it includes a
hard-coded `1_l_b_first_record_bang`. `sample_player_rebuild` combines GUI,
clock mapping, buffer selection, recording controls, vline index ramps,
interpolated stereo readers, and two-reader fades. Its loop detector is
forward-comparison based; its mixer-close message includes hard-coded ID 1.
Controls in that patch do not establish working recording or reverse loops.

Recovery retains the soundfiler/paired-array model, file-rate conversion,
`tabread4~` interpolation, `vline~` envelopes and complementary reader mixing.
`sample_playback_new` contains signed-direction endpoint comparisons and
zero-rate special handling; R1 replaces the endpoint message loop with a
signal accumulator with separate whole/fractional frames. `sampler_playback` has paired readers and a
comment identifying possible envelope popping. `sampler_playback_third`,
`sample-playback` and `voice` use incompatible sample naming/output buses.
`sample-data-new`, `live-buffer` and `previous_live-buffer` expose other
loading/recording experiments (including `pdlink`). They are reference
material, not automatically superseded or accepted implementations.

The installed `Documents/plugdata/Patches/Kasselvania/mlr-lite` differs from
GitHub in five patches/scripts and has a `pdlink_subprocess.pd` absent here.
It is preserved read-only. Adjacent `monome_plugdata` is on
`feature/serialosc-leases` at `09c820e` with four dirty files; it is untouched.
The connected MLR Grid path is `monome-object` plus OSC routing and matrix
controls inside `mlr.pd`, using plugdata/ELSE/Cyclone and SerialOSC. The two
Pd-Lua Grid handler files are not instantiated by this entry patch; both
register the same class name and are experiments, not an active adapter.
The `old-sample-playback`/`sample-playback` and `old-sample_playback_new`/
`sample_playback_new` pairs are byte-identical. `rate-change` only snapshots
positions/stores numbers and has no connected playback output. The subprocess patch is missing from this repository; physical
Grid/recording/application behavior has not been validated. R1 needs only
plugdata's bundled Pd objects and Pd-Lua and does not load those dependencies.

## Contract (written before implementation)

- `[r1-buffer INSTANCE BUFFER]` owns one logical stereo buffer. One owner per pair.
  `[r1-head~ INSTANCE HEAD BUFFER]` binds one musical head to it. IDs are nonempty
  symbols or numbers; instrument track routing is outside the engine. Use the parent
  patch's `$0` as INSTANCE. Private reader slots are not heads.
- `load PATH` accepts a stereo file whose metadata supplies its sample rate. Loading
  uses staging arrays. Files must have metadata rates from 8000 through 384000 Hz.
  Invalid/empty/non-stereo files leave the current buffer intact. Replacement is refused
  while any head is started, including rate zero or a stop fade. No resize occurs
  beneath an active reader.
- Public positions and `region START END` use seconds from file start; interval is
  half-open `[START, END)`, zero-based, within `[0, frames/file_rate]`. Region endpoints
  round to the nearest file frame. Minimum region is 0.02 s. Public `rate` is a signed
  multiplier in [-4,4]. Gain is linear [0,1]. `loop` accepts exactly 0 or 1. Default is
  full-file region, loop on, rate 1, gain 1, stopped at zero.
- `seek SECONDS` must be inside the active region. `start` resumes the held position; if
  at a completed boundary it restarts at the directional beginning. `stop` holds the
  position sampled at the command and fades the outgoing reader out. Rate zero holds
  position and fades to silence but retains started state and buffer ownership.
  Subsequent nonzero rate resumes. Repeated start/stop is idempotent.
- Discontinuous seek/region/rate/start changes use two internal stereo readers with a 5
  ms complementary linear crossfade. During a fade, valid subsequent transport commands
  coalesce into the latest desired state and are applied after at least the fade
  duration plus two rendered 64-frame Pd blocks; gain has its own 5 ms ramp. Stop
  retains ownership until those audio blocks complete (also when DSP is paused). No
  reader that is audible is reset mid-fade.
- Loop wrapping is in the audio path. A 1 ms taper on each side of the loop seam reduces
  discontinuity, deliberately attenuating audio near each edge. This is not a seamless
  or universally click-free splice. One-shot playback tapers at its terminal edge and
  then holds silent at the boundary.
- Position advances at signed `file_rate / host_rate` frames per output sample.
  Whole-frame and fractional-frame state are accumulated separately to avoid losing rate
  increments at large absolute indices. Seconds convert to file-frame coordinates;
  physical table indices are clipped to `[1, frames-3]` for four-point interpolation
  (the outer guard samples are held). Both channels use exactly the same index and gain.
  No resampling external or antialias filter is added; high-rate playback can alias.
- Host rate comes from `samplerate~` on DSP blocks, supporting 44.1/48 kHz and file/host
  mismatch. Host-rate changes update the divisor. Extremely long files are limited to
  2^23 frames for Pd float index precision.
- Reports identify head/buffer and include started state, actual sampled position,
  desired rate/region/loop/gain, transition state and host rate. Position reports are
  block snapshots at 20 ms intervals, not sample-timestamped events. Invalid selectors,
  wrong arity/type, non-finite values, out-of-range values and missing owners emit
  errors without changing state. Duplicate IDs fail component creation with a Pd console
  error, preserving the original owner. Stopped heads refresh buffer metadata on their
  next valid command.

## Executed validation

Actual standalone `/Applications/plugdata.app`, 2026-09-09: bundle **0.9.4**,
nightly **98ae0f78b** / `-test3`, Pd **0.56.3**, Pd-Lua **0.12.23**;
universal arm64/x86_64 executable on an arm64 Mac running macOS 26.4.1
(25E253). Binary SHA-256:
`86179a37e58e7a0f0436fc555f56ce41892e3f32ed19b4a3ba8f1cfe3c17476e`.
CoreAudio device buffer 512 frames; each head explicitly uses 64-frame Pd
blocks. No alternate runtime or mathematical playback model was substituted.

`tests/render-*.pd` loaded the real buffer/head abstractions, captured ten
separate audio channels with `writesf~`, and logged ordinary commands and
state. Main A/B/C share one owner. Other A/B use an independent owner in a
second instrument namespace, with the same musical/buffer IDs. Missing and
empty heads exercise failed start. The fixture generator supplies PCM16,
two-second stereo audio: L 220 Hz at 0.25 peak, R 330 Hz at 0.125 peak.

All **41 numerical checks per configuration pass**, plus five checks in a
separate large-position precision render:

| Host / initial file rate | Device output / input | Duration | Output peak | Largest adjacent-sample change |
|---|---|---:|---:|---:|
| 48000 / 48000 | MOTU 8A / Opal C1 | 10.997312 s | 0.250011 | 0.028778 |
| 44100 / 44100 | Built-in speakers / microphone | 10.996304 s | 0.250011 | 0.031361 |
| 48000 / 44100 | Built-in speakers / Opal C1 | 10.997312 s | 0.250008 | 0.028829 |

The automated checks cover ±1, 0.5, 2 and ±4 rates; signed position movement;
independent gains; zero-rate silence and ownership; separate stereo outputs;
seeks and loop/one-shot boundaries; boundary position hold and reverse restart;
30 commands at 1 ms spacing across overlapping fades; repeated starts/stops;
invalid type/arity/non-finite/range/loop/position requests; missing/empty/mono
files; failed replacement preserving the previous buffer version and replayable audio; replacement
while playing, during stop fade and with a sole rate-zero user; and a stop
while DSP is paused. Replacement succeeds only after rendered fade completion.

Main B and other B are **sample-identical** throughout A's changes; main A and
other A match before A's changes. The third head C renders reverse audio at
its own gain from the same buffer. The maximum spectral frequency error
across the tested rates/configurations is 0.0060 percent (0.02 percent test bound). Each channel's
initial frequency and the 0.5 R/L RMS ratio are checked. Eleven isolated
transition windows pass a 0.06 sample-step bound and have at most four
consecutive frames where both channels are below 1e-5; untouched B is checked
for the same dropout threshold. Rapid-command playback recovers, and all
output remains finite and within the fixture's peak bound. These thresholds
are specific to this reproducible signal, not perceptual click-free claims.
The capture-duration tolerance is one 512-frame device buffer because the
writesf start/stop capture has block-boundary truncation.

R1 testing exposed and repaired scoped numeric-symbol formatting, stereo table
message ordering, minimum-region float rounding, stale snapshots in one-shot
completion, boundary hold/restart behavior, and accumulator precision. A
pre-repair mismatch capture measured 219.7983 Hz for a requested 220 Hz tone.
The repaired accumulator also passes a 12-second-file regression at a 10-second
seek / rate 0.5 (110 Hz left and 165 Hz right) on a 48000 host / 44100 file. The final captures postdate
these repairs. No observed failing check remains in the retained final runs.

The initial MOTU/Opal setup did not switch to 44100 when requested. The built-in
pair supplied confirmed 44100 output, checked in both the WAV header and head
state reports. Temporary startup audio configuration was removed afterward;
the original MOTU/Opal 48000/512 setup was restored. Built-in speaker rate was
also returned to 48000; the built-in microphone remains at its original 44100.
Installed services and adjacent repositories were not changed.

### Evidence and reproduction

- `tests/evidence/runtime.json`: binary, platform, devices and exact engine hashes.
- `*-states.txt`: timestamped commands, owner/version/errors and head snapshots.
- `*-checks.json`: measurements, pass/fail decisions and full float capture hashes.
  `precision-*` records the additional 10-second-position regression.
- `*-A-transitions.wav`, `*-B-independent.wav`, `*-C-reverse.wav`: retained PCM16
  excerpts of actual component output. A/B excerpts cover 6.45–7.05 s of the capture; C
  covers 0.25–1.00 s. Conversion to PCM16 is documented in `tests/analyze_audio.py`;
  checks use the full float captures, not excerpts.
- Full ten-channel `*-full.wav` files remain locally in `tests/evidence` and are
  gitignored; rerunning the patches reproduces them. The generator and retained event
  schedules describe exact commands. Follow README to rerun.
- Lua syntax check: `luac -p engine/*.lua engine/*.pd_lua`. Audio analysis: `python3
  tests/analyze_audio.py` with NumPy (this run used NumPy 2.3.5 from the bundled Codex
  Python runtime). No Python package was installed.

The standalone demo was also opened in this runtime. Its file-load button,
A/B/C start controls, independent rate/region/gain messages and stop controls
were exercised through the GUI; separate position displays updated and then
held. This establishes a runnable control path, not human listening acceptance.

### Listening observations and open acceptance

**No human listening observations were collected.** The retained clips are
available for listening; perceptual click/dropout/gain acceptance remains open.
Loop-edge tapers intentionally attenuate the seam, and linear crossfades can
cancel correlated audio. Seamless loops and constant perceived loudness are
not claimed. The short-loop case is intentionally a demanding modulation
case, not proof of musical transparency. No antialias filtering is supplied
for high rates; table interpolation at very long-file indices and arbitrary waveforms need broader
qualification. File loading and finite-sample validation are synchronous and
can interrupt unrelated audio in the same environment; preload before a
performance. Static patch lifetimes are assumed: do not delete an owner while
heads are started or edit its private arrays.

Bitwig smoke testing, DAW lifecycle/save/recall, hardware controllers, recording,
overdubbing and full MLR application acceptance remain open and outside these
results. A DSP-pause ownership regression is not DAW lifecycle acceptance.
Next work requires separate authorization: human musical/transition listening,
then an agreed next toolkit slice or an explicit MLR adapter. R1 does not start
recording or replace the historical application.

Pd-Lua API reference used during implementation:
[upstream tutorial](https://agraef.github.io/pd-lua/tutorial/pd-lua-intro.html).
