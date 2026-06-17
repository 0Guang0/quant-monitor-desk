"""Source registry loader and DB sync tests (Batch A)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from backend.app.datasources.source_registry import (
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
    roles = reg.get_domain_roles("market_bar_1d")
    assert roles.primary_source_id == "baostock"
    assert isinstance(roles, DomainRoleBinding)


def test_load_yamlWithShadowRole_raisesLegacyRoleError(bad_shadow_yaml):
    reg = SourceRegistry(bad_shadow_yaml)
    with pytest.raises(LegacyRoleError):
        reg.load()


def test_load_yamlWithEmergencyRole_raisesLegacyRoleError(bad_emergency_yaml):
    reg = SourceRegistry(bad_emergency_yaml)
    with pytest.raises(LegacyRoleError):
        reg.load()


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


def test_load_pathOutsideProjectRoot_raises(tmp_path):
    outside = tmp_path / "outside.yaml"
    outside.write_text("sources: {}\ndomain_roles: {}\n", encoding="utf-8")
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
