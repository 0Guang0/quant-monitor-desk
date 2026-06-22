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
    baostock_skeleton_class,
):
    from backend.app.datasources.adapters.fetch_port import StubFetchPort

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = baostock_skeleton_class(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
    )
    req = request_factory("baostock", "cn_equity_daily_bar")
    result = adapter.fetch(req, con=con, record_fetch_log=True)
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
        supported_domains = frozenset({"cn_equity_daily_bar"})

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = BaostockSkeleton(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
        file_registry=stack["file_registry"],
    )
    req = request_factory("baostock", "cn_equity_daily_bar")
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
        ("NOT_PUBLISHED_YET", "not_published"),
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
        supported_domains = frozenset({"cn_equity_daily_bar"})

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = BaostockSkeleton(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=FailingPort(status=status, message=f"simulated {status}"),
    )
    req = request_factory("baostock", "cn_equity_daily_bar")
    result = adapter.fetch(req, con=con, record_fetch_log=True)
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
    assert "cn_equity_basic_financial" in adapter.supported_domains
    req = request_factory("baostock", "cn_equity_basic_financial")
    result = adapter.fetch(req, con=con)
    assert result.status == "SUCCESS"


def test_qmtAdapter_localClientMissing_returnsAuthFailed(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
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
    req = request_factory("qmt_xtdata", "cn_equity_minute_bar")
    result = adapter.fetch(req, con=con, record_fetch_log=True)
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
    req = request_factory("qmt_xtdata", "cn_equity_minute_bar")
    result = adapter.fetch(req, con=con)
    assert result.status == "SUCCESS"
    assert result.raw_file_paths


@pytest.mark.parametrize(
    "adapter_cls,source_id,domain",
    [
        ("AkshareAdapter", "akshare", "macro_supplementary"),
        ("CninfoAdapter", "cninfo", "cn_announcements"),
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


def test_cninfoAdapter_unpublished_returnsNotPublishedYet(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
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
    req = request_factory("cninfo", "cn_announcements")
    result = adapter.fetch(req, con=con, record_fetch_log=True)
    assert result.status == "NOT_PUBLISHED_YET"
    assert "not published" in (result.error_message or "").lower()
    row = con.execute(
        "SELECT status, error_type FROM fetch_log WHERE run_id=?", [req.run_id]
    ).fetchone()
    assert row[0] == "NOT_PUBLISHED_YET" and row[1] == "not_published"


def test_yahooAdapter_registryMarkedValidationOnly(batch_b_registry):
    rec = batch_b_registry.get("yahoo_finance")
    assert rec.validation_only is True


def test_createAdapter_unknownSource_raisesAdapterNotSupportedError(
    batch_b_registry,
    raw_data_root,
    file_registry_stack,
    stub_fetch_bytes,
):
    from backend.app.datasources.adapters import create_adapter
    from backend.app.datasources.adapters.fetch_port import StubFetchPort
    from backend.app.datasources.exceptions import AdapterNotSupportedError

    stack = file_registry_stack
    with pytest.raises(AdapterNotSupportedError) as exc_info:
        create_adapter(
            "not_a_source",
            batch_b_registry,
            raw_data_root,
            fetch_port=StubFetchPort(payload=stub_fetch_bytes),
            file_registry=stack["file_registry"],
        )
    assert exc_info.value.source_id == "not_a_source"
    assert "baostock" in exc_info.value.known


def test_createAdapter_withoutFetchPort_raisesAdapterConfigurationError(
    batch_b_registry,
    raw_data_root,
    file_registry_stack,
):
    from backend.app.datasources.adapters import create_adapter
    from backend.app.datasources.exceptions import AdapterConfigurationError

    stack = file_registry_stack
    with pytest.raises(AdapterConfigurationError, match="fetch_port is required"):
        create_adapter(
            "baostock",
            batch_b_registry,
            raw_data_root,
            file_registry=stack["file_registry"],
        )


def test_createAdapter_withoutFileRegistry_raisesAdapterConfigurationError(
    batch_b_registry,
    raw_data_root,
    stub_fetch_bytes,
):
    from backend.app.datasources.adapters import create_adapter
    from backend.app.datasources.adapters.fetch_port import StubFetchPort
    from backend.app.datasources.exceptions import AdapterConfigurationError

    with pytest.raises(AdapterConfigurationError, match="file_registry is required"):
        create_adapter(
            "baostock",
            batch_b_registry,
            raw_data_root,
            fetch_port=StubFetchPort(payload=stub_fetch_bytes),
        )


def test_createTestAdapter_defaultStubFetchPort_success(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    raw_data_root,
):
    from backend.app.datasources.adapters import create_test_adapter

    con = migrated_con(tmp_path)
    adapter = create_test_adapter("baostock", batch_b_registry, raw_data_root)
    req = request_factory("baostock", "cn_equity_daily_bar")
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
        supported_domains = frozenset({"cn_equity_daily_bar"})

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
        data_domain="cn_equity_daily_bar",
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
    file_registry_stack,
    stub_fetch_bytes,
):
    from backend.app.datasources.adapters import create_adapter
    from backend.app.datasources.adapters.fetch_port import StubFetchPort

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = create_adapter(
        "yahoo_finance",
        batch_b_registry,
        raw_data_root,
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
        file_registry=stack["file_registry"],
    )
    req = request_factory("yahoo_finance", "us_equity_daily_bar")
    result = adapter.fetch(req, con=con)
    assert result.status == "SUCCESS"
    assert result.row_count == 1
    assert len(result.raw_file_paths) == 1


@pytest.mark.parametrize(
    "source_id,domain",
    [
        ("baostock", "cn_equity_daily_bar"),
        ("qmt_xtdata", "cn_equity_minute_bar"),
        ("akshare", "macro_supplementary"),
        ("cninfo", "cn_announcements"),
        ("yahoo_finance", "us_equity_daily_bar"),
    ],
)
def test_createAdapter_allRegisteredSources_success(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    raw_data_root,
    file_registry_stack,
    stub_fetch_bytes,
    source_id,
    domain,
):
    from backend.app.datasources.adapters import create_adapter
    from backend.app.datasources.adapters.fetch_port import StubFetchPort

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = create_adapter(
        source_id,
        batch_b_registry,
        raw_data_root,
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
        file_registry=stack["file_registry"],
    )
    req = request_factory(source_id, domain)
    result = adapter.fetch(req, con=con)
    assert result.status == "SUCCESS"
    assert result.raw_file_paths


def test_largePayload_returnsFailedAndDoesNotWriteRaw(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
):
    from backend.app.datasources.adapters.fetch_port import StubFetchPort
    from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase

    class BaostockSkeleton(SkeletonAdapterBase):
        source_id = "baostock"
        supported_domains = frozenset({"cn_equity_daily_bar"})

    huge = b"x" * 200
    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = BaostockSkeleton(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=huge),
        max_payload_bytes=100,
    )
    req = request_factory("baostock", "cn_equity_daily_bar")
    result = adapter.fetch(req, con=con)
    assert result.status == "FAILED"
    assert "payload too large" in (result.error_message or "")
    assert not result.raw_file_paths


def test_payloadRowCount_propagatesToFetchResultAndFetchLog(
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
        supported_domains = frozenset({"cn_equity_daily_bar"})

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = BaostockSkeleton(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes, row_count=42),
    )
    req = request_factory("baostock", "cn_equity_daily_bar")
    result = adapter.fetch(req, con=con, record_fetch_log=True)
    assert result.row_count == 42
    row = con.execute("SELECT row_count FROM fetch_log WHERE run_id=?", [req.run_id]).fetchone()
    assert row[0] == 42


def test_payloadSchemaHash_propagatesToFetchResultAndFetchLog(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
):
    from backend.app.datasources.adapters.fetch_port import StubFetchPort
    from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase

    class BaostockSkeleton(SkeletonAdapterBase):
        source_id = "baostock"
        supported_domains = frozenset({"cn_equity_daily_bar"})

    schema_hash = "abc123schema"
    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = BaostockSkeleton(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=b'{"a":1}', schema_hash=schema_hash),
    )
    req = request_factory("baostock", "cn_equity_daily_bar")
    result = adapter.fetch(req, con=con, record_fetch_log=True)
    assert result.schema_hash == schema_hash
    row = con.execute("SELECT schema_hash FROM fetch_log WHERE run_id=?", [req.run_id]).fetchone()
    assert row[0] == schema_hash


def test_payloadRetryCount_propagatesToFetchResultAndFetchLog(
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
        supported_domains = frozenset({"cn_equity_daily_bar"})

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = BaostockSkeleton(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes, retry_count=3),
    )
    req = request_factory("baostock", "cn_equity_daily_bar")
    result = adapter.fetch(req, con=con, record_fetch_log=True)
    assert result.retry_count == 3
    row = con.execute("SELECT retry_count FROM fetch_log WHERE run_id=?", [req.run_id]).fetchone()
    assert row[0] == 3


def test_fetchRecordsLatencyMsWhenPayloadOmitsIt(
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
        supported_domains = frozenset({"cn_equity_daily_bar"})

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = BaostockSkeleton(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
    )
    req = request_factory("baostock", "cn_equity_daily_bar")
    result = adapter.fetch(req, con=con, record_fetch_log=True)
    assert result.latency_ms is not None
    assert result.latency_ms >= 0
    row = con.execute("SELECT latency_ms FROM fetch_log WHERE run_id=?", [req.run_id]).fetchone()
    assert row[0] is not None


def test_inferSchemaHash_detectsNestedStructureDrift():
    from backend.app.datasources.adapters.fetch_port import FetchPayload
    from backend.app.datasources.adapters.skeleton_base import _infer_schema_hash

    base = _infer_schema_hash(FetchPayload(content=b'{"a": {"b": 1}}', file_type="json"))
    nested = _infer_schema_hash(FetchPayload(content=b'{"a": {"c": 1}}', file_type="json"))
    assert base != nested


def test_inferSchemaHash_detectsTypeDrift():
    from backend.app.datasources.adapters.fetch_port import FetchPayload
    from backend.app.datasources.adapters.skeleton_base import _infer_schema_hash

    as_int = _infer_schema_hash(FetchPayload(content=b'{"a": 1}', file_type="json"))
    as_str = _infer_schema_hash(FetchPayload(content=b'{"a": "1"}', file_type="json"))
    assert as_int != as_str


def test_resolveAsOf_isoTimestamp_normalizesToDate(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
    stub_fetch_bytes,
):
    from backend.app.datasources.adapters.fetch_port import StubFetchPort
    from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase
    from backend.app.datasources.fetch_result import FetchRequest

    class BaostockSkeleton(SkeletonAdapterBase):
        source_id = "baostock"
        supported_domains = frozenset({"cn_equity_daily_bar"})

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = BaostockSkeleton(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
    )
    req = FetchRequest(
        run_id="r1",
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
        end_time="2026-06-17T15:30:00Z",
    )
    result = adapter.fetch(req, con=con)
    assert result.as_of_timestamp == "2026-06-17"


def test_resolveAsOf_invalidDate_returnsFailedFetch(
    tmp_path,
    migrated_con,
    batch_b_registry,
    request_factory,
    file_registry_stack,
    stub_fetch_bytes,
):
    from backend.app.datasources.adapters.fetch_port import StubFetchPort
    from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase
    from backend.app.datasources.fetch_result import FetchRequest

    class BaostockSkeleton(SkeletonAdapterBase):
        source_id = "baostock"
        supported_domains = frozenset({"cn_equity_daily_bar"})

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = BaostockSkeleton(
        batch_b_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
    )
    req = FetchRequest(
        run_id="r2",
        source_id="baostock",
        data_domain="cn_equity_daily_bar",
        end_time="not-a-date",
    )
    result = adapter.fetch(req, con=con)
    assert result.status == "FAILED"
    assert "invalid end_time" in (result.error_message or "")
