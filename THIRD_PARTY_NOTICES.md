# Third-party notices for alpha preparation

This is a preparation record, not a completed redistribution notice. Alpha.1 must
not be published until every component actually present in its archive has a
confirmed license and notice.

## plugmlr project code

Project-owned plugmlr source is licensed under the MIT License, copyright
2025-2026 Peter Kassel. See `LICENSE`. This grant does not cover the components
or assets listed below, which remain under their own terms or are excluded.

## Runtime prerequisites not distributed by plugmlr

- **[PlugData](https://github.com/plugdata-team/plugdata)** — supported alpha
  runtime: 0.9.4 nightly `98ae0f78b`.
  The tested build supplies Pd 0.56.3, pdlua 0.12.23, and the ELSE/Cyclone
  objects used by the patch. These are separate projects under their own terms.
- **[SerialOSC lease fork](https://github.com/kasselvania/serialosc)** —
  separate device service owned by `kasselvania/serialosc`, consumed at the
  exact candidate documented by
  `PlugData-Monome-Devices`. Preserve the upstream and fork license notices when
  installing or redistributing it.

## Pinned source dependency intended for the archive

- **[PlugData-Monome-Devices](https://github.com/kasselvania/PlugData-Monome-Devices)**
  — Git submodule revision
  `18b489399d01a9178e4667b849ec4368d72533db`.
  It supplies discovery, explicit selection, probe/claim/renew/release, normalized
  Grid events, and LED caching. It currently has no root license, so its source
  may not yet be copied into the public alpha archive.

## Behavioral references not distributed in the archive

- Monome/norns `mlr` and `mlre` are cited as musical/control references. They are
  not runtime dependencies of the pre-stretch plugmlr application.
- OP-1/OP-XY and Maschine manuals are cited as product-behavior references only.

## Excluded from alpha.1

- **[Rubber Band Library and command-line utility](https://github.com/breakfastquay/rubberband)**
  — excluded from the alpha.1 source line and release archive. Its official
  project publishes the library and utility under GPL-2.0-or-later, with a
  separate commercial licensing option.
  Revisit those terms before distributing an installer, binary, or integration.

## Project assets excluded from distribution

- `DrumLoop.wav` is a purchased sample-pack asset for which the project does not
  have redistribution rights. It has been removed from the alpha tree and must
  not appear in a release archive.
- Historical audio captures derived from that private sample remain engineering
  evidence only and must also be excluded from the release archive.

See `docs/PROVENANCE.md` for the complete release gate and the remaining
dependency and asset boundaries.
