#!/usr/bin/env python3
"""Authoritative CI perf-budget artifact (R3-B25-PERF-BUDGET-01 / R3F-HYG-06).

Runs bounded production_equivalent_smoke under .audit-sandbox/r3b275-audit.
Does not authorize live sources or touch canonical production DB.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / ".audit-sandbox" / "r3b275-audit"
ARTIFACT = DATA_ROOT / "production_equivalent_smoke_budget.json"
BUDGET_YAML = PROJECT_ROOT / "specs/contracts/production_equivalent_smoke_budget.yaml"


def main() -> int:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "scripts/production_equivalent_smoke.py",
        "--use-service-path",
        "--data-root",
        str(DATA_ROOT),
        "--write-artifact",
        str(ARTIFACT),
        "--budget-yaml",
        str(BUDGET_YAML),
    ]
    proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT), check=False)
    if proc.returncode != 0:
        print(f"ci_perf_budget_artifact: FAIL exit={proc.returncode}", file=sys.stderr)
        return proc.returncode
    if not ARTIFACT.is_file():
        print(f"ci_perf_budget_artifact: missing artifact {ARTIFACT}", file=sys.stderr)
        return 1
    print(f"ci_perf_budget_artifact: PASS artifact={ARTIFACT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
