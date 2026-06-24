# 来源索引 — Round 3 022 Layer4 market structure

> **Plan / Audit 读本文件** · Execute 只读 `implement.jsonl` + `context_pack.json`

---

## A. 血缘追溯

| 字段          | 值                                                                                           |
| ------------- | -------------------------------------------------------------------------------------------- |
| Round / Batch | Round 3 Batch 5 / Wave C                                                                     |
| Item ID       | `022`                                                                                        |
| 任务卡        | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/022_implement_layer4_market_structure.md` |
| Batch 地图    | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.2–§2.6                                               |
| Playbook      | `WAVE_C_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` §3.1 + §3.3 + §8.2                             |
| gate / 分支   | `021` merged + staged gate / `feature/round3-022-layer4-market`                              |
| 前置任务      | `.trellis/tasks/archive/2026-06/06-24-round3-021-layer3-snapshot`                            |

### AC 映射 → MASTER §2

| 任务卡                    | MASTER AC | 验证链 |
| ------------------------- | --------- | ------ |
| §1 registry/calendar/...  | AC-022-1  | §8.2   |
| module §10 calendar 规则  | AC-022-2  | §8.4   |
| contract breadth          | AC-022-3  | §8.4   |
| §15 lineage               | AC-022-4  | §8.5   |
| §15 as_of                 | AC-022-5  | §8.6   |
| §16 staged / Wave C       | AC-022-6  | §8.3   |
| D-09 boundaries           | AC-022-7  | §8.7   |
| §11 + playbook §8.2       | AC-022-8  | §10    |

### 路径纠偏

| Playbook 路径                               | 状态     | 替代口径                                              |
| ------------------------------------------- | -------- | ----------------------------------------------------- |
| specs/schema/schema.sql                     | **缺失** | `layer4_market_structure.md` §5 + contract models     |
| docs/decisions/ D-09 目录                   | **缺失** | `docs/quality/PENDING_USER_DECISIONS.md` §D-09        |

---

## B. 输入 manifest（E1 · implement.jsonl 来源）

| 路径                                                                                         | 类别     | manifest  | extract / for        |
| -------------------------------------------------------------------------------------------- | -------- | --------- | -------------------- |
| `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/022_implement_layer4_market_structure.md` | 任务卡   | required  | Plan AC              |
| `docs/modules/layer4_market_structure.md`                                                    | spec     | required  | AC-022-1..3          |
| `specs/contracts/layer4_market_contract.yaml`                                                | contract | required  | AC-022-2,3,7         |
| `specs/contracts/snapshot_lineage_contract.yaml`                                             | contract | required  | AC-022-4,5           |
| `backend/app/layer3_chains/snapshot_builder.py`                                              | wiring   | inherited | §8.6 upstream 模式   |
| `backend/app/core/snapshot_lineage.py`                                                       | wiring   | inherited | §8.5 lineage kernel  |
| `backend/app/db/write_manager.py`                                                            | wiring   | inherited | WriteManager 对照    |
| `tests/test_layer3_snapshot_builder.py`                                                    | wiring   | inherited | L3 回归不破坏        |
| `tests/test_batch3_staged_downstream_gate.py`                                                | rule     | required  | AC-022-8             |
| `tests/test_layer4_market_structure.py`                                                      | 测试     | deferred  | §5.1 Execute 创建    |
| `tests/fixtures/layer4_staged_market/**`                                                     | fixture  | deferred  | §8.3 Execute 创建    |
| `WAVE_C_MAIN_SESSION_COORDINATOR_PLAYBOOK.md`                                                | rule     | required  | §3 权威索引          |

---

## C. 六类覆盖自检

| 类别 | 路径                                                                 | [x] |
| ---- | -------------------------------------------------------------------- | --- |
| 决策 | `BATCH3_STAGED_DOWNSTREAM_GATE.md`；`PENDING_USER_DECISIONS.md` D-09 | [x] |
| 规则 | `GLOBAL_*.md`；`staged_acceptance_policy.md`；playbook §2.2          | [x] |
| 架构 | `docs/architecture/03_runtime_flows.md`；`04_data_architecture.md`   | [x] |
| 需求 | 任务卡 `022` + MASTER §3 + playbook §8.2                             | [x] |
| 契约 | `layer4_market_contract.yaml`；`snapshot_lineage_contract.yaml`      | [x] |
| 接线 | `layer3_chains/snapshot_builder.py`（021）；`write_manager.py`       | [x] |

**索引完整**

---

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。 由 `context_router.py --task` 写入；本段不重复列举。

## E. implement.jsonl 槽位

1. `MASTER.plan.md` · 2. `context_pack.json` · 3. `trellis-execute/SKILL.md` · 4+ ledger `required`
