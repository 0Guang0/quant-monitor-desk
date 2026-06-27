# 执行索引 — R3G-01 Sandbox Clean-Write Rehearsal

> P0i：**索引完整**（v4 · Plan 2026-06-27）

## 0. 冻结元数据

| 字段         | 值                                                                                                                           |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| slug         | `06-27-06-27-round3g-sandbox-rehearsal`                                                                                      |
| source_card  | `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_01_SANDBOX_CLEAN_WRITE_REHEARSAL.md` |
| frozen_card  | `frozen/R3G_01_SANDBOX_CLEAN_WRITE_REHEARSAL.md`                                                                             |
| batch / item | Batch 3G / `R3G-01`                                                                                                          |
| batch map    | `ROUND3_BATCH_IMPLEMENTATION_MAP.md`                                                                                         |
| branch       | `feature/round3g-sandbox-rehearsal`                                                                                          |

### 0.1 血缘

| 任务卡 AC                    | Step     | 验证链 |
| ---------------------------- | -------- | ------ |
| AC-01 sandbox only           | 9.4, 9.5 | §2.1   |
| AC-02 capped candidates      | 9.1      | §2     |
| AC-03 compose gates          | 9.4      | §2     |
| AC-03b SourceConflict defer  | 9.4      | §2     |
| AC-04 data-health per source | 9.4      | §2     |
| AC-05 report fields          | 9.3, 9.4 | §2     |
| AC-06 FRED auth              | 9.1, 9.4 | §2     |
| AC-07 no 参考项目            | 9.6      | §2     |
| AC-08 JQ2PTrade deny         | 9.6      | §2     |
| AC-09 OpenBB arch only       | 9.6      | §2     |
| AC-10 rollback + WM op       | 9.4      | §2     |
| AC-10b no-mutation proof     | 9.4      | §2     |
| AC-11 tests                  | 9.6, 9.7 | §2.1   |
| AC-12 CLI                    | 9.5      | §2     |
| AC-13 prod path refuse       | 9.5      | §2     |
| AC-14 production_live policy | 9.5, 9.6 | §2     |

## 1. 步骤与证据（Execute）

| Step | 锚点                       | RED 命令                                                                                            | GREEN 命令                                                                                                                                                                                                       | 证据路径                                    |
| ---- | -------------------------- | --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| 9.0  | Boot                       | `uv run pytest tests/test_round3g_sandbox_rehearsal_loader.py -q`（ModuleNotFoundError 预期）       | `true`（Boot 读清单记录）                                                                                                                                                                                        | `execute-evidence/9.0-{red,green}.txt`      |
| 9.1  | rehearsal_plan + FRED auth | `uv run pytest tests/test_round3g_sandbox_clean_write_rehearsal.py -q -k RehearsalPlan`（新测红）   | `uv run pytest tests/test_round3g_sandbox_clean_write_rehearsal.py -q -k RehearsalPlan`                                                                                                                          | `execute-evidence/9.1-{red,green}.txt`      |
| 9.2  | rehearsal_loader           | `uv run pytest tests/test_round3g_sandbox_rehearsal_loader.py -q`                                   | 同上全绿                                                                                                                                                                                                         | `execute-evidence/9.2-{red,green}.txt`      |
| 9.3  | rehearsal_report           | `uv run pytest tests/test_round3g_sandbox_rehearsal_report.py -q`                                   | 同上全绿                                                                                                                                                                                                         | `execute-evidence/9.3-{red,green}.txt`      |
| 9.4  | rehearsal_runner           | `uv run pytest tests/test_round3g_sandbox_clean_write_rehearsal.py -q -k RehearsalRunner`（新测红） | 同上全绿                                                                                                                                                                                                         | `execute-evidence/9.4-{red,green}.txt`      |
| 9.5  | CLI                        | `uv run pytest tests/test_round3g_sandbox_clean_write_rehearsal.py -q -k RehearsalCli`（新测红）    | 同上 + `qmd data sandbox-clean-write rehearse --help`                                                                                                                                                            | `execute-evidence/9.5-{red,green}.txt`      |
| 9.6  | guardrails                 | `uv run pytest tests/test_reference_adoption_guardrails.py -q -k r3g01SandboxCleanWrite`（新测红）  | `uv run pytest tests/test_reference_adoption_guardrails.py tests/test_round3g_sandbox_clean_write_rehearsal.py tests/test_round3g_sandbox_rehearsal_loader.py tests/test_round3g_sandbox_rehearsal_report.py -q` | `execute-evidence/9.6-{red,green}.txt`      |
| 9.7  | merge                      | 子集若有红                                                                                          | §2.1 Tier A+ 全库 pytest + loop_maintain                                                                                                                                                                         | `execute-evidence/9.7-{red,green,full}.txt` |

每步 GREEN 后：`uv run pytest -q`（全库）→ 0。

## 2. AC ↔ 测试 / 验收

| AC     | 测试 / 命令                | 通过条件                                                                |
| ------ | -------------------------- | ----------------------------------------------------------------------- |
| AC-01  | runner/CLI 测 sandbox-only | 生产路径拒绝；`production_mutation_allowed=false`                       |
| AC-02  | `test_*cap*` / plan        | 仅 baostock/cninfo/fred；超 cap 拒绝                                    |
| AC-03  | runner integration         | DSS/RoutePlanner/ResourceGuard/ValidationGate/WM + conflict summary     |
| AC-03b | runner test                | `conflict_check_summary.json` 单源 defer                                |
| AC-04  | runner per-source DH       | baostock→market_bar_p0；cninfo→staged_pilot_v3；fred→fred_sandbox_pilot |
| AC-05  | report tests               | 契约 `required_report_fields` 全有                                      |
| AC-06  | auth tests                 | 无 artifact → fail；有 artifact → fred 可排练                           |
| AC-07  | guardrails rg              | 无 `参考项目` runtime import                                            |
| AC-08  | guardrails                 | 无 JQ2PTrade 交易 API 名                                                |
| AC-09  | guardrails                 | OpenBB 仅架构引用                                                       |
| AC-10  | runner report              | `write_manager_operation_id` + `rollback_artifact_path`                 |
| AC-10b | runner evidence            | `production_db_no_mutation_proof.md` 存在                               |
| AC-11  | §1 9.6–9.7                 | 活卡 §9 所列 pytest 全绿                                                |
| AC-12  | CLI test `RehearsalCli`    | `--no-production-mutation` 缺失则失败                                   |
| AC-13  | CLI test                   | `DEFAULT_PRODUCTION_DB` 路径拒绝                                        |
| AC-14  | policy test                | 不宣称 production-live；对齐 `production_live_pilot_policy.md`          |

### 2.1 Tier

| 层  | 命令                                                                                                                                                                                                             | 环境     |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| A   | `uv run pytest tests/test_round3g_sandbox_clean_write_rehearsal.py tests/test_round3g_sandbox_rehearsal_loader.py tests/test_round3g_sandbox_rehearsal_report.py tests/test_reference_adoption_guardrails.py -q` | local/ci |
| A+  | `uv run pytest -q`（全库）                                                                                                                                                                                       | local/ci |
| B   | `uv sync --locked` + `uv run python scripts/loop_maintain.py --fix`（若触 backend/specs）                                                                                                                        | local/ci |

**Tier B 说明：** R3G-01 **无** Execute prod-path；sandbox DB 仅在 `.audit-sandbox/round3g/`。

## 3. 必须读原文（manifest）

| path                                                                                                                                         | manifest         | audience | extract                       | for      |
| -------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- | -------- | ----------------------------- | -------- |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`                                                                                        | must-read        | execute  | scope boundaries              | 9.0      |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`                                                                                         | must-read        | execute  | TDD 五字段                    | 9.0      |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`                                                                                        | must-read        | execute  | 无 broad fetch                | 9.0      |
| `specs/contracts/sandbox_clean_write_contract.yaml`                                                                                          | must-read        | both     | caps + report fields          | AC-02,05 |
| `specs/contracts/reference_adoption_guardrails.yaml`                                                                                         | must-read        | both     | 3G guardrails                 | 9.6      |
| `specs/contracts/data_quality_rules.yaml`                                                                                                    | must-read        | execute  | DQ 规则 SSOT                  | 9.4      |
| `specs/datasource_registry/source_registry.yaml`                                                                                             | must-read        | execute  | 25 源 posture                 | 9.1      |
| `specs/datasource_registry/source_capabilities.yaml`                                                                                         | must-read        | execute  | fred/baostock/cninfo          | 9.1      |
| `specs/datasource_registry/provider_catalog.yaml`                                                                                            | must-read        | execute  | `production_default_enabled`  | 9.1      |
| `backend/app/datasources/service.py`                                                                                                         | must-read        | execute  | fetch 边界                    | 9.4      |
| `backend/app/datasources/route_planner.py`                                                                                                   | must-read        | execute  | 路由                          | 9.4      |
| `backend/app/core/resource_guard.py`                                                                                                         | must-read        | execute  | cap 前门禁                    | 9.4      |
| `backend/app/db/write_manager.py`                                                                                                            | must-read        | execute  | clean write                   | 9.4      |
| `backend/app/db/validation_gate.py`                                                                                                          | must-read        | execute  | 写前校验                      | 9.4      |
| `backend/app/ops/data_health.py`                                                                                                             | must-read        | execute  | profile 入口                  | 9.4      |
| `backend/app/ops/data_health_profiles/ohlcv_rules.py`                                                                                        | must-read        | execute  | OHLCV 规则                    | 9.4      |
| `backend/app/ops/data_health_profiles/calendar_gap_rules.py`                                                                                 | must-read        | execute  | calendar gap                  | 9.4      |
| `backend/app/ops/data_health_profiles/report_builder.py`                                                                                     | must-read        | execute  | DH 报告                       | 9.4      |
| `backend/app/ops/staged_pilot.py`                                                                                                            | must-read        | execute  | compose 样板                  | 9.4      |
| `backend/app/ops/mutation_proof.py`                                                                                                          | must-read        | execute  | no-mutation 证据              | 9.4      |
| `backend/app/ops/fred_sandbox_pilot.py`                                                                                                      | must-read        | execute  | auth YAML 形态                | 9.1      |
| `backend/app/validators/source_conflict.py`                                                                                                  | must-read        | execute  | conflict defer 模式           | 9.4      |
| `.trellis/tasks/archive/2026-06/feature-round3-real-data-staged-pilot/execute-evidence/`                                                     | execute-required | execute  | Batch 2.5 staged 证据样板     | 9.2      |
| `.trellis/tasks/archive/2026-06/06-24-round3-real-data-staged-pilot-v2/execute-evidence/`                                                    | execute-required | execute  | Batch 3 staged v2 证据        | 9.2      |
| `tests/test_data_health_easyxt_profiles.py`                                                                                                  | must-read        | execute  | market_bar_p0 测试            | 9.4      |
| `backend/app/layer1_axes/ingestion.py`                                                                                                       | must-read        | execute  | 勿误扩 allowlist / 禁止 write | 9.0      |
| `backend/app/cli/data_commands.py`                                                                                                           | must-read        | execute  | CLI 挂载点                    | 9.5      |
| `docs/quality/production_live_pilot_policy.md`                                                                                               | must-read        | both     | 禁误宣称 live                 | 9.0      |
| `docs/quality/staged_acceptance_policy.md`                                                                                                   | must-read        | execute  | staged 分层                   | 9.0      |
| `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_02_EASYXT_DATA_HEALTH_REFACTOR.md` | must-read        | execute  | DH profile 写入门禁           | 9.4      |
| `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_06_QMD_DATA_HEALTH_CLI_RUNTIME.md` | must-read        | execute  | CLI runtime                   | 9.4      |
| `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/BATCH_3G_TASK_CARD_MANIFEST.md`                          | must-read        | both     | 3G 串行与范围                 | 9.0      |
| `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/README.md`                                               | must-read        | execute  | batch 入口                    | 9.0      |
| `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/BATCH_3G_COORDINATOR_PLAYBOOK.md`                        | must-read        | execute  | 分支/文件锁                   | 9.0      |
| `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/BATCH_3G_HARDENING_RULES.md`                             | must-read        | both     | 3G 边界                       | 9.0      |
| `.trellis/tasks/round3-fred-authorized-sandbox-pilot/execute-evidence/authorization.yaml`                                                    | execute-required | execute  | FRED auth 字段样板            | 9.1      |
| `docs/quality/batch3f_fred_live_pilot_authorization_2026-06-25.md`                                                                           | audit-only       | audit    | 人类可读授权孪生              | A8       |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`                                                                                                          | audit-only       | audit    | Round 3G 定位                 | A1       |
| `MODULE_COMPLETION_RATING.md`                                                                                                                | audit-only       | audit    | 禁 staged 冒充 R6             | A1       |
| `MIGRATION_MAP.md`                                                                                                                           | must-read        | both     | docs/specs 边界               | 9.0      |

## 4. 已并入冻结任务卡

| 来源                       | 并入        | 摘要                                              |
| -------------------------- | ----------- | ------------------------------------------------- |
| 活卡 §1 价值               | frozen §1   | sandbox 写入链证明                                |
| 活卡 §4 reference adoption | frozen §5   | EasyXT/JQ2PTrade/OpenBB 改写要点                  |
| 活卡 §6 caps               | frozen §6   | r3g01 candidate_caps                              |
| 活卡 §7 CLI                | frozen §7   | rehearse 命令形状                                 |
| 活卡 §8 forbidden          | frozen §8   | 停止条件                                          |
| plan-boot FRED auth        | frozen §6   | artifact 路径/字段                                |
| gitnexus-summary           | frozen §5   | staged_pilot 参考、greenfield 模块                |
| agent audit A-01           | frozen §9.4 | per-source DH 映射                                |
| agent audit A-22           | frozen §9.4 | 禁止 L1 ingestion write；sandbox_clean_write 边界 |

## 5. Audit 追溯集

| 类别                | 文件                                                                     |
| ------------------- | ------------------------------------------------------------------------ |
| 活任务卡            | `R3G_01_SANDBOX_CLEAN_WRITE_REHEARSAL.md`                                |
| frozen              | `frozen/R3G_01_SANDBOX_CLEAN_WRITE_REHEARSAL.md`                         |
| batch manifest      | `BATCH_3G_TASK_CARD_MANIFEST.md`                                         |
| round map           | `ROUND3_BATCH_IMPLEMENTATION_MAP.md`                                     |
| vertical slice plan | `docs/implementation_tasks/PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` |
| project map         | `docs/generated/project_map.generated.json`                              |
| 对抗审计            | `research/plan-adversarial-audit-main-session.md`                        |
| agent 审计          | `research/plan-adversarial-audit-agent.report.md`                        |
| closure             | `research/plan-adversarial-audit-closure.md`                             |

## 6. 机器路由

```bash
uv run python scripts/context_router.py --task .trellis/tasks/06-27-06-27-round3g-sandbox-rehearsal
```

Execute Boot：`frozen/*.md` → 本文 → `context_pack.json` → `trellis-execute/SKILL.md` → `implement.jsonl` 每条 → §3 `must-read`。

Handoff：`python .trellis/scripts/task.py validate-execute-handoff .trellis/tasks/06-27-06-27-round3g-sandbox-rehearsal`
