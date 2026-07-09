"""Phase 1 qmd-data acceptance envelope tests (task-02 T2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.cli.phase1_acceptance import (
    REPORT_VERSION,
    build_acceptance_envelope,
    compute_gate_eligible,
    dry_run_envelope_for_plan,
    is_production_equivalent_acceptance_root,
    merge_payload_with_envelope,
    require_phase1_data_root_for_live,
)
from backend.app.cli.errors import CliFailure, DOCS_ANCHOR_LIVE_ENV_GATE
from backend.app.ops.source_route_db_acceptance import AcceptanceReport, AcceptanceRequest


def _acceptance_root(tmp_path: Path) -> Path:
    root = tmp_path / ".audit-sandbox" / "source-route-db-envelope"
    root.mkdir(parents=True)
    return root


def test_phase1Acceptance_gateEligible_onlyForSourceRouteDbLive(tmp_path: Path) -> None:
    """覆盖范围：gate_eligible 判定规则
    测试对象：compute_gate_eligible / is_production_equivalent_acceptance_root
    目的/目标：仅 official live + source-route-db root 可为 gate-eligible
    验证点：dry-run 与普通 sandbox 为 False；source-route-db live 为 True
    失败含义：旧 sandbox 或 dry-run 被误计为 P1-GATE 通过
    """
    generic = tmp_path / ".audit-sandbox" / "wave3-accept" / "data"
    generic.mkdir(parents=True)
    p1_root = _acceptance_root(tmp_path)
    assert is_production_equivalent_acceptance_root(p1_root) is True
    assert is_production_equivalent_acceptance_root(generic) is False
    assert compute_gate_eligible(job_kind="sync", data_root=p1_root, dry_run=False) is True
    assert compute_gate_eligible(job_kind="sync", data_root=p1_root, dry_run=True) is False
    assert compute_gate_eligible(job_kind="sync", data_root=generic, dry_run=False) is False


def test_phase1Acceptance_requireLiveRoot_rejectsGenericSandbox(tmp_path: Path) -> None:
    """覆盖范围：live 验收 data root 强制规则
    测试对象：require_phase1_data_root_for_live
    目的/目标：非 source-route-db 的 live 路径必须 fail-closed
    验证点：普通 .audit-sandbox 抛 CliFailure 且 error_code=ISOLATED_ROOT_REQUIRED
    失败含义：live 验收可在非生产等价 root 运行并污染关账证据
    """
    generic = tmp_path / ".audit-sandbox" / "wave3" / "data"
    generic.mkdir(parents=True)
    with pytest.raises(CliFailure) as exc:
        require_phase1_data_root_for_live(generic)
    assert exc.value.error_code == "ISOLATED_ROOT_REQUIRED"
    assert exc.value.docs_anchor == DOCS_ANCHOR_LIVE_ENV_GATE


def test_phase1Acceptance_envelope_includesRequiredFields(tmp_path: Path) -> None:
    """覆盖范围：统一 AcceptanceReport 信封字段
    测试对象：build_acceptance_envelope
    目的/目标：CLI 输出必须携带契约要求的 gate、证据与链路状态字段
    验证点：含 report_version、gate_eligible、observability_evidence、route_status
    失败含义：正式命令仍只有 console 文本，审计无法结构化复核
    """
    request = AcceptanceRequest.from_target("macro_series:fred:fetch_macro_series")
    report = AcceptanceReport.not_implemented(request)
    root = _acceptance_root(tmp_path)
    envelope = build_acceptance_envelope(
        report,
        job_kind="sync",
        trigger="test",
        data_root=root,
        dry_run=True,
    )
    assert envelope["report_version"] == REPORT_VERSION
    assert envelope["gate_eligible"] is False
    assert "acceptance_report" in envelope
    assert "observability_evidence" in envelope
    assert "route_status" in envelope
    assert envelope["job_kind"] == "sync"


def test_phase1Acceptance_dryRunEnvelope_marksNonGate(tmp_path: Path) -> None:
    """覆盖范围：dry-run 计划信封
    测试对象：dry_run_envelope_for_plan
    目的/目标：dry-run 须显式 gate_eligible=false 且 implementation_mode=dry_run
    验证点：status=DRY_RUN；gate_eligible=False
    失败含义：dry-run 计划被误认为 live 验收完成
    """
    root = _acceptance_root(tmp_path)
    envelope = dry_run_envelope_for_plan(
        job_kind="backfill",
        trigger="test",
        data_root=root,
        source_id="fred",
        data_domain="macro_series",
    )
    assert envelope["gate_eligible"] is False
    assert envelope["status"] == "DRY_RUN"
    assert envelope["implementation_mode"] == "dry_run"


def test_phase1Acceptance_mergePayload_preservesCommandFields(tmp_path: Path) -> None:
    """覆盖范围：信封与既有 CLI payload 合并
    测试对象：merge_payload_with_envelope
    目的/目标：additive 扩展不得丢失 command/dry_run 等既有字段
    验证点：合并后 command 保留且 gate_eligible 注入
    失败含义：接入验收信封破坏现有 CLI 消费者
    """
    request = AcceptanceRequest.from_target("macro_series:fred:fetch_macro_series")
    report = AcceptanceReport.not_implemented(request)
    envelope = build_acceptance_envelope(
        report,
        job_kind="sync",
        trigger="test",
        data_root=_acceptance_root(tmp_path),
        dry_run=True,
    )
    merged = merge_payload_with_envelope({"command": "sync", "dry_run": True}, envelope)
    assert merged["command"] == "sync"
    assert merged["dry_run"] is True
    assert merged["gate_eligible"] is False


def test_phase1Acceptance_observabilityEvidence_routeFetchPath(tmp_path: Path) -> None:
    """覆盖范围：T15 route/fetch/raw 证据路径
    测试对象：build_acceptance_envelope observability_evidence
    目的/目标：成功/计划行须可追到 route_plan 持久化与 pipeline 路径
    验证点：route_plan_persistence=job_event_log；incremental_evidence.pipeline_path 非空
    失败含义：official report 无法证明 fetch 前已生成 route plan
    """
    from backend.app.cli.phase1_acceptance import PRODUCTION_PIPELINE_PATH, build_incremental_evidence

    request = AcceptanceRequest.from_target("macro_series:fred:fetch_macro_series")
    report = AcceptanceReport.from_route_payload(
        request,
        {
            "route_status": "READY",
            "selected_source_id": "fred",
            "route_plan_id": "rp-test-1",
            "route_grade": "primary",
        },
    )
    root = _acceptance_root(tmp_path)
    envelope = build_acceptance_envelope(
        report,
        job_kind="sync",
        trigger="test",
        data_root=root,
        dry_run=False,
        extra={
            "incremental_evidence": build_incremental_evidence(watermark_before="2024-01-01"),
            "staging_table": "stg_macro_series",
            "raw_file_paths": ["/tmp/raw.json"],
        },
    )
    obs = envelope["observability_evidence"]
    assert obs["route_plan_persistence"] == "job_event_log"
    assert obs["route_plan_id"] == "rp-test-1"
    assert envelope["incremental_evidence"]["pipeline_path"] == PRODUCTION_PIPELINE_PATH
    assert obs["staging_table"] == "stg_macro_series"
    assert obs["raw_file_paths"] == ["/tmp/raw.json"]


def test_phase1Acceptance_chainStatus_blocksWriteOnValidationFailure(tmp_path: Path) -> None:
    """覆盖范围：T16 validation 阻断写 clean
    测试对象：build_acceptance_envelope 链路状态字段
    目的/目标：validation_status=FAILED 时 write_status/clean_status 不得为 COMMITTED/WRITTEN
    验证点：write_status=NOT_RUN；clean_status=NOT_RUN
    失败含义：质量失败仍显示 clean 已写入，误导 primary-grade 合格
    """
    from dataclasses import replace

    request = AcceptanceRequest.from_target("cn_equity_daily_bar:baostock:fetch_daily_bar")
    base = AcceptanceReport.from_route_payload(
        request,
        {
            "route_status": "READY",
            "selected_source_id": "baostock",
            "route_plan_id": "rp-val-fail",
            "route_grade": "primary",
        },
    )
    report = replace(
        base,
        status="FAIL",
        failure_class="FAIL",
        validation_status="FAILED",
        write_grade="not_written",
    )
    envelope = build_acceptance_envelope(
        report,
        job_kind="sync",
        trigger="test",
        data_root=_acceptance_root(tmp_path),
        dry_run=False,
    )
    assert envelope["validation_status"] == "FAILED"
    assert envelope["write_status"] == "NOT_RUN"
    assert envelope["clean_status"] == "NOT_RUN"


def test_phase1Acceptance_chainStatus_withoutFetchEvidence_marksRawAndFetchFail(
    tmp_path: Path,
) -> None:
    """覆盖范围：R4 链路状态诚实性（无 fetch 证据）
    测试对象：build_acceptance_envelope 链路状态字段
    目的/目标：仅有 write_grade 成功、observability 无 fetch/raw 证据时不得标 fetch/raw=PRESENT
    验证点：fetch_status=FAIL；raw_status=FAIL；clean_status 仍可为 WRITTEN
    失败含义：验收信封假绿，审计无法区分「已写 clean」与「已证明 fetch/raw 证据」
    """
    from dataclasses import replace

    request = AcceptanceRequest.from_target("cn_equity_daily_bar:baostock:fetch_daily_bar")
    base = AcceptanceReport.from_route_payload(
        request,
        {
            "route_status": "READY",
            "selected_source_id": "baostock",
            "route_plan_id": "rp-no-evidence",
            "route_grade": "primary",
        },
    )
    report = replace(
        base,
        status="PASS",
        failure_class="NONE",
        write_grade="primary_grade_clean",
        validation_status="PASSED_PRIMARY",
    )
    envelope = build_acceptance_envelope(
        report,
        job_kind="sync",
        trigger="test",
        data_root=_acceptance_root(tmp_path),
        dry_run=False,
        extra={},
    )
    assert envelope["fetch_status"] == "FAIL"
    assert envelope["raw_status"] == "FAIL"
    assert envelope["clean_status"] == "WRITTEN"


def test_phase1Acceptance_degradedWriteGrade_preservedInEnvelope(tmp_path: Path) -> None:
    """覆盖范围：T17 degraded clean 语义保留
    测试对象：build_acceptance_envelope write_grade / source_role
    目的/目标：degraded_clean 须在 report 与 observability 中可见，供下游读取识别
    验证点：write_grade=degraded_clean；source_switched=True；observability write_grade 一致
    失败含义：fallback/degraded 写入被伪装成 primary-grade
    """
    from dataclasses import replace

    request = AcceptanceRequest.from_target("macro_series:fred:fetch_macro_series")
    base = AcceptanceReport.from_route_payload(
        request,
        {
            "route_status": "READY",
            "selected_source_id": "fred",
            "route_plan_id": "rp-deg",
            "route_grade": "degraded",
        },
    )
    report = replace(
        base,
        status="PASS",
        failure_class="NONE",
        write_grade="degraded_clean",
        source_role="fallback",
        source_switched=True,
        downstream_layer_read_status="DEGRADED_READ",
    )
    envelope = build_acceptance_envelope(
        report,
        job_kind="sync",
        trigger="test",
        data_root=_acceptance_root(tmp_path),
        dry_run=False,
    )
    assert envelope["write_grade"] == "degraded_clean"
    assert envelope["source_switched"] is True
    assert envelope["observability_evidence"]["write_grade"] == "degraded_clean"
    assert envelope["downstream_layer_read_status"] == "DEGRADED_READ"
