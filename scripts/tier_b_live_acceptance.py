#!/usr/bin/env python3
"""Tier B live acceptance CLI (M-DATA-03 AC-7 · validation_fetch).

Exit codes:
  0 — all requested sources pass validation_fetch
  1 — any source failure
  2 — invalid env (no QMD_ALLOW_LIVE_FETCH / main DB / missing keys)
"""

from __future__ import annotations

import argparse
import sys

from backend.app.ops.tier_b_live_acceptance import (
    TierBLiveEnvError,
    run_acceptance,
    run_acceptance_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Tier B live validation_fetch acceptance (isolated DATA_ROOT)"
    )
    parser.add_argument("--source-id", default=None, help="Single Tier B source (default: 10/10)")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Pilot subset: yahoo_finance + akshare",
    )
    parser.add_argument(
        "--data-root",
        default=None,
        help="Isolated DATA_ROOT (must be under .audit-sandbox/m-data-03/tier-b)",
    )
    parser.add_argument(
        "--report",
        default=None,
        metavar="PATH",
        help="Write TierBLiveAcceptanceReport JSON (live_tier_b_evidence_v1)",
    )
    args = parser.parse_args(argv)

    try:
        if args.report:
            return run_acceptance_report(
                args.report,
                source_id=args.source_id,
                quick=args.quick,
                data_root=args.data_root,
            )
        return run_acceptance(
            source_id=args.source_id,
            quick=args.quick,
            data_root=args.data_root,
        )
    except TierBLiveEnvError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
