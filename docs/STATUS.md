# Original application: observations and functionality map

Recorded 2026-09-09. The baseline is repository main at
`5f4b801fea36a33599b2a6bb8b2e34eaeeb527a6`, verified against the remote before
creating `codex/original-playback-observations`. That initial update changed
documentation only; the authorized load-refresh repair is recorded below.
The current job is to understand and harden the existing musical path in
small steps; the broad R1 implementation plan has been set aside.

## Preserved work and source map

The rejected rewrite is preserved on `codex/r1-shared-buffer-playback` at
`fb808b13c12bb818a7c59798c630be172ec08631` and in
[PR #1](https://github.com/kasselvania/plugmlr/pull/1). Its uncommitted changes,
untracked files, and ignored renders were saved with `git stash --all` as
`23dfe32e8cfd76a15ecc0f4c8a30248dd95704a0` (message begins
`Failed experiment: R1 rewrite before archival`). Do not apply or drop this stash
as part of the original application's investigation. Those experiments are not
acceptance evidence for this baseline.

| Source | Role in the original entry path |
| --- | --- |
| [mlr.pd](../mlr.pd) | Application controls, clock/Grid paths, `arrays-samples`, and mixer. Instantiates sample data, live buffer, and player for IDs 1–16. |
| [sample-data.pd](../sample-data.pd) | File chooser, two sample arrays, `soundfiler`, sample metadata publication. |
| [live_buffer.pd](../live_buffer.pd) | Live arrays, size/index metadata, recording-related messages. Recording not tested here. |
| [sample_player_rebuild.pd](../sample_player_rebuild.pd) | Selected buffer, transport, loop/slice logic, rate glide, playbar, two stereo readers, and gain transitions. |
| [mixer.pd](../mixer.pd) | Track output gain/envelope. Track 1 is implemented inline in `mlr.pd`; tracks 2–16 use this abstraction. |

Alternative players remain useful references, not automatically active code.
For example, `sampler_playback.pd` contains a post-load refresh receiver absent
from the active player. The installed copy at
`/Users/peterkassel/Documents/plugdata/Patches/Kasselvania/mlr-lite` also differs
from this checkout, including its player logic. It is a read-only reference;
the observed application was opened from this repository.

## What was observed

Runtime: `/Applications/plugdata.app`, **0.9.4 nightly `98ae0f78b`**, Pd **0.56.3**,
Pd-Lua **0.12.23**, on macOS **26.4.1 (25E253), arm64**. This was a native plugdata
session. Audio-device settings were not freshly recorded as part of this baseline.

- `mlr.pd` opened, along with its saved `arrays-samples` and `grid-input-output`
  views. The 1–16 buffer/player objects were visible; the console printed reader
  setup messages for them. With ordinary messages hidden and errors shown, the
  startup error view was empty. Ordinary messages were then restored.
- The existing Sample 1 load control opened the native chooser and loaded the
  repository's `DrumLoop.wav`. During this observation the control was triggered
  using plugdata's console selection and `bang` after pointer attempts were
  inconclusive; it was the existing `1-sample-load` control, not a helper loader.
- Both arrays in `sample-data 1` visibly populated. Its UI showed **631881 frames**,
  **44100 Hz**, and **39492.6** frames per slice (rounded display). Read-only
  `afinfo` agreed: stereo, 24-bit PCM, 44100 Hz, 631881 frames, 14.328367 seconds.
- Player 1 selected `sample_buffer`, `1`. Pressing its Play/Pause button moved the
  playbar. After the user raised the mixer, the user confirmed audible output.
  This establishes **Sample 1 → player/channel 1 → mixer → output**.

User listening report, recorded separately from source/console evidence:

> “it cuts out part way through the loop that plays, then, goes through a full
> loop without audio. then, starts again.”

The playbar continued moving. Representative console messages included
`dsp-message: dsp_off 0`, `voice_1_vline: 631881`, `dsp-message: dsp_on 1`, and
`voice_1_vline: 631865`. These are existing debug prints, not explicit runtime
errors or proof of a cause. The relationship to reader switching, gain fades,
loop bounds, and beat resets has not yet been established.

There is working playback infrastructure and a reproducible musical fault.
No explicit console error was observed in the inspected startup view; that does
not prove every path works or establish the cause of the audible fault. Other
channels, reverse, glide, slice triggering, quantization/beat reset, physical Grid
feedback, recording, and buffer replacement have not been individually validated.
Connected controls and code for several of these already exist.

Evidence here is the session's direct UI/console inspection, the user's listening
report, and the file metadata check. No rendered audio, numerical audio checks,
standalone console export, or new test harness was retained for this baseline.
No Pd patch was edited or saved during the observation.

## First chunk: loader to player metadata

This is a trace of the actual objects and `#X connect` edges, not a proposed new
interface. Line references below refer to the baseline commit above.

1. In `sample-data.pd` (lines 10–25), `$1-sample-load` triggers `openpanel`.
   `t a b b` fills two table symbols before sending the path through `pack s s s`
   and `prepend read -resize` to `soundfiler`. The resulting order is
   `read -resize PATH 1-sample_buffer_ID 0-sample_buffer_ID`: file channel 1 enters
   prefix `1`, file channel 2 enters prefix `0`.
2. The frame-count outlet supplies the end field and `N / 16` slice length.
   First index is set to zero; a literal `1` supplies the loaded flag. The rate
   metadata is divided by 1000, yielding samples per millisecond. The packet on
   `s_b_buffer_states` is `ID loaded_flag rate_kHz slice_frames first_index end`.
   For the observed file the graph yields `1 1 44.1 39492.5625 0 631881`; this
   exact packet was not captured as a console print. The field named “last index”
   carries frame count `N`, not `N - 1`.
3. In the player's `buffer_&_loop` (lines 175–208), `route` matches the selected
   buffer number. `t a b` sends `$0-loaded_sample` **before** unpacking the new
   metadata. `buffer_selection_setup_and_logic` uses that bang to select this
   player's own sample-buffer number through the existing GUI/message path.
4. Selection sends `$0-send_target`. The player sends the target's `_select_bang`
   and `_load_up` messages and refreshes cached indexes with `$0-update_indexes`.
   Only afterward does the pending sample packet finish unpacking. Its loaded
   flag is sent to `$0-loaded_update_indexes` after the other fields are stored,
   but the active player has **no receiver for that completion message**.
   The initial Play path separately sends `$0-update_indexes` (line 363).

This ordering is consistent with the observed console sequence: after loading,
`1188-loop_end` still printed `48000`; pressing Play printed `631881` and loop
start `0`. It identifies a metadata handoff problem to isolate. It does **not**
establish the cause of the subsequent alternating silent passes.

Three local candidates recorded by the initial trace (the first is now repaired
as described below; the other two remain unimplemented):

| Candidate | Existing evidence and narrow next check |
| --- | --- |
| Complete the post-load refresh after metadata is stored. | The active player emits an unreceived completion message. `sampler_playback.pd`, lines 1239–1242, already has `r $0-loaded_update_indexes → sel 1 → s $0-update_indexes`. Evaluate that small existing pattern against the selection order, then inspect load-time bounds before pressing Play. |
| Resolve the channel-order discrepancy. | The loader orders arrays `1, 0`; `tabread_processing` constructs reader targets `0, 1` (lines 708–730). The console printed `set 0-sample_buffer_1 1-sample_buffer_1`. Verify the complete output with distinct left-only/right-only material before changing ordering; ordinary stereo listening did not establish it. |
| Validate successful load publication. | `sample-data.pd` publishes a literal loaded flag without a positive-frame-count check; channel metadata is unused. Missing/empty/mono-file behavior has not been exercised. Check what the actual loader emits in those cases before adding a small guard. |

The next buffer trace must account for two existing details: sample and live
metadata packets have different layouts (`l_b_buffer_states` is
`ID rate_kHz first_index end slice_frames content_flag`), and `sample-data.pd`
has no `_select_bang` or `_load_up` receiver to republish metadata on reselection.
The loader also resizes its arrays directly. Selection, alignment, swapping, and
replacement behavior therefore need observation before refactoring.

## Follow-up: complete the post-load refresh

The user advanced the first candidate. On `codex/fix-sample-load-refresh`, the
active player's unreceived `s $0-loaded_update_indexes` is replaced by `sel 1`,
and its matching outlet is connected to the existing `s $0-update_indexes` in
`buffer_&_loop`. This is one object replacement and one connection. It recovers
the completion behavior found in `sampler_playback.pd` without adding a relay.
`unpack` emits the loaded flag last, after storing the end, start, slice size,
and sample rate, so the refresh reads the newly stored values. Object numbering
and every other existing connection remain unchanged.

Native plugdata checks, in the same runtime identified above:

| Check | Observed result |
| --- | --- |
| Fresh original application, load `DrumLoop.wav`, do not press Play. | Console player ID `1471` ends the load with `loop_end: 48000`, `loop_start: 0`. Reproduces stale active bounds. |
| Close that stopped instance, reopen the repaired `mlr.pd`, load the same file, do not press Play. | Player ID `1753` ends the load with `loop_end: 631881`, `loop_start: 0`. |
| Load the user's `SC_ICD_90_synth_chords_sunny_Cmaj.wav` into Sample 1 while still stopped. | The same player ends the load with `loop_end: 470400`, `loop_start: 0`. `afinfo` independently reports stereo 24-bit PCM, 44100 Hz, 470400 frames, 10.666667 seconds. The user's file is not included in the repository. |
| Open another load chooser and cancel it. | No new load-result messages; the buffer panel still shows start `0`, end `470400`, rate `44.1` samples/ms. |
| Inspect the repaired `buffer_&_loop` in the actual application. | The new `sel 1` connection and those master values are visible. Play has not been pressed during these comparisons. |

The initial selection still prints the previous bounds before completion. The
repair adds the missing final refresh; it does not make selection/loading atomic
or make replacement under an active reader safe. Loading while playing was not
tested. The loader's unchecked success flag and channel-order candidate remain
unchanged.

The before-repair chooser was opened by clicking Sample 1 Load. Pointer attempts
after reopening were inconclusive, so the repaired loads used plugdata's console
to select the same existing `bng_1` (inspector send symbol `1-sample-load`) and
send `bang`, followed by the native file chooser. No helper audio patch was opened.
This confirms the existing load-message path; it is not a general pointer/UI test.

An explicit error-only console inspection showed three errors caused by the
agent's navigation attempts: `canvas: no method for 'sample_player_rebuild_1_1'`,
`canvas: no method for 'buffer_&_loop'`, and
`No object found for: pd_buffer_&_loop_indexes_data_1`. These were not emitted by
loading. The inspection showed no additional errors. Console history was not
cleared, and both message and error visibility were restored. For future read-only
inspection, the working console sequence is `ls`, then `sel` with the exact
listed object ID, then `vis 1` and `deselect`; `cnv` sends a canvas message and
does not navigate to a child by name.

Repeat the first two rows using the original observation commit and this repair,
one application instance at a time. Inspect the final loop-bound prints before
pressing Play. This validates the control-message refresh in the actual patch.
It is not a rendered-audio test: no new listening verdict, recording, audio
numerical check, or claim that the alternating silent loops are fixed is made.
At the end of that comparison, the repaired application was left stopped with
its buffer panel open. This describes that check, not subsequent user activity.

## Whole-application functionality map

The user expanded the review to understand **all existing musical functions**
before choosing further repairs or refactoring. This section reads the actual
`.pd` declarations, canvas-local `#X connect` edges, trigger order, and matching
send/receive names. Source references here describe repair candidate
`0f8c26789ec6e70e815385d6dca88a0c0b92f0ef`; the remote main remains
`5f4b801fea36a33599b2a6bb8b2e34eaeeb527a6`.

This update changes documentation only. A read-only native UI/console snapshot
showed the existing application and subsequent user playback messages; it adds
no controlled behavior or listening result. The observations and load-refresh
comparison above remain the runtime evidence. Findings below establish wiring
and gaps, not the audible cause of each reported fault.

### How the existing parts relate

```mermaid
flowchart LR
  File[File chooser] --> Sample[Sample arrays and metadata]
  Live[Live arrays and metadata] --> Selection[Selected buffer and cached bounds]
  Sample --> Selection
  Grid[Grid and slice input] --> Quant[Quantization and slice position]
  Clock[Clock and PPQ] --> Quant
  Clock --> Motion
  Quant --> Motion[Transport and frame trajectory]
  Controls[Play, pause, stop, rate and direction] --> Motion
  Slew[Rate and direction slew] --> Motion
  Selection --> Motion
  Motion --> Loop[Loop boundary detection]
  Loop --> Motion
  Motion --> Readers[Two stereo readers and fades]
  Selection --> Readers
  Readers --> Mixer[Track and master mixer]
  Motion --> Display[Local playbar]
  Rec[Record Arm UI] -. no active writer connection .-> Live
```

The two readers are internal transition voices within one musical player.
The active patch also has a master `vline~` used for position snapshots and loop
detection; each reader has its own `vline~`. They receive related commands but
are not one physical signal path. This distinction matters when the playbar
moves during silence.

### Function catalogue

“Connected” below means a source path exists. It is not listening acceptance.
Player references mean `sample_player_rebuild.pd` unless stated otherwise.

| Function | Actual control, state, and path | Current status |
| --- | --- | --- |
| Stereo file load | `sample-data.pd`: `ID-sample-load` → chooser → `soundfiler` → two arrays, frame count, file rate, 16 equal slice lengths, loaded flag. | Load and final bound refresh observed. Success validation, replacement safety, and channel ordering remain open. |
| Buffer choice and metadata | Main sends default selections for IDs 1–16. Player `buffer_selection_setup_and_logic` and `buffer_&_loop`: type/number select array names, request metadata, and store start/end/rate/slice/content values. Delete dispatches to the selected target. | Substantial selection logic; reselection and type/number identity gaps below. Sample deletion has no handler. |
| Live storage, clear, and growth metadata | `live_buffer.pd`: two arrays, size query, first-record notifications, first/last indexes, resize, delete/clear, content flag. | Storage/metadata code exists. It does not itself supply an active recording writer. |
| Play, pause, resume, stop | Player root: flags dispatch initial play or pause/resume; snapshot current frame; rebuild motion; control mixer envelope. Stop clears flags and resets motion/reader selection. | Play and mixer output observed. Pause has a connected mixer-close path. Other transport combinations are not individually validated. |
| Slicing and jumps | `row_$1` → immediate/quantized selection → slice number × slice size; reverse chooses the next slice boundary; request reader transition and jump after a 1 ms delay. | Existing slicing, not missing by design. A slice jumps into the buffer and continues toward the current loop boundary; it does not automatically loop just that slice. |
| Position and visual playbar | Internal frame-position messages → ordered bound/rate refresh → duration calculation → `vline~`; 20 ms snapshots update the local playbar. | Moving playbar observed. The visible slider has no outgoing seek connection; it is a display in this version. |
| Key quantization | PPQ modulo a power-of-two interval; store pending slice; pass it at the selected tick. Immediate and quantized branches share the slice output. | Connected, with toggle meaning and repeated-key ordering problems below. No physical Grid test. |
| Loop bounds and wrap | `loop_logic`: compare master frame position to end, prepare a reader transition near end, then request start. Bounds are cached from selected-buffer metadata. | Forward-only detector in this version. No complete reverse wrap or dedicated user loop-enable path found. Internal bound controls are present. |
| Speed | Five presets: 0.25, 0.5, 1, 2, 4. Snapshot position and recalculate remaining duration from rate and file sample rate. | Real speed-control path exists. Magnitude and direction are separate; this is not a signed-rate message contract. |
| Rate slew/glide | Duration and curve knobs → `curve~` → `cyclone/snapshot~` at a nominal 5 ms interval → updated rate and trajectory; completion latches the target. | Existing glide implementation to retain. Its separate engage toggle has no consumer in this player. |
| Direction and direction slew | Direction button changes a 0/1 state and chooses the trajectory endpoint. Separate curve/delay logic appears intended to slow to zero, switch direction halfway, and return to the requested speed. | Direction selection exists; loop detection and reader inversion disagree with it. The direction-slew command construction is disconnected. |
| Clock mode and beat reset | `mlr.pd` derives internal/DAW PPQ and BPM. Player duration calculation has a clock mode; beat-reset selection counts PPQ intervals and emits a reset message. | Clock source code exists. Beat reset ends at an unreceived message; clock-duration inputs include obsolete metadata names. |
| Reader handoff and crossfade | `tabread_processing` selects stereo arrays. `gain_control_logic` alternates voice 0/1 and sends gain, message-gate, and DSP commands. | Core existing design worth understanding. The two reader implementations and transition handlers are asymmetric. |
| Recording and overdub | Active player exposes Record Arm and recording flags. Alternative `sampler_playback.pd` contains timed/endless recording decisions and stereo `poke~` writers. | Record Arm has no receiver and there is no writer in the active player. Alternative recording must be traced/recovered as a feature, not inferred from the button. Overdub mixing is unvalidated. |
| Input, track gain, and master | `mlr.pd` and `mixer.pd`: stereo player output → transport envelope → track gain → master → `dac~`. Separate input/monitoring sketches exist. | Track 1 output heard. Input knobs do not establish a recording route. Track 1 inline mixer duplicates the abstraction used for 2–16. |
| Grid input and visual feedback | Native OSC/SerialOSC patch routes press coordinates to row messages; LED logic and local playbar messages are separate. Lua handler alternatives are not instantiated by `mlr.pd`. | Only rows 1–6 are connected in the native row dispatcher. LED receives do not match the active player's private playbar publisher. Physical operation unvalidated. |

### Data and state already in use

- **Positions:** buffer metadata, slice offsets, trajectory targets, and reader
  indexes use sample frames. “End” is populated with frame count `N`, while
  “first” initially holds zero. There is no consistent checked end-boundary
  convention around interpolation, wrapping, and reverse entry yet.
- **Time and rate:** ramp/fade/slew durations use milliseconds; file Hz is divided
  by 1000 into frames/ms. Free-running duration uses
  `abs(target - current) / (rate_magnitude * frames_per_ms)`.
  The active calculation has no explicit zero/invalid-rate guard. Positive
  rate magnitude plus direction is the existing model; changing that model is
  outside this catalogue.
- **Metadata:** sample packets are
  `ID loaded rate_kHz slice_frames first end`; live packets are
  `ID rate_kHz first end slice_frames content`. These layouts differ.
- **Clock subdivisions:** the DAW branch publishes `floor(PPQ * 16)`; the
  internal branch sends `BPM * 16` to `clock` and counts its events. Key
  quantization uses `2^menu_index` ticks; beat reset uses `menu_value * 64`
  ticks for menu values 1–8. `global-transport` can control the internal clock,
  but no sender for it exists in the active entry graph. Automatic musical
  alignment is therefore not established simply by selecting clock mode.
- **Identity:** `$0` isolates much player-local state; `$1` identifies a track/row
  and its default buffer. Selected buffer type/number can differ from that
  default, but automatic selection mixes these roles. Arrays, row messages,
  output buses, BPM, and PPQ remain globally named. Copying a player with the
  same arguments would not create independent resources.
- **Timing:** transport flags, selected buffer values, the master trajectory,
  each reader's trajectory, gain envelopes, and pending delayed DSP-off events
  are separate state. Refactoring must preserve their ordering while making
  their owners explicit. Moving boxes into subpatches alone will not do that.

### Concrete gaps and inconsistencies

These are grouped by function rather than reduced to a single suspected cause.
They are not a claim that fixing one will resolve every playback fault.

**Buffer selection and storage**

1. `sample-data.pd` has no `_s_b_select_bang` or `_s_b_load_up` receiver to return
   its metadata when a previously loaded buffer is selected. The live equivalent
   `_l_b_select_bang` is present but unconnected. A selection request does not
   establish a fresh, complete buffer description. The player also dispatches
   delete to either buffer type, but only the live buffer has a delete handler.
2. Both metadata buses in `buffer_&_loop` route on selected number without a
   corresponding type filter. Sample receipt also fires `$0-loaded_sample`,
   which selects this player's own `$1` sample number before unpacking the
   packet. Selecting a different buffer and then loading it needs a specific
   check for target/cache disagreement; the post-load refresh does not fix this.
3. Loading directly resizes arrays, publishes a literal loaded flag, and ignores
   channel metadata. There is no active-reader replacement guard. Live deletion
   also resizes/clears storage without coordinating readers. Its reset size is
   a fixed 48000 frames, not a sample-rate-dependent duration.
4. `live_buffer.pd:18` receives hardcoded `1_l_b_first_record_bang` to obtain the
   sample rate. Other buffer IDs do not have their own corresponding trigger.
   The sample loader's `1, 0` channel order differs from the readers' `0, 1`
   target order; this needs a distinct-channel output check.

**Transport, slices, and clock**

5. Stop uses `s 1-mixer_env_close` at player line 1363, whereas Pause uses
   `s $1-mixer_env_close` at line 1191. Stopping another track can therefore
   address channel 1's mixer. Pause itself has both a snapshot/freeze path and
   that correctly parameterized mixer-close path; it is not wholly absent.
6. The transition router declares `pause resume stop`, but those outlets have
   no connections. Stop sends `stop 1` to this unused outlet. Several older
   envelope/DSP message names likewise have no receivers in the active graph.
   These branches need classification rather than being carried into a new
   interface as if they worked.
7. Slice position uses full-buffer `N / 16` without adding a nonzero first-index
   offset or clamping the requested slice. Current slicing therefore needs
   explicit behavior for a changed loop region. The current playbar does not
   implement mouse seeking.
8. Quantizer value `1` selects the immediate branch (player lines 410–414),
   contrary to the apparent “Quantize” checkbox meaning. Its pending-slice `[f]`
   at line 405 receives new keys at the hot inlet: a second key can pass through
   an already-open pending gate before the next tick. This is an ordering defect
   to reproduce with two keys inside one quantization interval.
9. `$0-reset-sync` at line 394 has no receiver in the active player. The main
   `stop-playback` button also has no receiver in the active entry graph.
   `calc_duration` still reads `$1_file_abs_start/end`, published by an alternative
   loader rather than `sample-data.pd`, and contains load-time placeholder values.
   Neither beat-reset nor synchronized duration is established by the visible
   clock controls. Several top-level per-track controls are only wired for track 1.

**Motion, speed, direction, and slew**

10. `loop_logic` (lines 597–648) has only `>=~` end comparisons and restarts from
    loop start. It has no direction-gated `<=~` start comparison or reverse
    restart-at-end path. Changing a ramp's direction alone cannot complete this
    loop implementation.
11. The pre-transition threshold is `loop_end - samples_per_ms * 3`. Rate changes
    update the subtraction's cold inlet without recomputing its output. The
    main update trigger also refreshes bounds before the later duration/rate
    calculation. Transition lookahead can therefore retain an earlier rate.
12. Rate slew is connected, but `$0-slew_engaged` has no receiver. Direction slew
    is more incomplete: `pack f f f f` at line 1338 has no hot-inlet connection;
    trigger outlets 0 and 1 at line 1336 are unused; the engaged branch's `[f]`
    at line 1335 has no output connection. Its snapshot toggle is also wired
    to the interval inlet, unlike the rate-slew path. Reconnecting one wire
    would not resolve this entire gesture.
13. The duration calculation divides by rate with no zero case, while the
    direction-slew sketch targets zero. Stopping at zero, reversing from a
    boundary, changing bounds during motion, and interrupting a slew need
    explicit musical behavior before those paths can be made consistent.

**Readers, transitions, and output**

14. Voice 0 connects its initialization counter to `gate~ 2`; voice 1 connects
    that counter only to a display (lines 965–1151). Voice 1 also lacks voice 0's
    `main_vline_gate` handler. Thus the two alternating readers do not respond
    to the same setup/control sequence. This is a concrete structural difference;
    its contribution to the reported silent pass still needs an audio check.
    **Follow-up:** the repair below reproduces that cause, initializes voice 1's
    direct outlet, and verifies continuous loop turns. The missing trajectory
    handler remains open.
15. Both readers contain `expr~ 1 - $v1`, a normalized-phase reversal operation,
    after a `vline~` carrying frame indexes. On that branch, frame 1000 becomes
    -999. The direct and transformed branches also both feed the table index
    inlet. This is an internal units mismatch, not evidence of correctly
    implemented reverse playback.
16. Loop/play fades use 6 ms and slice fades 9 ms. The original reader DSP-off
    objects display `delay 6`, but the routed `dsp_off 0` payload overrides that
    duration and schedules immediate shutdown. DSP-on does not cancel pending
    DSP-off. Voice 0's emitted
    fade-bang has no matching handler; voice 1's special fade branch includes
    unconnected continuation messages. Rapid commands can encounter stale
    delayed actions, and a fade can be cut short. **Follow-up:** the repair below
    converts that payload to a bang, waits 9 ms, and cancels pending local
    shutdowns on reactivation. The other unfinished fade branches remain open.
17. Mixer open ramps over 5 ms; mixer close is `0 0`, immediate. Together with
    reader envelopes and the master/reader trajectory split, this needs an
    end-to-end transition check. The source alone does not establish click,
    dropout, or gain performance.

**Recording, input, and external feedback**

18. Active Record Arm sends `$0-record_button_bang` (line 14) with no receiver.
    The armed Play outlet is unconnected and there are no `poke~`/`tabwrite~`
    writers in the active player. Recording flags and live arrays do not make
    a complete recording path. The alternative writer is described below.
19. Main Audio 1 input sends `1-live-buffer-in`, which has no active consumer.
    Other input gain/meter sketches do not complete a writer route. The separate
    `audio-in-subpatch.pd` input/monitor/`pdlink` patch is not instantiated by
    `mlr.pd`; its existence is not evidence that main's input controls record.
20. Local playbar updates use `$0-playbar_data_i`; the main Grid view listens to
    `1-playbar_data_i` and `2-playhead`. These names do not match the active
    publisher. Native press dispatch connects rows 1–6, with row 7/8 sends left
    unwired and no connected row 9–16 dispatcher. Test LED messages and Lua
    alternatives do not complete that route.

### Useful behavior in the other versions

These references were read for specific behavior, not ranked by filename.
None was loaded as a replacement, edited, or accepted through runtime testing.

| Source | What is worth understanding or recovering |
| --- | --- |
| `sampler_playback.pd` | Has a Record Arm receiver and timed/endless recording decisions, PPQ-aligned record start, first-record metadata, growable storage handling, input gain/gates, and stereo `poke~` writing in `poke_write_processing`. Timed length controls use measures; an existing comment assumes 4/4. “Overdub” controls are present, but input/write gating is not proof of a correct old-audio feedback mix. Full recording behavior remains unvalidated. Also contains the post-load refresh pattern used by the small repair. |
| `sample_playback_new.pd` and `old-sample_playback_new.pd` | Byte-identical pair. Contains direction-gated forward/reverse boundary comparisons, loop-point messages, and a `play_pause_stop` subpatch. Its very long duration fallback at rate zero is an older choice to inspect, not an adopted pause policy. |
| `sample-playback.pd` and `old-sample-playback.pd` | Byte-identical pair. Earlier stereo playback, slice/random-slice, loop, beat-reset, quantization, and rate-change paths. The explicit “Slice (plays till end of sample)” comment helps explain the musical meaning of slicing. |
| `sampler_playback_third.pd` | Earlier rate/curve/snapshot and bidirectional loop work. A reference for those sections; the entire alternative is not independently qualified. |
| `voice.pd` | Self-contained stereo loading, 16-way and random slice controls, and playback/position experiments. Useful for the simpler original slice path, not the active main abstraction. |
| `sample-data-new.pd`, `old-sample-data.pd` | Different table/metadata naming schemes. The former publishes `$1_file_abs_start/end`, explaining surviving consumers in the current duration calculation. Do not mix naming schemes without tracing their clients. |
| `previous_live-buffer.pd` | Separate stereo `poke~` buffer-writer and recording/index metadata. Parent delivery of writer controls needs recovery; not a complete active recorder. |
| `live-buffer.pd`, `audio-in-subpatch.pd` | Input selection/metering and separate ADC/monitor/`pdlink` routing. `live-buffer.pd` is different from the active `live_buffer.pd` storage component. |
| `rate-change.pd` | Small snapshot/rate/length sketch with no outlet; not a ready-made reusable speed component. |
| `monome_grid_handler.pd_lua`, `monome_grid_handler_fixed.pd_lua` | Press filtering, transport/row dispatch, configurable prefix. Both register the same class name; neither is instantiated in the active main path. |
| Installed `mlr-lite` copy | Its player has bidirectional loop comparisons and simpler direct-index readers with more symmetric gate handling. Writer objects also exist there, but the Record Arm connection is still not established. These are narrow read-only references, not a reason to copy the installed application wholesale. |

### Refactoring boundaries to review

The useful existing design is a buffer-backed musical player with slice/clock
input, continuous motion, and two readers for transitions. Preserve that story.
First make the existing subpatches and their state understandable; extract a
reusable abstraction only when its inputs, outputs, and ordering are clear.

| Part | State it should own | Boundary grounded in the existing code |
| --- | --- | --- |
| Buffer storage and description | Arrays, channel order, frame count, file rate, content status; permission to resize/clear. | Build on `sample-data` and `live_buffer`. Selection requests one complete description. Playback rate, transport, and fades do not belong here. |
| Musical input and timing | Row/column mapping, pending quantized key, interval and clock selection. | Convert controls into slice/jump/transport requests. Keep Grid and beat mapping outside the reader DSP. |
| Player motion and gestures | Playing/paused state, current frame, loop region, direction, requested/current speed, active slew. | Group existing transport, duration, loop, and slew logic around one ordered trajectory update. Keep rate and direction slew visible subpatches here initially; do not create competing owners of transport flags. |
| Stereo readers and transition scheduling | Outgoing/incoming reader state, each trajectory, gains, delayed shutdown. | Keep the two-reader design. Make the two command handlers consistent, and coordinate/cancel delayed actions. The readers are not additional musical players. |
| Recording writer | Write enable/index, first-record length/content, input/overdub behavior. | Recover the existing alternative in a separate later change. Coordinate storage ownership with the buffer; do not hide resize decisions in unrelated playback controls. |
| Output and feedback | Track/master gain and published display/controller position. | Reuse `mixer.pd`; reconcile track 1's duplicate implementation when appropriate. Report which position is displayed instead of treating the master playbar as proof of an audible reader position. |

Unconnected branches should be marked as unfinished or superseded after checking
their callers, then repaired or removed in a focused change. They should not
become new public controls merely because they have names. Historical patches
remain preserved as references during that work.

The next implementation candidate should be chosen from this map with a concrete
musical case. Reader setup/command symmetry and coordinated boundary handoff are
strong candidates for the reported intermittent playback. Direction-aware wrap
must be assessed with the same reader path. This review does not select an
unobserved cause or authorize a wholesale replacement.

For each subsequent repair, reproduce the relevant control sequence in the actual
application with the console visible, inspect the corresponding values, and
listen/render where the claim concerns audio. Keep those results separate from
the source trace. There are no new audio renders, numerical audio results, or
claims of working recording, reverse, glitch-free transitions, or Grid operation
in this documentation update. No additional-player expansion is part of it.

## Reader initialization and shutdown repair

Base: `763552816a269d008afcb39b913d970e31980415`; branch
`codex/fix-reader-handoff`. The user authorized the small reader-handoff repair
after reviewing the whole-functionality map.

The already-open session did not reproduce full silent passes: its 63.339 s
native output capture had audio across the loop turns. A fresh opening of the
same application, with `DrumLoop.wav` loaded before Play, did reproduce them.
In the fresh capture, 0.1 s RMS bins below 1e-6 cover approximately 15.2–30.0 s,
43.9–58.7 s, and 72.5–86.0 s. Player 1's console continued reporting loop bounds
and alternating reader DSP commands. Only one application instance was open.

During that same fresh recording, sending `1` to voice 1's existing `gate~ 2`
through the native console restored audio on its turns. No patch connection
was changed for this intervention. The missing initialization connection leaves
that gate closed on first use; prior control history can mask the failure.
This intervention establishes the full silent-pass cause, not every short gap
or transition fault. `DrumLoop.wav` itself contains silence near its end.

Repair contract: retain frame-index playback, the two existing stereo readers,
and the existing 6 ms loop/play and 9 ms slice gain ramps. Initialize both signal
gates to their direct-reader outlet. A reader's `dsp_on 1` cancels pending local
DSP-off delays. Convert the `dsp_off 0` payload to a bang before `delay`: a float
at that inlet overrides the delay time, so the existing message scheduled an
immediate shutdown despite the displayed 6 ms argument. Normal delayed shutdown
now waits 9 ms, covering the longest existing fade. No rate, loop-region,
direction, or recording interface changes are included. This does not complete
the unfinished independent reader trajectory gating or promise click-free jumps.

Native settings were freshly inspected: plugdata, CoreAudio, 48000 Hz, 512 frames,
8A outputs USB 1/2, Opal C1 input; DSP on, app gain 0.8, limiter off, oversampling
1x. Output recording uses plugdata's built-in recorder, exported at 48000 Hz,
24-bit stereo WAV, Normalize No. The source file is stereo 44100 Hz; this run
therefore exercises a file/host rate mismatch. No separate audio patch was loaded.
The native About view reports 0.9.4; the installed executable contains build
`98ae0f78b` and `Pd-0.56.3`, matching the earlier session identity. The native
error-only console view was empty after the repaired test. Message display was
restored afterward. No console history was deliberately cleared. Earlier console
navigation mistakes in the pre-repair investigation were operator errors, not
evidence of a DSP cause.

### Native audio results

These are recordings of this application's output through plugdata's built-in
recorder, not a separate playback model. Fresh before/after runs used track 1
gain 0.4 and the saved master gain 0.75. The initial already-open run used its
prior mixer state and is not a matched level comparison.

| Check | Observed result |
| --- | --- |
| Fresh original reader state | Alternating roughly 14.8 s silent intervals, including the file's own tail. Sending `1` to voice 1's signal gate during the same recording restores its turns. |
| Fresh repaired reader state | 256.299 s capture. After the 1.4 s recording lead-in, no quiet interval of 0.4 s or longer exceeds 0.5 s. Remaining quiet intervals match the source tail. No full silent pass or stuck playback after the burst. |
| Overlapping slice requests | Control-only panel sends `0, 8, 4, 12, 1, 9, 2, 10, 0`, 2 ms apart. All nine appear in the actual console. Sent about 53.1 s after Play (about 55 s into the recording); subsequent loop turns remain audible in the captured output. |
| Level through the readers | The first three repaired passes have the same settled 10 s RMS: output channels 1/2 = 0.06389196 / 0.06878518. The working first pre-repair pass has the same values. The fourth comparison window overlaps the burst and is excluded. |
| Peak and sample steps | Matched fresh before/after captures have identical channel peaks, 0.29312229 / 0.29277468, and identical largest adjacent-sample steps, 0.27922642 / 0.27937114. Neither reaches full scale. These bounds do not establish that every transition is inaudible. |
| Stop | Existing player Stop returned the visible playbar to the beginning. It was pressed after recording; this is a UI observation, not an audio stop-envelope measurement. |
| Channel order | Both output channels contain signal, but their relative RMS/DC signs match the source in the opposite order. This agrees with the previously catalogued loader `1,0` versus reader `0,1` mapping; the inline mixer preserves that order. Correct left/right ordering is not accepted or repaired here. |

The before-burst capture was made after manually opening the old reader's gate.
It also continued playing afterward. Thus this burst is a regression check of
the repaired scheduling, not evidence that the old delay produced a stuck reader
in that sequence. The float-to-delay bug is established by the actual message
trace and Pd's local `delay-help.pd` semantics: a float sets the duration and
starts the timer; a bang uses the current duration.

**Listening:** the user's report during repaired ordinary looping, before the
burst, was **“it is solid playback.”** No separate listening verdict was obtained
for the burst, and no assistant listening claim is made. Quiet-bin and sample-step
measurements are kept separate from this report.

**Limits:** this repair does not complete independent outgoing/incoming reader
trajectories, direction-aware wrapping, direction slew, or the stop handler.
Clicks or short gain disturbances during arbitrary jumps remain an acceptance
gap. The drum signal has natural transients and end silence; its maximum sample
step is not a click detector. PCM export cannot prove internal DSP never became
non-finite. Only the existing forward, unit-rate Sample 1 path and the stated
burst were exercised. No 44.1 kHz host run, reverse/rate campaign, other-track or
multi-instance acceptance, recording/overdub, physical Grid, or DAW lifecycle
test is claimed. The broad rejected R1 acceptance remains superseded by the
user's original-application recovery scope.

### Retained evidence

Files are in [evidence/reader-handoff](evidence/reader-handoff). Representative
audio is lossless FLAC, cropped from the native 48 kHz / 24-bit WAV exports with
ffmpeg 9.0.1. Each decoded clip was compared byte-for-byte with its source PCM
slice. No normalization or resampling was applied to those clips.

| Retained clip | Native capture interval | Purpose |
| --- | --- | --- |
| [fresh-before.flac](evidence/reader-handoff/fresh-before.flac) | Fresh before, 0–45 s | Audible reader, full silent reader pass, audible return. |
| [manual-gate-recovery.flac](evidence/reader-handoff/manual-gate-recovery.flac) | Same before recording, 80–116 s | Console gate intervention at about 86 s restores audio. |
| [before-burst.flac](evidence/reader-handoff/before-burst.flac) | Old reader, gate already open, 0–10 s | Pre-repair burst comparison. |
| [repaired-first-loops.flac](evidence/reader-handoff/repaired-first-loops.flac) | Repaired, 0–45 s | Three successive audible reader turns after fresh initialization. |
| [repaired-burst-and-loops.flac](evidence/reader-handoff/repaired-burst-and-loops.flac) | Repaired, 52–88 s | Burst followed by two loop boundaries. |

[results.json](evidence/reader-handoff/results.json) retains numerical summaries
and full-capture hashes; [clips.json](evidence/reader-handoff/clips.json) records
clip hashes and crop provenance. Large original WAV exports remain locally in
this folder, ignored by Git. Screenshots retain native settings, original/repaired
reader views, control prints, export settings, the final error view, and About.
Static validation found valid object indexes for all 912 player connections and
36 control-panel connections. The analysis script ran on the source and all four
native captures; Python syntax, JSON parsing, and `git diff --check` also passed.

### Repeat the handoff check

1. Use only one `mlr.pd` instance. Close and reopen it from this checkout so reader
   initialization is tested; opening an already-used reader can hide the bug.
2. Keep the native console's messages and errors visible. Load the included
   `DrumLoop.wav` with Sample 1 Load, then open `arrays-samples` →
   `sample_player_rebuild 1`. Confirm `sample_buffer`, `1` is selected.
3. Set the existing Audio 1 Out control to 0.4 and mixer Master to 0.75. Check
   your output level first. Record actual audio settings; this run used 48 kHz /
   512 frames. Start plugdata's output recorder, then the player's Play/Pause.
4. Observe at least three 14.329 s loop turns. The source's final ~0.5 s is quiet;
   an entire silent pass is a failure. Watch reader DSP/position console messages.
5. Open `tests/handoff-commands.pd`, which contains no audio objects or buffers.
   Select immediate input (main Quantize Track 1 value **1** in this version).
   Press Slice_burst once; verify all nine prints. Continue for two more loops.
6. Stop the native recorder and export WAV, 48000 Hz, 24-bit, Normalize No. Stop
   the player; inspect the console error view and restore message display.
7. Run `python3 tests/analyze_handoff.py DrumLoop.wav /path/to/capture.wav` with
   Python and NumPy. For retained clips, decode first with
   `ffmpeg -i clip.flac -c:a pcm_s24le /tmp/clip.wav`, then use the same script.
   A quiet interval is a measurement to compare with source/control timing,
   not automatically a dropout. Obtain a separate listening observation.

Next work should remain a single agreed musical behavior from the catalogue.
Completing reader trajectory ownership and direction-aware boundaries is still
necessary; it was not started as part of this repair.

## Reverse playback and loop boundaries

Authorized after merging PRs #2–#5. Base:
`fc17d598a60d4531b3beac78d1a49eccc5ad660d`; branch `codex/fix-reverse-loop`.

Before editing DSP, the existing native player was recorded with `DrumLoop.wav`.
Direction Change was pressed about 5.47 s after Play. The playbar travelled back
to the start and remained there; the console issued no reverse wrap. The 24.181 s
native capture is quiet from about 12.4 s through its end. This was the previously
used instance, not a fresh initialization: its peak is about twice the earlier
fresh-run level, consistent with the separately open stop/restart reader-gain
gap. It establishes the missing wrap, not a matched fresh-run gain baseline.

Repair contract, before implementation:

- Keep the current magnitude presets (0.25, 0.5, 1, 2, 4) and separate direction
  button. Direction state is 0 forward / 1 reverse; the existing endpoint
  selector uses 1 forward / 2 reverse. No new signed-rate interface is introduced.
- Keep frame positions and the loader's existing start/end bounds. Valid test
  regions satisfy `0 <= start < end <= frame_count`. The end remains the existing
  trajectory boundary; changing interpolation guards or channel ordering is
  separate work. File Hz / 1000 × magnitude gives frames per millisecond.
- With direction slew off, a direction change takes the current position and
  heads toward the opposite boundary. Reverse wrap goes from start to end;
  forward wrap goes from end to start. Play from stopped uses the selected
  direction's entry boundary. Stop keeps its existing reset-to-forward behavior.
  The direction button toggles the published state, replacing the separate
  counter; startup explicitly initializes that state to forward.
- Recover direction-gated comparisons from the earlier player versions inside
  the existing `loop_logic`. Keep its gain handoff and 3 ms preparation window,
  mirrored in reverse and refreshed with speed; cap that window to half a region.
  Disable boundary triggers while stopped/paused or with a non-positive region
  or speed. Sub-block loops and invalid direct internal messages are unqualified;
  rate-zero transport and missing-buffer validation remain separate gaps.
- Direction is implemented by the existing ascending/descending frame ramp.
  Disconnect the direction button's arming of the unfinished normalized-phase
  reader branch. Preserve the working ordinary two-reader loop/slice gain path.
  Do not claim this completes independent reader trajectories, arbitrary
  click-free transitions, or the disconnected direction-slew gesture.

The repair reuses the frame ramp, endpoint switches, `edge~` event path, both
readers, and the existing gain fades. The earlier `sample_playback_new.pd` and
`sampler_playback_third.pd` contain direction-gated comparisons useful to this
repair. Only `sample_player_rebuild.pd` changes application behavior; `mlr.pd`,
loader/buffer/mixer patches, historical alternatives, and dependencies are unchanged.

The first changed captures were not accepted as the final direction/rate test:
offline source matching found reversed startup and a rate command that retained
the previous rate. Additional repairs therefore make direction initialization
explicit and store the rate target before starting `curve~` (its zero-duration
completion can otherwise read the old target). Stop now sends DSP-off to both
existing readers, preventing a still-enabled reader from doubling the next
start's gain. A subsequent native capture exposed a brief first-wrap gain spike
because a disabled reader retained its old envelope. Stop now also resets both
reader envelopes to zero. The exact restart case was repeated after reloading.
These are local state-ordering repairs; the broader stop envelope,
direction-slew gesture, and independent reader trajectories remain separate.


### Native results and limits

Actual application: `/Applications/plugdata.app`, About **0.9.4**, executable
build **`98ae0f78b`**, embedded Pd **0.56.3**. Audio Settings were read directly:
CoreAudio, **48000 Hz / 512 frames**, 8A USB outputs 1/2. Source: included stereo
24-bit `DrumLoop.wav`, **44100 Hz**, 631881 frames. Audio 1 Out was 0.4, mixer
Master 0.75, app output gain 0.8, limiter off. Native recordings were exported
as stereo 24-bit WAV at 48000 Hz with Normalize No. The final error-only console
was empty; messages were restored and playback left stopped. No settings or
installed services were changed. No other audio-producing test patch was opened.

Observed UI/console behavior:

- Fresh Play travels forward. Direction Change commits direction 1 / selector 2
  and sends a descending frame ramp. At the start boundary it returns to the end
  and continues; the old recording instead remained silent after reaching start.
- A region of frames 44100–132300 (source seconds 1–3) wraps in both directions.
  Endpoint readback agrees with the selected direction. Near-start and near-end
  seeks continue rather than leaving playback stuck.
- Stop → Direction Change → Play starts reverse from the file end. Pause →
  Direction Change → Resume continues in the new direction. Stop/Play currently
  refreshes bounds from the selected buffer, so an ad hoc region is not preserved
  by that restart path; this repair does not add region recall.
- Three direction messages in the same Pd event leave playback running in the
  expected final direction. This is one bounded overlapping-command check, not
  acceptance of every pending event or arbitrary rapid transport sequence.

Numerical checks of actual application output:

- The final 100.789 s recording has peaks **0.294218 / 0.292787**, zero full-scale
  samples, and no ≥0.4 s quiet region except initial lead-in, the source tail,
  and the deliberate Stop/restart. Quiet bins use RMS <1e-6 in 0.1 s windows;
  they cannot exclude shorter dropouts.
- Source matching verifies +1 fresh playback, +2 faster playback, -2 after reverse
  restart, and +0.5 / -0.5 in the short region. The preceding direction check
  also verifies -1. Representative aligned windows correlate above 0.998 in both
  channels with fitted gain near 0.3. All sampled results, including lower scores
  at wraps/transients, are retained. The drum repeats phrases; global match
  positions alone are not region-confinement evidence. Region-constrained matches
  and native endpoint messages provide the additional checks.
- The pre-envelope-reset restart capture peaked at **0.504924 / 0.503979** on its
  first reverse wrap. The repeated final restart stayed within the final peaks
  above. This supports the specific envelope reset, not a universal gain guarantee.
- Comparing one recorded cycle with the next gives **1.000000 s forward / 1.001333 s
  reverse at 2x**, and **4.000000 s forward / 4.001333 s reverse at 0.5x**, for the
  1–3 s region. Correlations are effectively 1. The extra reverse block is a real
  timing limitation of the current boundary/ramp path, not sample-accurate looping.
- Largest adjacent-sample steps are **0.390704 / 0.390945**. For scale, a linearly
  interpolated source reference at 2x and gain 0.3 reaches about **0.386355 /
  0.386144**. The drum itself has sharp transients. These measurements neither
  establish audible clicks nor prove their absence. The shared ramp and existing
  fades still need a focused transition/listening review.

The console exposed **two successive trajectory durations around some speed
changes**, including a stale duration after the new one. Storing the target before
starting `curve~` fixes the observed final-target ordering defect, but does not
resolve the entire speed/slew sequence. Steady rates above are verified; immediate
rate transitions and nonzero glide are **not accepted**. Trace the remaining
`curve~`/snapshot/trajectory call order before changing that mechanism. Direction
slew, beat resets, recording/overdub, invalid/missing-buffer handling, channel-order
repair, and independent reader trajectories remain outside this change.

**Listening:** no new final-version human listening report is available. The prior
“solid playback” report belongs to reader-handoff PR #5. An earlier listening
question during this investigation preceded direction-state corrections and is
not final-version acceptance. No assistant listening claim is made.

This slice tests **48 kHz host with a 44.1 kHz file**. A 44.1 kHz host, Bitwig,
multiple instrument instances, and the rejected R1 shared-head interface were not
tested here. Integer PCM export also cannot establish internal DSP finiteness.

### Retained evidence

[Results](evidence/reverse-loop/results.json) contain full-capture hashes, final
player-file hash, numerical checks and limitations. [Clip provenance](evidence/reverse-loop/clips.json)
records exact sample crops; every FLAC was decoded and byte-compared against its
native PCM crop, with no normalization. Full WAVs and rejected intermediate
screens/events remain local and ignored. Early intent-only event labels are not
used as observed state. The transport check's exact event log was not retained;
its Stop/Pause intervals are identified from native screenshots and recorded silence.
The [final event log](evidence/reverse-loop/final-events.json) is relative to the
record-start helper returning, about one second after the native recorder begins.

| Clip | Native capture interval | Evidence |
| --- | --- | --- |
| [Before missing wrap](evidence/reverse-loop/before-missing-wrap.flac) | Original direction test, 8–24 s | Reverse reaches start, then sustained silence; previously used instance has higher gain. |
| [Before restart gain spike](evidence/reverse-loop/before-restart-gain-spike.flac) | Pre-envelope-reset transport, 22.5–25 s | First reverse wrap after restart. |
| [Repaired forward](evidence/reverse-loop/repaired-forward.flac) | Final, 1–20 s | Fresh forward playback and first full wrap. |
| [Repaired reverse restart](evidence/reverse-loop/repaired-reverse-restart.flac) | Final, 32–50 s | Reverse startup and two full reverse wraps at 2x. |
| [Repeated directions](evidence/reverse-loop/repaired-direction-burst.flac) | Final, 54–69 s | Short reverse region, three same-event direction changes, forward continuation. |
| [Slower directions](evidence/reverse-loop/repaired-slow-directions.flac) | Final, 77–100 s | 0.5x forward, direction change, 0.5x reverse. |

Screenshots retain native About, audio settings, loop-logic objects/connections,
direction/entry console messages, repeated-command output and the final error view.

### Repeat the direction check

1. Open a fresh single `mlr.pd` from this checkout. Show console messages and
   errors. Load `DrumLoop.wav` with Sample 1 Load; open arrays-samples →
   `sample_player_rebuild 1`. Use the existing mixer controls as in the README.
2. Leave rate slew duration at zero. Start plugdata's native output recorder,
   then Play. Observe a full forward loop, press Direction Change and observe
   reverse crossing the start and returning from the end.
3. Set the fourth speed cell (2x). Stop, press Direction Change while stopped,
   then Play. Observe two full reverse wraps, checking first-wrap gain as well.
4. Open `tests/reverse-controls.pd`. Enter the current player number shown in
   console messages such as `3401-loop_start`; it changes when the app reloads.
   This panel has no audio objects or buffers and uses existing internal receivers;
   it is a diagnostic, not a new public engine API.
5. Press Region_1_to_3s; watch the printed frame bounds and several wraps.
   Test Toggle_direction, Near_region_start/end, and Three_direction_toggles.
   Test Half_speed/Normal_speed/Double_speed, checking actual audio and messages.
   Test Pause → Direction Change → Resume separately. Record the command times.
6. Stop the native recorder, export 48000 Hz / 24-bit / Normalize No, then Stop
   playback. Inspect errors without clearing the console. Record listening
   observations separately; mark clicks, short gaps and gain anomalies explicitly.
7. With Python and NumPy, run `python3 tests/analyze_handoff.py capture.wav`.
   For a known steady short-region interval, run
   `python3 tests/analyze_reverse.py DrumLoop.wav capture.wav 54 --window .2 --region 1 3 --period 1`,
   replacing time and expected period with the recorded segment. Omit `--region`
   for full-file matching. Decode retained FLACs to PCM WAV first if needed.
   Clip timestamps are relative to their crop, unlike full-capture results.

Validation: final patch and panel connection indexes checked, native load and
console inspected, PCM analysis executed, FLAC crop identity checked, Python
syntax/JSON parsing and `git diff --check` passed. Listening/transition acceptance,
reverse timing accuracy and immediate speed/slew transitions remain open. Do not
start another repair automatically; these findings support the next scoped review.

## Free-form tape direction

The subsequent user discussion sets the near-term musical direction: reverse
immediately at the current position, or use the existing tape-slew idea and allow
the resulting timing drift. There is no automatic catch-up to an imagined
unaffected playhead. Clock locking, continuous/pitched speed controls and more
elaborate Arc manipulation can be considered after the current motion works.

The intended instant gesture flips direction without deliberately waiting,
seeking to another position or restarting the loop. The intended slew gesture
decelerates, passes through zero and accelerates in the other direction, keeping
the position reached by that motion. Neither gesture promises universal
click-free output. In particular, the measured extra reverse-loop block above
is an implementation defect to address, not intentional tape drift.

This is a behavior decision and source review, **not a new DSP implementation**.
PR #6 still has the speed/trajectory ordering and nonzero-slew gaps recorded
above. The existing controls and two readers are the starting point; the
unconnected direction-slew branches do not constitute a working feature.

### Tape reference catalogue

These are ideas to revisit, not a commitment to clone every device or its sound.
Sources were read on 2026-09-09; no reference hardware was auditioned here.

| Reference | Useful musical ideas | Relationship to plugmlr |
| --- | --- | --- |
| OP-1 field: tape transport | Reverse, brake/stop, fine speed and scrubbing. | Immediate direction and slew are the current focus; brake/scrub can follow. |
| OP-1 field: tape tricks and editing | Tempo-based chop, loop in/out, parameter memories, lift/drop, split/join and undo. | Future loop gestures and editing references. |
| OP-1 field: tape styles | Studio, vintage, portable-tape and disc characters. | Later coloration; no modeled tape sound is implemented here. |
| OP-XY: Tape auxiliary track | Play captured clips, change pitch/speed/loop length, blend with the original, choose source tracks; filter and modulate. | Later live capture and performance routing. |
| OP-XY: punch-in FX | Perform and record momentary effects for individual tracks or groups. | Later gesture mapping, independent of buffer motion. |
| mlre: tape performance | Reverse, octave speeds, scale transpose, rate slew and probabilistic warble. | Preserve free tape motion first; add pitch choices and modulation later. |
| mlre: interaction | Cuts/loops, pattern recording, snapshots, punch-ins and temporary parameter morphs. Arc adds scrub/warble and loop-window controls. | References for musical controls over an understood player. |
| mlre: tape management | Splices, main/temp sides, backup/undo and overdub fade-out. | Later recording and audio-management work. |
| Maschine: Stutter | Adjustable loop length, pitch and gate; forward/reverse; optional time quantization. | Useful free-versus-quantized performance reference for later. |
| Maschine: Scratcher | Brake, scratch, and a feedback delay with frequency shifting; release bypasses the effect. | Later gesture/effect idea. |
| Maschine: Saturator, Tape mode | Compression/coloration with frequency shaping. | Later audio effect, separate from tape transport. |

Primary references: [OP-1 field firmware 1.7.0, REV10 guide, Tape](https://assets.teenage.engineering/_img/69f248938d433104c4dd1846_original.pdf),
[OP-XY auxiliary guide, sections 15.2 and 15.6](https://teenage.engineering/guides/op-xy/auxiliary),
[mlre v2.2 manual](https://github.com/sonocircuit/mlre/blob/ba88531bd31656ec33b54beee4f67c5438ae7d35/doc/mlre%20v2.2%20-%20user%20manual.pdf),
and [Maschine software effect reference](https://docs.native-instruments.com/ni-tech-manuals/maschine-software-manual/en/effect-reference).
The OP-XY and Maschine references are the online manuals as read, not tests of
a pinned device/software build. mlre's manual describes periodic track reset
as an optional way to realign motion after rate changes; it is not required
for free tape play. It also warns that rapid repeated punch-ins may fail to
restore prior state. Reference behavior is subject to review too.

### From the current player toward mlre

The source reference is [sonocircuit/mlre](https://github.com/sonocircuit/mlre/tree/ba88531bd31656ec33b54beee4f67c5438ae7d35),
commit `ba88531bd31656ec33b54beee4f67c5438ae7d35`, whose code identifies itself
as v2.2.0 and requires norns version `231114`. It extends Brian Crabtree's mlr
and uses Ezra Buchla's softcut. It is a behavioral reference, not code that
currently runs inside plugdata.

Its [main source](https://github.com/sonocircuit/mlre/blob/ba88531bd31656ec33b54beee4f67c5438ae7d35/mlre.lua)
imports `musicutil` and `lattice`, plus its own UI, Grid, compatibility, LFO,
scales and pattern-time modules. It also uses norns clock/metro, params and
presets, file/audio operations, waveform/position callbacks, screen, MIDI, Grid
and Arc APIs. The broader phrase **basic norns tools remains undefined** pending
the user's clarification; this inventory does not authorize a whole norns
runtime or compatibility layer.

There is a channel-model decision before a literal port: mlre configures six
softcut voices and uses mono buffer read/write/copy operations and voice pan.
Its tape-side selection maps to softcut buffers. plugmlr currently reads paired
stereo arrays. Keep that stereo behavior while repairing its known ordering
defect; do not silently convert it to mono to match the reference. Buffer,
musical track and internal crossfade reader are distinct concepts.

| Chunk | Existing plugmlr path and remaining work |
| --- | --- |
| Playback motion | Follow `sample_player_rebuild.pd` rate/curve → position snapshot → trajectory → loop boundary → readers. Resolve stale updates, zero-rate behavior and direction slew; test both readers through interrupted gestures. |
| Cuts, regions and feedback | Keep the existing slice/loop UI and playbar. Repair slice offset/clamping, trace boundary changes and reconcile visual/Grid feedback with actual playback. Quantized launch/reset is a separate choice. |
| Recording and tape management | Trace `live_buffer.pd` and the historical writers already mapped here. The active record button has no completed writer path. File replacement, overdub, safe ownership, undo and splice operations need their own bounded jobs. |
| Controller connection | Adapt musical input/output to the new device package below. Existing global names and legacy Grid routing need review before multi-instance use. |
| Musical helpers | Add only the chosen parameter, pattern/macro, scale and modulation behaviors after their playback operations work. Choose which norns tools to share before implementing them. |
| Community delivery | Provide a runnable example using the actual package, explicit dependencies and credits. Source review and device-workbench acceptance do not establish an integrated instrument release. |

The next concrete repair candidate is the existing **speed and direction slew
path**, including how its two readers handle an interrupted trajectory. First
observe the current control and console, then trace all triggers for one speed
change and one slewed reversal. Define zero-rate and interruption behavior before
editing. Compare instant/slewed gestures and both loop boundaries in native audio,
with listening and numerical evidence kept separate. This note does not start
recording, controller migration or the rest of the catalogue automatically.

## Monome suite and leased SerialOSC

The user confirmed `kasselvania/PlugData-Monome-Devices` as the companion device
package and explicitly included the lease/release SerialOSC work in the suite.
The intended dependency path is:

```text
plugmlr musical controls and playback
  ↕ normalized device events, LED output and connection state
PlugData-Monome-Devices (selection and session ownership)
  ↕ OSC with opt-in leased destinations
kasselvania/serialosc (device worker and lease expiry)
  ↕ USB
Grid / Arc
```

Source pins were resolved from the remotes during this review. They identify
development candidates, not an installer bundle or the currently running service.

| Project | Relevant branch and exact reviewed revision | Responsibility |
| --- | --- | --- |
| plugmlr | Playback PR #6: `codex/fix-reverse-loop`, `a6aea1e83c4800632782b05132b8bedff7df6ef0`; main `fc17d598a60d4531b3beac78d1a49eccc5ad660d` | Instrument, buffer/player behavior and musical mapping. This documentation branch adds no DSP changes. |
| [PlugData-Monome-Devices](https://github.com/kasselvania/PlugData-Monome-Devices/tree/09c820e751525903ec61da00c5be1cb0ccd63a2b) | `feature/serialosc-leases`, `09c820e751525903ec61da00c5be1cb0ccd63a2b` | Discovery, explicit selection, session claim/renew/release, normalized Grid/Arc APIs; macOS candidate packaging. |
| [SerialOSC fork](https://github.com/kasselvania/serialosc/tree/7187832c349202b1a94a9b10080ae57d40069946) | `feature/leased-destinations`, `7187832c349202b1a94a9b10080ae57d40069946` | Version 1 lease protocol and worker-side expiry/darkening. macOS candidate reports `serialoscd 1.4.8 (7187832)`; this is not an upstream release. |
| [SerialOSC Steam Deck packaging](https://github.com/kasselvania/serialOSC-steam-deck/tree/ec2ff3b5dca5330b83946310a19bb90a0b66498f) | `codex/lease-candidate-packaging`, `ec2ff3b5dca5330b83946310a19bb90a0b66498f` | Rootless SteamOS build/install/rollback of the same pinned fork. The documented public rollback release remains upstream 1.4.7. |

The device package's main at `d90445162975519a7096120d58bc8964fa27d1b6`
is the older pre-lease path. SerialOSC main is
`c96ea389dbf82c84d17f6f7adddaf311aed49438`; Deck packaging main is
`bfad5fb7d5e84fba66333a7ee1b7d3df1993abb1`. A generic instruction to clone
all three default branches would miss the intended lease stack.

The package implements `monome-discovery`, `monome-registry`, `monome-session`,
`monome-grid` and `monome-arc`. Its live slots explicitly opt into lease mode;
the session abstraction defaults to legacy policy. In lease mode, unsupported
capability is not a claim and does not silently fall back. The client renews
every 2 seconds under a 6-second TTL, verifies ownership, and exposes legacy
takeover separately. SerialOSC handles expiry even if the client can no longer
send release. This addresses abandoned callbacks and lit hardware after host
death; it does not repair playback DSP or guarantee that the plugin host cannot
crash. See the pinned [lease workbench](https://github.com/kasselvania/PlugData-Monome-Devices/blob/09c820e751525903ec61da00c5be1cb0ccd63a2b/docs/LEASE-WORKBENCH.md)
and [fork protocol](https://github.com/kasselvania/serialosc/blob/7187832c349202b1a94a9b10080ae57d40069946/docs/leased-destinations.md).

**Reported companion-project evidence, not tests executed in this review:**
the device project's [macOS record](https://github.com/kasselvania/PlugData-Monome-Devices/blob/09c820e751525903ec61da00c5be1cb0ccd63a2b/docs/MACOS-LEASE-CANDIDATE.md)
includes two Grids and a four-ring Arc, simultaneous standalone lifecycle and
automatic dark/free recovery after Bitwig plugin-host termination. Its
[SteamOS record](https://github.com/kasselvania/PlugData-Monome-Devices/blob/09c820e751525903ec61da00c5be1cb0ccd63a2b/docs/STEAMOS-LEASE-CANDIDATE.md)
includes bounded standalone single/pair/all-three device tests, with an
intermittent dock reset documented. The [Deck Bitwig record](https://github.com/kasselvania/PlugData-Monome-Devices/blob/09c820e751525903ec61da00c5be1cb0ccd63a2b/docs/PLUGDATA-BITWIG-AB.md)
retains graphical selection and broader lifecycle gaps; terminal selection
does not establish usable graphical integration. These results apply to their
pinned builds, not all plugdata versions or this instrument.

**Integration gap:** `mlr.pd` still uses its legacy `monome-object.pd` path.
The new package has not been wired into it. When that job is chosen, use the
package's device events/LED/state interface and surface selection and release
through its session controls. Keep lease timers, raw ownership OSC and service
installation out of the musical player. Verify real Grid input → slice/playback
→ LED feedback plus release/reconnect in the actual application. Keep callback
resources distinct between instrument instances; device serial identity is not
a track or buffer ID.

For future setup, use the companion's pinned macOS candidate guide above or the
Deck packaging guide, including their preserved rollback paths. This review
changed no installed services, claimed no devices and added no new dependencies.
The companion provides a [development workbench bundle](https://github.com/kasselvania/PlugData-Monome-Devices/blob/09c820e751525903ec61da00c5be1cb0ccd63a2b/docs/WORKBENCH-BUNDLE.md),
not a finished end-user package. Its [project map](https://github.com/kasselvania/PlugData-Monome-Devices/blob/09c820e751525903ec61da00c5be1cb0ccd63a2b/docs/PROJECT-MAP.md)
also records an explicit license/package-layout gap before publication. The
reviewed mlre tree has no root LICENSE file; clarify reuse terms and preserve
attribution before distributing copied source.

Validation of this documentation update: remote revisions, primary manuals,
mlre imports/buffer operations and companion lease records were inspected;
relative links and `git diff --check` were checked. No new audio, device,
listening, installed-runtime or DAW acceptance is claimed.

## Speed control and crossover follow-up

This work starts from `51e8f70d2956c9994e808b2946e8aa5524d45eb4` on
`codex/fix-speed-slew-crossover`. Remote main remains
`fc17d598a60d4531b3beac78d1a49eccc5ad660d`; PRs #6 and #7 are still open.
The rejected R1 stash remains untouched.

### Repair contract, recorded before editing

The bounded implementation repairs the existing speed-selector control path.
It retains the original master frame ramp, two stereo readers, loop logic and
musical controls. It does not replace the sampler or claim to repair the separate
direction-slew sketch or reader crossover merely by repairing rate controls.

- Selector indexes 0 through 4 mean 0.25, 0.5, 1, 2 and 4 times source speed.
  Other selector values produce no change. Direction remains a separate control.
- Slew duration is milliseconds, clamped to 0..2000; the existing curve control
  is clamped to -1..0. Zero duration publishes the exact target synchronously,
  with interval reporting stopped. A positive duration uses the existing
  `curve~` and 5 ms control reports, initialized at the normal speed of 1.
- Each accepted rate report stores the rate before requesting one position
  snapshot. Completion stops periodic reports before publishing the exact target.
  A new command cancels the previous curve and replaces its target from the
  curve's current value. It must not toggle a reporter into an unknown state.
- These controls never request a zero or negative magnitude. Arbitrary zero-rate
  control is not a supported interface in this original player; the existing
  duration division remains unsuitable for tape-slew zero crossings. That gap
  must be repaired before enabling the direction-slew sketch.
- Positions and loop boundaries remain source-frame indexes. Duration is
  `abs(target_frame - current_frame) / (file_sample_rate / 1000 * magnitude)`.
  This repair does not change the established file/host conversion, endpoints,
  seek/start/stop semantics or add clock catch-up. Stopped/paused flags continue
  to prevent rate reports from starting a trajectory.
- The existing frame snapshots and ramps still approximate motion during a slew.
  Removing duplicate triggers is not a claim of sample-exact motion or click-free
  transitions. Native audio validation is required before accepting the repair.

### Trace results and disposition

These are findings from the actual `.pd` connections, not inferred diagnoses of
the computer or audio driver. The repaired path is still in
`sample_player_rebuild.pd`; no new playback component or external was introduced.

| Finding | Disposition |
| --- | --- |
| `curve~` starts at 0 while the player starts at rate 1. The first nonzero slew can therefore start from the wrong magnitude. | Initialize the existing curve at 1. |
| The loadbang that sets `cyclone/snapshot~`'s interval also activates reporting. Initial rate reports need not represent a user gesture. | Initialize it explicitly at `5 0 @active 0`; remove the interval-setting loadbang path. |
| Zero-duration selection still goes through an audio-block snapshot. That path can publish an older signal value instead of the just-selected rate. | Bypass sampling at zero duration: set the curve to the target and publish that target directly. |
| Both the selector and the sampled curve can request a trajectory. Two separate `change` objects also own publication and update requests. | Remove the extra selector request; use one `change` followed by `t b f`, publishing the magnitude before requesting the position. |
| Reporting starts/stops by banging a toggle, and completion publishes its target before disabling reporting. The unused stop message points at the interval inlet. | Use explicit 1/0, stop reporting first on completion, and send cancellation to the curve's left inlet before replacing a target. |
| The direction-slew branch has no hot connection to its four-field pack; the enabled branch's stored value has no outlet connection. | Unrepaired implementation gap. Do not call the existing toggle a working tape-reverse mode. |
| Direction is published before the intended deceleration. The direction reporter's toggle is connected to its interval inlet, and two midpoint snapshots surround the direction update. | Unrepaired ordering/wiring gaps; reconnecting the pack alone is insufficient. |
| Direction slew can request zero, but `calc_duration` divides by rate times sample rate. Rate and direction have separate curves publishing into the same selected-rate receiver. | Unrepaired zero-crossing and interrupted-gesture ownership gaps. |
| `tabread_processing` fans the same `vline_message` to both readers. Their input gates normally stay open. | Confirmed crossover defect: the outgoing reader also jumps. Gain ramps alone do not preserve its old trajectory. |
| `voice_1` drops `main_vline_gate` at its route outlet; `voice_0` receives that control, but the normal fade path never sends it. | Confirmed asymmetric/incomplete gate wiring. The installed, read-only `mlr-lite` copy contains the symmetric gate pattern, but is not a validated replacement. |
| Loop preparation starts the 6 ms gain handoff roughly 3 ms before the master wrap. Slice handoff starts 9 ms fades, then sends the shared jump after 1 ms. | Both readers may be audible when that shared discontinuity arrives. True trajectory handoff remains a separate repair. |
| Reader shutdown uses cancellable 9 ms delays from the previous repair; gain dispatch still uses zero-delay list storage. | Do not discard the proven shutdown repair. Check pending fade dispatch and reader reuse during rapid cuts when repairing the crossover. |

The implementation changes only the first five rows. It retains `curve~`, the
existing preset values, frame-duration calculation, snapshot-driven trajectory,
stereo tables and both readers. Loader ordering, slice offsets, beat reset,
recording, mixer, Grid/Arc and companion repositories are untouched. The remaining
rows are explicit gaps, not successful tests or promises that the current audio
path is click-free.

### Initial candidate observations and failed capture procedure

The original application and its console were inspected before source edits.
The open player identified itself as `3401`; Sample 1 already held the included
44.1 kHz stereo `DrumLoop.wav` (631881 frames). Console messages showed trajectory
updates and reader DSP handoffs. During the 600 ms rate gesture, repeated
`voice_1_vline` entries appeared. This supports the source trace of repeated
updates; it does not measure their audible effect.

The observed runtime was `/Applications/plugdata.app`, plugdata 0.9.4,
build `98ae0f78b`, Pd 0.56.3. Native Audio Settings showed CoreAudio, 48000 Hz,
512 samples, MacBook Pro Speakers and MacBook Pro Microphone. This differs from
the earlier USB-device fixture. The origin of that change is unknown; settings
were not changed and earlier results are not silently transferred to this one.

**Capture failure:** the agent started the native recorder without an automatic
stop and left it running across context compression. The user had to stop it
after minutes. This was an agent procedure failure, not evidence of a playback
or machine fault. No controlled baseline/after comparison or numerical audio
result is claimed from that recording. No controlled capture was retained at that point. The agent stopped interacting
with the native session after the user's correction. This describes the initial
`66adfe0` handoff; the resumed, automatically stopped runs and the regression
they exposed are recorded below.

**Listening:** no new listening acceptance for this candidate. The earlier user
report of “solid playback” belongs to the prior handoff repair only.

**Executed source checks:** `python3 tests/check_patch_connections.py
sample_player_rebuild.pd` checked 10 canvases, 988 objects and 944 connections
without an out-of-range object, connection to text, or invalid trigger/unpack
port. Negative fixtures for those three failures were rejected. The checker
does not instantiate externals or verify signal compatibility. A separate
comparison against the base verified identical objects/connections in all nine
nested canvases, including duration, looping, gain control and both readers.
`git diff --check` passed. These are structural checks, not audio tests.

### Validation checklist established before native follow-up

Use the original `mlr.pd`, one application instance, its actual player controls
and the console. Reload this checkout only after dealing with any unsaved native
edits. Load `DrumLoop.wav`, inspect Sample 1's buffer selection, start playback,
and raise track 1/master cautiously as in the README. Leave host/device settings
unchanged for the first comparison and record their identity.

1. Set rate slew duration to 0. Exercise selector indexes 0, 1, 2, 3, 4 and back
   to 2 while playing. Each final magnitude must match 0.25, 0.5, 1, 2, 4 and 1.
   Invalid selector values must not request another trajectory.
2. Set 600 ms duration, exercise 1x to 0.5x to 2x, and interrupt a slew with
   another selection before it finishes. Repeat with curve 0 and -1. Check the
   final target and continued playback after several complete loops.
3. Change speed while stopped and paused; it must not start playback. Resume and
   confirm the selected target. Check ordinary instant reverse at each speed.
   Leave direction slew disabled: it is explicitly unrepaired.
4. Before any audio capture, establish and verify an automatic stop independent
   of agent/UI progress. Capture the actual application's stereo output with
   a known-duration command schedule. Retain the schedule, source/capture hashes,
   host settings and representative audio. Native recorder start/stop clicks
   alone do not meet this requirement.
5. Use `tests/analyze_handoff.py` for capture levels/silence and
   `tests/analyze_reverse.py` for source alignment at its supported 0.5x/1x/2x
   rates. Extend the reference rates to include 0.25x/4x when checking those
   captures. Account for source silence and the existing swapped-channel path;
   a rate match does not establish correct channel ordering.
6. For crossover acceptance, capture the two reader positions and gains as well
   as the stereo sum during loops, cuts and commands closer than 9 ms. Verify an
   outgoing trajectory continues until inaudible, inspect boundary discontinuity,
   dropouts, stuck playback and gain sum. That acceptance cannot pass the present
   common-jump wiring merely because both speakers produce sound.

At the initial handoff, all native validation was open. The follow-up below
supersedes that status for the exact tested cases; it does not close the entire
checklist. No Bitwig or DAW lifecycle test was performed.

### Native follow-up: boundary collision

A passive `writesf~` tap with its own Pd stop timer now captures stereo player
output, master frame position and rate magnitude. A three-second check produced
exactly 144000 frames at 48 kHz and stopped without further agent action. A
24-second sequence also schedules transport stop at 23 seconds. Diagnostic
objects are attached temporarily; they are not added to the saved application.

The first comparison caught a regression in `66adfe0`: a rate change coincident
with the two-second loop boundary leaves the master held at frame 132300 until
the later reversal. The native console repeatedly reports that endpoint; the
capture contains a constant audio value. The prior player reaches every steady
preset without this freeze. This is a failed candidate result, not acceptance.

Additional repair contract before editing: a speed-change snapshot at or past
the active traversal endpoint must wrap to the opposite boundary of a valid
region before recalculating its trajectory. Otherwise an endpoint snapshot can
overwrite a just-issued wrap with a zero-distance ramp, leaving `edge~` high
and preventing another rising-edge wrap. Apply this only to speed retiming;
preserve ordinary interior positions, direction changes and explicit seeks.
Use the already-published loop bounds and direction. This keeps block-resolution
loop timing; it does not claim a sample-exact or independent-reader crossover.


The localized endpoint guard fixed that same collision in two 48 kHz runs,
including the final source with reader probes, and a 44.1 kHz run. The final
player adds four read-only `s~` taps from the existing reader position and gain
ramps; it adds no musical head or alternate audio generator. Gain and position
routing in the application remains the original routing. The saved `mlr.pd`,
loader, buffers, mixer and companion repositories were not edited in this pass.

#### Native fixture and retained results

The actual application was `/Applications/plugdata.app`: About showed **0.9.4**;
binary build identification was **98ae0f78b**, Pd **0.56.3**. Native Audio Settings
showed **CoreAudio / MacBook Pro Speakers / MacBook Pro Microphone / 512 samples**,
output gain 0.8, limiter off, oversampling 1x. Host operation was first 48000 Hz,
then 44100 Hz; 48000 Hz was restored and read back afterward. The source was the
included **DrumLoop.wav**, stereo, **44100 Hz / 631881 frames**. Thus the 48 kHz
runs exercise file/host rate mismatch in the actual original loader/player.

These captures tap the actual player's stereo signal **before the mixer**. They
do not establish speaker playback, foreground/background stability, controller
operation, or Bitwig lifecycle acceptance. UI and console were inspected during
loading and each run; the console showed reader trajectory/DSP messages and the
automatic stop. No new patch-load error was observed in the visible output.
Earlier diagnostic console errors (`No object found for: 1` and bad arguments
for `vis`) came from the agent's object-selection commands. They are not evidence
of a broken patch object. The shorthand console `NAME > vis 1` lost its argument
in this build; explicit selection followed by `vis 1` worked.

All files below are in [docs/evidence/speed-slew](evidence/speed-slew/). Each test
has full **lossless float NPZ samples**, **stereo FLAC listening audio**, and a
**JSON numerical report**. `manifest.json` binds source/fixture hashes, native
identity, original capture hashes and each retained artifact. FLAC is 24-bit
listening material; NPZ retains the original float values for reanalysis.

| Capture | Actual source loaded | Result |
| --- | --- | --- |
| `baseline-48k` | Base `51e8f70`, native player 3401 | 24 s, 4 channels. Existing steady presets already worked; longest active master hold 1.3125 ms. |
| `failed-candidate-48k` | Candidate `66adfe0`, player 3638 | 24 s, 4 channels. Master stuck for **14 s** at the loop end while rate controls continued changing. Kept as failed evidence. |
| `repaired-48k` | Endpoint guard and four reader taps, player 4110 | 24 s, 8 channels. Presets 0.25/0.5/1/2/4, interrupted 600 ms slew, instant reverse at 2x and speed change to reverse 1x; stop and 0.5x restart. No prolonged freeze; longest active hold **1.3125 ms**. |
| `repaired-44100` | Same loaded player, host rate changed in native settings | **23.999274 s**, 8 channels. Same sequence completed; longest active hold **1.428571 ms**. File length is 32 frames short of 24 s, within a Pd 64-frame block. |
| `cuts-48k` | Same player, restored 48 kHz host | 8 s, 8 channels. Original `row_1` slice path: one cut at 2 s, nine cuts 2 ms apart at 4 s, playback stop at 7 s. Master continued after the burst. |

All five captures contain **zero non-finite samples**. The repaired steady motion
measurements agree with the selected signed rates within 0.0005x in the listed
windows, excluding large wrap steps and reporting constant-position samples
separately. Float position quantization makes the *median* single-sample slope a
biased rate estimator; the retained checker uses the mean of moving steps.
Short holds and fractional loop timing remain visible and are not renamed
sample-exact looping. Changing speed while stopped did not start playback in
the tested sequence; output was zero in the checked stop windows.

The interrupted slew reached its final 2x magnitude by 14.9 s in both host runs.
Steady 1x windows match the known channel-swapped source with correlation above
0.9999 and gain near 1. Other windows, notably 2x/reverse and low-level material,
have lower correlation against the linearly interpolated master-position
reference (as low as 0.736 in the listed 44.1 kHz windows). The baseline also has
low matches in those regions. **This comparison does not close waveform or gain
fidelity acceptance**: it combines interpolation/alignment limitations with
unrepaired reader behavior. A low source level, including the quiet 0.5x restart
segment, is not automatically a dropout. No blanket no-dropout or unchanged-gain
claim is made from this sequence.

The reader traces directly confirm the source finding. At **2.001333 s** in the
48 kHz run, both positions jump about **-88199.54 frames**, with gains **0.5521 /
0.4479**. There are ten matching large simultaneous jumps with both gain taps
above 0.05 in that run and twelve at 44.1 kHz. At **2.002333 s** in the cut test,
both positions jump about **227697.31 frames** with gains **0.8866 / 0.1134**;
eight further matching jumps occur in the rapid burst. This is not an independent
outgoing trajectory. The 48 kHz loop jump has an adjacent stereo output step of
about **0.00848 / 0.04757**; these are measured differences, not a universal click
threshold or proof of audibility.

**Probe limitation:** `s~` inside a switched-off reader repeats its final signal
block. Its raw gain can therefore look nonzero after that reader is disabled.
Do not add raw gain taps across disabled readers and call that the output gain.
The retained full traces expose this, and the analysis labels it. Actual stereo
output remains the authority for audio level and silence. Crossover gain,
discontinuity and reader reuse need their own repair and output comparison.

**Listening:** after hearing `repaired-48k.flac`, the user reported: **“its clean.
i dont hear any clicks”**. This accepts the sound of that specific drum capture;
it does not erase the measured common-jump wiring or establish universal
click-free output. Earlier “solid playback” acceptance remains attributed to
the prior handoff fix.

#### Repeat the bounded native checks

1. Open this checkout's `mlr.pd` in the same plugdata build, one application
   instance. Load `DrumLoop.wav` using Sample 1 Load. Inspect the actual console
   and buffer selection. Record the host rate/device/buffer before changing them.
2. Open `pd arrays-samples`, then the actual `sample_player_rebuild 1`. Its
   console messages show its numeric `$0` ID (for example `4110-loop_end`). To
   open from this build's console while arrays-samples is selected, use
   `sel sample_player_rebuild_1_1`, then `vis 1`, then `deselect`.
3. Temporarily place `[tests/bounded-player-capture 1 ID]` and
   `[tests/speed-sequence 1 ID]` in that player's canvas, substituting its current
   ID. These are test attachments, not saved application objects. Console canvas
   commands are `cnv obj 50 650 tests/bounded-player-capture 1 ID` and
   `cnv obj 50 710 tests/speed-sequence 1 ID`. Toggle Pd DSP off/on after adding
   the signal tap so this runtime rebuilds the graph (`pd dsp 0`, `pd dsp 1`).
4. First check automatic capture stop with
   `1-test-capture start /absolute/path/check.wav 3000` while playback is stopped.
   The test tap arms a Pd delay **before** starting `writesf~`, clamps duration
   to 100–30000 ms, rejects overlapping starts, and has a 250 ms restart cooldown.
   Inspect `capture-stopped` in the console and the finalized file's length.
   Stop is also available as `1-test-capture stop`. Do not use the native output
   recorder without an independent stop. An initial header-only tap capture
   before the DSP rebuild was rejected; after rebuilding, the check produced
   exactly 144000 frames at 48 kHz and stopped itself.
5. Run `ID-test-speed symbol /absolute/path/speed.wav`. The fixture arms its own
   schedule; it stops playback at 23 s and capture at 24 s. Wait for the console
   stop and finalized file before proceeding. The first 20 s use source frames
   44100–132300 (1–3 s); the stop/restart reloads the full buffer region. The
   complete schedule is in `tests/speed-sequence.pd`.
6. Repeat at 44100 Hz host operation, then restore the original rate and verify
   it in native Audio Settings. Do not change device or hardware buffer size.
7. For cuts, temporarily add `[tests/cut-sequence ID]` and send
   `ID-test-cuts symbol /absolute/path/cuts.wav`. It uses track 1, sets the
   existing immediate quantizer mode, and sends through `row_1`. It stops itself
   after 8 s. Do not overlap this schedule with the speed schedule.
8. Reanalyze with NumPy and ffmpeg/ffprobe:
   `python tests/analyze_speed_capture.py DrumLoop.wav CAPTURE.wav` (add `--cuts`
   for the cut schedule). Use `--retain PREFIX` to retain the full float NPZ and
   stereo FLAC; NPZ files can be passed back as capture inputs. This is offline
   analysis of actual native output, not another playback runtime.
9. When finished, verify capture and playback stopped; close/reload the main
   without saving temporary test objects. In this session, the original main
   was left visible, DrumLoop.wav loaded, playback stopped, no recorder attached,
   and the host restored to 48000 Hz. Mixer settings after reload are defaults;
   raise track/master for a subsequent speaker listening check.

#### Remaining gates and next repair

Structural checks pass for the final player (10 canvases, 994 objects, 952
connections) and all three test patches. `git diff --check` passes. These source
checks are distinct from the native runs above.

The speed/boundary collision has a reproduced failure and a bounded repair.
The remaining speed checklist includes a fresh first gesture with nonzero slew,
other curve shapes, invalid selector inputs, paused changes, and instant reverse
at every preset; the retained schedule does not cover all those combinations.
Broader listening, waveform/gain fidelity, direction slew, independent crossover,
stereo ordering, and foreground/background operation remain open. No recording
or overdub function, multiple musical heads, controller connection, or DAW
lifecycle acceptance was added in this pass.

The next focused repair should make only the incoming reader receive a new
trajectory while the outgoing reader finishes its fade, restoring the missing
input-gate ownership and checking interrupted fades with these same probes.
That work has not been folded into this speed candidate. PR #8 stays draft and
unmerged for review; do not turn this evidence pass into another playback rewrite.

## Incoming-reader ownership candidate

This follow-up starts from PR #8, `f7aadb82bca4dcd6fb689b458a4954a9dad38014`,
on `codex/fix-crossover-ownership`. The checkout was clean, remote main remained
`fc17d598a60d4531b3beac78d1a49eccc5ad660d`, and the failed-experiment stash was
preserved. Before editing, the actual original main and console were inspected:
Sample 1 held DrumLoop.wav (631881 frames), player 4347 was stopped, and DSP was
on. No diagnostic recording was running.

Contract before implementation: keep the existing two stereo readers, frame
units, speed calculation, and 6 ms loop / 9 ms slice gain ramps. At a handoff,
close the outgoing reader's trajectory gate and open the incoming reader's gate
before issuing the new frame ramp. Leave the outgoing ramp untouched while its
gain falls. Begin the handoff when the new trajectory is issued, not at the
old pre-boundary signal or before the slice's existing 1 ms delay. Initial play
owns reader 0; ordinary speed/direction retiming addresses the selected reader.
Keep the existing cancellation of each reader's delayed DSP shutdown on reuse.
Stopping cancels pending slice/fade dispatch and resets selection immediately,
so an old delayed reset cannot change ownership after a quick restart.

The existing 1 ms slice scheduling remains; commands arriving faster than that
can replace the pending slice. A command during a 6/9 ms fade reuses one of the
two readers at its current gain. This slice does not promise that such reuse is
inaudible, add more readers, or impose a new quantization/queue policy. Measure
it explicitly with the 2 ms burst. The prior raw signal-tap limitation while
`switch~` is off still applies; actual output is the level authority.


### Source changes and first native pass

Normal gain-target dispatch now sends `main_vline_gate 0/1` before the existing
DSP command. Voice 1's previously unconnected route outlet now controls its
`switch`, symmetrically with voice 0; its trajectory gate initializes closed.
Loop handoff moved from the early threshold to the actual boundary trigger,
ordered before the new frame ramp. Slice handoff moved after its existing 1 ms
delay, ordered before the stored position. Gain-dispatch delays and pending
slice commands are cancelled on stop; the old delayed reader-selection reset
became immediate. The normal 6/9 ms gain ramp values, per-reader 9 ms shutdown
cancellation, frame calculations and stereo audio wiring are unchanged.

The first loaded version (player **4581**) ran in actual Mac plugdata **0.9.4**,
build **98ae0f78b**, Pd **0.56.3**. Its binary matches the prior fixture's recorded
SHA-256. The float WAV headers confirm **48000 Hz**. Device and 512-sample buffer
settings were not changed in this pass; their last native readback is the
preceding speed-validation session. Do not call that a fresh settings readback.
The original loader loaded **DrumLoop.wav**, 44100 Hz, stereo, 631881 frames.
The console displayed the new gate commands, reader DSP/position messages,
scheduled speed steps, and `capture-stopped` after both runs. The player UI
showed the original buffer selection and moving playbar.

Retained artifacts are in [evidence/crossover-ownership](evidence/crossover-ownership/).
`first-pass-speed-48k` is the existing 24-second speed/loop sequence;
`first-pass-cuts-48k` is the existing eight-second slice sequence. Each has full
float NPZ traces, stereo FLAC, and numerical JSON. The ownership reports also
check the prior PR #8 recordings as failing controls. `manifest.json` binds
source, recorder, capture and analysis identities.

| Check | Prior PR #8 audio | First crossover pass |
| --- | --- | --- |
| Loop wraps in the speed sequence | 13 events fail the sole-incoming-owner check | **13/13 preserve the outgoing reader**, no ownership failure |
| Single slice plus nine-cut 2 ms burst | 9 of 10 events fail ownership | **10/10 preserve the outgoing reader**, no ownership failure |
| Non-finite samples | None | **None** in either capture |
| Steady speeds / reverse / stopped windows | Recorded in PR #8 | Selected rates still reached; stopped test windows remain silent; longest active master hold remains **1.3125 ms** |
| Incoming reader above gain 0.05 during rapid reuse | Common-jump wiring confounds ownership | **8 burst cuts reuse an audible incoming reader**; this is an explicit limitation |

At the first loop wrap (**2.001333 s**), reader 0 stays at frame **132300**, while
reader 1 begins at **44100.457** with gain **0.003472**, reaching full gain across
the existing 6 ms fade. The stereo adjacent-sample difference at that exact jump
falls from **0.008476 / 0.047567** to **0.0000294 / 0.0001652**. At the first slice
(**2.002333 s**), the outgoing reader continues its old ramp (about **0.919
frames/sample**), while the incoming reader jumps to **315941.406**. This is the
existing dual-reader design working as a handoff, not a new musical playhead.
The largest steps across wider windows can still be source transients; the
single-boundary reduction is not a universal click/audibility threshold.

### Final edits and validation interruption

Source review after the first capture found that stopping could leave the
previous owner's trajectory gate open. The final edit closes **both** gates on
stop; initial play then opens reader 0. This extra gate message and three
connections were **not loaded in native** before UI access failed. The retained
`first-pass-source.patch`, applied to this candidate's source, reconstructs the
exact earlier source represented by the recordings. It removes only that later
stop-gate edit; the snapshot was reconstructed from the known edit sequence,
not saved by the native patch UI.

The passive recorder was also extended from eight to ten channels, adding the
two reader DSP flags. This is to distinguish a disabled reader's held `s~` probe
block from its active gain ramp when examining shutdown timing. It does not
change the player's audio. **The ten-channel fixture has only passed source
checks so far.** `tests/crossover-transport.pd` adds a bounded eight-second
schedule of stop/restart, pause/resume and rapid reversals during cuts; playback
stops at seven seconds. **That schedule has not yet run in native.**

Both first-pass recordings and playback had stopped before closing the main for
reload. The last verified UI then showed `mlr.pd` selected in the native file
chooser but **Open disabled**. Return made no visible change; Escape and later
accessibility readbacks timed out. Resetting the computer-use connection and
selecting the app by its discovered bundle ID also timed out. No application,
service or installed runtime was restarted, and no alternate runtime or message
socket was substituted. A read-only one-second process sample showed the main
thread servicing its event loop; it does not identify the chooser/control failure
cause or establish that all UI paths were responsive. The user was asked to
cancel the chooser and report whether the main responds. Last verified state
is that chooser; successful reload/restoration is not claimed.

**Listening:** no new report for the crossover capture yet. The earlier report
of clean playback/no clicks belongs to PR #8's speed capture and is not silently
transferred to this candidate.

### Continue validation

Use the bounded-capture attachment/reload procedure above. On the final source,
attach `[tests/bounded-player-capture 1 ID]`, `[tests/speed-sequence 1 ID]`,
`[tests/cut-sequence ID]`, and `[tests/crossover-transport ID]` temporarily inside
the actual player; rebuild the DSP graph after adding the signal recorder.
Verify the three-second automatic stop before the next run. Do not start a
second sequence until the previous one has stopped.

- `ID-test-speed symbol /absolute/path/speed.wav`: repeat all preset speeds,
  the interrupted slew, forward/reverse wraps and stop/restart (24 s).
- `ID-test-cuts symbol /absolute/path/cuts.wav`: single cut and 2 ms burst (8 s).
- `ID-test-transport symbol /absolute/path/transport.wav`: stop and restart during
  a fade, brief pause/resume, rapid reversals, and cancellation of a queued slice
  by stop (8 s). Inspect the UI and console as well as captured audio/state.
- `python tests/analyze_crossover.py CAPTURE.wav --mode speed` (or `cuts` /
  `transport`) inspects outgoing-reader continuity at master jumps. Run the
  existing `analyze_speed_capture.py` for rates, levels, silence and source
  alignment. Neither checker alone is a listening or complete audio-fidelity test.

Complete the final ten-channel runs at **48 and 44.1 kHz**, inspect the outgoing
DSP shutdown relative to the last nonzero gain, and investigate any actual
output dip or discontinuity. Restore the original 48 kHz host setting afterward.
Listen separately to the speed/loop and rapid-cut captures. Keep the two-reader
reuse limitation explicit; any new queue/latency policy needs its own musical
decision. Then close/reload without saving temporary diagnostics and leave the
original entry point loaded and stopped.

Final source checks pass: player **10 canvases / 1003 objects / 963 connections**;
recorder **38 objects / 40 connections**; transport fixture **62 objects / 60
connections**; `git diff --check` passes. The ownership checker rejects the
retained common-jump baseline and accepts all first-pass handoffs. These checks
do not close final-native, shutdown/gain, 44.1 kHz, listening or UI-restoration
gates. The follow-up PR remains draft and unmerged, separate from PR #8.
