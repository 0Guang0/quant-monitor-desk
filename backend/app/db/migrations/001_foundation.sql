CREATE TABLE IF NOT EXISTS schema_version (
    version_id      VARCHAR PRIMARY KEY,
    applied_at      TIMESTAMP,
    migration_file  VARCHAR,
    checksum        VARCHAR,
    applied_by      VARCHAR,
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS file_registry (
    file_id         VARCHAR PRIMARY KEY,
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

CREATE TABLE IF NOT EXISTS write_audit_log (
    write_id        VARCHAR PRIMARY KEY,
    run_id          VARCHAR,
    job_id          VARCHAR,
    target_table    VARCHAR,
    staging_table   VARCHAR,
    write_mode      VARCHAR,
    primary_keys    VARCHAR,
    rows_in_staging INTEGER,
    rows_inserted   INTEGER,
    rows_updated    INTEGER,
    rows_deleted    INTEGER,
    rows_rejected   INTEGER,
    validation_status VARCHAR,
    source_used     VARCHAR,
    started_at      TIMESTAMP,
    finished_at     TIMESTAMP,
    status          VARCHAR,
    error_message   TEXT
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
    created_at      TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stg_foundation_smoke (
    instrument_id   VARCHAR,
    trade_date      DATE,
    close           DOUBLE,
    source_used     VARCHAR,
    batch_id        VARCHAR,
    PRIMARY KEY (instrument_id, trade_date)
);
