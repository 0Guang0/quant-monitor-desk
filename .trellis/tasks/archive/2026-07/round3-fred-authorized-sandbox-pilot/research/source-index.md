# 来源索引 — B01-FRED FRED Authorized Sandbox Pilot

> **Plan / Audit 读本文件** · Execute 只读 `implement.jsonl` + `context_pack.json`

---

## A. 血缘追溯

| 字段          | 值                                                                                                 |
| ------------- | -------------------------------------------------------------------------------------------------- |
| Round / Batch | Round 3E · `BATCH_01_MODEL_SOURCE_READINESS`                                                       |
| Item ID       | `B01-C02` / Playbook `B01-FRED`                                                                    |
| 任务卡        | `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/R3E_fred_authorized_sandbox_pilot.md` |
| Batch 地图    | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.6                                                          |
| gate / 分支   | B01-WL P0 macro 白名单 / `feature/round3-fred-authorized-sandbox-pilot`                            |

### AC 映射 → MASTER §2

| 任务卡 §9 切片          | MASTER AC  | 验证链 |
| ----------------------- | ---------- | ------ |
| FRED-01 Registry        | AC-FRED-01 | §8.1   |
| FRED-02 Route           | AC-FRED-02 | §8.2   |
| FRED-03 Mock fetch      | AC-FRED-03 | §8.3   |
| FRED-04 Failures        | AC-FRED-04 | §8.4   |
| FRED-05 Evidence health | AC-FRED-05 | §8.5   |
| FRED-06 Closeout        | AC-FRED-06 | §8.6   |
| Live（可选）            | AC-FRED-07 | §8.7   |

### 路径纠偏

| 任务卡路径                                | 纠偏                                                                            |
| ----------------------------------------- | ------------------------------------------------------------------------------- |
| `backend/app/ops/data_health.py` 主体扩展 | **禁止** — playbook §8.5 + §2.6；改由 `fred_evidence_validator.py` + B01-DH2 v2 |
| registry 直接 commit                      | **主会话批处理** — 本分支仅 proposed delta + tests                              |

---

## B. 输入 manifest（E1 · implement.jsonl 来源）

| 路径                                                                | 类别       | manifest         | extract / for     |
| ------------------------------------------------------------------- | ---------- | ---------------- | ----------------- |
| `R3E_fred_authorized_sandbox_pilot.md`                              | 任务卡     | Plan             | AC / 切片         |
| `PROMPT_04_debt_r3b275_fred_staged_semantics.md`                    | legacy     | Plan             | B2.5-O-05 语义    |
| `018B_production_live_pilot_gate.md`                                | legacy L05 | Plan             | live opt-in gate  |
| `BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md`                     | 协调       | MASTER §6.0 摘要 | §8.5 · Track A #3 |
| `BATCH_01_HARDENING_RULES.md`                                       | rule       | required         | §3 授权           |
| `source_registry.yaml` / `source_capabilities.yaml`                 | contract   | required         | AC-FRED-01        |
| `staged_pilot*.py` / `route_planner.py`                             | wiring     | inherited        | §8.2–8.3          |
| `tests/test_fred_source_registry.py` · `test_fred_sandbox_pilot.py` | 测试       | deferred         | §5.1              |

---

## C. 六类覆盖自检

| 类别 | 路径                                                       | [x] |
| ---- | ---------------------------------------------------------- | --- |
| 决策 | `ROUND_3_DATA_PRODUCTION_READINESS/DECISIONS.md`（若存在） | [x] |
| 规则 | GLOBAL×4 · `BATCH_01_HARDENING_RULES.md`                   | [x] |
| 架构 | `docs/architecture/04_data_architecture.md`                | [x] |
| 需求 | R3E 任务卡 + MASTER §3                                     | [x] |
| 契约 | `specs/contracts/*` · registry yaml                        | [x] |
| 接线 | `backend/app/ops/` · `datasources/`                        | [x] |

**索引完整**

---

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。 由 `context_router.py --task` 写入；本段不重复列举。

## E. implement.jsonl 槽位

1. `MASTER.plan.md` · 2. `context_pack.json` · 3. `trellis-execute/SKILL.md` · 4+ ledger `required`
