-- Migration 012: Round 3F migration residuals (R3F-MIG-03/04).
-- R3F-MIG-03: explicit-column rebuild for fetch_log + manual_review_queue (no SELECT *).
-- R3F-MIG-04: registry_generation / removed_from_yaml_at lifecycle columns.

ALTER TABLE source_registry ADD COLUMN IF NOT EXISTS registry_generation INTEGER;
ALTER TABLE source_registry ADD COLUMN IF NOT EXISTS removed_from_yaml_at TIMESTAMP;

CREATE TABLE IF NOT EXISTS fetch_log_v3 (
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

INSERT INTO fetch_log_v3 (
    fetch_id, run_id, job_id, source_id, data_domain, market_id, instrument_id,
    request_params_hash, status, row_count, raw_file_paths, content_hash, schema_hash,
    as_of_timestamp, publish_timestamp, fetch_time, latency_ms, retry_count,
    error_type, error_message
)
SELECT
    fetch_id, run_id, job_id, source_id, data_domain, market_id, instrument_id,
    request_params_hash, status, row_count, raw_file_paths, content_hash, schema_hash,
    as_of_timestamp, publish_timestamp, fetch_time, latency_ms, retry_count,
    error_type, error_message
FROM fetch_log;
DROP TABLE fetch_log;
ALTER TABLE fetch_log_v3 RENAME TO fetch_log;

CREATE TABLE IF NOT EXISTS manual_review_queue_v3 (
    review_id           VARCHAR PRIMARY KEY,
    source_object_type  VARCHAR NOT NULL CHECK (
        source_object_type IN ('conflict', 'validation', 'revision', 'schema')
    ),
    source_object_id    VARCHAR NOT NULL,
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

INSERT INTO manual_review_queue_v3 (
    review_id, source_object_type, source_object_id, priority, title, description,
    suggested_action, status, assigned_to, created_at, resolved_at, resolution_note
)
SELECT
    review_id, source_object_type, source_object_id, priority, title, description,
    suggested_action, status, assigned_to, created_at, resolved_at, resolution_note
FROM manual_review_queue;
DROP TABLE manual_review_queue;
ALTER TABLE manual_review_queue_v3 RENAME TO manual_review_queue;
