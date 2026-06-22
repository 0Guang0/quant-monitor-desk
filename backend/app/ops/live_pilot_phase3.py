"""Live pilot — phase3 (split from live_pilot.py, OP-01)."""

from __future__ import annotations

import json
import uuid
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.app.config import DATA_ROOT, PROJECT_ROOT
from backend.app.core.resource_guard import Decision
from backend.app.datasources.service import DataSourceService
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.db.connection import ConnectionManager
from backend.app.db.validation_gate import DbValidationGate
from backend.app.db.write_manager import WriteManager
from backend.app.ops.live_pilot_auth import (
    _pilot_request_to_dict,
    assert_pilot_ready_before_fetch,
    validate_authorization,
)
from backend.app.ops.live_pilot_constants import (
    DEFAULT_AUTHORIZATION_PATH,
    DEFAULT_PRODUCTION_DB,
    DEFAULT_SANDBOX_ROOT,
    EASTMONEY_VERDICT_MD,
    FRED_PRIMARY_DEFERRED_NOTE,
    HITL_CONFIRMATION_MD,
    MAX_PILOT_ROW_CAP,
    ORIGINAL_REQUEST2_ENDPOINT_HOST,
    ORIGINAL_REQUEST2_VENDOR_API,
    PHASE3_NO_PRODUCTION_MUTATION_MD,
    PHASE3_RAW_EVIDENCE_JSON,
    PHASE3_REQUEST2_RECONCILIATION_MD,
    SIDECAR_REQUEST2_ENDPOINT_HOST,
    SIDECAR_REQUEST2_VENDOR_API,
)
from backend.app.ops.live_pilot_phase2 import (
    _resolve_hitl_path,
    preview_live_pilot,
    require_hitl_confirmation,
)
from backend.app.ops.live_pilot_types import (
    LivePilotFixtureForbiddenError,
    LivePilotRequest,
    LivePilotRouteNotReadyError,
)
from backend.app.ops.live_pilot_phase1 import _utc_now_iso
from backend.app.ops.mutation_proof import key_table_row_counts as _key_table_row_counts
from backend.app.storage.file_registry import FileRegistry


def _assert_live_fetch_port(fetch_port: object) -> None:
    from backend.app.datasources.adapters.fetch_port import LocalFixtureFetchPort, StubFetchPort

    if isinstance(fetch_port, (StubFetchPort, LocalFixtureFetchPort)):
        raise LivePilotFixtureForbiddenError(
            "fixture/staged FetchPort forbidden for live pilot evidence"
        )


def _ensure_sandbox_db(sandbox_root: Path) -> tuple[Path, Path]:
    sandbox_root = Path(sandbox_root)
    data_root = sandbox_root / "data"
    db_dir = data_root / "duckdb"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / "quant_monitor.duckdb"
    if not db_path.is_file():
        from backend.app.db.migrate import apply_migrations

        cm = ConnectionManager(db_path, profile="eco")
        with cm.writer() as con:
            apply_migrations(con)
    return data_root, db_path


def _symbol_to_instrument_id(symbol: str) -> str:
    return symbol if "." in symbol else symbol


class _InlineConnectionFileRegistry(FileRegistry):
    """FileRegistry that reuses an open writer connection (no nested write lock)."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self._inline_con = None

    def bind_connection(self, con) -> None:
        self._inline_con = con

    def register(self, saved):
        if self._inline_con is not None:
            return self.register_on_connection(
                self._inline_con,
                saved,
                run_id="batch275-live-pilot-raw",
                job_id="register",
                own_transaction=False,
            )
        return super().register(saved)


RAW_FILE_REGISTRY_VALIDATION_REPORT_ID = "batch275-live-pilot-raw-file-registry"


def _ensure_raw_file_registry_validation_report(
    con, request: LivePilotRequest, run_id: str
) -> None:
    con.execute(
        """
        INSERT OR REPLACE INTO validation_report (
            validation_report_id, run_id, job_id, data_domain, staging_table,
            source_id, status, checked_rows, failed_rows, warning_rows,
            quality_flags, stale_reason, can_write_clean, needs_manual_review,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            RAW_FILE_REGISTRY_VALIDATION_REPORT_ID,
            run_id,
            "register",
            request.data_domain,
            "stg_file_registry",
            request.source_id,
            "PASSED",
            0,
            0,
            0,
            "raw_file_registry_metadata_only",
            None,
            True,
            False,
            datetime.now(UTC),
        ],
    )


def run_live_pilot_raw_only(
    request: LivePilotRequest,
    *,
    sandbox_root: Path,
    pilot_request_id: str = "pilot-req",
    evidence_dir: Path | None = None,
) -> dict[str, Any]:
    """Sandbox raw-only live fetch for one authorized request (HITL + route gate)."""
    assert_pilot_ready_before_fetch(request)
    hitl_path = require_hitl_confirmation(evidence_dir=evidence_dir)
    if not request.raw_only:
        raise LivePilotAuthorizationError("live pilot first pass requires raw_only=true")

    preview = preview_live_pilot(
        replace(request, dry_run=True),
        pilot_request_id=f"{pilot_request_id}-pre",
    )
    if preview["explicit_source_route_status"] != "READY":
        raise LivePilotRouteNotReadyError(
            f"explicit source route not READY: {preview['explicit_source_route_status']}"
        )

    prod_before_counts = _key_table_row_counts(DEFAULT_PRODUCTION_DB)
    prod_before_hash = (
        DEFAULT_PRODUCTION_DB.read_bytes() if DEFAULT_PRODUCTION_DB.is_file() else None
    )

    data_root, sandbox_db = _ensure_sandbox_db(sandbox_root)
    from backend.app.datasources.fetch_result import FetchRequest
    from backend.app.ops.live_pilot_fetch_ports import create_live_fetch_port

    fetch_port = create_live_fetch_port(
        source_id=request.source_id,
        operation=request.operation,
        symbols_or_indicators=request.symbols_or_indicators,
        max_rows=request.max_rows,
    )
    _assert_live_fetch_port(fetch_port)

    registry = SourceRegistry()
    registry.load()
    cm = ConnectionManager(sandbox_db, profile="eco")
    write_manager = WriteManager(cm, DbValidationGate(cm))
    file_registry = _InlineConnectionFileRegistry(
        cm,
        write_manager,
        validation_report_id=RAW_FILE_REGISTRY_VALIDATION_REPORT_ID,
    )
    service = DataSourceService(
        source_registry=registry,
        fetch_port=fetch_port,
        file_registry_factory=lambda: file_registry,
        data_root=data_root,
    )

    symbol = request.symbols_or_indicators[0]
    fetch_req = FetchRequest(
        run_id=f"{pilot_request_id}-live",
        source_id=request.source_id,
        data_domain=request.data_domain,
        instrument_id=_symbol_to_instrument_id(symbol),
        force_refresh=True,
    )

    with cm.writer() as con:
        _ensure_raw_file_registry_validation_report(con, request, fetch_req.run_id)
        file_registry.bind_connection(con)
        result = service.fetch(
            fetch_req,
            con=con,
            job_id="register",
            operation=request.operation,
        )

    prod_after_counts = _key_table_row_counts(DEFAULT_PRODUCTION_DB)
    prod_after_hash = (
        DEFAULT_PRODUCTION_DB.read_bytes() if DEFAULT_PRODUCTION_DB.is_file() else None
    )

    raw_paths = [str(Path(p).resolve()) for p in result.raw_file_paths]
    sandbox_resolved = sandbox_root.resolve()
    for path in raw_paths:
        if not Path(path).resolve().is_relative_to(sandbox_resolved):
            raise LivePilotAuthorizationError(f"raw evidence path outside sandbox: {path}")

    try:
        hitl_rel = str(hitl_path.relative_to(PROJECT_ROOT))
    except ValueError:
        hitl_rel = str(hitl_path)

    return {
        "pilot_request_id": pilot_request_id,
        "authorization_evidence": request.authorization_evidence,
        "hitl_confirmation": hitl_rel,
        "request": _pilot_request_to_dict(request),
        "route_preview": preview,
        "fetch_result": result.model_dump(),
        "sandbox_root": str(sandbox_root),
        "sandbox_data_root": str(data_root),
        "production_mutation_proof": {
            "production_db_path": str(DEFAULT_PRODUCTION_DB),
            "db_hash_unchanged": prod_before_hash == prod_after_hash,
            "before_key_table_counts": prod_before_counts,
            "after_key_table_counts": prod_after_counts,
            "row_counts_unchanged": prod_before_counts == prod_after_counts,
        },
        "fred_primary_deferred": request.operation == "fetch_macro_series",
        "fred_primary_deferred_note": FRED_PRIMARY_DEFERRED_NOTE
        if request.operation == "fetch_macro_series"
        else None,
    }


def capture_phase3_raw_evidence(
    *,
    requests: tuple[LivePilotRequest, ...],
    sandbox_root: Path,
    evidence_dir: Path,
) -> dict[str, Any]:
    """Execute all authorized live raw-only fetches and persist evidence JSON."""
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    sandbox_root = Path(sandbox_root)

    fetches: list[dict[str, Any]] = []
    for index, request in enumerate(requests, start=1):
        live_request = LivePilotRequest(
            source_id=request.source_id,
            data_domain=request.data_domain,
            operation=request.operation,
            symbols_or_indicators=request.symbols_or_indicators,
            date_window=request.date_window,
            max_rows=request.max_rows,
            authorization_evidence=request.authorization_evidence,
            dry_run=False,
            raw_only=True,
            write_target="sandbox",
            allow_clean_write=False,
        )
        pilot_request_id = f"pilot-req-{index}"
        prod_before_counts = _key_table_row_counts(DEFAULT_PRODUCTION_DB)
        prod_before_hash = (
            DEFAULT_PRODUCTION_DB.read_bytes() if DEFAULT_PRODUCTION_DB.is_file() else None
        )
        try:
            fetches.append(
                run_live_pilot_raw_only(
                    live_request,
                    sandbox_root=sandbox_root / f"req-{index}",
                    pilot_request_id=pilot_request_id,
                    evidence_dir=evidence_dir,
                )
            )
        except Exception as exc:
            prod_after_counts = _key_table_row_counts(DEFAULT_PRODUCTION_DB)
            prod_after_hash = (
                DEFAULT_PRODUCTION_DB.read_bytes() if DEFAULT_PRODUCTION_DB.is_file() else None
            )
            failure_item = {
                "pilot_request_id": pilot_request_id,
                "authorization_evidence": live_request.authorization_evidence,
                "request": _pilot_request_to_dict(live_request),
                "sandbox_root": str(sandbox_root / f"req-{index}"),
                "fetch_result": {
                    "status": "FAILED",
                    "row_count": 0,
                    "raw_file_paths": [],
                    "content_hash": None,
                    "error_message": str(exc),
                },
                "production_mutation_proof": {
                    "production_db_path": str(DEFAULT_PRODUCTION_DB),
                    "db_hash_unchanged": prod_before_hash == prod_after_hash,
                    "before_key_table_counts": prod_before_counts,
                    "after_key_table_counts": prod_after_counts,
                    "row_counts_unchanged": prod_before_counts == prod_after_counts,
                },
            }
            fetches.append(failure_item)
            (evidence_dir / f"phase3_fetch_failure_{pilot_request_id}.json").write_text(
                json.dumps(failure_item, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

    generated_at = _utc_now_iso()
    payload: dict[str, Any] = {
        "generated_at": generated_at,
        "phase": "phase3_raw_micro_fetch",
        "sandbox_root": str(sandbox_root),
        "rerun_safe": True,
        "evidence_write_mode": "overwrite_with_per_request_failure_artifacts",
        "authorization_evidence": requests[0].authorization_evidence if requests else None,
        "fred_primary_deferred": True,
        "fred_primary_deferred_note": FRED_PRIMARY_DEFERRED_NOTE,
        "fetches": fetches,
    }

    proof_lines = [
        "# Phase 3 — No Production Mutation Proof",
        "",
        f"- **Generated at:** {generated_at}",
        f"- **Sandbox root:** `{sandbox_root}`",
        f"- **Production DB:** `{DEFAULT_PRODUCTION_DB}`",
        "",
    ]
    for item in fetches:
        proof = item["production_mutation_proof"]
        proof_lines.append(
            f"- **{item['pilot_request_id']}:** hash_unchanged={proof['db_hash_unchanged']} "
            f"row_counts_unchanged={proof['row_counts_unchanged']}"
        )

    (evidence_dir / PHASE3_RAW_EVIDENCE_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / PHASE3_NO_PRODUCTION_MUTATION_MD).write_text(
        "\n".join(proof_lines) + "\n",
        encoding="utf-8",
    )
    return payload


def capture_task_phase3_raw_evidence(
    evidence_dir: Path | str,
    *,
    sandbox_root: Path | None = None,
) -> dict[str, Any]:
    """Execute helper: HITL-gated live fetch for three authorized requests."""
    return capture_phase3_raw_evidence(
        requests=approved_pilot_requests(),
        sandbox_root=sandbox_root or DEFAULT_SANDBOX_ROOT,
        evidence_dir=Path(evidence_dir),
    )
