-- Migration 014: stg_foundation_smoke OHLCV + security_bar_1d column parity (R3H-06)

-- ponytail: rebuild staging for WriteManager column-order match with security_bar_1d
DROP TABLE IF EXISTS stg_foundation_smoke;
CREATE TABLE IF NOT EXISTS stg_foundation_smoke (
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
