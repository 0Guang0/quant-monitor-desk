"""Tests for production-equivalent smoke budget artifact (R3F-HYG-06)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from backend.app.ops.perf_budget import (
    build_smoke_artifact,
    evaluate_smoke_metrics,
    load_smoke_budget,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUDGET_YAML = PROJECT_ROOT / "specs/contracts/production_equivalent_smoke_budget.yaml"


def test_loadSmokeBudget_readsThresholdContract() -> None:
    """覆盖范围：smoke 预算契约 YAML 是否可加载
    测试对象：load_smoke_budget
    目的/目标：R3F-HYG-06 阈值配置须为机器可读 SSOT
    验证点：thresholds.elapsed_s_max 存在且为正数
    失败含义：perf budget 契约缺失或格式损坏，smoke 无法做阈值门禁
    """
    doc = load_smoke_budget(BUDGET_YAML)
    assert doc["version"] == "v1"
    assert float(doc["thresholds"]["elapsed_s_max"]) > 0


def test_evaluateSmokeMetrics_passesWithinBudget() -> None:
    """覆盖范围：bounded smoke 指标在阈值内时 artifact status=PASS
    测试对象：evaluate_smoke_metrics
    目的/目标：Batch6 产出可审计的 performance-budget artifact
    验证点：status PASS；violations 为空；含 does_not_authorize_live_sources
    失败含义：正常 smoke 指标被误判 FAIL，CI nightly 误红
    """
    budget = load_smoke_budget(BUDGET_YAML)
    metrics = {
        "elapsed_s": 12.4,
        "pytest_steps": 5,
        "shard_count_benchmark": 3,
        "guard_status": "observable",
    }
    artifact = evaluate_smoke_metrics(metrics, budget=budget, use_service_path=True)
    assert artifact["status"] == "PASS"
    assert artifact["violations"] == []
    assert artifact["does_not_authorize_live_sources"] is True


def test_evaluateSmokeMetrics_failsWhenElapsedExceedsBudget() -> None:
    """覆盖范围：elapsed_s 超阈值时须 FAIL 闭包
    测试对象：evaluate_smoke_metrics
    目的/目标：performance budget 超线必须可检测（非仅打印 metrics）
    验证点：pytest.raises(ValueError) 且消息含 elapsed_s
    失败含义：smoke 变慢但门禁仍绿，A6 benchmark 失去意义
    """
    budget = load_smoke_budget(BUDGET_YAML)
    metrics = {
        "elapsed_s": float(budget["thresholds"]["elapsed_s_max"]) + 1.0,
        "pytest_steps": 5,
        "shard_count_benchmark": 3,
        "guard_status": "observable",
    }
    with pytest.raises(ValueError, match="elapsed_s"):
        evaluate_smoke_metrics(metrics, budget=budget, use_service_path=True)


def test_evaluateSmokeMetrics_failsWhenPytestStepsBelowMin() -> None:
    """覆盖范围：pytest_steps 低于阈值时须 FAIL 闭包
    测试对象：evaluate_smoke_metrics
    目的/目标：smoke 步数不足不可误判 PASS
    验证点：pytest.raises(ValueError) 且消息含 pytest_steps
    失败含义：未跑满 service-path 步骤仍产出绿 artifact
    """
    budget = load_smoke_budget(BUDGET_YAML)
    metrics = {
        "elapsed_s": 10.0,
        "pytest_steps": int(budget["thresholds"]["pytest_steps_min"]) - 1,
        "shard_count_benchmark": 3,
        "guard_status": "observable",
    }
    with pytest.raises(ValueError, match="pytest_steps"):
        evaluate_smoke_metrics(metrics, budget=budget, use_service_path=True)


def test_evaluateSmokeMetrics_failsWhenShardCountBelowMin() -> None:
    """覆盖范围：shard_count_benchmark 低于阈值时须 FAIL 闭包
    测试对象：evaluate_smoke_metrics
    目的/目标：backfill shard 规模门禁不可被跳过
    验证点：pytest.raises(ValueError) 且消息含 shard_count_benchmark
    失败含义：规模回归未触发 budget FAIL
    """
    budget = load_smoke_budget(BUDGET_YAML)
    metrics = {
        "elapsed_s": 10.0,
        "pytest_steps": 5,
        "shard_count_benchmark": int(budget["thresholds"]["shard_count_benchmark_min"]) - 1,
        "guard_status": "observable",
    }
    with pytest.raises(ValueError, match="shard_count_benchmark"):
        evaluate_smoke_metrics(metrics, budget=budget, use_service_path=True)


def test_evaluateSmokeMetrics_failsWhenGuardStatusMismatch() -> None:
    """覆盖范围：service-path 下 guard_status 不符时须 FAIL
    测试对象：evaluate_smoke_metrics
    目的/目标：ResourceGuard 未演练时不可 PASS
    验证点：pytest.raises(ValueError) 且消息含 guard_status
    失败含义：跳过 resource_guard pytest 仍产出 PASS artifact
    """
    budget = load_smoke_budget(BUDGET_YAML)
    metrics = {
        "elapsed_s": 10.0,
        "pytest_steps": 5,
        "shard_count_benchmark": 3,
        "guard_status": "not_exercised",
    }
    with pytest.raises(ValueError, match="guard_status"):
        evaluate_smoke_metrics(metrics, budget=budget, use_service_path=True)


def test_loadSmokeBudget_rejectsBadYaml(tmp_path: Path) -> None:
    """覆盖范围：损坏的 budget YAML 须 fail-closed
    测试对象：load_smoke_budget
    目的/目标：契约损坏时脚本/CI 不得静默使用空阈值
    验证点：缺失 thresholds 或非 dict 文档均 ValueError
    失败含义：坏 YAML 被当作 PASS，perf gate 失效
    """
    bad_path = tmp_path / "bad_budget.yaml"
    bad_path.write_text("not_a_mapping\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid smoke budget"):
        load_smoke_budget(bad_path)

    missing_thresholds = tmp_path / "no_thresholds.yaml"
    missing_thresholds.write_text("version: v1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing thresholds"):
        load_smoke_budget(missing_thresholds)


def test_buildSmokeArtifact_failStatusWritableWithoutRaise() -> None:
    """覆盖范围：超阈值时 build_smoke_artifact 返回 FAIL 且不抛错
    测试对象：build_smoke_artifact
    目的/目标：ci_perf_budget_artifact 可先写 FAIL artifact 再 exit 非零
    验证点：status FAIL；violations 非空；metrics 原样保留
    失败含义：脚本在 evaluate 抛错前无法落盘 FAIL artifact
    """
    budget = load_smoke_budget(BUDGET_YAML)
    metrics = {
        "elapsed_s": float(budget["thresholds"]["elapsed_s_max"]) + 5.0,
        "pytest_steps": 5,
        "shard_count_benchmark": 3,
        "guard_status": "observable",
    }
    artifact = build_smoke_artifact(metrics, budget=budget, use_service_path=True)
    assert artifact["status"] == "FAIL"
    assert artifact["violations"]
    assert artifact["metrics"] == metrics


def test_ciPerfBudgetArtifact_main_writesFailArtifactAndExitsNonZero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：CI perf smoke 超阈值时写 FAIL artifact 并以 exit 1 结束（script wiring）
    测试对象：scripts.ci_perf_budget_artifact.run_bounded_service_path_smoke
    目的/目标：VR-PERF-001 超线须落盘 FAIL 再非零退出；真实指标边界见 test_evaluateSmokeMetrics_*
    验证点：返回码==1；artifact status FAIL；violations 非空
    失败含义：CI nightly 超阈值无 artifact 或仍 exit 0
    """
    import scripts.ci_perf_budget_artifact as ci_perf

    data_root = tmp_path / "data"
    artifact_path = tmp_path / "budget.json"
    budget_path = tmp_path / "tight_budget.yaml"
    budget_path.write_text(
        "version: v1\n"
        "thresholds:\n"
        "  elapsed_s_max: 1\n"
        "  pytest_steps_min: 0\n"
        "  shard_count_benchmark_min: 0\n"
        "  guard_status_required: observable\n",
        encoding="utf-8",
    )
    times = iter([0.0, 50.0])
    monkeypatch.setattr(ci_perf.time, "perf_counter", lambda: next(times))
    monkeypatch.setattr(
        ci_perf.subprocess,
        "run",
        lambda *args, **kwargs: type("_Proc", (), {"returncode": 0})(),
    )

    code = ci_perf.run_bounded_service_path_smoke(
        data_root=data_root,
        budget_yaml=budget_path,
        artifact_path=artifact_path,
        use_service_path=True,
    )
    assert code == 1
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["status"] == "FAIL"
    assert payload["violations"]


def test_sourceRouteDbSpine_blockedTargetWritesBlockedReport(tmp_path: Path) -> None:
    """覆盖范围：source-route DB 验收 spine 对缺授权目标写 BLOCKED 报告
    测试对象：SourceRouteDbAcceptanceSpine.execute
    目的/目标：Phase 1 权威验收路径须诚实 BLOCKED，不依赖已退役 smoke 脚本
    验证点：failure_class=BLOCKED；status=FAIL；route_plan_id 非空
    失败含义：矩阵 spine 无法在无授权时产出可审计 BLOCKED 报告
    """
    from backend.app.ops.source_route_db_acceptance import (
        AcceptanceRequest,
        SourceRouteDbAcceptanceSpine,
        write_acceptance_report,
    )

    data_root = tmp_path / ".audit-sandbox" / "source-route-db-smoke"
    report_path = data_root / "reports" / "source_route_db_acceptance.json"
    request = AcceptanceRequest.from_target("macro_series:fred:fetch_macro_series")
    report = SourceRouteDbAcceptanceSpine().execute(
        request,
        data_root=data_root,
        live_authorized=False,
    )
    write_acceptance_report(report, report_path)
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["failure_class"] == "BLOCKED"
    assert payload["status"] == "FAIL"
    assert payload["route_plan_id"]
