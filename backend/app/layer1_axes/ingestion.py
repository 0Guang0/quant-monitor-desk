"""Layer 1 observation ingestion bridge — route preview and staged ingest (Batch 2.5)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from pathlib import Path

import duckdb
from backend.app import config as app_config
from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.datasources.fetch_result import FetchRequest, FetchResult
from backend.app.datasources.route_models import SourceRoutePlan
from backend.app.datasources.service import (
    DataSourceService,
    ResourceGuardBlockedError,
)
from backend.app.db.connection import ConnectionManager
from backend.app.db.validation_gate import DbValidationGate
from backend.app.db.write_manager import WriteManager
from backend.app.layer1_axes.axis_loader import AxisSpecLoader
from backend.app.layer1_axes.feature_engine import AxisFeatureEngine, Layer1SnapshotError
from backend.app.layer1_axes.guardrails import (
    AxisEngineeringGuardrailValidator,
    GuardrailViolationError,
)
from backend.app.layer1_axes.interpretation import AxisInterpretationEngine
from backend.app.layer1_axes.lineage import Layer1SnapshotWriter, SnapshotLineageBuilder
from backend.app.layer1_axes.models import (
    AxisIndicatorDefinition,
    AxisLoadResult,
    ValidationReportRef,
)
from backend.app.layer1_axes.observation_mapper import (
    ObservationMappingError,
    map_micro_fetch_to_observation_row,
    observation_row_to_domain,
)
from backend.app.layer1_axes.observation_writer import Layer1ObservationWriter
from backend.app.storage.file_registry import FileRegistry
from backend.app.storage.raw_store import SavedFile
from backend.app.validators.data_quality import DataQualityRequest, DataQualityValidator
from backend.app.validators.source_conflict import SourceConflictRequest, SourceConflictValidator

FROZEN_STAGED_INDICATOR = "ENV-E1-DGS10"
STAGED_DATA_DOMAIN = "macro_supplementary"
STAGED_OPERATION = "fetch_macro_series"
STAGED_SERIES_ID = "DGS10"
STAGED_UNIT = "pct"
MACRO_FIXTURE_RELATIVE = "tests/fixtures/layer1_macro_observation_fixture.json"
FRED_PRIMARY_DEFERRED_NOTE = (
    "B2.5-O-05: declared primary_source FRED:DGS10 deferred; "
    "staged route macro_supplementary.fetch_macro_series used"
)

DEFAULT_INGESTION_ALLOWLIST: frozenset[str] = frozenset({FROZEN_STAGED_INDICATOR})
STAGED_FILE_REGISTRY_VALIDATION_REPORT_ID = "staged-micro-fetch-file-registry"

FORBIDDEN_INDICATOR_REJECTED = "FORBIDDEN_INDICATOR"
BLINDSPOT_INDICATOR_REJECTED = "BLINDSPOT_INDICATOR"
NOT_OBSERVABLE_REJECTED = "NOT_OBSERVABLE"
DISABLED_INDICATOR_REJECTED = "DISABLED_INDICATOR"
UNKNOWN_INDICATOR_REJECTED = "UNKNOWN_INDICATOR"
NOT_ON_ALLOWLIST_REJECTED = "NOT_ON_ALLOWLIST"


def _register_clean_file_registry_rows(
    con,
    *,
    conn_manager: ConnectionManager,
    fetch_result: FetchResult,
    validation_report_id: str,
    run_id: str,
    job_id: str,
    data_domain: str,
) -> tuple[str, ...]:
    """Register raw fetch files via FileRegistry + WriteManager (Phase 4 clean path)."""
    if fetch_result.status != "SUCCESS" or not fetch_result.raw_file_paths:
        return ()
    wm = WriteManager(conn_manager, DbValidationGate(conn_manager))
    registry = FileRegistry(conn_manager, wm, validation_report_id=validation_report_id)
    as_of_raw = fetch_result.as_of_timestamp or ""
    as_of_str = as_of_raw.split("T")[0] if "T" in as_of_raw else as_of_raw
    if not as_of_str:
        as_of_str = datetime.now(UTC).date().isoformat()
    registered: list[str] = []
    for local_path in fetch_result.raw_file_paths:
        saved = SavedFile(
            file_id=str(uuid.uuid4()),
            source=fetch_result.source_id,
            data_domain=data_domain,
            local_path=local_path,
            content_hash=fetch_result.content_hash or "",
            file_type="json",
            as_of=as_of_str,
        )
        registered.append(
            registry.register_on_connection(
                con,
                saved,
                run_id=run_id,
                job_id=job_id,
                own_transaction=False,
            )
        )
    return tuple(registered)


def _ensure_staged_file_registry_validation_report(
    con,
    *,
    validation_report_id: str,
    run_id: str,
    job_id: str,
    data_domain: str,
    source_id: str,
) -> None:
    con.execute(
        """
        INSERT OR REPLACE INTO validation_report (
            validation_report_id, run_id, job_id, data_domain, staging_table,
            source_id, status, checked_rows, failed_rows, warning_rows,
            quality_flags, stale_reason, can_write_clean, needs_manual_review,
            created_at, rule_set_id, rule_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            validation_report_id,
            run_id,
            job_id,
            data_domain,
            "stg_file_registry",
            source_id,
            "PASSED",
            0,
            0,
            0,
            "staged_file_registry_metadata_only",
            None,
            True,
            False,
            datetime.now(UTC),
            "p0_round_1",
            "p0_round_1",
        ],
    )


class IngestionRejectedError(ValueError):
    """Indicator blocked before route preview or fetch."""

    def __init__(self, message: str, *, reason_code: str, indicator_id: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.indicator_id = indicator_id


class IngestionCommitBlockedError(RuntimeError):
    """Clean write blocked by validation, conflict, guard, or mapping rules."""

    def __init__(self, message: str, *, reason_code: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(frozen=True)
class IngestionRouteBinding:
    indicator_id: str
    axis_id: str
    data_domain: str
    operation: str
    frequency: str
    unit: str
    primary_source_declared: str
    validation_source: str
    fallback_policy: str
    series_id: str | None = None
    staged_route_note: str | None = None


@dataclass(frozen=True)
class IndicatorRoutePreview:
    indicator_id: str
    as_of: date
    binding: IngestionRouteBinding
    route_plan: SourceRoutePlan
    resource_guard_decision: str
    resource_guard_reason: str
    capability_verified: bool
    stop_reason: str | None = None


@dataclass(frozen=True)
class RoutePreviewResult:
    previews: tuple[IndicatorRoutePreview, ...]
    dry_run: bool = True


@dataclass(frozen=True)
class MicroFetchResult:
    indicator_id: str
    as_of: date
    binding: IngestionRouteBinding
    route_plan: SourceRoutePlan
    fetch_result: FetchResult
    run_id: str
    job_id: str
    fetch_id: str | None
    file_registry_ids: tuple[str, ...]
    resource_guard_decision: str
    resource_guard_reason: str
    staged_fixture_path: str


@dataclass(frozen=True)
class IngestionCommitResult:
    indicator_id: str
    as_of: date
    micro_fetch: MicroFetchResult
    validation_report_id: str
    observation_write_status: str
    feature_write_status: str
    interpretation_write_status: str
    lineage_write_status: str
    observation_id: str
    feature_id: str
    interpretation_id: str
    lineage_snapshot_id: str
    source_fetch_ids: tuple[str, ...]
    source_content_hashes: tuple[str, ...]
    staged_fixture_path: str


class Layer1ObservationIngestionService:
    """Controlled Layer 1 observation ingestion facade (§3.4 wiring)."""

    def __init__(
        self,
        *,
        db_path: Path | str,
        data_root: Path | str | None = None,
        datasource: DataSourceService | None = None,
        axis_loader: AxisSpecLoader | None = None,
        allowlist: frozenset[str] | None = None,
    ) -> None:
        self._db_path = Path(db_path)
        self._data_root = Path(data_root) if data_root is not None else app_config.DATA_ROOT
        self._datasource = datasource or DataSourceService(data_root=self._data_root)
        self._axis_loader = axis_loader or AxisSpecLoader()
        self._allowlist = allowlist if allowlist is not None else DEFAULT_INGESTION_ALLOWLIST
        self._axis_load: AxisLoadResult | None = None
        self._conn_manager = ConnectionManager(self._db_path)

    def _load_axes(self) -> AxisLoadResult:
        if self._axis_load is None:
            self._axis_load = self._axis_loader.load()
        return self._axis_load

    def _indicator_by_id(self, indicator_id: str) -> AxisIndicatorDefinition:
        loaded = self._load_axes()
        for indicator in loaded.indicators:
            if indicator.indicator_id == indicator_id:
                return indicator
        raise IngestionRejectedError(
            f"unknown indicator {indicator_id!r}",
            reason_code=UNKNOWN_INDICATOR_REJECTED,
            indicator_id=indicator_id,
        )

    @staticmethod
    def _assert_indicator_eligible(indicator: AxisIndicatorDefinition) -> None:
        if indicator.is_forbidden:
            raise IngestionRejectedError(
                f"indicator {indicator.indicator_id!r} is forbidden",
                reason_code=FORBIDDEN_INDICATOR_REJECTED,
                indicator_id=indicator.indicator_id,
            )
        if indicator.is_blindspot:
            raise IngestionRejectedError(
                f"indicator {indicator.indicator_id!r} is BlindSpot",
                reason_code=BLINDSPOT_INDICATOR_REJECTED,
                indicator_id=indicator.indicator_id,
            )
        if not indicator.is_observable:
            raise IngestionRejectedError(
                f"indicator {indicator.indicator_id!r} is not observable",
                reason_code=NOT_OBSERVABLE_REJECTED,
                indicator_id=indicator.indicator_id,
            )
        if not indicator.is_enabled:
            raise IngestionRejectedError(
                f"indicator {indicator.indicator_id!r} is disabled",
                reason_code=DISABLED_INDICATOR_REJECTED,
                indicator_id=indicator.indicator_id,
            )

    @staticmethod
    def _resolve_binding(indicator: AxisIndicatorDefinition) -> IngestionRouteBinding:
        if indicator.indicator_id == FROZEN_STAGED_INDICATOR:
            return IngestionRouteBinding(
                indicator_id=indicator.indicator_id,
                axis_id=indicator.axis_id,
                data_domain=STAGED_DATA_DOMAIN,
                operation=STAGED_OPERATION,
                frequency=indicator.frequency,
                unit=STAGED_UNIT,
                primary_source_declared=indicator.primary_source,
                validation_source=indicator.validation_source,
                fallback_policy=indicator.fallback_policy,
                series_id=STAGED_SERIES_ID,
                staged_route_note=FRED_PRIMARY_DEFERRED_NOTE,
            )
        raise IngestionRejectedError(
            f"indicator {indicator.indicator_id!r} has no staged route binding",
            reason_code=NOT_ON_ALLOWLIST_REJECTED,
            indicator_id=indicator.indicator_id,
        )

    def _verify_capability(
        self,
        binding: IngestionRouteBinding,
        route_plan: SourceRoutePlan,
    ) -> bool:
        """018A Phase 2 step 5: capability registry must declare domain/operation."""
        source_id = route_plan.selected_source_id
        if source_id is not None:
            self._datasource.assert_capability_declared(
                source_id,
                binding.data_domain,
                binding.operation,
            )
            return True
        primary = self._datasource.primary_source_for_domain(binding.data_domain)
        self._datasource.assert_capability_declared(
            primary,
            binding.data_domain,
            binding.operation,
        )
        return True

    @staticmethod
    def _enforce_resource_guard(guard_decision: Decision, guard_reason: str) -> None:
        if guard_decision in (Decision.PAUSE, Decision.HARD_STOP):
            raise ResourceGuardBlockedError(
                guard_reason or f"ResourceGuard {guard_decision.value}",
                decision=guard_decision,
            )

    @staticmethod
    def _compose_stop_reason(
        *,
        guard_decision: Decision,
        guard_reason: str,
        route_plan: SourceRoutePlan,
    ) -> str | None:
        reasons: list[str] = []
        if guard_decision in (Decision.PAUSE, Decision.HARD_STOP):
            reasons.append(f"resource_guard={guard_decision.value}: {guard_reason or 'blocked'}")
        if route_plan.route_status != "READY":
            reasons.append(
                f"route_status={route_plan.route_status}; "
                "Phase 2 stops until staged/authorized route is READY"
            )
        return "; ".join(reasons) if reasons else None

    def _assert_allowlisted(self, indicator_id: str) -> None:
        if indicator_id not in self._allowlist:
            raise IngestionRejectedError(
                f"indicator {indicator_id!r} is not on the ingestion allowlist",
                reason_code=NOT_ON_ALLOWLIST_REJECTED,
                indicator_id=indicator_id,
            )

    def _row_counts(self, tables: tuple[str, ...]) -> dict[str, int | None]:
        from backend.app.db.row_counts import table_row_counts

        return table_row_counts(self._db_path, tables)

    def preview_routes(
        self,
        *,
        indicators: list[str],
        as_of: date,
        run_id: str = "layer1-route-preview",
        job_id: str = "layer1-route-preview",
    ) -> RoutePreviewResult:
        """Dry-run SourceRoutePlan preview — no fetch or DB writes (Phase 2)."""
        guard_decision, guard_reason = self._datasource.check_resource_guard()
        self._enforce_resource_guard(guard_decision, guard_reason)

        previews: list[IndicatorRoutePreview] = []
        for indicator_id in indicators:
            indicator = self._indicator_by_id(indicator_id)
            self._assert_indicator_eligible(indicator)
            self._assert_allowlisted(indicator_id)
            binding = self._resolve_binding(indicator)
            route_plan = self._datasource.preview_route(
                data_domain=binding.data_domain,
                operation=binding.operation,
                run_id=run_id,
                job_id=job_id,
            )
            capability_verified = self._verify_capability(binding, route_plan)
            previews.append(
                IndicatorRoutePreview(
                    indicator_id=indicator_id,
                    as_of=as_of,
                    binding=binding,
                    route_plan=route_plan,
                    resource_guard_decision=guard_decision.value,
                    resource_guard_reason=guard_reason,
                    capability_verified=capability_verified,
                    stop_reason=self._compose_stop_reason(
                        guard_decision=guard_decision,
                        guard_reason=guard_reason,
                        route_plan=route_plan,
                    ),
                )
            )
        return RoutePreviewResult(previews=tuple(previews), dry_run=True)

    def _prepare_micro_fetch_binding(
        self,
        *,
        indicator_id: str,
    ) -> IngestionRouteBinding:
        indicator = self._indicator_by_id(indicator_id)
        self._assert_indicator_eligible(indicator)
        self._assert_allowlisted(indicator_id)
        return self._resolve_binding(indicator)

    def _prepare_staged_route_and_request(
        self,
        *,
        indicator_id: str,
        as_of: date,
        run_id: str | None,
        job_id: str | None,
        run_id_prefix: str,
        job_id_prefix: str,
    ) -> tuple[IngestionRouteBinding, FetchRequest, SourceRoutePlan, str, str]:
        binding = self._prepare_micro_fetch_binding(indicator_id=indicator_id)
        resolved_run_id = run_id or f"{run_id_prefix}-{indicator_id}"
        resolved_job_id = job_id or f"{job_id_prefix}-{indicator_id}"
        primary_source = self._datasource.primary_source_for_domain(binding.data_domain)
        req = FetchRequest(
            run_id=resolved_run_id,
            source_id=primary_source,
            data_domain=binding.data_domain,
            end_time=as_of.isoformat(),
        )
        route_plan = self._datasource.preview_route(
            data_domain=binding.data_domain,
            operation=binding.operation,
            run_id=resolved_run_id,
            job_id=resolved_job_id,
        )
        self._verify_capability(binding, route_plan)
        staged_bypass = (
            self._datasource.staged_fixture_mode
            and indicator_id in self._allowlist
            and route_plan.route_status
            in {"VALIDATION_ONLY_BLOCKED", "DISABLED_SOURCE", "NO_AVAILABLE_SOURCE"}
        )
        if not staged_bypass and (
            route_plan.route_status != "READY" or route_plan.selected_source_id is None
        ):
            raise IngestionRejectedError(
                f"route not ready: {route_plan.route_status}",
                reason_code="ROUTE_NOT_READY",
                indicator_id=indicator_id,
            )
        return binding, req, route_plan, resolved_run_id, resolved_job_id

    def _fetch_staging_on_connection(
        self,
        con,
        *,
        binding: IngestionRouteBinding,
        req: FetchRequest,
        job_id: str,
        register_staged_files: bool,
    ) -> tuple[FetchResult, str | None, tuple[str, ...], Decision, str]:
        guard_decision, guard_reason = ResourceGuard(con=con).check()
        self._enforce_resource_guard(guard_decision, guard_reason)
        fetch_result = self._datasource.fetch(
            req,
            con=con,
            job_id=job_id,
            operation=binding.operation,
        )
        normalized_fetch = fetch_result.model_copy(
            update={
                "raw_file_paths": [
                    _relative_to_data_root(p, self._data_root) for p in fetch_result.raw_file_paths
                ]
            }
        )
        file_registry_ids: tuple[str, ...] = ()
        if register_staged_files:
            _ensure_staged_file_registry_validation_report(
                con,
                validation_report_id=STAGED_FILE_REGISTRY_VALIDATION_REPORT_ID,
                run_id=req.run_id,
                job_id=job_id,
                data_domain=binding.data_domain,
                source_id=fetch_result.source_id,
            )
            file_registry_ids = _register_clean_file_registry_rows(
                con,
                conn_manager=self._conn_manager,
                fetch_result=normalized_fetch,
                validation_report_id=STAGED_FILE_REGISTRY_VALIDATION_REPORT_ID,
                run_id=req.run_id,
                job_id=job_id,
                data_domain=binding.data_domain,
            )
        fetch_id: str | None = None
        if fetch_result.status == "SUCCESS":
            row = con.execute(
                """
                SELECT fetch_id FROM fetch_log
                WHERE job_id = ? AND run_id = ?
                ORDER BY fetch_time DESC LIMIT 1
                """,
                [job_id, req.run_id],
            ).fetchone()
            fetch_id = row[0] if row else None
        return normalized_fetch, fetch_id, file_registry_ids, guard_decision, guard_reason

    def micro_fetch_staging(
        self,
        *,
        indicator_id: str,
        as_of: date,
        run_id: str | None = None,
        job_id: str | None = None,
    ) -> MicroFetchResult:
        """Micro-fetch via DataSourceService — raw/fetch evidence only (Phase 3)."""
        binding, req, route_plan, resolved_run_id, resolved_job_id = (
            self._prepare_staged_route_and_request(
                indicator_id=indicator_id,
                as_of=as_of,
                run_id=run_id,
                job_id=job_id,
                run_id_prefix="layer1-micro-fetch",
                job_id_prefix="layer1-micro",
            )
        )
        with self._conn_manager.writer() as con:
            normalized_fetch, fetch_id, file_registry_ids, guard_decision, guard_reason = (
                self._fetch_staging_on_connection(
                    con,
                    binding=binding,
                    req=req,
                    job_id=resolved_job_id,
                    register_staged_files=True,
                )
            )
        return MicroFetchResult(
            indicator_id=indicator_id,
            as_of=as_of,
            binding=binding,
            route_plan=route_plan,
            fetch_result=normalized_fetch,
            run_id=resolved_run_id,
            job_id=resolved_job_id,
            fetch_id=fetch_id,
            file_registry_ids=file_registry_ids,
            resource_guard_decision=guard_decision.value,
            resource_guard_reason=guard_reason,
            staged_fixture_path=MACRO_FIXTURE_RELATIVE,
        )

    @staticmethod
    def _validation_source_requires_conflict(indicator: AxisIndicatorDefinition) -> bool:
        source = (indicator.validation_source or "").strip().lower()
        return source not in {"", "none", "none_optional", "n/a"}

    @staticmethod
    def _load_validation_report_ref(con, validation_report_id: str) -> ValidationReportRef:
        row = con.execute(
            """
            SELECT validation_report_id, rule_version,
                   source_fetch_ids_json, source_content_hashes_json
            FROM validation_report
            WHERE validation_report_id = ?
            """,
            [validation_report_id],
        ).fetchone()
        if row is None:
            raise IngestionCommitBlockedError(
                f"validation_report {validation_report_id!r} missing",
                reason_code="MISSING_VALIDATION_REPORT",
            )
        return ValidationReportRef(
            validation_report_id=str(row[0]),
            rule_version=str(row[1]),
            source_fetch_ids_json=str(row[2] or "[]"),
            source_content_hashes_json=str(row[3] or "[]"),
        )

    def commit_clean_observation_and_snapshots(
        self,
        *,
        indicator_id: str,
        as_of: date,
        run_id: str | None = None,
        job_id: str | None = None,
        fixture_path: Path | str | None = None,
    ) -> IngestionCommitResult:
        """Validate staged evidence, write clean observation, snapshots, and lineage (Phase 4)."""
        from backend.app.layer1_axes.ingestion_commit import (
            commit_clean_observation_and_snapshots as _commit_impl,
        )

        return _commit_impl(
            self,
            indicator_id=indicator_id,
            as_of=as_of,
            run_id=run_id,
            job_id=job_id,
            fixture_path=fixture_path,
        )


def _relative_path(path: Path) -> str:
    from backend.app.layer1_axes.ingestion_inventory import _relative_to_project

    return _relative_to_project(path)


def _relative_to_data_root(path: Path | str, data_root: Path) -> str:
    resolved = Path(path).resolve()
    root = data_root.resolve()
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError:
        return _relative_path(resolved)

