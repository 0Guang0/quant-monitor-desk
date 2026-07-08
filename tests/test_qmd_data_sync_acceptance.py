"""Phase 1 sync CLI production-equivalent acceptance tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from backend.app.cli import data_commands
from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.db.connection import ConnectionManager
from tests.incremental_baostock_support import SYMBOL


def _p1_root(tmp_path: Path) -> Path:
    root = tmp_path / ".audit-sandbox" / "source-route-db-sync"
    root.mkdir(parents=True)
    return root


def test_qmdData_syncAcceptance_dryRunEnvelopeNonGate(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：sync dry-run 验收信封
    测试对象：sync_incremental_by_source_id dry_run=True
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
    验证点：incremental_evidence 含 watermark_before；observability route_plan_id 非空
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
    assert "watermark_before" in incremental
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
    assert incremental.get("watermark_after") is not None
    obs = payload.get("observability_evidence") or {}
    assert obs.get("route_plan_persistence") == "job_event_log"
    assert obs.get("route_plan_id")


def test_qmdData_syncAcceptance_livePassRepeatRunIdempotent(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：official sync 重复运行幂等
    测试对象：sync_plan cn_equity_daily_bar live 两次
    目的/目标：重复增量同步不产生重复 clean 主键写入
    验证点：二次运行后 security_bar_1d 行数不增；watermark_after 保持或前进
    失败含义：增量 sync 缺幂等，重复跑会堆重复行
    """
    root = _p1_root(tmp_path)
    replay = root / "sync_replay_idem.json"
    _write_sync_incremental_replay(replay)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    _patch_baostock_matrix_replay(monkeypatch, replay)
    kwargs = dict(
        data_domain="cn_equity_daily_bar",
        dry_run=False,
        instrument_id=SYMBOL,
    )
    payload1 = data_commands.sync_plan(**kwargs)
    assert payload1["acceptance_report"]["status"] == "PASS"
    watermark_after_first = (payload1.get("incremental_evidence") or {}).get("watermark_after")
    db = root / "duckdb" / "quant_monitor.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.reader() as con:
        rows_after_first = con.execute(
            "SELECT COUNT(*) FROM security_bar_1d WHERE instrument_id = ?",
            [SYMBOL],
        ).fetchone()[0]
    payload2 = data_commands.sync_plan(**kwargs)
    assert payload2["acceptance_report"]["status"] == "PASS"
    with cm.reader() as con:
        rows_after_second = con.execute(
            "SELECT COUNT(*) FROM security_bar_1d WHERE instrument_id = ?",
            [SYMBOL],
        ).fetchone()[0]
    assert rows_after_second == rows_after_first
    watermark_after_second = (payload2.get("incremental_evidence") or {}).get("watermark_after")
    assert watermark_after_second is not None
    if watermark_after_first is not None:
        assert watermark_after_second >= watermark_after_first
