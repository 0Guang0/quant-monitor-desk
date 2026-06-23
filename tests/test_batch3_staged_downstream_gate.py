"""Batch 3 下游仅 staged 门禁文档测试。

覆盖范围：BATCH3_STAGED_DOWNSTREAM_GATE 文档、019 任务卡与 Round3 交接文
是否已闭合 staged-only 决策并禁止在未过门禁前启动 Layer2 运行时。
"""

from __future__ import annotations

from pathlib import Path

from tests.contract_gate_support import PROJECT_ROOT

GATE_DOC = PROJECT_ROOT / "docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md"
TASK_019 = (
    PROJECT_ROOT
    / "docs/implementation_tasks/ROUND_3_MODELING_LAYERS/019_implement_layer2_cross_asset_sensor.md"
)
ROUND3_MAP = PROJECT_ROOT / "ROUND3_BATCH_IMPLEMENTATION_MAP.md"
HANDOFF = PROJECT_ROOT / "docs/ROUND3_HANDOFF.md"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing expected document: {path}"
    return path.read_text(encoding="utf-8")


def test_batch3_staged_gate_records_fail_closed_decisions() -> None:
    """覆盖范围：Batch 3 下游仅 staged 门禁文档里的关键决策与禁止项
    测试对象：docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md
    目的/目标：Batch 3 门禁文档已闭合，且明确不开放 production-live
    验证点：含 R3-B3-STAGED-DOWNSTREAM-GATE、PILOT_FAIL_SOURCE、staged-only、**CLOSED**；禁止 live FRED、生产库写入、全市场拉取等措辞存在
    失败含义：门禁文档缺 fail-closed 条款，可能被误读为已允许线上数据
    """
    text = _read(GATE_DOC)
    for token in (
        "R3-B3-STAGED-DOWNSTREAM-GATE",
        "PILOT_FAIL_SOURCE",
        "R3-B2.75-REQ2-EM",
        "staged-only",
        "does not open production-live",
        "018C",
        "does not unblock production-live",
        "Fail-closed production-live language",
        "`019` staged-only start conditions",
        "**CLOSED**",
    ):
        assert token in text
    for token in (
        "live FRED primary",
        "production clean DB mutation",
        "QMT/xqshare/Yahoo",
        "full-market/full-history",
    ):
        assert token in text


def test_task019_and_handoff_require_closed_gate_before_runtime() -> None:
    """覆盖范围：019 任务卡、交接文档与 Round3 地图对 Batch 3 门禁的前置要求
    测试对象：019_implement_layer2_cross_asset_sensor.md、ROUND3_HANDOFF.md、ROUND3_BATCH_IMPLEMENTATION_MAP.md
    目的/目标：未闭合 staged 门禁前不得启动 Layer2 运行时分支
    验证点：019 含 R3-B3-STAGED-DOWNSTREAM-GATE 与 feature/round3-batch3-staged-gate；handoff 含 PILOT_FAIL_SOURCE 与 CLOSED；地图禁止启动 feature/round3-019-layer2-sensor
    失败含义：任务卡或交接文未绑门禁，可能绕过 staged-only 直接开 019 实现
    """
    assert "R3-B3-STAGED-DOWNSTREAM-GATE" in _read(TASK_019)
    assert "feature/round3-batch3-staged-gate" in _read(TASK_019)
    handoff = _read(HANDOFF)
    assert "PILOT_FAIL_SOURCE" in handoff
    assert "R3-B2.75-REQ2-EM" in handoff
    assert "CLOSED" in handoff
    assert "Do not start `feature/round3-019-layer2-sensor`" in _read(ROUND3_MAP)
