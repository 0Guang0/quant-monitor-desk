# 执行索引 — R3H-03 CN Market Adapters

> P0i：**索引完整**（v4 · Plan 2026-06-28）

## 0. 冻结元数据

| 字段         | 值                                                                                                                                        |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| slug         | `06-28-round3h-r3h03-cn-market`                                                                                                         |
| source_card  | `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_03_CN_MARKET_ADAPTERS.md`         |
| frozen_card  | `frozen/R3H_03_CN_MARKET_ADAPTERS.md`                                                                                                     |
| frozen_at    | 2026-06-28T09:30:00Z (audit-repair freeze)                                                                                                |
| batch / item | Batch 3H / `R3H-03`                                                                                                                       |
| batch map    | `PROJECT_IMPLEMENTATION_ROADMAP.md` §5                                                                                                    |
| branch       | `feature/round3h-r3h03-cn-market`                                                                                                         |
| user_gate    | 见 frozen §2.8：禁止主库；QMT/iFinD/xqshare 默认 authorization-disabled；Grill-me Q8/Q12/Q13 未决项 |

### 0.1 血缘

| 任务卡 AC              | Step | 验证链 |
| ---------------------- | ---- | ------ |
| AC-G11 baostock 产品化 | 9.1  | §2     |
| AC-G16 cninfo/akshare  | 9.3  | §2     |
| AC-BAOSTOCK            | 9.2  | §2     |
| AC-CNINFO              | 9.3  | §2     |
| AC-AKSHARE-VAL         | 9.4  | §2     |
| AC-TDX-FAMILY          | 9.5  | §2     |
| AC-EM-SINA             | 9.6  | §2     |
| AC-AUTH-GATED          | 9.7  | §2     |
| AC-REGISTRY-10         | 9.8  | §2     |
| AC-LAYER-CN            | 9.9  | §2     |
| AC-MERGE               | 9.10 | §2.1   |

**切片依赖（to-issues S0–S10）：** 9.1→阻塞 9.2–9.4/9.9；9.5–9.7 可在 9.1 后并行；9.8 须 9.2–9.7 + coordinator；9.10 最后。

## 1. 步骤与证据（Execute）

| Step | 锚点                      | RED 命令                                                                                                                                    | GREEN 命令                                                    | 证据路径                                    |
| ---- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------- |
| 9.0  | boot_test_skeleton        | `uv run pytest tests/test_cn_market_adapters.py -q`（ModuleNotFound）                                                                     | 同上空壳绿                                                    | `execute-evidence/9.0-{red,green}.txt`      |
| 9.1  | cn_market_evidence_contract | `uv run pytest tests/test_cn_market_adapters.py -q -k evidence_contract`                                                                  | 同上全绿                                                      | `execute-evidence/9.1-{red,green}.txt`      |
| 9.2  | baostock_port             | `uv run pytest tests/test_cn_market_adapters.py -q -k baostock`                                                                             | 同上全绿                                                      | `execute-evidence/9.2-{red,green}.txt`      |
| 9.3  | cninfo_port               | `uv run pytest tests/test_cn_market_adapters.py -q -k cninfo`                                                                               | 同上全绿                                                      | `execute-evidence/9.3-{red,green}.txt`      |
| 9.4  | akshare_validation_port   | `uv run pytest tests/test_cn_market_adapters.py -q -k akshare`                                                                              | 同上全绿                                                      | `execute-evidence/9.4-{red,green}.txt`      |
| 9.5  | tdx_family_ports          | `uv run pytest tests/test_cn_market_adapters.py -q -k "tdx or mootdx"`（RED：mootdx_port 缺失）                                            | 同上全绿                                                      | `execute-evidence/9.5-{red,green}.txt`      |
| 9.6  | eastmoney_sina_ports      | `uv run pytest tests/test_cn_market_adapters.py -q -k "eastmoney or sina"`                                                                  | 同上全绿                                                      | `execute-evidence/9.6-{red,green}.txt`      |
| 9.7  | auth_gated_ports          | `uv run pytest tests/test_cn_market_adapters.py -q -k "ifind or qmt or xqshare"`                                                            | 同上全绿                                                      | `execute-evidence/9.7-{red,green}.txt`      |
| 9.8  | registry_coordinator      | `uv run pytest tests/test_source_route_planner.py tests/test_source_capabilities.py -q -k "baostock or cninfo or akshare or tdx or mootdx or eastmoney or sina or ifind or qmt or xqshare"` | 同上全绿                                                      | `execute-evidence/9.8-{red,green}.txt`      |
| 9.9  | layer_cn_smoke            | `uv run pytest tests/test_cn_market_adapters.py -q -k layer_cn`                                                                             | 同上全绿                                                      | `execute-evidence/9.9-{red,green}.txt`      |
| 9.10 | merge_gate                | 子集若有红                                                                                                                                  | `uv run pytest -q` + `uv run python scripts/loop_maintain.py` | `execute-evidence/9.10-{red,green,full}.txt` |

每步 GREEN 后：`uv run pytest -q`（全库）→ 0。

## 2. AC ↔ 测试 / 验收

| AC                 | 测试 / 命令                      | 通过条件                                       |
| ------------------ | -------------------------------- | ---------------------------------------------- |
| AC-G11/G16         | `-k evidence_contract`           | cn_market 证据；staged pilot 形状迁出          |
| AC-BAOSTOCK        | `-k baostock` + route            | Primary READY + replay；未授权不 silent 替换   |
| AC-CNINFO          | `-k cninfo`                      | filings metadata + route                       |
| AC-AKSHARE-VAL     | `-k akshare`                     | validation_only；不可升 primary                |
| AC-TDX-FAMILY      | `-k "tdx or mootdx"`             | 双源独立；无 silent fallback                   |
| AC-EM-SINA         | `-k eastmoney or sina`           | conflict 证据字段                              |
| AC-AUTH-GATED      | `-k "ifind or qmt or xqshare"`   | 默认 DISABLED；授权正例 + 负例（含 xqshare）     |
| AC-REGISTRY-10     | route + capabilities             | 十源 manifest 与 registry 一致                 |
| AC-LAYER-CN        | `-k layer_cn`                    | Layer3/4/5 smoke（非 R3H-05）                  |
| AC-MERGE           | 全库 pytest + loop_maintain      | exit 0                                         |

### 2.1 Tier

| 层  | 命令                                                                                     | 环境          |
| --- | ---------------------------------------------------------------------------------------- | ------------- |
| A   | `uv run pytest tests/test_cn_market_adapters.py -q`      | local/ci      |
| A+  | `uv run pytest -q`                                                                       | local/ci      |
| B   | 用户显式授权下 optional CN live smoke（baostock/cninfo/tdx gate token）                  | audit-sandbox |
| D   | **禁止** 写 `data/duckdb/quant_monitor.duckdb`                                           | —             |

## 3. 必须读原文（manifest）

| path                                                                                                                                | manifest  | audience | extract               | for       |
| ----------------------------------------------------------------------------------------------------------------------------------- | --------- | -------- | --------------------- | --------- |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`                                                                               | must-read | execute  | scope boundaries      | 9.0       |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`                                                                                | must-read | execute  | TDD 五字段            | 9.0       |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`                                                                               | must-read | execute  | ResourceGuard         | 9.1–9.7   |
| `docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md`                                                                                 | must-read | execute  | §9 结构               | 9.0       |
| `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_MASS_REHEARSAL_OPEN_GAPS.md`                | must-read | both     | G11/G16/G2/G17        | 9.1       |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`                                                                                                 | must-read | both     | §5.0 3H→R3H-03        | 9.1       |
| `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_HARDENING_RULES.md`      | must-read | both     | closure               | 9.0       |
| `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_COORDINATOR_PLAYBOOK.md` | must-read | both     | registry 合并         | 9.8       |
| `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_TASK_CARD_MANIFEST.md`   | must-read | both     | 并行规则              | 9.0       |
| `specs/contracts/reference_adoption_guardrails.yaml`                                                                                | must-read | both     | L1/L2/L3              | 9.1       |
| `specs/contracts/layer5_evidence_contract.yaml`                                                                                     | must-read | both     | Layer smoke           | 9.9       |
| `specs/contracts/data_quality_rules.yaml`                                                                                           | must-read | execute  | DQ                    | 9.1       |
| `specs/contracts/source_conflict_rules.yaml`                                                                                        | must-read | execute  | EM/sina vs primary    | 9.6       |
| `specs/contracts/source_capability_contract.yaml`                                                                                   | must-read | execute  | port 契约             | 9.2       |
| `specs/contracts/source_route_contract.yaml`                                                                                        | must-read | both     | route                 | 9.8       |
| `specs/contracts/datasource_service_contract.yaml`                                                                                  | must-read | execute  | DSS                   | 9.2       |
| `specs/datasource_registry/source_registry.yaml`                                                                                    | must-read | both     | 十源 CN 行            | 9.8       |
| `specs/datasource_registry/source_capabilities.yaml`                                                                                | must-read | both     | CN domain fields      | 9.1       |
| `specs/verification/contract_coverage.yaml`                                                                                         | must-read | execute  | 覆盖                  | 9.8       |
| `docs/modules/data_sources.md`                                                                                                      | must-read | execute  | CN source 角色        | 9.2       |
| `docs/modules/source_route_plan.md`                                                                                                 | must-read | both     | primary/validation    | 9.8       |
| `backend/app/ops/staged_pilot_fetch_ports.py`                                                                                       | must-read | execute  | baostock/cninfo 迁移源 | 9.1       |
| `backend/app/datasources/fetch_ports/tdx_pytdx_port.py`                                                                             | must-read | execute  | TDX 基线 port         | 9.5       |
| `backend/app/datasources/normalizers/tdx.py`                                                                                        | must-read | execute  | TDX manifest 形状     | 9.5       |
| `backend/app/datasources/route_planner.py`                                                                                          | must-read | execute  | CN route 测           | 9.8       |
| `backend/app/datasources/capability_registry.py`                                                                                    | must-read | execute  | caps                  | 9.2       |
| `backend/app/core/resource_guard.py`                                                                                                | must-read | execute  | caps                  | 9.2       |
| `backend/app/datasources/adapters/baostock.py`                                                                                      | must-read | execute  | skeleton 迁出         | 9.2       |
| `backend/app/datasources/adapters/cninfo.py`                                                                                        | must-read | execute  | skeleton 迁出         | 9.3       |
| `backend/app/datasources/adapters/akshare.py`                                                                                       | must-read | execute  | validation skeleton   | 9.4       |
| `backend/app/datasources/adapters/qmt_xtdata.py`                                                                                    | must-read | execute  | auth-gated 边界       | 9.7       |
| `backend/app/ops/data_health_profiles/calendar_gap_rules.py`                                                                        | must-read | execute  | G2/G17 交易日历基线   | 9.9       |
| `backend/app/ops/tdx_live_manual_probe_gate.py`                                                                                     | must-read | execute  | TDX 授权 gate 形状    | 9.5       |
| `tests/test_source_route_planner.py`                                                                                                | must-read | execute  | route 回归            | 9.8       |
| `tests/test_source_capabilities.py`                                                                                                 | must-read | execute  | capability            | 9.8       |
| `tests/test_adapter_skeletons.py`                                                                                                   | must-read | execute  | skeleton 迁出回归     | 9.2       |
| `tests/test_staged_pilot.py`                                                                                                        | must-read | execute  | staged 迁出回归       | 9.1       |
| `MIGRATION_MAP.md`                                                                                                                  | must-read | both     | 边界                  | 9.0       |
| `MODULE_COMPLETION_RATING.md`                                                                                                       | audit-only | audit    | 完成度                | A1        |
| `参考项目/EasyXT/easy_xt/realtime_data/providers/tdx_provider.py`                                                                   | must-read  | execute  | TDX L2 对照（R3FR-03 已落地） | 9.5  |
| `参考项目/EasyXT/data_manager/smart_data_detector.py`                                                                               | must-read  | execute  | G2/G17 TradingCalendar L2 | 9.9  |
| `参考项目/EasyXT/data_manager/data_integrity_checker.py`                                                                            | must-read  | execute  | OHLCV 完整性 L2           | 9.9  |
| `specs/contracts/data_adapter_contract.md`                                                                                        | must-read  | execute  | 参考采纳 §6–7             | 9.1  |
| `research/reference-adoption-audit.md`                                                                                              | must-read  | execute  | 采纳矩阵 SSOT             | 9.0  |

## 4. 已并入冻结任务卡（不必再读原文 · Execute 禁止读 `research/*` Plan 草稿）

| 来源（Plan-only 草稿）                      | 并入 frozen              | 摘要                                  |
| ------------------------------------------- | ------------------------ | ------------------------------------- |
| `research/plan-boot.md`                     | §1.1、§2.8、§8           | 边界/3G G11/G16/禁止主库              |
| `research/brainstorm-session.md`            | §1.1                     | 方案 B 采纳；否决 catch-all           |
| `research/grill-me-session.md`              | §1.1、§1.2、§2.8、§8、§8.1、§9 | Q1–Q14 锁定；Q8/Q12/Q13 用户门        |
| `research/spec-driven-development-notes.md` | §5.1、§10                | 契约面 + spec→test 映射               |
| `research/project-overview.md`              | §4.2                     | 十源基线表                            |
| `research/gitnexus-summary.md`              | §4.1、§4.3               | impact 锚定；索引滞后注记             |
| `research/to-issues-slices.md`              | §9 首段、§0.1            | S0–S10 与 Step 9.x 对齐               |
| `research/integration-audit.md`             | §10.2                    | PASS_WITH_GAPS；对抗焦点              |
| `research/integration-ledger.md`            | §3 规则                  | 内联 vs manifest 分工                 |
| `research/original-plan-trace.md`           | §0.1                     | AC↔Step 追溯                          |
| 活卡 §1 Goal                                | §1                       | 十源闭环                              |
| 活卡 §5 per-source                          | §5                       | 角色表                                |
| 活卡 §7 caps                                | §7                       | ResourceGuard 默认                    |
| 活卡 §14 reference                          | §14 + `research/reference-adoption-audit.md` | **本地 `参考项目/` 存在（gitignore）**；Execute 须 Read 活卡三路径定 L1/L2/L3；禁止 runtime import |
| `research/reference-adoption-audit.md`      | §14 采纳矩阵             | 主会话 2026-06-28 审计；纠正 Plan「不读参考树」错误 |

## 5. Audit 追溯集

| 类别                  | 文件                                                  |
| --------------------- | ----------------------------------------------------- |
| 活任务卡              | `R3H_03_CN_MARKET_ADAPTERS.md`                        |
| frozen                | `frozen/R3H_03_CN_MARKET_ADAPTERS.md`                 |
| 3G 索引               | `R3G_MASS_REHEARSAL_OPEN_GAPS.md`                     |
| batch                 | `BATCH_3H_TASK_CARD_MANIFEST.md`                      |
| Plan 5d（Audit 可读） | `research/integration-audit.md`                       |
| omission              | `research/project-map-omission-check.md`              |

## 6. 机器路由

```bash
uv run python scripts/context_router.py --task .trellis/tasks/06-28-round3h-r3h03-cn-market
```

**Execute 三件套（唯一正文 SSOT）：**

1. `frozen/R3H_03_CN_MARKET_ADAPTERS.md`
2. `EXECUTION_INDEX.md`（§1 命令/§2 AC/§3 必读 manifest）
3. `implement.jsonl`（机器清单；**不含** `research/*`）

Execute Boot：`frozen` → 本文 → `context_pack.json` → `trellis-execute/SKILL.md` → `implement.jsonl` 每条 → §3 `must-read`。

Handoff：`python .trellis/scripts/task.py validate-execute-handoff .trellis/tasks/06-28-round3h-r3h03-cn-market`
