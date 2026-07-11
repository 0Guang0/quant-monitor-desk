"""G1-02 票 06（4a）：增量 bundle 正式入口行为 — 只问开关 + plan，无 ESR 旁路。

静态「生产源码无 ESR 字样」扫描已迁至
phase-scripts/check_g1_02_esr_fixture_hygiene.py（artifact-guard，非业务 pytest）。
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from backend.app.datasources.source_registry import SourceRegistry
from backend.app.db.migrate import apply_migrations
from backend.app.ops.macro_incremental_common import load_incremental_route_bundle
from tests.service_path_support import enable_source_route


def test_loadIncrementalRouteBundle_withSandboxOverlay_planReady(
    tmp_path: Path,
) -> None:
    """覆盖范围：沙箱正规 overlay → 增量 bundle 安检 READY（brief §7.2）
    测试对象：load_incremental_route_bundle + enable_source_route + plan(con=)
    目的/目标：隔离根写 overlay 后，干净 registry 的 planner 可 READY（无 ESR）
    验证点：route_status=READY；selected_source_id=fred；overlay_revision 非空
    失败含义：bundle 仍依赖内存启用，或未消费 con/overlay/platform 夹具
    """
    db = tmp_path / ".audit-sandbox" / "inc-06" / "duckdb" / "quant_monitor.duckdb"
    db.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db))
    apply_migrations(con)
    enable_source_route(
        tmp_path,
        source_id="fred",
        data_domain="macro_series",
        primary_source_id="fred",
        operation="fetch_macro_series",
        con=con,
    )
    matrix_path = tmp_path / "platform-matrix" / "platform-matrix-fred.yaml"
    # 正式路径证据：干净 load，不注入 enable_source_route 的内存改写副本（F06）
    _registry, _caps, planner = load_incremental_route_bundle(
        source_id="fred",
        data_domain="macro_series",
        platform_matrix_path=matrix_path,
    )
    plan = planner.plan(
        data_domain="macro_series",
        operation="fetch_macro_series",
        run_id="t06-bundle",
        job_id="t06-bundle-job",
        con=con,
    )
    assert plan.route_status == "READY"
    assert plan.selected_source_id == "fred"
    assert plan.overlay_revision


def test_loadIncrementalRouteBundle_productDefault_fredDisabled(
    tmp_path: Path,
) -> None:
    """覆盖范围：产品默认库同参仍 DISABLED（brief §7.2 反证）
    测试对象：load_incremental_route_bundle + plan(con=) 无 overlay
    目的/目标：默认关源不得因增量工厂变绿
    验证点：route_status 非 READY；无 selected_source_id
    失败含义：仍有 ESR/强制 platform 把产品默认伪装成已启用
    """
    db = tmp_path / "product" / "duckdb" / "quant_monitor.duckdb"
    db.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db))
    apply_migrations(con)
    reg = SourceRegistry()
    reg.load()
    reg.sync_to_db(con)
    _registry, _caps, planner = load_incremental_route_bundle(
        source_id="fred",
        data_domain="macro_series",
    )
    plan = planner.plan(
        data_domain="macro_series",
        operation="fetch_macro_series",
        run_id="t06-product",
        job_id="t06-product-job",
        con=con,
    )
    assert plan.route_status != "READY"
    assert plan.selected_source_id is None


def test_plan_preferredPrimary_pinsMootdxWhenBaostockAlsoAllowed(
    tmp_path: Path,
) -> None:
    """覆盖范围：显式 preferred_primary 钉主源（Standards：禁内存改 domain_roles）
    测试对象：SourceRoutePlanner.plan(preferred_primary_source_id=)
    目的/目标：baostock 亦允许时仍可选中 mootdx，无需改 registry 副本
    验证点：selected_source_id=mootdx；route_status=READY
    失败含义：仍依赖 enable_source_route 内存改 primary
    """
    import platform as py_platform

    import yaml

    from backend.app.datasources.activation_overlay import write_activation_overlay
    from backend.app.datasources.capability_registry import SourceCapabilityRegistry
    from backend.app.datasources.route_planner import SourceRoutePlanner

    db = tmp_path / ".audit-sandbox" / "pref-primary" / "duckdb" / "quant_monitor.duckdb"
    db.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db))
    apply_migrations(con)
    reg = SourceRegistry()
    reg.load()
    reg.sync_to_db(con, tombstone_missing=False)
    write_activation_overlay(
        con,
        source_id="mootdx",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        enabled=True,
        reason="[sandbox] pin mootdx preferred primary",
        changed_by="test_g1_02_preferred_primary",
        sandbox=True,
    )
    # 双源同矩阵平台放行，证明 preferred 而非「baostock 平台失败」导致选中
    base = yaml.safe_load(SourceRoutePlanner.DEFAULT_MATRIX.read_text(encoding="utf-8")) or {}
    plat = py_platform.system().lower()
    key = "windows" if plat == "windows" else "macos" if plat == "darwin" else "linux"
    entry = base.setdefault("platforms", {}).setdefault(key, {})
    for sid in ("baostock", "mootdx"):
        entry[sid] = {"available_if_user_configured": True, "default_enabled": True}
    matrix = tmp_path / "platform-matrix" / "both.yaml"
    matrix.parent.mkdir(parents=True, exist_ok=True)
    matrix.write_text(yaml.dump(base, allow_unicode=True), encoding="utf-8")
    caps = SourceCapabilityRegistry()
    caps.load()
    planner = SourceRoutePlanner(
        source_registry=reg,
        capability_registry=caps,
        platform_matrix_path=matrix,
    )
    without = planner.plan(
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        run_id="t06-pref-control",
        job_id="t06-pref-control-job",
        con=con,
    )
    assert without.selected_source_id == "baostock"
    plan = planner.plan(
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        run_id="t06-pref",
        job_id="t06-pref-job",
        con=con,
        preferred_primary_source_id="mootdx",
    )
    assert plan.route_status == "READY"
    assert plan.selected_source_id == "mootdx"


def test_plan_preferredPrimary_outsideDomainCandidates_doesNotInject(
    tmp_path: Path,
) -> None:
    """覆盖范围：preferred_primary 不得把域外源注入候选链（L5 正确性）
    测试对象：SourceRoutePlanner.plan(preferred_primary_source_id=)
    目的/目标：域角色未列出的源不能因 preferred 被当成 Primary 候选
    验证点：preferred=fred 于 cn_equity 时 selected 仍为域内源（baostock）或非 fred
    失败含义：plan 把任意 source_id 塞进 ordered，审计候选链被污染
    """
    from backend.app.datasources.capability_registry import SourceCapabilityRegistry
    from backend.app.datasources.route_planner import SourceRoutePlanner

    db = tmp_path / ".audit-sandbox" / "pref-alien" / "duckdb" / "quant_monitor.duckdb"
    db.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db))
    apply_migrations(con)
    reg = SourceRegistry()
    reg.load()
    reg.sync_to_db(con, tombstone_missing=False)
    caps = SourceCapabilityRegistry()
    caps.load()
    planner = SourceRoutePlanner(source_registry=reg, capability_registry=caps)
    plan = planner.plan(
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        run_id="t06-alien",
        job_id="t06-alien-job",
        con=con,
        preferred_primary_source_id="fred",
    )
    assert plan.selected_source_id != "fred"
    assert all(c.source_id != "fred" for c in plan.candidates)


def test_isAuditSandboxDataRoot_requiresPathSegment() -> None:
    """覆盖范围：沙箱根判定须为路径段，禁止子串误匹配（L5 信任边界）
    测试对象：is_audit_sandbox_data_root
    目的/目标：仅当某一 path part 等于 `.audit-sandbox` 才放行写 overlay
    验证点：真沙箱 True；`foo.audit-sandbox-backup` 等子串仿造 False
    失败含义：产品路径名含子串即可被 ensure 写启用
    """
    from backend.app.datasources.incremental_route_activation import (
        is_audit_sandbox_data_root,
    )

    assert is_audit_sandbox_data_root(Path("data") / ".audit-sandbox" / "run") is True
    assert is_audit_sandbox_data_root(Path("data") / "foo.audit-sandbox-backup") is False
    assert is_audit_sandbox_data_root(Path("data") / "prod") is False
