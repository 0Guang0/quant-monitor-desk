"""OHLCV profile rules — thin wrappers over data_health shared scans (R3FR-02)."""

from backend.app.ops.data_health import (
    check_duplicate_bar_keys,
    check_extreme_bar_returns,
    check_insufficient_history_bars,
    check_invalid_ohlc_relations,
    check_missing_ohlcv_fields,
    check_non_positive_ohlcv_prices,
    check_volume_outliers,
    run_profile_ohlcv_rules,
)

_MIN_HISTORY_DEFAULT = 2

check_insufficient_history = check_insufficient_history_bars
check_duplicate_primary_key = check_duplicate_bar_keys
check_missing_required_ohlcv_field = check_missing_ohlcv_fields
check_non_positive_price = check_non_positive_ohlcv_prices
check_invalid_ohlc = check_invalid_ohlc_relations
check_extreme_return = check_extreme_bar_returns
check_volume_outlier = check_volume_outliers
run_ohlcv_rules = run_profile_ohlcv_rules

__all__ = [
    "check_duplicate_primary_key",
    "check_extreme_return",
    "check_insufficient_history",
    "check_invalid_ohlc",
    "check_missing_required_ohlcv_field",
    "check_non_positive_price",
    "check_volume_outlier",
    "run_ohlcv_rules",
]
