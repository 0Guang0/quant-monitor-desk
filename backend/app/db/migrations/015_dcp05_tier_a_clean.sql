-- Migration 015: DCP-05 Tier A clean extensions (ADR-028)

CREATE TABLE IF NOT EXISTS us_disclosure_clean (
    accession_number        VARCHAR PRIMARY KEY,
    cik                     VARCHAR,
    form_type               VARCHAR,
    filing_date             DATE,
    report_date             DATE,
    primary_document_url    VARCHAR,
    data_domain             VARCHAR,
    source_used             VARCHAR,
    batch_id                VARCHAR,
    source_fetch_id         VARCHAR,
    content_hash            VARCHAR,
    schema_hash             VARCHAR,
    quality_flags           VARCHAR,
    created_at              TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stg_us_disclosure_smoke (
    accession_number        VARCHAR,
    cik                     VARCHAR,
    form_type               VARCHAR,
    filing_date             DATE,
    report_date             DATE,
    primary_document_url    VARCHAR,
    data_domain             VARCHAR,
    source_used             VARCHAR,
    batch_id                VARCHAR,
    source_fetch_id         VARCHAR,
    content_hash            VARCHAR,
    schema_hash             VARCHAR,
    quality_flags           VARCHAR,
    created_at              TIMESTAMP,
    PRIMARY KEY (accession_number)
);

CREATE TABLE IF NOT EXISTS crypto_derivative_clean (
    instrument_name         VARCHAR,
    as_of_timestamp         TIMESTAMP,
    data_domain             VARCHAR,
    expiration_timestamp    BIGINT,
    strike                  DOUBLE,
    option_type             VARCHAR,
    mark_iv                 DOUBLE,
    source_used             VARCHAR,
    batch_id                VARCHAR,
    source_fetch_id         VARCHAR,
    content_hash            VARCHAR,
    schema_hash             VARCHAR,
    quality_flags           VARCHAR,
    created_at              TIMESTAMP,
    PRIMARY KEY (instrument_name, as_of_timestamp, data_domain)
);

CREATE TABLE IF NOT EXISTS stg_crypto_derivative_smoke (
    instrument_name         VARCHAR,
    as_of_timestamp         TIMESTAMP,
    data_domain             VARCHAR,
    expiration_timestamp    BIGINT,
    strike                  DOUBLE,
    option_type             VARCHAR,
    mark_iv                 DOUBLE,
    source_used             VARCHAR,
    batch_id                VARCHAR,
    source_fetch_id         VARCHAR,
    content_hash            VARCHAR,
    schema_hash             VARCHAR,
    quality_flags           VARCHAR,
    created_at              TIMESTAMP,
    PRIMARY KEY (instrument_name, as_of_timestamp, data_domain)
);
