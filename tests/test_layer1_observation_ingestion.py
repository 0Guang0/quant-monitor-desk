"""Layer 1 observation ingestion pipeline tests (Batch 2.5 §8.2–8.5)."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime
from pathlib import Path
from unittest.mock import patch

import duckdb
import pytest
from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.datasources.adapters.fetch_port import LocalFixtureFetchPort
from backend.app.datasources.fetch_result import FetchRequest
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
from backend.app.sync.event_payload import parse_event_payload
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


def test_layer1Ingestion_phase1_captureUsesReadOnlyInspect(tmp_path: Path) -> None:
    """Inventory capture opens DB read-only without mutating baseline tables."""
    db = tmp_path / "baseline.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir()
    _init_db(db)
    before_hash = db.read_bytes()

    inventory = capture_phase1_inventory(db, data_root)

    assert inventory["inspect"]["db"]["read_only_open"] is True
    assert db.read_bytes() == before_hash


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


MACRO_FIXTURE_PATH = PROJECT_ROOT / "tests/fixtures/layer1_macro_observation_fixture.json"
PHASE3_ROW_COUNT_TABLES = ("axis_observation", "fetch_log", "file_registry", "job_event_log")


def _build_micro_fetch_service(
    tmp_path: Path,
    *,
    datasource: DataSourceService | None = None,
) -> tuple[Layer1ObservationIngestionService, Path]:
    db = tmp_path / "phase3.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir(parents=True, exist_ok=True)
    _init_db(db)
    if datasource is None:
        datasource = DataSourceService(
            data_root=data_root,
            fetch_port=LocalFixtureFetchPort(MACRO_FIXTURE_PATH, row_count=1),
        )
    service = Layer1ObservationIngestionService(
        db_path=db,
        data_root=data_root,
        datasource=datasource,
    )
    return service, db


def test_layer1MicroIngestion_usesDataSourceServiceBeforeFetch(
    tmp_path: Path, monkeypatch
) -> None:
    """Micro-fetch goes through DataSourceService.fetch, not Layer1 adapter factory."""
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, _ = _build_micro_fetch_service(tmp_path)
    calls: list[FetchRequest] = []
    original_fetch = DataSourceService.fetch

    def tracking_fetch(self, req, **kwargs):
        calls.append(req)
        return original_fetch(self, req, **kwargs)

    monkeypatch.setattr(DataSourceService, "fetch", tracking_fetch)
    adapter_imports: list[str] = []

    def forbidden_create_adapter(*args, **kwargs):
        adapter_imports.append("create_adapter")
        raise AssertionError("Layer1 must not call create_adapter")

    monkeypatch.setattr(
        "backend.app.datasources.adapters.create_adapter",
        forbidden_create_adapter,
    )

    result = service.micro_fetch_staging(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=date(2024, 6, 15),
    )

    assert len(calls) == 1
    assert calls[0].data_domain == STAGED_DATA_DOMAIN
    assert adapter_imports == []
    assert result.fetch_result.status == "SUCCESS"
    assert result.fetch_result.row_count == 1


def test_layer1MicroIngestion_persistsRoutePlanBeforeFetch(tmp_path: Path, monkeypatch) -> None:
    """ROUTE_PLAN job_event_log evidence exists before fetch_log for the same job."""
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_micro_fetch_service(tmp_path)

    result = service.micro_fetch_staging(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=date(2024, 6, 15),
    )

    con = duckdb.connect(str(db), read_only=True)
    try:
        route_row = con.execute(
            """
            SELECT created_at, payload_json FROM job_event_log
            WHERE job_id = ? AND event_type = 'ROUTE_PLAN'
            ORDER BY created_at ASC LIMIT 1
            """,
            [result.job_id],
        ).fetchone()
        fetch_row = con.execute(
            """
            SELECT fetch_time FROM fetch_log
            WHERE job_id = ?
            ORDER BY fetch_time ASC LIMIT 1
            """,
            [result.job_id],
        ).fetchone()
    finally:
        con.close()

    assert route_row is not None
    assert fetch_row is not None
    payload = parse_event_payload(route_row[1])
    assert payload.get("route_status") == "READY"
    assert payload.get("selected_source_id") == "akshare"
    assert payload.get("decision") == "route_plan"
    assert result.route_plan.route_status == "READY"


def test_layer1MicroIngestion_writesFetchLogAndRawEvidence(tmp_path: Path, monkeypatch) -> None:
    """Micro-fetch increments fetch_log and file_registry; raw files land under data root."""
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_micro_fetch_service(tmp_path)
    data_root = tmp_path / "data"
    before = _row_counts(db, ("fetch_log", "file_registry"))

    result = service.micro_fetch_staging(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=date(2024, 6, 15),
    )

    after = _row_counts(db, ("fetch_log", "file_registry"))
    assert after["fetch_log"] == (before["fetch_log"] or 0) + 1
    assert after["file_registry"] == (before["file_registry"] or 0) + 1
    assert result.fetch_result.raw_file_paths
    raw_path = data_root / result.fetch_result.raw_file_paths[0]
    assert raw_path.is_file()
    assert not Path(result.fetch_result.raw_file_paths[0]).is_absolute()
    assert result.fetch_result.content_hash is not None


def test_layer1MicroIngestion_phase3DoesNotWriteCleanAxisObservation(
    tmp_path: Path, monkeypatch
) -> None:
    """Phase 3 staging must not write clean axis_observation rows."""
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_micro_fetch_service(tmp_path)
    before_obs = _row_counts(db, ("axis_observation",))["axis_observation"]

    service.micro_fetch_staging(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=date(2024, 6, 15),
    )

    after_obs = _row_counts(db, ("axis_observation",))["axis_observation"]
    assert before_obs == after_obs == 0


def test_layer1MicroIngestion_resourceGuardPauseStopsBeforeFetch(
    tmp_path: Path, monkeypatch
) -> None:
    """ResourceGuard PAUSE blocks micro-fetch before fetch_log mutation."""
    monkeypatch.setattr(
        ResourceGuard,
        "check",
        lambda self: (Decision.PAUSE, "disk_free_gb below pause threshold"),
    )
    service, db = _build_micro_fetch_service(tmp_path)
    before = _row_counts(db, ("fetch_log", "file_registry", "job_event_log"))

    with pytest.raises(ResourceGuardBlockedError):
        service.micro_fetch_staging(
            indicator_id=FROZEN_STAGED_INDICATOR,
            as_of=date(2024, 6, 15),
        )

    after = _row_counts(db, ("fetch_log", "file_registry", "job_event_log"))
    assert before == after


def test_layer1Ingestion_phase3_taskEvidenceArtifacts(tmp_path: Path, monkeypatch) -> None:
    """Task execute-evidence exports phase3 json/md from fresh isolated sandbox."""
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
        operator_ack="authorized_for_phase3_test",
        evidence_dir=out,
    )

    from backend.app.layer1_axes.ingestion import capture_task_phase3_evidence

    evidence = capture_task_phase3_evidence(out, as_of=date(2024, 6, 15))
    assert (out / "phase3_micro_fetch_evidence.json").is_file()
    assert (out / "phase3_no_clean_write_proof.md").is_file()
    assert evidence["evidence_baseline_strategy"] == "fresh_phase3_sandbox"
    proof = evidence["no_clean_write_proof"]
    assert proof["axis_observation_unchanged"] is True
    assert proof["before_counts"]["fetch_log"] == 0
    assert proof["before_counts"]["file_registry"] == 0
    assert proof["fetch_log_delta"] == 1
    assert proof["file_registry_delta"] == 1
    assert "phase3-micro-fetch-sandbox" in evidence["evidence_data_root"]
    assert "phase3-micro-fetch-sandbox" in evidence["evidence_db_path"]
    raw_paths = evidence["micro_fetch"]["fetch_result"]["raw_file_paths"]
    assert raw_paths
    assert not Path(raw_paths[0]).is_absolute()


# --- Phase 4: clean write + snapshots (§8.5) ---

PHASE4_AS_OF = date(2024, 6, 15)
PHASE4_ROW_COUNT_TABLES = (
    "axis_observation",
    "fetch_log",
    "file_registry",
    "validation_report",
    "write_audit_log",
    "axis_feature_snapshot",
    "axis_interpretation_snapshot",
    "axis_snapshot_lineage",
)


def _build_phase4_service(
    tmp_path: Path,
    *,
    datasource: DataSourceService | None = None,
) -> tuple[Layer1ObservationIngestionService, Path]:
    db = tmp_path / "phase4.duckdb"
    data_root = tmp_path / "data"
    data_root.mkdir(parents=True, exist_ok=True)
    _init_db(db)
    if datasource is None:
        from backend.app.datasources.service import build_staged_fixture_service

        datasource = build_staged_fixture_service(
            data_root=data_root,
            fixture_path=MACRO_FIXTURE_PATH,
        )
    service = Layer1ObservationIngestionService(
        db_path=db,
        data_root=data_root,
        datasource=datasource,
    )
    return service, db


def test_layer1Observation_cleanWrite_requiresValidationReport(tmp_path: Path) -> None:
    """WriteManager rejects clean observation write without persisted validation_report."""
    from backend.app.layer1_axes.observation_writer import Layer1ObservationWriter

    db = tmp_path / "phase4-gate.duckdb"
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
    writer = Layer1ObservationWriter(cm)
    result = writer.write_observations(
        rows=[
            {
                "observation_id": "obs-missing-vr",
                "indicator_id": FROZEN_STAGED_INDICATOR,
                "as_of_timestamp": datetime(2024, 6, 15, 16, 0, tzinfo=UTC),
                "publish_timestamp": datetime(2024, 6, 15, 0, 0, tzinfo=UTC),
                "fetch_time": datetime(2024, 6, 15, 12, 0, tzinfo=UTC),
                "raw_value": 4.25,
                "raw_unit": "pct",
                "frequency": "daily",
                "source_used": "staged_fixture",
                "source_channel_id": "akshare",
                "data_lag_days": 0.0,
                "stale_reason": None,
                "quality_flags": "STAGED_FIXTURE",
                "content_hash": "abc",
                "schema_hash": "def",
                "source_switched": False,
                "created_at": datetime.now(UTC),
            }
        ],
        validation_report_id="missing-validation-report",
        run_id="run-vr",
        job_id="job-vr",
        source_used="staged_fixture",
    )
    assert result.status == "FAILED"
    con = duckdb.connect(str(db), read_only=True)
    try:
        assert con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0] == 0
        success_audits = con.execute(
            "SELECT COUNT(*) FROM write_audit_log WHERE status = 'SUCCESS'"
        ).fetchone()[0]
    finally:
        con.close()
    assert success_audits == 0


def test_layer1Observation_fetchFailure_blocksCleanWrite(tmp_path: Path, monkeypatch) -> None:
    """Failed fetch on commit path blocks clean write with OBSERVATION_MAPPING."""
    from datetime import UTC, datetime

    from backend.app.datasources.fetch_result import FetchResult
    from backend.app.datasources.service import DataSourceService
    from backend.app.layer1_axes.ingestion import IngestionCommitBlockedError

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)

    def failed_fetch(self, req, *, con, job_id=None, operation=None, **kwargs):
        return FetchResult(
            run_id=req.run_id,
            source_id=req.source_id,
            data_domain=req.data_domain,
            status="FAILED",
            row_count=0,
            fetch_time=datetime.now(UTC).isoformat(),
            error_message="injected fetch failure",
        )

    monkeypatch.setattr(DataSourceService, "fetch", failed_fetch)
    with pytest.raises(IngestionCommitBlockedError) as exc:
        service.commit_clean_observation_and_snapshots(
            indicator_id=FROZEN_STAGED_INDICATOR,
            as_of=PHASE4_AS_OF,
        )
    assert exc.value.reason_code == "OBSERVATION_MAPPING"
    assert _row_counts(db, ("axis_observation",))["axis_observation"] == 0


def test_layer1Observation_noneOptionalIndicator_skipsConflictValidator(
    tmp_path: Path, monkeypatch
) -> None:
    """Frozen ENV-E1-DGS10 uses validation_source=none_optional — conflict validator not invoked."""
    from backend.app.datasources.service import build_staged_fixture_service
    from backend.app.layer1_axes.ingestion import Layer1ObservationIngestionService
    from backend.app.validators.source_conflict import SourceConflictValidator

    data_root = tmp_path / "data"
    data_root.mkdir()
    indicator = Layer1ObservationIngestionService(
        db_path=tmp_path / "unused.duckdb",
        data_root=data_root,
        datasource=build_staged_fixture_service(
            data_root=data_root,
            fixture_path=MACRO_FIXTURE_PATH,
        ),
    )._indicator_by_id(FROZEN_STAGED_INDICATOR)
    assert Layer1ObservationIngestionService._validation_source_requires_conflict(indicator) is False

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)

    def conflict_must_not_run(self, con, request, **kwargs):
        raise AssertionError("SourceConflictValidator must not run for none_optional indicator")

    monkeypatch.setattr(SourceConflictValidator, "validate_table", conflict_must_not_run)
    result = service.commit_clean_observation_and_snapshots(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=PHASE4_AS_OF,
    )
    assert result.observation_write_status == "SUCCESS"


def test_layer1Observation_warningValidation_allowsCleanWrite(tmp_path: Path, monkeypatch) -> None:
    """WARNING validation with can_write_clean=True still commits observation rows."""
    from backend.app.validators.data_quality import DataQualityReport

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)

    def warning_validate(self, con, request, **kwargs):
        report = DataQualityReport(
            validation_report_id="vr-warning-ok",
            status="WARNING",
            checked_rows=1,
            failed_rows=0,
            warning_rows=1,
            quality_flags=("STALE",),
            can_write_clean=True,
            needs_manual_review=False,
            findings=(),
        )
        self._persist_report(con, request, report)
        return report

    monkeypatch.setattr(
        "backend.app.layer1_axes.ingestion.DataQualityValidator.validate_table",
        warning_validate,
    )
    result = service.commit_clean_observation_and_snapshots(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=PHASE4_AS_OF,
    )
    assert result.observation_write_status == "SUCCESS"
    assert _row_counts(db, ("axis_observation",))["axis_observation"] == 1


def test_layer1Observation_cleanWrite_usesWriteManager(tmp_path: Path, monkeypatch) -> None:
    """commit_clean_observation_and_snapshots records write_audit_log for axis_observation."""

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)
    before_audit = _row_counts(db, ("write_audit_log",))["write_audit_log"]

    result = service.commit_clean_observation_and_snapshots(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=PHASE4_AS_OF,
    )

    assert result.observation_write_status == "SUCCESS"
    con = duckdb.connect(str(db), read_only=True)
    try:
        audit_rows = con.execute(
            """
            SELECT target_table, status, validation_status
            FROM write_audit_log
            WHERE job_id = ?
            ORDER BY started_at
            """,
            [result.micro_fetch.job_id],
        ).fetchall()
        obs_count = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    finally:
        con.close()
    assert obs_count == 1
    assert any(row[0] == "axis_observation" and row[1] == "SUCCESS" for row in audit_rows)
    after_audit = _row_counts(db, ("write_audit_log",))["write_audit_log"]
    assert (after_audit or 0) > (before_audit or 0)


def test_layer1Observation_validationFailure_blocksCleanWrite(tmp_path: Path, monkeypatch) -> None:
    """Failed validation_report blocks clean observation write."""
    from backend.app.layer1_axes.ingestion import IngestionCommitBlockedError
    from backend.app.validators.data_quality import DataQualityReport

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)

    def failing_validate(self, con, request, **kwargs):
        report = DataQualityReport(
            validation_report_id="vr-fail",
            status="FAILED",
            checked_rows=1,
            failed_rows=1,
            warning_rows=0,
            quality_flags=("TEST_FAIL",),
            can_write_clean=False,
            needs_manual_review=False,
            findings=(),
        )
        self._persist_report(con, request, report)
        return report

    monkeypatch.setattr(
        "backend.app.layer1_axes.ingestion.DataQualityValidator.validate_table",
        failing_validate,
    )
    with pytest.raises(IngestionCommitBlockedError) as exc:
        service.commit_clean_observation_and_snapshots(
            indicator_id=FROZEN_STAGED_INDICATOR,
            as_of=PHASE4_AS_OF,
        )
    assert exc.value.reason_code == "VALIDATION_FAILED"
    assert _row_counts(db, ("axis_observation",))["axis_observation"] == 0


def test_layer1Observation_severeConflict_blocksCleanWrite(tmp_path: Path, monkeypatch) -> None:
    """Open severe source_conflict for the run blocks clean write via DbValidationGate."""
    from backend.app.layer1_axes.ingestion import IngestionCommitBlockedError

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)
    run_id = "layer1-commit-severe-test"

    def pass_validate(self, con, request, **kwargs):
        from backend.app.validators.data_quality import DataQualityReport

        report = DataQualityReport(
            validation_report_id="vr-severe-block",
            status="PASSED",
            checked_rows=1,
            failed_rows=0,
            warning_rows=0,
            quality_flags=(),
            can_write_clean=True,
            needs_manual_review=False,
            findings=(),
        )
        self._persist_report(con, request, report)
        con.execute(
            """
            INSERT INTO source_conflict (
                conflict_id, run_id, job_id, data_domain, field_name,
                primary_source, competing_source, severity, reconcile_status,
                manual_review_required
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                "conflict-severe-1",
                request.run_id,
                request.job_id,
                STAGED_DATA_DOMAIN,
                "raw_value",
                "akshare",
                "fred",
                "severe",
                "OPEN",
                False,
            ],
        )
        return report

    monkeypatch.setattr(
        "backend.app.layer1_axes.ingestion.DataQualityValidator.validate_table",
        pass_validate,
    )
    with pytest.raises(IngestionCommitBlockedError) as exc:
        service.commit_clean_observation_and_snapshots(
            indicator_id=FROZEN_STAGED_INDICATOR,
            as_of=PHASE4_AS_OF,
            run_id=run_id,
        )
    assert exc.value.reason_code == "WRITE_FAILED"


def test_layer1Observation_manualReview_blocksNonManualPatchWrite(
    tmp_path: Path, monkeypatch
) -> None:
    """needs_manual_review on validation_report blocks clean write."""
    from backend.app.layer1_axes.ingestion import IngestionCommitBlockedError
    from backend.app.validators.data_quality import DataQualityReport

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)

    def manual_review_validate(self, con, request, **kwargs):
        report = DataQualityReport(
            validation_report_id="vr-manual",
            status="PASSED",
            checked_rows=1,
            failed_rows=0,
            warning_rows=0,
            quality_flags=("SCHEMA_DRIFT",),
            can_write_clean=True,
            needs_manual_review=True,
            findings=(),
        )
        self._persist_report(con, request, report)
        return report

    monkeypatch.setattr(
        "backend.app.layer1_axes.ingestion.DataQualityValidator.validate_table",
        manual_review_validate,
    )
    with pytest.raises(IngestionCommitBlockedError) as exc:
        service.commit_clean_observation_and_snapshots(
            indicator_id=FROZEN_STAGED_INDICATOR,
            as_of=PHASE4_AS_OF,
        )
    assert exc.value.reason_code == "MANUAL_REVIEW_REQUIRED"


def test_layer1Observation_stagedFixture_qualityFlagPersisted(tmp_path: Path, monkeypatch) -> None:
    """Staged fixture commits must label axis_observation with STAGED_FIXTURE (AC-P4-4)."""
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)

    service.commit_clean_observation_and_snapshots(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=PHASE4_AS_OF,
    )

    con = duckdb.connect(str(db), read_only=True)
    try:
        row = con.execute(
            "SELECT quality_flags, source_used FROM axis_observation LIMIT 1"
        ).fetchone()
    finally:
        con.close()
    assert row is not None
    assert "STAGED_FIXTURE" in row[0]
    assert row[1] == "akshare"


def test_layer1Observation_lineageIncludesFetchIdsAndHashes(tmp_path: Path, monkeypatch) -> None:
    """axis_snapshot_lineage carries non-empty fetch ids and content hashes from validation."""
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)

    result = service.commit_clean_observation_and_snapshots(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=PHASE4_AS_OF,
    )

    assert result.source_fetch_ids
    assert result.source_content_hashes
    con = duckdb.connect(str(db), read_only=True)
    try:
        row = con.execute(
            """
            SELECT source_fetch_ids, source_content_hashes, rule_version, parameter_hash
            FROM axis_snapshot_lineage
            WHERE snapshot_id = ?
            """,
            [result.lineage_snapshot_id],
        ).fetchone()
    finally:
        con.close()
    assert row is not None
    fetch_ids = json.loads(row[0])
    content_hashes = json.loads(row[1])
    assert fetch_ids
    assert content_hashes
    assert row[2]
    assert row[3]


def test_layer1Observation_noFutureDataRejected(tmp_path: Path, monkeypatch) -> None:
    """Future publish_timestamp blocks commit before snapshots persist."""
    from backend.app.layer1_axes.ingestion import IngestionCommitBlockedError

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)

    def future_row(micro, *, data_root, fixture_path=None):
        from backend.app.layer1_axes.observation_mapper import map_micro_fetch_to_observation_row

        row = map_micro_fetch_to_observation_row(
            micro, data_root=data_root, fixture_path=fixture_path
        )
        row["publish_timestamp"] = datetime(2099, 1, 1, tzinfo=UTC)
        row["as_of_timestamp"] = datetime(2024, 6, 15, 16, 0, tzinfo=UTC)
        return row

    monkeypatch.setattr(
        "backend.app.layer1_axes.ingestion.map_micro_fetch_to_observation_row",
        future_row,
    )
    with pytest.raises(IngestionCommitBlockedError) as exc:
        service.commit_clean_observation_and_snapshots(
            indicator_id=FROZEN_STAGED_INDICATOR,
            as_of=PHASE4_AS_OF,
        )
    assert exc.value.reason_code == "NO_FUTURE_DATA"


def test_layer1Observation_forbiddenAndBlindspotNeverPersisted(tmp_path: Path) -> None:
    """Forbidden and BlindSpot indicators never reach axis_observation."""
    service, db = _build_phase4_service(tmp_path)
    for indicator_id, code in (
        ("ENV-FORBIDDEN-WM2NS", FORBIDDEN_INDICATOR_REJECTED),
        ("ENV-D-DTS_OPERATING_CASH_BALANCE", BLINDSPOT_INDICATOR_REJECTED),
    ):
        with pytest.raises(IngestionRejectedError) as exc:
            service.commit_clean_observation_and_snapshots(
                indicator_id=indicator_id,
                as_of=PHASE4_AS_OF,
            )
        assert exc.value.reason_code == code
    assert _row_counts(db, ("axis_observation",))["axis_observation"] == 0


def test_layer1Observation_postInspectShowsExpectedDeltasOnly(tmp_path: Path, monkeypatch) -> None:
    """Post-commit inventory deltas are limited to expected ingestion tables."""
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)
    before = _row_counts(db, PHASE4_ROW_COUNT_TABLES)

    service.commit_clean_observation_and_snapshots(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=PHASE4_AS_OF,
    )

    after = _row_counts(db, PHASE4_ROW_COUNT_TABLES)
    assert (after["axis_observation"] or 0) - (before["axis_observation"] or 0) == 1
    assert (after["axis_feature_snapshot"] or 0) - (before["axis_feature_snapshot"] or 0) == 1
    assert (after["axis_interpretation_snapshot"] or 0) - (
        before["axis_interpretation_snapshot"] or 0
    ) == 1
    assert (after["axis_snapshot_lineage"] or 0) - (before["axis_snapshot_lineage"] or 0) == 1
    assert (after["fetch_log"] or 0) - (before["fetch_log"] or 0) >= 1
    assert (after["file_registry"] or 0) - (before["file_registry"] or 0) == 1
    assert (after["validation_report"] or 0) - (before["validation_report"] or 0) >= 1
    assert (after["write_audit_log"] or 0) - (before["write_audit_log"] or 0) >= 4


def test_layer1Observation_mappingUsesRawFetchPayload(tmp_path: Path, monkeypatch) -> None:
    """metric_value and source_used derive from raw fetch JSON, not fixture alone."""
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)

    result = service.commit_clean_observation_and_snapshots(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=PHASE4_AS_OF,
    )
    raw_path = service._data_root / result.micro_fetch.fetch_result.raw_file_paths[0]
    payload = json.loads(raw_path.read_text(encoding="utf-8"))
    expected_value = payload["observations"][0]["metric_value"]

    con = duckdb.connect(str(db), read_only=True)
    try:
        row = con.execute(
            "SELECT raw_value, source_used FROM axis_observation WHERE observation_id = ?",
            [result.observation_id],
        ).fetchone()
    finally:
        con.close()
    assert row is not None
    assert row[0] == expected_value
    assert row[1] == result.micro_fetch.route_plan.selected_source_id


def test_layer1Observation_resourceGuardPauseBlocksCommit(
    tmp_path: Path, monkeypatch
) -> None:
    """ResourceGuard PAUSE blocks Phase 4 commit before any clean write."""
    monkeypatch.setattr(
        ResourceGuard,
        "check",
        lambda self: (Decision.PAUSE, "disk_free_gb below pause threshold"),
    )
    service, db = _build_phase4_service(tmp_path)
    with pytest.raises(ResourceGuardBlockedError):
        service.commit_clean_observation_and_snapshots(
            indicator_id=FROZEN_STAGED_INDICATOR,
            as_of=PHASE4_AS_OF,
        )
    assert _row_counts(db, ("axis_observation",))["axis_observation"] == 0


def test_layer1Observation_commitRejectsDuplicateObservation(
    tmp_path: Path, monkeypatch
) -> None:
    """Second commit for same indicator/as_of is rejected without duplicate rows."""
    from backend.app.layer1_axes.ingestion import IngestionCommitBlockedError

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)
    service.commit_clean_observation_and_snapshots(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=PHASE4_AS_OF,
    )
    with pytest.raises(IngestionCommitBlockedError) as exc:
        service.commit_clean_observation_and_snapshots(
            indicator_id=FROZEN_STAGED_INDICATOR,
            as_of=PHASE4_AS_OF,
        )
    assert exc.value.reason_code == "DUPLICATE_COMMIT"
    assert _row_counts(db, ("axis_observation",))["axis_observation"] == 1


def test_layer1Observation_writeAuditUsesSharedValidationReport(
    tmp_path: Path, monkeypatch
) -> None:
    """All Phase 4 clean writes share one validation_report_id in write_audit_log."""
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    service, db = _build_phase4_service(tmp_path)
    result = service.commit_clean_observation_and_snapshots(
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=PHASE4_AS_OF,
    )
    con = duckdb.connect(str(db), read_only=True)
    try:
        audit_rows = con.execute(
            """
            SELECT target_table, status
            FROM write_audit_log
            WHERE job_id = ?
            ORDER BY started_at
            """,
            [result.micro_fetch.job_id],
        ).fetchall()
        vr_rows = con.execute(
            """
            SELECT validation_report_id FROM validation_report
            WHERE run_id = ? AND job_id = ?
            """,
            [result.micro_fetch.run_id, result.micro_fetch.job_id],
        ).fetchall()
    finally:
        con.close()
    tables = {row[0] for row in audit_rows}
    assert "axis_observation" in tables
    assert "axis_feature_snapshot" in tables
    assert "axis_interpretation_snapshot" in tables
    assert "axis_snapshot_lineage" in tables
    assert len(audit_rows) >= 4
    assert all(row[1] == "SUCCESS" for row in audit_rows)
    assert any(row[0] == result.validation_report_id for row in vr_rows)


def test_layer1Ingestion_phase4_taskEvidenceArtifacts(tmp_path: Path, monkeypatch) -> None:
    """Task execute-evidence exports phase4 json/md aligned with phase1 baseline."""
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
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
        operator_ack="authorized_for_phase4_test",
        evidence_dir=out,
    )
    capture_task_phase2_evidence(out, as_of=date(2024, 6, 15))

    from backend.app.layer1_axes.ingestion import capture_task_phase4_evidence

    evidence = capture_task_phase4_evidence(out, as_of=date(2024, 6, 15))
    assert (out / "phase4_clean_write_and_snapshot_evidence.json").is_file()
    assert (out / "phase4_inventory_delta.md").is_file()
    assert evidence["phase1_baseline_attached"] is True
    assert evidence["evidence_baseline_strategy"] in {
        "phase1_sandbox_copy_reused",
        "sandbox_copy_aligned_with_phase1",
        "fresh_phase4_sandbox_fallback",
    }
    delta = evidence["inventory_delta"]["table_deltas"]
    assert delta["axis_observation"]["after"] == 1
    assert delta["fetch_log"]["after"] >= 1
    assert delta["file_registry"]["after"] >= 1

