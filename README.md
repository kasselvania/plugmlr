# plugmlr

An MLR-style musical application for plugdata, with sample and live buffers,
slice playback, rate controls, and a mixer. Current work is to understand and
harden the original application, following its existing signal and control paths.

The accepted checkpoint now includes playback/buffer PRs #6–#10, recording PR #11
and Stop/restart/instant-reverse PRs #12–#13. Fresh, fixed-length stereo takes use the original live buffers and a
local Pd stereo connection between the companion and application, as chosen by
the user. Separate plugdata-process transport remains unqualified: both tested
`pdlink~` arrangements shifted the right channel by one Pd block. See the
[current contract and evidence](docs/STATUS.md#current-inputrecording-recovery-contract).
The [48 kHz recording checkpoint](docs/STATUS.md#recording-checkpoint-with-the-new-hardware-source)
now includes real hardware takes, early Stop, recorded/imported switching, and the
user's report of useful levels with no audible problems in those captures.

The separate [Stop/restart repair](docs/STATUS.md#stoprestart-follow-up) fades the
existing readers for 6 ms before shutdown. Play during that interval waits for
cleanup at 9 ms; another Stop cancels it. Recording Stop remains direct, and empty
buffer playbars report zero. Paired native audio/state checks cover rapid commands
at 48 kHz; broader transition and host-rate qualification remains separate.

The merged [instant-reverse repair](docs/STATUS.md#instant-reverse-continuity-follow-up)
uses the current ramp position when Direction Change is pressed, eliminating the
old block-snapshot jump. It keeps the existing readers and loop/slice crossovers.
Native tests cover all five speeds, rapid turns, loop/fade boundaries and a file/host
sample-rate mismatch; the user heard clean direction changes in the musical capture.
Tape-direction slew remains open; speed and Pause follow-ups are below.

The [speed-slew position repair](docs/STATUS.md#speed-slew-position-follow-up) now
uses that same current-position calculation for rate reports. Paired native
captures remove the oversized position jumps during glide; the user heard clean
musical glides/reversals. The region/slice follow-up is described below.

The [Pause/Resume candidate](docs/STATUS.md#pauseresume-follow-up) fades the existing
readers before holding the current position, then restarts with their play fade.
Rapid toggles queue/cancel Resume; Stop, buffer switching and a new slice cancel
stale pause cleanup. The existing slice gesture resumes a paused track. Actual
48 kHz player/mixer checks cover these transitions; listening is recorded separately.

The [slice-policy candidate](docs/STATUS.md#slice-policy-checkpoint) keeps 16 fixed
whole-content slices. Any slice press exits a smaller loop; reverse enters at the
slice end. The choice is named `pd slice_policy` in `sample_player_rebuild.pd`,
separate from loop detection and reader fades. Pending slices own the next jump,
preventing a competing boundary fade. Alternative mappings are not enabled.

The [visible slice/loop candidate](docs/STATUS.md#visible-slice-and-loop-controls-review-candidate)
adds buttons 1–16, a whole-sample position/region display, and Start_s/End_s fields
with Apply and Full sample. Apply restarts at the region beginning forward or end
in reverse; paused edits wait for Resume. Edits are staged until Apply. Native UI,
player/mixer and regression checks are retained, including the [overlapping-handoff repair](docs/STATUS.md#overlapping-cut-handoffs-repaired-candidate).
Pending cuts wait for the prior fade before reusing a reader; paused Apply preserves
the mixer fade. Matched 48 kHz stress/regression checks pass. Very short natural
loops and broader host configurations remain unqualified.

The musical direction is free-form tape manipulation, growing toward an
mlre-inspired community instrument. The immediate behavior to finish is instant
reverse or an audible tape slew, with timing drift allowed. The
[tape reference catalogue and next work](docs/STATUS.md#free-form-tape-direction)
separate that decision from functions already tested.

The runnable entry point is **[mlr.pd](mlr.pd)**. Small repairs restore both
reader turns and bidirectional looping in the existing player. Direction Change
reverses playback; reverse wraps return to the region end. The
[recorded repair history](docs/STATUS.md#reverse-playback-and-loop-boundaries)
keeps each source change, native result, listening report, and remaining limit
separate. The current buffer and crossover candidates are described below.

The current [buffer candidate](docs/STATUS.md#buffer-selection-and-recording-length-settings)
repairs selection between the existing imported and live buffers. Open a player
from `pd arrays-samples` and use its **Buffer Select** menus. The panel below
shows the selected buffer, whether it contains audio, and its content duration.
Selecting while playing uses a short fade and starts the new buffer from its
beginning (end in reverse); selecting an empty buffer leaves playback stopped.
Stop cancels a pending restart. A subsequent one-line mixer-routing repair fixes
loading another slot muting track 1 while its playhead continues; the
[paired mixer-output capture](docs/STATUS.md#user-follow-up-loading-another-slot-muted-track-1)
records the failure and repair. This is a fade through silence, not a seamless
crossfade between different buffers.

For a selected live buffer, **grow / sec / bars** sets the next recording's
length mode; **Amount** sets seconds or whole bars. Bars currently mean 4/4.
The target duration follows the current project tempo; existing audio does not
resize or stretch when tempo changes. Fixed recording freezes that target at
Record; grow/trim, pause/resume, overdub and recording quantization remain
unimplemented. **Clear live** erases the selected live buffer after stopping its
readers and refuses while recording. Imported buffers use their load controls.

The [speed-control candidate](docs/STATUS.md#speed-control-and-crossover-follow-up)
orders rate-slew updates and prevents a speed change at the loop endpoint from
leaving playback stuck. Bounded native captures now cover all five speeds, an
interrupted slew, instant reverse, and stop/restart at 44.1 and 48 kHz. The
[retained results and reproduction steps](docs/STATUS.md#native-follow-up-boundary-collision)
include the failed candidate. That review found both readers jumping during
a fade. The user heard clean changes with no clicks in the repaired drum
capture; crossover repair and tape-direction slew remain open. This is still a
draft candidate, not a universal click-free playback claim.

The [crossover candidate](docs/STATUS.md#incoming-reader-ownership-candidate)
keeps the outgoing reader on its old trajectory during a loop or slice fade.
Native validation found and repaired a competing speed-boundary jump and a
brief shutdown-related gain dip. The original two readers and 6/9 ms fades are
retained. Bounded audio/state captures, failing controls and limitations are
recorded in STATUS. Rapid reader reuse is still not universally click-free;
tape-direction slew remains separate work. The user accepted this work as part of the playback/buffer checkpoint.

The [functionality map](docs/STATUS.md#whole-application-functionality-map)
traces the existing slice, loop, slew, transport, recording, and feedback paths,
identifies incomplete connections, and proposes small refactoring boundaries.
It is a source review, not a claim that those functions all work in the runtime.

## Run the original application

1. Open this checkout's `mlr.pd` in plugdata. Keep its sibling patches together.
2. Enable DSP and open plugdata's console, with both messages and errors visible.
3. Use **Sample 1 Load** to choose the included `DrumLoop.wav` or a stereo file.
4. Open `pd arrays-samples`, then `sample-data 1`, to inspect the loaded arrays.
   Open `sample_player_rebuild 1`; its buffer selection should show
   `sample_buffer`, `1` after loading.
5. Press **Play/Pause** in that player. Open `pd mixer` and raise **track 1 volume**
   and **Master Volume** as needed, starting quietly. The playbar should move
   and both reader turns should be audible. The included drum file has about
   half a second of silence at its end; that short pause is in the source.

Load Sample 2 as well, then select `sample_buffer`, `2` in player 1 to audition
that buffer through track 1. Loading a sample explicitly selects it in its own
numbered track; passive metadata updates do not redirect other players. Loading
or clearing stops all players selecting that buffer before changing its arrays.
Playback remains stopped after a load; press Play when ready. The new ordinary
message interfaces and native test steps are documented in STATUS.

## Record from standalone hardware input

1. Keep one `mlr.pd` and open **`audio-in-subpatch.pd` in the same standalone
   plugdata application**. This local bus does not cross separate processes.
2. In plugdata Audio settings, select the interface and enable the required
   input channels. Set **Host_L / Host_R** in the companion (this session: 3/4),
   raise **Volume In** (0–2×; 1 is unity), and choose **Local input bus 1**. Leave Monitor Mix at 0
   unless deliberate direct monitoring is wanted.
3. On `mlr.pd`, verify both **Recording input** meters, then enable
   **Arm_recording_input**. Arming does not detect a connected source: silence
   will record silence. Keep the companion and DSP running.
4. Open `pd arrays-samples` → `sample_player_rebuild 1`. Choose an empty
   `live_buffer` slot, select **sec** or **bars**, and set Amount. This slice
   accepts 64 host frames through 60 seconds at 44.1/48 kHz; runtime recording
   evidence currently covers 48 kHz only. Bars use the current 4/4 project tempo.
5. Press **Record live**. The panel reports Recording, then Loaded and the actual
   content duration. It stops at the frozen target; **Stop** ends early. A second
   Record refuses to overwrite existing content; use Clear live deliberately.
6. Press **Play/Pause**, with track and master gain raised quietly. The existing
   direction, speed, loop and sample/live-buffer selection operate on the take.
   No automatic playback follows recording. Switching selection does not redirect
   an active writer; reselect that live buffer to Stop it early.

Known playback limits: simultaneous loop-region/slice changes and Pause can
still produce abrupt steps. The early-take loop gap, hard Stop and instant-reverse
position jump have localized repairs with retained evidence; this does not
establish click-free transport for every signal.

Takes exist in memory; project recall and exporting recordings through a product
UI are not implemented. See STATUS for bounded test captures and remaining gates.

For direction/loop checks, use the [repeatable procedure](docs/STATUS.md#repeat-the-direction-check)
and [control-only panel](tests/reverse-controls.pd). For the prior handoff check, use the [repeatable procedure](docs/STATUS.md#repeat-the-handoff-check)
and optional [control-only slice panel](tests/handoff-commands.pd). This is still
the original application, with its existing shared global control names; open
only one copy for this check.

The recorded session used plugdata **0.9.4 nightly, build `98ae0f78b`**, with
Pd **0.56.3**. The patches use plugdata's multichannel Pd support and library
objects such as `popmenu`, `curve~`, `meter2~`, and `cyclone/snapshot~` from its
bundled ELSE/Cyclone environment. This is not a verified vanilla-Pd setup guide.
The existing Grid path uses `monome-object.pd` and SerialOSC; physical Grid
operation was not validated in this session. No dependency installation was
needed for the observed Sample 1 playback path.

The intended community suite pairs plugmlr with
[PlugData-Monome-Devices](https://github.com/kasselvania/PlugData-Monome-Devices/tree/feature/serialosc-leases)
and the [lease-aware SerialOSC fork](https://github.com/kasselvania/serialosc/tree/feature/leased-destinations).
The device package handles selection, claim, renewal and release; SerialOSC can
expire abandoned leases and darken the hardware after a client dies. The
[suite map](docs/STATUS.md#monome-suite-and-leased-serialosc) records exact source
pins, platform packaging and reported acceptance. This application still uses
its legacy connection patch: integration with the new device package remains
work to do, and installing a lease daemon alone does not migrate that path.

Alternative and historical patches remain alongside the entry point. Their names
do not establish which behavior works. The rejected shared-playback rewrite is
preserved separately and is not the current application; details are in STATUS.
