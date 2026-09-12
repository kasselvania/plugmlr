# Waveform, sample identity, diagnostics and finished-take saving

Review candidate based on `ba52e29507aae512f1c429aba87c9d21e3550ac3`
(`codex/ui-overview`, PR #37). Original `mlr.pd` and its existing musical engine
remain the application. No new compiled dependency or service change.

## Native observation

Mac plugdata **0.9.4 nightly 98ae0f78b**, **Pd 0.56.3**. Startup console reports
pdlua **0.12.23 (lua 5.5) (luajit 5.1)**, ELSE 1.0-rc14 and Cyclone 0.9-4.
Executable SHA-256:
`86179a37e58e7a0f0436fc555f56ce41892e3f32ed19b4a3ba8f1cfe3c17476e`.
CoreAudio, 8A input/output, 512 host frames, 1x oversampling, DSP On, output 0.8,
limiter Off. Native settings were inspected at 48,000 and 44,100 Hz and restored
to 48,000 Hz. The test replaces hardware input only in its copied fixture.

The actual player canvas shows stacked stereo waveforms, filename/slot identity,
written duration, fixed 16-way divisions, loop shading and moving position. Native
frames `cursor-a.jpg` and `cursor-b.jpg` show the running 2–5 s loop; `visual/score.txt`
contains that separate four-second auto-stopped observation. Those screenshots
precede only the final stopped-position repaint correction, not a DSP edit.
`player.jpg` shows the normal application; `sample-bank.jpg` shows imported
filename/slot readback; `live-takes.jpg` shows all sixteen
buffer-specific Save buttons and Saved feedback. `console-stopped.jpg` records
completion of the numerical score. `settings-48k.jpg` / `settings-44k.jpg` retain
native host settings.

Debug is initially Off. The native score enabled it at 5.000 s and disabled it at
5.100 s; routine transport/voice diagnostics appeared during that interval.
Expected missing-parent save and missing-file load errors remained visible with
Debug Off. The disconnected Grid compatibility message also remains visible.
No new Lua error appears in the accepted runs. Earlier development errors from
Lua's `1.0` identifier formatting and sends to unbound optional receivers were
fixed before these runs; they are not attributed to DSP or the computer.

The native Save chooser was completed with a filename containing a space. It
produced a byte-identical file to the message-driven export of the same take.
The diagnostic patch was closed after its automatic stop. The original app was
reopened with bundled DrumLoop.wav loaded in Sample 1, Player 1 selected, track
level 0.4 and Master 0.75, playback/recording/clock stopped, and Debug Off. Native
Overview, Sample bank and Player Open buttons were also exercised directly. The
normal Player 1 waveform is left visible, with no diagnostic patch or chooser open.

## Numerical results

The final production sources in each `source.json` passed **21/21 checks** at
both host rates. Each retained capture has eight float channels: master L/R,
player 1 L/R, player 2 L/R, actual generated recording input L/R. This is native
component audio through the existing complete application, not a replacement
mathematical playback model. Copied DAC outputs are disconnected from speakers.

| Check | 48 kHz host | 44.1 kHz host |
| --- | --- | --- |
| Bounded capture | 672,000 frames / 14 s | 617,344 frames / 13.9999 s |
| Stereo take written frames | 62,400 | 57,280 |
| Export versus actual captured input | Exact, both channels | Exact, both channels |
| Three stereo peak caches versus independent scan | Max error < 5e-7 | Max error < 5e-7 |
| Six steady mixer windows | Exact expected mix | Exact expected mix |
| Longest all-zero output run in active interval | 15 frames | 14 frames |
| Final stopped master and both players | Exact zero | Exact zero |
| Non-finite samples | None | None |

Input fixtures: bundled DrumLoop.wav, stereo 44.1 kHz / 14.3284 s, plus generated
stereo `short stereo.wav`, 48 kHz / 0.1 s, with unequal channels and single-frame
peaks. This covers file/host mismatch in both directions. Peak checks scan every
written source frame independently. The three caches are imported Sample 1,
imported Sample 2 and recorded Live 3. No user/private sample is included.

The score exercises two original players, display/cache construction while
playing, next/previous bank navigation, a short reverse loop, view changes,
recording, empty/missing/replaced content and save refusals. Full-transition
samples are retained: finite and mixer gain-bound checks include them. The
largest raw adjacent steps are about 0.400 at 48 kHz and 0.531 at 44.1 kHz;
these include drum transients and the intentionally abrupt test source. A raw
step is not a click verdict. The zero-run check rules out a full Pd block of
exact silence only within its measured interval, not all possible dropouts.

The 44.1 kHz recording Stop is 50 frames short of ideal 1.3 seconds, within one
64-frame Pd block. Export contains every frame reported as written. The initial
incorrect exact-duration assertion is retained in
`44k/rejected-exact-duration-assumption.json`; its other data belongs to that
earlier run. The corrected analyzer checks both written bounds and this timing
bound rather than conflating recorder timing with export truncation.

`guards/` preserves earlier checks of the unchanged save controller: first index
64 is respected; recording-only busy and Play arriving during the 30 ms queued
save delay refuse the write; empty buffers refuse; native chooser works; float
samples L=1.5/R=-1.25 are preserved without normalization. A 48 kHz take saved
with a 44.1 kHz host is byte-identical (`rate48-original.wav` and
`rate48-saved-at-44k.wav`). `source-before-display-clock-removal.json` identifies
that revision. Guard checks predate only display-clock/stopped-cursor changes;
the final complete 14-second runs identify the final production sources. The
trimmed comparison's earlier full reference file is not retained; `checks.json`
records its measured zero-error result and frame counts, and `trimmed.wav` is
retained. This does not pretend every earlier check is a final-source rerun.

## Listening, usability and remaining limits

[Listen to the actual final 48 kHz master](listening.wav). It is a 24-bit stereo
conversion with no normalization. Around 3.5–4.7 seconds, the short generated
stereo source is deliberately audible over the drum loop. Silence from roughly
7–11 seconds and after 12.5 seconds is intentional Stop. User listening of this
new file and hands-on usability acceptance remain **open**. No listening report
has been invented or inherited from a different capture.

The waveform is for completed content, including a just-finished recording. It
is not a continuously growing waveform. Peak calculation runs in bounded Pd
message callbacks, not a worker thread. The short native tests establish no
universal real-time guarantee, long-buffer performance budget, many-visible-view
capacity or background/occlusion reliability. Manual native tab closure is not
an independent tested visibility signal; navigation cancels pending requests.
Cursor rendering uses existing player reports and no new GUI timer.

Save WAV is synchronous soundfiler export guarded against all instrument playback,
recording and storage changes, then rechecked after the chooser/30 ms delay. It
does not suspend other patches, make background I/O, render a performance,
autosave, switch to streaming playback, or implement full recall. Saved means the
last requested write completed; external changes/deletion of that file are not
monitored. The application's existing global namespaces and Bitwig/instance
isolation limitations remain. Export safety depends on using the original
instrument's transport/storage controls, not arbitrary direct array mutation.

## Repeat in native plugdata

1. Keep only one instrument open. Stop playback/recording and close the original
   before opening the test, to avoid its existing global name collisions.
2. From the repo run `python3 tests/build_waveform_check.py`. It constructs
   `/tmp/plugmlr-waveform-check/check.pd`, using the real application plus passive
   taps, generated input and a score. No audio starts on load.
3. Open that file in the local Mac plugdata runtime. Inspect the actual console
   and Audio Settings. Set 48 kHz / 512 frames and DSP On. In the console send
   `ui-check-run bang`. The score stops capture at 14 seconds; a separate
   15-second watchdog stops capture, both players, clock and Live 3 recording.
4. Confirm `ui-check-capture-stopped` in the native console. Run
   `python3 tests/analyze_waveform_check.py /tmp/plugmlr-waveform-check` using a
   Python with NumPy. Archive audio, events, score and source identity before
   another run. Repeat at 44.1 kHz, then restore 48 kHz.
5. Use the stopped Live 3 take to repeat the save guards. Set
   `3_l_b_first_index float 64`, then `3_l_b_select_bang bang`, save and compare
   with the original take from frame 64. The separate `guards/score.txt` can be
   copied into the fixture directory for a bounded recorder/save-race test;
   archive the full-run outputs first. That score finishes at 1.6 seconds and
   retains the same independent watchdog. Select **Save WAV** in Live takes to
   test the native chooser. Only use test arrays for the outside-±1 float check.
6. Run `python3 tests/check_ui_overview.py`. It protects the original nested
   engine wiring and public controls while allowing the explicitly listed
   diagnostic/observer changes. Root `.pd` connections are also checked in
   `source-checks.json`.
7. Close the stopped test and reopen the original `mlr.pd`. Load DrumLoop.wav
   in Sample bank, select Sample 1 in Player 1, and raise track/Master to listen.

For retained analysis, decompress each `capture.wav.xz` into its rate directory,
then run the analyzer there. It uses the bundled repository DrumLoop.wav if
`input.wav` is absent. `source.json` binds the capture's fixture and production
files; `checksums.json` records the retained artifacts. Binary test results do
not depend on screenshots or a user's listening report.
