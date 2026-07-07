"""M-G1-03 P1-06′ — BindingSyncExecutor 唯一编排深度模块."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.binding_executor import execute_binding
from backend.app.sync.indicator_binding import load_binding
from tests.fred_macro_incremental_support import insert_axis_observation


def _cm(tmp_path: Path) -> ConnectionManager:
    cm = ConnectionManager(db_path=tmp_path / "exec.duckdb")
    with cm.writer() as con:
        apply_migrations(con)
    return cm


def test_bindingSyncExecutor_executeBinding_onlyOrchestrationPath(tmp_path, monkeypatch) -> None:
    """覆盖范围：binding → SyncJobSpec → orchestrator 唯一路径
    测试对象：backend.app.sync.binding_executor.execute_binding
    目的/目标：live 路径经真实 orchestrator 推进 data_sync_job 到可观测终态
    验证点：dry_run 预览 watermark；live COMPLETED + job 行 status=COMPLETED
    失败含义：executor 未走编排链或 job 行未落库，binding 入口不可审计
    """
    from dataclasses import replace

    from backend.app.core.resource_guard import Decision, ResourceGuard
    from backend.app.datasources.fetch_ports.fred_port import create_fred_fetch_port
    from backend.app.ops.fred_incremental_run import (
        build_fred_incremental_service,
        macro_staging_rows_from_bundle,
    )
    from backend.app.ops.fred_incremental_watermark import (
        enabled_fred_source_registry,
        read_since_dates_for_series,
    )
    from backend.app.ops.macro_incremental_common import (
        macro_incremental_validation_patch,
        macro_staging_adapter_patch,
    )
    from backend.app.sync.orchestrator import DataSyncOrchestrator
    from tests.service_path_support import enable_source_route

    binding = replace(load_binding("ENV-E1-DGS10"), incremental_watermark="DGS10")
    cm = _cm(tmp_path)
    with cm.writer() as con:
        insert_axis_observation(
            con,
            observation_id="obs-env-dgs10",
            indicator_id="DGS10",
            obs_date=date(2026, 6, 10),
        )

    dry = execute_binding(binding, "incremental", dry_run=True, connection_manager=cm)
    assert dry.status == "SKIPPED"
    assert "2026-06-10" in (dry.message or "")
    assert "2026-06-11" in (dry.message or "")

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    enable_source_route(
        monkeypatch, source_id="fred", data_domain="macro_series", primary_source_id="fred"
    )
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
        live = execute_binding(
            binding,
            "incremental",
            dry_run=False,
            connection_manager=cm,
            datasource_service=service,
        )

    assert live.status == "COMPLETED"
    with cm.writer() as con:
        job_row = con.execute(
            "SELECT status FROM data_sync_job WHERE job_id = ?", [live.job_id]
        ).fetchone()
        obs_count = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    assert job_row is not None and job_row[0] == "COMPLETED"
    assert obs_count >= 1
