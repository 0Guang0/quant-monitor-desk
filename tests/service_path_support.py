"""Shared helpers for production DataSourceService path tests (Round2.6)."""

from __future__ import annotations

import json
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
    """ponytail: migrate + bar staging + registry sync once per vendor E2E test."""
    db = tmp_path / db_filename
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
        ensure_bar_staging_tables(con, stg_table, clean_name=clean_table)
    reg = SourceRegistry(registry_yaml) if registry_yaml is not None else SourceRegistry()
    reg.load()
    with cm.writer() as con:
        reg.sync_to_db(con, tombstone_missing=False)
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


def write_bar_fixture(path: Path) -> None:
    path.write_text(
        json.dumps([{"symbol": "000001", "close": 10.5, "trade_date": "2026-06-15"}]),
        encoding="utf-8",
    )


def make_fixture_port(path: Path) -> LocalFixtureFetchPort:
    return LocalFixtureFetchPort(path, row_count=1)
