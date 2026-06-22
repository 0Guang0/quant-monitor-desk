"""Layer 5 snapshot lineage builder (023A foundation; read-only contract compat)."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime

from backend.app.layer5_evidence.models import SourceProvenance

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


class Layer5LineageError(ValueError):
    """Invalid Layer 5 lineage envelope."""


class Layer5LineageEnvelope:
    """Lineage envelope aligned with ``snapshot_lineage_contract.yaml`` field set."""

    __slots__ = LINEAGE_REQUIRED_FIELDS

    def __init__(
        self,
        *,
        snapshot_id: str,
        snapshot_type: str,
        layer_id: str,
        as_of_timestamp: datetime,
        generated_at: datetime,
        input_data_window_start: datetime,
        input_data_window_end: datetime,
        source_dataset_ids: tuple[str, ...],
        source_fetch_ids: tuple[str, ...],
        source_content_hashes: tuple[str, ...],
        rule_version: str,
        code_version: str,
        parameter_hash: str,
        resource_profile: str,
        upstream_snapshot_ids: tuple[str, ...],
        is_incremental: bool,
        rebuild_reason: str | None = None,
    ) -> None:
        self.snapshot_id = snapshot_id
        self.snapshot_type = snapshot_type
        self.layer_id = layer_id
        self.as_of_timestamp = as_of_timestamp
        self.generated_at = generated_at
        self.input_data_window_start = input_data_window_start
        self.input_data_window_end = input_data_window_end
        self.source_dataset_ids = source_dataset_ids
        self.source_fetch_ids = source_fetch_ids
        self.source_content_hashes = source_content_hashes
        self.rule_version = rule_version
        self.code_version = code_version
        self.parameter_hash = parameter_hash
        self.resource_profile = resource_profile
        self.upstream_snapshot_ids = upstream_snapshot_ids
        self.is_incremental = is_incremental
        self.rebuild_reason = rebuild_reason


class Layer5LineageBuilder:
    """Build lineage envelopes for Layer5 foundation snapshots."""

    def build(
        self,
        *,
        snapshot_id: str,
        snapshot_type: str,
        as_of: datetime,
        input_window_start: datetime,
        input_window_end: datetime,
        provenance: SourceProvenance,
        rule_version: str,
        parameter_hash: str,
        code_version: str = "layer5-foundation-v1",
        resource_profile: str = "eco",
        upstream_snapshot_ids: tuple[str, ...] = (),
        is_incremental: bool = False,
        rebuild_reason: str | None = None,
    ) -> Layer5LineageEnvelope:
        _validate_source_dataset_ids(provenance.source_dataset_ids)
        if not provenance.source_fetch_ids:
            raise Layer5LineageError("source_fetch_ids required for Layer 5 lineage")
        if not provenance.source_content_hashes:
            raise Layer5LineageError("source_content_hashes required for Layer 5 lineage")
        if as_of > input_window_end:
            raise Layer5LineageError("as_of_timestamp must not exceed input_data_window_end")

        envelope = Layer5LineageEnvelope(
            snapshot_id=snapshot_id,
            snapshot_type=snapshot_type,
            layer_id="layer5",
            as_of_timestamp=as_of,
            generated_at=datetime.now(UTC),
            input_data_window_start=input_window_start,
            input_data_window_end=input_window_end,
            source_dataset_ids=provenance.source_dataset_ids,
            source_fetch_ids=provenance.source_fetch_ids,
            source_content_hashes=provenance.source_content_hashes,
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


def lineage_row_to_db_tuple(lineage: Layer5LineageEnvelope) -> list:
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
            raise Layer5LineageError(
                f"agent outputs must not appear in source_dataset_ids: {ds_id!r}"
            )


def _assert_lineage_fields_complete(envelope: Layer5LineageEnvelope) -> None:
    optional_nullable = frozenset({"rebuild_reason"})
    for field in LINEAGE_REQUIRED_FIELDS:
        if field in optional_nullable:
            continue
        if getattr(envelope, field) is None:
            raise Layer5LineageError(f"lineage missing required field: {field!r}")
