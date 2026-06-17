"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest
from backend.app.datasources.fetch_result import FetchRequest, FetchResult
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.db.migrate import apply_migrations

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"


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
