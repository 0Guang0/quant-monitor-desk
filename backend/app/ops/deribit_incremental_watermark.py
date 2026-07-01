"""Deribit crypto derivative incremental watermark reader (R3-DCP-05 S11)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

STAGING_TABLE = "stg_crypto_derivative_smoke"
SURFACE_LOOKBACK_DAYS = 30


def read_as_of_date_watermark(
    con,
    instrument_name: str,
    *,
    data_domain: str = "crypto_options_surface",
) -> date | None:
    """Return max as_of date for one instrument in crypto_derivative_clean."""
    row = con.execute(
        """
        SELECT MAX(CAST(as_of_timestamp AS DATE))
        FROM crypto_derivative_clean
        WHERE instrument_name = ? AND data_domain = ?
        """,
        [instrument_name, data_domain],
    ).fetchone()
    if row is None or row[0] is None:
        return None
    value = row[0]
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def compute_since_date(
    watermark: date | None,
    *,
    cap_days: int = SURFACE_LOOKBACK_DAYS,
    today: date | None = None,
) -> date:
    ref = today or datetime.now(UTC).date()
    if watermark is None:
        return ref - timedelta(days=cap_days)
    return watermark + timedelta(days=1)


def enabled_deribit_source_registry():
    from backend.app.datasources.source_registry import DomainRoleBinding, SourceRegistry

    registry = SourceRegistry()
    registry.load()
    rec = registry.get("deribit")
    object.__setattr__(rec, "is_enabled", True)
    orig = registry.get_domain_roles

    def _domain_enabled(domain: str):
        binding = orig(domain)
        if domain != "crypto_options_surface":
            return binding
        return DomainRoleBinding(
            primary_source_id="deribit",
            validation_source_id=binding.validation_source_id,
            fallback_policy=binding.fallback_policy,
            domain_enabled_by_default=True,
            fallback_source_ids=binding.fallback_source_ids,
        )

    registry.get_domain_roles = _domain_enabled  # type: ignore[method-assign]
    return registry


def read_since_date_for_instrument(
    con,
    instrument_name: str,
    *,
    data_domain: str = "crypto_options_surface",
    cap_days: int = SURFACE_LOOKBACK_DAYS,
    today: date | None = None,
) -> str:
    return compute_since_date(
        read_as_of_date_watermark(con, instrument_name, data_domain=data_domain),
        cap_days=cap_days,
        today=today,
    ).isoformat()
