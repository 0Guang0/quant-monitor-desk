-- Migration 010: enforce non-null rule lineage on validation_report (Round2 re-audit A9-02).
-- Replay safety: applied once via schema_version; rebuild uses explicit column list below.

UPDATE validation_report
SET rule_set_id = 'p0_round_1'
WHERE rule_set_id IS NULL;

UPDATE validation_report
SET rule_version = COALESCE(rule_version, rule_set_id, 'p0_round_1')
WHERE rule_version IS NULL;

UPDATE data_quality_log
SET rule_version = 'p0_round_1'
WHERE rule_version IS NULL;

UPDATE source_conflict
SET tolerance_rule_set_id = 'p0_round_1'
WHERE tolerance_rule_set_id IS NULL;

UPDATE source_conflict
SET rule_version = 'p0_round_1'
WHERE rule_version IS NULL;

CREATE TABLE IF NOT EXISTS validation_report_v3 (
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
    rule_set_id             VARCHAR NOT NULL,
    rule_version            VARCHAR NOT NULL,
    source_fetch_ids_json   VARCHAR,
    source_content_hashes_json VARCHAR,
    created_at              TIMESTAMP
);

INSERT INTO validation_report_v3 (
    validation_report_id, run_id, job_id, data_domain, staging_table,
    source_id, status, checked_rows, failed_rows, warning_rows,
    quality_flags, stale_reason, can_write_clean, needs_manual_review,
    rule_set_id, rule_version, source_fetch_ids_json, source_content_hashes_json,
    created_at
)
SELECT
    validation_report_id, run_id, job_id, data_domain, staging_table,
    source_id, status, checked_rows, failed_rows, warning_rows,
    quality_flags, stale_reason, can_write_clean, needs_manual_review,
    rule_set_id, rule_version, source_fetch_ids_json, source_content_hashes_json,
    created_at
FROM validation_report;
DROP TABLE validation_report;
ALTER TABLE validation_report_v3 RENAME TO validation_report;
