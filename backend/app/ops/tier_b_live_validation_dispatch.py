"""Tier B live validation_fetch dispatch (M-DATA-03 AC-7 · ADR-008)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.datasources.adapters.fetch_port import PortError
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.product_live_ports import (
    SOURCE_LIVE_DEFAULTS,
    create_product_live_fetch_port,
)
from backend.app.storage.raw_store import RawStore

PASS_FETCH_STATUSES = frozenset({"SUCCESS", "OK"})
_EXTERNAL_FETCH_STATUSES = frozenset(
    {"RATE_LIMITED", "NETWORK_ERROR", "NOT_PUBLISHED_YET", "DISABLED_SOURCE", "AUTH_FAILED"}
)


@dataclass(frozen=True)
class LiveValidationOutcome:
    source_id: str
    fetch_status: str
    row_count: int
    detail: str = ""
    inspect_status: str = "NOT_APPLICABLE"
    clean_table: str = ""
    raw_paths: tuple[str, ...] = ()
    fetch_provenance: str = "mock_replay"


def _assert_resource_guard_ok() -> None:
    decision, reason = ResourceGuard().check()
    if decision != Decision.OK:
        raise RuntimeError(f"resource guard blocked: {decision.value}: {reason or 'paused'}")


def _bind_live_data_root(data_root: Path) -> Path:
    from backend.app.ops.tier_b_live_acceptance import assert_isolated_live_data_root

    resolved = assert_isolated_live_data_root(data_root)
    os.environ["QMD_DATA_ROOT"] = str(resolved)
    return resolved


def _default_instrument_id(source_id: str, binding: dict[str, Any]) -> str:
    if inst := binding.get("default_instrument"):
        return str(inst)
    defaults = SOURCE_LIVE_DEFAULTS[source_id]
    for key in ("symbols", "asset_ids", "concepts", "market_tickers", "market_slugs"):
        values = defaults.get(key)
        if values:
            return str(values[0])
    raise ValueError(f"no default instrument for source_id={source_id!r}")


def _relative_raw_path(data_root: Path, absolute: Path) -> str:
    return absolute.resolve().relative_to(data_root.resolve()).as_posix()


def run_tier_b_live_validation(source_id: str, data_root: Path) -> LiveValidationOutcome:
    """Product live fetch → raw evidence (validation_fetch, not incremental sync)."""
    from backend.app.ops.tier_b_live_acceptance import source_bindings

    resolved = _bind_live_data_root(data_root)
    _assert_resource_guard_ok()
    binding = source_bindings()[source_id]
    data_domain = str(binding["data_domain"])
    clean_table = str(binding["clean_table"])
    fetch_provenance = str(binding.get("fetch_provenance", "mock_replay"))
    instrument_id = _default_instrument_id(source_id, binding)

    port = create_product_live_fetch_port(source_id=source_id, data_domain=data_domain)
    req = FetchRequest(
        run_id=f"validation-{source_id}",
        source_id=source_id,
        data_domain=data_domain,
        instrument_id=instrument_id,
    )
    try:
        payload = port.fetch_payload(req)
    except PortError as exc:
        status = str(exc.status).upper()
        return LiveValidationOutcome(
            source_id=source_id,
            fetch_status=status,
            row_count=0,
            detail=f"port error: {exc.message}",
            inspect_status="NOT_APPLICABLE",
            clean_table=clean_table,
            fetch_provenance=fetch_provenance,
        )

    row_count = int(payload.row_count or 0)
    if row_count < 1:
        return LiveValidationOutcome(
            source_id=source_id,
            fetch_status="EMPTY_RESPONSE",
            row_count=0,
            detail="validation_fetch returned zero rows",
            inspect_status="NOT_APPLICABLE",
            clean_table=clean_table,
            fetch_provenance=fetch_provenance,
        )

    as_of = date.today().isoformat()
    store = RawStore(resolved)
    saved = store.save(
        payload.content,
        source=source_id,
        data_domain=data_domain,
        file_type=payload.file_type,
        as_of=as_of,
    )
    rel_path = _relative_raw_path(resolved, Path(saved.local_path))
    return LiveValidationOutcome(
        source_id=source_id,
        fetch_status="SUCCESS",
        row_count=row_count,
        detail=f"validation_fetch rows={row_count} raw={rel_path}; provenance={fetch_provenance}",
        inspect_status="NOT_APPLICABLE",
        clean_table=clean_table,
        raw_paths=(rel_path,),
        fetch_provenance=fetch_provenance,
    )


__all__ = [
    "LiveValidationOutcome",
    "PASS_FETCH_STATUSES",
    "run_tier_b_live_validation",
]
