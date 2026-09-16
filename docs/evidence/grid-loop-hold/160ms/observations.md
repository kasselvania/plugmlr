# Grid loop hold: 160 ms follow-up

The user reported the 40 ms immediate-cut version worked very well after an app
restart, then requested 160 ms. The production change from 8b772662fb96f8f4ba9c5e9cbbc722aeb0abd8d4
is only the LOOP_HOLD_MS constant. This extends loop qualification without
delaying ordinary slice requests. Release still owns loop commit.

Repeat with `python3 tests/build_grid_hold_check.py`, open
`/tmp/plugmlr-grid-hold-check/check.pd` in native plugdata, and enter
`grid-hold-check-run bang` in the console. The silent fixture finishes automatically
after 53.005 seconds; then run `python3 tests/check_grid_hold.py`.

The fixture uses a unique class name to exercise the changed source without
reloading the user's live application. Boundary scenarios use literal
0/5/159/160/161/200 ms overlaps. The established cancellation scenarios retain
their relative ordering, with all command and expected-event times multiplied
by four. Their names refer to the original timeline; source.json records actual times.

Result: all 53 native cases passed. The console confirmed plugdata 0.9.4 nightly
98ae0f78b / Pd 0.56.3 / pdlua 0.12.23 and the completion message, with no new
errors. The existing Grid-not-attached warning predates the run. The fixture
was closed afterward; the user's live MLR remained playing. Source checks
confirm the other 71 root Pd/Lua components still match the PR #42 base.
Lua syntax and diff checks passed. No audio recording or device claim was made.

User acceptance of the 40 ms interaction is distinct from the 160 ms timing
checks. A full plugdata restart is required before the user tries the new threshold.
No new audio acceptance or physical feel at 160 ms is claimed.
