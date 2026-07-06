"""FRED macro incremental watermark reader (R3-DCP-02).

Re-exports unified sync/watermark SSOT (M-G1-03 P1-05).
"""

from __future__ import annotations

from backend.app.sync.watermark import (
    compute_since_date,
    read_observation_date_watermark,
    read_since_dates_for_series,
)

STAGING_TABLE = "stg_axis_observation_smoke"


def enabled_fred_source_registry():
    """Enable fred + macro_series on a loaded SourceRegistry (incremental CLI/tests).

    ponytail: source_registry.yaml keeps fred disabled-by-default; this runtime patch
    enables the route for incremental CLI/tests until registry reconcile (Wave 3 P7).
    Upgrade path: remove patch when specs/datasource_registry marks fred enabled + domain on.
    """
    from backend.app.datasources.source_registry import DomainRoleBinding, SourceRegistry

    registry = SourceRegistry()
    registry.load()
    rec = registry.get("fred")
    object.__setattr__(rec, "is_enabled", True)
    orig = registry.get_domain_roles

    def _domain_enabled(domain: str):
        binding = orig(domain)
        if domain != "macro_series":
            return binding
        return DomainRoleBinding(
            primary_source_id="fred",
            validation_source_id=binding.validation_source_id,
            fallback_policy=binding.fallback_policy,
            domain_enabled_by_default=True,
            fallback_source_ids=binding.fallback_source_ids,
        )

    registry.get_domain_roles = _domain_enabled  # type: ignore[method-assign]
    return registry


__all__ = [
    "STAGING_TABLE",
    "compute_since_date",
    "enabled_fred_source_registry",
    "read_observation_date_watermark",
    "read_since_dates_for_series",
]
