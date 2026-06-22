"""Staged sandbox DDL for Layer 2 tables (no production migration on 019)."""

from __future__ import annotations

import duckdb

AXIS_SNAPSHOT_LINEAGE_TABLE = "axis_snapshot_lineage"

CROSS_ASSET_REGISTRY_DDL = """
CREATE TABLE IF NOT EXISTS cross_asset_registry (
    asset_id              VARCHAR PRIMARY KEY,
    display_name          VARCHAR,
    display_name_cn       VARCHAR,
    asset_group           VARCHAR,
    asset_type            VARCHAR,
    market                VARCHAR,
    instrument_id         VARCHAR,
    layer5_instrument_id  VARCHAR,
    primary_source        VARCHAR,
    validation_source     VARCHAR,
    fallback_policy       VARCHAR,
    mapped_axis           VARCHAR,
    is_axis_input         BOOLEAN,
    display_only          BOOLEAN,
    eligible_for_model    BOOLEAN,
    double_count_guard    VARCHAR,
    updated_at            TIMESTAMP
);
"""

CROSS_ASSET_OBSERVATION_DDL = """
CREATE TABLE IF NOT EXISTS cross_asset_observation (
    asset_id            VARCHAR,
    trade_time          TIMESTAMP,
    market              VARCHAR,
    asset_type          VARCHAR,
    open                DOUBLE,
    high                DOUBLE,
    low                 DOUBLE,
    close               DOUBLE,
    pre_close           DOUBLE,
    volume              DOUBLE,
    amount              DOUBLE,
    open_interest       DOUBLE,
    source              VARCHAR,
    as_of_timestamp     TIMESTAMP,
    fetch_time          TIMESTAMP,
    quality_flag        VARCHAR,
    PRIMARY KEY (asset_id, trade_time, source)
);
"""

CROSS_ASSET_DAILY_SNAPSHOT_DDL = """
CREATE TABLE IF NOT EXISTS cross_asset_daily_snapshot (
    snapshot_id          VARCHAR PRIMARY KEY,
    asset_id             VARCHAR,
    trade_date           DATE,
    close                DOUBLE,
    pct_change           DOUBLE,
    volume               DOUBLE,
    amount               DOUBLE,
    open_interest        DOUBLE,
    level_label          VARCHAR,
    change_label         VARCHAR,
    quality_flags        VARCHAR,
    source_used          VARCHAR,
    as_of_timestamp      TIMESTAMP,
    created_at           TIMESTAMP,
    lineage_snapshot_id  VARCHAR,
    active_contract      VARCHAR
);
"""

CROSS_ASSET_ROLL_EVENT_DDL = """
CREATE TABLE IF NOT EXISTS cross_asset_roll_event (
    roll_id              VARCHAR PRIMARY KEY,
    asset_id             VARCHAR,
    roll_event           BOOLEAN,
    old_contract         VARCHAR,
    new_contract         VARCHAR,
    roll_reason          VARCHAR,
    roll_date            DATE,
    volume_old           DOUBLE,
    volume_new           DOUBLE,
    open_interest_old    DOUBLE,
    open_interest_new    DOUBLE,
    created_at           TIMESTAMP
);
"""


def ensure_layer2_staging_tables(con: duckdb.DuckDBPyConnection) -> None:
    """Create Layer 2 sandbox tables for staged WriteManager tests."""
    con.execute(CROSS_ASSET_REGISTRY_DDL)
    con.execute(CROSS_ASSET_OBSERVATION_DDL)
    con.execute(CROSS_ASSET_DAILY_SNAPSHOT_DDL)
    con.execute(CROSS_ASSET_ROLL_EVENT_DDL)
