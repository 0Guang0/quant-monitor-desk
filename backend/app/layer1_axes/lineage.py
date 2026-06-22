"""Snapshot lineage builder and Layer 1 write integration."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime

import duckdb
from backend.app.core.snapshot_lineage import (
    LINEAGE_REQUIRED_FIELDS,
    assert_lineage_fields_complete,
    lineage_row_to_db_tuple,
    parameter_hash_for,
    validate_source_dataset_ids,
)
from backend.app.db.connection import ConnectionManager
from backend.app.db.validation_gate import DbValidationGate
from backend.app.db.write_manager import WriteManager, WriteRequest
from backend.app.layer1_axes.models import (
    FeatureSnapshotRow,
    InterpretationSnapshotRow,
    LineageEnvelope,
    ValidationReportRef,
)

LAYER1_TABLES = frozenset(
    {
        "axis_registry",
        "axis_indicator_registry",
        "axis_indicator_profile",
        "axis_observation",
        "axis_feature_snapshot",
        "axis_interpretation_snapshot",
        "axis_snapshot_lineage",
    }
)

class LineageSnapshotError(ValueError):
    """Invalid lineage envelope or write inputs."""


class Layer2WritebackError(ValueError):
    """Layer 2 values must not write back to Layer 1 tables."""


def guard_layer2_writeback(*, target_table: str, layer_id: str) -> None:
    if layer_id == "layer2" and target_table in LAYER1_TABLES:
        raise Layer2WritebackError(
            f"layer2 writeback to layer1 table {target_table!r} is forbidden"
        )


class SnapshotLineageBuilder:
    """Build lineage envelopes consumable by axis_snapshot_lineage."""

    def build(
        self,
        *,
        snapshot_id: str,
        snapshot_type: str,
        as_of: datetime,
        validation_report: ValidationReportRef,
        input_window_start: datetime,
        input_window_end: datetime,
        source_dataset_ids: tuple[str, ...],
        parameter_hash: str,
        code_version: str = "layer1-v1",
        resource_profile: str = "eco",
        upstream_snapshot_ids: tuple[str, ...] = (),
        is_incremental: bool = False,
        rebuild_reason: str | None = None,
        allow_synthetic_hashes: bool = False,
    ) -> LineageEnvelope:
        validate_source_dataset_ids(source_dataset_ids, error_type=LineageSnapshotError)
        try:
            fetch_ids = tuple(json.loads(validation_report.source_fetch_ids_json or "[]"))
        except json.JSONDecodeError as exc:
            raise LineageSnapshotError(
                f"invalid source_fetch_ids_json for {validation_report.validation_report_id!r}"
            ) from exc
        try:
            content_hashes = tuple(json.loads(validation_report.source_content_hashes_json or "[]"))
        except json.JSONDecodeError as exc:
            raise LineageSnapshotError(
                f"invalid source_content_hashes_json for {validation_report.validation_report_id!r}"
            ) from exc
        if not content_hashes:
            if not allow_synthetic_hashes:
                raise LineageSnapshotError(
                    "source_content_hashes required from validation_report for production lineage"
                )
            content_hashes = tuple(
                hashlib.sha256(ds.encode()).hexdigest() for ds in source_dataset_ids
            )
        envelope = LineageEnvelope(
            snapshot_id=snapshot_id,
            snapshot_type=snapshot_type,
            layer_id="layer1",
            as_of_timestamp=as_of,
            generated_at=datetime.now(UTC),
            input_data_window_start=input_window_start,
            input_data_window_end=input_window_end,
            source_dataset_ids=source_dataset_ids,
            source_fetch_ids=fetch_ids,
            source_content_hashes=content_hashes,
            rule_version=validation_report.rule_version,
            code_version=code_version,
            parameter_hash=parameter_hash,
            resource_profile=resource_profile,
            upstream_snapshot_ids=upstream_snapshot_ids,
            is_incremental=is_incremental,
            rebuild_reason=rebuild_reason,
        )
        assert_lineage_fields_complete(envelope, error_type=LineageSnapshotError)
        return envelope

    parameter_hash_for = staticmethod(parameter_hash_for)


def feature_row_to_db_tuple(row: FeatureSnapshotRow) -> list:
    return [
        row.feature_id,
        row.indicator_id,
        row.as_of_timestamp,
        row.raw_value,
        row.z_score,
        row.robust_z_score,
        row.percentile_rank,
        row.percentile_left_tail,
        row.percentile_right_tail,
        row.raw_delta_abs,
        row.raw_delta_pct,
        row.raw_delta_log,
        row.z_score_delta,
        row.percentile_delta,
        row.level_state,
        row.delta_state,
        row.state_bucket,
        row.extreme_flags,
        row.standardize_method,
        row.delta_method,
        row.window_len,
        row.window_unit,
        row.min_obs_required,
        row.valid_obs_count,
        row.coverage_ratio,
        ",".join(row.quality_flags),
        row.stale_reason,
        datetime.now(UTC),
    ]


def interpretation_row_to_db_tuple(row: InterpretationSnapshotRow) -> list:
    return [
        row.interpretation_id,
        row.indicator_id,
        row.as_of_timestamp,
        row.level_label,
        row.change_label,
        row.quality_label,
        row.level_interpretation,
        row.change_interpretation,
        row.boundary_reminder,
        row.warning_level,
        row.warning_type,
        row.warning_reason_code,
        row.summary_sentence,
        row.generated_by,
        row.explanation_version,
        row.needs_human_review,
        datetime.now(UTC),
    ]


class Layer1SnapshotWriter:
    """Write Layer 1 snapshots via staging → DbValidationGate → WriteManager."""

    def __init__(self, conn_manager: ConnectionManager) -> None:
        self._cm = conn_manager
        self._wm = WriteManager(conn_manager, DbValidationGate(conn_manager))

    def write_features(
        self,
        *,
        rows: list[FeatureSnapshotRow],
        validation_report_id: str,
        run_id: str = "layer1-run",
        job_id: str = "layer1-job",
        source_used: str = "layer1_fixture",
        data_domain: str = "layer1_axis_feature",
        con: duckdb.DuckDBPyConnection | None = None,
        own_transaction: bool = True,
    ):
        _reject_forbidden_substitute_flags(rows)
        if con is None:
            with self._cm.writer() as writer_con:
                return self._write_features_on_connection(
                    writer_con,
                    rows=rows,
                    validation_report_id=validation_report_id,
                    run_id=run_id,
                    job_id=job_id,
                    source_used=source_used,
                    data_domain=data_domain,
                    own_transaction=own_transaction,
                )
        return self._write_features_on_connection(
            con,
            rows=rows,
            validation_report_id=validation_report_id,
            run_id=run_id,
            job_id=job_id,
            source_used=source_used,
            data_domain=data_domain,
            own_transaction=own_transaction,
        )

    def _write_features_on_connection(
        self,
        con: duckdb.DuckDBPyConnection,
        *,
        rows: list[FeatureSnapshotRow],
        validation_report_id: str,
        run_id: str,
        job_id: str,
        source_used: str,
        data_domain: str,
        own_transaction: bool,
    ):
        staging = f"stg_axis_feature_{uuid.uuid4().hex[:8]}"
        con.execute(f"CREATE TABLE {staging} AS SELECT * FROM axis_feature_snapshot WHERE 1=0")
        for row in rows:
            con.execute(
                f"""
                INSERT INTO {staging} VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                feature_row_to_db_tuple(row),
            )
        req = WriteRequest(
            run_id=run_id,
            job_id=job_id,
            target_table="axis_feature_snapshot",
            staging_table=staging,
            write_mode="append_only",
            primary_keys=("feature_id",),
            validation_report_id=validation_report_id,
            source_used=source_used,
            data_domain=data_domain,
        )
        return self._wm.write(req, con=con, own_transaction=own_transaction)

    def write_lineage(
        self,
        *,
        lineage: LineageEnvelope,
        validation_report_id: str,
        run_id: str = "layer1-run",
        job_id: str = "layer1-job",
        source_used: str = "layer1_fixture",
        data_domain: str = "layer1_axis_feature",
        con: duckdb.DuckDBPyConnection | None = None,
        own_transaction: bool = True,
    ):
        if con is None:
            with self._cm.writer() as writer_con:
                return self._write_lineage_on_connection(
                    writer_con,
                    lineage=lineage,
                    validation_report_id=validation_report_id,
                    run_id=run_id,
                    job_id=job_id,
                    source_used=source_used,
                    data_domain=data_domain,
                    own_transaction=own_transaction,
                )
        return self._write_lineage_on_connection(
            con,
            lineage=lineage,
            validation_report_id=validation_report_id,
            run_id=run_id,
            job_id=job_id,
            source_used=source_used,
            data_domain=data_domain,
            own_transaction=own_transaction,
        )

    def _write_lineage_on_connection(
        self,
        con: duckdb.DuckDBPyConnection,
        *,
        lineage: LineageEnvelope,
        validation_report_id: str,
        run_id: str,
        job_id: str,
        source_used: str,
        data_domain: str,
        own_transaction: bool,
    ):
        staging = f"stg_axis_lineage_{uuid.uuid4().hex[:8]}"
        con.execute(f"CREATE TABLE {staging} AS SELECT * FROM axis_snapshot_lineage WHERE 1=0")
        con.execute(
            f"""
            INSERT INTO {staging} VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            lineage_row_to_db_tuple(lineage),
        )
        req = WriteRequest(
            run_id=run_id,
            job_id=job_id,
            target_table="axis_snapshot_lineage",
            staging_table=staging,
            write_mode="upsert_by_pk",
            primary_keys=("snapshot_id",),
            validation_report_id=validation_report_id,
            source_used=source_used,
            data_domain=data_domain,
        )
        return self._wm.write(req, con=con, own_transaction=own_transaction)

    def write_interpretation(
        self,
        *,
        rows: list[InterpretationSnapshotRow],
        validation_report_id: str,
        run_id: str = "layer1-run",
        job_id: str = "layer1-job",
        source_used: str = "layer1_fixture",
        data_domain: str = "layer1_axis_interpretation",
        con: duckdb.DuckDBPyConnection | None = None,
        own_transaction: bool = True,
    ):
        if con is None:
            with self._cm.writer() as writer_con:
                return self._write_interpretation_on_connection(
                    writer_con,
                    rows=rows,
                    validation_report_id=validation_report_id,
                    run_id=run_id,
                    job_id=job_id,
                    source_used=source_used,
                    data_domain=data_domain,
                    own_transaction=own_transaction,
                )
        return self._write_interpretation_on_connection(
            con,
            rows=rows,
            validation_report_id=validation_report_id,
            run_id=run_id,
            job_id=job_id,
            source_used=source_used,
            data_domain=data_domain,
            own_transaction=own_transaction,
        )

    def _write_interpretation_on_connection(
        self,
        con: duckdb.DuckDBPyConnection,
        *,
        rows: list[InterpretationSnapshotRow],
        validation_report_id: str,
        run_id: str,
        job_id: str,
        source_used: str,
        data_domain: str,
        own_transaction: bool,
    ):
        staging = f"stg_axis_interp_{uuid.uuid4().hex[:8]}"
        con.execute(
            f"CREATE TABLE {staging} AS SELECT * FROM axis_interpretation_snapshot WHERE 1=0"
        )
        for row in rows:
            con.execute(
                f"""
                INSERT INTO {staging} VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                interpretation_row_to_db_tuple(row),
            )
        req = WriteRequest(
            run_id=run_id,
            job_id=job_id,
            target_table="axis_interpretation_snapshot",
            staging_table=staging,
            write_mode="append_only",
            primary_keys=("interpretation_id",),
            validation_report_id=validation_report_id,
            source_used=source_used,
            data_domain=data_domain,
        )
        return self._wm.write(req, con=con, own_transaction=own_transaction)


def _reject_forbidden_substitute_flags(rows: list[FeatureSnapshotRow]) -> None:
    for row in rows:
        if "FORBIDDEN_SUBSTITUTE_USED" in row.quality_flags:
            raise LineageSnapshotError(
                f"forbidden substitute blocks write for indicator {row.indicator_id!r}"
            )
