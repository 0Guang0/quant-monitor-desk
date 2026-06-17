# Batch B §8 测试正文（Execute 引用）

> MASTER §8 仅 tracer + RED/GREEN 命令；**完整 pytest 在此**。

---

## §8.0 — conftest 追加

```python
@pytest.fixture
def raw_data_root(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    return root


@pytest.fixture
def file_registry_stack(tmp_path):
    """ConnectionManager + WriteManager + FileRegistry + RawStore on tmp_path DB."""
    from backend.app.db.connection import ConnectionManager
    from backend.app.db.migrate import apply_migrations
    from backend.app.db.write_manager import WriteManager
    from backend.app.storage.file_registry import FileRegistry
    from backend.app.storage.raw_store import RawStore
    import duckdb

    db = tmp_path / "t.duckdb"
    con = duckdb.connect(str(db))
    apply_migrations(con)
    con.close()
    cm = ConnectionManager(db)
    raw_root = tmp_path / "data"
    raw_root.mkdir()
    return {
        "cm": cm,
        "raw_store": RawStore(raw_root),
        "file_registry": FileRegistry(cm, WriteManager(cm)),
    }


@pytest.fixture
def stub_fetch_bytes():
    return b'{"symbol":"000001","close":10.0}'
```

```python
def test_adapterPackage_importable():
    import backend.app.datasources.adapters  # noqa: F401
```

---

## §8.1 — core skeleton tests

```python
from pathlib import Path

import pytest
from backend.app.storage.raw_store import sha256_hex


def test_skeletonAdapterBase_successWritesRawFile(
    tmp_path, migrated_con, loaded_registry, request_factory, file_registry_stack, stub_fetch_bytes,
):
    from backend.app.datasources.adapters.fetch_port import StubFetchPort
    from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase

    class BaostockSkeleton(SkeletonAdapterBase):
        source_id = "baostock"
        supported_domains = frozenset({"market_bar_1d", "fundamental"})

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = BaostockSkeleton(
        loaded_registry,
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
    assert con.execute("SELECT COUNT(*) FROM fetch_log WHERE run_id=?", [req.run_id]).fetchone()[0] == 1


def test_skeletonAdapterBase_registersFileRegistryWhenInjected(
    tmp_path, migrated_con, loaded_registry, request_factory, file_registry_stack, stub_fetch_bytes,
):
    from backend.app.datasources.adapters.fetch_port import StubFetchPort
    from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase

    class BaostockSkeleton(SkeletonAdapterBase):
        source_id = "baostock"
        supported_domains = frozenset({"market_bar_1d"})

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = BaostockSkeleton(
        loaded_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
        file_registry=stack["file_registry"],
    )
    req = request_factory("baostock", "market_bar_1d")
    result = adapter.fetch(req, con=con)
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
    tmp_path, migrated_con, loaded_registry, request_factory, file_registry_stack, status, error_type,
):
    from backend.app.datasources.adapters.fetch_port import FailingPort
    from backend.app.datasources.adapters.skeleton_base import SkeletonAdapterBase

    class BaostockSkeleton(SkeletonAdapterBase):
        source_id = "baostock"
        supported_domains = frozenset({"market_bar_1d"})

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = BaostockSkeleton(
        loaded_registry,
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
```

---

## §8.2 — BaostockAdapter

```python
def test_baostockAdapter_matchesRegistryDomains(
    tmp_path, migrated_con, loaded_registry, request_factory, file_registry_stack, stub_fetch_bytes,
):
    from backend.app.datasources.adapters.baostock import BaostockAdapter
    from backend.app.datasources.adapters.fetch_port import StubFetchPort

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = BaostockAdapter(
        loaded_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
    )
    assert adapter.source_id == "baostock"
    assert "fundamental" in adapter.supported_domains
    req = request_factory("baostock", "fundamental")
    result = adapter.fetch(req, con=con)
    assert result.status == "SUCCESS"
```

---

## §8.3 — QmtXtdataAdapter

```python
def test_qmtAdapter_localClientMissing_returnsAuthFailed(
    tmp_path, migrated_con, loaded_registry, request_factory, file_registry_stack,
):
    from backend.app.datasources.adapters.fetch_port import UnavailableClientPort
    from backend.app.datasources.adapters.qmt_xtdata import QmtXtdataAdapter

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = QmtXtdataAdapter(
        loaded_registry,
        raw_store=stack["raw_store"],
        fetch_port=UnavailableClientPort(reason="QMT client not running"),
    )
    req = request_factory("qmt_xtdata", "market_bar_1m")
    result = adapter.fetch(req, con=con)
    assert result.status == "AUTH_FAILED"
    row = con.execute(
        "SELECT status, error_type FROM fetch_log WHERE run_id=?", [req.run_id]
    ).fetchone()
    assert row[0] == "AUTH_FAILED" and row[1] == "auth"


def test_qmtAdapter_stubClient_successWritesRaw(
    tmp_path, migrated_con, loaded_registry, request_factory, file_registry_stack, stub_fetch_bytes,
):
    from backend.app.datasources.adapters.fetch_port import StubFetchPort
    from backend.app.datasources.adapters.qmt_xtdata import QmtXtdataAdapter

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = QmtXtdataAdapter(
        loaded_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
    )
    req = request_factory("qmt_xtdata", "market_bar_1m")
    result = adapter.fetch(req, con=con)
    assert result.status == "SUCCESS"
    assert result.raw_file_paths
```

---

## §8.4 — Akshare + Cninfo

```python
@pytest.mark.parametrize(
    "module_name,cls_name,source_id,domain",
    [
        ("backend.app.datasources.adapters.akshare", "AkshareAdapter", "akshare", "capital_flow"),
        ("backend.app.datasources.adapters.cninfo", "CninfoAdapter", "cninfo", "announcement"),
    ],
)
def test_vendorSkeleton_exposesSourceId(
    tmp_path, migrated_con, loaded_registry, request_factory, file_registry_stack, stub_fetch_bytes,
    module_name, cls_name, source_id, domain,
):
    import importlib
    from backend.app.datasources.adapters.fetch_port import StubFetchPort

    mod = importlib.import_module(module_name)
    cls = getattr(mod, cls_name)
    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = cls(
        loaded_registry,
        raw_store=stack["raw_store"],
        fetch_port=StubFetchPort(payload=stub_fetch_bytes),
    )
    assert adapter.source_id == source_id
    req = request_factory(source_id, domain)
    assert adapter.fetch(req, con=con).status == "SUCCESS"


def test_cninfoAdapter_unpublished_returnsEmptyResponse(
    tmp_path, migrated_con, loaded_registry, request_factory, file_registry_stack,
):
    from backend.app.datasources.adapters.cninfo import CninfoAdapter
    from backend.app.datasources.adapters.fetch_port import UnpublishedPort

    con = migrated_con(tmp_path)
    stack = file_registry_stack
    adapter = CninfoAdapter(
        loaded_registry,
        raw_store=stack["raw_store"],
        fetch_port=UnpublishedPort(),
    )
    req = request_factory("cninfo", "announcement")
    result = adapter.fetch(req, con=con)
    assert result.status == "EMPTY_RESPONSE"
    assert "not published" in (result.error_message or "").lower()
```

> **Fix parametrize in Execute:** use explicit imports `AkshareAdapter`, `CninfoAdapter` — avoid dynamic class name bug in last test template.

---

## §8.5 — Yahoo + factory

```python
def test_yahooAdapter_registryMarkedValidationOnly(loaded_registry):
    rec = loaded_registry.get("yahoo_finance")
    assert rec.validation_only is True


def test_createAdapter_unknownSource_raises(loaded_registry, raw_data_root):
    from backend.app.datasources.adapters import create_adapter
    with pytest.raises(KeyError):
        create_adapter("not_a_source", loaded_registry, raw_data_root)


def test_createAdapter_defaultFetchPort_success(
    tmp_path, migrated_con, loaded_registry, request_factory, raw_data_root,
):
    from backend.app.datasources.adapters import create_adapter
    from backend.app.storage.raw_store import RawStore

    con = migrated_con(tmp_path)
    adapter = create_adapter(
        "baostock", loaded_registry, raw_data_root, fetch_port=None,
    )
    req = request_factory("baostock", "market_bar_1d")
    result = adapter.fetch(req, con=con)
    assert result.status == "SUCCESS"
```
