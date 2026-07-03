"""M-DATA-03 AC-7 — Tier C local acceptance manifest (no GitHub live CI)."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIER_C_LIVE_YML = PROJECT_ROOT / ".github/workflows/tier-c-live.yml"
ACCEPTANCE_SCRIPT = PROJECT_ROOT / "scripts/tier_c_live_acceptance.py"


def test_tier_c_live_local_manifest_no_github_ci() -> None:
    """覆盖范围：Tier C live 验收本地清单（公开仓库无 GitHub CI）
    测试对象：workflow 缺席 · tier_c_live_acceptance 脚本
    目的/目标：AC-7 — 契约+本地脚本；无 workflow_dispatch / cron
    验证点：tier-c-live.yml 不存在；脚本含 --report
    失败含义：误恢复 GitHub live workflow 或 acceptance CLI 缺失
    """
    assert not TIER_C_LIVE_YML.is_file()
    assert ACCEPTANCE_SCRIPT.is_file()
    text = ACCEPTANCE_SCRIPT.read_text(encoding="utf-8")
    assert "--report" in text
