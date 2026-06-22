"""Layer 2 snapshot lineage builder (staged-only downstream)."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime

from backend.app.layer2_sensors.models import Layer2LineageEnvelope

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

_AGENT_SOURCE_PATTERN = re.compile(
    r"(agent[_-]?summary|generated_by=agent|建议|买入|卖出|信号)",
    re.IGNORECASE,
)


class Layer2LineageError(ValueError):
    """Invalid Layer 2 lineage envelope."""


class Layer2LineageBuilder:
    """Build lineage envelopes for cross_asset_daily_snapshot outputs."""

    def build(
        self,
        *,
        snapshot_id: str,
        snapshot_type: str,
        as_of: datetime,
        input_window_start: datetime,
        input_window_end: datetime,
        source_dataset_ids: tuple[str, ...],
        source_fetch_ids: tuple[str, ...],
        source_content_hashes: tuple[str, ...],
        rule_version: str,
        parameter_hash: str,
        code_version: str = "layer2-staged-v1",
        resource_profile: str = "eco",
        upstream_snapshot_ids: tuple[str, ...] = (),
        is_incremental: bool = False,
        rebuild_reason: str | None = None,
    ) -> Layer2LineageEnvelope:
        _validate_source_dataset_ids(source_dataset_ids)
        if not source_fetch_ids:
            raise Layer2LineageError("source_fetch_ids required for Layer 2 lineage")
        if not source_content_hashes:
            raise Layer2LineageError("source_content_hashes required for Layer 2 lineage")

        envelope = Layer2LineageEnvelope(
            snapshot_id=snapshot_id,
            snapshot_type=snapshot_type,
            layer_id="layer2",
            as_of_timestamp=as_of,
            generated_at=datetime.now(UTC),
            input_data_window_start=input_window_start,
            input_data_window_end=input_window_end,
            source_dataset_ids=source_dataset_ids,
            source_fetch_ids=source_fetch_ids,
            source_content_hashes=source_content_hashes,
            rule_version=rule_version,
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
    def parameter_hash_for(*, rule_version: str, inputs: tuple[str, ...]) -> str:
        payload = "|".join([rule_version, *inputs])
        return hashlib.sha256(payload.encode()).hexdigest()


def lineage_row_to_db_tuple(lineage: Layer2LineageEnvelope) -> list:
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


def _validate_source_dataset_ids(source_dataset_ids: tuple[str, ...]) -> None:
    for ds_id in source_dataset_ids:
        if _AGENT_SOURCE_PATTERN.search(ds_id):
            raise Layer2LineageError(
                f"agent outputs must not appear in source_dataset_ids: {ds_id!r}"
            )


def _assert_lineage_fields_complete(envelope: Layer2LineageEnvelope) -> None:
    optional_nullable = frozenset({"rebuild_reason"})
    for field in LINEAGE_REQUIRED_FIELDS:
        if field in optional_nullable:
            continue
        if getattr(envelope, field) is None:
            raise Layer2LineageError(f"lineage missing required field: {field!r}")
