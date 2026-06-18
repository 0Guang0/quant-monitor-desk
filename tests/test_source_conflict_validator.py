"""Pure logic tests for SourceConflictValidator (Batch C 8.5)."""

from __future__ import annotations

from pathlib import Path

from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.validators.source_conflict import (
    SourceConflictRequest,
    SourceConflictValidator,
)


def _request(**overrides: object) -> SourceConflictRequest:
    data: dict[str, object] = {
        "run_id": "run-1",
        "job_id": "job-1",
        "data_domain": "market_bar_1d",
        "primary_source": "qmt",
        "validation_sources": ("baostock",),
        "key_fields": ("instrument_id", "trade_date"),
        "comparable_fields": ("close",),
        "tolerance_rule_set_id": "p0_round_1",
    }
    data.update(overrides)
    return SourceConflictRequest(**data)


def _row(source_id: str, **overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "source_id": source_id,
        "instrument_id": "AAPL",
        "trade_date": "2026-06-15",
        "close": 100.0,
        "volume": 1_000.0,
        "settlement_price": 200.0,
        "main_inflow": 10_000.0,
    }
    data.update(overrides)
    return data


def _cm(tmp_path: Path) -> ConnectionManager:
    cm = ConnectionManager(tmp_path / "conflict.duckdb")
    with cm.writer() as con:
        apply_migrations(con)
    return cm


def _create_conflict_stage(con) -> None:
    con.execute(
        """
        CREATE TABLE stg_conflict (
            source_id VARCHAR,
            instrument_id VARCHAR,
            trade_date VARCHAR,
            close DOUBLE,
            main_inflow DOUBLE
        )
        """
    )


def test_validateRows_objectiveValueWithinTolerance_passedNoConflict() -> None:
    report = SourceConflictValidator().validate_rows(
        _request(),
        [_row("qmt", close=100.0), _row("baostock", close=100.04)],
    )

    assert report.status == "PASSED"
    assert report.can_write_primary_value is True
    assert report.needs_reconcile is False
    assert report.needs_manual_review is False
    assert report.conflicts == ()


def test_validateRows_objectiveValueAboveWarningThreshold_warning() -> None:
    report = SourceConflictValidator().validate_rows(
        _request(),
        [_row("qmt", close=100.0), _row("baostock", close=100.1)],
    )

    assert report.status == "WARNING"
    assert report.can_write_primary_value is True
    assert report.needs_reconcile is False
    conflict = report.conflicts[0]
    assert conflict.field_name == "close"
    assert conflict.competing_source == "baostock"
    assert conflict.severity == "warning"
    assert conflict.manual_review_required is False


def test_validateRows_objectiveValueAboveSevereThreshold_severeConflict() -> None:
    report = SourceConflictValidator().validate_rows(
        _request(),
        [_row("qmt", close=100.0), _row("baostock", close=100.25)],
    )

    assert report.status == "SEVERE_CONFLICT"
    assert report.can_write_primary_value is False
    assert report.needs_reconcile is True
    assert report.needs_manual_review is False
    conflict = report.conflicts[0]
    assert conflict.severity == "severe"
    assert conflict.manual_review_required is False
    assert conflict.normalized_diff == 0.0025


def test_validateRows_atExactSevereThreshold_classifiesWarningNotSevere() -> None:
    """relative_severe=0.002; diff must exceed threshold for severe."""
    report = SourceConflictValidator().validate_rows(
        _request(),
        [_row("qmt", close=100.0), _row("baostock", close=100.199)],
    )

    assert report.status == "WARNING"
    assert report.needs_reconcile is False
    assert report.conflicts[0].severity == "warning"


def test_validateRows_sourceSpecificMethodologyField_marksSeparateBySource() -> None:
    report = SourceConflictValidator().validate_rows(
        _request(comparable_fields=("main_inflow",)),
        [_row("qmt", main_inflow=10_000.0), _row("baostock", main_inflow=12_000.0)],
    )

    assert report.status == "PASSED"
    assert report.can_write_primary_value is True
    assert report.conflicts[0].severity == "methodology_difference"
    assert report.conflicts[0].manual_review_required is False


def test_validateRows_missingPeerSource_noFalseSevereConflict() -> None:
    report = SourceConflictValidator().validate_rows(
        _request(validation_sources=("missing_vendor",)),
        [_row("qmt", close=100.0)],
    )

    assert report.status == "PASSED"
    assert report.can_write_primary_value is True
    assert report.conflicts == ()


def test_validateRows_thresholdLookupUsesDataDomainAndField() -> None:
    market_report = SourceConflictValidator().validate_rows(
        _request(
            data_domain="market_bar_1d",
            comparable_fields=("volume",),
        ),
        [_row("qmt", volume=1_000.0), _row("baostock", volume=1_010.0)],
    )
    futures_report = SourceConflictValidator().validate_rows(
        _request(
            data_domain="futures_bar",
            comparable_fields=("settlement_price",),
        ),
        [
            _row("qmt", settlement_price=200.0),
            _row("baostock", settlement_price=201.0),
        ],
    )

    assert market_report.status == "WARNING"
    assert market_report.conflicts[0].field_name == "volume"
    assert market_report.conflicts[0].severity == "warning"
    assert futures_report.status == "SEVERE_CONFLICT"
    assert futures_report.conflicts[0].field_name == "settlement_price"


def test_validateTable_severeConflict_persistsConflictAwaitingReconcile(
    tmp_path: Path,
) -> None:
    cm = _cm(tmp_path)
    validator = SourceConflictValidator()
    with cm.writer() as con:
        _create_conflict_stage(con)
        con.execute(
            """
            INSERT INTO stg_conflict VALUES
                ('qmt', 'AAPL', '2026-06-15', 100.0, 10000.0),
                ('baostock', 'AAPL', '2026-06-15', 100.25, 12000.0)
            """
        )

        report = validator.validate_table(con, _request(), staging_table="stg_conflict")

        conflict = con.execute(
            """
            SELECT run_id, job_id, data_domain, instrument_id, field_name,
                   primary_source, primary_value, competing_source, competing_value,
                   severity, reconcile_status, manual_review_required
            FROM source_conflict
            """
        ).fetchone()
        review_count = con.execute("SELECT COUNT(*) FROM manual_review_queue").fetchone()[0]

    assert report.status == "SEVERE_CONFLICT"
    assert report.can_write_primary_value is False
    assert report.needs_reconcile is True
    assert report.needs_manual_review is False
    assert conflict == (
        "run-1",
        "job-1",
        "market_bar_1d",
        "AAPL",
        "close",
        "qmt",
        "100.0",
        "baostock",
        "100.25",
        "severe",
        "OPEN",
        False,
    )
    assert review_count == 0


def test_validateTable_multiInstrumentSevereConflicts_distinctInstrumentIds(
    tmp_path: Path,
) -> None:
    cm = _cm(tmp_path)
    validator = SourceConflictValidator()
    with cm.writer() as con:
        _create_conflict_stage(con)
        con.execute(
            """
            INSERT INTO stg_conflict VALUES
                ('qmt', 'AAPL', '2026-06-15', 100.0, 10000.0),
                ('baostock', 'AAPL', '2026-06-15', 100.25, 12000.0),
                ('qmt', 'MSFT', '2026-06-15', 200.0, 10000.0),
                ('baostock', 'MSFT', '2026-06-15', 200.5, 12000.0)
            """
        )

        report = validator.validate_table(con, _request(), staging_table="stg_conflict")
        rows = con.execute(
            "SELECT instrument_id, field_name FROM source_conflict ORDER BY instrument_id"
        ).fetchall()

    assert report.status == "SEVERE_CONFLICT"
    assert rows == [("AAPL", "close"), ("MSFT", "close")]


def test_recordUnresolvedReconcile_enqueuesManualReview(tmp_path: Path) -> None:
    cm = _cm(tmp_path)
    validator = SourceConflictValidator()
    with cm.writer() as con:
        _create_conflict_stage(con)
        con.execute(
            """
            INSERT INTO stg_conflict VALUES
                ('qmt', 'AAPL', '2026-06-15', 100.0, 10000.0),
                ('baostock', 'AAPL', '2026-06-15', 100.25, 12000.0)
            """
        )
        validator.validate_table(con, _request(), staging_table="stg_conflict")
        conflict_id = con.execute(
            "SELECT conflict_id FROM source_conflict LIMIT 1"
        ).fetchone()[0]
        validator.record_unresolved_reconcile(con, conflict_id)
        review = con.execute(
            "SELECT source_object_id, status FROM manual_review_queue"
        ).fetchone()
        flags = con.execute(
            "SELECT reconcile_status, manual_review_required FROM source_conflict"
        ).fetchone()

    assert review[0] == conflict_id
    assert review[1] == "OPEN"
    assert flags == ("UNRESOLVED", True)


def test_validateTable_methodologyDifference_doesNotWriteManualReview(
    tmp_path: Path,
) -> None:
    cm = _cm(tmp_path)
    validator = SourceConflictValidator()
    with cm.writer() as con:
        _create_conflict_stage(con)
        con.execute(
            """
            INSERT INTO stg_conflict VALUES
                ('qmt', 'AAPL', '2026-06-15', 100.0, 10000.0),
                ('baostock', 'AAPL', '2026-06-15', 100.0, 12000.0)
            """
        )

        report = validator.validate_table(
            con,
            _request(comparable_fields=("main_inflow",)),
            staging_table="stg_conflict",
        )
        conflict_count = con.execute("SELECT COUNT(*) FROM source_conflict").fetchone()[0]
        review_count = con.execute("SELECT COUNT(*) FROM manual_review_queue").fetchone()[0]

    assert report.status == "PASSED"
    assert report.can_write_primary_value is True
    assert report.conflicts[0].severity == "methodology_difference"
    assert conflict_count == 0
    assert review_count == 0
