# Cut-pattern checkpoint

Native Mac plugdata 0.9.4 nightly 98ae0f78b / Pd 0.56.3 / pdlua 0.12.23.
DSP was already On; the fixture sends no global DSP command, opens no device,
contains no DAC or audio recorder, and stops its test players automatically.
The native console showed completion and no new errors. Its existing
`grid_not_attached` warning remained. The fixture's page actions addressed test
players; Player 902's panel was closed before the fixture itself. User Track 1
remained loaded and paused. No physical Grid or listening result is claimed.

## Results

- 55 replay events matched expected timestamps within 0.05 ms in the Pd logical-time log.
  This is control timing, not measured DAC latency or sample-exact audio timing.
- 19 cuts were accepted through the original two players, including launches.
- Quantized input replaced earlier pending cuts before capture. Replay bypassed
  quantization without altering mode, and ran without new ppq ticks.
- Replay removed stale manual quantized input; invalid replay did not cancel it.
- Focus/page changes did not retarget stored events. Empty buffers did not start a take.
- Stop/Clear canceled future events. Restart began at the first recorded cut.
- Detach finished recording stopped; reconnect did not launch. DSP Off stopped
  playback; DSP On did not restart it (injected private DSP-message test).
- Minimum 10 ms loops and 7 ms event bursts retained expected repeat timing.
- Sole-renderer LED output distinguished empty/armed/recording/playing/stopped,
  including blinking and reconnect redraw. Physical LEDs are untested here.
- Production Lua with a simulated logical clock separately passed duration/event
  limits, invalid inputs, phase accumulation and reentrant Clear tests.
- Source guard: 70 other existing Pd/Lua components unchanged. Original player
  change is one pattern-player object, one observation wire, one cancel-flag wire.

First-fixture evidence retains incorrect later test setup: a PLAY row was used
instead of a CUT and a quantized cut had no tick. Corrected final run covers both.
Cached LED frames and disconnected output correctly produce no redundant write;
assertions inspect displayed state rather than demand an extra message.

## Repeat

Run `lua tests/cut_pattern_spec.lua`, then `python3 tests/build_cut_pattern_check.py`.
Open `/tmp/plugmlr-cut-pattern/check.pd` in native plugdata. It starts one second
after opening, finishes its score after 5.2 seconds and has a 9-second watchdog.
Inspect the native console, then run `python3 tests/check_cut_pattern.py`.
Close any test player panel and the test tab. The source manifest pins production
and fixture hashes; class/bus/track substitutions keep tests separate from user tracks.

For physical acceptance, restart plugdata and open mlr.pd. Load a sample, choose
Quantize Off (or run the clock for quantized cuts), press top-row key 5, play a
phrase across tracks, then press 5 to loop. Check stop/restart and ALT+5 Clear.
Pattern Stop intentionally leaves current audio playing. Patterns are volatile,
cut-only and use free elapsed time. No tempo-follow, bar rounding, overdub or save.

Interaction reference: sonocircuit/mlre manual v2.2, page 16, pinned at
ba88531bd31656ec33b54beee4f67c5438ae7d35; no upstream code copied.
