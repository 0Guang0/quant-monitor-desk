"""Round 3D — 五层模型输入白名单语义契约测试（瘦身版：schema + hardening + runtime）。"""

from __future__ import annotations

from typing import Any

import pytest
from backend.app.ops.staged_pilot import (
    assert_model_inputs_whitelist_present,
    load_pilot_v3_whitelist_scope,
)

from tests.contract_gate_support import PROJECT_ROOT, load_yaml

MODEL_INPUTS = PROJECT_ROOT / "specs" / "model_inputs"

REQUIRED_ROW_FIELDS = (
    "input_id",
    "layer",
    "business_purpose",
    "data_domain",
    "source_id",
    "operation",
    "role",
    "readiness",
    "symbol_or_series",
    "window_cap",
    "row_cap",
    "requires_user_authorization",
    "allowed_next_gate",
    "forbidden_claims",
    "closure_test",
    "notes",
)

LAYER1_P0_SERIES = frozenset({"DGS10", "T10Y3M", "VIXCLS", "SP500", "DFII10"})
DCP06_CLEAN_REPLAY_PROVEN = frozenset({"DGS10", "BAA10Y", "VIXCLS", "SPY", "088691"})

WHITELIST_FILES = {
    "layer1": MODEL_INPUTS / "layer1_source_whitelist.yaml",
    "layer2": MODEL_INPUTS / "layer2_source_whitelist.yaml",
    "layer3": MODEL_INPUTS / "layer3_anchor_source_plan.yaml",
    "layer4": MODEL_INPUTS / "layer4_market_source_plan.yaml",
    "layer5": MODEL_INPUTS / "layer5_instrument_source_plan.yaml",
}


def _load_whitelist_rows(layer_key: str) -> list[dict[str, Any]]:
    path = WHITELIST_FILES[layer_key]
    if not path.is_file():
        pytest.fail(f"missing whitelist file: {path.relative_to(PROJECT_ROOT)}")
    doc = load_yaml(path)
    rows = doc.get("rows") or []
    if not isinstance(rows, list) or not rows:
        pytest.fail(f"{path.name} must contain non-empty rows list")
    return rows


def _series_value(row: dict[str, Any]) -> str:
    sym = row.get("symbol_or_series")
    if isinstance(sym, list):
        return str(sym[0]) if sym else ""
    return str(sym or "")


def _all_whitelist_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in WHITELIST_FILES:
        rows.extend(_load_whitelist_rows(key))
    return rows


@pytest.mark.parametrize("layer_key", tuple(WHITELIST_FILES))
def test_modelInputWhitelist_rowsHaveRequiredFields(layer_key: str) -> None:
    """覆盖范围：五层白名单行 schema
    测试对象：specs/model_inputs/*.yaml rows
    目的/目标：每行含任务卡 §6 全部必填字段
    验证点：REQUIRED_ROW_FIELDS 全集存在于每行
    失败含义：下游无法无歧义选择 fetch scope 与 readiness
    """
    for row in _load_whitelist_rows(layer_key):
        missing = [f for f in REQUIRED_ROW_FIELDS if f not in row]
        assert not missing, f"{row.get('input_id')}: missing {missing}"


def test_layer1_p0_dcp06_cleanReplayProven() -> None:
    """覆盖范围：DCP-06 五轴 P0 clean replay 绑定行
    测试对象：layer1_source_whitelist.yaml DCP-06 proven 行
    目的/目标：DGS10/BAA10Y/VIXCLS/SPY/088691 readiness=clean_replay_proven 且 caps 齐全
    验证点：五行存在；readiness；row_cap/window_cap 非空；非 production_candidate
    失败含义：K1 与 Tier A clean replay 证据漂移，FR-6 不成立
    """
    rows = _load_whitelist_rows("layer1")
    proven = [r for r in rows if _series_value(r) in DCP06_CLEAN_REPLAY_PROVEN]
    found = {_series_value(r) for r in proven}
    assert found == DCP06_CLEAN_REPLAY_PROVEN
    for row in proven:
        assert row.get("readiness") == "clean_replay_proven"
        assert row.get("readiness") != "production_candidate"
        assert row.get("row_cap") is not None and int(row["row_cap"]) > 0
        assert row.get("window_cap") is not None


def test_layer1_macro_supplementary_not_fred_primary() -> None:
    """覆盖范围：macro_supplementary 不得替代 FRED primary
    测试对象：layer1_source_whitelist.yaml akshare/macro_supplementary 行
    目的/目标：hardening — akshare 不得为 P0 FRED 序列 primary_candidate
    验证点：macro_supplementary 行 role≠primary_candidate；symbol 不与 P0 FRED 重叠作 primary
    失败含义：B2.5-O-05 可被错误闭合
    """
    rows = _load_whitelist_rows("layer1")
    macro_rows = [r for r in rows if r.get("data_domain") == "macro_supplementary"]
    assert macro_rows, "macro_supplementary domain must be documented explicitly"
    for row in macro_rows:
        assert row.get("source_id") == "akshare"
        assert row.get("role") != "primary_candidate"
        assert row.get("readiness") != "production_candidate"
        series = _series_value(row)
        if series in LAYER1_P0_SERIES:
            pytest.fail(
                f"macro_supplementary must not claim FRED P0 series {series} as primary path"
            )


def test_layer4_usMarket_deferredByInputId() -> None:
    """覆盖范围：Layer4 US 市场输入显式 deferred
    测试对象：layer4_market_source_plan.yaml L4-US-DEFERRED 行
    目的/目标：G2-029 — US 延期须绑定具体 input_id，非 notes 模糊匹配
    验证点：input_id=L4-US-DEFERRED；readiness==deferred；role==deferred
    失败含义：US 市场路由误标为可拉数或 readiness 漂移
    """
    rows = _load_whitelist_rows("layer4")
    us = next((r for r in rows if r.get("input_id") == "L4-US-DEFERRED"), None)
    assert us is not None
    assert us.get("readiness") == "deferred"
    assert us.get("role") == "deferred"
    assert _series_value(us) == "US"


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


def test_forbidden_akshare_not_primary_candidate() -> None:
    """覆盖范围：hardening akshare 角色上限
    测试对象：全部白名单 akshare 行
    目的/目标：akshare 不得为 primary_candidate
    验证点：source_id=akshare 时 role≠primary_candidate
    失败含义：聚合源越权成为 Primary
    """
    ak_rows = [r for r in _all_whitelist_rows() if r.get("source_id") == "akshare"]
    assert ak_rows
    for row in ak_rows:
        assert row.get("role") != "primary_candidate", row.get("input_id")


def test_forbidden_fred_not_production_candidate() -> None:
    """覆盖范围：hardening fred 角色上限
    测试对象：全部白名单 fred 行
    目的/目标：FRED pilot 未闭合前不得 production_candidate
    验证点：source_id=fred 时 readiness≠production_candidate
    失败含义：FRED 越权声称 production-live
    """
    fred_rows = [r for r in _all_whitelist_rows() if r.get("source_id") == "fred"]
    assert fred_rows
    for row in fred_rows:
        assert row.get("readiness") != "production_candidate", row.get("input_id")
        assert row.get("requires_user_authorization") is True
