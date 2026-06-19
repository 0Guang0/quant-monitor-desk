"""Source capability registry — operation/field authority (Round2.6 Phase C)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from backend.app.config import PROJECT_ROOT

# Legacy adapter domain names mapped to source_registry / capability domains.
ADAPTER_DOMAIN_COMPATIBILITY_MAP: dict[str, dict[str, str]] = {
    "akshare": {
        "market_bar_1d": "cn_equity_daily_bar",
        "capital_flow": "macro_supplementary",
    },
    "baostock": {
        "market_bar_1d": "cn_equity_daily_bar",
        "fundamental": "cn_equity_basic_financial",
    },
    "cninfo": {
        "announcement": "cn_announcements",
    },
    "qmt_xtdata": {
        "market_bar_1d": "cn_equity_daily_bar",
        "market_bar_1m": "cn_equity_minute_bar",
    },
    "yahoo_finance": {
        "market_bar_1d": "us_equity_daily_bar",
    },
}


class CapabilityRegistryError(ValueError):
    """Raised when capability contract validation fails."""


class UnknownCapabilityError(CapabilityRegistryError):
    """Raised when source/domain/operation is not declared."""


class OperationDisabledError(CapabilityRegistryError):
    """Raised when operation exists but is disabled by default."""


class SourceCapabilityRegistry:
    DEFAULT_YAML: Path = PROJECT_ROOT / "specs/datasource_registry/source_capabilities.yaml"

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or self.DEFAULT_YAML
        self._raw: dict[str, Any] = {}

    def load(self, path: Path | None = None) -> None:
        yaml_path = path or self._path
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        if not isinstance(raw, dict):
            raise CapabilityRegistryError("capability registry root must be a mapping")
        self._raw = raw

    @property
    def sources(self) -> dict[str, Any]:
        return dict(self._raw.get("sources") or {})

    def resolve_registry_domain(self, source_id: str, domain: str) -> str:
        compat = ADAPTER_DOMAIN_COMPATIBILITY_MAP.get(source_id, {})
        return compat.get(domain, domain)

    def is_capability_declared(self, source_id: str, data_domain: str) -> bool:
        registry_domain = self.resolve_registry_domain(source_id, data_domain)
        entry = self.sources.get(source_id) or {}
        return registry_domain in (entry.get("domains") or {})

    def assert_source_domain_operation(
        self,
        source_id: str,
        domain: str,
        operation: str,
    ) -> None:
        registry_domain = self.resolve_registry_domain(source_id, domain)
        entry = self.sources.get(source_id)
        if entry is None:
            raise UnknownCapabilityError(f"source {source_id!r} has no capability declaration")
        if entry.get("status") == "proposed_disabled_source":
            raise OperationDisabledError(f"source {source_id!r} is proposed_disabled_source")
        domains = entry.get("domains") or {}
        domain_cfg = domains.get(registry_domain)
        if domain_cfg is None:
            raise UnknownCapabilityError(
                f"domain {registry_domain!r} not declared for source {source_id!r}"
            )
        operations = domain_cfg.get("operations") or {}
        op_cfg = operations.get(operation)
        if op_cfg is None:
            raise UnknownCapabilityError(
                f"operation {operation!r} not declared for {source_id!r}/{registry_domain!r}"
            )
        if op_cfg.get("enabled_by_default") is False:
            raise OperationDisabledError(
                f"operation {operation!r} disabled for {source_id!r}/{registry_domain!r}"
            )
