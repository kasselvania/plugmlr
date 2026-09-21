# Alpha release tooling

`alpha-files.txt` is the explicit project-owned payload for alpha.1. The builder
adds the complete tracked contents of the exact `dependencies/monome` commit,
without its Git metadata, plus generated source and checksum manifests.

Build and verify from a clean checkout with the submodule initialized:

```sh
python3 scripts/build_alpha_release.py
python3 scripts/build_alpha_release.py --verify \
  dist/plugmlr-v0.1.0-alpha.1.zip
```

The build fails closed when:

- the root checkout or submodule is dirty;
- the app source differs from the pre-stretch alpha authority;
- the submodule is absent, dirty, at the wrong revision, or lacks its MIT license;
- a manifest path is missing, duplicated, out of order, or untracked;
- a local link would be broken in the curated payload;
- private audio, root engineering evidence/test fixtures, Git metadata, or an
  unexpected media file enters the archive; or
- the output exceeds the bounded alpha package size.

The sibling `.zip.sha256` authenticates the complete archive.
`MANIFEST.sha256` inside the ZIP authenticates every payload file and
`RELEASE.json` records the exact plugmlr, application-code, Monome, SerialOSC,
and PlugData authorities.
