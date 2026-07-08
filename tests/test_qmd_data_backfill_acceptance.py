"""Phase 1 backfill CLI production-equivalent acceptance tests."""

from __future__ import annotations

from pathlib import Path

from backend.app.cli import data_commands
from backend.app.core.resource_guard import Decision, ResourceGuard


def _p1_root(tmp_path: Path) -> Path:
    root = tmp_path / ".audit-sandbox" / "source-route-db-backfill"
    root.mkdir(parents=True)
    return root


def test_qmdData_backfillAcceptance_tierADryRunNonGate(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：Tier A backfill dry-run 验收信封
    测试对象：backfill_plan dry_run=True
    目的/目标：bis 等 Tier A 域 dry-run 不再仅 baostock/fred 可规划
    验证点：shard_count>0；gate_eligible=False；acceptance_report 存在
    失败含义：backfill dry-run 覆盖仍局限 pilot 源或无验收信封
    """
    root = _p1_root(tmp_path)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.backfill_plan(
        data_domain="central_bank_policy",
        source_id="bis",
        start="2024-01-01",
        end="2024-01-31",
        dry_run=True,
    )
    assert payload["dry_run"] is True
    assert payload["shard_count"] >= 1
    assert payload.get("gate_eligible") is False
    assert "acceptance_report" in payload


def test_qmdData_backfillAcceptance_sourceRouteDbLiveBlockedWithoutAuth(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：source-route-db live backfill 缺授权
    测试对象：backfill_plan dry_run=False on bis
    目的/目标：Tier A live backfill 走 phase1 路径并诚实 BLOCKED
    验证点：gate_eligible=True；failure_class=BLOCKED
    失败含义：非 baostock/fred live backfill 仍落旧 wired-only 路径
    """
    root = _p1_root(tmp_path)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.backfill_plan(
        data_domain="central_bank_policy",
        source_id="bis",
        start="2024-01-01",
        end="2024-01-07",
        dry_run=False,
    )
    assert payload.get("gate_eligible") is True
    assert payload["acceptance_report"]["failure_class"] == "BLOCKED"


def test_qmdData_backfillAcceptance_dryRunIncludesTriggerReasonAndShardPlan(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：backfill dry-run 补数证据
    测试对象：backfill_plan dry_run=True backfill_evidence
    目的/目标：dry-run 须保存 trigger_reason 与 shard_plan 供 operator 审计
    验证点：backfill_evidence.trigger_reason；shard_plan 长度>=1；recompute=deferred
    失败含义：backfill 无触发原因或分片计划，补数能力不可追溯
    """
    root = _p1_root(tmp_path)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.backfill_plan(
        data_domain="central_bank_policy",
        source_id="bis",
        start="2024-01-01",
        end="2024-01-31",
        trigger_reason="manual_request",
        dry_run=True,
    )
    evidence = payload.get("backfill_evidence") or {}
    assert evidence.get("trigger_reason") == "manual_request"
    assert len(evidence.get("shard_plan") or []) >= 1
    assert evidence.get("affected_snapshot_recompute") == "deferred"


def test_qmdData_backfillAcceptance_liveBlockedShowsCheckpointSemantics(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：backfill live 缺授权 checkpoint 语义
    测试对象：run_phase1_backfill_live backfill_evidence
    目的/目标：BLOCKED 路径仍声明 checkpoint/resume 事件类型与 shard 计划
    验证点：checkpoint_event_types 含 SHARD_COMPLETE；shard_plan 非空
    失败含义：backfill 验收无法证明断点续跑/幂等写入设计已接入
    """
    root = _p1_root(tmp_path)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.backfill_plan(
        data_domain="central_bank_policy",
        source_id="bis",
        start="2024-01-01",
        end="2024-01-07",
        dry_run=False,
    )
    evidence = payload.get("backfill_evidence") or {}
    assert evidence.get("trigger_reason") == "eco_catchup"
    assert len(evidence.get("shard_plan") or []) >= 1
    checkpoint_types = evidence.get("checkpoint_event_types") or []
    assert "SHARD_COMPLETE" in checkpoint_types
