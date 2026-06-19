#!/usr/bin/env python3
"""Production-equivalent smoke runbook (Round2 audit P2-06).

Uses isolated QMD_DATA_ROOT under .audit-sandbox — does not touch project DB or source tree.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

from backend.app.sync.jobs import plan_backfill_shards

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _collect_scale_metrics(data_root: Path, *, guard_exercised: bool) -> dict[str, object]:
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Production-equivalent smoke")
    parser.add_argument(
        "--use-service-path",
        action="store_true",
        help="Run service-path pytest suite (capability→route→service)",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=PROJECT_ROOT / ".audit-sandbox" / "prod-equiv-smoke",
        help="Isolated QMD_DATA_ROOT (default: .audit-sandbox/prod-equiv-smoke)",
    )
    args = parser.parse_args()

    data_root = args.data_root.resolve()
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

    if args.use_service_path:
        steps.extend(
            [
                (
                    "pytest_resource_guard",
                    [
                        sys.executable,
                        "-m",
                        "pytest",
                        "tests/test_resource_guard.py",
                        "-q",
                    ],
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
    else:
        steps.extend(
            [
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
        )

    started = time.perf_counter()
    step_count = 0
    guard_exercised = False
    for name, cmd in steps:
        proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT), env=env, check=False)
        if proc.returncode != 0:
            print(f"FAIL: {name} exit={proc.returncode}", file=sys.stderr)
            return proc.returncode
        step_count += 1
        if name == "pytest_resource_guard":
            guard_exercised = True
        print(f"PASS: {name}")

    elapsed = time.perf_counter() - started
    metrics = _collect_scale_metrics(data_root, guard_exercised=guard_exercised)
    metrics["elapsed_s"] = round(elapsed, 2)
    metrics["pytest_steps"] = step_count
    print(f"production_equivalent_smoke: ALL PASS metrics={json.dumps(metrics, sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
