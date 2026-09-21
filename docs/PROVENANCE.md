# Source and asset provenance

This record identifies what is known well enough for engineering custody and what
must still be confirmed before granting a community license or publishing an
alpha archive. Git authorship is useful evidence, but it is not by itself proof
that every uploaded source or media asset may be relicensed.

## Repository authorship

All commits currently reachable from plugmlr main use the same maintainer email
under the names `Peter` or `kasselvania`. The initial history was uploaded in a
series of commits from May and June 2025 and contains no license headers or
provenance document.

The root commit `3a912cf29baaa836c7a4d73c44c7654f9ffde0dc` introduced:

- `mlr.pd`;
- `sample-data.pd`;
- `sample-playback.pd`;
- `rate-change.pd`;
- `monome-object.pd`; and
- `monome_grid_handler.pd_lua`.

Before release, the maintainer must confirm whether these are wholly original,
adapted from another named project, or contain copied portions. Any upstream
copyright and license must be recorded file-by-file when adaptation occurred.

Later work in this repository has been developed and reviewed as plugmlr-specific
repair, UI, recording, pattern, editor, and Grid integration work. That history
does not resolve the origin of the initial upload.

## Behavioral references

The engineering notes cite Monome/norns `mlr`, `mlre`, OP-1/OP-XY, and Maschine
manuals as behavioral and musical references. Current status notes explicitly
describe `mlre` as a behavioral reference rather than code running inside
plugmlr, and current Grid-buffer evidence records no upstream source copy. Before
release, verify that the shipped source remains an independent implementation and
retain attribution for the design references.

## Demo audio

`DrumLoop.wav` was added by commit `3d13a4e` on 2025-05-30. The maintainer has
now identified it as a purchased sample-pack asset for which the project does not
have redistribution rights. It was removed from the alpha branch and added to the
root ignore list so a private local copy cannot be recommitted accidentally.

Alpha publication therefore requires all of the following:

1. omit the private source from the release archive;
2. exclude retained evidence audio derived from it from the release archive;
3. make first-run instructions require a tester-supplied stereo WAV; and
4. if a demo is added later, use a newly generated/project-owned or compatibly
   licensed asset with an explicit notice.

Removal from the current tree does not erase the object from existing Git history.
Purging published history and cached GitHub objects is a separate destructive
repository operation and is not authorized by this documentation change.

## Companion device project

`dependencies/monome` is a Git submodule of
`kasselvania/PlugData-Monome-Devices`, pinned here at
`18b489399d01a9178e4667b849ec4368d72533db`. That repository owns device
discovery, registry, lease/session behavior, normalized Grid/Arc events, and LED
cache behavior. The plugmlr adapter owns the musical mapping.

The companion repository currently has no root license. Its contents must not be
materialized into a public plugmlr release archive until the maintainer grants an
explicit compatible license there. A Git submodule pointer is an exact source pin,
not redistribution permission.

## SerialOSC

The companion project consumes a separately pinned `kasselvania/serialosc` fork
for opt-in leased destinations and expiry/darkening behavior. SerialOSC remains a
separate service and source project. The alpha package should point to its accepted
installer/revision and reproduce the applicable upstream/fork notices; it should
not duplicate or relabel protocol ownership as plugmlr code.

## PlugData and bundled libraries

PlugData, Pd, pdlua, ELSE, and Cyclone are runtime prerequisites supplied by the
tested PlugData build. The alpha archive should not redistribute that application
unless a later packaging decision explicitly audits and satisfies its complete
license set. The support guide must name the exact tested build separately from
the plugmlr source license.

## Rubber Band

Rubber Band code and binaries are excluded from alpha.1. The later experimental
integration invokes an external command-line program and does not place Rubber
Band source in the pre-stretch application tree. Any future installer or bundle
must separately record the exact version, installation source, GPL/commercial
terms, and notices before redistribution.

## License decision gate

No root `LICENSE` file is added while initial-source authority and the companion
device project's license are unresolved. Public visibility does not grant
permission to copy, modify, or redistribute the repository.

After the maintainer confirms the initial source origin and desired grant:

1. add the selected root license;
2. add copyright/attribution notices where required;
3. license `PlugData-Monome-Devices` compatibly;
4. keep `DrumLoop.wav` and its derived evidence out of the release archive;
5. update `THIRD_PARTY_NOTICES.md` with exact versions and license links; and
6. re-run the release boundary review before tagging.
