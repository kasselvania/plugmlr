# Musical stretch controls and automatic adoption — 2026-09-17

Native plugdata0.9.4 nightly98ae0f78b, Pd0.56.3, ELSE1.0-rc14, pdlua0.12.23,
48kHz. Rubber Band4.0.0 R3 through the same background worker. Source manifests,
score, four rendered WAVs/JSONs and an eight-second original-mixer capture retained.
No DAC in fixture. Capture stopped at8s with an independent10s fallback.

The fixture uses all16 original players/owners, preserving the destination's ordinary
completion listener that mattered to the earlier crash. Unique Lua names avoid
changing the user's loaded classes. It enters90 BPM for a one-second region, sets
120 BPM and pitch0, then requests Render once. No Load command occurs anywhere in
the musical score. Three later Render requests each use the previous result.

All four copies were automatically loaded/selected; native UI ended at Sample913,
showing0.750s, confirmed120 BPM (rendered),1.5 beats, pitch0. Four manifests show
source90→target120 ratio0.75 first, then120→120 ratio1 for successive copies.
Each output has36000 frames/0.75s. Render pitch peak220/329.09Hz; actual adopted
player peak220/331Hz (within2Hz FFT tolerance around220/330). Stereo finite output;
other original player's10ms RMS stayed above0.0223/0.0444 and render-window RMS
ratio was1.00000016/0.99999998 against baseline. These are internal audio checks,
not CoreAudio/DAW deadline proof, universal click-free acceptance or user listening.

Native console had no new error, with the previous grid-not-attached warning and
capture-stop messages visible. UI screenshot retained. The final pass includes label cleanup and cancellation through the loading interval.
An earlier passing run is retained in first-pass/. Test manifests record the exact
native-tested source hashes.

Lua checks cover90→120, beats inference, half/double, linked-mode changes, unknown
BPM refusal, automatic adoption, edited-settings suppression, navigation away/back,
Cancel during load, occupied slots, duplicate completion and deferred receiver
teardown. Owner tests cover metadata assignment and reset on replacement. Existing
editor tests, five worker tests, Lua syntax and Pd connection validation pass.

Tempo metadata is session-owned by the Sample buffer. It is not currently read back
from a sidecar on manual reload. Files and richer manifests persist. No detector,
third bank, current-slot overwrite/revert or new DSP was implemented. Changing the
selection/settings during a job keeps the result file but does not switch the user.
Automatic import still uses the original synchronous loader; it may briefly stall.

User's open application was not restarted or overwritten. Its cached classes need
a full plugdata restart after saving patterns/takes before testing the new editor.
