# Native frontend review — 2026-09-12

Base: PR #36, `95a2d612fbb8c799c309850fc53d106d8211ff44`.
Branch: `codex/ui-overview`. This is a UI review candidate, not a replacement engine.

## Views and source boundary

- **Overview:** 16 original tracks, each with Open, Play/Pause, Stop, selected
  buffer/slot, existing transport state, whole-content position and linear Level.
  The original Master control now sits here; its default remains 0.75.
- **Player:** existing controls grouped into source/transport, cuts/loops,
  quantization, shared clock/Beat Reset, speed/glide, recording settings/actions.
  Buffer menu labels are Live/Sample; their existing numeric routing is unchanged.
- **Sample bank:** all 16 existing import slots, their original Load commands,
  content state and duration. For loaded content, duration is
  `(end-first)/(rate_kHz*1000)` seconds; empty content displays zero.
- **Live takes:** all 16 buffer-owned recording destinations, elapsed time, frozen
  limit, state and existing Finish controls. Navigation cannot finish a take.

`track-overview-row` is a view; `player-overview-bridge` forwards existing state
and the Stop command. `sample-bank-row` reads existing metadata. `ui-open-view`
only manages named canvases. It closes secondary views, then opens the requested
one after 20 ms; another navigation cancels that pending open. This compensates
for native `vis 1` not bringing an already-open tab forward. Overview closes the
secondary views without affecting their instantiated player/buffer components.
This shares the application's existing global namespace; it does not solve
multiple-application isolation. The original Grid connector remains its own view.

The source check protects **41 unchanged Pd files**, including the original
player, readers/fades, sample/live storage, recorder, mixer and controller logic.
The nested array, clock and Grid bodies match the base exactly; only startup
visibility flags changed. Inside the original mixer, one Master widget becomes
its named receiver, with every audio connection preserved. Master/level feedback
uses `set` and does not emit another command. No compiled dependency, service,
additional player or audio algorithm was introduced.

## Direct native observations

Baseline screenshots: [main](before-main.jpg), [player](before-player.jpg).
Current views: [overview](overview.jpg), [player](player.jpg),
[sample bank](sample-bank.jpg), [live takes](live-takes.jpg).

The original `mlr.pd` opens at the overview without popping up its wiring canvases.
All 16 overview and bank rows fit at the observed scale. Open works for tracks
1 and 16; Overview returns from player/bank/takes. Actual mouse Play/Pause/Stop
showed Playing, Paused with retained position, then Stopped. The new bank's Load
button opened the normal chooser and loaded the user's stereo synth file, showing
10.6667 seconds; no audio from that private file is published. The included
DrumLoop subsequently showed 14.3284 seconds. Tracks 1 and 2 can both display
Sample slot 1. The selected slot readout does not change another track's source.

All 16 Live Take rows render separately. Clicking Finish on idle destinations
1 and 16 leaves them idle. Active recording, hardware input and new recording
listening were **not** exercised in this UI pass. The existing Grid button still
opens its original connection patch; no device was claimed and no physical Grid
acceptance is inferred. That connector's layout was deliberately left unchanged.

The actual Run button and BPM field were used. Player feedback showed internal,
120 BPM, Ticking and advancing bar/beat while playback remained Stopped. Run was
then turned off; the count remained held. The normal overview was left open with
DrumLoop in Sample 1, track 1 level about 0.4, Master 0.75, internal 110 BPM,
clock/playback/recording stopped. DSP remains On; no diagnostic recorder is loaded.

### Problems found during the pass

The first navigation implementation could not focus the already-open main tab;
`ui-open-view` fixes that. Native inspection caught and fixed one overlapping
Live Take row and player-label collisions. The source comparison caught two
clock connections and two Grid connections accidentally changed during layout
editing. Both complete nested bodies were restored from the base, then the final
native capture added clock/BPM checks. These were implementation mistakes in the
UI candidate, not faults attributed to the DSP or computer.

The native error-only console was empty after the initial fixture run. Normal
startup still prints existing `grid_not_attached` diagnostic messages. Later,
two incorrectly formed manual console commands (`audio-1-out 0.4`) produced
`knob: no method for '0.4'` and `$1: argument number out of range`. The console
requires `audio-1-out float 0.4`; that command and actual slider interaction
worked. Their errors are visible in [the clock observation](player-clock.jpg).
The retained messages were then cleared from the UI, with messages and errors
both left enabled. A cleared console is not used as playback proof.

## Native audio and numerical results

Runtime: Mac plugdata **0.9.4 nightly 98ae0f78b / Pd 0.56.3**. Executable SHA-256:
`86179a37e58e7a0f0436fc555f56ce41892e3f32ed19b4a3ba8f1cfe3c17476e`.
The executable hash/version were rechecked against the preceding runtime record.
[Native settings](audio-settings.jpg): CoreAudio 8A input/output, **48 kHz**,
**512 frames**, oversampling **1×**, DSP On, output 0.8, limiter Off. File rate is
**44.1 kHz**. No device/settings changes or substitute runtime were used.

Four seven-second captures ran during development. The retained final run uses
the restored clock/Grid source and the final UI/master readback. The fixture is
a copy of the complete current `mlr.pd`: its DAC is replaced by an unconnected
signal join so it cannot play through speakers. Passive taps record the actual
post-master L/R and original players 1/2 L/R. An eight-second independent stop is
armed before recording; the score normally stops at seven seconds. Native
[console completion](capture-stopped.jpg) confirms `ui-check-capture-stopped`.

The final **19 numerical checks pass**. Ten steady windows match the expected
stereo mix exactly at float32 precision, including initial Master 0.75, Master
0.5/0.75 and track 1 level 0.4/0.2/0.4. Pause/Stop silence is verified at the
player taps; both final player and master taps are silent. Lane 2 stays running
through lane 1 transport changes and navigation. Both position streams advance
through player/bank/takes changes. Gain readbacks produce no command echoes.
At 120 BPM, the clock’s 16 ticks per quarter note are 31.25 ms apart; clock Stop
emits no further ticks while playback continues.

Whole-recording checks retain all transitions: no non-finite samples and no
output beyond the maximum requested gain bound. The longest exact-zero run
between the first start and final stops is 15 host frames (0.3125 ms). Stereo
peaks are 0.511735 / 0.510499. Maximum adjacent steps are 0.363241 / 0.362749;
these raw waveform measurements are **not** a click-freedom verdict. Steady gain
windows exclude intentional mixer attacks. The test is about UI command/gain
preservation, not a new full playback qualification.

`capture.wav.xz` preserves the native WAV exactly; `source.json` binds production
hashes, fixture hash and score. `events.txt`, `score.txt`, `audio-checks.json` and
`source-checks.json` retain the measurements and source boundary. The native WAV
header declares 335918 frames and leaves 1968 trailing bytes (82 six-channel
frames). Analysis uses only declared frames; all last events finish by 6.509 s.
[Listening WAV](listening.wav) contains the actual first two post-master channels.

**Listening:** no new listening test or user usability report yet. Earlier user
reports do not accept this UI or close PR #36's pending listening. New 44.1 kHz
host operation, DAW/plugin editor layout, smaller displays/other zoom levels,
foreground/background audio reliability and active recording UI remain open.

## Repeat

From the checkout, with other MLR/test patches closed:

```sh
python3 tests/check_ui_overview.py
python3 tests/build_ui_overview_check.py
```

Open `/tmp/plugmlr-ui-check/check.pd` in the named Mac plugdata runtime at
48 kHz. In its console, send `ui-check-run bang`. Wait for the automatic stop
message and verify both tracks/clock stopped. Do not run it beside another MLR
application: this checkpoint still has shared global names.

With a Python environment containing NumPy:

```sh
python3 tests/analyze_ui_overview.py /tmp/plugmlr-ui-check
python3 tests/analyze_ui_overview.py docs/evidence/ui-overview
```

Close the fixture and reopen the normal `mlr.pd`. Follow the README quick start
and review the actual controls. No listening or hardware report is fabricated by
the scripts. Product export/recall, direction slew, modulation and further Grid/
Arc design remain subsequent work.
