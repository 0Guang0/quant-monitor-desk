"""World Bank macro incremental orchestration (DCP-05 S05)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from backend.app.datasources.fetch_ports.world_bank_port import (
    COUNTRY_WHITELIST,
    INDICATOR_WHITELIST,
    create_world_bank_fetch_port,
)
from backend.app.ops.macro_incremental_common import (
    MacroIncrementalFetchProxy,
    MacroIncrementalRunReport,
    MacroIncrementalSourceConfig,
    build_axis_observation_row,
    build_macro_incremental_service,
    run_macro_incremental,
)
from backend.app.ops.world_bank_incremental_watermark import (
    DATA_DOMAIN,
    DEFAULT_COUNTRIES,
    DEFAULT_INDICATOR,
    SOURCE_ID,
    clean_indicator_id,
)
from backend.app.sync.orchestrator import DataSyncOrchestrator

_WB_INDICATORS = (DEFAULT_INDICATOR,)


def _reject_unknown_country(country: str) -> None:
    if country not in COUNTRY_WHITELIST:
        raise ValueError(f"country not in whitelist: {country!r}")
    if DEFAULT_INDICATOR not in INDICATOR_WHITELIST:
        raise ValueError(f"indicator not in whitelist: {DEFAULT_INDICATOR!r}")


def world_bank_staging_rows_from_bundle(
    bundle: dict[str, Any],
    *,
    instrument_id: str,
    start_date: str | None = None,
) -> list[dict[str, object]]:
    """Map World Bank indicator evidence → axis_observation staging rows."""
    content_hash = str(bundle.get("content_hash") or "wb-hash")
    schema_hash = str(bundle.get("schema_hash") or "wb-schema")
    fetch_time_raw = bundle.get("retrieved_at") or bundle.get("as_of_timestamp")
    if isinstance(fetch_time_raw, str):
        fetch_time = datetime.fromisoformat(fetch_time_raw.replace("Z", "+00:00"))
        if fetch_time.tzinfo is None:
            fetch_time = fetch_time.replace(tzinfo=UTC)
    else:
        fetch_time = datetime.now(UTC)
    rows: list[dict[str, object]] = []
    for obs in bundle.get("observations") or []:
        obs_date = str(obs.get("observation_date") or "")
        if not obs_date or (start_date and obs_date < start_date):
            continue
        raw = obs.get("value")
        if raw in (None, "", "."):
            continue
        country = str(obs.get("country_code") or instrument_id)
        indicator = str(obs.get("indicator_id") or DEFAULT_INDICATOR)
        rows.append(
            build_axis_observation_row(
                indicator_id=clean_indicator_id(country, indicator_id=indicator),
                obs_date=obs_date,
                raw_value=float(raw),
                source_used=str(bundle.get("source_id") or SOURCE_ID),
                content_hash=content_hash,
                schema_hash=schema_hash,
                frequency="annual",
                fetch_time=fetch_time,
                raw_unit=str(obs.get("unit") or "index"),
            )
        )
    return rows


_WB_CONFIG = MacroIncrementalSourceConfig(
    source_id=SOURCE_ID,
    data_domain=DATA_DOMAIN,
    adapter_id=SOURCE_ID,
    operation="fetch_indicator_series",
    trigger_reason="world_bank_macro_incremental",
    staging_rows_fn=world_bank_staging_rows_from_bundle,
    validate_instrument=_reject_unknown_country,
    indicator_resolver=lambda country: clean_indicator_id(country),
)


def build_world_bank_incremental_service(
    *,
    data_root,
    fetch_port,
    since_by_instrument: dict[str, str],
    job_events=None,
    source_registry=None,
) -> MacroIncrementalFetchProxy:
    return build_macro_incremental_service(
        config=_WB_CONFIG,
        data_root=data_root,
        fetch_port=fetch_port,
        since_by_instrument=since_by_instrument,
        job_events=job_events,
        source_registry=source_registry,
    )


def run_world_bank_incremental(
    orch: DataSyncOrchestrator,
    *,
    service: MacroIncrementalFetchProxy,
    countries: Sequence[str] = DEFAULT_COUNTRIES,
    use_mock: bool = True,
    source_registry=None,
) -> MacroIncrementalRunReport:
    return run_macro_incremental(
        orch,
        config=_WB_CONFIG,
        service=service,
        instrument_ids=countries,
        use_mock=use_mock,
        source_registry=source_registry,
    )


def create_world_bank_incremental_port(
    *, countries=DEFAULT_COUNTRIES, max_rows: int = 3, use_mock: bool = True
):
    return create_world_bank_fetch_port(
        countries=countries,
        indicators=_WB_INDICATORS,
        max_rows=max_rows,
        data_domain=DATA_DOMAIN,
        use_mock=use_mock,
    )
