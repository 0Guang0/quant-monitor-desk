"""Layer 4 snapshot lineage builder (staged-only downstream)."""

from __future__ import annotations

from datetime import UTC, datetime

from backend.app.core.snapshot_lineage import (
    assert_lineage_fields_complete,
    parameter_hash_for,
    validate_source_dataset_ids,
)
from backend.app.layer4_markets.models import Layer4LineageEnvelope


class Layer4LineageError(ValueError):
    """Invalid Layer 4 lineage envelope."""


class Layer4LineageBuilder:
    """Build lineage envelopes for market_breadth_snapshot outputs."""

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
        code_version: str = "layer4-staged-v1",
        resource_profile: str = "eco",
        upstream_snapshot_ids: tuple[str, ...] = (),
        is_incremental: bool = False,
        rebuild_reason: str | None = None,
    ) -> Layer4LineageEnvelope:
        validate_source_dataset_ids(source_dataset_ids, error_type=Layer4LineageError)
        if not source_fetch_ids:
            raise Layer4LineageError("source_fetch_ids required for Layer 4 lineage")
        if not source_content_hashes:
            raise Layer4LineageError("source_content_hashes required for Layer 4 lineage")

        envelope = Layer4LineageEnvelope(
            snapshot_id=snapshot_id,
            snapshot_type=snapshot_type,
            layer_id="layer4",
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
        assert_lineage_fields_complete(envelope, error_type=Layer4LineageError)
        return envelope

    parameter_hash_for = staticmethod(parameter_hash_for)
