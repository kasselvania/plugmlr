# Installation

This guide installs the exact environment being prepared for
`v0.1.0-alpha.1`. It is intentionally narrow. A different operating system,
PlugData build, host, or moving branch may work, but it is outside the supported
alpha claim.

## Requirements

- an Apple-silicon Mac;
- Git;
- PlugData standalone 0.9.4 nightly build `98ae0f78b`;
- one 16-bit PCM stereo WAV you have permission to use; and
- for Grid use only: a 16-by-8 Monome Grid, Homebrew, Apple Command Line Tools,
  and the pinned SerialOSC service described below.

The tested PlugData console identified Pd 0.56.3 and pdlua 0.12.23. Stable
PlugData 0.9.3 is not the alpha runtime: the companion device menu failed its
required dynamic-menu behavior there.

## 1. Get the exact source line

No alpha tag exists yet. Preparation testers should use the named preparation
branch, not moving `main`:

```sh
git clone https://github.com/kasselvania/plugmlr.git
cd plugmlr
git switch codex/alpha-boundary-and-licensing
git submodule update --init --recursive
```

Confirm the companion source pin:

```sh
git submodule status dependencies/monome
```

It must begin with:

```text
620b22c641003b3dcbca8ec94858839737a495bb dependencies/monome
```

That release commit adds the companion MIT license, notices, and documentation
to runtime revision `18b489399d01a9178e4667b849ec4368d72533db`; it does not
change device behavior.

After alpha.1 is tagged, the release tag or curated archive will replace this
temporary branch instruction. Do not assemble a release from moving `main`:
that line contains later stretch work which alpha.1 excludes.

## 2. Install the tested PlugData build

The supported runtime is the official macOS Universal 0.9.4 nightly associated
with PlugData commit `98ae0f78b` and
[GitHub Actions run 27418767000](https://github.com/plugdata-team/plugdata/actions/runs/27418767000).
The plugmlr repository does not redistribute PlugData.

The tested executable has this SHA-256:

```text
86179a37e58e7a0f0436fc555f56ce41892e3f32ed19b4a3ba8f1cfe3c17476e
```

After placing the application in `/Applications`, verify it with:

```sh
shasum -a 256 /Applications/plugdata.app/Contents/MacOS/plugdata
```

If the exact artifact is no longer obtainable, stop treating the environment as
the supported alpha lane. A newer build reporting only “0.9.4” is not identical
evidence; it needs the release checks repeated. The source archive does not
redistribute PlugData, so an unavailable pinned runtime blocks the clean-install
acceptance gate.

Launch PlugData through Finder, Spotlight, the Dock, or LaunchServices:

```sh
open -a plugdata
```

Do not execute the inner `Contents/MacOS/plugdata` binary directly. That bypasses
normal macOS application registration and has produced launcher aborts unrelated
to plugmlr.

## 3. Open plugmlr

In PlugData, open `mlr.pd` from the checkout. Keep the repository layout intact:
the entry patch loads sibling Pd/Lua files and the companion device submodule by
relative path.

Enable DSP and keep PlugData's console visible during the first run. Continue
with [First sound](FIRST_SOUND.md). A Grid is optional for sample playback.

## 4. Optional: install the Grid service

Skip this section if you are not using a Grid. The curated source archive
materializes the exact licensed companion revision under `dependencies/monome`.

The Grid path uses the lease-aware SerialOSC candidate. The candidate manager
requires the accepted stable service to exist as a rollback, so install them in
this order from `dependencies/monome`.

First install and verify the pinned null-port-safe stable service:

```sh
cd dependencies/monome
./tools/install_macos_serialosc.sh install
./tools/install_macos_serialosc.sh verify
```

This user-level installer fetches exact source, installs any missing Homebrew
build libraries, stops known competing SerialOSC jobs, and verifies one daemon
on UDP port 12002. It does not replace Homebrew Cellar files and needs no `sudo`.

Then prepare the lease candidate without activating it:

```sh
./tools/macos_serialosc_lease_candidate.sh prepare
./tools/macos_serialosc_lease_candidate.sh status
```

Quit PlugData and any other Monome client, and make sure attached devices are no
longer in use. Activate and verify the candidate:

```sh
./tools/macos_serialosc_lease_candidate.sh activate
./tools/macos_serialosc_lease_candidate.sh verify
```

The accepted candidate must report revision
`7187832c349202b1a94a9b10080ae57d40069946`, and it must be the sole owner of
UDP 12002. The switch preserves the stable service for rollback.

To restore that service later:

```sh
./tools/macos_serialosc_lease_candidate.sh restore-stable
```

The detailed service boundary is in the companion project's
[`MACOS-LEASE-CANDIDATE.md`](../dependencies/monome/docs/MACOS-LEASE-CANDIDATE.md).

## Next

- [Get first sound](FIRST_SOUND.md).
- [Connect and claim a Grid](GRID_GUIDE.md).
- If anything differs from the expected path, use
  [Troubleshooting](TROUBLESHOOTING.md).
