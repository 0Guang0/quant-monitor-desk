# 执行索引 — R3G-03 Limited Production Clean Write

> P0i：**索引完整**（v4 · Plan 2026-06-27）

## 0. 冻结元数据

| 字段         | 值                                                                                                                            |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| slug         | `06-27-round3g-limited-production-write`                                                                                      |
| source_card  | `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md` |
| frozen_card  | `frozen/R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md`                                                                             |
| batch / item | Batch 3G / `R3G-03`                                                                                                           |
| batch map    | `ROUND3_BATCH_IMPLEMENTATION_MAP.md`                                                                                          |
| branch       | `feature/round3g-limited-production-write`（建议）                                                                            |
| user_gate    | 见 frozen §2.8–10：Plan 授权 ≠ §6 approval；promote 只读 `audit_decision.json`                                                |

### 0.1 血缘

| 任务卡 AC                 | Step     | 验证链 |
| ------------------------- | -------- | ------ |
| AC-01 fail-closed 四门    | 9.1, 9.6 | §2     |
| AC-02 approval/audit 对齐 | 9.1      | §2     |
| AC-03 cap 边界            | 9.1, 9.4 | §2     |
| AC-04 no agent write      | 9.1, 9.7 | §2     |
| AC-05 before/after proof  | 9.2, 9.5 | §2     |
| AC-06 rollback dry-run    | 9.3, 9.5 | §2     |
| AC-07 QMD 门禁链          | 9.4      | §2     |
| AC-08 guardrails          | 9.7      | §2     |
| AC-09 pytest 矩阵         | 9.7, 9.8 | §2.1   |
| AC-10 release note        | 9.8      | §2     |

## 1. 步骤与证据（Execute）

| Step | 锚点                 | RED 命令                                                                                                  | GREEN 命令                                                                                                                                                            | 证据路径                                    |
| ---- | -------------------- | --------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| 9.0  | Boot                 | `uv run pytest tests/test_round3g_limited_production_clean_write.py -q -k PromoteEntry`（ModuleNotFound） | `true`（读 frozen + implement.jsonl）                                                                                                                                 | `execute-evidence/9.0-{red,green}.txt`      |
| 9.1  | approval_contract    | `uv run pytest tests/test_round3g_limited_production_clean_write.py -q -k ApprovalContract`（新测红）     | 同上全绿                                                                                                                                                              | `execute-evidence/9.1-{red,green}.txt`      |
| 9.2  | before_proof         | `uv run pytest tests/test_round3g_limited_production_clean_write.py -q -k BeforeProof`（新测红）          | 同上全绿                                                                                                                                                              | `execute-evidence/9.2-{red,green}.txt`      |
| 9.3  | rollback_plan        | `uv run pytest tests/test_round3g_limited_production_rollback.py -q -k RollbackPlan`（新测红）            | 同上全绿                                                                                                                                                              | `execute-evidence/9.3-{red,green}.txt`      |
| 9.4  | limited_entry runner | `uv run pytest tests/test_round3g_limited_production_clean_write.py -q -k PromoteRunner`（新测红）        | 同上全绿                                                                                                                                                              | `execute-evidence/9.4-{red,green}.txt`      |
| 9.5  | after_proof          | `uv run pytest tests/test_round3g_limited_production_clean_write.py -q -k AfterProof`（新测红）           | 同上全绿                                                                                                                                                              | `execute-evidence/9.5-{red,green}.txt`      |
| 9.6  | CLI promote          | `uv run pytest tests/test_round3g_limited_production_clean_write.py -q -k PromoteCli`（新测红）           | 同上 + `qmd data sandbox-clean-write promote --help`                                                                                                                  | `execute-evidence/9.6-{red,green}.txt`      |
| 9.7  | guardrails           | `uv run pytest tests/test_reference_adoption_guardrails.py -q -k r3g03`（新测红）                         | `uv run pytest tests/test_round3g_limited_production_clean_write.py tests/test_round3g_limited_production_rollback.py tests/test_reference_adoption_guardrails.py -q` | `execute-evidence/9.7-{red,green}.txt`      |
| 9.8  | merge                | 子集若有红                                                                                                | §2.1 Tier A+ 全库 pytest + loop_maintain + release note 片段                                                                                                          | `execute-evidence/9.8-{red,green,full}.txt` |

每步 GREEN 后：`uv run pytest -q`（全库）→ 0。

## 2. AC ↔ 测试 / 验收

| AC    | 测试 / 命令                                                                | 通过条件                                      |
| ----- | -------------------------------------------------------------------------- | --------------------------------------------- |
| AC-01 | `ApprovalContract` / `PromoteCli`                                          | 缺 approval/audit/before/rollback → 异常/非零 |
| AC-02 | `ApprovalContract`                                                         | 字段不一致 block                              |
| AC-03 | `ApprovalContract` + contract caps                                         | 超 r3g03*max*\* block                         |
| AC-04 | `ApprovalContract` + guardrails                                            | agent 标记 block                              |
| AC-05 | `BeforeProof` / `AfterProof`                                               | §7 字段齐全 JSON                              |
| AC-06 | `RollbackPlan`                                                             | dry_run 输出 affected keys                    |
| AC-07 | `PromoteRunner`                                                            | 报告含 WM op id + validation_status           |
| AC-08 | `test_reference_adoption_guardrails.py -k r3g03`                           | 无参考项目 runtime                            |
| AC-09 | §1 9.7–9.8                                                                 | 活卡 §10 所列 pytest 全绿                     |
| AC-10 | `docs/quality/release_notes/` 或任务 `research/release-note-r3g03.md` 片段 | 写明 source/domain/symbol/window              |

### 2.1 Tier

| 层  | 命令                                                                                                                                                                      | 环境              |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| A   | `uv run pytest tests/test_round3g_limited_production_clean_write.py tests/test_round3g_limited_production_rollback.py tests/test_reference_adoption_guardrails.py -q`     | local/ci          |
| A+  | `uv run pytest -q`（全库）                                                                                                                                                | local/ci          |
| B   | `qmd data sandbox-clean-write promote --approval-file <user-yaml> --audit-decision <path> --before-proof <path> --rollback-plan <path> --dry-run`（用户 approval 真路径） | Execute prod-path |

**Tier B 说明：** 仅当用户 §6 approval 中 `production_db_path` 与 Coordinator 显式授权时执行；Plan/CI 默认不跑真写。

## 3. 必须读原文（manifest）

| path                                                                                                                  | manifest         | audience | extract                                      | for      |
| --------------------------------------------------------------------------------------------------------------------- | ---------------- | -------- | -------------------------------------------- | -------- |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`                                                                 | must-read        | execute  | scope boundaries                             | 9.0      |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`                                                                  | must-read        | execute  | TDD 五字段                                   | 9.0      |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`                                                                 | must-read        | execute  | ResourceGuard                                | 9.4      |
| `specs/contracts/sandbox_clean_write_contract.yaml`                                                                   | must-read        | both     | r3g03_limited_entry                          | AC-01–04 |
| `specs/contracts/reference_adoption_guardrails.yaml`                                                                  | must-read        | both     | Round3G guardrails                           | 9.7      |
| `specs/contracts/data_quality_rules.yaml`                                                                             | must-read        | execute  | DQ SSOT                                      | 9.4      |
| `specs/datasource_registry/source_registry.yaml`                                                                      | must-read        | execute  | 候选源 posture                               | 9.1      |
| `specs/datasource_registry/source_capabilities.yaml`                                                                  | must-read        | execute  | fred auth                                    | 9.1      |
| `specs/datasource_registry/provider_catalog.yaml`                                                                     | must-read        | execute  | production_default_enabled                   | 9.1      |
| `backend/app/ops/sandbox_clean_write/rehearsal_runner.py`                                                             | must-read        | execute  | 编排样板                                     | 9.4      |
| `backend/app/ops/sandbox_clean_write/rehearsal_plan.py`                                                               | must-read        | execute  | cap 校验                                     | 9.1      |
| `backend/app/ops/sandbox_clean_write/adversarial_audit.py`                                                            | must-read        | execute  | 审计输入形状                                 | 9.1      |
| `backend/app/ops/sandbox_clean_write/audit_decision.py`                                                               | must-read        | execute  | AuditDecision 枚举                           | 9.1      |
| `backend/app/ops/mutation_proof.py`                                                                                   | must-read        | execute  | before/after proof                           | 9.2, 9.5 |
| `backend/app/db/write_manager.py`                                                                                     | must-read        | execute  | 生产写                                       | 9.4      |
| `backend/app/db/validation_gate.py`                                                                                   | must-read        | execute  | 写前校验                                     | 9.4      |
| `backend/app/core/resource_guard.py`                                                                                  | must-read        | execute  | cap 前门禁                                   | 9.4      |
| `backend/app/datasources/service.py`                                                                                  | must-read        | execute  | fetch 边界                                   | 9.4      |
| `backend/app/datasources/route_planner.py`                                                                            | must-read        | execute  | 路由                                         | 9.4      |
| `backend/app/ops/data_health_profiles/report_builder.py`                                                              | must-read        | execute  | DH 报告                                      | 9.4      |
| `backend/app/ops/staged_pilot.py`                                                                                     | must-read        | execute  | authorization 模式参考                       | 9.1      |
| `backend/app/cli/data_commands.py`                                                                                    | must-read        | execute  | CLI 挂载                                     | 9.6      |
| `backend/app/layer1_axes/ingestion.py`                                                                                | must-read        | execute  | 勿误扩 allowlist                             | 9.0      |
| `docs/quality/production_live_pilot_policy.md`                                                                        | must-read        | both     | 禁误宣称 live                                | 9.0      |
| `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/BATCH_3G_TASK_CARD_MANIFEST.md`   | must-read        | both     | 3G 串行                                      | 9.0      |
| `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/BATCH_3G_HARDENING_RULES.md`      | must-read        | both     | 参考项目边界                                 | 9.7      |
| `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/BATCH_3G_COORDINATOR_PLAYBOOK.md` | must-read        | execute  | 分支锁                                       | 9.0      |
| `.trellis/tasks/archive/2026-06/06-27-06-27-round3g-sandbox-rehearsal/frozen/R3G_01_SANDBOX_CLEAN_WRITE_REHEARSAL.md` | execute-required | execute  | R3G-01 报告字段对齐                          | 9.4      |
| `.trellis/tasks/archive/2026-06/06-27-06-27-round3g-adversarial-audit/research/execute-evidence/`                     | execute-required | execute  | audit 决策样板                               | 9.1      |
| `tests/fixtures/sandbox_clean_write/r3g01/`                                                                           | execute-required | execute  | 排练证据 fixture                             | 9.4      |
| `tests/fixtures/sandbox_clean_write/r3g03/`                                                                           | execute-required | execute  | promote approval/proof 样板（Plan 最小四套） | 9.1      |
| `tests/test_round3g_sandbox_clean_write_rehearsal.py`                                                                 | must-read        | execute  | rehearse CLI 拒生产路径回归                  | 9.6, 9.7 |
| `tests/test_round3g_pre_production_adversarial_audit.py`                                                              | must-read        | execute  | audit CLI 拒生产路径回归                     | 9.6, 9.7 |
| `tests/test_write_manager.py`                                                                                         | must-read        | execute  | WM bypass 对抗测参考                         | 9.4, 9.7 |
| `MIGRATION_MAP.md`                                                                                                    | must-read        | both     | docs/specs 边界                              | 9.0      |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`                                                                                   | audit-only       | audit    | Round 3G 定位                                | A1       |
| `MODULE_COMPLETION_RATING.md`                                                                                         | audit-only       | audit    | R3G-03 完成度                                | A1       |

## 4. 已并入冻结任务卡（不必再读原文）

| 来源                    | 并入            | 摘要                                                       |
| ----------------------- | --------------- | ---------------------------------------------------------- |
| 活卡 §1 价值            | frozen §1       | 有限生产入口                                               |
| 活卡 §2.8–10            | frozen §2       | Plan 授权≠§6 YAML；只读 audit_decision.json；非 sandbox DB |
| 活卡 §3 reference       | frozen §3       | EasyXT/JQ2PTrade/OpenBB/Agent 要点                         |
| 活卡 §4.1               | frozen §4       | 数据流、ponytail 复用表、impact 目标、blast radius         |
| 活卡 §6 approval schema | frozen §6       | YAML 最小字段 + r3g03 caps                                 |
| 活卡 §7 proof 字段      | frozen §7       | before/after/rollback                                      |
| 活卡 §8 + §8.1          | frozen §8       | forbidden + Execute 六条停止条件 + 风险缓解                |
| 活卡 §9 步骤            | frozen §9       | 9 步实现顺序                                               |
| 活卡 §10.1              | frozen §10.1    | block_if 对抗测矩阵                                        |
| grill-me Q1–Q7          | frozen §2/§8/§9 | dry_run 默认、无真删 rollback、FRED live 条件              |
| gitnexus-summary        | frozen §4.1     | 复用决策与 impact 符号                                     |
| prd 风险表              | frozen §8.1     | 双锁、逐字段 equality、rollback identify-only              |
| plan-boot 边界一句      | frozen §1       | promote 四门链                                             |
| EXECUTION_INDEX §0.1    | frozen §11 前   | AC↔Step 见索引 §0.1 / §2                                   |

## 5. Audit 追溯集

| 类别           | 文件                                                                    |
| -------------- | ----------------------------------------------------------------------- |
| 活任务卡       | `R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md`                              |
| frozen         | `frozen/R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md`                       |
| R3G-01 归档    | `.trellis/tasks/archive/2026-06/06-27-06-27-round3g-sandbox-rehearsal/` |
| R3G-02 归档    | `.trellis/tasks/archive/2026-06/06-27-06-27-round3g-adversarial-audit/` |
| batch manifest | `BATCH_3G_TASK_CARD_MANIFEST.md`                                        |
| round map      | `ROUND3_BATCH_IMPLEMENTATION_MAP.md`                                    |
| project map    | `docs/generated/project_map.generated.json`                             |
| Plan 对抗审计  | `research/plan-adversarial-audit-main-session.md`                       |
| omission       | `research/project-map-omission-check.md`                                |

## 6. 机器路由

```bash
uv run python scripts/context_router.py --task .trellis/tasks/06-27-round3g-limited-production-write
```

Execute Boot：`frozen/*.md` → 本文 → `context_pack.json` → `trellis-execute/SKILL.md` → `implement.jsonl` 每条 → §3 `must-read`。

Handoff：`python .trellis/scripts/task.py validate-execute-handoff .trellis/tasks/06-27-round3g-limited-production-write`
