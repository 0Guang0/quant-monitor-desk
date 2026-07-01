"""B3F-LIN acceptance gate — lineage / Layer3 registry closure evidence (R3F-LIN-01..03)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from backend.app.layer3_chains.snapshot_builder import (
    Layer3SnapshotError,
    _bar_for_trade_date,
)

from tests.contract_gate_support import PROJECT_ROOT, collect_pytest_node_id

_ARCHIVE_2026_06 = PROJECT_ROOT / ".trellis" / "tasks" / "archive" / "2026-06"
TASK_DIR = _ARCHIVE_2026_06 / "round3f-batch6-lineage-layer3-closure"
MANIFEST_PATH = TASK_DIR / "research" / "closure-evidence-manifest.yaml"
REGISTRY_DRAFT = TASK_DIR / "research" / "registry-proposed-delta.md"

_EXPECTED_ROADMAP_IDS = (
    "R3F-L3-01",
    "R3F-L3-02",
    "R3F-LIN-02",
    "R3F-LIN-02-negative",
    "R3F-LIN-01",
    "R3F-LIN-01-l3",
)


def test_b3fLin_closureEvidenceManifest_listsAllRoadmapIds() -> None:
    """覆盖范围：B3F-LIN Execute 闭环证据清单是否齐全
    测试对象：archive/2026-06/round3f-batch6-lineage-layer3-closure/research/closure-evidence-manifest.yaml
    目的/目标：R3F-LIN-03 — 主会话批处理 registry 前，分支内须有可审计的 pytest→registry ID 映射
    验证点：manifest 存在且含 closure_tests 全部六键（含负向与 L3 子项）
    失败含义：无 manifest 则无法证明 Batch6 lineage 项已由本分支验收，易与 3D.3 partial hygiene 混淆
    """
    assert MANIFEST_PATH.is_file(), f"missing closure manifest: {MANIFEST_PATH}"
    data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    closure_tests = data.get("closure_tests") or {}
    for roadmap_id in _EXPECTED_ROADMAP_IDS:
        assert roadmap_id in closure_tests, f"missing roadmap id {roadmap_id!r} in manifest"


def test_b3fLin_registryProposedDelta_documentsFourIds() -> None:
    """覆盖范围：registry 草案是否登记四条 Batch6 lineage 开放项
    测试对象：research/registry-proposed-delta.md（proposed only，非三件套直接闭合）
    目的/目标：R3F-LIN-03 — 分支交付 proposed delta，主会话/B3F-REG 批处理 RESOLVED
    验证点：四条 ID 均含 PROPOSED 行且含 RESOLVED 目标动作（非仅文件存在）
    失败含义：无草案即违反 playbook §2.1 registry 批处理纪律
    """
    assert REGISTRY_DRAFT.is_file(), f"missing registry draft: {REGISTRY_DRAFT}"
    text = REGISTRY_DRAFT.read_text(encoding="utf-8")
    for item_id in (
        "ADV-R3X-LINEAGE-001",
        "R3Y-LINEAGE-VR-001",
        "R3-B6-021-O-01",
        "R3-B6-021-O-02",
    ):
        assert item_id in text, f"registry draft missing {item_id}"
        section = text.split(item_id, maxsplit=1)[1].split("\n##", maxsplit=1)[0]
        assert "PROPOSED" in section.upper(), f"{item_id} missing PROPOSED action"


def test_b3fLin_r3fL301_malformedBarElement_failClosed() -> None:
    """覆盖范围：bars[] 非 mapping 元素在 schema 边界 fail-closed
    测试对象：snapshot_builder._bar_for_trade_date
    目的/目标：R3F-L3-01 / R3-B6-021-O-01 — 禁止 continue 静默跳过畸形 bar
    验证点：bars 含 int 元素 → Layer3SnapshotError 且消息含 mapping
    失败含义：021 遗留静默跳过，畸形 manifest 可渗入 Layer3 快照
    """
    from datetime import date

    cfg = {
        "bars": [
            42,
            {
                "trade_date": "2026-06-14",
                "close": 1.0,
                "as_of_timestamp": "2026-06-14T20:00:00+00:00",
            },
        ]
    }
    with pytest.raises(Layer3SnapshotError, match="mapping"):
        _bar_for_trade_date(cfg, date(2026, 6, 14), "MSFT")


def test_b3fLin_closureTests_mapToCollectibleNodes() -> None:
    """覆盖范围：manifest 中登记的 pytest node id 可被收集
    测试对象：closure-evidence-manifest.yaml closure_tests 全部条目
    目的/目标：R3F-LIN-03 — 验收命令与 manifest 一致，防止挂名测试不存在
    验证点：每条 node id 经 pytest --collect-only 成功且输出含测试名
    失败含义：registry 草案引用的测试不存在，closure 证据链断裂
    """
    if not MANIFEST_PATH.is_file():
        pytest.skip("manifest not created yet")
    data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    closure_tests = data.get("closure_tests") or {}
    assert closure_tests, "closure_tests empty"
    for roadmap_id, node_id in closure_tests.items():
        assert isinstance(node_id, str) and "::" in node_id, roadmap_id
        collect_pytest_node_id(node_id)
