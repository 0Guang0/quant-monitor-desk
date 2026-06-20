-- Migration 011: Layer 1 axis registry, observations, snapshots, and lineage (Round 3 Batch 2).

CREATE TABLE IF NOT EXISTS axis_registry (
    axis_id         VARCHAR PRIMARY KEY,
    axis_name       VARCHAR,
    axis_name_cn    VARCHAR,
    description     TEXT,
    spec_path       VARCHAR,
    updated_at      TIMESTAMP
);

CREATE TABLE IF NOT EXISTS axis_indicator_registry (
    indicator_id        VARCHAR PRIMARY KEY,
    axis_id             VARCHAR,
    indicator_name      VARCHAR,
    display_name_cn     VARCHAR,
    dest_tag            VARCHAR,
    layer_tag           VARCHAR,
    exec_tier           VARCHAR,
    frequency           VARCHAR,
    unit                VARCHAR,
    directionality      VARCHAR,
    primary_source      VARCHAR,
    validation_source   VARCHAR,
    fallback_policy     VARCHAR,
    formula             TEXT,
    allow_score         BOOLEAN,
    diagnostic_only     BOOLEAN,
    is_blindspot        BOOLEAN,
    is_forbidden        BOOLEAN,
    spec_path           VARCHAR,
    is_enabled          BOOLEAN,
    updated_at          TIMESTAMP
);

CREATE TABLE IF NOT EXISTS axis_indicator_profile (
    indicator_id                    VARCHAR PRIMARY KEY,
    axis_id                         VARCHAR,
    display_name_cn                 VARCHAR,
    plain_language_name             VARCHAR,
    plain_language_summary          TEXT,
    physical_meaning_static         TEXT,
    financial_meaning_static        TEXT,
    coverage_scope_static           TEXT,
    penetration_power_static        TEXT,
    boundary_static                 TEXT,
    blind_spot_static               TEXT,
    update_frequency                VARCHAR,
    primary_source                  VARCHAR,
    validation_source               VARCHAR,
    fallback_policy                 VARCHAR,
    display_template                TEXT,
    interpretation_guardrails       TEXT,
    no_action_semantics             BOOLEAN,
    spec_path                       VARCHAR,
    updated_at                      TIMESTAMP
);

CREATE TABLE IF NOT EXISTS axis_observation (
    observation_id      VARCHAR PRIMARY KEY,
    indicator_id        VARCHAR,
    as_of_timestamp     TIMESTAMP,
    publish_timestamp   TIMESTAMP,
    fetch_time          TIMESTAMP,
    raw_value           DOUBLE,
    raw_unit            VARCHAR,
    frequency           VARCHAR,
    source_used         VARCHAR,
    source_channel_id   VARCHAR,
    data_lag_days       DOUBLE,
    stale_reason        VARCHAR,
    quality_flags       VARCHAR,
    content_hash        VARCHAR,
    schema_hash         VARCHAR,
    source_switched     BOOLEAN,
    created_at          TIMESTAMP
);

CREATE TABLE IF NOT EXISTS axis_feature_snapshot (
    feature_id              VARCHAR PRIMARY KEY,
    indicator_id            VARCHAR,
    as_of_timestamp         TIMESTAMP,
    raw_value               DOUBLE,
    z_score                 DOUBLE,
    robust_z_score          DOUBLE,
    percentile_rank         DOUBLE,
    percentile_left_tail    DOUBLE,
    percentile_right_tail   DOUBLE,
    raw_delta_abs           DOUBLE,
    raw_delta_pct           DOUBLE,
    raw_delta_log           DOUBLE,
    z_score_delta           DOUBLE,
    percentile_delta        DOUBLE,
    level_state             VARCHAR,
    delta_state             VARCHAR,
    state_bucket            VARCHAR,
    extreme_flags           VARCHAR,
    standardize_method      VARCHAR,
    delta_method            VARCHAR,
    window_len              INTEGER,
    window_unit             VARCHAR,
    min_obs_required        INTEGER,
    valid_obs_count         INTEGER,
    coverage_ratio          DOUBLE,
    quality_flags           VARCHAR,
    stale_reason            VARCHAR,
    created_at              TIMESTAMP
);

CREATE TABLE IF NOT EXISTS axis_interpretation_snapshot (
    interpretation_id       VARCHAR PRIMARY KEY,
    indicator_id            VARCHAR,
    as_of_timestamp         TIMESTAMP,
    level_label             VARCHAR,
    change_label            VARCHAR,
    quality_label           VARCHAR,
    level_interpretation    TEXT,
    change_interpretation   TEXT,
    boundary_reminder       TEXT,
    warning_level           VARCHAR,
    warning_type            VARCHAR,
    warning_reason_code     VARCHAR,
    summary_sentence        TEXT,
    generated_by            VARCHAR,
    explanation_version     VARCHAR,
    needs_human_review      BOOLEAN,
    created_at              TIMESTAMP
);

CREATE TABLE IF NOT EXISTS axis_snapshot_lineage (
    snapshot_id                 VARCHAR PRIMARY KEY,
    snapshot_type               VARCHAR NOT NULL,
    layer_id                    VARCHAR NOT NULL,
    as_of_timestamp             TIMESTAMP NOT NULL,
    generated_at                TIMESTAMP NOT NULL,
    input_data_window_start     TIMESTAMP NOT NULL,
    input_data_window_end       TIMESTAMP NOT NULL,
    source_dataset_ids          VARCHAR NOT NULL,
    source_fetch_ids            VARCHAR NOT NULL,
    source_content_hashes       VARCHAR NOT NULL,
    rule_version                VARCHAR NOT NULL,
    code_version                VARCHAR NOT NULL,
    parameter_hash              VARCHAR NOT NULL,
    resource_profile            VARCHAR NOT NULL,
    upstream_snapshot_ids       VARCHAR NOT NULL,
    is_incremental              BOOLEAN NOT NULL,
    rebuild_reason              VARCHAR
);
