# Committed loop range on the Grid

Base: accepted release correction `19245a00b974c0e48ed79157f1c9ef542392377b`.
Native Mac plugdata 0.9.4 nightly 98ae0f78b / Pd 0.56.3. Bundle reports 0.9.4;
executable SHA-256 rechecked in this slice:
`86179a37e58e7a0f0436fc555f56ce41892e3f32ed19b4a3ba8f1cfe3c17476e`.

The two existing playback rows show a smaller committed loop at level 4 and the
running whole-content position at level 12. Pause/Stop remove the marker and
retain the range. Full content has no background; empty/switching buffers clear
the row. Attachment redraws, detach suppresses requests. Only actual committed
state is displayed, never a pending two-key gesture or queued cut.

`native-message-checks.json`: 57 actual native Pd command sequences pass. These
include the previous marker behavior, column suppression, independent rows,
range changes while stopped, paused persistence, invalid bounds, full-content
clearing, rounded file-frame boundaries and reconnect state. Expected complete
level rows are checked against the actual Pd-Lua renderer output, not a separate
model. Original 29-case historical evidence is preserved in grid-feedback.

`tests/check_grid_loop_feedback.py` verifies byte-exact player DSP, original MLR,
loop controller, live-region update, Grid gesture handler and device boundary
against the accepted base. Existing feedback/ALT/loop/tempo-fit/adapter guards
and Lua adapter tests also pass. Earlier exact display comparisons now defer
to the display-only guard; playback comparisons remain intact.

Native UI sequence: released the Grid (verified_lease_free), closed MLR and both
detached views, opened the silent fixture, ran checks, closed the fixture, then
reopened saved MLR. No new load error observed. The existing pre-attachment
legacy Grid command still reports grid_not_attached during application startup;
this is not a new renderer failure. Loaded DrumLoop in slots 1/2, restored track
gains .4/.3, internal clock and 1/16 quantization. Player 1's restored range is
2.68658–8.0597 seconds (physical keys 4–9). Player 2 uses half speed. Console
confirmed connected verified_lease and flushed 6 after claim; player panel showed
Loop_region and the expected bounds while stopped. The user answered “yes” when asked to verify the dim span, brighter moving
marker, paused range retention and ordinary-slice clearing. This accepts those
physical behaviors; the separate two-row/reconnect cases are native-message
checks, not an expanded physical report.

No audio fixture or recorder was opened. This is a read-only display change;
there is no new audio/listening acceptance claim. Existing audio evidence remains
bound to its earlier implementation. No service or dependency changed.

## Repeat

Close MLR before opening `tests/grid-feedback-check.pd` in native plugdata. Run
`python3 tests/check_grid_feedback_native.py` from the repo. The fixture uses
localhost UDP 17930/17931 and emits no audio or device claim. It deliberately
uses the real `grid-playback-row` and renderer. Close it afterward because its
connection messages use the application's shared Grid-connected symbol.

Run `python3 tests/check_grid_loop_feedback.py` plus the existing source guards.
Then reopen MLR, load a sample and claim the Grid through its connection panel.
Set a two-key loop: selected cells should be dim, running marker bright, pause
should retain the range, and an ordinary slice should clear the range background.
Check both display rows, full-content restoration and a device release/reclaim.
Physical testing remains separate from emitted LED messages.
