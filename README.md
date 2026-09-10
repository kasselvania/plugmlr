# plugmlr

An MLR-style musical application for plugdata, with sample and live buffers,
slice playback, rate controls, and a mixer. Current work is to understand and
harden the original application, following its existing signal and control paths.

The runnable entry point is **[mlr.pd](mlr.pd)**. The current repair initializes
the second reader and coordinates delayed shutdown in the existing player.
Fresh Sample 1 playback now continues across both readers' loop turns; the user
reported “solid playback.” See [the repair and evidence](docs/STATUS.md#reader-initialization-and-shutdown-repair)
for the native checks and remaining direction, transition, and channel-order gaps.

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

For the focused handoff check, use the [repeatable procedure](docs/STATUS.md#repeat-the-handoff-check)
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

Alternative and historical patches remain alongside the entry point. Their names
do not establish which behavior works. The rejected shared-playback rewrite is
preserved separately and is not the current application; details are in STATUS.
