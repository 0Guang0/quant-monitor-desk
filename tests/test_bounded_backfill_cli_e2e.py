"""R3-DCP-09 bounded backfill CLI replay e2e."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.app.cli import data_commands
from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.db.connection import ConnectionManager
from tests.incremental_baostock_support import SYMBOL, bootstrap_db

START = "2024-06-01"
END = "2024-07-31"


def _write_two_shard_replay(path: Path) -> None:
    payload = {
        "schema_version": "cn_market_evidence_v1",
        "source_id": "baostock",
        "data_domain": "cn_equity_daily_bar",
        "bars": [
            {
                "instrument_id": SYMBOL,
                "trade_date": "2024-06-25",
                "open": 1400.0,
                "high": 1410.0,
                "low": 1395.0,
                "close": 1405.0,
                "volume": 1000000,
                "source_used": "baostock",
            },
            {
                "instrument_id": SYMBOL,
                "trade_date": "2024-07-15",
                "open": 1410.0,
                "high": 1420.0,
                "low": 1405.0,
                "close": 1415.0,
                "volume": 1100000,
                "source_used": "baostock",
            },
        ],
        "source_fetch_id": "baostock-replay-backfill-e2e",
        "content_hash": "baostock-replay-hash-backfill-e2e",
        "as_of_timestamp": "2024-07-15T15:00:00Z",
        "retrieved_at": "2024-07-15T15:00:00Z",
        "trade_date": "2024-07-15",
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _patch_baostock_replay(monkeypatch, replay_path: Path) -> None:
    from backend.app.datasources.fetch_ports import baostock_port
    from backend.app.ops import baostock_incremental_run

    original = baostock_incremental_run.build_baostock_incremental_service

    def _build(*, data_root, symbol, job_events, use_mock=None):
        from backend.app.datasources.fetch_ports.baostock_port import BaostockMockFetchPort
        from backend.app.datasources.service import DataSourceService

        port = BaostockMockFetchPort(symbols=(symbol,), max_rows=500, replay_path=replay_path)
        return DataSourceService(data_root=data_root, fetch_port=port, job_events=job_events)

    monkeypatch.setattr(baostock_incremental_run, "build_baostock_incremental_service", _build)
    monkeypatch.setattr(baostock_port, "REPLAY_FIXTURE", replay_path)


def _patch_phase1_fallback_fetch(monkeypatch, replay_path: Path) -> None:
    """Wrap phase1 DataSourceService fetch to simulate authorized fallback source."""
    from backend.app.cli import phase1_acceptance
    from backend.app.datasources.fetch_result import FetchResult

    _patch_phase1_baostock_replay(monkeypatch, replay_path)
    original_build = phase1_acceptance._build_datasource_service

    def _build():
        svc = original_build()
        original_fetch = svc.fetch

        def _fetch(req, *, con, job_id=None, **kwargs):
            result = original_fetch(req, con=con, job_id=job_id, **kwargs)
            if result.status == "SUCCESS":
                return result.model_copy(update={"source_id": "qmt_xtdata"})
            return result

        svc.fetch = _fetch  # type: ignore[method-assign]
        return svc

    monkeypatch.setattr(phase1_acceptance, "_build_datasource_service", _build)


def _patch_phase1_backfill_conflict_peers(
    monkeypatch, replay_path: Path, *, peer_close: float = 2000.0
) -> None:
    """Seed severe conflict peer rows after real fetch on official backfill path."""
    from backend.app.cli import phase1_acceptance
    from backend.app.sync.runners import resolve_conflict_staging_table

    _patch_phase1_baostock_replay(monkeypatch, replay_path)
    original_build = phase1_acceptance._build_datasource_service

    def _build():
        svc = original_build()
        original_fetch = svc.fetch

        def _fetch(req, *, con, job_id=None, **kwargs):
            result = original_fetch(req, con=con, job_id=job_id, **kwargs)
            if job_id and result.status == "SUCCESS" and result.staging_table:
                table = resolve_conflict_staging_table(req.data_domain, job_id)
                if table:
                    from backend.app.db.sql_identifiers import quote_ident

                    stg = quote_ident(result.staging_table)
                    tbl = quote_ident(table)
                    con.execute(
                        f"""
                        CREATE TABLE IF NOT EXISTS {tbl} (
                            source_id VARCHAR, instrument_id VARCHAR,
                            trade_date VARCHAR, close DOUBLE
                        )
                        """
                    )
                    con.execute(f"DELETE FROM {tbl}")
                    con.execute(
                        f"""
                        INSERT INTO {tbl} (source_id, instrument_id, trade_date, close)
                        SELECT source_used, instrument_id, trade_date, close
                        FROM {stg}
                        """
                    )
                    for instrument_id, trade_date, close in con.execute(
                        f"SELECT instrument_id, trade_date, close FROM {stg}"
                    ).fetchall():
                        severe_close = float(close) * 1.5
                        con.execute(
                            f"INSERT INTO {tbl} VALUES (?, ?, ?, ?)",
                            ["akshare", instrument_id, trade_date, severe_close],
                        )
            return result

        svc.fetch = _fetch  # type: ignore[method-assign]
        return svc

    monkeypatch.setattr(phase1_acceptance, "_build_datasource_service", _build)


def _write_invalid_bar_replay(path: Path) -> None:
    payload = {
        "schema_version": "cn_market_evidence_v1",
        "source_id": "baostock",
        "data_domain": "cn_equity_daily_bar",
        "bars": [
            {
                "instrument_id": SYMBOL,
                "trade_date": "2024-06-25",
                "open": 1400.0,
                "high": 1410.0,
                "low": 1395.0,
                "close": -1.0,
                "volume": 1000000,
                "source_used": "baostock",
            }
        ],
        "source_fetch_id": "baostock-replay-invalid",
        "content_hash": "baostock-replay-hash-invalid",
        "as_of_timestamp": "2024-06-25T15:00:00Z",
        "retrieved_at": "2024-06-25T15:00:00Z",
        "trade_date": "2024-06-25",
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _patch_phase1_baostock_replay(monkeypatch, replay_path: Path) -> None:
    from backend.app.cli import phase1_acceptance
    from backend.app.datasources.fetch_ports.baostock_port import BaostockMockFetchPort
    from backend.app.datasources.service import DataSourceService
    from backend.app.datasources.source_registry import SourceRegistry

    def _build() -> DataSourceService:
        registry = SourceRegistry()
        registry.load()
        port = BaostockMockFetchPort(symbols=(SYMBOL,), max_rows=500, replay_path=replay_path)
        return DataSourceService(
            staged_fixture_mode=False,
            source_registry=registry,
            fetch_port=port,
        )

    monkeypatch.setattr(phase1_acceptance, "_build_datasource_service", _build)


def _patch_phase1_backfill_fail_on_second(monkeypatch, replay_path: Path) -> None:
    """Fail the second shard fetch on official backfill path (checkpoint resume probe)."""
    from backend.app.cli import phase1_acceptance
    from backend.app.datasources.fetch_result import FetchResult

    _patch_phase1_baostock_replay(monkeypatch, replay_path)
    original_build = phase1_acceptance._build_datasource_service
    calls = {"n": 0}

    def _build():
        svc = original_build()
        original_fetch = svc.fetch

        def _fetch(req, *, con, job_id=None, **kwargs):
            calls["n"] += 1
            if calls["n"] >= 2:
                return FetchResult(
                    run_id=req.run_id,
                    source_id=req.source_id,
                    data_domain=req.data_domain,
                    status="NETWORK_ERROR",
                    row_count=0,
                    fetch_time="2026-06-17T10:00:00Z",
                    error_message="shard 2 failed",
                )
            return original_fetch(req, con=con, job_id=job_id, **kwargs)

        svc.fetch = _fetch  # type: ignore[method-assign]
        return svc

    monkeypatch.setattr(phase1_acceptance, "_build_datasource_service", _build)


def test_boundedBackfill_cli_checkpointResume_skipsCompletedShards(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：official backfill 断点续跑
    测试对象：data_commands.backfill_plan + BackfillShardRunner SHARD_COMPLETE checkpoint
    目的/目标：首跑部分 shard 失败后，同 job_id 续跑跳过已完成分片
    验证点：首跑留下 SHARD_COMPLETE；backfill_evidence.checkpoint_task_id 非空；续跑 PASS 且 SHARD_COMPLETE≥2
    失败含义：official CLI 无法断点续跑，bounded backfill 成本不可控
    """
    sandbox = tmp_path / ".audit-sandbox" / "source-route-db-bf-resume"
    sandbox.mkdir(parents=True)
    replay = sandbox / "backfill_resume_replay.json"
    _write_two_shard_replay(replay)
    monkeypatch.setenv("QMD_DATA_ROOT", str(sandbox))
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    fixed_job_id = "job-p1-bf-resume-official"
    kwargs = dict(
        data_domain="cn_equity_daily_bar",
        source_id="baostock",
        start=START,
        end=END,
        max_shards=3,
        dry_run=False,
        resume_job_id=fixed_job_id,
    )

    _patch_phase1_backfill_fail_on_second(monkeypatch, replay)
    payload1 = data_commands.backfill_plan(**kwargs)
    assert payload1["job_id"] == fixed_job_id
    evidence1 = payload1.get("backfill_evidence") or {}
    assert evidence1.get("checkpoint_task_id")
    assert payload1["acceptance_report"]["failure_class"] in {"FAIL", "FAIL_EXTERNAL"}

    db = sandbox / "duckdb" / "quant_monitor.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.reader() as con:
        first_complete = con.execute(
            """
            SELECT task_id FROM job_event_log
            WHERE job_id = ? AND event_type = 'SHARD_COMPLETE'
            ORDER BY created_at ASC
            """,
            [fixed_job_id],
        ).fetchall()
    assert len(first_complete) == 1
    first_task_id = first_complete[0][0]

    _patch_phase1_baostock_replay(monkeypatch, replay)
    payload2 = data_commands.backfill_plan(**kwargs)
    assert payload2["acceptance_report"]["status"] == "PASS"
    evidence2 = payload2.get("backfill_evidence") or {}
    assert evidence2.get("checkpoint_task_id")
    with cm.reader() as con:
        all_complete = con.execute(
            """
            SELECT task_id FROM job_event_log
            WHERE job_id = ? AND event_type = 'SHARD_COMPLETE'
            ORDER BY created_at ASC
            """,
            [fixed_job_id],
        ).fetchall()
        row_count = con.execute(
            "SELECT COUNT(*) FROM security_bar_1d WHERE instrument_id = ?",
            [SYMBOL],
        ).fetchone()[0]
    assert len(all_complete) >= 2
    assert first_task_id in {row[0] for row in all_complete}
    assert row_count >= 2


def test_bounded_backfill_cli_replay_e2e_two_shards_idempotent(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：CLI backfill replay e2e 多分片
    测试对象：data_commands.backfill_plan --no-dry-run on source-route-db
    目的/目标：2+ shards 经金路径写 clean；重复跑幂等
    验证点：shard_count≥2；SHARD_COMPLETE 事件≥2；二次跑行数不增；backfill_evidence 可见
    失败含义：有界 backfill 产品路径未通，operator 无法补历史
    """
    sandbox = tmp_path / ".audit-sandbox" / "source-route-db-bf-e2e"
    sandbox.mkdir(parents=True)
    replay = sandbox / "backfill_replay.json"
    _write_two_shard_replay(replay)
    monkeypatch.setenv("QMD_DATA_ROOT", str(sandbox))
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    _patch_phase1_baostock_replay(monkeypatch, replay)

    kwargs = dict(
        data_domain="cn_equity_daily_bar",
        source_id="baostock",
        start=START,
        end=END,
        max_shards=3,
        dry_run=False,
    )
    payload1 = data_commands.backfill_plan(**kwargs)
    assert payload1["shard_count"] >= 2
    assert payload1.get("gate_eligible") is True
    assert payload1.get("backfill_evidence", {}).get("trigger_reason") == "eco_catchup"
    job_id = payload1.get("job_id")
    assert job_id

    db = sandbox / "duckdb" / "quant_monitor.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.reader() as con:
        shard_events = con.execute(
            """
            SELECT COUNT(*) FROM job_event_log
            WHERE job_id = ? AND event_type = 'SHARD_COMPLETE'
            """,
            [job_id],
        ).fetchone()[0]
        row_count = con.execute(
            "SELECT COUNT(*) FROM security_bar_1d WHERE instrument_id = ?",
            [SYMBOL],
        ).fetchone()[0]
    assert shard_events >= 2
    assert row_count >= 2
    with cm.reader() as con:
        closes = {
            row[0]: float(row[1])
            for row in con.execute(
                """
                SELECT trade_date, close FROM security_bar_1d
                WHERE instrument_id = ? AND trade_date IN ('2024-06-25', '2024-07-15')
                """,
                [SYMBOL],
            ).fetchall()
        }
    from datetime import date

    assert closes.get(date(2024, 6, 25)) == 1405.0
    assert closes.get(date(2024, 7, 15)) == 1415.0

    payload2 = data_commands.backfill_plan(**kwargs)
    assert payload2.get("job_id")
    with cm.reader() as con:
        row_count_after = con.execute(
            "SELECT COUNT(*) FROM security_bar_1d WHERE instrument_id = ?",
            [SYMBOL],
        ).fetchone()[0]
    assert row_count_after == row_count
    snapshot = payload1.get("backfill_evidence", {}).get("affected_snapshot_recompute") or {}
    assert snapshot.get("status") == "pending"
    assert snapshot.get("clean_table") == "security_bar_1d"
    assert snapshot.get("data_domain") == "cn_equity_daily_bar"
    obs = payload1.get("observability_evidence") or {}
    assert obs.get("fetch_log_ids")
    assert obs.get("rows_written", 0) >= 1


def test_boundedBackfill_cli_liveSevereConflictBlocksOfficialCleanWrite(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：official backfill 真实严重冲突阻断
    测试对象：data_commands.backfill_plan + SourceConflictValidator
    目的/目标：冲突 peer 经真实 validation 管道阻断 clean 写入
    验证点：conflict_status=SEVERE_CONFLICT；clean_status=NOT_RUN；status=FAIL
    失败含义：仅 mock job 结果，未证明 validator/gate 在 official path 阻断
    """
    sandbox = tmp_path / ".audit-sandbox" / "source-route-db-bf-severe"
    sandbox.mkdir(parents=True)
    replay = sandbox / "backfill_severe_replay.json"
    _write_two_shard_replay(replay)
    monkeypatch.setenv("QMD_DATA_ROOT", str(sandbox))
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    _patch_phase1_backfill_conflict_peers(monkeypatch, replay)
    payload = data_commands.backfill_plan(
        data_domain="cn_equity_daily_bar",
        source_id="baostock",
        start="2024-06-25",
        end="2024-06-25",
        max_shards=1,
        dry_run=False,
    )
    report = payload["acceptance_report"]
    assert report["conflict_status"] == "SEVERE_CONFLICT"
    assert payload["clean_status"] == "NOT_RUN"
    assert report["status"] == "FAIL"


def test_boundedBackfill_cli_liveValidationFailureBlocksOfficialCleanWrite(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：official backfill 数据质量阻断
    测试对象：data_commands.backfill_plan + DataQualityValidator
    目的/目标：非法 OHLC 在 official path 阻断 clean 写入
    验证点：validation_status=FAILED；clean_status=NOT_RUN；failure_class=FAIL
    失败含义：质量门只在低层单测存在，official CLI 仍显示可写 clean
    """
    sandbox = tmp_path / ".audit-sandbox" / "source-route-db-bf-dq"
    sandbox.mkdir(parents=True)
    replay = sandbox / "backfill_invalid_replay.json"
    _write_invalid_bar_replay(replay)
    monkeypatch.setenv("QMD_DATA_ROOT", str(sandbox))
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    _patch_phase1_baostock_replay(monkeypatch, replay)
    payload = data_commands.backfill_plan(
        data_domain="cn_equity_daily_bar",
        source_id="baostock",
        start=START,
        end="2024-06-30",
        max_shards=1,
        dry_run=False,
    )
    report = payload["acceptance_report"]
    assert report["validation_status"] in {"FAILED", "MANUAL_REVIEW_REQUIRED"}
    assert payload["clean_status"] == "NOT_RUN"
    assert report["failure_class"] == "FAIL"


def test_boundedBackfill_cli_liveFallbackDegradedCleanWriteOfficialPath(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：official backfill 授权 fallback 降级写入
    测试对象：WriteManager + _resolve_write_provenance on official path
    目的/目标：fallback 源写入须报告 degraded_clean 且审计字段齐全
    验证点：write_grade=degraded_clean；source_switched=True；downstream=DEGRADED_READ
    失败含义：降级写入仍依赖 monkeypatch WriteManager，非真实 provenance 规则
    """
    sandbox = tmp_path / ".audit-sandbox" / "source-route-db-bf-degraded"
    sandbox.mkdir(parents=True)
    replay = sandbox / "backfill_degraded_replay.json"
    _write_two_shard_replay(replay)
    monkeypatch.setenv("QMD_DATA_ROOT", str(sandbox))
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    _patch_phase1_fallback_fetch(monkeypatch, replay)
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
    assert report["downstream_layer_read_status"] == "DEGRADED_READ"
