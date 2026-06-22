"""Layer 1 Phase 4 clean commit (L1-02/03 ponytail extract)."""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path

import duckdb
from backend.app import config as app_config
from backend.app.core.resource_guard import ResourceGuard
from backend.app.layer1_axes.feature_engine import AxisFeatureEngine, Layer1SnapshotError
from backend.app.layer1_axes.guardrails import (
    AxisEngineeringGuardrailValidator,
    GuardrailViolationError,
)
from backend.app.layer1_axes.ingestion import (
    MACRO_FIXTURE_RELATIVE,
    IngestionCommitBlockedError,
    IngestionCommitResult,
    IngestionRejectedError,
    MicroFetchResult,
    NOT_ON_ALLOWLIST_REJECTED,
    _register_clean_file_registry_rows,
)
from backend.app.layer1_axes.interpretation import AxisInterpretationEngine
from backend.app.layer1_axes.lineage import Layer1SnapshotWriter, SnapshotLineageBuilder
from backend.app.layer1_axes.observation_mapper import (
    ObservationMappingError,
    map_micro_fetch_to_observation_row,
    observation_row_to_domain,
)
from backend.app.layer1_axes.observation_writer import Layer1ObservationWriter
from backend.app.validators.data_quality import DataQualityRequest, DataQualityValidator
from backend.app.validators.source_conflict import SourceConflictRequest, SourceConflictValidator

if False:  # TYPE_CHECKING-style import for service type
    from backend.app.layer1_axes.ingestion import Layer1ObservationIngestionService


def commit_clean_observation_and_snapshots(
    service: "Layer1ObservationIngestionService",
    *,
    indicator_id: str,
    as_of: date,
    run_id: str | None = None,
    job_id: str | None = None,
    fixture_path: Path | str | None = None,
) -> IngestionCommitResult:
    """Validate staged evidence, write clean observation, snapshots, and lineage (Phase 4)."""
    indicator = service._indicator_by_id(indicator_id)
    service._assert_indicator_eligible(indicator)
    service._assert_allowlisted(indicator_id)

    resolved_run_id = run_id or f"layer1-commit-{indicator_id}"
    resolved_job_id = job_id or f"layer1-commit-{indicator_id}"
    binding, req, route_plan, resolved_run_id, resolved_job_id = (
        service._prepare_staged_route_and_request(
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
    obs_writer = Layer1ObservationWriter(service._conn_manager)
    snapshot_writer = Layer1SnapshotWriter(service._conn_manager)

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

    with service._conn_manager.writer() as con:
        con.execute("BEGIN")
        try:
            normalized_fetch, fetch_id, _, guard_decision, guard_reason = (
                service._fetch_staging_on_connection(
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
                    data_root=service._data_root,
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
                service._load_axes().guardrails
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

            if service._validation_source_requires_conflict(indicator):
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
                    conn_manager=service._conn_manager,
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
            interp_engine = AxisInterpretationEngine()
            for interp_row in interp_rows:
                try:
                    interp_engine.reject_if_forbidden(interp_row.summary_sentence)
                except Exception as exc:
                    raise IngestionCommitBlockedError(
                        str(exc), reason_code="FORBIDDEN_INTERPRETATION"
                    ) from exc

            report_ref = service._load_validation_report_ref(
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
        staged_fixture_path=_relative_to_project(resolved_fixture),
    )


def _relative_to_project(path: Path) -> str:
    from backend.app.layer1_axes.ingestion_inventory import _relative_to_project

    return _relative_to_project(path)
