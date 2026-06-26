# QMD 项目实施总路线图（总施工图 / 业务版）

> **结论：需要按最新口径重写。** 旧版路线图已经抓住了大方向，但和最新任务卡相比还存在几类风险：
>
> - Batch04、README 等文件要求读取 `roadmap §1.4`，但路线图里没有这个编号段落，执行者会找不到“参考项目怎么用”的总规则。
> - 3F-R → 3G 的门禁不能只写“R3FR-01 完成”；最新任务卡要求 **Round 3F-R 完成，或者所有未完成项都有 ADR defer + owner + closure gate**，否则 3G 不能开。
> - `PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` 只能是覆盖地图，不是工单。真正执行必须回到对应任务卡。
> - Round5 不是补功能批次，不能把 3H / Round4 没做完的东西藏到发布批次里补。
>
> **本文件定位：** 这是根目录的“总施工图”。它串联所有批次、并行/串行关系、任务卡入口、交付标准、每个模块在哪个批次完成主能力、以及哪个批次做最终 R6 发布确认。  
> **通俗解释：** 本文件告诉你“整栋楼怎么施工”；每张任务卡告诉你“某个房间怎么施工”。地图不是工单，任务卡才是工单。

---

## 0. 本次重写已核实的最新任务卡

本路线图按以下文件核实后重写，后续执行者必须从这些 canonical 任务卡入口开工：

| 范围             | 已核实的口径文件                                                                                                      | 关键口径                                                                                 |
| ---------------- | --------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| 生产完成覆盖地图 | `docs/implementation_tasks/PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md`                                              | 只是覆盖/导航 checklist，不是 standalone execution card。                                |
| 当前执行顺序     | `docs/implementation_tasks/README.md`                                                                                 | 当前下一入口是 `ROUND_3_REFERENCE_ADOPTION_REFACTOR/`，之后才到 3G、3H、Round4、Round5。 |
| 完成度规则       | `MODULE_COMPLETION_RATING.md`                                                                                         | 不能用 docs、registry、placeholder、staged fixture 冒充 `R6_FULL_PRODUCTION_STABLE`。    |
| Batch 3F-R       | `BATCH_3FR_TASK_CARD_MANIFEST.md`、`BATCH_3FR_COORDINATOR_PLAYBOOK.md`、`R3FR_01_REFERENCE_RULES_AND_LICENSE_GATE.md` | R3FR-01 必须重跑；参考项目细节必须在任务卡本地，不能放中央 inventory。                   |
| Batch 3G         | `BATCH_3G_TASK_CARD_MANIFEST.md`、`BATCH_3G_COORDINATOR_PLAYBOOK.md`                                                  | R3G-01 → R3G-02 → R3G-03 严格串行；不能并行。                                            |
| Batch 3H         | `BATCH_3H_TASK_CARD_MANIFEST.md`、`BATCH_3H_COORDINATOR_PLAYBOOK.md`                                                  | R3H-01~04 可按 source domain 并行；R3H-05 必须最后审计，不能补 adapter。                 |
| Batch04 / Round4 | `BATCH_04_TASK_CARD_MANIFEST.md`、`BATCH_04_COORDINATOR_PLAYBOOK.md`、`B04_05_backtest_review_runtime.md`             | Round4 必须等 R3H-05 PASS/WARN；loose 024~030 只是历史输入；API 先打底。                 |
| Batch05 / Round5 | `BATCH_05_TASK_CARD_MANIFEST.md`、`BATCH_05_COORDINATOR_PLAYBOOK.md`                                                  | Round5 是 security / integration / release gate，不能作为补功能后门。                    |

如果本文件和某张 canonical 任务卡的具体执行细节冲突：**不要用路线图压过任务卡；应立即修路线图或任务卡，让二者重新闭环。**

---

## 1. 全局规则：什么才算完整生产级

### 1.1 一句话标准

一个模块只有同时做到“能跑、可控、可查、可测、可限制、可发布”，才可以在 Round5 被确认成 `R6_FULL_PRODUCTION_STABLE`。

不能把下面这些说成生产级：

```text
只有文档
只有 registry 行
只有 placeholder
只有 staged fixture
只有 sandbox demo
只有一个 sample adapter
只有 API/前端壳
```

### 1.2 生产级必须具备的证据

| 要求         | 小白解释                         | 必须看到的东西                                                                           |
| ------------ | -------------------------------- | ---------------------------------------------------------------------------------------- |
| 真实垂直闭环 | 至少有一条业务路径能跑到底       | API/CLI/服务/adapter/report 等实际调用链，不是假数据成功。                               |
| 明确范围     | 承诺什么、不承诺什么都写清楚     | `READY_WITH_EVIDENCE`、`ADR_DISABLED_OUT_OF_SCOPE`、release limitation。                 |
| 数据证据链   | 数据从哪里来、有没有被改过可追溯 | `fetch_log`、`source_fetch_id`、`content_hash`、`schema_hash`、replay/sandbox evidence。 |
| 资源保护     | 不允许一上来扫全市场/全历史      | ResourceGuard caps、row/window/symbol/source limits。                                    |
| 安全边界     | API/Agent/CLI 不得乱查乱写       | auth、no free SQL、no direct write、secret redaction、forbidden action tests。           |
| 测试门禁     | 不是“不报错”就算过               | contract tests、negative tests、regression tests、bounded smoke。                        |
| 发布记录     | 发版时知道哪些能用、哪些禁用     | release manifest、runbook、known limitations、rollback/disable path。                    |

### 1.3 R6 的两层判断

| 判断项              | 含义                                                                        |
| ------------------- | --------------------------------------------------------------------------- |
| **主能力完成批次**  | 这个模块的核心功能在哪个批次真正做出来。                                    |
| **R6 发布确认批次** | Round5 统一通过安全、集成、资源、文档和 manifest 后，才正式算可发布生产级。 |

所以，很多模块会在 3F-R、3G、3H 或 Round4 做完主能力，但最终生产级标签统一在 **Batch05 / Round5** 确认。

### 1.4 参考项目使用总规则（供 Batch04 等文件引用）

这是所有提到 `roadmap §1.4` 的任务卡要找的规则。

参考项目可以帮我们少走弯路，但不能直接变成 QMD runtime。所有 JQ2PTrade、EasyXT、OpenBB、agents-for-openbb、TradingAgents、TradingAgents-astock 相关采纳必须遵守：

| 规则               | 说明                                                                                                                                |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| 任务卡本地执行     | 参考路径、可借逻辑、禁止能力、QMD 目标文件、测试、not-done 条件，必须写在对应任务卡里。不能只写“参考某项目”。                       |
| 覆盖地图不是工单   | `PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` 只能检查有没有漏模块，不能替代任务卡。                                               |
| 不复制危险 runtime | 不得从 `参考项目/**` runtime import，不得复制 OpenBB AGPL runtime，不得引入 JQ2PTrade/EasyXT 交易 API。                             |
| 不引入交易动作     | 禁止 order、order_value、order_target、cancel_order、get_positions、run_daily、auto-login、broker/account/terminal control 等语义。 |
| 不允许空壳完成     | 如果只是 policy、shell、schema、registry、单个 metric，不能算完成。                                                                 |
| 最多三批达生产稳定 | 一个模块从首次实现到完整稳定，最多三个实施批次：第一批真实最小垂直闭环，第二批完成主承诺范围，第三批只做硬化/回归/发布 gate。       |

---

## 2. 总施工顺序：哪些串行，哪些并行

```text
历史底座：Round0 / Round1 / Round2 / Round2.6 / 早期 Round3 / 3V / 3F
  ↓
Batch 3F-R：参考项目采纳规则重跑 + data health / provider / backtest planning 重整
  ↓
Batch 3G：sandbox clean write → pre-production audit → limited production clean write（严格串行）
  ↓
Batch 3H：全部目标数据源生产入口，四个 source 分支并行，R3H-05 最后审计
  ↓
Batch04 / Round4：API 先打底，Agent / Frontend / Notification / Backtest 产品化分支并行
  ↓
Batch05 / Round5：Security / Integration / Release 发布门禁，确认所有模块 R6 或明确 limitation
```

| 总批次           | 是否新执行入口   | 并行/串行                                 | 业务目标                                                                         | 进入下一批次的硬门禁                                         |
| ---------------- | ---------------- | ----------------------------------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| 历史底座         | 否               | 不作为新开工入口                          | 已有项目骨架、DB、registry、staged Layer、治理基础                               | 只能作为历史输入，不能把 staged 当 production。              |
| Batch 3F-R       | 是，当前下一入口 | R3FR-01 先；之后可分支；R3FR-07 最后      | 把参考项目采纳、data health、provider catalog、TDX、Backtest planning 口径补扎实 | 3F-R 完成，或未完成项都有 ADR defer + owner + closure gate。 |
| Batch 3G         | 是，3F-R 后      | 严格串行                                  | 证明 clean write 可以在受控边界内安全发生                                        | R3G-02 允许 + 用户明确批准后才能 R3G-03。                    |
| Batch 3H         | 是，3G 后        | 4 个 source domain 分支并行，R3H-05 最后  | 所有目标 source 要么 READY_WITH_EVIDENCE，要么 ADR_DISABLED_OUT_OF_SCOPE         | R3H-05 输出 PASS 或 WARN_WITH_NARROWED_SCOPE_ADR。           |
| Batch04 / Round4 | 是，3H 后        | API 先，其他产品分支按依赖并行            | 把数据/证据能力变成 API、Agent、前端、通知、回测/复盘产品闭环                    | 每个产品模块都有真实 read-only 垂直闭环。                    |
| Batch05 / Round5 | 是，Round4 后    | B05-01 先；B05-02 等产物稳定；B05-03 最后 | 做最终 security / integration / release gate                                     | 通过则 release；不通过则阻断或写 release limitation。        |

---

## 3. Batch 3F-R：参考项目采纳与旧薄实现重整

### 3.1 执行入口

```text
docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/
```

核心文件：

```text
README.md
BATCH_3FR_TASK_CARD_MANIFEST.md
BATCH_3FR_COORDINATOR_PLAYBOOK.md
BATCH_3FR_HARDENING_RULES.md
R3FR_01_REFERENCE_RULES_AND_LICENSE_GATE.md
R3FR_02_EASYXT_DATA_HEALTH_REFACTOR.md
R3FR_03_TDX_PROVIDER_REFACTOR.md
R3FR_04_JQ2PTRADE_BACKTEST_ADOPTION_PLAN.md
R3FR_05_PROVIDER_CATALOG_OPENBB_REFERENCE.md
R3FR_06_QMD_DATA_HEALTH_CLI_RUNTIME.md
R3FR_07_LEGACY_WRAPPER_CLEANUP_AND_REDIRECTS.md
```

### 3.2 业务目标

3F-R 不是上线真实源，也不是写 production clean table。它解决的是：

- 参考项目能借什么，不能借什么。
- 哪些旧薄实现必须重写成真实垂直闭环。
- Round4 的 backtest/review 不能从零乱造，必须先吸收 JQ2PTrade/EasyXT 的可借结构。
- Provider catalog 必须覆盖每个 source，不能只有 registry 名字。

### 3.3 串行 / 并行安排

```text
R3FR-01：参考项目治理规则重跑（必须最先，严格串行）
  ↓
第一波并行，最多 3 条分支：
  分支 A：R3FR-02 + R3FR-06（data health engine + qmd data health CLI，必须作为一条垂直切片）
  分支 B：R3FR-04（Round4 backtest/review 采纳计划）
  分支 C：R3FR-05（OpenBB-inspired provider catalog）
  ↓
R3FR-03：TDX provider refactor（在分支 A profile contract 稳定后启动；可与 B/C 的余量并行）
  ↓
R3FR-07：legacy wrapper cleanup（必须最后）
```

### 3.4 原始任务卡对应关系

| 分支 | 任务卡                                            | 能否并行                            | 做什么                                                                  | 必须交付                                                                                                    |
| ---- | ------------------------------------------------- | ----------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Gate | `R3FR_01_REFERENCE_RULES_AND_LICENSE_GATE.md`     | 不可并行，必须最先                  | 重跑参考项目治理；明确覆盖地图不是工单；补齐路线图、guardrail、索引口径 | `specs/contracts/reference_adoption_guardrails.yaml`、路线图、README、static check 全部说明任务卡本地执行。 |
| A    | `R3FR_02_EASYXT_DATA_HEALTH_REFACTOR.md`          | 可与 B/C 并行                       | 借鉴 EasyXT 的数据完整性思路，重构 QMD data health profile engine       | `market_bar_p0` 等 profile，不是单规则微切片；OHLCV、calendar gap、stale、outlier、volume 等测试。          |
| A    | `R3FR_06_QMD_DATA_HEALTH_CLI_RUNTIME.md`          | 和 R3FR-02 是同一垂直切片           | 把 `qmd data health` 从 placeholder 接到真实 read-only profile runtime  | CLI 不再返回 `not_implemented_phase_c`；支持 JSON/text；不写库、不触发抓取。                                |
| B    | `R3FR_04_JQ2PTRADE_BACKTEST_ADOPTION_PLAN.md`     | 可与 A/C 并行                       | 把 Round4 backtest/review 改成参考采纳后的可执行计划                    | B04_05 必须有 frozen loader、no-action guard、runner、report、metrics、API binding，最多三批稳定。          |
| C    | `R3FR_05_PROVIDER_CATALOG_OPENBB_REFERENCE.md`    | 可与 A/B 并行；共享 registry 需协调 | 借鉴 OpenBB provider catalog 组织方式，但不复制 AGPL runtime            | `provider_catalog.yaml` 覆盖所有 active/proposed source，区分 metadata 与 adapter readiness。               |
| D    | `R3FR_03_TDX_PROVIDER_REFACTOR.md`                | 在 A 契约稳定后启动                 | 把 TDX 相关能力收进 QMD-owned disabled/raw-only provider port           | 默认禁用、只读、授权边界明确、无 auto-login、无 silent fallback、无全市场扫描。                             |
| Last | `R3FR_07_LEGACY_WRAPPER_CLEANUP_AND_REDIRECTS.md` | 不可提前                            | 清理旧 wrapper、redirect loose cards、修索引                            | 只能在替代实现和测试更强后收尾；不能新增更多微切片。                                                        |

### 3.5 本批次主能力完成的模块

| 模块                                    | 主能力完成批次      | Round5 R6 确认方式                                                                           |
| --------------------------------------- | ------------------- | -------------------------------------------------------------------------------------------- |
| 参考项目采纳治理                        | 3F-R / R3FR-01      | Batch05 确认没有中央 executable inventory、没有 runtime import、没有 unsafe copied runtime。 |
| Data health engine                      | 3F-R / R3FR-02      | Batch05 确认 profile tests、contract coverage、release limitation。                          |
| `qmd data health` CLI                   | 3F-R / R3FR-06      | Batch05 确认 packaged CLI、JSON/text 输出、无写入/抓取副作用。                               |
| Provider catalog / auth-license posture | 3F-R / R3FR-05 + 3H | Batch05 确认每个 source 都有 provider posture 和 final decision。                            |
| TDX provider 边界                       | 3F-R / R3FR-03 + 3H | Batch05 确认 disabled/raw-only/authorization posture 与 release limitation。                 |
| Backtest/Review 采纳计划                | 3F-R / R3FR-04      | Round4 B04_05 实现；Batch05 确认发布。                                                       |

### 3.6 进入 3G 的门禁

3G 不能只因为 R3FR-01 完成就开。必须满足以下之一：

```text
条件 A：Batch 3F-R 全部完成并通过 batch close criteria
条件 B：仍有 open 3F-R 项，但每个 open item 都有 ADR defer、owner、deferred phase、closure gate，且不会影响 3G clean-write 安全
```

---

## 4. Batch 3G：Sandbox Clean Write 与有限生产写入

### 4.1 执行入口

```text
docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/
```

核心文件：

```text
BATCH_3G_TASK_CARD_MANIFEST.md
BATCH_3G_COORDINATOR_PLAYBOOK.md
BATCH_3G_HARDENING_RULES.md
R3G_01_SANDBOX_CLEAN_WRITE_REHEARSAL.md
R3G_02_PRE_PRODUCTION_ADVERSARIAL_AUDIT.md
R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md
```

### 4.2 业务目标

3G 证明系统不是只能读数据，也能在严格保护下写 clean table。但写入必须像试飞一样：先在 sandbox 彩排，再被攻击性审计，最后才允许极小范围生产入口。

### 4.3 严格串行安排

3G 不允许并行。

| 顺序 | 任务卡                                       | 是否可并行                 | 做什么                                                                                                | 必须交付                                                                                                                  |
| ---- | -------------------------------------------- | -------------------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| 1    | `R3G_01_SANDBOX_CLEAN_WRITE_REHEARSAL.md`    | 不可并行                   | 在 sandbox rehearsal 中验证 baostock daily bar、cninfo metadata、authorized FRED P0 sample 等候选路径 | sandbox DB only、WriteManager audit、DbValidationGate PASS、DataHealth PASS/WARN、before/after proof、no-mutation proof。 |
| 2    | `R3G_02_PRE_PRODUCTION_ADVERSARIAL_AUDIT.md` | 等 R3G-01 证据完成         | 审计 R3G-01 证据，决定能否进入 limited production write                                               | 输出 `PASS_ALLOW_LIMITED_PROD_WRITE`、`WARN_ALLOW_WITH_MANUAL_APPROVAL` 或 `BLOCK_PRODUCTION_WRITE`。                     |
| 3    | `R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md`   | 等 R3G-02 allow + 用户批准 | 做极小范围 approved production entry                                                                  | 明确 source/domain/symbol/window/row cap、approval artifact、before/after proof、rollback dry run、audit log。            |

### 4.4 本批次主能力完成的模块

| 模块                                              | 主能力完成批次 | Round5 R6 确认方式                                                                     |
| ------------------------------------------------- | -------------- | -------------------------------------------------------------------------------------- |
| WriteManager + DbValidationGate 生产写入链路      | 3G             | Batch05 integration/resource smoke 确认写入默认关闭、受控、可回滚。                    |
| Sandbox clean write / limited production entry    | 3G             | Batch05 release manifest 记录 write posture、approval posture、rollback/disable path。 |
| Source conflict validator 写入前绑定              | 3G + 3H        | Batch05 确认 conflict report 已进入 readiness/write gate。                             |
| `qmd data` operator flows 中的 limited-write 入口 | 3G             | Batch05 确认没有越权写入和无批准写入路径。                                             |

### 4.5 禁止事项

- 不能全市场写入。
- 不能全历史写入。
- 不能默认 minute-level 扫描。
- 不能把 proposed-disabled source 直接写入生产表。
- 不能绕过 DataSourceService、SourceRoutePlanner、ResourceGuard、DataHealth、SourceConflict、WriteManager、DbValidationGate。
- 不能由 Agent 触发写入。
- 没有用户明确批准 source/domain/symbol/window/row cap，不能执行 R3G-03。

---

## 5. Batch 3H：全部目标真实数据源与 Layer1-Layer5 生产入口

### 5.1 执行入口

```text
docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/
```

核心文件：

```text
BATCH_3H_TASK_CARD_MANIFEST.md
BATCH_3H_COORDINATOR_PLAYBOOK.md
BATCH_3H_HARDENING_RULES.md
R3H_01_OFFICIAL_MACRO_DISCLOSURE_ADAPTERS.md
R3H_02_MARKET_DATA_ADAPTERS.md
R3H_03_CN_MARKET_ADAPTERS.md
R3H_04_PREDICTION_AND_WEB_EVIDENCE_ADAPTERS.md
R3H_05_LAYER_BINDING_AND_PRODUCTION_ENTRY_AUDIT.md
```

### 5.2 业务目标

3H 是 Round4 前最关键的门。它回答：系统到底哪些真实数据源能用，哪些不能用，哪些只能校验，哪些只能人工复核。

每个目标 source 最终只能有两类闭合：

| 状态                        | 含义                                                                                                                                                                                              |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `READY_WITH_EVIDENCE`       | 有 adapter/fetch port、auth/license、ResourceGuard、route、replay/sandbox evidence、fetch_log、content_hash、schema_hash、source_fetch_id、data health、source conflict、Layer/evidence binding。 |
| `ADR_DISABLED_OUT_OF_SCOPE` | 当前产品不承诺这个 source；有 ADR、route reason、release limitation，不得伪装成 ready。                                                                                                           |

### 5.3 并行分支安排

```text
共享 registry / capability / route / schema enum baseline freeze
  ↓
并行 4 个 source domain 分支：
  H-A：官方宏观/披露源
  H-B：市场/加密源
  H-C：中国市场/授权/校验源
  H-D：预测市场/网页证据源
  ↓
协调合并 shared registry/capability/route/test catalog changes
  ↓
R3H-05：最终 Layer1-Layer5 + source production-entry audit（必须最后）
```

共享文件包括：

```text
specs/datasource_registry/source_registry.yaml
specs/datasource_registry/source_capabilities.yaml
specs/contracts/source_capability_contract.yaml
specs/contracts/source_route_contract.yaml
specs/contracts/datasource_service_contract.yaml
specs/verification/contract_coverage.yaml
docs/modules/data_sources.md
docs/modules/source_route_plan.md
tests/test_catalog.yaml
```

这些文件不能由多个分支随意抢改，必须走 coordinator review。

### 5.4 原始任务卡对应关系

| 分支  | 任务卡                                               | 覆盖 source                                                                                                                   | 能否并行              | 必须交付                                                                                                    |
| ----- | ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | --------------------- | ----------------------------------------------------------------------------------------------------------- |
| H-A   | `R3H_01_OFFICIAL_MACRO_DISCLOSURE_ADAPTERS.md`       | `fred`, `us_treasury`, `sec_edgar`, `cftc_cot`, `bis`, `world_bank`                                                           | 可与 H-B/H-C/H-D 并行 | 每个 source adapter/gate/replay/route/evidence 或 ADR-disabled；Layer1/Layer5 绑定。                        |
| H-B   | `R3H_02_MARKET_DATA_ADAPTERS.md`                     | `alpha_vantage`, `stooq`, `yahoo_finance`, `deribit`, `coingecko`                                                             | 可并行                | 每个 source 有 bounded fetch/evidence 或 ADR-disabled；聚合源不能 silent primary。                          |
| H-C   | `R3H_03_CN_MARKET_ADAPTERS.md`                       | `baostock`, `akshare`, `cninfo`, `tdx_pytdx`, `mootdx`, `eastmoney`, `sina_finance`, `ths_ifind`, `qmt_xtdata`, `qmt_xqshare` | 可并行                | 中国市场源全部明确 primary/validation/authorization-disabled/ADR-disabled；QMT/iFinD/xqshare 不得默认启用。 |
| H-D   | `R3H_04_PREDICTION_AND_WEB_EVIDENCE_ADAPTERS.md`     | `kalshi`, `polymarket`, `web_search`                                                                                          | 可并行                | 只能 probability/evidence/manual-review；不得写 factual clean table。                                       |
| Audit | `R3H_05_LAYER_BINDING_AND_PRODUCTION_ENTRY_AUDIT.md` | 所有 source + Layer1-Layer5                                                                                                   | 必须最后              | 输出 PASS / WARN_WITH_ADR / BLOCK；不能在审计卡里补 adapter。                                               |

### 5.5 本批次主能力完成的模块

| 模块                                                         | 主能力完成批次 | Round5 R6 确认方式                                                          |
| ------------------------------------------------------------ | -------------- | --------------------------------------------------------------------------- |
| RawStore / FileRegistry / fetch_log 真实数据绑定             | 3H             | Batch05 确认所有 in-scope source 有 lineage evidence。                      |
| DataSourceService / SourceRoutePlanner / capability registry | 3H             | Batch05 确认 API/Agent/Sync 只消费 R3H final decision，不绕过 service。     |
| Vendor adapters / provider fetch ports                       | 3H             | Batch05 确认所有 target source READY 或 ADR-disabled。                      |
| Provider catalog 最终 source 姿态                            | 3H + 3F-R      | Batch05 release manifest 记录 license/auth/source posture。                 |
| ResourceGuard 在真实 adapter 中的执行                        | 3H             | Batch05 integration/resource smoke 复核。                                   |
| Source conflict validator 对真实 source/domain 的绑定        | 3H             | Batch05 确认冲突结果进入 readiness/write/release gate。                     |
| Layer1 axes                                                  | 3H / R3H-05    | Batch05 确认 real official/macro evidence 或 ADR narrowing。                |
| Layer2 sensors                                               | 3H / R3H-05    | Batch05 确认 real market/CN/validation source envelope。                    |
| Layer3 chains                                                | 3H / R3H-05    | Batch05 确认 CN/industry-chain evidence path 或 ADR narrowed scope。        |
| Layer4 markets                                               | 3H / R3H-05    | Batch05 确认 market/calendar/breadth source binding 或 ADR narrowed scope。 |
| Layer5 evidence                                              | 3H / R3H-05    | Batch05 确认 source_fetch_id/content_hash/schema_hash/limitation chain。    |

### 5.6 Round4 启动门禁

R3H-05 只能输出：

```text
PASS_ROUND4_REAL_DATA_READY
WARN_ROUND4_ALLOWED_WITH_NARROWED_SCOPE_ADR
BLOCK_ROUND4_DATA_ENTRY_INCOMPLETE
```

Round4 只能在前两个结果后开始。WARN 必须带明确 ADR，说明哪些 source/layer/domain 被收窄；不能把未完成 source 静默留到以后。

---

## 6. Batch04 / Round4：API、Agent、Frontend、Notification、Backtest 产品化

### 6.1 执行入口

```text
docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/
```

核心文件：

```text
BATCH_04_TASK_CARD_MANIFEST.md
BATCH_04_COORDINATOR_PLAYBOOK.md
BATCH_04_HARDENING_RULES.md
B04_01_api_runtime_security.md
B04_02_agent_policy_runtime.md
B04_03_frontend_error_boundary_and_routes.md
B04_04_notification_report_runtime.md
B04_05_backtest_review_runtime.md
```

历史 loose cards `024`–`030` 只作为输入，不是默认执行入口。

### 6.2 业务目标

Round4 把 3H 之前的底层能力变成用户和系统可用的产品形态：

- API：真实 read-only endpoint。
- Agent：policy-guarded read-only tool。
- Frontend：真实 API-bound page/panel。
- Notification/Report：event → report/notification_log。
- Backtest/Review：read-only review scenario + report artifact。

全部必须是 read-only / no-action；QMD 不是交易执行系统。

### 6.3 串行 / 并行安排

```text
前置条件：R3H-05 = PASS 或 WARN_WITH_NARROWED_SCOPE_ADR
  ↓
B04-01：API runtime/security 先启动，产出稳定 read-only contract
  ↓
API contract 稳定后，最多 4 个产品分支并行：
  分支 A：B04-02 Agent policy runtime
  分支 B：B04-03 Frontend route / error boundary / API-bound panel
  分支 C：B04-04 Notification / report runtime
  分支 D：B04-05 Backtest / review runtime
  ↓
Batch04 统一验收：每个产品模块都有真实第一垂直闭环
```

B04-05 还额外依赖 R3FR-04 和 Layer5/R3H evidence，不得做 blank engine。

### 6.4 原始任务卡对应关系

| 分支            | Canonical 任务卡                               | 历史 loose card 输入                                                                          | 能否并行                                | 必须交付                                                                                                                               |
| --------------- | ---------------------------------------------- | --------------------------------------------------------------------------------------------- | --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| API             | `B04_01_api_runtime_security.md`               | `024_implement_fastapi_routes.md`                                                             | 最先                                    | 一个 authenticated read-only source/capability/readiness endpoint；pagination、budget、error redaction；无 free SQL、无写接口。        |
| Agent           | `B04_02_agent_policy_runtime.md`               | `025_implement_agent_tool_layer.md`, `030_implement_no_action_semantics_guard.md`             | API contract 稳定后并行                 | 一个 policy-guarded read-only Agent tool；拒绝 forbidden tools/prompt injection；输出 evidence-bound。                                 |
| Frontend        | `B04_03_frontend_error_boundary_and_routes.md` | `026_implement_frontend_shell.md`, `027_implement_frontend_layer_pages.md`                    | route contract 稳定后并行               | 一个 API-bound page/panel；有 loading/empty/error states；不强行定稿用户最终视觉设计。                                                 |
| Notification    | `B04_04_notification_report_runtime.md`        | `028_implement_reports_and_notifications.md`                                                  | API/report contract 稳定后并行          | 一个 event → report/notification_log flow；dedup/cooldown/evidence refs。                                                              |
| Backtest/Review | `B04_05_backtest_review_runtime.md`            | `029_implement_backtest_and_review.md`, `030_implement_no_action_semantics_guard.md`, R3FR-04 | 可并行，但等 R3FR-04 与 evidence 准备好 | QMD-owned frozen loader、no-action guard、read-only runner、report artifact、metrics、API binding；不得复制 JQ2PTrade/EasyXT runtime。 |

### 6.5 本批次主能力完成的模块

| 模块                                 | 主能力完成批次            | Round5 R6 确认方式                                                                       |
| ------------------------------------ | ------------------------- | ---------------------------------------------------------------------------------------- |
| API backend                          | Batch04 / B04-01          | Batch05 security/integration/release manifest 确认。                                     |
| Agent layer                          | Batch04 / B04-02          | Batch05 确认 read-only、no-action、evidence-bound、prompt/tool guard。                   |
| Frontend dashboard / API-bound shell | Batch04 / B04-03          | Batch05 确认 build、contract、error/empty/loading states；最终视觉布局由用户设计。       |
| Notification/report runtime          | Batch04 / B04-04          | Batch05 确认 event/report/log/dedup/cooldown/retry/evidence refs。                       |
| Backtest/review runtime              | Batch04 / B04-05          | Batch05 确认 frozen loader、no-action guard、runner、metrics、report hash、API binding。 |
| No-action semantics guard            | Batch04 / B04-02 + B04-05 | Batch05 确认 Agent/API/review/report 都不会输出交易动作。                                |

### 6.6 Batch04 完成标准

Batch04 不能只交 shell。完成时必须满足：

- API 不再只有 `/health`，至少有一个真实 read-only readiness/source endpoint。
- Agent 不再只是 policy 文档，至少有一个可运行 read-only tool。
- Frontend 不再只是空壳，至少有一个绑定 API 的真实页面/面板。
- Notification/Report 不再只是 schema，至少有一条 event-to-report/log 流程。
- Backtest/Review 不再是 blank engine，至少有一个可执行 read-only scenario 和 report artifact。
- 所有输出都禁止 buy/sell/order/add/reduce/position 等动作语义。

---

## 7. Batch05 / Round5：安全、集成、发布闭环

### 7.1 执行入口

```text
docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/
```

核心文件：

```text
BATCH_05_TASK_CARD_MANIFEST.md
BATCH_05_COORDINATOR_PLAYBOOK.md
BATCH_05_HARDENING_RULES.md
B05_01_security_ci_release_gate.md
B05_02_integration_and_resource_smoke.md
B05_03_release_manifest_and_package_cleanup.md
```

历史 loose cards `031`–`036` 只作为输入，不是默认执行入口。

### 7.2 业务目标

Round5 不补功能，只做发布裁判。

如果 3H、3G、Round4 有东西没做完，Round5 只能：

1. 阻断发布；或
2. 写入 release manifest 的 `open_deferred_items` / `known_limitations`，并写清 owner、phase、closure test、source limitation、route/evidence status。

Round5 不能偷偷新增 adapter、API、Agent、Frontend、Backtest 功能来遮盖前面没完成的事实。

### 7.3 串行 / 半并行安排

```text
Round3F-R + 3G + 3H + Batch04 产物稳定
  ↓
B05-01：Security CI release gate 先启动
  ↓
B05-02：Integration/resource smoke 在 runtime artifacts 稳定后启动
  ↓
B05-03：Release manifest/package cleanup 最后汇总
```

说明：如果 B05-01 和 B05-02 的输入都已经稳定，二者可以在不同文件锁下并行推进；但 B05-03 永远最后，不能提前写乐观 release manifest。

### 7.4 原始任务卡对应关系

| 分支        | Canonical 任务卡                                 | 历史 loose card 输入                                                                                                        | 能否并行                                        | 必须交付                                                                                              |
| ----------- | ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Security    | `B05_01_security_ci_release_gate.md`             | `033_implement_security_and_boundary_tests.md`, `034_implement_docs_consistency_check.md`                                   | 最先；可与稳定后的 B05-02 分工并行              | secret/dependency/security scan、boundary tests、CI gate、docs consistency input。                    |
| Integration | `B05_02_integration_and_resource_smoke.md`       | `031_implement_integration_smoke_tests.md`, `032_implement_resource_limit_tests.md`                                         | 等 runtime artifacts 稳定；可与 B05-01 分工并行 | bounded integration smoke、ResourceGuard、production-equivalent smoke budget、sync/API/review paths。 |
| Release     | `B05_03_release_manifest_and_package_cleanup.md` | `035_implement_final_package_cleanup.md`, `036_create_final_release_manifest.md`, `034_implement_docs_consistency_check.md` | 必须最后                                        | release manifest、package cleanup、docs consistency、runbook pointers、source/write/module posture。  |

### 7.5 本批次最终确认的模块

Batch05 的核心不是“主能力开发”，而是确认所有承诺模块是否可发。

| 模块                                                  | 主能力完成批次                         | R6 确认批次 |
| ----------------------------------------------------- | -------------------------------------- | ----------- |
| Project scaffold / config / test harness              | 历史底座；release packaging 在 Batch05 | Batch05     |
| DuckDB schema / migration foundation                  | 历史底座；migration hygiene 在 Batch05 | Batch05     |
| Sync orchestration production-equivalent smoke        | 历史底座 + 3H/3G 输入                  | Batch05     |
| ResourceGuard 全链路发布确认                          | 3H + Batch04 + Batch05                 | Batch05     |
| Security / release packaging                          | Batch05                                | Batch05     |
| Release manifest / package cleanup / docs consistency | Batch05                                | Batch05     |
| 所有 3F-R / 3G / 3H / Batch04 模块的最终发布状态      | 各自主批次                             | Batch05     |

---

## 8. 全模块生产级闭环表

这张表是总闭环图。每个模块都必须在这里出现；Round5 之后不能还有“没人负责的半成品”。

| 模块                                           | 当前主要缺口                                                | 主能力完成批次                                    | 最终 R6 确认批次 | 必须交付什么                                                                           |
| ---------------------------------------------- | ----------------------------------------------------------- | ------------------------------------------------- | ---------------- | -------------------------------------------------------------------------------------- |
| 项目骨架 / config / test harness               | 需要 release package 与最终测试目录一致性                   | Batch05                                           | Batch05          | package check、test catalog、docs consistency、release manifest。                      |
| DuckDB schema / migration foundation           | 需要 migration hygiene 与 drift gate                        | Batch05                                           | Batch05          | schema drift check、migration registry、release manifest。                             |
| WriteManager + DbValidationGate                | 需要真实 clean-write 证明                                   | Batch3G                                           | Batch05          | sandbox rehearsal、limited production proof、rollback/no-mutation evidence。           |
| RawStore / FileRegistry / fetch_log            | 需要绑定每个 in-scope source                                | Batch3H                                           | Batch05          | source_fetch_id、content_hash、schema_hash、fetch_log、replay/sandbox evidence。       |
| ResourceGuard / performance budget             | 需要覆盖 adapter/API/review/sync 全链路                     | Batch3H + Batch04 + Batch05                       | Batch05          | 每条真实路径都有 caps、拒绝大查询、bounded integration smoke。                         |
| Source registry / capability / route planner   | 需要所有 source 最终状态                                    | Batch3H                                           | Batch05          | READY_WITH_EVIDENCE 或 ADR_DISABLED_OUT_OF_SCOPE；route tests。                        |
| Provider catalog / auth-license posture        | 需要覆盖 active/proposed source                             | Batch3F-R + Batch3H                               | Batch05          | provider metadata、license/auth、resource caps、release limitation。                   |
| DataSourceService facade                       | 需要真实 source-specific ports                              | Batch3H                                           | Batch05          | API/Agent/Sync 都通过 service boundary，不直接读 YAML/DB/adapter。                     |
| Vendor adapters / provider fetch ports         | 大量 source 仍未真实闭合                                    | Batch3H                                           | Batch05          | 每个 source adapter/evidence 或 ADR-disabled。                                         |
| Source conflict validator                      | 需要接入真实 source/domain                                  | Batch3H + Batch3G                                 | Batch05          | conflict report 进入 write/readiness/release gate。                                    |
| Data health engine                             | profile 不完整                                              | Batch3F-R / R3FR-02                               | Batch05          | EasyXT-style profiles、pass/warn/fail/blocked、profile-specific issue detail。         |
| `qmd data` CLI                                 | health command 不能是 placeholder                           | Batch3F-R / R3FR-06 + Batch3G limited-write flows | Batch05          | `qmd data health` 真实 read-only 输出；limited-write operator flow 不越权。            |
| Data quality validator profiles                | 需要 profile-level business checks                          | Batch3F-R                                         | Batch05          | OHLCV、required fields、calendar gap、stale、outlier、volume anomaly。                 |
| Sync orchestration                             | 需要 production-equivalent smoke                            | Batch05                                           | Batch05          | incremental/backfill/reconcile/data-quality bounded smoke，经 DataSourceService。      |
| Layer1 axes                                    | staged source 需要真实官方/宏观绑定                         | Batch3H / R3H-05                                  | Batch05          | official/macro evidence binding 或 ADR narrowed scope。                                |
| Layer2 sensors                                 | staged fixture 需要真实 market/CN/validation source         | Batch3H / R3H-05                                  | Batch05          | cross-asset sensor real source envelope。                                              |
| Layer3 chains                                  | staged chain 需要真实 CN/industry-chain evidence            | Batch3H / R3H-05                                  | Batch05          | chain source evidence 或 ADR narrowed scope。                                          |
| Layer4 markets                                 | CN_A staged fixture 需要真实 market/calendar/breadth source | Batch3H / R3H-05                                  | Batch05          | market structure source binding 或 ADR narrowed scope。                                |
| Layer5 evidence                                | 需要全链路 evidence lineage                                 | Batch3H / R3H-05                                  | Batch05          | source_fetch_id/content_hash/schema_hash/limitation chain。                            |
| Sandbox clean write / limited production entry | 只有规划和 contract 不够                                    | Batch3G                                           | Batch05          | rehearsal → audit → limited write；或 release 禁用说明。                               |
| API backend                                    | placeholder shell 不够                                      | Batch04 / B04-01                                  | Batch05          | authenticated read-only endpoint、pagination、budget、no free SQL、no write。          |
| Agent layer                                    | 需要真实 policy-guarded read-only tool                      | Batch04 / B04-02                                  | Batch05          | tool policy、prompt/tool rejection、evidence-bound output、no action。                 |
| Frontend dashboard                             | 用户会设计最终 UI，但 API-bound 产品路径要完成              | Batch04 / B04-03                                  | Batch05          | API-bound page/panel、loading/empty/error states、contract alignment。                 |
| Notifications / reports                        | 不能只有 schema                                             | Batch04 / B04-04                                  | Batch05          | event → report/notification_log、dedup/cooldown/evidence refs。                        |
| Backtest / review                              | 不能从零写 blank engine                                     | Batch04 / B04-05                                  | Batch05          | frozen loader、no-action guard、review runner、metrics、report artifact、API binding。 |
| Backtest/review metrics                        | 不能 metric-only 微切片                                     | Batch04 / B04-05                                  | Batch05          | metrics 从 QMD-owned review series 计算，连到可运行 scenario。                         |
| No-action semantics guard                      | 需要覆盖 Agent/API/review/report                            | Batch04 / B04-02 + B04-05                         | Batch05          | 交易动作语义拒绝测试、output validator。                                               |
| Reference adoption governance                  | 需要任务卡本地化与 license/runtime guard                    | Batch3F-R / R3FR-01                               | Batch05          | 无中央 executable inventory、无 `参考项目/**` runtime import、无 unsafe copy。         |
| Release/security packaging                     | 只有规划                                                    | Batch05                                           | Batch05          | security CI、integration smoke、manifest、package cleanup、runbooks。                  |
| 文档/规划/任务入口一致性                       | loose cards 容易误导                                        | R3FR-01 + Batch05                                 | Batch05          | canonical entrypoints、redirect notes、docs index、release manifest 一致。             |

---

## 9. 数据源生产级闭环表

所有目标 source 必须在 Batch3H 关闭，Round5 确认发布状态。

| 数据源组           | Source                                                                                                                        | 主能力完成批次 | 生产级结论要求                                                                                                |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------- | -------------- | ------------------------------------------------------------------------------------------------------------- |
| 官方宏观/披露      | `fred`, `us_treasury`, `sec_edgar`, `cftc_cot`, `bis`, `world_bank`                                                           | R3H-01         | 每个 source adapter/gate/replay/route/evidence 或 ADR_DISABLED_OUT_OF_SCOPE；Layer1/Layer5 绑定。             |
| 市场/加密          | `alpha_vantage`, `stooq`, `yahoo_finance`, `deribit`, `coingecko`                                                             | R3H-02         | 每个 source 有 auth/license/route/evidence；聚合/validation 源不能冒充 primary。                              |
| 中国市场           | `baostock`, `akshare`, `cninfo`, `tdx_pytdx`, `mootdx`, `eastmoney`, `sina_finance`, `ths_ifind`, `qmt_xtdata`, `qmt_xqshare` | R3H-03         | 每个 source primary/validation/authorization-disabled/ADR-disabled 姿态明确；QMT/iFinD/xqshare 不得默认启用。 |
| 预测市场/网页证据  | `kalshi`, `polymarket`, `web_search`                                                                                          | R3H-04         | 只能 probability/evidence/manual-review；不得写 factual clean table。                                         |
| 全部 source 总审计 | 所有 above source                                                                                                             | R3H-05         | Round4 只能消费 R3H final decision，不得消费 proposed-disabled 假完成。                                       |

---

## 10. 进入下一批次的门禁

| 从哪里到哪里     | 必须满足什么                                                                                                                                       |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| 历史底座 → 3F-R  | 以 3F/3V/3E/3D 等已有产物作为输入；当前新开工从 3F-R canonical folder 开始。                                                                       |
| 3F-R → 3G        | 3F-R 完成，或所有 open 3F-R 项都有 ADR defer + owner + deferred phase + closure gate；R3FR-01 必须已重跑；不得存在中央 executable inventory 风险。 |
| 3G → 3H          | sandbox rehearsal/audit/limited write 状态清楚；写入链路没有污染生产库风险；candidate source 的写入边界清晰。                                      |
| 3H → Round4      | R3H-05 输出 PASS 或 WARN_WITH_NARROWED_SCOPE_ADR；所有 target source 都 READY_WITH_EVIDENCE 或 ADR_DISABLED_OUT_OF_SCOPE。                         |
| Round4 → Round5  | API、Agent、Frontend、Notification、Backtest/Review 都有真实 read-only 垂直闭环，不是 shell/schema/policy-only。                                   |
| Round5 → Release | security CI、integration/resource smoke、release manifest、package cleanup、runbooks 全部通过；没有隐藏 blocker。                                  |

---

## 11. 执行者开工前检查清单

每次开工前，执行者必须确认：

1. 我是不是从 canonical batch folder 和 canonical task card 开始？
2. 我是不是误用了 loose historical card？如果是，停止，回到 manifest。
3. 我是不是把 `PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` 当工单用了？如果是，停止，回到任务卡。
4. 这条分支是否真的能并行？会不会和别的分支改同一 shared file？
5. 如果不能并行，路线图和 playbook 是否写成串行 gate？
6. 涉及参考项目时，任务卡里是否写清 reference paths、borrowable logic、forbidden semantics、QMD target files、tests、not-done conditions？
7. 涉及数据源时，是否先走 SourceRoutePlan / DataSourceService，而不是直接 adapter fetch？
8. 涉及数据时，是否有 fetch_log、source_fetch_id、content_hash、schema_hash？
9. 涉及写入时，是否有 ResourceGuard、DataHealth、SourceConflict、WriteManager、DbValidationGate？
10. 涉及 API/Agent/Frontend/Report/Review 时，是否 read-only、no free SQL、no write、no trading action？
11. 任务完成后，是否更新 tests、contract coverage、test catalog、docs index 或 release manifest？
12. 如果不能完成，是否写 ADR narrowed scope 或 release limitation，而不是模糊写“以后再补”？

---

## 12. 最终发布标准

Round5 完成后，本项目只能有两类状态：

| 状态                                             | 含义                                                                                          |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------- |
| `R6_FULL_PRODUCTION_STABLE`                      | 承诺范围内的模块已经可发布、可运行、可审计、可限制、可回滚/可禁用。                           |
| `ADR_DISABLED_OUT_OF_SCOPE` / release limitation | 当前产品明确不承诺该能力或 source，并且已写清原因、影响、owner、closure test 和后续关闭条件。 |

不允许出现第三类状态：

```text
“看起来差不多”
“只差一点”
“后面再补”
“registry 已经有了所以算完成”
“前端/API 包一下就算生产级”
“Round5 再顺手补功能”
```

最终 release manifest 必须把以下内容串起来：

- 每个模块的 R6 / limitation 状态。
- 每个 source 的 READY / ADR-disabled / disabled 状态。
- 每个模块对应的任务卡和测试命令。
- 每个已知限制、owner、closure gate。
- rollback / disable / resource cap / security posture。

只有这样，这张总施工图、各任务卡、测试证据和发布清单才算完整闭环。
