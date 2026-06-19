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


def make_staging_baostock_adapter_class(staging_table: str) -> type[SkeletonAdapterBase]:
    class StagingBaostockAdapter(SkeletonAdapterBase):
        source_id = "baostock"
        supported_domains = frozenset({"cn_equity_daily_bar"})

        def fetch(self, req, *, con, job_id=None):
            result = super().fetch(req, con=con, job_id=job_id)
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
