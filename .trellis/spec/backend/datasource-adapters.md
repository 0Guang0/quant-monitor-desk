# Datasource Adapter Skeletons (Batch B)

> Executable contracts for `backend/app/datasources/adapters/` — Round 2 Batch B.

---

## Scenario: Vendor adapter skeleton + FetchPort injection

### 1. Scope / Trigger

- New vendor adapter under `adapters/` or changes to `SkeletonAdapterBase`, `FetchPort`, `create_adapter`.
- Cross-layer: adapter → `RawStore` / optional `FileRegistry` / `BaseDataAdapter.fetch` → `fetch_log`.

### 2. Signatures

```python
class FetchPort(Protocol):
    def fetch_payload(self, req: FetchRequest) -> FetchPayload: ...

def create_adapter(
    source_id: str,
    registry: SourceRegistry,
    data_root: Path,
    *,
    fetch_port: FetchPort | None = None,
    file_registry: FileRegistry | None = None,
) -> BaseDataAdapter

def create_test_adapter(...) -> BaseDataAdapter  # tests only; default StubFetchPort
```

`PortError(status: PortErrorStatus, message: str)` — failure literals aligned 1:1 with `FetchResult.status` (incl. `NOT_PUBLISHED_YET`).

### 3. Contracts

| Field / rule | Constraint |
|--------------|------------|
| `FetchPayload.content` | Raw bytes written via `RawStore.save` on SUCCESS |
| `FetchPayload.file_type` | Passed to RawStore (default `"json"`) |
| `FetchPayload.row_count` | Optional; defaults to 1 on SUCCESS |
| `FetchPayload.schema_hash` | Optional; JSON dict keys fingerprint when omitted |
| SUCCESS `FetchResult` | `raw_file_paths`, `content_hash`, `schema_hash?`, `latency_ms?` |
| Failure `FetchResult` | `row_count=0`; no raw for `EMPTY_RESPONSE` / `NOT_PUBLISHED_YET` |
| FileRegistry | **Required** in `create_adapter()`; optional in direct skeleton tests |
| cninfo unpublished | `UnpublishedPort` → `NOT_PUBLISHED_YET` + business message |
| Default port | **Forbidden** in `create_adapter()` — use `create_test_adapter()` in tests |
| Payload size | `max_payload_bytes` default 10MB; oversized → `FAILED` before RawStore |

**Environment:** `QMD_DATA_ROOT` → `RawStore` root (same as Batch A).

### 4. Validation & Error Matrix

| Condition | Result |
|-----------|--------|
| Unknown `source_id` in `create_adapter` | `AdapterNotSupportedError` |
| Missing `fetch_port` / `file_registry` | `AdapterConfigurationError` |
| `PortError(AUTH_FAILED, …)` | `FetchResult.status=AUTH_FAILED`, fetch_log `error_type=auth` |
| `PortError(NOT_PUBLISHED_YET, …)` | `FetchResult.status=NOT_PUBLISHED_YET`, fetch_log `error_type=not_published` |
| `WriteManager` import in `adapters/` | **Forbidden** — use storage layer only via injected `RawStore` / `FileRegistry` |
| Real HTTP in skeleton | **Forbidden** — inject `FetchPort` implementation in later batch |

### 5. Good / Base / Bad Cases

**Good:** Inject `StubFetchPort` in tests; assert disk file + hash + optional FileRegistry row.

**Base:** `create_test_adapter("baostock", registry, data_root)` with default stub port.

**Bad:** Call `create_adapter()` without `fetch_port` / `file_registry` (raises `AdapterConfigurationError`).

### 6. Tests Required

| Test focus | Assertion points |
|------------|------------------|
| SUCCESS raw write | File exists; `content_hash == sha256_hex(payload)` |
| FileRegistry | Row `local_path` matches `raw_file_paths[0]` |
| PortError mapping | Parametrized 7 statuses incl. `NOT_PUBLISHED_YET` |
| QMT | AUTH_FAILED path + SUCCESS path |
| cninfo | `NOT_PUBLISHED_YET` + fetch_log `not_published` |
| Factory | Config errors + `AdapterNotSupportedError` |

### 7. Wrong vs Correct

#### Wrong

```python
from backend.app.storage.write_manager import WriteManager  # in adapters/

class MyAdapter(SkeletonAdapterBase):
    def _fetch_impl(self, req):
        # 勿在 adapter 内直接构造 failure status — 应经 FetchPort 抛 PortError
        return FetchResult(..., status="NOT_PUBLISHED_YET", ...)
```

#### Correct

```python
class CninfoAdapter(SkeletonAdapterBase):
    source_id = "cninfo"
    supported_domains = frozenset({"announcement"})

# Test double:
fetch_port=UnpublishedPort()  # → PortError(NOT_PUBLISHED_YET, ...)
```

---

## Design Decision: FetchPort vs inline HTTP

**Decision:** Skeleton adapters depend on `FetchPort` protocol; no `requests`/`httpx` in `adapters/`.

**Why:** Batch B delivers structure + test doubles; real vendor I/O lands in Batch C/D without changing adapter class shape.

---

## Design Decision: 勿让 SkeletonAdapterBase 膨胀为上帝类

**Decision（Batch C/D 前）：** `SkeletonAdapterBase` 只做编排 — FetchPort 调用、PortError 映射、RawStore/FileRegistry 写入、as_of 解析。不在基类内加解析、重试、限流、真实 SDK。

**Batch C/D 扩展时拆分：**

| 层 | 职责 |
|----|------|
| `FetchPort` | 网络 / SDK I/O |
| `PayloadParser`（未来） | bytes → staging rows / metadata |
| `EvidenceWriter`（未来） | RawStore + FileRegistry 组合 |
| `*Adapter` | 只编排上述组件 |

**Why:** 真实 adapter 若继续往基类堆逻辑，会破坏 Batch B 的 FetchPort 解耦；规矩写入 spec，实现延后 Batch C/D。

---

## Anti-patterns

| Don't | Why |
|-------|-----|
| Duplicate `_utc_now_iso` in skeleton | Import from `base_adapter` |
| Thin `FailingPort` wrappers for one-off tests | Use `FailingPort(status, message)` directly |
| Remove `UnpublishedPort` | Frozen semantic name for cninfo unpublished |
| Call `create_adapter()` without explicit port/registry | Raises `AdapterConfigurationError` |
