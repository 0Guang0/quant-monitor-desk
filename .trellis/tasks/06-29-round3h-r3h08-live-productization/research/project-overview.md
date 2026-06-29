# Project Overview — R3H-08 Live Productization

- **Query:** Wave 2 产品 live 入口与 Tier 落库触点
- **GitNexus:** query `live product fetch DataSourceService tier`
- **Date:** 2026-06-29

## 功能簇

| 簇             | 路径                                                      | R3H-08 角色                 |
| -------------- | --------------------------------------------------------- | --------------------------- |
| C2 Fetch SSOT  | `backend/app/datasources/service.py`                      | 唯一产品门面                |
| Fetch ports    | `backend/app/datasources/fetch_ports/*.py`                | per-source live             |
| Sync           | `backend/app/sync/orchestrator.py`                        | incremental/backfill 金路径 |
| Tier / promote | `backend/app/ops/sandbox_clean_write/`                    | A/B 写库守卫                |
| Rehearsal      | `backend/app/ops/live_pilot_phase3.py`, `staged_pilot.py` | **非**产品路径              |
| Probe          | `backend/app/ops/interface_probe.py`                      | 须经 service（defer 关账）  |

## 关键执行流

- `DataSyncOrchestrator.run_incremental` → `datasource_service.fetch`
- `limited_production_entry` → validation_only → pilot DB only
- `resolve_clean_write_target` → bar/disclosure/macro 域

## Caveats

- `live_pilot_phase3` 仍在 ops 层 — 产品 live 不得 import 为默认路径
- US market bar clean 域部分 defer Wave 3
