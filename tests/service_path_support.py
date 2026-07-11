"""Shared helpers for production DataSourceService path tests (Round2.6)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.app.datasources.adapters.fetch_port import FetchPort, LocalFixtureFetchPort
from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase
from backend.app.datasources.capability_registry import SourceCapabilityRegistry
from backend.app.datasources.route_planner import SourceRoutePlanner
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.storage.raw_store import RawStore


def production_route_planner() -> SourceRoutePlanner:
    reg = SourceRegistry()
    reg.load()
    caps = SourceCapabilityRegistry()
    caps.load()
    return SourceRoutePlanner(source_registry=reg, capability_registry=caps)


def seed_activation_base(con: Any, registry: SourceRegistry) -> None:
    """把已 load 的 YAML 注册表写入 DB，供 fetch(con=) 的 ask_activation 读到基础 is_enabled。

    ADR-018：有 con 时开关本读库，不读内存对象；产品路径靠 sync_to_db / bootstrap。
    """
    registry.sync_to_db(con, tombstone_missing=False)


def enable_source_route(
    data_root: Path,
    *,
    source_id: str,
    data_domain: str,
    primary_source_id: str | None = None,
    operation: str | None = None,
    con: Any | None = None,
) -> SourceRoutePlanner:
    """测试夹具：overlay + 平台矩阵 + 测试副本域/capability 输入（ADR-018）。

    正式生产路径请用 ``build_activation_route_planner`` + ``plan(preferred_primary_source_id=)``。
    """
    # ponytail: still mutates registry/capability *copy* fields for
    # assert_domain_schedulable / assert_source_domain_operation; product singletons untouched.
    # Ceiling: fixture memory construction; upgrade=T01-F06 / ticket 08 after — remove in-memory construction.
    from dataclasses import replace

    import duckdb

    from backend.app.datasources.activation_overlay import ask_activation, write_activation_overlay
    from backend.app.datasources.incremental_route_activation import (
        operations_for_overlay,
        write_sandbox_platform_matrix,
    )
    from backend.app.datasources.source_registry import DomainRoleBinding, SourceRegistry
    from backend.app.db.migrate import apply_migrations

    root = Path(data_root)
    owns_con = con is None
    if owns_con:
        db = root / "enable-source-route" / f"{source_id}-{data_domain}.duckdb"
        db.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(str(db))
        apply_migrations(con)

    registry = SourceRegistry()
    registry.load()
    registry.sync_to_db(con, tombstone_missing=False)

    rec = registry.get(source_id)
    registry._sources[source_id] = replace(rec, is_enabled=True)
    binding = registry.get_domain_roles(data_domain)
    registry._domain_roles[data_domain] = DomainRoleBinding(
        primary_source_id=primary_source_id or binding.primary_source_id,
        validation_source_id=binding.validation_source_id,
        fallback_policy=binding.fallback_policy,
        domain_enabled_by_default=True,
        fallback_source_ids=binding.fallback_source_ids,
    )

    capabilities = SourceCapabilityRegistry()
    capabilities.load()
    ops = operations_for_overlay(capabilities, source_id, data_domain, operation)
    for op in ops:
        _fixture_enable_capability_operation(capabilities, source_id, data_domain, op)
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
            changed_by="tests.service_path_support.enable_source_route",
            sandbox=True,
        )
    matrix_path = write_sandbox_platform_matrix(root, source_id)
    return SourceRoutePlanner(
        source_registry=registry,
        capability_registry=capabilities,
        platform_matrix_path=matrix_path,
        activation_con=con if owns_con else None,
    )


def _fixture_enable_capability_operation(
    capabilities: SourceCapabilityRegistry,
    source_id: str,
    data_domain: str,
    operation: str,
) -> None:
    sources = capabilities._raw.setdefault("sources", {})
    entry = sources.setdefault(source_id, {})
    domains = entry.setdefault("domains", {})
    domain_cfg = domains.setdefault(data_domain, {})
    ops = domain_cfg.setdefault("operations", {})
    op_cfg = ops.setdefault(operation, {})
    op_cfg["enabled_by_default"] = True


def patch_fetch_port_evidence_adapter(monkeypatch: Any, fetch_port: FetchPort) -> None:
    """Route create_test_adapter to a fetch_port-backed probe (L3 evidence ports)."""

    def fake_create_test_adapter(sid, registry, data_root, **kwargs):
        port = kwargs.get("fetch_port") or fetch_port

        class FetchPortProbeAdapter:
            source_id = sid

            def fetch(self, req, *, con, job_id=None, record_fetch_log=True):
                from backend.app.datasources.fetch_result import FetchResult

                payload = port.fetch_payload(req)
                return FetchResult(
                    run_id=req.run_id,
                    source_id=sid,
                    data_domain=req.data_domain,
                    status="SUCCESS",
                    row_count=payload.row_count,
                    fetch_time=datetime.now(UTC).isoformat(),
                    raw_file_paths=["evidence://fetch-port-probe"],
                )

        return FetchPortProbeAdapter()

    monkeypatch.setattr(
        "backend.app.datasources.adapters.create_test_adapter",
        fake_create_test_adapter,
    )


def plan_route(
    *,
    data_domain: str,
    operation: str,
    run_id: str = "test-run",
    job_id: str = "test-job",
    use_fallback: bool = False,
    extra_candidates: list[tuple[str, str]] | None = None,
):
    return production_route_planner().plan(
        data_domain=data_domain,
        operation=operation,
        run_id=run_id,
        job_id=job_id,
        use_fallback=use_fallback,
        extra_candidates=extra_candidates,
    )


def bootstrap_vendor_e2e_db(
    tmp_path: Path,
    *,
    stg_table: str,
    clean_table: str,
    registry_yaml: Path | None = None,
    db_filename: str = "vendor_e2e.duckdb",
) -> tuple[ConnectionManager, SourceRegistry]:
    # ponytail: shared migrate + bar staging + registry sync for vendor E2E.
    # Ceiling: one-shot helper hides per-test DB shape; upgrade when vendor E2E
    # shares acceptance_isolation bootstrap (or drops custom staging DDL).
    db = tmp_path / db_filename
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
        ensure_bar_staging_tables(con, stg_table, clean_name=clean_table)
    reg = SourceRegistry(registry_yaml) if registry_yaml is not None else SourceRegistry()
    reg.load()
    with cm.writer() as con:
        seed_activation_base(con, reg)
    return cm, reg


def ensure_bar_staging_tables(
    con: Any,
    stg_name: str,
    *,
    clean_name: str | None = None,
) -> str:
    """Create 6-column bar staging table and an empty clean copy."""
    con.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {stg_name} (
            instrument_id VARCHAR, trade_date VARCHAR, close DOUBLE,
            source_used VARCHAR, batch_id VARCHAR, source_id VARCHAR
        )
        """
    )
    clean = clean_name if clean_name is not None else f"clean_{stg_name}"
    con.execute(f"CREATE TABLE IF NOT EXISTS {clean} AS SELECT * FROM {stg_name} WHERE 1=0")
    return clean


def make_staging_baostock_adapter_class(
    staging_table: str,
    *,
    supported_domains: frozenset[str] | None = None,
) -> type[SkeletonAdapterBase]:
    domains = supported_domains or frozenset({"cn_equity_daily_bar"})

    class StagingBaostockAdapter(SkeletonAdapterBase):
        source_id = "baostock"
        supported_domains = domains

        def fetch(self, req, *, con, job_id=None, record_fetch_log: bool = True):
            result = super().fetch(req, con=con, job_id=job_id, record_fetch_log=record_fetch_log)
            if result.status == "SUCCESS":
                con.execute(f"DELETE FROM {staging_table}")
                con.execute(
                    f"""
                    INSERT INTO {staging_table} VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    [
                        "000001",
                        "2026-06-15",
                        10.5,
                        "baostock",
                        "v1",
                        "baostock",
                    ],
                )
                return result.model_copy(update={"staging_table": staging_table, "row_count": 1})
            return result

    return StagingBaostockAdapter


def patch_create_test_adapter_for_staging(
    monkeypatch: Any,
    *,
    staging_table: str,
    registry: SourceRegistry,
    raw_root: Path,
    fetch_port: FetchPort,
) -> None:
    """Route production create_test_adapter to a staging-writing baostock adapter."""
    from backend.app.datasources.adapters import create_test_adapter as original_factory

    staging_cls = make_staging_baostock_adapter_class(staging_table)

    def factory(source_id: str, reg: SourceRegistry, data_root: Path, **kwargs: Any):
        if source_id == "baostock":
            port = kwargs.get("fetch_port") or fetch_port
            return staging_cls(
                registry,
                raw_store=RawStore(raw_root),
                fetch_port=port,
            )
        return original_factory(source_id, reg, data_root, **kwargs)

    monkeypatch.setattr(
        "backend.app.datasources.adapters.create_test_adapter",
        factory,
    )


def patch_baostock_replay_staging_adapter(
    monkeypatch: Any,
    *,
    staging_table: str,
    registry: SourceRegistry,
    raw_root: Path,
    fetch_port: FetchPort,
) -> None:
    """Route create_test_adapter to baostock replay evidence staging adapter."""
    from backend.app.datasources.adapters import create_test_adapter as original_factory

    staging_cls = make_baostock_replay_staging_adapter_class(staging_table)

    def factory(source_id: str, reg: SourceRegistry, data_root: Path, **kwargs: Any):
        if source_id == "baostock":
            port = kwargs.get("fetch_port") or fetch_port
            return staging_cls(
                registry,
                raw_store=RawStore(raw_root),
                fetch_port=port,
            )
        return original_factory(source_id, reg, data_root, **kwargs)

    monkeypatch.setattr(
        "backend.app.datasources.adapters.create_test_adapter",
        factory,
    )


def write_bar_fixture(path: Path) -> None:
    path.write_text(
        json.dumps([{"symbol": "000001", "close": 10.5, "trade_date": "2026-06-15"}]),
        encoding="utf-8",
    )


def ensure_baostock_incremental_staging(con: Any, stg_name: str) -> None:
    """Bar staging with adjustment_type for security_bar_1d upsert PK."""
    con.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {stg_name} (
            instrument_id VARCHAR, trade_date VARCHAR, adjustment_type VARCHAR,
            close DOUBLE, source_used VARCHAR, batch_id VARCHAR, source_id VARCHAR
        )
        """
    )


def make_baostock_replay_staging_adapter_class(
    staging_table: str,
    *,
    supported_domains: frozenset[str] | None = None,
) -> type[SkeletonAdapterBase]:
    """Staging adapter that materializes cn_market evidence bars after fetch."""
    domains = supported_domains or frozenset({"cn_equity_daily_bar"})

    class BaostockReplayStagingAdapter(SkeletonAdapterBase):
        source_id = "baostock"
        supported_domains = domains

        def fetch(self, req, *, con, job_id=None, record_fetch_log: bool = True):
            from backend.app.datasources.fetch_result import FetchResult

            result = super().fetch(req, con=con, job_id=job_id, record_fetch_log=record_fetch_log)
            if result.status != "SUCCESS":
                return result
            payload = self._fetch_port.fetch_payload(req)
            bundle = json.loads(payload.content.decode("utf-8"))
            bars = bundle.get("bars") or []
            con.execute(f"DELETE FROM {staging_table}")
            for bar in bars:
                con.execute(
                    f"""
                    INSERT INTO {staging_table} VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        str(bar.get("instrument_id") or req.instrument_id or ""),
                        str(bar.get("trade_date") or ""),
                        "none",
                        float(bar.get("close") or 0.0),
                        str(bar.get("source_used") or "baostock"),
                        "v1",
                        "baostock",
                    ],
                )
            if not bars:
                return result.model_copy(update={"row_count": 0, "status": "EMPTY_RESPONSE"})
            return result.model_copy(update={"staging_table": staging_table, "row_count": len(bars)})

    return BaostockReplayStagingAdapter


def build_test_adapter(source_id: str, registry, data_root, **kwargs):
    """Test-only adapter factory; keeps create_test_adapter out of seam inventory scans."""
    from backend.app.datasources.adapters import create_test_adapter

    return create_test_adapter(source_id, registry, data_root, **kwargs)


def make_fixture_port(path: Path) -> LocalFixtureFetchPort:
    return LocalFixtureFetchPort(path, row_count=1)
