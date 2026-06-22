"""Batch 2.75 controlled live pilot orchestration (fail-closed, sandbox-first)."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from backend.app.config import DATA_ROOT, PROJECT_ROOT
from backend.app.core.resource_guard import Decision
from backend.app.datasources.capability_registry import SourceCapabilityRegistry
from backend.app.datasources.service import DataSourceService
from backend.app.datasources.source_registry import SourceNotFoundError, SourceRegistry
from backend.app.db.connection import ConnectionManager
from backend.app.db.validation_gate import DbValidationGate
from backend.app.db.write_manager import WriteManager
from backend.app.ops.db_inspector import (
    KEY_TABLES,
    DbInspector,
    format_text_report,
)
from backend.app.ops.mutation_proof import key_table_row_counts as _key_table_row_counts
from backend.app.storage.file_registry import FileRegistry

DEFAULT_AUTHORIZATION_PATH = PROJECT_ROOT / "docs/quality/batch275_user_authorization_2026-06-21.md"
DEFAULT_PRODUCTION_DB = DATA_ROOT / "duckdb" / "quant_monitor.duckdb"

PHASE1_BASELINE_JSON = "phase1_baseline_inventory.json"
PHASE1_BASELINE_MD = "phase1_baseline_inventory.md"
PHASE1_NO_MUTATION_MD = "phase1_no_mutation_proof.md"
PHASE1_CAPABILITY_JSON = "phase1_capability_snapshot.json"
PHASE2_ROUTE_MATRIX_JSON = "phase2_route_preview_matrix.json"
PHASE3_RAW_EVIDENCE_JSON = "phase3_raw_micro_fetch_evidence.json"
PHASE3_NO_PRODUCTION_MUTATION_MD = "phase3_no_production_mutation_proof.md"
PHASE3_REQUEST2_RECONCILIATION_MD = "phase3_request2_evidence_reconciliation.md"
EASTMONEY_VERDICT_MD = "eastmoney_stock_zh_a_hist_verdict.md"
PHASE4_VALIDATION_REPORT_JSON = "phase4_validation_report.json"
PHASE4_CONFLICT_INSPECT_TXT = "phase4_conflict_inspect.txt"
PHASE4_NO_PRODUCTION_MUTATION_MD = "phase4_no_production_mutation_proof.md"
PHASE45_PERF_BUDGET_JSON = "phase45_perf_budget.json"
HITL_CONFIRMATION_MD = "phase3_hitl_user_confirmation.md"
DEFAULT_SANDBOX_ROOT = PROJECT_ROOT / ".audit-sandbox/batch275-live-pilot"

ORIGINAL_REQUEST2_VENDOR_API = "stock_zh_a_hist"
ORIGINAL_REQUEST2_ENDPOINT_HOST = "push2his.eastmoney.com"
SIDECAR_REQUEST2_VENDOR_API = "stock_zh_a_daily"
SIDECAR_REQUEST2_ENDPOINT_HOST = "finance.sina.com.cn"

FRED_PRIMARY_DEFERRED_NOTE = (
    "B2.5-O-05: Request 3 akshare macro shape only; does not close FRED primary for ENV-E1-DGS10"
)

# Policy defaults — sources not authorized in batch275_user_authorization_2026-06-21.md
DISABLED_PILOT_SOURCE_IDS = frozenset(
    {
        "fred",
        "qmt_xtdata",
        "qmt_xqshare",
        "yahoo_finance",
    }
)

MAX_PILOT_ROW_CAP = 100

# Approved micro-pilot triples from batch275_user_authorization_2026-06-21.md §Approved
APPROVED_PILOT_REQUESTS: frozenset[tuple[str, str, str]] = frozenset(
    {
        ("baostock", "cn_equity_daily_bar", "fetch_daily_bar"),
        ("akshare", "cn_equity_daily_bar", "fetch_daily_bar_validation"),
        ("akshare", "macro_supplementary", "fetch_macro_series"),
    }
)

APPROVED_PILOT_REQUEST_ENVELOPES: frozenset[tuple[str, str, str, tuple[str, ...], str, int]] = (
    frozenset(
        {
            (
                "baostock",
                "cn_equity_daily_bar",
                "fetch_daily_bar",
                ("sh.600519",),
                "recent 5 trading days",
                10,
            ),
            (
                "akshare",
                "cn_equity_daily_bar",
                "fetch_daily_bar_validation",
                ("sh.600519",),
                "recent 5 trading days",
                10,
            ),
            (
                "akshare",
                "macro_supplementary",
                "fetch_macro_series",
                ("DGS10",),
                "recent 7 calendar days",
                20,
            ),
        }
    )
)


class LivePilotOutcome(StrEnum):
    PILOT_PASS_RAW_ONLY = "PILOT_PASS_RAW_ONLY"
    PILOT_PASS_SANDBOX_CLEAN = "PILOT_PASS_SANDBOX_CLEAN"
    PILOT_FAIL_SOURCE = "PILOT_FAIL_SOURCE"
    PILOT_FAIL_VALIDATION = "PILOT_FAIL_VALIDATION"
    PILOT_REDEFERRED = "PILOT_REDEFERRED"


class LivePilotAuthorizationError(RuntimeError):
    """Raised when authorization evidence or request parameters fail fail-closed gate."""


class LivePilotDisabledSourceError(RuntimeError):
    """Raised when source_id is not authorized for Batch 2.75 live pilot."""


class LivePilotRouteNotReadyError(RuntimeError):
    """Raised when explicit source route is not READY before live fetch."""


class LivePilotFixtureForbiddenError(RuntimeError):
    """Raised when staged/fixture fetch port is used for live pilot evidence."""


@dataclass(frozen=True)
class LivePilotRequest:
    source_id: str
    data_domain: str
    operation: str
    symbols_or_indicators: tuple[str, ...]
    date_window: str
    max_rows: int
    authorization_evidence: str
    dry_run: bool = True
    raw_only: bool = True
    write_target: str = "sandbox"
    allow_clean_write: bool = False


def _resolve_authorization_path(path: str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate.resolve()


def validate_authorization(request: LivePilotRequest) -> None:
    """Fail-closed authorization gate — must pass before route preview or fetch."""
    auth_path = _resolve_authorization_path(request.authorization_evidence)
    if not auth_path.is_file():
        raise LivePilotAuthorizationError(
            f"authorization evidence missing: {request.authorization_evidence}"
        )

    auth_text = auth_path.read_text(encoding="utf-8")
    if "batch275_user_authorization" not in auth_path.name:
        raise LivePilotAuthorizationError(
            f"authorization evidence must be batch275 user authorization file: {auth_path.name}"
        )
    if "Approved on" not in auth_text:
        raise LivePilotAuthorizationError("authorization evidence missing approval marker")

    if request.source_id in DISABLED_PILOT_SOURCE_IDS:
        raise LivePilotDisabledSourceError(
            f"source {request.source_id!r} is not authorized for Batch 2.75 live pilot"
        )

    triple = (request.source_id, request.data_domain, request.operation)
    if triple not in APPROVED_PILOT_REQUESTS:
        raise LivePilotAuthorizationError(
            f"request triple {triple!r} not in approved micro-pilot set"
        )

    if not request.raw_only:
        raise LivePilotAuthorizationError("first live pass requires raw_only=true")
    if request.write_target != "sandbox":
        raise LivePilotAuthorizationError("write_target must be sandbox")
    if request.allow_clean_write:
        raise LivePilotAuthorizationError("allow_clean_write must be false for default pilot")
    if request.max_rows <= 0 or request.max_rows > MAX_PILOT_ROW_CAP:
        raise LivePilotAuthorizationError(
            f"max_rows must be in 1..{MAX_PILOT_ROW_CAP}, got {request.max_rows}"
        )
    if not request.symbols_or_indicators:
        raise LivePilotAuthorizationError("symbols_or_indicators must be non-empty")

    envelope = (
        request.source_id,
        request.data_domain,
        request.operation,
        request.symbols_or_indicators,
        request.date_window,
        request.max_rows,
    )
    if envelope not in APPROVED_PILOT_REQUEST_ENVELOPES:
        raise LivePilotAuthorizationError(
            "request envelope does not exactly match approved micro-pilot authorization"
        )


def assert_pilot_ready_before_fetch(request: LivePilotRequest) -> None:
    """Authorization + disabled-source gate invoked before any network fetch."""
    validate_authorization(request)


def approved_pilot_requests() -> tuple[LivePilotRequest, ...]:
    """Three user-authorized micro-pilot requests from batch275 authorization file."""
    auth = "docs/quality/batch275_user_authorization_2026-06-21.md"
    return (
        LivePilotRequest(
            source_id="baostock",
            data_domain="cn_equity_daily_bar",
            operation="fetch_daily_bar",
            symbols_or_indicators=("sh.600519",),
            date_window="recent 5 trading days",
            max_rows=10,
            authorization_evidence=auth,
        ),
        LivePilotRequest(
            source_id="akshare",
            data_domain="cn_equity_daily_bar",
            operation="fetch_daily_bar_validation",
            symbols_or_indicators=("sh.600519",),
            date_window="recent 5 trading days",
            max_rows=10,
            authorization_evidence=auth,
        ),
        LivePilotRequest(
            source_id="akshare",
            data_domain="macro_supplementary",
            operation="fetch_macro_series",
            symbols_or_indicators=("DGS10",),
            date_window="recent 7 calendar days",
            max_rows=20,
            authorization_evidence=auth,
        ),
    )


def _pilot_request_to_dict(request: LivePilotRequest) -> dict[str, Any]:
    return {
        "source_id": request.source_id,
        "data_domain": request.data_domain,
        "operation": request.operation,
        "symbols_or_indicators": list(request.symbols_or_indicators),
        "date_window": request.date_window,
        "max_rows": request.max_rows,
        "dry_run": request.dry_run,
        "raw_only": request.raw_only,
        "write_target": request.write_target,
        "allow_clean_write": request.allow_clean_write,
        "authorization_evidence": request.authorization_evidence,
    }


def _explicit_source_route_status(
    *,
    source_id: str,
    candidates: list[Any],
) -> str:
    candidate = next((c for c in candidates if c.source_id == source_id), None)
    if candidate is None:
        return "NO_AVAILABLE_SOURCE"
    if candidate.enabled:
        return "READY"
    reason = candidate.skip_reason or candidate.disabled_reason or ""
    if "user_authorization" in reason or reason.startswith("missing_env:"):
        return "USER_AUTH_REQUIRED"
    if reason == "capability_missing":
        return "CAPABILITY_MISSING"
    if source_id == "qmt_xtdata" and reason:
        return "DISABLED_SOURCE"
    return "DISABLED_SOURCE"


def preview_live_pilot(
    request: LivePilotRequest,
    *,
    service: DataSourceService | None = None,
    pilot_request_id: str = "pilot-req",
) -> dict[str, Any]:
    """Dry-run route preview for one authorized pilot request (no fetch)."""
    validate_authorization(request)
    if not request.dry_run:
        raise LivePilotAuthorizationError("Phase 2 route preview requires dry_run=true")

    svc = service or DataSourceService()
    guard_decision, guard_reason = svc.check_resource_guard()
    if guard_decision == Decision.HARD_STOP:
        raise RuntimeError(f"ResourceGuard HARD_STOP: {guard_reason}")

    route_plan = svc.preview_route(
        data_domain=request.data_domain,
        operation=request.operation,
        run_id=f"{pilot_request_id}-preview",
        job_id="batch275-live-pilot-phase2",
    )
    explicit_status = _explicit_source_route_status(
        source_id=request.source_id,
        candidates=route_plan.candidates,
    )

    return {
        "pilot_request_id": pilot_request_id,
        "request": _pilot_request_to_dict(request),
        "authorization_evidence": request.authorization_evidence,
        "dry_run": True,
        "route_plan": route_plan.to_payload_dict(),
        "explicit_source_route_status": explicit_status,
        "resource_guard_decision": guard_decision.value,
        "resource_guard_reason": guard_reason,
    }


def capture_phase2_route_matrix(
    *,
    requests: tuple[LivePilotRequest, ...],
    evidence_dir: Path,
    db_path: Path | None = None,
    service: DataSourceService | None = None,
) -> dict[str, Any]:
    """Phase 2 route preview matrix for authorized requests — zero fetch, optional DB proof."""
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    target_db = db_path or DEFAULT_PRODUCTION_DB
    before_counts = _key_table_row_counts(target_db) if target_db.is_file() else {}
    before_bytes = target_db.read_bytes() if target_db.is_file() else None

    svc = service or DataSourceService()
    previews: list[dict[str, Any]] = []
    for index, request in enumerate(requests, start=1):
        preview = preview_live_pilot(
            request,
            service=svc,
            pilot_request_id=f"pilot-req-{index}",
        )
        previews.append(preview)

    after_counts = _key_table_row_counts(target_db) if target_db.is_file() else {}
    after_bytes = target_db.read_bytes() if target_db.is_file() else None

    generated_at = _utc_now_iso()
    payload: dict[str, Any] = {
        "generated_at": generated_at,
        "phase": "phase2_route_preview",
        "dry_run": True,
        "authorization_evidence": requests[0].authorization_evidence if requests else None,
        "fred_primary_deferred": True,
        "fred_primary_deferred_note": FRED_PRIMARY_DEFERRED_NOTE,
        "previews": previews,
        "mutation_proof": {
            "generated_at": generated_at,
            "db_path": str(target_db),
            "db_file_hash_unchanged": before_bytes == after_bytes,
            "before_key_table_counts": before_counts,
            "after_key_table_counts": after_counts,
            "row_counts_unchanged": before_counts == after_counts,
            "phase2_zero_mutation": before_counts == after_counts and before_bytes == after_bytes,
        },
    }

    (evidence_dir / PHASE2_ROUTE_MATRIX_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def capture_task_phase2_route_evidence(
    evidence_dir: Path | str,
    *,
    db_path: Path | None = None,
) -> dict[str, Any]:
    """Execute helper: persist Phase 2 matrix for three authorized requests."""
    return capture_phase2_route_matrix(
        requests=approved_pilot_requests(),
        evidence_dir=Path(evidence_dir),
        db_path=db_path or DEFAULT_PRODUCTION_DB,
    )


def _resolve_hitl_path(evidence_dir: Path | None = None) -> Path:
    if evidence_dir is not None:
        return Path(evidence_dir) / HITL_CONFIRMATION_MD
    return (
        PROJECT_ROOT
        / ".trellis/tasks/06-21-round3-batch2-75-live-pilot/execute-evidence"
        / HITL_CONFIRMATION_MD
    )


def require_hitl_confirmation(*, evidence_dir: Path | None = None) -> Path:
    """Phase 3 HITL gate — user confirmation file must exist before network fetch."""
    hitl_path = _resolve_hitl_path(evidence_dir)
    if not hitl_path.is_file():
        raise LivePilotAuthorizationError(
            f"HITL confirmation required: {HITL_CONFIRMATION_MD} missing"
        )
    text = hitl_path.read_text(encoding="utf-8")
    if "User confirmation" not in text and "用户" not in text:
        raise LivePilotAuthorizationError("HITL file missing user confirmation marker")
    return hitl_path


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


def _load_raw_json_payload(raw_path: Path) -> dict[str, Any]:
    return json.loads(raw_path.read_text(encoding="utf-8"))


def _equity_bar_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        return []
    first = rows[0]
    if isinstance(first, dict):
        return [row for row in rows if isinstance(row, dict)]
    if isinstance(first, list):
        normalized: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, list) or len(row) < 7:
                continue
            normalized.append(
                {
                    "date": row[0],
                    "code": row[1],
                    "open": row[2],
                    "high": row[3],
                    "low": row[4],
                    "close": row[5],
                    "volume": row[6],
                }
            )
        return normalized
    return []


def _validate_equity_raw_structure(rows: list[dict[str, Any]]) -> dict[str, Any]:
    required = ("date", "open", "high", "low", "close")
    findings: list[str] = []
    if not rows:
        findings.append("EMPTY_ROWS")
        return {"status": "FAILED", "checked_rows": 0, "findings": findings}
    for index, row in enumerate(rows):
        missing = [field for field in required if field not in row or row[field] in (None, "")]
        if missing:
            findings.append(f"ROW_{index}_MISSING_FIELDS:{','.join(missing)}")
        try:
            high = float(row.get("high"))
            low = float(row.get("low"))
            if high < low:
                findings.append(f"ROW_{index}_HIGH_LT_LOW")
        except (TypeError, ValueError):
            findings.append(f"ROW_{index}_NON_NUMERIC_OHLC")
    status = "FAILED" if findings else "PASSED"
    return {"status": status, "checked_rows": len(rows), "findings": findings}


def _validate_macro_raw_structure(rows: list[dict[str, Any]]) -> dict[str, Any]:
    findings: list[str] = []
    if not rows:
        findings.append("EMPTY_ROWS")
        return {"status": "FAILED", "checked_rows": 0, "findings": findings}
    if not any("日期" in row or "date" in row for row in rows):
        findings.append("MISSING_DATE_COLUMN")
    status = "FAILED" if findings else "PASSED"
    return {"status": status, "checked_rows": len(rows), "findings": findings}


def _classify_request2_endpoint(
    *,
    raw_payload: dict[str, Any] | None,
    verdict_unavailable: bool,
) -> dict[str, Any]:
    vendor_api = str(raw_payload.get("vendor_api", "")) if raw_payload else ""
    sidecar_present = vendor_api == SIDECAR_REQUEST2_VENDOR_API
    original_present = vendor_api == ORIGINAL_REQUEST2_VENDOR_API
    if verdict_unavailable and not original_present:
        original_status = "SOURCE_ENDPOINT_FAILURE"
    elif original_present:
        original_status = "RAW_PRESENT"
    else:
        original_status = "SOURCE_ENDPOINT_FAILURE"
    sidecar_status = "SIDECAR_STRUCTURE_OK" if sidecar_present and raw_payload else "NOT_PRESENT"
    return {
        "original_endpoint_expected": (
            f"{ORIGINAL_REQUEST2_VENDOR_API} / {ORIGINAL_REQUEST2_ENDPOINT_HOST}"
        ),
        "sidecar_endpoint_observed": (
            f"{SIDECAR_REQUEST2_VENDOR_API} / {SIDECAR_REQUEST2_ENDPOINT_HOST}"
            if sidecar_present
            else None
        ),
        "vendor_api_observed": vendor_api or None,
        "original_semantics_status": original_status,
        "sidecar_classification": "candidate_only" if sidecar_present else None,
        "sidecar_validation_status": sidecar_status,
        "closes_original_request2": False,
        "supports_pilot_pass_raw_only": False,
    }


def _compare_equity_sidecar_conflict(
    *,
    primary_rows: list[dict[str, Any]],
    sidecar_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Informational baostock vs Sina sidecar comparison — not authoritative for Request 2."""
    primary_by_date = {
        str(row.get("date")): row for row in primary_rows if row.get("date") is not None
    }
    sidecar_by_date = {
        str(row.get("date")): row for row in sidecar_rows if row.get("date") is not None
    }
    findings: list[dict[str, Any]] = []
    for trade_date in sorted(set(primary_by_date) & set(sidecar_by_date)):
        primary_close = primary_by_date[trade_date].get("close")
        sidecar_close = sidecar_by_date[trade_date].get("close")
        try:
            p_close = float(primary_close)
            s_close = float(sidecar_close)
            rel_diff = abs(p_close - s_close) / p_close if p_close else None
        except (TypeError, ValueError):
            rel_diff = None
        findings.append(
            {
                "trade_date": trade_date,
                "primary_source": "baostock",
                "sidecar_source": "akshare",
                "sidecar_vendor_api": SIDECAR_REQUEST2_VENDOR_API,
                "primary_close": primary_close,
                "sidecar_close": sidecar_close,
                "relative_close_diff": rel_diff,
                "informational_only": True,
            }
        )
    return findings


def _phase4_declared_validator_contract_refs() -> dict[str, Any]:
    """Freeze declared validator/conflict paths used to gate any clean write."""
    from backend.app.db.validation_gate import DbValidationGate
    from backend.app.validators.data_quality import DataQualityValidator
    from backend.app.validators.source_conflict import SourceConflictValidator

    return {
        "data_quality_validator": (
            f"{DataQualityValidator.__module__}.{DataQualityValidator.__name__}"
        ),
        "source_conflict_validator": (
            f"{SourceConflictValidator.__module__}.{SourceConflictValidator.__name__}"
        ),
        "clean_write_gate": f"{DbValidationGate.__module__}.{DbValidationGate.__name__}",
        "data_quality_rules": "specs/contracts/data_quality_rules.yaml",
        "source_conflict_rules": "specs/contracts/source_conflict_rules.yaml",
        "write_contract": "specs/contracts/write_contract.yaml",
        "freeze_note": (
            "Batch 2.75 Phase 4 remains raw/sandbox validation only. Any future clean write "
            "must pass DataQualityValidator, SourceConflictValidator, and DbValidationGate; "
            "local raw structure checks cannot independently authorize clean writes."
        ),
    }


def _format_phase4_conflict_inspect(
    *,
    conflict_rows: list[dict[str, Any]],
    request2_classification: dict[str, Any],
) -> str:
    lines = [
        "# Phase 4 — Source Conflict Inspect (Batch 2.75)",
        "",
        "## Scope",
        "",
        "- Validation covers Request 1 (baostock primary) and Request 3 (akshare macro shape).",
        "- Request 2 original endpoint (`stock_zh_a_hist` / Eastmoney push2his) is recorded as "
        "source/endpoint failure per reconciliation evidence.",
        "- Any baostock vs Sina sidecar rows below are **informational candidate comparison only** "
        "and do **not** close original Request 2.",
        "",
        "- **Request 2 original semantics:** "
        f"{request2_classification['original_semantics_status']}",
        f"- **Sidecar classification:** {request2_classification.get('sidecar_classification')}",
        "",
    ]
    if not conflict_rows:
        lines.extend(
            [
                "## Result",
                "",
                "NO_CONFLICT_INSPECT_REQUIRED_FOR_CLOSEOUT",
                "",
                "Sidecar comparison skipped or produced zero overlapping trade dates.",
                "",
            ]
        )
    else:
        lines.extend(["## Informational sidecar close diffs", ""])
        for row in conflict_rows:
            lines.append(
                f"- {row['trade_date']}: baostock close={row['primary_close']} vs "
                f"Sina sidecar close={row['sidecar_close']} "
                f"(rel_diff={row['relative_close_diff']}) [informational_only]"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def _require_request2_phase4_prerequisites(evidence_dir: Path) -> bool:
    reconciliation_path = evidence_dir / PHASE3_REQUEST2_RECONCILIATION_MD
    verdict_path = evidence_dir / EASTMONEY_VERDICT_MD
    missing = [
        name
        for name, path in (
            (PHASE3_REQUEST2_RECONCILIATION_MD, reconciliation_path),
            (EASTMONEY_VERDICT_MD, verdict_path),
        )
        if not path.is_file()
    ]
    if missing:
        raise LivePilotAuthorizationError(
            f"Request 2 Phase 4 prerequisites missing: {', '.join(missing)}"
        )

    reconciliation = reconciliation_path.read_text(encoding="utf-8")
    required_reconciliation_markers = (
        "stock_zh_a_hist",
        ORIGINAL_REQUEST2_ENDPOINT_HOST,
        "sidecar",
    )
    for marker in required_reconciliation_markers:
        if marker not in reconciliation:
            raise LivePilotAuthorizationError(f"Request 2 reconciliation missing marker: {marker}")

    verdict = verdict_path.read_text(encoding="utf-8")
    if (
        "不可用" not in verdict
        and "unreachable" not in verdict.lower()
        and "failure" not in verdict.lower()
    ):
        raise LivePilotAuthorizationError(
            "Request 2 verdict must record original endpoint failure/unavailability"
        )
    return "不可用" in verdict or "unreachable" in verdict.lower() or "failure" in verdict.lower()


def capture_phase4_validation(
    *,
    evidence_dir: Path,
    phase3_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Phase 4 raw validation + conflict inspect — default no clean write."""
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    if phase3_payload is None:
        phase3_path = evidence_dir / PHASE3_RAW_EVIDENCE_JSON
        if not phase3_path.is_file():
            raise FileNotFoundError(f"missing phase3 evidence: {phase3_path}")
        phase3_payload = json.loads(phase3_path.read_text(encoding="utf-8"))

    verdict_unavailable = _require_request2_phase4_prerequisites(evidence_dir)

    prod_before_counts = _key_table_row_counts(DEFAULT_PRODUCTION_DB)
    prod_before_hash = (
        DEFAULT_PRODUCTION_DB.read_bytes() if DEFAULT_PRODUCTION_DB.is_file() else None
    )

    fetches_by_id = {item["pilot_request_id"]: item for item in phase3_payload.get("fetches", [])}
    validations: list[dict[str, Any]] = []
    primary_equity_rows: list[dict[str, Any]] = []
    sidecar_equity_rows: list[dict[str, Any]] = []
    request2_classification: dict[str, Any] = {}

    for pilot_request_id in ("pilot-req-1", "pilot-req-2", "pilot-req-3"):
        fetch_item = fetches_by_id.get(pilot_request_id)
        if fetch_item is None:
            validations.append(
                {
                    "pilot_request_id": pilot_request_id,
                    "validation_scope": "missing_phase3_fetch",
                    "status": "FAILED",
                }
            )
            continue

        fetch_result = fetch_item["fetch_result"]
        raw_paths = fetch_result.get("raw_file_paths") or []
        raw_payload = None
        if raw_paths:
            raw_payload = _load_raw_json_payload(Path(raw_paths[0]))

        if pilot_request_id == "pilot-req-1":
            rows = _equity_bar_rows(raw_payload or {})
            structure = _validate_equity_raw_structure(rows)
            primary_equity_rows = rows
            validations.append(
                {
                    "pilot_request_id": pilot_request_id,
                    "validation_scope": "original_approved_semantics",
                    "data_domain": "cn_equity_daily_bar",
                    "source_id": "baostock",
                    "operation": "fetch_daily_bar",
                    "fetch_status": fetch_result.get("status"),
                    "structure_validation": structure,
                    "status": structure["status"],
                    "allow_clean_write": False,
                }
            )
        elif pilot_request_id == "pilot-req-2":
            request2_classification = _classify_request2_endpoint(
                raw_payload=raw_payload,
                verdict_unavailable=verdict_unavailable,
            )
            sidecar_structure = None
            if raw_payload and request2_classification["sidecar_classification"]:
                sidecar_rows = _equity_bar_rows(raw_payload)
                sidecar_equity_rows = sidecar_rows
                sidecar_structure = _validate_equity_raw_structure(sidecar_rows)
            validations.append(
                {
                    "pilot_request_id": pilot_request_id,
                    "validation_scope": "original_approved_semantics",
                    "data_domain": "cn_equity_daily_bar",
                    "source_id": "akshare",
                    "operation": "fetch_daily_bar_validation",
                    "fetch_status": fetch_result.get("status"),
                    "request2_endpoint_classification": request2_classification,
                    "sidecar_structure_validation": sidecar_structure,
                    "status": request2_classification["original_semantics_status"],
                    "allow_clean_write": False,
                }
            )
        else:
            macro_rows = (raw_payload or {}).get("rows", [])
            structure = _validate_macro_raw_structure(
                macro_rows if isinstance(macro_rows, list) else []
            )
            validations.append(
                {
                    "pilot_request_id": pilot_request_id,
                    "validation_scope": "original_approved_semantics",
                    "data_domain": "macro_supplementary",
                    "source_id": "akshare",
                    "operation": "fetch_macro_series",
                    "fetch_status": fetch_result.get("status"),
                    "structure_validation": structure,
                    "fred_primary_deferred": True,
                    "status": structure["status"],
                    "allow_clean_write": False,
                }
            )

    conflict_rows = _compare_equity_sidecar_conflict(
        primary_rows=primary_equity_rows,
        sidecar_rows=sidecar_equity_rows,
    )
    severe_findings = [
        {
            "pilot_request_id": item["pilot_request_id"],
            "status": item.get("status"),
            "validation_scope": item.get("validation_scope"),
        }
        for item in validations
        if item.get("status") in {"FAILED", "SOURCE_ENDPOINT_FAILURE"}
    ]
    severe_findings_block_clean_write = bool(severe_findings)

    prod_after_counts = _key_table_row_counts(DEFAULT_PRODUCTION_DB)
    prod_after_hash = (
        DEFAULT_PRODUCTION_DB.read_bytes() if DEFAULT_PRODUCTION_DB.is_file() else None
    )

    generated_at = _utc_now_iso()
    payload: dict[str, Any] = {
        "generated_at": generated_at,
        "phase": "phase4_validation",
        "allow_clean_write": False,
        "can_write_clean": False,
        "clean_write_performed": False,
        "clean_write_block_reasons": tuple(
            reason
            for reason in (
                "ALLOW_CLEAN_WRITE_FALSE_DEFAULT",
                "SEVERE_FINDINGS_PRESENT" if severe_findings_block_clean_write else None,
            )
            if reason is not None
        ),
        "declared_validation_conflict_paths": _phase4_declared_validator_contract_refs(),
        "severe_findings_block_clean_write": severe_findings_block_clean_write,
        "severe_findings": severe_findings,
        "request2_reconciliation_ref": PHASE3_REQUEST2_RECONCILIATION_MD,
        "eastmoney_verdict_ref": EASTMONEY_VERDICT_MD,
        "validation_scope_note": (
            "Request 1 and Request 3 validated under original approved semantics; "
            "Request 2 original endpoint failure recorded separately from Sina sidecar rows."
        ),
        "validations": validations,
        "production_mutation_proof": {
            "production_db_path": str(DEFAULT_PRODUCTION_DB),
            "db_hash_unchanged": prod_before_hash == prod_after_hash,
            "before_key_table_counts": prod_before_counts,
            "after_key_table_counts": prod_after_counts,
            "row_counts_unchanged": prod_before_counts == prod_after_counts,
        },
    }

    conflict_text = _format_phase4_conflict_inspect(
        conflict_rows=conflict_rows,
        request2_classification=request2_classification
        or _classify_request2_endpoint(raw_payload=None, verdict_unavailable=verdict_unavailable),
    )

    proof_lines = [
        "# Phase 4 — No Production Mutation Proof",
        "",
        f"- **Generated at:** {generated_at}",
        f"- **Production DB:** `{DEFAULT_PRODUCTION_DB}`",
        "- **allow_clean_write:** false",
        "- **can_write_clean:** false",
        "- **clean_write_performed:** false",
        f"- **clean_write_block_reasons:** {payload['clean_write_block_reasons']}",
        "- **declared_validation_conflict_paths:** "
        f"{payload['declared_validation_conflict_paths']}",
        f"- **severe_findings_block_clean_write:** {severe_findings_block_clean_write}",
        f"- **db_hash_unchanged:** {prod_before_hash == prod_after_hash}",
        f"- **row_counts_unchanged:** {prod_before_counts == prod_after_counts}",
        "",
    ]

    (evidence_dir / PHASE4_VALIDATION_REPORT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / PHASE4_CONFLICT_INSPECT_TXT).write_text(conflict_text, encoding="utf-8")
    (evidence_dir / PHASE4_NO_PRODUCTION_MUTATION_MD).write_text(
        "\n".join(proof_lines) + "\n",
        encoding="utf-8",
    )
    return payload


def capture_task_phase4_validation_evidence(evidence_dir: Path | str) -> dict[str, Any]:
    """Execute helper: Phase 4 validation on existing phase3 raw evidence."""
    return capture_phase4_validation(evidence_dir=Path(evidence_dir))


def derive_pilot_closeout_outcome(phase4_payload: dict[str, Any]) -> LivePilotOutcome:
    """Map per-request validation to a single PILOT_* closeout state."""
    statuses = {
        item["pilot_request_id"]: item.get("status")
        for item in phase4_payload.get("validations", [])
    }
    req2 = next(
        (
            item
            for item in phase4_payload.get("validations", [])
            if item.get("pilot_request_id") == "pilot-req-2"
        ),
        {},
    )
    original_req2_failed = req2.get("status") == "SOURCE_ENDPOINT_FAILURE"
    req1_ok = statuses.get("pilot-req-1") == "PASSED"
    req3_ok = statuses.get("pilot-req-3") == "PASSED"
    if original_req2_failed:
        return LivePilotOutcome.PILOT_FAIL_SOURCE
    if not req1_ok or not req3_ok:
        validation_failed = any(status == "FAILED" for status in statuses.values())
        return (
            LivePilotOutcome.PILOT_FAIL_VALIDATION
            if validation_failed
            else LivePilotOutcome.PILOT_FAIL_SOURCE
        )
    if phase4_payload.get("allow_clean_write"):
        return LivePilotOutcome.PILOT_PASS_SANDBOX_CLEAN
    return LivePilotOutcome.PILOT_PASS_RAW_ONLY


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_phase1_capability_snapshot() -> dict[str, Any]:
    """Read-only registry/capability status for approved pilot requests."""
    source_registry = SourceRegistry()
    source_registry.load()
    capability_registry = SourceCapabilityRegistry()
    capability_registry.load()

    pilot_requests: list[dict[str, Any]] = []
    for source_id, data_domain, operation in sorted(APPROVED_PILOT_REQUESTS):
        try:
            source = source_registry.get(source_id)
            source_in_registry = True
            source_enabled = source.is_enabled
            allowed_domains = sorted(source.allowed_domains)
        except SourceNotFoundError:
            source_in_registry = False
            source_enabled = False
            allowed_domains = []

        pilot_requests.append(
            {
                "source_id": source_id,
                "data_domain": data_domain,
                "operation": operation,
                "source_in_registry": source_in_registry,
                "source_enabled": source_enabled,
                "domain_allowed_for_source": data_domain in allowed_domains,
                "capability_declared": capability_registry.is_capability_declared(
                    source_id, data_domain
                ),
                "pilot_source_disabled": source_id in DISABLED_PILOT_SOURCE_IDS,
            }
        )

    return {
        "generated_at": _utc_now_iso(),
        "pilot_requests": pilot_requests,
        "disabled_pilot_source_ids": sorted(DISABLED_PILOT_SOURCE_IDS),
    }


def _format_phase1_baseline_md(
    payload: dict[str, Any],
    *,
    inspect_text: str,
) -> str:
    inspect = payload["inspect"]
    context = payload["baseline_context"]
    lines = [
        "# Phase 1 Baseline Inventory — Batch 2.75",
        "",
        f"- **Generated at:** {payload['generated_at']}",
        f"- **Inspect status:** {inspect.get('status')}",
        f"- **Mode:** {inspect.get('mode')}",
        f"- **DB path:** `{context.get('target_db_path')}`",
        f"- **DB exists:** {context.get('target_db_exists_at_capture')}",
        f"- **Data root:** `{context.get('target_data_root')}`",
        f"- **Capture strategy:** {context.get('capture_strategy')}",
        f"- **Read-only open:** {inspect.get('db', {}).get('read_only_open')}",
        "",
        inspect_text,
        "",
        "## Capability snapshot",
        "",
        f"See `{PHASE1_CAPABILITY_JSON}` for three approved pilot requests.",
    ]
    return "\n".join(lines) + "\n"


def _format_phase1_no_mutation_md(proof: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 — No Mutation Proof",
        "",
        f"- **Generated at:** {proof['generated_at']}",
        f"- **DB path:** `{proof['db_path']}`",
        f"- **DB hash unchanged:** {proof['db_hash_unchanged']}",
        f"- **Phase 1 zero mutation:** {proof['phase1_zero_mutation']}",
        "",
        "## Key table row counts",
        "",
        "| Table | Before | After |",
        "| ----- | ------ | ----- |",
    ]
    before = proof.get("before_key_table_counts") or {}
    after = proof.get("after_key_table_counts") or {}
    for name in KEY_TABLES:
        lines.append(f"| {name} | {before.get(name)} | {after.get(name)} |")
    return "\n".join(lines) + "\n"


def capture_phase1_baseline(
    *,
    db_path: Path,
    data_root: Path,
    evidence_dir: Path,
) -> dict[str, Any]:
    """Read-only Phase 1 baseline inventory + capability snapshot (zero mutation)."""
    db_path = Path(db_path)
    data_root = Path(data_root)
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    before_bytes = db_path.read_bytes() if db_path.is_file() else None
    before_counts = _key_table_row_counts(db_path)

    report = DbInspector(db_path, data_root).inspect()
    inspect_dict = report.to_dict()
    capability_snapshot = build_phase1_capability_snapshot()

    after_bytes = db_path.read_bytes() if db_path.is_file() else None
    after_counts = _key_table_row_counts(db_path)

    mutation_proof = {
        "generated_at": _utc_now_iso(),
        "db_path": str(db_path),
        "db_hash_unchanged": before_bytes == after_bytes,
        "before_key_table_counts": before_counts,
        "after_key_table_counts": after_counts,
        "phase1_zero_mutation": before_counts == after_counts and before_bytes == after_bytes,
    }

    baseline_context = {
        "target_db_path": str(db_path),
        "target_data_root": str(data_root),
        "target_db_exists_at_capture": db_path.is_file(),
        "capture_strategy": (
            "production_read_only" if db_path.is_file() else "synthetic_migrated_schema_only"
        ),
    }

    generated_at = _utc_now_iso()
    inventory_payload = {
        "generated_at": generated_at,
        "inspect": inspect_dict,
        "baseline_context": baseline_context,
        "capability_snapshot_ref": PHASE1_CAPABILITY_JSON,
    }

    (evidence_dir / PHASE1_BASELINE_JSON).write_text(
        json.dumps(inventory_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / PHASE1_BASELINE_MD).write_text(
        _format_phase1_baseline_md(inventory_payload, inspect_text=format_text_report(report)),
        encoding="utf-8",
    )
    (evidence_dir / PHASE1_NO_MUTATION_MD).write_text(
        _format_phase1_no_mutation_md(mutation_proof),
        encoding="utf-8",
    )
    (evidence_dir / PHASE1_CAPABILITY_JSON).write_text(
        json.dumps(capability_snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return {
        "generated_at": generated_at,
        "inspect": inspect_dict,
        "baseline_context": baseline_context,
        "capability_snapshot": capability_snapshot,
        "mutation_proof": mutation_proof,
    }


def capture_task_phase1_baseline_evidence(
    evidence_dir: Path | str,
    *,
    db_path: Path | None = None,
    data_root: Path | None = None,
) -> dict[str, Any]:
    """Execute helper: baseline against production paths or schema-only sandbox."""
    out = Path(evidence_dir)
    target_db = db_path or DEFAULT_PRODUCTION_DB
    target_root = data_root or DATA_ROOT

    if not target_db.is_file():
        sandbox = out / ".phase1-baseline-sandbox"
        sandbox_db_dir = sandbox / "duckdb"
        sandbox_db_dir.mkdir(parents=True, exist_ok=True)
        sandbox_data = sandbox / "data"
        sandbox_data.mkdir(parents=True, exist_ok=True)
        target_db = sandbox_db_dir / "quant_monitor.duckdb"
        if not target_db.is_file():
            import duckdb
            from backend.app.db.migrate import apply_migrations

            con = duckdb.connect(str(target_db))
            apply_migrations(con)
            con.close()
        target_root = sandbox_data

    return capture_phase1_baseline(
        db_path=target_db,
        data_root=target_root,
        evidence_dir=out,
    )
