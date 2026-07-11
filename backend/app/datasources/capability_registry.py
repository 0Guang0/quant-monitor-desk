"""Source capability registry — operation/field authority (Round2.6 Phase C)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from backend.app.config import PROJECT_ROOT

# ponytail: empty legacy alias map — adapters declare registry domains directly.
# Ceiling: no rename bridge; upgrade: add entries only when a real adapter domain rename lands.
ADAPTER_DOMAIN_COMPATIBILITY_MAP: dict[str, dict[str, str]] = {}


class CapabilityRegistryError(ValueError):
    """Raised when capability contract validation fails."""


class UnknownCapabilityError(CapabilityRegistryError):
    """Raised when source/domain/operation is not declared."""


class OperationDisabledError(CapabilityRegistryError):
    """Raised when operation exists but is disabled by default."""


_FIELD_KEYS = ("fields", "output", "observation_fields", "bundle_fields")


def _operation_declares_fields(op_cfg: dict[str, Any]) -> bool:
    return any(key in op_cfg for key in _FIELD_KEYS)


def _validate_capability_document(raw: dict[str, Any]) -> None:
    """Reject illegal capability docs at load (draft / gap / incomplete ops)."""
    if raw.get("status") == "draft":
        raise CapabilityRegistryError("capability registry status must not be draft")
    notes = raw.get("notes")
    if isinstance(notes, dict) and notes.get("implementation_gap"):
        raise CapabilityRegistryError(
            "implementation_gap must be resolved before capability registry load"
        )
    sources = raw.get("sources")
    if not isinstance(sources, dict) or not sources:
        raise CapabilityRegistryError("sources must be a non-empty mapping")
    for source_id, entry in sources.items():
        if not isinstance(entry, dict):
            raise CapabilityRegistryError(f"source {source_id!r} must be a mapping")
        if entry.get("status") == "draft":
            raise CapabilityRegistryError(f"source {source_id!r} status must not be draft")
        domains = entry.get("domains")
        if not isinstance(domains, dict) or not domains:
            raise CapabilityRegistryError(f"source {source_id!r} must declare domains")
        for domain, domain_cfg in domains.items():
            if not isinstance(domain_cfg, dict):
                raise CapabilityRegistryError(
                    f"source {source_id!r} domain {domain!r} must be a mapping"
                )
            operations = domain_cfg.get("operations")
            if not isinstance(operations, dict) or not operations:
                raise CapabilityRegistryError(
                    f"source {source_id!r} domain {domain!r} must declare operations"
                )
            for op_name, op_cfg in operations.items():
                if not isinstance(op_cfg, dict):
                    raise CapabilityRegistryError(
                        f"operation {op_name!r} for {source_id!r}/{domain!r} must be a mapping"
                    )
                if "frequency" not in op_cfg:
                    raise CapabilityRegistryError(
                        f"operation {op_name!r} for {source_id!r}/{domain!r} missing frequency"
                    )
                if not _operation_declares_fields(op_cfg):
                    raise CapabilityRegistryError(
                        f"operation {op_name!r} for {source_id!r}/{domain!r} "
                        f"missing fields|output"
                    )
                if "requires_auth" not in op_cfg:
                    raise CapabilityRegistryError(
                        f"operation {op_name!r} for {source_id!r}/{domain!r} missing requires_auth"
                    )


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
        _validate_capability_document(raw)
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

    def default_operation_for_domain(self, data_domain: str) -> str:
        """First enabled operation for domain across sources (DS-06)."""
        for entry in self.sources.values():
            domain_cfg = (entry.get("domains") or {}).get(data_domain)
            if not domain_cfg:
                continue
            for op_name, op_cfg in (domain_cfg.get("operations") or {}).items():
                if op_cfg.get("enabled_by_default", True):
                    return op_name
        return "fetch_daily_bar"

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
