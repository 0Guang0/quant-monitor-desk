# Input Inventory — 06-21-round3-batch2-75-live-pilot (P0i)

> 2026-06-21 · 追溯链：`README.md` 三层模型 → `MIGRATION_MAP.md` → `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §4.2 → `018B`

## 1. 任务来源展开

| 来源           | 路径                                        | 状态                 |
| -------------- | ------------------------------------------- | -------------------- |
| Batch map      | `R3-B2.75-PROD-LIVE-PILOT` §3               | in-repo              |
| 任务卡         | `018B_production_live_pilot_gate.md`        | in-repo              |
| 授权           | `batch275_user_authorization_2026-06-21.md` | Plan 创建            |
| 前置 Batch 2.5 | `06-20-round3-batch2-5-layer1-obs-ingest`   | archived PASS staged |
| GLOBAL×4       | `GLOBAL_*.md`                               | in-repo              |
| Plan 桥        | `TASK_INPUT_CONTEXT_INDEX.md`               | in-repo              |

## 2. 六类关键信息覆盖

| 类别         | 必须覆盖                                                       | 已定位路径                                                                          | 缺口                            |
| ------------ | -------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------- |
| decision     | D-11 QMT 禁用；三请求授权；FRED 不随 Request3 关闭             | `PENDING_USER_DECISIONS.md`, `batch275_user_authorization_2026-06-21.md`, 018B §3.1 | live shape 未验证（Execute）    |
| rule         | fail-closed pilot policy；eco limits                           | `production_live_pilot_policy.md`, `GLOBAL_*`, `resource_limits.yaml`               | perf smoke 未跑（§8.7）         |
| architecture | sandbox pilot 链；与 R2b 互斥                                  | `layer1_ingestion_refactor_rollback_plan.md` §6, MASTER §3.4                        | `live_pilot.py` 未建（Execute） |
| business     | 三 micro-pilot shape；B2.5-O-05 FRED gap                       | `018B` §3.1, `source_registry.yaml`, ENV-E1 spec yaml                               | live shape 未验证               |
| contract     | route/service/inspect/quality/conflict                         | `source_route_contract.yaml` 等 §4.2 bundle + `source_conflict_rules.yaml`          | Execute 实现待验                |
| wiring       | DataSourceService, DbInspector, ResourceGuard, source_conflict | `service.py`, `db_inspector.py`, `resource_guard.py`, `source_conflict.py`          | `live_pilot.py` 缺失            |

## 3. 交叉引用闭包（1-hop）

| 自                              | 引用                         | 状态                    |
| ------------------------------- | ---------------------------- | ----------------------- |
| 018B §3.1                       | authorization evidence path  | required — file created |
| Batch 2.5 evidence              | staged only — no promotion   | required                |
| `BATCH3_STAGED_DOWNSTREAM_GATE` | Batch 3 handoff              | required                |
| `datasource_service_contract`   | no fixture fallback for live | required                |

## 4. missing-in-repo（Plan/Execute 将创建）

| 路径                                     | 说明                           |
| ---------------------------------------- | ------------------------------ |
| `backend/app/ops/live_pilot.py`          | 试点编排                       |
| `tests/test_batch275_live_pilot_gate.py` | fail-closed + phase tests      |
| `execute-evidence/phase*.md/json`        | 018B 证据                      |
| `ROUND_3_MODELING_LAYERS/DECISIONS.md`   | 不存在 — GLOBAL + 授权文件代替 |

## 5. 门禁

- [x] 六类关键信息均有路径（缺口列标注 Execute 待闭合）
- [x] 与 `original-plan-trace.md` 一致
- [x] 与 ROUND3 map §4.2 一致

`P0i complete`
