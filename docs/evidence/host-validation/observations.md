# Host validation observations

Engine: PR23 `49ad1c2b86f0cc70478610b1866bca792d211a7a`. No engine changes.
Native standalone plugdata 0.9.4 build 98ae0f78b, Pd 0.56.3. CoreAudio / 8A / 512 frames / 1x.

## 44.1 kHz standalone

Actual Audio settings showed 44100 with buffer 512 and 8A input/output.
Both 12-second core/stress scores ran against the original Player 1 plus actual
post-master mixer, with device output muted. Console showed both automatic stop
messages after each capture. Tested 44.1 kHz matching and 48 kHz mismatched files;
20 numerical checks pass in each case. There is no new human listening report.

The first analysis of the matched core retained an overly narrow passive-tap
alignment assumption (current/64-sample-delayed rate). At block-phase-dependent
commands, captured rate sig~ and logical-time reader motion can differ for up to
two 64-frame blocks. The retained initial result reports 42 normal-sized steps.
The corrected analyzer bounds all transition steps by the maximum captured rate
in the preceding 128 samples; it does not exclude transition windows. The prior
48 kHz tempo-fit evidence still passes all 23 checks with this analyzer.

## Standalone restoration

Audio settings returned to 48000 / 512 / 8A, confirmed in native settings.
All three populated live buffers are byte-identical before/after (see JSON).
Originally empty Sample16 restored empty; track16 returned to Live16. Player1
returned to Live1, stopped, forward, Free, 4 beats, 1x, zero speed glide, internal
120 BPM stopped and Reset2beats. Native panel verified those values. Temporary
recording helper and both master taps removed; console object lists verified
their removal. Passive admin closed. Device output restored to .9. No runtime
diagnostic edits saved over source.

## Bitwig editor access

Bitwig Studio 6.1 launched and a separate Plugmlr Host Validation project was
created. The installed plugdata instrument was inserted through Bitwig's normal
browser. Its installed VST3 binary identifies as 0.9.4 / 98ae0f78b / Pd 0.56.3;
the exact loaded plugin format was not yet confirmed in Bitwig. The show-editor
button reports On. The user confirms the editor is visible. However the UI tool
cannot attach to Bitwig's ARM64 plugin-host window (timeout by full path/name;
bundle identifier is shared with the x64 host). No mlr patch was loaded in that
plugin and no Bitwig audio, clock, isolation or recall test is accepted. This is
a UI-access blocker, not a demonstrated plugin audio failure.

## Paired-player setup corrections

The first test wrapper's unqualified component names resolved to the installed
old player rather than this checkout. The actual console and canvas exposed it
before capture. Relative qualified ../sample_player_rebuild and ../mixer now
resolve this repository. Test track IDs 17/18 use four empty one-frame default
live arrays, and both explicitly select the existing reserved Sample16.
A misplaced extra passive tap survived a cut attempted in Run mode; the first
paired capture had three reader writers and is excluded. The extra tap was then
removed in Edit mode; actual ls output verified only the correct tap remains.
These were test setup errors; no engine source change was made.

## Accepted numerical paired captures

The corrected baseline and changes scores each ran for 10 seconds at 48 kHz,
with two reader-capture stops plus one four-channel mixer-capture stop observed
in the real console. Player IDs were 23853 (track17) and 23874 (track18).
Both read the same Sample16 arrays containing the deterministic 48 kHz source.
The wrapper has no DAC and adds no audible source to the user's mixer.

All 31 checks pass. B's stereo audio, master position, rate and reader positions
are identical between baseline and changes; the only reader-envelope difference
is 2.3283064e-10. Its actual mixer output is identical. A's signed rates are
1, -1, -2 and +2; its partial loop is .25..1.25 seconds, then a whole-content
slice restores full bounds. B independently changes Fit from 1 to 1.5 to .75.
A stays at free 2x through those changes. Mixer gains are .4/.3. Both Stop at
9 seconds and remain silent. Maximum audio steps are below .012, no qualified
audible-reader teleports are found and the longest active silent run is one
frame. No human listening report was requested for these numerical fixtures.

Afterward the test wrapper was closed, Sample16 restored empty (console metadata
`16 0 0 0 0 0`), track16 restored Live16 and original Player1 restored Live1.
Final live-buffer exports are still byte-identical to the original backups.

## Reproduce

Use a disposable session with this checkout's mlr.pd and bundled ELSE/Cyclone,
not a duplicate mlr alongside a loaded user session. Keep Sample15 empty and
reserve Sample16 for test data. Never save temporary player canvas changes.

For the rate checks follow the tempo-fit procedure in STATUS. Generate with
`python3 tests/make_tempo_fixture.py --rate 44100` or `--rate 48000`; load that
fixture into Sample16 and select 44100 host / 512 frames in Audio settings.
Use the existing tempo-fit core and stress scores, each with its independent
12-second recording stops. Preserve each output before the next score.

For paired players, set the host to 48000 and load tempo-stereo-480.wav into
Sample16. Open tests/host-pair-check.pd. It instantiates this checkout's original
player and mixer twice (explicit ../ paths), with unused track IDs 17/18.
Open each player canvas in the UI. Temporarily append `tests/host-player-tap 17
$0` or `tests/host-player-tap 18 $0` respectively; initialize only each helper.
Verify distinct IDs in the console and exactly one helper per player with `ls`.
Do not send loadbang to the full application. Rebuild DSP after attaching taps.
Both players must start Forward. In plugdata's console send:

```
host-pair-check symbol fixtures/host-pair-baseline.txt
```

Wait for host-pair-stopped and two capture-stopped messages. Copy
/tmp/host-pair-17.wav, /tmp/host-pair-18.wav and /tmp/host-pair-mixers.wav to
baseline-17.wav, baseline-18.wav and baseline-mixers.wav. Then run the same
command with fixtures/host-pair-changes.txt and retain changes-* files. Mixer
WAV channels are A-left, A-right, B-left, B-right. Ten-channel reader WAV order
is documented in bounded-player-capture.pd. Close the test wrapper afterward.

Analyze the retained evidence with Python plus NumPy and ffmpeg:

```sh
python3 tests/analyze_tempo_fit.py docs/evidence/host-validation/standalone-441-match --host-hz 44100
python3 tests/analyze_tempo_fit.py docs/evidence/host-validation/standalone-441-mismatch --host-hz 44100 --file-hz 48000
python3 tests/analyze_host_pair.py docs/evidence/host-validation/paired-players
python3 tests/analyze_tempo_fit.py docs/evidence/tempo-fit
python3 tests/check_tempo_fit.py
python3 tests/check_player_panel.py
```

Reader NPZ files retain exact decoded float32 samples; equality was verified
before removing larger reader WAVs. reader-storage.json records original WAV
hashes and frame counts. Mixer WAVs remain directly usable audio files.
