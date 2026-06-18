-- Batch D ingestion sync: data_sync_job + job_event_log (specs/schema/schema.sql L73-113).
-- Does NOT ALTER migrations 004/005 (BATCH_C_LEDGER C-C2).

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

CREATE INDEX IF NOT EXISTS idx_data_sync_job_run_id ON data_sync_job (run_id);
CREATE INDEX IF NOT EXISTS idx_job_event_log_job_id ON job_event_log (job_id);
