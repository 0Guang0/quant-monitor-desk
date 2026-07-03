"""S01 — ENVIRONMENT axis Tier A clean read → feature → interpretation e2e."""

from __future__ import annotations

from datetime import date

from backend.app.layer1_axes.clean_observation_reader import read_macro_clean_observations
from backend.app.layer1_axes.feature_engine import AxisFeatureEngine
from backend.app.layer1_axes.interpretation import AxisInterpretationEngine
from tests.layer1_clean_e2e_support import (
    AS_OF,
    bootstrap_layer1_clean_db,
    seed_macro_series,
)

SPEC_INDICATOR = "ENV-E1-DGS10"
DB_SERIES = "DGS10"
SEED_ROWS = 40


def test_layer1Environment_cleanRead_featureInterpretation_e2e(tmp_path) -> None:
    """覆盖范围：ENVIRONMENT P0 从 axis_observation replay 经特征到解读的垂直链
    测试对象：read_macro_clean_observations、AxisFeatureEngine、AxisInterpretationEngine
    目的/目标：ENV-E1-DGS10←DGS10 fred clean 非 fixture 读入后可产出可断言特征与解读
    验证点：source_used==fred；indicator_id==ENV-E1-DGS10；特征非 insufficient_history；解读含边界提醒
    失败含义：环境轴 clean 读未接通 Tier A replay，或仍依赖 staged_fixture 语义
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    with cm.writer() as con:
        seed_macro_series(
            con,
            db_indicator_id=DB_SERIES,
            n=SEED_ROWS,
            start=date(2026, 1, 1),
            base_value=4.0,
            source_used="fred",
        )
        history = read_macro_clean_observations(
            con, SPEC_INDICATOR, as_of_end=AS_OF
        )

    assert len(history) >= 30
    assert all(obs.indicator_id == SPEC_INDICATOR for obs in history)
    assert history[-1].source_used == "fred"
    assert "staged_fixture" not in history[-1].source_used

    engine = AxisFeatureEngine(min_obs_required=30, window_len=SEED_ROWS)
    current = history[-1]
    features = engine.compute_features(
        as_of=AS_OF,
        observations=[current],
        history=history,
    )
    assert len(features) == 1
    feat = features[0]
    assert feat.indicator_id == SPEC_INDICATOR
    assert feat.state_bucket != "insufficient_history"
    assert feat.z_score is not None
    assert feat.valid_obs_count >= 30

    interp_rows = AxisInterpretationEngine().build_interpretation(
        as_of=AS_OF,
        features=features,
    )
    assert len(interp_rows) == 1
    row = interp_rows[0]
    assert row.indicator_id == SPEC_INDICATOR
    assert row.boundary_reminder == "不构成交易动作"
    assert row.generated_by == "layer1_interpretation_engine"
