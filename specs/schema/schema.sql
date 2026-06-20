-- Quant Monitor Schema Draft - P0 Round 1
-- 本文件是 schema 契约 v1；后续模块扩展后继续合并 Layer 1/2/3/4/5 专用表。

CREATE TABLE IF NOT EXISTS schema_version (
    version_id          VARCHAR PRIMARY KEY,
    applied_at          TIMESTAMP,
    migration_file      VARCHAR,
    checksum            VARCHAR,
    applied_by          VARCHAR,
    notes               TEXT
);

CREATE TABLE IF NOT EXISTS source_registry (
    source_id              VARCHAR PRIMARY KEY,
    source_name            VARCHAR,
    source_type            VARCHAR CHECK (
        source_type IS NULL OR source_type IN (
            'broker_terminal', 'public_market_data', 'aggregator', 'filing_announcement',
            'official_api', 'local_sdk', 'vendor_api'
        )
    ),
    allowed_domain         VARCHAR,
    allowed_domains_json   VARCHAR,
    trust_level            INTEGER,
    license_type           VARCHAR CHECK (
        license_type IS NULL OR license_type IN (
            'user_local_authorized', 'public_free', 'public_free_aggregator',
            'public_official', 'public_terms_sensitive',
            'official_free', 'local_authorized', 'public_web'
        )
    ),
    official_api           BOOLEAN,
    is_enabled             BOOLEAN,
    default_priority       INTEGER,
    rate_limit_policy      VARCHAR,
    auth_required          BOOLEAN,
    requires_local_client  BOOLEAN,
    expected_frequency     VARCHAR,
    expected_lag           VARCHAR,
    timezone               VARCHAR,
    fallback_allowed       BOOLEAN,
    validation_only        BOOLEAN,
    notes                  TEXT,
    updated_at             TIMESTAMP
);

CREATE TABLE IF NOT EXISTS file_registry (
    file_id             VARCHAR PRIMARY KEY,
    file_type           VARCHAR,
    source              VARCHAR,
    source_url          VARCHAR,
    local_path          VARCHAR,
    content_hash        VARCHAR,
    schema_hash         VARCHAR,
    fetch_time          TIMESTAMP,
    as_of_timestamp     TIMESTAMP,
    parse_status        VARCHAR,
    quality_flag        VARCHAR
);

CREATE TABLE IF NOT EXISTS data_sync_job (
    job_id              VARCHAR PRIMARY KEY,
    run_id              VARCHAR,
    job_type            VARCHAR,
    data_domain         VARCHAR,
    market_id           VARCHAR,
    instrument_id       VARCHAR,
    partition_key       VARCHAR,
    date_start          DATE,
    date_end            DATE,
    source_id           VARCHAR,
    adapter_id          VARCHAR,
    status              VARCHAR CHECK (
        status IS NULL OR status IN (
            'CREATED', 'PLANNED', 'FETCHING', 'STAGED', 'VALIDATING',
            'WAITING_RECONCILE', 'RECONCILING', 'READY_TO_WRITE', 'WRITING',
            'COMPLETED', 'FAILED_FINAL', 'SKIPPED', 'CANCELLED',
            'MANUAL_REVIEW_REQUIRED', 'FAILED_RETRYABLE'
        )
    ),
    priority            INTEGER,
    retry_count         INTEGER,
    max_retries         INTEGER,
    cursor_before       VARCHAR,
    cursor_after        VARCHAR,
    validation_report_id VARCHAR,
    conflict_report_id  VARCHAR,
    write_id            VARCHAR,
    error_type          VARCHAR,
    error_message       TEXT,
    created_at          TIMESTAMP,
    started_at          TIMESTAMP,
    finished_at         TIMESTAMP,
    updated_at          TIMESTAMP
);

CREATE TABLE IF NOT EXISTS job_event_log (
    event_id        VARCHAR PRIMARY KEY,
    run_id          VARCHAR,
    job_id          VARCHAR,
    task_id         VARCHAR,
    event_type      VARCHAR,
    old_status      VARCHAR,
    new_status      VARCHAR,
    message         TEXT,
    payload_json    TEXT,
    created_at      TIMESTAMP
);

CREATE TABLE IF NOT EXISTS validation_report (
    validation_report_id    VARCHAR PRIMARY KEY,
    run_id                  VARCHAR,
    job_id                  VARCHAR,
    data_domain             VARCHAR,
    staging_table           VARCHAR,
    source_id               VARCHAR,
    status                  VARCHAR,
    checked_rows            INTEGER,
    failed_rows             INTEGER,
    warning_rows            INTEGER,
    quality_flags           VARCHAR,
    stale_reason            VARCHAR,
    can_write_clean         BOOLEAN,
    needs_manual_review     BOOLEAN,
    rule_set_id             VARCHAR NOT NULL,
    rule_version            VARCHAR NOT NULL,
    source_fetch_ids_json   VARCHAR,
    source_content_hashes_json VARCHAR,
    created_at              TIMESTAMP
);

CREATE TABLE IF NOT EXISTS data_quality_log (
    log_id              VARCHAR PRIMARY KEY,
    validation_report_id VARCHAR,
    run_id              VARCHAR,
    job_id              VARCHAR,
    data_domain         VARCHAR,
    source_id           VARCHAR,
    table_name          VARCHAR,
    row_key             VARCHAR,
    field_name          VARCHAR,
    rule_id             VARCHAR,
    severity            VARCHAR,
    observed_value      VARCHAR,
    expected_condition  VARCHAR,
    message             TEXT,
    rule_version        VARCHAR,
    created_at          TIMESTAMP
);

CREATE TABLE IF NOT EXISTS source_conflict (
    conflict_id             VARCHAR PRIMARY KEY,
    run_id                  VARCHAR,
    job_id                  VARCHAR,
    data_domain             VARCHAR,
    market_id               VARCHAR,
    instrument_id           VARCHAR,
    field_name              VARCHAR,
    as_of_timestamp         TIMESTAMP,
    primary_source          VARCHAR,
    primary_value           VARCHAR,
    competing_source        VARCHAR,
    competing_value         VARCHAR,
    normalized_diff         DOUBLE,
    tolerance_warning       DOUBLE,
    tolerance_severe        DOUBLE,
    tolerance_rule_set_id   VARCHAR,
    rule_version            VARCHAR,
    severity                VARCHAR NOT NULL CHECK (severity IN ('warning', 'severe')),
    reconcile_status        VARCHAR CHECK (
        reconcile_status IS NULL OR reconcile_status IN (
            'OPEN', 'N/A', 'UNRESOLVED', 'RESOLVED_BY_REFETCH',
            'RESOLVED_MANUAL', 'CLOSED'
        )
    ),
    manual_review_required  BOOLEAN,
    resolution              VARCHAR,
    resolution_note         TEXT,
    created_at              TIMESTAMP,
    resolved_at             TIMESTAMP
);

CREATE TABLE IF NOT EXISTS write_audit_log (
    write_id            VARCHAR PRIMARY KEY,
    run_id              VARCHAR,
    job_id              VARCHAR,
    target_table        VARCHAR,
    staging_table       VARCHAR,
    write_mode          VARCHAR,
    primary_keys        VARCHAR,
    partition_keys      VARCHAR,
    rows_in_staging     INTEGER,
    rows_inserted       INTEGER,
    rows_updated        INTEGER,
    rows_deleted        INTEGER,
    rows_rejected       INTEGER,
    validation_status   VARCHAR,
    conflict_status     VARCHAR,
    source_used         VARCHAR,
    source_role         VARCHAR,
    source_switched     BOOLEAN,
    stale_reason        VARCHAR,
    started_at          TIMESTAMP,
    finished_at         TIMESTAMP,
    status              VARCHAR,
    error_message       TEXT,
    traceback_digest    VARCHAR,
    data_domain          VARCHAR,
    conflict_report_id   VARCHAR,
    requested_by         VARCHAR,
    allow_partial_write  BOOLEAN
);

CREATE TABLE IF NOT EXISTS resource_guard_log (
    event_id        VARCHAR PRIMARY KEY,
    decision        VARCHAR,
    reason          VARCHAR,
    profile         VARCHAR,
    available_memory_gb DOUBLE,
    disk_free_gb    DOUBLE,
    process_rss_mb  DOUBLE,
    project_size_gb DOUBLE,
    created_at      TIMESTAMP,
    system_memory_usage_pct DOUBLE,
    system_disk_usage_pct DOUBLE,
    cache_size_gb DOUBLE,
    duckdb_temp_size_gb DOUBLE
);

CREATE TABLE IF NOT EXISTS stg_foundation_smoke (
    instrument_id   VARCHAR,
    trade_date      DATE,
    close           DOUBLE,
    source_used     VARCHAR,
    batch_id        VARCHAR,
    PRIMARY KEY (instrument_id, trade_date)
);

CREATE TABLE IF NOT EXISTS stg_file_registry (
    file_id         VARCHAR,
    file_type       VARCHAR,
    source          VARCHAR,
    source_url      VARCHAR,
    local_path      VARCHAR,
    content_hash    VARCHAR,
    schema_hash     VARCHAR,
    fetch_time      TIMESTAMP,
    as_of_timestamp TIMESTAMP,
    parse_status    VARCHAR,
    quality_flag    VARCHAR
);

CREATE TABLE IF NOT EXISTS fetch_log (
    fetch_id            VARCHAR PRIMARY KEY,
    run_id              VARCHAR,
    job_id              VARCHAR,
    source_id           VARCHAR,
    data_domain         VARCHAR,
    market_id           VARCHAR,
    instrument_id       VARCHAR,
    request_params_hash VARCHAR,
    status              VARCHAR CHECK (
        status IS NULL OR status IN (
            'SUCCESS', 'EMPTY_RESPONSE', 'NOT_PUBLISHED_YET', 'DISABLED_SOURCE',
            'AUTH_FAILED', 'RATE_LIMITED', 'NETWORK_ERROR', 'SCHEMA_DRIFT', 'FAILED'
        )
    ),
    row_count           INTEGER,
    raw_file_paths      VARCHAR,
    content_hash        VARCHAR,
    schema_hash         VARCHAR,
    as_of_timestamp     TIMESTAMP,
    publish_timestamp   TIMESTAMP,
    fetch_time          TIMESTAMP,
    latency_ms          INTEGER,
    retry_count         INTEGER,
    error_type          VARCHAR,
    error_message       TEXT
);

CREATE TABLE IF NOT EXISTS manual_review_queue (
    review_id           VARCHAR PRIMARY KEY,
    source_object_type  VARCHAR NOT NULL CHECK (
        source_object_type IN ('conflict', 'validation', 'revision', 'schema')
    ),
    source_object_id    VARCHAR,
    priority            VARCHAR,
    title               VARCHAR,
    description         TEXT,
    suggested_action    TEXT,
    status              VARCHAR CHECK (
        status IS NULL OR status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'DISMISSED', 'CANCELLED')
    ),
    assigned_to         VARCHAR,
    created_at          TIMESTAMP,
    resolved_at         TIMESTAMP,
    resolution_note     TEXT
);

CREATE TABLE IF NOT EXISTS instrument_registry (
    instrument_id       VARCHAR PRIMARY KEY,
    symbol              VARCHAR,
    name                VARCHAR,
    market_id           VARCHAR,
    asset_type          VARCHAR,
    currency            VARCHAR,
    exchange            VARCHAR,
    is_active           BOOLEAN,
    list_date           DATE,
    delist_date         DATE,
    source_used         VARCHAR,
    updated_at          TIMESTAMP
);

CREATE TABLE IF NOT EXISTS security_bar_1d (
    instrument_id       VARCHAR,
    trade_date          DATE,
    open                DOUBLE,
    high                DOUBLE,
    low                 DOUBLE,
    close               DOUBLE,
    pre_close           DOUBLE,
    volume              DOUBLE,
    amount              DOUBLE,
    adjustment_type     VARCHAR,
    source_used         VARCHAR,
    batch_id            VARCHAR,
    quality_flags       VARCHAR,
    created_at          TIMESTAMP,
    PRIMARY KEY (instrument_id, trade_date, adjustment_type)
);


-- Backtest / Review tables
CREATE TABLE IF NOT EXISTS backtest_scenario_registry (
    scenario_id VARCHAR PRIMARY KEY,
    scenario_name TEXT,
    backtest_type VARCHAR,
    description TEXT,
    input_requirements_json JSON,
    default_window_json JSON,
    metric_set_json JSON,
    resource_profile VARCHAR,
    no_action_semantics BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS backtest_run_log (
    run_id VARCHAR PRIMARY KEY,
    scenario_id VARCHAR,
    run_status VARCHAR,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    requested_by VARCHAR,
    resource_mode VARCHAR,
    date_range_start DATE,
    date_range_end DATE,
    universe_size INTEGER,
    event_count INTEGER,
    output_path TEXT,
    error_code VARCHAR,
    quality_flags_json JSON
);

CREATE TABLE IF NOT EXISTS backtest_event_set (
    event_id VARCHAR PRIMARY KEY,
    run_id VARCHAR,
    event_type VARCHAR,
    source_layer VARCHAR,
    target_id VARCHAR,
    event_timestamp TIMESTAMP,
    evidence_ids_json JSON,
    facts_used_json JSON,
    quality_flags_json JSON
);

CREATE TABLE IF NOT EXISTS backtest_metric_snapshot (
    metric_id VARCHAR PRIMARY KEY,
    run_id VARCHAR,
    event_id VARCHAR,
    target_id VARCHAR,
    horizon VARCHAR,
    metric_name VARCHAR,
    metric_value DOUBLE,
    metric_unit VARCHAR,
    sample_size INTEGER,
    quality_flags_json JSON,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS backtest_report (
    backtest_report_id VARCHAR PRIMARY KEY,
    run_id VARCHAR,
    title TEXT,
    summary TEXT,
    local_path TEXT,
    limitations TEXT,
    no_action_semantics BOOLEAN,
    generated_at TIMESTAMP,
    needs_human_review BOOLEAN
);

-- Alert event table
CREATE TABLE IF NOT EXISTS alert_event (
    alert_id VARCHAR PRIMARY KEY,
    alert_type VARCHAR,
    severity VARCHAR,
    source_layer VARCHAR,
    target_id VARCHAR,
    title TEXT,
    summary TEXT,
    trigger_reason_code VARCHAR,
    facts_used_json JSON,
    evidence_ids_json JSON,
    quality_flags_json JSON,
    dedup_key VARCHAR,
    cooldown_until TIMESTAMP,
    status VARCHAR,
    no_action_semantics BOOLEAN,
    created_at TIMESTAMP
);

-- Layer 1 axis tables (synced from migration 011_layer1_tables.sql; closes B2.5-O-02)

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

