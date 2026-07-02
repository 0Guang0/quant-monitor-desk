# EXTERNAL-INDEX — R3-DCP-09

> 包外必读与源码字典 · Plan v4.1

---

## §A 切片开工前必读（外部）

| 路径                                                                                                                               | 用途                       |
| ---------------------------------------------------------------------------------------------------------------------------------- | -------------------------- |
| `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3_DCP_09_BOUNDED_BACKFILL_CI.md` | 活卡 §1–§5                 |
| `docs/implementation_tasks/.../R3_DCP_TO_ISSUES_INDEX.md`                                                                        | Wave 4 DCP-09 索引         |
| `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5                                                                                           | Wave 4 目标                |
| `docs/decisions/ADR-030-bounded-backfill-cap-and-ci-nightly.md`                                                                    | cap + nightly 决策         |
| `docs/modules/data_sync_orchestrator.md` §13.4.3 · §13.7 · §13.11                                                                  | Backfill 流程 + CLI 设计   |
| `specs/contracts/reference_adoption_guardrails.yaml`                                                                               | 借鉴梯                     |
| `docs/quality/待修复清单.md` §4                                                                                                    | 台账 WAVE3-ACC-* 承接      |
| `docs/quality/production_live_pilot_policy.md`                                                                                       | live/nightly 边界          |

---

## §B 执行情境路由（外部）

| 情境              | 路径                                                      |
| ----------------- | --------------------------------------------------------- |
| Backfill runner   | `backend/app/sync/runners.py` `BackfillShardRunner`      |
| Shard planner     | `backend/app/sync/jobs.py` `plan_backfill_shards`         |
| Smoke budget      | `specs/contracts/production_equivalent_smoke_budget.yaml` |
| PR CI             | `.github/workflows/ci.yml`                                |
| Nightly CI        | `.github/workflows/nightly.yml`（Execute S04 新建）       |
| Nightly ops       | `docs/ops/nightly_ci.md`（Execute S04 新建）              |

---

## §C 源码 / 测试字典

| 符号 / 路径                                              | 说明                              |
| -------------------------------------------------------- | --------------------------------- |
| `plan_backfill_shards`                                   | 31 天/片 eco 分片                 |
| `ECO_MAX_BACKFILL_DAYS_PER_TASK`                         | `jobs.py` 常量 = 31               |
| `DataSyncOrchestrator.run_backfill`                      | 金路径入口                        |
| `wave3_isolated_production_acceptance.py`                | 隔离验收；`--quick` 跳过 `pytest_full`（S03） |
| `wave3_live_production_acceptance.py`                    | 连网验收；`--fail-on-severity` findings gate（S05） |
| `pytest -q --run-network -m network tests/test_batch275_live_pilot_gate.py::test_livePilot_phase3RawOnly_threeRequestsLive` | nightly network 子集（`ACC-LIVE-NETWORK-CI-001`） |
| `test_production_equivalent_smoke_budget.py`             | shard_count_benchmark 门禁        |
| `tests/test_sync_orchestrator.py`（backfill 相关）        | runner 契约先例                   |

---

## §D 参考项目源码（只读 · Execute RED 前实读）

| 文件                                                                            | 等级              |
| ------------------------------------------------------------------------------- | ----------------- |
| `参考项目/OpenBB/openbb_platform/core/openbb_core/provider/abstract/fetcher.py` | architecture_only |
| `参考项目/EasyXT/data_manager/unified_data_interface.py` L172–244               | forbidden         |

落盘：`research/execute-reference-read-evidence-dcp09.md`（Execute 阶段）
