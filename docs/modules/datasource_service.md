# DataSourceService（Round2.6）

## 1. 目的

`DataSourceService` 是生产路径唯一的数据源 fetch facade，用于收敛 `SourceRegistry`、`SourceCapabilityRegistry`、`SourceRoutePlan`、`ResourceGuard`、adapter factory、fetch_log / job_event_log 的调用边界。

当前 `create_adapter()` 已经要求显式 `FetchPort` 与 `FileRegistry`，这是正确安全边界；Round2.6 不是推翻该实现，而是把它收敛到一个服务入口，避免 Orchestrator、API、Agent、Layer 模块各自直接构造 adapter。

## 2. 权威契约

- `specs/contracts/datasource_service_contract.yaml`
- `specs/contracts/source_route_contract.yaml`
- `specs/contracts/source_capability_contract.yaml`

## 3. 生产调用规则（R3H-10 现行）

1. 生产代码只有 `DataSourceService` 可以直接调用 `create_adapter()`。
2. **Sync 金路径：** `run_incremental` / `run_backfill` 在生产 profile 下必须显式传入 `datasource_service=`（ADR-025；`guard_production_datasource_service_required`）。禁止 `adapter=` 旁路（`guard_production_adapter_bypass`）。
3. **`run_reconcile`：** 仍 `adapter=` 形参；生产 profile adapter 旁路 fail-closed。`datasource_service=` 金路径 **defer → R3H-08**（ADR-025 §Reconcile defer）。
4. API 只能调用 `preview_route()` 或只读 diagnostics，不得构造 adapter。
5. Agent 不得 import adapter factory 或 vendor adapter。
6. 测试仍可使用 `create_test_adapter()`，但必须显式说明 test-only。

## 4. 建议接口

```python
class DataSourceService:
    def preview_route(self, data_domain: str, operation: str, market_id: str | None = None) -> SourceRoutePlan:
        ...

    def fetch(self, request: FetchRequest, *, job_id: str | None = None) -> FetchResult:
        ...
```

## 5. 与已有实现的关系

| 当前实现                                                  | Round2.6 后续变化                                                                  |
| --------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `backend/app/datasources/adapters/create_adapter`         | 保留，但生产路径只由 DataSourceService 调用                                        |
| `backend/app/sync/runners.py` 接收 adapter                | incremental/backfill 生产 profile 须 `datasource_service=`；reconcile defer R3H-08 |
| `tests/test_vendor_fetch_e2e.py` 直接构造 fixture adapter | 保留为旧路径证据；新增 service-path E2E                                            |

## 6. 验收

```bash
python -m pytest tests/test_datasource_service.py tests/test_sync_orchestrator.py tests/test_vendor_fetch_e2e.py -q
```

## 7. Rehearsal vs product live (R3H-10)

- **Product fetch SSOT:** `DataSourceService.fetch()` / `preview_route()` with `datasources/fetch_ports/*` (contract `status: active`).
- **Rehearsal-only (not product live):** `ops/staged_pilot_*`, `ops/live_pilot_*`, `scripts/run_staged_pilot.py`, `ops/interface_probe`, CLI `--live-wire` rehearsal flags.
- Rehearsal paths may inject `FetchPort` for bounded evidence but must **not** be cited as R3H-08 product live readiness.
