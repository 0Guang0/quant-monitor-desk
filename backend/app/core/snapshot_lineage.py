"""Shared snapshot lineage kernel (SC-01 / L2-01)."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Protocol

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

AGENT_SOURCE_PATTERN = re.compile(
    r"(agent[_-]?summary|generated_by=agent|建议|买入|卖出|信号)",
    re.IGNORECASE,
)

LINEAGE_OPTIONAL_NULLABLE = frozenset({"rebuild_reason"})


class LineageEnvelopeLike(Protocol):
    snapshot_id: str
    snapshot_type: str
    layer_id: str
    as_of_timestamp: Any
    generated_at: Any
    input_data_window_start: Any
    input_data_window_end: Any
    source_dataset_ids: tuple[str, ...]
    source_fetch_ids: tuple[str, ...]
    source_content_hashes: tuple[str, ...]
    rule_version: str
    code_version: str
    parameter_hash: str
    resource_profile: str
    upstream_snapshot_ids: tuple[str, ...]
    is_incremental: bool
    rebuild_reason: str | None


def parameter_hash_for(*, rule_version: str, inputs: tuple[str, ...]) -> str:
    payload = "|".join([rule_version, *inputs])
    return hashlib.sha256(payload.encode()).hexdigest()


def validate_source_dataset_ids(
    source_dataset_ids: tuple[str, ...],
    *,
    error_type: type[Exception] = ValueError,
) -> None:
    """Enforce snapshot_lineage_contract agent_outputs_not_source."""
    for ds_id in source_dataset_ids:
        if AGENT_SOURCE_PATTERN.search(ds_id):
            raise error_type(
                f"agent outputs must not appear in source_dataset_ids: {ds_id!r}"
            )


def assert_lineage_fields_complete(
    envelope: LineageEnvelopeLike,
    *,
    error_type: type[Exception] = ValueError,
) -> None:
    for field in LINEAGE_REQUIRED_FIELDS:
        if field in LINEAGE_OPTIONAL_NULLABLE:
            continue
        if getattr(envelope, field) is None:
            raise error_type(f"lineage missing required field: {field!r}")


def lineage_row_to_db_tuple(lineage: LineageEnvelopeLike) -> list:
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
