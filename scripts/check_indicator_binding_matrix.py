#!/usr/bin/env python3
"""M-G1-03 P1-01 — 62×指标绑定矩阵校验（SSOT: indicator_binding_registry.yaml）."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY = REPO_ROOT / "specs/layer1_axes/indicator_binding_registry.yaml"
EXPECTED_ROWS = 62


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Layer1 indicator binding matrix")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Phase 2: adr_id must not be PENDING; all bindings complete",
    )
    args = parser.parse_args(argv)
    if not REGISTRY.is_file():
        print(f"RED: missing registry {REGISTRY.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 1
    # ponytail: row/schema validation implemented in P1-01 Execute
    print("RED: registry loader/schema checks not implemented (M-G1-03 S01)", file=sys.stderr)
    if args.strict:
        print("RED: --strict requires Phase 2 matrix fill", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
