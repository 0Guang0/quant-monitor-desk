"""Layer 5 snapshot lineage builder (023A foundation; read-only contract compat)."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.app.core.snapshot_lineage import (
    LINEAGE_REQUIRED_FIELDS,
    assert_lineage_fields_complete,
    lineage_row_to_db_tuple,
    parameter_hash_for,
    validate_source_dataset_ids,
)
from backend.app.layer5_evidence.models import SourceProvenance


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
        validate_source_dataset_ids(provenance.source_dataset_ids, error_type=Layer5LineageError)
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
        assert_lineage_fields_complete(envelope, error_type=Layer5LineageError)
        return envelope

    parameter_hash_for = staticmethod(parameter_hash_for)
