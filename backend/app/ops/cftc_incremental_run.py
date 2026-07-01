"""CFTC COT macro incremental orchestration (DCP-05 S06)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from backend.app.datasources.fetch_ports.cftc_cot_port import (
    MARKET_WHITELIST,
    create_cftc_cot_fetch_port,
)
from backend.app.ops.macro_incremental_common import (
    MacroIncrementalFetchProxy,
    MacroIncrementalRunReport,
    MacroIncrementalSourceConfig,
    build_axis_observation_row,
    build_macro_incremental_service,
    compute_since_date,
    enabled_source_registry,
    read_observation_date_watermark,
    read_since_dates_for_instruments,
    run_macro_incremental,
)
from backend.app.sync.orchestrator import DataSyncOrchestrator

SOURCE_ID = "cftc_cot"
DATA_DOMAIN = "cot_positioning"
DEFAULT_MARKETS = ("088691",)
WEEKLY_ADVANCE_DAYS = 7


def enabled_cftc_source_registry():
    return enabled_source_registry(source_id=SOURCE_ID, data_domain=DATA_DOMAIN)


def read_since_dates_for_markets(con, market_codes, **kwargs):
    return read_since_dates_for_instruments(
        con, market_codes, advance_days=WEEKLY_ADVANCE_DAYS, **kwargs
    )


def _reject_unknown_market(market: str) -> None:
    if market not in MARKET_WHITELIST:
        raise ValueError(f"market not in whitelist: {market!r}")


def cftc_staging_rows_from_bundle(
    bundle: dict[str, Any],
    *,
    instrument_id: str,
    start_date: str | None = None,
) -> list[dict[str, object]]:
    """Map COT positioning evidence → axis_observation staging rows."""
    content_hash = str(bundle.get("content_hash") or "cftc-hash")
    schema_hash = str(bundle.get("schema_hash") or "cftc-schema")
    fetch_time_raw = bundle.get("retrieved_at") or bundle.get("as_of_timestamp")
    if isinstance(fetch_time_raw, str):
        fetch_time = datetime.fromisoformat(fetch_time_raw.replace("Z", "+00:00"))
        if fetch_time.tzinfo is None:
            fetch_time = fetch_time.replace(tzinfo=UTC)
    else:
        fetch_time = datetime.now(UTC)
    rows: list[dict[str, object]] = []
    for obs in bundle.get("observations") or []:
        obs_date = str(obs.get("report_date") or obs.get("observation_date") or "")
        if not obs_date or (start_date and obs_date < start_date):
            continue
        long_c = obs.get("long_contracts")
        short_c = obs.get("short_contracts")
        if long_c in (None, "", ".") or short_c in (None, "", "."):
            continue
        market = str(obs.get("market_code") or instrument_id)
        net = float(long_c) - float(short_c)
        rows.append(
            build_axis_observation_row(
                indicator_id=market,
                obs_date=obs_date,
                raw_value=net,
                source_used=str(bundle.get("source_id") or SOURCE_ID),
                content_hash=content_hash,
                schema_hash=schema_hash,
                frequency="weekly",
                fetch_time=fetch_time,
                raw_unit="contracts",
            )
        )
    return rows


_CFTC_CONFIG = MacroIncrementalSourceConfig(
    source_id=SOURCE_ID,
    data_domain=DATA_DOMAIN,
    adapter_id=SOURCE_ID,
    operation="fetch_cot_positioning",
    trigger_reason="cftc_macro_incremental",
    staging_rows_fn=cftc_staging_rows_from_bundle,
    validate_instrument=_reject_unknown_market,
    advance_days=WEEKLY_ADVANCE_DAYS,
)


def build_cftc_incremental_service(
    *,
    data_root,
    fetch_port,
    since_by_instrument: dict[str, str],
    job_events=None,
    source_registry=None,
) -> MacroIncrementalFetchProxy:
    return build_macro_incremental_service(
        config=_CFTC_CONFIG,
        data_root=data_root,
        fetch_port=fetch_port,
        since_by_instrument=since_by_instrument,
        job_events=job_events,
        source_registry=source_registry,
    )


def run_cftc_incremental(
    orch: DataSyncOrchestrator,
    *,
    service: MacroIncrementalFetchProxy,
    markets: Sequence[str] = DEFAULT_MARKETS,
    use_mock: bool = True,
    source_registry=None,
) -> MacroIncrementalRunReport:
    return run_macro_incremental(
        orch,
        config=_CFTC_CONFIG,
        service=service,
        instrument_ids=markets,
        use_mock=use_mock,
        source_registry=source_registry,
    )


def create_cftc_incremental_port(*, markets=DEFAULT_MARKETS, max_rows: int = 3, use_mock: bool = True):
    return create_cftc_cot_fetch_port(markets=markets, max_rows=max_rows, use_mock=use_mock)
