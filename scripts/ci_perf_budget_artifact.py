#!/usr/bin/env python3
"""Authoritative CI perf-budget artifact (R3-B25-PERF-BUDGET-01 / R3F-HYG-06).

Runs bounded service-path pytest smoke under .audit-sandbox/r3b275-audit.
Does not authorize live sources or touch canonical production DB.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

from backend.app.sync.jobs import plan_backfill_shards

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / ".audit-sandbox" / "r3b275-audit"
ARTIFACT = DATA_ROOT / "production_equivalent_smoke_budget.json"
BUDGET_YAML = PROJECT_ROOT / "specs/contracts/production_equivalent_smoke_budget.yaml"


def collect_scale_metrics(data_root: Path, *, guard_exercised: bool) -> dict[str, object]:
    metrics: dict[str, object] = {
        "data_root": str(data_root),
        "db_exists": False,
        "fetch_log_rows": 0,
        "fetch_log_row_count_sum": 0,
        "resource_guard_log_rows": 0,
        "route_plan_events": 0,
        "sync_job_rows": 0,
        "shard_count_benchmark": len(plan_backfill_shards(date(2026, 1, 1), date(2026, 3, 31))),
        "guard_status": "observable" if guard_exercised else "not_exercised",
    }
    db_path = data_root / "duckdb" / "quant_monitor.duckdb"
    if not db_path.exists():
        return metrics
    metrics["db_exists"] = True
    try:
        import duckdb

        con = duckdb.connect(str(db_path), read_only=True)
        try:
            metrics["fetch_log_rows"] = con.execute("SELECT COUNT(*) FROM fetch_log").fetchone()[0]
            metrics["fetch_log_row_count_sum"] = con.execute(
                "SELECT COALESCE(SUM(row_count), 0) FROM fetch_log"
            ).fetchone()[0]
            metrics["resource_guard_log_rows"] = con.execute(
                "SELECT COUNT(*) FROM resource_guard_log"
            ).fetchone()[0]
            metrics["route_plan_events"] = con.execute(
                """
                SELECT COUNT(*) FROM job_event_log WHERE event_type = 'ROUTE_PLAN'
                """
            ).fetchone()[0]
            metrics["sync_job_rows"] = con.execute("SELECT COUNT(*) FROM data_sync_job").fetchone()[
                0
            ]
        finally:
            con.close()
    except Exception as exc:  # pragma: no cover - diagnostic only
        metrics["db_query_error"] = str(exc)
    return metrics


def run_bounded_service_path_smoke(
    *,
    data_root: Path,
    budget_yaml: Path,
    artifact_path: Path,
    use_service_path: bool = True,
) -> int:
    """Run init/sync-registry + bounded pytest; write threshold-checked artifact."""
    data_root = data_root.resolve()
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
    ]
    if use_service_path:
        steps.extend(
            [
                (
                    "pytest_resource_guard",
                    [sys.executable, "-m", "pytest", "tests/test_resource_guard.py", "-q"],
                ),
                (
                    "pytest_service_path",
                    [
                        sys.executable,
                        "-m",
                        "pytest",
                        "tests/test_source_capabilities.py",
                        "tests/test_source_route_planner.py",
                        "tests/test_datasource_service.py",
                        "tests/test_sync_orchestrator.py::test_plannedJobWritesRoutePlanBeforeFetching",
                        "tests/test_sync_orchestrator.py::test_servicePath_guardBlocked_setsFailedRetryableWithFormattedMessage",
                        "-q",
                    ],
                ),
                (
                    "pytest_vendor_service_e2e",
                    [
                        sys.executable,
                        "-m",
                        "pytest",
                        "tests/test_vendor_fetch_e2e.py::test_vendorFixtureFetch_e2eThroughDataSourceServicePath",
                        "-q",
                    ],
                ),
            ]
        )

    started = time.perf_counter()
    step_count = 0
    guard_exercised = False
    for name, cmd in steps:
        proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT), env=env, check=False)
        if proc.returncode != 0:
            print(f"ci_perf_budget_artifact: FAIL {name} exit={proc.returncode}", file=sys.stderr)
            return proc.returncode
        step_count += 1
        if name == "pytest_resource_guard":
            guard_exercised = True

    elapsed = time.perf_counter() - started
    metrics = collect_scale_metrics(data_root, guard_exercised=guard_exercised)
    metrics["elapsed_s"] = round(elapsed, 2)
    metrics["pytest_steps"] = step_count

    from backend.app.ops.perf_budget import build_smoke_artifact, load_smoke_budget

    budget = load_smoke_budget(budget_yaml)
    artifact = build_smoke_artifact(metrics, budget=budget, use_service_path=use_service_path)
    artifact_path = artifact_path.resolve()
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if artifact["status"] == "FAIL":
        print(
            "ci_perf_budget_artifact: budget FAIL "
            f"violations={json.dumps(artifact['violations'])}",
            file=sys.stderr,
        )
        return 1
    return 0


def main() -> int:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    code = run_bounded_service_path_smoke(
        data_root=DATA_ROOT,
        budget_yaml=BUDGET_YAML,
        artifact_path=ARTIFACT,
        use_service_path=True,
    )
    if code != 0:
        return code
    if not ARTIFACT.is_file():
        print(f"ci_perf_budget_artifact: missing artifact {ARTIFACT}", file=sys.stderr)
        return 1
    print(f"ci_perf_budget_artifact: PASS artifact={ARTIFACT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
