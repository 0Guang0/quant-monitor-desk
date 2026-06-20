"""Snapshot lineage builder and Layer 1 write integration."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import UTC, datetime

from backend.app.db.connection import ConnectionManager
from backend.app.db.validation_gate import DbValidationGate
from backend.app.db.write_manager import WriteManager, WriteRequest
from backend.app.layer1_axes.models import (
    FeatureSnapshotRow,
    InterpretationSnapshotRow,
    LineageEnvelope,
    ValidationReportRef,
)

LINEAGE_REQUIRED_FIELDS = (
    "snapshot_id",
    "snapshot_type",
    "layer_id",
    "as_of_timestamp",
    "generated_at",
    "input_data_window_start",
    "input_data_window_end",
    "source_dataset_ids",
    "source_fetch_ids",
    "source_content_hashes",
    "rule_version",
    "code_version",
    "parameter_hash",
    "resource_profile",
    "upstream_snapshot_ids",
    "is_incremental",
    "rebuild_reason",
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

_AGENT_SOURCE_PATTERN = re.compile(
    r"(agent[_-]?summary|generated_by=agent|建议|买入|卖出|信号)",
    re.IGNORECASE,
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
        _validate_source_dataset_ids(source_dataset_ids)
        try:
            fetch_ids = tuple(json.loads(validation_report.source_fetch_ids_json or "[]"))
        except json.JSONDecodeError as exc:
            raise LineageSnapshotError(
                f"invalid source_fetch_ids_json for {validation_report.validation_report_id!r}"
            ) from exc
        try:
            content_hashes = tuple(
                json.loads(validation_report.source_content_hashes_json or "[]")
            )
        except json.JSONDecodeError as exc:
            raise LineageSnapshotError(
                f"invalid source_content_hashes_json for {validation_report.validation_report_id!r}"
            ) from exc
        if not content_hashes:
            if not allow_synthetic_hashes and not validation_report.source_content_hashes_json:
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
        _assert_lineage_fields_complete(envelope)
        return envelope

    @staticmethod
    def parameter_hash_for(
        *,
        rule_version: str,
        inputs: tuple[str, ...],
    ) -> str:
        payload = "|".join([rule_version, *inputs])
        return hashlib.sha256(payload.encode()).hexdigest()


def _validate_source_dataset_ids(source_dataset_ids: tuple[str, ...]) -> None:
    """Enforce snapshot_lineage_contract agent_outputs_not_source."""
    for ds_id in source_dataset_ids:
        if _AGENT_SOURCE_PATTERN.search(ds_id):
            raise LineageSnapshotError(
                f"agent outputs must not appear in source_dataset_ids: {ds_id!r}"
            )


def _assert_lineage_fields_complete(envelope: LineageEnvelope) -> None:
    """Single source of truth for lineage completeness (LINEAGE_REQUIRED_FIELDS)."""
    optional_nullable = frozenset({"rebuild_reason"})
    for field in LINEAGE_REQUIRED_FIELDS:
        if field in optional_nullable:
            continue
        if getattr(envelope, field) is None:
            raise LineageSnapshotError(f"lineage missing required field: {field!r}")


def lineage_row_to_db_tuple(lineage: LineageEnvelope) -> list:
    return [
        lineage.snapshot_id,
        lineage.snapshot_type,
        lineage.layer_id,
        lineage.as_of_timestamp,
        lineage.generated_at,
        lineage.input_data_window_start,
        lineage.input_data_window_end,
        json.dumps(list(lineage.source_dataset_ids)),
        json.dumps(list(lineage.source_fetch_ids)),
        json.dumps(list(lineage.source_content_hashes)),
        lineage.rule_version,
        lineage.code_version,
        lineage.parameter_hash,
        lineage.resource_profile,
        json.dumps(list(lineage.upstream_snapshot_ids)),
        lineage.is_incremental,
        lineage.rebuild_reason,
    ]


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
    ):
        _reject_forbidden_substitute_flags(rows)
        staging = f"stg_axis_feature_{uuid.uuid4().hex[:8]}"
        with self._cm.writer() as con:
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
                source_used="layer1_fixture",
                data_domain="layer1_axis_feature",
            )
            return self._wm.write(req, con=con, own_transaction=True)

    def write_lineage(
        self,
        *,
        lineage: LineageEnvelope,
        validation_report_id: str,
        run_id: str = "layer1-run",
        job_id: str = "layer1-job",
    ):
        staging = f"stg_axis_lineage_{uuid.uuid4().hex[:8]}"
        with self._cm.writer() as con:
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
                source_used="layer1_fixture",
                data_domain="layer1_axis_feature",
            )
            return self._wm.write(req, con=con, own_transaction=True)

    def write_interpretation(
        self,
        *,
        rows: list[InterpretationSnapshotRow],
        validation_report_id: str,
        run_id: str = "layer1-run",
        job_id: str = "layer1-job",
    ):
        staging = f"stg_axis_interp_{uuid.uuid4().hex[:8]}"
        with self._cm.writer() as con:
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
                source_used="layer1_fixture",
                data_domain="layer1_axis_feature",
            )
            return self._wm.write(req, con=con, own_transaction=True)


def _reject_forbidden_substitute_flags(rows: list[FeatureSnapshotRow]) -> None:
    for row in rows:
        if "FORBIDDEN_SUBSTITUTE_USED" in row.quality_flags:
            raise LineageSnapshotError(
                f"forbidden substitute blocks write for indicator {row.indicator_id!r}"
            )
