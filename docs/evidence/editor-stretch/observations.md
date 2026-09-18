# Existing sample-editor stretch integration

Native app: plugdata 0.9.4 nightly 98ae0f78b, Pd0.56.3, ELSE1.0-rc14,
pdlua0.12.23, 48kHz. Rubber Band CLI4.0.0, native launch from the Pd-Lua bridge.

## Passing bounded run

`native-pass/manifest.json` identifies exact production sources and fixture edits.
The fixture copies the original player/mixer and editor into isolated IDs901–916;
only ID range, Lua class names and test command taps differ. It has no DAC.
`score.txt` starts the real players, stages0.5–1.5s, asks for2x/+12, loads the
rendered copy into empty916, and auditions through the existing engine. Capture
stops at8s with an independent10s fallback. The fixture now starts itself one second
after opening; do not leave its capture unbounded when changing the score.

`analysis.json`: eight-second four-channel actual mixer capture, two-second stereo
render, both rendered and played pitches440/660Hz. Other original player remained
above0.022/0.044 RMS in10ms windows. Its during-render/import RMS ratios versus
baseline were1.00000016/0.99999999. Output was finite. This measures internal audio;
it does not certify CoreAudio/Bitwig deadlines, every transition, or large files.
The retained WAVs are synthetic fixtures, not copyrighted user samples.

`editor.jpg` shows the existing editor with the new controls, selected copy,
correct two-second waveform and source-slot identity. Runtime warnings visible
higher in the console are from earlier failed runs, not new pass errors. One final
post-capture change formats the origin slot label as an integer instead of `901.0`;
processing, routing and audio are unchanged. Lua control tests were rerun afterward.

## Failures retained, not relabelled as passes

- Initial fixture omitted dummy live-buffer owners, producing missing view-get
  receiver warnings before capture. Added owners to the isolated test fixture.
- `failed-first-render`: Pd numbers serialized as24000.0; Python integer parsing
  rejected them. Explicit integer argv fixed the actual native boundary.
- `failed-first-load`: Pd slot916.0 formed the wrong destination symbol. Integer
  conversion fixed the bus name; native console exposed this directly.
- Native mouse/AX automation did not reliably fire buttons. Commands were therefore
  tested through their exact editor bus. Physical interaction remains a user gate.

Failed captures are losslessly compressed. First failures left original playback
running; they did not produce or adopt falsely labelled successful renders.

## Additional checks and limitations

Lua tests cover bad controls, exact integer argv, shell quoting, duplicate Render,
Cancel, occupied slots, a manual selection winning over delayed adoption, and load
timeout. Existing editor tests cover source retention and in-flight slot vacancy.
Five Python tests cover exclusive bounds/stereo frame preservation, source unchanged,
bad bounds/rate/missing files, float WAV, invalid parameters and no crop overwrite.
Patch indexes and Lua syntax pass.

`music-worker/` is a separate worker-only test of the repository DrumLoop.wav:
stereo24-bit44.1kHz, selection0–4s, duration1.25x, pitch+7. Output is5s. It is not
new native44.1kHz-host or sample-rate-mismatch evidence. No user listening report
has yet been received for this integration. Copies preserve gain processing from
Rubber Band; no normalization/limiter is added by this bridge.

Completed copies persist in `renders/`; temporary jobs/logs are in the system temp
folder. Source-file editing after loading is unsupported: reload the source first.
The cropper detects mid-read changes and mismatched bounds/rate, not same-size
external content edits made since the original load. Only stereo PCM/float RIFF WAV
is supported initially. Load copy uses the original synchronous loader and can stall.

User's original session was restored with tracks1/2 paused, all live tracks empty,
and an unsaved pattern bank. No app restart, source overwrite or pattern replacement.
To use the new classes, save patterns/takes, fully quit and reopen plugdata, open
mlr.pd and load the source sample. Render copy -> Load copy -> Audition loop all live
in the existing editor. No terminal or separate workbench is needed for user testing.
