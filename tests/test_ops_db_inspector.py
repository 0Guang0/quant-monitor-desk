"""Ops DB inspector tests (Round 3 Batch 1)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.ops.db_inspector import (
    REQUIRED_TOP_LEVEL_FIELDS,
    DbInspector,
)


def _init_db(db_path: Path) -> None:
    con = duckdb.connect(str(db_path))
    apply_migrations(con)
    con.close()


def _seed_evidence(db_path: Path) -> None:
    _init_db(db_path)
    cm = ConnectionManager(db_path)
    with cm.writer() as con:
        con.execute(
            """
            INSERT INTO fetch_log (
                fetch_id, run_id, source_id, data_domain, status, row_count, fetch_time
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            ["f-1", "run-1", "baostock", "market_bar_1d", "SUCCESS", 42],
        )
        con.execute(
            """
            INSERT INTO data_sync_job (
                job_id, run_id, job_type, status, created_at
            ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            ["job-1", "run-1", "backfill", "COMPLETED"],
        )


def test_dbInspect_missingDb_returnsFail(tmp_path: Path) -> None:
    missing = tmp_path / "missing.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir()
    report = DbInspector(missing, data_root).inspect()
    assert report.status == "FAIL"
    assert report.db["exists"] is False
    assert report.db["read_only_open"] is False
    assert report.errors
    assert any("not found" in err.lower() for err in report.errors)


def test_dbInspect_deferredItemMapping_nonEmpty(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _init_db(db)
    report = DbInspector(db, tmp_path).inspect()
    assert report.deferred_item_mapping
    item_ids = {entry["item_id"] for entry in report.deferred_item_mapping}
    assert item_ids >= {
        "DB-R3-001",
        "DB-R3-002",
        "R3-PARTIAL-2",
        "R2.6-IMPL-8",
        "R3-EARLY-DB-INSPECT-CLI",
    }
    for entry in report.deferred_item_mapping:
        assert entry["evidence_fields"]


def test_dbInspect_dbFile_unchanged(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _init_db(db)
    before = db.read_bytes()
    DbInspector(db, tmp_path).inspect()
    after = db.read_bytes()
    assert before == after


def test_dbInspect_emptySchemaDb_returnsWarn(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _init_db(db)
    report = DbInspector(db, tmp_path).inspect()
    assert report.status == "WARN"
    assert report.db["read_only_open"] is True
    assert report.schema["table_count"] > 0
    assert any(t["name"] == "schema_version" and t["exists"] for t in report.key_tables)


def test_dbInspect_outputJsonShape_hasRequiredFields(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _init_db(db)
    payload = DbInspector(db, tmp_path).inspect().to_dict()
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        assert field in payload
    assert payload["mode"] == "read_only"
    assert payload["status"] in {"PASS", "WARN", "FAIL"}
    json.dumps(payload)


def test_dbInspect_fixtureWithEvidence_reportsCounts(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _seed_evidence(db)
    report = DbInspector(db, tmp_path).inspect()
    fetch_table = next(t for t in report.key_tables if t["name"] == "fetch_log")
    assert fetch_table["exists"] is True
    assert fetch_table["row_count"] == 1
    assert report.evidence["latest_fetch"]["source_id"] == "baostock"
    assert report.evidence["latest_fetch"]["row_count"] == 42
    assert report.evidence["job_status_counts"].get("COMPLETED") == 1


def test_dbInspect_pathScan_staysUnderDataRoot(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _init_db(db)
    data_root = tmp_path / "data"
    raw_dir = data_root / "raw" / "vendor"
    raw_dir.mkdir(parents=True)
    (raw_dir / "sample.csv").write_text("x", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.parquet").write_text("x", encoding="utf-8")

    report = DbInspector(db, data_root, limit=5).inspect()
    assert report.data_root["raw_files_count"] == 1
    assert report.data_root["parquet_files_count"] == 0
    assert report.data_root["scan_limited"] is False


def test_dbInspect_limit_hardCapsAtContractMaximum(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _init_db(db)
    data_root = tmp_path / "data"
    raw_dir = data_root / "raw"
    raw_dir.mkdir(parents=True)
    for i in range(110):
        (raw_dir / f"sample-{i}.csv").write_text("x", encoding="utf-8")

    report = DbInspector(db, data_root, limit=500).inspect()
    assert report.data_root["raw_files_count"] == 100
    assert report.data_root["scan_limited"] is True


def test_dbInspect_pathOutsideDataRoot_rejectedFromScan(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _init_db(db)
    data_root = tmp_path / "data"
    data_root.mkdir()
    outside = tmp_path / "outside-secrets"
    outside.mkdir()
    for i in range(5):
        (outside / f"leak-{i}.parquet").write_text("x", encoding="utf-8")

    assert len(list(outside.glob("*.parquet"))) == 5

    report = DbInspector(db, data_root, include_path_check=True).inspect()
    assert report.data_root["path"] == str(data_root)
    assert report.data_root["exists"] is True
    assert report.data_root["parquet_files_count"] == 0
    assert report.data_root["raw_files_count"] == 0
    assert report.data_root["scan_limited"] is False


def test_dbInspect_limit_floorClampsToMinimumOne(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _init_db(db)
    data_root = tmp_path / "data"
    raw_dir = data_root / "raw"
    raw_dir.mkdir(parents=True)
    for i in range(5):
        (raw_dir / f"sample-{i}.csv").write_text("x", encoding="utf-8")

    report = DbInspector(db, data_root, limit=0).inspect()
    assert report.data_root["raw_files_count"] == 1
    assert report.data_root["scan_limited"] is True


def test_qmdOps_cli_limitHardCapsAtContractMaximum(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _init_db(db)
    data_root = tmp_path / "data"
    raw_dir = data_root / "raw"
    raw_dir.mkdir(parents=True)
    for i in range(110):
        (raw_dir / f"sample-{i}.csv").write_text("x", encoding="utf-8")

    project_root = Path(__file__).resolve().parents[1]
    cmd = [
        sys.executable,
        str(project_root / "scripts" / "qmd_ops.py"),
        "db-inspect",
        "--db",
        str(db),
        "--data-root",
        str(data_root),
        "--limit",
        "500",
        "--format",
        "json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=project_root)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["data_root"]["raw_files_count"] == 100
    assert payload["data_root"]["scan_limited"] is True


def test_qmdOps_cli_invokesSameInspector(tmp_path: Path, monkeypatch) -> None:
    db = tmp_path / "t.duckdb"
    _init_db(db)
    data_root = tmp_path / "data"
    data_root.mkdir()
    project_root = Path(__file__).resolve().parents[1]
    cmd = [
        sys.executable,
        str(project_root / "scripts" / "qmd_ops.py"),
        "db-inspect",
        "--db",
        str(db),
        "--data-root",
        str(data_root),
        "--format",
        "json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=project_root)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["mode"] == "read_only"
    assert payload["db"]["read_only_open"] is True
    assert "deferred_item_mapping" in payload


def test_dbInspect_symlinkOutsideDataRoot_notCounted(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _init_db(db)
    data_root = tmp_path / "data"
    raw_dir = data_root / "raw"
    raw_dir.mkdir(parents=True)
    outside = tmp_path / "outside-secrets"
    outside.mkdir()
    (outside / "leak.parquet").write_text("x", encoding="utf-8")
    try:
        raw_dir.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported on this platform")

    report = DbInspector(db, data_root, include_path_check=True).inspect()
    assert report.data_root["parquet_files_count"] == 0
    assert report.data_root["raw_files_count"] == 0


def test_qmdOps_cli_rejectsForbiddenSqlFlag(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    cmd = [
        sys.executable,
        str(project_root / "scripts" / "qmd_ops.py"),
        "db-inspect",
        "--sql",
        "SELECT 1",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=project_root)
    assert result.returncode != 0


def test_qmdOps_cli_rejectsForbiddenEnableQmtFlag(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    cmd = [
        sys.executable,
        str(project_root / "scripts" / "qmd_ops.py"),
        "db-inspect",
        "--enable-qmt",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=project_root)
    assert result.returncode != 0


def test_dbInspect_includePathCheckDisabled_skipsScanCounts(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _init_db(db)
    data_root = tmp_path / "data"
    raw_dir = data_root / "raw"
    raw_dir.mkdir(parents=True)
    (raw_dir / "sample.csv").write_text("x", encoding="utf-8")

    report = DbInspector(db, data_root, include_path_check=False).inspect()
    assert report.data_root["raw_files_count"] == 0
    assert report.data_root["parquet_files_count"] == 0
    assert report.data_root["scan_limited"] is False


def test_qmdOps_cli_jsonRoundTripsStrictly(tmp_path: Path) -> None:
    db = tmp_path / "t.duckdb"
    _init_db(db)
    data_root = tmp_path / "data"
    data_root.mkdir()
    project_root = Path(__file__).resolve().parents[1]
    cmd = [
        sys.executable,
        str(project_root / "scripts" / "qmd_ops.py"),
        "db-inspect",
        "--db",
        str(db),
        "--data-root",
        str(data_root),
        "--format",
        "json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=project_root)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    json.dumps(payload)
