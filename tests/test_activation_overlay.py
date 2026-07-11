"""问开关（activation overlay）契约与持久化测试 — G1-02 票 03 / brief 3A。"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from backend.app.datasources.activation_overlay import (
    ask_activation,
    write_activation_overlay,
)
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.db.migrate import apply_migrations

# P-MACRO：fred 默认关；P-DAILY 形：baostock 默认开
_P_MACRO_SOURCE = "fred"
_P_MACRO_DOMAIN = "macro_series"
_P_MACRO_OPERATION = "fetch_macro_series"
_P_DAILY_SOURCE = "baostock"
_P_DAILY_DOMAIN = "cn_equity_daily_bar"
_P_DAILY_OPERATION = "fetch_daily_bar"


def _migrated_synced_db(tmp_path: Path, *parts: str) -> duckdb.DuckDBPyConnection:
    """在 tmp_path 下按路径建库：迁移 + YAML sync。"""
    db = tmp_path.joinpath(*parts)
    db.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db))
    apply_migrations(con)
    reg = SourceRegistry()
    reg.load()
    reg.sync_to_db(con)
    return con


def test_askActivation_returnsThreeFieldDecision(tmp_path: Path) -> None:
    """覆盖范围：问开关最小对外契约（ADR-018 / brief 3A）
    测试对象：ask_activation(source_id, data_domain, operation)
    目的/目标：输入仅三键，输出固定为 is_allowed / reason_code / overlay_revision
    验证点：字段齐全；P-MACRO 无 overlay 时拒绝且 reason=DISABLED_SOURCE
    失败含义：开关本契约漂移，下游安检/RoutePlan 无法同参消费
    """
    con = _migrated_synced_db(tmp_path, "product", "duckdb", "quant_monitor.duckdb")
    decision = ask_activation(
        con,
        source_id=_P_MACRO_SOURCE,
        data_domain=_P_MACRO_DOMAIN,
        operation=_P_MACRO_OPERATION,
    )
    assert decision.is_allowed is False
    assert decision.reason_code == "DISABLED_SOURCE"
    assert isinstance(decision.overlay_revision, str)


def test_askActivation_baseEnabledSource_allowsWithoutOverlay(tmp_path: Path) -> None:
    """覆盖范围：无 overlay 时回落 DB 基础 is_enabled
    测试对象：ask_activation（baostock / cn_equity_daily_bar）
    目的/目标：YAML 默认启用源在产品库无覆盖层时应 is_allowed=True
    验证点：is_allowed True；reason_code 为空串；overlay_revision 为空串
    失败含义：开关本把默认启用源误拒，或偷偷依赖内存对象
    """
    con = _migrated_synced_db(tmp_path, "product", "duckdb", "quant_monitor.duckdb")
    decision = ask_activation(
        con,
        source_id=_P_DAILY_SOURCE,
        data_domain=_P_DAILY_DOMAIN,
        operation=_P_DAILY_OPERATION,
    )
    assert decision.is_allowed is True
    assert decision.reason_code == ""
    assert decision.overlay_revision == ""


def test_askActivation_ignoresInMemorySetattrBypass(tmp_path: Path) -> None:
    """覆盖范围：禁止内存撬门冒充启用（ADR-018 §2）
    测试对象：ask_activation 在 object.__setattr__(is_enabled) 之后
    目的/目标：未写 overlay 时，突变已加载对象的 is_enabled 不得放行问开关
    验证点：setattr 后 is_allowed 仍为 False；reason_code 仍为 DISABLED_SOURCE
    失败含义：测试/CLI 可继续靠内存 OVERRIDE 绕过开关本
    """
    con = _migrated_synced_db(tmp_path, "product", "duckdb", "quant_monitor.duckdb")
    reg = SourceRegistry()
    reg.load()
    rec = reg.get(_P_MACRO_SOURCE)
    assert rec.is_enabled is False
    object.__setattr__(rec, "is_enabled", True)
    assert rec.is_enabled is True

    decision = ask_activation(
        con,
        source_id=_P_MACRO_SOURCE,
        data_domain=_P_MACRO_DOMAIN,
        operation=_P_MACRO_OPERATION,
    )
    assert decision.is_allowed is False
    assert decision.reason_code == "DISABLED_SOURCE"


def test_sandboxOverlay_allowsWhileProductDefaultStillDenies(tmp_path: Path) -> None:
    """覆盖范围：隔离根正规 overlay 可测允许；产品默认库同参仍拒绝（P-MACRO）
    测试对象：write_activation_overlay(sandbox=True) + ask_activation（两套独立 DuckDB）
    目的/目标：沙箱写标明 sandbox 用途的 overlay 后问开关允许；产品库无该行仍拒绝
    验证点：sandbox is_allowed True 且 overlay_revision 非空；product is_allowed False
    失败含义：产品默认被测试需要撬开，或沙箱无法用正规 overlay 证明启用
    """
    product = _migrated_synced_db(tmp_path, "product", "duckdb", "quant_monitor.duckdb")
    sandbox = _migrated_synced_db(
        tmp_path,
        ".audit-sandbox",
        "source-route-db",
        "duckdb",
        "quant_monitor.duckdb",
    )

    revision = write_activation_overlay(
        sandbox,
        source_id=_P_MACRO_SOURCE,
        data_domain=_P_MACRO_DOMAIN,
        operation=_P_MACRO_OPERATION,
        enabled=True,
        reason="[sandbox] enable fred for G1-02 ask-activation proof",
        changed_by="test_activation_overlay",
        sandbox=True,
    )
    assert revision

    allowed = ask_activation(
        sandbox,
        source_id=_P_MACRO_SOURCE,
        data_domain=_P_MACRO_DOMAIN,
        operation=_P_MACRO_OPERATION,
    )
    assert allowed.is_allowed is True
    assert allowed.overlay_revision == revision

    denied = ask_activation(
        product,
        source_id=_P_MACRO_SOURCE,
        data_domain=_P_MACRO_DOMAIN,
        operation=_P_MACRO_OPERATION,
    )
    assert denied.is_allowed is False
    assert denied.reason_code == "DISABLED_SOURCE"


def test_overlayEnabledFalse_deniesEvenWhenBaseEnabled(tmp_path: Path) -> None:
    """覆盖范围：overlay.enabled=false 覆盖基础启用（禁后门 / 正规拒绝）
    测试对象：write_activation_overlay(enabled=False) + ask_activation（baostock）
    目的/目标：管理员关闭覆盖层必须拒绝，不能靠基础 is_enabled 或内存放行
    验证点：is_allowed False；reason_code=DISABLED_SOURCE；revision 来自 overlay
    失败含义：关闭覆盖无效，或存在 force_enable 式旁路
    """
    sandbox = _migrated_synced_db(
        tmp_path,
        ".audit-sandbox",
        "source-route-db",
        "duckdb",
        "quant_monitor.duckdb",
    )
    before = ask_activation(
        sandbox,
        source_id=_P_DAILY_SOURCE,
        data_domain=_P_DAILY_DOMAIN,
        operation=_P_DAILY_OPERATION,
    )
    assert before.is_allowed is True

    revision = write_activation_overlay(
        sandbox,
        source_id=_P_DAILY_SOURCE,
        data_domain=_P_DAILY_DOMAIN,
        operation=_P_DAILY_OPERATION,
        enabled=False,
        reason="[sandbox] admin disable baostock for ask-activation deny proof",
        changed_by="test_activation_overlay",
        sandbox=True,
    )
    after = ask_activation(
        sandbox,
        source_id=_P_DAILY_SOURCE,
        data_domain=_P_DAILY_DOMAIN,
        operation=_P_DAILY_OPERATION,
    )
    assert after.is_allowed is False
    assert after.reason_code == "DISABLED_SOURCE"
    assert after.overlay_revision == revision


def test_writeSandboxOverlay_requiresSandboxMarker(tmp_path: Path) -> None:
    """覆盖范围：沙箱 overlay 必须标明用途（ADR-018）
    测试对象：write_activation_overlay(sandbox=True, reason 无 sandbox 字样)
    目的/目标：sandbox=True 时拒绝未标明沙箱用途的写入
    验证点：raises ValueError(match=sandbox)
    失败含义：测试可写无标记 overlay，证据档位无法区分沙箱与产品
    """
    sandbox = _migrated_synced_db(
        tmp_path,
        ".audit-sandbox",
        "source-route-db",
        "duckdb",
        "quant_monitor.duckdb",
    )
    with pytest.raises(ValueError, match="sandbox"):
        write_activation_overlay(
            sandbox,
            source_id=_P_MACRO_SOURCE,
            data_domain=_P_MACRO_DOMAIN,
            operation=_P_MACRO_OPERATION,
            enabled=True,
            reason="enable fred without purpose mark",
            changed_by="test_activation_overlay",
            sandbox=True,
        )


def test_migrationCreatesSourceActivationOverlayTable() -> None:
    """覆盖范围：§5.2.1 表形随迁移落地
    测试对象：apply_migrations → source_activation_overlay
    目的/目标：新库应有 design 规定的 overlay 表（字段可写）
    验证点：表存在；可插入含 revision 的一行；017 记入 schema_version
    失败含义：问开关无持久化载体，只能退回内存 OVERRIDE
    """
    con = duckdb.connect(":memory:")
    applied = apply_migrations(con)
    assert "017_source_activation_overlay" in applied
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    assert "source_activation_overlay" in tables
    con.execute(
        """
        INSERT INTO source_activation_overlay (
            overlay_id, source_id, data_domain, operation, enabled,
            reason, changed_by, changed_at, revision
        ) VALUES (
            'ov-1', 'fred', 'macro_series', 'fetch_macro_series', true,
            '[sandbox] probe', 'test', CURRENT_TIMESTAMP, 'rev-1'
        )
        """
    )
    row = con.execute(
        "SELECT revision FROM source_activation_overlay WHERE overlay_id='ov-1'"
    ).fetchone()
    assert row[0] == "rev-1"
