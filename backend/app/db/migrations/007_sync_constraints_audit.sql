-- Migration 007: sync job status CHECK constraints + write_audit_log contract columns.
-- DuckDB cannot ALTER ADD CHECK on existing tables; rebuild sync tables with inline CHECK.

ALTER TABLE write_audit_log ADD COLUMN IF NOT EXISTS partition_keys VARCHAR;
ALTER TABLE write_audit_log ADD COLUMN IF NOT EXISTS conflict_status VARCHAR;
ALTER TABLE write_audit_log ADD COLUMN IF NOT EXISTS source_role VARCHAR;
ALTER TABLE write_audit_log ADD COLUMN IF NOT EXISTS source_switched BOOLEAN;
ALTER TABLE write_audit_log ADD COLUMN IF NOT EXISTS stale_reason VARCHAR;
ALTER TABLE write_audit_log ADD COLUMN IF NOT EXISTS traceback_digest VARCHAR;
ALTER TABLE write_audit_log ADD COLUMN IF NOT EXISTS data_domain VARCHAR;
ALTER TABLE write_audit_log ADD COLUMN IF NOT EXISTS conflict_report_id VARCHAR;
ALTER TABLE write_audit_log ADD COLUMN IF NOT EXISTS requested_by VARCHAR;
ALTER TABLE write_audit_log ADD COLUMN IF NOT EXISTS allow_partial_write BOOLEAN;

CREATE TABLE IF NOT EXISTS data_sync_job_v2 (
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

INSERT INTO data_sync_job_v2 SELECT * FROM data_sync_job;
DROP TABLE data_sync_job;
ALTER TABLE data_sync_job_v2 RENAME TO data_sync_job;

CREATE TABLE IF NOT EXISTS job_event_log_v2 (
    event_id        VARCHAR PRIMARY KEY,
    run_id          VARCHAR,
    job_id          VARCHAR,
    task_id         VARCHAR,
    event_type      VARCHAR,
    old_status      VARCHAR CHECK (
        old_status IS NULL OR old_status IN (
            'CREATED', 'PLANNED', 'FETCHING', 'STAGED', 'VALIDATING',
            'WAITING_RECONCILE', 'RECONCILING', 'READY_TO_WRITE', 'WRITING',
            'COMPLETED', 'FAILED_FINAL', 'SKIPPED', 'CANCELLED',
            'MANUAL_REVIEW_REQUIRED', 'FAILED_RETRYABLE'
        )
    ),
    new_status      VARCHAR CHECK (
        new_status IS NULL OR new_status IN (
            'CREATED', 'PLANNED', 'FETCHING', 'STAGED', 'VALIDATING',
            'WAITING_RECONCILE', 'RECONCILING', 'READY_TO_WRITE', 'WRITING',
            'COMPLETED', 'FAILED_FINAL', 'SKIPPED', 'CANCELLED',
            'MANUAL_REVIEW_REQUIRED', 'FAILED_RETRYABLE'
        )
    ),
    message         TEXT,
    payload_json    TEXT,
    created_at      TIMESTAMP
);

INSERT INTO job_event_log_v2 SELECT * FROM job_event_log;
DROP TABLE job_event_log;
ALTER TABLE job_event_log_v2 RENAME TO job_event_log;

CREATE INDEX IF NOT EXISTS idx_data_sync_job_run_id ON data_sync_job (run_id);
CREATE INDEX IF NOT EXISTS idx_job_event_log_job_id ON job_event_log (job_id);
