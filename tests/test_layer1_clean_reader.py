"""S00 — Layer1CleanObservationReader contract tests."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from backend.app.layer1_axes.clean_observation_reader import (
    CleanObservationFallbackForbiddenError,
    CleanObservationReadError,
    amihud_observations_from_bars,
    read_bar_history,
    read_macro_clean_observations,
)
from tests.layer1_clean_e2e_support import (
    AS_OF,
    bootstrap_layer1_clean_db,
    seed_macro_series,
    seed_spy_bars,
)


def test_layer1CleanReader_macro_readsSpecIndicatorFromCleanTable(tmp_path) -> None:
    """覆盖范围：macro P0 从 axis_observation 读入并还原 spec indicator_id
    测试对象：read_macro_clean_observations
    目的/目标：DGS10 行映射为 ENV-E1-DGS10；source_used 为 tier A clean（fred）
    验证点：len>=30；indicator_id==ENV-E1-DGS10；source_used==fred；非 staged_fixture
    失败含义：clean 读路径未接通或错误回退到 fixture 语义
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    start = date(2026, 1, 1)
    with cm.writer() as con:
        seed_macro_series(con, db_indicator_id="DGS10", n=40, start=start, base_value=4.0)
        obs = read_macro_clean_observations(con, "ENV-E1-DGS10", as_of_end=AS_OF)
    assert len(obs) >= 30
    assert all(o.indicator_id == "ENV-E1-DGS10" for o in obs)
    assert obs[-1].source_used == "fred"
    assert "staged_fixture" not in obs[-1].source_used


def test_layer1CleanReader_emptyMacro_failClosedNoFallback(tmp_path) -> None:
    """覆盖范围：clean 表无行时禁止 silent 换源（EasyXT forbidden 对齐）
    测试对象：read_macro_clean_observations
    目的/目标：空结果须 CleanObservationReadError，不得返回空列表冒充成功
    验证点：pytest.raises(CleanObservationReadError)
    失败含义：空库仍“成功”会掩盖 Tier A 未写入或悄悄 fallback
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    with cm.writer() as con:
        with pytest.raises(CleanObservationReadError):
            read_macro_clean_observations(con, "ENV-E1-DGS10")


def test_layer1CleanReader_rejectsStagedFixtureSourceUsed(tmp_path) -> None:
    """覆盖范围：axis_observation 行若标 staged_fixture 须拒绝
    测试对象：read_macro_clean_observations
    目的/目标：非 clean 来源行不得进入 Layer1 clean 读路径
    验证点：pytest.raises(CleanObservationFallbackForbiddenError)
    失败含义：staged 行混入 PASS 路径
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    with cm.writer() as con:
        seed_macro_series(
            con,
            db_indicator_id="DGS10",
            n=5,
            start=date(2026, 2, 1),
            base_value=3.0,
            source_used="staged_fixture",
        )
        with pytest.raises(CleanObservationFallbackForbiddenError):
            read_macro_clean_observations(con, "ENV-E1-DGS10")


def test_layer1CleanReader_amihudFromSpyBars(tmp_path) -> None:
    """覆盖范围：流动性 P0 从 security_bar_1d 推导 Amihud 序列
    测试对象：read_bar_history + amihud_observations_from_bars
    目的/目标：ADR-029 ponytail bar 路径可产出 LIQ.B-I1.AMIHUD_ILLIQ 观测
    验证点：len>=25；indicator_id 正确；raw_value>0
    失败含义：流动性轴无法从 Tier A bar clean 读入
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    with cm.writer() as con:
        seed_spy_bars(con, n=60, start=date(2026, 1, 1))
        bars = read_bar_history(con, "SPY")
        obs = amihud_observations_from_bars(
            bars, spec_indicator_id="LIQ.B-I1.AMIHUD_ILLIQ", as_of=AS_OF
        )
    assert len(obs) >= 25
    assert obs[-1].indicator_id == "LIQ.B-I1.AMIHUD_ILLIQ"
    assert obs[-1].raw_value is not None and obs[-1].raw_value > 0
