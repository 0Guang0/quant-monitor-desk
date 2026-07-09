"""ADR-011 / performance_limits.md §8 bounded backfill cap contract tests."""

from __future__ import annotations

from datetime import date

import pytest

from backend.app.datasources.fetch_window import backfill_trading_days
from backend.app.sync.jobs import (
    ABSOLUTE_MAX_BACKFILL_SHARDS,
    ABSOLUTE_MAX_TRADING_DAYS,
    BackfillShardCapExceededError,
    DEFAULT_MAX_BACKFILL_SHARDS,
    MAX_TRADING_DAYS_PER_SHARD,
    load_bounded_backfill_cap,
    plan_backfill_shards,
)


def test_planBackfillShards_truncateToCap_withoutMaxShards_capsAtTwentyTradingDays() -> None:
    """覆盖范围：金路径 truncate 时无 max_shards 仍受 20 交易日硬顶（AUD-DOUBT-01）
    测试对象：plan_backfill_shards（orchestrator/scheduler/baostock 同款 truncate_to_cap=True）
    目的/目标：调度器/编排器宽窗回补须裁至 20 交易日再分片，不得无界拆片
    验证点：40 交易日窗 + truncate_to_cap → 4 片、总交易日=20
    失败含义：生产路径可绕过 performance_limits §8 硬顶
    """
    domain = "cn_equity_daily_bar"
    shards = plan_backfill_shards(
        date(2026, 1, 1),
        date(2026, 3, 5),
        data_domain=domain,
        truncate_to_cap=True,
    )
    assert len(shards) == 4
    total = sum(
        len(backfill_trading_days(domain, start, end)) for _tid, start, end in shards
    )
    assert total == 20


def test_planBackfillShards_withoutMaxShards_exceedsAbsoluteCap_failClosed() -> None:
    """覆盖范围：无 max_shards 时超 20 交易日 fail-closed
    测试对象：plan_backfill_shards 绝对硬顶
    目的/目标：禁止静默扩窗；须 truncate 或缩窗
    验证点：>20 交易日且无法截断时抛 BackfillShardCapExceededError
    失败含义：orchestrator 路径 cap 缺失
    """
    with pytest.raises(BackfillShardCapExceededError, match="absolute cap"):
        plan_backfill_shards(
            date(2025, 1, 1),
            date(2025, 6, 30),
            data_domain="cn_equity_daily_bar",
        )


def test_boundedBackfillCap_yamlAlignsPerformanceLimitsSection8() -> None:
    """覆盖范围：bounded_backfill_cap.yaml 与 performance_limits §8 数字一致
    测试对象：load_bounded_backfill_cap
    目的/目标：机器可读 cap 不得再使用 31 自然日/片旧模型
    验证点：max_trading_days_per_shard==5；absolute_max_trading_days==20；默认预算=5 交易日
    失败含义：运行副本与 design 权威脱节，CLI 上限不可审计
    """
    caps = load_bounded_backfill_cap().get("caps") or {}
    assert load_bounded_backfill_cap().get("docs_anchor") == (
        "docs/decisions/ADR-011-bounded-backfill-cap-and-ci-nightly.md"
    )
    assert caps["max_trading_days_per_shard"] == 5
    assert caps["absolute_max_trading_days"] == 20
    assert caps["default_max_backfill_shards"] == 1
    assert caps["default_max_backfill_shards"] * caps["max_trading_days_per_shard"] == 5
    assert caps["default_max_backfill_shards"] == DEFAULT_MAX_BACKFILL_SHARDS
    assert caps["absolute_max_backfill_shards"] == ABSOLUTE_MAX_BACKFILL_SHARDS


def test_planBackfillShards_thirtyCalendarDays_twentyTradingDays_passesAtHardCap() -> None:
    """覆盖范围：task_plan S5 RED — 30 自然日跨度、仅 20 交易日应 PASS
    测试对象：plan_backfill_shards + cn_trading_calendar
    目的/目标：计量按交易日而非自然日；恰达硬顶 20 交易日不得误拒
    验证点：2025-03-01..2025-03-30 日历跨度 30 天、交易日 20；max_shards=4 成功分 4 片
    失败含义：仍按自然日误判超限，operator 无法补满法定 20 交易日窗
    """
    domain = "cn_equity_daily_bar"
    start = date(2025, 3, 1)
    end = date(2025, 3, 30)
    trading_days = backfill_trading_days(domain, start, end)
    assert len(trading_days) == 20

    shards = plan_backfill_shards(
        start,
        end,
        data_domain=domain,
        max_shards=4,
    )
    assert len(shards) == 4
    total = sum(
        len(backfill_trading_days(domain, shard_start, shard_end))
        for _tid, shard_start, shard_end in shards
    )
    assert total == 20


def test_planBackfillShards_exceedsTwentyTradingDays_failClosed() -> None:
    """覆盖范围：task_plan S5 RED — 超 20 交易日须 fail-closed
    测试对象：plan_backfill_shards max_shards 与 absolute cap
    目的/目标：硬顶 20 交易日不可静默扩窗
    验证点：24 交易日窗 + max_shards=4 抛 BackfillShardCapExceededError
    失败含义：有界 backfill 硬顶失效
    """
    with pytest.raises(BackfillShardCapExceededError):
        plan_backfill_shards(
            date(2025, 3, 1),
            date(2025, 4, 4),
            data_domain="cn_equity_daily_bar",
            max_shards=4,
        )


def test_planBackfillShards_defaultShardBudget_allowsFiveTradingDaysOnly() -> None:
    """覆盖范围：CLI 默认预算 5 交易日（AUD-S5-01）
    测试对象：plan_backfill_shards + DEFAULT_MAX_BACKFILL_SHARDS
    目的/目标：默认 max_shards=1 → 整窗≤5 交易日，对齐 performance_limits §8 默认列
    验证点：5 交易日窗 PASS；6 交易日窗 FAIL
    失败含义：默认仍按 3 片=15 交易日，与 design「默认 5」冲突
    """
    domain = "cn_equity_daily_bar"
    five_day_start = date(2026, 1, 5)
    five_day_end = date(2026, 1, 9)
    assert len(backfill_trading_days(domain, five_day_start, five_day_end)) == 5

    shards_ok = plan_backfill_shards(
        five_day_start,
        five_day_end,
        data_domain=domain,
        max_shards=DEFAULT_MAX_BACKFILL_SHARDS,
    )
    assert len(shards_ok) == 1

    six_day_end = date(2026, 1, 12)
    assert len(backfill_trading_days(domain, five_day_start, six_day_end)) == 6
    with pytest.raises(BackfillShardCapExceededError):
        plan_backfill_shards(
            five_day_start,
            six_day_end,
            data_domain=domain,
            max_shards=DEFAULT_MAX_BACKFILL_SHARDS,
        )


def test_planBackfillShards_cnEquity_splitsByTradingDaysNotCalendarDays() -> None:
    """覆盖范围：A 股 backfill 分片按交易日计数
    测试对象：plan_backfill_shards + cn_trading_calendar
    目的/目标：单片最多 5 个交易日，不得按 timedelta 自然日切窗
    验证点：2026-01-05..2026-01-14 产生 2 片；每片交易日数≤5
    失败含义：周末/节假日被算进片宽，违背 ADR-011 交易日计量
    """
    domain = "cn_equity_daily_bar"
    shards = plan_backfill_shards(
        date(2026, 1, 5),
        date(2026, 1, 14),
        data_domain=domain,
        max_shards=4,
    )
    assert len(shards) == 2
    for _task_id, shard_start, shard_end in shards:
        count = len(backfill_trading_days(domain, shard_start, shard_end))
        assert count <= MAX_TRADING_DAYS_PER_SHARD


def test_planBackfillShards_cliCap_exceedsShardBudget_failClosed() -> None:
    """覆盖范围：显式 max_shards=3 时超 15 交易日须拒绝
    测试对象：plan_backfill_shards max_shards 边界
    目的/目标：无 truncate_to_cap 时 fail-closed，对齐 BACKFILL_CAP_EXCEEDED 路径
    验证点：2026-01-01..2026-06-30 + max_shards=3 抛 BackfillShardCapExceededError
    失败含义：operator 可绕过有界 backfill 触发大窗抓取
    """
    with pytest.raises(BackfillShardCapExceededError):
        plan_backfill_shards(
            date(2026, 1, 1),
            date(2026, 6, 30),
            data_domain="cn_equity_daily_bar",
            max_shards=3,
        )


def test_planBackfillShards_truncateToCap_clipsToShardBudget() -> None:
    """覆盖范围：truncate_to_cap 在交易日模型下截断
    测试对象：plan_backfill_shards truncate_to_cap
    目的/目标：显式 truncate 须可审计且 shard 数≤max_shards
    验证点：大窗 + max_shards=3 + truncate → 3 片、总交易日≤15
    失败含义：truncate 标志在 S5 交易日改造后失效
    """
    domain = "cn_equity_daily_bar"
    shards = plan_backfill_shards(
        date(2026, 1, 1),
        date(2026, 6, 30),
        data_domain=domain,
        max_shards=3,
        truncate_to_cap=True,
    )
    assert len(shards) == 3
    total_trading_days = sum(
        len(backfill_trading_days(domain, start, end)) for _tid, start, end in shards
    )
    assert total_trading_days <= 3 * MAX_TRADING_DAYS_PER_SHARD


def test_planBackfillShards_usEquity_usesUsTradingCalendar() -> None:
    """覆盖范围：美股日线域 backfill 分片
    测试对象：plan_backfill_shards + us_trading_calendar
    目的/目标：us_equity_daily_bar 须走 CAL-US，不得复用 A 股历
    验证点：2026-01-02..2026-01-16 仅 1 片（含 MLK 周末）
    失败含义：美股 backfill 误用 CN 历或自然日切窗
    """
    domain = "us_equity_daily_bar"
    shards = plan_backfill_shards(
        date(2026, 1, 2),
        date(2026, 1, 16),
        data_domain=domain,
        max_shards=1,
        truncate_to_cap=True,
    )
    assert len(shards) == 1
    assert len(backfill_trading_days(domain, shards[0][1], shards[0][2])) <= MAX_TRADING_DAYS_PER_SHARD


def test_backfillTradingDays_macroDomain_countsCalendarDays() -> None:
    """覆盖范围：macro 等非股类域 backfill 计数边界（AUD-S5-05）
    测试对象：backfill_trading_days 兜底分支
    目的/目标：无交易所日历时按日历日计数且行为可测，避免误以为走 CN/US 历
    验证点：macro_series 2026-01-01..2026-01-07 返回 7 个日历日
    失败含义：macro 域 silently 套用股类交易日历或计数不可审计
    """
    days = backfill_trading_days("macro_series", date(2026, 1, 1), date(2026, 1, 7))
    assert days == [
        date(2026, 1, 1),
        date(2026, 1, 2),
        date(2026, 1, 3),
        date(2026, 1, 4),
        date(2026, 1, 5),
        date(2026, 1, 6),
        date(2026, 1, 7),
    ]
