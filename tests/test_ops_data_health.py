"""Tests for read-only ops data health (C-20)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from backend.app.ops.data_health import (
    DataHealthCheckResult,
    DataHealthLoadError,
    DataHealthService,
    build_report,
    check_daily_bars,
    check_lineage_entry,
    check_metadata_rows,
    check_result_from_dict,
    check_result_to_dict,
    check_staleness,
    load_evidence_bundle,
    require_evidence_bundle,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_FIXTURES = _PROJECT_ROOT / "tests" / "fixtures" / "data_health"
_V2_EVIDENCE = _FIXTURES / "v2_integration_bundle"

_GOOD_BUNDLE = _FIXTURES / "good_bundle"
_BAD_BAR_BUNDLE = _FIXTURES / "bad_bar_bundle"
_GOOD_BAR = {
    "symbol": "sh.600519",
    "trade_date": "2024-01-02",
    "open": 1,
    "high": 2,
    "low": 1,
    "close": 2,
    "volume": 1,
}


def _run_data_health_cli(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "backend.app.ops.data_health_cli", *args]
    return subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=_PROJECT_ROOT)


def test_dataHealthModel_roundtrip_success() -> None:
    """覆盖范围：DataHealth 模型字段 roundtrip
    测试对象：backend/app/ops/data_health.py
    目的/目标：证明 severity/rule_id 与 contract 对齐可序列化
    验证点：model roundtrip 后字段一致
    失败含义：报告无法机器可读，gate 输入失效
    """
    original = DataHealthCheckResult(
        rule_id="INVALID_OHLC",
        severity="FAIL",
        status="FAIL",
        source_id="baostock",
        domain="cn_equity_daily_bar",
        evidence_path="foo.json",
        row_count=10,
        message="bad ohlc",
    )
    roundtrip = check_result_from_dict(check_result_to_dict(original))
    assert roundtrip == original


def test_dataHealthLoader_missingManifest_fails(tmp_path: Path) -> None:
    """覆盖范围：manifest loader 缺文件失败路径
    测试对象：data_health manifest loader
    目的/目标：缺 evidence 时必须 FAIL 而非空 PASS
    验证点：raises 或 overall_status FAIL
    失败含义：坏 evidence 被当成健康
    """
    bundle = load_evidence_bundle(tmp_path)
    assert bundle.load_error is not None
    report = DataHealthService().check_evidence_dir(tmp_path)
    assert report.overall_status == "FAIL"

    with pytest.raises(DataHealthLoadError):
        require_evidence_bundle(tmp_path)


def test_dataHealthDailyBar_invalidOhlc_fails() -> None:
    """覆盖范围：日 K OHLC 坏数据
    测试对象：daily bar health rules
    目的/目标：INVALID_OHLC 可被检出
    验证点：checks 含 INVALID_OHLC 且 status FAIL
    失败含义：价量坏数据进入下游
    """
    bars = [
        {
            "symbol": "sh.600519",
            "trade_date": "2024-01-02",
            "open": 10,
            "high": 5,
            "low": 8,
            "close": 9,
            "volume": 100,
        },
        {
            "symbol": "sh.600519",
            "trade_date": "2024-01-03",
            "open": 9,
            "high": 11,
            "low": 8,
            "close": 10,
            "volume": 50,
        },
    ]
    checks = check_daily_bars(bars)
    assert any(c.rule_id == "INVALID_OHLC" and c.status == "FAIL" for c in checks)


def test_dataHealthDailyBar_duplicateKey_fails() -> None:
    """覆盖范围：日 K 主键重复
    测试对象：daily bar duplicate key rule
    目的/目标：DUPLICATE_PRIMARY_KEY 可被检出
    验证点：checks 含 DUPLICATE_PRIMARY_KEY 且 status FAIL
    失败含义：重复 bar 不可见
    """
    bars = [_GOOD_BAR, dict(_GOOD_BAR)]
    checks = check_daily_bars(bars, min_history=1)
    assert any(c.rule_id == "DUPLICATE_PRIMARY_KEY" and c.status == "FAIL" for c in checks)


def test_dataHealthDailyBar_negativeVolume_fails() -> None:
    """覆盖范围：日 K 负成交量
    测试对象：daily bar volume rule
    目的/目标：NEGATIVE_VOLUME 可被检出
    验证点：checks 含 NEGATIVE_VOLUME 且 status FAIL
    失败含义：非法成交量通过检查
    """
    bars = [dict(_GOOD_BAR, volume=-1), dict(_GOOD_BAR, trade_date="2024-01-03")]
    checks = check_daily_bars(bars)
    assert any(c.rule_id == "NEGATIVE_VOLUME" and c.status == "FAIL" for c in checks)


def test_dataHealthDailyBar_insufficientHistory_fails() -> None:
    """覆盖范围：日 K 历史不足
    测试对象：daily bar history window rule
    目的/目标：INSUFFICIENT_HISTORY 可被检出
    验证点：checks 含 INSUFFICIENT_HISTORY 且 status FAIL
    失败含义：窗口不足不可见
    """
    bars = [_GOOD_BAR]
    checks = check_daily_bars(bars, min_history=2)
    assert any(c.rule_id == "INSUFFICIENT_HISTORY" and c.status == "FAIL" for c in checks)


def test_dataHealthMetadata_emptyTitle_fails() -> None:
    """覆盖范围：cninfo metadata 空标题
    测试对象：metadata health rules
    目的/目标：MISSING_REQUIRED_FIELD 可检出
    验证点：rule_id 与 FAIL status
    失败含义：元数据缺口不可见
    """
    checks = check_metadata_rows([{"title": "", "announcement_date": "2024-01-01"}])
    assert any(c.rule_id == "MISSING_REQUIRED_FIELD" and c.status == "FAIL" for c in checks)


def test_dataHealthLineage_missingContentHash_fails() -> None:
    """覆盖范围：lineage 缺 content_hash
    测试对象：source lineage health
    目的/目标：MISSING_CONTENT_HASH 可检出
    验证点：lineage check FAIL
    失败含义：血缘不可审计
    """
    checks = check_lineage_entry(
        {
            "source_used": "baostock",
            "source_fetch_id": "fetch-1",
            "as_of_timestamp": "2026-06-01T00:00:00Z",
        },
        domain="cn_equity_daily_bar",
    )
    assert any(c.rule_id == "MISSING_CONTENT_HASH" and c.status == "FAIL" for c in checks)


def test_dataHealthLineage_missingSourceUsed_fails() -> None:
    """覆盖范围：lineage 缺 source_used
    测试对象：source lineage health
    目的/目标：MISSING_SOURCE_USED 可检出
    验证点：checks 含 MISSING_SOURCE_USED 且 FAIL
    失败含义：来源不可追溯
    """
    checks = check_lineage_entry(
        {
            "source_fetch_id": "fetch-1",
            "content_hash": "abc",
            "as_of_timestamp": "2026-06-01T00:00:00Z",
        },
        domain="cn_equity_daily_bar",
    )
    assert any(c.rule_id == "MISSING_SOURCE_USED" and c.status == "FAIL" for c in checks)


def test_dataHealthLineage_missingFetchId_fails() -> None:
    """覆盖范围：lineage 缺 source_fetch_id
    测试对象：source lineage health
    目的/目标：MISSING_SOURCE_FETCH_ID 可检出
    验证点：checks 含 MISSING_SOURCE_FETCH_ID 且 FAIL
    失败含义：fetch 批次不可追溯
    """
    checks = check_lineage_entry(
        {
            "source_used": "baostock",
            "content_hash": "abc",
            "as_of_timestamp": "2026-06-01T00:00:00Z",
        },
        domain="cn_equity_daily_bar",
    )
    assert any(c.rule_id == "MISSING_SOURCE_FETCH_ID" and c.status == "FAIL" for c in checks)


def test_dataHealthLineage_missingAsOf_fails() -> None:
    """覆盖范围：lineage 缺 as_of_timestamp
    测试对象：source lineage health
    目的/目标：MISSING_AS_OF_TIMESTAMP 可检出
    验证点：checks 含 MISSING_AS_OF_TIMESTAMP 且 FAIL
    失败含义：时点不可审计
    """
    checks = check_lineage_entry(
        {
            "source_used": "baostock",
            "source_fetch_id": "fetch-1",
            "content_hash": "abc",
        },
        domain="cn_equity_daily_bar",
    )
    assert any(c.rule_id == "MISSING_AS_OF_TIMESTAMP" and c.status == "FAIL" for c in checks)


def test_dataHealthLineage_validationOnlyMisuse_fails() -> None:
    """覆盖范围：validation-only 误作 primary
    测试对象：source route misuse rule
    目的/目标：VALIDATION_ONLY_AS_PRIMARY 可检出
    验证点：checks 含 VALIDATION_ONLY_AS_PRIMARY 且 FAIL
    失败含义：validation-only 误晋升
    """
    checks = check_lineage_entry(
        {
            "source_used": "akshare",
            "source_fetch_id": "fetch-1",
            "content_hash": "abc",
            "as_of_timestamp": "2026-06-01T00:00:00Z",
        },
        domain="cn_equity_daily_bar",
        primary_source_id="akshare",
    )
    assert any(
        c.rule_id == "VALIDATION_ONLY_AS_PRIMARY" and c.status == "FAIL" for c in checks
    )


def test_dataHealthLineage_disabledSource_fails() -> None:
    """覆盖范围：disabled source 被使用
    测试对象：source registry misuse rule
    目的/目标：DISABLED_SOURCE_USED 可检出
    验证点：checks 含 DISABLED_SOURCE_USED 且 FAIL
    失败含义：禁用源被当作有效输入
    """
    checks = check_lineage_entry(
        {
            "source_used": "qmt_xtdata",
            "source_fetch_id": "fetch-1",
            "content_hash": "abc",
            "as_of_timestamp": "2026-06-01T00:00:00Z",
        },
        domain="cn_equity_daily_bar",
        primary_source_id="qmt_xtdata",
    )
    assert any(c.rule_id == "DISABLED_SOURCE_USED" and c.status == "FAIL" for c in checks)


def test_dataHealthLineage_unknownSource_fails() -> None:
    """覆盖范围：registry 外 source_id
    测试对象：check_lineage_entry registry fail-closed
    目的/目标：未知源不得静默跳过 DISABLED_SOURCE_USED 语义检查
    验证点：checks 含 not found in registry 且 FAIL
    失败含义：对抗性 manifest 可绕过 registry 门禁
    """
    checks = check_lineage_entry(
        {
            "source_used": "totally_fake_source",
            "source_fetch_id": "fetch-1",
            "content_hash": "abc",
            "as_of_timestamp": "2026-06-01T00:00:00Z",
        },
        domain="cn_equity_daily_bar",
        primary_source_id="totally_fake_source",
    )
    assert any(
        c.rule_id == "DISABLED_SOURCE_USED"
        and c.status == "FAIL"
        and "not found in registry" in c.message
        for c in checks
    )


def test_dataHealthLineage_v2ManifestEntry_passes() -> None:
    """覆盖范围：v2 manifest_entries 无顶层 source_used
    测试对象：check_lineage_entry v2 字段回退
    目的/目标：staged_pilot v2 条目不得假 FAIL MISSING_SOURCE_USED
    验证点：request.source_id + as_of_timestamp 回退后无 lineage FAIL
    失败含义：canonical v2 evidence 被误判不健康
    """
    entry = {
        "source_fetch_id": "fetch-baostock",
        "content_hash": "evidence-hash",
        "as_of_timestamp": "2026-06-23T18:11:44Z",
        "request": {"source_id": "baostock", "data_domain": "cn_equity_daily_bar"},
    }
    checks = check_lineage_entry(
        entry,
        domain="cn_equity_daily_bar",
        primary_source_id="baostock",
    )
    lineage_fail = {
        c.rule_id
        for c in checks
        if c.status == "FAIL" and c.rule_id.startswith("MISSING_")
    }
    assert not lineage_fail


def test_dataHealthStaleness_staleData_warns() -> None:
    """覆盖范围：陈旧数据窗口
    测试对象：staleness/window health
    目的/目标：STALE_DATA 对齐契约 severity WARN
    验证点：staleness check status WARN
    失败含义：warning 级规则抬升 overall_status 为 FAIL
    """
    checks = check_staleness(
        rows=[{"symbol": "sh.600519"}],
        as_of_timestamp="2020-01-01T00:00:00Z",
    )
    assert any(c.rule_id == "STALE_DATA" and c.status == "WARN" for c in checks)


def test_dataHealthStaleness_emptyResponse_fails() -> None:
    """覆盖范围：空响应/无行数据
    测试对象：staleness/window health
    目的/目标：EMPTY_RESPONSE 可检出
    验证点：checks 含 EMPTY_RESPONSE 且 FAIL
    失败含义：空数据被当成健康
    """
    checks = check_staleness(rows=[], domain="cn_equity_daily_bar")
    assert any(c.rule_id == "EMPTY_RESPONSE" and c.status == "FAIL" for c in checks)


def test_dataHealthReport_jsonAndText_success() -> None:
    """覆盖范围：报告 JSON + 文本双输出
    测试对象：report builder
    目的/目标：JSON 与 text summary 字段齐全
    验证点：overall_status、checks、production_db_mutated false
    失败含义：运营无法读报告
    """
    checks = [
        DataHealthCheckResult(
            rule_id="INVALID_OHLC",
            severity="INFO",
            status="PASS",
            source_id="baostock",
            domain="cn_equity_daily_bar",
            evidence_path=None,
            row_count=2,
            message="ok",
        )
    ]
    report = build_report(checks, profile="cn_equity_daily_bar", gate_rationale="test gate")
    payload = report.to_dict()
    assert payload["overall_status"] == "PASS"
    assert payload["production_db_mutated"] is False
    assert payload["source_fetch_performed"] is False
    assert payload["checks"]
    assert report.text_summary
    assert "overall" in report.text_summary.lower() or "Overall" in report.text_summary


def test_dataHealthCli_readOnly_exitZero() -> None:
    """覆盖范围：CLI 只读入口
    测试对象：data_health_cli
    目的/目标：只读 CLI 可退出 0 且不写 DB
    验证点：exit code 0；无 fetch
    失败含义：无 operable 入口
    """
    result = _run_data_health_cli("--evidence", str(_GOOD_BUNDLE), "--format", "json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["production_db_mutated"] is False
    assert payload["source_fetch_performed"] is False


def test_dataHealthCli_badEvidence_exitNonZero(tmp_path: Path) -> None:
    """覆盖范围：CLI 坏 evidence 退出码
    测试对象：data_health_cli fail-closed
    目的/目标：缺 manifest 时 CLI 非零退出
    验证点：returncode == 2
    失败含义：坏 evidence 被当成可操作成功
    """
    empty = tmp_path / "empty_evidence"
    empty.mkdir()
    result = _run_data_health_cli("--evidence", str(empty))
    assert result.returncode == 2


def test_dataHealthCli_pathOutsideProject_rejected(tmp_path: Path) -> None:
    """覆盖范围：CLI evidence 路径 sandbox
    测试对象：data_health_cli project-relative guard
    目的/目标：越界 evidence 目录被拒绝
    验证点：returncode == 2
    失败含义：可读取项目外 staged manifest
    """
    outside = tmp_path / "outside"
    outside.mkdir()
    result = _run_data_health_cli("--evidence", str(outside))
    assert result.returncode == 2


def test_dataHealthIntegration_badBarBundle_fails() -> None:
    """覆盖范围：service 路径坏 bar bundle
    测试对象：DataHealthService + committed bad_bar_bundle fixture
    目的/目标：集成路径须执行日 K 规则并 FAIL
    验证点：overall_status FAIL 且含 INVALID_OHLC
    失败含义：坏 bar 仅单测可见、service 路径放行
    """
    report = DataHealthService().check_evidence_dir(_BAD_BAR_BUNDLE)
    assert report.overall_status == "FAIL"
    assert any(c.rule_id == "INVALID_OHLC" and c.status == "FAIL" for c in report.checks)


def test_dataHealthIntegration_v2Evidence_bundle() -> None:
    """覆盖范围：v2 staged pilot evidence 集成
    测试对象：DataHealthService 对 archive evidence 目录
    目的/目标：canonical v2 evidence 不得假 FAIL；须跑日 K 规则
    验证点：overall_status PASS/WARN；无 MISSING_SOURCE_USED；日 K 规则曾运行
    失败含义：v2 假 FAIL 或集成路径仍是 manifest 半壳
    """
    assert _V2_EVIDENCE.is_dir(), f"missing v2 evidence root: {_V2_EVIDENCE}"
    report = DataHealthService().check_evidence_dir(_V2_EVIDENCE)
    assert report.overall_status in {"PASS", "WARN"}
    assert not any(c.rule_id == "MISSING_SOURCE_USED" for c in report.checks)
    assert any(
        c.rule_id in {"INVALID_OHLC", "INSUFFICIENT_HISTORY", "EMPTY_RESPONSE"}
        for c in report.checks
    )
    assert isinstance(report.sandbox_clean_write_gate_ready, bool)
    assert report.gate_rationale


def test_dataHealthCli_profileUnknown_exit2() -> None:
    """覆盖范围：CLI 未知 profile
    测试对象：data_health_cli --profile 路由
    目的/目标：未知 profile 须 exit 2
    验证点：returncode == 2
    失败含义：未知 profile 被静默当成 v1 bundle
    """
    result = _run_data_health_cli(
        "--evidence",
        str(_GOOD_BUNDLE),
        "--profile",
        "not_a_real_profile",
    )
    assert result.returncode == 2


def test_dataHealthCli_profileFred_routes() -> None:
    """覆盖范围：CLI v2 profile 路由
    测试对象：data_health_cli --profile fred_sandbox_pilot
    目的/目标：--profile 路由到 v2 checker；默认仍 v1 bundle
    验证点：FRED complete fixture exit 0；JSON profile 字段正确
    失败含义：CLI 未暴露 v2 profile
    """
    fred_dir = _FIXTURES / "fred_sandbox" / "complete"
    result = _run_data_health_cli(
        "--evidence",
        str(fred_dir),
        "--profile",
        "fred_sandbox_pilot",
        "--format",
        "json",
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["profile"] == "fred_sandbox_pilot"
    assert payload["overall_status"] == "PASS"


def test_opsDataHealth_dh2Path_noSnapshotDdl() -> None:
    """覆盖范围：DH2 只读路径不得建 source_health_snapshot 表
    测试对象：backend.app.ops.data_health 只读 profile 路径
    目的/目标：VR-DATAHEALTH-001 — Batch01/DH2 禁止 CREATE snapshot 表
    验证点：data_health 模块无 snapshot DDL / writer 默认接线
    失败含义：DH2 路径误建表，违反 Batch 3F 边界
    """
    import backend.app.ops.data_health as dh

    source = Path(dh.__file__).read_text(encoding="utf-8")
    assert dh.DH2_FORBIDS_SNAPSHOT_DDL is True
    assert "source_health_writer" not in source
    assert "CREATE TABLE" not in source or "source_health_snapshot" not in source
