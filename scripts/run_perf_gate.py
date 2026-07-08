#!/usr/bin/env python3
"""Run opt-in pytest wall-clock perf gates (P5 / Slice B)."""

from __future__ import annotations

import argparse

from scripts.perf_gate_profiles import PROFILES, run_profiles


def main() -> int:
    parser = argparse.ArgumentParser(description="Run wall-clock pytest perf gates (QMD_PERF_GATE).")
    parser.add_argument(
        "--profile",
        choices=[*PROFILES.keys(), "all"],
        default="all",
        help="Profile to measure (default: all sequentially)",
    )
    args = parser.parse_args()
    names = tuple(PROFILES.keys()) if args.profile == "all" else (args.profile,)
    if args.profile == "all":
        print(
            "perf_gate: running quick + full + ci-parallel "
            f"(expect ~{sum(p.budget_sec for p in PROFILES.values()):.0f}s wall-clock budget sum on cold run)",
            flush=True,
        )
    return run_profiles(names)


if __name__ == "__main__":
    raise SystemExit(main())
