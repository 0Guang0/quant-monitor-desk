"""Round 3D — model input whitelist runtime loader。

YAML schema/hardening：`uv run python phase-scripts/check_model_input_whitelist.py --strict`
"""

from __future__ import annotations

from backend.app.ops.staged_pilot import (
    assert_model_inputs_whitelist_present,
    load_pilot_v3_whitelist_scope,
)


def test_modelInputWhitelist_runtimeLoader_returnsBaostockRows() -> None:
    """覆盖范围：runtime whitelist loader 可读合并 YAML
    测试对象：assert_model_inputs_whitelist_present / load_pilot_v3_whitelist_scope
    目的/目标：staged pilot 路径须能加载真实白名单行，不只靠静态 YAML 扫描
    验证点：assert 不抛错；baostock 行非空且含 input_id/source_id
    失败含义：YAML 存在但 runtime loader 不可用，B01-WL pilot 无法 fail-closed
    """
    assert_model_inputs_whitelist_present()
    rows = load_pilot_v3_whitelist_scope()["baostock"]
    assert rows
    assert all(row.get("source_id") == "baostock" for row in rows)
    assert all(row.get("input_id") for row in rows)
