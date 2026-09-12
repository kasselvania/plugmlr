# plugmlr

An MLR-style stereo instrument for plugdata, built from the original sample/live
buffers, playback controls and dual-reader crossfades. The wider direction is a
reusable musical toolkit; the failed replacement engine is not the active path.

The current checkpoint includes imported/live buffer selection, forward/reverse
playback, five speeds and speed glide, Stop/Pause, 16 whole-content slices,
editable loops, fixed-length stereo recording, and an internal slice clock.
The current recording recovery adds bounded Free recording and a take view with
buffer-specific Finish controls. Native 48 kHz checks cover simultaneous takes,
growth alongside playback and DSP interruption. The exact-loop-end Reverse and
stale-boundary handoffs are now repaired in the original player, with native
44.1/48 kHz evidence and [a stereo listening capture](docs/evidence/loop-boundary-handoff/listening.wav).
Listening acceptance for this checkpoint remains open.
PRs #18 and #19 are merged; the user accepted both their musical captures.
See [current status](docs/STATUS.md#current-checkpoint--2026-09-11) for remaining
work and links to the retained numerical/listening evidence. Older STATUS sections
record what was true at that point in the repair history.

**Player view:** open `mlr.pd`, then click **Open player 1**.
The dedicated view keeps the existing player controls together with transport,
direction, selected speed, clock source/BPM/count, and reset feedback. Run controls
the shared clock; Play controls the selected player. Reset reports Off, waiting
for Play/Resume/clock, or Counting. Its flash means a reset request, not a claim of
sample-exact execution. Wiring stays available
in `sample_player_rebuild.pd`; the new view does not instantiate another player.
Native reset-menu selection is verified. On 2026-09-11, the user approved the
layout and successfully tested the internal clock and Beat Reset.

**Tempo fit:** enable **Fit** and set **Sample beats** to the
full sample's quarter-note length (1..64; four beats per 4/4 bar). At preset 1x,
playback fits that length to the shared BPM. Presets .25/.5/2/4 multiply the fitted
speed; **Target speed x** shows the resulting tape speed, including its pitch change.
Smaller loops and slices keep that speed. Tempo changes use Speed glide; glide can
drift from the clock. Run controls ticks, independently of Fit. Beat Reset still
repositions playback separately. Free restores the selected preset. Missing content
or a rate outside 1/64..64 shows **Fit unavailable / Free** and uses the free preset.

Speed-glide reports are bounded between the last applied speed and the new target.
The [playback/slew review](docs/evidence/playback-slew-review/observations.md)
retains the earlier loop-timing and reader-reuse failures. The
[natural-loop repair](docs/evidence/natural-loop-timing/observations.md) schedules
wraps from the existing ramp duration and shortens fades when a reader needs to
be reused. Native 44.1/48 kHz tests cover cycles down to 2 ms and interrupted
turns/glides. A full cycle shorter than one host sample stops with feedback.
Shorter fades can change the sound; numerical checks are not universal click-free
acceptance. [New musical listening material](docs/evidence/natural-loop-timing/listening.wav)
is ready for review.

**Slice controls:** each player has a Quantize checkbox and Slice grid menu.
Checked means queued slices wait for a matching clock tick; unchecked means
immediate. Default is unchecked with a 1/16-note grid. The main Track 1 checkbox
mirrors player 1. Scripted `<track>-quantizer` messages keep the legacy convention:
1 = immediate, 0 = quantized. Stop/Pause, buffer selection, mode and grid changes
cancel pending keys. Any committed slice restores whole-content loop bounds.

**Clock:** select internal with the main source button, choose BPM (30–320),
then enable Run. Clock Run controls ticks, separately from playback. Clock Stop
holds the count and retains a pending key; player Stop/Pause cancels that key.
Changing BPM does not restart the current audio ramp. The [Beat Reset candidate](docs/STATUS.md#beat-reset-contract-review-candidate)
adds **Reset every** to each player: Off, 1 beat, 2 beats, 1 bar, 2 bars, 4 bars,
8 bars (4/4). It restores full-sample bounds and jumps to the start forward or
end in reverse on the next matching shared-clock boundary. Paused/stopped tracks
stay silent; speed is unchanged. Public `<track>-reset-beats` accepts
0/1/2/4/8/16/32. Same-tick reset supersedes a quantized slice through the existing
crossover. The replacement listening capture is accepted; native dropdown selection and reset timing are verified.
Tempo fit is a rate adjustment, not phase locking. DAW/MIDI synchronization and
tape-direction slew remain open.

**Buffers and recording:** selection while playing fades to the new buffer's
beginning (end in reverse); selecting an empty buffer stops playback. Fixed fresh
stereo recording accepts seconds or 4/4 bars and freezes its target at Record.
Free starts with one second of capacity, doubles near 90% occupancy and stops at
Stop or 60 seconds. Only written content becomes playable; unused capacity stays
allocated. This recovers the original growth policy through the buffer-owned writer.
Recording pause/resume, overdub, physical shrink and recording quantization remain open.
Recording direction/speed and their slew are planned artistic tape controls;
the current input writer stays forward at 1x independently of playback controls.
Takes remain in memory: there is no product export or project-recall UI yet.

The runtime used for recent validation is plugdata 0.9.4 nightly `98ae0f78b` /
Pd 0.56.3, with bundled ELSE/Cyclone objects. This is not a vanilla-Pd claim.
Keep the sibling patches together and use one application instance: shared global
names prevent isolated copies in one Pd environment. Playback now has bounded
44.1/48 kHz and file/host-mismatch evidence, plus a two-player shared-buffer
comparison. Bitwig audio/clock and plugin-instance isolation remain open. See
[host validation](docs/STATUS.md#host-and-instance-validation-review-candidate). Dependencies and the Monome suite connection are below.

## Connect a Grid

The next layout work follows the [pinned mlre manual and adaptation map](docs/STATUS.md#mlre-control-reference-and-next-grid-slice--2026-09-11).
This is a design reference; the current patch implements the controls below.

Initialize the pinned connection package after cloning or updating:
`git submodule update --init --recursive`.

Open `mlr.pd` and click **Grid_connection**. Choose the device, click **probe**,
then **claim** when the console reports it free. Session shows `connected` only
following the package's verified lease. Click **release** before closing or
moving the Grid to another application. Discovery does not auto-claim; an existing
owner is not automatically displaced. Details and failures appear in the console.

The adapter retains the original musical mapping: physical rows 1–6 (zero-based)
feed the original numbered row controls. It does not introduce a new Grid layout.
Legacy LED messages are translated into the package's cached LED controls.
The second and third physical rows show a moving whole-sample position marker
for players 1 and 2. Press Play first: slice keys do not start a stopped player.
Stop, Pause, empty buffers and buffer switching clear the marker; reconnect
redraws current state. Other rows keep their original controls without new
playback feedback. Hardware-global intensity below 15 is explicitly unsupported. See the [adapter checkpoint](docs/STATUS.md#grid-adapter-review-candidate--2026-09-11).

### Grid quick reference

Physical key numbers count from 1. Track rows 2/3 control players 1/2; these are
also the two rows with tested playback feedback. Top-row key 2 marks CUT.

| Action | Gesture / meaning |
| --- | --- |
| Start, pause, resume | Hold **ALT**, top-right key 16, then press a track-row key. |
| Cut | Press a track-row key without modifiers. Start the player first. Cuts follow that player's Quantize setting. |
| Loop a range | Hold one track key, press another on the same row, release either. Both cells are included. |
| Loop one cell | Hold **MOD**, top-row key 14 (third from right), then press a track key. Commits on press; release does not retrigger. |
| Leave a smaller loop | Make an ordinary cut; it restores full-content bounds. |
| Read the LEDs | Dim cells show the committed smaller loop; the brighter moving cell is playback. Pause/Stop retain the dim range. |
| Change the visible player | Press a key on its track row; its existing player panel opens. |
| Hard Stop | Use Stop on the player panel. ALT uses Pause/Resume. |

ALT transport and loop commits act immediately; ordinary cuts retain per-player
quantization. Grid loop commits preserve a running position inside the new range
and wrap immediately if outside it. On-screen Apply still jumps to the loop entry.
ALT wins when both modifiers are held. ALT/MOD presses, Stop/Pause, buffer changes
and disconnect cancel unfinished two-key gestures; a third held track key cancels
the pair until all row keys are released. Full content has no dim background.

These controls have physical acceptance; the combined two-lane capture also has
numerical and listening acceptance. See the [current checkpoint](docs/STATUS.md).
Other views and bottom-row controls remain reserved, not implemented.

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
   **Enable_recording_input**. Enabling does not detect a connected source: silence
   will record silence. Keep the companion and DSP running.
4. Open `pd arrays-samples` → `sample_player_rebuild 1`. Choose an empty
   `live_buffer` slot. Select **sec** or **bars** and set **Amount (fixed)**,
   or choose **Free** to finish manually within its displayed **60-second cap**.
   Fixed takes accept 64 host frames through 60 seconds at 44.1/48 kHz; this
   recovery's native evidence covers 48 kHz. Bars use the current 4/4 project tempo.
   Start/Stop are immediate; a bar-sized take is not a quantized launch.
5. Press **Record live**. The panel reports Recording, then Loaded and the actual
   content duration. **Stop** finishes a Free take or ends a fixed take early;
   either mode stops at its frozen limit. A second Record refuses to overwrite
   existing content; use Clear live deliberately. Recording state and Last error
   are separate; a refused command does not mean the running take stopped.
6. Press **Play/Pause**, with track and master gain raised quietly. The existing
   direction, speed, loop and sample/live-buffer selection operate on the take.
   No automatic playback follows recording. Switching selection does not redirect
   an active writer. Open **Recording takes / Finish** on the main window to see
   each live buffer's activity, elapsed seconds and frozen limit. Its **Finish**
   always addresses that row's buffer, even after browsing elsewhere. Idle rows
   show zero progress; content duration remains in the buffer/player view.

Turning DSP off finishes the written portion and leaves recording stopped when
DSP returns. A zero-frame take stays Empty. Hardware/host reconfiguration without
a Pd DSP-off message is not yet qualified as a safe interruption.

Playback repairs include the earlier loop/selection collisions, Pause, hard Stop
and instant-reverse position jump. Very short natural loops and broader host
configurations remain unqualified; retained tests do not establish universally
click-free playback.

Takes exist in memory; project recall and exporting recordings through a product
UI are not implemented. See STATUS for bounded test captures and remaining gates.
The [Free recording tests](docs/evidence/free-recording/observations.md) and
[recording continuity tests](docs/evidence/recording-continuity/observations.md)
run silently in dedicated fixtures. The latter retains a musical listening file
and the failing exact-boundary reversal. Device delivery during allocation,
44.1 kHz Free growth and user listening remain open.

For direction/loop checks, use the [repeatable procedure](docs/STATUS.md#repeat-the-direction-check)
and [control-only panel](tests/reverse-controls.pd). For the prior handoff check, use the [repeatable procedure](docs/STATUS.md#repeat-the-handoff-check)
and optional [control-only slice panel](tests/handoff-commands.pd). This is still
the original application, with its existing shared global control names; open
only one copy for this check.

The recorded session used plugdata **0.9.4 nightly, build `98ae0f78b`**, with
Pd **0.56.3**. The patches use plugdata's multichannel Pd support and library
objects such as `popmenu`, `curve~`, `meter2~`, and `cyclone/snapshot~` from its
bundled ELSE/Cyclone environment. This is not a verified vanilla-Pd setup guide.
The current Grid path uses `mlr-grid.pd` and the pinned Monome package. Physical
connection, corner LEDs and one original musical row route were verified; the
moving marker has also been observed by the user; detailed hardware transition
checks remain open. No dependency
installation was needed for the observed Sample 1 playback path.

The intended community suite pairs plugmlr with
[PlugData-Monome-Devices](https://github.com/kasselvania/PlugData-Monome-Devices/tree/feature/serialosc-leases)
and the [lease-aware SerialOSC fork](https://github.com/kasselvania/serialosc/tree/feature/leased-destinations).
The device package handles selection, claim, renewal and release; SerialOSC can
expire abandoned leases and darken the hardware after a client dies. The
[suite map](docs/STATUS.md#monome-suite-and-leased-serialosc) records exact source
pins, platform packaging and reported acceptance. The application now routes its original Grid messages through that package.
Installing a lease daemon alone does not migrate other legacy patches.

Alternative and historical patches remain alongside the entry point. Their names
do not establish which behavior works. The rejected shared-playback rewrite is
preserved separately and is not the current application; details are in STATUS.
