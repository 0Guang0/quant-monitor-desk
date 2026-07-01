"""US Treasury macro incremental orchestration (DCP-05 S03)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from backend.app.datasources.adapters.fetch_port import PortError
from backend.app.datasources.fetch_ports.us_treasury_port import (
    YIELD_CURVE_TENOR_WHITELIST,
    create_us_treasury_fetch_port,
)
from backend.app.ops.macro_incremental_common import (
    MacroIncrementalFetchProxy,
    MacroIncrementalRunReport,
    MacroIncrementalSourceConfig,
    build_axis_observation_row,
    build_macro_incremental_service,
    run_macro_incremental,
)
from backend.app.ops.us_treasury_incremental_watermark import (
    DATA_DOMAIN,
    DEFAULT_TENORS,
    SOURCE_ID,
)
from backend.app.sync.orchestrator import DataSyncOrchestrator


def _reject_unknown_tenor(tenor: str) -> None:
    if tenor not in YIELD_CURVE_TENOR_WHITELIST:
        raise ValueError(f"tenor not in whitelist: {tenor!r}")


def treasury_staging_rows_from_bundle(
    bundle: dict[str, Any],
    *,
    instrument_id: str,
    start_date: str | None = None,
) -> list[dict[str, object]]:
    """Map yield curve evidence → axis_observation staging rows."""
    content_hash = str(bundle.get("content_hash") or "treasury-hash")
    schema_hash = str(bundle.get("schema_hash") or "treasury-schema")
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
        raw = obs.get("yield_percent")
        if raw in (None, "", "."):
            continue
        tenor = str(obs.get("tenor") or instrument_id)
        rows.append(
            build_axis_observation_row(
                indicator_id=tenor,
                obs_date=obs_date,
                raw_value=float(raw),
                source_used=str(bundle.get("source_id") or SOURCE_ID),
                content_hash=content_hash,
                schema_hash=schema_hash,
                frequency="daily",
                fetch_time=fetch_time,
                raw_unit="percent",
            )
        )
    return rows


_US_TREASURY_CONFIG = MacroIncrementalSourceConfig(
    source_id=SOURCE_ID,
    data_domain=DATA_DOMAIN,
    adapter_id=SOURCE_ID,
    operation="fetch_yield_curve",
    trigger_reason="us_treasury_macro_incremental",
    staging_rows_fn=treasury_staging_rows_from_bundle,
    validate_instrument=_reject_unknown_tenor,
)


def build_us_treasury_incremental_service(
    *,
    data_root,
    fetch_port,
    since_by_instrument: dict[str, str],
    job_events=None,
    source_registry=None,
) -> MacroIncrementalFetchProxy:
    return build_macro_incremental_service(
        config=_US_TREASURY_CONFIG,
        data_root=data_root,
        fetch_port=fetch_port,
        since_by_instrument=since_by_instrument,
        job_events=job_events,
        source_registry=source_registry,
    )


def run_us_treasury_incremental(
    orch: DataSyncOrchestrator,
    *,
    service: MacroIncrementalFetchProxy,
    tenors: Sequence[str] = DEFAULT_TENORS,
    use_mock: bool = True,
    source_registry=None,
) -> MacroIncrementalRunReport:
    return run_macro_incremental(
        orch,
        config=_US_TREASURY_CONFIG,
        service=service,
        instrument_ids=tenors,
        use_mock=use_mock,
        source_registry=source_registry,
    )


def create_us_treasury_incremental_port(*, tenors=DEFAULT_TENORS, max_rows: int = 3, use_mock: bool = True):
    return create_us_treasury_fetch_port(
        tenors=tenors,
        max_rows=max_rows,
        data_domain=DATA_DOMAIN,
        use_mock=use_mock,
    )
