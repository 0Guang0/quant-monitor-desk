# R3-DCP-05 执行入口 — 路由地图（Execute SSOT）

> **角色：** 本任务 **唯一 Execute 读入口**  
> **任务目录：** `.trellis/tasks/wave4-r3-dcp-05-tier-a/`  
> **活卡（包外）：** `EXTERNAL-INDEX.md` → `R3_DCP_05_TIER_A_INCREMENTAL.md`  
> **协议：** Plan v4.1 · `plan-skill-outputs.yaml`

---

## 1. 目的 · 价值 · 完成条件

| 维度         | 内容                                                             |
| ------------ | ---------------------------------------------------------------- |
| **目的**     | 11 个 Tier A 源产品增量 sync + **全部 clean upsert**（ADR-028）  |
| **价值**     | Wave 4 DCP-05；DCP-06 真 clean 前置；关 `ACC-BAOSTOCK-NO-LIVE`   |
| **评级**     | D1/E1/C3 → R5 路径；A2 migration +1 批                           |
| **完成条件** | S00–S13 全绿 · 11/11 clean e2e · `uv run pytest -q` · Audit PASS |
| **不在范围** | FRED live primary · G12 · Tier B/C · cron 矩阵                   |

---

## 2. 约束 · 规则

| 类别     | 约束                                                     | 详述                               |
| -------- | -------------------------------------------------------- | ---------------------------------- |
| ADR-028  | 11 源 canonical domain → clean 表                        | `docs/decisions/ADR-028-*.md`      |
| ADR-025  | Sync 必须 datasource_service                             | fail-closed                        |
| 参考采纳 | `参考项目/**` 只读；L 梯见 `reference-adoption-dcp05.md` | guardrails.yaml                    |
| 真网     | `QMD_ALLOW_LIVE_FETCH` + 隔离库                          | ADR-027                            |
| 主库     | 禁止 silent 写 canonical `data/duckdb/`                  | `DEBT.plan.md` · ADR-027 · 活卡 §3 |
| GitNexus | impact + detect_changes                                  | `gitnexus-summary.md`              |

---

## 3. 验证命令

```bash
uv run pytest tests/test_baostock_incremental_e2e.py tests/test_fred_macro_incremental_e2e.py tests/test_schema_migration.py -q
uv run pytest -q
uv run python scripts/loop_maintain.py
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/wave4-r3-dcp-05-tier-a
```

证据：`research/execute-evidence/sNN-green.txt`

---

## 4. ADR 索引

| ADR                                                                                        | 标题                                       | 切片    |
| ------------------------------------------------------------------------------------------ | ------------------------------------------ | ------- |
| [ADR-028](../../../../docs/decisions/ADR-028-dcp05-tier-a-clean-domain-extension.md)       | DCP-05 Tier A clean domain + migration 015 | **S00** |
| [ADR-025](../../../../docs/decisions/ADR-025-r3h10-sync-fail-closed-datasource-service.md) | Sync fail-closed service                   | 全片    |
| [ADR-027](../../../../docs/decisions/ADR-027-r3h08-product-live-env-gate.md)               | Product live env gate                      | **S01** |

---

## 5. 执行包阅读规则

### 5.1 包内文件地图

| 文件                                         | Skill                       | 摘要                   |
| -------------------------------------------- | --------------------------- | ---------------------- |
| `00-EXECUTION-ENTRY.md`                      | trellis-plan 5e             | 本路由                 |
| `EXTERNAL-INDEX.md`                          | trellis-plan 5e             | 包外 §A/B/C            |
| `plan-boot.md`                               | P0                          | Boot 复述              |
| `to-issues-slices.md`                        | to-issues                   | **切片 AC SSOT**       |
| `plan-task-breakdown.md`                     | planning-and-task-breakdown | 任务/CP                |
| `plan-spec.md`                               | spec-driven-development     | 技术规格 + 015 sketch  |
| `plan-context.md`                            | context-engineering         | 上下文/路由            |
| `plan-doubt-review.md`                       | doubt-driven-development    | 怀疑审查               |
| `reference-adoption-dcp05.md`                | trellis-research            | 参考 L1/L2/L3          |
| `project-overview.md`                        | GitNexus 1a                 | 子系统                 |
| `gitnexus-summary.md`                        | GitNexus 1b                 | 冲击面                 |
| `plan-consolidation.md`                      | trellis-plan 5e             | 分流对照               |
| `integration-audit.md`                       | trellis-before-dev          | 集成审计               |
| `parallel-dispatch-protocol.md`              | trellis-channel             | 并行派发协议           |
| `execute-reference-read-evidence-s01-s08.md` | trellis-execute             | S01/S08 参考读证据     |
| `execute-reference-read-evidence-s02-s06.md` | trellis-execute             | S02–S06 参考读证据     |
| `execute-reference-read-evidence-s07-s11.md` | trellis-execute             | S07–S11 参考读证据     |
| `gitnexus-audit-summary.md`                  | audit-boot                  | Audit GitNexus 摘要    |
| `audit-a1-report.md`                         | audit A1                    | 维度审计报告           |
| `audit-a2-report.md`                         | audit A2                    | 维度审计报告           |
| `audit-a3-report.md`                         | audit A3                    | 维度审计报告           |
| `audit-a4-report.md`                         | audit A4                    | 维度审计报告           |
| `audit-a5-report.md`                         | audit A5                    | 维度审计报告           |
| `audit-a6-report.md`                         | audit A6                    | 维度审计报告           |
| `audit-a7-report.md`                         | audit A7                    | 维度审计报告           |
| `audit-a8-report.md`                         | audit A8                    | 维度审计报告           |
| `audit-repair-ledger.md`                     | repair-boot                 | Repair 关账 ledger     |
| `contract-compliance-evidence.md`            | doubt 跟进 · 契约还债       | GitNexus/门禁/TDD 声明 |

### 5.2 切片开工前必读

**SSOT 超集：** `EXTERNAL-INDEX.md` §A（包外 8 项路径表）。下列为包内最小开工集；§A 未列项（wave index、roadmap、orchestrator §13.4.2、guardrails、待修复清单、ops 文档）**开工前须按 §A 补读**。

1. 本文件 §1–§4
2. `to-issues-slices.md` 当前切片行
3. `reference-adoption-dcp05.md`
4. ADR-028
5. 活卡 `R3_DCP_05_TIER_A_INCREMENTAL.md`（EXTERNAL-INDEX §A 第 1 行）
6. **其余包外必读：** `EXTERNAL-INDEX.md` §A 第 2–8 行（wave index · roadmap · orchestrator · guardrails · 待修复清单 · ops 文档）

### 5.3 执行情境路由

| 情境           | 再读                                                            |
| -------------- | --------------------------------------------------------------- |
| S00 schema     | `plan-spec.md` migration sketch · `013_clean_domain_tables.sql` |
| 宏观源 S03–S06 | `ops/fred_incremental_run.py` · reference bis L2                |
| baostock S01   | DCP-01 归档 · `data_commands.py:443`                            |
| registry S13   | `待修复清单.md` §4 eastmoney · loop_maintain                    |

---

## 6. Execute 顺序指针

见 `to-issues-slices.md` 依赖图：S00 → 并行源片 → S12 → S13

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。 由 `context_router.py --task` 写入；本段不重复列举。
