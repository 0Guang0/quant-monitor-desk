"""R3-DCP-05 mootdx incremental E2E — service path + security_bar_1d."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.datasources.fetch_ports.mootdx_port import create_mootdx_fetch_port
from backend.app.datasources.fetch_ports.tdx_fetch_guards import EQUITY_INDEX_MAX_ROWS
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.ops.db_inspector import DbInspector
from backend.app.ops.mootdx_incremental_run import (
    build_mootdx_incremental_service,
    run_mootdx_bar_incremental,
)
from backend.app.sync.watermark import compute_incremental_window, read_bar_trade_date_watermark

from tests.incremental_mootdx_support import (
    FIXTURE_DATE,
    SYMBOL,
    bootstrap_db,
    build_live_service,
    build_service,
    fetch_security_bar_row,
    incremental_spec,
    run_mootdx_replay_incremental,
    seed_watermark_row,
)
from tests.live_incremental_support import bootstrap_acceptance_cm


def test_mootdxIncremental_e2e_writesSecurityBar1d(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：mootdx replay fixture 经服务路径增量写入 security_bar_1d
    测试对象：watermark + DataSourceService + run_incremental
    目的/目标：watermark 窗内 bar 应经金路径 upsert 到 clean 表
    验证点：COMPLETED；clean 表含 fixture trade_date 行且 source_used=mootdx
    失败含义：mootdx 增量链断则 DCP-05 bar 源无法落库
    """
    cm, _data_root, result = run_mootdx_replay_incremental(
        tmp_path, monkeypatch, job_id="job-mootdx-e2e-1"
    )
    assert result.status == "COMPLETED"
    with cm.reader() as con:
        row = fetch_security_bar_row(con, FIXTURE_DATE.isoformat())
    assert row is not None
    assert float(row[1]) == 1405.0
    assert row[2] == "mootdx"


def test_mootdxIncremental_opsRun_writesSecurityBar1d(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：mootdx_incremental_run 金路径封装
    测试对象：run_mootdx_bar_incremental + build_mootdx_incremental_service
    目的/目标：ops 层应复用 orchestrator 写入 security_bar_1d
    验证点：COMPLETED；fixture 行存在
    失败含义：ops 封装断裂则 S12 CLI 无法接线
    """
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    cm = bootstrap_db(tmp_path)
    with cm.writer() as con:
        seed_watermark_row(con, "2024-06-24")
        wm = read_bar_trade_date_watermark(con, instrument_id=SYMBOL)
    window = compute_incremental_window(wm, end=FIXTURE_DATE)
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    from backend.app.sync.orchestrator import DataSyncOrchestrator

    orch = DataSyncOrchestrator(cm)
    service = build_mootdx_incremental_service(
        data_root=raw_root,
        symbol=SYMBOL,
        job_events=orch._jobs,
        use_mock=True,
    )
    run_result = run_mootdx_bar_incremental(
        orch,
        service=service,
        window=window,
        symbol=SYMBOL,
        product_live=False,
        job_id="job-mootdx-ops-1",
    )
    assert run_result.status == "COMPLETED"
    with cm.reader() as con:
        count = con.execute(
            "SELECT COUNT(*) FROM security_bar_1d WHERE instrument_id = ? AND trade_date = ?",
            [SYMBOL, FIXTURE_DATE.isoformat()],
        ).fetchone()[0]
    assert count >= 1


def test_mootdxPort_replayFiltersByFetchWindow() -> None:
    """覆盖范围：mootdx replay 窗过滤
    测试对象：MootdxMockFetchPort.fetch_payload
    目的/目标：start/end 之外的 bar 不应出现在 payload
    验证点：窗外 row_count=0；窗内 row_count=1
    失败含义：未过滤会破坏 incremental 语义（仿 baostock S01）
    """
    port = create_mootdx_fetch_port(symbols=(SYMBOL,), max_rows=EQUITY_INDEX_MAX_ROWS, use_mock=True)
    outside = FetchRequest(
        run_id="r1",
        source_id="mootdx",
        data_domain="cn_equity_daily_bar",
        instrument_id=SYMBOL,
        start_time="2020-01-01",
        end_time="2020-01-02",
    )
    inside = FetchRequest(
        run_id="r2",
        source_id="mootdx",
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


def test_mootdxIncremental_repeatRun_noRowGrowth(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：连续两次 mootdx 增量 sync
    测试对象：upsert_by_pk 幂等
    目的/目标：重复跑同一窗不应增加 security_bar_1d 行数
    验证点：两次 COMPLETED；行数保持 2（seed + fixture）
    失败含义：幂等失败会导致日常 sync 数据膨胀
    """
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    cm = bootstrap_db(tmp_path)
    with cm.writer() as con:
        seed_watermark_row(con, "2024-06-24")
    window = compute_incremental_window(date(2024, 6, 24), end=FIXTURE_DATE)
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    service, orch = build_service(cm, raw_root)
    kwargs = dict(
        datasource_service=service,
        clean_table="security_bar_1d",
        write_mode="upsert_by_pk",
        primary_keys=("instrument_id", "trade_date", "adjustment_type"),
    )
    r1 = orch.run_incremental(incremental_spec(window, job_id="job-mootdx-idem-1"), **kwargs)
    r2 = orch.run_incremental(incremental_spec(window, job_id="job-mootdx-idem-2"), **kwargs)
    with cm.reader() as con:
        count = con.execute(
            "SELECT COUNT(*) FROM security_bar_1d WHERE instrument_id = ?", [SYMBOL]
        ).fetchone()[0]
    assert r1.status == "COMPLETED"
    assert r2.status == "COMPLETED"
    assert count == 2


def test_mootdxIncremental_emptyResponse_whenWatermarkCurrent(
    tmp_path: Path, monkeypatch
) -> None:
    """覆盖范围：水位已追平时增量 sync 不写新行
    测试对象：run_mootdx_bar_incremental + caught-up window
    目的/目标：watermark==end 时 orchestrator SKIPPED，security_bar_1d 行数不变
    验证点：status==SKIPPED；行数保持 seed 的 1 行
    失败含义：追平后仍 fetch/write，bar 增量语义错误
    """
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    cm = bootstrap_db(tmp_path)
    with cm.writer() as con:
        seed_watermark_row(con, FIXTURE_DATE.isoformat())
        before = con.execute(
            "SELECT COUNT(*) FROM security_bar_1d WHERE instrument_id = ?", [SYMBOL]
        ).fetchone()[0]
    window = compute_incremental_window(FIXTURE_DATE, end=FIXTURE_DATE)
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    service, orch = build_service(cm, raw_root)
    result = run_mootdx_bar_incremental(
        orch,
        service=service,
        window=window,
        symbol=SYMBOL,
        product_live=False,
        job_id="job-mootdx-empty-1",
    )
    assert result.status == "SKIPPED"
    with cm.reader() as con:
        after = con.execute(
            "SELECT COUNT(*) FROM security_bar_1d WHERE instrument_id = ?", [SYMBOL]
        ).fetchone()[0]
    assert after == before


def test_mootdxLive_noSilentFallbackWhenGateClosed(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：无 QMD_ALLOW_LIVE_FETCH 时 mootdx live port 阻断
    测试对象：create_mootdx_fetch_port(use_mock=False)
    目的/目标：live 被拒时不得静默退回 mock port
    验证点：抛 ProductLiveGateError · LIVE_FETCH_REJECTED
    失败含义：mootdx live 路径渗入 silent fallback
    """
    from backend.app.datasources.fetch_ports.mootdx_port import create_mootdx_fetch_port
    from backend.app.datasources.fetch_ports.tdx_fetch_guards import EQUITY_INDEX_MAX_ROWS
    from backend.app.datasources.product_live_gate import ProductLiveGateError

    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    with pytest.raises(ProductLiveGateError) as exc_info:
        create_mootdx_fetch_port(symbols=(SYMBOL,), max_rows=EQUITY_INDEX_MAX_ROWS, use_mock=False)
    assert exc_info.value.code == "LIVE_FETCH_REJECTED"


@pytest.mark.network
def test_mootdxIncremental_liveNetwork_writesSecurityBar1d(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：隔离 sandbox + mootdx product live 写 security_bar_1d
    测试对象：build_mootdx_incremental_service(use_mock=False) + run_mootdx_bar_incremental
    目的/目标：QMD_ALLOW_LIVE_FETCH=1 时 product live 金路径落库
    验证点：COMPLETED；clean 表含 fixture trade_date 行；DbInspector 表存在
    失败含义：Tier A mootdx live 增量链断
    """
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    cm = bootstrap_acceptance_cm(isolated_live_data_root)
    with cm.writer() as con:
        seed_watermark_row(con, "2024-06-24")
        wm = read_bar_trade_date_watermark(con, instrument_id=SYMBOL)
    window = compute_incremental_window(wm, end=FIXTURE_DATE)
    raw_root = isolated_live_data_root / "raw" / "mootdx"
    raw_root.mkdir(parents=True, exist_ok=True)
    service, orch = build_live_service(cm, raw_root, monkeypatch)
    result = run_mootdx_bar_incremental(
        orch,
        service=service,
        window=window,
        symbol=SYMBOL,
        product_live=True,
        job_id="job-mootdx-live-e2e-1",
    )
    assert result.status == "COMPLETED"
    assert result.product_live is True
    with cm.reader() as con:
        row = con.execute(
            """
            SELECT trade_date, close FROM security_bar_1d
            WHERE instrument_id = ? AND trade_date = ?
            """,
            [SYMBOL, FIXTURE_DATE.isoformat()],
        ).fetchone()
    assert row is not None
    inspect_report = DbInspector(cm.db_path, raw_root).inspect()
    bar_table = next(t for t in inspect_report.key_tables if t["name"] == "security_bar_1d")
    assert bar_table["exists"] is True
    assert bar_table["row_count"] is not None and bar_table["row_count"] >= 1


@pytest.mark.network
def test_mootdxIncremental_liveNetwork_idempotentSecondRun(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：隔离 sandbox 连续两次 mootdx product live 增量
    测试对象：run_mootdx_bar_incremental 幂等 upsert
    目的/目标：重复 live 跑同一窗不应增加 security_bar_1d 行数
    验证点：两次 COMPLETED；行数保持 2（seed + fixture）
    失败含义：live 幂等失败会导致日常 sync 数据膨胀
    """
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    cm = bootstrap_acceptance_cm(isolated_live_data_root)
    with cm.writer() as con:
        seed_watermark_row(con, "2024-06-24")
        wm = read_bar_trade_date_watermark(con, instrument_id=SYMBOL)
    window = compute_incremental_window(wm, end=FIXTURE_DATE)
    raw_root = isolated_live_data_root / "raw" / "mootdx"
    raw_root.mkdir(parents=True, exist_ok=True)
    service, orch = build_live_service(cm, raw_root, monkeypatch)
    kwargs = dict(
        service=service,
        window=window,
        symbol=SYMBOL,
        product_live=True,
    )
    r1 = run_mootdx_bar_incremental(orch, job_id="job-mootdx-live-idem-1", **kwargs)
    r2 = run_mootdx_bar_incremental(orch, job_id="job-mootdx-live-idem-2", **kwargs)
    with cm.reader() as con:
        count = con.execute(
            "SELECT COUNT(*) FROM security_bar_1d WHERE instrument_id = ?", [SYMBOL]
        ).fetchone()[0]
    assert r1.status == "COMPLETED"
    assert r2.status == "COMPLETED"
    assert count == 2
