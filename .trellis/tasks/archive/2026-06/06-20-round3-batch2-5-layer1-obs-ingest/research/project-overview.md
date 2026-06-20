# Project Overview — Round 3 Batch 2.5 (Plan 1a)

> ≤1 page · GitNexus-deferred light survey · 2026-06-20

## 任务定位

Batch 2.5 是 Round 3 **强制桥接批**：在 Batch 2（Layer 1 loader + snapshot，fixture observation）与 Batch 3（Layer 2）之间，建立**受控、可审计**的 `axis_observation` 摄取路径（route → fetch evidence → validation → WriteManager → snapshots → lineage）。

## 代码热点（Execute 将触达）

| 区域       | 路径                                                                            | 本批角色                                                                                      |
| ---------- | ------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Layer 1    | `backend/app/layer1_axes/`                                                      | 新增 `ingestion.py`（或窄扩展 `sync/runners.py`）；复用 loader/feature/interpretation/lineage |
| 数据源门面 | `backend/app/datasources/service.py`                                            | **唯一** adapter factory 调用点                                                               |
| 路由       | `backend/app/datasources/route_planner.py`                                      | Phase 2 dry-run / Phase 3 route evidence                                                      |
| 同步管道   | `backend/app/sync/pipeline.py`, `orchestrator.py`                               | 可选窄 runner；禁止 broad backfill                                                            |
| 校验       | `backend/app/validators/data_quality.py`, `source_conflict.py`                  | Phase 4 必经                                                                                  |
| 写入       | `backend/app/db/write_manager.py`, `validation_gate.py`                         | clean `axis_observation` + snapshots                                                          |
| 存储证据   | `backend/app/storage/raw_store.py`, `file_registry.py`                          | Phase 3 raw/file_registry                                                                     |
| 运维       | `backend/app/ops/db_inspector.py`                                               | Phase 1/4 只读 inventory                                                                      |
| 测试       | `tests/test_layer1_*`, `test_datasource_service.py`, `test_vendor_fetch_e2e.py` | Phase 0 gate + 新 ingestion 测试                                                              |

## 前置状态

- Batch 2 archived PASS：`axis_registry`…`axis_snapshot_lineage` 表与引擎已存在（migration 011）。
- **无** production Layer1 observation 摄取；`layer1_axes/ingestion.py` 不存在。
- `specs/schema/schema.sql` 仍缺 axis DDL（migration 011 为准）— Phase 0 必查。

## 关键风险（→ MASTER §7）

1. Layer1 指标 `primary_source`（FRED 等）与 `source_registry` 已启用源不完全对齐 → 默认 **staged/fixture** 路径，非 live FRED。
2. 五阶段 gate：Execute 不得跳过 Audit A0–A4。
3. 模块边界：Layer1 不得 `import create_adapter`。

## 下一步

Phase 2b/5a 将 018A §8 五阶段冻结为 MASTER §2 AC + §8 RED/GREEN。
