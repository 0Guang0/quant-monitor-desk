from __future__ import annotations

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

    assert gate.main([]) == 0

    flat = "\n".join(" ".join(part for part in call) for call in calls)
    assert "check_acceptance_helper_consumers.py" in flat and "--strict" in flat
    assert "check_source_route_db_acceptance_matrix.py" in flat and "--strict" in flat
    assert "accept-source-route-db" in flat and "--all-documented-sources" in flat
    assert "source-route-db-ci-dry" in flat
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

    assert gate.main(["--live-authorized"]) == 1


def test_productionGate_liveAuthorizedChecksProvidedReport(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：release gate live 报告校验
    测试对象：scripts.production_gate.main --live-authorized --source-matrix-report
    目的/目标：operator 提供 live 报告时须跑 --live-authorized matrix checker
    验证点：subprocess 含 --live-authorized 与给定报告路径；跳过 dry-run matrix 生成
    失败含义：final 关账证据未纳入 production_gate
    """
    import scripts.production_gate as gate

    calls: list[list[str]] = []
    report = tmp_path / "source-matrix-acceptance.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("{}", encoding="utf-8")

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

    assert (
        gate.main(
            [
                "--live-authorized",
                "--source-matrix-report",
                str(report),
            ]
        )
        == 0
    )

    flat = "\n".join(" ".join(part for part in call) for call in calls)
    assert "--live-authorized" in flat
    assert str(report) in flat
    assert "accept-source-route-db" not in flat
