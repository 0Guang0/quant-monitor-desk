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


def test_bounded_backfill_cli_e2e_two_shards_shard_complete_and_idempotent(
    monkeypatch, tmp_path: Path
) -> None:
    """覆盖范围：CLI backfill replay e2e 多分片
    测试对象：data_commands.backfill_plan --no-dry-run
    目的/目标：2+ shards 经金路径写 clean；重复跑幂等
    验证点：shard_count≥2；SHARD_COMPLETE 事件≥2；二次跑行数不增
    失败含义：有界 backfill 产品路径未通，operator 无法补历史
    """
    sandbox = tmp_path / ".audit-sandbox" / "bf-e2e"
    sandbox.mkdir(parents=True)
    replay = sandbox / "backfill_replay.json"
    _write_two_shard_replay(replay)
    monkeypatch.setenv("QMD_DATA_ROOT", str(sandbox))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    _patch_baostock_replay(monkeypatch, replay)

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
    assert payload1["job_status"] == "COMPLETED"

    db = sandbox / "duckdb" / "quant_monitor.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.reader() as con:
        shard_events = con.execute(
            """
            SELECT COUNT(*) FROM job_event_log
            WHERE job_id = ? AND event_type = 'SHARD_COMPLETE'
            """,
            [payload1["job_id"]],
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
    assert payload2["job_status"] == "COMPLETED"
    with cm.reader() as con:
        row_count_after = con.execute(
            "SELECT COUNT(*) FROM security_bar_1d WHERE instrument_id = ?",
            [SYMBOL],
        ).fetchone()[0]
    assert row_count_after == row_count
