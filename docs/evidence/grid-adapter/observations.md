# Grid adapter observations and repeat procedure

2026-09-11. Native runtime and scope are recorded in STATUS's adapter checkpoint.

## Retained results

`native-events.json` is collected from the actual loaded adapter outlet over the
silent fixture's test-only UDP mirror. It contains size 16/8 and key 3/2 down/up.
The fake server reported callback 17880, corner levels 6 and 15, then after Release
callback zero and eight all-zero LED rows. These are simulator results, not photos.
The physical user confirmed both opposite corner LEDs through integrated MLR;
native console showed (0,0) down/up, (2,1) down/up, and observed-row_1: 2.
Release was read in the actual console: darkened, detached, verified_lease_free.
The historical no-lights failure happened before the old MLR destination was
released; it is documented in the earlier migration checkpoint.

## Repeat

1. Initialize submodules. Run `lua tests/mlr_grid_compat_spec.lua` and
   `python3 tests/check_grid_adapter.py`. Run `tests/check_patch_connections.py`
   separately for mlr.pd, mlr-grid.pd and each of the two Grid test patches.
2. With MLR closed, start `python3 dependencies/monome/tools/fake_serialosc.py`.
   Open tests/grid-adapter-check.pd in native plugdata. It has no audio objects.
   It uses simulated discovery 12012; the live application uses 12002.
3. Send FUDI UDP messages to localhost:17920, separated by semicolons/newlines:
   `session select_index 0`, `session probe`, then after free readback
   `session claim`. Inspect native console at each step.
4. Send `led /monome/grid/led/level/set 0 0 6` and
   `led /monome/grid/led/row 0 7 0 128`. In fake-server stdin, issue
   `grid m100` and `state m100`; use `key m100 3 2 1` and `key m100 3 2 0`.
   Native outlet messages are also mirrored to localhost:17921 for an observer.
5. Send `session release`; confirm dark LEDs and port zero in fake readback.
   Close fixture and quit fake server before physical work.
6. Open MLR, Grid_connection, select the physical device, Probe then Claim.
   If not free, identify the owner rather than silently taking over. Open the
   silent tests/grid-routing-observer.pd and press/release physical keys.
   Verify keys and original row_N messages in the native console. Send legacy
   LEDs through monome_in or use the original LED controls. Obtain user visual
   confirmation separately. Release, verify readback, close observer.

The tests deliberately do not load or start audio. Audible musical behavior and
play-position LED repair are follow-up work; detached initial clears and unsupported
manual intensity/invalid LED messages produce explicit diagnostics.
