-- Migration 009: DB CHECK constraints on status/enum columns (Round2 audit P1-04).
-- DuckDB cannot ALTER ADD CHECK; rebuild affected tables with inline CHECK.

CREATE TABLE IF NOT EXISTS fetch_log_v2 (
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

INSERT INTO fetch_log_v2 SELECT * FROM fetch_log;
DROP TABLE fetch_log;
ALTER TABLE fetch_log_v2 RENAME TO fetch_log;

CREATE TABLE IF NOT EXISTS source_registry_v2 (
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

INSERT INTO source_registry_v2 (
    source_id, source_name, source_type, allowed_domain, allowed_domains_json,
    trust_level, license_type, official_api, is_enabled, default_priority,
    rate_limit_policy, auth_required, requires_local_client, expected_frequency,
    expected_lag, timezone, fallback_allowed, validation_only, notes, updated_at
)
SELECT
    source_id, source_name, source_type, allowed_domain, allowed_domains_json,
    trust_level, license_type, official_api, is_enabled, default_priority,
    rate_limit_policy, auth_required, requires_local_client, expected_frequency,
    expected_lag, timezone, fallback_allowed, validation_only, notes, updated_at
FROM source_registry;
DROP TABLE source_registry;
ALTER TABLE source_registry_v2 RENAME TO source_registry;

CREATE TABLE IF NOT EXISTS manual_review_queue_v2 (
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

INSERT INTO manual_review_queue_v2 SELECT * FROM manual_review_queue;
DROP TABLE manual_review_queue;
ALTER TABLE manual_review_queue_v2 RENAME TO manual_review_queue;

CREATE TABLE IF NOT EXISTS source_conflict_v2 (
    conflict_id             VARCHAR PRIMARY KEY,
    run_id                  VARCHAR NOT NULL,
    job_id                  VARCHAR,
    data_domain             VARCHAR NOT NULL,
    market_id               VARCHAR,
    instrument_id           VARCHAR,
    field_name              VARCHAR NOT NULL,
    as_of_timestamp         TIMESTAMP,
    primary_source          VARCHAR NOT NULL,
    primary_value           VARCHAR,
    competing_source        VARCHAR NOT NULL,
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
    manual_review_required  BOOLEAN NOT NULL,
    resolution              VARCHAR,
    resolution_note         TEXT,
    created_at              TIMESTAMP,
    resolved_at             TIMESTAMP
);

INSERT INTO source_conflict_v2 (
    conflict_id, run_id, job_id, data_domain, market_id, instrument_id,
    field_name, as_of_timestamp, primary_source, primary_value,
    competing_source, competing_value, normalized_diff, tolerance_warning,
    tolerance_severe, tolerance_rule_set_id, rule_version, severity,
    reconcile_status, manual_review_required, resolution, resolution_note,
    created_at, resolved_at
)
SELECT
    conflict_id, run_id, job_id, data_domain, market_id, instrument_id,
    field_name, as_of_timestamp, primary_source, primary_value,
    competing_source, competing_value, normalized_diff, tolerance_warning,
    tolerance_severe, tolerance_rule_set_id, rule_version, severity,
    reconcile_status, manual_review_required, resolution, resolution_note,
    created_at, resolved_at
FROM source_conflict;
DROP TABLE source_conflict;
ALTER TABLE source_conflict_v2 RENAME TO source_conflict;
