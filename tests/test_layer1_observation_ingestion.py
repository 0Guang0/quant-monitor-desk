"""Layer 1 observation ingestion pipeline tests (Batch 2.5 §8.2–8.5)."""

from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import patch

import duckdb
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.layer1_axes.ingestion_inventory import (
    INVENTORY_JSON_NAME,
    INVENTORY_MD_NAME,
    PHASE1_MINIMUM_KEY_TABLES,
    assess_phase2_gate,
    capture_phase1_inventory,
    capture_task_phase1_evidence,
    copy_sandbox_db,
    data_root_content_fingerprint,
    file_sha256,
    record_operator_classification,
)
from backend.app.ops.db_inspector import REQUIRED_TOP_LEVEL_FIELDS
from tests.contract_gate_support import PROJECT_ROOT

TASK_EVIDENCE_DIR = (
    PROJECT_ROOT
    / ".trellis/tasks/06-20-round3-batch2-5-layer1-obs-ingest/execute-evidence"
)


def _init_db(db_path: Path) -> None:
    con = duckdb.connect(str(db_path))
    apply_migrations(con)
    con.close()


def _row_counts(db_path: Path, tables: tuple[str, ...]) -> dict[str, int | None]:
    con = duckdb.connect(str(db_path), read_only=True)
    counts: dict[str, int | None] = {}
    try:
        for name in tables:
            exists = con.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'main' AND table_name = ?
                """,
                [name],
            ).fetchone()[0]
            if not exists:
                counts[name] = None
                continue
            counts[name] = int(con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0])
    finally:
        con.close()
    return counts


def test_layer1Ingestion_phase1_inventory_readOnly(tmp_path: Path) -> None:
    """Read-only open; produce inventory json/md."""
    db = tmp_path / "baseline.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir()
    _init_db(db)

    out = tmp_path / "evidence"
    inventory = capture_phase1_inventory(db, data_root, evidence_dir=out)

    assert (out / INVENTORY_JSON_NAME).is_file()
    assert (out / INVENTORY_MD_NAME).is_file()
    inspect = inventory["inspect"]
    assert inspect["mode"] == "read_only"
    assert inspect["db"]["read_only_open"] is True
    assert inspect["db"]["exists"] is True
    assert inventory["inventory_type"] == "read_only"
    assert inventory["phase"] == "phase1_before_ingestion"
    assert inventory["db_evidence_classification"] == "schema_only_empty"
    assert inventory["phase2_gate"]["phase2_authorized"] is True

    md_text = (out / INVENTORY_MD_NAME).read_text(encoding="utf-8")
    assert "schema_only_empty" in md_text
    assert "Read-only open: True" in md_text
    assert "**Phase 2 authorized:** True" in md_text


def test_layer1Ingestion_phase1_inventory_requiredTableKeys(tmp_path: Path) -> None:
    """Inventory includes 018A Phase 1 minimum key table row counts."""
    db = tmp_path / "baseline.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir()
    _init_db(db)

    inventory = capture_phase1_inventory(db, data_root)
    phase1_tables = inventory["phase1_minimum_key_tables"]
    assert set(phase1_tables) == set(PHASE1_MINIMUM_KEY_TABLES)

    inspect_tables = {t["name"]: t for t in inventory["inspect"]["key_tables"]}
    for name in PHASE1_MINIMUM_KEY_TABLES:
        assert name in phase1_tables
        assert inspect_tables[name]["exists"] is True
        assert phase1_tables[name] == inspect_tables[name]["row_count"]

    for field in REQUIRED_TOP_LEVEL_FIELDS:
        assert field in inventory["inspect"]


def test_layer1Ingestion_phase1_zeroMutation(tmp_path: Path) -> None:
    """DB file hash, row counts, and data-root fingerprint unchanged after capture."""
    db = tmp_path / "baseline.duckdb"
    data_root = tmp_path / "data"
    raw_dir = data_root / "raw" / "vendor"
    raw_dir.mkdir(parents=True)
    (raw_dir / "seed.csv").write_text("x", encoding="utf-8")
    _init_db(db)

    before_bytes = db.read_bytes()
    before_hash = hashlib.sha256(before_bytes).hexdigest()
    before_counts = _row_counts(db, PHASE1_MINIMUM_KEY_TABLES)
    before_root = data_root_content_fingerprint(data_root)

    capture_phase1_inventory(db, data_root, evidence_dir=tmp_path / "out")

    after_bytes = db.read_bytes()
    after_hash = hashlib.sha256(after_bytes).hexdigest()
    after_counts = _row_counts(db, PHASE1_MINIMUM_KEY_TABLES)
    after_root = data_root_content_fingerprint(data_root)

    assert before_hash == after_hash
    assert before_bytes == after_bytes
    assert before_counts == after_counts
    assert before_root == after_root


def test_layer1Ingestion_phase1_copyProvenanceWhenSandbox(tmp_path: Path) -> None:
    """Sandbox DB copy records source path, checksum, and size."""
    source = tmp_path / "source.duckdb"
    sandbox = tmp_path / "sandbox.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir()
    _init_db(source)

    provenance = copy_sandbox_db(source, sandbox)
    assert sandbox.is_file()
    assert provenance["copy_sha256"] == file_sha256(source)
    assert provenance["copy_size_bytes"] == source.stat().st_size

    inventory = capture_phase1_inventory(
        sandbox,
        data_root,
        evidence_dir=tmp_path / "out",
        copy_source=source,
    )
    assert inventory["copy_provenance"] is not None
    assert inventory["copy_provenance"]["copy_source"] == provenance["copy_source"]
    assert inventory["copy_provenance"]["copy_sha256"] == provenance["copy_sha256"]
    assert inventory["copy_provenance"]["copy_size_bytes"] == provenance["copy_size_bytes"]

    md_text = (tmp_path / "out" / INVENTORY_MD_NAME).read_text(encoding="utf-8")
    assert "Sandbox copy provenance" in md_text
    assert provenance["copy_sha256"] in md_text


def test_layer1Ingestion_phase1_classify_fixtureOrStagedEvidence(tmp_path: Path) -> None:
    """fetch_log rows classify as fixture/staged and block Phase 2."""
    db = tmp_path / "baseline.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir()
    _init_db(db)
    cm = ConnectionManager(db)
    with cm.writer() as con:
        con.execute(
            """
            INSERT INTO fetch_log (
                fetch_id, run_id, source_id, data_domain, status, row_count, fetch_time
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            ["f-1", "run-1", "macro_supplementary", "macro_supplementary", "SUCCESS", 1],
        )

    inventory = capture_phase1_inventory(db, data_root)
    assert inventory["db_evidence_classification"] == "fixture_or_staged_evidence"
    gate = assess_phase2_gate(inventory)
    assert gate["phase2_authorized"] is False
    assert gate["stop_reason"] is not None


def test_layer1Ingestion_phase1_classify_productionLikeData(tmp_path: Path) -> None:
    """axis_observation rows classify as production-like and block Phase 2."""
    db = tmp_path / "baseline.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir()
    _init_db(db)
    cm = ConnectionManager(db)
    with cm.writer() as con:
        con.execute(
            """
            INSERT INTO axis_observation (
                observation_id, indicator_id, as_of_timestamp, publish_timestamp,
                fetch_time, raw_value, raw_unit, frequency, source_used,
                source_channel_id, data_lag_days, content_hash, schema_hash,
                source_switched, created_at
            ) VALUES (
                ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
                1.0, 'pct', 'daily', 'fixture', 'fixture', 0,
                'hash', 'schema', false, CURRENT_TIMESTAMP
            )
            """,
            ["obs-1", "ENV-E1-DGS10"],
        )

    inventory = capture_phase1_inventory(db, data_root)
    assert inventory["db_evidence_classification"] == "production_like_data"
    assert inventory["phase2_gate"]["phase2_authorized"] is False


def test_layer1Ingestion_phase1_classify_userProvidedData(tmp_path: Path) -> None:
    """file_registry without fetch_log classifies as user-provided and blocks Phase 2."""
    db = tmp_path / "baseline.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir()
    _init_db(db)
    cm = ConnectionManager(db)
    with cm.writer() as con:
        con.execute(
            """
            INSERT INTO file_registry (
                file_id, file_type, source, local_path, content_hash, parse_status
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ["file-1", "raw", "user_import", "raw/user/import.csv", "abc", "PARSED"],
        )

    inventory = capture_phase1_inventory(db, data_root)
    assert inventory["db_evidence_classification"] == "user_provided_data"
    assert inventory["phase2_gate"]["phase2_authorized"] is False


def test_layer1Ingestion_phase1_phase2Gate_blocksUntilReview(tmp_path: Path) -> None:
    """018A stop rule: non-schema classifications require explicit review."""
    for classification, authorized in (
        ("schema_only_empty", True),
        ("schema_with_config_only", True),
        ("fixture_or_staged_evidence", False),
        ("user_provided_data", False),
        ("production_like_data", False),
        ("unknown_data_present", False),
    ):
        gate = assess_phase2_gate({"db_evidence_classification": classification})
        assert gate["phase2_authorized"] is authorized, classification


def test_layer1Ingestion_phase1_captureDoesNotCallWriterOrMigrations(tmp_path: Path) -> None:
    """Inventory path must not invoke writer connections or apply_migrations."""
    db = tmp_path / "baseline.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir()
    _init_db(db)

    with (
        patch.object(ConnectionManager, "writer", side_effect=AssertionError("writer forbidden")),
        patch(
            "backend.app.layer1_axes.ingestion_inventory.apply_migrations",
            side_effect=AssertionError("apply_migrations forbidden"),
        ),
    ):
        inventory = capture_phase1_inventory(db, data_root)

    assert inventory["inspect"]["db"]["read_only_open"] is True


def test_layer1Ingestion_phase1_taskEvidenceUsesProjectTargetPaths(
    tmp_path: Path, monkeypatch
) -> None:
    """Task evidence records QMD_DATA_ROOT targets and synthetic baseline when DB missing."""
    data_root = tmp_path / "data"
    data_root.mkdir()
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    import backend.app.config as config_module

    monkeypatch.setattr(config_module, "DATA_ROOT", data_root)

    out = tmp_path / "evidence"
    inventory = capture_task_phase1_evidence(out)

    baseline = inventory["baseline_context"]
    assert baseline["target_db_exists_at_capture"] is False
    assert baseline["capture_strategy"] == "synthetic_migrated_schema_only"
    assert str(data_root) in baseline["target_data_root"]
    assert baseline["target_db_path"].endswith("quant_monitor.duckdb")
    assert inventory["phase2_gate"]["phase2_authorized"] is True
    assert (out / INVENTORY_JSON_NAME).is_file()
    sandbox_db = out / ".phase1-baseline-sandbox" / "duckdb" / "quant_monitor.duckdb"
    assert sandbox_db.is_file()


def test_layer1Ingestion_phase1_warnStatusDoesNotImplyUnsafeWhenSchemaOnly(tmp_path: Path) -> None:
    """WARN inspect + schema_only_empty documents safe Phase 2 authorization."""
    db = tmp_path / "baseline.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir()
    _init_db(db)

    inventory = capture_phase1_inventory(db, data_root, evidence_dir=tmp_path / "out")
    assert inventory["inspect"]["status"] == "WARN"
    assert inventory["db_evidence_classification"] == "schema_only_empty"
    md_text = (tmp_path / "out" / INVENTORY_MD_NAME).read_text(encoding="utf-8")
    assert "Inspect status WARN" in md_text
    assert "does **not** block Phase 2" in md_text
    assert "Phase 2 route dry-run is authorized" in md_text


def test_layer1Ingestion_phase1_enrichedInventory_hasRegistryAndFileSamples(tmp_path: Path) -> None:
    """Inventory includes source_registry snapshot and data-root file paths (F-A3-09/10)."""
    db = tmp_path / "baseline.duckdb"
    data_root = tmp_path / "data"
    raw = data_root / "raw" / "vendor"
    raw.mkdir(parents=True)
    (raw / "trace.csv").write_text("1", encoding="utf-8")
    _init_db(db)

    inventory = capture_phase1_inventory(db, data_root)
    assert inventory["data_root_file_samples"]
    assert inventory["data_root_file_samples"][0]["relative_path"].startswith("raw/")
    assert "sha256" in inventory["data_root_file_samples"][0]
    assert "staging_table_row_counts" in inventory
    assert isinstance(inventory["source_registry_snapshot"], list)


def test_layer1Ingestion_phase1_operatorMemoFlipsPhase2Gate(tmp_path: Path) -> None:
    """Operator classification memo authorizes Phase 2 when automated gate blocks (F-A3-01)."""
    db = tmp_path / "baseline.duckdb"
    data_root = tmp_path / "data"
    raw = data_root / "raw"
    raw.mkdir(parents=True)
    (raw / "leftover.parquet").write_text("x", encoding="utf-8")
    _init_db(db)

    out = tmp_path / "evidence"
    inventory = capture_phase1_inventory(db, data_root, evidence_dir=out)
    assert inventory["phase2_gate"]["phase2_authorized"] is False

    memo = out / "phase1_data_classification.md"
    memo.write_text("# classification memo\nfixture artifacts\n", encoding="utf-8")
    updated = record_operator_classification(
        inventory,
        memo_path=memo,
        classification=inventory["db_evidence_classification"],
        operator_ack="operator_reviewed_fixture_lineage",
        evidence_dir=out,
    )
    assert updated["phase2_gate"]["phase2_authorized"] is True
    assert updated["phase2_gate"]["authorization_source"] == "operator_classification_memo"
    md_text = (out / INVENTORY_MD_NAME).read_text(encoding="utf-8")
    assert "**Phase 2 authorized:** True" in md_text


def test_layer1Ingestion_phase1_taskEvidenceSandboxCopyPath(tmp_path: Path, monkeypatch) -> None:
    """capture_task_phase1_evidence uses sandbox copy when target DB exists (F-A3-13)."""
    data_root = tmp_path / "data"
    data_root.mkdir()
    target_db = data_root / "duckdb" / "quant_monitor.duckdb"
    target_db.parent.mkdir(parents=True)
    _init_db(target_db)

    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    import backend.app.config as config_module

    monkeypatch.setattr(config_module, "DATA_ROOT", data_root)

    out = tmp_path / "evidence"
    inventory = capture_task_phase1_evidence(out)
    assert inventory["baseline_context"]["capture_strategy"] == "sandbox_copy_of_target_db"
    assert inventory["copy_provenance"] is not None
    assert inventory["copy_provenance"]["copy_sha256"] == file_sha256(target_db)
