"""R3G-01 rehearsal report tests — contract required_report_fields."""

from __future__ import annotations

from backend.app.ops.data_health import DataHealthCheckResult, build_report
from backend.app.ops.sandbox_clean_write.rehearsal_report import (
    build_data_health_summary,
    build_rehearsal_report,
    required_report_fields,
)
from tests.contract_gate_support import PROJECT_ROOT


def _sample_dh_report() -> object:
    checks = [
        DataHealthCheckResult(
            rule_id="DUPLICATE_PRIMARY_KEY",
            severity="INFO",
            status="PASS",
            source_id="baostock",
            domain="market_bar_1d",
            evidence_path="bars.json",
            row_count=2,
            message="ok",
        ),
        DataHealthCheckResult(
            rule_id="INVALID_OHLC",
            severity="WARN",
            status="WARN",
            source_id="baostock",
            domain="market_bar_1d",
            evidence_path="bars.json",
            row_count=2,
            message="warn",
        ),
    ]
    return build_report(checks, profile="market_bar_p0", gate_ready=False)


def test_rehearsalReport_requiredFieldsFromContract() -> None:
    """覆盖范围：契约 required_report_fields 全字段
    测试对象：required_report_fields + build_rehearsal_report
    目的/目标：排练报告 JSON 须含 lineage 与 WriteManager 审计字段
    验证点：契约列出的每个字段均在 report payload 中
    失败含义：报告缺字段，3G 证据链不可追溯
    """
    fields = required_report_fields()
    assert "write_manager_operation_id" in fields
    assert "rollback_artifact_path" in fields
    dh = _sample_dh_report()
    report = build_rehearsal_report(
        candidate_set="r3g_p0",
        source_id="baostock",
        domain="cn_equity_daily_bar",
        bundle_rows={"raw": 2, "staged": 2, "clean": 1},
        window_start="2024-01-02",
        window_end="2024-01-03",
        validation_status="PASSED",
        data_health_status=dh.overall_status,
        data_health_summary=build_data_health_summary(dh),
        source_fetch_id_coverage=1.0,
        content_hash_coverage=1.0,
        schema_hash_coverage=0.0,
        write_manager_operation_id="wm-test-id",
        rollback_artifact_path=".audit-sandbox/round3g/evidence/rollback_artifact.json",
        symbol_or_series_count=1,
    )
    for field in fields:
        assert field in report, f"missing contract field: {field}"


def test_rehearsalReport_dataHealthSummary_nestedCounts() -> None:
    """覆盖范围：嵌套 data_health_summary 计数
    测试对象：build_data_health_summary
    目的/目标：DH 结果以 pass/warn/fail 与 violation 计数呈现，非自由文本
    验证点：summary 含 validation_pass_count、duplicate_primary_key_count 等键
    失败含义：报告退化为不可机读的 prose-only 摘要
    """
    dh = _sample_dh_report()
    summary = build_data_health_summary(dh)
    assert "validation_pass_count" in summary
    assert "validation_warn_count" in summary
    assert "validation_fail_count" in summary
    assert "duplicate_primary_key_count" in summary
    assert "ohlc_violation_count" in summary
    assert "calendar_gap_violation_count" in summary
    assert summary["validation_pass_count"] >= 1


def test_rehearsalReport_sandboxOnlyFlags() -> None:
    """覆盖范围：排练报告 sandbox-only 语义
    测试对象：build_rehearsal_report 附加字段
    目的/目标：报告不得宣称 production-live 或允许生产 mutation
    验证点：production_mutation_allowed is False；production_live_claim is False
    失败含义：排练报告误宣称生产写入门已打开
    """
    dh = _sample_dh_report()
    report = build_rehearsal_report(
        candidate_set="r3g_p0",
        source_id="fred",
        domain="macro_series",
        bundle_rows={"raw": 1, "staged": 1, "clean": 1},
        window_start="2024-01-02",
        window_end="2024-01-02",
        validation_status="PASSED",
        data_health_status=dh.overall_status,
        data_health_summary=build_data_health_summary(dh),
        source_fetch_id_coverage=1.0,
        content_hash_coverage=1.0,
        schema_hash_coverage=0.0,
        write_manager_operation_id="wm-fred",
        rollback_artifact_path="rollback.json",
        symbol_or_series_count=1,
    )
    assert report["production_mutation_allowed"] is False
    assert report["sandbox_only"] is True
    assert report["production_live_claim"] is False
