"""数据质量校验器纯逻辑测试（Batch C 8.3）。

覆盖范围：staging 行级规则、表级持久化、FetchResult 证据链与 Layer1/Layer3 专项规则。
"""

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
    """覆盖范围：market_bar_1d 合法行情行通过全量质量规则
    测试对象：DataQualityValidator.validate_rows
    目的/目标：完整 OHLCV 行在枚举、时间戳、陈旧度规则下应放行 clean write
    验证点：status=PASSED；checked_rows=1；can_write_clean=True；findings 为空
    失败含义：合法行情被误拒，下游 clean 表写入被不必要阻断
    """
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
    """覆盖范围：主键字段为空时的 fail-closed
    测试对象：DataQualityValidator.validate_rows
    目的/目标：instrument_id 为空不得通过主键完整性检查
    验证点：status=FAILED；can_write_clean=False；quality_flags 含 MISSING_PRIMARY_KEY
    失败含义：无主键行可进入 clean 路径，数据去重与关联会失真
    """
    report = DataQualityValidator().validate_rows(
        _request(),
        [_row(instrument_id="")],
        expected_columns=EXPECTED_COLUMNS,
    )

    assert report.status == "FAILED"
    assert report.can_write_clean is False
    assert "MISSING_PRIMARY_KEY" in report.quality_flags


def test_validateRows_duplicatePrimaryKey_failed() -> None:
    """覆盖范围：同一主键多行重复检测
    测试对象：DataQualityValidator.validate_rows
    目的/目标：相同 instrument_id+trade_date 的两行应计为重复主键
    验证点：status=FAILED；failed_rows=1；quality_flags 含 DUPLICATE_PRIMARY_KEY
    失败含义：重复主键未拦截，clean 表可能出现覆盖或双写
    """
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
    """覆盖范围：必填字段缺失时 finding 业务上下文
    测试对象：DataQualityValidator.validate_rows / ValidationFinding
    目的/目标：close 为 None 应产出可审计的 MISSING_REQUIRED_FIELD finding
    验证点：status=FAILED；finding.severity=failed；row_key 含 AAPL 与日期；field_name=close；observed_value=None；expected_condition 与 message 含 required 语义
    失败含义：缺失必填字段无行级定位信息，运维无法对照具体坏行
    """
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
    assert finding.observed_value is None
    assert "required" in finding.expected_condition
    assert "required field" in finding.message


def test_validateRows_invalidTimestamp_failed() -> None:
    """覆盖范围：时间戳字段格式非法
    测试对象：DataQualityValidator.validate_rows
    目的/目标：trade_date 非日期字符串应触发时间戳规则
    验证点：status=FAILED；quality_flags 含 MISSING_TIMESTAMP
    失败含义：非法日期可混入 staging，时序分析与对齐会出错
    """
    report = DataQualityValidator().validate_rows(
        _request(),
        [_row(trade_date="not-a-date")],
        expected_columns=EXPECTED_COLUMNS,
        timestamp_fields=("trade_date",),
    )

    assert report.status == "FAILED"
    assert "MISSING_TIMESTAMP" in report.quality_flags


def test_validateRows_invalidEnum_failed() -> None:
    """覆盖范围：枚举字段越界取值
    测试对象：DataQualityValidator.validate_rows
    目的/目标：adjustment_type 不在允许集合内应拒绝
    验证点：status=FAILED；quality_flags 含 INVALID_ENUM
    失败含义：未知复权类型进入 clean 表，回测与展示语义不一致
    """
    report = DataQualityValidator().validate_rows(
        _request(),
        [_row(adjustment_type="surprise")],
        expected_columns=EXPECTED_COLUMNS,
        enum_values={"adjustment_type": ("none", "forward", "backward")},
    )

    assert report.status == "FAILED"
    assert "INVALID_ENUM" in report.quality_flags


def test_validateRows_schemaDrift_failedAndManualReview() -> None:
    """覆盖范围：未声明列的 schema 漂移
    测试对象：DataQualityValidator.validate_rows
    目的/目标：行内多出 expected_columns 未列字段应阻断并请求人工复核
    验证点：status=FAILED；needs_manual_review=True；can_write_clean=False；quality_flags 含 SCHEMA_DRIFT
    失败含义：供应商新增列静默入库，schema 契约与迁移无法对齐
    """
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
    """覆盖范围：as_of 超陈旧阈值时的 WARNING 路径
    测试对象：DataQualityValidator.validate_rows
    目的/目标：超过 max_stale_days 应告警但不阻断 clean write
    验证点：status=WARNING；can_write_clean=True；warning_rows=1；quality_flags 含 STALE_DATA
    失败含义：陈旧数据要么被误拒要么无告警，延迟监控失效
    """
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
    """覆盖范围：批次历史行数不足 WARNING
    测试对象：DataQualityValidator.validate_rows
    目的/目标：行数低于 min_history_rows 应 WARNING 且仍允许写入
    验证点：status=WARNING；can_write_clean=True；quality_flags 含 INSUFFICIENT_HISTORY
    失败含义：历史深度不足无告警，冷启动或断档场景无法被运维发现
    """
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
    """覆盖范围：OHLC 价格区间逻辑矛盾
    测试对象：DataQualityValidator.validate_rows
    目的/目标：high 低于 low 属于无效 K 线
    验证点：status=FAILED；quality_flags 含 INVALID_PRICE_RANGE
    失败含义：自相矛盾 OHLC 进入 clean 表，因子与风控计算会失真
    """
    report = DataQualityValidator().validate_rows(
        _request(),
        [_row(high=8.0, low=9.0)],
        expected_columns=EXPECTED_COLUMNS,
    )

    assert report.status == "FAILED"
    assert "INVALID_PRICE_RANGE" in report.quality_flags


def test_validateRows_negativePriceVolumeAmount_failed() -> None:
    """覆盖范围：价格、成交量、金额非负约束
    测试对象：DataQualityValidator.validate_rows
    目的/目标：负 open、负 volume、负 amount 应分别打标
    验证点：status=FAILED；quality_flags 同时含 NEGATIVE_PRICE、INVALID_VOLUME、INVALID_AMOUNT
    失败含义：负值行情混入，聚合统计与风险指标不可信
    """
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
    """覆盖范围：表级校验通过时 validation_report 持久化
    测试对象：DataQualityValidator.validate_table
    目的/目标：PASSED 报告应写入 DB 且无需 data_quality_log 明细行
    验证点：report.status=PASSED；validation_report 行 status/计数/can_write_clean 与报告一致；data_quality_log 计数为 0
    失败含义：表级校验结果不落库，DbValidationGate 无法按 report_id 追溯
    """
    cm = _cm(tmp_path)
    validator = DataQualityValidator()
    with cm.writer() as con:
        _create_quality_stage(con)
        con.execute("INSERT INTO stg_quality VALUES ('AAPL','2026-06-15',195.0,'qmt','b1')")
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
    """覆盖范围：FAILED 报告与 DbValidationGate 写入门禁联动
    测试对象：validate_table + DbValidationGate.assert_can_write
    目的/目标：can_write_clean=false 时下游写入门面应拒绝
    验证点：report.status=FAILED 且 can_write_clean=False；assert_can_write 抛出 ValidationRejected
    失败含义：质量未通过仍可 append clean，fail-closed 写路径被击穿
    """
    cm = _cm(tmp_path)
    validator = DataQualityValidator()
    with cm.writer() as con:
        _create_quality_stage(con)
        con.execute("INSERT INTO stg_quality VALUES (NULL,'2026-06-15',195.0,'qmt','b1')")
        report = validator.validate_table(
            con,
            _request(staging_table="stg_quality", required_fields=("close", "source_used")),
            expected_columns=("instrument_id", "trade_date", "close", "source_used", "batch_id"),
            timestamp_fields=("trade_date",),
        )

    assert report.status == "FAILED"
    assert report.can_write_clean is False
    with pytest.raises(ValidationRejected, match="status=FAILED"):
        DbValidationGate(cm).assert_can_write(report.validation_report_id, "append_only")


def test_validateFetchResult_successMissingStagingTable_notCleanWriteReady(tmp_path: Path) -> None:
    """覆盖范围：FetchResult 成功但 staging 表不存在
    测试对象：DataQualityValidator.validate_fetch_result
    目的/目标：SUCCESS 状态不能掩盖缺失 staging 表
    验证点：status=FAILED；can_write_clean=False；quality_flags 含 MISSING_STAGING_TABLE
    失败含义：无 staging 仍可标记可写，fetch 成功与可落库语义脱钩
    """
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
    """覆盖范围：FetchResult 声明 raw 路径但文件缺失
    测试对象：DataQualityValidator.validate_fetch_result
    目的/目标：raw_file_paths 指向不存在文件应阻断 clean write
    验证点：status=FAILED；can_write_clean=False；quality_flags 含 MISSING_RAW_EVIDENCE
    失败含义：无 raw 证据仍可写 clean，取证与重放链断裂
    """
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
    """覆盖范围：校验失败不得破坏 raw 证据文件
    测试对象：DataQualityValidator.validate_fetch_result
    目的/目标：FAILED 后 raw 文件字节内容应保持原样
    验证点：report.status=FAILED；raw_path.read_bytes 与写入前一致
    失败含义：质量校验改写或删除 raw，失败现场无法复现与审计
    """
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
    """覆盖范围：Layer1 source_used 血缘必填规则
    测试对象：DataQualityValidator.validate_rows
    目的/目标：缺失 source_used 应触发 MISSING_SOURCE_USED 且含 lineage 语义
    验证点：status=FAILED；finding.rule_id=MISSING_SOURCE_USED；field_name=source_used；expected_condition 含 lineage
    失败含义：无来源血缘行可入库，多源冲突与追溯无法定位主源
    """
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
    """覆盖范围：fallback 无原因说明的 fail-closed
    测试对象：DataQualityValidator.validate_rows
    目的/目标：fallback_used=True 且 fallback_reason 为空应拒绝
    验证点：status=FAILED；quality_flags 含 FALLBACK_WITHOUT_REASON
    失败含义：静默 fallback 无审计理由，主备切换不可解释
    """
    report = DataQualityValidator().validate_rows(
        _request(),
        [_row(fallback_used=True, fallback_reason=None)],
        expected_columns=EXPECTED_COLUMNS,
    )

    assert report.status == "FAILED"
    assert "FALLBACK_WITHOUT_REASON" in report.quality_flags


def test_validateRows_blindspotWithRawValue_failed() -> None:
    """覆盖范围：盲点行不得携带 raw_value
    测试对象：DataQualityValidator.validate_rows
    目的/目标：is_blindspot=True 且存在 raw_value 违反盲点契约
    验证点：status=FAILED；quality_flags 含 BLINDSPOT_SHOULD_NOT_HAVE_VALUE
    失败含义：不可观测指标却带原始值，Layer1 盲点边界被突破
    """
    report = DataQualityValidator().validate_rows(
        _request(),
        [_row(is_blindspot=True, raw_value="secret")],
        expected_columns=EXPECTED_COLUMNS,
    )

    assert report.status == "FAILED"
    assert "BLINDSPOT_SHOULD_NOT_HAVE_VALUE" in report.quality_flags


def test_validateRows_layer3DuplicateAnchorId_failed() -> None:
    """覆盖范围：Layer3 anchor_id 唯一性
    测试对象：DataQualityValidator.validate_rows（layer3_anchors）
    目的/目标：重复 anchor_id 应拒绝且无行情行时仍校验锚点
    验证点：status=FAILED；quality_flags 含 DUPLICATE_ANCHOR_ID
    失败含义：重复锚点进入 Layer3，图结构与路由解析歧义
    """
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
    """覆盖范围：Layer3 node_id 引用完整性
    测试对象：DataQualityValidator.validate_rows（layer3_anchors）
    目的/目标：anchor 指向未知 node_id 应拒绝
    验证点：status=FAILED；quality_flags 含 MISSING_NODE_REFERENCE
    失败含义：悬空锚点引用入库，Layer3 图遍历会遇到断链
    """
    report = DataQualityValidator().validate_rows(
        _request(),
        [],
        layer3_anchors=[{"anchor_id": "a1", "node_id": "missing", "priority": "P1"}],
        known_node_ids=frozenset({"n1"}),
    )

    assert report.status == "FAILED"
    assert "MISSING_NODE_REFERENCE" in report.quality_flags


def test_validateRows_layer3P0MissingSourceKeys_failed() -> None:
    """覆盖范围：Layer3 P0 锚点必填 source_keys
    测试对象：DataQualityValidator.validate_rows（layer3_anchors）
    目的/目标：priority=P0 且无 source_keys 应拒绝
    验证点：status=FAILED；quality_flags 含 P0_MISSING_SOURCE_KEYS
    失败含义：P0 锚点无源键绑定，关键观测无法映射到数据源
    """
    report = DataQualityValidator().validate_rows(
        _request(),
        [],
        layer3_anchors=[{"anchor_id": "a1", "node_id": "n1", "priority": "P0"}],
        known_node_ids=frozenset({"n1"}),
    )

    assert report.status == "FAILED"
    assert "P0_MISSING_SOURCE_KEYS" in report.quality_flags


def test_validateRows_missingPrimaryKey_findingHasContractFields() -> None:
    """覆盖范围：主键缺失 finding 契约字段完整性
    测试对象：DataQualityValidator.validate_rows / ValidationFinding
    目的/目标：MISSING_PRIMARY_KEY finding 应含标准 severity、field_name 与 expected_condition
    验证点：finding.severity=failed；field_name=instrument_id；message 非空；expected_condition 含 primary key
    失败含义：主键违规 finding 缺契约字段，自动化报表与人工复核无法解析
    """
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
