"""DCP-05 S06 — CFTC incremental e2e tests."""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from backend.app.datasources.product_live_gate import ProductLiveGateError
from backend.app.ops.db_inspector import DbInspector

from backend.app.ops.cftc_incremental_run import (
    DATA_DOMAIN,
    DEFAULT_MARKETS,
    SOURCE_ID,
    WEEKLY_ADVANCE_DAYS,
    read_since_dates_for_markets,
    build_cftc_incremental_service,
    create_cftc_incremental_port,
    run_cftc_incremental,
)
from backend.app.datasources.incremental_route_activation import load_plain_source_registry
from tests.macro_incremental_support import (
    FIXED_TODAY,
    bootstrap_macro_live_e2e_ctx,
    build_macro_e2e_ctx,
    insert_axis_observation,
)


@pytest.fixture
def cftc_incremental_e2e_ctx(tmp_path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    port = create_cftc_incremental_port(markets=DEFAULT_MARKETS, max_rows=3, use_mock=True)
    return build_macro_e2e_ctx(
        tmp_path,
        monkeypatch,
        source_id=SOURCE_ID,
        data_domain=DATA_DOMAIN,
        fetch_port=port,
        since_reader=read_since_dates_for_markets,
        instrument_ids=DEFAULT_MARKETS,
        service_builder=build_cftc_incremental_service,
        registry_factory=load_plain_source_registry,
    )


def test_cftcIncremental_e2e_replay_writesAxisObservation(
    cftc_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：mock port + run_incremental 写 axis_observation
    测试对象：run_cftc_incremental + DataSourceService 金路径
    目的/目标：replay 经 orchestrator 完成 validate + upsert 到 macro clean
    验证点：status==COMPLETED；axis_observation 行数>=1；indicator_id==088691
    失败含义：cftc 增量无法走 Sync 金路径写 macro clean
    """
    ctx = cftc_incremental_e2e_ctx
    report = run_cftc_incremental(
        ctx["orch"],
        service=ctx["service"],
        markets=DEFAULT_MARKETS,
        source_registry=ctx["registry"],
    )
    assert report.instrument_results[0]["status"] == "COMPLETED"
    with ctx["cm"].writer() as con:
        count = con.execute(
            "SELECT COUNT(*) FROM axis_observation WHERE indicator_id = '088691'"
        ).fetchone()[0]
        assert count >= 1
        row = con.execute(
            "SELECT raw_value FROM axis_observation WHERE indicator_id = '088691' LIMIT 1"
        ).fetchone()
    assert row is not None and float(row[0]) == 20000.0


def test_cftcIncremental_idempotent_secondRun_rowCountStable(
    cftc_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：连续两次增量跑 row count 不增
    测试对象：run_cftc_incremental 幂等 upsert
    目的/目标：重复跑 observation_id PK upsert 不重复插入
    验证点：两次 COMPLETED 后 COUNT(*) 相等
    失败含义：幂等失败，生产重复跑会膨胀行数
    """
    ctx = cftc_incremental_e2e_ctx
    run_cftc_incremental(
        ctx["orch"], service=ctx["service"], source_registry=ctx["registry"]
    )
    with ctx["cm"].writer() as con:
        first = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    run_cftc_incremental(
        ctx["orch"], service=ctx["service"], source_registry=ctx["registry"]
    )
    with ctx["cm"].writer() as con:
        second = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    assert first == second
    assert first >= 1


def test_cftcIncremental_weeklyWatermark_advancesSevenDays() -> None:
    """覆盖范围：CFTC 周频水位 advance_days=7
    测试对象：read_since_dates_for_markets + compute_since_date
    目的/目标：周频 COT 水位后 since = watermark + 7 天
    验证点：watermark=2026-06-01 → since=2026-06-08
    失败含义：日频水位导致周频源重复拉取或漏拉
    """
    import duckdb

    from backend.app.db.migrate import apply_migrations
    from backend.app.ops.macro_incremental_common import compute_since_date, read_observation_date_watermark

    con = duckdb.connect(":memory:")
    apply_migrations(con)
    insert_axis_observation(
        con,
        observation_id="obs-cftc",
        indicator_id="088691",
        obs_date=date(2026, 6, 1),
    )
    wm = read_observation_date_watermark(con, "088691")
    since = compute_since_date(wm, today=date(2026, 6, 30), advance_days=WEEKLY_ADVANCE_DAYS)
    assert since == date(2026, 6, 8)


def test_cftcIncremental_emptyResponse_whenWatermarkCurrent(
    cftc_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：水位已最新时 replay 返回 EMPTY_RESPONSE
    测试对象：cftc staging adapter + run_cftc_incremental
    目的/目标：since 之后无新观测时不写假行
    验证点：status==EMPTY_RESPONSE；axis_observation 行数不变
    失败含义：水位追上仍拉取或写入，增量语义错误
    """
    ctx = cftc_incremental_e2e_ctx
    with ctx["cm"].writer() as con:
        insert_axis_observation(
            con,
            observation_id="obs-cftc-seed",
            indicator_id="088691",
            obs_date=FIXED_TODAY,
        )
        before = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    with patch(
        "backend.app.datasources.fetch_ports.cftc_cot_port.datetime",
        wraps=datetime,
    ) as mock_dt:
        mock_dt.now.return_value = datetime.combine(FIXED_TODAY, time(0), tzinfo=UTC)
        report = run_cftc_incremental(
            ctx["orch"], service=ctx["service"], source_registry=ctx["registry"]
        )
    assert report.instrument_results[0]["status"] == "EMPTY_RESPONSE"
    with ctx["cm"].writer() as con:
        after = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    assert after == before


def test_cftcLive_noSilentFallbackWhenGateClosed(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：无 QMD_ALLOW_LIVE_FETCH 时 cftc live port 阻断
    测试对象：create_cftc_incremental_port(use_mock=False)
    目的/目标：EasyXT forbidden — live 被拒时不得静默退回 mock port
    验证点：抛 ProductLiveGateError · LIVE_FETCH_REJECTED
    失败含义：cftc_cot live 路径渗入 silent fallback
    """
    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    with pytest.raises(ProductLiveGateError) as exc_info:
        create_cftc_incremental_port(markets=DEFAULT_MARKETS, max_rows=3, use_mock=False)
    assert exc_info.value.code == "LIVE_FETCH_REJECTED"


@pytest.mark.network
def test_cftcIncremental_liveNetwork_writesAxisObservation(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：隔离 sandbox + CFTC live API 写 axis_observation
    测试对象：run_cftc_incremental(use_mock=False) + CftcLiveFetchPort
    目的/目标：QMD_ALLOW_LIVE_FETCH=1 时真网周频增量写 macro clean
    验证点：status∈{COMPLETED,EMPTY_RESPONSE}；COMPLETED 时 axis_observation≥1；DbInspector 表存在
    失败含义：Tier A cftc_cot live 金路径未接通或误写主库
    """
    ctx = bootstrap_macro_live_e2e_ctx(
        isolated_live_data_root,
        monkeypatch,
        source_id=SOURCE_ID,
        data_domain=DATA_DOMAIN,
        port_factory=lambda **kw: create_cftc_incremental_port(
            markets=DEFAULT_MARKETS, max_rows=3, **kw
        ),
        since_reader=read_since_dates_for_markets,
        instrument_ids=DEFAULT_MARKETS,
        service_builder=build_cftc_incremental_service,
        registry_factory=load_plain_source_registry,
    )
    report = run_cftc_incremental(
        ctx["orch"],
        service=ctx["service"],
        markets=DEFAULT_MARKETS,
        use_mock=False,
        source_registry=ctx["registry"],
    )
    status = report.instrument_results[0]["status"]
    assert status in {"COMPLETED", "EMPTY_RESPONSE"}
    inspect_report = DbInspector(ctx["cm"].db_path, ctx["raw_root"]).inspect()
    axis_table = next(t for t in inspect_report.key_tables if t["name"] == "axis_observation")
    assert axis_table["exists"] is True
    if status == "COMPLETED":
        with ctx["cm"].writer() as con:
            count = con.execute(
                "SELECT COUNT(*) FROM axis_observation WHERE indicator_id = '088691'"
            ).fetchone()[0]
        assert count >= 1
        assert axis_table["row_count"] is not None and axis_table["row_count"] >= 1


@pytest.mark.network
def test_cftcIncremental_liveNetwork_idempotentSecondRun(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：隔离 sandbox 连续两次 CFTC live 增量
    测试对象：run_cftc_incremental live 幂等 upsert
    目的/目标：重复 live 跑 observation_id PK 不膨胀行数
    验证点：first≥1；两次 COUNT(*) 相等
    失败含义：live 幂等失败会导致日常 sync 重复膨胀
    """
    ctx = bootstrap_macro_live_e2e_ctx(
        isolated_live_data_root,
        monkeypatch,
        source_id=SOURCE_ID,
        data_domain=DATA_DOMAIN,
        port_factory=lambda **kw: create_cftc_incremental_port(
            markets=DEFAULT_MARKETS, max_rows=3, **kw
        ),
        since_reader=read_since_dates_for_markets,
        instrument_ids=DEFAULT_MARKETS,
        service_builder=build_cftc_incremental_service,
        registry_factory=load_plain_source_registry,
    )
    run_cftc_incremental(
        ctx["orch"],
        service=ctx["service"],
        markets=DEFAULT_MARKETS,
        use_mock=False,
        source_registry=ctx["registry"],
    )
    with ctx["cm"].writer() as con:
        first = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    run_cftc_incremental(
        ctx["orch"],
        service=ctx["service"],
        markets=DEFAULT_MARKETS,
        use_mock=False,
        source_registry=ctx["registry"],
    )
    with ctx["cm"].writer() as con:
        second = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    assert first >= 1
    assert first == second
