"""R3H-07 US trading calendar SSOT tests (CAL-US).

覆盖范围：us_trading_calendar 模块 API 与 CAL-US 端到端负向（S07-01..04）。
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from backend.app.config import PROJECT_ROOT

_AV_REPLAY = (
    PROJECT_ROOT / "tests/fixtures/replay/market_data/alpha_vantage/aapl_daily_replay.json"
)
_STOOQ_REPLAY = PROJECT_ROOT / "tests/fixtures/replay/market_data/stooq/global_daily_replay.json"
_YAHOO_REPLAY = (
    PROJECT_ROOT / "tests/fixtures/replay/market_data/yahoo_finance/aapl_validation_replay.json"
)

_US_EQUITY_SOURCE_CASES = (
    (
        "backend.app.datasources.fetch_ports.yahoo_finance_port",
        "create_yahoo_finance_fetch_port",
        "yahoo_finance",
        "us_equity_daily_bar",
        "AAPL",
        {"symbols": ("AAPL",), "max_rows": 3},
    ),
    (
        "backend.app.datasources.fetch_ports.stooq_port",
        "create_stooq_fetch_port",
        "stooq",
        "us_equity_daily_bar",
        "AAPL.US",
        {"symbols": ("AAPL.US",), "max_rows": 3},
    ),
    (
        "backend.app.datasources.fetch_ports.alpha_vantage_port",
        "create_alpha_vantage_fetch_port",
        "alpha_vantage",
        "us_equity_daily_bar",
        "AAPL",
        {"symbols": ("AAPL",), "max_rows": 3, "use_mock": True},
    ),
)


def _market_req(source_id: str, data_domain: str, instrument_id: str, **overrides: object):
    from backend.app.datasources.fetch_result import FetchRequest

    return FetchRequest(
        run_id=f"r3h07-{source_id}",
        source_id=source_id,
        data_domain=data_domain,
        instrument_id=instrument_id,
        **overrides,
    )


@pytest.mark.parametrize(
    ("factory_path", "factory_name", "source_id", "data_domain", "instrument_id", "factory_kwargs"),
    _US_EQUITY_SOURCE_CASES,
)
def test_marketData_usSourceEvidence_windowKindTradingSessions(
    factory_path: str,
    factory_name: str,
    source_id: str,
    data_domain: str,
    instrument_id: str,
    factory_kwargs: dict[str, object],
) -> None:
    """覆盖范围：三源 US equity mock fetch evidence window_kind（S07-BOOT + S07-02）
    测试对象：yahoo_finance / stooq / alpha_vantage fetch_payload
    目的/目标：CAL-US 闭合后三源均 emit trading_sessions
    验证点：bundle.window_kind == trading_sessions
    失败含义：窗口语义仍为 calendar_days 或仅部分源接线
    """
    import importlib

    mod = importlib.import_module(factory_path)
    port = getattr(mod, factory_name)(**factory_kwargs)
    payload = port.fetch_payload(_market_req(source_id, data_domain, instrument_id))
    body = json.loads(payload.content.decode("utf-8"))
    assert body.get("window_kind") == "trading_sessions", source_id


@pytest.mark.parametrize(
    ("factory_path", "factory_name", "source_id", "instrument_id", "factory_kwargs"),
    [
        (path, name, sid, inst, kw)
        for path, name, sid, _dom, inst, kw in _US_EQUITY_SOURCE_CASES
    ],
)
def test_usEquityPort_explicitWindowSpan_120CalendarDaysWithinTradingSessionCap_allowed(
    factory_path: str,
    factory_name: str,
    source_id: str,
    instrument_id: str,
    factory_kwargs: dict[str, object],
) -> None:
    """覆盖范围：US equity 显式 start/end 窗 trading-session span cap（ADR-007）
    测试对象：三源 US equity fetch_payload 显式窗口校验
    目的/目标：120 自然日但 ≤120 交易日时不拒
    验证点：约 120 日历日窗 fetch 成功（无 PortError）
    失败含义：仍按自然日计界，误拒合法 trading-session 窗
    """
    import importlib

    from backend.app.datasources.fetch_ports.alpha_vantage_port import MAX_WINDOW_DAYS

    mod = importlib.import_module(factory_path)
    port = getattr(mod, factory_name)(**factory_kwargs)
    end = date(2024, 6, 14)
    start = end - timedelta(days=MAX_WINDOW_DAYS)
    payload = port.fetch_payload(
        _market_req(
            source_id,
            "us_equity_daily_bar",
            instrument_id,
            start_time=start.isoformat(),
            end_time=end.isoformat(),
        )
    )
    assert payload.row_count >= 0


@pytest.mark.parametrize(
    ("factory_path", "factory_name", "source_id", "instrument_id", "factory_kwargs"),
    [
        (path, name, sid, inst, kw)
        for path, name, sid, _dom, inst, kw in _US_EQUITY_SOURCE_CASES
    ],
)
def test_usEquityPort_explicitWindowSpan_overMaxTradingSessions_rejected(
    factory_path: str,
    factory_name: str,
    source_id: str,
    instrument_id: str,
    factory_kwargs: dict[str, object],
) -> None:
    """覆盖范围：US equity 显式窗超 120 交易日拒绝
    测试对象：三源 fetch_payload + reject_fetch_window_span_over_cap
    目的/目标：ADR-007 span cap 按 trading sessions 计界
    验证点：跨度含 >120 交易日时 PortError 且消息含 cap
    失败含义：超窗仍可拉取，recent_trading_window_start 未接入
    """
    import importlib

    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.ops.data_health_profiles.us_trading_calendar import get_trading_days

    mod = importlib.import_module(factory_path)
    port = getattr(mod, factory_name)(**factory_kwargs)
    end = date(2024, 6, 14)
    start = date(2023, 10, 1)
    assert len(get_trading_days(start, end)) > 120
    with pytest.raises(PortError, match="cap"):
        port.fetch_payload(
            _market_req(
                source_id,
                "us_equity_daily_bar",
                instrument_id,
                start_time=start.isoformat(),
                end_time=end.isoformat(),
            )
        )


def test_usTradingCalendar_thanksgiving2024_isNonTradingDay() -> None:
    """覆盖范围：US 固定联邦假日 Thanksgiving 2024
    测试对象：us_trading_calendar.is_trading_day
    目的/目标：S07-01 证明 NYSE 感恩节为非交易日
    验证点：date(2024, 11, 28) → False
    失败含义：假日表缺失 Thanksgiving，CAL-US 负向测无法闭合
    """
    from backend.app.ops.data_health_profiles.us_trading_calendar import is_trading_day

    assert is_trading_day(date(2024, 11, 28)) is False


def test_usTradingCalendar_dayAfterThanksgiving2024_isTradingDay() -> None:
    """覆盖范围：感恩节次日（Black Friday 2024 NYSE 开市）
    测试对象：us_trading_calendar.is_trading_day
    目的/目标：ADR-007 边界 — 仅假日闭市，相邻交易日仍开市
    验证点：date(2024, 11, 29) → True
    失败含义：假日规则过宽，误拒相邻交易日
    """
    from backend.app.ops.data_health_profiles.us_trading_calendar import is_trading_day

    assert is_trading_day(date(2024, 11, 29)) is True


def test_usTradingCalendar_regularWeekday_isTradingDay() -> None:
    """覆盖范围：普通周二交易日
    测试对象：us_trading_calendar.is_trading_day
    目的/目标：S07-01 基线交易日判定
    验证点：date(2024, 6, 11)（周二）→ True
    失败含义：weekday 判定错误，正常拉数窗被误拒
    """
    from backend.app.ops.data_health_profiles.us_trading_calendar import is_trading_day

    assert is_trading_day(date(2024, 6, 11)) is True


def test_usTradingCalendar_getTradingDays_respectsBounds() -> None:
    """覆盖范围：get_trading_days 有界范围与周末排除
    测试对象：us_trading_calendar.get_trading_days
    目的/目标：S07-01 证明 API 对称 CN 且范围有界（非万年历扫描）
    验证点：短窗内仅含交易日；超 _RANGE_END 日期 is_trading_day False
    失败含义：无界日历或周末未排除，window cap 语义不可信
    """
    from backend.app.ops.data_health_profiles.us_trading_calendar import (
        _RANGE_END,
        get_trading_days,
        is_trading_day,
    )

    days = get_trading_days(date(2024, 6, 10), date(2024, 6, 14))
    assert date(2024, 6, 10) in days
    assert date(2024, 6, 11) in days
    assert date(2024, 6, 15) not in days
    assert date(2024, 6, 16) not in days
    assert is_trading_day(_RANGE_END + timedelta(days=1)) is False


def test_usTradingCalendar_getMissingTradingDays_thanksgivingWeek() -> None:
    """覆盖范围：get_missing_trading_days 行为（感恩节周）
    测试对象：us_trading_calendar.get_missing_trading_days
    目的/目标：A5-P3-001 证明缺失交易日检测含周中交易日缺口（非假日本身）
    验证点：2024-11-25..29 窗内缺 11-27（周三）时返回该交易日
    失败含义：missing-days API 未闭合，数据健康探针无法检测假日周缺口
    """
    from backend.app.ops.data_health_profiles.us_trading_calendar import get_missing_trading_days

    missing = get_missing_trading_days(
        date(2024, 11, 25),
        date(2024, 11, 29),
        [date(2024, 11, 25), date(2024, 11, 26), date(2024, 11, 29)],
    )
    assert missing == [date(2024, 11, 27)]


def test_yahooFinance_fetchPayload_excludesHolidayBars(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：yahoo mock bar 生成过滤 US 假日
    测试对象：YahooFinanceMockFetchPort._mock_bars + filter_us_trading_day_bars
    目的/目标：S07-02 假日不得出现在 evidence bars
    验证点：注入含 Thanksgiving 的日期列表后 fetch 无 2024-11-28 bar
    失败含义：自然日 mock 仍产出假日 bar，负向窗未闭合
    """
    monkeypatch.setattr(
        "backend.app.datasources.fetch_window.recent_trading_dates",
        lambda **_: [date(2024, 11, 28), date(2024, 11, 27)],
    )
    from backend.app.datasources.fetch_ports.yahoo_finance_port import create_yahoo_finance_fetch_port

    port = create_yahoo_finance_fetch_port(symbols=("AAPL",), max_rows=3)
    payload = port.fetch_payload(_market_req("yahoo_finance", "us_equity_daily_bar", "AAPL"))
    body = json.loads(payload.content.decode("utf-8"))
    trade_dates = {bar["trade_date"] for bar in body.get("bars") or []}
    assert "2024-11-28" not in trade_dates
    assert trade_dates


def test_stooqFinance_fetchPayload_excludesHolidayBars(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：stooq US equity mock 假日 bar 负向（镜像 yahoo）
    测试对象：StooqMockFetchPort._mock_bars + mock_us_equity_daily_bars
    目的/目标：A5-P3-002 stooq 假日过滤有专用负向测
    验证点：注入 Thanksgiving 候选日后 fetch 无 2024-11-28 bar
    失败含义：stooq 路径假日 bar 未过滤，三源负向覆盖不对称
    """
    monkeypatch.setattr(
        "backend.app.datasources.fetch_window.recent_trading_dates",
        lambda **_: [date(2024, 11, 28), date(2024, 11, 27)],
    )
    from backend.app.datasources.fetch_ports.stooq_port import create_stooq_fetch_port

    port = create_stooq_fetch_port(symbols=("AAPL.US",), max_rows=3)
    payload = port.fetch_payload(_market_req("stooq", "us_equity_daily_bar", "AAPL.US"))
    body = json.loads(payload.content.decode("utf-8"))
    trade_dates = {bar["trade_date"] for bar in body.get("bars") or []}
    assert "2024-11-28" not in trade_dates
    assert trade_dates


def test_calUs_holidayWindow_usFetchProducesNoTradingBars(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：感恩节窗口 US fetch 负向（端到端 port）
    测试对象：alpha_vantage mock fetch + us_trading_calendar
    目的/目标：S07-04 固定假日窗不得产出有效交易日 bar
    验证点：仅 Thanksgiving 候选时被 filter 至空 → MarketDataEvidenceError 或 0 假日 bar
    失败含义：假日窗仍返回 bar，CAL-US 负向 AC 未闭合
    """
    monkeypatch.setattr(
        "backend.app.datasources.fetch_window.recent_trading_dates",
        lambda **_: [date(2024, 11, 28)],
    )
    from backend.app.datasources.fetch_ports.alpha_vantage_port import create_alpha_vantage_fetch_port
    from backend.app.datasources.normalizers.market_data import MarketDataEvidenceError

    port = create_alpha_vantage_fetch_port(symbols=("AAPL",), max_rows=3, use_mock=True)
    with pytest.raises(MarketDataEvidenceError, match="requires bars"):
        port.fetch_payload(_market_req("alpha_vantage", "us_equity_daily_bar", "AAPL"))


def test_datasourceService_usEquityFetch_exposesTradingSessionWindow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：DataSourceService 金路径 US equity fetch evidence
    测试对象：DataSourceService.fetch + yahoo_finance mock port
    目的/目标：S07-02 经 service 拉数后 bundle window_kind 可验证（R3H-10 金路径）
    验证点：FetchResult raw 文件 JSON window_kind == trading_sessions
    失败含义：service 路径与 port 直调 window 语义分叉
    """
    from backend.app.core.resource_guard import Decision, ResourceGuard
    from backend.app.datasources.fetch_ports.yahoo_finance_port import create_yahoo_finance_fetch_port
    from backend.app.datasources.service import DataSourceService
    from backend.app.db.connection import ConnectionManager
    from backend.app.db.migrate import apply_migrations
    from tests.service_path_support import enable_source_route

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    planner = enable_source_route(
        monkeypatch,
        source_id="yahoo_finance",
        data_domain="us_equity_daily_bar",
        primary_source_id="yahoo_finance",
    )
    orig_plan = planner.plan

    def _ready_yahoo_plan(**kwargs: object):
        from dataclasses import replace

        plan = orig_plan(**kwargs)
        if kwargs.get("data_domain") == "us_equity_daily_bar":
            return replace(plan, route_status="READY", selected_source_id="yahoo_finance")
        return plan

    monkeypatch.setattr(planner, "plan", _ready_yahoo_plan)
    port = create_yahoo_finance_fetch_port(symbols=("AAPL",), max_rows=3)

    db = tmp_path / "us-cal.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)

    service = DataSourceService(
        source_registry=planner._registry,
        route_planner=planner,
        data_root=tmp_path / "raw",
        fetch_port=port,
        staged_fixture_mode=True,
    )
    req = _market_req("yahoo_finance", "us_equity_daily_bar", "AAPL")
    with cm.writer() as con:
        result = service.fetch(req, con=con, job_id="job-us-cal")
    assert result.status == "SUCCESS"
    assert result.raw_file_paths
    body = json.loads(Path(result.raw_file_paths[0]).read_text(encoding="utf-8"))
    assert body.get("window_kind") == "trading_sessions"
