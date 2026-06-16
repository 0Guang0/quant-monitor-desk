CREATE UNIQUE INDEX IF NOT EXISTS idx_file_registry_content_hash ON file_registry(content_hash);

CREATE TABLE IF NOT EXISTS stg_file_registry (
    file_id         VARCHAR,
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
