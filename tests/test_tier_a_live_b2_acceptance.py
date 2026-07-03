"""M-DATA-03 S-R2-B2 — tier_a_live_acceptance B2 validate_table tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from backend.app.datasources.live_tier_router import TIER_A_SOURCES
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.ops.tier_a_live_acceptance import (
    run_acceptance_report,
    source_bindings,
)
from backend.app.ops.tier_a_live_incremental_dispatch import LiveIncrementalOutcome
from backend.app.validation.data_quality_validator import run_b2_validate_table
from backend.app.validators.data_quality import DataQualityRequest, DataQualityValidator


def _mock_outcome(source_id: str) -> LiveIncrementalOutcome:
    binding = source_bindings()[source_id]
    return LiveIncrementalOutcome(
        source_id=source_id,
        sync_status="COMPLETED",
        inspect_status="PASS",
        clean_table=binding["clean_table"],
        clean_row_count=1,
        detail="b2 acceptance mock",
    )


@pytest.mark.parametrize("source_id", sorted(TIER_A_SOURCES))
def test_runB2ValidateTable_usesSourceBindings(
    source_id: str,
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：11 源 source_bindings → validate_table 请求
    测试对象：run_b2_validate_table
    目的/目标：每源 B2 按契约 clean_table / rule_set_id / data_domain 校验
    验证点：DataQualityRequest.staging_table、rule_set_id、data_domain 与 binding 一致
    失败含义：B2 主路径未按统一验收层绑定表跑质量规则
    """
    from backend.app.ops.tier_a_live_acceptance import ensure_isolated_db

    binding = source_bindings()[source_id]
    db_path = ensure_isolated_db(isolated_live_data_root)
    captured: list[DataQualityRequest] = []

    def _capture_validate_table(
        self,
        con,
        request: DataQualityRequest,
        **kwargs: Any,
    ):
        captured.append(request)
        return DataQualityValidator()._build_report(checked_rows=0, findings=[])

    monkeypatch.setattr(DataQualityValidator, "validate_table", _capture_validate_table)

    status, _detail = run_b2_validate_table(
        source_id,
        binding=binding,
        db_path=db_path,
        run_id="run-b2-bindings",
        job_id=f"job-b2-{source_id}",
    )

    assert status == "PASSED"
    assert len(captured) == 1
    req = captured[0]
    assert req.source_id == source_id
    assert req.staging_table == binding["clean_table"]
    assert req.rule_set_id == binding["rule_set_id"]
    assert req.data_domain == binding["data_domain"]


def test_runB2ValidateTable_passesOnValidSecurityBarRow(
    isolated_live_data_root: Path,
) -> None:
    """覆盖范围：security_bar_1d 最小合法行
    测试对象：run_b2_validate_table（baostock 绑定）
    目的/目标：clean 表有合法行情行时 B2 应 PASSED
    验证点：status==PASSED；staging_table==security_bar_1d
    失败含义：合法 clean 数据仍被 B2 拒绝，阻断验收主路径
    """
    from backend.app.ops.tier_a_live_acceptance import ensure_isolated_db

    binding = source_bindings()["baostock"]
    db_path = ensure_isolated_db(isolated_live_data_root)
    cm = ConnectionManager(db_path=db_path)
    with cm.writer() as con:
        con.execute(
            """
            INSERT INTO security_bar_1d (
                instrument_id, trade_date, open, high, low, close, pre_close,
                volume, amount, adjustment_type, source_used, batch_id
            ) VALUES (
                'sh.600000', DATE '2026-06-15', 10.0, 11.0, 9.5, 10.5, 10.0,
                1000.0, 10500.0, 'none', 'baostock', 'b2-test'
            )
            """
        )

    status, detail = run_b2_validate_table(
        "baostock",
        binding=binding,
        db_path=db_path,
        run_id="run-b2-bar",
        job_id="job-b2-bar",
    )
    assert status == "PASSED"
    assert "PASSED" in detail


def test_reportRun_setsB2ValidationStatusForElevenSources(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """覆盖范围：--report 全量 11 源 B2 状态
    测试对象：run_acceptance_report per-source b2_validation_status
    目的/目标：acceptance report 接线 validate_table，禁止 pending
    验证点：11 行 b2_validation_status ∈ {PASSED,WARNING,FAILED}；manifest 同步
    失败含义：验收报告仍旁路 B2 或 manifest 与 report 不一致
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setenv("FRED_API_KEY", "a" * 32)
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "b" * 16)
    monkeypatch.setenv("SEC_EDGAR_USER_AGENT", "contract-test@example.com")

    def _mock_incremental(source_id: str, _data_root: Path) -> LiveIncrementalOutcome:
        return _mock_outcome(source_id)

    monkeypatch.setattr(
        "backend.app.ops.tier_a_live_acceptance.run_tier_a_live_incremental",
        _mock_incremental,
    )

    report_path = tmp_path / "tier-a-b2-report.json"
    exit_code = run_acceptance_report(
        report_path,
        data_root=isolated_live_data_root,
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    allowed = {"PASSED", "WARNING", "FAILED"}
    for row in report["sources"]:
        assert row["b2_validation_status"] in allowed, row["source_id"]
        manifest_path = isolated_live_data_root / row["evidence_manifest_path"]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["acceptance"]["b2_validation_status"] == row["b2_validation_status"]
    assert len(report["sources"]) == 11
