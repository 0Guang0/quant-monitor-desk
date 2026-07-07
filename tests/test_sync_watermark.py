"""M-G1-03 P1-05 — unified sync watermark entry."""

from __future__ import annotations

from datetime import date

import pytest

from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.ops import fred_incremental_watermark as ops_wm
from backend.app.sync import watermark as sync_wm
from tests.fred_macro_incremental_support import insert_axis_observation
from tests.incremental_baostock_support import SYMBOL, seed_watermark_row


FIXED_TODAY = date(2026, 6, 30)


def test_syncWatermark_emptyTable_returnsNone(tmp_path) -> None:
    """覆盖范围：空表 watermark 读入口
    测试对象：read_watermark 无历史行
    目的/目标：macro/bar 域空表应返回 None 供 cold-start since 计算
    验证点：macro_series 与 cn_equity_daily_bar 均为 None
    失败含义：空表误报假水位，增量窗计算错误
    """
    cm = ConnectionManager(db_path=tmp_path / "wm-empty.duckdb")
    with cm.writer() as con:
        apply_migrations(con)
    with cm.writer() as con:
        assert sync_wm.read_watermark(con, "macro_series", "DGS10") is None
        assert sync_wm.read_watermark(con, "cn_equity_daily_bar", SYMBOL) is None


def test_syncWatermark_unknownDomain_raisesValueError(tmp_path) -> None:
    """覆盖范围：未知 domain 的 fail-closed
    测试对象：read_watermark(domain=...)
    目的/目标：非 macro/bar 域不得静默返回假水位
    验证点：pytest.raises(ValueError, match=unsupported watermark domain)
    失败含义：错误 domain 被当作有效水位，编排拉错表
    """
    cm = ConnectionManager(db_path=tmp_path / "wm-bad-domain.duckdb")
    with cm.writer() as con:
        apply_migrations(con)
    with cm.writer() as con:
        with pytest.raises(ValueError, match="unsupported watermark domain"):
            sync_wm.read_watermark(con, "not_a_real_domain", "key")


def test_syncWatermark_computeSinceDate_coldStartAndAdvance(tmp_path) -> None:
    """覆盖范围：compute_since_date 冷启动与水位+1 日边界
    测试对象：compute_since_date(watermark, cap_days, today)
    目的/目标：无水位走 capped cold-start；有水位走 watermark+advance_days
    验证点：None → today-cap（2026-05-31）；2026-06-10 → 2026-06-11（today 固定）
    失败含义：macro/bar 增量 since 窗与生产 compute_since_date 不一致
    """
    assert sync_wm.compute_since_date(None, cap_days=30, today=FIXED_TODAY) == date(2026, 5, 31)
    assert sync_wm.compute_since_date(date(2026, 6, 10), today=FIXED_TODAY) == date(2026, 6, 11)


def test_syncWatermark_readWatermark_singleEntryMacroAndBar(tmp_path) -> None:
    """覆盖范围：sync watermark 单一读入口
    测试对象：backend.app.sync.watermark.read_watermark
    目的/目标：macro_series 与 bar domain 共用 read_watermark(domain, key)
    验证点：ops watermark 改为 re-export，无双实现
    失败含义：增量窗口不一致导致重复/漏抓
    """
    cm = ConnectionManager(db_path=tmp_path / "wm.duckdb")
    with cm.writer() as con:
        apply_migrations(con)
        insert_axis_observation(
            con,
            observation_id="obs-dgs10",
            indicator_id="DGS10",
            obs_date=date(2026, 6, 10),
        )
        seed_watermark_row(con, "2026-06-15")

    with cm.writer() as con:
        macro_wm = sync_wm.read_watermark(con, "macro_series", "DGS10")
        bar_wm = sync_wm.read_watermark(con, "cn_equity_daily_bar", SYMBOL)

    assert macro_wm == date(2026, 6, 10)
    assert bar_wm == date(2026, 6, 15)
    assert ops_wm.read_observation_date_watermark is sync_wm.read_observation_date_watermark
    assert ops_wm.compute_since_date is sync_wm.compute_since_date
    assert ops_wm.read_since_dates_for_series is sync_wm.read_since_dates_for_series
