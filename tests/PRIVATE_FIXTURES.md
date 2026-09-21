# Private historical fixtures

The files below were used for retained engineering evidence but are not licensed
for community redistribution. They are deliberately absent from a clean checkout
and must never be included in a release archive.

## DrumLoop.wav

- Origin: purchased sample pack; redistribution permission not held by plugmlr.
- Historical path: repository root as `DrumLoop.wav`.
- Format: 24-bit stereo PCM WAV, 44,100 Hz, 631,881 frames.
- SHA-256: `bd3986375276ea5ff0204de532b890778d45276cd93976726a29e2d1ab2f21f6`.

Some historical analyzers compare retained captures against this exact source or
its exact length. Maintainers who lawfully possess the same asset may place a
private copy at the repository root; `.gitignore` prevents it from being added.
Verify the hash before using it. These analyzers are evidence-reproduction tools,
not part of the alpha release gate.

New tests and release checks must use project-owned deterministic fixtures under
`tests/fixtures/` and must not add new dependencies on this private file.
