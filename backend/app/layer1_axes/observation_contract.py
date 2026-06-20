"""axis_observation DDL and WriteManager trace contract (Batch 2.5 Phase 0 gate).

Runtime write path (`Layer1ObservationWriter` / `ingestion.py`) is Phase 4 scope;
this module pins the migration 011 ↔ design-doc column contract for gate tests.
"""

from __future__ import annotations

# Authoritative: migration 011 + docs/modules/layer1_global_regime_panel.md §6.3
AXIS_OBSERVATION_TABLE = "axis_observation"

AXIS_OBSERVATION_DDL_COLUMNS: tuple[str, ...] = (
    "observation_id",
    "indicator_id",
    "as_of_timestamp",
    "publish_timestamp",
    "fetch_time",
    "raw_value",
    "raw_unit",
    "frequency",
    "source_used",
    "source_channel_id",
    "data_lag_days",
    "stale_reason",
    "quality_flags",
    "content_hash",
    "schema_hash",
    "source_switched",
    "created_at",
)

# Non-nullable / business-required fields for DataQualityValidator (nullable DDL cols excluded).
AXIS_OBSERVATION_REQUIRED_FIELDS: tuple[str, ...] = (
    "observation_id",
    "indicator_id",
    "as_of_timestamp",
    "publish_timestamp",
    "fetch_time",
    "raw_value",
    "raw_unit",
    "frequency",
    "source_used",
    "source_channel_id",
    "content_hash",
    "schema_hash",
    "source_switched",
)

# write_contract.yaml required fields for clean observation writes (Phase 4)
WRITE_REQUEST_REQUIRED_FOR_OBSERVATION: tuple[str, ...] = (
    "run_id",
    "job_id",
    "target_table",
    "staging_table",
    "write_mode",
    "data_domain",
    "primary_keys",
    "validation_report_id",
    "source_used",
    "source_role",
)

# 018A §3 trace: fetch_log → validation_report → observation (no fetch_id column on table)
FETCH_TO_OBSERVATION_TRACE_VIA = (
    "validation_report.source_fetch_ids_json",
    "validation_report.source_content_hashes_json",
    "axis_observation.content_hash",
    "axis_observation.source_used",
)
