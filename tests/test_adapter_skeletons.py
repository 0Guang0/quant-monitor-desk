"""Round 2 Batch B — adapter skeleton tests."""

from pathlib import Path

import pytest
from backend.app.storage.raw_store import sha256_hex


def test_adapterPackage_importable():
    import backend.app.datasources.adapters  # noqa: F401


def test_skeletonAdapterBase_successWritesRawFile(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
    stub_fetch_bytes,
):
    from backend.app.datasources.adapters.fetch_port import StubFetchPort
    from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase

    class BaostockSkeleton(SkeletonAdapterBase):
        source_id = "baostock"
        supported_domains = frozenset({"market_bar_1d", "fundamental"})

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = BaostockSkeleton(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
    )
    req = request_factory("baostock", "market_bar_1d")
    result = adapter.fetch(req, con=con)
    assert result.status == "SUCCESS"
    assert result.row_count == 1
    assert len(result.raw_file_paths) == 1
    assert Path(result.raw_file_paths[0]).is_file()
    assert result.content_hash == sha256_hex(stub_fetch_bytes)
    fetch_log_count = con.execute(
        "SELECT COUNT(*) FROM fetch_log WHERE run_id=?", [req.run_id]
    ).fetchone()[0]
    assert fetch_log_count == 1


def test_skeletonAdapterBase_registersFileRegistryWhenInjected(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
    stub_fetch_bytes,
):
    from backend.app.datasources.adapters.fetch_port import StubFetchPort
    from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase

    class BaostockSkeleton(SkeletonAdapterBase):
        source_id = "baostock"
        supported_domains = frozenset({"market_bar_1d"})

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = BaostockSkeleton(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
        file_registry=stack["file_registry"],
    )
    req = request_factory("baostock", "market_bar_1d")
    result = adapter.fetch(req, con=con)
    con.close()
    with stack["cm"].reader() as reader:
        row = reader.execute(
            "SELECT local_path, content_hash FROM file_registry WHERE local_path = ?",
            [result.raw_file_paths[0]],
        ).fetchone()
    assert row is not None
    assert row[0] == result.raw_file_paths[0]
    assert row[1] == result.content_hash


@pytest.mark.parametrize(
    "status,error_type",
    [
        ("AUTH_FAILED", "auth"),
        ("RATE_LIMITED", "rate_limit"),
        ("NETWORK_ERROR", "network"),
        ("SCHEMA_DRIFT", "schema"),
        ("EMPTY_RESPONSE", "empty"),
        ("FAILED", "failed"),
    ],
)
def test_portErrors_mapStatusAndFetchLog(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
    status,
    error_type,
):
    from backend.app.datasources.adapters.fetch_port import FailingPort
    from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase

    class BaostockSkeleton(SkeletonAdapterBase):
        source_id = "baostock"
        supported_domains = frozenset({"market_bar_1d"})

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = BaostockSkeleton(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=FailingPort(status=status, message=f"simulated {status}"),
    )
    req = request_factory("baostock", "market_bar_1d")
    result = adapter.fetch(req, con=con)
    assert result.status == status
    row = con.execute(
        "SELECT status, error_type FROM fetch_log WHERE run_id=?", [req.run_id]
    ).fetchone()
    assert row[0] == status and row[1] == error_type


def test_baostockAdapter_matchesRegistryDomains(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
    stub_fetch_bytes,
):
    from backend.app.datasources.adapters.baostock import BaostockAdapter
    from backend.app.datasources.adapters.fetch_port import StubFetchPort

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = BaostockAdapter(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
    )
    assert adapter.source_id == "baostock"
    assert "fundamental" in adapter.supported_domains
    req = request_factory("baostock", "fundamental")
    result = adapter.fetch(req, con=con)
    assert result.status == "SUCCESS"


def test_qmtAdapter_localClientMissing_returnsAuthFailed(
    tmp_path, migrated_con, batch_b_registry, request_factory, file_registry_stack,
):
    from backend.app.datasources.adapters.fetch_port import FailingPort
    from backend.app.datasources.adapters.qmt_xtdata import QmtXtdataAdapter

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = QmtXtdataAdapter(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=FailingPort("AUTH_FAILED", "QMT client not running"),
    )
    req = request_factory("qmt_xtdata", "market_bar_1m")
    result = adapter.fetch(req, con=con)
    assert result.status == "AUTH_FAILED"
    row = con.execute(
        "SELECT status, error_type FROM fetch_log WHERE run_id=?", [req.run_id]
    ).fetchone()
    assert row[0] == "AUTH_FAILED" and row[1] == "auth"


def test_qmtAdapter_stubClient_successWritesRaw(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
    stub_fetch_bytes,
):
    from backend.app.datasources.adapters.fetch_port import StubFetchPort
    from backend.app.datasources.adapters.qmt_xtdata import QmtXtdataAdapter

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = QmtXtdataAdapter(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
    )
    req = request_factory("qmt_xtdata", "market_bar_1m")
    result = adapter.fetch(req, con=con)
    assert result.status == "SUCCESS"
    assert result.raw_file_paths


@pytest.mark.parametrize(
    "adapter_cls,source_id,domain",
    [
        ("AkshareAdapter", "akshare", "capital_flow"),
        ("CninfoAdapter", "cninfo", "announcement"),
    ],
)
def test_vendorSkeleton_exposesSourceId(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
    stub_fetch_bytes,
    adapter_cls,
    source_id,
    domain,
):
    import importlib

    from backend.app.datasources.adapters.fetch_port import StubFetchPort

    mod = importlib.import_module("backend.app.datasources.adapters")
    cls = getattr(mod, adapter_cls)
    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = cls(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
    )
    assert adapter.source_id == source_id
    req = request_factory(source_id, domain)
    assert adapter.fetch(req, con=con).status == "SUCCESS"


def test_cninfoAdapter_unpublished_returnsEmptyResponse(
    tmp_path, migrated_con, batch_b_registry, request_factory, file_registry_stack,
):
    from backend.app.datasources.adapters.cninfo import CninfoAdapter
    from backend.app.datasources.adapters.fetch_port import UnpublishedPort

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = CninfoAdapter(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=UnpublishedPort(),
    )
    req = request_factory("cninfo", "announcement")
    result = adapter.fetch(req, con=con)
    assert result.status == "EMPTY_RESPONSE"
    assert "not published" in (result.error_message or "").lower()
    row = con.execute(
        "SELECT status, error_type FROM fetch_log WHERE run_id=?", [req.run_id]
    ).fetchone()
    assert row[0] == "EMPTY_RESPONSE" and row[1] == "empty"


def test_yahooAdapter_registryMarkedValidationOnly(batch_b_registry):
    rec = batch_b_registry.get("yahoo_finance")
    assert rec.validation_only is True


def test_createAdapter_unknownSource_raises(batch_b_registry, raw_data_root):
    from backend.app.datasources.adapters import create_adapter

    with pytest.raises(KeyError):
        create_adapter("not_a_source", batch_b_registry, raw_data_root)


def test_createAdapter_defaultFetchPort_success(
    tmp_path, migrated_con, batch_b_registry, request_factory, raw_data_root,
):
    from backend.app.datasources.adapters import create_adapter

    con = migrated_con(tmp_path)
    adapter = create_adapter(
        "baostock", batch_b_registry, raw_data_root, fetch_port=None,
    )
    req = request_factory("baostock", "market_bar_1d")
    result = adapter.fetch(req, con=con)
    assert result.status == "SUCCESS"


def test_skeletonAdapterBase_resolveAsOfFromEndTime(
    tmp_path,
    migrated_con,
    batch_b_registry,
    file_registry_stack,
    stub_fetch_bytes,
):
    from backend.app.datasources.adapters.fetch_port import StubFetchPort
    from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase
    from backend.app.datasources.fetch_result import FetchRequest

    class BaostockSkeleton(SkeletonAdapterBase):
        source_id = "baostock"
        supported_domains = frozenset({"market_bar_1d"})

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = BaostockSkeleton(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
    )
    req = FetchRequest(
        run_id="run-asof",
        source_id="baostock",
        data_domain="market_bar_1d",
        end_time="2026-06-01T15:30:00Z",
    )
    result = adapter.fetch(req, con=con)
    assert result.status == "SUCCESS"
    assert result.as_of_timestamp == "2026-06-01"
    assert "2026-06-01" in Path(result.raw_file_paths[0]).parts


def test_yahooAdapter_createAdapter_fetchesSuccessfully(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    raw_data_root,
):
    from backend.app.datasources.adapters import create_adapter

    con = migrated_con(tmp_path)
    adapter = create_adapter("yahoo_finance", batch_b_registry, raw_data_root)
    req = request_factory("yahoo_finance", "market_bar_1d")
    result = adapter.fetch(req, con=con)
    assert result.status == "SUCCESS"
    assert result.row_count == 1
    assert len(result.raw_file_paths) == 1


@pytest.mark.parametrize(
    "source_id,domain",
    [
        ("baostock", "market_bar_1d"),
        ("qmt_xtdata", "market_bar_1m"),
        ("akshare", "capital_flow"),
        ("cninfo", "announcement"),
        ("yahoo_finance", "market_bar_1d"),
    ],
)
def test_createAdapter_allRegisteredSources_success(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    raw_data_root,
    source_id,
    domain,
):
    from backend.app.datasources.adapters import create_adapter

    con = migrated_con(tmp_path)
    adapter = create_adapter(source_id, batch_b_registry, raw_data_root)
    req = request_factory(source_id, domain)
    result = adapter.fetch(req, con=con)
    assert result.status == "SUCCESS"
    assert result.raw_file_paths
