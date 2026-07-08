"""Promote frozen design artifacts into runtime mirror paths (design -> runtime only)."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Shown by tests/test_design_runtime_parity.py on FAIL. SSOT for remediation wording.
PARITY_FAILURE_REMEDIATION = (
    "design/runtime parity drift detected. "
    "Fix ONLY with: uv run python scripts/promote_design_runtime.py (design -> runtime). "
    "NEVER edit **/design/** files to match runtime mirrors just to pass tests. "
    "If the spec must change: edit design/ after explicit user review (+ ADR when required), then promote."
)

FILE_PAIRS: tuple[tuple[str, str], ...] = (
    ("specs/contracts/design/resource_limits.yaml", "specs/contracts/resource_limits.yaml"),
    (
        "specs/contracts/design/source_conflict_rules.yaml",
        "specs/contracts/source_conflict_rules.yaml",
    ),
)

DIR_PAIRS: tuple[tuple[str, str], ...] = (
    (
        "specs/layer1_axes/design/restructured_axes_v1_1",
        "specs/layer1_axes/restructured_axes_v1_1",
    ),
)


def promote(*, dry_run: bool = False) -> list[str]:
    """Copy design paths to runtime mirrors. Returns promoted relative paths."""
    promoted: list[str] = []
    for design_rel, runtime_rel in FILE_PAIRS:
        design = ROOT / design_rel
        runtime = ROOT / runtime_rel
        if not design.is_file():
            raise FileNotFoundError(f"missing design file: {design_rel}")
        if dry_run:
            promoted.append(runtime_rel)
            continue
        runtime.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(design, runtime)
        promoted.append(runtime_rel)
    for design_rel, runtime_rel in DIR_PAIRS:
        design = ROOT / design_rel
        runtime = ROOT / runtime_rel
        if not design.is_dir():
            raise FileNotFoundError(f"missing design directory: {design_rel}")
        if dry_run:
            promoted.append(runtime_rel)
            continue
        if runtime.exists():
            shutil.rmtree(runtime)
        shutil.copytree(design, runtime)
        promoted.append(runtime_rel)
    return promoted


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Promote MIGRATION_MAP design artifacts to runtime mirror paths",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List runtime targets without writing",
    )
    args = parser.parse_args(argv)
    paths = promote(dry_run=args.dry_run)
    verb = "would promote" if args.dry_run else "promoted"
    for rel in paths:
        print(f"promote_design_runtime: {verb} {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
