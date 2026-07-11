"""FRED registry/capability — runtime series cap（B01-FRED FRED-01）。

registry 默认禁用策略：`uv run python phase-scripts/check_fred_source_registry_policy.py --strict`
"""

from __future__ import annotations

import pytest


def test_fredRegistry_exceedsMaxSeries_rejected() -> None:
    """覆盖范围：FRED pilot series cap（≤5）
    测试对象：fred_sandbox_pilot.validate_series_whitelist
    目的/目标：超过 5 个 series 的请求须被拒绝
    验证点：6 个白名单 series 触发 FredPilotSeriesRejectedError
    失败含义：无 cap 会导致全 catalog 扫描风险
    """
    from backend.app.ops.fred_sandbox_pilot import (
        P0_SERIES_WHITELIST,
        FredPilotSeriesRejectedError,
        validate_series_whitelist,
    )

    too_many = tuple(sorted(P0_SERIES_WHITELIST)) + ("EXTRA",)
    with pytest.raises(FredPilotSeriesRejectedError, match="max 5 series"):
        validate_series_whitelist(too_many)
