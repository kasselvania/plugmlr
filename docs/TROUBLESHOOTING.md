# Troubleshooting

Keep PlugData's console visible. The alpha intentionally exposes errors instead
of silently guessing around missing audio, stale device ownership, or unsupported
runtime state.

## No sound after pressing Play

Check these in order:

1. PlugData DSP is on and the intended output device is selected.
2. The Sample row reports **Loaded** with a non-zero duration.
3. The player is set to **Sample** and the loaded slot number.
4. The track **Level** is above zero and **Master** is at a safe audible value.
5. Press Play again after loading or replacing the buffer; replacement stops its
   readers deliberately.
6. Try a clearly audible stereo WAV. No demo file is shipped, and source silence,
   unusual channel layout, or very low level can be mistaken for a transport bug.
7. Look for object-creation, Lua, or file-read errors in the console.

If a clean restart is needed, save takes and patterns first, fully quit PlugData,
launch it normally, and reopen `mlr.pd`.

## A cut is waiting instead of playing

The player's **Quantize** option is probably enabled. Start the internal clock or
turn Quantize off. Stop, Pause, buffer selection, slice-mode changes, and some
Grid transitions cancel pending cuts.

## Controls behave like an older version

PlugData may cache Pd-Lua classes after a patch-only reload. Save live takes and
the pattern bank, fully quit PlugData, relaunch the application, and reopen
`mlr.pd`.

## Recording meters do not move

- `audio-in-subpatch.pd` must be open in the same PlugData process as `mlr.pd`.
- Enable the intended hardware input channels in PlugData's audio settings.
- Match **Host_L** and **Host_R** to those channel numbers.
- Set **Volume In** above zero and select **Local input bus 1**.
- Confirm the two recording-input meters move before enabling recording input.

The enable switch does not prove that a source exists; silence records silence.
Do not reconfigure the audio interface during an active take with DSP still on.

## Save WAV is refused

Finish the take and stop all players before saving. Save is synchronous and
writes only completed content. Check the console and row status for a file error,
cancelled chooser, active recording, or active playback refusal.

## A live take or pattern disappeared

Saving the Pd patch is not project persistence.

- Live audio must be saved with that row's **Save WAV** action.
- Patterns must be saved with **Save bank**.
- Pattern files do not contain audio, buffer assignments, tempo, gain, or a full
  project state.
- There is no autosave, quit warning, or crash recovery.

## `DrumLoop.wav` is missing

This is intentional. It came from a purchased sample pack and cannot be
redistributed. Use your own licensed stereo WAV. Historical evidence may still
name the private fixture, but neither it nor audio derived from it belongs in the
alpha archive.

## Grid problems

### No device appears

1. Confirm the submodule is initialized:

   ```sh
   git submodule status dependencies/monome
   ```

2. Verify the lease candidate:

   ```sh
   cd dependencies/monome
   ./tools/macos_serialosc_lease_candidate.sh verify
   ```

3. Confirm exactly one process owns UDP 12002:

   ```sh
   lsof -nP -iUDP:12002
   ```

4. Reconnect the Grid, return to plugmlr's Grid window, and click **rescan**.
5. Check the console for discovery or object-creation errors.

Do not run the Homebrew, stable project, and lease-candidate SerialOSC services
at the same time.

### Probe does not report free/available

Probe is read-only. A legacy destination, different lease owner, or displaced
state is an ownership boundary, not a prompt to keep clicking Claim.

Release the Grid from its actual owner, then select and probe again. plugmlr has
no automatic takeover and does not silently displace another application.

### Claim never reaches connected

- Confirm the selected serial ID is the intended physical Grid.
- Confirm probe succeeded immediately before claim.
- Verify candidate revision `7187832c349202b1a94a9b10080ae57d40069946`.
- Read the console for `unsupported`, `claimed`, `displaced`, callback-bind, or
  readback errors.
- Do not equate visible LEDs with verified ownership; **Session connected** is
  required.

### Grid remains lit after release or a crash

After a normal release, wait for the verified darkening/readback sequence. After
a client crash, the lease candidate should expire the abandoned lease within its
six-second policy, darken the device, and return its destination to port 0.

If it remains lit, do not assume ownership is free. Verify the service, use the
companion's non-mutating probe, and record the console and daemon state before
restarting anything:

```sh
cd dependencies/monome
./tools/macos_serialosc_lease_candidate.sh status
python3 tools/live_serialosc_lease.py probe
```

### Grid presses work but the screen does not change

PLAY/CUT can request a plugmlr view, but this PlugData build cannot always bring
the root tab in front of another tab. Select the `mlr.pd` tab manually. This does
not by itself mean Grid input or ownership failed.

## Unsupported-environment symptoms

The following need independent qualification rather than a troubleshooting
workaround:

- Intel macOS, Windows, Linux, or SteamOS;
- PlugData stable 0.9.3 or an arbitrary newer nightly;
- AU/VST3/CLAP/LV2 or DAW-hosted use;
- more than one plugmlr instance;
- other Grid layouts or Arc as a plugmlr controller; and
- Rubber Band stretch or pitch rendering.

## Report a useful alpha problem

Include:

- plugmlr commit (`git rev-parse HEAD`);
- submodule commit (`git submodule status dependencies/monome`);
- PlugData version/build and executable SHA-256;
- macOS version, audio interface, sample rate, and device buffer size;
- whether the failure used sample playback, recording, or Grid;
- for Grid issues, the stable serial ID, candidate revision, Session state, and
  whether the surface was dark before the attempt;
- exact steps from a fresh PlugData launch; and
- relevant console text without private file paths or purchased audio.

State what was actually observed. A passing static check is not evidence that
audio sounded correct or that physical hardware completed a lifecycle.
