# 执行索引 — R3H-01 Official Macro Disclosure Adapters

> P0i：**索引完整**（v4 · Plan 2026-06-28）

## 0. 冻结元数据

| 字段         | 值                                                                                                                                              |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| slug         | `06-28-round3h-r3h01-official-macro`                                                                                                            |
| source_card  | `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_01_OFFICIAL_MACRO_DISCLOSURE_ADAPTERS.md` |
| frozen_card  | `frozen/R3H_01_OFFICIAL_MACRO_DISCLOSURE_ADAPTERS.md`                                                                                           |
| frozen_at    | _pending freeze-task-card_                                                                                                                      |
| batch / item | Batch 3H / `R3H-01`                                                                                                                             |
| batch map    | `PROJECT_IMPLEMENTATION_ROADMAP.md` §5                                                                                                          |
| branch       | `feature/round3h-r3h01-official-macro`（建议）                                                                                                  |
| user_gate    | 见 frozen §2.8：禁止主库；FRED live 须 R3E 授权                                                                                                 |

### 0.1 血缘

| 任务卡 AC          | Step | 验证链 |
| ------------------ | ---- | ------ |
| AC-G10 证据合一    | 9.1  | §2     |
| AC-FRED port/route | 9.2  | §2     |
| AC-US-TREASURY     | 9.3  | §2     |
| AC-SEC             | 9.4  | §2     |
| AC-CFTC-BIS-WB     | 9.5  | §2     |
| AC-REGISTRY 六源   | 9.6  | §2     |
| AC-LAYER smoke     | 9.7  | §2     |
| AC-MERGE           | 9.8  | §2.1   |

**切片依赖（to-issues S0–S8）：** 9.1→阻塞 9.2/9.7；9.3–9.5 可并行（9.1 后）；9.6 须 9.2–9.5 + coordinator；9.8 最后。

## 1. 步骤与证据（Execute）

| Step | 锚点                   | RED 命令                                                                                                                                                | GREEN 命令                                                    | 证据路径                                    |
| ---- | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------- |
| 9.0  | boot_test_skeleton     | `uv run pytest tests/test_official_macro_adapters.py -q`（ModuleNotFound）                                                                              | 同上空壳绿                                                    | `execute-evidence/9.0-{red,green}.txt`      |
| 9.1  | fred_evidence_contract | `uv run pytest tests/test_official_macro_adapters.py -q -k evidence_contract`                                                                           | 同上全绿                                                      | `execute-evidence/9.1-{red,green}.txt`      |
| 9.2  | fred_fetch_port        | `uv run pytest tests/test_official_macro_adapters.py -q -k fred_port`                                                                                   | 同上全绿                                                      | `execute-evidence/9.2-{red,green}.txt`      |
| 9.3  | us_treasury_port       | `uv run pytest tests/test_official_macro_adapters.py -q -k us_treasury`                                                                                 | 同上全绿                                                      | `execute-evidence/9.3-{red,green}.txt`      |
| 9.4  | sec_edgar_port         | `uv run pytest tests/test_sec_edgar_adapter.py -q`                                                                                                      | 同上全绿                                                      | `execute-evidence/9.4-{red,green}.txt`      |
| 9.5  | cftc_bis_wb            | `uv run pytest tests/test_official_macro_adapters.py -q -k "cftc or bis or world_bank"`                                                                 | 同上全绿                                                      | `execute-evidence/9.5-{red,green}.txt`      |
| 9.6  | registry_coordinator   | `uv run pytest tests/test_source_route_planner.py tests/test_source_capabilities.py -q -k "fred or treasury or sec_edgar or cftc or bis or world_bank"` | 同上全绿                                                      | `execute-evidence/9.6-{red,green}.txt`      |
| 9.7  | layer_smoke            | `uv run pytest tests/test_official_macro_adapters.py -q -k layer`                                                                                       | 同上全绿                                                      | `execute-evidence/9.7-{red,green}.txt`      |
| 9.8  | merge_gate             | 子集若有红                                                                                                                                              | `uv run pytest -q` + `uv run python scripts/loop_maintain.py` | `execute-evidence/9.8-{red,green,full}.txt` |

每步 GREEN 后：`uv run pytest -q`（全库）→ 0。

## 2. AC ↔ 测试 / 验收

| AC             | 测试 / 命令                      | 通过条件                                     |
| -------------- | -------------------------------- | -------------------------------------------- |
| AC-G10         | `-k evidence_contract`           | 无 bridge sidecar；`observation_date` 端到端 |
| AC-FRED        | `-k fred_port` + route           | READY + 未授权 DISABLED                      |
| AC-US-TREASURY | `-k us_treasury`                 | READY 或 ADR 文件存在                        |
| AC-SEC         | `test_sec_edgar_adapter.py`      | identity + replay                            |
| AC-CFTC-BIS-WB | `-k "cftc or bis or world_bank"` | 各源终态                                     |
| AC-REGISTRY    | route + capabilities             | manifest 与 registry 一致                    |
| AC-LAYER       | `-k layer`                       | Layer1/L5 smoke                              |
| AC-MERGE       | 全库 pytest + loop_maintain      | exit 0                                       |

### 2.1 Tier

| 层  | 命令                                                                                     | 环境          |
| --- | ---------------------------------------------------------------------------------------- | ------------- |
| A   | `uv run pytest tests/test_official_macro_adapters.py tests/test_sec_edgar_adapter.py -q` | local/ci      |
| A+  | `uv run pytest -q`                                                                       | local/ci      |
| B   | `FRED_API_KEY` + R3E authorization 下 optional live smoke（用户显式）                    | audit-sandbox |
| D   | **禁止** 写 `data/duckdb/quant_monitor.duckdb`                                           | —             |

## 3. 必须读原文（manifest）

| path                                                                                                                                | manifest   | audience | extract          | for     |
| ----------------------------------------------------------------------------------------------------------------------------------- | ---------- | -------- | ---------------- | ------- |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`                                                                               | must-read  | execute  | scope boundaries | 9.0     |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`                                                                                | must-read  | execute  | TDD 五字段       | 9.0     |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`                                                                               | must-read  | execute  | ResourceGuard    | 9.2–9.5 |
| `docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md`                                                                                 | must-read  | execute  | §9 结构          | 9.0     |
| `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_MASS_REHEARSAL_OPEN_GAPS.md`                | must-read  | both     | G10/G14          | 9.1     |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`                                                                                                 | must-read  | both     | §5.0 3G→3H       | 9.1     |
| `specs/contracts/reference_adoption_guardrails.yaml`                                                                                | must-read  | both     | L1/L2            | 9.2     |
| `specs/contracts/layer5_evidence_contract.yaml`                                                                                     | must-read  | both     | Layer5 smoke     | 9.7     |
| `specs/contracts/data_quality_rules.yaml`                                                                                           | must-read  | execute  | DQ               | 9.1     |
| `specs/contracts/source_capability_contract.yaml`                                                                                   | must-read  | execute  | port 契约        | 9.2     |
| `specs/contracts/source_route_contract.yaml`                                                                                        | must-read  | both     | route            | 9.6     |
| `specs/contracts/datasource_service_contract.yaml`                                                                                  | must-read  | execute  | DSS              | 9.2     |
| `specs/datasource_registry/source_registry.yaml`                                                                                    | must-read  | both     | 六源             | 9.6     |
| `specs/datasource_registry/source_capabilities.yaml`                                                                                | must-read  | both     | fred fields      | 9.1     |
| `specs/verification/contract_coverage.yaml`                                                                                         | must-read  | execute  | 覆盖             | 9.6     |
| `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_HARDENING_RULES.md`      | must-read  | both     | closure          | 9.0     |
| `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_COORDINATOR_PLAYBOOK.md` | must-read  | both     | registry 合并    | 9.6     |
| `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_TASK_CARD_MANIFEST.md`   | must-read  | both     | 并行规则         | 9.0     |
| `backend/app/ops/sandbox_clean_write/rehearsal_loader.py`                                                                           | must-read  | execute  | promote 读证据   | 9.1     |
| `backend/app/ops/sandbox_clean_write/live_evidence_bridge.py`                                                                       | must-read  | execute  | 待瘦身           | 9.1     |
| `backend/app/ops/fred_fetch_ports.py`                                                                                               | must-read  | execute  | 迁移源           | 9.2     |
| `backend/app/ops/fred_sandbox_pilot.py`                                                                                             | must-read  | execute  | R3E 授权         | 9.2     |
| `backend/app/ops/live_pilot_phase3.py`                                                                                              | must-read  | execute  | live 证据产出    | 9.1     |
| `backend/app/datasources/route_planner.py`                                                                                          | must-read  | execute  | route 测         | 9.6     |
| `backend/app/datasources/capability_registry.py`                                                                                    | must-read  | execute  | caps             | 9.2     |
| `backend/app/core/resource_guard.py`                                                                                                | must-read  | execute  | caps             | 9.2     |
| `backend/app/layer1_axes/ingestion_evidence.py`                                                                                     | must-read  | execute  | Layer smoke      | 9.7     |
| `tests/fixtures/sandbox_clean_write/r3g01/fred/`                                                                                    | must-read  | execute  | 既有 fixture     | 9.1     |
| `tests/test_source_route_planner.py`                                                                                                | must-read  | execute  | route 回归       | 9.6     |
| `tests/test_source_capabilities.py`                                                                                                 | must-read  | execute  | capability       | 9.6     |
| `tests/test_reference_adoption_guardrails.py`                                                                                       | must-read  | execute  | guardrails       | 9.8     |
| `tests/test_round3g_limited_production_clean_write.py`                                                                              | must-read  | execute  | bridge 回归      | 9.1     |
| `MIGRATION_MAP.md`                                                                                                                  | must-read  | both     | 边界             | 9.0     |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`                                                                                                 | audit-only | audit    | §5.0             | A1      |
| `MODULE_COMPLETION_RATING.md`                                                                                                       | audit-only | audit    | 完成度           | A1      |

## 4. 已并入冻结任务卡（不必再读原文 · Execute 禁止读 `research/*` Plan 草稿）

> **v4 规则：** 下列 Plan 草稿结论已内联进 `frozen/*.md`；**不得**列入 `implement.jsonl` §3。Execute 只读三件套 + §3 manifest + `trellis-execute`。

| 来源（Plan-only 草稿）                      | 并入 frozen              | 摘要                                  |
| ------------------------------------------- | ------------------------ | ------------------------------------- |
| `research/plan-boot.md`                     | §2.8、§8                 | 边界/3G 输入/禁止主库                 |
| `research/brainstorm-session.md`            | §1.1                     | 方案 A–D 否决/采纳；风险表            |
| `research/grill-me-session.md`              | §1.1、§2.8、§8、§8.1、§9 | Q1–Q14 锁定决策                       |
| `research/spec-driven-development-notes.md` | §5.1、§10                | 契约面 + spec→test 映射               |
| `research/project-overview.md`              | §4.2                     | fred 基线状态；3H 目标流              |
| `research/gitnexus-summary.md`              | §4.3                     | impact 锚定；MEDIUM 风险；analyze CLI |
| `research/to-issues-slices.md`              | §9 首段、§0.1            | S0–S8 与 Step 9.x 对齐；并行依赖      |
| `research/integration-audit.md`             | §10.1                    | PASS_WITH_GAPS；对抗焦点              |
| `research/integration-ledger.md`            | §3 规则                  | 内联 vs manifest 分工                 |
| `research/original-plan-trace.md`           | §0.1                     | AC↔Step 追溯                          |
| 活卡 §1 Goal                                | §1                       | 六源闭环                              |
| 活卡 §4.1                                   | §4.1                     | 数据流/impact                         |
| 活卡 §7 caps                                | §7                       | ResourceGuard 默认                    |
| 活卡 §14 reference_project                  | §14                      | OpenBB 借鉴 only                      |

## 5. Audit 追溯集

| 类别                  | 文件                                                  |
| --------------------- | ----------------------------------------------------- |
| 活任务卡              | `R3H_01_OFFICIAL_MACRO_DISCLOSURE_ADAPTERS.md`        |
| frozen                | `frozen/R3H_01_OFFICIAL_MACRO_DISCLOSURE_ADAPTERS.md` |
| 3G 索引               | `R3G_MASS_REHEARSAL_OPEN_GAPS.md`                     |
| batch                 | `BATCH_3H_TASK_CARD_MANIFEST.md`                      |
| Plan 5d（Audit 可读） | `research/integration-audit.md`                       |
| omission              | `research/project-map-omission-check.md`              |

> Plan 草稿 `research/brainstorm-session.md` 等 **不在** Audit 追溯集；结论已在 frozen §1.1 / §5.1。

## 6. 机器路由

```bash
uv run python scripts/context_router.py --task .trellis/tasks/06-28-round3h-r3h01-official-macro
```

**Execute 三件套（唯一正文 SSOT）：**

1. `frozen/R3H_01_OFFICIAL_MACRO_DISCLOSURE_ADAPTERS.md`
2. `EXECUTION_INDEX.md`（§1 命令/§2 AC/§3 必读 manifest）
3. `implement.jsonl`（机器清单；**不含** `research/*`）

Execute Boot：`frozen` → 本文 → `context_pack.json` → `trellis-execute/SKILL.md` → `implement.jsonl` 每条 → §3 `must-read`。

Handoff：`python .trellis/scripts/task.py validate-execute-handoff .trellis/tasks/06-28-round3h-r3h01-official-macro`
