"""S04 — Liquidity axis clean read e2e (ADR-029 ponytail)."""

from __future__ import annotations

from datetime import date

from backend.app.layer1_axes.clean_observation_reader import (
    amihud_observations_from_bars,
    read_bar_history,
)
from backend.app.layer1_axes.feature_engine import AxisFeatureEngine
from backend.app.layer1_axes.interpretation import AxisInterpretationEngine
from tests.layer1_clean_e2e_support import (
    AS_OF,
    bootstrap_layer1_clean_db,
    seed_spy_bars,
)

LIQ_INDICATOR = "LIQ.B-I1.AMIHUD_ILLIQ"


def test_layer1Liquidity_cleanAmihudE2e_alphaVantageBars(tmp_path) -> None:
    """覆盖范围：流动性 P0 从 security_bar_1d 经 Amihud 代理贯通特征与解读
    测试对象：read_bar_history + amihud_observations_from_bars + AxisFeatureEngine + AxisInterpretationEngine
    目的/目标：ADR-029 ponytail（alpha_vantage bar）可产出 LIQ.B-I1.AMIHUD_ILLIQ 绿路径；非 staged_fixture
    验证点：len>=25；source_used==alpha_vantage；特征非 insufficient_history；解读 1 行
    失败含义：流动性轴无法从 Tier A bar clean 贯通 Layer1 面板语义
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    with cm.writer() as con:
        seed_spy_bars(con, n=60, start=date(2026, 1, 1))
        bars = read_bar_history(con, "SPY")
        history = amihud_observations_from_bars(
            bars, spec_indicator_id=LIQ_INDICATOR, as_of=AS_OF
        )

    assert len(history) >= 25
    assert all(o.indicator_id == LIQ_INDICATOR for o in history)
    assert all(o.source_used == "alpha_vantage" for o in history)
    assert all("staged_fixture" not in o.source_used for o in history)

    engine = AxisFeatureEngine(min_obs_required=25, window_len=40)
    current = history[-1]
    feat = engine.compute_features(
        as_of=AS_OF, observations=[current], history=history
    )[0]
    assert feat.indicator_id == LIQ_INDICATOR
    assert feat.state_bucket != "insufficient_history"
    assert feat.raw_value is not None and feat.raw_value > 0

    interp_rows = AxisInterpretationEngine().build_interpretation(
        as_of=AS_OF, features=[feat]
    )
    assert len(interp_rows) == 1
    assert interp_rows[0].indicator_id == LIQ_INDICATOR
    assert interp_rows[0].level_label == feat.state_bucket
    assert interp_rows[0].boundary_reminder == "不构成交易动作"
