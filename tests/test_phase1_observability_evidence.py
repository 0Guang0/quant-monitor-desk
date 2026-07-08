"""Phase 1 R4 observability evidence tests (task-02 R4-OBS slice)."""

from __future__ import annotations


from backend.app.cli.phase1_acceptance import (
    _collect_observability_from_job,
    aggregate_scheduler_parent_report,
    build_acceptance_envelope,
)
from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.datasources.service import DataSourceService
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.ops.source_route_db_acceptance import AcceptanceReport, AcceptanceRequest
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.jobs import SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator
from tests.support.orchestration_flow_fixtures import ensure_batch_d_staging_tables
from tests.service_path_support import (
    ensure_bar_staging_tables,
    make_fixture_port,
    patch_create_test_adapter_for_staging,
    write_bar_fixture,
)


def _p1_root(tmp_path: Path) -> Path:
    root = tmp_path / ".audit-sandbox" / "source-route-db-obs"
    root.mkdir(parents=True)
    return root


def test_phase1Observability_schedulerParent_completedChildrenPass(tmp_path: Path) -> None:
    """覆盖范围：R4-OBS-04 scheduler parent 聚合
    测试对象：aggregate_scheduler_parent_report
    目的/目标：required child 状态为 COMPLETED 时 parent 须为 PASS，不得误标 FAIL
    验证点：两 child status=COMPLETED → parent status=PASS、failure_class=NONE
    失败含义：子任务已完工但总单盖失败章，运维误判整次 scheduler 失败
    """
    root = _p1_root(tmp_path)
    child_envelopes = [
        {
            "job_type": "backfill",
            "required": True,
            "status": "COMPLETED",
            "acceptance_report": {"status": "PASS"},
        },
        {
            "job_type": "full_load",
            "required": True,
            "status": "COMPLETED",
            "acceptance_report": {"status": "PASS"},
        },
    ]
    parent = aggregate_scheduler_parent_report(
        profile="weekly_backfill",
        data_root=root,
        dry_run=False,
        child_envelopes=child_envelopes,
        skipped_non_core=False,
        resource_guard_decision="ok",
    )
    assert parent["status"] == "PASS"
    assert parent["acceptance_report"]["failure_class"] == "NONE"


def test_phase1Observability_collectFromJob_fetchLogStagingHashesDuration(
    tmp_path, registry_yaml_fixture, monkeypatch
) -> None:
    """覆盖范围：R4-OBS-01/02/03 job 级 observability 收集
    测试对象：_collect_observability_from_job
    目的/目标：成功 job 须从 fetch_log/validation_report/job 表回填 raw、staging、指纹与耗时
    验证点：raw_file_ids 非空；staging_table 非空；schema_hash/content_hash 非空；duration_ms>0
    失败含义：official envelope 无法充当可追溯收据，审计须读源码拼证据
    """
    from backend.app.cli import phase1_acceptance

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    monkeypatch.setattr(
        phase1_acceptance,
        "read_watermark_iso",
        lambda *args, **kwargs: "2024-01-01",
    )
    cm = ConnectionManager(db_path=tmp_path / "obs.duckdb")
    with cm.writer() as con:
        apply_migrations(con)
        ensure_batch_d_staging_tables(con)
    orch = DataSyncOrchestrator(cm)
    fixture = tmp_path / "obs_fixture.json"
    write_bar_fixture(fixture)
    reg = SourceRegistry()
    reg.load()
    stg = "stg_obs_evidence"
    with orch._cm.writer() as con:
        ensure_bar_staging_tables(con, stg, clean_name="clean_obs")

    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    port = make_fixture_port(fixture)
    patch_create_test_adapter_for_staging(
        monkeypatch,
        staging_table=stg,
        registry=reg,
        raw_root=raw_root,
        fetch_port=port,
    )
    service = DataSourceService(
        source_registry=reg,
        data_root=raw_root,
        fetch_port=port,
        job_events=orch._jobs,
    )
    spec = SyncJobSpec(
        run_id="run-obs",
        job_id="job-obs",
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
    result = orch.run_incremental(spec, datasource_service=service, clean_table="clean_obs")
    assert result.status == "COMPLETED"

    extra = _collect_observability_from_job(orch._cm, result, route_plan_persisted=True)
    assert extra.get("fetch_log_ids")
    assert extra.get("raw_file_paths")
    assert extra.get("raw_file_ids")
    assert extra.get("staging_table") == stg
    assert (extra.get("rows_staged") or 0) > 0
    assert extra.get("schema_hash")
    assert extra.get("content_hash")
    assert extra.get("duration_ms") is not None
    assert extra["duration_ms"] >= 0


def test_phase1Observability_envelope_livePassStagingAndHashesPresent(tmp_path: Path) -> None:
    """覆盖范围：R4-OBS-01/02/03 envelope 链路状态与 observability 字段
    测试对象：build_acceptance_envelope + _chain_status
    目的/目标：有完整 extra 时 staging/raw 须 PRESENT，observability 指纹与耗时不为 null
    验证点：staging_status=PRESENT；obs.schema_hash/content_hash/duration_ms 非空
    失败含义：成功行收据仍假红或缺指纹，无法关账
    """
    from dataclasses import replace

    request = AcceptanceRequest.from_target("cn_equity_daily_bar:baostock:fetch_daily_bar")
    base = AcceptanceReport.from_route_payload(
        request,
        {
            "route_status": "READY",
            "selected_source_id": "baostock",
            "route_plan_id": "rp-obs-envelope",
            "route_grade": "primary",
        },
    )
    report = replace(
        base,
        status="PASS",
        failure_class="NONE",
        write_grade="primary_grade_clean",
        validation_status="PASSED_PRIMARY",
    )
    extra = {
        "fetch_log_ids": ["fetch-obs-1"],
        "raw_file_paths": ["/data/raw/baostock/abc.json"],
        "raw_file_ids": ["file-obs-1"],
        "staging_table": "stg_foundation_smoke",
        "rows_staged": 3,
        "validation_report_id": "vr-obs-1",
        "validation_run_ids": ["vr-obs-1"],
        "write_id": "write-obs-1",
        "rows_written": 3,
        "schema_hash": "schema-obs-abc",
        "content_hash": "content-obs-def",
        "duration_ms": 1200,
        "route_plan_persisted": True,
    }
    envelope = build_acceptance_envelope(
        report,
        job_kind="sync",
        trigger="test",
        data_root=_p1_root(tmp_path),
        dry_run=False,
        extra=extra,
    )
    assert envelope["staging_status"] == "PRESENT"
    assert envelope["raw_status"] == "PRESENT"
    obs = envelope["observability_evidence"]
    assert obs["raw_file_ids"] == ["file-obs-1"]
    assert obs["staging_table"] == "stg_foundation_smoke"
    assert obs["schema_hash"] == "schema-obs-abc"
    assert obs["content_hash"] == "content-obs-def"
    assert obs["duration_ms"] == 1200
