"""Pure logic tests for DataQualityValidator (Batch C 8.3)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.db.validation_gate import DbValidationGate, ValidationRejected
from backend.app.validators.data_quality import (
    DataQualityRequest,
    DataQualityValidator,
)


def _request(**overrides: object) -> DataQualityRequest:
    data: dict[str, object] = {
        "run_id": "run-1",
        "job_id": "job-1",
        "data_domain": "market_bar_1d",
        "source_id": "qmt",
        "staging_table": "stg_market_bar_1d",
        "primary_keys": ("instrument_id", "trade_date"),
        "required_fields": ("close", "source_used"),
        "rule_set_id": "p0_round_1",
    }
    data.update(overrides)
    return DataQualityRequest(**data)


def _row(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "instrument_id": "AAPL",
        "trade_date": "2026-06-15",
        "open": 10.0,
        "high": 12.0,
        "low": 9.0,
        "close": 11.0,
        "volume": 100.0,
        "amount": 1100.0,
        "adjustment_type": "none",
        "source_used": "qmt",
        "as_of_timestamp": "2026-06-15T15:00:00+00:00",
    }
    data.update(overrides)
    return data


EXPECTED_COLUMNS = tuple(_row().keys())


def _create_quality_stage(con) -> None:
    con.execute(
        """
        CREATE TABLE stg_quality (
            instrument_id VARCHAR,
            trade_date VARCHAR,
            close DOUBLE,
            source_used VARCHAR,
            batch_id VARCHAR
        )
        """
    )


def test_validateRows_validMarketBar_passesAndCanWriteClean() -> None:
    report = DataQualityValidator().validate_rows(
        _request(),
        [_row()],
        expected_columns=EXPECTED_COLUMNS,
        timestamp_fields=("trade_date", "as_of_timestamp"),
        enum_values={"adjustment_type": ("none", "forward", "backward")},
        as_of_field="as_of_timestamp",
        max_stale_days=7,
        min_history_rows=1,
        reference_time=datetime(2026, 6, 16, tzinfo=UTC),
    )

    assert report.status == "PASSED"
    assert report.checked_rows == 1
    assert report.can_write_clean is True
    assert report.findings == ()


def test_validateRows_missingPrimaryKey_failed() -> None:
    report = DataQualityValidator().validate_rows(
        _request(),
        [_row(instrument_id="")],
        expected_columns=EXPECTED_COLUMNS,
    )

    assert report.status == "FAILED"
    assert report.can_write_clean is False
    assert "MISSING_PRIMARY_KEY" in report.quality_flags


def test_validateRows_duplicatePrimaryKey_failed() -> None:
    rows = [_row(), _row(close=12.0)]

    report = DataQualityValidator().validate_rows(
        _request(),
        rows,
        expected_columns=EXPECTED_COLUMNS,
    )

    assert report.status == "FAILED"
    assert report.failed_rows == 1
    assert "DUPLICATE_PRIMARY_KEY" in report.quality_flags


def test_validateRows_missingRequiredField_findingHasBusinessContext() -> None:
    report = DataQualityValidator().validate_rows(
        _request(),
        [_row(close=None)],
        expected_columns=EXPECTED_COLUMNS,
    )

    finding = next(f for f in report.findings if f.rule_id == "MISSING_REQUIRED_FIELD")
    assert report.status == "FAILED"
    assert finding.severity == "failed"
    assert finding.row_key == "instrument_id=AAPL|trade_date=2026-06-15"
    assert finding.field_name == "close"
    assert finding.observed_value == "None"
    assert "required" in finding.expected_condition
    assert "required field" in finding.message


def test_validateRows_invalidTimestamp_failed() -> None:
    report = DataQualityValidator().validate_rows(
        _request(),
        [_row(trade_date="not-a-date")],
        expected_columns=EXPECTED_COLUMNS,
        timestamp_fields=("trade_date",),
    )

    assert report.status == "FAILED"
    assert "MISSING_TIMESTAMP" in report.quality_flags


def test_validateRows_invalidEnum_failed() -> None:
    report = DataQualityValidator().validate_rows(
        _request(),
        [_row(adjustment_type="surprise")],
        expected_columns=EXPECTED_COLUMNS,
        enum_values={"adjustment_type": ("none", "forward", "backward")},
    )

    assert report.status == "FAILED"
    assert "INVALID_ENUM" in report.quality_flags


def test_validateRows_schemaDrift_failedAndManualReview() -> None:
    row = _row()
    row["unexpected_vendor_column"] = "new"

    report = DataQualityValidator().validate_rows(
        _request(),
        [row],
        expected_columns=EXPECTED_COLUMNS,
    )

    assert report.status == "FAILED"
    assert report.needs_manual_review is True
    assert report.can_write_clean is False
    assert "SCHEMA_DRIFT" in report.quality_flags


def test_validateRows_staleData_warningCanStillWrite() -> None:
    report = DataQualityValidator().validate_rows(
        _request(),
        [_row(as_of_timestamp="2026-06-10T15:00:00+00:00")],
        expected_columns=EXPECTED_COLUMNS,
        as_of_field="as_of_timestamp",
        max_stale_days=2,
        reference_time=datetime(2026, 6, 16, tzinfo=UTC),
    )

    assert report.status == "WARNING"
    assert report.can_write_clean is True
    assert report.warning_rows == 1
    assert "STALE_DATA" in report.quality_flags


def test_validateRows_insufficientHistory_warning() -> None:
    report = DataQualityValidator().validate_rows(
        _request(),
        [_row()],
        expected_columns=EXPECTED_COLUMNS,
        min_history_rows=2,
    )

    assert report.status == "WARNING"
    assert report.can_write_clean is True
    assert "INSUFFICIENT_HISTORY" in report.quality_flags


def test_validateRows_highBelowLow_failed() -> None:
    report = DataQualityValidator().validate_rows(
        _request(),
        [_row(high=8.0, low=9.0)],
        expected_columns=EXPECTED_COLUMNS,
    )

    assert report.status == "FAILED"
    assert "INVALID_PRICE_RANGE" in report.quality_flags


def test_validateRows_negativePriceVolumeAmount_failed() -> None:
    rows = [
        _row(instrument_id="AAPL", open=-1.0),
        _row(instrument_id="MSFT", volume=-100.0),
        _row(instrument_id="NVDA", amount=-1.0),
    ]

    report = DataQualityValidator().validate_rows(
        _request(),
        rows,
        expected_columns=EXPECTED_COLUMNS,
    )

    assert report.status == "FAILED"
    assert {"NEGATIVE_PRICE", "INVALID_VOLUME", "INVALID_AMOUNT"}.issubset(
        set(report.quality_flags)
    )


def _cm(tmp_path: Path) -> ConnectionManager:
    cm = ConnectionManager(tmp_path / "validation.duckdb")
    with cm.writer() as con:
        apply_migrations(con)
    return cm


def test_validateTable_persistsValidationReportAndDataQualityLog(tmp_path: Path) -> None:
    cm = _cm(tmp_path)
    validator = DataQualityValidator()
    with cm.writer() as con:
        _create_quality_stage(con)
        con.execute(
            "INSERT INTO stg_quality VALUES ('AAPL','2026-06-15',195.0,'qmt','b1')"
        )
        report = validator.validate_table(
            con,
            _request(staging_table="stg_quality", required_fields=("close", "source_used")),
            expected_columns=("instrument_id", "trade_date", "close", "source_used", "batch_id"),
            timestamp_fields=("trade_date",),
        )

        stored = con.execute(
            """
            SELECT status, checked_rows, failed_rows, warning_rows,
                   can_write_clean, needs_manual_review
            FROM validation_report WHERE validation_report_id = ?
            """,
            [report.validation_report_id],
        ).fetchone()
        log_count = con.execute(
            "SELECT COUNT(*) FROM data_quality_log WHERE validation_report_id = ?",
            [report.validation_report_id],
        ).fetchone()[0]

    assert report.status == "PASSED"
    assert stored == ("PASSED", 1, 0, 0, True, False)
    assert log_count == 0


def test_validateTable_failedReportRejectedByDbValidationGate(tmp_path: Path) -> None:
    cm = _cm(tmp_path)
    validator = DataQualityValidator()
    with cm.writer() as con:
        _create_quality_stage(con)
        con.execute(
            "INSERT INTO stg_quality VALUES (NULL,'2026-06-15',195.0,'qmt','b1')"
        )
        report = validator.validate_table(
            con,
            _request(staging_table="stg_quality", required_fields=("close", "source_used")),
            expected_columns=("instrument_id", "trade_date", "close", "source_used", "batch_id"),
            timestamp_fields=("trade_date",),
        )

    assert report.status == "FAILED"
    assert report.can_write_clean is False
    with pytest.raises(ValidationRejected):
        DbValidationGate(cm).assert_can_write(report.validation_report_id, "append_only")


def test_validateFetchResult_successMissingStagingTable_notCleanWriteReady(tmp_path: Path) -> None:
    from backend.app.datasources.fetch_result import FetchResult

    validator = DataQualityValidator()
    fetch = FetchResult(
        run_id="run-1",
        source_id="qmt",
        data_domain="market_bar_1d",
        status="SUCCESS",
        staging_table="missing_staging",
        row_count=1,
        fetch_time="2026-06-17T10:00:00Z",
    )

    report = validator.validate_fetch_result(
        None,
        _request(staging_table="missing_staging"),
        fetch,
        expected_columns=EXPECTED_COLUMNS,
    )

    assert report.status == "FAILED"
    assert report.can_write_clean is False
    assert "MISSING_STAGING_TABLE" in report.quality_flags


def test_validateFetchResult_missingRawEvidence_notCleanWriteReady(tmp_path: Path) -> None:
    from backend.app.datasources.fetch_result import FetchResult

    missing_raw = tmp_path / "does-not-exist.json"
    fetch = FetchResult(
        run_id="run-1",
        source_id="qmt",
        data_domain="market_bar_1d",
        status="SUCCESS",
        raw_file_paths=[str(missing_raw)],
        row_count=1,
        fetch_time="2026-06-17T10:00:00Z",
    )

    report = DataQualityValidator().validate_fetch_result(
        None,
        _request(staging_table="stg_absent"),
        fetch,
        expected_columns=EXPECTED_COLUMNS,
    )

    assert report.status == "FAILED"
    assert report.can_write_clean is False
    assert "MISSING_RAW_EVIDENCE" in report.quality_flags


def test_validateFetchResult_failurePreservesRawEvidence(tmp_path: Path) -> None:
    from backend.app.datasources.fetch_result import FetchResult

    raw_path = tmp_path / "raw.json"
    raw_path.write_bytes(b'{"instrument_id":"AAPL"}')
    fetch = FetchResult(
        run_id="run-1",
        source_id="qmt",
        data_domain="market_bar_1d",
        status="SUCCESS",
        raw_file_paths=[str(raw_path)],
        row_count=1,
        fetch_time="2026-06-17T10:00:00Z",
    )

    report = DataQualityValidator().validate_fetch_result(
        None,
        _request(staging_table="stg_absent"),
        fetch,
        expected_columns=EXPECTED_COLUMNS,
    )

    assert report.status == "FAILED"
    assert raw_path.read_bytes() == b'{"instrument_id":"AAPL"}'


def test_validateRows_missingSourceUsed_emitsLayer1RuleId() -> None:
    report = DataQualityValidator().validate_rows(
        _request(),
        [_row(source_used=None)],
        expected_columns=EXPECTED_COLUMNS,
    )

    finding = next(f for f in report.findings if f.rule_id == "MISSING_SOURCE_USED")
    assert report.status == "FAILED"
    assert finding.field_name == "source_used"
    assert "lineage" in finding.expected_condition


def test_validateRows_fallbackWithoutReason_failed() -> None:
    report = DataQualityValidator().validate_rows(
        _request(),
        [_row(fallback_used=True, fallback_reason=None)],
        expected_columns=EXPECTED_COLUMNS,
    )

    assert report.status == "FAILED"
    assert "FALLBACK_WITHOUT_REASON" in report.quality_flags


def test_validateRows_blindspotWithRawValue_failed() -> None:
    report = DataQualityValidator().validate_rows(
        _request(),
        [_row(is_blindspot=True, raw_value="secret")],
        expected_columns=EXPECTED_COLUMNS,
    )

    assert report.status == "FAILED"
    assert "BLINDSPOT_SHOULD_NOT_HAVE_VALUE" in report.quality_flags


def test_validateRows_layer3DuplicateAnchorId_failed() -> None:
    anchors = [
        {"anchor_id": "a1", "node_id": "n1", "priority": "P1", "source_keys": "k"},
        {"anchor_id": "a1", "node_id": "n2", "priority": "P1", "source_keys": "k"},
    ]
    report = DataQualityValidator().validate_rows(
        _request(),
        [],
        layer3_anchors=anchors,
        known_node_ids=frozenset({"n1", "n2"}),
    )

    assert report.status == "FAILED"
    assert "DUPLICATE_ANCHOR_ID" in report.quality_flags


def test_validateRows_layer3MissingNodeReference_failed() -> None:
    report = DataQualityValidator().validate_rows(
        _request(),
        [],
        layer3_anchors=[{"anchor_id": "a1", "node_id": "missing", "priority": "P1"}],
        known_node_ids=frozenset({"n1"}),
    )

    assert report.status == "FAILED"
    assert "MISSING_NODE_REFERENCE" in report.quality_flags


def test_validateRows_layer3P0MissingSourceKeys_failed() -> None:
    report = DataQualityValidator().validate_rows(
        _request(),
        [],
        layer3_anchors=[{"anchor_id": "a1", "node_id": "n1", "priority": "P0"}],
        known_node_ids=frozenset({"n1"}),
    )

    assert report.status == "FAILED"
    assert "P0_MISSING_SOURCE_KEYS" in report.quality_flags


def test_validateRows_missingPrimaryKey_findingHasContractFields() -> None:
    report = DataQualityValidator().validate_rows(
        _request(),
        [_row(instrument_id="")],
        expected_columns=EXPECTED_COLUMNS,
    )

    finding = next(f for f in report.findings if f.rule_id == "MISSING_PRIMARY_KEY")
    assert finding.severity == "failed"
    assert finding.field_name == "instrument_id"
    assert finding.message
    assert "primary key" in finding.expected_condition
