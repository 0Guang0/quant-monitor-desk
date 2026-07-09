"""Layer4 clean read unit tests (S08-READ / S08-ADAPTER)."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest

from backend.app.layer4_markets.clean_read import (
    USEquityCleanMarketAdapter,
    aggregate_breadth_from_bars,
    build_calendar_row,
    collect_clean_lineage_provenance,
)
from backend.app.layer4_markets.market_structure import Layer4MarketError, MarketStructureBuilder
from backend.app.layer4_markets.models import MarketBreadthSnapshotRow
from tests.layer4_clean_e2e_support import (
    AS_OF,
    TRADE_DATE,
    bootstrap_layer4_clean_db,
    seed_us_breadth_fixture,
    seed_us_equity_bar,
    seed_us_instrument_registry,
)


def test_cleanRead_aggregateBreadth_knownBars(tmp_path) -> None:
    """覆盖范围：security_bar_1d 已知 bar 集聚合 breadth
    测试对象：aggregate_breadth_from_bars
    目的/目标：证明 advancers/decliners/total_amount 可从 clean bar 可断言计算
    验证点：advancers==2；decliners==1；total_amount>0；source 含 tier_a_clean
    失败含义：US_EQ clean breadth 聚合逻辑未接线或计数错误
    """
    cm = bootstrap_layer4_clean_db(tmp_path)
    with cm.writer() as con:
        expected_adv, expected_dec, expected_amount = seed_us_breadth_fixture(con)
        row = aggregate_breadth_from_bars(
            con, market_id="US_EQ", trade_date=TRADE_DATE, as_of=AS_OF
        )

    assert row.advancers == expected_adv
    assert row.decliners == expected_dec
    assert row.total_amount == pytest.approx(expected_amount)
    assert "tier_a_clean" in row.source
    assert "staged_fixture" not in row.source


def test_cleanRead_calendarRow_fromSsot() -> None:
    """覆盖范围：US 交易日历 SSOT 合成 calendar 行
    测试对象：build_calendar_row
    目的/目标：证明 calendar 行来自 us_trading_calendar 而非 staged fixture
    验证点：is_trading_day 与 trade_date 一致；source==us_trading_calendar_ssot
    失败含义：calendar 仍依赖 fixture，R3H-07 SSOT 未接入 Layer4 clean 路径
    """
    row = build_calendar_row(market_id="US_EQ", trade_date=TRADE_DATE, as_of=AS_OF)
    assert row.is_trading_day is True
    assert row.source == "us_trading_calendar_ssot"
    assert row.market_id == "US_EQ"


def test_usEquityCleanAdapter_loadBreadthAndCalendar(tmp_path) -> None:
    """覆盖范围：USEquityCleanMarketAdapter 读 clean 表
    测试对象：USEquityCleanMarketAdapter.load_calendar / load_breadth
    目的/目标：adapter 仅读 clean + SSOT，不写 clean 表
    验证点：breadth advancers==2；calendar is_trading_day；source 无 staged_fixture
    失败含义：adapter 未封装 clean read，Builder 无法接 tier_a_clean 路径
    """
    cm = bootstrap_layer4_clean_db(tmp_path)
    with cm.writer() as con:
        seed_us_breadth_fixture(con)
        adapter = USEquityCleanMarketAdapter(con)
        calendar_rows = adapter.load_calendar(TRADE_DATE, AS_OF)
        breadth = adapter.load_breadth(TRADE_DATE, AS_OF)

    assert len(calendar_rows) == 1
    assert calendar_rows[0].is_trading_day is True
    assert breadth.advancers == 2
    assert breadth.decliners == 1
    assert "staged_fixture" not in breadth.source
    assert "staged_fixture" not in calendar_rows[0].source


def test_cleanRead_noBars_failClosed(tmp_path) -> None:
    """覆盖范围：无 clean bar 时的 fail-closed
    测试对象：aggregate_breadth_from_bars
    目的/目标：空 bar 集不得静默产出 breadth
    验证点：Layer4MarketError 含 no clean security_bar_1d
    失败含义：空输入仍绿，e2e 可能产出假 breadth
    """
    cm = bootstrap_layer4_clean_db(tmp_path)
    with cm.writer() as con:
        with pytest.raises(Layer4MarketError, match="no clean security_bar_1d"):
            aggregate_breadth_from_bars(
                con, market_id="US_EQ", trade_date=TRADE_DATE, as_of=AS_OF
            )


def test_cleanRead_flatBar_excludedFromAdvancersDecliners(tmp_path) -> None:
    """覆盖范围：close==pre_close 的 flat bar 聚合语义
    测试对象：aggregate_breadth_from_bars
    目的/目标：flat bar 不计入 advancers 或 decliners，但 amount 仍累加
    验证点：1 flat bar 时 advancers==0；decliners==0；total_amount>0
    失败含义：flat 语义被 >=/<= 改写，breadth 计数与调研不一致
    """
    cm = bootstrap_layer4_clean_db(tmp_path)
    with cm.writer() as con:
        seed_us_instrument_registry(con, instruments=(("US.AAPL", "AAPL"),))
        seed_us_equity_bar(
            con,
            instrument_id="US.AAPL",
            trade_date=TRADE_DATE,
            close=100.0,
            pre_close=100.0,
            amount=500.0,
        )
        row = aggregate_breadth_from_bars(
            con, market_id="US_EQ", trade_date=TRADE_DATE, as_of=AS_OF
        )
    assert row.advancers == 0
    assert row.decliners == 0
    assert row.total_amount == pytest.approx(500.0)


def test_cleanRead_nullPreClose_failClosed(tmp_path) -> None:
    """覆盖范围：pre_close 缺失时的 fail-closed
    测试对象：aggregate_breadth_from_bars
    目的/目标：NULL pre_close 须 Layer4MarketError，不得 TypeError
    验证点：pytest.raises(Layer4MarketError, match=missing pre_close)
    失败含义：脏数据抛未包装异常，Layer4 fail-closed 错误模型被破坏
    """
    cm = bootstrap_layer4_clean_db(tmp_path)
    with cm.writer() as con:
        seed_us_instrument_registry(con, instruments=(("US.AAPL", "AAPL"),))
        con.execute(
            """
            INSERT INTO security_bar_1d (
                instrument_id, trade_date, open, high, low, close, pre_close, volume, amount,
                adjustment_type, source_used, batch_id, quality_flags, created_at
            ) VALUES (?, ?, 100, 101, 99, 100, NULL, 1000, 100000, 'none', 'alpha_vantage', 'batch-x', NULL, CURRENT_TIMESTAMP)
            """,
            ["US.AAPL", TRADE_DATE.isoformat()],
        )
        with pytest.raises(Layer4MarketError, match="missing pre_close"):
            aggregate_breadth_from_bars(
                con, market_id="US_EQ", trade_date=TRADE_DATE, as_of=AS_OF
            )


def test_cleanRead_lineageNoBars_failClosed(tmp_path) -> None:
    """覆盖范围：lineage 收集空 bar 集 fail-closed
    测试对象：collect_clean_lineage_provenance
    目的/目标：空 bar 集不得产出 lineage provenance
    验证点：Layer4MarketError 含 no clean rows for lineage
    失败含义：空输入仍产出 lineage，e2e 可能绑定假 provenance
    """
    cm = bootstrap_layer4_clean_db(tmp_path)
    with cm.writer() as con:
        with pytest.raises(Layer4MarketError, match="no clean security_bar_1d"):
            collect_clean_lineage_provenance(
                con, market_id="US_EQ", trade_date=TRADE_DATE
            )


def test_buildCalendarRow_nonUsEq_failClosed() -> None:
    """覆盖范围：build_calendar_row 市场 ID 门禁
    测试对象：build_calendar_row
    目的/目标：非 US_EQ market_id 须 fail-closed
    验证点：CN_A → Layer4MarketError 含 only supports US_EQ
    失败含义：误传 CN_A 仍产出 US 日历行，调用方无 guard
    """
    with pytest.raises(Layer4MarketError, match="only supports 'US_EQ'"):
        build_calendar_row(market_id="CN_A", trade_date=TRADE_DATE, as_of=AS_OF)


def test_cleanReadBreadth_nonUsEq_failClosed(tmp_path) -> None:
    """覆盖范围：tier_a_clean Builder 非 US_EQ 负向
    测试对象：MarketStructureBuilder.build(source_mode=tier_a_clean)
    目的/目标：tier_a_clean 仅支持 US_EQ，CN_A 须 fail-closed
    验证点：CN_A → Layer4MarketError 含 only supports US_EQ
    失败含义：门禁放宽可 silent 接受非 P0 market_id
    """
    cm = bootstrap_layer4_clean_db(tmp_path)
    with cm.writer() as con:
        with pytest.raises(Layer4MarketError, match="only supports US_EQ"):
            MarketStructureBuilder().build(
                market_id="CN_A",
                trade_date=TRADE_DATE,
                as_of=AS_OF,
                source_mode="tier_a_clean",
                clean_con=con,
            )


def test_cleanReadBreadth_missingCleanCon_failClosed() -> None:
    """覆盖范围：tier_a_clean 缺 clean_con 负向
    测试对象：MarketStructureBuilder.build(source_mode=tier_a_clean)
    目的/目标：clean_con=None 须 fail-closed
    验证点：Layer4MarketError 含 requires clean_con
    失败含义：无 DB 连接仍 build，tier_a_clean 路径可假绿
    """
    with pytest.raises(Layer4MarketError, match="requires clean_con"):
        MarketStructureBuilder().build(
            market_id="US_EQ",
            trade_date=TRADE_DATE,
            as_of=AS_OF,
            source_mode="tier_a_clean",
            clean_con=None,
        )


def test_cleanReadBreadth_rejectsFutureBreadthObservation(tmp_path) -> None:
    """覆盖范围：tier_a_clean 未来 breadth 观测拒绝（builder guard，adapter 经 stub 注入）
    测试对象：MarketStructureBuilder._build_tier_a_clean + _finalize_market_build
    目的/目标：与 staged 022 对称，future breadth as_of 须 fail-closed
    验证点：stubbed adapter 返回 future breadth → Layer4MarketError 含 future
    失败含义：clean 路径缺 future 闸，look-ahead 可混入 snapshot
    """
    cm = bootstrap_layer4_clean_db(tmp_path)
    future_breadth = MarketBreadthSnapshotRow(
        market_id="US_EQ",
        trade_date=TRADE_DATE,
        advancers=2,
        decliners=1,
        total_amount=1_000_000.0,
        breadth_label="positive_breadth",
        source="tier_a_clean:security_bar_1d",
        quality_flag="ok",
        as_of_timestamp=AS_OF + timedelta(days=1),
    )
    with cm.writer() as con:
        seed_us_breadth_fixture(con)
        with patch.object(
            USEquityCleanMarketAdapter, "load_breadth", return_value=future_breadth
        ):
            with pytest.raises(Layer4MarketError, match="future"):
                MarketStructureBuilder().build(
                    market_id="US_EQ",
                    trade_date=TRADE_DATE,
                    as_of=AS_OF,
                    source_mode="tier_a_clean",
                    clean_con=con,
                )


def test_usEquityCleanAdapter_nullPreClose_failClosed(tmp_path) -> None:
    """覆盖范围：真实 adapter 读入畸形 clean bar（NULL pre_close）
    测试对象：USEquityCleanMarketAdapter.load_breadth
    目的/目标：adapter 路径须 fail-closed，不得依赖 builder stub
    验证点：NULL pre_close DB 行 → Layer4MarketError 含 missing pre_close
    失败含义：adapter 放行脏 bar，tier_a_clean 路径可产出假 breadth
    """
    cm = bootstrap_layer4_clean_db(tmp_path)
    with cm.writer() as con:
        seed_us_instrument_registry(con, instruments=(("US.AAPL", "AAPL"),))
        con.execute(
            """
            INSERT INTO security_bar_1d (
                instrument_id, trade_date, open, high, low, close, pre_close, volume, amount,
                adjustment_type, source_used, batch_id, quality_flags, created_at
            ) VALUES (?, ?, 100, 101, 99, 100, NULL, 1000, 100000, 'none', 'alpha_vantage', 'batch-bad', NULL, CURRENT_TIMESTAMP)
            """,
            ["US.AAPL", TRADE_DATE.isoformat()],
        )
        adapter = USEquityCleanMarketAdapter(con)
        with pytest.raises(Layer4MarketError, match="missing pre_close"):
            adapter.load_breadth(TRADE_DATE, AS_OF)
