"""S05 — SENTIMENT axis Tier A clean read e2e (COT LF net)."""

from __future__ import annotations

from datetime import date

from backend.app.layer1_axes.clean_observation_reader import read_macro_clean_observations
from backend.app.layer1_axes.feature_engine import AxisFeatureEngine
from backend.app.layer1_axes.interpretation import AxisInterpretationEngine
from tests.layer1_clean_e2e_support import (
    AS_OF,
    COT_SOURCE,
    bootstrap_layer1_clean_db,
    seed_cot_lf_net_weekly,
)

SPEC_INDICATOR = "SEN-S1-COT_LF_NET"


def test_layer1SentimentClean_e2e_cotLfNet_readFeatureInterpret(tmp_path) -> None:
    """覆盖范围：情绪轴 P0 COT 杠杆基金净头寸从 Tier A clean 读到特征与解读
    测试对象：read_macro_clean_observations → AxisFeatureEngine → AxisInterpretationEngine
    目的/目标：ADR-029 SEN-S1-COT_LF_NET 经 DB 088691 / cftc_cot 非 fixture 贯通 Layer1
    验证点：len>=20；spec indicator_id；source_used==cftc_cot；特征非 insufficient_history；解读含边界提醒
    失败含义：COT clean 读路径未接通或仍依赖 staged/EasyXT 式换源
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    with cm.writer() as con:
        seed_cot_lf_net_weekly(con, n=80, start=date(2024, 6, 3))
        observations = read_macro_clean_observations(
            con, SPEC_INDICATOR, as_of_end=AS_OF
        )

    assert len(observations) >= 20
    assert all(o.indicator_id == SPEC_INDICATOR for o in observations)
    assert observations[-1].source_used == COT_SOURCE
    assert "staged_fixture" not in observations[-1].source_used

    feature_engine = AxisFeatureEngine(
        frequency="weekly", min_obs_required=20, window_len=60
    )
    features = feature_engine.compute_features(
        as_of=AS_OF,
        observations=[observations[-1]],
        history=observations,
    )
    assert len(features) == 1
    feat = features[0]
    assert feat.indicator_id == SPEC_INDICATOR
    assert feat.state_bucket != "insufficient_history"
    assert "INSUFFICIENT_HISTORY" not in feat.quality_flags

    interpretations = AxisInterpretationEngine().build_interpretation(
        as_of=AS_OF, features=[feat]
    )
    assert len(interpretations) == 1
    interp = interpretations[0]
    assert interp.indicator_id == SPEC_INDICATOR
    assert interp.boundary_reminder == "不构成交易动作"
    assert interp.needs_human_review is False
