"""Shared qmd_ops db-inspect CLI subprocess helpers for ops contract tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_qmd_db_inspect_cli(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(_PROJECT_ROOT / "scripts" / "qmd_ops.py"), "db-inspect", *args]
    return subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=_PROJECT_ROOT)


def parse_cli_json(result: subprocess.CompletedProcess[str]) -> dict:
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)
