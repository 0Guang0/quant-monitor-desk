# 执行索引 — R3FR-07 Legacy Wrapper Cleanup and Redirects

> P0i：**索引完整**（v4 · 对抗性 Plan 审计 2026-06-27 已修复 ADV-07-01..25）  
> **读者：Execute + Audit**  
> **冻结任务卡：** `frozen/R3FR_07_LEGACY_WRAPPER_CLEANUP_AND_REDIRECTS.md`  
> **审计矩阵：** `AUDIT.plan.md`  
> **对抗性审计：** `research/adversarial-plan-audit.report.md`

---

## 0. 冻结元数据

| 字段         | 值                                                                                                                                                    |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| slug         | `06-27-round3fr-cleanup-rehome`                                                                                                                       |
| task_dir     | `.trellis/tasks/06-27-06-27-round3fr-cleanup-rehome`                                                                                                  |
| source_card  | `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_07_LEGACY_WRAPPER_CLEANUP_AND_REDIRECTS.md` |
| frozen_card  | `frozen/R3FR_07_LEGACY_WRAPPER_CLEANUP_AND_REDIRECTS.md`                                                                                              |
| batch / item | `ROUND_3_REFERENCE_ADOPTION_REFACTOR` / `R3FR-07`                                                                                                     |
| 分支         | `chore/round3fr-cleanup-rehome`（**禁止在 master 上 Execute**）                                                                                       |
| batch map    | `PROJECT_IMPLEMENTATION_ROADMAP.md` §3F-R · `ROUND3_BATCH_IMPLEMENTATION_MAP.md`                                                                      |

### 0.1 血缘

| AC       | Step | 测试 / 命令                                                                                 | 验证链 |
| -------- | ---- | ------------------------------------------------------------------------------------------- | ------ |
| AC-07-01 | 9.1  | `test_r3fr07_*`（parent + batch README + impl README）                                      | §2     |
| AC-07-02 | 9.2  | `test_checkDailyBars_canonicalRedirectDoc` + `test_ops_data_health.py`                      | §2     |
| AC-07-02 | 9.3  | `test_healthCheck_canonicalRedirectDoc` + `test_qmd_data_cli.py`                            | §2     |
| AC-07-02 | 9.4  | `test_tdxProbePort_delegateDoc` + tdx 回归                                                  | §2     |
| AC-07-03 | 9.5  | `test_roadmapAndHandoff_mark3frClosed`                                                      | §2     |
| AC-07-04 | 9.5  | `test_batch3gReadme_preconditionsSatisfied` + `test_batch3gCoordinator_preconditionWording` | §2     |
| AC-07-05 | 9.5  | `test_moduleRating_providerCatalogPostR3fr05`                                               | §2     |
| AC-07-06 | 9.7  | §2.1 Tier B                                                                                 | §2.1   |
| AC-07-07 | 9.5  | `test_batchImplementationMap_checkpointPost3fr07`                                           | §2     |
| AC-07-08 | 9.1  | `test_inventoryRedirectCard_intact`                                                         | §2     |

### 0.2 前置 replacement 证据（只读对照）

| 前置任务   | 归档摘要路径                                                                                          |
| ---------- | ----------------------------------------------------------------------------------------------------- |
| R3FR-02+06 | `.trellis/tasks/archive/2026-06/06-26-round3fr-data-health-cli/research/execute-evidence-summary.md`  |
| R3FR-03    | `.trellis/tasks/archive/2026-06/06-26-round3fr-tdx-provider/research/execute-evidence-summary.md`     |
| R3FR-05    | `.trellis/tasks/archive/2026-06/06-26-round3fr-provider-catalog/research/execute-evidence-summary.md` |

---

## 1. 步骤与证据（Execute）

| Step | 切片                | RED 命令                                                                                                                                                                                                                                | GREEN 命令         | 证据                                   |
| ---- | ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | -------------------------------------- |
| 9.0  | Boot 基线           | `uv run pytest tests/test_reference_adoption_guardrails.py tests/test_qmd_data_cli.py tests/test_ops_data_health.py tests/test_tdx_manual_probe.py tests/test_tdx_live_manual_probe_authorization.py tests/test_provider_catalog.py -q` | 同左               | `execute-evidence/9.0-{red,green}.txt` |
| 9.1  | 规划叙事            | `uv run pytest tests/test_r3fr07_legacy_wrapper_cleanup.py -k "Readme or inventory" -q`（须先 RED）                                                                                                                                     | 同左               | `9.1-{red,green}.txt`                  |
| 9.2  | data health shim    | **先** GitNexus `impact(check_daily_bars)`；`uv run pytest tests/test_r3fr07_legacy_wrapper_cleanup.py::test_checkDailyBars_canonicalRedirectDoc tests/test_ops_data_health.py -q`                                                      | 同左               | `9.2-{red,green}.txt`                  |
| 9.3  | CLI redirect        | `uv run pytest tests/test_r3fr07_legacy_wrapper_cleanup.py::test_healthCheck_canonicalRedirectDoc tests/test_qmd_data_cli.py tests/test_data_cli_contract.py -q`                                                                        | 同左               | `9.3-{red,green}.txt`                  |
| 9.4  | TDX redirect        | `uv run pytest tests/test_r3fr07_legacy_wrapper_cleanup.py::test_tdxProbePort_delegateDoc tests/test_tdx_manual_probe.py tests/test_tdx_live_manual_probe_authorization.py -q`                                                          | 同左               | `9.4-{red,green}.txt`                  |
| 9.5  | 3F-R 关门 / 3G 入口 | `uv run pytest tests/test_r3fr07_legacy_wrapper_cleanup.py -k "roadmap or batch3g or moduleRating or batchImplementation" -q`                                                                                                           | 同左               | `9.5-{red,green}.txt`                  |
| 9.6  | guardrails + loop   | `uv run pytest tests/test_reference_adoption_guardrails.py tests/test_documentation_index.py tests/test_docs_specs_indexed.py -q`；新测后 `uv run python scripts/loop_maintain.py --fix`；再 `uv run python scripts/loop_maintain.py`   | 同左               | `9.6-{red,green}.txt`                  |
| 9.7  | 全量验收            | N/A（收尾）                                                                                                                                                                                                                             | `uv run pytest -q` | `9.7-{red,green}.txt`                  |

> 每步 GREEN：`incremental-implementation` → 相关 targeted pytest。

---

## 2. AC ↔ 测试 / 验收

| AC       | 测试 / 命令                                                            | 通过条件                                 |
| -------- | ---------------------------------------------------------------------- | ---------------------------------------- |
| AC-07-01 | `test_r3fr07_*` README 族（parent/batch/impl）                         | 无 stale `health_check` placeholder 声称 |
| AC-07-02 | `test_r3fr07_*` runtime redirect + 回归                                | docstring/委托存在；回归全绿             |
| AC-07-03 | `test_roadmapAndHandoff_mark3frClosed`                                 | 3F-R CLOSED + 3G next                    |
| AC-07-04 | `test_batch3gReadme_*` + `test_batch3gCoordinator_*`                   | 前置 satisfied；非 blocked-only          |
| AC-07-05 | `test_moduleRating_providerCatalogPostR3fr05`                          | provider catalog ≥ R2                    |
| AC-07-06 | 任务卡 §5 五档 + `test_r3fr07` + `test_provider_catalog` + full pytest | 全绿                                     |
| AC-07-07 | `test_batchImplementationMap_checkpointPost3fr07`                      | map checkpoint 反映 3F-R 关门            |
| AC-07-08 | `test_inventoryRedirectCard_intact`                                    | inventory 卡仍 redirect                  |

### 2.1 Tier

| 层  | 命令                                                                                                                 |
| --- | -------------------------------------------------------------------------------------------------------------------- |
| A   | 任务卡 §11 targeted pytest + `test_r3fr07` + `test_provider_catalog.py`                                              |
| B   | `uv run pytest -q`                                                                                                   |
| C   | `uv run python scripts/loop_maintain.py --fix` 后 `loop_maintain.py`                                                 |
| D   | `uv run python .trellis/scripts/task.py validate-execute-handoff .trellis/tasks/06-27-06-27-round3fr-cleanup-rehome` |

---

## 3. 必须读原文（manifest · 自动生成 jsonl）

> **规则：** 已无损并入 frozen §5–§8 的标 `summary-ok`，不得重复列入。  
> `context_pack.json` modules 为空时，**以本表为权威**（ADV-07-22）；Boot 可复跑 `context_router.py --task <dir>`。

| path                                                                                                                                                    | manifest         | audience | extract                             | for      |
| ------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- | -------- | ----------------------------------- | -------- |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`                                                                                                   | must-read        | execute  | scope boundaries                    | §9.0     |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`                                                                                                    | must-read        | execute  | 五字段 TDD                          | §10      |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`                                                                                                   | must-read        | execute  | 无 live fetch / 无界扫描            | §9.0     |
| `MIGRATION_MAP.md`                                                                                                                                      | must-read        | execute  | docs vs backend 边界                | §9.0     |
| `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_HARDENING_RULES.md`                      | must-read        | both     | §9 cleanup boundary                 | §8       |
| `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_COORDINATOR_PLAYBOOK.md`                 | must-read        | execute  | §2 文件锁 · §3 合并顺序             | §9.0     |
| `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_TASK_CARD_MANIFEST.md`                   | must-read        | execute  | R3FR DONE 行                        | §9.1     |
| `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/README.md`                                                                               | must-read        | execute  | §3 过时叙事修正                     | AC-07-01 |
| `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/README.md`                                         | must-read        | execute  | §1 表 placeholder 列                | AC-07-01 |
| `docs/implementation_tasks/README.md`                                                                                                                   | must-read        | execute  | §执行顺序 item 9→10                 | AC-07-03 |
| `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`                                                                                            | execute-required | execute  | 勿误关 DEFERRED                     | §8       |
| `docs/implementation_tasks/PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md`                                                                                | must-read        | both     | 地图不是工单                        | §9.6     |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`                                                                                                                     | must-read        | execute  | §3.6 条件 A                         | AC-07-03 |
| `docs/ROUND3_HANDOFF.md`                                                                                                                                | must-read        | execute  | 3F-R CLOSED 节                      | AC-07-03 |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md`                                                                                                                    | must-read        | execute  | checkpoint 行                       | AC-07-07 |
| `MODULE_COMPLETION_RATING.md`                                                                                                                           | must-read        | execute  | provider catalog 评级               | AC-07-05 |
| `docs/ops/data_health_cli.md`                                                                                                                           | must-read        | execute  | CLI 行为与 envelope                 | §9.3     |
| `specs/contracts/data_cli_contract.yaml`                                                                                                                | must-read        | both     | `must_use: run_data_health_profile` | §9.3     |
| `specs/contracts/data_quality_rules.yaml`                                                                                                               | must-read        | execute  | `ops_cli_profiles`                  | §9.2/9.3 |
| `specs/contracts/reference_adoption_guardrails.yaml`                                                                                                    | must-read        | both     | no central inventory                | §9.6     |
| `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/README.md`                                                          | must-read        | both     | §3 前置条件                         | AC-07-04 |
| `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/BATCH_3G_TASK_CARD_MANIFEST.md`                                     | must-read        | both     | 3G 卡结构                           | AC-07-04 |
| `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/BATCH_3G_COORDINATOR_PLAYBOOK.md`                                   | must-read        | both     | §0 门禁措辞                         | AC-07-04 |
| `.trellis/tasks/06-27-06-27-round3fr-cleanup-rehome/research/integration-ledger.md`                                                                     | execute-required | execute  | 允许/禁止文件                       | §9.0     |
| `.trellis/tasks/archive/2026-06/06-26-round3fr-data-health-cli/research/execute-evidence-summary.md`                                                    | execute-required | execute  | R3FR-02+06 已 stronger              | §9.2     |
| `.trellis/tasks/archive/2026-06/06-26-round3fr-tdx-provider/research/execute-evidence-summary.md`                                                       | execute-required | execute  | R3FR-03 已 stronger                 | §9.4     |
| `.trellis/tasks/archive/2026-06/06-26-round3fr-provider-catalog/research/execute-evidence-summary.md`                                                   | execute-required | execute  | R3FR-05 已 stronger                 | §9.5     |
| `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_01_REFERENCE_INVENTORY_AND_LICENSE_MATRIX.md` | audit-only       | audit    | redirect 卡对照                     | AC-07-08 |

---

## 4. 已并入冻结任务卡（不必再读原文）

| 来源                                 | 并入章节           | 摘要                  |
| ------------------------------------ | ------------------ | --------------------- |
| 活任务卡附录 B/C cleanup behavior    | frozen §8          | wrapper redirect 规则 |
| `research/grill-me-session.md` Q1–Q6 | frozen §8 停止条件 | 非 doc-only           |

---

## 5. Audit 追溯集

| 类别               | 文件                                                                       |
| ------------------ | -------------------------------------------------------------------------- |
| 活任务卡           | `R3FR_07_LEGACY_WRAPPER_CLEANUP_AND_REDIRECTS.md`                          |
| frozen             | `frozen/R3FR_07_LEGACY_WRAPPER_CLEANUP_AND_REDIRECTS.md`                   |
| omission-check     | `research/project-map-omission-check.md`                                   |
| adversarial        | `research/adversarial-plan-audit.report.md`                                |
| integration-ledger | `research/integration-ledger.md`                                           |
| unresolved         | `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`               |
| round map          | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` · `PROJECT_IMPLEMENTATION_ROADMAP.md` |
| handoff            | `docs/ROUND3_HANDOFF.md`                                                   |

---

## 6. 机器路由

`context_pack.json` — `uv run python scripts/context_router.py --task .trellis/tasks/06-27-06-27-round3fr-cleanup-rehome`  
Execute Boot：`frozen/*.md` → 本文 → `implement.jsonl` **每一条** → `context_pack.json` → `trellis-execute/SKILL.md` → §3 行。
