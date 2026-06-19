"""Round2 ABCD adversarial audit remediation tests."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import duckdb
import pytest
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.event_payload import SCHEMA_KEYS, parse_event_payload
from backend.app.sync.jobs import SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator
from backend.app.validators.data_quality import DataQualityRequest, DataQualityValidator
from tests.test_batch_d_orchestration_flow import (
    CLEAN_TABLE,
    CONFLICT_STG,
    BatchDIncrementalAdapter,
    _incremental_spec,
    _orch_stack,
)


def _migrated_cm(tmp_path: Path) -> ConnectionManager:
    db = tmp_path / "audit.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    return cm


def test_validationReport_persistsRuleVersionAndFetchLineage(
    tmp_path: Path, registry_yaml_fixture: Path, monkeypatch
) -> None:
    from backend.app.core.resource_guard import Decision, ResourceGuard

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    orch, adapter = _orch_stack(tmp_path, registry_yaml_fixture)
    result = orch.run_incremental(
        _incremental_spec("job-lineage"),
        adapter=adapter,
        conflict_staging_table=CONFLICT_STG,
        clean_table=CLEAN_TABLE,
    )
    assert result.validation_report_id
    with orch._cm.writer() as con:
        row = con.execute(
            """
            SELECT rule_set_id, rule_version, source_fetch_ids_json, source_content_hashes_json
            FROM validation_report WHERE validation_report_id = ?
            """,
            [result.validation_report_id],
        ).fetchone()
    assert row is not None
    assert row[0] == "p0_round_1"
    assert row[1] == "p0_round_1"
    fetch_ids = json.loads(row[2] or "[]")
    assert isinstance(fetch_ids, list)
    assert len(fetch_ids) >= 1, "expected fetch lineage ids from fetch_log"
    content_hashes = json.loads(row[3] or "[]")
    assert isinstance(content_hashes, list)


def test_sourceConflict_persistsToleranceRuleVersion(
    tmp_path: Path, registry_yaml_fixture: Path, monkeypatch
) -> None:
    from backend.app.core.resource_guard import Decision, ResourceGuard

    class SevereConflictAdapter(BatchDIncrementalAdapter):
        _conflict_peer_rows = (
            ("baostock", "AAPL", "2026-06-15", 100.0),
            ("qmt_xtdata", "AAPL", "2026-06-15", 150.0),
        )

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    orch, _ = _orch_stack(tmp_path, registry_yaml_fixture)
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    adapter = SevereConflictAdapter(reg)
    orch.run_incremental(
        _incremental_spec("job-conflict-ver"),
        adapter=adapter,
        conflict_staging_table=CONFLICT_STG,
        clean_table=CLEAN_TABLE,
    )
    with orch._cm.writer() as con:
        row = con.execute(
            """
            SELECT tolerance_rule_set_id, rule_version
            FROM source_conflict
            WHERE job_id = ?
            LIMIT 1
            """,
            ["job-conflict-ver"],
        ).fetchone()
    assert row is not None
    assert row[0] == "p0_round_1"
    assert row[1] == "p0_round_1"


def test_dbRejectsInvalidFetchStatus(tmp_path: Path) -> None:
    cm = _migrated_cm(tmp_path)
    with cm.writer() as con, pytest.raises(duckdb.ConstraintException):
        con.execute(
            """
            INSERT INTO fetch_log (
                fetch_id, run_id, source_id, data_domain, status, row_count, fetch_time
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            ["f-bad", "run-1", "baostock", "market_bar_1d", "NOT_A_STATUS", 0],
        )


def test_dbRejectsInvalidManualReviewStatus(tmp_path: Path) -> None:
    cm = _migrated_cm(tmp_path)
    with cm.writer() as con, pytest.raises(duckdb.ConstraintException):
        con.execute(
            """
            INSERT INTO manual_review_queue (
                review_id, source_object_type, source_object_id, status
            ) VALUES (?, ?, ?, ?)
            """,
            ["r-bad", "conflict", "c-1", "INVALID_STATUS"],
        )


def test_backfillShard_successPath_validatesAndWritesClean(tmp_path: Path, monkeypatch) -> None:
    from backend.app.core.resource_guard import Decision, ResourceGuard
    from tests.test_sync_orchestrator import _BackfillCountAdapter

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    cm = _migrated_cm(tmp_path)
    orch = DataSyncOrchestrator(cm)
    spec = SyncJobSpec(
        run_id="run-bf-vw",
        job_id="job-bf-vw",
        job_type="backfill",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id=None,
        date_start=date(2026, 1, 1),
        date_end=date(2026, 1, 31),
        instrument_id=None,
        partition_key=None,
        trigger_reason="eco_catchup",
    )
    results = orch.run_backfill(
        spec,
        adapter=_BackfillCountAdapter(),
        clean_table=_BackfillCountAdapter.CLEAN,
    )
    assert any(r.status == "COMPLETED" for r in results)
    with cm.writer() as con:
        clean_count = con.execute(f"SELECT COUNT(*) FROM {_BackfillCountAdapter.CLEAN}").fetchone()[
            0
        ]
        report_count = con.execute(
            "SELECT COUNT(*) FROM validation_report WHERE job_id = ?", ["job-bf-vw"]
        ).fetchone()[0]
    assert clean_count >= 1
    assert report_count >= 1


def test_runReconcile_refetchStillDiff_entersManualReview(tmp_path: Path) -> None:
    from backend.app.datasources.fetch_result import FetchResult

    class StillDiffAdapter:
        source_id = "baostock"

        def fetch(self, req, *, con, job_id=None):
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS stg_refetch_diff (
                    source_id VARCHAR, instrument_id VARCHAR,
                    trade_date VARCHAR, close DOUBLE
                )
                """
            )
            con.execute("DELETE FROM stg_refetch_diff")
            con.execute(
                "INSERT INTO stg_refetch_diff VALUES (?, ?, ?, ?), (?, ?, ?, ?)",
                [
                    "baostock",
                    "AAPL",
                    "2026-06-15",
                    100.0,
                    "qmt_xtdata",
                    "AAPL",
                    "2026-06-15",
                    200.0,
                ],
            )
            return FetchResult(
                run_id=req.run_id,
                source_id=self.source_id,
                data_domain=req.data_domain,
                status="SUCCESS",
                row_count=2,
                fetch_time="2026-06-17T10:00:00Z",
                staging_table="stg_refetch_diff",
                raw_file_paths=["/tmp/refetch.parquet"],
            )

    orch = DataSyncOrchestrator(_migrated_cm(tmp_path))
    conflict_id = "conflict-refetch-diff"
    with orch._cm.writer() as con:
        con.execute(
            """
            INSERT INTO source_conflict (
                conflict_id, run_id, job_id, data_domain, field_name,
                primary_source, primary_value, competing_source, competing_value,
                normalized_diff, severity, reconcile_status, manual_review_required,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                conflict_id,
                "run-rc",
                "job-rc",
                "market_bar_1d",
                "close",
                "baostock",
                "100",
                "qmt_xtdata",
                "200",
                1.0,
                "severe",
                "OPEN",
                False,
                datetime.now(UTC),
            ],
        )
    result = orch.run_reconcile(conflict_id, adapter=StillDiffAdapter())
    assert result.status == "MANUAL_REVIEW_REQUIRED"


def test_runReconcile_refetchMatches_resolvesByRefetch(tmp_path: Path) -> None:
    from backend.app.datasources.fetch_result import FetchResult

    class MatchAdapter:
        source_id = "baostock"

        def fetch(self, req, *, con, job_id=None):
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS stg_refetch_match (
                    source_id VARCHAR, instrument_id VARCHAR,
                    trade_date VARCHAR, close DOUBLE
                )
                """
            )
            con.execute("DELETE FROM stg_refetch_match")
            con.execute(
                "INSERT INTO stg_refetch_match VALUES (?, ?, ?, ?), (?, ?, ?, ?)",
                [
                    "baostock",
                    "AAPL",
                    "2026-06-15",
                    100.0,
                    "qmt_xtdata",
                    "AAPL",
                    "2026-06-15",
                    100.0,
                ],
            )
            return FetchResult(
                run_id=req.run_id,
                source_id=self.source_id,
                data_domain=req.data_domain,
                status="SUCCESS",
                row_count=2,
                fetch_time="2026-06-17T10:00:00Z",
                staging_table="stg_refetch_match",
                raw_file_paths=["/tmp/refetch.parquet"],
            )

    orch = DataSyncOrchestrator(_migrated_cm(tmp_path))
    conflict_id = "conflict-refetch-match"
    with orch._cm.writer() as con:
        con.execute(
            """
            INSERT INTO source_conflict (
                conflict_id, run_id, job_id, data_domain, field_name,
                primary_source, primary_value, competing_source, competing_value,
                normalized_diff, severity, reconcile_status, manual_review_required,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                conflict_id,
                "run-rc",
                "job-rc",
                "market_bar_1d",
                "close",
                "baostock",
                "100",
                "qmt_xtdata",
                "100",
                0.0,
                "severe",
                "OPEN",
                False,
                datetime.now(UTC),
            ],
        )
    result = orch.run_reconcile(conflict_id, adapter=MatchAdapter())
    assert result.status == "COMPLETED"
    with orch._cm.writer() as con:
        status = con.execute(
            "SELECT reconcile_status FROM source_conflict WHERE conflict_id = ?",
            [conflict_id],
        ).fetchone()[0]
    assert status == "RESOLVED_BY_REFETCH"


def test_jobEventLog_payloadSchema_isMachineReadable(tmp_path: Path, monkeypatch) -> None:
    from backend.app.core.resource_guard import Decision, ResourceGuard

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    orch, adapter = _orch_stack(tmp_path, Path("tests/fixtures/source_registry_valid.yaml"))
    orch.run_incremental(
        _incremental_spec("job-payload"),
        adapter=adapter,
        conflict_staging_table=CONFLICT_STG,
        clean_table=CLEAN_TABLE,
    )
    with orch._cm.writer() as con:
        rows = con.execute(
            """
            SELECT payload_json FROM job_event_log
            WHERE job_id = ? AND payload_json IS NOT NULL
            """,
            ["job-payload"],
        ).fetchall()
    assert rows
    for (payload_json,) in rows:
        payload = parse_event_payload(payload_json)
        assert isinstance(payload, dict)
        if payload:
            assert any(key in payload for key in SCHEMA_KEYS)


def test_partialSuccess_eachItemWritesAuditEvent(tmp_path: Path, monkeypatch) -> None:
    from backend.app.core.resource_guard import Decision, ResourceGuard
    from tests.test_sync_orchestrator import _BackfillCountAdapter

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    orch = DataSyncOrchestrator(_migrated_cm(tmp_path))
    spec = SyncJobSpec(
        run_id="run-partial",
        job_id="job-partial",
        job_type="backfill",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id=None,
        date_start=date(2026, 1, 1),
        date_end=date(2026, 3, 31),
        instrument_id=None,
        partition_key=None,
        trigger_reason="eco_catchup",
    )
    orch.run_backfill(
        spec,
        adapter=_BackfillCountAdapter(),
        clean_table=_BackfillCountAdapter.CLEAN,
    )
    with orch._cm.writer() as con:
        events = con.execute(
            """
            SELECT task_id, event_type, payload_json
            FROM job_event_log
            WHERE job_id = ? AND task_id IS NOT NULL
            """,
            ["job-partial"],
        ).fetchall()
    assert len(events) >= 3
    for _task_id, _event_type, payload_json in events:
        payload = parse_event_payload(payload_json)
        assert payload.get("task_id") is not None or payload.get("decision") is not None


def test_allowedDomains_dbLoaderRoundTrip(registry_yaml_fixture: Path, tmp_path: Path) -> None:
    cm = _migrated_cm(tmp_path)
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    with cm.writer() as con:
        reg.sync_to_db(con, tombstone_missing=False)
        row = con.execute(
            """
            SELECT allowed_domain, allowed_domains_json
            FROM source_registry WHERE source_id = 'baostock'
            """
        ).fetchone()
    assert row is not None
    db_domains = json.loads(row[0])
    json_domains = json.loads(row[1])
    assert db_domains == json_domains
    rec = reg.get("baostock")
    assert frozenset(db_domains) == rec.allowed_domains


def test_dataQualityLog_persistsRuleVersion(tmp_path: Path) -> None:
    cm = _migrated_cm(tmp_path)
    validator = DataQualityValidator()
    with cm.writer() as con:
        con.execute(
            """
            CREATE TABLE stg_rule_ver (
                instrument_id VARCHAR, trade_date VARCHAR, close DOUBLE,
                source_used VARCHAR, batch_id VARCHAR, source_id VARCHAR
            )
            """
        )
        con.execute(
            """
            INSERT INTO stg_rule_ver VALUES
            (NULL, '2026-06-15', 1.0, 'baostock', 'b1', 'baostock')
            """
        )
        report = validator.validate_table(
            con,
            DataQualityRequest(
                run_id="run-rv",
                job_id="job-rv",
                data_domain="market_bar_1d",
                source_id="baostock",
                staging_table="stg_rule_ver",
                primary_keys=("instrument_id", "trade_date"),
                required_fields=("close", "source_used"),
                rule_set_id="p0_round_1",
            ),
            expected_columns=(
                "instrument_id",
                "trade_date",
                "close",
                "source_used",
                "batch_id",
                "source_id",
            ),
            timestamp_fields=("trade_date",),
        )
        row = con.execute(
            """
            SELECT rule_version FROM data_quality_log
            WHERE validation_report_id = ?
            LIMIT 1
            """,
            [report.validation_report_id],
        ).fetchone()
    assert row is not None
    assert row[0] == "p0_round_1"


def test_runReconcile_refetchFails_entersManualReview(tmp_path: Path) -> None:
    from backend.app.datasources.fetch_result import FetchResult

    class FailFetchAdapter:
        source_id = "baostock"

        def fetch(self, req, *, con, job_id=None):
            return FetchResult(
                run_id=req.run_id,
                source_id=self.source_id,
                data_domain=req.data_domain,
                status="NETWORK_ERROR",
                row_count=0,
                fetch_time="2026-06-17T10:00:00Z",
                error_message="reconcile fetch failed",
                retry_count=2,
            )

    orch = DataSyncOrchestrator(_migrated_cm(tmp_path))
    conflict_id = "conflict-refetch-fail"
    with orch._cm.writer() as con:
        con.execute(
            """
            INSERT INTO source_conflict (
                conflict_id, run_id, job_id, data_domain, field_name,
                primary_source, primary_value, competing_source, competing_value,
                normalized_diff, severity, reconcile_status, manual_review_required,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                conflict_id,
                "run-rc",
                "job-rc",
                "market_bar_1d",
                "close",
                "baostock",
                "100",
                "qmt_xtdata",
                "200",
                1.0,
                "severe",
                "OPEN",
                False,
                datetime.now(UTC),
            ],
        )
    result = orch.run_reconcile(conflict_id, adapter=FailFetchAdapter())
    assert result.status == "MANUAL_REVIEW_REQUIRED"


def test_eventPayload_parseMalformed_returnsParseError() -> None:
    from backend.app.sync.event_payload import parse_event_payload, payload_parse_failed

    payload = parse_event_payload("{not-json")
    assert payload_parse_failed(payload)


def test_incrementalJob_emitsItemSuccessEvent(
    tmp_path: Path, registry_yaml_fixture: Path, monkeypatch
) -> None:
    from backend.app.core.resource_guard import Decision, ResourceGuard

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    orch, adapter = _orch_stack(tmp_path, registry_yaml_fixture)
    orch.run_incremental(
        _incremental_spec("job-item-success"),
        adapter=adapter,
        conflict_staging_table=CONFLICT_STG,
        clean_table=CLEAN_TABLE,
    )
    with orch._cm.writer() as con:
        row = con.execute(
            """
            SELECT event_type, payload_json FROM job_event_log
            WHERE job_id = ? AND event_type = 'ITEM_SUCCESS'
            """,
            ["job-item-success"],
        ).fetchone()
    assert row is not None


def test_backfill_requiresCleanTable(tmp_path: Path, monkeypatch) -> None:
    from datetime import date

    from backend.app.core.resource_guard import Decision, ResourceGuard
    from tests.test_sync_orchestrator import _BackfillCountAdapter

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    orch = DataSyncOrchestrator(_migrated_cm(tmp_path))
    spec = SyncJobSpec(
        run_id="run-req",
        job_id="job-req",
        job_type="backfill",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id=None,
        date_start=date(2026, 1, 1),
        date_end=date(2026, 1, 31),
        instrument_id=None,
        partition_key=None,
        trigger_reason="eco_catchup",
    )
    with pytest.raises(TypeError):
        orch.run_backfill(spec, adapter=_BackfillCountAdapter())
