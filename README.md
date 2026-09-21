# plugmlr

plugmlr is an MLR-style stereo instrument for
[PlugData](https://plugdata.org/). It combines shared sample and live-recording
buffers, sixteen playable slices per track, tape-style speed and direction,
editable loops, an internal clock, performance patterns, and an explicitly
claimed Monome Grid.

> **Alpha preparation:** `v0.1.0-alpha.1` has not been published. The current
> release line deliberately excludes the later Rubber Band stretch work.
> The companion source is licensed and the curated package gate is in place;
> clean-install validation and the release tag remain open. See the
> [alpha boundary](docs/ALPHA_RELEASE.md) before describing or distributing
> this build.

## Start here

1. [Install the supported alpha environment](docs/INSTALLATION.md).
2. [Get first sound without a Grid](docs/FIRST_SOUND.md).
3. Read the [user guide](docs/USER_GUIDE.md) for playback, editing, recording,
   clocks, patterns, and saving.
4. If you have a Monome Grid, follow the explicit
   [select → probe → claim → release workflow](docs/GRID_GUIDE.md).
5. Use the [troubleshooting guide](docs/TROUBLESHOOTING.md) before reporting a
   problem.

The entry point is `mlr.pd`. Keep it with all sibling patches and the initialized
`dependencies/monome` submodule.

## Alpha.1 at a glance

The deliberately narrow supported lane is:

| Part | Supported alpha target |
| --- | --- |
| Computer | Apple-silicon Mac |
| Runtime | PlugData standalone 0.9.4 nightly `98ae0f78b` |
| Audio | 48 kHz primary lane; tester-supplied 16-bit PCM stereo WAV |
| Instances | One open plugmlr application instance |
| Controller | Legacy Grid `m1000853`, 16 columns by 8 rows |
| Device layer | packaged at `620b22c641003b3dcbca8ec94858839737a495bb`; tested runtime source at parent `18b489399d01a9178e4667b849ec4368d72533db` |
| SerialOSC | Lease candidate `7187832c349202b1a94a9b10080ae57d40069946` |

The alpha includes sample and live-buffer playback, forward/reverse operation,
five speed presets, sixteen slices, editable loops, internal clocking, tempo fit,
fixed/free recording, WAV export, eight free-time pattern slots, and the PLAY/CUT
Grid performance surface for tracks 1–6.

It does **not** claim DAW/plugin operation, multiple instances, full project
recall, external clock sync, arbitrary Grid layouts, Arc control, SteamOS support,
or Rubber Band time stretching. The exact boundary is maintained in the
[feature-status matrix](docs/FEATURE_STATUS.md) and
[known issues](docs/KNOWN_ISSUES.md).

## Protect your work

- No demo audio is distributed. For first sound, load a 16-bit PCM stereo WAV
  you have permission to use.
- Live takes exist in memory until you explicitly save them as WAV files.
- Performance patterns require a separate **Save bank** action.
- Saving the Pd patch does not create a complete plugmlr project.
- Fully quit PlugData after updating Lua files; reopening only the patch can use
  cached classes.
- Release a claimed Grid before closing plugmlr or moving the device to another
  application.

## Documentation

| Document | Purpose |
| --- | --- |
| [Installation](docs/INSTALLATION.md) | Exact source, PlugData, submodule, and optional SerialOSC setup |
| [First sound](docs/FIRST_SOUND.md) | Smallest sample-playback check |
| [User guide](docs/USER_GUIDE.md) | Core instrument workflows and persistence limits |
| [Grid guide](docs/GRID_GUIDE.md) | Connection lifecycle, page map, gestures, and tested boundary |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Symptom-based recovery and useful report details |
| [Alpha boundary](docs/ALPHA_RELEASE.md) | Supported target, claims, non-claims, and publication gates |
| [Acceptance record](docs/ALPHA_ACCEPTANCE.md) | Exact clean-package results and open tag blockers |
| [Feature status](docs/FEATURE_STATUS.md) | Included, experimental, and excluded functionality |
| [Known issues](docs/KNOWN_ISSUES.md) | Release-facing limitations and safety notes |
| [Provenance](docs/PROVENANCE.md) | Source, dependency, and asset custody |
| Engineering status (`docs/STATUS.md` in the full repository) | Detailed historical evidence; intentionally omitted from the curated archive |

## License

Project-owned plugmlr source is licensed under the [MIT License](LICENSE).
Third-party dependencies and assets remain under their own terms; see
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and the
[provenance record](docs/PROVENANCE.md). The purchased `DrumLoop.wav` sample and
captures derived from it are not distributed.
