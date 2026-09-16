# Recording continuity: native observations, 2026-09-11

This continues the bounded Free recovery on PR #34. It does not implement
recording direction/speed, overdub or Grid recording. Base main:
`29ab51e653eded9db9c5aa09850ec4a1352d97e9`; follow-up started from
`f3c22f403d9c5a9aa751f78901350331b8ce9daa`.

## Runtime and capture boundary

Actual headful Mac **plugdata 0.9.4 nightly `98ae0f78b` / Pd 0.56.3**, CoreAudio
**8A**, **48,000 Hz**, **512 device frames**, **1× oversampling**, output 0.8,
limiter Off. The application binary and production source hashes are in
[runtime-and-sources.json](runtime-and-sources.json). Settings were read back in
the native UI: [audio](audio-settings.png), [oversampling](dsp-options.png).

`tests/build_record_session_check.py` uses the repository's `DrumLoop.wav`,
resampled to 48 kHz: one longer input file and a one-second loop for the other lane.
The observed player is the **verbatim production file plus appended controls and
passive taps**. All sibling abstractions resolve to this checkout through local
temporary symlinks. The actual sample/live-buffer and mixer components are loaded.
The two mixer outputs are summed with a common 0.75 multiplier; this is not the
complete `mlr.pd` inline mixer/master, device output, Bitwig, or a two-application test.
There is no DAC, hardware input, Grid claim, or companion in the audio fixture.

The 10 captured channels are: input L/R, player A L/R, player B L/R, combined
post-mixer L/R, logical position A/B. **Do not audition the 10-channel capture**:
its last two channels contain frame numbers. Use [listening.wav](listening.wav),
which contains only the combined stereo mix converted to 16-bit PCM without
normalization. The archived `.wav.gz` files preserve original native file bytes.

Each test arms its independent 16-second watchdog **before** starting capture;
the score finishes at 14 seconds. Both paths stop captures, source playback,
recording and both players, then export the live arrays and event log. Completion
was read in the actual console after each run. No capture depended on another
agent turn. plugdata was left at [Home](final-home.png), DSP On, with no patch open.

The native 10-channel WAV header declares 164 fewer frames than its physical
payload for run/zero/boundary, and 158 fewer for DSP. The analyzer reads declared
audio, reports trailing bytes, and does not repair the originals. All tested
transitions finish more than a second before that final 3.3–3.4 ms. The stereo
array exports have no trailing bytes. The cause of this capture-header discrepancy
was not isolated; it is not evidence of missing frames in the buffer writer.

## Executed cases and numerical results

| Case / retained report | Observed result |
| --- | --- |
| [run](run-results.json) | 21/21 recorder and 10/10 playback checks. Live 1 records 3.1 s while Free grows through 2/4 s capacity. Live 2 records 2.8 s into its fixed 4 s capacity. Browsing, playback direction/speed and next-take length edits leave capture unchanged. Finish 1 leaves take 2 recording. |
| [dsp](dsp-results.json) | 12/12 recorder checks. DSP Off finishes exactly 57,600 frames after 1.2 s of recording; DSP On does not resume. Loaded is reported at 2.503 s and on the 3.2 s query. |
| [zero](zero-results.json) | 13/13 recorder checks. Same-tick Start/Stop stays Empty; Start during 3 ms cleanup is refused with Buffer_busy; a later Start succeeds and records 52,800 frames. |
| [boundary](boundary-results.json) | **Playback FAIL:** 21/21 recorder checks, 7/10 playback checks. Reverse at the exact first loop boundary leaves motion stuck; all three later speed checks fail. |
| [boundary-initial](boundary-initial-results.json) | The original failing run before passive boundary taps were added. Same three playback failures. Retained rather than overwritten by the successful comparison. |

All written stereo samples equal the actual captured input, including growth
windows and the final written frame. Each buffer uses **one common stereo offset**
(normally Start +64 frames), not independent channel realignment. All retained
signal values are finite, and unused array tails are zero.

In the successful run, player B's repeated one-second waveform is bit-identical
before, during and after growth and player A's controls. A loops the 148,800-frame
written region, not the 192,000-frame capacity. Its measured median frame steps
are +1, -1, -0.5 and -2; no exact stereo-zero dropout occurs in its playing window.
Both players and the mixer are silent after the intentional Stop at 12.5 s.

The mixed output equals `0.75 * (0.4*A + 0.3*B)` outside the production mixers'
intentional 5 ms opening fades. The maximum residual over **all** samples,
including those fades, is 0.0005421. The post-mixer peak is 0.507315; maximum
adjacent-sample change is 0.317553. That last figure includes the drum source's
own transients; it does not establish click audibility or universal click freedom.

## Exact-boundary failure and source trace

In the failing score, recording finishes at 4.4 s and playback starts at 4.9 s.
At 8 s the natural forward wrap and Reverse share a logical timestamp. The
passive trace records:

```
8000 trace1 boundary-entry 0;
8000 trace1 target 0 148800 3100;
8000 trace1 direction 1;
8000 trace1 boundary-entry 0.00404825;
8000 trace1 detector-direction 2;
8000 trace1 entry 148800;
8000 trace1 target 0.00404825 0 8.43385e-05;
```

The resulting audio and position hold at frame zero through the later speed
commands. Moving Reverse to 8.3 s produces a normal natural wrap followed by
working reverse/.5x/2x playback; the successful score is otherwise identical.

`sample_player_rebuild.pd`, `pd loop_logic`, has one `edge~` after its combined
forward/reverse endpoint expression. The observed handoff is consistent with
that condition never dropping between the forward boundary and the near-zero
reverse ramp, leaving no fresh rising edge. The existing speed endpoint retry
then waits for the loop handoff. This is a source-supported repair hypothesis
with a native reproduction, **not a completed fix**. The player source is unchanged
by this follow-up. Keep this test failing until the repair is validated.

## Native UI and console, separate from audio measurements

- The first instrumented-player load could not locate sibling helpers. The
  visible console reported `couldn't create`; no recording was started. The
  fixture was closed and dependency paths corrected before the retained captures.
- [Two active rows](run-active.png) show separate elapsed values and 60/4 s
  frozen limits. [DSP active](dsp-active.png) shows actual progress, followed by
  idle at completion. The public buffer-addressed Finish path used by the rows
  was exercised by the timed score. The physical GUI Finish was checked while idle.
- [MLR entry](mlr-entry.png) and [take view](mlr-takes.png) show the final button
  location and a successful native click opening the correct panel. Its first
  location overlapped sample labels; a location below the mixer did not respond
  to the UI clicks. The final position to the right of the load controls was
  checked after reopening MLR. No main audio wiring changed.
- Original MLR loaded its existing Grid path and reported `grid_not_attached`
  while unclaimed. No Grid device session or physical controller acceptance is
  claimed here. The other original startup/voice debug messages remain.
- Each `*-console.png` records automatic fixture completion; it is not a complete
  export of all prior console history. `*-events.txt` retains the timed passive
  observations used for the numerical checks.

## Listening and limits

**No new listening report: the user was away.** Keep the successful
[listening.wav](listening.wav) for later: lane B starts at 0.1 s; the new take
joins at 4.9 s; Reverse is at 8.3 s, half speed at 9 s, double speed at 10 s;
intentional Stop is at 12.5 s. No acoustic/device-output capture was made.

Open: exact-boundary Reverse repair, listening/native usability acceptance,
device delivery during allocations, 44.1 kHz Free growth, forced allocation
failure and sample-rate changes without Pd DSP Off. Ordinary fixed recording
has earlier evidence; it does not automatically accept these Free cases.
Pause/append, overdub, quantized recording, recording speed/direction, physical
shrink, larger memory limits and DAW lifecycle remain future work.

## Repeat

1. Close MLR and other fixtures in plugdata. Keep the sibling source files and
   bundled dependencies available. The builder requires Python 3 and ffmpeg;
   the analyzer additionally uses numpy.
2. From the repository run `python3 tests/build_record_session_check.py`.
   Open `/tmp/plugmlr-record-session/check.pd` in the native runtime above, with
   DSP On at 48 kHz / 1×. Read the actual console before proceeding.
3. In the native console enter `record-session-view bang`, then
   `record-session-check run` (no leading semicolon). Observe the two active
   rows. Wait for `record-session-finished: bang`, about 14 seconds.
4. Copy `capture.wav`, `live1.wav`, `live2.wav`, `events.txt` from the temporary
   directory to a new evidence directory with `run-` prefixes **before** another
   test. Run `python3 tests/analyze_record_session.py /path/to/evidence/run`.
5. Repeat with `dsp`, `zero`, and `boundary`, copying each result under its own
   prefix. `boundary` currently returns a nonzero analyzer exit status; do not
   relabel it a pass. `record-session-check stop` is an additional manual stop;
   the independent watchdog is already armed for every capture.
6. Close the fixture after completion. For user listening, use the stereo
   `listening.wav`, or extract only capture channels 7/8. Preserve numerical and
   listening observations separately.

`initial-manifest.json` describes the first run/dsp/zero fixture; `manifest.json`
adds passive boundary traces and separates the successful later-turn `run` from
the retained `boundary` score. Both use the same unchanged production player.
