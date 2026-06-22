"""Round 3 PROMPT_14 staged real-data pilot orchestration (fail-closed, sandbox-first)."""

from __future__ import annotations

import json
from contextvars import ContextVar
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from backend.app.config import DATA_ROOT, PROJECT_ROOT
from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.datasources.capability_registry import SourceCapabilityRegistry
from backend.app.datasources.route_models import SourceRoutePlan
from backend.app.datasources.route_planner import SourceRoutePlanner
from backend.app.datasources.service import DataSourceService
from backend.app.datasources.source_registry import SourceNotFoundError, SourceRegistry
from backend.app.db.connection import ConnectionManager
from backend.app.db.validation_gate import DbValidationGate, ValidationGateError, ValidationRejected
from backend.app.db.write_manager import WriteManager, WriteRequest
from backend.app.ops.mutation_proof import build_production_mutation_proof
from backend.app.ops.mutation_proof import key_table_row_counts as _key_table_row_counts
from backend.app.storage.file_registry import STG_FILE_REGISTRY, FileRegistry, _parse_as_of_timestamp
from backend.app.storage.staged_evidence import (
    STAGED_FILE_REGISTRY_PARSE_STATUS,
    STAGED_FILE_REGISTRY_QUALITY,
)
from backend.app.storage.raw_store import SavedFile

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


def reset_network_call_budget() -> None:
    """Test hook: reset per-run network call counter."""
    _NETWORK_BUDGET_CTX.set(_NetworkCallBudget())


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
) -> dict[str, Any]:
    """Dry-run route preview for one authorized pilot request (no fetch)."""
    validate_authorization(request)
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
) -> dict[str, Any]:
    """Sandbox raw-only fetch for one authorized request (route gate + network cap)."""
    assert_pilot_ready_before_fetch(request)
    if not request.raw_only:
        raise StagedPilotAuthorizationError("staged pilot requires raw_only=true")

    preview = preview_staged_pilot(
        replace(request, dry_run=True),
        pilot_request_id=f"{pilot_request_id}-pre",
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
