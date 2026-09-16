# Grid screen navigation

Native Mac plugdata 0.9.4 nightly 98ae0f78b, Pd 0.56.3, pdlua 0.12.23.
No audio objects, recording, or device claims in the finite silent fixture.

- CUT: actual Player 2 panel appeared. All six track addresses passed message checks.
- PLAY: actual test tab remained selected after closing the player panel.
- Root vis workaround: same failure; removed after checking matching runtime source.
- No new native console errors; existing grid_not_attached warning retained.
- Closing the test manually left the main overview visible. That is not PLAY acceptance.
- Physical Grid screen-following and Bitwig navigation are untested.

`rejected-close-only` captures the current limited implementation: 32 routing records
pass, but the requested reliable home focus does not. `rejected-root-vis` retains
the attempted correction and its actual screen, not a successful replacement.

Repeat with `python3 tests/build_grid_screen_check.py`, open the emitted check.pd
in native plugdata alongside mlr.pd, observe Player 2 around two seconds and PLAY
around thirteen seconds. The score finishes automatically around fourteen seconds.
Run `python3 tests/check_grid_screen.py`; passing logs do not accept home navigation.
