# 执行索引 — R3H-02 Market Data Adapters

> P0i：**索引完整**（v4 · Plan 2026-06-28）

## 0. 冻结元数据

| 字段         | 值                                                                                                                                |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| slug         | `06-28-06-28-round3h-r3h02-market-data`                                                                                           |
| source_card  | `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_02_MARKET_DATA_ADAPTERS.md` |
| frozen_card  | `frozen/R3H_02_MARKET_DATA_ADAPTERS.md`                                                                                           |
| frozen_at    | 2026-06-28（对抗性审计回补后 re-freeze）                                                                                          |
| batch / item | Batch 3H / `R3H-02`                                                                                                               |
| batch map    | `PROJECT_IMPLEMENTATION_ROADMAP.md` §5.0                                                                                          |
| branch       | `feature/round3h-r3h02-market-data`（建议）                                                                                       |
| user_gate    | 见 frozen §2.8：禁止主库；yahoo validation-only；AV live 须 API key                                                               |

### 0.1 血缘

| 任务卡 AC            | Step | 验证链 |
| -------------------- | ---- | ------ |
| AC-EVIDENCE 契约     | 9.1  | §2     |
| AC-ALPHA port/route  | 9.2  | §2     |
| AC-STOOQ validation  | 9.3  | §2     |
| AC-YAHOO validation  | 9.4  | §2     |
| AC-CRYPTO deribit/cg | 9.5  | §2     |
| AC-REGISTRY 五源     | 9.6  | §2     |
| AC-LAYER smoke       | 9.7  | §2     |
| AC-MERGE             | 9.8  | §2.1   |

**切片依赖（to-issues S0–S8）：** 9.1→阻塞 9.2–9.5/9.7；9.3–9.5 可并行（9.1 后）；9.6 须 9.2–9.5 + coordinator；9.8 最后。

## 1. 步骤与证据（Execute）

| Step | 锚点                          | RED 命令                                                                                                                                                                            | GREEN 命令                                                                                                                                                          | 证据路径                                                   |
| ---- | ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| 9.0  | boot_test_skeleton            | `uv run pytest tests/test_market_data_adapters.py tests/test_crypto_market_adapters.py -q`（ModuleNotFound）                                                                        | 同上空壳绿                                                                                                                                                          | `execute-evidence/9.0-{red,green}.txt`                     |
| 9.1  | market_data_evidence_contract | `uv run pytest tests/test_market_data_adapters.py -q -k evidence_contract`                                                                                                          | 同上全绿                                                                                                                                                            | `execute-evidence/9.1-{red,green}.txt`                     |
| 9.2  | alpha_vantage_port            | `uv run pytest tests/test_market_data_adapters.py -q -k alpha_vantage`                                                                                                              | 同上全绿                                                                                                                                                            | `execute-evidence/9.2-{red,green}.txt`                     |
| 9.3  | stooq_port                    | `uv run pytest tests/test_market_data_adapters.py -q -k stooq`                                                                                                                      | 同上全绿                                                                                                                                                            | `execute-evidence/9.3-{red,green}.txt`                     |
| 9.4  | yahoo_finance_port            | `uv run pytest tests/test_market_data_adapters.py -q -k yahoo`                                                                                                                      | 同上全绿                                                                                                                                                            | `execute-evidence/9.4-{red,green}.txt`                     |
| 9.5  | deribit_coingecko_ports       | `uv run pytest tests/test_crypto_market_adapters.py -q`                                                                                                                             | 同上全绿                                                                                                                                                            | `execute-evidence/9.5-{red,green}.txt`                     |
| 9.6  | registry_coordinator          | `uv run pytest tests/test_source_route_planner.py tests/test_source_capabilities.py tests/test_provider_catalog.py -q -k "alpha_vantage or stooq or yahoo or deribit or coingecko"` | 同上全绿 + `execute-evidence/9.6-manifest.md`                                                                                                                       | `execute-evidence/9.6-{red,green}.txt` + `9.6-manifest.md` |
| 9.7  | layer_smoke                   | `uv run pytest tests/test_market_data_adapters.py tests/test_crypto_market_adapters.py -q -k layer`                                                                                 | 同上全绿                                                                                                                                                            | `execute-evidence/9.7-{red,green}.txt`                     |
| 9.8  | merge_gate                    | 子集若有红                                                                                                                                                                          | `uv run pytest -q` + `uv run python scripts/loop_maintain.py` + `tests/test_r3h_source_final_decisions.py` + `tests/test_round3g_limited_production_clean_write.py` | `execute-evidence/9.8-{red,green,full}.txt`                |

每步 GREEN 后：`uv run pytest -q`（全库）→ 0。

## 2. AC ↔ 测试 / 验收

| AC               | 测试 / 命令                              | 通过条件                                |
| ---------------- | ---------------------------------------- | --------------------------------------- |
| AC-EVIDENCE      | `-k evidence_contract`                   | market_data_evidence_v1 端到端          |
| AC-ALPHA         | `-k alpha_vantage` + route               | READY + 未授权 DISABLED                 |
| AC-STOOQ         | `-k stooq`                               | validation READY；非 silent primary     |
| AC-YAHOO         | `-k yahoo`                               | validation-only；3G fixture 已迁 replay |
| AC-CRYPTO        | `test_crypto_market_adapters`            | deribit/coingecko 终态 + caps           |
| AC-NO-SILENT-PRI | `-k stooq` + `test_advR3xRoute001`       | validation 源不得 silent primary        |
| AC-CAPS          | `-k alpha_vantage` + resource tests      | option-chain/衍生品 cap 硬拒绝          |
| AC-REGISTRY      | route + capabilities + `9.6-manifest.md` | 五源 manifest 与 registry 一致          |
| AC-LAYER         | `-k layer`                               | L2/L4/L5 smoke                          |
| AC-MERGE         | 全库 pytest + loop_maintain              | exit 0                                  |

### 2.1 Tier

| 层  | 命令                                                                                       | 环境          |
| --- | ------------------------------------------------------------------------------------------ | ------------- |
| A   | `uv run pytest tests/test_market_data_adapters.py tests/test_crypto_market_adapters.py -q` | local/ci      |
| A+  | `uv run pytest -q`                                                                         | local/ci      |
| B   | `ALPHA_VANTAGE_API_KEY` 下 optional live smoke（用户显式）                                 | audit-sandbox |
| D   | **禁止** 写 `data/duckdb/quant_monitor.duckdb`                                             | —             |

## 3. 必须读原文（manifest）

| path                                                                                                                                | manifest   | audience | extract             | for      |
| ----------------------------------------------------------------------------------------------------------------------------------- | ---------- | -------- | ------------------- | -------- |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`                                                                               | must-read  | execute  | scope boundaries    | 9.0      |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`                                                                                | must-read  | execute  | TDD 五字段          | 9.0      |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`                                                                               | must-read  | execute  | ResourceGuard       | 9.2–9.5  |
| `docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md`                                                                                 | must-read  | execute  | §9 结构             | 9.0      |
| `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_MASS_REHEARSAL_OPEN_GAPS.md`                | must-read  | both     | G2/G13/G16          | 9.4      |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`                                                                                                 | must-read  | both     | §5.0 R3H-02         | 9.0      |
| `specs/contracts/reference_adoption_guardrails.yaml`                                                                                | must-read  | both     | L1/L2               | 9.2      |
| `specs/contracts/layer5_evidence_contract.yaml`                                                                                     | must-read  | both     | Layer5 smoke        | 9.7      |
| `specs/contracts/data_quality_rules.yaml`                                                                                           | must-read  | execute  | DQ OHLCV            | 9.1      |
| `specs/contracts/source_capability_contract.yaml`                                                                                   | must-read  | execute  | port 契约           | 9.2      |
| `specs/contracts/source_route_contract.yaml`                                                                                        | must-read  | both     | route               | 9.6      |
| `specs/contracts/datasource_service_contract.yaml`                                                                                  | must-read  | execute  | DSS                 | 9.2      |
| `specs/contracts/resource_limits.yaml`                                                                                              | must-read  | execute  | caps                | 9.2      |
| `specs/datasource_registry/source_registry.yaml`                                                                                    | must-read  | both     | 五源                | 9.6      |
| `specs/datasource_registry/source_capabilities.yaml`                                                                                | must-read  | both     | market fields       | 9.1      |
| `specs/verification/contract_coverage.yaml`                                                                                         | must-read  | execute  | 覆盖                | 9.6      |
| `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_HARDENING_RULES.md`      | must-read  | both     | closure             | 9.0      |
| `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_COORDINATOR_PLAYBOOK.md` | must-read  | both     | registry 合并       | 9.6      |
| `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_TASK_CARD_MANIFEST.md`   | must-read  | both     | 并行规则            | 9.0      |
| `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/README.md`                        | must-read  | both     | batch closure       | 9.0      |
| `docs/modules/data_sources.md`                                                                                                      | must-read  | execute  | 多源冲突/角色       | 9.3–9.4  |
| `docs/modules/source_route_plan.md`                                                                                                 | must-read  | execute  | route 设计          | 9.6      |
| `docs/quality/staged_acceptance_policy.md`                                                                                          | must-read  | execute  | RED/GREEN 证据      | 9.0      |
| `backend/app/datasources/adapters/fetch_port.py`                                                                                    | must-read  | execute  | FetchPort 契约      | 9.2      |
| `backend/app/datasources/normalizers/evidence_bundle.py`                                                                            | must-read  | execute  | finalize_bundle     | 9.1      |
| `backend/app/datasources/service.py`                                                                                                | must-read  | execute  | DSS.fetch           | 9.2–9.5  |
| `backend/app/datasources/adapters/__init__.py`                                                                                      | must-read  | execute  | yahoo 注册迁移      | 9.4      |
| `backend/app/ops/sandbox_clean_write/limited_production_entry.py`                                                                   | must-read  | execute  | yahoo validation op | 9.4      |
| `backend/app/ops/staged_pilot.py`                                                                                                   | must-read  | execute  | pilot 源列表        | 9.4, 9.8 |
| `backend/app/layer1_axes/ingestion_evidence.py`                                                                                     | must-read  | execute  | layer preview 模式  | 9.7      |
| `backend/app/layer4_markets/market_structure.py`                                                                                    | must-read  | execute  | L4 禁止字段边界     | 9.7      |
| `backend/app/layer5_evidence/foundation.py`                                                                                         | must-read  | execute  | L5 validator        | 9.7      |
| `tests/test_official_macro_adapters.py`                                                                                             | must-read  | execute  | layer_smoke 模板    | 9.7      |
| `tests/test_source_registry.py`                                                                                                     | must-read  | execute  | registry 回归       | 9.6      |
| `tests/test_provider_catalog.py`                                                                                                    | must-read  | execute  | 五源 status         | 9.6      |
| `tests/test_r3h_source_final_decisions.py`                                                                                          | must-read  | execute  | 五源任务卡覆盖      | 9.8      |
| `tests/test_round3g_limited_production_clean_write.py`                                                                              | must-read  | execute  | yahoo bundle 回归   | 9.4, 9.8 |
| `tests/test_catalog.yaml`                                                                                                           | must-read  | execute  | 新模块登记          | 9.8      |
| `backend/app/datasources/adapters/yahoo_finance.py`                                                                                 | must-read  | execute  | 迁移源              | 9.4      |
| `backend/app/datasources/fetch_ports/fred_port.py`                                                                                  | must-read  | execute  | port 模式参照       | 9.2      |
| `backend/app/ops/sandbox_clean_write/rehearsal_loader.py`                                                                           | must-read  | execute  | yahoo bundle        | 9.4      |
| `backend/app/datasources/route_planner.py`                                                                                          | must-read  | execute  | route 测            | 9.6      |
| `backend/app/datasources/capability_registry.py`                                                                                    | must-read  | execute  | caps                | 9.2      |
| `backend/app/core/resource_guard.py`                                                                                                | must-read  | execute  | caps                | 9.2      |
| `tests/fixtures/sandbox_clean_write/r3g01/yahoo_finance/`                                                                           | must-read  | execute  | 3G fixture          | 9.4      |
| `tests/test_source_route_planner.py`                                                                                                | must-read  | execute  | route 回归          | 9.6      |
| `tests/test_source_capabilities.py`                                                                                                 | must-read  | execute  | capability          | 9.6      |
| `tests/test_r3x_residual_open_items_closure.py`                                                                                     | must-read  | execute  | validation block    | 9.4      |
| `tests/test_reference_adoption_guardrails.py`                                                                                       | must-read  | execute  | guardrails          | 9.8      |
| `MIGRATION_MAP.md`                                                                                                                  | must-read  | both     | 边界                | 9.0      |
| `MODULE_COMPLETION_RATING.md`                                                                                                       | audit-only | audit    | 完成度              | A1       |

## 4. 已并入冻结任务卡（不必再读原文 · Execute 禁止读 `research/*` Plan 草稿）

| 来源（Plan-only 草稿）                      | 并入 frozen                    | 摘要                              |
| ------------------------------------------- | ------------------------------ | --------------------------------- |
| `research/plan-boot.md`                     | §2.8、§8、前置 R3H-01/3G       | Batch README + 五源 baseline      |
| `research/brainstorm-session.md`            | §1.1                           | 方案 A–E 否决/采纳                |
| `research/grill-me-session.md`              | §1.1、§1.2、§2.8、§8、§8.1、§9 | Q1–Q14 + ADR 策略                 |
| `research/spec-driven-development-notes.md` | §5.1、§10                      | 契约面 + spec→test + crypto 字段  |
| `research/project-overview.md`              | §4.2                           | 五源基线状态                      |
| `research/gitnexus-summary.md`              | §4.3                           | impact 表；MEDIUM 风险            |
| `research/to-issues-slices.md`              | §9 首段、§0.1                  | S0–S8 与 Step 9.x 对齐            |
| `research/integration-audit.md`             | §10.2                          | 攻击面闭包 + Plan GAP 说明        |
| `research/integration-ledger.md`            | §3 行扩充                      | 内联 vs manifest 分工（无新决策） |
| `research/project-map-omission-check.md`    | §9.0、§12                      | Execute 须新建测试/fixture 清单   |
| `research/original-plan-trace.md`           | §0.1                           | AC↔Step 追溯                      |
| `research/plan-consolidation.md`            | n/a（Plan-only）               | 5e 分流记录；Execute 不读         |
| 活卡 §1 Goal                                | §1                             | 五源闭环                          |
| 活卡 §4.1                                   | §4.1                           | 数据流/impact                     |
| 活卡 §7 caps                                | §7                             | ResourceGuard 默认                |
| 活卡 §14 reference_project                  | §14                            | OpenBB 借鉴 only                  |

## 5. Audit 追溯集

| 类别                  | 文件                                                                 |
| --------------------- | -------------------------------------------------------------------- |
| 活任务卡              | `R3H_02_MARKET_DATA_ADAPTERS.md`                                     |
| frozen                | `frozen/R3H_02_MARKET_DATA_ADAPTERS.md`                              |
| R3H-01 参照           | `.trellis/tasks/archive/2026-06/06-28-round3h-r3h01-official-macro/` |
| 3G 索引               | `R3G_MASS_REHEARSAL_OPEN_GAPS.md`                                    |
| batch                 | `BATCH_3H_TASK_CARD_MANIFEST.md`                                     |
| Plan 5d（Audit 可读） | `research/integration-audit.md`                                      |
| omission              | `research/project-map-omission-check.md`                             |

## 6. 机器路由

```bash
uv run python scripts/context_router.py --task .trellis/tasks/06-28-06-28-round3h-r3h02-market-data
```

**Execute 三件套（唯一正文 SSOT）：**

1. `frozen/R3H_02_MARKET_DATA_ADAPTERS.md`
2. `EXECUTION_INDEX.md`（§1 命令/§2 AC/§3 必读 manifest）
3. `implement.jsonl`（机器清单；**不含** `research/*`）

Execute Boot：`frozen` → 本文 → `context_pack.json` → `trellis-execute/SKILL.md` → `implement.jsonl` 每条 → §3 `must-read`。

Handoff：`python .trellis/scripts/task.py validate-execute-handoff .trellis/tasks/06-28-06-28-round3h-r3h02-market-data`
