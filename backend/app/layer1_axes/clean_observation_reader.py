"""Read Layer 1 P0 observations from Tier A clean tables (DCP-06 S00).

ponytail: macro rows use DCP-05 `indicator_id` = series/market code; spec
indicator_id is restored on `AxisObservation` via `P0_MACRO_DB_KEYS`.
Upgrade: single registry table mapping spec_id → clean key (Batch 6).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import UTC, datetime

from backend.app.layer1_axes.models import AxisObservation

FORBIDDEN_FALLBACK_SOURCE_PREFIXES = ("staged_fixture", "macro_supplementary")

# spec indicator_id → axis_observation.indicator_id (Tier A clean key)
P0_MACRO_DB_KEYS: dict[str, str] = {
    "ENV-E1-DGS10": "DGS10",
    "CRD.CS1.BAA10Y": "BAA10Y",
    "RA.R1.VIXCLS_30D_IMPLIED_VOL": "VIXCLS",
    "SEN-S1-COT_LF_NET": "088691",
}

P0_BAR_BINDING: dict[str, str] = {
    "LIQ.B-I1.AMIHUD_ILLIQ": "SPY",
}

# ponytail: mirror K1 whitelist row_cap/window_cap numbers; upgrade: load YAML at runtime
P0_ROW_CAPS: dict[str, int] = {
    "ENV-E1-DGS10": 500,
    "CRD.CS1.BAA10Y": 500,
    "RA.R1.VIXCLS_30D_IMPLIED_VOL": 120,
    "SEN-S1-COT_LF_NET": 120,
    "LIQ.B-I1.AMIHUD_ILLIQ": 300,
}

P0_WINDOW_CAPS: dict[str, int] = {
    "ENV-E1-DGS10": 252,
    "CRD.CS1.BAA10Y": 252,
    "RA.R1.VIXCLS_30D_IMPLIED_VOL": 60,
    "SEN-S1-COT_LF_NET": 104,
    "LIQ.B-I1.AMIHUD_ILLIQ": 60,
}


def resolve_read_limit(spec_indicator_id: str, *, requested: int | None = None) -> int:
    cap = P0_ROW_CAPS.get(spec_indicator_id, 500)
    if requested is None:
        return cap
    return min(requested, cap)


def resolve_window_cap(spec_indicator_id: str) -> int:
    return P0_WINDOW_CAPS.get(spec_indicator_id, 252)


def resolve_bar_read_limit(instrument_id: str, *, requested: int | None = None) -> int:
    spec_id = next(
        (sid for sid, sym in P0_BAR_BINDING.items() if sym == instrument_id),
        None,
    )
    cap = P0_ROW_CAPS.get(spec_id, 300) if spec_id else 300
    if requested is None:
        return cap
    return min(requested, cap)


class CleanObservationReadError(LookupError):
    """Clean table has no usable rows for the requested P0 indicator."""


class CleanObservationFallbackForbiddenError(RuntimeError):
    """Attempt to use a disallowed non-clean source (EasyXT-style fallback guard)."""


def resolve_macro_db_key(spec_indicator_id: str) -> str:
    key = P0_MACRO_DB_KEYS.get(spec_indicator_id)
    if key is None:
        raise KeyError(f"no macro clean binding for spec indicator: {spec_indicator_id!r}")
    return key


def _row_to_observation(
    *,
    spec_indicator_id: str,
    db_indicator_id: str,
    as_of_timestamp: datetime,
    publish_timestamp: datetime,
    raw_value: float | None,
    source_used: str,
    source_switched: bool,
    quality_flags: str | None,
) -> AxisObservation:
    if any(source_used.startswith(p) for p in FORBIDDEN_FALLBACK_SOURCE_PREFIXES):
        raise CleanObservationFallbackForbiddenError(
            f"refusing non-clean source_used for Layer1 clean read: {source_used!r}"
        )
    flags: tuple[str, ...] = ()
    if quality_flags:
        flags = tuple(f.strip() for f in str(quality_flags).split(",") if f.strip())
    return AxisObservation(
        indicator_id=spec_indicator_id,
        as_of_timestamp=as_of_timestamp,
        publish_timestamp=publish_timestamp,
        raw_value=raw_value,
        source_used=source_used,
        source_switched=bool(source_switched),
        quality_flags=flags,
    )


def read_macro_clean_observations(
    con,
    spec_indicator_id: str,
    *,
    as_of_end: datetime | None = None,
    limit: int | None = None,
) -> list[AxisObservation]:
    """Load macro/COT rows from axis_observation; fail-closed if empty."""
    db_key = resolve_macro_db_key(spec_indicator_id)
    effective_limit = resolve_read_limit(spec_indicator_id, requested=limit)
    params: list[object] = [db_key]
    sql = """
        SELECT indicator_id, as_of_timestamp, publish_timestamp, raw_value,
               source_used, source_switched, quality_flags
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
        raise CleanObservationReadError(
            f"no clean axis_observation rows for {spec_indicator_id!r} (db_key={db_key!r})"
        )
    out: list[AxisObservation] = []
    for row in rows:
        as_of_ts = row[1]
        pub_ts = row[2]
        if not isinstance(as_of_ts, datetime):
            as_of_ts = datetime.fromisoformat(str(as_of_ts))
        if not isinstance(pub_ts, datetime):
            pub_ts = datetime.fromisoformat(str(pub_ts))
        if as_of_ts.tzinfo is None:
            as_of_ts = as_of_ts.replace(tzinfo=UTC)
        if pub_ts.tzinfo is None:
            pub_ts = pub_ts.replace(tzinfo=UTC)
        out.append(
            _row_to_observation(
                spec_indicator_id=spec_indicator_id,
                db_indicator_id=str(row[0]),
                as_of_timestamp=as_of_ts,
                publish_timestamp=pub_ts,
                raw_value=float(row[3]) if row[3] is not None else None,
                source_used=str(row[4]),
                source_switched=bool(row[5]),
                quality_flags=row[6],
            )
        )
    return out


def read_bar_history(
    con,
    instrument_id: str,
    *,
    limit: int | None = None,
) -> list[dict[str, object]]:
    """Return ascending bar dicts from security_bar_1d."""
    effective_limit = resolve_bar_read_limit(instrument_id, requested=limit)
    rows = con.execute(
        """
        SELECT trade_date, open, high, low, close, volume, source_used
        FROM security_bar_1d
        WHERE instrument_id = ?
        ORDER BY trade_date ASC
        LIMIT ?
        """,
        [instrument_id, effective_limit],
    ).fetchall()
    if not rows:
        raise CleanObservationReadError(
            f"no clean security_bar_1d rows for instrument {instrument_id!r}"
        )
    bars: list[dict[str, object]] = []
    for row in rows:
        source_used = str(row[6] or "")
        if any(source_used.startswith(p) for p in FORBIDDEN_FALLBACK_SOURCE_PREFIXES):
            raise CleanObservationFallbackForbiddenError(
                f"refusing non-clean bar source_used: {source_used!r}"
            )
        bars.append(
            {
                "trade_date": str(row[0]),
                "open": float(row[1]) if row[1] is not None else None,
                "high": float(row[2]) if row[2] is not None else None,
                "low": float(row[3]) if row[3] is not None else None,
                "close": float(row[4]) if row[4] is not None else None,
                "volume": float(row[5]) if row[5] is not None else None,
                "source_used": source_used,
            }
        )
    return bars


def amihud_observations_from_bars(
    bars: Sequence[dict[str, object]],
    *,
    spec_indicator_id: str,
    as_of: datetime,
) -> list[AxisObservation]:
    """ponytail: daily Amihud proxy from OHLCV clean bars (ADR-029 liquidity anchor)."""
    if spec_indicator_id not in P0_BAR_BINDING:
        raise KeyError(spec_indicator_id)
    observations: list[AxisObservation] = []
    prev_close: float | None = None
    for bar in bars:
        close = bar.get("close")
        volume = bar.get("volume")
        high = bar.get("high")
        low = bar.get("low")
        if close is None or volume is None or float(volume) <= 0:
            prev_close = float(close) if close is not None else prev_close
            continue
        close_f = float(close)
        if prev_close is None or prev_close <= 0:
            prev_close = close_f
            continue
        typical = (float(high) + float(low) + close_f) / 3.0 if high is not None and low is not None else close_f
        dollar_vol = float(volume) * typical
        if dollar_vol <= 0:
            prev_close = close_f
            continue
        amihud = abs(math.log(close_f / prev_close)) / dollar_vol
        trade_date = str(bar["trade_date"])
        pub = datetime.fromisoformat(f"{trade_date}T16:00:00+00:00")
        observations.append(
            AxisObservation(
                indicator_id=spec_indicator_id,
                as_of_timestamp=as_of,
                publish_timestamp=pub,
                raw_value=amihud,
                source_used=str(bar.get("source_used") or "alpha_vantage"),
            )
        )
        prev_close = close_f
    if not observations:
        raise CleanObservationReadError(
            f"could not derive Amihud series for {spec_indicator_id!r} from bars"
        )
    return observations
