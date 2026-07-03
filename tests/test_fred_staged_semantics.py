"""B2.5-O-05 FRED / macro_supplementary staged 语义门禁测试。

覆盖范围：审计延期、生产试点策略、Batch3 gate 与 Round3 任务卡对 FRED 主源的禁止误读。
"""

from __future__ import annotations

from pathlib import Path

from tests.contract_gate_support import PROJECT_ROOT

POLICY = PROJECT_ROOT / "docs/quality/production_live_pilot_policy.md"
GATE_DOC = PROJECT_ROOT / "docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md"
HANDOFF = PROJECT_ROOT / "docs/ROUND3_HANDOFF.md"
from tests.repo_paths import ROUND3_BATCH_IMPLEMENTATION_MAP as ROUND3_MAP, impl_task

TASK_018A = impl_task("ROUND_3_MODELING_LAYERS", "018A_layer1_observation_ingestion_bridge.md")
TASK_019 = impl_task("ROUND_3_MODELING_LAYERS", "019_implement_layer2_cross_asset_sensor.md")
AUDIT_DEFERRED = PROJECT_ROOT / "docs/AUDIT_DEFERRED_REGISTRY.md"
UNRESOLVED = PROJECT_ROOT / "docs/UNRESOLVED_ISSUES_REGISTRY.md"
PENDING_FIX = PROJECT_ROOT / "docs/quality/ROUND3_BATCH25_PENDING_FIX_REGISTRY.md"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing expected document: {path}"
    return path.read_text(encoding="utf-8")


def test_b250o05_remainsDeferred_withExplicitClosureCommand() -> None:
    """覆盖范围：B2.5-O-05 在三份延期/待修注册表中的登记
    测试对象：AUDIT_DEFERRED、UNRESOLVED_ISSUES、ROUND3_BATCH25_PENDING_FIX 注册表
    目的/目标：FRED 主源闭合项保持延期且带明确闭合命令与测试锚点
    验证点：三表均含 B2.5-O-05；审计/待修表含 RE-DEFERRED、FRED:DGS10、
    test_fred_staged_semantics.py 等 token
    失败含义：注册表缺失会导致 agent 误以为 Request 3 已关闭 FRED 主源
    """
    audit, unresolved, pending = map(_read, (AUDIT_DEFERRED, UNRESOLVED, PENDING_FIX))

    for registry in (audit, unresolved, pending):
        assert "B2.5-O-05" in registry

    for token in (
        "RE-DEFERRED",
        "Request 3",
        "FRED:DGS10",
        "macro_supplementary",
        "Batch 6",
        "test_fred_staged_semantics.py",
    ):
        assert token in audit or token in unresolved or token in pending


def test_policy_and_gate_forbidFredPrimaryMisreadFromRequest3() -> None:
    """覆盖范围：生产试点策略与 Batch3 gate 对 FRED 误读的禁止条款
    测试对象：production_live_pilot_policy.md、BATCH3_STAGED_DOWNSTREAM_GATE.md
    目的/目标：Request 3 不得被引用为 live FRED primary；macro 仅 staged supplementary
    验证点：策略含 B2.5-O-05、does not close、not be cited as live FRED primary；gate 含同类禁止表述
    失败含义：策略缺口会允许 staged 宏观数据被宣称生产主源
    """
    policy, gate = map(_read, (POLICY, GATE_DOC))

    for token in (
        "B2.5-O-05",
        "Request 3",
        "does **not** close `B2.5-O-05`",
        "macro_supplementary",
        "not be cited as live FRED primary",
        "staged supplementary route",
    ):
        assert token in policy

    assert "B2.5-O-05" in gate
    assert "Request 3" in gate
    assert "does **not** close" in gate
    assert "macro_supplementary" in gate


def test_handoff_map_and_taskCards_preserveStagedMacroSemantics() -> None:
    """覆盖范围：Round3 handoff、实现地图与 018A/019 任务卡
    测试对象：ROUND3_HANDOFF、ROUND3_BATCH_IMPLEMENTATION_MAP、018A/019 任务文档
    目的/目标：交接与任务卡持续声明 macro_supplementary 仅为形状证据、不闭合 B2.5-O-05
    验证点：各文档含 B2.5-O-05 与 macro_supplementary；handoff/map 含 does not close；
    018A 含 supplementary macro shape evidence only
    失败含义：任务卡语义漂移会导致建模层误用 Request 3 为 FRED 主源
    """
    handoff, round3_map, task_018a, task_019 = map(
        _read, (HANDOFF, ROUND3_MAP, TASK_018A, TASK_019)
    )

    for text in (handoff, round3_map, task_018a, task_019):
        assert "B2.5-O-05" in text
        assert "macro_supplementary" in text

    assert "does **not** close" in handoff
    assert "does **not** close" in round3_map
    assert "supplementary macro shape evidence only" in task_018a
    assert "Request 3" in task_019


def test_macroSupplementary_cannotCloseB250o05() -> None:
    """覆盖范围：macro_supplementary 不得闭合 B2.5-O-05
    测试对象：fred_sandbox_pilot.build_pilot_closeout
    目的/目标：仅 macro/akshare 证据时 B2.5-O-05 保持 RE-DEFERRED
    验证点：macro 源 closeout 的 b2_5_o_05_closed=False；fred-only 才记录证据
    失败含义：Request 3 宏观形状被误读为 FRED 主源闭合
    """
    from backend.app.ops.fred_sandbox_pilot import build_pilot_closeout

    macro_closeout = build_pilot_closeout(
        manifest={"source_id": "akshare", "series": [{"series_id": "DGS10"}]},
        health={"status": "PASS"},
    )
    assert macro_closeout["b2_5_o_05_closed"] is False
    assert macro_closeout["fred_only_evidence"] is False
    assert macro_closeout["macro_supplementary_cannot_close"] is True
    assert macro_closeout["b2_5_o_05_decision"] == "RE-DEFERRED"
