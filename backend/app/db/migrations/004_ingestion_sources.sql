-- Batch A ingestion: source_registry + fetch_log (Round 2)

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

CREATE TABLE IF NOT EXISTS fetch_log (
    fetch_id            VARCHAR PRIMARY KEY,
    run_id              VARCHAR,
    job_id              VARCHAR,
    source_id           VARCHAR,
    data_domain         VARCHAR,
    market_id           VARCHAR,
    instrument_id       VARCHAR,
    request_params_hash VARCHAR,
    status              VARCHAR,
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
