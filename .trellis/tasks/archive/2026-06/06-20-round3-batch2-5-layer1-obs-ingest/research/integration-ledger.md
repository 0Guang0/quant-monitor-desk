# Integration Ledger — Round 3 Batch 2.5

> Plan 5c · v3 context packing

## 打包策略

| 策略            | 含义                        |
| --------------- | --------------------------- |
| inline          | MASTER 已总结               |
| summary+pointer | MASTER 摘要 + 原稿          |
| pointer         | implement.jsonl extract/for |

## ledger

| source                                                                      | category     | strategy                                    | master_anchor | for_ac_step |
| --------------------------------------------------------------------------- | ------------ | ------------------------------------------- | ------------- | ----------- |
| `docs/quality/PENDING_USER_DECISIONS.md`                                    | **decision** | summary+pointer                             | §0.7          | AC-PRE      |
| `018A` + `layer1_global_regime_panel.md`                                    | **business** | pointer                                     | §1.1, §3.4    | AC-TRACE-1  |
| `docs/architecture/module_boundary_matrix.md`                               | architecture | pointer                                     | §3.3          | AC-P0-4     |
| `docs/architecture/03_runtime_flows.md`                                     | architecture | pointer                                     | §3.4          | AC-TRACE-1  |
| `docs/modules/datasource_service.md`                                        | design       | pointer                                     | §3.4          | AC-P3-1     |
| `docs/modules/write_manager.md`                                             | rule         | pointer                                     | §3.4          | AC-P4-2     |
| `specs/contracts/source_route_contract.yaml`                                | contract     | pointer                                     | §6            | AC-P2-\*    |
| `specs/contracts/write_contract.yaml`                                       | contract     | pointer                                     | §6            | AC-P4-2     |
| `specs/contracts/snapshot_lineage_contract.yaml`                            | contract     | pointer                                     | §6            | AC-P4-4     |
| `specs/contracts/ops_db_inspect_contract.yaml`                              | contract     | pointer                                     | §8.2          | AC-P1-\*    |
| `backend/app/datasources/service.py`                                        | wiring       | pointer                                     | §4            | AC-P3-1     |
| `backend/app/db/validation_gate.py`                                         | wiring       | pointer                                     | §3.4          | AC-P4-1     |
| `backend/app/core/resource_guard.py`                                        | wiring       | pointer                                     | §3.4          | AC-P3-3     |
| `backend/app/sync/pipeline.py`                                              | wiring       | pointer（MASTER §0.6；非 implement — E11a） | §3.4          | AC-P4-1     |
| `backend/app/sync/orchestrator.py`                                          | wiring       | pointer（E11a）                             | §4            | AC-PRE      |
| `backend/app/sync/runners.py`                                               | wiring       | pointer（E11a；默认不窄改）                 | §4            | AC-P0-2     |
| `backend/app/storage/raw_store.py`                                          | wiring       | pointer                                     | §3.4          | AC-P3-2     |
| `backend/app/layer1_axes/*.py`                                              | wiring       | pointer                                     | §4            | AC-P4-3     |
| `configs/layer1_axes.yml`                                                   | config       | pointer                                     | §4            | AC-P2-1     |
| `GLOBAL_*.md`                                                               | rule         | summary+pointer                             | §0.7          | AC-GATE     |
| `.trellis/tasks/archive/2026-06/06-20-round3-batch2-layer1/audit.report.md` | gate         | pointer                                     | §0.7          | AC-PRE      |

## inline 清单

- 五阶段 gate + Audit A0–A4 串行
- 默认 staged/fixture ingestion
- schema.sql vs migration 011 滞后（O-02）
- FRED primary vs registry 对齐 gap
