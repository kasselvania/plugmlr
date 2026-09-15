# Eight performance-pattern slots — 2026-09-15

Base `d25b266364fc2b52821cf5c6751614b49d90ae85` (PR #47). The user reports excellent
results from that single-slot timeline and approved eight slots, one active at a
time. Switching while recording explicitly finishes and keeps the outgoing take.
The user report accepts the prior musical experience, not every untested edge case.

## Native observations

Read the actual plugdata UI/console before and after the finite check. Runtime:
**plugdata 0.9.4 nightly 98ae0f78b / Pd 0.56.3 / pdlua 0.12.23**. The pre-existing
`grid_not_attached` message remained; no new errors appeared. The native console
reported `pattern-check-done: bang`. The test tab was closed afterwards; the user's
loaded/paused Track 1 and original application were preserved.

The native fixture used the actual Grid classifier, sole LED renderer, performance
bank and two original players. Test slots 901/902, private buses and unique Lua
class names isolate it from the open user patch. The stereo source is generated
by the existing fixture builder. No DAC, writesf, physical Grid claim, or global
DSP command is present. Normal stop: 14.6 seconds after score start; independent
watchdog: 18 seconds. No audio recording was started.

The check passed **38 new bank replay commands plus all 77 previous timeline
regression commands**. Fixed expected logical times are checked to 0.05 ms in the Pd
text log; this is not a measurement of audio-device or physical-key latency.

- All eight physical key addresses through the actual classifier: Record, Finish,
  play/stop, ALT-clear, MOD suppression, duplicate-down and release handling.
- Switching during recording retains its full 200 ms duration and action. Switching
  to an empty slot cannot record the outgoing pattern's scheduled replay.
- Only one slot is recording/playing at every observed status transition.
- Each slot's events, timing and initial controls remain separate. Replayed cuts
  reached the original players, including after switching between tracks.
- Clear of an inactive slot leaves active playback alone; active Clear cancels
  future events. Stopped/recording/playing/empty states render on all eight keys.
- Page change/reconnect retains LED states. Disconnect while recording finishes
  the take; reconnect does not start it. Simulated DSP-off stops the timeline.
- Empty recording remains empty when another slot is launched. Invalid slot
  commands do not interrupt the active phrase.
- The first 8.9 seconds repeat the previous cuts/speed/direction/transport, both-gap,
  rapid-command, quantizer-bypass and continuous-tape-boundary checks.

**75 existing patch/Lua components are byte-identical to the base**, including
all `.pd` files and the player adapter. Only the timeline, key classifier and LED
renderer changed in production. No new audio engine or external dependency.

The Lua test also covers all eight stores with distinct initial states, inactive
Clear preserving the pending clock, invalid slot IDs, switching during a callback,
Clear during the snapshot request, independent 4096-event / 300-second limits, and
the original timing/state cases. These limits use a simulated logical clock.

## Reproduce

From the repository root:

```sh
lua tests/performance_pattern_spec.lua
python3 tests/build_pattern_bank_check.py
```

Open `/tmp/plugmlr-pattern-bank/check.pd` in local plugdata with DSP already on.
It starts after one second and stops automatically. Inspect the actual console,
then run:

```sh
python3 tests/check_pattern_bank.py
```

Close only the test tab. Retained `events.txt`, `source.json`, both analysis files
and the console screenshot are from the native check. The builder reproduces the
patches/source signal. The old single-slot fixture remains available separately.

## Playtest and remaining limits

Physical eight-slot interaction/listening remains open. No new audio capture or
Bitwig lifecycle claim. The prior user's positive report covered the single-slot
version, not this bank expansion. DSP-off here was injected on the fixture's
private control bus; the user's global DSP stayed on.

Save live takes before a full plugdata restart, reopen `mlr.pd`, then use top-row
keys 5–12 on PLAY/CUT. Record into one slot, switch while recording, finish the
second, and switch back. Clear a stopped slot while another plays. Each key should
retain its own status. Patterns are still volatile and closing loses them.

One active pattern, immediate switches, current buffers and current glide/Fit
settings. No beat/bar launch, pattern saving, overdub, loop-gesture capture or
simultaneous patterns. Inactive slots own no running scheduler. Starting a slot
restores its participating tracks' starting speed/direction; it does not reset
position or transport until a recorded action asks for that change.

Switching cancels future timeline dispatches. Already dispatched player fades or
queued transitions remain player-owned and finish normally; this bank does not
roll them back. As before, recording observes actions when the player accepts
them, including requests queued before Record.
