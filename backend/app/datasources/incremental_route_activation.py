"""增量 / 金路径沙箱启用助手（ADR-018 · G1-02 票 06/07）。

功能：在隔离数据根（``.audit-sandbox``）写入正规 overlay，并构造本机平台矩阵夹具，
供 CLI 回补预览、增量验收与产品路径同参同拒绝。

业务价值：沙箱可 READY 证明启用接缝；产品默认库不会因旧 ESR 假开。

退役/清理：G1-02 关账且管理员写 overlay 的产品 CLI 落地后，可评估是否仍需
「dry-run 自动写沙箱 overlay」；若仅测试夹具需要，迁回 tests/service_path_support。

Standards：本模块**禁止**改 registry/capability 内存副本；副本构造仅允许在
``tests/service_path_support.enable_source_route``（T01-F06）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.app.datasources.activation_overlay import ask_activation, write_activation_overlay
from backend.app.datasources.capability_registry import SourceCapabilityRegistry
from backend.app.datasources.source_registry import SourceRegistry


def is_audit_sandbox_data_root(data_root: Path | str) -> bool:
    # 路径段精确匹配，禁止 `foo.audit-sandbox-backup` 子串误放行
    return any(part == ".audit-sandbox" for part in Path(data_root).parts)


def load_plain_source_registry() -> SourceRegistry:
    """加载未改写的 SourceRegistry（启用只靠 overlay / plan(con=)）。"""
    registry = SourceRegistry()
    registry.load()
    return registry


def write_sandbox_platform_matrix(data_root: Path, source_id: str) -> Path:
    """在沙箱根下写平台矩阵夹具：本机 platform 放行该源（输入构造，非 setattr）。"""
    import platform as py_platform

    import yaml

    from backend.app.datasources.route_planner import SourceRoutePlanner

    base = yaml.safe_load(SourceRoutePlanner.DEFAULT_MATRIX.read_text(encoding="utf-8")) or {}
    plat = py_platform.system().lower()
    key = "windows" if plat == "windows" else "macos" if plat == "darwin" else "linux"
    platforms = base.setdefault("platforms", {})
    entry = platforms.setdefault(key, {})
    entry[source_id] = {
        "available_if_user_configured": True,
        "default_enabled": True,
    }
    path = Path(data_root) / "platform-matrix" / f"platform-matrix-{source_id}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(base, allow_unicode=True), encoding="utf-8")
    return path


def ensure_sandbox_route_activation(
    con: Any,
    *,
    data_root: Path,
    source_id: str,
    data_domain: str,
    operation: str,
) -> Path | None:
    """沙箱根：sync 基础注册表 + 写 overlay（若尚未允许）+ 平台矩阵。

    非 ``.audit-sandbox`` 根：不写任何东西，返回 None（产品默认保持诚实关闭）。
    """
    root = Path(data_root)
    if not is_audit_sandbox_data_root(root):
        return None

    registry = load_plain_source_registry()
    registry.sync_to_db(con, tombstone_missing=False)

    caps = SourceCapabilityRegistry()
    caps.load()
    ops = operations_for_overlay(caps, source_id, data_domain, operation)
    for op in ops:
        decision = ask_activation(
            con,
            source_id=source_id,
            data_domain=data_domain,
            operation=op,
        )
        if decision.is_allowed:
            continue
        write_activation_overlay(
            con,
            source_id=source_id,
            data_domain=data_domain,
            operation=op,
            enabled=True,
            reason=f"[sandbox] enable {source_id} for {data_domain}/{op}",
            changed_by="datasources.incremental_route_activation",
            sandbox=True,
        )
    return write_sandbox_platform_matrix(root, source_id)


def prepare_audit_sandbox_route_activation(
    data_root: Path,
    *,
    source_id: str,
    data_domain: str,
    operation: str,
) -> Path | None:
    """在 ``QMD_DATA_ROOT`` 的 quant_monitor.duckdb 写正规 overlay + 平台矩阵。

    供 sync dry-run / CLI 测试显式启用（**不**在 dry-run 路径静默调用，以保留
    「未启用源 fail-closed」反证）。
    """
    from backend.app.db.connection import ConnectionManager
    from backend.app.db.migrate import apply_migrations

    root = Path(data_root)
    if not is_audit_sandbox_data_root(root):
        raise ValueError(
            f"prepare_audit_sandbox_route_activation requires .audit-sandbox root; got {root}"
        )
    db = root / "duckdb" / "quant_monitor.duckdb"
    db.parent.mkdir(parents=True, exist_ok=True)
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
        return ensure_sandbox_route_activation(
            con,
            data_root=root,
            source_id=source_id,
            data_domain=data_domain,
            operation=operation,
        )


def build_activation_route_planner(
    *,
    platform_matrix_path: Path | None = None,
    activation_con: Any | None = None,
):
    """正式路径：干净 registry/capability + 可选平台矩阵 / activation_con。

    不改内存副本。钉非 YAML primary 源请用 ``plan(preferred_primary_source_id=)``。
    """
    from backend.app.datasources.route_planner import SourceRoutePlanner

    registry = load_plain_source_registry()
    capabilities = SourceCapabilityRegistry()
    capabilities.load()
    return SourceRoutePlanner(
        source_registry=registry,
        capability_registry=capabilities,
        platform_matrix_path=platform_matrix_path,
        activation_con=activation_con,
    )


def plan_with_preferred_primary(
    *,
    source_id: str,
    data_domain: str,
    operation: str,
    con: Any | None = None,
    platform_matrix_path: Path | None = None,
    run_id: str = "preview-run",
    job_id: str = "preview-job",
):
    """干净 planner + preferred_primary（CLI sync/backfill 预览共用）。"""
    planner = build_activation_route_planner(
        platform_matrix_path=platform_matrix_path,
    )
    return planner.plan(
        data_domain=data_domain,
        operation=operation,
        run_id=run_id,
        job_id=job_id,
        con=con,
        preferred_primary_source_id=source_id,
    )


def operations_for_overlay(
    capabilities: SourceCapabilityRegistry,
    source_id: str,
    data_domain: str,
    operation: str | None,
) -> list[str]:
    if operation:
        return [operation]
    domain_cfg = ((capabilities.sources.get(source_id) or {}).get("domains") or {}).get(
        data_domain
    ) or {}
    ops_map = domain_cfg.get("operations") or {}
    if ops_map:
        return sorted(ops_map)
    # default_operation_for_domain 恒有回落，不再 bare-except
    return [capabilities.default_operation_for_domain(data_domain)]
