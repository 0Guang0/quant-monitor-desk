"""DCP-05 S04 — BIS incremental e2e tests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from backend.app.datasources.fetch_ports.bis_port import BisLiveFetchPort
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.ops.bis_incremental_run import (
    build_bis_incremental_service,
    create_bis_incremental_port,
    run_bis_incremental,
)
from backend.app.ops.bis_incremental_run import (
    DATA_DOMAIN,
    DEFAULT_COUNTRIES,
    SOURCE_ID,
    enabled_bis_source_registry,
    read_since_dates_for_instruments,
    watermark_start_year,
)
from tests.macro_incremental_support import build_macro_e2e_ctx, insert_axis_observation


@pytest.fixture
def bis_incremental_e2e_ctx(tmp_path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    port = create_bis_incremental_port(countries=DEFAULT_COUNTRIES, max_rows=3, use_mock=True)
    return build_macro_e2e_ctx(
        tmp_path,
        monkeypatch,
        source_id=SOURCE_ID,
        data_domain=DATA_DOMAIN,
        fetch_port=port,
        since_reader=read_since_dates_for_instruments,
        instrument_ids=DEFAULT_COUNTRIES,
        service_builder=build_bis_incremental_service,
        registry_factory=enabled_bis_source_registry,
    )


def test_bisIncremental_e2e_replay_writesAxisObservation(
    bis_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：mock port + run_incremental 写 axis_observation
    测试对象：run_bis_incremental + DataSourceService 金路径
    目的/目标：replay 经 orchestrator 完成 validate + upsert 到 macro clean
    验证点：status==COMPLETED；axis_observation 行数>=1；indicator_id==US
    失败含义：bis 增量无法走 Sync 金路径写 macro clean
    """
    ctx = bis_incremental_e2e_ctx
    report = run_bis_incremental(
        ctx["orch"],
        service=ctx["service"],
        countries=DEFAULT_COUNTRIES,
        source_registry=ctx["registry"],
    )
    assert report.instrument_results[0]["status"] == "COMPLETED"
    with ctx["cm"].writer() as con:
        count = con.execute(
            "SELECT COUNT(*) FROM axis_observation WHERE indicator_id = 'US'"
        ).fetchone()[0]
        assert count >= 1
        row = con.execute(
            "SELECT raw_value FROM axis_observation WHERE indicator_id = 'US' LIMIT 1"
        ).fetchone()
    assert row is not None and float(row[0]) == 5.25


def test_bisIncremental_idempotent_secondRun_rowCountStable(
    bis_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：连续两次增量跑 row count 不增
    测试对象：run_bis_incremental 幂等 upsert
    目的/目标：重复跑 observation_id PK upsert 不重复插入
    验证点：两次 COMPLETED 后 COUNT(*) 相等
    失败含义：幂等失败，生产重复跑会膨胀行数
    """
    ctx = bis_incremental_e2e_ctx
    run_bis_incremental(ctx["orch"], service=ctx["service"], source_registry=ctx["registry"])
    with ctx["cm"].writer() as con:
        first = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    run_bis_incremental(ctx["orch"], service=ctx["service"], source_registry=ctx["registry"])
    with ctx["cm"].writer() as con:
        second = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    assert first == second
    assert first >= 1


def test_bisIncremental_emptyResponse_whenWatermarkCurrent(
    bis_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：水位已最新时 replay 返回 EMPTY_RESPONSE
    测试对象：bis staging adapter + run_bis_incremental
    目的/目标：since 之后无新观测时不写假行
    验证点：status==EMPTY_RESPONSE；axis_observation 行数不变
    失败含义：水位追上仍拉取或写入，增量语义错误
    """
    ctx = bis_incremental_e2e_ctx
    today = datetime.now(UTC).date()
    with ctx["cm"].writer() as con:
        insert_axis_observation(
            con,
            observation_id="obs-bis-seed",
            indicator_id="US",
            obs_date=today,
        )
        before = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    report = run_bis_incremental(
        ctx["orch"], service=ctx["service"], source_registry=ctx["registry"]
    )
    assert report.instrument_results[0]["status"] == "EMPTY_RESPONSE"
    with ctx["cm"].writer() as con:
        after = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    assert after == before


def test_bisLivePort_startPeriod_fromWatermarkStartTime() -> None:
    """覆盖范围：BIS live port startPeriod 来自 FetchRequest.start_time（L2）
    测试对象：BisLiveFetchPort._resolve_start_year
    目的/目标：digital-oracle bis.py L54-66 对齐：水位年 → API startPeriod
    验证点：start_time=2023-06-15 → start_year=2023
    失败含义：live BIS 仍硬编码 start_year，增量窗错误
    """
    port = BisLiveFetchPort(countries=("US",), max_rows=3, data_domain="central_bank_policy")
    req = FetchRequest(
        run_id="bis-start-year",
        source_id="bis",
        data_domain="central_bank_policy",
        instrument_id="US",
        start_time="2023-06-15",
    )
    assert port._resolve_start_year(req) == 2023
    assert watermark_start_year("2023-06-15") == 2023
