"""Phase 1 scheduler production-equivalent acceptance tests."""

from __future__ import annotations

from pathlib import Path

from backend.app.cli import data_commands
from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.db.connection import ConnectionManager
from tests.incremental_baostock_support import SYMBOL
from tests.test_bounded_backfill_cli_e2e import _patch_phase1_baostock_replay


def _p1_root(tmp_path: Path) -> Path:
    root = tmp_path / ".audit-sandbox" / "source-route-db-scheduler"
    root.mkdir(parents=True)
    return root


def test_syncSchedulerAcceptance_dryRunParentChildEnvelope(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：scheduler dry-run parent/child 验收信封
    测试对象：scheduler_run dry_run=True
    目的/目标：profile 展开须产出 parent report 与 child 列表
    验证点：child_reports 存在；gate_eligible=False；status=DRY_RUN
    失败含义：scheduler 仍只是 plan 文本，无统一 AcceptanceReport 聚合
    """
    root = _p1_root(tmp_path)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.scheduler_run(profile="daily_close", dry_run=True)
    assert payload["dry_run"] is True
    assert payload.get("gate_eligible") is False
    assert "child_reports" in payload
    assert isinstance(payload["jobs"], list)
    assert len(payload["jobs"]) >= 1
    assert payload["jobs"][0].get("acceptance_report")


def test_syncSchedulerAcceptance_liveIncrementalChildEnvelope(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：scheduler live incremental child 报告
    测试对象：scheduler_run dry_run=False on source-route-db
    目的/目标：live incremental jobs 关联 child acceptance 字段
    验证点：jobs 含 acceptance_report；parent status 可判定
    失败含义：live scheduler 仍吞掉 child 失败为模糊 FAILED_FINAL
    """
    root = _p1_root(tmp_path)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.scheduler_run(profile="daily_close", dry_run=False)
    assert payload.get("gate_eligible") is True
    assert "child_envelopes" in payload
    incremental_jobs = [j for j in payload["jobs"] if j.get("job_type") == "incremental"]
    assert incremental_jobs
    assert incremental_jobs[0].get("acceptance_report")
    assert incremental_jobs[0]["acceptance_report"]["failure_class"] == "BLOCKED"
    assert incremental_jobs[0]["acceptance_report"]["route_plan_id"] is not None


def test_syncSchedulerAcceptance_liveWeeklyBackfillChildUsesSpineReport(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：weekly_backfill profile live child spine 报告
    测试对象：scheduler_run dry_run=False profile=weekly_backfill
    目的/目标：live backfill/full_load child 须来自 execute_spine_or_binding_live 而非 synthetic
    验证点：backfill child acceptance_report.route_plan_id 非空；缺授权时 failure_class=BLOCKED
    失败含义：scheduler live child 仍为手工 AcceptanceReport(route_plan_id=None)
    """
    root = _p1_root(tmp_path)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.scheduler_run(profile="weekly_backfill", dry_run=False)
    backfill_jobs = [j for j in payload["jobs"] if j.get("job_type") == "backfill"]
    assert backfill_jobs
    report = backfill_jobs[0]["acceptance_report"]
    assert report["route_plan_id"] is not None
    assert report["failure_class"] == "BLOCKED"


def test_syncSchedulerAcceptance_weeklyBackfillLiveFullLoadChildPass(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：weekly_backfill profile live full_load child PASS
    测试对象：scheduler_run profile=weekly_backfill dry_run=False
    目的/目标：scheduler 展开 full_load child 并走 execute_spine_or_binding_live 生产 runner
    验证点：full_load child status=COMPLETED/PASS；acceptance_report.route_plan_id 非空；clean 写入
    失败含义：scheduler full_load 仅 dry-run/BLOCKED，profile 生产调度未闭合
    """
    import json

    root = _p1_root(tmp_path)
    replay = root / "scheduler_full_load_replay.json"
    replay.write_text(
        json.dumps(
            {
                "schema_version": "cn_market_evidence_v1",
                "source_id": "baostock",
                "data_domain": "cn_equity_daily_bar",
                "bars": [
                    {
                        "instrument_id": SYMBOL,
                        "trade_date": "2024-01-10",
                        "open": 1400.0,
                        "high": 1410.0,
                        "low": 1395.0,
                        "close": 1405.0,
                        "volume": 1000000,
                        "source_used": "baostock",
                    }
                ],
                "source_fetch_id": "baostock-replay-scheduler-fl",
                "content_hash": "baostock-replay-hash-scheduler-fl",
                "as_of_timestamp": "2024-01-10T15:00:00Z",
                "retrieved_at": "2024-01-10T15:00:00Z",
                "trade_date": "2024-01-10",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    _patch_phase1_baostock_replay(monkeypatch, replay)
    payload = data_commands.scheduler_run(
        profile="weekly_backfill",
        dry_run=False,
        job_type_filter="full_load",
    )
    full_load_jobs = [j for j in payload["jobs"] if j.get("job_type") == "full_load"]
    assert full_load_jobs
    child = full_load_jobs[0]
    report = child["acceptance_report"]
    assert report["route_plan_id"] is not None
    assert report["status"] == "PASS"
    assert child.get("clean_status") == "WRITTEN"
    job_id = child.get("job_id") or report.get("sync_job_id")
    if job_id:
        db = root / "duckdb" / "quant_monitor.duckdb"
        cm = ConnectionManager(db_path=db)
        with cm.reader() as con:
            rows = con.execute(
                "SELECT COUNT(*) FROM security_bar_1d WHERE instrument_id = ?",
                [SYMBOL],
            ).fetchone()[0]
        assert rows >= 1


def test_syncSchedulerAcceptance_weeklyBackfillLiveBackfillChildPass(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：weekly_backfill profile live backfill child PASS
    测试对象：scheduler_run profile=weekly_backfill dry_run=False job_type_filter=backfill
    目的/目标：scheduler 展开 backfill child 并走 execute_spine_or_binding_live 生产 runner
    验证点：backfill child status=PASS；acceptance_report.route_plan_id 非空；clean 写入
    失败含义：scheduler backfill 仅 dry-run/BLOCKED，profile 生产调度未闭合
    """
    import json

    root = _p1_root(tmp_path)
    replay = root / "scheduler_backfill_replay.json"
    replay.write_text(
        json.dumps(
            {
                "schema_version": "cn_market_evidence_v1",
                "source_id": "baostock",
                "data_domain": "cn_equity_daily_bar",
                "bars": [
                    {
                        "instrument_id": SYMBOL,
                        "trade_date": "2024-01-10",
                        "open": 1400.0,
                        "high": 1410.0,
                        "low": 1395.0,
                        "close": 1405.0,
                        "volume": 1000000,
                        "source_used": "baostock",
                    }
                ],
                "source_fetch_id": "baostock-replay-scheduler-bf",
                "content_hash": "baostock-replay-hash-scheduler-bf",
                "as_of_timestamp": "2024-01-10T15:00:00Z",
                "retrieved_at": "2024-01-10T15:00:00Z",
                "trade_date": "2024-01-10",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    _patch_phase1_baostock_replay(monkeypatch, replay)
    payload = data_commands.scheduler_run(
        profile="weekly_backfill",
        dry_run=False,
        job_type_filter="backfill",
    )
    backfill_jobs = [j for j in payload["jobs"] if j.get("job_type") == "backfill"]
    assert backfill_jobs
    child = backfill_jobs[0]
    report = child["acceptance_report"]
    assert report["route_plan_id"] is not None
    assert report["status"] == "PASS"
    assert child.get("clean_status") == "WRITTEN"
    job_id = child.get("job_id") or report.get("sync_job_id")
    if job_id:
        db = root / "duckdb" / "quant_monitor.duckdb"
        cm = ConnectionManager(db_path=db)
        with cm.reader() as con:
            rows = con.execute(
                "SELECT COUNT(*) FROM security_bar_1d WHERE instrument_id = ?",
                [SYMBOL],
            ).fetchone()[0]
        assert rows >= 1


def test_syncSchedulerAcceptance_childDryRunCarriesRouteEvidence(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：scheduler child dry-run route 证据
    测试对象：scheduler_run child envelope observability_evidence
    目的/目标：child report 须含 route_plan_id，不能只有 job status
    验证点：首个 child observability_evidence.route_plan_id 非空
    失败含义：scheduler child 仍是 synthetic status 包装，无 route/fetch 证据
    """
    root = _p1_root(tmp_path)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.scheduler_run(profile="daily_close", dry_run=True)
    child = payload["jobs"][0]
    obs = child.get("observability_evidence") or {}
    assert obs.get("route_plan_id") is not None
    assert child["acceptance_report"].get("route_plan_id") is not None


def test_syncSchedulerAcceptance_resourceGuardPauseSkipsNonCoreWithEvidence(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：ResourceGuard 暂停非核心任务证据
    测试对象：scheduler_run live + PAUSE decision
    目的/目标：non-core revision_audit 被跳过时 parent 保留 guard 决策与原因
    验证点：skipped_non_core=True；resource_guard_decision=PAUSE；revision_audit SKIPPED
    失败含义：ResourceGuard 跳过不可审计，运维无法解释为何缺 revision_audit
    """
    root = _p1_root(tmp_path)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    monkeypatch.setattr(
        ResourceGuard, "check", lambda self: (Decision.PAUSE, "cpu threshold")
    )
    payload = data_commands.scheduler_run(profile="daily_close", dry_run=False)
    assert payload.get("skipped_non_core") is True
    assert payload.get("resource_guard_decision") == "PAUSE"
    revision_jobs = [j for j in payload["jobs"] if j.get("job_type") == "revision_audit"]
    assert revision_jobs
    assert revision_jobs[0]["status"] == "SKIPPED"
    assert payload["observability_evidence"].get("resource_guard_decision") == "PAUSE"


def test_syncSchedulerAcceptance_weeklyBackfillProfileHasWindowSemantics(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：weekly_backfill profile 窗口语义
    测试对象：sync_scheduler_profiles.yaml weekly_backfill
    目的/目标：backfill/full_load profile entry 必须有 date_start/date_end
    验证点：weekly_backfill dry-run 展开 backfill/full_load 且含 window 字段
    失败含义：scheduler 无 backfill/full_load window profile 样例，P1 证据不足
    """
    root = _p1_root(tmp_path)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.scheduler_run(profile="weekly_backfill", dry_run=True)
    backfill_jobs = [j for j in payload["jobs"] if j.get("job_type") == "backfill"]
    full_load_jobs = [j for j in payload["jobs"] if j.get("job_type") == "full_load"]
    assert backfill_jobs
    assert full_load_jobs
    assert backfill_jobs[0].get("window", {}).get("date_start")
    assert backfill_jobs[0].get("window", {}).get("date_end")
