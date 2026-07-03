"""S03 — RISK_APPETITE axis Tier A clean read → feature → interpretation e2e."""

from __future__ import annotations

from datetime import date

from backend.app.layer1_axes.clean_observation_reader import read_macro_clean_observations
from backend.app.layer1_axes.feature_engine import AxisFeatureEngine
from backend.app.layer1_axes.interpretation import AxisInterpretationEngine
from tests.layer1_clean_e2e_support import AS_OF, bootstrap_layer1_clean_db, seed_macro_series

SPEC_INDICATOR = "RA.R1.VIXCLS_30D_IMPLIED_VOL"
DB_INDICATOR = "VIXCLS"


def test_layer1RiskAppetite_cleanReadFeatureInterpretation_e2e(tmp_path) -> None:
    """覆盖范围：风险偏好轴 P0 从 axis_observation clean 表 replay 到特征与解读
    测试对象：read_macro_clean_observations → AxisFeatureEngine → AxisInterpretationEngine
    目的/目标：VIXCLS fred clean 种子经 spec 映射 RA.R1.VIXCLS_30D_IMPLIED_VOL 全链路可断言
    验证点：len>=30；indicator_id 正确；source_used==fred 非 staged_fixture；特征 state_bucket 非 insufficient_history；解读含指标 id
    失败含义：风险偏好轴未接通 Tier A clean 或非 fixture 证明链断裂
    """
    cm = bootstrap_layer1_clean_db(tmp_path)
    start = date(2026, 1, 1)
    with cm.writer() as con:
        seed_macro_series(
            con,
            db_indicator_id=DB_INDICATOR,
            n=40,
            start=start,
            base_value=18.0,
            source_used="fred",
            step=0.15,
        )
        history = read_macro_clean_observations(con, SPEC_INDICATOR, as_of_end=AS_OF)
    assert len(history) >= 30
    assert all(o.indicator_id == SPEC_INDICATOR for o in history)
    assert all(o.source_used == "fred" for o in history)
    assert "staged_fixture" not in history[-1].source_used

    engine = AxisFeatureEngine(min_obs_required=30, window_len=40)
    current = history[-1]
    features = engine.compute_features(as_of=AS_OF, observations=[current], history=history)
    feat = features[0]
    assert feat.indicator_id == SPEC_INDICATOR
    assert feat.state_bucket != "insufficient_history"
    assert feat.z_score is not None

    interp_rows = AxisInterpretationEngine().build_interpretation(as_of=AS_OF, features=[feat])
    assert len(interp_rows) == 1
    assert SPEC_INDICATOR in interp_rows[0].level_interpretation
    assert interp_rows[0].boundary_reminder == "不构成交易动作"
