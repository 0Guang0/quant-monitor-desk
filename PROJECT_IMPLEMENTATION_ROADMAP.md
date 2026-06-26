# 项目实施路线图（按重构后的批次文件夹执行）

> 本文件是后续执行的总入口。  
> 旧的 Round3 历史计划、散落任务卡和 Trellis 历史证据只作为追溯资料；未来执行以本文件和 `docs/implementation_tasks/**/BATCH_*` 文件夹为准。  
> 当前规则很简单：**一个批次文件夹就是一个执行入口；只有可以分支并行、不会互相改同一核心文件而冲突的任务，才作为同批次并行 track。必须前后依赖的任务，只能写成 gate 顺序，不能假装成并行批次。**

---

## 0. 一句话说明当前状态

项目已经完成了前期建模、数据治理、source registry、capability registry、route plan、data health、WriteManager、DbValidationGate 等基础能力，但这些能力大多仍处于 **staged / sandbox / fixture / proposed-disabled** 状态。

也就是说：

- 可以继续做 read-only 检查、沙盒演练、API 展示、source readiness 展示。
- 不能默认生产写入。
- 不能默认 live production 抓取。
- 不能因为 registry 里新增了数据源，就认为 adapter 已实现或数据源已可生产启用。
- 不能把 `参考项目/**` 的源码直接当成本项目 runtime。
- 参考采纳规则以 `specs/contracts/reference_adoption_guardrails.yaml` 为 SSOT；`license_gate` 要求各采纳任务卡含 `reference_project:` 块（R3FR-01 已机读验收）。

后续的主线不再重开旧 Round3，而是按下面这些 canonical 批次文件夹继续：

```text
docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/
docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/
docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/
docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/
docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/
```

---

## 1. 全局执行规则

### 1.1 先读哪些文件

每个执行者开始前必须先读：

```text
PROJECT_IMPLEMENTATION_ROADMAP.md
MODULE_COMPLETION_RATING.md
docs/implementation_tasks/PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md  # 覆盖地图，不是工单；执行仍以具体任务卡为准
docs/quality/待修复清单.md
docs/implementation_tasks/README.md
docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md
docs/implementation_tasks/GLOBAL_TESTING_POLICY.md
docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md
docs/modules/data_sources.md
docs/modules/source_route_plan.md
specs/datasource_registry/source_registry.yaml
specs/datasource_registry/source_capabilities.yaml
specs/contracts/source_capability_contract.yaml
specs/contracts/source_route_contract.yaml
specs/contracts/datasource_service_contract.yaml
specs/verification/contract_coverage.yaml
tests/test_catalog.yaml
```

涉及某个批次时，还必须读该批次文件夹里的：

```text
README.md
BATCH_*_TASK_CARD_MANIFEST.md
BATCH_*_HARDENING_RULES.md
BATCH_*_COORDINATOR_PLAYBOOK.md
```

### 1.2 批次怎么理解

本项目以后按下面的规则理解“批次”：

1. **批次文件夹是唯一执行入口。** 例如 Batch04 就只认 `BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/`。
2. **旧 loose card 只是历史输入。** 例如 Round4 的 `024_*.md` 到 `030_*.md` 不能直接派工，必须走 `B04_*` canonical card。
3. **能并行才放同一批次。** 如果两个任务会改同一核心模块、互相依赖结果、或者一个必须等另一个审计通过，就不能当成并行任务。
4. **同批次内也可以有 gate 顺序。** 有些批次文件夹是“串行 gate 包”，例如 3G；里面的任务必须按顺序走，不能并行开多个生产写入相关分支。
5. **每个小任务必须有一张任务卡。** 任务卡必须写清楚目的、范围、边界、要改哪些文件、参考项目怎么借鉴、哪些源码不能复制、测试怎么跑。

### 1.3 禁止事项

任何后续批次都禁止：

- 默认启用 production-live。
- 默认启用 production clean write。
- 默认全市场、全历史、分钟级全量扫描。
- 把 staged / fixture / sandbox 证据说成 production-ready。
- 把 validation-only 源提升成 Primary。
- 绕过 `DataSourceService`、`SourceRoutePlan`、`ResourceGuard`、`WriteManager`、`DbValidationGate`。
- 让 Agent 文本变成事实源。
- 让 `web_search`、Polymarket、Kalshi 等概率/网页源直接写 clean 表。
- 直接 import 或复制 `参考项目/**` 到 backend runtime。

### 1.4 参考项目使用规则

参考项目路径：

```text
C:\Users\Guang\Desktop\quant-monitor-desk\参考项目
```

参考项目只能作为架构和实现思路来源，不能绕过本项目契约。

| 参考项目          | 可以借鉴                                                        | 必须禁止                                                      |
| ----------------- | --------------------------------------------------------------- | ------------------------------------------------------------- |
| EasyXT            | data health 检查、交易日缺失、OHLCV 规则、TDX provider 生命周期 | 自动登录、账户控制、交易、全市场默认下载、硬编码 DB/table     |
| JQ2PTrade         | read-only loader、report shape、backtest/review deny-list       | order API、portfolio execution、scheduler hooks、任意策略执行 |
| OpenBB            | provider catalog 架构、provider metadata、optional extras       | 复制 AGPL runtime source、复制 provider fetcher class         |
| agents-for-openbb | Agent/UI artifact 形态、dashboard/widget 思路                   | 把外部 Agent 逻辑当事实源、触发写入、绕过 QMD evidence        |

---

## 2. 当前数据源扩展后的新口径

本轮已经把多个参考项目中用到的数据源写入本项目 registry/capability/design/contract。必须记住：**新增 source 是 proposed / disabled-by-default，不是 adapter 已完成。**

新增源包括：

```text
us_treasury
sec_edgar
cftc_cot
bis
world_bank
deribit
coingecko
kalshi
polymarket
stooq
alpha_vantage
mootdx
eastmoney
sina_finance
ths_ifind
web_search
```

这些源当前统一规则：

- `enabled_by_default=false`
- 进入 route plan 时必须先是 `DISABLED_SOURCE`
- 没有 adapter、license/auth、ResourceGuard、route-plan test、replay evidence 前不能启用
- 不能因为它们在 registry 中出现，就让调度器真的抓取
- `source_type` 和 `license_type` 必须兼容 `specs/schema/schema.sql` 与 migration 009 的 CHECK 枚举

### 2.1 新增源怎么定位

| 数据源          | 当前定位                        | 简单解释                                                   |
| --------------- | ------------------------------- | ---------------------------------------------------------- |
| `us_treasury`   | 官方宏观 Primary 候选           | 美国国债收益率、利率曲线；可靠但不是实时交易信号           |
| `sec_edgar`     | 官方披露 Primary 候选           | 美国公司公告、Form 4；需要保存 accession/content_hash      |
| `cftc_cot`      | 官方周频 Primary 候选           | CFTC 持仓；可靠但滞后，不能当实时仓位                      |
| `bis`           | 官方/准官方宏观 Primary 候选    | 政策利率、credit gap；低频背景变量                         |
| `world_bank`    | 官方低频 Primary 候选           | GDP、人口、贸易；长期背景，不做短线触发                    |
| `deribit`       | 加密衍生品 Primary 候选         | 期货曲线、期权 IV；只能 market-data，不碰账户交易          |
| `coingecko`     | 加密参考/Validation             | 聚合价格和币种映射；不能替代交易所逐笔事实源               |
| `kalshi`        | 监管预测市场概率源              | 输出 probability signal，不解析事实结果                    |
| `polymarket`    | 预测市场 Validation             | 补充事件概率；必须记录流动性和 resolution source           |
| `stooq`         | 全球日频行情 Validation         | 低频历史验证，不做实时主源                                 |
| `alpha_vantage` | API-key gated Primary candidate | 美股、ETF、期权链、FX、商品、宏观；需 key 与限流           |
| `mootdx`        | A 股 TDX-compatible Validation  | 默认禁用，不 silent fallback                               |
| `eastmoney`     | A 股补充 Validation             | 板块、资金流、公告备份；口径必须分源保存                   |
| `sina_finance`  | A 股轻量 Validation/Fallback    | 只做校验/诊断，不直接接管主值                              |
| `ths_ifind`     | 授权后 Validation               | 概念、研报、资金流；必须确认商业授权                       |
| `web_search`    | evidence/manual_review only     | 网页证据，只能进人工复核或 evidence staging，不写 clean 表 |

### 2.2 数据源扩展对后续批次的影响

新增数据源影响最大的不是立即写 adapter，而是要求后续批次更新执行口径：

1. **R3FR-05 Provider Catalog** 必须覆盖所有 active/proposed source，不再只覆盖第一批旧源。
2. **B04_01 API source readiness** 必须展示 proposed-disabled sources，但不能让它们 fetch。
3. **SourceRoutePlan** 必须把新增源 route 成 `DISABLED_SOURCE`，直到启用证据齐全。
4. **Batch05 release manifest** 必须准确写出哪些 source 只是 proposed，不能把它们包装成生产已启用。

---

## 3. 后续批次总览

| 执行顺序 | canonical 批次文件夹                        | 性质                         | 是否可并行                                 | 业务目标                                                                                                             |
| -------- | ------------------------------------------- | ---------------------------- | ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| 1        | `BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/`    | 参考项目采纳与旧薄实现重构   | 部分可并行，见 §4                          | 先补基础规则、provider catalog、data health、TDX、backtest plan，避免后面继续重复造轮子                              |
| 2        | `BATCH_3G_SANDBOX_CLEAN_WRITE/`             | clean write 串行 gate 包     | 不可并行跳 gate                            | 先沙盒彩排，再审计，再极小范围生产写入，证明写入链路安全                                                             |
| 3        | `BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/`      | 全部目标 source 真实接入闭环 | 按 source/domain family 并行，最终统一审计 | 所有 registry/capability 目标 source 必须完成 adapter/gate/replay/route/evidence，或 ADR 明确排除；Round4 前强制完成 |
| 4        | `BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/`   | 产品化并行批次               | 可以按 track 并行，但有轻依赖              | 基于 3H 的真实数据/readiness/evidence 做 API、Agent、Frontend、Notification、Backtest 产品化                         |
| 5        | `BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/` | 发布 gate 批次               | 可并行但不能补产品功能                     | Security CI、integration/resource smoke、release manifest/package cleanup                                            |

---

## 4. Round 3F-R — 参考项目采纳与旧薄实现重构

执行入口：

```text
docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/
```

这个批次的目的很直接：**先把后面要用的基础能力补扎实，避免 Round3G/Round4 继续从零写重复轮子。**

### 4.1 任务卡

| 任务卡                                            | 能否并行                  | 说明                                                                              |
| ------------------------------------------------- | ------------------------- | --------------------------------------------------------------------------------- |
| `R3FR_01_REFERENCE_RULES_AND_LICENSE_GATE.md`     | 必须最先                  | 先定参考项目使用规则、license 边界、禁止复制 runtime source                       |
| `R3FR_02_EASYXT_DATA_HEALTH_REFACTOR.md`          | 可与 R3FR-03/04/05 并行   | 用 EasyXT 思路补 data health profile，不碰 TDX provider/catalog/backtest 文件     |
| `R3FR_06_QMD_DATA_HEALTH_CLI_RUNTIME.md`          | 与 R3FR-02 是同一垂直切片 | CLI 必须跟 data health engine 一起闭环，不能单独做 message-only wrapper           |
| `R3FR_03_TDX_PROVIDER_REFACTOR.md`                | 可并行                    | 只做 TDX disabled/raw-only provider port，不启用生产抓取                          |
| `R3FR_04_JQ2PTRADE_BACKTEST_ADOPTION_PLAN.md`     | 可并行                    | 规划 Round4 backtest/review 怎么借鉴 JQ2PTrade/EasyXT，不实现生产 backtest engine |
| `R3FR_05_PROVIDER_CATALOG_OPENBB_REFERENCE.md`    | 可并行但需读最新 registry | provider catalog 必须覆盖所有 active/proposed source，包括新增数据源              |
| `R3FR_07_LEGACY_WRAPPER_CLEANUP_AND_REDIRECTS.md` | 必须最后                  | 等替代任务完成后再清理旧 wrapper 和历史入口                                       |

### 4.2 完成标准

Round 3F-R 完成时必须满足：

- 每个参考项目的使用边界写清楚。
- 不存在 central executable `reference_adoption_inventory.md` 要求。
- Data health 从薄检查升级为可执行 profile。
- `qmd data health` 有真实 read-only 路径。
- TDX/mootdx/pytdx 类源仍默认禁用，且只读/raw-only。
- Provider catalog 覆盖所有 registry source，包括新增 proposed-disabled sources。
- Round4 backtest/review 不再允许从零写 blank engine。
- 旧 loose card 或 wrapper 不再误导执行者直接开工。

---

## 5. Round 3G — Sandbox Clean Write 与有限生产写入入口

执行入口：

```text
docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/
```

注意：虽然目录名里有 `BATCH_3G`，但它不是普通并行批次，而是 **串行 gate 包**。它的三个任务不能并行乱跑。

### 5.1 串行顺序

| 顺序 | 任务卡                                       | 是否可并行              | 说明                                                      |
| ---- | -------------------------------------------- | ----------------------- | --------------------------------------------------------- |
| 1    | `R3G_01_SANDBOX_CLEAN_WRITE_REHEARSAL.md`    | 不可与后两步并行        | 先在 sandbox 做 clean write 彩排，不碰 production DB      |
| 2    | `R3G_02_PRE_PRODUCTION_ADVERSARIAL_AUDIT.md` | 必须等 R3G-01           | 攻击性审计，确认不会污染生产库                            |
| 3    | `R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md`   | 必须等 R3G-02 PASS/WARN | 只允许极小范围、人工批准、可回滚的 production clean write |

### 5.2 第一批只允许

第一批 sandbox 或 limited production clean write 只能考虑小样本：

- `baostock` → A 股日线小窗口
- `cninfo` → 公告 metadata 小窗口
- `fred` → P0 macro series 小窗口（仍需 key/gate）

新增 proposed-disabled 数据源，例如 `us_treasury`、`sec_edgar`、`alpha_vantage`、`deribit` 等，不能因为已经进入 registry 就进入 3G 写入范围。它们必须在 **Batch 3H** 中全部完成 adapter、auth/license、ResourceGuard、route test、replay evidence 与 Layer/evidence 绑定；无法完成的 source 必须有 ADR 明确排除，不能只留作“以后再做”。

### 5.3 禁止范围

- 不做全市场。
- 不做全历史。
- 不做分钟线。
- 不做期权链全量。
- 不启用 QMT/TDX/Yahoo 作为 production primary。
- 不启用新增 proposed-disabled source。
- 不让 Agent/通知/报告驱动交易语义。

---

## 6. Round 3H — 全部真实数据源接入与生产入口闭环

执行入口：

```text
docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/
```

Batch 3H 是 Round4 之前的强制门禁。它不是“再选几个源做样例”，而是把 `source_registry.yaml` / `source_capabilities.yaml` 中的全部目标 source 做出最终结论。

每个 source 只能有两种结论：

1. `READY_WITH_EVIDENCE`：adapter/fetch port、auth/license、ResourceGuard、route tests、replay fixture/sandbox sample、fetch_log/content_hash/schema_hash/source_fetch_id、data health/source conflict、Layer evidence 绑定都完成。
2. `ADR_DISABLED_OUT_OF_SCOPE`：明确写 ADR 收窄当前产品承诺范围，source 继续保持 `DISABLED_SOURCE`，并进入 release limitation。

Batch 3H 的并行方式：

| 任务卡                                               | 覆盖范围                                                                                                                      | 并行规则                                           |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| `R3H_01_OFFICIAL_MACRO_DISCLOSURE_ADAPTERS.md`       | `fred`, `us_treasury`, `sec_edgar`, `cftc_cot`, `bis`, `world_bank`                                                           | 可并行；官方宏观/披露源独立分支                    |
| `R3H_02_MARKET_DATA_ADAPTERS.md`                     | `alpha_vantage`, `stooq`, `yahoo_finance`, `deribit`, `coingecko`                                                             | 可并行；市场/加密行情源独立分支                    |
| `R3H_03_CN_MARKET_ADAPTERS.md`                       | `baostock`, `akshare`, `cninfo`, `tdx_pytdx`, `mootdx`, `eastmoney`, `sina_finance`, `ths_ifind`, `qmt_xtdata`, `qmt_xqshare` | 可并行；中国市场源独立分支，但不能 silent fallback |
| `R3H_04_PREDICTION_AND_WEB_EVIDENCE_ADAPTERS.md`     | `kalshi`, `polymarket`, `web_search`                                                                                          | 可并行；只能 probability/evidence/manual_review    |
| `R3H_05_LAYER_BINDING_AND_PRODUCTION_ENTRY_AUDIT.md` | 汇总全部 source 与 Layer1–5 真实数据绑定                                                                                      | 必须最后；只做审计，不补实现                       |

Round4 只能在 `R3H-05` 输出 `PASS_ROUND4_REAL_DATA_READY` 或 `WARN_ROUND4_ALLOWED_WITH_NARROWED_SCOPE_ADR` 后开始。若输出 `BLOCK_ROUND4_DATA_ENTRY_INCOMPLETE`，不得进入 Round4。

---

## 7. Round 4 — API、Agent、前端、通知、回测/复核产品化

执行入口：

```text
docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/
```

Round4 只有一个 canonical 批次：**Batch04**。旧路线图里的 “Batch 4.1 / 4.2 / 4.3 / 4.4 / 4.5” 不再当作五个连续批次理解；它们现在是 Batch04 里的五条产品化 track。Round4 的前提是 Batch3H 已经让真实数据接入闭环通过，不能用 API/前端去包装一批仍未实现的 proposed-disabled source。

这些 track 可以分支并行，但要遵守轻依赖：

- API source/readiness endpoint 是 Agent 和 Frontend 的主要输入，建议先开或最先合。
- Agent 不能直接绕过 API/service 去读 DB。
- Frontend 不能直接读 DB。
- Notification/Report 和 Backtest/Review 可以并行，但不能写 production clean 表，也不能输出交易动作。

### 6.1 Batch04 任务卡

| 任务卡                                         | 并行性                            | 第一批必须交付什么                                                                                                |
| ---------------------------------------------- | --------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `B04_01_api_runtime_security.md`               | 建议最先                          | 一个真实 read-only API，例如 source/capability/readiness endpoint；必须显示 proposed-disabled source 但不能 fetch |
| `B04_02_agent_policy_runtime.md`               | 可在 API contract 稳定后并行      | 一个 policy-guarded read-only Agent tool；不能 free SQL、不能写库、不能输出交易动作                               |
| `B04_03_frontend_error_boundary_and_routes.md` | 可在 API mock/contract 稳定后并行 | 一个 API-bound 页面/面板；不能只有 ErrorBoundary 或 deferred routes                                               |
| `B04_04_notification_report_runtime.md`        | 可并行                            | 一个 event → report/notification_log 流程；不能 schema-only                                                       |
| `B04_05_backtest_review_runtime.md`            | 可并行                            | 一个 read-only review scenario；必须借鉴 JQ2PTrade/EasyXT，但不能复制交易 API                                     |

### 6.2 Batch04 完成标准

Batch04 完成时，不能只是“搭了壳”。必须有：

- API 有真实可调用 read-only endpoint。
- Agent 有真实可执行 read-only tool。
- Frontend 有至少一个真实 API-bound 页面。
- Notification/Report 有至少一条真实事件流。
- Backtest/Review 有至少一个可运行 read-only scenario。

如果做不到，就不能写成完成，只能阻断或明确 re-defer。

---

## 8. Round 5 — 安全、集成、发布收口

执行入口：

```text
docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/
```

Round5 不是补功能批次。它只做 release gate。

如果 Round3G 或 Round4 有功能没完成，Round5 的正确做法是：

- 阻断发布，或
- 写入 release manifest 的 open/deferred item，说明 owner、phase、closure test。

不能在 Round5 偷偷新增一个“补功能小任务”。

### 7.1 Batch05 任务卡

| 任务卡                                           | 并行性             | 目标                                                                         |
| ------------------------------------------------ | ------------------ | ---------------------------------------------------------------------------- |
| `B05_01_security_ci_release_gate.md`             | 可并行             | secret scan、dependency/security scan、security CI gate                      |
| `B05_02_integration_and_resource_smoke.md`       | 可并行             | bounded integration smoke、ResourceGuard、production-equivalent smoke budget |
| `B05_03_release_manifest_and_package_cleanup.md` | 可并行，但最后汇总 | release manifest、docs consistency、package cleanup、runbook 指针            |

### 7.2 Batch05 必须体现新增数据源状态

Release manifest 必须准确写出：

- 哪些 source 是 active。
- 哪些 source 是 sandbox candidate。
- 哪些 source 只是 proposed-disabled。
- 哪些 source 需要 API key、用户授权或商业授权。
- 哪些 source 只能 evidence/manual_review。
- 哪些 source 绝对不能写 clean 表。

尤其是 `web_search`、`kalshi`、`polymarket`、`coingecko`、`eastmoney`、`sina_finance`、`ths_ifind` 这类源，必须写清楚限制，不能被包装成生产主源。

---

## 9. 数据源 adapter 的 Batch3H 完整实现路线

新增 source 已进入 registry/capability，但 adapter 还没有完整实现。这里不能再写成 Round5 之后的“后续 adapter 批次”；它必须作为 **Batch3H** 在 Round4 前完成。

Batch3H 不是按优先级挑一部分做，而是按可并行的数据域拆成四组，**每组必须覆盖全部 source**：

| Batch3H 任务卡                                   | 必须覆盖的数据源                                                                                                              | 完成口径                                                                                    |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `R3H_01_OFFICIAL_MACRO_DISCLOSURE_ADAPTERS.md`   | `fred`, `us_treasury`, `sec_edgar`, `cftc_cot`, `bis`, `world_bank`                                                           | 全部 READY_WITH_EVIDENCE 或 ADR_DISABLED_OUT_OF_SCOPE                                       |
| `R3H_02_MARKET_DATA_ADAPTERS.md`                 | `alpha_vantage`, `stooq`, `yahoo_finance`, `deribit`, `coingecko`                                                             | 全部 READY_WITH_EVIDENCE 或 ADR_DISABLED_OUT_OF_SCOPE                                       |
| `R3H_03_CN_MARKET_ADAPTERS.md`                   | `baostock`, `akshare`, `cninfo`, `tdx_pytdx`, `mootdx`, `eastmoney`, `sina_finance`, `ths_ifind`, `qmt_xtdata`, `qmt_xqshare` | 全部 READY/validation-only READY/authorized-disabled 或 ADR_DISABLED_OUT_OF_SCOPE           |
| `R3H_04_PREDICTION_AND_WEB_EVIDENCE_ADAPTERS.md` | `kalshi`, `polymarket`, `web_search`                                                                                          | 全部 evidence/probability path 或 ADR_DISABLED_OUT_OF_SCOPE；不得 clean-write factual table |

每个 adapter 都必须完成：

```text
adapter 实现
contract tests
route planner tests
ResourceGuard gate
auth/license gate
fetch_log / content_hash / schema_hash
replay fixture 或 sandbox sample
docs/generated index 更新
CI 验证记录
```

没有这些证据，不得把 source 从 `DISABLED_SOURCE` 提升为 `READY`。也不得因为其中一个 source 完成，就把同组其他 source 留作未定义的“以后再做”；未完成者必须写 ADR 并在 route/release manifest 中保持 disabled/out-of-scope。

---

## 10. 推荐执行顺序

```text
1. BATCH_3FR_REFERENCE_ADOPTION_REFACTOR
   先补参考项目使用规则、provider catalog、data health、TDX、backtest plan。

2. BATCH_3G_SANDBOX_CLEAN_WRITE
   串行：sandbox rehearsal → pre-production audit → limited production clean write，证明 clean-write 链路安全。

3. BATCH_3H_REAL_DATA_PRODUCTION_ENTRY
   并行完成全部目标 source 的 adapter/auth/license/ResourceGuard/route/replay/evidence/Layer 绑定；未完成者必须 ADR_DISABLED_OUT_OF_SCOPE。

4. BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION
   基于 3H 已闭合的真实数据/readiness/evidence，做 API / Agent / Frontend / Notification / Backtest 产品化。

5. BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE
   发布 gate：security CI / integration smoke / release manifest。
```

---

## 11. 什么情况下可以进入 production clean write

必须同时满足：

1. Round 3F-R 已完成，或者未完成项有明确 ADR defer。
2. Round 3G sandbox rehearsal PASS。
3. Round 3G pre-production adversarial audit 输出：
   - `PASS_ALLOW_LIMITED_PROD_WRITE`，或
   - `WARN_ALLOW_WITH_MANUAL_APPROVAL`
4. 用户明确批准：source、domain、symbol/series、window、row cap。
5. WriteManager / DbValidationGate / ResourceGuard / DataHealth / SourceConflict / Layer5 evidence 都有记录。
6. rollback/no-mutation proof 可查。

第一批 production clean write 只允许极小范围；不允许把新增 proposed-disabled source 直接纳入 3G 写入。但进入 Round4 前，Batch3H 必须对全部目标 source 完成 adapter/evidence 闭环或 ADR 排除，不能把真实数据接入债务留给产品化阶段。

---

## 12. 执行者最后检查清单

每次开工前问自己：

1. 我是不是从 canonical batch folder 入口开始的？
2. 我是不是直接执行了旧 loose card？如果是，停止。
3. 这个任务有没有独立任务卡？
4. 这个任务和同批次其他任务能不能并行，不会改同一核心文件互相冲突？
5. 如果不能并行，路线图是否写成 gate 顺序，而不是伪装成批次？
6. 涉及数据源时，是否先走 SourceRoutePlan，而不是直接 adapter fetch？
7. 新增 source 是否仍是 disabled/proposed，是否有证据才能 READY？
8. Batch3H 是否已经覆盖全部目标 source，而不是只完成一组样例 adapter？
9. 每个未完成 source 是否有 ADR_DISABLED_OUT_OF_SCOPE，而不是含糊留到以后？
10. 涉及参考项目时，是否只借鉴架构/逻辑，没有复制 runtime source？
11. 涉及 clean write 时，是否先有 data health、conflict summary、WriteManager、DbValidationGate？
12. 任务完成时，是否更新了 tests、contract coverage、test catalog 或 release manifest？

如果本文件和旧规划冲突：**未来执行以本文件为准；历史追溯仍看旧任务、旧证据和 Trellis archive。**
