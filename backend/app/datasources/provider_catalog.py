"""Provider catalog YAML loader (R3FR-05 — architecture metadata only)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from backend.app.config import PROJECT_ROOT

DEFAULT_CATALOG_PATH = PROJECT_ROOT / "specs/datasource_registry/provider_catalog.yaml"


class ProviderCatalogError(ValueError):
    """Raised when provider catalog contract validation fails."""


def load_provider_catalog(path: Path | None = None) -> dict[str, Any]:
    """Load provider catalog YAML; returns parsed document root."""
    yaml_path = path or DEFAULT_CATALOG_PATH
    resolved = yaml_path.resolve()
    root = PROJECT_ROOT.resolve()
    if not resolved.is_relative_to(root):
        raise ProviderCatalogError(f"catalog path must be under project root, got: {yaml_path}")
    raw = yaml.safe_load(resolved.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ProviderCatalogError("provider catalog root must be a mapping")
    providers = raw.get("providers")
    if not isinstance(providers, list):
        raise ProviderCatalogError("providers must be a list")
    return raw


def provider_for_source(source_id: str, catalog: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Return the provider entry owning ``source_id``, or None if unknown."""
    doc = catalog if catalog is not None else load_provider_catalog()
    for entry in doc.get("providers") or []:
        if not isinstance(entry, dict):
            continue
        source_ids = entry.get("source_ids") or []
        if source_id in source_ids:
            return entry
    return None
