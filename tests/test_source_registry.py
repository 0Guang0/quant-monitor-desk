"""Source registry loader and DB sync tests (Batch A)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from backend.app.datasources.source_registry import (
    DomainDisabledError,
    DomainNotAllowedError,
    DomainRoleBinding,
    InvalidRegistryError,
    LegacyRoleError,
    SourceDisabledError,
    SourceNotFoundError,
    SourceRegistry,
)


def test_load_validYaml_parsesPrimaryDomainRoles(registry_yaml_fixture):
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    roles = reg.get_domain_roles("market_bar_1d")
    assert roles.primary_source_id == "baostock"
    assert isinstance(roles, DomainRoleBinding)


def test_defaultYaml_loadsFromRepoSeed():
    reg = SourceRegistry()
    reg.load()
    roles = reg.get_domain_roles("cn_equity_daily_bar")
    assert roles.primary_source_id == "baostock"
    assert roles.validation_source_id == "akshare"
    assert isinstance(roles, DomainRoleBinding)


def test_load_yamlWithShadowRole_raisesLegacyRoleError(bad_shadow_yaml):
    reg = SourceRegistry(bad_shadow_yaml)
    with pytest.raises(LegacyRoleError):
        reg.load()


def test_load_yamlWithEmergencyRole_raisesLegacyRoleError(bad_emergency_yaml):
    reg = SourceRegistry(bad_emergency_yaml)
    with pytest.raises(LegacyRoleError):
        reg.load()


def test_load_yamlWithTopLevelShadowSource_raisesLegacyRoleError(
    bad_top_level_shadow_source_yaml,
):
    reg = SourceRegistry(bad_top_level_shadow_source_yaml)
    with pytest.raises(LegacyRoleError, match="shadow_source"):
        reg.load()


def test_load_yamlWithTopLevelEmergencySource_raisesLegacyRoleError(
    bad_top_level_emergency_source_yaml,
):
    reg = SourceRegistry(bad_top_level_emergency_source_yaml)
    with pytest.raises(LegacyRoleError, match="emergency_source"):
        reg.load()


def test_load_primaryDomainNotInAllowedDomains_raises(
    bad_primary_domain_mismatch_yaml,
):
    reg = SourceRegistry(bad_primary_domain_mismatch_yaml)
    with pytest.raises(InvalidRegistryError, match="does not allow domain"):
        reg.load()


def test_load_boolStringRejected_raisesInvalidRegistryError(bad_bool_string_yaml):
    reg = SourceRegistry(bad_bool_string_yaml)
    with pytest.raises(InvalidRegistryError, match="YAML boolean"):
        reg.load()


def test_load_validationSourceDisabled_raisesInvalidRegistryError(
    bad_validation_disabled_yaml,
):
    reg = SourceRegistry(bad_validation_disabled_yaml)
    with pytest.raises(InvalidRegistryError, match="validation.*disabled"):
        reg.load()


def test_load_validationSourceDomainMismatch_raisesInvalidRegistryError(
    bad_validation_domain_mismatch_yaml,
):
    reg = SourceRegistry(bad_validation_domain_mismatch_yaml)
    with pytest.raises(InvalidRegistryError, match="validation.*does not allow domain"):
        reg.load()


def test_load_validationStringNull_raisesInvalidRegistryError(
    bad_validation_string_null_yaml,
):
    reg = SourceRegistry(bad_validation_string_null_yaml)
    with pytest.raises(InvalidRegistryError, match="string 'null'"):
        reg.load()


def test_load_validationYamlNull_allowsNoValidationSource():
    path = Path(__file__).parent / "fixtures" / "source_registry_batch_b.yaml"
    reg = SourceRegistry(path)
    reg.load()
    roles = reg.get_domain_roles("market_bar_1m")
    assert roles.validation_source_id is None


def test_load_primaryUnknownLicense_raises(bad_unknown_license_primary_yaml):
    reg = SourceRegistry(bad_unknown_license_primary_yaml)
    with pytest.raises(InvalidRegistryError):
        reg.load()


def test_load_yaml_unknownPrimaryReference_raises(bad_unknown_primary_yaml):
    reg = SourceRegistry(bad_unknown_primary_yaml)
    with pytest.raises(InvalidRegistryError):
        reg.load()


def test_load_invalidFallbackPolicy_raises(bad_invalid_fallback_yaml):
    reg = SourceRegistry(bad_invalid_fallback_yaml)
    with pytest.raises(InvalidRegistryError):
        reg.load()


def test_load_malformedYaml_raises(malformed_yaml):
    reg = SourceRegistry(malformed_yaml)
    with pytest.raises(InvalidRegistryError):
        reg.load()


def test_load_pathOutsideProjectRoot_raises(tmp_path, monkeypatch):
    import backend.app.datasources.source_registry as registry_mod

    fake_project_root = tmp_path / "project"
    fake_project_root.mkdir()
    outside = tmp_path / "outside" / "outside.yaml"
    outside.parent.mkdir()
    outside.write_text("sources: {}\ndomain_roles: {}\n", encoding="utf-8")
    monkeypatch.setattr(registry_mod, "PROJECT_ROOT", fake_project_root)
    reg = SourceRegistry(outside)
    with pytest.raises(InvalidRegistryError, match="project root"):
        reg.load()


def test_getDomainRoles_unknownDomain_raisesKeyError(loaded_registry):
    with pytest.raises(KeyError):
        loaded_registry.get_domain_roles("no_such_domain")


def test_getSource_unknownId_raisesSourceNotFoundError(loaded_registry):
    with pytest.raises(SourceNotFoundError):
        loaded_registry.get("no_such_source")


@pytest.mark.parametrize(
    "policy",
    [
        "retry_same_source",
        "use_validation_source_with_flag",
        "use_last_good_cache",
        "mark_missing",
        "manual_review_required",
        "skip_until_next_publish",
    ],
)
def test_load_validFallbackPolicy_succeeds(policy, registry_yaml_fixture):
    text = registry_yaml_fixture.read_text(encoding="utf-8")
    text = text.replace("retry_same_source", policy)
    fixtures_dir = Path(__file__).parent / "fixtures"
    with tempfile.TemporaryDirectory(dir=fixtures_dir) as d:
        p = Path(d) / "policy.yaml"
        p.write_text(text, encoding="utf-8")
        reg = SourceRegistry(p)
        reg.load()
        roles = reg.get_domain_roles("market_bar_1d")
        assert roles.fallback_policy == policy


def test_assertDomainAllowed_unknownDomain_raises(loaded_registry):
    with pytest.raises(DomainNotAllowedError):
        loaded_registry.assert_domain_allowed("baostock", "unknown_domain")


def test_assertEnabled_disabledSource_raisesSourceDisabledError(disabled_registry):
    with pytest.raises(SourceDisabledError):
        disabled_registry.assert_enabled("baostock")


def test_syncToDb_removedYamlSource_isTombstoned(tmp_path, migrated_con, registry_yaml_fixture):
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    con = migrated_con(tmp_path)
    reg.sync_to_db(con)
    con.execute(
        """
        INSERT INTO source_registry (
            source_id, source_name, source_type, allowed_domain, is_enabled
        ) VALUES ('orphan_source', 'Orphan', 'api', '[]', true)
        """
    )
    reg.sync_to_db(con)
    row = con.execute(
        "SELECT is_enabled FROM source_registry WHERE source_id='orphan_source'"
    ).fetchone()
    assert row is not None
    assert row[0] is False


def test_syncToDb_insertsSourceRows(tmp_path, migrated_con, registry_yaml_fixture):
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    con = migrated_con(tmp_path)
    n = reg.sync_to_db(con)
    assert n >= 1
    count = con.execute("SELECT COUNT(*) FROM source_registry").fetchone()[0]
    assert count == n


def test_syncToDb_roundTrip_preservesAllColumns(tmp_path, migrated_con, registry_yaml_fixture):
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    con = migrated_con(tmp_path)
    reg.sync_to_db(con)
    row = con.execute("""
        SELECT rate_limit_policy, auth_required, allowed_domain
        FROM source_registry WHERE source_id='baostock'
    """).fetchone()
    assert row[0]
    assert json.loads(row[2])


def test_syncToDb_calledTwice_isIdempotent(tmp_path, migrated_con, registry_yaml_fixture):
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    con = migrated_con(tmp_path)
    n1 = reg.sync_to_db(con)
    n2 = reg.sync_to_db(con)
    assert n1 == n2
    count = con.execute("SELECT COUNT(*) FROM source_registry").fetchone()[0]
    assert count == n1


def test_syncToDb_secondCall_updatesUpdatedAt(tmp_path, migrated_con, registry_yaml_fixture):
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    con = migrated_con(tmp_path)
    reg.sync_to_db(con)
    t1 = con.execute(
        "SELECT updated_at FROM source_registry WHERE source_id='baostock'"
    ).fetchone()[0]
    reg.sync_to_db(con)
    t2 = con.execute(
        "SELECT updated_at FROM source_registry WHERE source_id='baostock'"
    ).fetchone()[0]
    assert t2 >= t1


def test_syncToDb_withinExplicitTransaction_rollsBackOnRollback(
    tmp_path,
    migrated_con,
    registry_yaml_fixture,
):
    """Caller-owned transaction (P1-4): ROLLBACK undoes sync_to_db writes."""
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    con = migrated_con(tmp_path)
    con.execute("BEGIN")
    n = reg.sync_to_db(con)
    assert n >= 1
    con.execute("ROLLBACK")
    count = con.execute("SELECT COUNT(*) FROM source_registry").fetchone()[0]
    assert count == 0


def test_disabledPrimaryDomain_returnsDisabledSource():
    reg = SourceRegistry()
    reg.load()
    roles = reg.get_domain_roles("cn_equity_minute_bar")
    assert roles.domain_enabled_by_default is False
    with pytest.raises(DomainDisabledError, match="DISABLED_SOURCE"):
        reg.assert_domain_schedulable("cn_equity_minute_bar")


def test_fallbackDisabledByDefault_isSkippedUntilConfigured():
    reg = SourceRegistry()
    reg.load()
    roles = reg.get_domain_roles("cn_equity_daily_bar")
    assert roles.fallback_policy == "skip_until_next_publish"
    assert roles.fallback_source_ids == ("qmt_xtdata",)
    assert reg.disabled_fallback_source_ids("cn_equity_daily_bar") == frozenset({"qmt_xtdata"})


@pytest.mark.parametrize("banned_role", ["Shadow", "Emergency"])
def test_legacySourceRoles_forbiddenAsSourceRoles(banned_role, registry_yaml_fixture):
    text = registry_yaml_fixture.read_text(encoding="utf-8")
    text = text.replace("primary: baostock", f"primary: {banned_role}", 1)
    fixtures_dir = Path(__file__).parent / "fixtures"
    with tempfile.TemporaryDirectory(dir=fixtures_dir) as d:
        p = Path(d) / "banned_role.yaml"
        p.write_text(text, encoding="utf-8")
        reg = SourceRegistry(p)
        with pytest.raises(LegacyRoleError):
            reg.load()


def test_legacySourceRoles_forbiddenTopLevelKeys(registry_yaml_fixture):
    text = registry_yaml_fixture.read_text(encoding="utf-8")
    text = "shadow_source: {}\n" + text
    fixtures_dir = Path(__file__).parent / "fixtures"
    with tempfile.TemporaryDirectory(dir=fixtures_dir) as d:
        p = Path(d) / "shadow_top.yaml"
        p.write_text(text, encoding="utf-8")
        reg = SourceRegistry(p)
        with pytest.raises(LegacyRoleError, match="shadow_source"):
            reg.load()
