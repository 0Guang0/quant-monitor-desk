"""R3X residual open-items closure regression umbrella (PROMPT_15)."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from backend.app.datasources.adapters import _ADAPTER_TYPES
from backend.app.datasources.exceptions import AdapterConfigurationError
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.route_planner import SourceRoutePlanner
from backend.app.datasources.service import DataSourceService, _default_operation
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.layer1_axes.feature_engine import AxisFeatureEngine
from backend.app.layer1_axes.interpretation import AxisInterpretationEngine, InterpretationRejectedError
from backend.app.validators.source_conflict import CONFLICT_DOMAIN_ALIASES, SourceConflictValidator
from tests.contract_gate_support import PROJECT_ROOT, load_yaml
from tests.service_path_support import production_route_planner

SOURCE_REGISTRY = PROJECT_ROOT / "specs/datasource_registry/source_registry.yaml"


def test_advR3xRoute001_validationOnlyPrimaryBlocked() -> None:
    """ADV-R3X-ROUTE-001: validation_only source must not be sole READY Primary."""
    planner = production_route_planner()
    plan = planner.plan(
        data_domain="macro_supplementary",
        operation="fetch_macro_series",
        run_id="r3x-route-001",
        job_id="j3x-route-001",
    )
    assert plan.route_status in {"VALIDATION_ONLY_BLOCKED", "DISABLED_SOURCE", "NO_AVAILABLE_SOURCE"}
    assert plan.selected_source_id is None
    akshare = next(c for c in plan.candidates if c.source_id == "akshare")
    assert akshare.skip_reason == "validation_only_cannot_be_primary"


def test_advR3xRoute003_domainDisabledByDefault() -> None:
    """ADV-R3X-ROUTE-003: domain_enabled_by_default=false returns DISABLED_SOURCE."""
    planner = production_route_planner()
    plan = planner.plan(
        data_domain="cn_equity_minute_bar",
        operation="fetch_minute_bar",
        run_id="r3x-route-003",
        job_id="j3x-route-003",
    )
    assert plan.route_status == "DISABLED_SOURCE"
    assert "DOMAIN_DISABLED_BY_DEFAULT" in plan.quality_flags


def test_advR3xRoute004_validationRoleAddsQualityFlag() -> None:
    """ADV-R3X-ROUTE-004: Validation role selection adds quality flag."""
    registry = SourceRegistry()
    registry.load(SOURCE_REGISTRY)
    from backend.app.datasources.capability_registry import SourceCapabilityRegistry

    planner = SourceRoutePlanner(
        source_registry=registry,
        capability_registry=SourceCapabilityRegistry(),
    )
    plan = planner.plan(
        data_domain="cn_equity_daily_bar",
        operation="fetch_daily_bar",
        run_id="r3x-route-004",
        job_id="j3x-route-004",
        extra_candidates=[("akshare", "Validation")],
    )
    if plan.selected_source_id == "akshare":
        assert "VALIDATION_SOURCE_USED" in plan.quality_flags


def test_advR3xService001_productionFetchRequiresFileRegistry() -> None:
    """ADV-R3X-SERVICE-001: production fetch must not silently use test adapter."""
    service = DataSourceService()
    req = FetchRequest(
        run_id="r3x-svc",
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
    )
    con = duckdb.connect(":memory:")
    with pytest.raises(AdapterConfigurationError, match="fetch_port"):
        service.fetch(req, con=con, job_id=None)


def test_advR3xConflict001_domainAliasThresholdLookup() -> None:
    """ADV-R3X-CONFLICT-001: cn_equity_daily_bar aliases to market_bar_1d thresholds."""
    validator = SourceConflictValidator()
    threshold = validator._threshold_for("cn_equity_daily_bar", "close")
    assert threshold is not None
    assert "cn_equity_daily_bar" in CONFLICT_DOMAIN_ALIASES


def test_advA2_009_tdxPytdxRegisteredInFactory() -> None:
    """ADV-A2-009: TdxPytdxAdapter registered (disabled-by-default unchanged)."""
    assert "tdx_pytdx" in _ADAPTER_TYPES


def test_advA2_004_cninfoSupportsFilingsDomains() -> None:
    """ADV-A2-004: cninfo adapter declares cn_filings and cn_pdf_reports."""
    from backend.app.datasources.adapters.cninfo import CninfoAdapter

    assert "cn_filings" in CninfoAdapter.supported_domains
    assert "cn_pdf_reports" in CninfoAdapter.supported_domains


def test_advA1_001_writeRequestRequiresDataDomain(tmp_path: Path) -> None:
    """ADV-A1-001: WriteRequest without data_domain is rejected."""
    from backend.app.db.connection import ConnectionManager
    from backend.app.db.migrate import apply_migrations
    from backend.app.db.write_manager import WriteRequest
    from tests.db_helpers import create_test_write_manager

    db = tmp_path / "wm.duckdb"
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
    wm = create_test_write_manager(cm)
    req = WriteRequest(
        run_id="r",
        job_id="j",
        target_table="t",
        staging_table="s",
        write_mode="append_only",
        primary_keys=("id",),
        validation_report_id="stub-pass-x",
        source_used="baostock",
        data_domain="",
    )
    with pytest.raises(ValueError, match="data_domain"):
        wm.write(req)


def test_advA5_001_gitignoreSecretPatterns() -> None:
    """ADV-A5-001: .gitignore includes secret file patterns."""
    text = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in ("*.secret", "*.key", "credentials.*"):
        assert pattern in text


def test_advA6_004_viteApiProxy() -> None:
    """ADV-A6-004: Vite dev proxy forwards /api/* to backend."""
    text = (PROJECT_ROOT / "frontend/vite.config.ts").read_text(encoding="utf-8")
    assert '"/api"' in text


def test_advR3xL1_002_interpretationRejectsForbiddenTerms() -> None:
    """ADV-R3X-L1-002 / ADV-A4-002: forbidden terms reject write path."""
    from tests.test_layer1_interpretation import _history

    engine = AxisInterpretationEngine()
    hist = _history("ENV-E1-EFFR", 5)
    feat = AxisFeatureEngine(min_obs_required=3, window_len=10).compute_features(
        as_of=hist[-1].as_of_timestamp,
        observations=[hist[-1]],
        history=hist,
    )[0]
    with pytest.raises(InterpretationRejectedError):
        engine.build_interpretation(
            as_of=hist[-1].as_of_timestamp,
            features=[feat],
            templates={feat.indicator_id: "建议买入"},
        )


def test_advR3xCap002_tdxPytdxFactoryParity() -> None:
    """ADV-R3X-CAP-002: tdx_pytdx factory registration matches qmt pattern."""
    assert "qmt_xtdata" in _ADAPTER_TYPES
    assert "tdx_pytdx" in _ADAPTER_TYPES


def test_defaultOperation_coversAllDomainRoles() -> None:
    """Regression: domain_roles keys remain mapped in _default_operation."""
    registry = load_yaml(SOURCE_REGISTRY)
    role_keys = set((registry.get("domain_roles") or {}).keys())
    assert all(_default_operation(k) for k in role_keys)


def test_advR3xWrite002_unsupportedWriteModeRejected(tmp_path) -> None:
    """ADV-R3X-WRITE-002: contract write_modes not yet implemented are rejected."""
    from backend.app.db.connection import ConnectionManager
    from backend.app.db.migrate import apply_migrations
    from backend.app.db.write_manager import WriteRequest
    from tests.db_helpers import create_test_write_manager

    db = tmp_path / "wm2.duckdb"
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
    wm = create_test_write_manager(cm)
    req = WriteRequest(
        run_id="r",
        job_id="j",
        target_table="t",
        staging_table="s",
        write_mode="replace_partition",
        primary_keys=("id",),
        validation_report_id="stub-pass-x",
        source_used="baostock",
        data_domain="cn_equity_daily_bar",
    )
    with pytest.raises(ValueError, match="not implemented"):
        wm.write(req)


def test_advA2_002_healthCheckStub(tmp_path: Path) -> None:
    """ADV-A2-002: BaseDataAdapter.health_check returns structured stub."""
    from backend.app.datasources.adapters import create_test_adapter
    from backend.app.datasources.source_registry import SourceRegistry

    registry = SourceRegistry()
    registry.load()
    adapter = create_test_adapter("baostock", registry, tmp_path)
    report = adapter.health_check()
    assert report["status"] == "STUB_OK"
    assert "cn_equity_daily_bar" in report["supported_domains"]


def test_advR3xCap001_compatibilityMapEmpty() -> None:
    """ADV-R3X-CAP-001: legacy compatibility map cleared; adapters use registry domains."""
    from backend.app.datasources.capability_registry import ADAPTER_DOMAIN_COMPATIBILITY_MAP

    assert ADAPTER_DOMAIN_COMPATIBILITY_MAP == {}


def test_advA3_016_orchestratorDeferredRunners(tmp_path) -> None:
    """ADV-A3-016: run_full_load / run_data_quality explicit deferred APIs."""
    from backend.app.db.connection import ConnectionManager
    from backend.app.db.migrate import apply_migrations
    from backend.app.sync.jobs import SyncJobSpec
    from backend.app.sync.orchestrator import DataSyncOrchestrator
    from datetime import date

    db = tmp_path / "orch.duckdb"
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
    orch = DataSyncOrchestrator(cm)
    spec = SyncJobSpec(
        run_id="r",
        job_id="j",
        job_type="full_load",
        data_domain="cn_equity_daily_bar",
        market_id="CN_A",
        source_id="baostock",
        adapter_id=None,
        date_start=date(2026, 1, 1),
        date_end=date(2026, 1, 2),
        instrument_id=None,
        partition_key=None,
        trigger_reason=None,
    )
    with pytest.raises(NotImplementedError, match="run_full_load"):
        orch.run_full_load(spec)
    with pytest.raises(NotImplementedError, match="run_data_quality"):
        orch.run_data_quality(spec)


def test_advA1_012_minStagingRowsEnforced(tmp_path) -> None:
    """ADV-A1-012 / ADV-A1-015: empty staging rejected before clean write."""
    from backend.app.db.connection import ConnectionManager
    from backend.app.db.migrate import apply_migrations
    from backend.app.db.write_manager import WriteRequest
    from tests.db_helpers import create_test_write_manager

    db = tmp_path / "empty-stg.duckdb"
    cm = ConnectionManager(db)
    with cm.writer() as con:
        apply_migrations(con)
        con.execute("CREATE TABLE t (id INTEGER)")
        con.execute("CREATE TABLE s (id INTEGER)")
    wm = create_test_write_manager(cm)
    req = WriteRequest(
        run_id="r",
        job_id="j",
        target_table="t",
        staging_table="s",
        write_mode="append_only",
        primary_keys=("id",),
        validation_report_id="stub-pass-x",
        source_used="baostock",
        data_domain="cn_equity_daily_bar",
    )
    with pytest.raises(ValueError, match="minimum"):
        wm.write(req)
