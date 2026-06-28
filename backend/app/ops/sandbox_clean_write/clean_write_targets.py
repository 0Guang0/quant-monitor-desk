"""Domain → clean table / staging / write_mode routing (R3H-06 SSOT)."""

from __future__ import annotations

from dataclasses import dataclass

BAR_DOMAINS = frozenset({"cn_equity_daily_bar"})
# ponytail: yahoo_finance → us_equity_daily_bar deferred Wave 3 (not registered here)
METADATA_DOMAINS = frozenset({"cn_announcements", "cn_filings", "cn_pdf_reports"})
MACRO_DOMAINS = frozenset({"macro_series"})


class CleanWriteTargetError(ValueError):
    """Domain has no registered clean write target."""


@dataclass(frozen=True)
class CleanWriteTarget:
    target_table: str
    staging_table: str
    write_mode: str
    primary_keys: tuple[str, ...]


def resolve_clean_write_target(domain: str) -> CleanWriteTarget:
    """Map data_domain to clean promote target (bar / disclosure / macro)."""
    if domain in BAR_DOMAINS:
        return CleanWriteTarget(
            target_table="security_bar_1d",
            staging_table="stg_foundation_smoke",
            write_mode="upsert_by_pk",
            primary_keys=("instrument_id", "trade_date", "adjustment_type"),
        )
    if domain in METADATA_DOMAINS:
        return CleanWriteTarget(
            target_table="cn_announcement_clean",
            staging_table="stg_disclosure_smoke",
            write_mode="upsert_by_pk",
            primary_keys=("announcement_id",),
        )
    if domain in MACRO_DOMAINS:
        return CleanWriteTarget(
            target_table="axis_observation",
            staging_table="stg_axis_observation_smoke",
            write_mode="upsert_by_pk",
            primary_keys=("observation_id",),
        )
    raise CleanWriteTargetError(f"no clean write target for domain: {domain!r}")
