"""SEC EDGAR incremental watermark reader (R3-DCP-05 S09)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from backend.app.datasources.fetch_ports.sec_edgar_port import MAX_FILINGS

STAGING_TABLE = "stg_us_disclosure_smoke"
FILING_LOOKBACK_DAYS = 120


def read_filing_date_watermark(con, cik: str) -> date | None:
    """Return max filing_date for one CIK in us_disclosure_clean."""
    row = con.execute(
        """
        SELECT MAX(CAST(filing_date AS DATE))
        FROM us_disclosure_clean
        WHERE cik = ?
        """,
        [cik],
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
    cap_days: int = FILING_LOOKBACK_DAYS,
    today: date | None = None,
) -> date:
    ref = today or datetime.now(UTC).date()
    if watermark is None:
        return ref - timedelta(days=min(cap_days, MAX_FILINGS))
    return watermark + timedelta(days=1)


def enabled_sec_edgar_source_registry():
    from backend.app.datasources.source_registry import DomainRoleBinding, SourceRegistry

    registry = SourceRegistry()
    registry.load()
    rec = registry.get("sec_edgar")
    object.__setattr__(rec, "is_enabled", True)
    orig = registry.get_domain_roles

    def _domain_enabled(domain: str):
        binding = orig(domain)
        if domain != "us_filings":
            return binding
        return DomainRoleBinding(
            primary_source_id="sec_edgar",
            validation_source_id=binding.validation_source_id,
            fallback_policy=binding.fallback_policy,
            domain_enabled_by_default=True,
            fallback_source_ids=binding.fallback_source_ids,
        )

    registry.get_domain_roles = _domain_enabled  # type: ignore[method-assign]
    return registry


def read_since_date_for_cik(
    con,
    cik: str,
    *,
    cap_days: int = FILING_LOOKBACK_DAYS,
    today: date | None = None,
) -> str:
    return compute_since_date(
        read_filing_date_watermark(con, cik),
        cap_days=cap_days,
        today=today,
    ).isoformat()
