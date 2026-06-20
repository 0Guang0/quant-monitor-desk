"""Layer 1 observation ingestion pipeline tests (Batch 2.5 §8.2–8.5)."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import duckdb
import pytest
from backend.app.core.resource_guard import Decision
from backend.app.datasources.route_models import SourceRouteCandidate, SourceRoutePlan
from backend.app.datasources.service import DataSourceService, ResourceGuardBlockedError
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.layer1_axes.ingestion import (
    BLINDSPOT_INDICATOR_REJECTED,
    FORBIDDEN_INDICATOR_REJECTED,
    FROZEN_STAGED_INDICATOR,
    STAGED_DATA_DOMAIN,
    STAGED_OPERATION,
    IngestionRejectedError,
    Layer1ObservationIngestionService,
    capture_task_phase2_evidence,
)
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


PHASE2_ROW_COUNT_TABLES = ("axis_observation", "fetch_log", "file_registry")


def _build_ingestion_service(
    tmp_path: Path,
    *,
    data_root: Path | None = None,
    datasource: DataSourceService | None = None,
) -> tuple[Layer1ObservationIngestionService, Path]:
    db = tmp_path / "phase2.duckdb"
    root = data_root or tmp_path / "data"
    root.mkdir(parents=True, exist_ok=True)
    _init_db(db)
    service = Layer1ObservationIngestionService(
        db_path=db,
        data_root=root,
        datasource=datasource,
    )
    return service, db


def test_layer1Ingestion_routePreview_noMutation(tmp_path: Path) -> None:
    """Dry-run preview leaves axis_observation and fetch_log row counts unchanged."""
    service, db = _build_ingestion_service(tmp_path)
    before_hash = hashlib.sha256(db.read_bytes()).hexdigest()
    before_counts = _row_counts(db, PHASE2_ROW_COUNT_TABLES)
    as_of = date(2024, 6, 15)

    result = service.preview_routes(indicators=[FROZEN_STAGED_INDICATOR], as_of=as_of)

    after_hash = hashlib.sha256(db.read_bytes()).hexdigest()
    after_counts = _row_counts(db, PHASE2_ROW_COUNT_TABLES)
    assert before_hash == after_hash
    assert before_counts == after_counts
    assert len(result.previews) == 1
    preview = result.previews[0]
    assert preview.indicator_id == FROZEN_STAGED_INDICATOR
    assert preview.route_plan.route_status == "READY"
    assert preview.route_plan.selected_source_id is not None
    assert preview.binding.data_domain == STAGED_DATA_DOMAIN
    assert preview.binding.operation == STAGED_OPERATION
    assert preview.capability_verified is True
    assert preview.resource_guard_decision in {"OK", "WARN"}


def test_layer1Ingestion_forbiddenIndicator_rejectedBeforeRoute(tmp_path: Path) -> None:
    """Forbidden indicators are rejected before SourceRoutePlan is built."""
    service, _ = _build_ingestion_service(tmp_path)
    with pytest.raises(IngestionRejectedError) as exc:
        service.preview_routes(indicators=["ENV-FORBIDDEN-WM2NS"], as_of=date(2024, 6, 15))
    assert exc.value.reason_code == FORBIDDEN_INDICATOR_REJECTED


def test_layer1Ingestion_blindspot_rejectedBeforeFetch(tmp_path: Path) -> None:
    """BlindSpot indicators are rejected before any fetch-capable route step."""
    service, _ = _build_ingestion_service(tmp_path)
    with pytest.raises(IngestionRejectedError) as exc:
        service.preview_routes(
            indicators=["ENV-D-DTS_OPERATING_CASH_BALANCE"],
            as_of=date(2024, 6, 15),
        )
    assert exc.value.reason_code == BLINDSPOT_INDICATOR_REJECTED


def test_layer1Ingestion_disabledSource_returnsRouteStatusWithoutFetch(
    tmp_path: Path, monkeypatch
) -> None:
    """DISABLED_SOURCE / USER_AUTH_REQUIRED previews never invoke fetch."""
    fetch_called: list[str] = []

    def forbidden_fetch(self, *args, **kwargs):
        fetch_called.append("fetch")
        raise AssertionError("fetch must not run during Phase 2 dry-run")

    monkeypatch.setattr(DataSourceService, "fetch", forbidden_fetch)

    def disabled_preview(self, **kwargs):
        return SourceRoutePlan(
            route_plan_id=SourceRoutePlan.new_id(),
            run_id=kwargs.get("run_id", "preview-run"),
            job_id=kwargs.get("job_id", "preview-job"),
            data_domain=kwargs.get("data_domain", STAGED_DATA_DOMAIN),
            operation=kwargs.get("operation", STAGED_OPERATION),
            route_status="DISABLED_SOURCE",
            selected_source_id=None,
            candidates=[
                SourceRouteCandidate(
                    source_id="qmt_xtdata",
                    role="Primary",
                    enabled=False,
                    allowed_domain="cn_equity_minute_bar",
                    capability_declared=True,
                    disabled_reason="source_disabled_by_default",
                    skip_reason="source_disabled_by_default",
                )
            ],
        )

    monkeypatch.setattr(DataSourceService, "preview_route", disabled_preview)
    service, _ = _build_ingestion_service(tmp_path)

    result = service.preview_routes(indicators=[FROZEN_STAGED_INDICATOR], as_of=date(2024, 6, 15))

    assert fetch_called == []
    assert result.previews[0].route_plan.route_status == "DISABLED_SOURCE"
    assert result.previews[0].route_plan.selected_source_id is None
    assert result.previews[0].stop_reason is not None


def test_layer1Ingestion_noSilentFallback(tmp_path: Path) -> None:
    """Every disabled candidate documents skip_reason; non-READY routes have no selection."""
    service, _ = _build_ingestion_service(tmp_path)
    result = service.preview_routes(indicators=[FROZEN_STAGED_INDICATOR], as_of=date(2024, 6, 15))
    plan = result.previews[0].route_plan
    for candidate in plan.candidates:
        if not candidate.enabled:
            assert candidate.skip_reason is not None
    if plan.route_status != "READY":
        assert plan.selected_source_id is None
    if plan.selected_source_id is not None:
        selected = next(c for c in plan.candidates if c.source_id == plan.selected_source_id)
        assert selected.enabled is True
        assert selected.skip_reason is None


def test_layer1Ingestion_routePreview_resourceGuardPauseRaises(tmp_path: Path, monkeypatch) -> None:
    """ResourceGuard PAUSE blocks preview (parity with DataSourceService.fetch)."""
    monkeypatch.setattr(
        DataSourceService,
        "check_resource_guard",
        lambda self: (Decision.PAUSE, "disk_free_gb below pause threshold"),
    )
    service, _ = _build_ingestion_service(tmp_path)
    with pytest.raises(ResourceGuardBlockedError):
        service.preview_routes(indicators=[FROZEN_STAGED_INDICATOR], as_of=date(2024, 6, 15))


def test_layer1Ingestion_userAuthRequired_returnsRouteStatusWithoutFetch(
    tmp_path: Path, monkeypatch
) -> None:
    """USER_AUTH_REQUIRED preview never invokes fetch."""
    fetch_called: list[str] = []

    def forbidden_fetch(self, *args, **kwargs):
        fetch_called.append("fetch")
        raise AssertionError("fetch must not run during Phase 2 dry-run")

    monkeypatch.setattr(DataSourceService, "fetch", forbidden_fetch)

    def auth_preview(self, **kwargs):
        return SourceRoutePlan(
            route_plan_id=SourceRoutePlan.new_id(),
            run_id="run-auth",
            job_id="job-auth",
            data_domain=kwargs.get("data_domain", STAGED_DATA_DOMAIN),
            operation=kwargs.get("operation", STAGED_OPERATION),
            route_status="USER_AUTH_REQUIRED",
            selected_source_id=None,
            candidates=[
                SourceRouteCandidate(
                    source_id="qmt_xqshare",
                    role="Primary",
                    enabled=False,
                    allowed_domain="cn_equity_realtime",
                    capability_declared=True,
                    disabled_reason="user_authorization_required",
                    skip_reason="user_authorization_required",
                )
            ],
        )

    monkeypatch.setattr(DataSourceService, "preview_route", auth_preview)
    service, _ = _build_ingestion_service(tmp_path)
    result = service.preview_routes(indicators=[FROZEN_STAGED_INDICATOR], as_of=date(2024, 6, 15))
    assert fetch_called == []
    assert result.previews[0].route_plan.route_status == "USER_AUTH_REQUIRED"
    assert result.previews[0].stop_reason is not None


def test_layer1Ingestion_notOnAllowlist_rejected(tmp_path: Path) -> None:
    """Indicators without staged binding are rejected even if observable."""
    service, _ = _build_ingestion_service(tmp_path)
    with pytest.raises(IngestionRejectedError) as exc:
        service.preview_routes(indicators=["ENV-E1-EFFR"], as_of=date(2024, 6, 15))
    assert exc.value.reason_code == "NOT_ON_ALLOWLIST"


def test_layer1Ingestion_phase2_fixtureAsOfMatchesPreviewEvidence(tmp_path: Path) -> None:
    """Staged fixture as_of aligns with Phase 2 preview window."""
    fixture = json.loads(
        (PROJECT_ROOT / "tests/fixtures/layer1_macro_observation_fixture.json").read_text(
            encoding="utf-8"
        )
    )
    as_of = date(2024, 6, 15)
    assert fixture["as_of"] == as_of.isoformat()
    service, _ = _build_ingestion_service(tmp_path)
    result = service.preview_routes(indicators=[FROZEN_STAGED_INDICATOR], as_of=as_of)
    preview = result.previews[0]
    assert preview.binding.unit == "pct"
    assert preview.binding.series_id == fixture["series_id"]


def test_layer1Ingestion_phase1_gitkeepOnly_classifiesSchemaOnly(tmp_path: Path) -> None:
    """Placeholder .gitkeep files alone must not force fixture_or_staged_evidence."""
    db = tmp_path / "baseline.duckdb"
    data_root = tmp_path / "data"
    (data_root / "raw").mkdir(parents=True)
    (data_root / "parquet").mkdir(parents=True)
    (data_root / "raw" / ".gitkeep").write_text("", encoding="utf-8")
    (data_root / "parquet" / ".gitkeep").write_text("", encoding="utf-8")
    _init_db(db)
    inventory = capture_phase1_inventory(db, data_root)
    assert inventory["db_evidence_classification"] == "schema_only_empty"
    assert inventory["phase2_gate"]["phase2_authorized"] is True


def test_layer1Ingestion_routePreview_capabilityDeclaredForSelectedSource(
    tmp_path: Path,
) -> None:
    """018A Phase 2 step 5: capability registry declares domain/operation for selected source."""
    service, _ = _build_ingestion_service(tmp_path)
    result = service.preview_routes(indicators=[FROZEN_STAGED_INDICATOR], as_of=date(2024, 6, 15))
    preview = result.previews[0]
    assert preview.capability_verified is True
    assert preview.route_plan.selected_source_id == "akshare"


def test_layer1Ingestion_phase2TaskEvidence_usesSandboxDbAlignedWithPhase1(
    tmp_path: Path, monkeypatch
) -> None:
    """Task Phase 2 evidence inspects Phase 1 sandbox DB, not production path."""
    data_root = tmp_path / "data"
    data_root.mkdir()
    target_db = data_root / "duckdb" / "quant_monitor.duckdb"
    target_db.parent.mkdir(parents=True)
    _init_db(target_db)
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    import backend.app.config as config_module

    monkeypatch.setattr(config_module, "DATA_ROOT", data_root)
    out = tmp_path / "evidence"
    capture_task_phase1_evidence(out)
    capture_task_phase2_evidence(out, as_of=date(2024, 6, 15))
    payload = json.loads((out / "phase2_route_preview.json").read_text(encoding="utf-8"))
    proof = payload["mutation_proof"]
    assert proof["db_capture_strategy"] in {
        "phase1_sandbox_copy_reused",
        "sandbox_copy_aligned_with_phase1",
    }
    assert "phase1-baseline-sandbox" in proof["db_path"]


def test_layer1Ingestion_phase2TaskEvidence_requiresPhase1GateWhenInventoryPresent(
    tmp_path: Path, monkeypatch
) -> None:
    """Task evidence export honors Phase 1 phase2_gate when inventory JSON exists."""
    out = tmp_path / "evidence"
    out.mkdir()
    db = tmp_path / "db.duckdb"
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
            ["f-phase2-gate", "run-1", "macro_supplementary", "macro_supplementary", "SUCCESS", 1],
        )
    capture_phase1_inventory(db, data_root, evidence_dir=out)
    inventory = json.loads((out / INVENTORY_JSON_NAME).read_text(encoding="utf-8"))
    assert inventory["phase2_gate"]["phase2_authorized"] is False

    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    import backend.app.config as config_module

    monkeypatch.setattr(config_module, "DATA_ROOT", data_root)
    with pytest.raises(RuntimeError, match="Phase 2"):
        capture_task_phase2_evidence(out, as_of=date(2024, 6, 15))


def test_layer1Ingestion_phase2_taskEvidenceArtifacts(tmp_path: Path, monkeypatch) -> None:
    """Task execute-evidence exports route preview json/md and no-mutation proof."""
    out = tmp_path / "evidence"
    data_root = tmp_path / "data"
    data_root.mkdir()
    db = tmp_path / "db.duckdb"
    _init_db(db)
    inventory = capture_phase1_inventory(db, data_root, evidence_dir=out)
    memo = out / "phase1_data_classification.md"
    memo.write_text("# fixture memo\n", encoding="utf-8")
    record_operator_classification(
        inventory,
        memo_path=memo,
        classification=inventory["db_evidence_classification"],
        operator_ack="authorized_for_phase2_test",
        evidence_dir=out,
    )

    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    import backend.app.config as config_module

    monkeypatch.setattr(config_module, "DATA_ROOT", data_root)
    from backend.app.layer1_axes.ingestion import capture_phase2_route_evidence

    service = Layer1ObservationIngestionService(db_path=db, data_root=data_root)
    evidence = capture_phase2_route_evidence(
        service=service,
        indicators=[FROZEN_STAGED_INDICATOR],
        as_of=date(2024, 6, 15),
        evidence_dir=out,
    )
    assert (out / "phase2_route_preview.json").is_file()
    assert (out / "phase2_route_preview_matrix.md").is_file()
    assert (out / "phase2_no_mutation_proof.md").is_file()
    payload = json.loads((out / "phase2_route_preview.json").read_text(encoding="utf-8"))
    assert payload["frozen_indicator"] == FROZEN_STAGED_INDICATOR
    assert payload["previews"][0]["route_plan"]["route_status"] == "READY"
    assert payload["previews"][0]["capability_verified"] is True
    assert payload["previews"][0]["intended_as_of_range"]["start"] == "2024-06-15"
    assert evidence["mutation_proof"]["row_counts_unchanged"] is True
