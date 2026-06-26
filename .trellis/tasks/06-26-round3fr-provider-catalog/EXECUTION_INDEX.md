# 执行索引 — R3FR-05 Provider Catalog OpenBB Reference

> P0i：**索引完整**（v4 · 对抗性审计 2026-06-26 已修复）

## 0. 冻结元数据

| 字段          | 值                                                                                                                                                 |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| slug          | `06-26-round3fr-provider-catalog`                                                                                                                  |
| source_card   | `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_05_PROVIDER_CATALOG_OPENBB_REFERENCE.md` |
| frozen_card   | `frozen/R3FR_05_PROVIDER_CATALOG_OPENBB_REFERENCE.md`                                                                                              |
| batch/item    | Batch 3F-R / `R3FR-05`                                                                                                                             |
| batch map     | `ROUND3_BATCH_IMPLEMENTATION_MAP.md`                                                                                                               |
| branch        | `feature/round3fr-provider-catalog`                                                                                                                |
| registry 基数 | 当前 23 + 本批补 2 = **25** catalog 覆盖                                                                                                           |

### 0.1 血缘

| 任务卡 AC | Step     | 验证链                                      |
| --------- | -------- | ------------------------------------------- |
| AC-1      | 9.2      | §2 test_everyRegistrySource_hasCatalogEntry |
| AC-2      | 9.1, 9.2 | §2 enum + required fields                   |
| AC-3      | 9.2      | §2 production + proposed external           |
| AC-4      | 9.2      | §2 fred/TDX/QMT/xqshare                     |
| AC-5      | 9.5      | §2 openbb + guardrails                      |
| AC-6      | 9.1–9.6  | §2 + 全库 pytest                            |
| AC-7      | 9.4, 9.6 | §2 contract refs + loop --fix               |

## 1. 步骤与证据（Execute）

| Step | 锚点       | RED 命令                                                                      | GREEN 命令                                                                                      | 证据路径                                      |
| ---- | ---------- | ----------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | --------------------------------------------- |
| 9.0  | Boot       | `uv run pytest tests/test_provider_catalog.py -q`（预期 ModuleNotFoundError） | `true`（Boot 完成记录）                                                                         | `execute-evidence/9.0-{red,green}.txt`        |
| 9.1  | §5 结构    | 同上 RED                                                                      | `uv run pytest tests/test_provider_catalog.py -q -k "RequiredFields or Enums"`                  | `execute-evidence/9.1-{red,green}.txt`        |
| 9.2  | §4 全量    | registry/capability 覆盖红                                                    | `uv run pytest tests/test_provider_catalog.py tests/test_source_capabilities.py -q`             | `execute-evidence/9.2-{red,green}.txt`        |
| 9.3  | loader     | loader 测试红                                                                 | `uv run pytest tests/test_provider_catalog.py -q -k loader`                                     | `execute-evidence/9.3-{red,green}.txt`        |
| 9.4  | contracts  | `test_provider_catalog_contractRefs` 红                                       | `uv run pytest tests/test_provider_catalog.py tests/test_source_capabilities.py -q -k contract` | `execute-evidence/9.4-{red,green}.txt`        |
| 9.5  | guardrails | `test_r3fr05ProviderCatalogClosure` 红                                        | `uv run pytest tests/test_reference_adoption_guardrails.py -q -k r3fr05`                        | `execute-evidence/9.5-{red,green}.txt`        |
| 9.6  | merge      | 子集若有红则 RED                                                              | 见 §2.1 Tier A+B+全库                                                                           | `execute-evidence/9.6-{red,green,full}-*.txt` |

每步 GREEN 后：`uv run pytest -q`（全库）→ 0。

## 2. AC ↔ 测试 / 验收

| AC   | 测试 / 命令                                                                                                 | 通过条件                         |
| ---- | ----------------------------------------------------------------------------------------------------------- | -------------------------------- |
| AC-1 | `test_everyRegistrySource_hasCatalogEntry`                                                                  | 25 源、每源恰一 provider         |
| AC-2 | `test_catalogRequiredFields_present` + `test_catalogEnums_matchSchemaCheck`                                 | 字段全、enum 零违规              |
| AC-3 | `test_proposedExternalSources_notProductionEnabled` + `test_productionDefaultCandidate_distinctFromEnabled` | 外部源 + 两字段分离              |
| AC-4 | `test_fredAndLocalTerminalPosture`                                                                          | fred auth；qmt/tdx/xqshare false |
| AC-5 | `test_openbbReference_noRuntimeCopy` + `test_r3fr05ProviderCatalogClosure`                                  | 双绿                             |
| AC-6 | §1 9.6 + 全库 pytest                                                                                        | 全绿                             |
| AC-7 | `test_provider_catalog_contractRefs` + `loop_maintain.py --fix`                                             | contract 路径 + catalog 登记     |

附加必做（非独立 AC）：

- `test_catalogStatus_matchesCapabilityRegistry`
- `test_catalogEnabledByDefault_notLooserThanRegistry`
- `test_catalogPosture_alignsWithSourceRegistry`
- `test_unknownSourceInRegistry_mustHaveCapabilityOrProposedStatus`（9.2 后仍绿）

### 2.1 Tier

| 层  | 命令                                                                                                                                                          | 环境     |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| A   | `uv run pytest tests/test_provider_catalog.py tests/test_source_capabilities.py tests/test_reference_adoption_guardrails.py tests/test_source_registry.py -q` | local/ci |
| A+  | `uv run pytest -q`（全库）                                                                                                                                    | local/ci |
| B   | `uv run python scripts/loop_maintain.py --fix`                                                                                                                | local/ci |

## 3. 必须读原文（manifest）

| path                                                                                                                                    | manifest  | audience | extract                 | for  |
| --------------------------------------------------------------------------------------------------------------------------------------- | --------- | -------- | ----------------------- | ---- |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`                                                                                   | must-read | execute  | scope                   | 9.0  |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`                                                                                    | must-read | execute  | TDD + 五字段            | 9.1  |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`                                                                                   | must-read | execute  | 无 live fetch           | 9.0  |
| `specs/schema/schema.sql`                                                                                                               | must-read | both     | CHECK enums             | AC-2 |
| `backend/app/db/migrations/009_status_check_constraints.sql`                                                                            | must-read | both     | CHECK enums             | AC-2 |
| `specs/datasource_registry/source_registry.yaml`                                                                                        | must-read | execute  | 23+2 源                 | 9.2  |
| `specs/datasource_registry/source_capabilities.yaml`                                                                                    | must-read | execute  | status + openbb stub    | 9.2  |
| `specs/contracts/source_capability_contract.yaml`                                                                                       | must-read | both     | AC-7 编辑目标           | 9.4  |
| `specs/contracts/datasource_service_contract.yaml`                                                                                      | must-read | both     | AC-7 编辑目标           | 9.4  |
| `specs/contracts/reference_adoption_guardrails.yaml`                                                                                    | must-read | both     | OpenBB + required_tests | 9.5  |
| `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_COORDINATOR_PLAYBOOK.md` | must-read | execute  | file lock / merge       | 9.2  |

## 4. 已并入冻结任务卡

| 来源                             | 并入         | 摘要                              |
| -------------------------------- | ------------ | --------------------------------- |
| `design.md` §1–§3                | frozen §5–§6 | 模型、映射、loader                |
| `openbb_provider_architecture`   | frozen §5    | gitignore 参考项目；读 guardrails |
| `MIGRATION_MAP.md` / project_map | §6 loop      | Execute 后 `--fix` 索引           |

## 5. Audit 追溯集

| 类别        | 文件                                                  |
| ----------- | ----------------------------------------------------- |
| 活任务卡    | `R3FR_05_PROVIDER_CATALOG_OPENBB_REFERENCE.md`        |
| frozen      | `frozen/R3FR_05_PROVIDER_CATALOG_OPENBB_REFERENCE.md` |
| 对抗审计    | `research/plan-adversarial-audit.report.md`           |
| batch       | `BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/README.md`     |
| round map   | `ROUND3_BATCH_IMPLEMENTATION_MAP.md`                  |
| project map | `docs/generated/project_map.generated.json`           |

## 6. Loop / context / handoff

- `test_provider_catalog.py` 在 **9.1 创建后** 由 Execute 追加到 `implement.jsonl`（Plan 阶段路径不存在，勿预列）

- Execute 6.pre：`research/gitnexus-execute-summary.md`（非 Plan 的 `gitnexus-summary.md`）
- Handoff：`validate-execute-handoff` + `research/context-closure.md`
- `validate-plan-freeze` exit 0 **不**等于 manifest 全量无缺口；Execute 前可读 `research/plan-adversarial-audit.report.md`
