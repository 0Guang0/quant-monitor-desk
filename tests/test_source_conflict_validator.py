"""多源冲突校验器纯逻辑测试（Batch C 8.5）。

覆盖范围：主源与校验源客观字段偏差分级、方法论差异、表级落库与人工复核队列。
"""

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
    """覆盖范围：客观字段偏差在容忍度内
    测试对象：SourceConflictValidator.validate_rows
    目的/目标：主源与校验源 close 偏差极小时应无冲突且可写主源值
    验证点：status=PASSED；can_write_primary_value=True；needs_reconcile=False；needs_manual_review=False；conflicts 为空
    失败含义：正常偏差被误报冲突，主源写入被不必要阻断
    """
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
    """覆盖范围：客观字段超 warning 阈值但未达 severe
    测试对象：SourceConflictValidator.validate_rows
    目的/目标：中等偏差应 WARNING 且仍可写主源值
    验证点：status=WARNING；can_write_primary_value=True；needs_reconcile=False；首条 conflict 为 close/baostock、severity=warning、不需人工复核
    失败含义：warning 级偏差被静默或误升 severe，运维无法分级处理
    """
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
    """覆盖范围：客观字段超 severe 阈值
    测试对象：SourceConflictValidator.validate_rows
    目的/目标：大偏差应 SEVERE_CONFLICT 且禁止写主源、需 reconcile
    验证点：status=SEVERE_CONFLICT；can_write_primary_value=False；needs_reconcile=True；conflict.severity=severe；normalized_diff=0.0025
    失败含义：严重分歧仍可写主源，错误行情静默入主表
    """
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
    """覆盖范围：severe 阈值边界（不含等于）
    测试对象：SourceConflictValidator.validate_rows
    目的/目标：恰在 relative_severe 边界应 WARNING 而非 severe
    验证点：status=WARNING；needs_reconcile=False；conflicts[0].severity=warning
    失败含义：边界值分类错误，轻微超限被误拦或严重超限被放行
    """
    report = SourceConflictValidator().validate_rows(
        _request(),
        [_row("qmt", close=100.0), _row("baostock", close=100.199)],
    )

    assert report.status == "WARNING"
    assert report.needs_reconcile is False
    assert report.conflicts[0].severity == "warning"


def test_validateRows_sourceSpecificMethodologyField_marksSeparateBySource() -> None:
    """覆盖范围：方法论差异字段按源区分、不视为数值冲突
    测试对象：SourceConflictValidator.validate_rows
    目的/目标：main_inflow 等源特异字段偏差应标 methodology_difference 且仍可写主源
    验证点：status=PASSED；can_write_primary_value=True；conflicts[0].severity=methodology_difference；不需人工复核
    失败含义：口径差异被当成 severe 冲突，主源资金流字段被误拦
    """
    report = SourceConflictValidator().validate_rows(
        _request(comparable_fields=("main_inflow",)),
        [_row("qmt", main_inflow=10_000.0), _row("baostock", main_inflow=12_000.0)],
    )

    assert report.status == "PASSED"
    assert report.can_write_primary_value is True
    assert report.conflicts[0].severity == "methodology_difference"
    assert report.conflicts[0].manual_review_required is False


def test_validateRows_missingPeerSource_noFalseSevereConflict() -> None:
    """覆盖范围：校验源无对端行时不产生伪严重冲突
    测试对象：SourceConflictValidator.validate_rows
    目的/目标：仅有主源行、对端 vendor 缺失时应 PASSED 且无 conflicts
    验证点：status=PASSED；can_write_primary_value=True；conflicts 为空
    失败含义：缺对端被误报 severe，正常单源批次无法写入
    """
    report = SourceConflictValidator().validate_rows(
        _request(validation_sources=("missing_vendor",)),
        [_row("qmt", close=100.0)],
    )

    assert report.status == "PASSED"
    assert report.can_write_primary_value is True
    assert report.conflicts == ()


def test_validateRows_thresholdLookupUsesDataDomainAndField() -> None:
    """覆盖范围：容忍度查找按 data_domain 与 field 区分
    测试对象：SourceConflictValidator.validate_rows
    目的/目标：market volume 与 futures settlement 应套用不同阈值规则
    验证点：market_bar_1d+volume→WARNING；futures_bar+settlement_price→SEVERE_CONFLICT；各自 conflict.field_name 正确
    失败含义：全域共用阈值，期货结算价与股票成交量误判同一严重级别
    """
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
    """覆盖范围：表级 severe 冲突写入 source_conflict 待 reconcile
    测试对象：SourceConflictValidator.validate_table
    目的/目标：severe 应落库 OPEN 行且不自动进 manual_review_queue
    验证点：report 为 SEVERE_CONFLICT 且不可写主源；source_conflict 行含 run/job/标的/双方值/severe/OPEN；manual_review_queue 计数为 0
    失败含义：严重冲突不落库，reconcile 工作流无法挂起待处理项
    """
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
    """覆盖范围：多标的 severe 冲突逐标的独立落库
    测试对象：SourceConflictValidator.validate_table
    目的/目标：AAPL 与 MSFT 各应一条 source_conflict 且 field 均为 close
    验证点：report.status=SEVERE_CONFLICT；source_conflict 两行 instrument_id 分别为 AAPL、MSFT
    失败含义：多标的冲突合并或漏记，单标的 reconcile 无法精准处理
    """
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
    """覆盖范围：未解决 reconcile 转入人工复核队列
    测试对象：SourceConflictValidator.record_unresolved_reconcile
    目的/目标：reconcile 失败应写 manual_review_queue 且 conflict 标 UNRESOLVED
    验证点：review.source_object_id 等于 conflict_id 且 status=OPEN；source_conflict.reconcile_status=UNRESOLVED 且 manual_review_required=True
    失败含义：僵持冲突无人工队列入口，运维无法接手未决项
    """
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
        conflict_id = con.execute("SELECT conflict_id FROM source_conflict LIMIT 1").fetchone()[0]
        validator.record_unresolved_reconcile(con, conflict_id)
        review = con.execute("SELECT source_object_id, status FROM manual_review_queue").fetchone()
        flags = con.execute(
            "SELECT reconcile_status, manual_review_required FROM source_conflict"
        ).fetchone()

    assert review[0] == conflict_id
    assert review[1] == "OPEN"
    assert flags == ("UNRESOLVED", True)


def test_validateTable_methodologyDifference_doesNotWriteManualReview(
    tmp_path: Path,
) -> None:
    """覆盖范围：方法论差异不写冲突表与人工队列
    测试对象：SourceConflictValidator.validate_table
    目的/目标：methodology_difference 应 PASSED 且 source_conflict/review 计数均为 0
    验证点：report.status=PASSED；can_write_primary_value=True；conflicts[0].severity=methodology_difference；两表计数为 0
    失败含义：口径差异误入 reconcile 或人工队列，制造无效运维负担
    """
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
