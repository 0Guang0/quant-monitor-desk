"""Tests for Layer 1 axis loader, guardrails, and migration 011 (Batch 2 §8.1–8.2)."""

from __future__ import annotations

import shutil
from pathlib import Path

import duckdb
import pytest
import yaml
from backend.app.config import PROJECT_ROOT
from backend.app.layer1_axes.axis_loader import (
    AxisSpecLoader,
    AxisSpecLoadError,
)
from backend.app.layer1_axes.guardrails import (
    AxisEngineeringGuardrailValidator,
    GuardrailViolationError,
)

MIGRATION_011 = "011_layer1_tables"

LAYER1_REGISTRY_TABLES = frozenset(
    {
        "axis_registry",
        "axis_indicator_registry",
        "axis_indicator_profile",
    }
)

AXIS_SNAPSHOT_LINEAGE_COLUMNS = frozenset(
    {
        "snapshot_id",
        "snapshot_type",
        "layer_id",
        "as_of_timestamp",
        "generated_at",
        "input_data_window_start",
        "input_data_window_end",
        "source_dataset_ids",
        "source_fetch_ids",
        "source_content_hashes",
        "rule_version",
        "code_version",
        "parameter_hash",
        "resource_profile",
        "upstream_snapshot_ids",
        "is_incremental",
        "rebuild_reason",
    }
)


def _table_columns(con: duckdb.DuckDBPyConnection, table_name: str) -> set[str]:
    rows = con.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = ?
        """,
        [table_name],
    ).fetchall()
    return {row[0] for row in rows}


def test_layer1Migration_createsRegistryTables(migrated_con, tmp_path) -> None:
    """migration 011 creates axis registry tables."""
    con = migrated_con(tmp_path)
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    assert LAYER1_REGISTRY_TABLES.issubset(tables)
    versions = {row[0] for row in con.execute("SELECT version_id FROM schema_version").fetchall()}
    assert MIGRATION_011 in versions
    con.close()


def test_layer1Migration_createsSnapshotLineageTable(migrated_con, tmp_path) -> None:
    """axis_snapshot_lineage exists with lineage contract columns including rule_version."""
    con = migrated_con(tmp_path)
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    assert "axis_snapshot_lineage" in tables
    cols = _table_columns(con, "axis_snapshot_lineage")
    assert AXIS_SNAPSHOT_LINEAGE_COLUMNS.issubset(cols)
    assert "rule_version" in cols
    con.close()


def _spec_root() -> Path:
    return PROJECT_ROOT / "specs/layer1_axes/restructured_axes_v1_1"


def _copy_specs(tmp_path: Path) -> Path:
    dest = tmp_path / "specs"
    shutil.copytree(_spec_root(), dest)
    return dest


def test_axisSpecLoader_loadsFiveAxes() -> None:
    result = AxisSpecLoader().load(spec_root=_spec_root())
    axis_ids = {a.axis_id for a in result.axes}
    assert axis_ids == {
        "ENVIRONMENT",
        "CREDIT_STRESS",
        "RISK_APPETITE",
        "LIQUIDITY",
        "SENTIMENT",
    }
    assert len(result.indicators) > 0
    observable = [i for i in result.indicators if i.is_observable]
    assert len(observable) > 0


def test_axisSpecLoader_missingIndicatorId_rejects(tmp_path: Path) -> None:
    root = _copy_specs(tmp_path)
    spec_path = root / "environment_axis" / "environment_axis_indicator_spec.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    first = spec["modules"]["E0_money_quantity"]["indicators"][0]
    del first["indicator_id"]
    spec_path.write_text(yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
    with pytest.raises(AxisSpecLoadError, match="indicator_id"):
        AxisSpecLoader().load(spec_root=root, enabled_axes=["environment"])


def test_axisSpecLoader_missingQualityRules_rejects(tmp_path: Path) -> None:
    root = _copy_specs(tmp_path)
    spec_path = root / "environment_axis" / "environment_axis_indicator_spec.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    ind = spec["modules"]["E0_money_quantity"]["indicators"][0]
    ind["quality_rules"] = []
    spec_path.write_text(yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
    with pytest.raises(AxisSpecLoadError, match="quality_rules"):
        AxisSpecLoader().load(spec_root=root, enabled_axes=["environment"])


def test_axisSpecLoader_forbiddenIndicator_notObservable() -> None:
    result = AxisSpecLoader().load(spec_root=_spec_root())
    forbidden = [i for i in result.indicators if i.is_forbidden]
    assert forbidden, "expected at least one forbidden indicator from specs"
    assert all(not i.is_observable for i in forbidden)


def test_axisSpecLoader_blindspot_notObservable() -> None:
    result = AxisSpecLoader().load(spec_root=_spec_root())
    blind = [i for i in result.indicators if i.is_blindspot]
    assert blind, "expected blindspot indicators"
    assert all(not i.is_observable for i in blind)


def test_axisEngineeringGuardrail_rejectsForbiddenSubstitute() -> None:
    result = AxisSpecLoader().load(spec_root=_spec_root())
    validator = AxisEngineeringGuardrailValidator(result.guardrails)
    credit = next(i for i in result.indicators if i.forbidden_substitutes)
    substitute = credit.forbidden_substitutes[0]
    with pytest.raises(GuardrailViolationError, match="forbidden substitute"):
        validator.reject_forbidden_substitute(credit, substitute_id=substitute)


def test_layer1ShadowDiagnostics_areExplicitlyAllowedButNoTakeover() -> None:
    result = AxisSpecLoader().load(spec_root=_spec_root())
    shadows = [i for i in result.indicators if i.is_shadow and i.module == "shadow_diagnostics"]
    assert len(shadows) >= 3
    for ind in shadows:
        AxisEngineeringGuardrailValidator.assert_shadow_diagnostics_allowed(ind)
        assert "no_takeover" in ind.role_notes.lower() or ind.diagnostic_only


def test_shadowDiagnosticLabels_doNotEnterSourceRegistryRoles() -> None:
    result = AxisSpecLoader().load(spec_root=_spec_root())
    for ind in result.indicators:
        if ind.is_shadow:
            assert ind.primary_source.lower() != "shadow"
            assert ind.dest_tag == "SHADOW"


def test_shadowDiagnosticsOutsideGroup_requireExplicitDiagnosticOnly(tmp_path: Path) -> None:
    root = _copy_specs(tmp_path)
    spec_path = root / "liquidity_axis" / "liquidity_axis_indicator_spec.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    spec["modules"]["L1_tightness"]["indicators"].append(
        {
            "indicator_id": "LIQ.SHADOW.ORPHAN_TEST",
            "display_name_cn": "orphan shadow",
            "plain_language_summary": "shadow outside group",
            "layer": "Shadow",
            "dest_tag": "SHADOW",
            "frequency": "daily",
            "primary_source": "none",
        }
    )
    spec_path.write_text(yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
    result = AxisSpecLoader().load(spec_root=root, enabled_axes=["liquidity"])
    orphan = next(i for i in result.indicators if i.indicator_id == "LIQ.SHADOW.ORPHAN_TEST")
    with pytest.raises(GuardrailViolationError, match="diagnostic_only"):
        AxisEngineeringGuardrailValidator.assert_shadow_outside_group_has_diagnostic_only(orphan)
    orphan_diag = next(
        (i for i in result.indicators if i.indicator_id == "LIQ.SHADOW.ORPHAN_TEST"),
    )
    assert orphan_diag.is_shadow
    # Fix by setting diagnostic_only — loader should mark it
    assert not orphan_diag.diagnostic_only


def test_axisSpecLoader_emptySpecRoot_rejects(tmp_path: Path) -> None:
    empty_root = tmp_path / "empty_specs"
    empty_root.mkdir()
    with pytest.raises(AxisSpecLoadError, match="missing indicator spec"):
        AxisSpecLoader().load(spec_root=empty_root, enabled_axes=["environment"])


def test_axisSpecLoader_allForbiddenAxis_registersNoneObservable(tmp_path: Path) -> None:
    root = _copy_specs(tmp_path)
    spec_path = root / "environment_axis" / "environment_axis_indicator_spec.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    for mod in spec.get("modules", {}).values():
        for ind in mod.get("indicators", []):
            ind["status"] = "forbidden"
            ind["layer"] = "Forbidden"
            ind["dest_tag"] = "FORBIDDEN"
    spec_path.write_text(yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
    result = AxisSpecLoader().load(spec_root=root, enabled_axes=["environment"])
    assert len(result.indicators) > 0
    assert all(i.is_forbidden for i in result.indicators)
    assert not any(i.is_observable for i in result.indicators)


def test_axisSpecLoader_missingQualityRulesKey_appliesContractDefaults(tmp_path: Path) -> None:
    root = _copy_specs(tmp_path)
    spec_path = root / "environment_axis" / "environment_axis_indicator_spec.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    ind = spec["modules"]["E0_money_quantity"]["indicators"][0]
    indicator_id = ind["indicator_id"]
    ind.pop("quality_rules", None)
    spec_path.write_text(yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
    result = AxisSpecLoader().load(spec_root=root, enabled_axes=["environment"])
    loaded = next(i for i in result.indicators if i.indicator_id == indicator_id)
    assert loaded.quality_rules == (
        "MISSING_VALUE",
        "STALE_DATA",
        "INSUFFICIENT_HISTORY",
        "SOURCE_SWITCHED",
    )


def test_axisSpecLoader_observableIndicators_matchContractFields() -> None:
    result = AxisSpecLoader().load(spec_root=_spec_root())
    observable = [i for i in result.indicators if i.is_observable]
    assert observable, "expected observable indicators"
    profiles_by_id = {p.indicator_id: p for p in result.profiles}
    definition_fields = {
        "frequency",
        "unit",
        "primary_source",
        "validation_source",
        "fallback_policy",
    }
    for ind in observable:
        profile = profiles_by_id[ind.indicator_id]
        assert profile.plain_language_summary
        assert profile.display_name_cn
        assert ind.layer_tag
        for field in definition_fields:
            assert getattr(ind, field, None) not in (None, ""), (
                f"{ind.indicator_id} missing contract field {field!r}"
            )


def test_axisSpecLoader_rejectsSpecRootOutsideAllowedRoots() -> None:
    evil_root = (PROJECT_ROOT.resolve().parent.parent / "evil_layer1_specs_outside").resolve()
    with pytest.raises(AxisSpecLoadError, match="spec_root"):
        AxisSpecLoader().load(
            spec_root=evil_root,
            enabled_axes=["environment"],
        )


def test_axisSpecLoader_engineeringRules_documentProjectionMetadata() -> None:
    result = AxisSpecLoader().load(spec_root=_spec_root(), enabled_axes=["environment"])
    env_guard = next(g for g in result.guardrails if g.axis_id == "ENVIRONMENT")
    assert env_guard.engineering_rules_path
    eng_path = PROJECT_ROOT / env_guard.engineering_rules_path
    text = eng_path.read_text(encoding="utf-8")
    assert "projection_method" in text
    assert "source_frequency_map" in text
