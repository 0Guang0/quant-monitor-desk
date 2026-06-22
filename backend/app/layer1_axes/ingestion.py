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

    def _row_counts(self, tables: tuple[str, ...]) -> dict[str, int | None]:
        con = duckdb.connect(str(self._db_path), read_only=True)
        counts: dict[str, int | None] = {}
        try:
            for name in tables:
                exists = con.execute(
                    """
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'main' AND table_name = ?
                    """,
                    [name],
                ).fetchone()[0]
                if not exists:
                    counts[name] = None
                    continue
                counts[name] = int(con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0])
        finally:
            con.close()
        return counts

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
            if indicator_id not in self._allowlist:
                raise IngestionRejectedError(
                    f"indicator {indicator_id!r} is not on the ingestion allowlist",
                    reason_code=NOT_ON_ALLOWLIST_REJECTED,
                    indicator_id=indicator_id,
                )
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
        if indicator_id not in self._allowlist:
            raise IngestionRejectedError(
                f"indicator {indicator_id!r} is not on the ingestion allowlist",
                reason_code=NOT_ON_ALLOWLIST_REJECTED,
                indicator_id=indicator_id,
            )
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
        indicator = self._indicator_by_id(indicator_id)
        self._assert_indicator_eligible(indicator)
        if indicator_id not in self._allowlist:
            raise IngestionRejectedError(
                f"indicator {indicator_id!r} is not on the ingestion allowlist",
                reason_code=NOT_ON_ALLOWLIST_REJECTED,
                indicator_id=indicator_id,
            )

        resolved_run_id = run_id or f"layer1-commit-{indicator_id}"
        resolved_job_id = job_id or f"layer1-commit-{indicator_id}"
        binding, req, route_plan, resolved_run_id, resolved_job_id = (
            self._prepare_staged_route_and_request(
                indicator_id=indicator_id,
                as_of=as_of,
                run_id=resolved_run_id,
                job_id=resolved_job_id,
                run_id_prefix="layer1-commit",
                job_id_prefix="layer1-commit",
            )
        )
        resolved_fixture = (
            Path(fixture_path)
            if fixture_path is not None
            else app_config.PROJECT_ROOT / MACRO_FIXTURE_RELATIVE
        )
        quality_validator = DataQualityValidator()
        conflict_validator = SourceConflictValidator()
        obs_writer = Layer1ObservationWriter(self._conn_manager)
        snapshot_writer = Layer1SnapshotWriter(self._conn_manager)

        from backend.app.layer1_axes.observation_contract import (
            AXIS_OBSERVATION_DDL_COLUMNS,
            AXIS_OBSERVATION_REQUIRED_FIELDS,
        )

        micro: MicroFetchResult | None = None
        observation_row: dict[str, object] | None = None
        quality_report = None
        obs_write = None
        feature_write = None
        interp_write = None
        lineage_write = None
        feature_rows = None
        interp_rows = None
        lineage = None
        source_used = ""

        with self._conn_manager.writer() as con:
            con.execute("BEGIN")
            try:
                normalized_fetch, fetch_id, _, guard_decision, guard_reason = (
                    self._fetch_staging_on_connection(
                        con,
                        binding=binding,
                        req=req,
                        job_id=resolved_job_id,
                        register_staged_files=False,
                    )
                )

                micro = MicroFetchResult(
                    indicator_id=indicator_id,
                    as_of=as_of,
                    binding=binding,
                    route_plan=route_plan,
                    fetch_result=normalized_fetch,
                    run_id=resolved_run_id,
                    job_id=resolved_job_id,
                    fetch_id=fetch_id,
                    file_registry_ids=(),
                    resource_guard_decision=guard_decision.value,
                    resource_guard_reason=guard_reason,
                    staged_fixture_path=MACRO_FIXTURE_RELATIVE,
                )

                try:
                    observation_row = map_micro_fetch_to_observation_row(
                        micro,
                        data_root=self._data_root,
                        fixture_path=resolved_fixture,
                    )
                except ObservationMappingError as exc:
                    raise IngestionCommitBlockedError(
                        str(exc), reason_code="OBSERVATION_MAPPING"
                    ) from exc

                as_of_dt = observation_row["as_of_timestamp"]
                assert isinstance(as_of_dt, datetime)
                domain_obs = observation_row_to_domain(observation_row)
                if domain_obs.publish_timestamp > as_of_dt:
                    raise IngestionCommitBlockedError(
                        "publish_timestamp after as_of_timestamp",
                        reason_code="NO_FUTURE_DATA",
                    )

                duplicate = con.execute(
                    """
                    SELECT observation_id FROM axis_observation
                    WHERE indicator_id = ? AND as_of_timestamp = ?
                    LIMIT 1
                    """,
                    [indicator_id, as_of_dt],
                ).fetchone()
                if duplicate:
                    raise IngestionCommitBlockedError(
                        f"observation already committed for {indicator_id} on {as_of.isoformat()}",
                        reason_code="DUPLICATE_COMMIT",
                    )

                staging_table = f"stg_axis_obs_commit_{uuid.uuid4().hex[:8]}"
                source_used = str(observation_row["source_used"])
                guardrail_validator = AxisEngineeringGuardrailValidator(
                    self._load_axes().guardrails
                )
                try:
                    guardrail_validator.reject_forbidden_substitute(
                        indicator,
                        substitute_id=source_used,
                    )
                except GuardrailViolationError as exc:
                    raise IngestionCommitBlockedError(
                        str(exc), reason_code="GUARDRAIL_VIOLATION"
                    ) from exc
                con.execute(
                    f"CREATE TABLE {staging_table} AS SELECT * FROM axis_observation WHERE 1=0"
                )
                con.execute(
                    f"""
                    INSERT INTO {staging_table} VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                    """,
                    [observation_row[col] for col in AXIS_OBSERVATION_DDL_COLUMNS],
                )
                quality_request = DataQualityRequest(
                    run_id=resolved_run_id,
                    job_id=resolved_job_id,
                    data_domain=micro.binding.data_domain,
                    source_id=micro.fetch_result.source_id,
                    staging_table=staging_table,
                    primary_keys=("observation_id",),
                    required_fields=AXIS_OBSERVATION_REQUIRED_FIELDS,
                    rule_set_id=quality_validator._rule_set_id,  # noqa: SLF001
                )
                quality_report = quality_validator.validate_table(
                    con,
                    quality_request,
                    expected_columns=AXIS_OBSERVATION_DDL_COLUMNS,
                    timestamp_fields=("as_of_timestamp", "publish_timestamp", "fetch_time"),
                )
                if not quality_report.can_write_clean:
                    raise IngestionCommitBlockedError(
                        f"validation failed: {quality_report.status}",
                        reason_code="VALIDATION_FAILED",
                    )
                if quality_report.needs_manual_review:
                    raise IngestionCommitBlockedError(
                        "manual review required before clean write",
                        reason_code="MANUAL_REVIEW_REQUIRED",
                    )

                if self._validation_source_requires_conflict(indicator):
                    conflict_staging = f"stg_axis_obs_conflict_{uuid.uuid4().hex[:8]}"
                    con.execute(
                        f"CREATE TABLE {conflict_staging} AS "
                        "SELECT * FROM source_conflict WHERE 1=0"
                    )
                    conflict_request = SourceConflictRequest(
                        run_id=resolved_run_id,
                        job_id=resolved_job_id,
                        data_domain=micro.binding.data_domain,
                        source_id=micro.fetch_result.source_id,
                        staging_table=conflict_staging,
                        primary_keys=("conflict_id",),
                        rule_set_id="source_conflict_v1",
                    )
                    conflict_report = conflict_validator.validate_table(
                        con,
                        conflict_request,
                        staging_table=conflict_staging,
                    )
                    if conflict_report.status == "SEVERE_CONFLICT":
                        raise IngestionCommitBlockedError(
                            "severe source conflict blocks clean write",
                            reason_code="SEVERE_CONFLICT",
                        )

                try:
                    file_registry_ids = _register_clean_file_registry_rows(
                        con,
                        conn_manager=self._conn_manager,
                        fetch_result=normalized_fetch,
                        validation_report_id=quality_report.validation_report_id,
                        run_id=resolved_run_id,
                        job_id=resolved_job_id,
                        data_domain=micro.binding.data_domain,
                    )
                except RuntimeError as exc:
                    raise IngestionCommitBlockedError(str(exc), reason_code="WRITE_FAILED") from exc
                micro = replace(micro, file_registry_ids=file_registry_ids)

                obs_write = obs_writer.write_observations(
                    rows=[observation_row],
                    validation_report_id=quality_report.validation_report_id,
                    run_id=resolved_run_id,
                    job_id=resolved_job_id,
                    source_used=source_used,
                    data_domain=micro.binding.data_domain,
                    con=con,
                    own_transaction=False,
                )
                if obs_write.status != "SUCCESS":
                    raise IngestionCommitBlockedError(
                        obs_write.error_message or "observation write failed",
                        reason_code="WRITE_FAILED",
                    )

                feature_engine = AxisFeatureEngine(
                    resource_guard=ResourceGuard(con=con),
                    frequency=micro.binding.frequency,
                    min_obs_required=1,
                    window_len=1,
                )
                try:
                    feature_rows = feature_engine.compute_features(
                        as_of=as_of_dt,
                        observations=[domain_obs],
                        history=[domain_obs],
                    )
                except Layer1SnapshotError as exc:
                    raise IngestionCommitBlockedError(
                        str(exc), reason_code="NO_FUTURE_DATA"
                    ) from exc

                interp_rows = AxisInterpretationEngine().build_interpretation(
                    as_of=as_of_dt,
                    features=feature_rows,
                )

                report_ref = self._load_validation_report_ref(
                    con, quality_report.validation_report_id
                )
                lineage_builder = SnapshotLineageBuilder()
                raw_datasets = tuple(f"raw:{path}" for path in micro.fetch_result.raw_file_paths)
                parameter_hash = lineage_builder.parameter_hash_for(
                    rule_version=report_ref.rule_version,
                    inputs=(indicator_id, micro.binding.data_domain, *raw_datasets),
                )
                lineage = lineage_builder.build(
                    snapshot_id=feature_rows[0].feature_id,
                    snapshot_type="axis_feature_snapshot",
                    as_of=as_of_dt,
                    validation_report=report_ref,
                    input_window_start=as_of_dt,
                    input_window_end=as_of_dt,
                    source_dataset_ids=raw_datasets or (f"staged_fixture:{resolved_fixture.name}",),
                    parameter_hash=parameter_hash,
                    resource_profile="eco",
                    allow_synthetic_hashes=False,
                )

                snapshot_source = source_used
                snapshot_domain = micro.binding.data_domain
                feature_write = snapshot_writer.write_features(
                    rows=feature_rows,
                    validation_report_id=quality_report.validation_report_id,
                    run_id=resolved_run_id,
                    job_id=resolved_job_id,
                    source_used=snapshot_source,
                    data_domain=snapshot_domain,
                    con=con,
                    own_transaction=False,
                )
                interp_write = snapshot_writer.write_interpretation(
                    rows=interp_rows,
                    validation_report_id=quality_report.validation_report_id,
                    run_id=resolved_run_id,
                    job_id=resolved_job_id,
                    source_used=snapshot_source,
                    data_domain=snapshot_domain,
                    con=con,
                    own_transaction=False,
                )
                lineage_write = snapshot_writer.write_lineage(
                    lineage=lineage,
                    validation_report_id=quality_report.validation_report_id,
                    run_id=resolved_run_id,
                    job_id=resolved_job_id,
                    source_used=snapshot_source,
                    data_domain=snapshot_domain,
                    con=con,
                    own_transaction=False,
                )

                con.execute("COMMIT")
            except IngestionCommitBlockedError:
                con.execute("ROLLBACK")
                raise
            except IngestionRejectedError:
                con.execute("ROLLBACK")
                raise
            except Exception:
                con.execute("ROLLBACK")
                raise

        assert micro is not None
        assert observation_row is not None
        assert quality_report is not None
        assert obs_write is not None
        assert feature_write is not None
        assert interp_write is not None
        assert lineage_write is not None
        assert feature_rows is not None
        assert interp_rows is not None
        assert lineage is not None

        return IngestionCommitResult(
            indicator_id=indicator_id,
            as_of=as_of,
            micro_fetch=micro,
            validation_report_id=quality_report.validation_report_id,
            observation_write_status=obs_write.status,
            feature_write_status=feature_write.status,
            interpretation_write_status=interp_write.status,
            lineage_write_status=lineage_write.status,
            observation_id=str(observation_row["observation_id"]),
            feature_id=feature_rows[0].feature_id,
            interpretation_id=interp_rows[0].interpretation_id,
            lineage_snapshot_id=lineage.snapshot_id,
            source_fetch_ids=lineage.source_fetch_ids,
            source_content_hashes=lineage.source_content_hashes,
            staged_fixture_path=_relative_path(resolved_fixture),
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


from backend.app.layer1_axes.ingestion_evidence import (  # noqa: E402 — facade re-export (PR-R2a)
    NO_MUTATION_MD,
    PHASE2_MUTATION_TABLES,
    PHASE3_EVIDENCE_JSON,
    PHASE3_MUTATION_TABLES,
    PHASE3_NO_CLEAN_WRITE_MD,
    PHASE3_SANDBOX_DIRNAME,
    PHASE4_EVIDENCE_JSON,
    PHASE4_INVENTORY_DELTA_MD,
    PHASE4_MUTATION_TABLES,
    PHASE4_SANDBOX_DIRNAME,
    ROUTE_PREVIEW_JSON,
    ROUTE_PREVIEW_MD,
    capture_phase2_route_evidence,
    capture_phase3_micro_fetch_evidence,
    capture_phase4_clean_write_evidence,
    capture_task_phase2_evidence,
    capture_task_phase3_evidence,
    capture_task_phase4_evidence,
    format_phase2_no_mutation_md,
    format_phase2_route_preview_md,
    format_phase3_no_clean_write_md,
    format_phase4_inventory_delta_md,
)

__all__ = [
    "BLINDSPOT_INDICATOR_REJECTED",
    "DEFAULT_INGESTION_ALLOWLIST",
    "DISABLED_INDICATOR_REJECTED",
    "FORBIDDEN_INDICATOR_REJECTED",
    "FROZEN_STAGED_INDICATOR",
    "FRED_PRIMARY_DEFERRED_NOTE",
    "IngestionCommitBlockedError",
    "IngestionCommitResult",
    "IngestionRejectedError",
    "IngestionRouteBinding",
    "IndicatorRoutePreview",
    "Layer1ObservationIngestionService",
    "MACRO_FIXTURE_RELATIVE",
    "MicroFetchResult",
    "NO_MUTATION_MD",
    "NOT_OBSERVABLE_REJECTED",
    "NOT_ON_ALLOWLIST_REJECTED",
    "PHASE2_MUTATION_TABLES",
    "PHASE3_EVIDENCE_JSON",
    "PHASE3_MUTATION_TABLES",
    "PHASE3_NO_CLEAN_WRITE_MD",
    "PHASE3_SANDBOX_DIRNAME",
    "PHASE4_EVIDENCE_JSON",
    "PHASE4_INVENTORY_DELTA_MD",
    "PHASE4_MUTATION_TABLES",
    "PHASE4_SANDBOX_DIRNAME",
    "ROUTE_PREVIEW_JSON",
    "ROUTE_PREVIEW_MD",
    "RoutePreviewResult",
    "STAGED_DATA_DOMAIN",
    "STAGED_OPERATION",
    "STAGED_SERIES_ID",
    "STAGED_UNIT",
    "UNKNOWN_INDICATOR_REJECTED",
    "capture_phase2_route_evidence",
    "capture_phase3_micro_fetch_evidence",
    "capture_phase4_clean_write_evidence",
    "capture_task_phase2_evidence",
    "capture_task_phase3_evidence",
    "capture_task_phase4_evidence",
    "format_phase2_no_mutation_md",
    "format_phase2_route_preview_md",
    "format_phase3_no_clean_write_md",
    "format_phase4_inventory_delta_md",
]
