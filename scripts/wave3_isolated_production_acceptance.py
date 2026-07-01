#!/usr/bin/env python3
"""Wave 1–3 isolated production-chain acceptance (no canonical main-DB writes).

Writes evidence JSON under .audit-sandbox/wave3-acceptance-<run_id>/.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUN_ID = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
ACCEPT_ROOT = PROJECT_ROOT / ".audit-sandbox" / f"wave3-acceptance-{RUN_ID}"
DATA_ROOT = ACCEPT_ROOT / "data"
ARTIFACT = ACCEPT_ROOT / "acceptance_evidence.json"


def _fingerprint(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {"exists": False, "path": str(path)}
    stat = path.stat()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "exists": True,
        "path": str(path),
        "size": stat.st_size,
        "mtime": stat.st_mtime,
        "sha256": digest,
    }


def _run(
    name: str,
    cmd: list[str],
    *,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> dict[str, object]:
    started = time.perf_counter()
    proc = subprocess.run(
        cmd,
        cwd=str(cwd or PROJECT_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "name": name,
        "cmd": cmd,
        "exit_code": proc.returncode,
        "elapsed_s": round(time.perf_counter() - started, 2),
        "stdout_tail": proc.stdout[-4000:] if proc.stdout else "",
        "stderr_tail": proc.stderr[-4000:] if proc.stderr else "",
        "pass": proc.returncode == 0,
    }


def main() -> int:
    from backend.app.config import DATA_ROOT as CONFIG_DATA_ROOT

    canonical_main = (CONFIG_DATA_ROOT / "duckdb" / "quant_monitor.duckdb").resolve()
    ACCEPT_ROOT.mkdir(parents=True, exist_ok=True)
    isolated_root = ACCEPT_ROOT / "data"
    isolated_root.mkdir(parents=True, exist_ok=True)

    base_env = os.environ.copy()
    base_env["PYTHONPATH"] = str(PROJECT_ROOT)
    base_env["QMD_DATA_ROOT"] = str(isolated_root)
    base_env["QMD_ALLOW_LIVE_FETCH"] = "1"
    base_env["QMD_FRED_INCREMENTAL_USE_MOCK"] = "1"

    report: dict[str, object] = {
        "run_id": RUN_ID,
        "accept_root": str(ACCEPT_ROOT),
        "isolated_data_root": str(isolated_root),
        "canonical_main_db_before": _fingerprint(canonical_main),
        "steps": [],
        "findings": [],
    }

    steps: list[tuple[str, list[str], dict[str, str] | None]] = [
        ("production_gate", [sys.executable, "scripts/production_gate.py"], None),
        (
            "init_db",
            [sys.executable, "scripts/init_db.py"],
            base_env,
        ),
        (
            "sync_registry",
            [
                sys.executable,
                "scripts/sync_registry.py",
                "--yaml",
                str(PROJECT_ROOT / "specs/datasource_registry/source_registry.yaml"),
            ],
            base_env,
        ),
        (
            "pytest_full",
            [sys.executable, "-m", "pytest", "-q", "--tb=no"],
            base_env,
        ),
        (
            "prod_equiv_smoke",
            [
                sys.executable,
                "scripts/production_equivalent_smoke.py",
                "--use-service-path",
                "--data-root",
                str(ACCEPT_ROOT / "prod-equiv-nested"),
                "--write-artifact",
                str(ACCEPT_ROOT / "prod_equiv_budget.json"),
            ],
            base_env,
        ),
        (
            "round3_gate_matrix",
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_round3_verification_command_matrix.py",
                "tests/test_unresolved_item_task_coverage.py",
                "tests/test_round3_audit_registry_alignment.py",
                "tests/test_production_live_pilot_policy.py",
                "-q",
                "--tb=no",
            ],
            base_env,
        ),
        (
            "wave3_dcp_tests",
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_baostock_incremental_watermark.py",
                "tests/test_baostock_incremental_e2e.py",
                "tests/test_fred_macro_incremental_watermark.py",
                "tests/test_fred_macro_incremental_e2e.py",
                "tests/test_fred_macro_incremental_cli.py",
                "tests/test_incremental_post_write_inspect.py",
                "tests/test_qmd_data_cli.py",
                "-q",
                "--tb=no",
            ],
            base_env,
        ),
        (
            "qmd_route_preview",
            [
                sys.executable,
                "-m",
                "backend.app.cli.main",
                "data",
                "route-preview",
                "--domain",
                "cn_equity_daily_bar",
                "--operation",
                "fetch_daily_bar",
            ],
            base_env,
        ),
        (
            "qmd_baostock_sync_dry_run",
            [
                sys.executable,
                "-m",
                "backend.app.cli.main",
                "data",
                "sync",
                "--domain",
                "cn_equity_daily_bar",
                "--dry-run",
            ],
            base_env,
        ),
        (
            "qmd_fred_sync_execute_mock",
            [
                sys.executable,
                "-m",
                "backend.app.cli.main",
                "data",
                "sync",
                "--domain",
                "macro_series",
                "--source-id",
                "fred",
                "--no-dry-run",
            ],
            base_env,
        ),
        (
            "loop_maintain_check",
            [sys.executable, "scripts/loop_maintain.py"],
            base_env,
        ),
    ]

    step_results: list[dict[str, object]] = []
    failed = 0
    for name, cmd, env in steps:
        result = _run(name, cmd, env=env or base_env)
        step_results.append(result)
        if not result["pass"]:
            failed += 1
            report["findings"].append(
                {
                    "id": f"ACC-{name.upper()}",
                    "severity": "BLOCKING" if name in {"pytest_full", "production_gate"} else "HIGH",
                    "step": name,
                    "message": f"acceptance step failed exit={result['exit_code']}",
                }
            )

    report["steps"] = step_results
    report["canonical_main_db_after"] = _fingerprint(canonical_main)
    before = report["canonical_main_db_before"]
    after = report["canonical_main_db_after"]
    if before.get("sha256") != after.get("sha256") or before.get("mtime") != after.get("mtime"):
        report["findings"].append(
            {
                "id": "ACC-MAIN-DB-POLLUTION",
                "severity": "CRITICAL",
                "message": "canonical main DB fingerprint changed during acceptance",
                "before": before,
                "after": after,
            }
        )
        failed += 1
    else:
        report["main_db_pollution"] = False

    isolated_db = isolated_root / "duckdb" / "quant_monitor.duckdb"
    report["isolated_db"] = _fingerprint(isolated_db)
    report["summary"] = {
        "steps_total": len(step_results),
        "steps_failed": failed,
        "pass": failed == 0,
    }
    ARTIFACT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    print(f"evidence: {ARTIFACT}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
