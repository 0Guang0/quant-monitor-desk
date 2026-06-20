"""Layer 1 observation ingestion bridge — route preview and staged ingest (Batch 2.5)."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, replace
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import duckdb
from backend.app import config as app_config
from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.datasources.fetch_result import FetchRequest, FetchResult
from backend.app.datasources.route_models import SourceRoutePlan
from backend.app.datasources.service import (
    DataSourceService,
    ResourceGuardBlockedError,
    build_staged_fixture_service,
)
from backend.app.db.connection import ConnectionManager
from backend.app.db.validation_gate import DbValidationGate
from backend.app.db.write_manager import WriteManager
from backend.app.layer1_axes.axis_loader import AxisSpecLoader
from backend.app.layer1_axes.feature_engine import AxisFeatureEngine, Layer1SnapshotError
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
from backend.app.storage.staged_evidence import register_staged_file_registry_rows
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

FORBIDDEN_INDICATOR_REJECTED = "FORBIDDEN_INDICATOR"
BLINDSPOT_INDICATOR_REJECTED = "BLINDSPOT_INDICATOR"
NOT_OBSERVABLE_REJECTED = "NOT_OBSERVABLE"
DISABLED_INDICATOR_REJECTED = "DISABLED_INDICATOR"
UNKNOWN_INDICATOR_REJECTED = "UNKNOWN_INDICATOR"
NOT_ON_ALLOWLIST_REJECTED = "NOT_ON_ALLOWLIST"

PHASE2_MUTATION_TABLES: tuple[str, ...] = (
    "axis_observation",
    "fetch_log",
    "file_registry",
    "axis_feature_snapshot",
    "axis_interpretation_snapshot",
    "axis_snapshot_lineage",
)

ROUTE_PREVIEW_JSON = "phase2_route_preview.json"
ROUTE_PREVIEW_MD = "phase2_route_preview_matrix.md"
NO_MUTATION_MD = "phase2_no_mutation_proof.md"
PHASE3_EVIDENCE_JSON = "phase3_micro_fetch_evidence.json"
PHASE3_NO_CLEAN_WRITE_MD = "phase3_no_clean_write_proof.md"
PHASE3_SANDBOX_DIRNAME = ".phase3-micro-fetch-sandbox"
PHASE4_SANDBOX_DIRNAME = ".phase4-clean-write-sandbox"
PHASE4_EVIDENCE_JSON = "phase4_clean_write_and_snapshot_evidence.json"
PHASE4_INVENTORY_DELTA_MD = "phase4_inventory_delta.md"

PHASE4_MUTATION_TABLES: tuple[str, ...] = (
    "axis_observation",
    "fetch_log",
    "file_registry",
    "validation_report",
    "write_audit_log",
    "axis_feature_snapshot",
    "axis_interpretation_snapshot",
    "axis_snapshot_lineage",
    "data_quality_log",
)

PHASE3_MUTATION_TABLES: tuple[str, ...] = (
    "axis_observation",
    "fetch_log",
    "file_registry",
    "job_event_log",
)


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
        if route_plan.route_status != "READY" or route_plan.selected_source_id is None:
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
            file_registry_ids = register_staged_file_registry_rows(con, normalized_fetch)
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


def _binding_to_dict(binding: IngestionRouteBinding) -> dict[str, Any]:
    return asdict(binding)


def _preview_to_dict(preview: IndicatorRoutePreview) -> dict[str, Any]:
    return {
        "indicator_id": preview.indicator_id,
        "as_of": preview.as_of.isoformat(),
        "intended_as_of_range": {
            "start": preview.as_of.isoformat(),
            "end": preview.as_of.isoformat(),
        },
        "binding": _binding_to_dict(preview.binding),
        "route_plan": preview.route_plan.to_payload_dict(),
        "resource_guard_decision": preview.resource_guard_decision,
        "resource_guard_reason": preview.resource_guard_reason,
        "capability_verified": preview.capability_verified,
        "stop_reason": preview.stop_reason,
    }


def format_phase2_route_preview_md(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 2 — Route Preview Matrix",
        "",
        f"- **Generated at:** {payload['generated_at']}",
        f"- **Frozen indicator:** `{payload['frozen_indicator']}`",
        f"- **Dry-run:** {payload['dry_run']}",
        f"- **FRED live deferred:** {payload.get('fred_primary_deferred')}",
        "",
        "## Allowlist",
        "",
    ]
    for item in payload.get("allowlist", []):
        lines.append(f"- `{item}`")
    lines.extend(["", "## Route previews", ""])
    for entry in payload.get("previews", []):
        plan = entry["route_plan"]
        binding = entry["binding"]
        lines.extend(
            [
                f"### `{entry['indicator_id']}` @ {entry['as_of']}",
                "",
                f"- data_domain: `{binding['data_domain']}`",
                f"- operation: `{binding['operation']}`",
                f"- series_id: `{binding.get('series_id')}`",
                f"- declared primary: `{binding['primary_source_declared']}`",
                f"- staged note: {binding.get('staged_route_note')}",
                f"- route_status: `{plan['route_status']}`",
                f"- selected_source_id: `{plan.get('selected_source_id')}`",
                f"- resource_guard: `{entry['resource_guard_decision']}`",
                f"- capability_verified: {entry.get('capability_verified')}",
                f"- intended_as_of_range: {entry.get('intended_as_of_range')}",
                f"- stop_reason: {entry.get('stop_reason')}",
                "",
                "| source_id | role | enabled | skip_reason |",
                "| --------- | ---- | ------- | ----------- |",
            ]
        )
        for candidate in plan.get("candidates", []):
            lines.append(
                f"| `{candidate['source_id']}` | {candidate['role']} | "
                f"{candidate['enabled']} | {candidate.get('skip_reason')} |"
            )
        lines.append("")
    proof = payload.get("mutation_proof", {})
    lines.extend(
        [
            "## No-mutation proof",
            "",
            f"- db_path: `{proof.get('db_path')}`",
            f"- db_capture_strategy: `{proof.get('db_capture_strategy')}`",
            f"- db_file_hash_unchanged: {proof.get('db_file_hash_unchanged')}",
            f"- row_counts_unchanged: {proof.get('row_counts_unchanged')}",
            f"- before: `{proof.get('before_counts')}`",
            f"- after: `{proof.get('after_counts')}`",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def _format_count_table_md(title: str, counts: dict[str, int | None]) -> list[str]:
    lines = [f"## {title}", "", "| table | row_count |", "| ----- | --------- |"]
    for name, count in counts.items():
        lines.append(f"| `{name}` | {count} |")
    lines.append("")
    return lines


def format_phase2_no_mutation_md(proof: dict[str, Any]) -> str:
    lines = [
        "# Phase 2 — No Mutation Proof",
        "",
        f"- **Generated at:** {proof['generated_at']}",
        f"- **DB path:** `{proof['db_path']}`",
        f"- **DB file hash unchanged:** {proof.get('db_file_hash_unchanged')}",
        f"- **Capture strategy:** {proof.get('db_capture_strategy')}",
        f"- **Row counts unchanged:** {proof['row_counts_unchanged']}",
        "",
    ]
    lines.extend(_format_count_table_md("Before preview", proof.get("before_counts", {})))
    lines.extend(_format_count_table_md("After preview", proof.get("after_counts", {})))
    return "\n".join(lines) + "\n"


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


def _db_file_hash(db_path: Path) -> str:
    if not db_path.is_file():
        return hashlib.sha256(b"").hexdigest()
    return hashlib.sha256(db_path.read_bytes()).hexdigest()


def capture_phase2_route_evidence(
    *,
    service: Layer1ObservationIngestionService,
    indicators: list[str],
    as_of: date,
    evidence_dir: Path | str,
    phase2_gate: dict[str, Any] | None = None,
    db_capture_strategy: str = "unspecified",
    baseline_db_relative: str | None = None,
) -> dict[str, Any]:
    """Run dry-run preview and persist Phase 2 evidence artifacts."""
    out = Path(evidence_dir)
    out.mkdir(parents=True, exist_ok=True)
    db_path = service._db_path
    before_hash = _db_file_hash(db_path)
    before_counts = service._row_counts(PHASE2_MUTATION_TABLES)
    result = service.preview_routes(indicators=indicators, as_of=as_of)
    after_hash = _db_file_hash(db_path)
    after_counts = service._row_counts(PHASE2_MUTATION_TABLES)
    mutation_proof = {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "db_path": _relative_path(db_path),
        "db_path_absolute": str(db_path.resolve()),
        "db_file_hash_before": before_hash,
        "db_file_hash_after": after_hash,
        "db_file_hash_unchanged": before_hash == after_hash,
        "db_capture_strategy": db_capture_strategy,
        "baseline_db_relative": baseline_db_relative,
        "before_counts": before_counts,
        "after_counts": after_counts,
        "row_counts_unchanged": before_counts == after_counts,
    }
    fixture_path = app_config.PROJECT_ROOT / MACRO_FIXTURE_RELATIVE
    payload: dict[str, Any] = {
        "phase": "phase2_route_preview",
        "generated_at": mutation_proof["generated_at"],
        "frozen_indicator": FROZEN_STAGED_INDICATOR,
        "fred_primary_deferred": True,
        "fred_primary_deferred_note": FRED_PRIMARY_DEFERRED_NOTE,
        "staged_fixture_path": MACRO_FIXTURE_RELATIVE,
        "staged_fixture_exists": fixture_path.is_file(),
        "allowlist": sorted(service._allowlist),
        "dry_run": result.dry_run,
        "route_persistence_phase3_note": (
            "Phase 3 will persist SourceRoutePlan via job_event_log.payload_json "
            "(per source_route_plan.md §5 option 2); no source_route_log in this batch."
        ),
        "source_conflict_phase4_note": (
            "Frozen indicator validation_source=none_optional; SourceConflictValidator "
            "not applicable for single-source staged scope unless validation source added."
        ),
        "previews": [_preview_to_dict(p) for p in result.previews],
        "mutation_proof": mutation_proof,
    }
    if phase2_gate is not None:
        payload["phase2_gate"] = phase2_gate
    json_path = out / ROUTE_PREVIEW_JSON
    md_path = out / ROUTE_PREVIEW_MD
    proof_path = out / NO_MUTATION_MD
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_phase2_route_preview_md(payload), encoding="utf-8")
    proof_path.write_text(format_phase2_no_mutation_md(mutation_proof), encoding="utf-8")
    return payload


def _load_phase2_gate(evidence_dir: Path) -> dict[str, Any] | None:
    """Require Phase 1 authorization when inventory evidence is present (018A §8 Phase 1)."""
    from backend.app.layer1_axes.ingestion_inventory import INVENTORY_JSON_NAME

    inv_path = evidence_dir / INVENTORY_JSON_NAME
    if not inv_path.is_file():
        return None
    inventory = json.loads(inv_path.read_text(encoding="utf-8"))
    gate = inventory.get("phase2_gate") or {}
    if not gate.get("phase2_authorized"):
        raise RuntimeError(
            gate.get("stop_reason")
            or "Phase 2 route preview blocked: phase1 inventory not authorized"
        )
    return gate


def _micro_fetch_to_dict(result: MicroFetchResult) -> dict[str, Any]:
    return {
        "indicator_id": result.indicator_id,
        "as_of": result.as_of.isoformat(),
        "binding": _binding_to_dict(result.binding),
        "route_plan": result.route_plan.to_payload_dict(),
        "fetch_result": result.fetch_result.model_dump(),
        "run_id": result.run_id,
        "job_id": result.job_id,
        "fetch_id": result.fetch_id,
        "file_registry_ids": list(result.file_registry_ids),
        "resource_guard_decision": result.resource_guard_decision,
        "resource_guard_reason": result.resource_guard_reason,
        "staged_fixture_path": result.staged_fixture_path,
        "fred_primary_deferred": True,
        "fred_primary_deferred_note": FRED_PRIMARY_DEFERRED_NOTE,
    }


def format_phase3_no_clean_write_md(proof: dict[str, Any]) -> str:
    lines = [
        "# Phase 3 — No Clean Write Proof",
        "",
        f"- **Generated at:** {proof['generated_at']}",
        f"- **DB path:** `{proof['db_path']}`",
        f"- **axis_observation unchanged:** {proof['axis_observation_unchanged']}",
        f"- **fetch_log delta:** {proof['fetch_log_delta']}",
        f"- **file_registry delta:** {proof['file_registry_delta']}",
        "",
    ]
    lines.extend(_format_count_table_md("Before micro-fetch", proof.get("before_counts", {})))
    lines.extend(_format_count_table_md("After micro-fetch", proof.get("after_counts", {})))
    return "\n".join(lines) + "\n"


def capture_phase3_micro_fetch_evidence(
    *,
    service: Layer1ObservationIngestionService,
    indicator_id: str,
    as_of: date,
    evidence_dir: Path | str,
) -> dict[str, Any]:
    """Run micro-fetch staging and persist Phase 3 evidence artifacts."""
    out = Path(evidence_dir)
    out.mkdir(parents=True, exist_ok=True)
    db_path = service._db_path
    before_counts = service._row_counts(PHASE3_MUTATION_TABLES)
    result = service.micro_fetch_staging(indicator_id=indicator_id, as_of=as_of)
    after_counts = service._row_counts(PHASE3_MUTATION_TABLES)
    before_obs = before_counts.get("axis_observation") or 0
    after_obs = after_counts.get("axis_observation") or 0
    before_fetch = before_counts.get("fetch_log") or 0
    after_fetch = after_counts.get("fetch_log") or 0
    before_files = before_counts.get("file_registry") or 0
    after_files = after_counts.get("file_registry") or 0
    proof = {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "db_path": _relative_path(db_path),
        "axis_observation_unchanged": before_obs == after_obs,
        "fetch_log_delta": after_fetch - before_fetch,
        "file_registry_delta": after_files - before_files,
        "before_counts": before_counts,
        "after_counts": after_counts,
    }
    payload: dict[str, Any] = {
        "phase": "phase3_micro_fetch",
        "generated_at": proof["generated_at"],
        "frozen_indicator": FROZEN_STAGED_INDICATOR,
        "micro_fetch": _micro_fetch_to_dict(result),
        "no_clean_write_proof": proof,
    }
    json_path = out / PHASE3_EVIDENCE_JSON
    md_path = out / PHASE3_NO_CLEAN_WRITE_MD
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_phase3_no_clean_write_md(proof), encoding="utf-8")
    return payload


def capture_task_phase3_evidence(
    evidence_dir: Path | str,
    *,
    as_of: date,
    db_path: Path | str | None = None,
    data_root: Path | str | None = None,
    datasource: DataSourceService | None = None,
) -> dict[str, Any]:
    """Write task execute-evidence for Phase 3 using an isolated fresh sandbox."""
    import shutil

    from backend.app.db.migrate import apply_migrations
    from backend.app.layer1_axes.ingestion_inventory import TARGET_DB_RELATIVE

    out = Path(evidence_dir)
    _load_phase2_gate(out)
    sandbox_base = out / PHASE3_SANDBOX_DIRNAME
    if sandbox_base.exists():
        shutil.rmtree(sandbox_base)
    phase3_db = sandbox_base / TARGET_DB_RELATIVE
    phase3_data_root = sandbox_base / "data"
    phase3_db.parent.mkdir(parents=True, exist_ok=True)
    phase3_data_root.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(phase3_db))
    try:
        apply_migrations(con)
    finally:
        con.close()

    fixture_path = app_config.PROJECT_ROOT / MACRO_FIXTURE_RELATIVE
    resolved_datasource = datasource or build_staged_fixture_service(
        data_root=phase3_data_root,
        fixture_path=fixture_path,
    )
    service = Layer1ObservationIngestionService(
        db_path=phase3_db,
        data_root=phase3_data_root,
        datasource=resolved_datasource,
    )
    payload = capture_phase3_micro_fetch_evidence(
        service=service,
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=as_of,
        evidence_dir=out,
    )
    payload["evidence_baseline_strategy"] = "fresh_phase3_sandbox"
    payload["evidence_data_root"] = _relative_path(phase3_data_root)
    payload["evidence_db_path"] = _relative_path(phase3_db)
    json_path = out / PHASE3_EVIDENCE_JSON
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def capture_task_phase2_evidence(
    evidence_dir: Path | str,
    *,
    as_of: date,
    db_path: Path | str | None = None,
    data_root: Path | str | None = None,
) -> dict[str, Any]:
    """Write task execute-evidence for Phase 2 using project/sandbox targets."""
    from backend.app.db.migrate import apply_migrations
    from backend.app.layer1_axes.ingestion_inventory import (
        INVENTORY_JSON_NAME,
        SANDBOX_BASELINE_DIRNAME,
        TARGET_DB_RELATIVE,
        copy_sandbox_db,
        resolve_phase1_target_paths,
    )

    targets = resolve_phase1_target_paths(data_root=data_root, db_path=db_path)
    out = Path(evidence_dir)
    _load_phase2_gate(out)
    phase2_gate = None
    inv_path = out / INVENTORY_JSON_NAME
    if inv_path.is_file():
        phase2_gate = json.loads(inv_path.read_text(encoding="utf-8")).get("phase2_gate")
    sandbox_db = out / SANDBOX_BASELINE_DIRNAME / TARGET_DB_RELATIVE
    db_capture_strategy = "synthetic_migrated_schema_only"
    baseline_db_relative = _relative_path(sandbox_db)

    if sandbox_db.is_file():
        inspect_db = sandbox_db
        db_capture_strategy = "phase1_sandbox_copy_reused"
    elif targets.target_db_exists:
        sandbox_db.parent.mkdir(parents=True, exist_ok=True)
        copy_sandbox_db(targets.target_db, sandbox_db)
        inspect_db = sandbox_db
        db_capture_strategy = "sandbox_copy_aligned_with_phase1"
    else:
        inspect_db = sandbox_db
        inspect_db.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(str(inspect_db))
        try:
            apply_migrations(con)
        finally:
            con.close()
        db_capture_strategy = "synthetic_migrated_schema_only"

    service = Layer1ObservationIngestionService(
        db_path=inspect_db,
        data_root=targets.data_root,
    )
    return capture_phase2_route_evidence(
        service=service,
        indicators=[FROZEN_STAGED_INDICATOR],
        as_of=as_of,
        evidence_dir=out,
        phase2_gate=phase2_gate,
        db_capture_strategy=db_capture_strategy,
        baseline_db_relative=baseline_db_relative,
    )


def format_phase4_inventory_delta_md(delta: dict[str, Any]) -> str:
    lines = [
        "# Phase 4 — Inventory Delta",
        "",
        f"- **Generated at:** {delta['generated_at']}",
        f"- **DB path:** `{delta['db_path']}`",
        f"- **Frozen indicator:** `{delta['frozen_indicator']}`",
        f"- **Staged fixture:** `{delta.get('staged_fixture_path')}`",
        "",
        "## Row-count deltas",
        "",
        "| table | before | after | delta |",
        "| ----- | ------ | ----- | ----- |",
    ]
    for name, counts in delta.get("table_deltas", {}).items():
        before = counts.get("before")
        after = counts.get("after")
        delta_val = (after or 0) - (before or 0)
        lines.append(f"| `{name}` | {before} | {after} | {delta_val} |")
    lines.append("")
    return "\n".join(lines) + "\n"


def capture_phase4_clean_write_evidence(
    *,
    service: Layer1ObservationIngestionService,
    indicator_id: str,
    as_of: date,
    evidence_dir: Path | str,
    phase1_inventory: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run Phase 4 commit and persist clean-write + snapshot evidence."""
    out = Path(evidence_dir)
    out.mkdir(parents=True, exist_ok=True)
    db_path = service._db_path
    before_counts = service._row_counts(PHASE4_MUTATION_TABLES)
    result = service.commit_clean_observation_and_snapshots(
        indicator_id=indicator_id,
        as_of=as_of,
    )
    after_counts = service._row_counts(PHASE4_MUTATION_TABLES)
    table_deltas = {
        name: {"before": before_counts.get(name), "after": after_counts.get(name)}
        for name in PHASE4_MUTATION_TABLES
    }
    delta_doc = {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "db_path": _relative_path(db_path),
        "frozen_indicator": FROZEN_STAGED_INDICATOR,
        "staged_fixture_path": MACRO_FIXTURE_RELATIVE,
        "fred_primary_deferred": True,
        "table_deltas": table_deltas,
        "phase1_baseline_attached": phase1_inventory is not None,
    }
    payload: dict[str, Any] = {
        "phase": "phase4_clean_write",
        "generated_at": delta_doc["generated_at"],
        "frozen_indicator": FROZEN_STAGED_INDICATOR,
        "commit": {
            "indicator_id": result.indicator_id,
            "as_of": result.as_of.isoformat(),
            "validation_report_id": result.validation_report_id,
            "observation_id": result.observation_id,
            "feature_id": result.feature_id,
            "interpretation_id": result.interpretation_id,
            "lineage_snapshot_id": result.lineage_snapshot_id,
            "source_fetch_ids": list(result.source_fetch_ids),
            "source_content_hashes": list(result.source_content_hashes),
            "observation_write_status": result.observation_write_status,
            "feature_write_status": result.feature_write_status,
            "interpretation_write_status": result.interpretation_write_status,
            "lineage_write_status": result.lineage_write_status,
            "staged_fixture_path": result.staged_fixture_path,
            "fred_primary_deferred_note": FRED_PRIMARY_DEFERRED_NOTE,
        },
        "inventory_delta": delta_doc,
    }
    if phase1_inventory is not None:
        payload["phase1_baseline_classification"] = phase1_inventory.get(
            "db_evidence_classification"
        )
    json_path = out / PHASE4_EVIDENCE_JSON
    md_path = out / PHASE4_INVENTORY_DELTA_MD
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_phase4_inventory_delta_md(delta_doc), encoding="utf-8")
    return payload


def capture_task_phase4_evidence(
    evidence_dir: Path | str,
    *,
    as_of: date,
    db_path: Path | str | None = None,
    data_root: Path | str | None = None,
    datasource: DataSourceService | None = None,
) -> dict[str, Any]:
    """Write task execute-evidence for Phase 4 aligned with Phase 1 sandbox baseline."""
    import shutil

    from backend.app.db.migrate import apply_migrations
    from backend.app.layer1_axes.ingestion_inventory import (
        INVENTORY_JSON_NAME,
        SANDBOX_BASELINE_DIRNAME,
        TARGET_DB_RELATIVE,
        copy_sandbox_db,
        resolve_phase1_target_paths,
    )

    out = Path(evidence_dir)
    _load_phase2_gate(out)
    phase1_inventory = None
    inv_path = out / INVENTORY_JSON_NAME
    if inv_path.is_file():
        phase1_inventory = json.loads(inv_path.read_text(encoding="utf-8"))

    targets = resolve_phase1_target_paths(data_root=data_root, db_path=db_path)
    sandbox_db = out / SANDBOX_BASELINE_DIRNAME / TARGET_DB_RELATIVE
    db_capture_strategy = "synthetic_migrated_schema_only"
    evidence_data_root = targets.data_root

    if sandbox_db.is_file():
        inspect_db = sandbox_db
        db_capture_strategy = "phase1_sandbox_copy_reused"
    elif targets.target_db_exists:
        sandbox_db.parent.mkdir(parents=True, exist_ok=True)
        copy_sandbox_db(targets.target_db, sandbox_db)
        inspect_db = sandbox_db
        db_capture_strategy = "sandbox_copy_aligned_with_phase1"
    else:
        sandbox_base = out / PHASE4_SANDBOX_DIRNAME
        if sandbox_base.exists():
            shutil.rmtree(sandbox_base)
        inspect_db = sandbox_base / TARGET_DB_RELATIVE
        evidence_data_root = sandbox_base / "data"
        inspect_db.parent.mkdir(parents=True, exist_ok=True)
        evidence_data_root.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(str(inspect_db))
        try:
            apply_migrations(con)
        finally:
            con.close()
        db_capture_strategy = "fresh_phase4_sandbox_fallback"

    fixture_path = app_config.PROJECT_ROOT / MACRO_FIXTURE_RELATIVE
    phase4_data_root = out / PHASE4_SANDBOX_DIRNAME / "data"
    phase4_data_root.mkdir(parents=True, exist_ok=True)
    resolved_datasource = datasource or build_staged_fixture_service(
        data_root=phase4_data_root,
        fixture_path=fixture_path,
    )
    service = Layer1ObservationIngestionService(
        db_path=inspect_db,
        data_root=phase4_data_root,
        datasource=resolved_datasource,
    )
    payload = capture_phase4_clean_write_evidence(
        service=service,
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=as_of,
        evidence_dir=out,
        phase1_inventory=phase1_inventory,
    )
    payload["evidence_baseline_strategy"] = db_capture_strategy
    payload["evidence_data_root"] = _relative_path(phase4_data_root)
    payload["evidence_db_path"] = _relative_path(inspect_db)
    payload["phase1_baseline_attached"] = phase1_inventory is not None
    json_path = out / PHASE4_EVIDENCE_JSON
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
