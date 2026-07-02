#!/usr/bin/env python3
"""Tier A live acceptance CLI (M-DATA-03 S00-INFRA · ADR-034).

Exit codes:
  0 — all requested sources pass sync (inspect/health in S-ACCEPT)
  1 — any source sync failure
  2 — invalid env (no QMD_ALLOW_LIVE_FETCH / main DB / missing keys)
"""

from __future__ import annotations

import argparse
import sys

from backend.app.ops.tier_a_live_acceptance import TierALiveEnvError, run_acceptance


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tier A live acceptance (isolated DATA_ROOT)")
    parser.add_argument("--source-id", default=None, help="Single Tier A source (default: 11/11)")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Pilot subset: fred + baostock",
    )
    parser.add_argument(
        "--data-root",
        default=None,
        help="Isolated DATA_ROOT (must be under .audit-sandbox/m-data-03)",
    )
    args = parser.parse_args(argv)

    try:
        return run_acceptance(
            source_id=args.source_id,
            quick=args.quick,
            data_root=args.data_root,
        )
    except TierALiveEnvError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
