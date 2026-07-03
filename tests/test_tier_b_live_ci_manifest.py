"""M-DATA-03 AC-7 — tier-b-live workflow manifest tests."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIER_B_LIVE_YML = PROJECT_ROOT / ".github/workflows/tier-b-live.yml"
FAILURE_ARTIFACT_GLOB = "tier_b_live_acceptance_failure_*.json"
REPORT_GLOB = "tier-b-report.json"


def test_tier_b_live_ci_manifest_workflow_dispatch_and_artifacts() -> None:
    """覆盖范围：tier-b-live workflow 可执行清单
    测试对象：.github/workflows/tier-b-live.yml
    目的/目标：AC-7 CI — workflow_dispatch、schedule --quick、failure artifact 路径
    验证点：workflow_dispatch；schedule cron；--quick 条件；upload-artifact glob；tier-b sandbox
    失败含义：tier-b CI 漂移无法被 pytest 捕获，关账证据与 workflow 脱节
    """
    yml = TIER_B_LIVE_YML.read_text(encoding="utf-8")
    assert "workflow_dispatch" in yml
    assert "schedule:" in yml
    assert "cron:" in yml
    assert "--quick" in yml
    assert "--report" in yml
    assert "QMD_ALLOW_LIVE_FETCH" in yml
    assert ".audit-sandbox/m-data-03" in yml
    assert "tier-b" in yml
    assert "upload-artifact@v4" in yml
    assert FAILURE_ARTIFACT_GLOB in yml
    assert REPORT_GLOB in yml
    assert "if: failure()" in yml
