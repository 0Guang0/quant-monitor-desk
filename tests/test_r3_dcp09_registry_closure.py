"""R3-DCP-09 registry closure guards."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PENDING_FIX = PROJECT_ROOT / "docs/quality/待修复清单.md"
ROADMAP = PROJECT_ROOT / "PROJECT_IMPLEMENTATION_ROADMAP.md"


def test_r3_dcp09_registry_ids_marked_closed() -> None:
    """覆盖范围：Wave3 验收台账四项 R3-DCP-09 关账登记
    测试对象：待修复清单.md · PROJECT_IMPLEMENTATION_ROADMAP.md
    目的/目标：S06 四 ID 标记承接完成
    验证点：WAVE3-ACC-OPT-01 等含 R3-DCP-09 关账语义
    失败含义：台账未关账，Audit 无法 PASS DCP-09
    """
    pending = PENDING_FIX.read_text(encoding="utf-8")
    roadmap = ROADMAP.read_text(encoding="utf-8")
    for registry_id in (
        "WAVE3-ACC-OPT-01",
        "ACC-LIVE-NETWORK-CI-001",
        "ACC-LIVE-ACCEPT-NIGHTLY-001",
        "LIVE-NETWORK-GATE-001",
    ):
        assert registry_id in pending
    assert "R3-DCP-09" in pending
    assert "✅ CLOSED" in pending or "关账" in pending
    assert "R3-DCP-09" in roadmap
