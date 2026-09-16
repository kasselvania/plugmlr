# Pattern-bank files — 2026-09-15

Base: `912ec750a157a6d05353ed475d95d8b146cf5755` (PR48). Runtime read directly
from the native console: plugdata 0.9.4 nightly 98ae0f78b, Pd 0.56.3,
pdlua 0.12.23 (Lua 5.5, luajit 5.1 listed).

## Native observations

The finite private-bus fixture instantiates two original players, a production
recorder/adapter and a second fresh recorder. It has no DAC or audio recording.
Normal stop is 15.9 seconds after the score begins; a 23-second watchdog stops both
recorders and both players. Actual console completion was inspected.

The first run saved a doubled extension and could not reopen the intended name.
The suffix comparison was fixed and added to the core tests; the retained final
run passes. Old temporary doubled-extension artifacts are not acceptance evidence.

After the fixture, opened `panel-check.pd`: Replace bank changed the visible status
to Loaded (stopped). Save bank opened the native chooser and wrote
`Native ü bank.plugmlr-patterns`. Load bank opened the native chooser and restored
that exact file with Loaded (stopped) feedback. Its bytes match `roundtrip`.
macOS returned the filename in decomposed Unicode; the path remained usable.

Opened repository `mlr.pd` and inspected the footer and console. The footer's help
line initially wrapped/clipped; shortened it. Existing unattached-Grid feedback
appeared (`mlr-grid-compat: unsupported_or_invalid grid_not_attached ...`). No Grid
was claimed. No new persistence exception or missing-object error appeared.

## Numerical/source checks

- 125 native replay commands: 77 prior timeline, 38 prior eight-slot, 10 save/load.
- All populated/empty slots restore stopped/empty; fresh recorder replays stored
  gaps, controls and cuts into the original player command path.
- Invalid-version and missing reads leave the existing bank intact. Invalid load
  during playback preserves the next scheduled cut. Saving preserves replay.
- Dirty loads stage; Cancel and later edits invalidate the candidate. Recording
  refuses Replace; a later explicit Replace restores the full validated bank.
- Lua tests cover lossless floating-point times, 8×4096 events, malformed bounds,
  unknown types/versions, missing/duplicate/unused states, truncation, nonfinite
  data, 4 MiB bound, spaced Unicode paths and destination rename failure.
- Current-base guard: 75 other components byte-identical, nested application wiring
  identical, root changes restricted to footer/background/technical object positions.
- Historical `check_ui_overview.py` fails its outdated Grid-controller comparison.
  It was executed and not weakened; current-base checks supply this slice's boundary.

## Reproduce

From repository root:

```
lua tests/performance_pattern_spec.lua
lua tests/pattern_bank_file_spec.lua
python3 tests/build_pattern_files_check.py
```

Open `/tmp/plugmlr-pattern-files/check.pd` in native plugdata. Wait for
`pattern-check-done: bang`, then:

```
python3 tests/check_pattern_files.py /tmp/plugmlr-pattern-files
```

While that stopped fixture remains open, open its `panel-check.pd` for chooser
checks. Close both test tabs afterwards. Open the repository `mlr.pd` to inspect
main layout. Rebuild gives fixture Lua classes unique names to avoid cached versions.
The retained `source.json` identifies the exact production/fixture hashes and score.

## Limits and user acceptance

The user accepted the preceding eight performance slots. The initial implementation added native UI/control persistence evidence. On
2026-09-16 the user also reported testing Save/Load: sequencing was “a little odd”
but accepted for now, and the instructional readout was praised. No new audio
quality or specific hardware coverage is inferred from that report.
No audio was recorded. No DAW/save-reopen lifecycle claim. Files exclude audio,
assignments and project state. I/O is synchronous; disk latency and performance
under I/O are not qualified. There is no autosave, undo of replacement or quit guard.
