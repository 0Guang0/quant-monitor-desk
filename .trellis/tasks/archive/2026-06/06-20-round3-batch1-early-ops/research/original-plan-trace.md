# Original Plan Trace — 06-20-round3-batch1-early-ops

## Round / Batch

Round 3 · **Batch 1** — early entry, real-data/DB proof, prerequisite ops.

权威索引：`ROUND3_BATCH_IMPLEMENTATION_MAP.md` §3 + §4.2 · 项目地图：`MIGRATION_MAP.md` §6 QMD Ops DB Inspect CLI。

三层追溯全文：`research/three-layer-trace.md`。

## 任务卡清单

本批 **无** 正式 `NNN_*.md` 编号任务卡。原始任务来源为：

| Layer | 路径                                                           | 说明                             |
| ----- | -------------------------------------------------------------- | -------------------------------- |
| L2    | `docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md`         | early close 原始计划             |
| L2    | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/README.md`  | Round 3 边界；inspect CLI 无编号 |
| L2    | `docs/ROUND3_HANDOFF.md`                                       | Round 3 入口交接                 |
| L2    | `ROUND_2_6_.../016F_define_prod_equivalent_scale_benchmark.md` | 规模基准设计（追溯 only）        |
| L1    | `docs/ops/db_inspect_cli.md`                                   | 冻结设计（非 task 卡）           |
| L1    | `specs/contracts/ops_db_inspect_contract.yaml`                 | 机器契约                         |

**排除（Batch 2+）：** `017`–`023` under `ROUND_3_MODELING_LAYERS/`

## AC 映射（登记册 / 原始计划 → MASTER §2 草案）

| Item ID                     | 原始来源                                                    | MASTER §2 草案 AC                                                                      |
| --------------------------- | ----------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `DOC-R3-001`                | `UNRESOLVED_ISSUES_REGISTRY` + `ROUND3_HANDOFF.md`          | AC-DOC-1：handoff 顶部写明 R2.6 Contract + Routing Service Gate archived PASS          |
| `DOC-R3-002`                | `UNRESOLVED_ISSUES_REGISTRY` + `ROUND3_EARLY_CLOSE_PLAN.md` | AC-DOC-2：`AUDIT_DEFERRED_REGISTRY.md` wins on conflict                                |
| `R2.6-IMPL-8`               | `ROUND3_EARLY_CLOSE_PLAN` §Real QMT/Yahoo + registry        | AC-OPS-1：live 默认禁用；仅文档化 user-authorized staging；inspect 不启用              |
| `DB-R3-001`                 | registry + `local_file_system.md`                           | AC-DB-1：inspect 报告 raw/parquet counts + documented absence 或存在证据               |
| `DB-R3-002`                 | registry + `db_inspect_cli.md` §5.1                         | AC-DB-2：`read_only_open` + key_tables row counts                                      |
| `R3-PARTIAL-2`              | `ROUND3_EARLY_CLOSE_PLAN` + `data_adapter_contract.md`      | AC-E2E-1：fixture FetchPort E2E **或** `run_full_load` skeleton pytest + registry 更新 |
| `R3-EARLY-DB-INSPECT-CLI`   | `ROUND3_EARLY_CLOSE_PLAN` + frozen design                   | AC-CLI-1..N：契约字段、安全不变量、无 mutation 测试                                    |
| `R3-EARLY-PROD-SCALE-BENCH` | `016F` + `production_equivalent_smoke.py`                   | AC-BENCH-1：smoke 证据归档或显式 re-defer 链到 `R2.6-IMPL-7`                           |

## 输入文件已读（specs / architecture / modules / code）

| 路径                                               | 类别     | manifest                           |
| -------------------------------------------------- | -------- | ---------------------------------- |
| `docs/implementation_tasks/GLOBAL_*.md` (×4)       | 全局规则 | summarized in MASTER               |
| `docs/modules/duckdb_and_parquet.md`               | 模块设计 | summarized                         |
| `docs/modules/local_file_system.md`                | 模块设计 | summarized                         |
| `docs/modules/write_manager.md`                    | 模块设计 | summarized                         |
| `docs/modules/data_sources.md`                     | 模块设计 | summarized                         |
| `docs/modules/qmt_xtdata_adapter.md`               | 模块设计 | summarized                         |
| `docs/modules/source_capability_registry.md`       | 模块设计 | summarized                         |
| `docs/modules/source_route_plan.md`                | 模块设计 | summarized                         |
| `docs/modules/datasource_service.md`               | 模块设计 | summarized                         |
| `docs/modules/data_sync_orchestrator.md`           | 模块设计 | summarized                         |
| `docs/ops/db_inspect_cli.md`                       | 运维设计 | **Execute must-read**              |
| `docs/ops/data_sync_quick_reference.md`            | 运维     | summarized                         |
| `docs/ops/qmt_xqshare_setup.md`                    | 运维     | summarized                         |
| `docs/ops/privacy_data_flow.md`                    | 运维     | summarized                         |
| `specs/contracts/ops_db_inspect_contract.yaml`     | 契约     | **Execute must-read**              |
| `specs/contracts/data_adapter_contract.md`         | 契约     | summarized; E2E trace              |
| `specs/contracts/data_cli_contract.yaml`           | 契约     | summarized                         |
| `specs/contracts/source_route_contract.yaml`       | 契约     | summarized                         |
| `specs/contracts/datasource_service_contract.yaml` | 契约     | summarized                         |
| `specs/contracts/sync_job_contract.yaml`           | 契约     | summarized                         |
| `specs/contracts/platform_source_matrix.yaml`      | 契约     | summarized                         |
| `specs/contracts/runtime_versions.md`              | 运行时   | MASTER §10                         |
| `backend/app/db/connection.py`                     | 接线     | **Execute must-read** (`reader()`) |
| `scripts/init_db.py`                               | 脚本     | inherited path conventions         |
| `scripts/production_equivalent_smoke.py`           | 脚本     | **Execute must-read** (bench)      |
| `tests/test_vendor_fetch_e2e.py`                   | 测试     | inherited; R3-PARTIAL-2 基线       |

## 路径纠偏

| 声明                              | 实际                                                                                  |
| --------------------------------- | ------------------------------------------------------------------------------------- |
| `qmd ops db-inspect` 最终命令     | v1 允许 `python scripts/qmd_ops.py db-inspect` 薄包装                                 |
| `.tmp/inspect_db.py`              | 禁止复用                                                                              |
| `backend/app/ops/db_inspector.py` | 尚不存在 — Execute 新建                                                               |
| `run_full_load`                   | **全仓库无实现** — R3-PARTIAL-2 若选 skeleton 须新建                                  |
| `test_vendor_fetch_e2e.py`        | 已有 orchestrator + service-path fixture E2E — 与 registry DEFERRED 需 Plan reconcile |
