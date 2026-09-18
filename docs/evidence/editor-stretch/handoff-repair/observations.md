# Handoff lifetime repair — 2026-09-17

The user crashed plugdata after Render copy / Load copy. The full local report's
triggered audio thread ends at bindlist_bang+16, called from bindlist_bang+32.
The installed ARM64 binary traverses a linked receiver list, calls the receiver,
then reads the next link. Our copy_loaded callback destroyed its own Pd receiver
before that traversal finished. Installed Pd-Lua Receive:destruct calls the native
_receivefree immediately. This is a concrete unsafe lifetime operation consistent
with the report; the original crash was not deliberately repeated in the user's app.

The original fixture had Players901/902 but adopted into916. It therefore omitted
916's normal buffer-selection receiver. The full application has the corresponding
Player16 receiver, creating the shared bindlist. That missing condition invalidated
the earlier handoff-safety conclusion.

Repair: copy_loaded only marks completion and schedules the existing Pd clock.
The clock removes the temporary receiver and selects the copy after synchronous
message delivery returns. Repeated completion messages coalesce. A manual selection
before that clock runs still wins. No renderer, sample loader, DSP or UI change.

Regression test first failed on the original code with "Receiver freed during
message delivery". The same test passes after repair and rejects both receiver
freeing and buffer selection during dispatch. Other Lua editor checks, five Python
worker checks, Lua syntax and Pd connection checks pass.

Native test now instantiates all16 original players and owners (IDs901–916), with
six imports into916 through911. Same installed plugdata0.9.4 nightly98ae0f78b,
Pd0.56.3, ELSE1.0-rc14, pdlua0.12.23, 48kHz. No DAC. The eight-second capture stopped
with the independent ten-second fallback available. Native UI displayed Sample911
selected, and console contained the stop report with no errors. Screenshot retained.
Actual original-mixer audio remained finite; rendered/adopted channels measured
440/660Hz. Other track minimum10ms RMS0.0223/0.0444 and relative render-window
RMS1.00000016/0.99999998. These are internal samples, not proof of device deadlines
or subjective musical quality. No new user listening acceptance.

The independent receiver arrangement is now present in the native test, but this
is still a bounded fixture rather than a claim of full-application/DAW acceptance.
The separate Render/Load workflow and BPM usability remain pending follow-ups.
The proposed musical-tempo model is not implemented in this crash repair.

After validation the fixture was closed and the actual repository mlr.pd opened
fresh, with all slots empty and playback stopped. Native console showed the existing
mlr-grid-compat unsupported_or_invalid grid_not_attached warning; no stretch error.
No user samples, patterns or takes were restored from the crashed session.
