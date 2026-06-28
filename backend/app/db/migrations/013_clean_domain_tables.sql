-- Migration 013: Clean domain tables (R3H-06 Wave 1)

CREATE TABLE IF NOT EXISTS instrument_registry (
    instrument_id       VARCHAR PRIMARY KEY,
    symbol              VARCHAR,
    name                VARCHAR,
    market_id           VARCHAR,
    asset_type          VARCHAR,
    currency            VARCHAR,
    exchange            VARCHAR,
    is_active           BOOLEAN,
    list_date           DATE,
    delist_date         DATE,
    source_used         VARCHAR,
    updated_at          TIMESTAMP
);

CREATE TABLE IF NOT EXISTS security_bar_1d (
    instrument_id       VARCHAR,
    trade_date          DATE,
    open                DOUBLE,
    high                DOUBLE,
    low                 DOUBLE,
    close               DOUBLE,
    pre_close           DOUBLE,
    volume              DOUBLE,
    amount              DOUBLE,
    adjustment_type     VARCHAR,
    source_used         VARCHAR,
    batch_id            VARCHAR,
    quality_flags       VARCHAR,
    created_at          TIMESTAMP,
    PRIMARY KEY (instrument_id, trade_date, adjustment_type)
);

CREATE TABLE IF NOT EXISTS cn_announcement_clean (
    announcement_id         VARCHAR PRIMARY KEY,
    instrument_id           VARCHAR,
    title                   VARCHAR,
    publish_timestamp       TIMESTAMP,
    announcement_url        VARCHAR,
    announcement_type       VARCHAR,
    data_domain             VARCHAR,
    source_used             VARCHAR,
    pdf_file_id             VARCHAR,
    extracted_text_file_id  VARCHAR,
    content_status          VARCHAR,
    batch_id                VARCHAR,
    source_fetch_id         VARCHAR,
    content_hash            VARCHAR,
    schema_hash             VARCHAR,
    quality_flags           VARCHAR,
    created_at              TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stg_disclosure_smoke (
    announcement_id         VARCHAR,
    instrument_id           VARCHAR,
    title                   VARCHAR,
    publish_timestamp       TIMESTAMP,
    announcement_url        VARCHAR,
    announcement_type       VARCHAR,
    data_domain             VARCHAR,
    source_used             VARCHAR,
    pdf_file_id             VARCHAR,
    extracted_text_file_id  VARCHAR,
    content_status          VARCHAR,
    batch_id                VARCHAR,
    source_fetch_id         VARCHAR,
    content_hash            VARCHAR,
    schema_hash             VARCHAR,
    quality_flags           VARCHAR,
    created_at              TIMESTAMP,
    PRIMARY KEY (announcement_id)
);

-- ponytail: macro promote staging mirrors axis_observation column order (011)
CREATE TABLE IF NOT EXISTS stg_axis_observation_smoke (
    observation_id      VARCHAR,
    indicator_id        VARCHAR,
    as_of_timestamp     TIMESTAMP,
    publish_timestamp   TIMESTAMP,
    fetch_time          TIMESTAMP,
    raw_value           DOUBLE,
    raw_unit            VARCHAR,
    frequency           VARCHAR,
    source_used         VARCHAR,
    source_channel_id   VARCHAR,
    data_lag_days       DOUBLE,
    stale_reason        VARCHAR,
    quality_flags       VARCHAR,
    content_hash        VARCHAR,
    schema_hash         VARCHAR,
    source_switched     BOOLEAN,
    created_at          TIMESTAMP,
    PRIMARY KEY (observation_id)
);
