"""S02 — CREDIT_STRESS CRD.CS1.BAA10Y clean read e2e."""

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

SPEC_INDICATOR = "CRD.CS1.BAA10Y"
DB_KEY = "BAA10Y"


def test_layer1CreditStress_cleanReadToFeatureAndInterpretation(tmp_path) -> None:
    """覆盖范围：信用压力轴 P0 从 Tier A clean 贯通特征与解读
    测试对象：read_macro_clean_observations → AxisFeatureEngine → AxisInterpretationEngine
    目的/目标：BAA10Y clean 种子经 spec id CRD.CS1.BAA10Y 完成非 fixture 垂直链路
    验证点：source_used==fred；indicator_id 正确；特征含 z_score；解读文案无交易动作词
    失败含义：信用轴 clean 垂直未接通或仍走 staged fixture 语义
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    start = date(2026, 1, 1)
    with cm.writer() as con:
        seed_macro_series(
            con,
            db_indicator_id=DB_KEY,
            n=60,
            start=start,
            base_value=1.8,
            source_used="fred",
            step=0.02,
        )
        history = read_macro_clean_observations(con, SPEC_INDICATOR, as_of_end=AS_OF)

    assert len(history) >= 30
    assert all(o.indicator_id == SPEC_INDICATOR for o in history)
    assert all(o.source_used == "fred" for o in history)
    assert all("staged_fixture" not in o.source_used for o in history)

    feature_engine = AxisFeatureEngine(min_obs_required=30, window_len=60)
    current = history[-1]
    features = feature_engine.compute_features(
        as_of=AS_OF,
        observations=[current],
        history=history,
    )
    assert len(features) == 1
    feat = features[0]
    assert feat.indicator_id == SPEC_INDICATOR
    assert feat.state_bucket != "insufficient_history"
    assert feat.z_score is not None
    assert "INSUFFICIENT_HISTORY" not in feat.quality_flags

    interpretations = AxisInterpretationEngine().build_interpretation(
        as_of=AS_OF,
        features=features,
    )
    assert len(interpretations) == 1
    interp = interpretations[0]
    assert interp.indicator_id == SPEC_INDICATOR
    assert interp.summary_sentence
    assert "买入" not in interp.summary_sentence
    assert "卖出" not in interp.summary_sentence
