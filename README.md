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

**Frontend:** `mlr.pd` opens a stacked 16-track overview with Play/Pause, Stop,
selected buffer/slot, transport state, position and Level. Master is on the main
screen. Click a track's **Open** button for its focused player, **Sample bank**
for imported files, or **Live takes / Finish** for recording destinations.
**Overview** returns from a focused view without stopping playback. Slots on
the overview are readouts; choose the buffer type and slot inside the player.
This UI is a review candidate: [screenshots, checks and procedure](docs/evidence/ui-overview/observations.md).

**Waveform and sample identity:** the focused player shows separate L/R waveforms,
16 whole-content slice divisions, the committed loop range and a moving cursor.
The preview is built once per buffer when requested; recording gets a waveform
when finished. **Prev/Next** skips empty slots within the selected bank. The
Sample bank shows the last successfully loaded filename. **Debug** on the main
screen enables routine console prints; load/record errors remain visible.

**Load from a player:** select **Sample** and a **Slot**, then click **Load sample**
next to Slot. The file replaces that shared slot and restores the full-sample loop
and start position; speed, reverse, glide, quantization, Fit and Beat Reset stay as
set. Cancel leaves the buffer alone. Players using the replaced slot stop before
loading; press Play when ready. The button is hidden for Live buffers.

**Experimental stretch / tune:** in **Edit sample**, select Start/End, set
**Duration_x** (2 doubles length; 0.5 halves it) and **Pitch_semitones** (+12 is
one octave up), then **Render copy**. When ready, **Load copy** selects an unused
Sample slot; use **Audition loop** above to hear it through the existing player.
Original audio and player speed/reverse controls are preserved. For an unshifted
comparison, use player speed 1 and turn off Tempo Fit. Copies and render manifests
remain in `renders/` beside this patch; load their WAVs normally in later sessions.
This optional Mac experiment requires Python 3 and Rubber Band CLI (already
installed on the development Mac); opening MLR does not launch or require them.
The source must be an unchanged, accessible stereo PCM/float WAV. Duration range
0.25–4x; pitch ±24 semitones. Background rendering does not resize any audio array;
**Load copy** uses the existing synchronous loader and may briefly stall audio.
After updating, save patterns/live takes and fully restart plugdata once because
Pd-Lua caches classes. Then open `mlr.pd`, load a sample and use its editor.

**Edit an imported sample:** open its player and click **Edit sample** on the
waveform. The player waveform now has a seconds ruler and separate `S1–S16`
slice labels. In the editor, drag either selection edge or enter Start/End in
seconds; zoom, scroll, or Fit selection for detail. **Audition loop** uses the
current player and its speed/direction; **Stop** ends it. **Set player loop**
applies the selection without trimming the sample.

**Trim sample** changes the shared buffer's usable range and stops its readers.
All 16 slices then divide that range. **Restore original** restores the full
loaded sample. Both channels and the original arrays remain intact in memory;
no source file is changed. Times retain their coordinates in the original file,
so trimming 3–11 seconds gives an 8-second sample with ruler endpoints 3 and 11.
Trim is not saved by saving the Pd patch. Export of an edited imported sample,
project recall and offline tuning/stretching are not included in this slice.
[Editor checks and capture](docs/evidence/sample-editor/observations.md).

**Save a take:** Finish recording, stop all players, open **Live takes / Finish**,
and click **Save WAV** on the desired buffer row. Choose a destination. Feedback
reports success or refusal; the row changes to Saved. Export includes only written
stereo frames as 32-bit float WAV at the take's recorded rate, without normalizing.
Playback stays in RAM. This synchronous export requires a stopped instrument;
background saving, disk playback and project recall remain future work.
[Native checks, screenshots and listening file](docs/evidence/waveform-take-tools/observations.md).

**Protecting takes:** Clear on an unsaved live buffer asks for a separate
**Discard** within five seconds; repeated Clear never confirms. Switching buffers,
changing views, saving or changing the take cancels that request. Saved/empty
buffers retain one-step Clear; recording/storage activity refuses it. **Save WAV
before closing**: saving the Pd patch does not save live audio, and this patch
cannot veto closing or recover a crashed session.
[Take-protection and fresh-launch evidence](docs/evidence/take-protection/observations.md).

**Player view:** click **Open** on track 1.
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
immediate. Default is unchecked with a 1/16-note grid. Scripted `<track>-quantizer` messages keep the legacy convention:
1 = immediate, 0 = quantized. Stop/Pause, buffer selection, mode and grid changes
cancel pending keys. Any committed slice restores whole-content loop bounds.

**Live loops:** Start_s and End_s now take effect as you edit them; there is no
Apply button. **Move_s** sets the window's start while moving both edges together,
preserving length. Edges clamp at each other and at the usable sample boundaries.
The player keeps its running position inside the window, or wraps into it when
outside. Paused/stopped edits stay silent. A slice key returns to the usual
whole-content cuts, with the selected quantization. Controller messages use
`<track>-loop-window start|end|move <seconds>` (absolute source-file seconds).
This is separate from the sample editor's staged selection and shared trim.
There is no one-slice minimum, but one-frame loops expose sharp transitions in
the current crossover engine. See the [native tests and limits](docs/evidence/live-loop-window/observations.md).

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
Takes remain in memory until closing; use Save WAV to retain finished audio.
There is no full project-recall UI yet.

The runtime used for recent validation is plugdata 0.9.4 nightly `98ae0f78b` /
Pd 0.56.3, with bundled ELSE/Cyclone objects. This is not a vanilla-Pd claim.
Keep the sibling patches together and use one application instance: shared global
names prevent isolated copies in one Pd environment. Playback now has bounded
44.1/48 kHz and file/host-mismatch evidence, plus a two-player shared-buffer
comparison. Bitwig audio/clock and plugin-instance isolation remain open. See
[host validation](docs/STATUS.md#host-and-instance-validation-review-candidate). Dependencies and the Monome suite connection are below.

## Connect a Grid

**PLAY and CUT:** the first two top-row keys now select PLAY and CUT. CUT is
selected on startup. Both pages cover Players 1–6; the current page is brighter.
The layout follows the [pinned mlre reference](docs/STATUS.md#mlre-control-reference-and-next-grid-slice--2026-09-11),
with a PLAY name because recording controls are not active on this page yet.

On **PLAY**, each of the six rows below navigation controls its corresponding player.
Count columns from the left, starting at 1:

| Columns | Action / feedback |
| --- | --- |
| 3–6 | Select the focused track without playing or opening a window. The selected block is brighter. |
| 8 | Reverse. Bright = reverse; dim = forward. |
| 10–14 | ¼, ½, 1, 2, 4× presets. The chosen preset is brighter; existing glide and tempo Fit still apply. |
| 16 | Play/Pause/Resume. Bright = playing, medium = paused, dim = stopped/ready, dark = empty or switching. |
| Bottom row | The focused player's 16 cuts, loop range and moving playhead, with the same ALT/MOD/80 ms hold gestures as CUT. |

Other PLAY-row keys are inactive. Top-row keys 5–12 are the eight pattern slots. ALT/MOD
plus PLAY-row controls do nothing; those modifiers still work on the bottom cut
strip. Changing page or explicitly selecting PLAY focus cancels unfinished held
loop gestures. Release old held keys before using them in the new context.
Page changes preserve playback, buffer selection and already queued musical cuts.
Grid focus alone stays screen-silent. Press **CUT** (top-row key 2) to open the
focused player panel, including when CUT is already selected. **PLAY** closes
player panels using the existing Overview action. In this plugdata build it
cannot force the root home tab forward when another tab is selected; select
`mlr.pd` on screen in that case. A dedicated home view is under discussion.
Players 7–16 remain accessible on screen.

**Update:** fully quit and reopen plugdata, then reopen `mlr.pd`, to load changed
Lua controls. Save any live takes first. The existing device select/Probe/Claim
workflow is unchanged. This checkpoint has native gesture, six-player command
readback and LED-message checks; the user has accepted physical PLAY/CUT operation. The new screen-following
behavior still needs a physical playtest.
[Controls, results and repeat procedure](docs/evidence/grid-pages/observations.md).

The CUT gesture reference follows the [pinned mlre manual and adaptation map](docs/STATUS.md#mlre-control-reference-and-next-grid-slice--2026-09-11).
This is a design reference; the current patch implements the controls below.

Initialize the pinned connection package after cloning or updating:
`git submodule update --init --recursive`.

Open `mlr.pd` and click **Grid**. Choose the device, click **probe**,
then **claim** when the console reports it free. Session shows `connected` only
following the package's verified lease. Click **release** before closing or
moving the Grid to another application. Discovery does not auto-claim; an existing
owner is not automatically displaced. Details and failures appear in the console.

The adapter retains the original musical track routes and translates LED messages
into the package's cached controls. CUT now shows playback/loop feedback on all
six track rows. Ordinary slices start or resume the selected cell; quantized slices
wait for a matching clock tick. Hardware-global intensity below 15 remains
unsupported. Connection details: [adapter checkpoint](docs/STATUS.md#grid-adapter-review-candidate--2026-09-11).

### BUFFER: select a track’s audio from the Grid

Hold **ALT (top-right key 16)** and press **top-row key 15 (Q)**, then release ALT.
This borrows mlre’s ALT+Q tape-page navigation; our page selects independent
sample/live buffer slots, not regions/splices within a tape.

| BUFFER area | Action |
| --- | --- |
| Top row | PLAY (1), CUT (2), patterns (5–12), MOD (14), Q/BUFFER (15), ALT (16). BUFFER lights key 15. |
| Rows 2–7 | Tracks 1–6. Press column 1–16 to assign that buffer slot to the row’s track. |
| Bottom-left (1) | View imported **Sample** slots. |
| Bottom-right (16) | View **Live** slots, including empty recording destinations. |

The bright bottom key identifies the viewed bank. Changing banks only changes
what you see. Slot lights are faint when empty, dim when populated, and brightest
for the track’s committed selection. A switching track briefly dims its previous
selection. A track assigned to the other bank has no selected cell in this view.
Selections made on screen update the same lights.

A slot press focuses its track without opening a window; **CUT** then opens that
player. Release held keys when changing bank/page. ALT/MOD suppress slot selection.
The existing selection behavior applies: playing tracks restart at the new buffer’s
direction-aware edge; empty targets stop; stopped/paused tracks do not launch.
Selecting an empty Live slot does **not** start recording. No Record/Clear/file
loading controls or pattern capture of buffer assignments are added here.

Save live takes **and the pattern bank**, fully quit/reopen plugdata, then reopen
`mlr.pd` for this update. The currently open session is left intact. Native control
checks passed; physical BUFFER-page usability remains to be tested.
[Evidence and repeat procedure](docs/evidence/grid-buffer/observations.md).

### Eight pattern slots: record and switch performances

After fully quitting/reopening plugdata and reopening `mlr.pd`, **top-row keys 5–12**
are Patterns 1–8 on PLAY, CUT and BUFFER. Save any live audio before quitting.

1. Press a dim pattern key to **start recording now** (flashing). Any wait before your
   first action is part of the phrase.
2. Play cuts, change speed/direction, or Play/Pause/Stop Players 1–6.
3. Press that same key again to finish and loop (lit). The wait after your last action is
   also retained. With no actions, the slot returns empty.
4. Press again to stop the pattern (medium); press again to restart it.
5. Hold **ALT + a pattern key** to clear only that slot. This does not erase audio.

Only one pattern records or plays at a time. Press another slot to switch
immediately: an unfinished recording is finished and kept, a populated destination
starts from its timeline beginning, and an empty destination starts recording.
Each slot retains its own duration, actions and initial controls. Clearing another
slot does not interrupt the active one. Switching does not implicitly stop the tape.

Pattern Stop cancels future pattern actions; the tracks keep their current
transport state. Use their transport controls to stop audio. Disconnecting Grid
or switching DSP off stops the pattern; reconnecting does not launch it.
You can continue playing live over a running pattern.

At each lap, participating tracks restore their speed preset and direction from
when you pressed Record. The tape keeps its position and transport state until
an actual recorded cut or transport action changes it. Speed changes use the
current glide settings. A leading gap means **no pattern actions**, not forced silence.
If you want a retrigger at the beginning, record a cut there.

Cuts are captured when accepted by the player, including any quantization wait,
and replay without a second quantization. Transport records resolved actions,
so a cancelled queued Play is not stored. On-screen actions on these same controls
are included. The pattern follows each track's current buffer; changing buffers
changes the material it plays.

This is a free-time performance timeline: no later tempo-follow or bar rounding.
It does not record loop gestures, buffer selection, Fit/glide changes, gain or audio.
Unsaved patterns are lost on closing. Per-slot limits: 4096 actions / five minutes;
reaching either limit stops recording and retains the events. Minimum loop is 10 ms.
[Native checks and remaining limits](docs/evidence/pattern-bank/observations.md).

### Save and load the pattern bank

Use **Save bank** beneath the main overview's track list to save all eight slots
in one `.plugmlr-patterns` file. The extension is added if omitted. Finish any
pattern recording first. The status line reports success or a file error.

**Load bank** reads all eight slots. If there are unsaved edits, choose **Save bank**
to keep them, then **Replace bank** to install the selected file; **Cancel load**
keeps the current bank. Recording or clearing a slot cancels a pending replacement.
Loaded patterns are stopped: press their Grid slot to play. Tracks already playing
keep moving; loading does not send player transport commands.

Files contain timing, cuts, transport, direction/speed events and participating
tracks' initial speed/direction. They do **not** contain audio, buffer assignments,
tempo, glide/Fit settings or project state. Reload your audio separately; patterns
act on the tracks' current buffers. Saving the Pd patch alone does not save patterns.
There is no autosave or quit warning. File I/O is synchronous; this is not a guarantee
against slow-disk interruptions during performance.

[Persistence checks and native UI evidence](docs/evidence/pattern-files/observations.md).

### Grid quick reference

Physical key numbers count from 1. CUT rows 2–7 control Players 1–6.
The preceding physical musical acceptance covers Players 1/2; the user has also accepted the six-row PLAY/CUT layout. Top-row key 2 selects
CUT and opens the focused player panel.

| Action | Gesture / meaning |
| --- | --- |
| Start, pause, resume | Hold **ALT**, top-right key 16, then press a track-row key. |
| Cut | Press a track-row key without modifiers. Starts or resumes at that slice. Cuts follow that player's Quantize setting. |
| Loop a range | Hold two track keys on the same row together for at least **80 ms**, then release either. Both cells are included. Each key-down still makes an ordinary cut. |
| Loop one cell | Hold **MOD**, top-row key 14 (third from right), then press a track key. Commits on press; release does not retrigger. |
| Leave a smaller loop | Make an ordinary cut; it restores full-content bounds. |
| Read the LEDs | Dim cells show the committed smaller loop; the brighter moving cell is playback. Pause/Stop retain the dim range. |
| Select Grid focus | CUT follows the last touched track. PLAY columns 3–6 select without playing. Neither opens a window. |
| Hard Stop | Use Stop on the player panel. ALT uses Pause/Resume. |

ALT transport and loop commits act immediately; ordinary cuts retain per-player
quantization. Shorter two-key overlaps never commit a loop; they do not delay
or suppress the slice presses. The threshold is `LOOP_HOLD_MS` in
`grid-cut-keys.pd_lua`, kept in one place for feel adjustments.
The 80 ms hold begins when the second key goes down. That second press also
cuts immediately; the hold threshold only qualifies loop selection. A stopped
clock leaves quantized cuts waiting for a matching tick. Fully restart plugdata
after updating Lua controls.
Grid loop commits preserve a running position inside the new range
and wrap immediately if outside it. On-screen Start/End/Move use that same live
behavior; Full sample and explicit loop-region lists retain their entry jump.
ALT wins when both modifiers are held. ALT/MOD presses, Stop/Pause, buffer changes
and disconnect cancel unfinished two-key gestures; a third held track key cancels
the pair until all row keys are released. Full content has no dim background.

The preceding CUT gestures have physical acceptance; the combined two-lane capture
also has numerical and listening acceptance. The new page layout is not yet physically accepted. See the [current checkpoint](docs/STATUS.md).
Grid audio-recording controls remain reserved. PLAY and its focused bottom
cut strip are described above.

## Run the original application

1. Open this checkout's `mlr.pd` in plugdata. Keep its sibling patches together.
2. Enable DSP and open plugdata's console, with messages and errors visible.
3. Click **Sample bank**, then **Load** beside Sample 1. Choose the included
   `DrumLoop.wav` or a stereo file. Check **Loaded** and its duration in seconds.
4. Click **Overview**, then **Open** on track 1. Its source should show
   **Sample**, slot **1**. Cuts/loops, timing, speed and recording are grouped here.
5. Return to **Overview**. Raise track 1's **Level** cautiously and check
   **Master** (default 0.75). Press **Play / pause**. The state and position marker
   follow the original player. Press again to Pause; **Stop** resets its position.
   The included drum file has about half a second of silence at its end.

To share a buffer, open another track and choose the same **Sample** slot.
To audition a different buffer through track 1, load Sample 2 in the bank and
choose **Sample**, **2** in player 1. Loading still explicitly selects a sample
in its same-numbered track; passive metadata updates do not redirect other
players. Loading/clearing stops readers of that buffer before changing arrays.
Press Play after a load. Bank slots, live buffers and playback tracks are
separate identities, even where the old default routing uses matching numbers.

Original wiring remains below the overview at **ORIGINAL ENGINE WIRING**.
Open `pd arrays-samples` and `sample-data 1` there to inspect the arrays; playback
logic remains in `sample_player_rebuild.pd`. Views send existing commands and
show existing state; they do not instantiate additional players.

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
4. Click track 1’s **Open**. Choose **Live** and an empty slot. Under
   **NEXT TAKE**, select **sec** or **bars** and set **Fixed amount**,
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
   an active writer. Open **Live takes / Finish** on the main window to see
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

## Separate stretch compatibility experiment

The [offline-stretch workbench](experiments/offline-stretch/README.md) investigates
bundled phase-vocoder rendering, an optional external processor and threaded file
loading. It does not modify the sample editor or application engine. Read its
measured limitations before treating it as an editing feature.
