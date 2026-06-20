"""Layer 1 ingestion Phase 0 gate tests (Round 3 Batch 2.5 §8.1)."""

from __future__ import annotations

import json
import re

import duckdb
import yaml
from backend.app.datasources.capability_registry import SourceCapabilityRegistry
from backend.app.datasources.route_planner import SourceRoutePlanner
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.db.migrate import MIGRATIONS_DIR, apply_migrations
from backend.app.layer1_axes.observation_contract import (
    AXIS_OBSERVATION_DDL_COLUMNS,
    AXIS_OBSERVATION_TABLE,
    FETCH_TO_OBSERVATION_TRACE_VIA,
    WRITE_REQUEST_REQUIRED_FOR_OBSERVATION,
)
from backend.app.ops.db_inspector import FUTURE_PHASE_KEY_TABLES, KEY_TABLES
from tests.contract_gate_support import PROJECT_ROOT, load_yaml, scan_package_for_create_adapter

TASK_ROOT = PROJECT_ROOT / ".trellis/tasks/06-20-round3-batch2-5-layer1-obs-ingest"
PIPELINE_TESTS = TASK_ROOT / "research/layer1-ingestion-pipeline-tests.md"
SERVICE_CONTRACT = PROJECT_ROOT / "specs/contracts/datasource_service_contract.yaml"
LAYER1_AXES_CONFIG = PROJECT_ROOT / "configs/layer1_axes.yml"

MIGRATION_011 = PROJECT_ROOT / "backend/app/db/migrations/011_layer1_tables.sql"
SCHEMA_SQL = PROJECT_ROOT / "specs/schema/schema.sql"
SOURCE_REGISTRY = PROJECT_ROOT / "specs/datasource_registry/source_registry.yaml"
WRITE_CONTRACT = PROJECT_ROOT / "specs/contracts/write_contract.yaml"
LINEAGE_CONTRACT = PROJECT_ROOT / "specs/contracts/snapshot_lineage_contract.yaml"
LAYER1_AXIS_CONTRACT = PROJECT_ROOT / "specs/contracts/layer1_axis_contract.yaml"
DATA_QUALITY_RULES = PROJECT_ROOT / "specs/contracts/data_quality_rules.yaml"
DATA_CLI_CONTRACT = PROJECT_ROOT / "specs/contracts/data_cli_contract.yaml"
SOURCE_ROUTE_CONTRACT = PROJECT_ROOT / "specs/contracts/source_route_contract.yaml"
OPS_INSPECT_CONTRACT = PROJECT_ROOT / "specs/contracts/ops_db_inspect_contract.yaml"
MODULE_SPEC_DDL = PROJECT_ROOT / "docs/modules/layer1_global_regime_panel.md"

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

INGESTION_MIGRATIONS = (
    "004_ingestion_sources",
    "005_ingestion_validation",
    "006_ingestion_sync",
    "007_ingestion_sync_hardening",
    "008_lineage_fields",
    "009_fetch_log_check",
    "010_validation_report_not_null",
    "011_layer1_tables",
)

FROZEN_STAGED_INDICATOR = "ENV-E1-DGS10"
STAGED_DATA_DOMAIN = "macro_supplementary"
STAGED_OPERATION = "fetch_macro_series"


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


def test_layer1Ingestion_phase0_migration011_definesAxisTables() -> None:
    """migration 011 defines all Layer 1 axis tables."""
    migration_text = MIGRATION_011.read_text(encoding="utf-8")
    for table in LAYER1_AXIS_TABLES:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in migration_text


def test_layer1Ingestion_phase0_schemaSqlLagTrackedAsO02() -> None:
    """schema.sql lags migration 011 for axis tables — O-02 DEFERRED, not silent."""
    schema_text = SCHEMA_SQL.read_text(encoding="utf-8")
    missing = [t for t in LAYER1_AXIS_TABLES if t not in schema_text]
    assert "axis_observation" in missing
    assert len(missing) == len(LAYER1_AXIS_TABLES)


def test_layer1Ingestion_phase0_applyMigrations_createsAxisTables() -> None:
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    assert LAYER1_AXIS_TABLES.issubset(tables)
    versions = {row[0] for row in con.execute("SELECT version_id FROM schema_version").fetchall()}
    assert "011_layer1_tables" in versions
    con.close()


def test_layer1Migration_axisObservation_columnsMatchModuleSpec(migrated_con, tmp_path) -> None:
    """axis_observation columns match module spec DDL and observation_contract."""
    con = migrated_con(tmp_path)
    cols = _table_columns(con, AXIS_OBSERVATION_TABLE)
    assert set(AXIS_OBSERVATION_DDL_COLUMNS) == cols
    spec_text = MODULE_SPEC_DDL.read_text(encoding="utf-8")
    for col in AXIS_OBSERVATION_DDL_COLUMNS:
        assert col in spec_text
    con.close()


def test_layer1Ingestion_phase0_migrations004to011PresentOnDisk() -> None:
    """Ingestion-chain migration files 004–011 exist (018A Phase 0 gate scope)."""
    for version_id in INGESTION_MIGRATIONS:
        prefix = version_id.split("_", 1)[0]
        matches = list(MIGRATIONS_DIR.glob(f"{prefix}_*.sql"))
        assert matches, f"missing migration file for {version_id}"


def test_layer1Ingestion_phase0_ingestionChainTablesAfterApply() -> None:
    """Post-migrate DB contains ingestion evidence tables required for §3 trace."""
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    required = {
        "source_registry",
        "fetch_log",
        "file_registry",
        "validation_report",
        "write_audit_log",
        AXIS_OBSERVATION_TABLE,
    }
    assert required.issubset(tables)
    con.close()


def test_layer1_axes_doesNotImportCreateAdapter() -> None:
    violations = scan_package_for_create_adapter("layer1_axes")
    assert violations == [], (
        "layer1_axes must not import adapter factory: " + "; ".join(violations)
    )


def test_sourceRegistry_roles_forbidShadowEmergency() -> None:
    doc = yaml.safe_load(SOURCE_REGISTRY.read_text(encoding="utf-8")) or {}
    assert doc.get("source_role_model") == "Primary / Validation / FallbackPolicy"
    rules = doc.get("rules") or {}
    forbidden = {str(r) for r in (rules.get("legacy_roles_forbidden") or [])}
    assert forbidden >= {"Shadow", "Emergency", "shadow_source", "emergency_source"}
    text = SOURCE_REGISTRY.read_text(encoding="utf-8")
    for role in ("Shadow", "Emergency"):
        assert not re.search(rf"\b{role}\b\s*:", text)


def test_layer1Ingestion_phase0_frozenIndicator_stagedRouteCapabilityDeclared() -> None:
    """AC-P2-0: ENV-E1-DGS10 staged path uses macro_supplementary.fetch_macro_series."""
    reg = SourceRegistry(SOURCE_REGISTRY)
    reg.load()
    cap = SourceCapabilityRegistry()
    cap.load()
    cap.assert_source_domain_operation("akshare", STAGED_DATA_DOMAIN, STAGED_OPERATION)
    binding = reg.get_domain_roles(STAGED_DATA_DOMAIN)
    assert binding.primary_source_id == "akshare"
    planner = SourceRoutePlanner(source_registry=reg, capability_registry=cap)
    plan = planner.plan(
        data_domain=STAGED_DATA_DOMAIN,
        operation=STAGED_OPERATION,
        run_id="phase0-route",
        job_id="phase0-job",
    )
    assert plan.data_domain == STAGED_DATA_DOMAIN
    assert plan.operation == STAGED_OPERATION
    assert plan.selected_source_id == "akshare"
    assert plan.route_status == "READY"
    assert plan.candidates


def test_layer1Ingestion_phase0_writeContractMapsToObservationTarget() -> None:
    contract = load_yaml(WRITE_CONTRACT)
    required = set(contract["write_request"]["required"])
    assert set(WRITE_REQUEST_REQUIRED_FOR_OBSERVATION) == required
    reject_if = contract["validation_gate"]["reject_if"]
    assert "validation_status == FAILED" in reject_if
    assert "source_conflict_severity == severe" in reject_if


def test_layer1Ingestion_phase0_writeContractRejectIf_hasPlannedValidatorHooks() -> None:
    """§3.4 direct-validator path must honor write_contract.validation_gate.reject_if."""
    mapping = {
        "validation_status == FAILED": "DbValidationGate + DataQualityValidator",
        "source_conflict_severity == severe": "DbValidationGate + SourceConflictValidator",
        "manual_review_required == true and write_mode != manual_patch": "DbValidationGate",
    }
    contract = load_yaml(WRITE_CONTRACT)
    for rule in mapping:
        assert rule in contract["validation_gate"]["reject_if"]


def test_layer1Lineage_phase0_ddlStoresSerializedFetchIds(migrated_con, tmp_path) -> None:
    """Contract lists are JSON-serialized in VARCHAR columns (app-layer parse)."""
    con = migrated_con(tmp_path)
    cols = _table_columns(con, "axis_snapshot_lineage")
    assert "source_fetch_ids" in cols
    assert "source_content_hashes" in cols
    contract = load_yaml(LINEAGE_CONTRACT)
    assert contract["required_fields"]["source_fetch_ids"] == "list[string]"
    con.close()


def test_layer1Ingestion_phase0_dataQualityRules_layer1SectionExists() -> None:
    rules = load_yaml(DATA_QUALITY_RULES)
    layer1 = rules.get("layer1_rules") or []
    rule_ids = {r["id"] for r in layer1}
    assert rule_ids >= {
        "MISSING_SOURCE_USED",
        "FALLBACK_WITHOUT_REASON",
        "BLINDSPOT_SHOULD_NOT_HAVE_VALUE",
    }


def test_layer1Ingestion_phase0_layer1AxisContractRequiredFields() -> None:
    contract = load_yaml(LAYER1_AXIS_CONTRACT)
    assert "indicator_id" in contract["required_indicator_fields"]
    assert "FORBIDDEN_SUBSTITUTE_USED" in contract["quality_flags"]


def test_layer1Ingestion_phase0_dataCliContract_loadable() -> None:
    doc = load_yaml(DATA_CLI_CONTRACT)
    assert doc.get("purpose")
    assert "qmd data sync" in doc.get("commands", {})


def test_layer1Ingestion_phase0_sourceRouteContract_forbidsSilentFallback() -> None:
    doc = load_yaml(SOURCE_ROUTE_CONTRACT)
    assert "silent fallback is forbidden" in doc.get("purpose", "").lower()


def test_layer1Ingestion_phase0_noSilentFallback_backendScan() -> None:
    from tests.test_reference_adoption_guardrails import test_noSilentFallbackCopied

    test_noSilentFallbackCopied()


def test_layer1Ingestion_phase0_frozenIndicator_metadataEligible() -> None:
    """AC-P2-0: ENV-E1-DGS10 is enabled observable state indicator in axis spec."""
    cfg = load_yaml(LAYER1_AXES_CONFIG)
    spec_root = PROJECT_ROOT / cfg["spec_root"]
    env_spec = spec_root / "environment_axis" / "environment_axis_indicator_spec.yaml"
    doc = load_yaml(env_spec)
    indicators = []
    for section in (doc.get("modules") or {}).values():
        indicators.extend(section.get("indicators") or [])
    frozen = next(i for i in indicators if i["indicator_id"] == FROZEN_STAGED_INDICATOR)
    assert frozen["layer"] == "Layer1_State"
    assert frozen.get("primary_source")
    assert "forbidden" not in str(frozen).lower()
    assert "blindspot" not in frozen["indicator_id"].lower()


def test_layer1Ingestion_phase0_layer1AxesConfig_resolvesSpecRoot() -> None:
    """configs/layer1_axes.yml spec_root must resolve and include frozen indicator."""
    cfg = load_yaml(LAYER1_AXES_CONFIG)
    spec_root = PROJECT_ROOT / cfg["spec_root"]
    assert spec_root.is_dir()
    env_spec = spec_root / "environment_axis" / "environment_axis_indicator_spec.yaml"
    text = env_spec.read_text(encoding="utf-8")
    assert FROZEN_STAGED_INDICATOR in text


def test_layer1Ingestion_phase0_datasourceServiceFactoryBoundaryEnforced() -> None:
    """Semantic factory boundary: forbidden packages must not import create_adapter."""
    contract = load_yaml(SERVICE_CONTRACT)
    forbidden_pkgs = contract.get("call_boundaries", {}).get("forbidden_direct_callers") or []
    assert any("layer1_axes" in pkg for pkg in forbidden_pkgs)
    violations: list[str] = []
    for pkg in forbidden_pkgs:
        pkg_path = pkg.replace("backend.app.", "")
        violations.extend(scan_package_for_create_adapter(pkg_path))
    assert violations == [], (
        "forbidden packages must not import create_adapter: " + "; ".join(violations)
    )


def test_layer1Ingestion_phase0_validationGateModule_exposesDbValidationGate() -> None:
    from backend.app.db.validation_gate import DbValidationGate, ValidationRejected

    assert DbValidationGate.__name__ == "DbValidationGate"
    assert ValidationRejected.__name__ == "ValidationRejected"


def test_layer1Ingestion_phase0_resourceGuard_exposesCheckBeforeFetch() -> None:
    from backend.app.core.resource_guard import Decision, ResourceGuard

    assert hasattr(ResourceGuard, "check")
    assert Decision.PAUSE.value == "PAUSE"


def test_dbInspect_keyTables_includeLayer1AxisTables() -> None:
    contract_tables = load_yaml(OPS_INSPECT_CONTRACT)["key_tables"]
    for table in LAYER1_AXIS_TABLES:
        assert table in KEY_TABLES
        assert table in contract_tables
    for future in FUTURE_PHASE_KEY_TABLES:
        assert future in KEY_TABLES


def test_layer1Ingestion_phase0_axisObservation_noDbCheck_classified() -> None:
    """ADR-002: axis_observation CHECK deferred; app validators enforce no-future-data."""
    ddl = MIGRATION_011.read_text(encoding="utf-8")
    obs_block = ddl.split("CREATE TABLE IF NOT EXISTS axis_observation")[1].split(");")[0]
    assert "CHECK" not in obs_block.upper()


def test_layer1Ingestion_phase0_fetchTraceFieldsDocumented() -> None:
    assert len(FETCH_TO_OBSERVATION_TRACE_VIA) >= 3
    assert "validation_report.source_fetch_ids_json" in FETCH_TO_OBSERVATION_TRACE_VIA


def test_layer1Ingestion_phase0_stagedFixturePresent() -> None:
    """AC-P2-0 / §8.4: staged macro fixture exists before micro-fetch."""
    fixture = PROJECT_ROOT / "tests/fixtures/layer1_macro_observation_fixture.json"
    assert fixture.is_file()
    doc = json.loads(fixture.read_text(encoding="utf-8"))
    assert doc["indicator_id"] == FROZEN_STAGED_INDICATOR
    assert doc["series_id"] == "DGS10"
    assert doc["as_of"] == "2024-06-15"


def test_layer1Ingestion_phase0_axisObservationWritePath_deferredToPhase4() -> None:
    """Phase 0 records Phase 4 closure test; commit/micro-fetch deferred to §8.4–8.5."""
    ingestion = PROJECT_ROOT / "backend/app/layer1_axes/ingestion.py"
    assert ingestion.is_file()
    text = ingestion.read_text(encoding="utf-8")
    assert "commit_clean_observation" not in text
    assert "micro_fetch_staging" not in text
    assert "DuckDBWriteManager" not in text
    closure_test = "test_layer1Observation_cleanWrite_usesWriteManager"
    pipeline_tests = PIPELINE_TESTS.read_text(encoding="utf-8")
    assert closure_test in pipeline_tests
