# Take protection, persistence round trip and longer native run

Implementation base: PR #38, `566c8608e4d3244471db81118ed1939b471c3eca`.
Branch: `codex/take-protection-validation`. This is a draft review candidate.

## Changed behavior

`take-clear-control.pd_lua` replaces the single Clear receiver in `live_buffer.pd`.
The existing buffer still owns content, reader shutdown, its 20 ms fade and resize.
Unsaved Clear arms a five-second request; only a separate Discard confirms it.
Repeated Clear renews the request without clearing. Saved/empty buffers keep
one-step Clear. Recording or storage activity refuses both actions. Missing
metadata refuses the action. Content/status changes, Save, storage activity,
selection, view navigation, Cancel and expiry disarm the request.

Public per-buffer receiver: `N_l_b_delete_buffer`, where N is live slot 1..16.
Selectors are `bang` (Clear), `discard` and `cancel`. The player buttons use
its existing private delete route and `buffer-selection`, not another storage
path. `mlr-cancel-clear` cancels pending requests on any player selection;
`mlr-close-views` cancels them on navigation. Feedback names the affected slot.
There is no new audio processor, thread, buffer store or reader in this helper.

The focused player adds Discard/status and a readable persistence reminder.
Live Takes also says that saving the Pd patch does not save live audio.
Save WAV is still synchronous, stopped-instrument export. No close veto,
background writer, disk playback, crash recovery or project recall is implied.

## Actual runtime and UI

Native `/Applications/plugdata.app`: **0.9.4 nightly 98ae0f78b / Pd 0.56.3**.
Console startup also reports ELSE 1.0-rc14, Cyclone 0.9-4 and
pdlua 0.12.23 (lua 5.5 / luajit 5.1).
Executable SHA-256:
`86179a37e58e7a0f0436fc555f56ce41892e3f32ed19b4a3ba8f1cfe3c17476e`.
CoreAudio 8A input/output, 512 frames, 1x, limiter Off. Host rates below are
read from the actual capture, separately from file metadata. Native audio settings
were read and restored to 48 kHz. Tests disconnect the copied DAC and replace
hardware input with generated stereo; captures include the actual original mixer.
These are native engine recordings, not physical-output or Bitwig tests.

The native console was inspected after every run. The disconnected Grid's
`grid_not_attached` warning remains; no new Lua/object errors appeared during the
scores. The 70-second run showed Live 3 recording, then Saved and idle; capture
stop appeared in the console. Views showed the populated 60-second waveform.

Direct mouse attempts on the bottom Clear/Discard buttons did not produce a
state change through the UI tool. Existing Overview/Open navigation did respond.
This remains an **unverified button-interaction gate**, not accepted usability
or an established cause. The ordinary command route reached the same private
player receiver and displayed the correct armed/cleared states. The two
`clear-command-*.jpg` images document commands, not mouse acceptance.
`controls-click-unconfirmed.jpg` retains the earlier unsuccessful observation.
The Save reminder was moved left so the floating toolbar no longer covers it.

During restoration, console numeric arguments were initially sent as selectors
(`global-transport 0` etc.), producing `inlet: expected 'float' but got '0'`.
The commands were corrected to `global-transport float 0`, `mlr-debug float 0`
and `audio-1-out float 0.4`. The error screenshot was retained, the console was
cleared with errors still enabled, and subsequent native inspection showed no
new messages. This was a restoration-command error, not a test-score result.
Normal `mlr.pd` was reopened alone, DrumLoop.wav loaded into Sample 1, track 1
selected it at Level 0.4, and all playback/recording was left stopped.

## Failure exposed and localized repair

The first 48 kHz captures had nonzero audio and correct saved samples, but did
not keep looping. A stronger check found a held endpoint/DC after the first
pass. `startup48-failed/readers.wav.xz` confirms the original frame ramp advances
at one file frame per host frame, reaches 62336, and stays there with reader gain
1. Repeating the same score without changing source, host rate or DSP passes
after the first Stop (`startup48-repeat`). The earlier 44.1 kHz run also followed
Stop; the sample-rate change was not established as the cause.

Code trace: `pd loop_logic` requires `$0-slice-loop-allowed` for natural wraps.
`pd slice_policy` clears it while preparing a cut and restores it on commit or
Stop, but never initialized it. With no pending slice on first load, the loop
expression still had its default zero. **One loadbang now connects to the existing
message 1 in slice_policy.** Pending cut ownership, timing, DSP, interpolation,
reader handoff and Stop behavior are unchanged. `check_ui_overview.py` checks
this exact exception against the protected prior source.

The initial weak nonzero/zero-dropout checks are superseded. All retained
`checks.json` files were regenerated with expected-pitch and held-sample checks;
failures remain failures. No old capture was replaced by repaired audio.

## Numerical results

Every case retains its exact production-file hashes, fixture hash, score,
timestamped events, native float audio and results. A changed cosmetic footer is
identified by the differing player-panel hash in the earliest guard capture.
Only `repaired-*` and `long48` contain the first-wrap initialization.

| Retained run | Host / file Hz | Result |
|---|---|---|
| guards48 | 48000 / generated input | Clear-state tests pass; five advancing-audio checks fail on old initialization |
| record48, reopen48 | 48000 / 48000 | Export/reimport exact; held-sample and pitch checks fail |
| startup48-failed | 48000 / 48000 | Same failure, with passive reader taps |
| startup48-repeat | 48000 / 48000 | 13/13 after Stop, unchanged implementation |
| reopen441 | 44100 / 48000 | 13/13, prior implementation after Stop |
| repaired-record48 | 48000 / native input | **16/16**, first Play after fresh native launch |
| repaired-reopen48 | 48000 / 48000 | **13/13**, first Play after fresh native launch |
| repaired-reopen441 | 44100 / 48000 | **13/13**, first Play after fresh native launch |
| repaired-guards48 | 48000 / native input | **23/23**, including continuing audio during refused Clear |
| long48 | 48000 / 48000 | **20/20**, 70-second native run |

The five final cases pass **85 numerical checks**. Also executed: 18 Lua guard
behavior checks, all 55 root Pd connection checks, the UI/source preservation
check and `git diff --check`. Lua plumbing tests are not native/audio evidence.

Short recorded exports retain 62336 frames after a deliberate first index of 64.
Every exported float equals the corresponding recorded input frame in both
channels; no channel-relative offset is allowed. Reimported arrays equal the WAV
exactly, and the player/mixer preserves expected 337/811 Hz pitch at both host
rates (measured peaks about 337.113/810.997 Hz). Stop produces zero output.

The long Free take grows through capacities 2/4/8/16/32/60 seconds and finishes
with **2,880,000 stereo frames**, exactly 60 seconds. All exported samples equal
the actual captured input, including every growth boundary. Both lanes keep
changing throughout, the actual master matches the original weighted mixer,
all samples are finite, and no 64-frame zero dropout occurs across the complete
active mix interval, including view changes and audio transitions. The capture
stops at 70 seconds; a separately armed 72-second watchdog stops it and both
recorders/players if the score fails. No recording was left across an agent turn
without that automatic stop.

Maximum adjacent master steps are reported, not silently filtered out: about
0.149/0.00637 in the repaired 48 kHz tone check, 0.153/0.00694 at 44.1 kHz,
and 0.212/0.212 in the mixed drum/tone long run. The left test signal is a saw;
these values alone cannot identify audible clicks. There is no universal
click-free or performance claim.

The ten-channel passive reader WAV has the previously observed writesf header
under-count: its reported trailing bytes are retained and disclosed. The main
eight-channel captures have zero trailing bytes. Analyses use declared frames.

## Background observation and listening

During long48, Cmd-H was requested at 9.106 seconds; a native Finder Recents
window was opened with its focused list observed at 27.662 seconds, then closed
at 61.623 seconds. Plugdata readback then showed Playing and a populated waveform.
See `background-observation.json`. These app-specific snapshots do not establish
that plugdata remained hidden/occluded for the whole interval. **Strict background
window acceptance stays open**; the captured audio and recording continuity pass
across the entire interval of Finder interaction.

[Listen to the 24-second excerpt](long-run-listening.wav): actual post-master
channels from long48 seconds 16–40, with no normalization. Loop Apply is at clip
second 4, reverse at 10, forward at 18. `listening.json` records exact crop/hash.
**No new human listening report has been received.** Prior accepted musical
captures are separate. Direct hardware input, physical output, Grid gestures,
Bitwig lifecycle and unrestricted multi-instance acceptance were not retested.

## Repeat procedure

Use an otherwise idle native plugdata session, with user takes saved first.
The fixture instantiates the complete original application; never open it beside
another MLR copy with the same global buses. It does not drive the DAC.

1. Run `python3 tests/build_take_protection_check.py record`. Open
   `/tmp/plugmlr-take-check/check.pd` alone. Send `ui-check-run bang` in the native
   console. Inspect the UI/console and wait for automatic capture stop (8 seconds).
   Keep the capture, score, source.json, events.txt and roundtrip.wav before the
   next build. Close plugdata completely to remove RAM buffers.
2. Build `reopen`, then reopen plugdata and the fixture. Run the same command.
   Test 48 kHz and a fresh 44.1 kHz launch using the saved 48 kHz WAV. Do not press
   Stop or a slice before the score: that would mask the original initialization bug.
3. Build/run `guards` from a fresh launch (18 seconds). The final generated Live 4
   take supports the pending manual check: open Player 1, press Clear, observe the
   unsaved warning, then Discard within five seconds. Repeat Clear alone must leave
   the take intact. Test expiry/navigation and inspect the named slot feedback.
4. Build/run `long` (70 seconds; Free's message selector is `dynamic`). Record
   actual other-window interaction times and visual evidence of visibility/focus.
   Inspect the final Saved/idle state. No manual stop is required for the score.
5. With Python + NumPy, run `python tests/analyze_take_protection.py DIRECTORY`.
   It reads raw WAV or retained lossless `.wav.xz` archives. The directory needs
   its matching source/score/events and export files. Failed baseline runs should
   exit nonzero. Do not rename them as final successes.
6. Run `lua tests/check_take_clear.lua`, `python3 tests/check_ui_overview.py`,
   and the root Pd connection checks. Restore 48 kHz/512, normal mlr.pd alone,
   all transport/recorders stopped, and inspect the native console again.

Remain within this slice. The separately documented reader one-frame reference
audit, disk I/O alternatives, project recall and additional heads are future work.
