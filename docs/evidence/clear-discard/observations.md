# Clear / Discard: connections, wrong-slot race and native button observations

Follow-up to PR #39 at `dc141ce6d1b3b04ebea580a50fc86c626a466ba1`.
Original PR base: `566c8608e4d3244471db81118ed1939b471c3eca`.
No musical engine or production panel layout replacement.

## Actual connection trace

| Stage | Actual source and ordering |
|---|---|
| Visible Clear | `player-panel.pd` object 6, bang -> `$1-delete_buffer`; panel argument 1 is the owning player's private `$0`, not the track or slot. |
| Visible Discard | Panel object 81 sends `$0-discard`; receiver 83 -> message `discard` 84 -> send `$1-delete_buffer` 85. Internal `$0` is panel-local. |
| Live-only route | `buffer-selection.pd` 78 receives the player's delete bus; 79 admits kind 0 (Live). Kind 1 (Sample) drops it. |
| Selection handoff | Valid selection marks `$1-buffer-switching=1` immediately; its existing 20 ms delay installs kind, slot, array ID and send target before publishing switching=0. New objects 95–97 gate Clear/Discard on that flag. Commands during switching are dropped, never queued. |
| Destination | Receiver 75 reads `$1-send_target`; object 81 makes `%s_delete_buffer`; dynamic send 80 addresses e.g. `4_l_b_delete_buffer`. The two buttons share this path. |
| Confirmation owner | `take-clear-control 4` in `live_buffer 4` receives that destination. It synchronously queries `live_buffer_4-view-get` for metadata. Missing initial state, recording or busy storage refuses. Unsaved Clear arms for five seconds; separate Discard accepts only an armed request. Saved/empty Clear remains immediate. |
| Cancellation | Selection and navigation cancel; content/status/save/storage changes, expiry or explicit Cancel disarm. Repeated Clear cannot substitute for Discard. |
| Storage ownership | Helper outlet -> `live_buffer.pd` 80/81: second recording/storage busy check -> 82: claim storage busy=1 before entering the original clear path. |
| Reader shutdown | 72 triggers `buffer-will-change` with the live target (73/76); each matching player's `buffer-selection` receiver 73/74 sends its Stop. Content readiness is invalidated and broadcast before delay 74. |
| Actual destruction | After 20 ms, trigger 57 executes right-to-left: resize both `0-live_buffer_N` (L) and `1-live_buffer_N` (R) to 48000 frames; const 0 on both; first/last/slice=0; record-complete=0; publish updated content. Then release storage busy. The 48000-frame allocation is capacity, not one second at every host rate. |
| Feedback | Buffer metadata updates ready/state/waveform and selected player state. `mlr-clear-status` is shared last-action feedback naming the affected live slot. It does not independently identify the current panel's selection. |

There is no additional discard storage path or message-rate audio process.
Clearing a shared live buffer stops every matching reader, not just the initiating
track. Clearing imported sample slots is intentionally not connected here.

## Confirmed wrong-slot race and small repair

Before: selecting Live 4 at 500 ms left the route targeting Live 3 until 520 ms.
Clear at 501 and Discard at 502 reached Live 3 and erased it. Selecting Sample 1
at 600 ms followed by the same commands erased the previous Live 4. The native
console and timestamped metadata showed both failures. Selection cancellation
alone was insufficient: the commands armed a new request after cancellation.

After: one additional `spigot 1`, controlled by `r $1-buffer-switching -> == 0`,
sits between the existing live-kind gate and dynamic send. Both slots survive
the two transitions. Settled Clear at 750 ms arms Live 3; Discard at 800 clears
only Live 3. Live 4 stays ready and Unsaved. The original helper/storage logic
is untouched. There is no queue and no inferred replacement target.

The first repair connected to its appended spigot before declaring it in the
Pd file. Native console reported `cannot connect to non-existing object` and
`(spigot->???) connection failed`; settled Clear did not work. The retained
`rejected-forward-reference` run is **not accepted**. Moving the connection below
the declaration fixes it; the patch-index checker now checks declaration order.

## Tests actually run

Runtime: `/Applications/plugdata.app`, **0.9.4 nightly 98ae0f78b / Pd 0.56.3**;
pdlua 0.12.23, ELSE 1.0-rc14, Cyclone 0.9-4. The retained native WAV headers are
48 kHz. The existing CoreAudio configuration remains 512 frames, 1x, limiter Off.
Only one full application fixture was loaded at a time. Generated 337 Hz left
and 811 Hz right signals record disposable 0.1-second takes. No hardware source,
user take or speaker output is part of this test.

| Run | Native routing / content checks |
|---|---|
| `before` | 6/12; wrong live slots cleared during handoff |
| `rejected-forward-reference` | 9/12; no settled commands reached destination |
| `after` | **12/12**; handoffs protected, settled Clear/Discard works |

`source.json` binds production hashes, copied fixture hashes and exact score;
`events.txt` records actual Pd readback. `capture.wav.xz` retains the two-second,
eight-channel native capture (master L/R, player 1 L/R, player 2 L/R, input L/R).
Playback is intentionally stopped for this routing test: it makes no new claims
about clicks, reader transition audio, listening, DAW lifecycle or 44.1 kHz.
Earlier PR #39 evidence remains separately scoped. All captures have score Stop
at two seconds and an independently armed four-second watchdog.

Existing `tests/check_take_clear.lua`: **18/18** behavior checks. Source protection
and declaration-order checks run against actual current patches; no engine edits
beyond the named routing gate are accepted by `check_ui_overview.py`.

## Native mouse observations — separate from command validation

On the original production panel at 100%, UI-tool clicks at Clear (751,681) and
Discard (841,681) produced no new state. The copied-panel passive probe also
confirmed that Clear emitted no receiver print. Play/Overview
and the upper clock Run were reachable. At 75%, Clear still did not respond.
In edit mode the upper Play could be selected in the inspector; Clear could not.

Disposable copied-panel comparisons kept symbols/connections intact:

- Hiding only `buffer-panel`'s graph-on-parent display did not restore Clear.
- Moving Clear upward in the right column did not restore it.
- Swapping Clear and Play positions made **Clear work** in the upper-left
  position, emitting `UI-1068-delete_buffer: bang` and `Live 1: empty`.
  Play then emitted nothing at Clear's old position. The screenshot's labels
  deliberately remain the original labels in this diagnostic, so consult the
  exact coordinate-swap recipe below; it is not a proposed user layout.
- Native zoom, window fitting/movement and viewport scroll did not establish a
  general cause or a working original-button interaction.

The positional failure is real in these automation attempts. It does **not**
establish a broken send symbol, broken Clear implementation, overlapping buffer
subpanel, runtime defect, or automation defect. No production layout change is
justified by this evidence alone. Human original-position button acceptance is
still separate. No new human listening result was requested for this silent test.

`probed-clear-no-output.png`, `upper-button-selectable.png`,
`no-buffer-gop-still-no-output.png`, `swapped-clear-works-play-does-not.png` and
the before/after console screenshots retain the distinctions.

## Repeat

1. Stop playback/recording and preserve any user takes before closing normal MLR.
2. From the repository, `python3 tests/build_clear_route_check.py`.
3. Open `/tmp/plugmlr-clear-route-check/check.pd` alone in native plugdata.
4. In its console send `ui-check-run bang`; wait for `ui-check-capture-stopped`.
5. Run `python3 tests/analyze_clear_route.py /tmp/plugmlr-clear-route-check`.
6. Open Player 1 from the overview. It selects disposable Unsaved Live 4.
   Click Clear: waveform must remain and the warning must name Live 4.
   Click Discard within five seconds: waveform must become Empty. Retain both
   native UI and console output; console commands are not a substitute for step 6.
7. Close the stopped fixture and restore normal `mlr.pd` alone.

For the positional comparison only, copy the generated `observed-panel.pd` and
swap the first Play object's `30 135` with Clear's `820 680`, leaving all symbols,
labels and connections untouched. Reload the disposable fixture and use empty
Live 1. Restore the generated panel before any ordinary usage. This is a
reproduction recipe, never a production layout recommendation.

## Remaining bounded gaps

- Original-position mouse/human acceptance is open; the selected-slot gate repair
  does not claim to fix this independent UI observation.
- `record-controls.pd` has a similar live-target routing delay, with Record and
  Stop sharing a send. That is a **source finding, not a new runtime result**;
  changing its Stop ownership requires a separate recording test. It is deferred
  with the user's requested pause, not silently accepted.
- Shared last-action status can mention a different slot from the currently
  selected one. It is feedback history, not selected-slot readiness.
- These global instrument buses still assume a single full MLR application per
  Pd environment. No new instance-isolation or persistence claim is made.

No Grid UI work, merges or next slice are included.

Final restoration: normal repository `mlr.pd` is open alone, with DrumLoop.wav
in Sample 1, Player 1 Level 0.4, Master 0.75, clock/playback/recording stopped
and Debug Off. Native settings read back CoreAudio 8A input/output, 48000 Hz,
512 frames, 1x and limiter Off. No physical button reply arrived during this
run; the disposable fixture was closed and the manual procedure remains above.
