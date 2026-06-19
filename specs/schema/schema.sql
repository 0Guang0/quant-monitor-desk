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
    source_type            VARCHAR,
    allowed_domain         VARCHAR,
    trust_level            INTEGER,
    license_type           VARCHAR,
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
    status              VARCHAR,
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
    severity                VARCHAR,
    reconcile_status        VARCHAR,
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
    traceback_digest    VARCHAR
);

CREATE TABLE IF NOT EXISTS manual_review_queue (
    review_id           VARCHAR PRIMARY KEY,
    source_object_type  VARCHAR,
    source_object_id    VARCHAR,
    priority            VARCHAR,
    title               VARCHAR,
    description         TEXT,
    suggested_action    TEXT,
    status              VARCHAR,
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

