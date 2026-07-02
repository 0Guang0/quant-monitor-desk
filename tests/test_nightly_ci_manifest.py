"""R3-DCP-09 nightly CI manifest tests."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
NIGHTLY_YML = PROJECT_ROOT / ".github/workflows/nightly.yml"
NIGHTLY_DOC = PROJECT_ROOT / "docs/ops/nightly_ci.md"
PYTEST_NODE = (
    "tests/test_batch275_live_pilot_gate.py::test_livePilot_phase3RawOnly_threeRequestsLive"
)


def test_nightly_ci_manifest_workflow_dispatch_and_network_subset() -> None:
    """覆盖范围：nightly workflow 可执行清单
    测试对象：.github/workflows/nightly.yml + docs/ops/nightly_ci.md
    目的/目标：ACC-LIVE-NETWORK-CI-001 · LIVE-NETWORK-GATE-001 关账
    验证点：workflow_dispatch；--run-network；batch275 node id
    失败含义：nightly 不可手动触发或缺 network 子集，live gate 漂移
    """
    yml = NIGHTLY_YML.read_text(encoding="utf-8")
    doc = NIGHTLY_DOC.read_text(encoding="utf-8")
    assert "workflow_dispatch" in yml
    assert "--run-network" in yml
    assert PYTEST_NODE in yml
    assert PYTEST_NODE in doc
    assert "--fail-on-severity HIGH,CRITICAL" in yml
    assert "wave3_live_production_acceptance.py" in yml
