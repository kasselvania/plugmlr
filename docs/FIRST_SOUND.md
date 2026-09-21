# First sound

This is the smallest supported playback check. It does not require a Grid,
recording input, a DAW, or the private demo sample used during development.

## Before starting

- Complete [Installation](INSTALLATION.md).
- Use PlugData standalone, not a DAW plugin.
- Have one 16-bit PCM stereo WAV you have permission to use. Other formats may
  work, but they are not the first-run acceptance lane.
- Start with speakers or headphones at a conservative level.

## Load and play one sample

1. Launch PlugData normally and open this checkout's `mlr.pd`.
2. Enable DSP and open PlugData's console. Keep errors visible.
3. Click **Sample bank**.
4. On the Sample 1 row, click **Load** and choose your 16-bit PCM stereo WAV.
5. Confirm that the row reports **Loaded** and shows a non-zero duration.
6. Click **Overview**, then **Open** on track 1.
7. Confirm that the player source is **Sample**, slot **1**. If it is not, set
   those values explicitly.
8. Return to **Overview**. Raise track 1 **Level** cautiously. Leave **Master**
   near its default of 0.75.
9. Press track 1 **Play / pause**. The state should show playing, the position
   should move, and stereo audio should reach the selected output.
10. Press **Play / pause** again to pause, then **Stop**. Stop returns the player
    to its direction-aware starting edge.

Loading or replacing a buffer stops readers of that shared buffer. Press Play
again after a load. A silent ending or very low source level can look like a
transport failure, so test with a clearly audible file before diagnosing plugmlr.

## Exercise the basic controls

With track 1 playing:

- choose forward or reverse;
- try the ¼, ½, 1, 2, and 4× speed presets;
- press several of the sixteen slice controls;
- drag or enter a smaller Start/End loop, then return to the full sample; and
- enable the internal clock only if you want to try quantized cuts or Beat Reset.

Tempo **Fit** changes tape speed and pitch. It is not time stretching. Rubber
Band processing is not part of alpha.1.

## What success establishes

This check establishes only that the exact standalone runtime can load your file
and produce basic sample playback through one track. It does not establish Grid,
recording, file-format breadth, DAW/plugin, multiple-instance, or universal
click-free behavior.

Continue with the [user guide](USER_GUIDE.md) or
[Grid guide](GRID_GUIDE.md). If the check fails, follow
[No sound after pressing Play](TROUBLESHOOTING.md#no-sound-after-pressing-play).
