# Grid guide

This guide covers the alpha's accepted Monome lane: legacy Grid `m1000853`,
16 columns by 8 rows, through the pinned lease-aware SerialOSC candidate. The
companion device layer has broader hardware evidence, but plugmlr does not claim
those other layouts as accepted instrument surfaces.

## Before connecting

1. Complete the optional Grid section of [Installation](INSTALLATION.md).
2. Connect the Grid and confirm the lease candidate is the only SerialOSC service
   on UDP 12002:

   ```sh
   cd dependencies/monome
   ./tools/macos_serialosc_lease_candidate.sh verify
   ```

3. Launch PlugData normally, open `mlr.pd`, enable DSP, and keep the console
   visible.

Opening plugmlr or discovering a Grid does not claim it.

## Select, probe, claim, release

1. Click **Grid** in `mlr.pd`.
2. Choose the Grid by stable serial ID in **Select-device**. If it is absent,
   click **rescan**.
3. Click **probe**. Probe reads the selected device's current destination and
   lease state without taking ownership.
4. Read the **Session** field and console. Continue only when the exact device is
   reported free/available. Discovery alone is not permission to claim.
5. Click **claim**. The Session field must reach **connected** after exact
   ownership readback. The lease renews while the session remains healthy.
6. Press a harmless key and confirm both key input and matching LED response.
7. Before closing plugmlr or using another Monome application, click **release**.
   Release first darkens the valid Grid surface, then relinquishes ownership only
   if readback still matches this session.

plugmlr provides no takeover button. If probe reports a legacy destination,
another owner, or displacement, do not try to force it. Release the device from
the owning application and repeat selection and probe. The companion workbench
has a separately named takeover path for controlled acceptance work; it is not a
normal plugmlr operation.

## Surface map

Physical columns and rows below are numbered from 1.

| Top-row key | Action |
| --- | --- |
| 1 | PLAY page |
| 2 | CUT page; also opens the focused player's panel |
| 5–12 | Pattern slots 1–8 |
| 14 | MOD modifier |
| 15 | Q; hold ALT and press Q to enter BUFFER |
| 16 | ALT modifier |

CUT is selected at startup. PLAY and CUT cover tracks 1–6. Tracks 7–16 remain
available on screen.

## CUT page

Rows 2–7 map to tracks 1–6. Each row's sixteen keys address that track's slices.

| Gesture | Result |
| --- | --- |
| Press one row key | Start or resume at that slice; follows the player's Quantize setting |
| ALT + row key | Play, pause, or resume that track immediately |
| Hold two keys on one row for at least 80 ms, then release either | Commit the inclusive multi-cell loop; both key-downs still make ordinary cuts |
| MOD + row key | Commit a one-cell loop immediately |
| Ordinary cut after a smaller loop | Restore full-content bounds and cut to the chosen cell |

Dim cells show a committed smaller loop; the brighter moving cell shows playback.
Pause and Stop retain the dim loop range. Hard Stop remains on the player's screen
panel. ALT wins if ALT and MOD are both held.

A short two-key overlap does not commit a loop. A third held row key cancels that
pair until all row keys are released. Changing page, buffer, or transport cancels
unfinished gestures.

## PLAY page

Each of rows 2–7 controls one track:

| Columns | Action or feedback |
| --- | --- |
| 3–6 | Select the focused track without playing it |
| 8 | Direction; bright is reverse, dim is forward |
| 10–14 | ¼, ½, 1, 2, and 4× speed presets |
| 16 | Play/Pause/Resume; brightness reports transport state |

The bottom row plays the focused track's sixteen cuts and uses the same loop
gestures as CUT. ALT or MOD does nothing to the other PLAY-row controls.

PLAY asks PlugData to show the overview and CUT asks it to show the focused
player. If another PlugData tab stays in front, select the root `mlr.pd` tab
manually; screen following cannot always foreground it.

## BUFFER page — experimental

Hold ALT (key 16), press Q (key 15), then release ALT.

| Area | Action |
| --- | --- |
| Rows 2–7 | Assign Sample/Live slot 1–16 to tracks 1–6 |
| Bottom-left key | View imported Sample slots |
| Bottom-right key | View Live slots, including empty recording destinations |

The bright bottom key identifies the viewed bank. Empty slots are faint,
populated slots are dim, and the track's current selection is brightest. A bank
change changes only the view. Selecting an empty Live slot does not start
recording.

This page has native routing and LED checks but has not completed physical
usability acceptance. It is present as experimental functionality, not part of
the physical alpha claim.

## Pattern keys

Top-row keys 5–12 work on PLAY, CUT, and BUFFER:

- press a dim slot to start recording a performance timeline;
- press it again to finish and loop;
- press again to stop or restart it; and
- hold ALT and press the slot to clear it.

Pattern timing includes the wait before the first action and after the last.
Only one slot runs at a time. See [Performance patterns](USER_GUIDE.md#performance-patterns)
for persistence and capture limits.

## Disconnect or recover

- Normal exit: click **release**, confirm the Grid goes dark, then close.
- USB disconnect: the device layer synthesizes releases for held keys and removes
  the device. On reconnect, select, probe, and claim it again; it never auto-claims.
- Client crash: the accepted daemon should expire the abandoned six-second lease,
  darken the Grid, and return it to free port 0. Verify rather than assuming.
- Displacement: plugmlr refuses to release or overwrite a destination it no longer
  owns. Resolve the other owner, then begin again with probe.

See [Grid troubleshooting](TROUBLESHOOTING.md#grid-problems) for the symptom-based
checks.
