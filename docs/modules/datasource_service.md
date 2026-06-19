# DataSourceService（Round2.6）

## 1. 目的

`DataSourceService` 是生产路径唯一的数据源 fetch facade，用于收敛 `SourceRegistry`、`SourceCapabilityRegistry`、`SourceRoutePlan`、`ResourceGuard`、adapter factory、fetch_log / job_event_log 的调用边界。

当前 `create_adapter()` 已经要求显式 `FetchPort` 与 `FileRegistry`，这是正确安全边界；Round2.6 不是推翻该实现，而是把它收敛到一个服务入口，避免 Orchestrator、API、Agent、Layer 模块各自直接构造 adapter。

## 2. 权威契约

- `specs/contracts/datasource_service_contract.yaml`
- `specs/contracts/source_route_contract.yaml`
- `specs/contracts/source_capability_contract.yaml`

## 3. 生产调用规则

1. 生产代码只有 `DataSourceService` 可以直接调用 `create_adapter()`。
2. Orchestrator runner 后续应依赖 `DataSourceService.fetch()` 或窄 `fetch_callable`。
3. API 只能调用 `preview_route()` 或只读 diagnostics，不得构造 adapter。
4. Agent 不得 import adapter factory 或 vendor adapter。
5. 测试仍可使用 `create_test_adapter()`，但必须显式说明 test-only。

## 4. 建议接口

```python
class DataSourceService:
    def preview_route(self, data_domain: str, operation: str, market_id: str | None = None) -> SourceRoutePlan:
        ...

    def fetch(self, request: FetchRequest, *, job_id: str | None = None) -> FetchResult:
        ...
```

## 5. 与已有实现的关系

| 当前实现 | Round2.6 后续变化 |
|---|---|
| `backend/app/datasources/adapters/create_adapter` | 保留，但生产路径只由 DataSourceService 调用 |
| `backend/app/sync/runners.py` 接收 adapter | 后续改为接收 service 或 fetch callable |
| `tests/test_vendor_fetch_e2e.py` 直接构造 fixture adapter | 保留为旧路径证据；新增 service-path E2E |

## 6. 验收

```bash
python -m pytest tests/test_datasource_service.py tests/test_sync_orchestrator.py tests/test_vendor_fetch_e2e.py -q
```
