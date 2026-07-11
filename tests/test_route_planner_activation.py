"""RoutePlanner 安检接线 ask_activation + overlay_revision — G1-02 票 04 / brief 3B。"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest

from backend.app.datasources.activation_overlay import (
    ask_activation,
    write_activation_overlay,
)
from backend.app.datasources.capability_registry import SourceCapabilityRegistry
from backend.app.datasources.route_planner import SourceRoutePlanner
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.db.migrate import apply_migrations

_P_DAILY_SOURCE = "baostock"
_P_DAILY_DOMAIN = "cn_equity_daily_bar"
_P_DAILY_OPERATION = "fetch_daily_bar"


def _migrated_synced_db(tmp_path: Path, *parts: str) -> duckdb.DuckDBPyConnection:
    db = tmp_path.joinpath(*parts)
    db.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db))
    apply_migrations(con)
    reg = SourceRegistry()
    reg.load()
    reg.sync_to_db(con)
    return con


def _planner() -> SourceRoutePlanner:
    reg = SourceRegistry()
    reg.load()
    caps = SourceCapabilityRegistry()
    caps.load()
    return SourceRoutePlanner(source_registry=reg, capability_registry=caps)


def test_plan_withCon_exposesOverlayRevisionFromAskActivation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """覆盖范围：安检层消费问开关后 overlay_revision 可观察（ADR-018 / brief 3B）
    测试对象：SourceRoutePlanner.plan(con=…)（P-DAILY + 沙箱 overlay）
    目的/目标：有 DB 连接时合成结果携带与 ask_activation 一致的 overlay_revision
    验证点：route_status=READY；plan.overlay_revision == ask 的 revision；日志含同字段
    失败含义：安检未接开关本，或 revision 未进入 RoutePlan/可观察日志
    """
    con = _migrated_synced_db(
        tmp_path, ".audit-sandbox", "planner-04", "duckdb", "quant_monitor.duckdb"
    )
    revision = write_activation_overlay(
        con,
        source_id=_P_DAILY_SOURCE,
        data_domain=_P_DAILY_DOMAIN,
        operation=_P_DAILY_OPERATION,
        enabled=True,
        reason="[sandbox] baostock overlay revision observable",
        changed_by="test_route_planner_activation",
        sandbox=True,
    )
    asked = ask_activation(
        con,
        source_id=_P_DAILY_SOURCE,
        data_domain=_P_DAILY_DOMAIN,
        operation=_P_DAILY_OPERATION,
    )
    assert asked.is_allowed is True
    assert asked.overlay_revision == revision

    plan = _planner().plan(
        data_domain=_P_DAILY_DOMAIN,
        operation=_P_DAILY_OPERATION,
        run_id="t04-rev",
        job_id="t04-rev-job",
        con=con,
    )
    assert plan.route_status == "READY"
    assert plan.selected_source_id == _P_DAILY_SOURCE
    assert plan.overlay_revision == revision

    err = capsys.readouterr().err
    events = [json.loads(line) for line in err.splitlines() if line.strip().startswith("{")]
    policy = [e for e in events if e.get("event") in {"source_policy_resolved", "source_policy_denied"}]
    assert policy, f"expected source_policy_* log, got stderr={err!r}"
    assert policy[-1]["overlay_revision"] == revision
    assert policy[-1]["reason_code"] in {"", "READY", plan.route_status}
    assert "correlation_id" in policy[-1] or "run_id" in policy[-1]


def test_plan_withCon_overlayDisable_blocksBaseEnabledSource(tmp_path: Path) -> None:
    """覆盖范围：正规 overlay.enabled=false 覆盖基础启用（安检只读合成）
    测试对象：SourceRoutePlanner.plan(con=…)（baostock overlay 关闭）
    目的/目标：开关本拒绝后该源不得被安检选中（可降到其他候选，但不得选 baostock）
    验证点：baostock.enabled False；selected != baostock；overlay_revision 非空
    失败含义：安检仍只读内存 is_enabled，overlay 拒绝无效
    """
    con = _migrated_synced_db(
        tmp_path, ".audit-sandbox", "planner-04-deny", "duckdb", "quant_monitor.duckdb"
    )
    revision = write_activation_overlay(
        con,
        source_id=_P_DAILY_SOURCE,
        data_domain=_P_DAILY_DOMAIN,
        operation=_P_DAILY_OPERATION,
        enabled=False,
        reason="[sandbox] deny baostock via overlay",
        changed_by="test_route_planner_activation",
        sandbox=True,
    )
    plan = _planner().plan(
        data_domain=_P_DAILY_DOMAIN,
        operation=_P_DAILY_OPERATION,
        run_id="t04-deny",
        job_id="t04-deny-job",
        con=con,
    )
    baostock = next(c for c in plan.candidates if c.source_id == _P_DAILY_SOURCE)
    assert baostock.enabled is False
    assert baostock.skip_reason == "source_disabled_by_default"
    assert plan.selected_source_id != _P_DAILY_SOURCE
    assert plan.overlay_revision == revision


def test_plan_withCon_ignoresInMemoryIsEnabledSetattr(tmp_path: Path) -> None:
    """覆盖范围：安检路径禁止内存撬门冒充关闭/启用（ADR-018）
    测试对象：SourceRoutePlanner.plan(con=…) 在 object.__setattr__(is_enabled=False) 之后
    目的/目标：有 con 时启用判定读 ask_activation/DB，不读已加载对象突变
    验证点：setattr baostock.is_enabled=False 后 plan 仍 READY（DB 基础仍启用）
    失败含义：安检仍信内存对象，测试/CLI 可继续 OVERRIDE
    """
    con = _migrated_synced_db(
        tmp_path, ".audit-sandbox", "planner-04-mem", "duckdb", "quant_monitor.duckdb"
    )
    reg = SourceRegistry()
    reg.load()
    rec = reg.get(_P_DAILY_SOURCE)
    object.__setattr__(rec, "is_enabled", False)
    assert rec.is_enabled is False

    caps = SourceCapabilityRegistry()
    caps.load()
    planner = SourceRoutePlanner(source_registry=reg, capability_registry=caps)
    plan = planner.plan(
        data_domain=_P_DAILY_DOMAIN,
        operation=_P_DAILY_OPERATION,
        run_id="t04-mem",
        job_id="t04-mem-job",
        con=con,
    )
    assert plan.route_status == "READY"
    assert plan.selected_source_id == _P_DAILY_SOURCE
