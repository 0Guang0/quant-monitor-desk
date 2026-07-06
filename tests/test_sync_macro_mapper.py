"""M-G1-03 P1-06 — sync domain row mappers (pure functions)."""

from __future__ import annotations

import inspect

from backend.app.sync.mappers import macro_series as mapper_mod
from backend.app.sync.mappers.macro_series import map_macro_series_bundle_to_axis_observations


def test_syncMacroMapper_axisObservation_pureNoOrchestrator() -> None:
    """覆盖范围：macro_series → axis_observation mapper
    测试对象：backend.app.sync.mappers.*
    目的/目标：mapper 为纯函数；无 orchestrator/watermark 调用
    验证点：单测覆盖 macro→axis_observation 字段映射
    失败含义：mapper 与编排耦合，无法复用 BindingSyncExecutor
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

    source = inspect.getsource(mapper_mod)
    assert "orchestrator" not in source
    assert "read_watermark" not in source
    assert "DataSyncOrchestrator" not in source
