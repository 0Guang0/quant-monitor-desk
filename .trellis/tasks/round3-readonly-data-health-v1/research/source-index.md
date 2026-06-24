# 来源索引 — round3-readonly-data-health-v1

> **Plan / Audit 读本文件** · Execute 只读 `implement.jsonl` + `context_pack.json`

---

## A. 血缘追溯

| 字段 | 值 |
| ---- | --- |
| Round / Batch | Round 3 Wave **C** · slice **C-20** |
| Item ID | `R3Y-readonly-data-health-v1` / PROMPT_20 |
| 任务卡 | `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_readonly_data_health_v1.md` |
| Batch 地图 | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.2 C-20 |
| gate / 分支 | staged pilot v2 archived / `feature/round3-readonly-data-health-v1` |
| 前置任务 | `.trellis/tasks/archive/2026-06/06-24-round3-real-data-staged-pilot-v2` |

### AC 映射 → MASTER §2

| 任务卡 / Playbook §8.1 | MASTER AC | 验证链 |
| ---------------------- | --------- | ------ |
| Plan 行 | AC-DH-PLAN | freeze |
| 实现行 | AC-DH-IMPL | §8.8 |
| 业务 AC | AC-DH-BIZ | §8.9 |
| 规则面 | AC-DH-RULES | §8.3–8.6 |
| 切片证据 | AC-DH-SLICE | §8.1–8.9 evidence |
| 测试 | AC-DH-TEST | §10 |
| MAP 验证 | AC-DH-MAP | §10 Tier A |
| Audit | AC-DH-AUDIT | Audit |
| 边界 | AC-DH-BOUND | §3.3 |

---

## B. 输入 manifest（E1 · implement.jsonl 来源）

| 路径 | 类别 | manifest | extract / for |
| ---- | ---- | -------- | ------------- |
| `R3Y_readonly_data_health_v1.md` | 任务卡 | required | Plan AC |
| `PROMPT_20_*.md` | 任务卡 | required | 启动边界 |
| `data_quality_rules.yaml` | contract | required | rule_id |
| `backend/app/ops/db_inspector.py` | wiring | inherited | 只读模式 |
| `backend/app/validators/data_quality.py` | wiring | inherited | 规则语义 |
| `archive/.../staged-pilot-v2/execute-evidence/` | evidence | required | §8.9 |
| `tests/test_ops_data_health.py` | 测试 | deferred | §5.1 Execute 创建 |

---

## C. 六类覆盖自检

| 类别 | 路径 | [x] |
| ---- | ---- | --- |
| 决策 | `production_live_pilot_policy.md`；`R3-B2.75-REQ2-EM` DEFERRED | [x] |
| 规则 | `GLOBAL_*.md`；`staged_acceptance_policy.md`；playbook §2.2 | [x] |
| 架构 | `module_boundary_matrix.md`；`ops_and_performance.md` | [x] |
| 需求 | R3Y 任务卡 + MASTER §3 | [x] |
| 契约 | `data_quality_rules.yaml` 等 §3.2 全表 | [x] |
| 接线 | db_inspector / staged_pilot / validators | [x] |

**索引完整**

---

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。 由 `context_router.py --task` 写入；本段不重复列举。

## E. implement.jsonl 槽位

1. `MASTER.plan.md` · 2. `context_pack.json` · 3. `trellis-execute/SKILL.md` · 4+ ledger `required`
