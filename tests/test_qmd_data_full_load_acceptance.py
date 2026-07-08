"""Phase 1 full-load CLI production-equivalent acceptance tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from backend.app.cli import data_commands
from backend.app.cli.errors import CliFailure
from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.db.connection import ConnectionManager
from tests.incremental_baostock_support import SYMBOL
from tests.test_bounded_backfill_cli_e2e import (
    END,
    START,
    _patch_phase1_baostock_replay,
    _write_two_shard_replay,
)


def _p1_root(tmp_path: Path) -> Path:
    root = tmp_path / ".audit-sandbox" / "source-route-db-full-load"
    root.mkdir(parents=True)
    return root


def test_qmdData_fullLoadAcceptance_macroDomainDryRunNonPilot(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：full-load macro 域 dry-run 非 pilot
    测试对象：full_load_plan macro_series/fred
    目的/目标：full-load 不再硬拒绝非 baostock 组合
    验证点：不再 CAPABILITY_MISSING；gate_eligible=False
    失败含义：full-load 仍停留 cn_equity_daily_bar+baostock pilot
    """
    root = _p1_root(tmp_path)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    monkeypatch.setattr(
        data_commands,
        "route_preview",
        lambda **kwargs: {
            "route_status": "READY",
            "selected_source_id": "fred",
            "route_plan": {"route_plan_id": "route-test"},
        },
    )
    payload = data_commands.full_load_plan(
        data_domain="macro_series",
        source_id="fred",
        start="2024-01-01",
        end="2024-01-31",
        dry_run=True,
    )
    assert payload["dry_run"] is True
    assert payload.get("gate_eligible") is False
    assert "acceptance_report" in payload


def test_qmdData_fullLoadAcceptance_barDomainDryRun(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：full-load bar 域 dry-run
    测试对象：full_load_plan cn_equity_daily_bar/baostock
    目的/目标：bar cold-start 路径可规划且带验收信封
    验证点：shard_count>=1；acceptance_report 存在
    失败含义：bar full-load 规划或信封缺失
    """
    root = _p1_root(tmp_path)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.full_load_plan(
        data_domain="cn_equity_daily_bar",
        source_id="baostock",
        start="2024-01-01",
        end="2024-01-31",
        dry_run=True,
    )
    assert payload["shard_count"] >= 1
    assert "acceptance_report" in payload


def test_qmdData_fullLoadAcceptance_unknownSourceFailsClosed() -> None:
    """覆盖范围：full-load 未知源 fail-closed
    测试对象：full_load_plan 非法 source_id
    目的/目标：无法 live 的源须结构化失败而非 pilot 限制文案
    验证点：CAPABILITY_MISSING
    失败含义：错误仍表现为 pilot 限制，掩盖 registry 缺口
    """
    with pytest.raises(CliFailure) as exc:
        data_commands.full_load_plan(
            data_domain="macro_series",
            source_id="not_a_real_source",
            start="2024-01-01",
            dry_run=True,
        )
    assert exc.value.error_code == "CAPABILITY_MISSING"


def test_qmdData_fullLoadAcceptance_cliSourceRouteDbLiveBlockedEnvelope(tmp_path: Path) -> None:
    """覆盖范围：真实 CLI full-load 在 source-route-db 根下的 live-blocked 路径
    测试对象：backend.app.cli.main subprocess + full_load_plan
    目的/目标：缺 live 授权时 full-load 也必须返回统一验收信封
    验证点：命令 exit 0；gate_eligible=True；failure_class=BLOCKED
    失败含义：full-load 仍被旧 route-preview/pilot 路径提前拦截，无法作为 P1 证据
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
            "full-load",
            "--domain",
            "macro_series",
            "--source-id",
            "fred",
            "--start",
            "2024-01-01",
            "--end",
            "2024-01-07",
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


def test_qmdData_fullLoadAcceptance_dryRunShowsBoundedSmokeScope(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：full-load dry-run 有界 smoke 语义
    测试对象：full_load_plan dry_run full_load_evidence
    目的/目标：区分 bounded_smoke 与完整历史重建，并暴露独立 run_id
    验证点：execution_scope=bounded_smoke；run_id 存在；shard_plan 非空
    失败含义：full-load 与 backfill smoke 混淆，cold-start 边界不清
    """
    root = _p1_root(tmp_path)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.full_load_plan(
        data_domain="cn_equity_daily_bar",
        source_id="baostock",
        start="2024-01-01",
        end="2024-01-31",
        dry_run=True,
    )
    evidence = payload.get("full_load_evidence") or {}
    assert evidence.get("execution_scope") == "bounded_smoke"
    assert payload.get("run_id")
    assert len(evidence.get("shard_plan") or []) >= 1


def test_qmdData_fullLoadAcceptance_liveBlockedShowsFullLoadCheckpointTypes(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：full-load live 缺授权 checkpoint 事件语义
    测试对象：run_phase1_full_load_live full_load_evidence
    目的/目标：BLOCKED 路径声明 FULL_LOAD_* checkpoint 事件类型供续跑审计
    验证点：checkpoint_event_types 含 FULL_LOAD_COMPLETE；run_id 独立
    失败含义：full-load 断点续跑证据不可从 official report 追溯
    """
    root = _p1_root(tmp_path)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    payload = data_commands.full_load_plan(
        data_domain="macro_series",
        source_id="fred",
        start="2024-01-01",
        end="2024-01-07",
        dry_run=False,
    )
    evidence = payload.get("full_load_evidence") or {}
    checkpoint_types = evidence.get("checkpoint_event_types") or []
    assert "FULL_LOAD_COMPLETE" in checkpoint_types
    assert payload.get("run_id")
    assert evidence.get("execution_scope") == "bounded_smoke"


def test_qmdData_fullLoadAcceptance_livePassReplayFetchCleanWriteAndCheckpoint(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：official full-load live PASS 产品路径
    测试对象：full_load_plan cn_equity_daily_bar/baostock live
    目的/目标：有界 cold-start 经 official CLI 完成 fetch→clean 并产出 FULL_LOAD checkpoint
    验证点：status=PASS；write_grade=primary_grade_clean；FULL_LOAD_COMPLETE 事件；clean 有行
    失败含义：full-load 仅有 dry-run/BLOCKED，PRD 最高接缝未闭合
    """
    root = _p1_root(tmp_path)
    replay = root / "full_load_replay.json"
    _write_two_shard_replay(replay)
    monkeypatch.setenv("QMD_DATA_ROOT", str(root))
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    _patch_phase1_baostock_replay(monkeypatch, replay)
    payload = data_commands.full_load_plan(
        data_domain="cn_equity_daily_bar",
        source_id="baostock",
        start=START,
        end=END,
        max_shards=3,
        dry_run=False,
    )
    report = payload["acceptance_report"]
    assert payload.get("gate_eligible") is True
    assert report["status"] == "PASS"
    assert report["write_grade"] == "primary_grade_clean"
    assert report["route_plan_id"] is not None
    assert payload["clean_status"] == "WRITTEN"
    evidence = payload.get("full_load_evidence") or {}
    assert evidence.get("execution_scope") == "bounded_smoke"
    assert "FULL_LOAD_COMPLETE" in (evidence.get("checkpoint_event_types") or [])
    job_id = payload.get("job_id")
    assert job_id
    db = root / "duckdb" / "quant_monitor.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.reader() as con:
        complete_events = con.execute(
            """
            SELECT COUNT(*) FROM job_event_log
            WHERE job_id = ? AND event_type = 'FULL_LOAD_COMPLETE'
            """,
            [job_id],
        ).fetchone()[0]
        row_count = con.execute(
            "SELECT COUNT(*) FROM security_bar_1d WHERE instrument_id = ?",
            [SYMBOL],
        ).fetchone()[0]
    assert complete_events >= 1
    assert row_count >= 2
    snapshot = payload.get("full_load_evidence", {}).get("affected_snapshot_recompute") or {}
    assert snapshot.get("status") == "pending"
    assert snapshot.get("clean_table") == "security_bar_1d"
