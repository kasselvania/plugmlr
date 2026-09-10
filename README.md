# plugmlr

An MLR-style musical application for plugdata, with sample and live buffers,
slice playback, rate controls, and a mixer. Current work is to understand and
harden the original application, following its existing signal and control paths.

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
Stop cancels a pending restart. This is a fade through silence, not a seamless
crossfade between different buffers.

For a selected live buffer, **grow / sec / bars** sets the next recording's
length mode; **Amount** sets seconds or whole bars. Bars currently mean 4/4.
The target duration follows the current project tempo; existing audio does not
resize or stretch when tempo changes. These are configuration controls only:
audio recording, growing/trim operations, and recording quantization remain
unimplemented. **Clear live** erases the selected live buffer after stopping its
readers. Imported buffers are replaced through their load controls.

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
tape-direction slew remains separate work. The PR stays unmerged.

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
