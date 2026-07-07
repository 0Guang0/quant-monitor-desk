from __future__ import annotations

from pathlib import Path

from backend.app.core.resource_guard import Decision, ResourceGuard, ResourceSnapshot
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.service import DataSourceService, ResourceGuardBlockedError
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.event_payload import parse_event_payload
from backend.app.sync.jobs import SyncJobSpec, SyncJobStateMachine


def test_dataSourceService_resourceGuardPausedRoutePlan_writesBlockedRouteGrade(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """覆盖范围：ResourceGuard 阻断后的 route_grade 字段（事件序列与 fetch_log 见 test_serviceGuardBlocked_emitsResourceGuardPausedRoutePlan）
    测试对象：DataSourceService.fetch + job_event_log ROUTE_PLAN payload
    目的/目标：资源阻断必须把 route_grade 改为 blocked，不能沿用阻断前 READY 的 primary
    验证点：第二条 ROUTE_PLAN route_status=RESOURCE_GUARD_PAUSED 且 route_grade=blocked；不断言 fetch_log
    失败含义：容量阻断会在验收报告中伪装成 primary 路由，误导生产等价验收
    """
    snap = ResourceSnapshot(
        available_memory_gb=0.1,
        disk_free_gb=0.1,
        process_rss_mb=100.0,
        project_size_gb=0.1,
    )

    def _hard_stop(self):
        return Decision.HARD_STOP, "available memory below threshold"

    monkeypatch.setattr(ResourceGuard, "snapshot", lambda self: snap)
    monkeypatch.setattr(ResourceGuard, "check", _hard_stop)

    db = tmp_path / "guard.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    jobs = SyncJobStateMachine(cm)
    reg = SourceRegistry()
    reg.load()
    service = DataSourceService(source_registry=reg, data_root=tmp_path / "raw", job_events=jobs)
    spec = SyncJobSpec(
        run_id="run-guard-grade",
        job_id="job-guard-grade",
        job_type="incremental",
        data_domain="cn_equity_daily_bar",
        market_id="CN_A",
        source_id="baostock",
        adapter_id="baostock",
        date_start=None,
        date_end=None,
        instrument_id="000001",
        partition_key=None,
        trigger_reason=None,
    )
    job_id = jobs.create_job(spec)
    req = FetchRequest(
        run_id="run-guard-grade",
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
    )

    with cm.writer() as con:
        try:
            service.fetch(req, con=con, job_id=job_id)
        except ResourceGuardBlockedError:
            pass
        else:
            raise AssertionError("expected ResourceGuardBlockedError")

    with cm.writer() as con:
        rows = con.execute(
            """
            SELECT payload_json FROM job_event_log
            WHERE job_id = ? AND event_type = 'ROUTE_PLAN'
            ORDER BY created_at ASC
            """,
            [job_id],
        ).fetchall()

    assert len(rows) == 2
    first = parse_event_payload(rows[0][0])
    second = parse_event_payload(rows[1][0])
    assert first["route_status"] == "READY"
    assert first["route_grade"] == "primary"
    assert second["route_status"] == "RESOURCE_GUARD_PAUSED"
    assert second["route_grade"] == "blocked"
    assert second.get("selected_source_id") is None
