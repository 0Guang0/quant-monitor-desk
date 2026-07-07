"""FRED registry/capability guard tests (B01-FRED FRED-01)."""

from __future__ import annotations

import pytest
from tests.contract_gate_support import PROJECT_ROOT, load_yaml

SOURCE_REGISTRY = PROJECT_ROOT / "specs/datasource_registry/source_registry.yaml"
SOURCE_CAPABILITIES = PROJECT_ROOT / "specs/datasource_registry/source_capabilities.yaml"


def _fred_registry_entry() -> dict:
    registry = load_yaml(SOURCE_REGISTRY)
    for source in registry.get("sources") or []:
        if source.get("source_id") == "fred":
            return source
    raise AssertionError("fred source_id missing from source_registry.yaml")


def _fred_capability_entry() -> dict:
    capabilities = load_yaml(SOURCE_CAPABILITIES)
    return (capabilities.get("sources") or {}).get("fred") or {}


def test_fredRegistry_disabledByDefault_notProductionLive() -> None:
    """覆盖范围：fred sandbox/disabled-by-default 登记
    测试对象：specs/datasource_registry/source_registry.yaml · source_capabilities.yaml
    目的/目标：防止 fred 被默认可 production-live 路由
    验证点：fred 行存在、enabled_by_default=False、capability 无 production_default
    失败含义：registry YAML 为稳定契约；漂移会导致未授权 FRED 被当作生产源
    """
    entry = _fred_registry_entry()
    assert entry.get("enabled_by_default") is False
    assert "macro_series" in (entry.get("allowed_domains") or [])

    cap = _fred_capability_entry()
    assert cap.get("status") in {"sandbox_candidate", "proposed_disabled_source", "READY_WITH_EVIDENCE"}
    for domain_cfg in (cap.get("domains") or {}).values():
        for op in (domain_cfg.get("operations") or {}).values():
            assert op.get("production_default") is not True
            assert op.get("enabled_by_default") is False


def test_fredRegistry_exceedsMaxSeries_rejected() -> None:
    """覆盖范围：FRED pilot series cap（≤5）
    测试对象：fred_sandbox_pilot.validate_series_whitelist
    目的/目标：超过 5 个 series 的请求须被拒绝
    验证点：6 个白名单 series 触发 FredPilotSeriesRejectedError
    失败含义：无 cap 会导致全 catalog 扫描风险
    """
    from backend.app.ops.fred_sandbox_pilot import (
        P0_SERIES_WHITELIST,
        FredPilotSeriesRejectedError,
        validate_series_whitelist,
    )

    too_many = tuple(sorted(P0_SERIES_WHITELIST)) + ("EXTRA",)
    with pytest.raises(FredPilotSeriesRejectedError, match="max 5 series"):
        validate_series_whitelist(too_many)
