"""Round2 审计 P1-03 — 厂商 fixture 经真实编排器与服务路径的 E2E 测试。

覆盖范围：LocalFixtureFetchPort → adapter → DataSyncOrchestrator 增量同步全链路写库与审计。
"""

from __future__ import annotations

from pathlib import Path

from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.storage.raw_store import RawStore
from backend.app.sync.jobs import SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator
from tests.service_path_support import (
    bootstrap_vendor_e2e_db,
    make_fixture_port,
    make_staging_baostock_adapter_class,
    write_bar_fixture,
)

FIXTURE_JSON = Path(__file__).parent / "fixtures" / "vendor_bar_fixture.json"
STG_TABLE = "stg_vendor_e2e"
CLEAN_TABLE = "clean_vendor_e2e"


def test_vendorFixtureFetch_e2eOrchestratorPath(
    tmp_path: Path, registry_yaml_fixture: Path, monkeypatch
) -> None:
    """覆盖范围：fixture 经编排器直连 adapter 的增量同步
    测试对象：DataSyncOrchestrator.run_incremental + FixtureStagingAdapter
    目的/目标：验证 fetch_log、validation_report、write_audit_log 与 clean 表各至少一条记录
    验证点：status==COMPLETED；fetch/report/audit 计数≥1；clean 表 1 行
    失败含义：编排器主路径断链会导致 Round2 vendor E2E 门禁失效
    """
    write_bar_fixture(FIXTURE_JSON)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))

    cm, reg = bootstrap_vendor_e2e_db(
        tmp_path,
        stg_table=STG_TABLE,
        clean_table=CLEAN_TABLE,
        registry_yaml=registry_yaml_fixture,
    )

    staging_cls = make_staging_baostock_adapter_class(
        STG_TABLE,
        supported_domains=frozenset({"market_bar_1d"}),
    )
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    adapter = staging_cls(
        reg,
        raw_store=RawStore(raw_root),
        fetch_port=make_fixture_port(FIXTURE_JSON),
    )
    orch = DataSyncOrchestrator(cm)
    spec = SyncJobSpec(
        run_id="run-vendor-e2e",
        job_id="job-vendor-e2e",
        job_type="incremental",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id="baostock",
        date_start=None,
        date_end=None,
        instrument_id="000001",
        partition_key=None,
        trigger_reason=None,
    )
    result = orch.run_incremental(spec, adapter=adapter, clean_table=CLEAN_TABLE)
    assert result.status == "COMPLETED"
    with cm.writer() as con:
        fetch_count = con.execute(
            "SELECT COUNT(*) FROM fetch_log WHERE job_id = ?", ["job-vendor-e2e"]
        ).fetchone()[0]
        report_count = con.execute(
            "SELECT COUNT(*) FROM validation_report WHERE job_id = ?", ["job-vendor-e2e"]
        ).fetchone()[0]
        audit_count = con.execute(
            "SELECT COUNT(*) FROM write_audit_log WHERE job_id = ?", ["job-vendor-e2e"]
        ).fetchone()[0]
        clean_count = con.execute(f"SELECT COUNT(*) FROM {CLEAN_TABLE}").fetchone()[0]
    assert fetch_count >= 1
    assert report_count >= 1
    assert audit_count >= 1
    assert clean_count == 1


def test_vendorFixtureFetch_e2eThroughDataSourceServicePath(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：fixture 经 DataSourceService 注入编排器的增量同步
    测试对象：DataSourceService + DataSyncOrchestrator.run_incremental(datasource_service=...)
    目的/目标：服务路径须写出 ROUTE_PLAN 事件、选中 baostock 并完成校验与落库
    验证点：status==COMPLETED；ROUTE_PLAN payload decision=route_plan 且 selected_source_id=baostock；fetch/report/audit/clean 均达标
    失败含义：生产服务路径与直连 adapter 行为分叉会导致 routing gate 假绿
    """
    from backend.app.datasources.service import DataSourceService
    from backend.app.sync.event_payload import parse_event_payload
    from tests.service_path_support import (
        make_fixture_port,
        patch_create_test_adapter_for_staging,
        write_bar_fixture,
    )

    write_bar_fixture(FIXTURE_JSON)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))

    cm, reg = bootstrap_vendor_e2e_db(
        tmp_path,
        stg_table=STG_TABLE,
        clean_table=CLEAN_TABLE,
        db_filename="vendor_svc_e2e.duckdb",
    )

    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    port = make_fixture_port(FIXTURE_JSON)
    patch_create_test_adapter_for_staging(
        monkeypatch,
        staging_table=STG_TABLE,
        registry=reg,
        raw_root=raw_root,
        fetch_port=port,
    )

    orch = DataSyncOrchestrator(cm)
    service = DataSourceService(
        source_registry=reg,
        data_root=raw_root,
        fetch_port=port,
        job_events=orch._jobs,
    )
    spec = SyncJobSpec(
        run_id="run-vendor-svc",
        job_id="job-vendor-svc",
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
    result = orch.run_incremental(spec, datasource_service=service, clean_table=CLEAN_TABLE)
    assert result.status == "COMPLETED"
    with cm.writer() as con:
        route_row = con.execute(
            """
            SELECT payload_json FROM job_event_log
            WHERE job_id = ? AND event_type = 'ROUTE_PLAN' LIMIT 1
            """,
            [result.job_id],
        ).fetchone()
        fetch_count = con.execute(
            "SELECT COUNT(*) FROM fetch_log WHERE job_id = ?", [result.job_id]
        ).fetchone()[0]
    assert route_row is not None
    payload = parse_event_payload(route_row[0])
    assert payload.get("decision") == "route_plan"
    assert payload.get("selected_source_id") == "baostock"
    assert fetch_count >= 1
    with cm.writer() as con:
        report_count = con.execute(
            "SELECT COUNT(*) FROM validation_report WHERE job_id = ?", [result.job_id]
        ).fetchone()[0]
        audit_count = con.execute(
            "SELECT COUNT(*) FROM write_audit_log WHERE job_id = ?", [result.job_id]
        ).fetchone()[0]
        clean_count = con.execute(f"SELECT COUNT(*) FROM {CLEAN_TABLE}").fetchone()[0]
    assert report_count >= 1
    assert audit_count >= 1
    assert clean_count == 1
