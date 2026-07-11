from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_productionGate_defaultRunsSourceMatrixDryRunChecks(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：PR/CI 默认 production_gate 矩阵 dry-run 门禁
    测试对象：scripts.production_gate.main
    目的/目标：默认须跑 helper strict、matrix static 与 dry-run closure，不触发 live fetch
    验证点：subprocess 含 check_acceptance_helper_consumers --strict 与 dry-run matrix 命令；无 --allow-live-fetch
    失败含义：CI 无法防止 source matrix 假绿或误跑 live 矩阵
    """
    import scripts.production_gate as gate

    calls: list[list[str]] = []

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        calls.append(list(cmd))
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(gate.subprocess, "run", fake_run)
    monkeypatch.setattr(gate, "check_no_prod_stub_validation", lambda: None)
    monkeypatch.setattr(gate, "check_workflow_permissions", lambda: None)
    monkeypatch.setattr(gate, "check_dependabot_present", lambda: None)
    monkeypatch.setattr(gate, "check_agent_contract", lambda: None)
    monkeypatch.setattr(gate, "check_resource_contract", lambda: None)
    monkeypatch.setattr(gate, "check_module_boundaries", lambda: None)
    monkeypatch.setattr(gate, "check_reference_adoption_guardrails", lambda: None)
    monkeypatch.setattr(gate, "check_datasource_service_boundaries", lambda: None)
    monkeypatch.setattr(gate, "check_platform_source_matrix", lambda: None)
    monkeypatch.setattr(gate, "check_contract_drift", lambda: None)
    monkeypatch.setattr(gate, "check_provider_catalog", lambda: None)
    monkeypatch.setattr(gate, "check_sync_job_contract", lambda: None)
    monkeypatch.setattr(gate, "check_source_route_db_acceptance_contract", lambda: None)

    assert gate.main([]) == 0

    flat = "\n".join(" ".join(part for part in call) for call in calls)
    assert "check_acceptance_helper_consumers.py" in flat and "--strict" in flat
    assert "check_source_route_db_acceptance_matrix.py" in flat and "--strict" in flat
    assert "accept-source-route-db" in flat and "--all-documented-sources" in flat
    assert "source-route-db-ci-dry" in flat
    assert "--target" not in flat
    assert "--allow-live-fetch" not in flat
    assert "--live-authorized" not in flat


def test_productionGate_liveAuthorizedRequiresReportPath(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：release gate 参数校验
    测试对象：scripts.production_gate.main --live-authorized
    目的/目标：live 报告校验必须显式绑定报告路径，防环境变量误触发
    验证点：缺少 --source-matrix-report 时 exit 1 且 stderr 含 PRODUCTION_GATE_FAIL
    失败含义：operator gate 可在无报告时假绿
    """
    import scripts.production_gate as gate

    monkeypatch.setattr(gate.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess([], 0, "", ""))
    monkeypatch.setattr(gate, "check_no_prod_stub_validation", lambda: None)
    monkeypatch.setattr(gate, "check_workflow_permissions", lambda: None)
    monkeypatch.setattr(gate, "check_dependabot_present", lambda: None)
    monkeypatch.setattr(gate, "check_agent_contract", lambda: None)
    monkeypatch.setattr(gate, "check_resource_contract", lambda: None)
    monkeypatch.setattr(gate, "check_module_boundaries", lambda: None)
    monkeypatch.setattr(gate, "check_reference_adoption_guardrails", lambda: None)
    monkeypatch.setattr(gate, "check_datasource_service_boundaries", lambda: None)
    monkeypatch.setattr(gate, "check_platform_source_matrix", lambda: None)
    monkeypatch.setattr(gate, "check_contract_drift", lambda: None)
    monkeypatch.setattr(gate, "check_provider_catalog", lambda: None)
    monkeypatch.setattr(gate, "check_sync_job_contract", lambda: None)
    monkeypatch.setattr(gate, "check_source_route_db_acceptance_contract", lambda: None)

    assert gate.main(["--live-authorized"]) == 1


def test_productionGate_liveAuthorizedChecksProvidedReport(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：release gate live 报告校验 outcome
    测试对象：scripts.production_gate.main --live-authorized --source-matrix-report
    目的/目标：mock/replay 支撑的 live PASS 报告须被真实 live checker 拒绝
    验证点：gate.main exit 1；subprocess checker 输出含 evidence_honesty_violations
    失败含义：final 关账证据可被假 live 报告绕过 production_gate
    """
    import scripts.production_gate as gate

    from backend.app.ops.source_route_db_acceptance_matrix import iter_matrix_targets, matrix_target_key

    data_root = tmp_path / "live-gate-sandbox"
    raw_dir = data_root / "raw" / "alpha_vantage" / "us_equity_daily_bar" / "2026-07-07"
    raw_dir.mkdir(parents=True)
    raw_dir.joinpath("evidence.json").write_text(
        json.dumps(
            {
                "source_id": "alpha_vantage",
                "source_fetch_id": "av-mock-AAPL-deadbeef",
                "bars": [],
            }
        ),
        encoding="utf-8",
    )
    av_target = next(t for t in iter_matrix_targets() if t.request.source_id == "alpha_vantage")
    report = tmp_path / "source-matrix-acceptance.json"
    report.write_text(
        json.dumps(
            {
                "matrix_count": 22,
                "live_authorized": True,
                "closure_mode": "final_live_authorized",
                "closure_status": "PASS",
                "data_root": str(data_root),
                "rows": [
                    {
                        "target": matrix_target_key(av_target),
                        "source_id": "alpha_vantage",
                        "status": "PASS",
                        "implementation_mode": "live",
                        "failure_class": "NONE",
                        "closure_outcome": "PASS",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(gate, "check_no_prod_stub_validation", lambda: None)
    monkeypatch.setattr(gate, "check_workflow_permissions", lambda: None)
    monkeypatch.setattr(gate, "check_dependabot_present", lambda: None)
    monkeypatch.setattr(gate, "check_agent_contract", lambda: None)
    monkeypatch.setattr(gate, "check_resource_contract", lambda: None)
    monkeypatch.setattr(gate, "check_module_boundaries", lambda: None)
    monkeypatch.setattr(gate, "check_reference_adoption_guardrails", lambda: None)
    monkeypatch.setattr(gate, "check_datasource_service_boundaries", lambda: None)
    monkeypatch.setattr(gate, "check_platform_source_matrix", lambda: None)
    monkeypatch.setattr(gate, "check_contract_drift", lambda: None)
    monkeypatch.setattr(gate, "check_provider_catalog", lambda: None)
    monkeypatch.setattr(gate, "check_sync_job_contract", lambda: None)
    monkeypatch.setattr(gate, "check_source_route_db_acceptance_contract", lambda: None)
    monkeypatch.setattr(gate, "check_acceptance_helper_consumers_strict", lambda: None)
    monkeypatch.setattr(gate, "check_source_route_matrix_static", lambda: None)

    assert (
        gate.main(
            [
                "--live-authorized",
                "--source-matrix-report",
                str(report),
            ]
        )
        == 1
    )
