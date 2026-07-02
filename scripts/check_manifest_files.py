#!/usr/bin/env python3
"""Verify MANIFEST.json listed files exist (optional sha256 check)."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "MANIFEST.json"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def check_manifest(
    manifest_path: Path = DEFAULT_MANIFEST,
    *,
    verify_hash: bool = False,
) -> list[str]:
    errors: list[str] = []
    if not manifest_path.is_file():
        return [f"missing manifest: {manifest_path.relative_to(REPO_ROOT)}"]

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in data.get("files", []):
        rel = entry.get("path")
        if not rel:
            errors.append("manifest entry missing path")
            continue
        from repo_path_resolve import resolve_repo_path

        path = resolve_repo_path(rel)
        if not path.is_file():
            errors.append(f"missing file: {rel}")
            continue
        if verify_hash:
            expected = entry.get("sha256")
            if expected:
                actual = _sha256(path)
                if actual != expected:
                    errors.append(f"hash mismatch: {rel}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Check MANIFEST.json file existence")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--verify-hash", action="store_true")
    args = parser.parse_args()
    errors = check_manifest(args.manifest, verify_hash=args.verify_hash)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    print("OK: manifest files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
