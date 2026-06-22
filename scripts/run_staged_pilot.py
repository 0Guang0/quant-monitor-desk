"""Thin CLI wrapper for PROMPT_14 staged real-data pilot."""

from __future__ import annotations

import argparse
from pathlib import Path

from backend.app.config import PROJECT_ROOT
from backend.app.ops.staged_pilot import (
    DEFAULT_SANDBOX_ROOT,
    run_full_staged_pilot,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run R3X staged real-data pilot (bounded)")
    parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=PROJECT_ROOT
        / ".trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence",
        help="Directory for pilot evidence artifacts",
    )
    parser.add_argument(
        "--sandbox-root",
        type=Path,
        default=DEFAULT_SANDBOX_ROOT,
        help="Sandbox data root for raw/staging evidence",
    )
    parser.add_argument(
        "--skip-live-fetch",
        action="store_true",
        help="Route preview + validation only (no network fetch)",
    )
    args = parser.parse_args()

    result = run_full_staged_pilot(
        args.evidence_dir,
        sandbox_root=args.sandbox_root,
        skip_live_fetch=args.skip_live_fetch,
    )
    print(f"staged pilot outcome: {result['outcome']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
