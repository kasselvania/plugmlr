# Grid Record/Finish — 2026-09-16

Base `4c3caff961680a9207c52022ee2244e4b34bd1c1` (accepted BUFFER merge).
User approved remembering the buffer that a track started, so a later Finish
cannot accidentally follow a newly selected buffer.

PLAY column1 uses mlre's record-column position, adapted to our existing fresh-take
writer. It is not overdub, arm-next-cut or mlre tape recording emulation. The six
track rows share the original16 Live buffers. Original Free/sec/bar settings and
input enable remain on screen. No writer/DSP/input/storage implementation changed.

## Native run

Observed actual plugdata UI/console: 0.9.4 nightly98ae0f78b, Pd0.56.3,
pdlua0.12.23; host48kHz. User main remained open with its loaded samples; tests
used private players/buffers901+, unique Lua class names and generated stereo
input. No physical Grid claim, user input, DAC, global DSP or application restart.
The finite score ends20.5s after its one-second delayed start; independent32s
watchdog stops every private writer and player. Console reached
`pattern-check-done: bang`; test tab closed after completion.

The first fixture accidentally declared a one-channel send~ and recorded a silent
right channel. That failed sample, manifest, events, patch and screenshot are in
rejected-mono-fixture. Corrected the fixture to `s~ bcheck-input-record-input 2`,
matching the original application's explicit stereo bus. No production audio
change. Final console shows both expected refusal messages and successful stereo
exports; old entries were not cleared to disguise the failed fixture.

Actual original-writer takes:

| Buffer | Action | Written frames at48kHz |
| --- | --- | --- |
|901|Start, switch Track1 to Sample, Finish remembered Live1|14400 (300ms)|
|902|Fixed0.2s automatic finish|9600|
|903|External buffer Finish releases track ownership|Within64 frames of70ms|
|904|Duplicate key and detach/reconnect do not finish; fresh press does|9600 (200ms)|

The native log verifies admission and recording0/1, not just command dispatch.
Second-track access to an active shared buffer was refused. Unarmed and populated
starts retained no ownership. A press during the selection handoff was refused.
Fixed and external completion restored dim state; an owning track remained bright
while viewing an imported Sample. Medium state showed recording owned elsewhere.
The fixture's export occurs after every take has finished.

`record-analysis.json` verifies both written channels fit the generated220Hz L
(amplitude0.1) and330Hz R(0.2), residual below0.00002, finite output, duration
within one64-frame block, exact fixed length, and zero unwritten capacity. These
are actual buffer samples written by the original writer. They do not establish
universal click-free behavior or post-mixer playback quality. Free capacity is
retained, so its exported test WAVs include silent unwritten tails.

All115 prior native pattern replay cases and17 BUFFER requests/16 commits passed.
Lua tests cover six independent owners, rejected starts, external recording,
completion, invalid IDs, modifier/duplicate/release routing and existing80ms CUT,
pattern timeline and file-codec regressions. Strict current-base guard protects
all76 prior patch/Lua components except the three deliberately changed Grid files.

No new listening report, physical Grid recording, live hardware input,44.1kHz,
Bitwig, recording quantization, overdub, resampling or save/export UX acceptance.
The prior hardware path remains available but was not exercised here.

## Reproduce

From repository root, with Python including numpy for sample analysis:

```sh
lua tests/grid_record_spec.lua
lua tests/grid_buffer_spec.lua
lua tests/performance_pattern_spec.lua
lua tests/pattern_bank_file_spec.lua
python3 tests/build_grid_record_check.py
```

With native DSP already on, open `/tmp/plugmlr-grid-record/check.pd`. It runs once
and stops automatically. Do not run concurrent fixture copies. Read the native
console, then run `python3 tests/check_grid_record.py`. Close only the fixture tab.
Builders preserve original musical/writer logic; the record bridge test copy
accepts isolated901–916 IDs and targets private player readback. Logs, exact source
hashes, score, four stereo exports and console image are retained here.

## Physical playtest

Save live takes and pattern bank before fully quitting/reopening plugdata and
reopening mlr.pd. Existing cached Lua in the open application has not been replaced.

1. Set up stereo input and enable recording on the main screen. Use BUFFER to
   assign an empty Live slot to Track1. Set Free/sec/bars on its player panel.
2. Go to PLAY. Press column1 on row2. Bright means an admitted running take.
3. Change Track1's buffer to a Sample. Return to PLAY; its column1 stays bright.
   Press it: the original Live take finishes. The Sample is not recorded into.
4. Select the recorded Live slot and cut/play it. Listen for the take and verify
   duration on screen. Recording does not launch playback automatically.
5. Try fixed length. Its light clears on completion without a second press.

Dark=no selected Live destination (or switching); dim3=Live selected, not proof
of audible/armed input; medium7=selected buffer recording elsewhere; bright15=
this track's running take. Inspect console if Start is refused. Finish on the
Live takes screen always remains available. Grid detach/page changes do not finish
recording; the existing bounded duration and DSP-off behavior remain in force.
