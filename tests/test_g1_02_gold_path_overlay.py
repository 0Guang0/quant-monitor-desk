"""G1-02 票 07（4b）：金路径正式入口行为 — 非 fred + 沙箱 overlay → READY。

关账双门（故意拆开，符合 testing-guidelines / TEST-EVIDENCE-GOVERNANCE）：
- 本文件：业务 outcome（else 分支 + overlay → READY）
- 「只清 fred 漏 else → 红」静态反证：
  `uv run python phase-scripts/check_g1_02_esr_fixture_hygiene.py --strict`
  （artifact-guard，禁止再塞回业务 pytest）
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from backend.app.cli import data_commands
from backend.app.db.migrate import apply_migrations
from tests.service_path_support import enable_source_route


def test_goldPathBackfill_sandboxOverlay_nonFredReady(tmp_path: Path) -> None:
    """覆盖范围：非 fred 金路径 + 沙箱 overlay → READY（E-CLI-20 else）
    测试对象：_gold_path_backfill_route_preview(source_id=baostock, con=)
    目的/目标：else 分支与服务同路，只读问开关+安检
    验证点：route_status=READY；selected_source_id=baostock
    失败含义：else 仍靠 ESR，或未接 con/overlay
    """
    db = tmp_path / ".audit-sandbox" / "gold-07" / "duckdb" / "quant_monitor.duckdb"
    db.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db))
    apply_migrations(con)
    enable_source_route(
        tmp_path,
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
        primary_source_id="baostock",
        operation="fetch_daily_bar",
        con=con,
    )
    matrix_path = tmp_path / "platform-matrix" / "platform-matrix-baostock.yaml"
    plan, _decision, _reason = data_commands._gold_path_backfill_route_preview(
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        con=con,
        platform_matrix_path=matrix_path,
    )
    assert plan.route_status == "READY"
    assert plan.selected_source_id == "baostock"


def test_goldPathBackfill_preferredPrimary_pinsMootdxOverBaostock(
    tmp_path: Path,
) -> None:
    """覆盖范围：金路径显式 source_id=mootdx 须钉主源（ACC / review Required）
    测试对象：_gold_path_backfill_route_preview(source_id=mootdx)
    目的/目标：baostock 亦允许时仍选中 mootdx（preferred_primary 贯通）
    验证点：selected_source_id=mootdx；route_status=READY
    失败含义：ensure 后仍按 YAML primary 选中 baostock
    """
    import platform as py_platform

    import yaml

    from backend.app.datasources.activation_overlay import write_activation_overlay
    from backend.app.datasources.route_planner import SourceRoutePlanner
    from backend.app.datasources.source_registry import SourceRegistry

    db = tmp_path / ".audit-sandbox" / "gold-mootdx" / "duckdb" / "quant_monitor.duckdb"
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
        reason="[sandbox] gold path pin mootdx",
        changed_by="test_g1_02_gold_path_overlay",
        sandbox=True,
    )
    base = yaml.safe_load(SourceRoutePlanner.DEFAULT_MATRIX.read_text(encoding="utf-8")) or {}
    plat = py_platform.system().lower()
    key = "windows" if plat == "windows" else "macos" if plat == "darwin" else "linux"
    entry = base.setdefault("platforms", {}).setdefault(key, {})
    for sid in ("baostock", "mootdx"):
        entry[sid] = {"available_if_user_configured": True, "default_enabled": True}
    matrix = tmp_path / "platform-matrix" / "both.yaml"
    matrix.parent.mkdir(parents=True, exist_ok=True)
    matrix.write_text(yaml.dump(base, allow_unicode=True), encoding="utf-8")

    plan, _decision, _reason = data_commands._gold_path_backfill_route_preview(
        source_id="mootdx",
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        con=con,
        platform_matrix_path=matrix,
    )
    assert plan.route_status == "READY"
    assert plan.selected_source_id == "mootdx"
