# plugmlr

An MLR-style stereo instrument for plugdata, built from the original sample/live
buffers, playback controls and dual-reader crossfades. The wider direction is a
reusable musical toolkit; the failed replacement engine is not the active path.

The current checkpoint includes imported/live buffer selection, forward/reverse
playback, five speeds and speed glide, Stop/Pause, 16 whole-content slices,
editable loops, fixed-length stereo recording, and an internal slice clock.
PRs #18 and #19 are merged; the user accepted both their musical captures.
See [current status](docs/STATUS.md#current-checkpoint--2026-09-11) for remaining
work and links to the retained numerical/listening evidence. Older STATUS sections
record what was true at that point in the repair history.

**Player view (review candidate):** open `mlr.pd`, then click **Open player 1**.
The dedicated view keeps the existing player controls together with transport,
direction, selected speed, clock source/BPM/count, and reset feedback. Run controls
the shared clock; Play controls the selected player. Reset reports Off, waiting
for Play/Resume/clock, or Counting. Its flash means a reset request, not a claim of
sample-exact execution. Tempo fitting remains unfinished. Wiring stays available
in `sample_player_rebuild.pd`; the new view does not instantiate another player.
Native reset-menu selection is verified. Human usability assessment remains open.

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
Tempo-locked audio, DAW/MIDI synchronization and tape-direction slew remain open.

**Buffers and recording:** selection while playing fades to the new buffer's
beginning (end in reverse); selecting an empty buffer stops playback. Fixed fresh
stereo recording accepts seconds or 4/4 bars and freezes its target at Record.
Early Stop retains only the written content as playable bounds. Grow/trim,
recording pause/resume, overdub and recording quantization are not implemented.
Takes remain in memory: there is no product export or project-recall UI yet.

The runtime used for recent validation is plugdata 0.9.4 nightly `98ae0f78b` /
Pd 0.56.3, with bundled ELSE/Cyclone objects. This is not a vanilla-Pd claim.
Keep the sibling patches together and use one application instance: shared global
names, multi-instance isolation, broader host settings and DAW lifecycle still
need qualification. Dependencies and the Monome suite connection are below.

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

Playback repairs include the earlier loop/selection collisions, Pause, hard Stop
and instant-reverse position jump. Very short natural loops and broader host
configurations remain unqualified; retained tests do not establish universally
click-free playback.

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
