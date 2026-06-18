-- Batch C ingestion validation: validation_report / data_quality_log /
-- source_conflict / manual_review_queue + defensive CHECK constraints.
--
-- IMPORTANT (Round 2 Batch C):
--   These four tables did NOT exist in migrations 001-004 (they only appear in the
--   design spec specs/schema/schema.sql). Migration 005 therefore CREATEs them with
--   inline CHECK constraints. DuckDB cannot safely ALTER TABLE ADD CONSTRAINT on
--   already-applied tables, so the fetch_log status / SUCCESS-evidence guards that
--   belong to migration 004 (already applied) remain enforced at the application
--   layer (FetchResult model + FetchLogWriter._validate_for_persist). That fallback
--   is documented in BATCH_C_REPAIR_STATUS.md §3 and the FetchLogWriter docstring.

-- Validation report: outcome of a single DataQualityValidator run.
CREATE TABLE IF NOT EXISTS validation_report (
    validation_report_id    VARCHAR PRIMARY KEY,
    run_id                  VARCHAR NOT NULL,
    job_id                  VARCHAR,
    data_domain             VARCHAR NOT NULL,
    staging_table           VARCHAR,
    source_id               VARCHAR NOT NULL,
    status                  VARCHAR NOT NULL CHECK (status IN ('PASSED', 'WARNING', 'FAILED')),
    checked_rows            INTEGER NOT NULL CHECK (checked_rows >= 0),
    failed_rows             INTEGER NOT NULL CHECK (failed_rows >= 0),
    warning_rows            INTEGER NOT NULL CHECK (warning_rows >= 0),
    quality_flags           VARCHAR,
    stale_reason            VARCHAR,
    can_write_clean         BOOLEAN NOT NULL,
    needs_manual_review     BOOLEAN NOT NULL,
    created_at              TIMESTAMP
);

-- Per-row quality findings attached to a validation report.
CREATE TABLE IF NOT EXISTS data_quality_log (
    log_id              VARCHAR PRIMARY KEY,
    validation_report_id VARCHAR NOT NULL,
    run_id              VARCHAR NOT NULL,
    job_id              VARCHAR,
    data_domain         VARCHAR NOT NULL,
    source_id           VARCHAR NOT NULL,
    table_name          VARCHAR,
    row_key             VARCHAR,
    field_name          VARCHAR,
    rule_id             VARCHAR NOT NULL,
    severity            VARCHAR NOT NULL CHECK (severity IN ('failed', 'warning')),
    observed_value      VARCHAR,
    expected_condition  VARCHAR,
    message             TEXT,
    created_at          TIMESTAMP
);

-- Multi-source value conflicts on objective-fact fields.
CREATE TABLE IF NOT EXISTS source_conflict (
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
    severity                VARCHAR NOT NULL CHECK (severity IN ('warning', 'severe')),
    reconcile_status        VARCHAR,
    manual_review_required  BOOLEAN NOT NULL,
    resolution              VARCHAR,
    resolution_note         TEXT,
    created_at              TIMESTAMP,
    resolved_at             TIMESTAMP
);

-- Manual review queue: unresolved severe conflicts / schema drift etc.
-- Manual review must NOT directly patch clean tables; it queues a review
-- (or a downstream manual_patch write request) only.
CREATE TABLE IF NOT EXISTS manual_review_queue (
    review_id           VARCHAR PRIMARY KEY,
    source_object_type  VARCHAR NOT NULL CHECK (
        source_object_type IN ('conflict', 'validation', 'revision', 'schema')
    ),
    source_object_id    VARCHAR NOT NULL,
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
