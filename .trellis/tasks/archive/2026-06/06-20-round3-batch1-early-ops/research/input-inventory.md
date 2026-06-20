# Input Inventory — 06-20-round3-batch1-early-ops (P0i)

> 2026-06-20 · 文档宇宙审计 · 三层追溯见 `three-layer-trace.md`

## 1. 任务卡展开

| 来源         | 路径                                                           | 状态      |
| ------------ | -------------------------------------------------------------- | --------- |
| Round3 early | `docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md`         | in-repo   |
| Round3 边界  | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/README.md`  | in-repo   |
| Handoff      | `docs/ROUND3_HANDOFF.md`                                       | in-repo   |
| 016F 追溯    | `ROUND_2_6_.../016F_define_prod_equivalent_scale_benchmark.md` | in-repo   |
| GLOBAL×4     | `GLOBAL_*.md`                                                  | in-repo   |
| 冻结设计     | `docs/ops/db_inspect_cli.md`                                   | in-repo   |
| 契约         | `specs/contracts/ops_db_inspect_contract.yaml`                 | in-repo   |
| 批次地图     | `ROUND3_BATCH_IMPLEMENTATION_MAP.md`                           | in-repo   |
| v3           | `research/integration-ledger.md`                               | Plan 产出 |

## 2. 六类关键信息覆盖

| 类别         | 必须覆盖                   | 已定位路径                                                                    | 缺口                    |
| ------------ | -------------------------- | ----------------------------------------------------------------------------- | ----------------------- |
| decision     | registry + early defer     | `AUDIT_DEFERRED_REGISTRY.md`, `ROUND3_EARLY_CLOSE_PLAN.md`                    | 无                      |
| rule         | GLOBAL + write boundary    | `GLOBAL_*`, `write_manager.md`                                                | 无                      |
| architecture | data root + duckdb         | `local_file_system.md`, `duckdb_and_parquet.md`                               | 无                      |
| business     | early close + inspect      | `ROUND3_EARLY_CLOSE_PLAN.md`, `db_inspect_cli.md`                             | 无                      |
| contract     | ops inspect + adapter      | `ops_db_inspect_contract.yaml`, `data_adapter_contract.md`                    | 无                      |
| wiring       | connection + tests + smoke | `connection.py`, `test_vendor_fetch_e2e.py`, `production_equivalent_smoke.py` | `backend/app/ops/` 待建 |

## 3. 交叉引用闭包（1-hop）

| 自                           | 引用                           | 状态     |
| ---------------------------- | ------------------------------ | -------- |
| `db_inspect_cli.md`          | `ops_db_inspect_contract.yaml` | required |
| `ROUND3_EARLY_CLOSE_PLAN.md` | `db_inspect_cli.md`            | required |
| `MIGRATION_MAP.md`           | `backend/app/ops/`             | required |

## 4. missing-in-repo

| 路径                                   | 说明                                            |
| -------------------------------------- | ----------------------------------------------- |
| `backend/app/ops/db_inspector.py`      | Execute 新建                                    |
| `scripts/qmd_ops.py`                   | Execute 新建                                    |
| `tests/test_ops_db_inspector.py`       | Execute 新建                                    |
| `backend/app/cli/main.py`              | v1 不实现；transitional CLI only                |
| `ROUND_3_MODELING_LAYERS/DECISIONS.md` | 本 Round 无 DECISIONS 文件（Batch 1 无 NNN 卡） |

## 5. 门禁

- [x] 任务来源 + §3 输入已展开
- [x] 六类关键信息均有路径
- [x] 与 `original-plan-trace.md` 一致

`P0i complete`
