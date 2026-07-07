"""M-G1-03 P1-06 — sync domain row mappers (pure functions)."""

from __future__ import annotations

from backend.app.sync.mappers.macro_series import map_macro_series_bundle_to_axis_observations


def test_syncMacroMapper_axisObservation_mapsFieldsAndSkipsMissingValues() -> None:
    """覆盖范围：macro_series → axis_observation mapper
    测试对象：map_macro_series_bundle_to_axis_observations
    目的/目标：mapper 将 bundle 观测映射为 axis_observation 行并跳过缺失值
    验证点：`.` 值被过滤；有效行含 indicator_id/raw_value/observation_id
    失败含义：脏观测入库或 mapper 与编排耦合无法复用
    """
    bundle = {
        "source_id": "fred",
        "content_hash": "h1",
        "schema_hash": "s1",
        "observations": [
            {"series_id": "DGS10", "observation_date": "2026-06-01", "value": "."},
            {"series_id": "DGS10", "observation_date": "2026-06-02", "value": "4.1"},
        ],
    }
    rows = map_macro_series_bundle_to_axis_observations(bundle, series_id="DGS10")
    assert len(rows) == 1
    assert rows[0]["indicator_id"] == "DGS10"
    assert rows[0]["raw_value"] == 4.1
    assert rows[0]["observation_id"]
