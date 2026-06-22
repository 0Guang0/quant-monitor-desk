"""Round2.6 Phase B/C — source capability and adapter domain contract tests."""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from typing import Any

import pytest
import yaml
from backend.app.datasources.capability_registry import (
    ADAPTER_DOMAIN_COMPATIBILITY_MAP,
    OperationDisabledError,
    SourceCapabilityRegistry,
    UnknownCapabilityError,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_REGISTRY = PROJECT_ROOT / "specs/datasource_registry/source_registry.yaml"
SOURCE_CAPABILITIES = PROJECT_ROOT / "specs/datasource_registry/source_capabilities.yaml"
ADAPTERS_PKG = "backend.app.datasources.adapters"


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_source_registry() -> dict[str, Any]:
    return load_yaml(SOURCE_REGISTRY)


def load_source_capabilities() -> dict[str, Any]:
    return load_yaml(SOURCE_CAPABILITIES)


def capability_domains_for_source(capabilities: dict[str, Any], source_id: str) -> set[str]:
    entry = (capabilities.get("sources") or {}).get(source_id) or {}
    return set((entry.get("domains") or {}).keys())


def iter_production_adapter_classes():
    """Yield (source_id, adapter_class) for concrete adapter modules."""
    import backend.app.datasources.adapters as adapters_pkg

    skip = {
        "fetch_port",
        "skeleton_base",
        "__init__",
    }
    for mod_info in pkgutil.iter_modules(adapters_pkg.__path__, adapters_pkg.__name__ + "."):
        stem = mod_info.name.rsplit(".", 1)[-1]
        if stem in skip:
            continue
        mod = importlib.import_module(mod_info.name)
        for attr in dir(mod):
            obj = getattr(mod, attr)
            if (
                isinstance(obj, type)
                and hasattr(obj, "source_id")
                and hasattr(obj, "supported_domains")
                and attr.endswith("Adapter")
            ):
                yield getattr(obj, "source_id"), obj


def test_everyAllowedDomain_hasCapabilityDeclaration() -> None:
    registry = load_source_registry()
    capabilities = load_source_capabilities()
    missing: list[str] = []
    for source in registry.get("sources") or []:
        source_id = source["source_id"]
        declared = capability_domains_for_source(capabilities, source_id)
        for domain in source.get("allowed_domains") or []:
            if domain not in declared:
                missing.append(f"{source_id}:{domain}")
    assert missing == [], f"allowed_domains missing capability declarations: {missing}"


def test_unknownSourceInRegistry_mustHaveCapabilityOrProposedStatus() -> None:
    registry = load_source_registry()
    capabilities = load_source_capabilities()
    cap_sources = set((capabilities.get("sources") or {}).keys())
    for source in registry.get("sources") or []:
        source_id = source["source_id"]
        if source_id not in cap_sources:
            raise AssertionError(
                f"source_registry source {source_id!r} has no entry in source_capabilities.yaml"
            )


def test_proposedDisabledSource_qmtXqshare_notEnabledByDefault() -> None:
    capabilities = load_source_capabilities()
    entry = (capabilities.get("sources") or {}).get("qmt_xqshare") or {}
    assert entry.get("status") == "proposed_disabled_source"
    for domain_cfg in (entry.get("domains") or {}).values():
        for op in (domain_cfg.get("operations") or {}).values():
            assert op.get("enabled_by_default") is False


def test_adapterSupportedDomains_reconciledToCapabilityRegistryOrCompatibilityMap() -> None:
    capabilities = load_source_capabilities()
    mismatches: list[str] = []
    for source_id, adapter_cls in iter_production_adapter_classes():
        compat = ADAPTER_DOMAIN_COMPATIBILITY_MAP.get(source_id, {})
        declared = capability_domains_for_source(capabilities, source_id)
        for legacy_domain in adapter_cls.supported_domains:
            registry_domain = compat.get(legacy_domain, legacy_domain)
            if registry_domain not in declared:
                mismatches.append(
                    f"{source_id}: adapter domain {legacy_domain!r} "
                    f"maps to {registry_domain!r} but capability missing"
                )
    assert mismatches == [], (
        "adapter supported_domains not reconciled to capabilities; "
        f"update adapters or ADAPTER_DOMAIN_COMPATIBILITY_MAP: {mismatches}"
    )


def test_compatibilityMap_doesNotEnableNewSources() -> None:
    registry_ids = {s["source_id"] for s in load_source_registry().get("sources") or []}
    assert set(ADAPTER_DOMAIN_COMPATIBILITY_MAP.keys()).issubset(registry_ids)


def test_unknownCapability_rejectedBeforeFetch() -> None:
    """Contract tracer: unknown domain must not appear in capability registry."""
    capabilities = load_source_capabilities()
    all_domains: set[str] = set()
    for _source_id, entry in (capabilities.get("sources") or {}).items():
        all_domains.update((entry.get("domains") or {}).keys())
    assert "market_bar_1d" not in all_domains, (
        "legacy abstract domain must not be declared as capability authority"
    )
    assert "cn_equity_daily_bar" in all_domains


def test_compatibilityMap_coversEveryProductionAdapter() -> None:
    capabilities = load_source_capabilities()
    for source_id, adapter_cls in iter_production_adapter_classes():
        compat = ADAPTER_DOMAIN_COMPATIBILITY_MAP.get(source_id, {})
        declared = capability_domains_for_source(capabilities, source_id)
        for legacy_domain in adapter_cls.supported_domains:
            if legacy_domain in declared:
                continue
            if legacy_domain not in compat:
                raise AssertionError(
                    f"{source_id}: legacy domain {legacy_domain!r} requires "
                    "ADAPTER_DOMAIN_COMPATIBILITY_MAP entry"
                )


def test_capabilityRegistry_assertSourceDomainOperation_acceptsKnown() -> None:
    reg = SourceCapabilityRegistry()
    reg.load()
    reg.assert_source_domain_operation("baostock", "cn_equity_daily_bar", "fetch_daily_bar")


def test_capabilityRegistry_assertSourceDomainOperation_rejectsUnknown() -> None:
    reg = SourceCapabilityRegistry()
    reg.load()
    with pytest.raises(UnknownCapabilityError):
        reg.assert_source_domain_operation("baostock", "cn_equity_realtime", "fetch_daily_bar")


def test_capabilityRegistry_resolveRegistryDomain_forLegacyAdapterDomain() -> None:
    reg = SourceCapabilityRegistry()
    reg.load()
    assert reg.resolve_registry_domain("baostock", "market_bar_1d") == "cn_equity_daily_bar"
    assert reg.is_capability_declared("baostock", "market_bar_1d") is True
    assert reg.is_capability_declared("baostock", "cn_equity_daily_bar") is True


def test_proposedDisabledSource_tdxPytdx_notEnabledByDefault() -> None:
    capabilities = load_source_capabilities()
    entry = (capabilities.get("sources") or {}).get("tdx_pytdx") or {}
    assert entry.get("status") == "proposed_disabled_source"
    for domain_cfg in (entry.get("domains") or {}).values():
        for op in (domain_cfg.get("operations") or {}).values():
            assert op.get("enabled_by_default") is False


def test_capabilityRegistry_rejectsProposedDisabledSource() -> None:
    reg = SourceCapabilityRegistry()
    reg.load()
    with pytest.raises(OperationDisabledError):
        reg.assert_source_domain_operation(
            "qmt_xqshare", "cn_equity_realtime", "fetch_realtime_quote_remote"
        )
