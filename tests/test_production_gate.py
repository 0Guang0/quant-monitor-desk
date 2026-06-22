"""ADV-A5-002: production_gate.py smoke tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_productionGate_exitsZero() -> None:
    script = PROJECT_ROOT / "scripts" / "production_gate.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "production_gate: PASS" in result.stdout
