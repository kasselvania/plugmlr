# User guide

This guide covers the release-facing workflows in the alpha source line. It is
not a promise of behavior outside the environment in
[ALPHA_RELEASE.md](ALPHA_RELEASE.md).

## The main screen

`mlr.pd` opens a sixteen-track overview. Each row shows its focused buffer,
transport state, position, and level.

- **Open** shows that track's player.
- **Sample bank** manages imported files shared by all tracks.
- **Live takes / Finish** shows recording destinations and completed takes.
- **Grid** opens device selection and ownership controls.
- **Overview** returns from another view without stopping playback.
- **Master** controls the final output level.
- **Debug** enables routine console messages; errors remain visible regardless.

Slots shown on the overview are readouts. Change a track's Sample/Live source
and slot from its focused player or from the experimental Grid BUFFER page.

## Samples and shared buffers

There are sixteen Sample slots. Load from **Sample bank**, or choose **Sample**
and a slot in a focused player and use **Load sample**.

Replacing a slot stops every reader of that shared buffer before changing its
arrays. It restores that buffer's full-sample loop and start position, but keeps
the player's speed, direction, glide, quantization, Fit, and Beat Reset settings.
Press Play when ready. Loading a numbered bank row may focus the corresponding
track, but sample slots and playback tracks remain separate identities.

More than one track may play the same shared buffer. **Prev/Next** skips empty
slots within the currently selected Sample or Live bank.

## Playback, slices, and loops

Each player provides Play/Pause, hard Stop, forward/reverse, five speed presets,
speed glide, sixteen whole-content slices, and an editable loop window.

- With **Quantize** off, a slice starts immediately.
- With **Quantize** on, it waits for the selected internal-clock division.
- Stop, Pause, buffer changes, mode changes, and grid changes cancel pending
  quantized cuts.
- Entering a slice restores the full usable content before selecting its cut.
- Start and End update the live loop immediately. Move shifts both edges while
  preserving loop length.

Very short loops can expose sharp transitions. Accepted loop lengths are not a
promise of click-free playback for every source.

## Clock, Beat Reset, and tempo fit

Select the internal clock, choose 30–320 BPM, and enable **Run**. Clock Run
controls ticks; it does not start or stop a player.

Each player can set **Reset every** to Off, 1 beat, 2 beats, 1 bar, 2 bars,
4 bars, or 8 bars. A reset restores full-sample bounds and jumps at the next
matching shared-clock boundary. A stopped or paused track stays silent.

For **Fit**, enter the full sample's quarter-note length from 1–64 beats and
enable Fit. At the 1× preset, plugmlr adjusts tape rate to fit that duration to
the shared BPM; the other speed presets multiply the result. This changes pitch
and can drift during a speed glide. It is not phase locking or offline stretch.

## Edit an imported sample — experimental

Open a player using a Sample buffer and click **Edit sample** on its waveform.
The editor can:

- set a staged selection using draggable edges or Start/End seconds;
- zoom, scroll, and fit the selection;
- audition the selection through the current player;
- apply it as that player's loop;
- trim the shared buffer's usable range; and
- restore the original in-memory range.

Trim stops readers of the shared buffer and makes all sixteen slices divide the
new usable range. It does not change the source file, but it is not retained by
saving the Pd patch. Edited-sample export and project recall are not included.
This editor has native checks but remains an experimental alpha surface.

## Record a live take

The supported recording lane is PlugData standalone at 48 kHz.

1. Keep one `mlr.pd` open and open `audio-in-subpatch.pd` in the **same PlugData
   process**. Its local bus does not cross application processes.
2. In PlugData's audio settings, select the interface and enable the desired
   input channels.
3. In `audio-in-subpatch.pd`, set **Host_L** and **Host_R** to those channel
   numbers, set **Volume In** (1 is unity), and choose **Local input bus 1**.
   Leave Monitor/Mix at 0 unless direct monitoring is intentional.
4. In `mlr.pd`, confirm both recording-input meters move, then enable
   **Enable_recording_input**. The switch cannot detect a silent or disconnected
   source; the meters are the check.
5. Open a player, select **Live** and an empty slot, then choose a fixed seconds,
   fixed bars, or **Free** take. Free recording has a 60-second cap.
6. Click **Record live**. Stop finishes a Free take or ends a fixed take early.
   Recording does not automatically begin playback.

Recording is forward at 1× regardless of playback speed and direction. There is
no overdub, recording pause/resume, or quantized record launch.

## Save or clear a take

Stop all players, open **Live takes / Finish**, and use **Save WAV** on the
desired row. A finished take is written synchronously as 32-bit float stereo WAV
at its recorded rate. Wait for success before resuming performance.

Clearing an unsaved take requires a separate **Discard** within five seconds;
repeatedly pressing Clear does not confirm it. A saved or empty buffer clears in
one step. Closing PlugData, a crash, or saving the Pd patch does not preserve an
unsaved take.

## Performance patterns

Grid top-row keys 5–12 are eight free-time pattern slots. On-screen changes to
the same captured controls are also included.

1. Press an empty slot to begin recording immediately.
2. Perform cuts, speed/direction changes, or track transport actions.
3. Press the slot again to finish and begin looping.
4. Press again to stop; press once more to restart.
5. Hold ALT and press a pattern slot to clear only that slot.

Only one pattern records or plays at a time. Patterns capture accepted control
actions, not audio, loops, buffer selection, Fit/glide settings, gain, or tempo.
They replay against each track's current buffer. Each slot is limited to 4096
actions or five minutes, with a 10 ms minimum loop.

Use **Save bank** beneath the overview to write all eight slots to one
`.plugmlr-patterns` file. **Load bank** reads one back, with an explicit replace
step when current edits are unsaved. Pattern banks do not contain audio or a
complete project.

## End a session safely

Before closing or updating PlugData:

1. save every important live take as WAV;
2. save the pattern bank if it matters;
3. release any claimed Grid and confirm it goes dark; and
4. fully quit PlugData before opening changed Lua code.

See [Known issues](KNOWN_ISSUES.md) for the complete persistence and support
boundary.
