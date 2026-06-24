# 来源索引 — B01-DH2 Read-only Data Health v2

> Plan / Audit 读本文件 · Execute 只读 `implement.jsonl` + `context_pack.json`

---

## A. 血缘追溯

| 字段          | 值                                                                                           |
| ------------- | -------------------------------------------------------------------------------------------- |
| Round / Batch | Round 3E.4 · `BATCH_01_MODEL_SOURCE_READINESS`                                               |
| Item ID       | B01-C05 / Playbook B01-DH2                                                                   |
| 任务卡        | `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/R3E_readonly_data_health_v2.md` |
| Legacy        | B01-L03 `R3Y_readonly_data_health_v1.md` · `PROMPT_20`                                       |
| 分支          | `feature/round3-readonly-data-health-v2`                                                     |
| Worktree      | `../quant-monitor-desk-wt-b01-dh2`                                                           |

### AC 映射 → MASTER §4

| 任务卡 §                                    | MASTER AC       | 验证链          |
| ------------------------------------------- | --------------- | --------------- |
| §2 预期结果（whitelist/FRED/TDX/v3/rollup） | AC-DH2-PROFILE  | §9.1–9.5        |
| §6 BLOCKED 语义                             | AC-DH2-BLOCKED  | §9.1            |
| §8 边界（no fetch/DB）                      | AC-DH2-BOUND    | §9.6 + Audit A3 |
| §10 最小测试                                | AC-DH2-TEST     | §5 + §10        |
| §12 完成标准                                | AC-DH2-GATE     | §9.6            |
| master 红测 integration                     | AC-DH2-BASELINE | §9.0            |

### 路径纠偏

| 原引用                                                  | 纠偏                                                                         |
| ------------------------------------------------------- | ---------------------------------------------------------------------------- |
| v2 archive evidence `.audit-sandbox/mock/baostock.json` | 文件不存在 → DH2-BASE 用 `tests/fixtures/data_health/v2_integration_bundle/` |
| `specs/model_inputs/**`                                 | WL 未合并 → profile 返回 BLOCKED；fixture 驱动测试                           |

---

## B. 输入 manifest（E1 · implement.jsonl 来源）

| 路径                                            | 类别          | manifest  | extract / for     |
| ----------------------------------------------- | ------------- | --------- | ----------------- |
| `R3E_readonly_data_health_v2.md`                | 任务卡        | required  | Plan AC           |
| `R3Y_readonly_data_health_v1.md`                | legacy        | required  | v1 模式           |
| `PROMPT_20_*.md`                                | legacy prompt | required  | v1 边界           |
| `R3D_model_input_whitelist.md`                  | 兄弟 C01      | required  | whitelist schema  |
| `R3E_fred_authorized_sandbox_pilot.md`          | 兄弟 C02      | required  | FRED evidence     |
| `R3E_tdx_manual_probe_addendum.md`              | 兄弟 C03      | required  | TDX evidence      |
| `R3E_real_data_staged_pilot_v3.md`              | 兄弟 C04      | required  | v3 evidence       |
| `BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` | 协调          | required  | §3.7              |
| `BATCH_01_HARDENING_RULES.md`                   | 审计          | required  | §1–§10            |
| `backend/app/ops/data_health.py`                | 接线          | inherited | §9.x              |
| `tests/test_data_health_v2.py`                  | 测试          | deferred  | §5.1 Execute 创建 |

---

## C. 六类覆盖自检

| 类别 | 路径                                                     | [x] |
| ---- | -------------------------------------------------------- | --- |
| 决策 | `ROUND_3_DATA_PRODUCTION_READINESS/README.md`            | [x] |
| 规则 | `GLOBAL_*.md` · `BATCH_01_HARDENING_RULES.md`            | [x] |
| 架构 | `module_boundary_matrix.md` · `MIGRATION_MAP.md`         | [x] |
| 需求 | R3E 任务卡 + MASTER §3                                   | [x] |
| 契约 | `data_quality_rules.yaml` · `source_conflict_rules.yaml` | [x] |
| 接线 | `data_health.py` · `staged_pilot.py`                     | [x] |

**索引完整**

---

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。 由 `context_router.py --task` 写入；本段不重复列举。

## E. implement.jsonl 槽位

1. `MASTER.plan.md` · 2. `context_pack.json` · 3. `trellis-execute/SKILL.md` · 4+ ledger `required`
