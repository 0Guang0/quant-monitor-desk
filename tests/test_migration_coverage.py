"""已落地建模表 migration 覆盖测试。"""



from __future__ import annotations



import duckdb

import pytest

from backend.app.db.migrate import apply_migrations



LAYER1_AXIS_TABLES = frozenset(

    {

        "axis_registry",

        "axis_indicator_registry",

        "axis_indicator_profile",

        "axis_observation",

        "axis_feature_snapshot",

        "axis_interpretation_snapshot",

        "axis_snapshot_lineage",

    }

)



L5_MIGRATED_TABLES = frozenset(

    {

        "instrument_registry",

        "security_bar_1d",

    }

)



CLEAN_DOMAIN_MIGRATED_TABLES = frozenset(

    {

        "cn_announcement_clean",

        "stg_disclosure_smoke",

        "stg_axis_observation_smoke",

        "us_disclosure_clean",

        "stg_us_disclosure_smoke",

        "crypto_derivative_clean",

        "stg_crypto_derivative_smoke",

    }

)



DCP05_TIER_A_TABLES = frozenset(

    {

        "us_disclosure_clean",

        "crypto_derivative_clean",

        "stg_us_disclosure_smoke",

        "stg_crypto_derivative_smoke",

    }

)



_DOMAIN_TABLE_CASES = (

    ("L5 bar", L5_MIGRATED_TABLES, None),

    ("L1 axis", LAYER1_AXIS_TABLES, "011_layer1_tables"),

    ("clean domain", CLEAN_DOMAIN_MIGRATED_TABLES, None),

    ("DCP-05 Tier A", DCP05_TIER_A_TABLES, "015_dcp05_tier_a_clean"),

)





@pytest.mark.parametrize("label,expected_tables,version_id", _DOMAIN_TABLE_CASES)

def test_migrationCoverage_domainTables_existAfterMigrations(

    label: str, expected_tables: frozenset[str], version_id: str | None

) -> None:

    """覆盖范围：分域 migration 表清单（参数化，避免与 schema_migration 重复单测）

    测试对象：apply_migrations 后 SHOW TABLES / schema_version

    目的/目标：各域表集与版本 ID 可回归断言，文档化域边界

    验证点：expected_tables ⊆ tables；version_id 存在（若指定）

    失败含义：域 migration 未应用或表名/版本漂移

    """

    _ = label

    con = duckdb.connect(":memory:")

    apply_migrations(con)

    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}

    assert expected_tables.issubset(tables)

    if version_id is not None:

        versions = {row[0] for row in con.execute("SELECT version_id FROM schema_version").fetchall()}

        assert version_id in versions

