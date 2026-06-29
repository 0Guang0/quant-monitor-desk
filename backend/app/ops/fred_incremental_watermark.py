"""FRED macro incremental watermark reader (R3-DCP-02).

ponytail: local ops module until track A exposes macro API on sync/watermark*.py.
Upgrade path: import macro reader from sync/watermark when merged.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta

from backend.app.datasources.fetch_ports.fred_port import MAX_WINDOW_DAYS

STAGING_TABLE = "stg_axis_observation_smoke"


def read_observation_date_watermark(con, indicator_id: str) -> date | None:
    """Return max observation date for one FRED series (indicator_id = series_id)."""
    row = con.execute(
        """
        SELECT MAX(CAST(publish_timestamp AS DATE))
        FROM axis_observation
        WHERE indicator_id = ?
        """,
        [indicator_id],
    ).fetchone()
    if row is None or row[0] is None:
        return None
    value = row[0]
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def compute_since_date(
    watermark: date | None,
    *,
    cap_days: int = MAX_WINDOW_DAYS,
    today: date | None = None,
) -> date:
    """Next fetch window start: watermark+1 day or capped cold-start lookback."""
    ref = today or datetime.now(UTC).date()
    if watermark is None:
        return ref - timedelta(days=cap_days)
    return watermark + timedelta(days=1)


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


def read_since_dates_for_series(
    con,
    series_ids: Sequence[str],
    *,
    cap_days: int = MAX_WINDOW_DAYS,
    today: date | None = None,
) -> dict[str, str]:
    """Per-series ISO since dates for FetchRequest.start_time injection."""
    return {
        series_id: compute_since_date(
            read_observation_date_watermark(con, series_id),
            cap_days=cap_days,
            today=today,
        ).isoformat()
        for series_id in series_ids
    }
