"""Layer 1 axis domain models (Round 3 Batch 2)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AxisDefinition:
    axis_id: str
    axis_name: str
    axis_name_cn: str
    description: str
    spec_path: str


@dataclass(frozen=True)
class AxisIndicatorDefinition:
    indicator_id: str
    axis_id: str
    indicator_name: str
    display_name_cn: str
    dest_tag: str
    layer_tag: str
    exec_tier: str
    frequency: str
    unit: str
    directionality: str
    primary_source: str
    validation_source: str
    fallback_policy: str
    formula: str
    allow_score: bool
    diagnostic_only: bool
    is_blindspot: bool
    is_forbidden: bool
    is_shadow: bool
    is_observable: bool
    module: str
    quality_rules: tuple[str, ...]
    stale_rules: tuple[str, ...]
    forbidden_substitutes: tuple[str, ...]
    spec_path: str
    role_notes: str = ""
    is_enabled: bool = True


@dataclass(frozen=True)
class AxisIndicatorProfile:
    indicator_id: str
    axis_id: str
    display_name_cn: str
    plain_language_name: str
    plain_language_summary: str
    physical_meaning_static: str
    financial_meaning_static: str
    coverage_scope_static: str
    penetration_power_static: str
    boundary_static: str
    blind_spot_static: str
    update_frequency: str
    primary_source: str
    validation_source: str
    fallback_policy: str
    display_template: str
    interpretation_guardrails: str
    no_action_semantics: bool
    spec_path: str


@dataclass(frozen=True)
class AxisEngineeringGuardrail:
    axis_id: str
    forbidden_terms: tuple[str, ...]
    engineering_rules_path: str


@dataclass(frozen=True)
class AxisLoadResult:
    axes: tuple[AxisDefinition, ...]
    indicators: tuple[AxisIndicatorDefinition, ...]
    profiles: tuple[AxisIndicatorProfile, ...]
    guardrails: tuple[AxisEngineeringGuardrail, ...]


@dataclass(frozen=True)
class AxisObservation:
    indicator_id: str
    as_of_timestamp: datetime
    publish_timestamp: datetime
    raw_value: float | None
    source_used: str
    source_switched: bool = False
    fallback_policy: str | None = None
    quality_flags: tuple[str, ...] = ()


@dataclass(frozen=True)
class FeatureSnapshotRow:
    feature_id: str
    indicator_id: str
    as_of_timestamp: datetime
    raw_value: float | None
    z_score: float | None
    robust_z_score: float | None
    percentile_rank: float | None
    percentile_left_tail: float | None
    percentile_right_tail: float | None
    raw_delta_abs: float | None
    raw_delta_pct: float | None
    raw_delta_log: float | None
    z_score_delta: float | None
    percentile_delta: float | None
    level_state: str | None
    delta_state: str | None
    state_bucket: str
    extreme_flags: str
    standardize_method: str
    delta_method: str
    window_len: int
    window_unit: str
    min_obs_required: int
    valid_obs_count: int
    coverage_ratio: float
    quality_flags: tuple[str, ...]
    stale_reason: str | None = None


@dataclass(frozen=True)
class InterpretationSnapshotRow:
    interpretation_id: str
    indicator_id: str
    as_of_timestamp: datetime
    level_label: str
    change_label: str
    quality_label: str
    level_interpretation: str
    change_interpretation: str
    boundary_reminder: str
    warning_level: str
    warning_type: str
    warning_reason_code: str
    summary_sentence: str
    generated_by: str
    explanation_version: str
    needs_human_review: bool


@dataclass(frozen=True)
class LineageEnvelope:
    snapshot_id: str
    snapshot_type: str
    layer_id: str
    as_of_timestamp: datetime
    generated_at: datetime
    input_data_window_start: datetime
    input_data_window_end: datetime
    source_dataset_ids: tuple[str, ...]
    source_fetch_ids: tuple[str, ...]
    source_content_hashes: tuple[str, ...]
    rule_version: str
    code_version: str
    parameter_hash: str
    resource_profile: str
    upstream_snapshot_ids: tuple[str, ...]
    is_incremental: bool
    rebuild_reason: str | None = None


@dataclass(frozen=True)
class ValidationReportRef:
    validation_report_id: str
    rule_version: str
    source_fetch_ids_json: str
    source_content_hashes_json: str
