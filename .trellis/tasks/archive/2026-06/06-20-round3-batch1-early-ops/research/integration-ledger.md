# Integration Ledger — Round 3 Batch 1 Early Ops

> Plan 5c · v3 context packing · 对抗审计后更新

## 打包策略

| 策略            | 含义                                  |
| --------------- | ------------------------------------- |
| inline          | 已写入 MASTER；Execute 以 MASTER 为准 |
| summary+pointer | MASTER 摘要 + 原稿对照                |
| pointer         | 按 extract/for 精读原稿               |

## ledger

| source                                                                                                                | category     | strategy        | master_anchor | execute_extract                      | for_ac_step        |
| --------------------------------------------------------------------------------------------------------------------- | ------------ | --------------- | ------------- | ------------------------------------ | ------------------ |
| `research/integration-ledger.md`                                                                                      | rule         | inline          | MASTER §0.4   | v3 boot routing map                  | §8.0 Boot          |
| `README.md`                                                                                                           | rule         | summary+pointer | MASTER §0.8   | docs/specs 非实现边界                | §3.1               |
| `docs/quality/PENDING_USER_DECISIONS.md`                                                                              | decision     | summary+pointer | MASTER §0.7   | D-01/D-11                            | AC-OPS-1 / §10     |
| `specs/contracts/runtime_versions.md`                                                                                 | rule         | summary+pointer | MASTER §10    | uv sync --locked                     | §8.0 / §10         |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`                                                                 | rule         | summary+pointer | MASTER §0.7   | 执行边界摘录                         | AC-CLI-3           |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`                                                                  | rule         | summary+pointer | MASTER §0.7   | 语义断言                             | §8.1-8.4           |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`                                                                 | rule         | summary+pointer | MASTER §0.7   | eco/scan_limited                     | §6                 |
| `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/README.md`                                                         | rule         | summary+pointer | MASTER §3.2   | 017-023 禁止                         | defer              |
| `docs/ROUND3_HANDOFF.md`                                                                                              | business     | pointer         | MASTER §2     | DOC-R3-001 编辑                      | AC-DOC-1 / §8.3    |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md`                                                                                  | decision     | pointer         | MASTER §2     | 八项状态                             | AC-DB/DOC/E2E      |
| `docs/RESOLVED_ISSUES_REGISTRY.md`                                                                                    | decision     | summary+pointer | MASTER §3.1   | 闭合移入                             | §8.3               |
| `docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md`                                                                | business     | summary+pointer | MASTER §13    | early close 六项；inspect CLI 冻结   | AC-CLI-\*          |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016F_define_prod_equivalent_scale_benchmark.md` | business     | pointer         | MASTER §13    | smoke 设计                           | AC-BENCH-1         |
| `.trellis/tasks/archive/2026-06/06-19-round2-6-routing-service-gate/audit.report.md`                                  | decision     | pointer         | MASTER §0.7   | 前置 PASS                            | AC-PRE             |
| `docs/ops/db_inspect_cli.md`                                                                                          | business     | pointer         | MASTER §6     | Phase A §5–11；deferred_item_mapping | AC-CLI-1..5 / §8.1 |
| `specs/contracts/ops_db_inspect_contract.yaml`                                                                        | contract     | pointer         | MASTER §6     | key_tables；forbidden args           | AC-CLI-\* / §8.1   |
| `specs/schema/schema.sql`                                                                                             | contract     | pointer         | MASTER §6     | 表名权威                             | AC-CLI-4           |
| `docs/modules/data_sources.md`                                                                                        | architecture | pointer         | MASTER §6     | evidence.latest_fetch                | AC-DB / E2E        |
| `docs/modules/write_manager.md`                                                                                       | rule         | summary+pointer | MASTER §3.3   | inspect 禁止 writer                  | AC-CLI-3           |
| `docs/modules/local_file_system.md`                                                                                   | architecture | summary+pointer | MASTER §2     | data/duckdb 路径约定                 | AC-DB-1            |
| `docs/modules/duckdb_and_parquet.md`                                                                                  | architecture | pointer         | MASTER §4     | key_tables 语义                      | AC-DB-2            |
| `backend/app/db/connection.py`                                                                                        | wiring       | pointer         | MASTER §6     | reader read_only                     | AC-CLI-3 / §8.1    |
| `scripts/production_equivalent_smoke.py`                                                                              | wiring       | pointer         | MASTER §9     | isolated sandbox                     | AC-BENCH-1 / §8.5  |
| `scripts/production_gate.py`                                                                                          | gate         | pointer         | MASTER §10    | Tier B                               | AC-GATE / §8.6     |
| `scripts/check_doc_links.py`                                                                                          | gate         | pointer         | MASTER §10    | doc link                             | AC-DOC-\* / §8.3   |
| `tests/test_vendor_fetch_e2e.py`                                                                                      | wiring       | pointer         | MASTER §2     | fixture E2E                          | AC-E2E-1 / §8.4    |
| `docs/AUDIT_DEFERRED_REGISTRY.md`                                                                                     | decision     | summary+pointer | MASTER §8.3   | registry wins                        | AC-DOC-2           |

## inline 清单（Execute 以 MASTER 为准）

- §0.7 GLOBAL 与 D-01/D-11 摘要
- §0.8 README 项目边界
- §3.2 全部 defer 项（017–023、migration 008、live QMT、future CLI phases）
- §3.3 只读 DB 边界
- `test_sync_jobs.py` full_load skeleton 引用（E11：不得入 implement；§8.4 命令内引用）
