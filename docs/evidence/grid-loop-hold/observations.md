# Two-key loop hold: native gesture evidence

Base: PR #42, `a09c10b5a2a653862d648564f93a9ac3586656d3`.
Production change: `grid-cut-keys.pd_lua` only. No playback, quantizer, loop
handoff, buffer, LED renderer, adapter, package or SerialOSC change.

## Behavior to try

Every fresh ordinary track-row key-down emits its slice into the existing Pd
quantizer. Duplicate downs remain ignored. With exactly two keys held on a row,
a one-shot clock arms the loop after 40 ms of continuous overlap, measured from
the second down. The first release commits the inclusive range once, only if
armed. The clock itself emits nothing. A shorter overlap has no release action.
The existing once-per-gesture behavior remains: after the first release, a new
pair can form when the row's held keys have cleared. Further ordinary key-downs
still make cuts. Third-key cancellation and ALT/MOD priority remain in place.

`LOOP_HOLD_MS` is the sole threshold constant, near the top of grid-cut-keys.
This candidate favors responsive finger patterns: the second key now cuts too.
No 40 ms delay is added to slice delivery; musical quantization still determines
when those requests play. MOD plus one key still makes an immediate one-cell loop.
The existing loop-release keep-position/wrap behavior is unchanged.

## Native test

Run `python3 tests/build_grid_hold_check.py`, then open
`/tmp/plugmlr-grid-hold-check/check.pd` in standalone plugdata. Enter
`grid-hold-check-run bang` in its console. A 13.255-second qlist runs the cases
and automatically writes events.txt and prints `grid-hold-check-done: bang`.
It has no audio objects, device session, OSC transport or application player sends.
Then run `python3 tests/check_grid_hold.py`.

The test executes a byte-for-byte source copy apart from a unique class name,
which avoids accidentally exercising the user's already-cached Lua class.
Source and fixture hashes are in source.json. A real Pd timer timestamps slice,
transport and loop messages. No fake clock or Python timing model replaces the
native Lua/Pd scheduler. The expected outputs are explicit in the builder.

Observed in the UI: plugdata **0.9.4 nightly 98ae0f78b**, **Pd 0.56.3**,
pdlua **0.12.23**, DSP enabled. Native console completion is retained in
native-complete.png. The existing `mlr-grid-compat: unsupported_or_invalid
 grid_not_attached ...` message predates this test; no new diagnostic errors
appeared during load/run/closure. The original Player 1 stayed paused on
`Longcase_83_A.wav` and was returned to view; its sample and Grid lease were untouched.

All **53 cases pass**, covering:

- 0, 5, 39, 40, 41 and 100 ms overlaps, either key released first, across rows 1/2/6.
- A long first hold followed by a brief second hold: still no loop.
- No autonomous loop at timer expiry; a release is required.
- Duplicate down does not restart the deadline or emit another slice.
- Third key still cuts while cancelling the possible loop.
- Cancellation before and after arming; an old deadline cannot arm a new pair.
- Independent rows with different hold lengths and two simultaneous qualified loops.
- Rapid taps while the first key remains held, with no lost slice presses.
- ALT transport, immediate MOD loops, ALT-over-MOD priority and modifier cancellation.
- Disconnect before/after arming, stale releases and malformed input.

The source-boundary check also verifies all **71 other root Pd/Lua files**
against base #42, including the original audio, quantization, loop and device paths.
The current UI source-preservation check and Lua syntax check pass.
Historical gesture scripts retain their old checkpoint expectations; this fixture
is the current check for overlapping-key slice dispatch and minimum loop hold.

## Acceptance still open

This proves actual native gesture timing/output, not physical finger feel or
new audio acceptance. No recording was started and no new audio evidence is
claimed for this input-only change. Pd-Lua's registered-clock ownership provides
object teardown; ordinary test closure was observed, but forced destruction
exactly during the 40 ms interval was not a separate native test.

Restart plugdata and reopen mlr.pd before trying the new class; reopening a patch
inside the same process may retain cached Lua. The currently loaded user session
was deliberately left intact. Compare fast patterns and a deliberate two-key
hold; 40 ms can be adjusted after the user tries it. The user explicitly regards
the second-key choice as an experiment in feel, not settled product acceptance.
Subsequent user feedback rejects perceived 40 ms latency and suppressed presses.
The revised candidate has immediate cut dispatch, but was tested in an isolated
native class and was not loaded by the agent into the user's live MLR session.
Do not record that feedback as positive physical acceptance, or assert that the
candidate was what the user heard. Keep the 40 ms overlap policy experimental.
