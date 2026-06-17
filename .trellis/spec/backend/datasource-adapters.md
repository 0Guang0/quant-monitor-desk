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
```

`PortError(status: PortErrorStatus, message: str)` — six failure literals aligned 1:1 with `FetchResult.status` failure states (not `SUCCESS`).

### 3. Contracts

| Field / rule | Constraint |
|--------------|------------|
| `FetchPayload.content` | Raw bytes written via `RawStore.save` on SUCCESS |
| `FetchPayload.file_type` | Passed to RawStore (default `"json"`) |
| SUCCESS `FetchResult` | `row_count=1`, `raw_file_paths`, `content_hash`, `as_of_timestamp` |
| Failure `FetchResult` | `row_count=0`, `error_message` required; no raw paths for `EMPTY_RESPONSE` |
| FileRegistry (optional) | When injected, `register(saved)` after save; `local_path == raw_file_paths[0]` |
| cninfo unpublished | `UnpublishedPort` → `EMPTY_RESPONSE` + business message (not a new FetchStatus literal) |
| Default port | `StubFetchPort(payload=b"{}")` when `fetch_port=None` |

**Environment:** `QMD_DATA_ROOT` → `RawStore` root (same as Batch A).

### 4. Validation & Error Matrix

| Condition | Result |
|-----------|--------|
| Unknown `source_id` in `create_adapter` | `KeyError` |
| `PortError(AUTH_FAILED, …)` | `FetchResult.status=AUTH_FAILED`, fetch_log `error_type=auth` |
| `PortError(EMPTY_RESPONSE, …)` | `FetchResult.status=EMPTY_RESPONSE`, fetch_log `error_type=empty`, no raw file |
| `WriteManager` import in `adapters/` | **Forbidden** — use storage layer only via injected `RawStore` / `FileRegistry` |
| Real HTTP in skeleton | **Forbidden** — inject `FetchPort` implementation in later batch |

### 5. Good / Base / Bad Cases

**Good:** Inject `StubFetchPort` in tests; assert disk file + hash + optional FileRegistry row.

**Base:** `create_adapter("baostock", registry, data_root)` with default stub port → SUCCESS + minimal `{}` raw file.

**Bad:** Import `WriteManager` in adapter module; add 8th `FetchStatus` for “not published”; bypass `BaseDataAdapter.fetch` for fetch_log.

### 6. Tests Required

| Test focus | Assertion points |
|------------|------------------|
| SUCCESS raw write | File exists; `content_hash == sha256_hex(payload)` |
| FileRegistry | Row `local_path` matches `raw_file_paths[0]` |
| PortError mapping | Parametrized 6 statuses → status + fetch_log `error_type` |
| QMT | AUTH_FAILED path + SUCCESS path |
| cninfo | EMPTY_RESPONSE + message + fetch_log `empty` |
| Factory | Unknown source raises; all five sources SUCCESS |

### 7. Wrong vs Correct

#### Wrong

```python
from backend.app.storage.write_manager import WriteManager  # in adapters/

class MyAdapter(SkeletonAdapterBase):
    def _fetch_impl(self, req):
        return FetchResult(..., status="NOT_PUBLISHED_YET", ...)  # 8th status
```

#### Correct

```python
class CninfoAdapter(SkeletonAdapterBase):
    source_id = "cninfo"
    supported_domains = frozenset({"announcement"})

# Test double:
fetch_port=UnpublishedPort()  # → PortError(EMPTY_RESPONSE, "announcement not published yet")
```

---

## Design Decision: FetchPort vs inline HTTP

**Decision:** Skeleton adapters depend on `FetchPort` protocol; no `requests`/`httpx` in `adapters/`.

**Why:** Batch B delivers structure + test doubles; real vendor I/O lands in Batch C/D without changing adapter class shape.

---

## Anti-patterns

| Don't | Why |
|-------|-----|
| Duplicate `_utc_now_iso` in skeleton | Import from `base_adapter` |
| Thin `FailingPort` wrappers for one-off tests | Use `FailingPort(status, message)` directly |
| Remove `UnpublishedPort` | MASTER §6.4 frozen semantic name for AC-10 |
