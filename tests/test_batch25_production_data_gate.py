"""Batch 2.5 production-data readiness gate tests.

These tests intentionally inspect the Batch 2.5 evidence and current local data root.
They do not modify production code or production data. Their purpose is to prevent
staged/fixture evidence from being promoted to production-live readiness by wording drift.
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb

from tests.contract_gate_support import PROJECT_ROOT


TASK_DIR = PROJECT_ROOT / ".trellis/tasks/06-20-round3-batch2-5-layer1-obs-ingest"
EVIDENCE_DIR = TASK_DIR / "execute-evidence"


def _read_text(path: Path) -> str:
    assert path.is_file(), f"missing evidence file: {path}"
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> dict:
    assert path.is_file(), f"missing evidence file: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def _table_count(con: duckdb.DuckDBPyConnection, table_name: str) -> int:
    exists = con.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'main' AND table_name = ?
        """,
        [table_name],
    ).fetchone()[0]
    assert exists == 1, f"expected table to exist: {table_name}"
    return int(con.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0])


def test_batch25_deferredItems_documentedInRegistries() -> None:
    """All active Batch 2.5 DEFERRED IDs must appear in authoritative registries with closure hooks."""
    deferred_ids = ("B2.5-O-02", "B2.5-O-03", "B2.5-O-05", "B2.5-O-06")
    audit_deferred = _read_text(PROJECT_ROOT / "docs/AUDIT_DEFERRED_REGISTRY.md")
    unresolved = _read_text(PROJECT_ROOT / "docs/UNRESOLVED_ISSUES_REGISTRY.md")
    task_register = _read_text(TASK_DIR / "research/batch25-deferred-items.md")
    final_registry = _read_text(EVIDENCE_DIR / "final_registry_update.md")

    for item_id in deferred_ids:
        assert f"| {item_id} |" in audit_deferred
        assert f"| {item_id} |" in unresolved
        assert item_id in task_register
        assert "DEFERRED" in task_register or "Deferred" in task_register
        assert item_id in final_registry

    resolved_ids = ("B2.5-O-04", "B2.5-O-07")
    resolved = _read_text(PROJECT_ROOT / "docs/RESOLVED_ISSUES_REGISTRY.md")
    for item_id in resolved_ids:
        assert item_id in resolved


def test_batch25_evidence_is_staged_not_production_live() -> None:
    """Batch 2.5 evidence must not be interpreted as production-live ingestion."""
    master = _read_text(TASK_DIR / "MASTER.plan.md")
    registry = _read_text(PROJECT_ROOT / "docs/AUDIT_DEFERRED_REGISTRY.md")
    phase1_classification = _read_text(EVIDENCE_DIR / "phase1_data_classification.md")
    phase2 = _read_json(EVIDENCE_DIR / "phase2_route_preview.json")
    phase4 = _read_json(EVIDENCE_DIR / "phase4_clean_write_and_snapshot_evidence.json")

    assert "**staged/fixture**（非 live production）" in master
    assert "B2.5-O-05" in master
    assert "**DEFERRED**" in master
    assert "| B2.5-O-05 |" in registry
    assert "User-authorized live" in registry
    assert "live requires auth evidence" in registry

    assert "external_user_auth_required | false" in phase1_classification
    assert "Are data-root files production live vendor ingestion? | **No**" in phase1_classification
    assert "Are DB rows production observation writes?            | **No**" in phase1_classification

    assert phase2["dry_run"] is True
    assert phase2["fred_primary_deferred"] is True
    preview = phase2["previews"][0]
    assert preview["binding"]["primary_source_declared"] == "FRED:DGS10"
    assert preview["binding"]["data_domain"] == "macro_supplementary"
    assert preview["binding"]["operation"] == "fetch_macro_series"
    assert "deferred" in preview["binding"]["staged_route_note"].lower()
    assert preview["route_plan"]["selected_source_id"] == "akshare"

    assert phase4["phase1_baseline_classification"] == "fixture_or_staged_evidence"
    assert ".phase4-clean-write-sandbox" in phase4["evidence_db_path"]
    assert phase4["commit"]["staged_fixture_path"].startswith("tests/fixtures/")
    assert "deferred" in phase4["commit"]["fred_primary_deferred_note"].lower()


def test_current_target_db_has_no_clean_layer1_production_observations() -> None:
    """The current target DB must not contain clean Layer 1 rows promoted as production data."""
    db_path = PROJECT_ROOT / "data/duckdb/quant_monitor.duckdb"
    assert db_path.is_file(), "target DB should exist before readiness is evaluated"

    con = duckdb.connect(str(db_path), read_only=True)
    try:
        assert _table_count(con, "fetch_log") == 0
        assert _table_count(con, "validation_report") == 0
        assert _table_count(con, "write_audit_log") == 0
        assert _table_count(con, "axis_observation") == 0
        assert _table_count(con, "axis_feature_snapshot") == 0
        assert _table_count(con, "axis_interpretation_snapshot") == 0
        assert _table_count(con, "axis_snapshot_lineage") == 0
    finally:
        con.close()


def test_current_raw_data_root_contains_only_staged_batch25_fixture_payloads() -> None:
    """Any non-placeholder current raw files for Batch 2.5 must remain staged fixture evidence."""
    raw_root = PROJECT_ROOT / "data/raw"
    raw_files = sorted(p for p in raw_root.rglob("*") if p.is_file() and p.name != ".gitkeep")
    assert raw_files, "expected current Batch 2.5 staged raw evidence to be explicit"

    for raw_file in raw_files:
        payload = json.loads(raw_file.read_text(encoding="utf-8"))
        assert payload["source_used"] == "staged_fixture"
        assert payload["data_domain"] == "macro_supplementary"
        assert payload["operation"] == "fetch_macro_series"
        assert payload["indicator_id"] == "ENV-E1-DGS10"
        assert "FRED:DGS10 deferred" in payload["staged_route_note"]
