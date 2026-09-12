# MOD single-cell loop

Base main `d8f843d78863887bbad2f628bf7bfeafaf7490e9` after merging accepted PRs
#27–#30. The checkpoint tree equals physically accepted `e6a1b51`.

Reference: local read-only mlre checkout verified at
`ba88531bd31656ec33b54beee4f67c5438ae7d35`, lib/grid_mlre.lua track_cut lines
140–185. Upstream MOD calls its single-cell loop on down. We retain our own
keep-position loop semantics, stereo and player. ALT takes precedence here;
upstream ALT+MOD chop behavior is not implemented. No upstream code copied.

Native Mac plugdata 0.9.4 nightly 98ae0f78b / Pd 0.56.3, same executable and
runtime as the merged Grid-feedback checkpoint. The console confirmed
`pdx: reloading grid-cut-keys` before creating fresh objects. Grid was released
(verified_lease_free), MLR and detached views closed, and the silent native
fixture opened. `native-keys.json`: 104 sequences pass. The 78 earlier cases
retain their musical expectations; attachment now also lights the available
MOD LED. Added cases check down-only cell commitment, duplicate suppression,
both release orders, endpoints, held pair cancellation, separate rows/focus,
ALT precedence and clearing modifiers on detach/reconnect.

Production change is confined to the existing gesture Lua class: MOD state,
LED and a new route to its existing loop outlet. No timer or audio processing.
`check_grid_mod.py` verifies exact accepted MLR, player, loop bridge/control,
logical-position handling, renderer and device adapter. Existing source guards
and Lua adapter tests also pass. Display-only guard excludes this later input
change and defers its preservation check to the MOD guard.

The fixture was closed. Saved MLR reopened with DrumLoop in both slots, gains
.4/.3, 1/16 quantization, internal clock at 110 BPM and Player 2 half speed.
Both players initially stopped. Native console confirms connected verified_lease;
no new load error observed. The user confirmed the physical single-cell workflow: “it works.” This records
functional acceptance, not a separate detailed artifact-free listening report. No recording was started for this input-only slice. Earlier audio
captures remain bound to their earlier tests; no new numerical audio result is
claimed. Combined CUT workflow stress remains the next separate checkpoint.

## Repeat

With MLR closed, open tests/grid-cut-keys-check.pd in native plugdata. Run
`python3 tests/check_grid_loop_native.py` from the repo (localhost UDP 17932/17933).
The fixture has no audio, global musical commands or device claim. Close it
before restoring MLR. Run `python3 tests/check_grid_mod.py` and existing guards.

On hardware: start a player with ALT + track row. Hold MOD (top-row key 14),
press one track key, then release in either order. Only that cell should loop;
an ordinary unmodified cut exits the loop. Try the first/last cell, another row,
paused state and ALT+MOD precedence. Test audible output separately from the
native emitted-message record; do not infer listening acceptance from it.
