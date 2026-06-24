"""Tests for read-only data health v2 profiles (B01-DH2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.ops import data_health as data_health_mod
from backend.app.ops.data_health import DataHealthService

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_FIXTURES = _PROJECT_ROOT / "tests" / "fixtures" / "data_health"
_SERVICE = DataHealthService()


def test_dataHealthV2_whitelist_fixture_pass() -> None:
    """覆盖范围：whitelist fixture PASS 路径
    测试对象：model_input_whitelist profile + B01-WL fixture YAML
    目的/目标：evidence 目录含 whitelist fixture 时须 PASS 而非 BLOCKED
    验证点：overall_status PASS；含 MODEL_INPUT_WHITELIST
    失败含义：合法 fixture 被当成缺 SSOT
    """
    evidence = _FIXTURES / "whitelist"
    report = _SERVICE.check_evidence_dir(
        evidence, profile="model_input_whitelist"
    )
    assert report.overall_status == "PASS"
    assert any(
        c.rule_id == "MODEL_INPUT_WHITELIST" and c.status == "PASS"
        for c in report.checks
    )


def test_dataHealthV2_whitelist_missing_blocked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：whitelist profile 缺 SSOT
    测试对象：model_input_whitelist profile
    目的/目标：specs/model_inputs 未合并时须 BLOCKED 而非静默 PASS
    验证点：overall_status == BLOCKED；含 MODEL_INPUT_WHITELIST_MISSING
    失败含义：缺 WL 却放行或猜 scope
    """
    monkeypatch.setattr(
        data_health_mod, "_model_inputs_whitelist_available", lambda: False
    )
    evidence = _FIXTURES / "fred_sandbox" / "complete"
    report = _SERVICE.check_evidence_dir(
        evidence, profile="model_input_whitelist"
    )
    assert report.overall_status == "BLOCKED"
    assert any(
        c.rule_id == "MODEL_INPUT_WHITELIST_MISSING" and c.status == "BLOCKED"
        for c in report.checks
    )
    assert not report.sandbox_clean_write_gate_ready


def test_dataHealthV2_fred_missingAsOf_fails() -> None:
    """覆盖范围：FRED profile 缺 as_of
    测试对象：fred_sandbox_pilot profile
    目的/目标：缺 as_of_timestamp 须 FAIL
    验证点：overall_status FAIL；含 MISSING_AS_OF_TIMESTAMP
    失败含义：FRED lineage 半壳被当成可操作
    """
    evidence = _FIXTURES / "fred_sandbox" / "missing_as_of"
    report = _SERVICE.check_evidence_dir(evidence, profile="fred_sandbox_pilot")
    assert report.overall_status == "FAIL"
    assert any(
        c.rule_id == "MISSING_AS_OF_TIMESTAMP" and c.status == "FAIL"
        for c in report.checks
    )


def test_dataHealthV2_fred_macroSupplementary_noPrimaryClose() -> None:
    """覆盖范围：FRED macro_supplementary 边界
    测试对象：fred_sandbox_pilot profile
    目的/目标：macro_supplementary 不得关闭 FRED primary readiness
    验证点：含 FRED_PRIMARY_NOT_CLOSED；无 FRED primary PASS 关闭语义
    失败含义：macro 替代 FRED primary
    """
    evidence = _FIXTURES / "fred_sandbox" / "macro_supplementary"
    report = _SERVICE.check_evidence_dir(evidence, profile="fred_sandbox_pilot")
    assert any(
        c.rule_id == "FRED_PRIMARY_NOT_CLOSED" and c.status == "WARN"
        for c in report.checks
    )
    assert not any(
        c.rule_id == "FRED_SANDBOX_EVIDENCE" and c.status == "PASS"
        for c in report.checks
    )


def test_dataHealthV2_tdx_missingAuth_fails() -> None:
    """覆盖范围：TDX 无授权
    测试对象：tdx_manual_probe profile
    目的/目标：无授权声明须 FAIL/BLOCKED
    验证点：overall_status FAIL；含 MISSING_AUTHORIZATION
    失败含义：未授权 TDX probe 被放行
    """
    evidence = _FIXTURES / "tdx_probe" / "missing_auth"
    report = _SERVICE.check_evidence_dir(evidence, profile="tdx_manual_probe")
    assert report.overall_status == "FAIL"
    assert any(
        c.rule_id == "MISSING_AUTHORIZATION" and c.status == "FAIL"
        for c in report.checks
    )


def test_dataHealthV2_tdx_productionPrimary_fails() -> None:
    """覆盖范围：TDX production primary 禁止
    测试对象：tdx_manual_probe profile
    目的/目标：TDX 作 primary 须 FAIL
    验证点：overall_status FAIL；含 VALIDATION_ONLY_AS_PRIMARY
    失败含义：validation-only source 升格 primary
    """
    evidence = _FIXTURES / "tdx_probe" / "production_primary"
    report = _SERVICE.check_evidence_dir(evidence, profile="tdx_manual_probe")
    assert report.overall_status == "FAIL"
    assert any(
        c.rule_id == "VALIDATION_ONLY_AS_PRIMARY" and c.status == "FAIL"
        for c in report.checks
    )


def test_dataHealthV2_aksharePrimary_fails() -> None:
    """覆盖范围：v3 AkShare primary 禁止
    测试对象：staged_pilot_v3 profile
    目的/目标：AkShare 不得作 primary
    验证点：overall_status FAIL；含 VALIDATION_ONLY_AS_PRIMARY
    失败含义：AkShare 升格主源
    """
    evidence = _FIXTURES / "staged_pilot_v3" / "akshare_primary"
    report = _SERVICE.check_evidence_dir(evidence, profile="staged_pilot_v3")
    assert report.overall_status == "FAIL"
    assert any(
        c.rule_id == "VALIDATION_ONLY_AS_PRIMARY" and c.status == "FAIL"
        for c in report.checks
    )


def test_dataHealthV2_cninfoPdfBulk_failsMetadataOnly() -> None:
    """覆盖范围：v3 cninfo PDF bulk 禁止
    测试对象：staged_pilot_v3 profile
    目的/目标：metadata-only profile 禁止 PDF bulk
    验证点：overall_status FAIL；含 CNINFO_PDF_BULK_FORBIDDEN
    失败含义：bulk PDF 下载被 v3 放行
    """
    evidence = _FIXTURES / "staged_pilot_v3" / "cninfo_pdf_bulk"
    report = _SERVICE.check_evidence_dir(evidence, profile="staged_pilot_v3")
    assert report.overall_status == "FAIL"
    assert any(
        c.rule_id == "CNINFO_PDF_BULK_FORBIDDEN" and c.status == "FAIL"
        for c in report.checks
    )


def test_dataHealthV2_v3CapBreach_fails() -> None:
    """覆盖范围：v3 cap 违规
    测试对象：staged_pilot_v3 profile
    目的/目标：超 cap 须 FAIL
    验证点：overall_status FAIL；含 RESOURCE_CAP_BREACH
    失败含义：ResourceGuard cap 被绕过
    """
    evidence = _FIXTURES / "staged_pilot_v3" / "cap_breach"
    report = _SERVICE.check_evidence_dir(evidence, profile="staged_pilot_v3")
    assert report.overall_status == "FAIL"
    assert any(
        c.rule_id == "RESOURCE_CAP_BREACH" and c.status == "FAIL"
        for c in report.checks
    )


def test_dataHealthV2_rollup_outOfBounds_fails() -> None:
    """覆盖范围：rollup 子 evidence 路径 sandbox
    测试对象：source_readiness_rollup profile
    目的/目标：manifest profiles 含项目外相对路径须 FAIL
    验证点：overall_status FAIL；含 EVIDENCE_PATH_OUT_OF_BOUNDS
    失败含义：rollup 可读取 PROJECT_ROOT 外目录
    """
    evidence = _FIXTURES / "rollup" / "out_of_bounds"
    report = _SERVICE.check_evidence_dir(
        evidence, profile="source_readiness_rollup"
    )
    assert report.overall_status == "FAIL"
    assert any(
        c.rule_id == "EVIDENCE_PATH_OUT_OF_BOUNDS" and c.status == "FAIL"
        for c in report.checks
    )


def test_dataHealthV2_rollup_stagedOnly_warns() -> None:
    """覆盖范围：rollup staged-only 汇总
    测试对象：source_readiness_rollup profile
    目的/目标：staged-only 混合源须 WARN 汇总
    验证点：overall_status WARN；含 STAGED_ONLY_ROLLUP
    失败含义：staged-only 被宣传为 production-ready
    """
    evidence = _FIXTURES / "rollup" / "staged_only"
    report = _SERVICE.check_evidence_dir(
        evidence, profile="source_readiness_rollup"
    )
    assert report.overall_status == "WARN"
    assert any(
        c.rule_id == "STAGED_ONLY_ROLLUP" and c.status == "WARN"
        for c in report.checks
    )


def test_dataHealthV2_gate_requiresFullSafetyEvidence() -> None:
    """覆盖范围：rehearsal gate 安全证据
    测试对象：source_readiness_rollup gate
    目的/目标：缺 mutation/conflict proof 时 gate false；齐全时可 true
    验证点：incomplete gate false；complete gate true 且文案非空
    失败含义：半壳证据宣称 sandbox clean-write 可操作
    """
    incomplete = _FIXTURES / "rollup" / "gate_incomplete"
    incomplete_report = _SERVICE.check_evidence_dir(
        incomplete, profile="source_readiness_rollup"
    )
    assert incomplete_report.sandbox_clean_write_gate_ready is False
    assert "missing safety evidence" in incomplete_report.gate_rationale

    complete = _FIXTURES / "rollup" / "gate_complete"
    complete_report = _SERVICE.check_evidence_dir(
        complete, profile="source_readiness_rollup"
    )
    assert complete_report.sandbox_clean_write_gate_ready is True
    assert "rehearsal eligible" in complete_report.gate_rationale
