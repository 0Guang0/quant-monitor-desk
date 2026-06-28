"""CN market data health profile (R3H-03 G2/G17 full closure).

L2 migrate:
- TradingCalendar gap detection via calendar_gap_rules + cn_trading_calendar
  (EasyXT smart_data_detector.py)
- OHLCV integrity semantics via ohlcv_rules (EasyXT data_integrity_checker.py patterns)
"""

from __future__ import annotations

from typing import Any

from backend.app.ops.data_health import DataHealthCheckResult
from backend.app.ops.data_health_profiles.calendar_gap_rules import check_missing_trading_day
from backend.app.ops.data_health_profiles.ohlcv_rules import run_ohlcv_rules

_CN_MIN_HISTORY = 2


def check_cn_market_bars(
    bars: list[dict[str, Any]],
    *,
    domain: str,
    source_id: str | None = None,
) -> list[DataHealthCheckResult]:
    """CN bar health: authoritative calendar FAIL + OHLCV integrity (G2/G17)."""
    results: list[DataHealthCheckResult] = []
    results.extend(
        check_missing_trading_day(
            bars,
            domain=domain,
            source_id=source_id,
            calendar_authority=True,
        )
    )
    results.extend(
        run_ohlcv_rules(
            bars,
            domain=domain,
            source_id=source_id,
            min_history=_CN_MIN_HISTORY,
        )
    )
    return results
