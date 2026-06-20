"""A6 audit-perf: micro-fetch ENV-E1-DGS10 elapsed + RSS (eco profile)."""

from __future__ import annotations

import gc
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import tracemalloc
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
AUDIT_SANDBOX = PROJECT_ROOT / ".audit-sandbox" / "r3b25-audit"
AUDIT_PROD_ROOT = PROJECT_ROOT / ".audit-sandbox" / "r3b25-audit-prod-equiv"
PROD_DATA = PROJECT_ROOT / "data"
PROD_DB = PROD_DATA / "duckdb" / "quant_monitor.duckdb"
FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "layer1_macro_observation_fixture.json"
INDICATOR = "ENV-E1-DGS10"
AS_OF = date(2024, 6, 15)
THRESHOLDS = {"elapsed_s_max": 5.0, "rss_mb_max": 512.0}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def setup_cli_sandbox() -> Path:
    data_root = AUDIT_SANDBOX / "data"
    if data_root.exists():
        shutil.rmtree(data_root)
    data_root.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["QMD_DATA_ROOT"] = str(data_root)
    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "init_db.py")],
        cwd=PROJECT_ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return data_root


def setup_prod_equiv_copy() -> Path:
    dest = AUDIT_PROD_ROOT / "data"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(PROD_DATA, dest)
    return dest


def measure_micro_fetch(data_root: Path) -> dict:
    os.environ["QMD_DATA_ROOT"] = str(data_root)
    os.environ["QMD_RESOURCE_PROFILE"] = "eco"

    import psutil

    import duckdb
    from backend.app.core.resource_guard import ResourceGuard
    from backend.app.datasources.service import build_staged_fixture_service
    from backend.app.layer1_axes.ingestion import Layer1ObservationIngestionService

    db_path = data_root / "duckdb" / "quant_monitor.duckdb"
    if not db_path.is_file():
        con = duckdb.connect(str(db_path))
        from backend.app.db.migrate import apply_migrations

        apply_migrations(con)
        con.close()

    datasource = build_staged_fixture_service(data_root=data_root, fixture_path=FIXTURE)
    service = Layer1ObservationIngestionService(
        db_path=db_path,
        data_root=data_root,
        datasource=datasource,
    )

    proc = psutil.Process()
    gc.collect()
    tracemalloc.start()
    t0 = time.perf_counter()
    result = service.micro_fetch_staging(indicator_id=INDICATOR, as_of=AS_OF)
    elapsed = time.perf_counter() - t0
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    rss_mb = proc.memory_info().rss / (1024 * 1024)

    guard = ResourceGuard()
    decision, reason = guard.check()

    return {
        "elapsed_s": round(elapsed, 4),
        "rss_after_mb": round(rss_mb, 2),
        "peak_traced_bytes": peak,
        "row_count": result.fetch_result.row_count,
        "fetch_status": result.fetch_result.status,
        "resource_guard_decision": decision.value,
        "resource_guard_reason": reason,
        "data_root": str(data_root.relative_to(PROJECT_ROOT)),
        "profile": "eco",
        "indicator_id": INDICATOR,
    }


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"cli-sandbox", "audit-prod-path"}:
        print("usage: a6_perf_benchmark.py cli-sandbox|audit-prod-path", file=sys.stderr)
        return 2

    label = sys.argv[1]
    if label == "cli-sandbox":
        data_root = setup_cli_sandbox()
    else:
        data_root = setup_prod_equiv_copy()

    metrics = measure_micro_fetch(data_root)
    metrics["label"] = label
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
