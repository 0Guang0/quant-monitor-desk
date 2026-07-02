"""Read Layer 2 P0 cross-asset observations from Tier A clean (DCP-07 S00).

ponytail: macro index levels (VIXCLS) map raw_value → close; OHLC collapsed to
single level. Upgrade: dedicated bar table path for ETF/futures P0 assets.
"""

from __future__ import annotations

from datetime import UTC, datetime, time

from backend.app.layer2_sensors.models import CrossAssetObservation, CrossAssetRegistryEntry
from backend.app.layer2_sensors.sensor_loader import P0_CLEAN_REPLAY_ASSET_IDS

FORBIDDEN_FALLBACK_SOURCE_PREFIXES = ("staged_fixture", "macro_supplementary")

P0_ALLOWED_SOURCE_BY_ASSET: dict[str, str] = {
    "L2-VIX": "fred",
}

P0_ROW_CAPS: dict[str, int] = {
    "L2-VIX": 120,
}


class Layer2CleanObservationReadError(LookupError):
    """Clean table has no usable rows for the requested Layer2 P0 asset."""


class Layer2CleanObservationFallbackForbiddenError(RuntimeError):
    """Attempt to use a disallowed non-clean source (EasyXT-style fallback guard)."""


def resolve_clean_db_key(instrument_id: str) -> str:
    """Map registry instrument label (e.g. FRED:VIXCLS) → axis_observation.indicator_id."""
    label = instrument_id.strip()
    if label.startswith("FRED:"):
        key = label.split(":", 1)[1]
        if key:
            return key
    raise KeyError(f"no macro clean binding for instrument_id: {instrument_id!r}")


def resolve_read_limit(asset_id: str, *, requested: int | None = None) -> int:
    cap = P0_ROW_CAPS.get(asset_id, 500)
    if requested is None:
        return cap
    return min(requested, cap)


def _assert_clean_source_used(source_used: str, *, expected_source: str) -> None:
    if any(source_used.startswith(p) for p in FORBIDDEN_FALLBACK_SOURCE_PREFIXES):
        raise Layer2CleanObservationFallbackForbiddenError(
            f"refusing non-clean source_used for Layer2 clean read: {source_used!r}"
        )
    if source_used != expected_source:
        raise Layer2CleanObservationFallbackForbiddenError(
            f"refusing non-Tier-A source_used {source_used!r}; expected {expected_source!r}"
        )


def _row_to_observation(
    *,
    registry_entry: CrossAssetRegistryEntry,
    as_of_timestamp: datetime,
    publish_timestamp: datetime,
    fetch_time: datetime,
    raw_value: float | None,
    source_used: str,
    source_switched: bool,
    quality_flags: str | None,
) -> CrossAssetObservation:
    asset_id = registry_entry.asset_id
    expected = P0_ALLOWED_SOURCE_BY_ASSET.get(asset_id)
    if expected is None:
        raise KeyError(f"no P0 clean replay allowlist for asset: {asset_id!r}")
    _assert_clean_source_used(source_used, expected_source=expected)
    if source_switched:
        raise Layer2CleanObservationFallbackForbiddenError(
            f"refusing source_switched row for Layer2 clean read: {asset_id!r}"
        )
    quality_flag = ""
    if quality_flags:
        quality_flag = str(quality_flags).split(",")[0].strip()
    level = float(raw_value) if raw_value is not None else None
    trade_time = as_of_timestamp
    if trade_time.hour == 0 and trade_time.minute == 0:
        trade_time = datetime.combine(
            publish_timestamp.date(), time(16, 0), tzinfo=UTC
        )
    return CrossAssetObservation(
        asset_id=asset_id,
        trade_time=trade_time,
        market=registry_entry.market,
        asset_type=registry_entry.asset_type,
        open=level,
        high=level,
        low=level,
        close=level,
        pre_close=None,
        volume=None,
        amount=None,
        open_interest=None,
        source=source_used,
        as_of_timestamp=publish_timestamp,
        fetch_time=fetch_time,
        quality_flag=quality_flag,
    )


class Layer2CleanObservationReader:
    """Load P0 cross-asset macro rows from axis_observation; fail-closed if empty."""

    def read_observations(
        self,
        con,
        registry_entry: CrossAssetRegistryEntry,
        *,
        as_of_end: datetime | None = None,
        limit: int | None = None,
    ) -> list[CrossAssetObservation]:
        if registry_entry.asset_id not in P0_CLEAN_REPLAY_ASSET_IDS:
            raise KeyError(
                f"asset {registry_entry.asset_id!r} is not in Layer2 P0 clean replay whitelist"
            )
        db_key = resolve_clean_db_key(registry_entry.instrument_id)
        effective_limit = resolve_read_limit(registry_entry.asset_id, requested=limit)
        params: list[object] = [db_key]
        sql = """
            SELECT indicator_id, as_of_timestamp, publish_timestamp, fetch_time,
                   raw_value, source_used, source_switched, quality_flags, content_hash
            FROM axis_observation
            WHERE indicator_id = ?
        """
        if as_of_end is not None:
            sql += " AND publish_timestamp <= ?"
            params.append(as_of_end)
        sql += " ORDER BY publish_timestamp ASC LIMIT ?"
        params.append(effective_limit)
        rows = con.execute(sql, params).fetchall()
        if not rows:
            raise Layer2CleanObservationReadError(
                f"no clean axis_observation rows for {registry_entry.asset_id!r} "
                f"(db_key={db_key!r})"
            )
        out: list[CrossAssetObservation] = []
        for row in rows:
            as_of_ts = row[1]
            pub_ts = row[2]
            fetch_ts = row[3]
            if not isinstance(as_of_ts, datetime):
                as_of_ts = datetime.fromisoformat(str(as_of_ts))
            if not isinstance(pub_ts, datetime):
                pub_ts = datetime.fromisoformat(str(pub_ts))
            if not isinstance(fetch_ts, datetime):
                fetch_ts = datetime.fromisoformat(str(fetch_ts))
            if as_of_ts.tzinfo is None:
                as_of_ts = as_of_ts.replace(tzinfo=UTC)
            if pub_ts.tzinfo is None:
                pub_ts = pub_ts.replace(tzinfo=UTC)
            if fetch_ts.tzinfo is None:
                fetch_ts = fetch_ts.replace(tzinfo=UTC)
            # ponytail: replay seeds may stamp wall-clock fetch_time; clamp for as_of replay
            if as_of_end is not None and fetch_ts > as_of_end:
                fetch_ts = as_of_end
            out.append(
                _row_to_observation(
                    registry_entry=registry_entry,
                    as_of_timestamp=as_of_ts,
                    publish_timestamp=pub_ts,
                    fetch_time=fetch_ts,
                    raw_value=float(row[4]) if row[4] is not None else None,
                    source_used=str(row[5]),
                    source_switched=bool(row[6]),
                    quality_flags=row[7],
                )
            )
        return out
