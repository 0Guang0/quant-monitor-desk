"""Shared matrix evidence-fetch runner (SSOT with tier_c_live_validation_dispatch)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from backend.app.datasources.adapters.fetch_port import PortError
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.product_live_ports import SOURCE_LIVE_DEFAULTS, create_product_live_fetch_port
from backend.app.storage.raw_store import RawStore

_EXTERNAL_FETCH_STATUSES = frozenset(
    {"RATE_LIMITED", "NETWORK_ERROR", "NOT_PUBLISHED_YET", "DISABLED_SOURCE", "AUTH_FAILED"}
)


def resolve_matrix_evidence_instrument_id(
    source_id: str,
    instrument_id: str | None = None,
) -> str | None:
    """SSOT with tier_c_live_validation_dispatch._default_instrument_id (no binding table)."""
    if instrument_id is not None:
        return instrument_id
    defaults = SOURCE_LIVE_DEFAULTS.get(source_id)
    if defaults is None:
        return None
    for key in ("symbols", "asset_ids", "concepts", "market_tickers", "market_slugs", "queries"):
        values = defaults.get(key)
        if values:
            return str(values[0])
    return None


def run_matrix_evidence_fetch_live(
    *,
    request,
    data_root: Path,
    instrument_id: str | None = None,
) -> tuple[str, bool, str | None]:
    """Product live fetch + raw persist; returns (sync_status, ok, error_message)."""
    port = create_product_live_fetch_port(
        source_id=request.source_id,
        data_domain=request.data_domain,
        operation=request.operation,
    )
    resolved_instrument = resolve_matrix_evidence_instrument_id(
        request.source_id,
        instrument_id,
    )
    fetch_req = FetchRequest(
        run_id="acceptance-evidence-fetch",
        source_id=request.source_id,
        data_domain=request.data_domain,
        instrument_id=resolved_instrument,
    )
    try:
        payload = port.fetch_payload(fetch_req)
    except PortError as exc:
        status = str(exc.status).upper()
        return status, False, f"evidence fetch port error: {exc.message}"

    row_count = int(payload.row_count or 0)
    if row_count < 1:
        return "EMPTY_RESPONSE", False, "evidence fetch returned zero rows"

    raw_root = data_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    store = RawStore(data_root)
    store.save(
        payload.content,
        source=request.source_id,
        data_domain=request.data_domain,
        file_type=payload.file_type,
        as_of=date.today().isoformat(),
    )
    return "SUCCESS", True, None


def evidence_fetch_failure_class(sync_status: str) -> str:
    status = sync_status.upper()
    if status in {"USER_AUTH_REQUIRED", "AUTH_FAILED"}:
        return "BLOCKED"
    if status in _EXTERNAL_FETCH_STATUSES:
        return "FAIL_EXTERNAL"
    return "FAIL_EXTERNAL"
