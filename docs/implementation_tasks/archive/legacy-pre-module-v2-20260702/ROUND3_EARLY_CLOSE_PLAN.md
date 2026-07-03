# Round3 Early Close Plan (from Round2 ABCD audit)

> **Authority:** When this plan conflicts with current item state, [`docs/AUDIT_DEFERRED_REGISTRY.md`](../AUDIT_DEFERRED_REGISTRY.md) wins. Pair registries: [`UNRESOLVED_ISSUES_REGISTRY.md`](../UNRESOLVED_ISSUES_REGISTRY.md) · [`RESOLVED_ISSUES_REGISTRY.md`](../RESOLVED_ISSUES_REGISTRY.md).

Items deferred from strict Round2 skeleton to Round3 early phase:

| Item                                             | Round3 phase | Notes                                                                                                                                                                                                                                                                         |
| ------------------------------------------------ | ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Real QMT / broker terminal vendor E2E            | R3 early     | Requires user authorization; keep default disabled. Staging path: `docs/ops/qmt_xqshare_setup.md` (no `--enable-qmt` on inspect CLI per D-11).                                                                                                                                |
| Real Yahoo / rate-limited public API soak        | R3 early     | Staging snapshot + read-only sandbox                                                                                                                                                                                                                                          |
| Layer snapshot lineage consumers                 | R3 mid       | Depends on validation_report rule_version fields (closed in audit remediation)                                                                                                                                                                                                |
| Playwright / route-level frontend contract tests | R4           | Frontend shell only in Round2                                                                                                                                                                                                                                                 |
| Production-scale shard latency benchmarks        | R3 early     | Use `scripts/production_equivalent_smoke.py` + fixture-scale datasets                                                                                                                                                                                                         |
| **Local DB inspect CLI**                         | **R3 early** | 冻结设计：`docs/ops/db_inspect_cli.md`；契约：`specs/contracts/ops_db_inspect_contract.yaml`。执行者**仅**按冻结设计实现 read-only CLI + tests（禁止重新设计、禁止复用 `.tmp` 脚本）。无独立 task 文件，见 `docs/ROUND3_HANDOFF.md` 与 `ROUND3_BATCH_IMPLEMENTATION_MAP.md`。 |

Round2 audit remediation closes: fixture vendor E2E, DB lineage fields, orchestrator runner split, backfill validate+write, reconcile re-fetch.

## Unresolved item coverage（Plan 不得遗漏）

Plan 阶段必须读取 `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`，并核对以下仍未闭合项；若当前 batch 不关闭，必须写 explicit re-deferral：

| ID                                        | 目标阶段                                      | 本计划处理要求                                                                                       |
| ----------------------------------------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `R2.6-IMPL-8`                             | Batch 2.75 或 user-authorized staging E2E     | live QMT/Yahoo/xqshare validation 只能授权后执行；默认 disabled。                                    |
| `R3-AUDIT-DEF-01`                         | Round3 ops hygiene 或 Round5 docs consistency | `KEY_TABLES` / mapping 常量与 `ops_db_inspect_contract.yaml` 的 SSOT drift 风险必须关闭或 re-defer。 |
| `R3-AUDIT-DEF-02`                         | Batch 2.75 或 user-authorized staging E2E     | fixture/full_load skeleton 不能被说成 production live vendor soak。                                  |
| `R3-AUDIT-DEF-03`                         | Round3 ops hygiene 或 Round5 docs consistency | scan cap 对 raw/parquet/audit/report 子目录的边界测试或 contract 等价说明必须补齐。                  |
| `R3-B25-PERF-BUDGET-01` / `R3-B25-HYG-03` | Batch 2.75 或 CI nightly                      | production-equivalent benchmark / performance-budget artifact 必须刷新或 explicit re-defer。         |
