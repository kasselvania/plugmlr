# Alpha known issues

These are release-facing limits for the alpha source line. Historical failures
and detailed reproduction artifacts remain in `STATUS.md` and `docs/evidence/`.

## Data and session safety

- Live takes remain in memory. Save important takes as WAV before closing,
  restarting PlugData, changing versions, or testing device/runtime changes.
- The Pd patch does not save the eight-slot performance bank. Use **Save bank**
  separately. Pattern files do not contain audio, buffer assignments, tempo,
  gain, or full project state.
- There is no autosave, close/quit warning, or crash recovery. Unsaved-take
  protection guards the explicit Clear action only.
- Saving and loading are synchronous. Slow disks can interrupt a performance.

## Runtime and isolation

- Only the exact Apple-silicon PlugData standalone runtime named in
  `ALPHA_RELEASE.md` is the supported alpha target.
- Shared global Pd symbols prevent safe multiple plugmlr instances in one Pd
  environment.
- DAW/plugin lifecycle, host clock, project reload, and editor behavior are not
  accepted for this alpha.
- Lua classes may remain cached across patch reloads. After an update, save takes
  and patterns, fully quit PlugData, reopen it, and then reopen `mlr.pd`.

## Audio and recording

- Primary recording evidence is 48 kHz. Bounded 44.1 kHz playback evidence does
  not establish a complete 44.1 kHz recording lane.
- Very short loops can expose sharp transitions. A full cycle shorter than one
  host sample is refused, but accepted lengths are not guaranteed click-free for
  every source and transition.
- Tempo fit changes tape speed and therefore pitch. It is not a phase-locked
  time-stretch or synchronization system.
- Recording is forward at 1x. Playback direction, speed, and glide do not change
  captured input.
- Recording pause/resume, overdub, quantized recording, and physical buffer
  shrinking are not implemented.
- Reconfiguring the audio interface while DSP remains on is not qualified as a
  safe recording interruption.
- The included development drum loop has roughly half a second of quiet material
  at its end, which can make slow reverse/reset demonstrations sound silent.

## Grid and UI

- The instrument's physical alpha lane is a 16-by-8 Grid. Wider device-layer
  lifecycle evidence does not establish additional plugmlr layouts.
- The Grid BUFFER page has native routing/LED evidence but still needs a physical
  usability pass.
- PLAY/CUT screen-following cannot always bring the root `mlr.pd` tab to the
  front. Select that tab manually when another PlugData tab remains visible.
- Hardware-global Grid intensity below 15 is not supported by the adapter.
- Discovery does not auto-claim a device and an existing owner is not silently
  displaced. Release the Grid explicitly before moving it to another application.
- Running multiple SerialOSC services on UDP 12002 causes contention. Use only
  the accepted companion-project service for the alpha lane.

## Patterns and files

- Pattern timing is free-time and does not follow later tempo changes or round to
  bars. Leading and trailing silence in the gesture timeline is retained.
- Pattern replay uses the tracks' current buffers; the bank does not restore
  buffer assignments.
- Pattern-bank and take-file operations are manual. There is no unified project
  file or automatic metadata recall.

## Excluded stretch work

Rubber Band rendering and the associated sample-copy adoption path are not part
of alpha.1. A narrow receiver-lifetime defect has a retained repair and regression
campaign, but wider teardown, audio-quality, alternate-host, failure-path, and
redistribution checks remain separate. Do not copy the stretch files from remote
main into this release line or describe the alpha as supporting time stretch.
