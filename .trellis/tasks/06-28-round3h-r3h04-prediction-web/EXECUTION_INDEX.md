# 执行索引 — R3H-04 Prediction and Web Evidence Adapters

> P0i：**索引完整**（v4 · Plan 2026-06-28）

## 0. 冻结元数据

| 字段         | 值                                                                                                                                  |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| slug         | `06-28-round3h-r3h04-prediction-web`                                                                                                |
| source_card  | `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_04_PREDICTION_AND_WEB_EVIDENCE_ADAPTERS.md` |
| frozen_card  | `frozen/R3H_04_PREDICTION_AND_WEB_EVIDENCE_ADAPTERS.md`                                                                             |
| frozen_at    | （`freeze-task-card` 后填写）                                                                                                       |
| batch / item | Batch 3H / `R3H-04`                                                                                                                 |
| batch map    | `PROJECT_IMPLEMENTATION_ROADMAP.md` §5.0                                                                                            |
| branch       | `feature/round3h-r3h04-prediction-web`                                                                                              |
| parallel     | R3H-03（CN market）；禁止交叉改对方 source                                                                                          |
| user_gate    | 见 frozen **§2.8** Plan vs Execute gates：禁止主库；mock-first READY；web_search 默认 mock stub；禁止改 R3H-03 CN 源 |

### 0.1 血缘

| 任务卡 AC            | Step | 验证链 |
| -------------------- | ---- | ------ |
| AC-PROB-NORM 契约    | 9.1  | §2     |
| AC-KALSHI            | 9.2  | §2     |
| AC-POLY              | 9.3  | §2     |
| AC-WEB               | 9.4  | §2     |
| AC-REGISTRY 三源     | 9.5  | §2     |
| AC-NO-CLEAN/RESOLVE  | 9.6  | §2     |
| AC-L5                | 9.7  | §2     |
| AC-MERGE             | 9.8  | §2.1   |

**切片依赖（S0–S8）：** 9.1→阻塞 9.2–9.4/9.7；9.2–9.4 可并行（9.1 后）；9.5 须 9.2–9.4 + coordinator；9.6 须 9.5；9.7 须 9.4；9.8 最后。

## 1. 步骤与证据（Execute）

| Step | 锚点                          | RED 命令                                                                                                                                                         | GREEN 命令                                                                                                                                                       | 证据路径                                                   |
| ---- | ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| 9.0  | boot_test_skeleton            | `uv run pytest tests/test_prediction_market_adapters.py tests/test_web_evidence_adapter.py tests/test_no_clean_write_for_web_evidence.py -q`（ModuleNotFound） | 同上空壳绿                                                                                                                                                       | `execute-evidence/9.0-{red,green}.txt`                     |
| 9.1  | probability_evidence_contract | `uv run pytest tests/test_prediction_market_adapters.py -q -k evidence_contract`                                                                                 | 同上全绿                                                                                                                                                         | `execute-evidence/9.1-{red,green}.txt`                     |
| 9.2  | kalshi_port                   | `uv run pytest tests/test_prediction_market_adapters.py -q -k kalshi`                                                                                            | 同上全绿                                                                                                                                                         | `execute-evidence/9.2-{red,green}.txt`                     |
| 9.3  | polymarket_port               | `uv run pytest tests/test_prediction_market_adapters.py -q -k polymarket`                                                                                        | 同上全绿                                                                                                                                                         | `execute-evidence/9.3-{red,green}.txt`                     |
| 9.4  | web_search_evidence           | `uv run pytest tests/test_web_evidence_adapter.py -q`                                                                                                            | 同上全绿                                                                                                                                                         | `execute-evidence/9.4-{red,green}.txt`                     |
| 9.5  | registry_coordinator          | `uv run pytest tests/test_source_route_planner.py tests/test_source_capabilities.py tests/test_provider_catalog.py -q -k "kalshi or polymarket or web_search"`   | 同上全绿 + `execute-evidence/9.5-manifest.md`                                                                                                                    | `execute-evidence/9.5-{red,green}.txt` + `9.5-manifest.md` |
| 9.6  | clean_write_negative          | `uv run pytest tests/test_no_clean_write_for_web_evidence.py -q`                                                                                                 | 同上全绿                                                                                                                                                         | `execute-evidence/9.6-{red,green}.txt`                     |
| 9.7  | layer5_smoke                  | `uv run pytest tests/test_prediction_market_adapters.py tests/test_web_evidence_adapter.py -q -k layer`                                                          | 同上全绿                                                                                                                                                         | `execute-evidence/9.7-{red,green}.txt`                     |
| 9.8  | merge_gate                    | 子集若有红                                                                                                                                                       | `uv run pytest -q` + `uv run python scripts/loop_maintain.py` + `tests/test_r3h_source_final_decisions.py`                                                       | `execute-evidence/9.8-{red,green,full}.txt`                |

每步 GREEN 后：`uv run pytest -q`（全库）→ 0。

## 2. AC ↔ 测试 / 验收

| AC              | 测试 / 命令                              | 通过条件                                      |
| --------------- | ---------------------------------------- | --------------------------------------------- |
| AC-PROB-NORM    | `-k evidence_contract`                   | probability_signal_evidence_v1 字段 + 哈希    |
| AC-KALSHI       | `-k kalshi` + route                      | READY + replay；无 factual resolution         |
| AC-POLY         | `-k polymarket`                          | liquidity/volume/spread；resolution_source 非事实 |
| AC-WEB          | `test_web_evidence_adapter`              | manual_review staging + need_human_review     |
| AC-NO-CLEAN     | `test_no_clean_write_for_web_evidence`   | 三源不得选 clean writer                       |
| AC-NO-RESOLVE   | 同上 `-k resolve`                        | 预测市场不得 resolve 事件结果                 |
| AC-REGISTRY     | route + capabilities + `9.5-manifest.md` | 三源 READY 或 ADR                             |
| AC-L5           | `-k layer`                               | L5 foundation manual_review 校验              |
| AC-MERGE        | 全库 pytest + loop_maintain              | exit 0                                        |

### 2.1 Tier

| 层  | 命令                                                                                       | 环境          |
| --- | ------------------------------------------------------------------------------------------ | ------------- |
| A   | `uv run pytest tests/test_prediction_market_adapters.py tests/test_web_evidence_adapter.py tests/test_no_clean_write_for_web_evidence.py -q` | local/ci      |
| A+  | `uv run pytest -q`                                                                         | local/ci      |
| B   | 可选 kalshi/polymarket live smoke（用户显式 + API key）                                    | audit-sandbox |
| D   | **禁止** 写 `data/duckdb/quant_monitor.duckdb`                                             | —             |

## 3. 必须读原文（manifest）

| path                                                                                                                                | manifest   | audience | extract                  | for      |
| ----------------------------------------------------------------------------------------------------------------------------------- | ---------- | -------- | ------------------------ | -------- |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`                                                                               | must-read  | execute  | scope boundaries         | 9.0      |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`                                                                                | must-read  | execute  | TDD 五字段               | 9.0      |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`                                                                               | must-read  | execute  | caps 语义                | 9.2–9.4  |
| `docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md`                                                                                 | must-read  | execute  | §9 结构                  | 9.0      |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`                                                                                                 | must-read  | both     | §5.0 R3H-04              | 9.0      |
| `specs/contracts/layer5_evidence_contract.yaml`                                                                                     | must-read  | both     | manual_review            | 9.7      |
| `specs/contracts/user_input_privacy_contract.yaml`                                                                                  | must-read  | both     | web evidence 隐私        | 9.4, 9.6 |
| `specs/contracts/source_capability_contract.yaml`                                                                                   | must-read  | execute  | port 契约                | 9.2      |
| `specs/contracts/source_route_contract.yaml`                                                                                        | must-read  | both     | evidence-only route      | 9.5, 9.6 |
| `specs/contracts/datasource_service_contract.yaml`                                                                                  | must-read  | execute  | DSS.fetch                | 9.2–9.4  |
| `specs/datasource_registry/source_registry.yaml`                                                                                    | must-read  | both     | 三源行                   | 9.5      |
| `specs/datasource_registry/source_capabilities.yaml`                                                                                | must-read  | both     | probability/web fields   | 9.1      |
| `specs/verification/contract_coverage.yaml`                                                                                         | must-read  | execute  | 覆盖登记                 | 9.5      |
| `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_HARDENING_RULES.md`      | must-read  | both     | §4 源类边界              | 9.0      |
| `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_COORDINATOR_PLAYBOOK.md` | must-read  | both     | registry 合并            | 9.5      |
| `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_TASK_CARD_MANIFEST.md`   | must-read  | both     | 并行规则                 | 9.0      |
| `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/README.md`                        | must-read  | both     | batch closure            | 9.0      |
| `docs/modules/data_sources.md`                                                                                                      | must-read  | execute  | 非事实源角色             | 9.2–9.4  |
| `docs/modules/source_route_plan.md`                                                                                                 | must-read  | execute  | evidence route           | 9.5      |
| `docs/quality/staged_acceptance_policy.md`                                                                                          | must-read  | execute  | RED/GREEN 证据           | 9.0      |
| `backend/app/datasources/adapters/fetch_port.py`                                                                                    | must-read  | execute  | FetchPort 契约           | 9.2      |
| `backend/app/datasources/normalizers/evidence_bundle.py`                                                                            | must-read  | execute  | finalize_bundle          | 9.1      |
| `backend/app/datasources/service.py`                                                                                                | must-read  | execute  | DSS.fetch                | 9.2–9.4  |
| `backend/app/layer5_evidence/foundation.py`                                                                                         | must-read  | execute  | manual_review 校验       | 9.7      |
| `backend/app/datasources/fetch_ports/coingecko_port.py`                                                                             | must-read  | execute  | mock port 模式参照       | 9.2      |
| `backend/app/datasources/route_planner.py`                                                                                          | must-read  | execute  | route 测                 | 9.5      |
| `backend/app/datasources/capability_registry.py`                                                                                    | must-read  | execute  | capability               | 9.5      |
| `tests/test_official_macro_adapters.py`                                                                                             | must-read  | execute  | layer_smoke 模板         | 9.7      |
| `tests/test_source_registry.py`                                                                                                     | must-read  | execute  | registry 回归            | 9.5      |
| `tests/test_provider_catalog.py`                                                                                                    | must-read  | execute  | 三源 status              | 9.5      |
| `tests/test_r3h_source_final_decisions.py`                                                                                          | must-read  | execute  | 三源任务卡覆盖           | 9.8      |
| `tests/test_source_route_planner.py`                                                                                                | must-read  | execute  | route 回归               | 9.5      |
| `tests/test_source_capabilities.py`                                                                                                 | must-read  | execute  | capability               | 9.5      |
| `tests/test_catalog.yaml`                                                                                                           | must-read  | execute  | 新模块登记               | 9.8      |
| `MIGRATION_MAP.md`                                                                                                                  | must-read  | both     | 边界                     | 9.0      |
| `MODULE_COMPLETION_RATING.md`                                                                                                       | audit-only | audit    | 完成度                   | A1       |
| `specs/contracts/reference_adoption_guardrails.yaml`                                                                                | must-read  | both     | L1/L2/L3 + OpenBB 规则   | 9.0      |
| `specs/contracts/data_adapter_contract.md`                                                                                        | must-read  | execute  | 参考采纳 §6–7            | 9.1      |
| `参考项目/agents-for-openbb/30-vanilla-agent-raw-widget-data/vanilla_agent_raw_context/main.py`                                     | must-read  | execute  | widget artifact 形状     | 9.7      |
| `参考项目/agents-for-openbb/40-vanilla-agent-dashboard-widgets/vanilla_agent_dashboard_widgets/main.py`                             | must-read  | execute  | dashboard artifact 形状  | 9.7      |
| `research/reference-adoption-audit.md`                                                                                              | must-read  | execute  | 采纳矩阵 SSOT            | 9.0      |

## 4. 已并入冻结任务卡（不必再读原文 · Execute 禁止读 `research/*` Plan 草稿）

| 来源                                        | 并入 frozen | 摘要                               |
| ------------------------------------------- | ----------- | ---------------------------------- |
| `research/plan-boot.md`                     | §2.8、§8    | Batch + 三源 baseline + gates      |
| `research/brainstorm-session.md`            | §1.1        | 方案 A–G                           |
| `research/grill-me-session.md`              | §1.1、§1.2、§2.8 | Q1–Q12 + mock-first           |
| `research/spec-driven-development-notes.md` | §5.1、§10   | schema + spec→test                 |
| `research/project-overview.md`              | §4.2        | 三源基线                           |
| `research/gitnexus-summary.md`              | §4.3        | impact MEDIUM                      |
| `research/to-issues-slices.md`              | §9 首段     | S0–S8                              |
| `research/integration-audit.md`             | §10.2       | 攻击面闭包                         |
| `research/integration-ledger.md`            | §3 扩充     | 内联 vs manifest                   |
| `research/project-map-omission-check.md`    | §9.0、§12   | 新建文件清单                       |
| `research/original-plan-trace.md`           | §0.1        | AC↔Step                            |
| `research/plan-consolidation.md`            | n/a         | 5e 分流；Execute 不读              |
| 活卡 §7 caps                                | §7          | 端口 cap 表                        |
| 活卡 §8–§15                                 | §8–§15      | 步骤/测试/red flags/skills         |
| 活卡 §3 OpenBB 参考路径                    | §14 + `research/reference-adoption-audit.md` | **本地 `参考项目/agents-for-openbb` 存在**；architecture_only；禁止 agent runtime |
| `research/reference-adoption-audit.md`    | §14 采纳矩阵 | 主会话 2026-06-28 审计 |

## 5. Audit 追溯集

| 类别                  | 文件                                                                 |
| --------------------- | -------------------------------------------------------------------- |
| 活任务卡              | `R3H_04_PREDICTION_AND_WEB_EVIDENCE_ADAPTERS.md`                     |
| frozen                | `frozen/R3H_04_PREDICTION_AND_WEB_EVIDENCE_ADAPTERS.md`              |
| R3H-02 参照           | `.trellis/tasks/archive/2026-06/06-28-06-28-round3h-r3h02-market-data/` |
| batch                 | `BATCH_3H_TASK_CARD_MANIFEST.md`                                     |
| parallel branch       | `_tmp-r3h03-r3h04-parallel/BRANCH-R3H-04.md`                         |
| Plan 5d（Audit 可读） | `research/integration-audit.md`                                      |
| omission              | `research/project-map-omission-check.md`                             |

## 6. 机器路由

```bash
uv run python scripts/context_router.py --task .trellis/tasks/06-28-round3h-r3h04-prediction-web
```

**Execute 三件套（唯一正文 SSOT）：**

1. `frozen/R3H_04_PREDICTION_AND_WEB_EVIDENCE_ADAPTERS.md`
2. `EXECUTION_INDEX.md`（§1 命令/§2 AC/§3 必读 manifest）
3. `implement.jsonl`（机器清单；**不含** `research/*`）

Execute Boot：`frozen` → 本文 → `context_pack.json` → `trellis-execute/SKILL.md` → `implement.jsonl` 每条 → §3 `must-read`。

Handoff：`python .trellis/scripts/task.py validate-execute-handoff .trellis/tasks/06-28-round3h-r3h04-prediction-web`
