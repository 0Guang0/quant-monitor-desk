"""CNINFO metadata incremental watermark reader (R3-DCP-05 S07)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

STAGING_TABLE = "stg_disclosure_smoke"
METADATA_LOOKBACK_DAYS = 30


def read_metadata_publish_watermark(con, instrument_id: str) -> date | None:
    """Return max publish date for one issuer in cn_announcement_clean."""
    row = con.execute(
        """
        SELECT MAX(CAST(publish_timestamp AS DATE))
        FROM cn_announcement_clean
        WHERE instrument_id = ?
        """,
        [instrument_id],
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
    cap_days: int = METADATA_LOOKBACK_DAYS,
    today: date | None = None,
) -> date:
    ref = today or datetime.now(UTC).date()
    if watermark is None:
        return ref - timedelta(days=cap_days)
    return watermark + timedelta(days=1)


def read_since_date_for_instrument(
    con,
    instrument_id: str,
    *,
    cap_days: int = METADATA_LOOKBACK_DAYS,
    today: date | None = None,
) -> str:
    return compute_since_date(
        read_metadata_publish_watermark(con, instrument_id),
        cap_days=cap_days,
        today=today,
    ).isoformat()
