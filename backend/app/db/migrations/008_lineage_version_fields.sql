-- Migration 008: rule/version lineage fields + allowed_domains_json alias (Round2 audit P1-02, P2-05).

ALTER TABLE validation_report ADD COLUMN IF NOT EXISTS rule_set_id VARCHAR;
ALTER TABLE validation_report ADD COLUMN IF NOT EXISTS rule_version VARCHAR;
ALTER TABLE validation_report ADD COLUMN IF NOT EXISTS source_fetch_ids_json VARCHAR;
ALTER TABLE validation_report ADD COLUMN IF NOT EXISTS source_content_hashes_json VARCHAR;

ALTER TABLE data_quality_log ADD COLUMN IF NOT EXISTS rule_version VARCHAR;

ALTER TABLE source_conflict ADD COLUMN IF NOT EXISTS tolerance_rule_set_id VARCHAR;
ALTER TABLE source_conflict ADD COLUMN IF NOT EXISTS rule_version VARCHAR;

-- allowed_domain (singular) stores JSON array; allowed_domains_json mirrors for clarity.
ALTER TABLE source_registry ADD COLUMN IF NOT EXISTS allowed_domains_json VARCHAR;
UPDATE source_registry
SET allowed_domains_json = allowed_domain
WHERE allowed_domains_json IS NULL AND allowed_domain IS NOT NULL;
