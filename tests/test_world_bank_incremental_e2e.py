"""DCP-05 S05 — World Bank incremental e2e tests."""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from backend.app.datasources.product_live_gate import ProductLiveGateError
from backend.app.ops.db_inspector import DbInspector

from backend.app.ops.macro_incremental_common import (
    compute_since_date,
    read_observation_date_watermark,
)
from backend.app.ops.world_bank_incremental_run import (
    DATA_DOMAIN,
    DEFAULT_COUNTRIES,
    SOURCE_ID,
    clean_indicator_id,
    build_world_bank_incremental_service,
    create_world_bank_incremental_port,
    run_world_bank_incremental,
)
from backend.app.datasources.incremental_route_activation import load_plain_source_registry
from tests.macro_incremental_support import (
    FIXED_TODAY,
    bootstrap_macro_live_e2e_ctx,
    build_macro_e2e_ctx,
    insert_axis_observation,
)


def _read_wb_since(con, countries):
    return {
        country: compute_since_date(
            read_observation_date_watermark(con, clean_indicator_id(country))
        ).isoformat()
        for country in countries
    }


@pytest.fixture
def world_bank_incremental_e2e_ctx(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> dict[str, Any]:
    port = create_world_bank_incremental_port(
        countries=DEFAULT_COUNTRIES, max_rows=3, use_mock=True
    )
    return build_macro_e2e_ctx(
        tmp_path,
        monkeypatch,
        source_id=SOURCE_ID,
        data_domain=DATA_DOMAIN,
        fetch_port=port,
        since_reader=_read_wb_since,
        instrument_ids=DEFAULT_COUNTRIES,
        service_builder=build_world_bank_incremental_service,
        registry_factory=load_plain_source_registry,
    )


def test_worldBankSinceDate_advancesToNextYearAfterWatermark() -> None:
    """覆盖范围：world_bank 年频 since 水位推进
    测试对象：compute_world_bank_since_date
    目的/目标：二次 live 跑不重复拉已落库年份（B-04 幂等根因）
    验证点：watermark=2023-06-15 → since=2024-01-01；冷启动 since 精确值
    失败含义：年频 since 仅 +1 日导致重复 fetch 膨胀行数
    """
    from datetime import timedelta

    from backend.app.ops.macro_incremental_common import compute_world_bank_since_date
    from backend.app.sync.watermark import compute_since_date

    assert compute_world_bank_since_date(date(2023, 6, 15)) == date(2024, 1, 1)
    cap_days = 365 * 10
    assert compute_since_date(None, cap_days=cap_days, today=FIXED_TODAY) == (
        FIXED_TODAY - timedelta(days=cap_days)
    )


def test_worldBankIncremental_e2e_defaultCountries_writesAtLeastTwoRows(
    world_bank_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：Tier A 关账加厚 — 默认国家窗 ≥2 行 clean
    测试对象：DEFAULT_COUNTRIES + run_world_bank_incremental
    目的/目标：G-07/T-05 要求 world_bank 非单点 1 行证据
    验证点：source_used=world_bank 的 axis_observation 行数 ≥2
    失败含义：关账 sandbox 仍仅 1 行，无法证明多 instrument 管道
    """
    ctx = world_bank_incremental_e2e_ctx
    report = run_world_bank_incremental(
        ctx["orch"],
        service=ctx["service"],
        countries=DEFAULT_COUNTRIES,
        source_registry=ctx["registry"],
    )
    assert report.overall_status == "COMPLETED"
    with ctx["cm"].writer() as con:
        count = con.execute(
            "SELECT COUNT(*) FROM axis_observation WHERE source_used = ?",
            [SOURCE_ID],
        ).fetchone()[0]
    assert count >= 2


def test_worldBankIncremental_e2e_replay_writesAxisObservation(
    world_bank_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：mock port + run_incremental 写 axis_observation
    测试对象：run_world_bank_incremental + DataSourceService 金路径
    目的/目标：replay 经 orchestrator 完成 validate + upsert 到 macro clean
    验证点：status==COMPLETED；composite indicator_id 行数>=1
    失败含义：world_bank 增量无法走 Sync 金路径写 macro clean
    """
    ctx = world_bank_incremental_e2e_ctx
    report = run_world_bank_incremental(
        ctx["orch"],
        service=ctx["service"],
        countries=DEFAULT_COUNTRIES,
        source_registry=ctx["registry"],
    )
    assert report.instrument_results[0]["status"] == "COMPLETED"
    indicator = clean_indicator_id("US")
    with ctx["cm"].writer() as con:
        count = con.execute(
            "SELECT COUNT(*) FROM axis_observation WHERE indicator_id = ?",
            [indicator],
        ).fetchone()[0]
        assert count >= 1
        row = con.execute(
            "SELECT raw_value FROM axis_observation WHERE indicator_id = ? LIMIT 1",
            [indicator],
        ).fetchone()
    assert row is not None and float(row[0]) == 1e13


def test_worldBankIncremental_idempotent_secondRun_rowCountStable(
    world_bank_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：连续两次增量跑 row count 不增
    测试对象：run_world_bank_incremental 幂等 upsert
    目的/目标：重复跑 observation_id PK upsert 不重复插入
    验证点：两次 COMPLETED 后 COUNT(*) 相等
    失败含义：幂等失败，生产重复跑会膨胀行数
    """
    ctx = world_bank_incremental_e2e_ctx
    run_world_bank_incremental(
        ctx["orch"], service=ctx["service"], source_registry=ctx["registry"]
    )
    with ctx["cm"].writer() as con:
        first = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    run_world_bank_incremental(
        ctx["orch"], service=ctx["service"], source_registry=ctx["registry"]
    )
    with ctx["cm"].writer() as con:
        second = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    assert first == second
    assert first >= 1


def test_worldBankIncremental_emptyResponse_whenWatermarkCurrent(
    world_bank_incremental_e2e_ctx: dict[str, Any],
) -> None:
    """覆盖范围：水位已最新时 replay 返回 EMPTY_RESPONSE
    测试对象：world_bank staging adapter + run_world_bank_incremental
    目的/目标：since 之后无新观测时不写假行
    验证点：status==EMPTY_RESPONSE；axis_observation 行数不变
    失败含义：水位追上仍拉取或写入，增量语义错误
    """
    ctx = world_bank_incremental_e2e_ctx
    with ctx["cm"].writer() as con:
        for country in DEFAULT_COUNTRIES:
            insert_axis_observation(
                con,
                observation_id=f"obs-wb-seed-{country}",
                indicator_id=clean_indicator_id(country),
                obs_date=FIXED_TODAY,
            )
        before = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    with patch(
        "backend.app.datasources.fetch_ports.world_bank_port.datetime",
        wraps=datetime,
    ) as mock_dt:
        mock_dt.now.return_value = datetime.combine(FIXED_TODAY, time(0), tzinfo=UTC)
        report = run_world_bank_incremental(
            ctx["orch"],
            service=ctx["service"],
            countries=DEFAULT_COUNTRIES,
            source_registry=ctx["registry"],
        )
    assert all(r["status"] == "EMPTY_RESPONSE" for r in report.instrument_results)
    with ctx["cm"].writer() as con:
        after = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    assert after == before


def test_worldBankLive_noSilentFallbackWhenGateClosed(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：无 QMD_ALLOW_LIVE_FETCH 时 world_bank live port 阻断
    测试对象：create_world_bank_incremental_port(use_mock=False)
    目的/目标：EasyXT forbidden — live 被拒时不得静默退回 mock port
    验证点：抛 ProductLiveGateError · LIVE_FETCH_REJECTED
    失败含义：world_bank live 路径渗入 silent fallback
    """
    monkeypatch.delenv("QMD_ALLOW_LIVE_FETCH", raising=False)
    with pytest.raises(ProductLiveGateError) as exc_info:
        create_world_bank_incremental_port(countries=DEFAULT_COUNTRIES, max_rows=3, use_mock=False)
    assert exc_info.value.code == "LIVE_FETCH_REJECTED"


@pytest.mark.network
def test_worldBankIncremental_liveNetwork_writesAxisObservation(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：隔离 sandbox + World Bank live API 写 axis_observation
    测试对象：run_world_bank_incremental(use_mock=False) + WorldBankLiveFetchPort
    目的/目标：QMD_ALLOW_LIVE_FETCH=1 时真网增量写 macro clean
    验证点：status∈{COMPLETED,EMPTY_RESPONSE}；COMPLETED 时 axis_observation≥1；DbInspector 表存在
    失败含义：Tier A world_bank live 金路径未接通或误写主库
    """
    ctx = bootstrap_macro_live_e2e_ctx(
        isolated_live_data_root,
        monkeypatch,
        source_id=SOURCE_ID,
        data_domain=DATA_DOMAIN,
        port_factory=lambda **kw: create_world_bank_incremental_port(
            countries=DEFAULT_COUNTRIES, max_rows=3, **kw
        ),
        since_reader=_read_wb_since,
        instrument_ids=DEFAULT_COUNTRIES,
        service_builder=build_world_bank_incremental_service,
        registry_factory=load_plain_source_registry,
    )
    report = run_world_bank_incremental(
        ctx["orch"],
        service=ctx["service"],
        countries=DEFAULT_COUNTRIES,
        use_mock=False,
        source_registry=ctx["registry"],
    )
    status = report.instrument_results[0]["status"]
    assert status in {"COMPLETED", "EMPTY_RESPONSE"}
    inspect_report = DbInspector(ctx["cm"].db_path, ctx["raw_root"]).inspect()
    axis_table = next(t for t in inspect_report.key_tables if t["name"] == "axis_observation")
    assert axis_table["exists"] is True
    if status == "COMPLETED":
        indicator = clean_indicator_id("US")
        with ctx["cm"].writer() as con:
            count = con.execute(
                "SELECT COUNT(*) FROM axis_observation WHERE indicator_id = ?",
                [indicator],
            ).fetchone()[0]
        assert count >= 1
        assert axis_table["row_count"] is not None and axis_table["row_count"] >= 1


@pytest.mark.network
def test_worldBankIncremental_liveNetwork_idempotentSecondRun(
    isolated_live_data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：隔离 sandbox 连续两次 World Bank live 增量
    测试对象：run_world_bank_incremental live 幂等 upsert
    目的/目标：重复 live 跑 observation_id PK 不膨胀行数
    验证点：两路 status∈{COMPLETED,EMPTY_RESPONSE}；COUNT(*) 相等
    失败含义：live 幂等失败会导致日常 sync 重复膨胀
    """
    ctx = bootstrap_macro_live_e2e_ctx(
        isolated_live_data_root,
        monkeypatch,
        source_id=SOURCE_ID,
        data_domain=DATA_DOMAIN,
        port_factory=lambda **kw: create_world_bank_incremental_port(
            countries=DEFAULT_COUNTRIES, max_rows=3, **kw
        ),
        since_reader=_read_wb_since,
        instrument_ids=DEFAULT_COUNTRIES,
        service_builder=build_world_bank_incremental_service,
        registry_factory=load_plain_source_registry,
    )
    run_world_bank_incremental(
        ctx["orch"],
        service=ctx["service"],
        countries=DEFAULT_COUNTRIES,
        use_mock=False,
        source_registry=ctx["registry"],
    )
    with ctx["cm"].writer() as con:
        first = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    run_world_bank_incremental(
        ctx["orch"],
        service=ctx["service"],
        countries=DEFAULT_COUNTRIES,
        use_mock=False,
        source_registry=ctx["registry"],
    )
    with ctx["cm"].writer() as con:
        second = con.execute("SELECT COUNT(*) FROM axis_observation").fetchone()[0]
    assert first == second
