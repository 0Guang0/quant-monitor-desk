-- Rename incremental bookmark columns to watermark_* (terminology SSOT).
-- ponytail: DuckDB blocks RENAME COLUMN when indexes depend on the table; rebuild like 007.

DROP INDEX IF EXISTS idx_data_sync_job_run_id;

CREATE TABLE data_sync_job_wm (
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
    watermark_before    VARCHAR,
    watermark_after     VARCHAR,
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

INSERT INTO data_sync_job_wm (
    job_id, run_id, job_type, data_domain, market_id, instrument_id, partition_key,
    date_start, date_end, source_id, adapter_id, status, priority, retry_count, max_retries,
    watermark_before, watermark_after, validation_report_id, conflict_report_id, write_id,
    error_type, error_message, created_at, started_at, finished_at, updated_at
)
SELECT
    job_id, run_id, job_type, data_domain, market_id, instrument_id, partition_key,
    date_start, date_end, source_id, adapter_id, status, priority, retry_count, max_retries,
    cursor_before, cursor_after, validation_report_id, conflict_report_id, write_id,
    error_type, error_message, created_at, started_at, finished_at, updated_at
FROM data_sync_job;

DROP TABLE data_sync_job;
ALTER TABLE data_sync_job_wm RENAME TO data_sync_job;

CREATE INDEX IF NOT EXISTS idx_data_sync_job_run_id ON data_sync_job (run_id);
