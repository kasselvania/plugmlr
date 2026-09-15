# Free-time performance pattern — 2026-09-15

Implemented on `codex/grid-performance-timeline`, stacked on the cut-only checkpoint
`fe0a5d49027a0eb0cb75f20d87063e34ca0f9810` (PR #46). This supersedes its first-cut
arming behavior. See STATUS for the contract approved before integration.

## Native UI and controls

Read the actual plugdata console before and after each check. Runtime shown there:
plugdata **0.9.4 nightly 98ae0f78b**, Pd **0.56.3**, pdlua **0.12.23** (Lua 5.5 / LuaJIT 5.1).
DSP stayed on. The pre-existing `grid_not_attached` warning remained; no new Lua,
connection, method or stack errors appeared. The console reported
`pattern-check-done: bang` for each of three finite runs. The final run is retained.
The intermediate runs refined test coverage and added missing initial speed
readback to the fixture; they did not reveal a production playback failure.

The fixture instantiated two original players, with private slots 901/902 and
musical identities 1/2. Both read the same four-second stereo test file. Test buses
and Lua class names were isolated from the already-open MLR. It never connected
speakers, wrote audio, claimed Grid, or changed global DSP. A 9-second watchdog
stopped scheduling and the test players; normal completion was 8.9 seconds after
the score began. All test tabs were closed afterwards. User Track 1 remained
loaded/paused; the user's existing application was not restarted or hot-reloaded.

`check_performance_pattern.py` passed against the retained native log:

- **77 replay commands**, including restore, cuts, speed, both directions and
  Play/Pause/Resume/Stop, checked against fixed expected times and original-player
  state/accepted-action readback.
- Record at 200 ms; first action at 400 ms; last at 1300 ms; Finish at 1400 ms:
  **1200 ms duration, 200 ms leading gap, 100 ms trailing gap**.
- Latest-wins original quantizer capture; replay without further ticks; stale
  pending cut cancelled by replay. Live speed changes still reach the player.
- Rapid transport at 1–3 ms spacing: cancelled Resume/Play does not become a
  recorded Play. Accepted actions repeat with the same transport state.
- Controls-only pattern restores speed/direction while the original position
  feed keeps moving; no transport or cut messages at the boundaries. A stopped
  track stays stopped through repeated control-restoration boundaries.
- Only participating tracks restored; the other lane's controls remain unchanged.
- Pattern Stop, restart, Clear, detach and simulated DSP-off cancellation. Reconnect
  and simulated DSP-on do not restart. Empty/malformed recording and LED states.
- **73 existing patch/Lua components byte-identical** to the base. The original
  player differs only by passive transport observation taps. Its DSP, quantizer,
  pending-entry queues, pause/stop fades and reader handoffs remain unchanged.

Timing is Pd logical message timing as written to the text log, checked within
0.05 ms of the expected score. It is not an audio-device latency measurement.
Actual native position reports support continuity for these cases; they do not
establish universally click-free output.

## Other checks

`lua tests/performance_pattern_spec.lua`: immediate start, both gaps, typed events,
participating-track restore, Stop/restart/Clear including reentrant Clear, malformed
inputs, 4096-event cap, 300-second cap, 10 ms minimum. This uses a simulated clock.
Lua syntax checks and Pd connection checks also passed. The old cut-only tests
and evidence remain historical; the performance suite checks the active path.

## Reproduce

From the repository root:

```sh
lua tests/performance_pattern_spec.lua
python3 tests/build_performance_pattern_check.py
```

Open `/tmp/plugmlr-performance-pattern/check.pd` in the local plugdata runtime
with DSP on. It starts after one second and finishes automatically. Read the
native console, then run:

```sh
python3 tests/check_performance_pattern.py
```

Close only the test tab. `events.txt`, `source.json`, `analysis.json` and the native
console screenshot here are retained from the final run. The builder regenerates
the fixture and its stereo source. No captured audio is used as evidence here.

## User playtest and limits

**Physical Grid playtest and listening for this new timeline remain open.** Prior
cut-page listening acceptance does not cover this change. No new audio capture,
Bitwig lifecycle test, or installed service change was performed.

Save live takes, fully quit/reopen plugdata, reopen `mlr.pd`, connect Grid, and load
samples. Press key 5; wait; play cuts, reverse/forward and speed changes on two
tracks; wait again; press key 5. Both gaps should repeat. The initial speed and
direction return every lap while the tape keeps moving until a recorded cut or
transport action. Try stopping/restarting the pattern and playing over it.

A gap is absence of pattern actions, **not forced silence**. Start/pause state is
not restored at lap boundaries. Thus a transport action already satisfied by the
current tape state has no new effect. This intentionally records a performance
of controls, not a deterministic rendering of the same audio each lap.

No loop gestures, buffer assignment, Fit/glide edits, gain, audio, pattern saving,
overdub, beat-time conversion or quantized pattern launch in this slice. Playback
uses the current buffer and current glide/Fit settings. The broader application
still uses its existing shared buses; this is not full multi-instance isolation.
