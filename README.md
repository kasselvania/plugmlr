# plugmlr

An MLR-style musical application for plugdata, with sample and live buffers,
slice playback, rate controls, and a mixer. Current work is to understand and
harden the original application, following its existing signal and control paths.

The runnable entry point is **[mlr.pd](mlr.pd)**. Sample 1 has been heard through
player/channel 1 and the mixer. Playback currently cuts out during a loop, stays
silent for another pass, then returns. See [the observation record](docs/STATUS.md)
for what was actually checked and what remains untested.

## Run the original application

1. Open this checkout's `mlr.pd` in plugdata. Keep its sibling patches together.
2. Enable DSP and open plugdata's console, with both messages and errors visible.
3. Use **Sample 1 Load** to choose the included `DrumLoop.wav` or a stereo file.
4. Open `pd arrays-samples`, then `sample-data 1`, to inspect the loaded arrays.
   Open `sample_player_rebuild 1`; its buffer selection should show
   `sample_buffer`, `1` after loading.
5. Press **Play/Pause** in that player. Open `pd mixer` and raise **track 1 volume**
   and **Master Volume** as needed, starting quietly. The playbar should move;
   the looping fault above is still present.

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
