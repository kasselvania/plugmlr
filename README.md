# plugmlr

An expandable, softcut-style stereo playback/recording toolkit for **plugdata**.
MLR is its first substantial musical application, not the toolkit's head-count
or musical-control limit. R1 recovers shared-buffer playback; recording and
overdubbing are future work. This is not an exact softcut implementation.

## Run R1

Requires Mac plugdata with its bundled **Pd-Lua** (validated runtime and results
are in [docs/STATUS.md](docs/STATUS.md)). No new external needs installation.

1. Open `demo/shared-playback.pd` in plugdata and enable DSP.
2. Double-click the left `r1-demo-instance` box to open its controls.
3. Click `load ../tests/stereo-48000.wav`, then `start` under A and B. Alternatively
   use **Choose_stereo_file**. The retained fixture is a quiet two-second stereo
   tone: L 220 Hz, R 330 Hz at half L's amplitude.
4. Use each head's seek, region, loop, rate and gain messages independently.
   Start C to hear a third head through the identical interface.
5. Open the right instance and repeat. Each has its own `$0` namespace inside
   the **same Pd environment**. Stop A, B and C before replacing its buffer.

The entry patch mixes separate head outputs at a conservative level. The
components themselves have no GUI, DAC, controller mapping or track identity.
`mlr.pd` and all historical patches remain intact; their old external/controller
requirements and incomplete behavior do not apply to this demo.

## Embed the components

Use a parent `$0` (or another unique instrument-instance ID):

```
[engine/r1-buffer $0 shared]
[engine/r1-head~ $0 A shared]
[engine/r1-head~ $0 B shared]
[engine/r1-head~ $0 C shared]
```

Use a path appropriate to the caller's directory. The buffer inlet accepts
`load PATH` and `status`. PATH is absolute or relative to the `engine` directory;
the demo file chooser supplies an absolute path. Buffer binding is fixed by
creation arguments in R1. Each head inlet accepts ordinary messages:

| Message | Meaning |
|---|---|
| `start`, `stop` | Explicit transport; repeated commands are idempotent |
| `seek 0.75` | File position in seconds inside the current region |
| `region 0.25 1.5` | Half-open loop/playback bounds in seconds |
| `loop 0` / `loop 1` | One-shot / wrap |
| `rate -1`, `rate 0.5` | Signed multiplier, supported range -4 to 4 |
| `rate 0` | Hold silently while retaining buffer ownership |
| `gain 0.5` | Linear gain from 0 to 1 |
| `status` | Current state and sampled position |

Head outlets are **left audio, right audio, messages**. `state` atoms are
`INSTANCE HEAD BUFFER started position_seconds rate start_seconds end_seconds
loop gain transitioning host_rate`. Buffer reports `loaded INSTANCE BUFFER
frames file_rate duration_seconds version` and `buffer INSTANCE BUFFER frames
file_rate version in_use`. Errors are explicit messages on the status outlet.
See the full contract and transition limitations in [docs/STATUS.md](docs/STATUS.md).

## Repeat validation

`python3 tests/make_fixture.py` regenerates fixtures. `python3
tests/generate_harness.py` regenerates the render patches and command schedules.
Set the plugdata host rate **before opening** the corresponding patch:

- `tests/render-48k.pd`: 48 kHz host, 48 kHz file.
- `tests/render-44k.pd`: 44.1 kHz host, 44.1 kHz file.
- `tests/render-mismatch.pd`: 48 kHz host, 44.1 kHz file.

`tests/render-precision.pd` adds a 48 kHz host test with a 44.1 kHz file, a
10-second seek and rate 0.5. It completes after about four seconds.

Each of the three main patches automatically renders actual component outputs for 11 seconds to
`tests/evidence/*-full.wav`, logs state/commands and prints `R1-DONE` after about
13 seconds. Close it before the next run. There is no DAC in the harness.
Run `python3 tests/analyze_audio.py` with NumPy available to check the captures.
Retained excerpts/results and their scope are described in the status note.
