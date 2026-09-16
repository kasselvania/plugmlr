# Grid BUFFER selection — 2026-09-16

Base/main `42c4754d8e8bc2e6a26d4f35891a4d6653497c58`. Scope: expose the existing
track buffer selector on Grid, preserving the accepted stereo engine and pattern
bank. This is a control/UI checkpoint, not another audio-engine qualification.

## Layout and prior art

The reference is [mlre grid_mlre.lua at ba88531](https://github.com/sonocircuit/mlre/blob/ba88531bd31656ec33b54beee4f67c5438ae7d35/lib/grid_mlre.lua).
It places REC/CUT navigation at top1/2, macros at5–12, MOD14, Q15 and ALT16;
ALT+Q opens TAPE. Six track rows sit below permanent navigation. Its REC page
combines track focus, reverse/speed/transport and focused-track bottom cuts.
Our existing PLAY/CUT pages adapt that arrangement, with fewer active controls.

This slice borrows ALT+Q and the six-row structure. It does not copy mlre's tape
splice model: our Sample and Live slots are independent stereo buffers. Row2 is
Track1, through Row7/Track6; columns1–16 assign that track's buffer slot. Bottom1
views Sample, bottom16 views Live. Browsing banks does not select or play audio.
Top5–12 remain our performance-pattern bank. Other bottom controls stay inactive.
No upstream source code was copied.

Faint1=empty; dim5=populated; bright15=committed assignment. Switching dims the old
assignment to8 until the original selector commits. The other bank has no false
selected cell. Bank keys use5/15. Top15 lights12 on BUFFER (4 while ALT is held
on other pages). Every selection uses the existing `buffer-select` message path.

## Native observations

**plugdata 0.9.4 nightly 98ae0f78b / Pd 0.56.3 / pdlua 0.12.23**, standalone Mac.
Read the actual UI and console. The user's main was open, Player1 paused with a
sample and a previously loaded pattern bank. It stayed open; no main reload,
Grid claim, input/device change, global DSP command or audio recording occurred.

The first fixture load exposed `take-clear-control $1 ... couldn't create` because
private test slots exceeded its production limit, plus `receive~ ... no matching
send` for its unused recording input. Closed that test, retained its console
screenshot, and corrected the fixture: a uniquely named copy accepts901..916,
and an explicit two-channel zero bus feeds its writer input. Production Clear and
input patches are unchanged. That first attempt is not acceptance evidence.

The corrected finite run reached `pattern-check-done: bang`; the actual console
showed no additional errors after those earlier retained messages. The completion
screenshot intentionally still shows the old failures. Closed only the test tab
and returned to main. `events.txt` is the corrected run, ending at18700 ms.
Normal completion cancels the score, stops all six private players/patterns and
disconnects fixture display output; independent watchdog27 seconds.

## Checks executed

- **17 Grid assignment requests, 16 actual committed targets**, all six original
  players. Three rapid requests coalesced to the last; an additional external
  selection exercised the same path used by on-screen controls.
- Populated Sample1/2 and a real file load into Sample16; empty Sample3; empty
  Live slots and seeded Live16 content metadata through the original owner.
- Page/bank browsing sent no player commands. Track1 switches left Track2's
  transport/selection untouched. Shared-buffer metadata updates remain expected.
- Playing tracks resumed at existing selection entry; stopped tracks stayed
  stopped. A paused track's selection became stopped, as the original selector
  already specifies. Empty selections stopped playback, without rejecting the slot.
- Selection/population/clear metadata reflected in LEDs, including external
  selection, loading while another bank is viewed, slot16 and reconnect.
- Modifier suppression, duplicate downs, held keys across page/bank changes,
  cancelled CUT loop gesture, explicit screen-following routes and pattern controls.
- **115 preceding native pattern replay cases passed** (77 timeline +38 bank).
- Lua checks cover all96 Sample addresses, Live destinations, invalid readback,
  79/80 ms loop qualification, and original timeline/eight-slot/file codec cases.
- Strict source comparison: **75 patch/Lua components unchanged** from this
  slice's base. The two changed Pd files only append routing/readback; the only
  other production edits are the existing key classifier and sole LED renderer.

`analysis.json`, prior-regression analyses, score and source hashes bind these
results. Logical event timestamps are not device latency or audio measurements.
No new listening, audio capture, physical Grid or Bitwig acceptance is claimed.
Seeded live metadata tests selection/display, not recording or Clear/Discard.
The inherited global buffer buses still do not isolate two complete applications.

## Reproduce

From the repository root:

```sh
lua tests/grid_buffer_spec.lua
lua tests/performance_pattern_spec.lua
lua tests/pattern_bank_file_spec.lua
python3 tests/build_grid_buffer_check.py
```

With DSP already enabled, open `/tmp/plugmlr-grid-buffer/check.pd` in the local Mac
plugdata runtime. It starts after one second and finishes automatically. Inspect
the native console; then:

```sh
python3 tests/check_grid_buffer.py /tmp/plugmlr-grid-buffer
```

Close only the test tab. The builder uses unique production Lua test class names,
private musical/player buses and actual players901–906/buffers901–916; metadata
normalization rejects the user's1–16 slots. No DAC/capture or device commands.
Repeated completed runs require closing and reopening the test. Do not run two
copies concurrently. Source hashes cover production and generated fixture files.

## Physical playtest still open

Save live takes and the pattern bank, fully quit/reopen plugdata, then reopen
`mlr.pd` to load changed cached Lua. The existing open main still has old classes;
this work deliberately did not destroy its live state to install the update.

1. Connect the Grid through the usual device page. Load two different samples.
2. Hold top16 ALT, tap top15 Q, release ALT. Bottom-left should be brightest.
3. On row2 select Sample1, row3 Sample2. Go to CUT and play both rows.
4. Return with ALT+Q; select another loaded slot on just row2. Row3 should carry
   on. Check dim populated cells against the on-screen sample bank.
5. Bottom16 shows Live. Merely viewing it should not change either player.
6. Assign an empty Live slot: that track should stop and show the assigned slot.
   Return to Sample and select a loaded slot; CUT can launch it again.
7. Change selection on screen; check that the Grid follows. Use a pattern slot
   from BUFFER, then return to PLAY/CUT; its status must remain visible.

Listen for buffer-switch problems and judge whether bank/selection brightness is
clear. This is the remaining usability gate. Recording, resampling/overdub and
pattern capture of buffer assignments are future work, not hidden page functions.
