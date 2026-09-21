# Alpha feature status

This matrix applies only to the alpha target in `ALPHA_RELEASE.md`. It records the
current claim ceiling; it is not a roadmap promise.

## Included in alpha.1

| Area | Included boundary | Evidence ceiling |
| --- | --- | --- |
| Sample buffers | Load 16-bit PCM stereo WAV files, select Sample slots 1–16, replace a slot through the guarded loader | Native load/selection and shared-buffer checks; no arbitrary-format promise |
| Live buffers | Select Live slots 1–16, record a fresh take, finish early or at its fixed/free limit | Primary recording evidence is 48 kHz standalone |
| Playback | Play, Pause/Resume, hard Stop, forward/reverse, 0.25/0.5/1/2/4x speed, bounded glide | Original dual-reader stereo engine; not universally click-free |
| Slices and loops | Sixteen whole-content cuts, immediate/quantized launch, live Start/End/Move, Grid one-cell/two-key loops | Native numerical/listening evidence plus bounded physical Grid checks |
| Clocking | Internal clock, slice grids, Beat Reset, tempo fit | Internal clock only; fit changes tape rate and pitch rather than phase-locking audio |
| Recording storage | Fixed or Free recording, written-content bounds, DSP-off finish, unsaved-take guard | No pause/resume, overdub, quantized launch, or physical array shrink |
| WAV export | Save a finished stopped take as 32-bit float stereo WAV | Synchronous operation; stopped instrument required |
| Instrument UI | Sixteen-track overview, focused player, sample bank, live-take panel, waveform and cursor | Review-grade PlugData UI; root-tab focus has a known limitation |
| Patterns | Eight free-time performance slots and versioned manual bank save/load | Control timeline only; no audio, buffer, tempo, gain, or project recall |
| Grid connection | Explicit select, probe, lease claim, readback, release, disconnect cleanup | Exact pinned device/service candidates only |
| Grid performance | PLAY/CUT pages for tracks 1–6, transport, speed/direction, cuts, loops, playback feedback | Physically exercised 16-by-8 lane; other layouts are not instrument acceptance |

## Experimental or incomplete

| Area | Current state | Alpha treatment |
| --- | --- | --- |
| Grid BUFFER page | Native routing and LED checks pass; physical usability remains open | Present but marked experimental |
| Grid screen following | PLAY/CUT can request the corresponding view; PlugData cannot always foreground the root tab | Present with documented manual fallback |
| Sample trim/editor | Reversible shared-buffer trim and loop selection have native checks | Present; no edited-sample export or recall claim |
| 44.1 kHz operation | Bounded playback and transition checks exist | Additional test lane, not complete recording/platform support |
| File/host-rate mismatch | Bounded playback checks exist | No blanket format compatibility claim |
| Very short loops | Bounded checks reach millisecond-scale cycles | One-frame/sub-sample and arbitrary-source sound quality remain unqualified |
| Hardware input reconfiguration | DSP-off handling is exercised | Live interface reconfiguration without DSP-off is unqualified |
| Pattern sequencing feel | Save/load was accepted with an acknowledged sequencing quirk | Preserve and document; do not silently redefine timing |

## Excluded from alpha.1

| Area | Reason |
| --- | --- |
| Rubber Band stretch/pitch rendering | Broader crash, teardown, dependency, musical-quality, and clean-install gates remain open |
| DAW/plugin use | Bitwig audio, clock, editor, save/reload, and multi-instance lifecycle are not accepted for the instrument |
| Multiple plugmlr instances | Shared global Pd names prevent isolation |
| Full project recall | Pd patch save does not retain live audio, loaded-file state, or the pattern bank as one project |
| Automatic persistence/recovery | No autosave, quit interception, or crash recovery |
| External clock sync | DAW/MIDI clock switching, seeks, loops, and transport lifecycle are open |
| Advanced recording | No pause/resume, overdub, recording quantization, direction, speed, or slew |
| Arc and additional Grid layouts | Device-layer evidence is not instrument mapping/usability acceptance |
| SteamOS/Steam Deck | Companion service packaging exists, but plugmlr application acceptance does not |

## Changing this matrix

A feature moves upward only with an exact source revision and the evidence needed
for the new claim. Static checks cannot promote a physical-device claim, and a
physical controller check cannot promote DAW, audio-quality, or multi-instance
acceptance.
