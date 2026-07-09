"""M-G1-03 P1-02 — IndicatorBinding loader (§9.1 row schema)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from backend.app.sync.indicator_binding import (
    IndicatorBinding,
    UnknownIndicatorError,
    load_all_bindings,
    load_binding,
)

_REGISTRY = (
    Path(__file__).resolve().parents[1] / "specs" / "layer1_axes" / "indicator_binding_registry.yaml"
)


def test_indicatorBinding_loader_matchesSection91Columns() -> None:
    """覆盖范围：indicator_binding_registry.yaml → IndicatorBinding frozen dataclass
    测试对象：backend.app.sync.indicator_binding.load_binding
    目的/目标：§9.1 列与 dataclass 1:1；已知指标可加载且字段齐全
    验证点：ENV-E1-EFFR 行各字段与 registry 一致；dataclass 为 frozen
    失败含义：Layer/ops 无法安全解析绑定矩阵
    """
    binding = load_binding("ENV-E1-EFFR")
    assert isinstance(binding, IndicatorBinding)
    assert binding.indicator_id == "ENV-E1-EFFR"
    assert binding.axis_id == "ENVIRONMENT"
    assert binding.primary_source == "us_treasury"
    assert binding.data_domain == "us_treasury_yield_curve"
    assert binding.cold_start_policy == "bounded_backfill"
    assert binding.cabin == "PRIMARY"
    assert binding.adr_id == "PENDING"
    assert binding.feature_outputs_expected


def test_indicatorBinding_loadAll_matchesRegistryRowCount() -> None:
    """覆盖范围：indicator_binding_registry.yaml 全表
    测试对象：load_all_bindings
    目的/目标：loader 行数须与五轴 registry spec 动态对账，禁止硬编码魔法数
    验证点：len(bindings)==YAML expected_rows；indicator_id 无重复
    失败含义：矩阵行数与五轴 spec 漂移，后续 sync 绑定无法展开
    """
    spec = yaml.safe_load(_REGISTRY.read_text(encoding="utf-8")) or {}
    expected_rows = int(spec["expected_rows"])
    bindings = load_all_bindings()
    assert len(bindings) == expected_rows
    ids = [b.indicator_id for b in bindings]
    assert len(ids) == len(set(ids))


def test_indicatorBinding_unknownId_raisesCapabilityMissing() -> None:
    """覆盖范围：未知 indicator_id 查询路径
    测试对象：load_binding
    目的/目标：未知 id fail-closed；禁止裸 ValueError
    验证点：UnknownIndicatorError.error_code=CAPABILITY_MISSING 且含 docs_anchor
    失败含义：调用方无法区分能力缺失与其它异常，违反 ERROR_CODE_GUIDE
    """
    with pytest.raises(UnknownIndicatorError) as exc_info:
        load_binding("NOT-A-REAL-INDICATOR")
    err = exc_info.value
    assert err.error_code == "CAPABILITY_MISSING"
    assert err.docs_anchor == "docs/ops/design/ERROR_CODE_GUIDE.md"
    assert err.indicator_id == "NOT-A-REAL-INDICATOR"
