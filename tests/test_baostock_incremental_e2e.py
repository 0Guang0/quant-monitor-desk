"""R3-DCP-01 baostock incremental E2E — service path + security_bar_1d."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from backend.app.config import PROJECT_ROOT
from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.datasources.fetch_ports.baostock_port import create_baostock_fetch_port
from backend.app.datasources.service import DataSourceService
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.jobs import SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator
from backend.app.sync.watermark import compute_incremental_window, read_bar_trade_date_watermark

REPLAY_FIXTURE = (
    PROJECT_ROOT / "tests/fixtures/replay/cn_market/baostock/sh600519_daily_replay.json"
)
SYMBOL = "sh.600519"
FIXTURE_DATE = date(2024, 6, 25)


def _bootstrap_db(tmp_path: Path) -> ConnectionManager:
    db = tmp_path / "baostock_incr.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    return cm


def _seed_watermark_row(con, trade_date: str) -> None:
    con.execute("DELETE FROM security_bar_1d WHERE instrument_id = ?", [SYMBOL])
    con.execute(
        """
        INSERT INTO security_bar_1d (
            instrument_id, trade_date, open, high, low, close, pre_close, volume, amount,
            adjustment_type, source_used, batch_id, quality_flags, created_at
        ) VALUES (?, ?, 1, 1, 1, 1, NULL, NULL, NULL, 'none', 'seed', 'b0', NULL, CURRENT_TIMESTAMP)
        """,
        [SYMBOL, trade_date],
    )


def _build_service(cm: ConnectionManager, raw_root: Path) -> DataSourceService:
    orch = DataSyncOrchestrator(cm)
    port = create_baostock_fetch_port(
        symbols=(SYMBOL,),
        max_rows=500,
        use_mock=True,
    )
    return DataSourceService(
        data_root=raw_root,
        fetch_port=port,
        job_events=orch._jobs,
    ), orch


def _incremental_spec(window, *, job_id: str) -> SyncJobSpec:
    return SyncJobSpec(
        run_id=job_id,
        job_id=job_id,
        job_type="incremental",
        data_domain="cn_equity_daily_bar",
        market_id="CN_A",
        source_id="baostock",
        adapter_id="baostock",
        date_start=window.date_start,
        date_end=window.date_end,
        instrument_id=SYMBOL,
        partition_key=None,
        trigger_reason="test",
    )


def test_baostockIncremental_e2e_writesSecurityBar1d(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：replay fixture 经服务路径增量写入 security_bar_1d
    测试对象：watermark + DataSourceService + run_incremental
    目的/目标：watermark 窗内 bar 应经金路径 upsert 到 clean 表
    验证点：COMPLETED；clean 表含 fixture trade_date 行
    失败含义：产品增量链断则 qmd data sync 无法落库
    """
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    cm = _bootstrap_db(tmp_path)
    with cm.writer() as con:
        _seed_watermark_row(con, "2024-06-24")
        wm = read_bar_trade_date_watermark(con, instrument_id=SYMBOL)
    window = compute_incremental_window(wm, end=FIXTURE_DATE)
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    service, orch = _build_service(cm, raw_root)
    spec = _incremental_spec(window, job_id="job-baostock-e2e-1")
    result = orch.run_incremental(
        spec,
        datasource_service=service,
        clean_table="security_bar_1d",
        write_mode="upsert_by_pk",
        primary_keys=("instrument_id", "trade_date", "adjustment_type"),
    )
    assert result.status == "COMPLETED"
    with cm.reader() as con:
        row = con.execute(
            """
            SELECT trade_date, close FROM security_bar_1d
            WHERE instrument_id = ? AND trade_date = ?
            """,
            [SYMBOL, FIXTURE_DATE.isoformat()],
        ).fetchone()
    assert row is not None
    assert float(row[1]) == 1405.0


def test_baostockIncremental_repeatRun_noRowGrowth(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：连续两次相同增量 sync
    测试对象：upsert_by_pk 幂等
    目的/目标：重复跑同一窗不应增加 security_bar_1d 行数
    验证点：两次 COMPLETED；行数保持 2（seed + fixture）
    失败含义：幂等失败会导致日常 sync 数据膨胀
    """
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    cm = _bootstrap_db(tmp_path)
    with cm.writer() as con:
        _seed_watermark_row(con, "2024-06-24")
    window = compute_incremental_window(date(2024, 6, 24), end=FIXTURE_DATE)
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    service, orch = _build_service(cm, raw_root)
    kwargs = dict(
        datasource_service=service,
        clean_table="security_bar_1d",
        write_mode="upsert_by_pk",
        primary_keys=("instrument_id", "trade_date", "adjustment_type"),
    )
    r1 = orch.run_incremental(_incremental_spec(window, job_id="job-bao-idem-1"), **kwargs)
    r2 = orch.run_incremental(_incremental_spec(window, job_id="job-bao-idem-2"), **kwargs)
    with cm.reader() as con:
        count = con.execute(
            "SELECT COUNT(*) FROM security_bar_1d WHERE instrument_id = ?", [SYMBOL]
        ).fetchone()[0]
    assert r1.status == "COMPLETED"
    assert r2.status == "COMPLETED"
    assert count == 2


def test_baostockPort_replayFiltersByFetchWindow() -> None:
    """覆盖范围：baostock replay 窗过滤
    测试对象：BaostockMockFetchPort.fetch_payload
    目的/目标：start/end 之外的 bar 不应出现在 payload
    验证点：窗外请求 row_count=0；窗内 row_count=1
    失败含义：未过滤会拉取全量 fixture 破坏 incremental 语义
    """
    import json

    from backend.app.datasources.fetch_result import FetchRequest

    port = create_baostock_fetch_port(symbols=(SYMBOL,), max_rows=500, use_mock=True)
    outside = FetchRequest(
        run_id="r1",
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
        instrument_id=SYMBOL,
        start_time="2020-01-01",
        end_time="2020-01-02",
    )
    inside = FetchRequest(
        run_id="r2",
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
        instrument_id=SYMBOL,
        start_time=FIXTURE_DATE.isoformat(),
        end_time=FIXTURE_DATE.isoformat(),
    )
    out_payload = port.fetch_payload(outside)
    in_payload = port.fetch_payload(inside)
    out_bundle = json.loads(out_payload.content.decode("utf-8"))
    in_bundle = json.loads(in_payload.content.decode("utf-8"))
    assert out_payload.row_count == 0
    assert in_payload.row_count == 1
    assert out_bundle.get("bars") == []
    assert len(in_bundle.get("bars") or []) == 1


def test_baostockPort_invertedWindow_returnsEmptyBars() -> None:
    """覆盖范围：baostock port caught-up 倒置窗
    测试对象：BaostockMockFetchPort.fetch_payload start > end
    目的/目标：倒置窗应返回 0 bar，不做 min/max 静默归一化
    验证点：row_count==0；bars 为空列表
    失败含义：port 归一化会把已落库日重新纳入 fetch
    """
    import json

    from backend.app.datasources.fetch_result import FetchRequest

    port = create_baostock_fetch_port(symbols=(SYMBOL,), max_rows=500, use_mock=True)
    inverted = FetchRequest(
        run_id="r-inv",
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
        instrument_id=SYMBOL,
        start_time="2026-07-01",
        end_time="2026-06-30",
    )
    payload = port.fetch_payload(inverted)
    bundle = json.loads(payload.content.decode("utf-8"))
    assert payload.row_count == 0
    assert bundle.get("bars") == []
