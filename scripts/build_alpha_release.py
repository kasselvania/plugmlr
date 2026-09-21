#!/usr/bin/env python3
"""Build and verify the deterministic plugmlr alpha.1 source archive."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
VERSION = "v0.1.0-alpha.1"
PACKAGE_NAME = f"plugmlr-{VERSION}"
APP_AUTHORITY = "4c3caff961680a9207c52022ee2244e4b34bd1c1"
MONOME_RUNTIME_AUTHORITY = "18b489399d01a9178e4667b849ec4368d72533db"
MONOME_RELEASE_COMMIT = "620b22c641003b3dcbca8ec94858839737a495bb"
SERIALOSC_COMMIT = "7187832c349202b1a94a9b10080ae57d40069946"
PLUGDATA_BUILD = "98ae0f78b"
MANIFEST_PATH = ROOT / "release" / "alpha-files.txt"
MONOME_ROOT = ROOT / "dependencies" / "monome"
ENTRYPOINTS = ("mlr.pd", "audio-in-subpatch.pd")
SOURCE_SUFFIXES = (".pd", ".pd_lua", ".lua")
MEDIA_SUFFIXES = {
    ".aif",
    ".aiff",
    ".flac",
    ".m4a",
    ".mp3",
    ".ogg",
    ".wav",
}
MAX_UNCOMPRESSED_BYTES = 10 * 1024 * 1024
MAX_ZIP_BYTES = 5 * 1024 * 1024


class ReleaseError(RuntimeError):
    pass


def git(*args: str, cwd: Path = ROOT, text: bool = True) -> str | bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=text,
    )
    if result.returncode:
        stderr = result.stderr.strip() if text else result.stderr.decode().strip()
        raise ReleaseError(f"git {' '.join(args)} failed: {stderr}")
    return result.stdout


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def clean_lines(path: Path) -> list[str]:
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            lines.append(line)
    return lines


def validate_relative_path(raw: str) -> PurePosixPath:
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ReleaseError(f"unsafe manifest path: {raw}")
    if any(part in {"", ".", ".git"} for part in path.parts):
        raise ReleaseError(f"invalid manifest path: {raw}")
    return path


def tracked_files(repo: Path) -> list[str]:
    output = git("ls-files", "-z", cwd=repo, text=False)
    return sorted(item.decode("utf-8") for item in output.split(b"\0") if item)


def ensure_clean(repo: Path, label: str, allow_dirty: bool) -> None:
    status_output = git("status", "--porcelain", "--untracked-files=all", cwd=repo)
    if status_output.strip() and not allow_dirty:
        raise ReleaseError(f"{label} checkout is dirty:\n{status_output.rstrip()}")


def ensure_mit_license(path: Path, label: str) -> None:
    if not path.is_file():
        raise ReleaseError(f"{label} license is missing: {path}")
    text = path.read_text(encoding="utf-8")
    required = (
        "MIT License",
        "Copyright (c)",
        "Permission is hereby granted, free of charge",
        'THE SOFTWARE IS PROVIDED "AS IS"',
    )
    for phrase in required:
        if phrase not in text:
            raise ReleaseError(f"{label} license is not the expected MIT grant")


def load_root_manifest() -> list[str]:
    if not MANIFEST_PATH.is_file():
        raise ReleaseError(f"release manifest is missing: {MANIFEST_PATH}")
    paths = clean_lines(MANIFEST_PATH)
    if paths != sorted(paths):
        raise ReleaseError("release/alpha-files.txt must stay sorted")
    if len(paths) != len(set(paths)):
        raise ReleaseError("release/alpha-files.txt contains duplicate paths")
    tracked = set(tracked_files(ROOT))
    for raw in paths:
        validate_relative_path(raw)
        path = ROOT / raw
        if not path.is_file():
            raise ReleaseError(f"manifest file is missing: {raw}")
        if raw not in tracked:
            raise ReleaseError(f"manifest file is not tracked: {raw}")
    return paths


def pd_dependencies(path: Path) -> set[str]:
    dependencies: set[str] = set()
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("#X obj "):
            continue
        parts = line.rstrip(";").split()
        if len(parts) < 5:
            continue
        object_name = parts[4]
        candidates = [f"{object_name}.pd", f"{object_name}.pd_lua"]
        if object_name == "pdlua" and len(parts) > 5:
            candidates.append(parts[5])
        if object_name in {"clone", "else/clone"}:
            for atom in parts[5:]:
                candidates.extend((f"{atom}.pd", f"{atom}.pd_lua"))
        for candidate in candidates:
            local = ROOT / candidate
            if local.is_file():
                dependencies.add(PurePosixPath(candidate).as_posix())
    return dependencies


def lua_dependencies(path: Path) -> set[str]:
    dependencies: set[str] = set()
    text = path.read_text(encoding="utf-8", errors="replace")
    for name in re.findall(r"[\"']([^\"']+\.lua)[\"']", text):
        candidate = (path.parent / name).resolve()
        try:
            relative = candidate.relative_to(ROOT).as_posix()
        except ValueError:
            continue
        if candidate.is_file():
            dependencies.add(relative)
    return dependencies


def application_closure() -> set[str]:
    seen: set[str] = set()
    pending = list(ENTRYPOINTS)
    while pending:
        relative = pending.pop()
        if relative in seen:
            continue
        path = ROOT / relative
        if not path.is_file():
            raise ReleaseError(f"application dependency is missing: {relative}")
        seen.add(relative)
        dependencies: set[str] = set()
        if path.suffix == ".pd":
            dependencies |= pd_dependencies(path)
        if path.name.endswith((".lua", ".pd_lua")):
            dependencies |= lua_dependencies(path)
        pending.extend(sorted(dependencies - seen))
    return {path for path in seen if not path.startswith("dependencies/monome/")}


def validate_application_sources(root_paths: list[str]) -> None:
    listed_sources = {path for path in root_paths if path.endswith(SOURCE_SUFFIXES)}
    closure = application_closure()
    if listed_sources != closure:
        missing = sorted(closure - listed_sources)
        extra = sorted(listed_sources - closure)
        details = []
        if missing:
            details.append("missing from release manifest: " + ", ".join(missing))
        if extra:
            details.append("not reachable from alpha entry points: " + ", ".join(extra))
        raise ReleaseError("application source closure mismatch; " + "; ".join(details))

    for relative in sorted(listed_sources):
        committed = git("show", f"{APP_AUTHORITY}:{relative}", text=False)
        current = (ROOT / relative).read_bytes()
        if current != committed:
            raise ReleaseError(
                f"alpha application source differs from {APP_AUTHORITY}: {relative}"
            )


def validate_monome(allow_dirty: bool) -> list[str]:
    if not (MONOME_ROOT / ".git").exists():
        raise ReleaseError("dependencies/monome is not initialized")
    ensure_clean(MONOME_ROOT, "Monome submodule", allow_dirty)
    actual = git("rev-parse", "HEAD", cwd=MONOME_ROOT).strip()
    if actual != MONOME_RELEASE_COMMIT:
        raise ReleaseError(
            f"Monome revision mismatch: expected {MONOME_RELEASE_COMMIT}, got {actual}"
        )
    ensure_mit_license(MONOME_ROOT / "LICENSE", "Monome companion")
    required = {"LICENSE", "README.md", "THIRD_PARTY_NOTICES.md"}
    paths = tracked_files(MONOME_ROOT)
    missing = sorted(required - set(paths))
    if missing:
        raise ReleaseError("Monome release files are missing: " + ", ".join(missing))
    return paths


def validate_local_links(root_paths: list[str], monome_paths: list[str]) -> None:
    packaged = set(root_paths)
    packaged |= {f"dependencies/monome/{path}" for path in monome_paths}
    markdown = [path for path in packaged if path.endswith(".md")]
    pattern = re.compile(r"\]\(([^)]+)\)")
    for relative in markdown:
        source = ROOT / relative
        for target in pattern.findall(source.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            raw_path = target.split("#", 1)[0]
            if not raw_path:
                continue
            candidate = (PurePosixPath(relative).parent / raw_path)
            normalized = PurePosixPath(os.path.normpath(candidate.as_posix())).as_posix()
            directory_prefix = normalized.rstrip("/") + "/"
            if normalized not in packaged and not any(
                path.startswith(directory_prefix) for path in packaged
            ):
                raise ReleaseError(f"broken packaged link: {relative} -> {target}")


def source_epoch() -> int:
    return int(git("show", "-s", "--format=%ct", "HEAD").strip())


def release_metadata() -> bytes:
    payload = {
        "application_code_authority": APP_AUTHORITY,
        "monome_release_commit": MONOME_RELEASE_COMMIT,
        "monome_runtime_authority": MONOME_RUNTIME_AUTHORITY,
        "plugdata_build": PLUGDATA_BUILD,
        "plugmlr_commit": git("rev-parse", "HEAD").strip(),
        "schema_version": 1,
        "serialosc_candidate": SERIALOSC_COMMIT,
        "version": VERSION,
    }
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def validate_payload_path(relative: str) -> None:
    lowered = relative.lower()
    path = PurePosixPath(relative)
    if ".git" in path.parts:
        raise ReleaseError(f"Git metadata entered release payload: {relative}")
    if relative == "DrumLoop.wav" or lowered.endswith("/drumloop.wav"):
        raise ReleaseError(f"private sample entered release payload: {relative}")
    if relative.startswith(("docs/evidence/", "tests/")):
        raise ReleaseError(f"engineering-only content entered release payload: {relative}")
    if path.suffix.lower() in MEDIA_SUFFIXES:
        raise ReleaseError(f"unexpected media entered release payload: {relative}")


def collect_payload(root_paths: list[str], monome_paths: list[str]) -> dict[str, bytes]:
    payload: dict[str, bytes] = {}
    for relative in root_paths:
        validate_payload_path(relative)
        payload[relative] = (ROOT / relative).read_bytes()
    for child in monome_paths:
        relative = f"dependencies/monome/{child}"
        validate_payload_path(relative)
        source = MONOME_ROOT / child
        if source.is_symlink():
            raise ReleaseError(f"symlinks are not allowed in alpha payload: {relative}")
        payload[relative] = source.read_bytes()
    payload["RELEASE.json"] = release_metadata()
    return payload


def zip_info(name: str, epoch: int, executable: bool = False) -> zipfile.ZipInfo:
    timestamp = dt.datetime.fromtimestamp(epoch, tz=dt.timezone.utc)
    if timestamp.year < 1980:
        timestamp = timestamp.replace(year=1980, month=1, day=1)
    info = zipfile.ZipInfo(name, timestamp.timetuple()[:6])
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    mode = 0o755 if executable else 0o644
    info.external_attr = (stat.S_IFREG | mode) << 16
    return info


def is_executable(relative: str) -> bool:
    source = ROOT / relative
    return source.exists() and os.access(source, os.X_OK)


def build_archive(output_dir: Path, allow_dirty: bool) -> Path:
    ensure_clean(ROOT, "plugmlr", allow_dirty)
    ensure_mit_license(ROOT / "LICENSE", "plugmlr")
    root_paths = load_root_manifest()
    validate_application_sources(root_paths)
    monome_paths = validate_monome(allow_dirty)
    validate_local_links(root_paths, monome_paths)
    payload = collect_payload(root_paths, monome_paths)

    uncompressed = sum(len(data) for data in payload.values())
    if uncompressed > MAX_UNCOMPRESSED_BYTES:
        raise ReleaseError(
            f"payload is too large: {uncompressed} bytes (max {MAX_UNCOMPRESSED_BYTES})"
        )

    checksums = "".join(
        f"{sha256(payload[path])}  {path}\n" for path in sorted(payload)
    ).encode("utf-8")
    payload["MANIFEST.sha256"] = checksums

    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"{PACKAGE_NAME}.zip"
    epoch = source_epoch()
    with zipfile.ZipFile(
        archive,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
        strict_timestamps=True,
    ) as handle:
        for relative in sorted(payload):
            archive_path = f"{PACKAGE_NAME}/{relative}"
            handle.writestr(
                zip_info(archive_path, epoch, is_executable(relative)),
                payload[relative],
            )

    if archive.stat().st_size > MAX_ZIP_BYTES:
        raise ReleaseError(
            f"archive is too large: {archive.stat().st_size} bytes (max {MAX_ZIP_BYTES})"
        )
    checksum_path = archive.with_suffix(archive.suffix + ".sha256")
    checksum_path.write_text(
        f"{sha256(archive.read_bytes())}  {archive.name}\n",
        encoding="utf-8",
    )
    verify_archive(archive)
    return archive


def verify_archive(archive: Path) -> None:
    if not archive.is_file():
        raise ReleaseError(f"archive does not exist: {archive}")
    checksum_path = archive.with_suffix(archive.suffix + ".sha256")
    if not checksum_path.is_file():
        raise ReleaseError(f"external checksum is missing: {checksum_path}")
    checksum_line = checksum_path.read_text(encoding="utf-8").strip()
    try:
        expected_archive_digest, expected_archive_name = checksum_line.split("  ", 1)
    except ValueError as error:
        raise ReleaseError("external checksum has an invalid format") from error
    if expected_archive_name != archive.name:
        raise ReleaseError("external checksum names a different archive")
    if expected_archive_digest != sha256(archive.read_bytes()):
        raise ReleaseError("external archive checksum mismatch")

    prefix = f"{PACKAGE_NAME}/"
    with zipfile.ZipFile(archive) as handle:
        bad = handle.testzip()
        if bad:
            raise ReleaseError(f"ZIP CRC failure: {bad}")
        names = handle.namelist()
        if names != sorted(names) or len(names) != len(set(names)):
            raise ReleaseError("archive paths are unsorted or duplicated")
        if any(not name.startswith(prefix) for name in names):
            raise ReleaseError("archive contains an unexpected top-level path")
        relative_names = [name.removeprefix(prefix) for name in names]
        for relative in relative_names:
            validate_relative_path(relative)
            validate_payload_path(relative)
        required = {
            "LICENSE",
            "MANIFEST.sha256",
            "README.md",
            "RELEASE.json",
            "THIRD_PARTY_NOTICES.md",
            "dependencies/monome/LICENSE",
            "dependencies/monome/THIRD_PARTY_NOTICES.md",
            "mlr.pd",
        }
        missing = sorted(required - set(relative_names))
        if missing:
            raise ReleaseError("archive is missing required files: " + ", ".join(missing))

        manifest = handle.read(prefix + "MANIFEST.sha256").decode("utf-8")
        expected: dict[str, str] = {}
        for line in manifest.splitlines():
            digest, relative = line.split("  ", 1)
            expected[relative] = digest
        payload_names = set(relative_names) - {"MANIFEST.sha256"}
        if set(expected) != payload_names:
            raise ReleaseError("internal checksum manifest does not match archive payload")
        for relative, digest in expected.items():
            actual = sha256(handle.read(prefix + relative))
            if actual != digest:
                raise ReleaseError(f"checksum mismatch inside archive: {relative}")

        metadata = json.loads(handle.read(prefix + "RELEASE.json"))
        if metadata.get("version") != VERSION:
            raise ReleaseError("release metadata version mismatch")
        if metadata.get("application_code_authority") != APP_AUTHORITY:
            raise ReleaseError("release metadata application authority mismatch")
        if metadata.get("monome_release_commit") != MONOME_RELEASE_COMMIT:
            raise ReleaseError("release metadata Monome revision mismatch")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "dist",
        help="directory for the ZIP and its external SHA-256 file",
    )
    parser.add_argument("--verify", type=Path, help="verify an existing archive")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="development-only build from a dirty checkout; never use for publication",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.verify:
            verify_archive(args.verify.resolve())
            print(f"verified {args.verify}")
            return 0
        archive = build_archive(args.output_dir.resolve(), args.allow_dirty)
        digest = sha256(archive.read_bytes())
        print(f"built {archive}")
        print(f"sha256 {digest}")
        return 0
    except ReleaseError as error:
        print(f"release error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
