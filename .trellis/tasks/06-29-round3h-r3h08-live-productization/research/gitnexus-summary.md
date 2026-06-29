# GitNexus Impact Summary — R3H-08 Plan 1b

- **Target:** `DataSourceService` (upstream)
- **Risk:** **MEDIUM**
- **Direct dependents (d=1):** 6
- **Date:** 2026-06-29

## Blast radius

| 深度 | 数量 | 含义                                       |
| ---- | ---- | ------------------------------------------ |
| d=1  | 6    | 直接 import/call — **改 service 接口会破** |
| d=2  | 6    | 间接                                       |
| d=3  | 2    | 传递                                       |

## 已知上游（context 抽样）

- `tests/test_datasource_service.py`
- `tests/test_sync_orchestrator.py`
- `tests/test_vendor_fetch_e2e.py`
- `backend/app/sync/runners.py`
- `backend/app/ops/staged_pilot.py`
- `backend/app/ops/live_pilot_phase3.py`
- `backend/app/ops/interface_probe.py`
- `backend/app/layer1_axes/ingestion.py`

## Plan 约束

- R3H-08 **优先新增** `product_live_gate.py` / `live_tier_router.py`，**最小**改动 `DataSourceService` 公有 API
- 扩展现有 `fetch_ports` 而非新旁路模块
- Execute 每切片前对将改 symbol 再跑 `impact()`

## 拟新增符号（Execute 前再 impact）

- `ProductLiveGate`
- `resolve_live_tier` / `LiveTierRouter`
