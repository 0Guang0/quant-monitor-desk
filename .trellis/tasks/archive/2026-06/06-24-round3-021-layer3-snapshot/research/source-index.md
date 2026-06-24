# 来源索引 — Round 3 021 Layer3 snapshot builder

> **Plan / Audit 读本文件** · Execute 只读 `implement.jsonl` + `context_pack.json`

---

## A. 血缘追溯

| 字段          | 值                                                                                           |
| ------------- | -------------------------------------------------------------------------------------------- |
| Round / Batch | Round 3 Batch 4                                                                              |
| Item ID       | `021`                                                                                        |
| 任务卡        | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/021_implement_layer3_snapshot_builder.md` |
| Batch 地图    | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` § Batch 4                                               |
| gate / 分支   | `020` merged + staged gate / `feature/round3-021-layer3-snapshot`                            |
| 前置任务      | `.trellis/tasks/archive/2026-06/06-23-round3-020-layer3-loader`                              |

### AC 映射 → MASTER §2

| 任务卡                        | MASTER AC | 验证链 |
| ----------------------------- | --------- | ------ |
| §1 snapshot + Layer5 view     | AC-021-1  | §8.3   |
| §15 lineage 字段              | AC-021-2  | §8.2   |
| §15 as_of / 未来数据          | AC-021-3  | §8.4   |
| §8.12.6 event_only 跳过行情   | AC-021-4  | §8.5   |
| §2 Layer5 边界 / mapping view | AC-021-5  | §8.3   |
| §16 staged-only               | AC-021-6  | §8.3   |
| §11 验收命令                  | AC-021-7  | §10    |

---

## B. 输入 manifest（E1 · implement.jsonl 来源）

| 路径                                                                                         | 类别     | manifest  | extract / for        |
| -------------------------------------------------------------------------------------------- | -------- | --------- | -------------------- |
| `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/021_implement_layer3_snapshot_builder.md` | 任务卡   | required  | Plan AC              |
| `docs/modules/layer3_industry_shock_anchor.md`                                               | spec     | required  | AC-021-1/4/5         |
| `specs/contracts/snapshot_lineage_contract.yaml`                                             | contract | required  | AC-021-2/3           |
| `backend/app/layer3_chains/loader.py`                                                        | wiring   | inherited | §8.3 loader 输入     |
| `backend/app/layer2_sensors/snapshot_builder.py`                                             | wiring   | inherited | §8 模式参考          |
| `backend/app/core/snapshot_lineage.py`                                                       | wiring   | inherited | §8.2 lineage kernel  |
| `tests/fixtures/layer3_staged_bundle/**`                                                     | fixture  | inherited | AC-021-1 loader 输入 |
| `tests/fixtures/layer3_l5_staged_bars/**`                                                    | fixture  | deferred  | §8.3 Execute 创建    |
| `tests/test_layer3_snapshot_builder.py`                                                      | 测试     | deferred  | §5.1 Execute 创建    |
| `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`                                              | rule     | required  | §0 staged            |

---

## C. 六类覆盖自检

| 类别 | 路径                                                               | [x] |
| ---- | ------------------------------------------------------------------ | --- |
| 决策 | `BATCH3_STAGED_DOWNSTREAM_GATE.md`；D-09 ADR-0003                  | [x] |
| 规则 | `GLOBAL_*.md`；`staged_acceptance_policy.md`                       | [x] |
| 架构 | `docs/architecture/03_runtime_flows.md`；`04_data_architecture.md` | [x] |
| 需求 | 任务卡 `021` + MASTER §3                                           | [x] |
| 契约 | `snapshot_lineage_contract.yaml`                                   | [x] |
| 接线 | `loader.py`（020）；`snapshot_builder.py`（019/020 模式）          | [x] |

**索引完整**

---

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。由 `context_router.py --task` 写入。

## E. implement.jsonl 槽位

1. `MASTER.plan.md` · 2. `context_pack.json` · 3. `trellis-execute/SKILL.md` · 4+ ledger `required`
