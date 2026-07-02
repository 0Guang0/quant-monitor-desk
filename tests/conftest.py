"""Shared pytest fixtures."""

from __future__ import annotations

import os
import warnings
from pathlib import Path

import duckdb
import pytest

try:
    from starlette.exceptions import StarletteDeprecationWarning

    warnings.filterwarnings("ignore", category=StarletteDeprecationWarning)
except ImportError:
    pass

from backend.app.datasources.fetch_result import FetchRequest, FetchResult
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.db.migrate import apply_migrations

try:
    import httpx2  # noqa: F401
except ImportError:
    pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"


def pytest_configure(config) -> None:
    try:
        from starlette.exceptions import StarletteDeprecationWarning

        warnings.filterwarnings("ignore", category=StarletteDeprecationWarning)
    except ImportError:
        pass
    _ensure_v2_evidence_mock_baostock()
    _ensure_prediction_live_authorization_bootstrap()
    _ensure_r3g_fred_authorization_bootstrap()
    _ensure_audit_sandbox_pytest_basetemp()


def _ensure_v2_evidence_mock_baostock() -> None:
    """Materialize v2 archive evidence raw payload for data-health integration (OPEN-01)."""
    dest = PROJECT_ROOT / ".audit-sandbox" / "mock" / "baostock.json"
    if dest.is_file():
        return
    src = FIXTURES / "data_health" / "v2_baostock_raw.json"
    if not src.is_file():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(src.read_bytes())


def _ensure_prediction_live_authorization_bootstrap() -> None:
    """Materialize R3H-04 live-smoke auth YAML for fresh clones/worktrees."""
    dest = (
        PROJECT_ROOT
        / ".audit-sandbox"
        / "round3h"
        / "prediction_market_live_authorization.yaml"
    )
    if dest.is_file():
        return
    src = FIXTURES / "prediction_market_live_authorization.template.yaml"
    if not src.is_file():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(src.read_bytes())


def _ensure_r3g_fred_authorization_bootstrap() -> None:
    """Materialize R3G FRED auth YAML for fresh clones/worktrees."""
    dest = PROJECT_ROOT / ".audit-sandbox" / "round3g" / "fred_user_authorization.yaml"
    if dest.is_file():
        return
    src = FIXTURES / "sandbox_clean_write" / "r3g01" / "fred" / "fred_user_authorization_fixture.yaml"
    if not src.is_file():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(src.read_bytes())


def _ensure_audit_sandbox_pytest_basetemp() -> None:
    """Pre-create shared pytest basetemp for A8 sandbox runs on fresh clones (A8-B3V-04)."""
    (PROJECT_ROOT / ".audit-sandbox" / "pytest").mkdir(parents=True, exist_ok=True)


def _patch_path_for_windows_long_paths() -> None:
    """A8 basetemp under deep .audit-sandbox paths exceeds MAX_PATH on Windows."""
    if os.name != "nt":
        return
    from backend.app.storage.path_compat import (
        needs_extended_path,
        to_extended_path,
    )

    _orig_is_file = Path.is_file
    _orig_exists = Path.exists
    _orig_read_text = Path.read_text
    _orig_read_bytes = Path.read_bytes

    def _is_file(self, follow_symlinks: bool = True) -> bool:
        if needs_extended_path(self):
            return _orig_is_file(to_extended_path(self), follow_symlinks=follow_symlinks)
        return _orig_is_file(self, follow_symlinks=follow_symlinks)

    def _exists(self, follow_symlinks: bool = True) -> bool:
        if needs_extended_path(self):
            return _orig_exists(to_extended_path(self), follow_symlinks=follow_symlinks)
        return _orig_exists(self, follow_symlinks=follow_symlinks)

    def _read_text(self, encoding: str | None = None, errors: str | None = None) -> str:
        if needs_extended_path(self):
            return _orig_read_text(to_extended_path(self), encoding=encoding, errors=errors)
        return _orig_read_text(self, encoding=encoding, errors=errors)

    def _read_bytes(self) -> bytes:
        if needs_extended_path(self):
            return _orig_read_bytes(to_extended_path(self))
        return _orig_read_bytes(self)

    Path.is_file = _is_file  # type: ignore[method-assign]
    Path.exists = _exists  # type: ignore[method-assign]
    Path.read_text = _read_text  # type: ignore[method-assign]
    Path.read_bytes = _read_bytes  # type: ignore[method-assign]


_patch_path_for_windows_long_paths()


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-network",
        action="store_true",
        default=False,
        help="Run tests marked @pytest.mark.network (live vendor fetch)",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-network"):
        return
    skip_network = pytest.mark.skip(reason="need --run-network for live vendor fetch tests")
    for item in items:
        if "network" in item.keywords:
            item.add_marker(skip_network)


_SKIP_RESOURCE_GUARD_AUTOPATCH = frozenset(
    {"test_resource_guard.py", "test_foundation_smoke.py"}
)


@pytest.fixture(autouse=True)
def _resourceGuardOkUnlessTestOverrides(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ponytail: unit tests must not flake on host memory; guard cases patch their own check."""
    if request.node.fspath and request.node.fspath.basename in _SKIP_RESOURCE_GUARD_AUTOPATCH:
        return
    from backend.app.core.resource_guard import Decision, ResourceGuard

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))


@pytest.fixture
def registry_yaml_fixture() -> Path:
    return FIXTURES / "source_registry_valid.yaml"


@pytest.fixture
def bad_shadow_yaml() -> Path:
    return FIXTURES / "bad_shadow.yaml"


@pytest.fixture
def bad_emergency_yaml() -> Path:
    return FIXTURES / "bad_emergency.yaml"


@pytest.fixture
def bad_top_level_shadow_source_yaml() -> Path:
    return FIXTURES / "bad_top_level_shadow_source.yaml"


@pytest.fixture
def bad_top_level_emergency_source_yaml() -> Path:
    return FIXTURES / "bad_top_level_emergency_source.yaml"


@pytest.fixture
def bad_primary_domain_mismatch_yaml() -> Path:
    return FIXTURES / "bad_primary_domain_mismatch.yaml"


@pytest.fixture
def bad_bool_string_yaml() -> Path:
    return FIXTURES / "bad_bool_string.yaml"


@pytest.fixture
def bad_validation_disabled_yaml() -> Path:
    return FIXTURES / "bad_validation_disabled.yaml"


@pytest.fixture
def bad_validation_domain_mismatch_yaml() -> Path:
    return FIXTURES / "bad_validation_domain_mismatch.yaml"


@pytest.fixture
def bad_validation_string_null_yaml() -> Path:
    return FIXTURES / "bad_validation_string_null.yaml"


@pytest.fixture
def bad_unknown_primary_yaml() -> Path:
    return FIXTURES / "bad_unknown_primary.yaml"


@pytest.fixture
def bad_unknown_license_primary_yaml() -> Path:
    return FIXTURES / "bad_unknown_license_primary.yaml"


@pytest.fixture
def bad_invalid_fallback_yaml() -> Path:
    return FIXTURES / "bad_invalid_fallback.yaml"


@pytest.fixture
def malformed_yaml() -> Path:
    return FIXTURES / "malformed.yaml"


@pytest.fixture
def disabled_registry():
    p = FIXTURES / "source_registry_disabled_baostock.yaml"
    reg = SourceRegistry(p)
    reg.load()
    return reg


@pytest.fixture
def loaded_registry(registry_yaml_fixture):
    reg = SourceRegistry(registry_yaml_fixture)
    reg.load()
    return reg


@pytest.fixture
def batch_b_registry():
    p = FIXTURES / "source_registry_batch_b.yaml"
    reg = SourceRegistry(p)
    reg.load()
    return reg


@pytest.fixture
def baostock_skeleton_class():
    from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase

    class BaostockSkeleton(SkeletonAdapterBase):
        source_id = "baostock"
        supported_domains = frozenset({"cn_equity_daily_bar", "cn_equity_basic_financial"})

    return BaostockSkeleton


@pytest.fixture
def baostock_skeleton_market_only_class():
    from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase

    class BaostockSkeleton(SkeletonAdapterBase):
        source_id = "baostock"
        supported_domains = frozenset({"cn_equity_daily_bar"})

    return BaostockSkeleton


@pytest.fixture
def migrated_con():
    def _open(tmp_path):
        db = tmp_path / "t.duckdb"
        con = duckdb.connect(str(db))
        apply_migrations(con)
        return con

    return _open


@pytest.fixture
def request_factory():
    def _make(source_id: str, domain: str = "market_bar_1d") -> FetchRequest:
        return FetchRequest(run_id="run-1", source_id=source_id, data_domain=domain)

    return _make


@pytest.fixture
def success_result():
    def _make():
        return FetchResult(
            run_id="run-1",
            source_id="baostock",
            data_domain="market_bar_1d",
            status="SUCCESS",
            row_count=42,
            fetch_time="2026-06-17T10:00:00Z",
            staging_table="stg_batch_a_smoke",
            raw_file_paths=["/data/raw/baostock/run-1.parquet"],
            content_hash="abc",
            schema_hash="def",
        )

    return _make


@pytest.fixture
def network_error_result():
    def _make():
        return FetchResult(
            run_id="run-1",
            source_id="baostock",
            data_domain="market_bar_1d",
            status="NETWORK_ERROR",
            row_count=0,
            fetch_time="2026-06-17T10:00:00Z",
            error_message="timeout",
        )

    return _make


@pytest.fixture
def empty_response_result():
    def _make():
        return FetchResult(
            run_id="run-1",
            source_id="baostock",
            data_domain="market_bar_1d",
            status="EMPTY_RESPONSE",
            row_count=0,
            fetch_time="2026-06-17T10:00:00Z",
            staging_table=None,
            raw_file_paths=[],
        )

    return _make


@pytest.fixture
def raw_data_root(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    return root


@pytest.fixture
def non_sandbox_data_root(tmp_path: Path) -> Path:
    """QMD_DATA_ROOT without `.audit-sandbox` in resolved parts (A8 basetemp safe)."""
    root = PROJECT_ROOT / ".pytest-non-sandbox-data" / f"case-{id(tmp_path)}"
    root.mkdir(parents=True, exist_ok=True)
    return root


@pytest.fixture
def file_registry_stack(tmp_path):
    """ConnectionManager + WriteManager + FileRegistry + RawStore on tmp_path DB."""
    from backend.app.db.connection import ConnectionManager
    from backend.app.storage.file_registry import FileRegistry
    from backend.app.storage.raw_store import RawStore
    from tests.db_helpers import create_test_write_manager

    db = tmp_path / "t.duckdb"
    con = duckdb.connect(str(db))
    apply_migrations(con)
    con.close()
    cm = ConnectionManager(db)
    raw_root = tmp_path / "data"
    raw_root.mkdir(parents=True, exist_ok=True)
    return {
        "cm": cm,
        "raw_store": RawStore(raw_root),
        "file_registry": FileRegistry(
            cm,
            create_test_write_manager(cm),
            validation_report_id="stub-pass-registry",
        ),
    }


@pytest.fixture
def stub_fetch_bytes():
    return b'{"symbol":"000001","close":10.0}'
