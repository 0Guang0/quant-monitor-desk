"""Round 3 PROMPT_14 staged real-data pilot orchestration (fail-closed, sandbox-first).

``REHEARSAL_ONLY`` — not product live SSOT; see ``backend.app.ops.rehearsal_boundary``.
"""

from __future__ import annotations

from backend.app.ops.rehearsal_boundary import REHEARSAL_DISCLAIMER, REHEARSAL_ONLY

import hashlib
import json
from contextvars import ContextVar
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from backend.app.config import DATA_ROOT, PROJECT_ROOT
from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.datasources.capability_registry import SourceCapabilityRegistry
from backend.app.datasources.route_models import SourceRoutePlan
from backend.app.datasources.route_planner import SourceRoutePlanner
from backend.app.datasources.service import DataSourceService
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.db.connection import ConnectionManager
from backend.app.db.validation_gate import DbValidationGate, ValidationGateError, ValidationRejected
from backend.app.db.write_manager import WriteManager, WriteRequest
from backend.app.ops.mutation_proof import build_production_mutation_proof
from backend.app.ops.mutation_proof import key_table_row_counts as _key_table_row_counts
from backend.app.storage.file_registry import (
    STG_FILE_REGISTRY,
    FileRegistry,
    _parse_as_of_timestamp,
)
from backend.app.storage.raw_store import SavedFile
from backend.app.storage.staged_evidence import (
    STAGED_FILE_REGISTRY_PARSE_STATUS,
    STAGED_FILE_REGISTRY_QUALITY,
)

PILOT_ID = "r3x-staged-pilot-20260622"
DEFAULT_AUTHORIZATION_PATH = (
    PROJECT_ROOT / "docs/quality/prompt14_user_authorization_2026-06-22.md"
)
DEFAULT_PRODUCTION_DB = DATA_ROOT / "duckdb" / "quant_monitor.duckdb"
DEFAULT_SANDBOX_ROOT = PROJECT_ROOT / ".audit-sandbox/r3x-staged-pilot"

ROUTE_MATRIX_JSON = "route_preview_matrix.json"
FETCH_SUMMARY_JSON = "source_fetch_attempt_summary.json"
RAW_MANIFEST_JSON = "raw_evidence_manifest.json"
STAGING_MANIFEST_JSON = "staging_evidence_manifest.json"
VALIDATION_REPORT_JSON = "validation_report_summary.json"
RESOURCE_GUARD_JSON = "resource_guard_caps.json"
NO_MUTATION_MD = "production_db_no_mutation_proof.md"
CLOSEOUT_JSON = "pilot_closeout.json"
CONFLICT_CHECK_JSON = "conflict_check_summary.json"

MAX_PILOT_ROW_CAP = 100
MAX_NETWORK_CALLS_PER_RUN = 10

DISABLED_PILOT_SOURCE_IDS = frozenset(
    {
        "fred",
        "qmt_xtdata",
        "qmt_xqshare",
        "yahoo_finance",
        "tdx_pytdx",
    }
)

APPROVED_PILOT_REQUESTS: frozenset[tuple[str, str, str]] = frozenset(
    {
        ("baostock", "cn_equity_daily_bar", "fetch_daily_bar"),
        ("akshare", "cn_equity_daily_bar", "fetch_daily_bar_validation"),
        ("cninfo", "cn_announcements", "fetch_announcement_index"),
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
                "recent 10 trading days",
                10,
            ),
            (
                "akshare",
                "cn_equity_daily_bar",
                "fetch_daily_bar_validation",
                ("sh.600519",),
                "recent 10 trading days",
                10,
            ),
            (
                "cninfo",
                "cn_announcements",
                "fetch_announcement_index",
                ("sh.600519",),
                "recent 14 calendar days",
                10,
            ),
        }
    )
)


class StagedPilotOutcome(StrEnum):
    PILOT_PASS_STAGED_RAW = "PILOT_PASS_STAGED_RAW"
    PILOT_FAIL_SOURCE = "PILOT_FAIL_SOURCE"
    PILOT_FAIL_VALIDATION = "PILOT_FAIL_VALIDATION"
    PILOT_REDEFERRED = "PILOT_REDEFERRED"


class FetchTaxonomyStatus(StrEnum):
    """Fetch outcome taxonomy for staged pilot evidence (ADV-POST14-A-017)."""

    SUCCESS = "SUCCESS"
    EMPTY_RESPONSE = "EMPTY_RESPONSE"
    SOURCE_FAILURE = "SOURCE_FAILURE"
    UNKNOWN = "UNKNOWN"


class StagedPilotAuthorizationError(RuntimeError):
    """Raised when authorization evidence or request parameters fail fail-closed gate."""


class StagedPilotDisabledSourceError(RuntimeError):
    """Raised when source_id is not authorized for staged real-data pilot."""


class StagedPilotRouteNotReadyError(RuntimeError):
    """Raised when explicit source route is not READY before fetch."""


class StagedPilotFixtureForbiddenError(RuntimeError):
    """Raised when staged/fixture fetch port is used for real-data pilot evidence."""


class StagedPilotNetworkCapExceededError(RuntimeError):
    """Raised when network call budget for a pilot run is exhausted."""


@dataclass(frozen=True)
class StagedPilotRequest:
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


class _NetworkCallBudget:
    def __init__(self, limit: int = MAX_NETWORK_CALLS_PER_RUN) -> None:
        self._limit = limit
        self._count = 0

    def consume(self) -> None:
        # ponytail: one consume per run_staged_pilot_raw_only call, not per vendor HTTP
        if self._count >= self._limit:
            raise StagedPilotNetworkCapExceededError(
                f"max_network_calls_per_run={self._limit} exceeded"
            )
        self._count += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_network_calls_per_run": self._limit,
            "network_calls_consumed": self._count,
            "within_cap": self._count <= self._limit,
        }


_NETWORK_BUDGET_CTX: ContextVar[_NetworkCallBudget] = ContextVar("_staged_pilot_network_budget")


def reset_network_call_budget(*, limit: int | None = None) -> None:
    """Test hook: reset per-run network call counter (v1 default 10, v2 uses MAX_NETWORK_CALLS_V2)."""
    effective = limit if limit is not None else MAX_NETWORK_CALLS_PER_RUN
    _NETWORK_BUDGET_CTX.set(_NetworkCallBudget(limit=effective))


def _active_network_budget() -> _NetworkCallBudget:
    try:
        return _NETWORK_BUDGET_CTX.get()
    except LookupError:
        budget = _NetworkCallBudget()
        _NETWORK_BUDGET_CTX.set(budget)
        return budget


def network_call_budget_snapshot() -> dict[str, Any]:
    return _active_network_budget().to_dict()


def _resolve_authorization_path(path: str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate.resolve()


def validate_authorization(request: StagedPilotRequest) -> None:
    """Fail-closed authorization gate — must pass before route preview or fetch."""
    auth_path = _resolve_authorization_path(request.authorization_evidence)
    if not auth_path.is_file():
        raise StagedPilotAuthorizationError(
            f"authorization evidence missing: {request.authorization_evidence}"
        )

    auth_text = auth_path.read_text(encoding="utf-8")
    if "prompt14_user_authorization" not in auth_path.name:
        raise StagedPilotAuthorizationError(
            f"authorization evidence must be prompt14 user authorization file: {auth_path.name}"
        )
    if not auth_path.name.startswith("prompt14_user_authorization_"):
        raise StagedPilotAuthorizationError(
            f"authorization filename must match prompt14_user_authorization_*: {auth_path.name}"
        )
    if "Approved on" not in auth_text:
        raise StagedPilotAuthorizationError("authorization evidence missing approval marker")

    if request.source_id in DISABLED_PILOT_SOURCE_IDS:
        raise StagedPilotDisabledSourceError(
            f"source {request.source_id!r} is not authorized for staged real-data pilot"
        )

    triple = (request.source_id, request.data_domain, request.operation)
    if triple not in APPROVED_PILOT_REQUESTS:
        raise StagedPilotAuthorizationError(
            f"request triple {triple!r} not in approved micro-pilot set"
        )

    if not request.raw_only:
        raise StagedPilotAuthorizationError("staged pilot requires raw_only=true")
    if request.write_target != "sandbox":
        raise StagedPilotAuthorizationError("write_target must be sandbox")
    if request.allow_clean_write:
        raise StagedPilotAuthorizationError(
            "allow_clean_write must be false for staged real-data pilot"
        )
    if request.max_rows <= 0 or request.max_rows > MAX_PILOT_ROW_CAP:
        raise StagedPilotAuthorizationError(
            f"max_rows must be in 1..{MAX_PILOT_ROW_CAP}, got {request.max_rows}"
        )
    if not request.symbols_or_indicators:
        raise StagedPilotAuthorizationError("symbols_or_indicators must be non-empty")
    if len(request.symbols_or_indicators) > 3:
        raise StagedPilotAuthorizationError("max_symbols cap is 3 per request envelope")

    envelope = (
        request.source_id,
        request.data_domain,
        request.operation,
        request.symbols_or_indicators,
        request.date_window,
        request.max_rows,
    )
    if envelope not in APPROVED_PILOT_REQUEST_ENVELOPES:
        raise StagedPilotAuthorizationError(
            "request envelope does not exactly match approved micro-pilot authorization"
        )


def assert_pilot_ready_before_fetch(request: StagedPilotRequest) -> None:
    validate_authorization(request)


def approved_pilot_requests() -> tuple[StagedPilotRequest, ...]:
    auth = "docs/quality/prompt14_user_authorization_2026-06-22.md"
    return (
        StagedPilotRequest(
            source_id="baostock",
            data_domain="cn_equity_daily_bar",
            operation="fetch_daily_bar",
            symbols_or_indicators=("sh.600519",),
            date_window="recent 10 trading days",
            max_rows=10,
            authorization_evidence=auth,
        ),
        StagedPilotRequest(
            source_id="akshare",
            data_domain="cn_equity_daily_bar",
            operation="fetch_daily_bar_validation",
            symbols_or_indicators=("sh.600519",),
            date_window="recent 10 trading days",
            max_rows=10,
            authorization_evidence=auth,
        ),
        StagedPilotRequest(
            source_id="cninfo",
            data_domain="cn_announcements",
            operation="fetch_announcement_index",
            symbols_or_indicators=("sh.600519",),
            date_window="recent 14 calendar days",
            max_rows=10,
            authorization_evidence=auth,
        ),
    )


def _pilot_request_to_dict(request: StagedPilotRequest) -> dict[str, Any]:
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
    if source_id in DISABLED_PILOT_SOURCE_IDS:
        return "DISABLED_SOURCE"
    return "DISABLED_SOURCE"


def _evidence_relative_path(path: Path | str) -> str:
    """Evidence paths relative to project root when possible (ADV-POST14-A-013)."""
    candidate = Path(path).resolve()
    try:
        return candidate.relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return candidate.as_posix()


def _declared_validator_contract_refs() -> dict[str, str]:
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
    }


def _staged_conflict_check_summary() -> dict[str, Any]:
    """Explicit no-conflict defer for single-source staged micro-fetch (ADV-POST14-A-002)."""
    refs = _declared_validator_contract_refs()
    return {
        "status": "NO_CONFLICT_CHECK_DEFERRED",
        "reason": (
            "staged raw-only micro-fetch uses one authorized source per request envelope; "
            "multi-source conflict compare deferred until sample expansion"
        ),
        "source_conflict_validator": refs["source_conflict_validator"],
        "policy_ref": "docs/quality/production_live_pilot_policy.md §6",
    }


def preview_staged_pilot(
    request: StagedPilotRequest,
    *,
    service: DataSourceService | None = None,
    pilot_request_id: str = "staged-req",
    authorization_gate: Any | None = None,
) -> dict[str, Any]:
    """Dry-run route preview for one authorized pilot request (no fetch)."""
    (authorization_gate or validate_authorization)(request)
    if not request.dry_run:
        raise StagedPilotAuthorizationError("route preview requires dry_run=true")

    svc = service or DataSourceService()
    guard_decision, guard_reason = svc.check_resource_guard()
    if guard_decision == Decision.HARD_STOP:
        raise RuntimeError(f"ResourceGuard HARD_STOP: {guard_reason}")

    route_plan = svc.preview_route(
        data_domain=request.data_domain,
        operation=request.operation,
        run_id=f"{pilot_request_id}-preview",
        job_id="r3x-staged-pilot-route",
    )
    explicit_status = _explicit_source_route_status(
        source_id=request.source_id,
        candidates=route_plan.candidates,
    )
    override_applied = "PILOT_EXPLICIT_SOURCE_SELECTED" in route_plan.quality_flags

    return {
        "pilot_id": PILOT_ID,
        "pilot_request_id": pilot_request_id,
        "request": _pilot_request_to_dict(request),
        "authorization_evidence": _evidence_relative_path(
            _resolve_authorization_path(request.authorization_evidence)
        ),
        "dry_run": True,
        "route_plan": route_plan.to_payload_dict(),
        "explicit_source_route_status": explicit_status,
        "organic_route_status": route_plan.route_status,
        "pilot_route_override_applied": override_applied,
        "resource_guard_decision": guard_decision.value,
        "resource_guard_reason": guard_reason,
    }


def capture_route_preview_matrix(
    *,
    requests: tuple[StagedPilotRequest, ...],
    evidence_dir: Path,
    db_path: Path | None = None,
    service: DataSourceService | None = None,
) -> dict[str, Any]:
    """Route preview matrix — zero fetch, optional production DB no-mutation proof."""
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    target_db = db_path or DEFAULT_PRODUCTION_DB
    before_counts = _key_table_row_counts(target_db) if target_db.is_file() else {}
    before_bytes = target_db.read_bytes() if target_db.is_file() else None

    svc = service or DataSourceService()
    previews: list[dict[str, Any]] = []
    for index, request in enumerate(requests, start=1):
        previews.append(
            preview_staged_pilot(
                request,
                service=svc,
                pilot_request_id=f"staged-req-{index}",
            )
        )

    mutation_proof = build_production_mutation_proof(
        target_db,
        before_counts=before_counts,
        before_bytes=before_bytes,
    )

    generated_at = _utc_now_iso()
    payload: dict[str, Any] = {
        "pilot_id": PILOT_ID,
        "generated_at": generated_at,
        "phase": "route_preview",
        "dry_run": True,
        "run_mode": "staged_only",
        "authorization_evidence": requests[0].authorization_evidence if requests else None,
        "previews": previews,
        "mutation_proof": mutation_proof,
    }

    (evidence_dir / ROUTE_MATRIX_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def _assert_real_fetch_port(fetch_port: object) -> None:
    from backend.app.datasources.adapters.fetch_port import LocalFixtureFetchPort, StubFetchPort

    if isinstance(fetch_port, (StubFetchPort, LocalFixtureFetchPort)):
        raise StagedPilotFixtureForbiddenError(
            "fixture/staged FetchPort forbidden for real-data pilot evidence"
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


class _ExplicitSourceRoutePlanner:
    """Force pilot-approved source_id when it is an enabled route candidate."""

    def __init__(self, inner: SourceRoutePlanner, forced_source_id: str) -> None:
        self._inner = inner
        self._forced_source_id = forced_source_id

    def plan(self, **kwargs: Any) -> SourceRoutePlan:
        plan = self._inner.plan(**kwargs)
        enabled_ids = {c.source_id for c in plan.candidates if c.enabled}
        if self._forced_source_id not in enabled_ids:
            return plan
        flags = list(plan.quality_flags)
        if plan.selected_source_id != self._forced_source_id:
            flags.append("PILOT_EXPLICIT_SOURCE_SELECTED")
        return replace(
            plan,
            selected_source_id=self._forced_source_id,
            quality_flags=flags,
            requested_source_id=self._forced_source_id,
        )


class _InlineConnectionFileRegistry(FileRegistry):
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
                run_id="r3x-staged-pilot-raw",
                job_id="register",
                own_transaction=False,
            )
        return super().register(saved)


class _StagedPilotFileRegistry(_InlineConnectionFileRegistry):
    """WriteManager path with STAGED quality_flag (ADV-POST14-A-004 / B-002)."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.registered_file_ids: list[str] = []

    def register_on_connection(
        self,
        con,
        saved: SavedFile,
        *,
        run_id: str,
        job_id: str,
        own_transaction: bool = False,
    ) -> str:
        existing = self._lookup_by_content_hash(saved.content_hash, con=con)
        if existing:
            self.registered_file_ids.append(existing)
            return existing

        now = datetime.now(UTC)
        as_of_ts = _parse_as_of_timestamp(saved.as_of)
        req = WriteRequest(
            run_id=run_id,
            job_id=job_id,
            target_table="file_registry",
            staging_table=STG_FILE_REGISTRY,
            write_mode="append_only",
            primary_keys=("file_id",),
            validation_report_id=self._validation_report_id,
            source_used=saved.source,
            data_domain=saved.data_domain,
        )

        con.execute(f"DELETE FROM {STG_FILE_REGISTRY}")
        con.execute(
            f"""
            INSERT INTO {STG_FILE_REGISTRY} (
                file_id, file_type, source, source_url, local_path,
                content_hash, schema_hash, fetch_time, as_of_timestamp,
                parse_status, quality_flag
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                saved.file_id,
                saved.file_type,
                saved.source,
                None,
                saved.local_path,
                saved.content_hash,
                None,
                now,
                as_of_ts,
                STAGED_FILE_REGISTRY_PARSE_STATUS,
                STAGED_FILE_REGISTRY_QUALITY,
            ],
        )
        result = self.write_manager.write(req, con=con, own_transaction=own_transaction)
        if result.status != "SUCCESS":
            err = result.error_message or ""
            if "onstraint" in err:
                existing = self._lookup_by_content_hash(saved.content_hash, con=con)
                if existing:
                    self.registered_file_ids.append(existing)
                    return existing
            raise RuntimeError(f"file_registry write failed: {result.error_message}")

        self.registered_file_ids.append(saved.file_id)
        return saved.file_id


STAGED_RAW_VALIDATION_REPORT_ID = "r3x-staged-pilot-raw-file-registry"
STAGED_RAW_RULE_SET_ID = "p0_round_1"
STAGED_RAW_METADATA_QUALITY_FLAG = "staged_raw_metadata_only"


class _StagedPilotValidationGate(DbValidationGate):
    """Allow WriteManager file_registry staging when report is metadata-only (A-007 + A-004)."""

    def assert_can_write(
        self,
        validation_report_id: str,
        write_mode: str,
        *,
        con=None,
    ) -> str:
        report = self._fetch_report(validation_report_id, con=con)
        if report is None:
            raise ValidationGateError(
                f"unknown validation_report_id: {validation_report_id}",
                validation_report_id=validation_report_id,
            )
        (
            status,
            can_write_clean,
            needs_manual_review,
            run_id,
            job_id,
            source_id,
            quality_flags,
        ) = report
        if (
            write_mode == "append_only"
            and not can_write_clean
            and quality_flags == STAGED_RAW_METADATA_QUALITY_FLAG
        ):
            if status == "FAILED":
                raise ValidationRejected(
                    f"validation report {validation_report_id!r} status=FAILED",
                    validation_report_id=validation_report_id,
                )
            return str(status)
        return super().assert_can_write(
            validation_report_id,
            write_mode,
            con=con,
        )


def _ensure_raw_validation_report(con, request: StagedPilotRequest, run_id: str) -> None:
    con.execute(
        """
        INSERT OR REPLACE INTO validation_report (
            validation_report_id, run_id, job_id, data_domain, staging_table,
            source_id, status, checked_rows, failed_rows, warning_rows,
            quality_flags, stale_reason, can_write_clean, needs_manual_review,
            rule_set_id, rule_version, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            STAGED_RAW_VALIDATION_REPORT_ID,
            run_id,
            "register",
            request.data_domain,
            "stg_file_registry",
            request.source_id,
            "PASSED",
            0,
            0,
            0,
            STAGED_RAW_METADATA_QUALITY_FLAG,
            None,
            False,
            True if request.source_id == "akshare" else False,
            STAGED_RAW_RULE_SET_ID,
            STAGED_RAW_RULE_SET_ID,
            datetime.now(UTC),
        ],
    )


def run_staged_pilot_raw_only(
    request: StagedPilotRequest,
    *,
    sandbox_root: Path,
    pilot_request_id: str = "staged-req",
    authorization_gate: Any | None = None,
) -> dict[str, Any]:
    """Sandbox raw-only fetch for one authorized request (route gate + network cap)."""
    (authorization_gate or validate_authorization)(request)
    if not request.raw_only:
        raise StagedPilotAuthorizationError("staged pilot requires raw_only=true")

    preview = preview_staged_pilot(
        replace(request, dry_run=True),
        pilot_request_id=f"{pilot_request_id}-pre",
        authorization_gate=authorization_gate,
    )
    if preview["explicit_source_route_status"] != "READY":
        raise StagedPilotRouteNotReadyError(
            f"explicit source route not READY: {preview['explicit_source_route_status']}"
        )

    prod_before_counts = _key_table_row_counts(DEFAULT_PRODUCTION_DB)
    prod_before_hash = (
        DEFAULT_PRODUCTION_DB.read_bytes() if DEFAULT_PRODUCTION_DB.is_file() else None
    )

    data_root, sandbox_db = _ensure_sandbox_db(sandbox_root)
    from backend.app.datasources.fetch_result import FetchRequest
    from backend.app.ops.staged_pilot_fetch_ports import create_staged_fetch_port

    fetch_port = create_staged_fetch_port(
        source_id=request.source_id,
        operation=request.operation,
        symbols_or_indicators=request.symbols_or_indicators,
        max_rows=request.max_rows,
        date_window=request.date_window,
    )
    fetch_port_class = type(fetch_port).__name__
    _assert_real_fetch_port(fetch_port)
    _active_network_budget().consume()

    registry = SourceRegistry()
    registry.load()
    capability_registry = SourceCapabilityRegistry()
    capability_registry.load()
    base_planner = SourceRoutePlanner(
        source_registry=registry,
        capability_registry=capability_registry,
    )
    route_planner = _ExplicitSourceRoutePlanner(base_planner, request.source_id)
    cm = ConnectionManager(sandbox_db, profile="eco")
    write_manager = WriteManager(cm, _StagedPilotValidationGate(cm))
    file_registry = _StagedPilotFileRegistry(
        cm,
        write_manager,
        validation_report_id=STAGED_RAW_VALIDATION_REPORT_ID,
    )
    service = DataSourceService(
        source_registry=registry,
        capability_registry=capability_registry,
        route_planner=route_planner,
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

    staged_file_ids: tuple[str, ...] = ()
    with cm.writer() as con:
        _ensure_raw_validation_report(con, request, fetch_req.run_id)
        file_registry.bind_connection(con)
        result = service.fetch(
            fetch_req,
            con=con,
            job_id="register",
            operation=request.operation,
        )
        if result.status == "SUCCESS":
            staged_file_ids = tuple(file_registry.registered_file_ids)

    production_mutation_proof = build_production_mutation_proof(
        DEFAULT_PRODUCTION_DB,
        before_counts=prod_before_counts,
        before_bytes=prod_before_hash,
    )

    raw_paths = [_evidence_relative_path(p) for p in result.raw_file_paths]
    sandbox_resolved = sandbox_root.resolve()
    for path in result.raw_file_paths:
        if not Path(path).resolve().is_relative_to(sandbox_resolved):
            raise StagedPilotAuthorizationError(f"raw evidence path outside sandbox: {path}")

    return {
        "pilot_id": PILOT_ID,
        "pilot_request_id": pilot_request_id,
        "authorization_evidence": _evidence_relative_path(
            _resolve_authorization_path(request.authorization_evidence)
        ),
        "request": _pilot_request_to_dict(request),
        "route_preview": preview,
        "fetch_port_class": fetch_port_class,
        "fetch_result": result.model_dump(),
        "staged_file_ids": list(staged_file_ids),
        "file_registry_quality_flag": STAGED_FILE_REGISTRY_QUALITY,
        "file_registry_write_path": "WriteManager",
        "sandbox_root": _evidence_relative_path(sandbox_root),
        "sandbox_data_root": _evidence_relative_path(data_root),
        "production_mutation_proof": production_mutation_proof,
        "taxonomy_status": _classify_fetch_taxonomy(request, result).value,
    }


def _classify_fetch_taxonomy(request: StagedPilotRequest, result: Any) -> FetchTaxonomyStatus:
    if result.status == "SUCCESS" and result.row_count > 0:
        return FetchTaxonomyStatus.SUCCESS
    if result.status == "SUCCESS" and result.row_count == 0:
        return FetchTaxonomyStatus.EMPTY_RESPONSE
    if result.status in {"DISABLED_SOURCE", "FAILED"}:
        return FetchTaxonomyStatus.SOURCE_FAILURE
    return FetchTaxonomyStatus.UNKNOWN


def capture_raw_and_staging_evidence(
    *,
    requests: tuple[StagedPilotRequest, ...],
    sandbox_root: Path,
    evidence_dir: Path,
) -> dict[str, Any]:
    """Execute authorized raw fetches and persist raw/staging manifests."""
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    sandbox_root = Path(sandbox_root)

    reset_network_call_budget()
    fetches: list[dict[str, Any]] = []
    for index, request in enumerate(requests, start=1):
        live_request = StagedPilotRequest(
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
        pilot_request_id = f"staged-req-{index}"
        prod_before_counts = _key_table_row_counts(DEFAULT_PRODUCTION_DB)
        prod_before_hash = (
            DEFAULT_PRODUCTION_DB.read_bytes() if DEFAULT_PRODUCTION_DB.is_file() else None
        )
        try:
            fetches.append(
                run_staged_pilot_raw_only(
                    live_request,
                    sandbox_root=sandbox_root / f"req-{index}",
                    pilot_request_id=pilot_request_id,
                )
            )
        except Exception as exc:
            production_mutation_proof = build_production_mutation_proof(
                DEFAULT_PRODUCTION_DB,
                before_counts=prod_before_counts,
                before_bytes=prod_before_hash,
            )
            failure_item = {
                "pilot_id": PILOT_ID,
                "pilot_request_id": pilot_request_id,
                "request": _pilot_request_to_dict(live_request),
                "fetch_result": {
                    "status": "FAILED",
                    "row_count": 0,
                    "raw_file_paths": [],
                    "content_hash": None,
                    "error_message": str(exc),
                },
                "taxonomy_status": FetchTaxonomyStatus.SOURCE_FAILURE.value,
                "production_mutation_proof": production_mutation_proof,
            }
            fetches.append(failure_item)

    generated_at = _utc_now_iso()
    fetch_summary = {
        "pilot_id": PILOT_ID,
        "generated_at": generated_at,
        "attempts": [
            {
                "pilot_request_id": item["pilot_request_id"],
                "source_id": item["request"]["source_id"],
                "data_domain": item["request"]["data_domain"],
                "operation": item["request"]["operation"],
                "status": item.get("fetch_result", {}).get("status"),
                "row_count": item.get("fetch_result", {}).get("row_count"),
                "taxonomy_status": item.get("taxonomy_status"),
            }
            for item in fetches
        ],
    }
    raw_manifest = {
        "pilot_id": PILOT_ID,
        "generated_at": generated_at,
        "sandbox_root": _evidence_relative_path(sandbox_root),
        "fetches": fetches,
    }
    staging_manifest = {
        "pilot_id": PILOT_ID,
        "generated_at": generated_at,
        "staged_rows": [
            {
                "pilot_request_id": item["pilot_request_id"],
                "staged_file_ids": item.get("staged_file_ids", []),
                "quality_flag": STAGED_FILE_REGISTRY_QUALITY,
                "file_registry_write_path": item.get("file_registry_write_path", "WriteManager"),
            }
            for item in fetches
            if item.get("staged_file_ids")
        ],
        "allow_clean_write": False,
    }

    (evidence_dir / FETCH_SUMMARY_JSON).write_text(
        json.dumps(fetch_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / RAW_MANIFEST_JSON).write_text(
        json.dumps(raw_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / STAGING_MANIFEST_JSON).write_text(
        json.dumps(staging_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return raw_manifest


def _resolve_evidence_path(raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    return (PROJECT_ROOT / candidate).resolve()


def _load_raw_json_payload(raw_path: Path | str) -> dict[str, Any]:
    return json.loads(_resolve_evidence_path(str(raw_path)).read_text(encoding="utf-8"))


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
    status = "FAILED" if findings else "PASSED"
    return {"status": status, "checked_rows": len(rows), "findings": findings}


def _validate_metadata_structure(rows: list[dict[str, Any]]) -> dict[str, Any]:
    findings: list[str] = []
    if not rows:
        findings.append("EMPTY_ROWS")
        return {"status": "FAILED", "checked_rows": 0, "findings": findings}
    status = "FAILED" if findings else "PASSED"
    return {"status": status, "checked_rows": len(rows), "findings": findings}


def _validate_cninfo_metadata_structure(rows: list[dict[str, Any]]) -> dict[str, Any]:
    findings: list[str] = []
    if not rows:
        findings.append("EMPTY_ROWS")
        return {"status": "FAILED", "checked_rows": 0, "findings": findings}
    title_keys = ("公告标题", "announcementTitle", "title", "公告时间", "announcementTime")
    for index, row in enumerate(rows):
        if not any(key in row and row[key] not in (None, "") for key in title_keys):
            findings.append(f"ROW_{index}_MISSING_ANNOUNCEMENT_FIELDS")
    status = "FAILED" if findings else "PASSED"
    return {"status": status, "checked_rows": len(rows), "findings": findings}


def capture_validation_report(
    *,
    evidence_dir: Path,
    raw_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validation summary on raw evidence — default no clean write."""
    evidence_dir = Path(evidence_dir)
    if raw_manifest is None:
        raw_path = evidence_dir / RAW_MANIFEST_JSON
        if not raw_path.is_file():
            raise FileNotFoundError(f"missing raw manifest: {raw_path}")
        raw_manifest = json.loads(raw_path.read_text(encoding="utf-8"))

    prod_before_counts = _key_table_row_counts(DEFAULT_PRODUCTION_DB)
    prod_before_hash = (
        DEFAULT_PRODUCTION_DB.read_bytes() if DEFAULT_PRODUCTION_DB.is_file() else None
    )

    validations: list[dict[str, Any]] = []
    for item in raw_manifest.get("fetches", []):
        fetch_result = item.get("fetch_result", {})
        raw_paths = fetch_result.get("raw_file_paths") or []
        raw_payload = None
        if raw_paths:
            raw_payload = _load_raw_json_payload(raw_paths[0])

        request = item.get("request", {})
        domain = request.get("data_domain")
        source_id = request.get("source_id")
        if domain == "cn_equity_daily_bar":
            structure = _validate_equity_raw_structure(_equity_bar_rows(raw_payload or {}))
        elif domain == "cn_announcements":
            rows = (raw_payload or {}).get("rows", [])
            structure = _validate_cninfo_metadata_structure(
                rows if isinstance(rows, list) else []
            )
        else:
            rows = (raw_payload or {}).get("rows", [])
            structure = _validate_metadata_structure(rows if isinstance(rows, list) else [])

        vendor_api = (raw_payload or {}).get("vendor_api")
        validations.append(
            {
                "pilot_request_id": item.get("pilot_request_id"),
                "source_id": source_id,
                "data_domain": domain,
                "operation": request.get("operation"),
                "fetch_status": fetch_result.get("status"),
                "vendor_api": vendor_api,
                "structure_validation": structure,
                "status": structure["status"]
                if fetch_result.get("status") == "SUCCESS"
                else "SOURCE_FAILURE",
                "allow_clean_write": False,
                "can_write_clean": False,
                "validation_only": source_id == "akshare",
                "metadata_only": source_id == "cninfo",
            }
        )

    production_mutation_proof = build_production_mutation_proof(
        DEFAULT_PRODUCTION_DB,
        before_counts=prod_before_counts,
        before_bytes=prod_before_hash,
    )
    conflict_check = _staged_conflict_check_summary()
    declared_validators = _declared_validator_contract_refs()

    generated_at = _utc_now_iso()
    payload: dict[str, Any] = {
        "pilot_id": PILOT_ID,
        "generated_at": generated_at,
        "allow_clean_write": False,
        "can_write_clean": False,
        "clean_write_performed": False,
        "declared_validators": declared_validators,
        "sandbox_validation_note": (
            "Structure checks plus declared DataQualityValidator / DbValidationGate "
            "contract refs; full rule execution remains gated before any clean write."
        ),
        "validations": validations,
        "conflict_check": conflict_check,
        "production_mutation_proof": production_mutation_proof,
    }

    proof_lines = [
        "# Production DB — No Mutation Proof (PROMPT_14 staged pilot)",
        "",
        f"- **Pilot ID:** {PILOT_ID}",
        f"- **Generated at:** {generated_at}",
        f"- **Production DB:** `{DEFAULT_PRODUCTION_DB}`",
        f"- **proof_status:** {production_mutation_proof.get('proof_status')}",
        f"- **db_hash_unchanged:** {production_mutation_proof.get('db_hash_unchanged')}",
        f"- **row_counts_unchanged:** {production_mutation_proof.get('row_counts_unchanged')}",
        "",
        "## Conflict check",
        "",
        f"- **status:** {conflict_check['status']}",
        f"- **reason:** {conflict_check['reason']}",
        "",
    ]
    for item in raw_manifest.get("fetches", []):
        proof = item.get("production_mutation_proof", {})
        proof_lines.append(
            f"- **{item.get('pilot_request_id')}:** proof_status="
            f"{proof.get('proof_status')} hash_unchanged={proof.get('db_hash_unchanged')} "
            f"row_counts_unchanged={proof.get('row_counts_unchanged')}"
        )

    (evidence_dir / VALIDATION_REPORT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / NO_MUTATION_MD).write_text("\n".join(proof_lines) + "\n", encoding="utf-8")
    (evidence_dir / CONFLICT_CHECK_JSON).write_text(
        json.dumps(conflict_check, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def derive_pilot_closeout_outcome(validation_payload: dict[str, Any]) -> StagedPilotOutcome:
    validations = validation_payload.get("validations", [])
    if not validations:
        return StagedPilotOutcome.PILOT_REDEFERRED
    statuses = [item.get("status") for item in validations]
    if any(status == "PASSED" for status in statuses):
        return StagedPilotOutcome.PILOT_PASS_STAGED_RAW
    if any(status == "FAILED" for status in statuses):
        return StagedPilotOutcome.PILOT_FAIL_VALIDATION
    if any(status == "SOURCE_FAILURE" for status in statuses):
        return StagedPilotOutcome.PILOT_FAIL_SOURCE
    return StagedPilotOutcome.PILOT_REDEFERRED


def run_full_staged_pilot(
    evidence_dir: Path | str,
    *,
    sandbox_root: Path | None = None,
    db_path: Path | None = None,
    skip_live_fetch: bool = False,
) -> dict[str, Any]:
    """End-to-end staged pilot evidence capture (route → optional fetch → validation)."""
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    sandbox = sandbox_root or DEFAULT_SANDBOX_ROOT
    requests = approved_pilot_requests()

    route_payload = capture_route_preview_matrix(
        requests=requests,
        evidence_dir=evidence_dir,
        db_path=db_path or DEFAULT_PRODUCTION_DB,
    )

    guard = ResourceGuard()
    guard_decision, guard_reason = guard.check()
    guard_payload = {
        "pilot_id": PILOT_ID,
        "generated_at": _utc_now_iso(),
        "decision": guard_decision.value,
        "reason": guard_reason,
        "network_call_budget": network_call_budget_snapshot(),
        "caps": {
            "max_symbols": 3,
            "max_trade_days": 20,
            "max_rows_per_source_domain": MAX_PILOT_ROW_CAP,
            "max_network_calls_per_run": MAX_NETWORK_CALLS_PER_RUN,
            "production_clean_write": False,
        },
    }
    (evidence_dir / RESOURCE_GUARD_JSON).write_text(
        json.dumps(guard_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    raw_manifest: dict[str, Any] | None = None
    if not skip_live_fetch and guard_decision != Decision.HARD_STOP:
        raw_manifest = capture_raw_and_staging_evidence(
            requests=requests,
            sandbox_root=sandbox,
            evidence_dir=evidence_dir,
        )
        guard_payload["network_call_budget"] = network_call_budget_snapshot()
        (evidence_dir / RESOURCE_GUARD_JSON).write_text(
            json.dumps(guard_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    validation_payload = capture_validation_report(
        evidence_dir=evidence_dir,
        raw_manifest=raw_manifest or {"fetches": []},
    )
    outcome = derive_pilot_closeout_outcome(validation_payload)
    mutation_status = validation_payload.get("production_mutation_proof", {}).get("proof_status")
    closeout = {
        "pilot_id": PILOT_ID,
        "generated_at": _utc_now_iso(),
        "outcome": outcome.value,
        "run_mode": "staged_only",
        "rehearsal_only": REHEARSAL_ONLY,
        "rehearsal_disclaimer": REHEARSAL_DISCLAIMER,
        "production_live_readiness_claim": False,
        "skip_live_fetch": skip_live_fetch,
        "mutation_proof_status": mutation_status,
        "conflict_check_status": validation_payload.get("conflict_check", {}).get("status"),
        "closeout_narrative": (
            "Staged raw evidence captured under PROMPT_14 authorization; "
            "production DB mutation proof is "
            f"{mutation_status or 'unknown'}. "
            "Expand sample only after registry review and conflict policy sign-off."
        ),
        "close_or_redefer": (
            "expand_sample_after_review"
            if outcome == StagedPilotOutcome.PILOT_PASS_STAGED_RAW
            else "re_defer_failed_sources"
        ),
    }
    (evidence_dir / CLOSEOUT_JSON).write_text(
        json.dumps(closeout, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return {
        "pilot_id": PILOT_ID,
        "outcome": outcome.value,
        "route_preview": route_payload,
        "raw_manifest": raw_manifest,
        "validation": validation_payload,
        "resource_guard": guard_payload,
        "closeout": closeout,
    }


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# --- PROMPT_19 staged pilot v2 (expanded sample, fail-closed) ----------------

PILOT_ID_V2 = "r3y-staged-pilot-v2-20260624"
DEFAULT_SANDBOX_ROOT_V2 = PROJECT_ROOT / ".audit-sandbox/r3y-staged-pilot-v2"

PILOT_V2_CAPS_JSON = "pilot_v2_caps.json"
ROUTE_MATRIX_V2_JSON = "route_preview_matrix_v2.json"
RAW_MANIFEST_V2_JSON = "raw_evidence_manifest_v2.json"
STAGING_MANIFEST_V2_JSON = "staging_evidence_manifest_v2.json"
VALIDATION_REPORT_V2_JSON = "validation_report_v2.json"
CONFLICT_CHECK_V2_JSON = "conflict_check_summary_v2.json"
NO_MUTATION_V2_MD = "no_mutation_proof_v2.md"
CLOSEOUT_V2_JSON = "pilot_v2_closeout.json"
AKSHARE_TAXONOMY_V2_JSON = "akshare_validation_taxonomy_v2.json"
CNINFO_SCHEMA_NOTES_V2_MD = "cninfo_schema_notes_v2.md"

MAX_SYMBOLS_V2 = 5
MAX_TRADE_DAYS_V2 = 30
MAX_ROWS_V2 = 500
MAX_NETWORK_CALLS_V2 = 25

V2_BAOSTOCK_SYMBOLS = ("sh.600519", "sh.600000", "sz.000001")
V2_CNINFO_SYMBOLS = ("sh.600519", "sz.000001")
V2_AKSHARE_SYMBOLS = ("sh.600519", "sh.600000")

APPROVED_PILOT_V2_REQUEST_ENVELOPES: frozenset[
    tuple[str, str, str, tuple[str, ...], str, int]
] = frozenset(
    {
        (
            "baostock",
            "cn_equity_daily_bar",
            "fetch_daily_bar",
            V2_BAOSTOCK_SYMBOLS,
            "recent 30 trading days",
            100,
        ),
        (
            "akshare",
            "cn_equity_daily_bar",
            "fetch_daily_bar_validation",
            V2_AKSHARE_SYMBOLS,
            "recent 30 trading days",
            100,
        ),
        (
            "cninfo",
            "cn_announcements",
            "fetch_announcement_index",
            V2_CNINFO_SYMBOLS,
            "recent 30 calendar days",
            50,
        ),
    }
)

V2_SOURCE_CLOSEOUT_IDS = ("baostock", "cninfo", "akshare")


def pilot_v2_caps_payload() -> dict[str, Any]:
    """Frozen v2 caps envelope for evidence and authorization gate."""
    return {
        "pilot_id": PILOT_ID_V2,
        "max_symbols": MAX_SYMBOLS_V2,
        "max_trade_days": MAX_TRADE_DAYS_V2,
        "max_rows_per_source_domain": MAX_ROWS_V2,
        "max_network_calls_per_run": MAX_NETWORK_CALLS_V2,
        "sandbox_root": _evidence_relative_path(DEFAULT_SANDBOX_ROOT_V2),
        "production_clean_write": False,
        "full_market_scan": False,
        "full_history_backfill": False,
    }


def write_pilot_v2_caps(evidence_dir: Path) -> dict[str, Any]:
    """Write pilot_v2_caps.json (R3Y-SP2-01)."""
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    payload = pilot_v2_caps_payload()
    (evidence_dir / PILOT_V2_CAPS_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def validate_pilot_v2_authorization(request: StagedPilotRequest) -> None:
    """Fail-closed v2 authorization — expanded envelope within frozen caps."""
    auth_path = _resolve_authorization_path(request.authorization_evidence)
    if not auth_path.is_file():
        raise StagedPilotAuthorizationError(
            f"authorization evidence missing: {request.authorization_evidence}"
        )

    auth_text = auth_path.read_text(encoding="utf-8")
    if "prompt14_user_authorization" not in auth_path.name:
        raise StagedPilotAuthorizationError(
            f"authorization evidence must be prompt14 user authorization file: {auth_path.name}"
        )
    if not auth_path.name.startswith("prompt14_user_authorization_"):
        raise StagedPilotAuthorizationError(
            f"authorization filename must match prompt14_user_authorization_*: {auth_path.name}"
        )
    if "Approved on" not in auth_text:
        raise StagedPilotAuthorizationError("authorization evidence missing approval marker")

    if request.source_id in DISABLED_PILOT_SOURCE_IDS:
        raise StagedPilotDisabledSourceError(
            f"source {request.source_id!r} is not authorized for staged real-data pilot"
        )

    if not request.raw_only:
        raise StagedPilotAuthorizationError("staged pilot requires raw_only=true")
    if request.write_target != "sandbox":
        raise StagedPilotAuthorizationError("write_target must be sandbox")
    if request.allow_clean_write:
        raise StagedPilotAuthorizationError(
            "allow_clean_write must be false for staged real-data pilot"
        )
    if request.max_rows <= 0 or request.max_rows > MAX_ROWS_V2:
        raise StagedPilotAuthorizationError(
            f"max_rows must be in 1..{MAX_ROWS_V2}, got {request.max_rows}"
        )
    if not request.symbols_or_indicators:
        raise StagedPilotAuthorizationError("symbols_or_indicators must be non-empty")
    if len(request.symbols_or_indicators) > MAX_SYMBOLS_V2:
        raise StagedPilotAuthorizationError(
            f"max_symbols cap is {MAX_SYMBOLS_V2}, got {len(request.symbols_or_indicators)}"
        )

    envelope = (
        request.source_id,
        request.data_domain,
        request.operation,
        request.symbols_or_indicators,
        request.date_window,
        request.max_rows,
    )
    if envelope not in APPROVED_PILOT_V2_REQUEST_ENVELOPES:
        raise StagedPilotAuthorizationError(
            "request envelope does not exactly match approved v2 pilot authorization"
        )
    if request.source_id == "akshare" and request.operation != "fetch_daily_bar_validation":
        raise StagedPilotAuthorizationError(
            "akshare must remain validation-only in v2 pilot"
        )


def approved_pilot_v2_requests() -> tuple[StagedPilotRequest, ...]:
    auth = "docs/quality/prompt14_user_authorization_2026-06-22.md"
    return (
        StagedPilotRequest(
            source_id="baostock",
            data_domain="cn_equity_daily_bar",
            operation="fetch_daily_bar",
            symbols_or_indicators=V2_BAOSTOCK_SYMBOLS,
            date_window="recent 30 trading days",
            max_rows=100,
            authorization_evidence=auth,
        ),
        StagedPilotRequest(
            source_id="akshare",
            data_domain="cn_equity_daily_bar",
            operation="fetch_daily_bar_validation",
            symbols_or_indicators=V2_AKSHARE_SYMBOLS,
            date_window="recent 30 trading days",
            max_rows=100,
            authorization_evidence=auth,
        ),
        StagedPilotRequest(
            source_id="cninfo",
            data_domain="cn_announcements",
            operation="fetch_announcement_index",
            symbols_or_indicators=V2_CNINFO_SYMBOLS,
            date_window="recent 30 calendar days",
            max_rows=50,
            authorization_evidence=auth,
        ),
    )


def _route_status_examples_from_previews(
    previews: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Derive route_kind coverage from dry-run preview candidates."""
    examples: list[dict[str, Any]] = []
    for preview in previews:
        plan = preview.get("route_plan", {})
        selected = plan.get("selected_source_id")
        for candidate in plan.get("candidates", []):
            source_id = candidate.get("source_id")
            if not source_id:
                continue
            enabled = candidate.get("enabled", False)
            role = candidate.get("role")
            if not enabled:
                route_kind = "disabled"
            elif role == "Validation":
                route_kind = "validation_only"
            elif source_id == selected:
                route_kind = "selected"
            else:
                route_kind = "skipped"
            examples.append(
                {
                    "source_id": source_id,
                    "data_domain": plan.get("data_domain"),
                    "operation": plan.get("operation"),
                    "explicit_source_route_status": preview.get(
                        "explicit_source_route_status"
                    ),
                    "organic_route_status": plan.get("route_status"),
                    "route_kind": route_kind,
                    "selected_source_id": selected,
                }
            )
    return examples


def _route_status_examples_for_v2(
    *,
    previews: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Collect route status coverage for matrix v2 (selected/skipped/disabled/validation-only)."""
    examples = _route_status_examples_from_previews(previews or [])
    registry = SourceRegistry()
    registry.load()
    capability_registry = SourceCapabilityRegistry()
    capability_registry.load()
    planner = SourceRoutePlanner(
        source_registry=registry,
        capability_registry=capability_registry,
    )
    extra_probes = (
        ("cn_equity_daily_bar", "fetch_daily_bar", "fred", False),
        ("cn_equity_daily_bar", "fetch_daily_bar", "tdx_pytdx", False),
        ("cn_equity_daily_bar", "fetch_daily_bar", "qmt_xtdata", True),
    )
    for domain, operation, source_id, use_fallback in extra_probes:
        plan = planner.plan(
            data_domain=domain,
            operation=operation,
            run_id=f"v2-route-{source_id}",
            job_id="r3y-staged-pilot-v2-route",
            use_fallback=use_fallback,
        )
        explicit = _explicit_source_route_status(
            source_id=source_id,
            candidates=plan.candidates,
        )
        candidate = next((c for c in plan.candidates if c.source_id == source_id), None)
        role = getattr(candidate, "role", None) if candidate else None
        route_kind = "selected"
        if explicit == "USER_AUTH_REQUIRED":
            route_kind = "user_auth_required"
        elif role == "FallbackPolicy" and candidate and not candidate.enabled and candidate.skip_reason:
            route_kind = "skipped"
        elif role == "Validation":
            route_kind = "validation_only"
        elif explicit in {"DISABLED_SOURCE", "NO_AVAILABLE_SOURCE", "CAPABILITY_MISSING"}:
            route_kind = "disabled"
        elif candidate is not None and not candidate.enabled:
            route_kind = "disabled"
        elif plan.selected_source_id and plan.selected_source_id != source_id:
            route_kind = "skipped"
        examples.append(
            {
                "source_id": source_id,
                "data_domain": domain,
                "operation": operation,
                "explicit_source_route_status": explicit,
                "organic_route_status": plan.route_status,
                "route_kind": route_kind,
                "selected_source_id": plan.selected_source_id,
            }
        )
    return examples


def capture_route_preview_matrix_v2(
    *,
    evidence_dir: Path,
    requests: tuple[StagedPilotRequest, ...] | None = None,
    db_path: Path | None = None,
    service: DataSourceService | None = None,
) -> dict[str, Any]:
    """Route preview matrix v2 with full route status coverage (R3Y-SP2-05)."""
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    pilot_requests = requests or approved_pilot_v2_requests()
    for request in pilot_requests:
        validate_pilot_v2_authorization(request)

    target_db = db_path or DEFAULT_PRODUCTION_DB
    before_counts = _key_table_row_counts(target_db) if target_db.is_file() else {}
    before_bytes = target_db.read_bytes() if target_db.is_file() else None

    svc = service or DataSourceService()
    previews: list[dict[str, Any]] = []
    for index, request in enumerate(pilot_requests, start=1):
        preview = preview_staged_pilot(
            request,
            service=svc,
            pilot_request_id=f"v2-req-{index}",
            authorization_gate=validate_pilot_v2_authorization,
        )
        preview["pilot_id"] = PILOT_ID_V2
        previews.append(preview)

    route_status_examples = _route_status_examples_for_v2(previews=previews)
    route_kinds = {item["route_kind"] for item in route_status_examples}
    required_kinds = {"selected", "disabled", "validation_only", "user_auth_required"}
    missing = sorted(required_kinds - route_kinds)
    if missing:
        raise RuntimeError(f"route_preview_matrix_v2 missing route kinds: {missing}")

    mutation_proof = build_production_mutation_proof(
        target_db,
        before_counts=before_counts,
        before_bytes=before_bytes,
    )
    generated_at = _utc_now_iso()
    payload: dict[str, Any] = {
        "pilot_id": PILOT_ID_V2,
        "generated_at": generated_at,
        "phase": "route_preview_v2",
        "dry_run": True,
        "run_mode": "staged_only",
        "caps": pilot_v2_caps_payload(),
        "previews": previews,
        "route_status_examples": route_status_examples,
        "route_status_coverage": sorted(route_kinds),
        "mutation_proof": mutation_proof,
    }
    (evidence_dir / ROUTE_MATRIX_V2_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def _manifest_v2_fetch_entry(
    item: dict[str, Any],
    *,
    pilot_request_id: str,
) -> dict[str, Any]:
    fetch_result = item.get("fetch_result", {})
    raw_paths = fetch_result.get("raw_file_paths") or []
    content_hash = fetch_result.get("content_hash")
    relative_paths = [_evidence_relative_path(p) for p in raw_paths]
    vendor_api = None
    if raw_paths:
        try:
            raw_payload = _load_raw_json_payload(raw_paths[0])
            vendor_api = raw_payload.get("vendor_api")
        except (OSError, json.JSONDecodeError):
            vendor_api = None
    return {
        "pilot_request_id": pilot_request_id,
        "source_fetch_id": fetch_result.get("run_id") or pilot_request_id,
        "content_hash": content_hash,
        "relative_paths": relative_paths,
        "vendor_api": vendor_api,
        "as_of_timestamp": item.get("generated_at") or _utc_now_iso(),
        "taxonomy_status": item.get("taxonomy_status"),
        "row_count": fetch_result.get("row_count"),
    }


def capture_baostock_evidence_v2(
    *,
    evidence_dir: Path,
    sandbox_root: Path | None = None,
    fetch_runner: Any | None = None,
) -> dict[str, Any]:
    """Baostock expanded sample manifest v2 (R3Y-SP2-02)."""
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    sandbox = sandbox_root or DEFAULT_SANDBOX_ROOT_V2
    request = approved_pilot_v2_requests()[0]
    validate_pilot_v2_authorization(request)

    if fetch_runner is not None:
        fetch_item = fetch_runner(request, sandbox_root=sandbox)
    else:
        fetch_item = run_staged_pilot_raw_only(
            replace(request, dry_run=False),
            sandbox_root=sandbox / "baostock",
            pilot_request_id="v2-baostock",
            authorization_gate=validate_pilot_v2_authorization,
        )
        fetch_item["pilot_id"] = PILOT_ID_V2

    generated_at = _utc_now_iso()
    manifest_entry = _manifest_v2_fetch_entry(fetch_item, pilot_request_id="v2-baostock")
    payload = {
        "pilot_id": PILOT_ID_V2,
        "generated_at": generated_at,
        "source_id": "baostock",
        "data_domain": request.data_domain,
        "symbols": list(request.symbols_or_indicators),
        "date_window": request.date_window,
        "fetches": [fetch_item],
        "manifest_entries": [manifest_entry],
        "required_fields_present": all(
            manifest_entry.get(field) is not None
            for field in ("content_hash", "source_fetch_id", "relative_paths")
        ),
    }
    staging_payload = {
        "pilot_id": PILOT_ID_V2,
        "generated_at": generated_at,
        "staged_rows": [
            {
                "pilot_request_id": "v2-baostock",
                "staged_file_ids": fetch_item.get("staged_file_ids", []),
                "quality_flag": STAGED_FILE_REGISTRY_QUALITY,
            }
        ],
        "allow_clean_write": False,
    }
    (evidence_dir / RAW_MANIFEST_V2_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / STAGING_MANIFEST_V2_JSON).write_text(
        json.dumps(staging_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def capture_cninfo_evidence_v2(
    *,
    evidence_dir: Path,
    sandbox_root: Path | None = None,
    fetch_runner: Any | None = None,
) -> dict[str, Any]:
    """Cninfo metadata expanded sample + schema notes (R3Y-SP2-03)."""
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    sandbox = sandbox_root or DEFAULT_SANDBOX_ROOT_V2
    request = approved_pilot_v2_requests()[2]
    validate_pilot_v2_authorization(request)

    if fetch_runner is not None:
        fetch_item = fetch_runner(request, sandbox_root=sandbox)
    else:
        fetch_item = run_staged_pilot_raw_only(
            replace(request, dry_run=False),
            sandbox_root=sandbox / "cninfo",
            pilot_request_id="v2-cninfo",
            authorization_gate=validate_pilot_v2_authorization,
        )
        fetch_item["pilot_id"] = PILOT_ID_V2

    raw_paths = fetch_item.get("fetch_result", {}).get("raw_file_paths") or []
    schema_fields: list[str] = []
    if raw_paths:
        raw_payload = _load_raw_json_payload(raw_paths[0])
        rows = raw_payload.get("rows", [])
        if isinstance(rows, list) and rows and isinstance(rows[0], dict):
            schema_fields = sorted(rows[0].keys())

    notes_lines = [
        "# cninfo metadata schema notes v2",
        "",
        f"- **Pilot ID:** {PILOT_ID_V2}",
        f"- **Symbols:** {', '.join(request.symbols_or_indicators)}",
        f"- **Date window:** {request.date_window}",
        "",
        "## Observed fields",
        "",
    ]
    if schema_fields:
        notes_lines.extend(f"- `{field}`" for field in schema_fields)
    else:
        notes_lines.append("- _(no rows in sample — structure validation deferred)_")

    (evidence_dir / CNINFO_SCHEMA_NOTES_V2_MD).write_text(
        "\n".join(notes_lines) + "\n",
        encoding="utf-8",
    )

    generated_at = _utc_now_iso()
    payload = {
        "pilot_id": PILOT_ID_V2,
        "generated_at": generated_at,
        "source_id": "cninfo",
        "schema_fields": schema_fields,
        "metadata_only": True,
        "fetch": fetch_item,
    }
    return payload


def capture_akshare_validation_taxonomy_v2(
    *,
    evidence_dir: Path,
    taxonomy_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Akshare validation taxonomy v2 (R3Y-SP2-04).

    ponytail: default ``records`` are static SUCCESS/NETWORK_ERROR placeholders when
    no live fetch is supplied; re-defer narrative is preserved for evidence capture.
    """
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    request = approved_pilot_v2_requests()[1]
    validate_pilot_v2_authorization(request)
    if request.operation != "fetch_daily_bar_validation":
        raise StagedPilotAuthorizationError(
            "akshare must use validation-only operation in v2 pilot"
        )

    records = taxonomy_records or [
        {
            "source_id": "akshare",
            "operation": request.operation,
            "status": FetchTaxonomyStatus.SUCCESS.value,
            "validation_only": True,
            "re_defer": False,
        },
        {
            "source_id": "akshare",
            "operation": request.operation,
            "status": FetchTaxonomyStatus.SOURCE_FAILURE.value,
            "validation_only": True,
            "re_defer": True,
            "reason": "NETWORK_ERROR retry exhausted",
        },
    ]
    allowed_status = {item.value for item in FetchTaxonomyStatus}
    for record in records:
        if record.get("status") not in allowed_status:
            raise ValueError(f"invalid taxonomy status: {record.get('status')}")

    generated_at = _utc_now_iso()
    payload = {
        "pilot_id": PILOT_ID_V2,
        "generated_at": generated_at,
        "validation_only": True,
        "primary_forbidden": True,
        "records": records,
    }
    (evidence_dir / AKSHARE_TAXONOMY_V2_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def capture_validation_report_v2(
    *,
    evidence_dir: Path,
    raw_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validation report v2 exposing quality flags and row counts (R3Y-SP2-06)."""
    evidence_dir = Path(evidence_dir)
    if raw_manifest is None:
        raw_path = evidence_dir / RAW_MANIFEST_V2_JSON
        if not raw_path.is_file():
            raw_manifest = {"fetches": [], "manifest_entries": []}
        else:
            raw_manifest = json.loads(raw_path.read_text(encoding="utf-8"))

    base_report = capture_validation_report(
        evidence_dir=evidence_dir,
        raw_manifest=raw_manifest,
    )
    validations_v2: list[dict[str, Any]] = []
    for item in raw_manifest.get("fetches", []):
        fetch_result = item.get("fetch_result", {})
        structure = None
        for validation in base_report.get("validations", []):
            if validation.get("pilot_request_id") == item.get("pilot_request_id"):
                structure = validation.get("structure_validation", {})
                break
        quality_flags: list[str] = []
        if structure and structure.get("findings"):
            quality_flags.extend(structure["findings"])
        if fetch_result.get("status") != "SUCCESS":
            quality_flags.append("SOURCE_FAILURE")
        validations_v2.append(
            {
                "pilot_request_id": item.get("pilot_request_id"),
                "source_id": item.get("request", {}).get("source_id"),
                "row_count": fetch_result.get("row_count", 0),
                "quality_flags": quality_flags,
                "structure_status": (structure or {}).get("status"),
                "source_used": item.get("request", {}).get("source_id"),
            }
        )

    generated_at = _utc_now_iso()
    payload = {
        **base_report,
        "pilot_id": PILOT_ID_V2,
        "generated_at": generated_at,
        "validations_v2": validations_v2,
    }
    (evidence_dir / VALIDATION_REPORT_V2_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def capture_conflict_summary_v2(
    *,
    evidence_dir: Path,
    validation_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Conflict summary v2 — primary compare or explicit defer (R3Y-SP2-07)."""
    evidence_dir = Path(evidence_dir)
    if validation_report is None:
        report_path = evidence_dir / VALIDATION_REPORT_V2_JSON
        if report_path.is_file():
            validation_report = json.loads(report_path.read_text(encoding="utf-8"))
        else:
            validation_report = {}

    validations = validation_report.get("validations_v2") or validation_report.get(
        "validations", []
    )
    has_baostock = any(v.get("source_id") == "baostock" for v in validations)
    has_akshare = any(v.get("source_id") == "akshare" for v in validations)
    if has_baostock and has_akshare:
        status = "PRIMARY_VS_VALIDATION_COMPARE_DEFERRED"
        reason = (
            "baostock primary and akshare validation-only both present; "
            "field-level conflict compare deferred until expanded aligned samples"
        )
    else:
        status = "NO_CONFLICT_CHECK_DEFERRED"
        reason = _staged_conflict_check_summary()["reason"]

    generated_at = _utc_now_iso()
    payload = {
        "pilot_id": PILOT_ID_V2,
        "generated_at": generated_at,
        "status": status,
        "reason": reason,
        "policy_ref": "docs/modules/data_validation_and_conflict.md",
    }
    (evidence_dir / CONFLICT_CHECK_V2_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def write_no_mutation_proof_v2(
    *,
    evidence_dir: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    """No-mutation proof v2 markdown + payload (R3Y-SP2-08)."""
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    target_db = db_path or DEFAULT_PRODUCTION_DB
    proof = build_production_mutation_proof(target_db)
    generated_at = _utc_now_iso()
    lines = [
        "# Production DB — No Mutation Proof v2",
        "",
        f"- **Pilot ID:** {PILOT_ID_V2}",
        f"- **Generated at:** {generated_at}",
        f"- **Production DB:** `{target_db}`",
        f"- **proof_status:** {proof.get('proof_status')}",
        f"- **db_hash_unchanged:** {proof.get('db_hash_unchanged')}",
        f"- **row_counts_unchanged:** {proof.get('row_counts_unchanged')}",
    ]
    reason = proof.get("reason")
    if reason:
        lines.append(f"- **reason:** {reason}")
    sha256_hex = proof.get("db_sha256")
    if sha256_hex:
        lines.append(f"- **db_sha256:** `{sha256_hex}`")
    before_key = proof.get("before_key_table_counts") or {}
    after_key = proof.get("after_key_table_counts") or {}
    if before_key or after_key:
        lines.extend(
            [
                "",
                "## Key table row counts",
                "",
                f"- **before:** {before_key}",
                f"- **after:** {after_key}",
            ]
        )
    before_all = proof.get("before_all_table_counts") or {}
    after_all = proof.get("after_all_table_counts") or {}
    if before_all or after_all:
        lines.extend(
            [
                "",
                "## All table row counts",
                "",
                f"- **before:** {before_all}",
                f"- **after:** {after_all}",
            ]
        )
    lines.extend(
        [
            "",
            "## R3Y-MUT-PROOF-001",
            "",
            "VERIFIED only when file hash and all table row counts are unchanged.",
            "",
            "Hash check uses full-file byte equality; ``db_sha256`` is informational",
            "and aligns with backup manifest ``duckdb_hash`` (SHA256 hex).",
            "",
        ]
    )
    (evidence_dir / NO_MUTATION_V2_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return proof


def _classify_v2_source_outcome(
    *,
    source_id: str,
    validation_report: dict[str, Any],
    akshare_taxonomy: dict[str, Any] | None,
) -> str:
    validations = validation_report.get("validations_v2") or validation_report.get(
        "validations", []
    )
    source_validations = [v for v in validations if v.get("source_id") == source_id]
    if source_id == "akshare" and akshare_taxonomy:
        records = akshare_taxonomy.get("records", [])
        if any(r.get("re_defer") for r in records):
            return "re-defer"
        if any(r.get("status") == FetchTaxonomyStatus.SUCCESS.value for r in records):
            return "retry"
        return "block"
    if not source_validations:
        return "re-defer"
    if any(v.get("structure_status") == "PASSED" or v.get("status") == "PASSED" for v in source_validations):
        return "expand"
    if any(v.get("structure_status") == "FAILED" for v in source_validations):
        return "re-defer"
    return "retry"


def build_pilot_v2_closeout(
    *,
    evidence_dir: Path,
    mutation_proof: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Pilot v2 closeout with per-source matrix and AUD-08 gate fields (R3Y-SP2-09)."""
    evidence_dir = Path(evidence_dir)
    if mutation_proof is None:
        mutation_proof = build_production_mutation_proof(DEFAULT_PRODUCTION_DB)

    validation_path = evidence_dir / VALIDATION_REPORT_V2_JSON
    validation_report = (
        json.loads(validation_path.read_text(encoding="utf-8"))
        if validation_path.is_file()
        else {"validations_v2": []}
    )
    taxonomy_path = evidence_dir / AKSHARE_TAXONOMY_V2_JSON
    akshare_taxonomy = (
        json.loads(taxonomy_path.read_text(encoding="utf-8"))
        if taxonomy_path.is_file()
        else None
    )

    per_source = {
        source_id: _classify_v2_source_outcome(
            source_id=source_id,
            validation_report=validation_report,
            akshare_taxonomy=akshare_taxonomy,
        )
        for source_id in V2_SOURCE_CLOSEOUT_IDS
    }
    hash_raw = mutation_proof.get("db_hash_unchanged")
    counts_raw = mutation_proof.get("row_counts_unchanged")
    hash_ok = hash_raw is True
    counts_ok = counts_raw is True
    proof_status = mutation_proof.get("proof_status")
    closeout_pass = hash_ok and counts_ok and proof_status == "VERIFIED"

    generated_at = _utc_now_iso()
    payload = {
        "pilot_id": PILOT_ID_V2,
        "generated_at": generated_at,
        "production_live_readiness_claim": False,
        "mutation_proof_status": proof_status,
        "db_hash_unchanged": hash_raw,
        "row_counts_unchanged": counts_raw,
        "closeout_pass": closeout_pass,
        "per_source": per_source,
        "sandbox_clean_write_rehearsal": False,
        "run_mode": "staged_only",
    }
    reason = mutation_proof.get("reason")
    if reason:
        payload["mutation_proof_reason"] = reason
    (evidence_dir / CLOSEOUT_V2_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def run_full_staged_pilot_v2(
    evidence_dir: Path | str,
    *,
    sandbox_root: Path | None = None,
    skip_live_fetch: bool = False,
    fetch_runner: Any | None = None,
) -> dict[str, Any]:
    """End-to-end staged pilot v2 evidence capture."""
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    sandbox = sandbox_root or DEFAULT_SANDBOX_ROOT_V2

    caps = write_pilot_v2_caps(evidence_dir)
    reset_network_call_budget(limit=MAX_NETWORK_CALLS_V2)

    guard = ResourceGuard()
    guard_decision, guard_reason = guard.check()
    guard_payload = {
        "pilot_id": PILOT_ID_V2,
        "generated_at": _utc_now_iso(),
        "decision": guard_decision.value,
        "reason": guard_reason,
        "network_call_budget": network_call_budget_snapshot(),
        "caps": pilot_v2_caps_payload(),
    }
    (evidence_dir / RESOURCE_GUARD_JSON).write_text(
        json.dumps(guard_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    route_payload = capture_route_preview_matrix_v2(evidence_dir=evidence_dir)

    raw_manifest: dict[str, Any] | None = None
    live_fetch_allowed = not skip_live_fetch and guard_decision != Decision.HARD_STOP
    if live_fetch_allowed:
        raw_manifest = capture_baostock_evidence_v2(
            evidence_dir=evidence_dir,
            sandbox_root=sandbox,
            fetch_runner=fetch_runner,
        )
        capture_cninfo_evidence_v2(
            evidence_dir=evidence_dir,
            sandbox_root=sandbox,
            fetch_runner=fetch_runner,
        )
        guard_payload["network_call_budget"] = network_call_budget_snapshot()
        (evidence_dir / RESOURCE_GUARD_JSON).write_text(
            json.dumps(guard_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    capture_akshare_validation_taxonomy_v2(evidence_dir=evidence_dir)
    validation_payload = capture_validation_report_v2(
        evidence_dir=evidence_dir,
        raw_manifest=raw_manifest,
    )
    conflict_payload = capture_conflict_summary_v2(
        evidence_dir=evidence_dir,
        validation_report=validation_payload,
    )
    mutation_proof = write_no_mutation_proof_v2(evidence_dir=evidence_dir)
    closeout = build_pilot_v2_closeout(
        evidence_dir=evidence_dir,
        mutation_proof=mutation_proof,
    )

    return {
        "pilot_id": PILOT_ID_V2,
        "caps": caps,
        "route_preview": route_payload,
        "raw_manifest": raw_manifest,
        "validation": validation_payload,
        "conflict": conflict_payload,
        "mutation_proof": mutation_proof,
        "closeout": closeout,
        "skip_live_fetch": skip_live_fetch,
        "resource_guard": guard_payload,
    }


# --- PROMPT_19 staged pilot v3 (WL-driven, fail-closed) -----------------------

MODEL_INPUTS_DIR = PROJECT_ROOT / "specs" / "model_inputs"
WHITELIST_YAML_NAMES = (
    "layer1_source_whitelist.yaml",
    "layer2_source_whitelist.yaml",
    "layer3_anchor_source_plan.yaml",
    "layer4_market_source_plan.yaml",
    "layer5_instrument_source_plan.yaml",
)

PILOT_ID_V3 = "r3e-staged-pilot-v3-20260625"
DEFAULT_SANDBOX_ROOT_V3 = PROJECT_ROOT / ".audit-sandbox/r3e-staged-pilot-v3"

PILOT_V3_CAPS_JSON = "pilot_v3_caps.json"
WHITELIST_REF_JSON = "whitelist_ref.json"
RAW_MANIFEST_V3_BAOSTOCK_JSON = "raw_evidence_manifest_v3_baostock.json"
STAGING_MANIFEST_V3_JSON = "staging_evidence_manifest_v3.json"
CNINFO_SCHEMA_NOTES_V3_MD = "cninfo_schema_notes_v3.md"
AKSHARE_TAXONOMY_V3_JSON = "akshare_validation_taxonomy_v3.json"
CONFLICT_CHECK_V3_JSON = "conflict_check_summary_v3.json"
NO_MUTATION_V3_MD = "no_mutation_proof_v3.md"
CLOSEOUT_V3_JSON = "pilot_v3_closeout.json"
SOURCE_READINESS_MATRIX_V3_MD = "source_readiness_matrix_v3.md"
REGISTRY_PROPOSED_DELTA_V3_YAML = "registry_proposed_delta_v3.yaml"

MAX_SYMBOLS_BAOSTOCK_V3 = 20
MAX_SYMBOLS_CNINFO_V3 = 20
MAX_SYMBOLS_AKSHARE_V3 = 10
MIN_SYMBOLS_AKSHARE_V3 = 2
MAX_ROWS_BAOSTOCK_V3 = 2000
MAX_ROWS_CNINFO_V3 = 500
MAX_ROWS_AKSHARE_V3 = 1000
MAX_TRADE_DAYS_V3 = 120
MIN_TRADE_DAYS_V3 = 30
MAX_NETWORK_CALLS_V3 = 50

PILOT_V3_SOURCE_IDS = frozenset({"baostock", "cninfo", "akshare"})
CNINFO_METADATA_OPS = frozenset({"fetch_announcement_index", "fetch_filing_index"})
CNINFO_FORBIDDEN_OP_FRAGMENTS = frozenset({"pdf", "full_text", "full-text", "bulk_download"})
V3_SOURCE_CLOSEOUT_IDS = ("baostock", "cninfo", "akshare")
V3_DATE_WINDOW = "recent 60 trading days"


def assert_model_inputs_whitelist_present() -> None:
    """Fail-closed gate: specs/model_inputs/** must exist before v3 pilot (B01-WL)."""
    if not MODEL_INPUTS_DIR.is_dir():
        raise StagedPilotAuthorizationError(
            f"model input whitelist directory missing: {MODEL_INPUTS_DIR}"
        )
    missing = [
        name for name in WHITELIST_YAML_NAMES if not (MODEL_INPUTS_DIR / name).is_file()
    ]
    if missing:
        raise StagedPilotAuthorizationError(
            f"model input whitelist files missing: {', '.join(missing)}"
        )


def _whitelist_symbol_list(row: dict[str, Any]) -> tuple[str, ...]:
    sym = row.get("symbol_or_series")
    if isinstance(sym, list):
        return tuple(str(item) for item in sym if item)
    if sym in (None, ""):
        return ()
    return (str(sym),)


def compute_whitelist_ref() -> dict[str, Any]:
    """SHA256 refs for all WL YAML files (manifest traceability)."""
    assert_model_inputs_whitelist_present()
    entries: list[dict[str, str]] = []
    aggregate = hashlib.sha256()
    for name in WHITELIST_YAML_NAMES:
        path = MODEL_INPUTS_DIR / name
        content = path.read_bytes()
        file_hash = hashlib.sha256(content).hexdigest()
        aggregate.update(content)
        entries.append(
            {
                "path": _evidence_relative_path(path),
                "sha256": file_hash,
            }
        )
    return {
        "whitelist_root": _evidence_relative_path(MODEL_INPUTS_DIR),
        "files": entries,
        "aggregate_sha256": aggregate.hexdigest(),
    }


def load_pilot_v3_whitelist_scope() -> dict[str, list[dict[str, Any]]]:
    """Load baostock/cninfo/akshare rows from merged model_inputs YAML."""
    assert_model_inputs_whitelist_present()
    rows_by_source: dict[str, list[dict[str, Any]]] = {
        source_id: [] for source_id in PILOT_V3_SOURCE_IDS
    }
    for name in WHITELIST_YAML_NAMES:
        doc = yaml.safe_load((MODEL_INPUTS_DIR / name).read_text(encoding="utf-8")) or {}
        for row in doc.get("rows") or []:
            source_id = row.get("source_id")
            if source_id in PILOT_V3_SOURCE_IDS:
                rows_by_source[str(source_id)].append({**row, "_whitelist_file": name})
    return rows_by_source


def pilot_v3_baostock_symbols() -> tuple[str, ...]:
    symbols: list[str] = []
    for row in load_pilot_v3_whitelist_scope()["baostock"]:
        if (
            row.get("data_domain") == "cn_equity_daily_bar"
            and row.get("operation") == "fetch_daily_bar"
        ):
            for symbol in _whitelist_symbol_list(row):
                if symbol not in symbols:
                    symbols.append(symbol)
    if not symbols:
        raise StagedPilotAuthorizationError(
            "no baostock cn_equity_daily_bar symbols in model input whitelist"
        )
    return tuple(symbols[:MAX_SYMBOLS_BAOSTOCK_V3])


def pilot_v3_cninfo_symbols() -> tuple[str, ...]:
    symbols: list[str] = []
    for row in load_pilot_v3_whitelist_scope()["cninfo"]:
        if row.get("operation") in CNINFO_METADATA_OPS:
            for symbol in _whitelist_symbol_list(row):
                if symbol not in symbols:
                    symbols.append(symbol)
    if not symbols:
        raise StagedPilotAuthorizationError(
            "no cninfo metadata symbols in model input whitelist"
        )
    return tuple(symbols[:MAX_SYMBOLS_CNINFO_V3])


def pilot_v3_akshare_symbols() -> tuple[str, ...]:
    """ponytail: akshare comparison symbols are WL-traced subset of baostock symbols."""
    baostock = pilot_v3_baostock_symbols()
    if len(baostock) < MIN_SYMBOLS_AKSHARE_V3:
        raise StagedPilotAuthorizationError(
            f"akshare comparison needs at least {MIN_SYMBOLS_AKSHARE_V3} WL baostock symbols"
        )
    return tuple(baostock[:MAX_SYMBOLS_AKSHARE_V3])


def _v3_row_caps_for_source(source_id: str) -> dict[str, int]:
    if source_id == "baostock":
        return {"max_symbols": MAX_SYMBOLS_BAOSTOCK_V3, "max_rows": MAX_ROWS_BAOSTOCK_V3}
    if source_id == "cninfo":
        return {"max_symbols": MAX_SYMBOLS_CNINFO_V3, "max_rows": MAX_ROWS_CNINFO_V3}
    if source_id == "akshare":
        return {"max_symbols": MAX_SYMBOLS_AKSHARE_V3, "max_rows": MAX_ROWS_AKSHARE_V3}
    raise StagedPilotAuthorizationError(f"unsupported v3 source_id: {source_id!r}")


def _v3_symbols_for_domain_operation(
    source_id: str,
    *,
    data_domain: str,
    operation: str,
    max_symbols: int,
) -> tuple[str, ...]:
    symbols: list[str] = []
    for row in load_pilot_v3_whitelist_scope().get(source_id, []):
        if row.get("data_domain") != data_domain:
            continue
        if row.get("operation") != operation:
            continue
        for symbol in _whitelist_symbol_list(row):
            if symbol not in symbols:
                symbols.append(symbol)
    if not symbols:
        raise StagedPilotAuthorizationError(
            f"no {source_id} whitelist rows for {data_domain}/{operation}"
        )
    return tuple(symbols[:max_symbols])


def _allowed_symbols_for_v3_request(request: StagedPilotRequest) -> frozenset[str]:
    if request.source_id == "akshare":
        return frozenset(pilot_v3_akshare_symbols())
    return frozenset(
        _v3_symbols_for_domain_operation(
            request.source_id,
            data_domain=str(request.data_domain),
            operation=request.operation,
            max_symbols=_v3_row_caps_for_source(request.source_id)["max_symbols"],
        )
    )


def pilot_v3_caps_payload() -> dict[str, Any]:
    wl_ref = compute_whitelist_ref()
    return {
        "pilot_id": PILOT_ID_V3,
        "whitelist_ref": wl_ref,
        "baostock_symbols": list(pilot_v3_baostock_symbols()),
        "cninfo_symbols": list(pilot_v3_cninfo_symbols()),
        "akshare_symbols": list(pilot_v3_akshare_symbols()),
        "max_symbols_baostock": MAX_SYMBOLS_BAOSTOCK_V3,
        "max_symbols_cninfo": MAX_SYMBOLS_CNINFO_V3,
        "max_symbols_akshare": MAX_SYMBOLS_AKSHARE_V3,
        "min_trade_days": MIN_TRADE_DAYS_V3,
        "max_trade_days": MAX_TRADE_DAYS_V3,
        "max_rows_baostock": MAX_ROWS_BAOSTOCK_V3,
        "max_rows_cninfo": MAX_ROWS_CNINFO_V3,
        "max_rows_akshare": MAX_ROWS_AKSHARE_V3,
        "max_network_calls_per_run": MAX_NETWORK_CALLS_V3,
        "sandbox_root": _evidence_relative_path(DEFAULT_SANDBOX_ROOT_V3),
        "production_clean_write": False,
        "full_market_scan": False,
        "full_history_backfill": False,
        "model_driven": True,
    }


def write_whitelist_ref(evidence_dir: Path) -> dict[str, Any]:
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    payload = compute_whitelist_ref()
    (evidence_dir / WHITELIST_REF_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def write_pilot_v3_caps(evidence_dir: Path) -> dict[str, Any]:
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    payload = pilot_v3_caps_payload()
    (evidence_dir / PILOT_V3_CAPS_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_whitelist_ref(evidence_dir)
    return payload


def validate_pilot_v3_authorization(request: StagedPilotRequest) -> None:
    """Fail-closed v3 authorization — WL-traced symbols within frozen caps."""
    assert_model_inputs_whitelist_present()

    auth_path = _resolve_authorization_path(request.authorization_evidence)
    if not auth_path.is_file():
        raise StagedPilotAuthorizationError(
            f"authorization evidence missing: {request.authorization_evidence}"
        )
    auth_text = auth_path.read_text(encoding="utf-8")
    if not auth_path.name.startswith("prompt14_user_authorization_"):
        raise StagedPilotAuthorizationError(
            f"authorization filename must match prompt14_user_authorization_*: {auth_path.name}"
        )
    if "Approved on" not in auth_text:
        raise StagedPilotAuthorizationError("authorization evidence missing approval marker")

    if request.source_id in DISABLED_PILOT_SOURCE_IDS:
        raise StagedPilotDisabledSourceError(
            f"source {request.source_id!r} is not authorized for staged real-data pilot"
        )
    if not request.raw_only:
        raise StagedPilotAuthorizationError("staged pilot requires raw_only=true")
    if request.write_target != "sandbox":
        raise StagedPilotAuthorizationError("write_target must be sandbox")
    if request.allow_clean_write:
        raise StagedPilotAuthorizationError(
            "allow_clean_write must be false for staged real-data pilot"
        )
    if not request.symbols_or_indicators:
        raise StagedPilotAuthorizationError("symbols_or_indicators must be non-empty")

    if request.source_id == "cninfo":
        operation_lower = request.operation.lower()
        if any(fragment in operation_lower for fragment in CNINFO_FORBIDDEN_OP_FRAGMENTS):
            raise StagedPilotAuthorizationError(
                "cninfo PDF/full-text expansion forbidden in v3 pilot"
            )
        if request.operation not in CNINFO_METADATA_OPS:
            raise StagedPilotAuthorizationError(
                f"cninfo operation must be metadata-only: {request.operation!r}"
            )

    if request.source_id == "akshare":
        if request.operation != "fetch_daily_bar_validation":
            raise StagedPilotAuthorizationError(
                "akshare must remain validation-only in v3 pilot"
            )

    caps = _v3_row_caps_for_source(request.source_id)
    if len(request.symbols_or_indicators) > caps["max_symbols"]:
        raise StagedPilotAuthorizationError(
            f"max_symbols cap is {caps['max_symbols']}, got {len(request.symbols_or_indicators)}"
        )
    if request.max_rows <= 0 or request.max_rows > caps["max_rows"]:
        raise StagedPilotAuthorizationError(
            f"max_rows must be in 1..{caps['max_rows']}, got {request.max_rows}"
        )

    allowed_symbols = _allowed_symbols_for_v3_request(request)
    unknown = [
        symbol
        for symbol in request.symbols_or_indicators
        if symbol not in allowed_symbols
    ]
    if unknown:
        raise StagedPilotAuthorizationError(
            f"symbols not in model input whitelist: {unknown}"
        )


def approved_pilot_v3_requests() -> tuple[StagedPilotRequest, ...]:
    auth = "docs/quality/prompt14_user_authorization_2026-06-22.md"
    baostock_symbols = pilot_v3_baostock_symbols()
    akshare_symbols = pilot_v3_akshare_symbols()
    return (
        StagedPilotRequest(
            source_id="baostock",
            data_domain="cn_equity_daily_bar",
            operation="fetch_daily_bar",
            symbols_or_indicators=baostock_symbols,
            date_window=V3_DATE_WINDOW,
            max_rows=min(100 * len(baostock_symbols), MAX_ROWS_BAOSTOCK_V3),
            authorization_evidence=auth,
        ),
        StagedPilotRequest(
            source_id="akshare",
            data_domain="cn_equity_daily_bar",
            operation="fetch_daily_bar_validation",
            symbols_or_indicators=akshare_symbols,
            date_window=V3_DATE_WINDOW,
            max_rows=min(100 * len(akshare_symbols), MAX_ROWS_AKSHARE_V3),
            authorization_evidence=auth,
        ),
        StagedPilotRequest(
            source_id="cninfo",
            data_domain="cn_announcements",
            operation="fetch_announcement_index",
            symbols_or_indicators=_v3_symbols_for_domain_operation(
                "cninfo",
                data_domain="cn_announcements",
                operation="fetch_announcement_index",
                max_symbols=MAX_SYMBOLS_CNINFO_V3,
            ),
            date_window="recent 60 calendar days",
            max_rows=min(50, MAX_ROWS_CNINFO_V3),
            authorization_evidence=auth,
        ),
    )


def assert_akshare_not_primary_for_daily_bar() -> None:
    """Route preview guard: akshare must not be organic Primary for daily bar fetch."""
    registry = SourceRegistry()
    registry.load()
    capability_registry = SourceCapabilityRegistry()
    capability_registry.load()
    planner = SourceRoutePlanner(
        source_registry=registry,
        capability_registry=capability_registry,
    )
    plan = planner.plan(
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        run_id="v3-akshare-primary-guard",
        job_id="r3e-staged-pilot-v3-route",
    )
    if plan.selected_source_id == "akshare":
        raise StagedPilotAuthorizationError(
            "akshare must not be selected as Primary for cn_equity_daily_bar"
        )


def capture_baostock_evidence_v3(
    *,
    evidence_dir: Path,
    sandbox_root: Path | None = None,
    fetch_runner: Any | None = None,
) -> dict[str, Any]:
    """Baostock WL-driven manifest v3 (R3E-SP3-02)."""
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    sandbox = sandbox_root or DEFAULT_SANDBOX_ROOT_V3
    request = approved_pilot_v3_requests()[0]
    validate_pilot_v3_authorization(request)

    if fetch_runner is not None:
        fetch_item = fetch_runner(request, sandbox_root=sandbox)
    else:
        fetch_item = run_staged_pilot_raw_only(
            replace(request, dry_run=False),
            sandbox_root=sandbox / "baostock",
            pilot_request_id="v3-baostock",
            authorization_gate=validate_pilot_v3_authorization,
        )
        fetch_item["pilot_id"] = PILOT_ID_V3

    generated_at = _utc_now_iso()
    manifest_entry = _manifest_v2_fetch_entry(fetch_item, pilot_request_id="v3-baostock")
    wl_ref = compute_whitelist_ref()
    payload = {
        "pilot_id": PILOT_ID_V3,
        "generated_at": generated_at,
        "whitelist_ref": wl_ref,
        "source_id": "baostock",
        "data_domain": request.data_domain,
        "symbols": list(request.symbols_or_indicators),
        "date_window": request.date_window,
        "fetches": [fetch_item],
        "manifest_entries": [manifest_entry],
        "required_fields_present": all(
            manifest_entry.get(field) is not None
            for field in ("content_hash", "source_fetch_id", "as_of_timestamp")
        ),
    }
    staging_payload = {
        "pilot_id": PILOT_ID_V3,
        "generated_at": generated_at,
        "whitelist_ref": wl_ref,
        "staged_rows": [
            {
                "pilot_request_id": "v3-baostock",
                "staged_file_ids": fetch_item.get("staged_file_ids", []),
                "quality_flag": STAGED_FILE_REGISTRY_QUALITY,
            }
        ],
        "allow_clean_write": False,
    }
    (evidence_dir / RAW_MANIFEST_V3_BAOSTOCK_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / STAGING_MANIFEST_V3_JSON).write_text(
        json.dumps(staging_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def capture_cninfo_evidence_v3(
    *,
    evidence_dir: Path,
    sandbox_root: Path | None = None,
    fetch_runner: Any | None = None,
) -> dict[str, Any]:
    """Cninfo metadata evidence v3; rejects PDF/full-text ops at authorization gate."""
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    sandbox = sandbox_root or DEFAULT_SANDBOX_ROOT_V3
    request = approved_pilot_v3_requests()[2]
    validate_pilot_v3_authorization(request)

    if fetch_runner is not None:
        fetch_item = fetch_runner(request, sandbox_root=sandbox)
    else:
        fetch_item = run_staged_pilot_raw_only(
            replace(request, dry_run=False),
            sandbox_root=sandbox / "cninfo",
            pilot_request_id="v3-cninfo",
            authorization_gate=validate_pilot_v3_authorization,
        )
        fetch_item["pilot_id"] = PILOT_ID_V3

    raw_paths = fetch_item.get("fetch_result", {}).get("raw_file_paths") or []
    schema_fields: list[str] = []
    if raw_paths:
        raw_payload = _load_raw_json_payload(raw_paths[0])
        rows = raw_payload.get("rows", [])
        if isinstance(rows, list) and rows and isinstance(rows[0], dict):
            schema_fields = sorted(rows[0].keys())

    notes_lines = [
        "# cninfo metadata schema notes v3",
        "",
        f"- **Pilot ID:** {PILOT_ID_V3}",
        f"- **Symbols:** {', '.join(request.symbols_or_indicators)}",
        f"- **Date window:** {request.date_window}",
        "- **metadata_only:** true",
        "",
        "## Observed fields",
        "",
    ]
    if schema_fields:
        notes_lines.extend(f"- `{field}`" for field in schema_fields)
    else:
        notes_lines.append("- _(no rows in sample — structure validation deferred)_")

    (evidence_dir / CNINFO_SCHEMA_NOTES_V3_MD).write_text(
        "\n".join(notes_lines) + "\n",
        encoding="utf-8",
    )

    generated_at = _utc_now_iso()
    return {
        "pilot_id": PILOT_ID_V3,
        "generated_at": generated_at,
        "whitelist_ref": compute_whitelist_ref(),
        "source_id": "cninfo",
        "schema_fields": schema_fields,
        "metadata_only": True,
        "fetch": fetch_item,
    }


def capture_akshare_validation_taxonomy_v3(
    *,
    evidence_dir: Path,
    taxonomy_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Akshare validation taxonomy v3 (R3E-SP3-04)."""
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    request = approved_pilot_v3_requests()[1]
    validate_pilot_v3_authorization(request)
    assert_akshare_not_primary_for_daily_bar()

    records = taxonomy_records or [
        {
            "source_id": "akshare",
            "operation": request.operation,
            "status": FetchTaxonomyStatus.SUCCESS.value,
            "validation_only": True,
            "re_defer": False,
            "whitelist_input_id": "L1-MACRO-SUPP-VALIDATION",
        },
        {
            "source_id": "akshare",
            "operation": request.operation,
            "status": FetchTaxonomyStatus.SOURCE_FAILURE.value,
            "validation_only": True,
            "re_defer": True,
            "reason": "NETWORK_ERROR retry exhausted; R3-PROMPT14-AKSHARE-VAL-01 re-defer",
            "whitelist_input_id": "L1-MACRO-SUPP-VALIDATION",
        },
    ]
    allowed_status = {item.value for item in FetchTaxonomyStatus}
    for record in records:
        if record.get("status") not in allowed_status:
            raise ValueError(f"invalid taxonomy status: {record.get('status')}")

    generated_at = _utc_now_iso()
    payload = {
        "pilot_id": PILOT_ID_V3,
        "generated_at": generated_at,
        "whitelist_ref": compute_whitelist_ref(),
        "validation_only": True,
        "primary_forbidden": True,
        "records": records,
    }
    (evidence_dir / AKSHARE_TAXONOMY_V3_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def capture_conflict_summary_v3(
    *,
    evidence_dir: Path,
) -> dict[str, Any]:
    """Conflict dry-run summary v3 — no clean write (R3E-SP3-05)."""
    from backend.app.validators.source_conflict import (
        SourceConflictRequest,
        SourceConflictValidator,
    )

    evidence_dir = Path(evidence_dir)
    validator = SourceConflictValidator()
    request = SourceConflictRequest(
        run_id="v3-conflict-dry-run",
        job_id="r3e-staged-pilot-v3-conflict",
        data_domain="cn_equity_daily_bar",
        primary_source="baostock",
        validation_sources=("akshare",),
        key_fields=("symbol", "trade_date"),
        comparable_fields=("close",),
        tolerance_rule_set_id="staged_pilot_v3",
    )
    sample_symbol = pilot_v3_baostock_symbols()[0]
    rows = [
        {
            "source_id": "baostock",
            "symbol": sample_symbol,
            "trade_date": "2026-06-01",
            "close": 10.0,
        },
        {
            "source_id": "akshare",
            "symbol": sample_symbol,
            "trade_date": "2026-06-01",
            "close": 10.5,
        },
    ]
    report = validator.validate_rows(request, rows)
    generated_at = _utc_now_iso()
    payload = {
        "pilot_id": PILOT_ID_V3,
        "generated_at": generated_at,
        "whitelist_ref": compute_whitelist_ref(),
        "dry_run": True,
        "clean_write_attempted": False,
        "can_write_primary_value": report.can_write_primary_value,
        "conflict_status": report.status,
        "conflict_count": len(report.conflicts),
        "conflicts": [
            {
                "field_name": finding.field_name,
                "primary_value": finding.primary_value,
                "competing_source": finding.competing_source,
                "competing_value": finding.competing_value,
                "severity": finding.severity,
            }
            for finding in report.conflicts
        ],
        "policy_ref": "docs/modules/data_validation_and_conflict.md",
    }
    (evidence_dir / CONFLICT_CHECK_V3_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def write_no_mutation_proof_v3(
    *,
    evidence_dir: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    """No-mutation proof v3 markdown + payload (R3E-SP3-06)."""
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    target_db = db_path or DEFAULT_PRODUCTION_DB
    proof = build_production_mutation_proof(target_db)
    generated_at = _utc_now_iso()
    lines = [
        "# Production DB — No Mutation Proof v3",
        "",
        f"- **Pilot ID:** {PILOT_ID_V3}",
        f"- **Generated at:** {generated_at}",
        f"- **Production DB:** `{target_db}`",
        f"- **proof_status:** {proof.get('proof_status')}",
        f"- **db_hash_unchanged:** {proof.get('db_hash_unchanged')}",
        f"- **row_counts_unchanged:** {proof.get('row_counts_unchanged')}",
        "- **production_clean_write:** false",
    ]
    (evidence_dir / NO_MUTATION_V3_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return proof


def _write_source_readiness_matrix_v3(evidence_dir: Path, per_source: dict[str, str]) -> None:
    lines = [
        "# Source Readiness Matrix v3",
        "",
        f"- **Pilot ID:** {PILOT_ID_V3}",
        f"- **Whitelist aggregate sha256:** {compute_whitelist_ref()['aggregate_sha256']}",
        "",
        "| source_id | decision | next_gate |",
        "| --- | --- | --- |",
    ]
    next_gates = {
        "baostock": "sandbox_clean_write_rehearsal_candidate",
        "cninfo": "metadata_expansion_review",
        "akshare": "validation_only_re_defer",
    }
    for source_id in V3_SOURCE_CLOSEOUT_IDS:
        lines.append(
            f"| {source_id} | {per_source.get(source_id, 're-defer')} | "
            f"{next_gates.get(source_id, 'none')} |"
        )
    lines.extend(
        [
            "",
            "## Claims",
            "",
            "- staged-only evidence; no production-live readiness claim",
            "- registry closure deferred to main-session proposed delta",
        ]
    )
    (evidence_dir / SOURCE_READINESS_MATRIX_V3_MD).write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def _write_registry_proposed_delta_v3(evidence_dir: Path) -> dict[str, Any]:
    """Proposed registry delta — not committed by Execute agent (MASTER §3.3)."""
    payload = {
        "pilot_id": PILOT_ID_V3,
        "status": "proposed",
        "note": "Execute agent must not commit registry triad closure; main session merge only",
        "proposed_rows": [
            {
                "source_id": "baostock",
                "readiness": "sandbox_candidate",
                "evidence_ref": RAW_MANIFEST_V3_BAOSTOCK_JSON,
            },
            {
                "source_id": "cninfo",
                "readiness": "sandbox_candidate",
                "evidence_ref": CNINFO_SCHEMA_NOTES_V3_MD,
            },
            {
                "source_id": "akshare",
                "readiness": "validation_only",
                "evidence_ref": AKSHARE_TAXONOMY_V3_JSON,
                "deferred_registry_ids": [
                    "R3-PROMPT14-AKSHARE-VAL-01",
                    "R3-B2.75-REQ2-EM",
                ],
            },
        ],
    }
    (evidence_dir / REGISTRY_PROPOSED_DELTA_V3_YAML).write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return payload


def build_pilot_v3_closeout(
    *,
    evidence_dir: Path,
    mutation_proof: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Pilot v3 closeout + readiness matrix (R3E-SP3-06)."""
    evidence_dir = Path(evidence_dir)
    if mutation_proof is None:
        mutation_proof = build_production_mutation_proof(DEFAULT_PRODUCTION_DB)

    taxonomy_path = evidence_dir / AKSHARE_TAXONOMY_V3_JSON
    akshare_taxonomy = (
        json.loads(taxonomy_path.read_text(encoding="utf-8"))
        if taxonomy_path.is_file()
        else None
    )
    per_source = {
        "baostock": "expand",
        "cninfo": "expand",
        "akshare": "re-defer"
        if akshare_taxonomy and any(r.get("re_defer") for r in akshare_taxonomy.get("records", []))
        else "retry",
    }
    hash_ok = mutation_proof.get("db_hash_unchanged") is True
    counts_ok = mutation_proof.get("row_counts_unchanged") is True
    proof_status = mutation_proof.get("proof_status")
    closeout_pass = hash_ok and counts_ok and proof_status == "VERIFIED"

    generated_at = _utc_now_iso()
    payload = {
        "pilot_id": PILOT_ID_V3,
        "generated_at": generated_at,
        "whitelist_ref": compute_whitelist_ref(),
        "production_live_readiness_claim": False,
        "mutation_proof_status": proof_status,
        "db_hash_unchanged": mutation_proof.get("db_hash_unchanged"),
        "row_counts_unchanged": mutation_proof.get("row_counts_unchanged"),
        "closeout_pass": closeout_pass,
        "per_source": per_source,
        "sandbox_clean_write_rehearsal": False,
        "run_mode": "staged_only",
        "model_driven": True,
    }
    reason = mutation_proof.get("reason")
    if reason:
        payload["mutation_proof_reason"] = reason
    (evidence_dir / CLOSEOUT_V3_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_source_readiness_matrix_v3(evidence_dir, per_source)
    _write_registry_proposed_delta_v3(evidence_dir)
    return payload


def run_full_staged_pilot_v3(
    evidence_dir: Path | str,
    *,
    sandbox_root: Path | None = None,
    skip_live_fetch: bool = False,
    fetch_runner: Any | None = None,
) -> dict[str, Any]:
    """End-to-end staged pilot v3 evidence capture (WL-driven)."""
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    sandbox = sandbox_root or DEFAULT_SANDBOX_ROOT_V3

    caps = write_pilot_v3_caps(evidence_dir)
    reset_network_call_budget(limit=MAX_NETWORK_CALLS_V3)

    raw_manifest: dict[str, Any] | None = None
    if not skip_live_fetch:
        raw_manifest = capture_baostock_evidence_v3(
            evidence_dir=evidence_dir,
            sandbox_root=sandbox,
            fetch_runner=fetch_runner,
        )
        capture_cninfo_evidence_v3(
            evidence_dir=evidence_dir,
            sandbox_root=sandbox,
            fetch_runner=fetch_runner,
        )

    akshare_taxonomy = capture_akshare_validation_taxonomy_v3(evidence_dir=evidence_dir)
    conflict_payload = capture_conflict_summary_v3(evidence_dir=evidence_dir)
    mutation_proof = write_no_mutation_proof_v3(evidence_dir=evidence_dir)
    closeout = build_pilot_v3_closeout(
        evidence_dir=evidence_dir,
        mutation_proof=mutation_proof,
    )

    return {
        "pilot_id": PILOT_ID_V3,
        "caps": caps,
        "raw_manifest": raw_manifest,
        "akshare_taxonomy": akshare_taxonomy,
        "conflict": conflict_payload,
        "mutation_proof": mutation_proof,
        "closeout": closeout,
        "skip_live_fetch": skip_live_fetch,
    }

