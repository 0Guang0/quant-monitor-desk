"""Phase 1 sync CLI production-equivalent acceptance tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

from backend.app.cli import data_commands
from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.db.connection import ConnectionManager
from backend.app.sync.jobs import SyncJobResult
from tests.incremental_baostock_support import SYMBOL
from tests.test_bounded_backfill_cli_e2e import (
    END,
    START,
    _patch_phase1_baostock_replay,
    _write_two_shard_replay,
)


def _p1_root(tmp_path: Path) -> Path:
    root = tmp_path / ".audit-sandbox" / "source-route-db-sync"
    root.mkdir(parents=True)
    return root


def test_qmdData_syncAcceptance_dryRunEnvelopeNonGate(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：sync dry-run 验收信封
    测试对象：sync_tier_a_by_source_id dry_run=True
    目的/目标：dry-run 必须附带 acceptance 字段且 gate_eligible=false
    验证点：acceptance_report 存在；gate_eligible=False；status=DRY_RUN
    失败含义：sync dry-run 无统一验收形状或误计 P1-GATE
    """
    root = _p1_root(tmp_path)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.sync_plan(
        data_domain="macro_series",
        source_id="fred",
        dry_run=True,
    )
    assert payload["dry_run"] is True
    assert payload.get("gate_eligible") is False
    assert "acceptance_report" in payload
    assert payload["status"] == "DRY_RUN"


def test_qmdData_syncAcceptance_sourceRouteDbLiveWithoutAuthBlocked(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：source-route-db live sync 缺授权诚实阻断
    测试对象：run_phase1_sync_live via sync_plan
    目的/目标：live 缺 QMD_ALLOW_LIVE_FETCH 时输出 BLOCKED 验收报告，非假 PASS
    验证点：gate_eligible=True；failure_class=BLOCKED；acceptance_report_path 存在
    失败含义：无授权 live 被当作成功或未产出结构化报告
    """
    root = _p1_root(tmp_path)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.sync_plan(
        data_domain="macro_series",
        source_id="fred",
        dry_run=False,
    )
    assert payload.get("gate_eligible") is True
    report = payload["acceptance_report"]
    assert report["failure_class"] == "BLOCKED"
    assert payload.get("acceptance_report_path")
    assert Path(payload["acceptance_report_path"]).is_file()


def test_qmdData_syncAcceptance_cliEnvRootIsNotSelfRejected(tmp_path: Path) -> None:
    """覆盖范围：真实 CLI 启动时 QMD_DATA_ROOT 指向 source-route-db 验收根
    测试对象：backend.app.cli.main subprocess + live sync 验收隔离检查
    目的/目标：正式 CLI 入口必须接受生产等价隔离根，而不是把 env 根误判为主库
    验证点：命令 exit 0；gate_eligible=True；缺 live 授权时诚实 BLOCKED
    失败含义：P1-GATE 只能通过 qmd_ops 参数路径，正式 qmd-data live 入口无法验收
    """
    root = _p1_root(tmp_path)
    env = os.environ.copy()
    env["QMD_DATA_ROOT"] = str(root)
    env["QMD_ALLOW_LIVE_FETCH"] = "0"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "backend.app.cli.main",
            "data",
            "sync",
            "--domain",
            "macro_series",
            "--source-id",
            "fred",
            "--no-dry-run",
            "--format",
            "json",
        ],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["gate_eligible"] is True
    assert payload["acceptance_report"]["failure_class"] == "BLOCKED"


def test_qmdData_syncAcceptance_liveBlockedShowsIncrementalWatermarkEvidence(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：sync live 缺授权时的增量证据
    测试对象：run_phase1_sync_live envelope incremental_evidence
    目的/目标：BLOCKED 报告仍须暴露 cursor/watermark 与 route_plan 可追溯证据
    验证点：incremental_evidence 含 cursor_before；observability route_plan_id 非空
    失败含义：sync 验收只有 failure_class，无法证明 incremental 路径已规划
    """
    root = _p1_root(tmp_path)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.sync_plan(
        data_domain="macro_series",
        source_id="fred",
        dry_run=False,
    )
    incremental = payload.get("incremental_evidence") or {}
    assert "cursor_before" in incremental
    assert incremental.get("pipeline_path")
    obs = payload.get("observability_evidence") or {}
    assert obs.get("route_plan_id") is not None
    assert payload["acceptance_report"]["route_plan_id"] is not None


def test_qmdData_syncAcceptance_dryRunTierAShowsWatermarkWindow(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：Tier A sync dry-run 增量窗口
    测试对象：sync_tier_a dry-run incremental_evidence
    目的/目标：dry-run 须展示 watermark 驱动的待更新窗口，证明 incremental 语义
    验证点：incremental_evidence 含 window_date_start/window_date_end
    失败含义：sync dry-run 无 watermark 窗，incremental 能力不可审计
    """
    root = _p1_root(tmp_path)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.sync_plan(
        data_domain="macro_series",
        source_id="fred",
        dry_run=True,
        end="2024-06-30",
    )
    incremental = payload.get("incremental_evidence") or {}
    assert incremental.get("window_date_start") is not None
    assert incremental.get("window_date_end") is not None


def _write_sync_incremental_replay(path: Path) -> None:
    from datetime import UTC, date, datetime, timedelta

    trade_date = (datetime.now(UTC).date() - timedelta(days=5)).isoformat()
    payload = {
        "schema_version": "cn_market_evidence_v1",
        "source_id": "baostock",
        "data_domain": "cn_equity_daily_bar",
        "bars": [
            {
                "instrument_id": SYMBOL,
                "trade_date": trade_date,
                "open": 1400.0,
                "high": 1410.0,
                "low": 1395.0,
                "close": 1405.0,
                "volume": 1000000,
                "source_used": "baostock",
            }
        ],
        "source_fetch_id": "baostock-replay-sync-e2e",
        "content_hash": "baostock-replay-hash-sync-e2e",
        "as_of_timestamp": f"{trade_date}T15:00:00Z",
        "retrieved_at": f"{trade_date}T15:00:00Z",
        "trade_date": trade_date,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _patch_baostock_matrix_replay(monkeypatch, replay_path: Path) -> None:
    from backend.app.ops import baostock_incremental_run
    from backend.app.datasources.fetch_ports.baostock_port import BaostockMockFetchPort
    from backend.app.datasources.service import DataSourceService

    def _build(*, data_root, symbol, job_events, use_mock=None):
        port = BaostockMockFetchPort(symbols=(symbol,), max_rows=500, replay_path=replay_path)
        return DataSourceService(data_root=data_root, fetch_port=port, job_events=job_events)

    monkeypatch.setattr(baostock_incremental_run, "build_baostock_incremental_service", _build)


def test_qmdData_syncAcceptance_livePassReplayFetchCleanWriteAndCursor(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：official sync live PASS 产品路径
    测试对象：sync_plan cn_equity_daily_bar live + matrix baostock handler
    目的/目标：QMD_ALLOW_LIVE_FETCH=1 时真实 fetch→staging→validation→write→cursor 可追溯
    验证点：status=PASS；write_grade=primary_grade_clean；clean_status=WRITTEN；route_plan_id 非空
    失败含义：sync 仅有 dry-run/BLOCKED 证据，无法证明增量生产链路在 official CLI 跑通
    """
    root = _p1_root(tmp_path)
    replay = root / "sync_replay.json"
    _write_sync_incremental_replay(replay)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    _patch_baostock_matrix_replay(monkeypatch, replay)
    payload = data_commands.sync_plan(
        data_domain="cn_equity_daily_bar",
        dry_run=False,
        instrument_id=SYMBOL,
    )
    report = payload["acceptance_report"]
    assert payload.get("gate_eligible") is True
    assert report["status"] == "PASS"
    assert report["write_grade"] == "primary_grade_clean"
    assert report["route_plan_id"] is not None
    assert payload["clean_status"] == "WRITTEN"
    incremental = payload.get("incremental_evidence") or {}
    assert incremental.get("pipeline_path")
    assert payload["observability_evidence"].get("route_plan_persistence") == "job_event_log"


def test_qmdData_backfillAcceptance_liveSevereConflictBlocksOfficialCleanWrite(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：official backfill severe conflict 阻断 clean write
    测试对象：data_commands.backfill_plan live envelope
    目的/目标：严重冲突须在 official path 产品可见且阻断 clean 写入
    验证点：conflict_status=SEVERE_CONFLICT；clean_status=NOT_RUN；failure_class=FAIL
    失败含义：低层 orchestrator 测绿但 qmd-data 路径仍显示可写 clean
    """
    from backend.app.cli import phase1_acceptance

    root = _p1_root(tmp_path)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))

    def _severe_shard_job(
        request,
        job_type,
        *,
        orch,
        service,
        date_start,
        date_end,
        instrument_id,
        trigger_reason,
    ):
        job_id = f"job-p1-severe-{uuid.uuid4().hex[:8]}"
        with orch._cm.writer() as con:
            con.execute(
                """
                INSERT INTO data_sync_job (
                    job_id, run_id, job_type, status, data_domain, market_id, source_id,
                    validation_report_id, conflict_report_id, created_at, updated_at
                ) VALUES (?, ?, ?, 'WAITING_RECONCILE', ?, 'CN_A', ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                [
                    job_id,
                    f"run-{job_id}",
                    job_type,
                    request.data_domain,
                    request.source_id,
                    "vr-severe-1",
                    "cr-severe-1",
                ],
            )
        return SyncJobResult(
            job_id=job_id,
            status="WAITING_RECONCILE",
            validation_report_id="vr-severe-1",
            conflict_report_id="cr-severe-1",
            message="severe multi-source conflict",
        )

    monkeypatch.setattr(phase1_acceptance, "_run_shard_job_without_binding", _severe_shard_job)
    payload = data_commands.backfill_plan(
        data_domain="cn_equity_daily_bar",
        source_id="baostock",
        start=START,
        end=END,
        max_shards=2,
        dry_run=False,
    )
    report = payload["acceptance_report"]
    assert report["conflict_status"] == "SEVERE_CONFLICT"
    assert payload["clean_status"] == "NOT_RUN"
    assert payload["write_status"] == "NOT_RUN"
    assert report["status"] == "FAIL"


def test_qmdData_backfillAcceptance_liveDegradedCleanWriteOfficialPath(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：official backfill degraded clean 写入
    测试对象：data_commands.backfill_plan + WriteManager fallback 审计
    目的/目标：FallbackPolicy 授权降级写入须在 official CLI 报告 degraded_clean
    验证点：write_grade=degraded_clean；source_switched=True；clean_status=WRITTEN
    失败含义：仅有信封字段单测，无真实 WriteManager 经 official path 的降级写入证据
    """
    from dataclasses import replace

    from backend.app.db.write_manager import WriteManager

    root = tmp_path / ".audit-sandbox" / "source-route-db-sync-degraded"
    root.mkdir(parents=True)
    replay = root / "backfill_degraded_replay.json"
    _write_two_shard_replay(replay)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    _patch_phase1_baostock_replay(monkeypatch, replay)

    original_write = WriteManager.write

    def _degraded_write(self, request, *, con=None, own_transaction=True):
        request = replace(
            request,
            source_role="fallback",
            source_switched=True,
            quality_flags=("SOURCE_FALLBACK_USED",),
            fallback_reason="primary_rate_limited",
        )
        return original_write(self, request, con=con, own_transaction=own_transaction)

    monkeypatch.setattr(WriteManager, "write", _degraded_write)
    payload = data_commands.backfill_plan(
        data_domain="cn_equity_daily_bar",
        source_id="baostock",
        start=START,
        end=END,
        max_shards=2,
        dry_run=False,
    )
    report = payload["acceptance_report"]
    assert report["write_grade"] == "degraded_clean"
    assert report["source_switched"] is True
    assert payload["clean_status"] == "WRITTEN"
    assert payload["observability_evidence"]["write_grade"] == "degraded_clean"
