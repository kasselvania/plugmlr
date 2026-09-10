# plugmlr

An MLR-style musical application for plugdata, with sample and live buffers,
slice playback, rate controls, and a mixer. Current work is to understand and
harden the original application, following its existing signal and control paths.

The musical direction is free-form tape manipulation, growing toward an
mlre-inspired community instrument. The immediate behavior to finish is instant
reverse or an audible tape slew, with timing drift allowed. The
[tape reference catalogue and next work](docs/STATUS.md#free-form-tape-direction)
separate that decision from functions already tested.

The runnable entry point is **[mlr.pd](mlr.pd)**. Small repairs now restore both
reader turns and bidirectional looping in the existing player. Direction Change
reverses playback; reverse wraps return to the region end. The current native
checks also cover reverse startup and repeated direction commands. See
[the results and remaining limits](docs/STATUS.md#reverse-playback-and-loop-boundaries):
reverse loop timing, speed/slew ordering, transition quality, and stereo ordering
still need work. The earlier “solid playback” listening report applies to the
reader-handoff repair; listening acceptance for this direction repair is open.

The [speed-control candidate](docs/STATUS.md#speed-control-and-crossover-follow-up)
repairs zero-duration selection and orders rate-slew updates. It has not yet
passed native audio validation. The crossover review found that both readers
receive the same position jump during a fade; independent outgoing-reader
motion and direction slew remain unfinished.

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
