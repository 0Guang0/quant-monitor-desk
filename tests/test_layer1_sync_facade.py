"""M-G1-03 P1-13 — layer1 sync_indicator facade seam."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.indicator_binding import load_binding
from backend.app.sync.layer1_sync_facade import sync_indicator
from tests.fred_macro_incremental_support import insert_axis_observation


def _cm(tmp_path: Path) -> ConnectionManager:
    cm = ConnectionManager(db_path=tmp_path / "facade.duckdb")
    with cm.writer() as con:
        apply_migrations(con)
    return cm


def test_layer1SyncFacade_syncIndicator_thinWrapperOnly(tmp_path: Path) -> None:
    """覆盖范围：Layer 对外 sync 接缝
    测试对象：backend.app.sync.layer1_sync_facade.sync_indicator
    目的/目标：sync_indicator 应通过绑定 ID 执行 dry-run 增量同步
    验证点：返回 SKIPPED SyncJobResult 且消息含已有观测日期
    失败含义：Layer 须直接懂 SyncJobSpec（违反 AD-MG103-10）
    """
    binding = load_binding("ENV-E1-DGS10")
    assert binding.indicator_id == "ENV-E1-DGS10"

    cm = _cm(tmp_path)
    with cm.writer() as con:
        insert_axis_observation(
            con,
            observation_id="obs-facade-dgs10",
            indicator_id="ENV-E1-DGS10",
            obs_date=date(2026, 6, 10),
        )

    result = sync_indicator(
        "ENV-E1-DGS10",
        "incremental",
        dry_run=True,
        connection_manager=cm,
    )
    assert result.status == "SKIPPED"
    assert result.job_id
    assert "2026-06-10" in (result.message or "")

    with pytest.raises(LookupError, match="unknown indicator_id"):
        sync_indicator("NOT-A-REAL-INDICATOR", "incremental", dry_run=True)


def test_layer1SyncFacade_syncIndicator_nonDryRun_completesIncremental(
    tmp_path: Path, monkeypatch
) -> None:
    """覆盖范围：Layer 对外 sync 非 dry-run 增量路径
    测试对象：sync_indicator(dry_run=False) + execute_binding 金路径
    目的/目标：facade 在提供 datasource_service 时须驱动真实 incremental 编排
    验证点：result.status==COMPLETED；axis_observation 有新增行
    失败含义：Layer 只能 dry-run 预览，无法经 facade 触发真实同步
    """
    from backend.app.core.resource_guard import Decision, ResourceGuard
    from backend.app.datasources.fetch_ports.fred_port import create_fred_fetch_port
    from backend.app.ops.fred_incremental_run import (
        build_fred_incremental_service,
        macro_staging_rows_from_bundle,
    )
    from backend.app.ops.macro_incremental_common import (
        macro_incremental_validation_patch,
        macro_staging_adapter_patch,
    )
    from backend.app.ops.fred_incremental_watermark import (
        enabled_fred_source_registry,
        read_since_dates_for_series,
    )
    from backend.app.sync.indicator_binding import load_binding
    from backend.app.sync.orchestrator import DataSyncOrchestrator
    from dataclasses import replace
    from tests.fred_macro_incremental_support import bootstrap_fred_incremental_db
    from tests.service_path_support import enable_source_route

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    binding = load_binding("ENV-E1-DGS10")
    monkeypatch.setattr(
        "backend.app.sync.layer1_sync_facade.load_binding",
        lambda _indicator_id: replace(binding, incremental_watermark="DGS10"),
    )
    enable_source_route(
        monkeypatch, source_id="fred", data_domain="macro_series", primary_source_id="fred"
    )
    cm = bootstrap_fred_incremental_db(tmp_path)
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    port = create_fred_fetch_port(series_ids=("DGS10",), max_rows=3, use_mock=True)
    orch = DataSyncOrchestrator(cm)

    def _staging_rows(bundle, *, instrument_id: str = "", start_date: str | None = None, **_kwargs):
        return macro_staging_rows_from_bundle(
            bundle,
            series_id=instrument_id or "DGS10",
            start_date=start_date,
        )

    with cm.writer() as con:
        since_by_series = read_since_dates_for_series(con, ("DGS10",))
    service = build_fred_incremental_service(
        data_root=raw_root,
        fetch_port=port,
        since_by_series=since_by_series,
        job_events=orch._jobs,
        source_registry=enabled_fred_source_registry(),
    )
    with macro_staging_adapter_patch(
        source_id="fred",
        data_domain="macro_series",
        fetch_port=port,
        staging_rows_fn=_staging_rows,
    ), macro_incremental_validation_patch():
        result = sync_indicator(
            "ENV-E1-DGS10",
            "incremental",
            dry_run=False,
            connection_manager=cm,
            datasource_service=service,
        )
    assert result.status == "COMPLETED"
    with cm.writer() as con:
        count = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    assert count >= 1
