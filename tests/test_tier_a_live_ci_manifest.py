"""M-DATA-03 S-R2-CI — Tier A local acceptance manifest (no GitHub live CI)."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIER_A_LIVE_YML = PROJECT_ROOT / ".github/workflows/tier-a-live.yml"
ACCEPTANCE_SCRIPT = PROJECT_ROOT / "scripts/tier_a_live_acceptance.py"
EVIDENCE_MD = (
    PROJECT_ROOT
    / ".trellis/tasks/archive/2026-07/m-data-03-tier-a-live/research/archive/non-plan/execute"
    / "r2-tier-a-live-accept-evidence.md"
)
SANDBOX_SSOT_SEGMENT = "r2-live-20260703220000"


def test_tier_a_live_local_manifest_no_github_ci() -> None:
    """覆盖范围：Tier A live 验收本地清单（公开仓库无 GitHub CI）
    测试对象：workflow 缺席 · acceptance 脚本 · 关账 evidence md
    目的/目标：D-03 + 路径 A — 真网证据仅本地沙箱；无 workflow_dispatch / cron
    验证点：tier-a-live.yml 不存在；脚本与 evidence 关账 run 锚点存在
    失败含义：关账锚点漂移或误恢复 GitHub live workflow
    """
    assert not TIER_A_LIVE_YML.is_file()
    assert ACCEPTANCE_SCRIPT.is_file()
    assert EVIDENCE_MD.is_file()
    evidence = EVIDENCE_MD.read_text(encoding="utf-8")
    assert SANDBOX_SSOT_SEGMENT in evidence
    script = ACCEPTANCE_SCRIPT.read_text(encoding="utf-8")
    assert "--report" in script
