#!/usr/bin/env python3
"""Production-equivalent smoke runbook (Round2 audit P2-06).

Uses isolated QMD_DATA_ROOT under .audit-sandbox — does not touch project DB or source tree.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    data_root = PROJECT_ROOT / ".audit-sandbox" / "prod-equiv-smoke"
    data_root.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["QMD_DATA_ROOT"] = str(data_root)
    env["PYTHONPATH"] = str(PROJECT_ROOT)

    steps: list[tuple[str, list[str]]] = [
        ("init_db", [sys.executable, "scripts/init_db.py"]),
        (
            "sync_registry",
            [
                sys.executable,
                "scripts/sync_registry.py",
                "--yaml",
                str(PROJECT_ROOT / "specs/datasource_registry/source_registry.yaml"),
            ],
        ),
        (
            "pytest_prod_path",
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_sync_orchestrator.py::test_syncRegistry_cli_syncsYamlToDb",
                "-q",
            ],
        ),
        (
            "pytest_vendor_e2e",
            [sys.executable, "-m", "pytest", "tests/test_vendor_fetch_e2e.py", "-q"],
        ),
    ]

    for name, cmd in steps:
        proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT), env=env, check=False)
        if proc.returncode != 0:
            print(f"FAIL: {name} exit={proc.returncode}", file=sys.stderr)
            return proc.returncode
        print(f"PASS: {name}")

    print("production_equivalent_smoke: ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
