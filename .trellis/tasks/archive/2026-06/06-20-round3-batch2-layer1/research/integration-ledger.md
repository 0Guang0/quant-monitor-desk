# Integration Ledger — Round 3 Batch 2 Layer 1

> Plan 5c · v3 context packing

## 打包策略

| 策略            | 含义                                  |
| --------------- | ------------------------------------- |
| inline          | 已写入 MASTER；Execute 以 MASTER 为准 |
| summary+pointer | MASTER 摘要 + 原稿对照                |
| pointer         | 按 extract/for 精读原稿               |

## ledger

| source                                                                         | category     | strategy        | master_anchor | execute_extract                    | for_ac_step    |
| ------------------------------------------------------------------------------ | ------------ | --------------- | ------------- | ---------------------------------- | -------------- |
| `research/integration-ledger.md`                                               | rule         | inline          | MASTER §0.4   | v3 boot routing                    | §8.0           |
| `README.md`                                                                    | rule         | summary+pointer | MASTER §0.8   | docs/specs 非实现边界              | §3.1           |
| `docs/quality/PENDING_USER_DECISIONS.md`                                       | decision     | summary+pointer | MASTER §0.7   | D-09 Layer1 only                   | AC-017/018     |
| `specs/contracts/runtime_versions.md`                                          | rule         | summary+pointer | MASTER §10    | uv sync --locked                   | §8.0/§10       |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`                          | rule         | summary+pointer | MASTER §0.7   | WriteManager/no drive-by           | §3.3           |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`                           | rule         | summary+pointer | MASTER §0.7   | 语义断言                           | §8.2-8.5       |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`                          | rule         | summary+pointer | MASTER §0.7   | eco/窗口限制                       | §8.3           |
| `configs/layer1_axes.yml`                                                      | config       | pointer         | MASTER §6     | spec_root + enabled_axes           | AC-017-1       |
| `docs/modules/layer1_global_regime_panel.md`                                   | architecture | pointer         | MASTER §4/§6  | §6 DDL §7 窗口 §8 计算 §13 测试    | AC-017/018     |
| `specs/contracts/layer1_axis_contract.yaml`                                    | contract     | pointer         | MASTER §6     | required fields + forbidden terms  | AC-017-2/018-3 |
| `specs/layer1_axes/restructured_axes_v1_1/**`                                  | domain       | pointer         | MASTER §6     | 五轴 YAML 权威                     | AC-017-1       |
| `specs/contracts/snapshot_lineage_contract.yaml`                               | contract     | pointer         | MASTER §6     | required_fields + validation_tests | AC-LINEAGE-\*  |
| `docs/adr/ADR-0003-layer1-standardization-only.md`                             | decision     | summary+pointer | MASTER §0.7   | D-09                               | AC-018-1       |
| `docs/modules/duckdb_and_parquet.md`                                           | architecture | summary+pointer | MASTER §3.1   | Layer1 表在 DuckDB                 | §8.1           |
| `docs/modules/write_manager.md`                                                | rule         | pointer         | MASTER §3.3   | snapshot 写入路径                  | AC-018-1       |
| `backend/app/db/write_manager.py`                                              | wiring       | pointer         | MASTER §6     | WriteRequest API                   | §8.3-8.5       |
| `backend/app/validators/data_quality.py`                                       | wiring       | pointer         | MASTER §6     | rule_version + fetch lineage       | AC-LINEAGE-2   |
| `backend/app/db/migrations/008_lineage_version_fields.sql`                     | migration    | summary+pointer | MASTER §0.7   | validation_report 字段             | AC-LINEAGE-2   |
| `.trellis/tasks/archive/2026-06/06-20-round3-batch1-early-ops/audit.report.md` | gate         | pointer         | MASTER §0.7   | Batch1 PASS                        | AC-PRE         |
| `docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md`                         | business     | summary+pointer | MASTER §1.3   | lineage consumers scope            | AC-LINEAGE-\*  |

## inline 清单

- §0.7 GLOBAL + D-09 摘要
- §0.8 README 边界
- §3.2 defer：019-023、Layer1 API、live fetch、migration 008 CHECK
- §3.3 WriteManager 强制路径
- 路径纠偏：`backend/app/layer1_axes/` 非 `backend/layers/`
