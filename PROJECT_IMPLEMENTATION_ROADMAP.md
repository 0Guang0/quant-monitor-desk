# Project Implementation Roadmap

> **Purpose:** 从当前 `integration/round3-batch3f` 最新状态出发，只规划尚未完成的代表任务，避免执行者继续被旧 Round3 历史批次干扰。  
> **Status checkpoint:** `integration/round3-batch3f` @ `d0393153`（Batch 3F / Batch6 data governance **DONE** — 八路 integration merge + full pytest green）；**下一入口 Round 3F-R（Reference Adoption Refactor）**，先处理成熟参考项目采纳与重复轮子重构，再进入 Round 3G。  
> **This file supersedes forward planning in:** `ROUND3_BATCH_IMPLEMENTATION_MAP.md` for **future work only**. 旧 map 保留作历史追踪与证据索引；后续新任务优先读本文件。  
> **First executable batch entrypoint:** `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/README.md`.

---

## 0. 当前业务状态（一句话）

系统已经完成五层建模的 staged 内核：Layer1–Layer4 的主要结构、Layer5 foundation、数据源路由、安全门禁、read-only data health、小样本真实数据 staged pilot 都已落地；但还没有正式进入生产真实数据入库，也没有 production clean write、完整 Layer5 evidence chain、Batch6 数据治理/迁移/CLI/backfill、API/前端/通知产品化。

---

## 1. 全局执行规则（所有后续 Round 必须遵守）

### 1.1 执行者启动前必须读

- `PROJECT_IMPLEMENTATION_ROADMAP.md`（本文件）
- `MIGRATION_MAP.md`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`
- `docs/RESOLVED_ISSUES_REGISTRY.md`
- `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`
- `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`
- `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`
- `docs/quality/staged_acceptance_policy.md`
- `docs/quality/production_live_pilot_policy.md`
- `.trellis/spec/guides/complex-task-planning-protocol.md`
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`

### 1.2 必须使用的工程纪律

所有正式代码任务必须遵守：

- `/to-issues`：Plan 阶段必须拆成 tracer-bullet vertical slices，每个 issue 都要能独立验证、独立产出 evidence。
- `/tdd`：正式实现前先写或补 RED test，再实现 GREEN。
- `/ponytail` full：控制文件体积、函数复杂度、重复路径、单一权威入口。
- `/karpathy-guidelines`：代码保持简单、直接、可读、可调试。
- `/testing-guidelines`：测试必须覆盖行为和业务语义。

测试要求：

- 新增或修改测试必须用 docstring 或就近注释说明：覆盖范围、测试对象、目的/目标。
- 不得为了通过测试而改变测试目的/目标。
- 可以修复测试表达方式，但必须保留原始验证目标。
- 任何代码修复后必须跑完整测试；若因环境限制无法运行，必须记录命令、错误和风险。

### 1.3 全局禁止事项

- 不得默认启用 production-live。
- 不得默认启用 production clean write。
- 不得全市场 / 全历史 / 分钟级全量扫描作为默认行为。
- 不得把 staged / fixture / sandbox 证据宣传为 production-ready。
- 不得把 AkShare validation-only 提升为 Primary。
- 不得把 TDX/QMT/xqshare/Yahoo/FRED 默认开启。
- 不得绕过 `DataSourceService` / `SourceRoutePlanner` / `WriteManager` / `DbValidationGate` / `ResourceGuard`。
- 不得把 Agent 文本当事实源。
- 不得让 Layer2–5 默认复制 Layer1 的完整标准化字段。

### 1.4 成熟参考项目采纳规则（避免未来批次重复造轮子）

从 Round 3F-R 开始，未来任务不得默认从零实现下列能力；必须优先读取并评估本仓库 `参考项目/` 下的成熟项目，再按 QMD 契约改造落地：

| 能力域                               | 不得从零写的内容                                                                                     | 必须优先参考                                                                                                        | QMD 落位方式                                                                                  | 禁止边界                                                                        |
| ------------------------------------ | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Data health / OHLCV                  | 交易日缺失、空值、非正价格、OHLC 关系、异常涨跌幅、成交量异常、完整性报告                            | EasyXT `data_manager/data_integrity_checker.py`、`smart_data_detector.py`                                           | `backend/app/ops/data_health_profiles/**` + `specs/contracts/data_quality_rules.yaml`         | 不保留硬编码 DB/table、SQL 拼接、`sys.path.insert`、production write            |
| TDX / pytdx provider                 | TDX 连接管理、server list、代码解析、pytdx dependency error、daily/index/security-list provider 细节 | EasyXT `easy_xt/realtime_data/providers/tdx_provider.py`；若后续引入 Python TDX extractor 仓库，先做 license matrix | `backend/app/datasources/fetch_ports/tdx_pytdx_port.py` + QMD authorization/caps/raw evidence | 不自写底层 TDX 协议；不默认启用；不全市场/全历史/分钟线默认；不 silent fallback |
| Backtest / review lifecycle          | DuckDB 本地数据加载、回测 CLI 形态、报告 builder、API allow/deny mapping                             | JQ2PTrade `ptrade_local/**`、`api_mapping.json`；EasyXT `easyxt_backtest/**` performance/report ideas               | Round4 `backend/app/review/**` / review sandbox / no-action guard                             | 不复制交易 API、自动下单、任意策略执行、broker connection                       |
| Provider plugin / catalog            | provider metadata、optional extras、auth/cost/terms/quality role taxonomy                            | OpenBB `openbb_platform/providers/` 仅作架构参考；`agents-for-openbb` 仅未来 Agent/UI reference                     | `specs/datasource_registry/provider_catalog.yaml` + `provider_catalog.py`                     | OpenBB 主仓库 AGPLv3 不得复制 runtime source                                    |
| Agent analysis / dashboard artifacts | analyst role taxonomy、reasoning/report widgets、charts/tables/PDF/dashboard examples                | TradingAgents / TradingAgents-astock / agents-for-openbb，先 license review                                         | Round4 Agent/UI 任务卡显式采纳                                                                | 不把 Agent 文本当事实源；不输出自动交易动作                                     |

未来新批次若要从零实现上述能力，必须先写 ADR 说明：已读取哪些参考项目、为何不能改造复用、替代方案如何仍满足 QMD 契约。没有 ADR，不得派工从零实现。

### 1.5 完成度与反过度工程规则

根目录 `MODULE_COMPLETION_RATING.md` 是当前实现完成度快照，只用于规划、任务卡、审计；设计文档、契约、架构设计、规则定义仍描述完整成品形态，不在其中标注当前完成度。

每个模块或重大功能最多用三个实施批次达到完整生产可用稳定形态：第一批至少交付真实最小垂直闭环，第二批完成声明范围的生产可用主体，第三批只允许做硬化、回归、发布 gate。已有部分实现的模块，其下一个实施批次必须直接补齐主承诺范围，不能继续拆成“加一个指标/加一个字段/加一个 guard/加一个 registry note”的微切片。

---

## 2. 后续 Round 总览

| Round          | 名称                                           | 业务目标                                                                                                        | 合并策略                                                                                                 |
| -------------- | ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| **Round 3D**   | Evidence Chain & Model Input Closure           | 补完整 Layer5 证据链，并把五层模型第一批真实输入白名单定清楚                                                    | `023` 主线串行；输入白名单和 lineage 债务可并行                                                          |
| **Round 3E**   | Controlled Real Source Pilots                  | 以 sandbox/raw/staging 方式接入 FRED、TDX、baostock/cninfo/akshare 扩样                                         | 多源分支并行，但禁止 production write                                                                    |
| **Round 3V**   | Verified Audit Cleanup & Routing               | 将 verified audit report 中属实 `VR-*` 问题按底座/模型/ops/产品化/release 分流并补任务卡                        | 3V.1 先行；3V.2 核对后并行；不得混入 production write                                                    |
| **Round 3F**   | Batch6 Data Governance & Ops                   | 做迁移、`qmd data`、source health、backfill/reconcile、packaging/hygiene                                        | 按子系统并行；最后统一 gate                                                                              |
| **Round 3F-R** | Reference Adoption Refactor                    | 在 3G 前用 EasyXT/JQ2PTrade/OpenBB 等成熟参考项目重构薄自研轮子，并把未来批次不得从零写的能力写入规划           | 先 task-local reference rules/license，再 data health+CLI、TDX、provider/backtest planning，最后 cleanup |
| **Round 3G**   | Sandbox Clean Write & Limited Production Entry | 先沙盒 clean-write 彩排，再极小范围 production clean write                                                      | 严格串行 gate，不得并行跳过审计；必须等 3F-R 完成或 ADR defer                                            |
| **Round 4**    | API, UI, Notifications                         | 让后端能力变成用户可见 API、dashboard、通知中心；Backtest/Agent/UI 不得从零造轮子，必须先执行 §1.4 参考采纳规则 | API 与前端可分批并行                                                                                     |
| **Round 5+**   | Security, Scale, Release Hardening             | 安全 CI、性能预算、生产运维闭环                                                                                 | 生产发布前必须完成                                                                                       |

---

# Round 3D — Evidence Chain & Model Input Closure

## Round 3D 业务目标

让系统从“有 Layer1–4 staged 模型”升级为“每个模型输出都能回答：这个结论来自哪些数据、哪个源、哪个 fetch、哪个 hash、有没有冲突、是否经过人工复核”。

当前最关键的未完成项：完整 `023` Layer5 evidence chain。

---

## Batch 3D.1 — Full Layer5 Evidence Chain（串行主线） — **DONE** @ `376e30e6`

**分支：** `feature/round3-023b-evidence-chain-full`（已 FF 合入 `master`）  
**并行性：** 串行；不要与会修改 Layer5 contract / evidence chain / manual review semantics 的分支并行合并。  
**前置：** `022` + `023A` 已在主线。

### 任务

| Task ID      | 任务                                                  | 业务目的                                                          | 范围                                                                      | 禁止范围                       | Gate                                                  |
| ------------ | ----------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------ | ----------------------------------------------------- |
| `R3D-023-01` | Instrument registry + evidence identity               | 让每个股票、ETF、期货、宏观指标、公告证据都有稳定身份             | `instrument_registry`、instrument/evidence ref、source hash/fetch id 字段 | 不接 live source、不做生产写入 | identity uniqueness tests；source hash/fetch id tests |
| `R3D-023-02` | Bars / events / financials / valuation evidence model | 让 Layer5 能承载价格、事件、财报、估值证据                        | schema/model/builder/test skeleton；优先 staged inputs                    | 不做全量历史 bar，不做正式回填 | model validation tests；no-future-data tests          |
| `R3D-023-03` | Evidence chain builder                                | 能把 Layer3/4/5 证据串起来，支撑“为什么这么判断”                  | evidence chain node/edge、upstream snapshot ids、manual review flags      | Agent 文本不得作为事实源       | chain trace tests；agent-text-not-fact-source tests   |
| `R3D-023-04` | Conflict UX decision for `R3-PARTIAL-4`               | 明确 severe conflict 是进 manual review 还是 instant severe queue | ADR + pytest for chosen path                                              | 不做完整人工审核 UI            | UX ADR + conflict path test                           |
| `R3D-023-05` | Adapter/storage port boundary if touched              | 避免 evidence path 继续依赖具体 storage 类                        | 只在 Layer5 evidence path 需要时做最小 port injection                     | 不重构全部 adapter             | module boundary test                                  |

### 必读索引

- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/023_implement_layer5_evidence_chain.md`
- `docs/modules/layer5_security_evidence.md`
- `specs/contracts/layer5_evidence_contract.yaml`
- `specs/contracts/snapshot_lineage_contract.yaml`
- `docs/modules/data_validation_and_conflict.md`
- `docs/modules/write_manager.md`
- `docs/AUDIT_DEFERRED_REGISTRY.md` rows: `R3-PARTIAL-4`, `R2-RISK-2`, `ADV-R3X-LINEAGE-001`, `R3Y-LINEAGE-VR-001`
- `backend/app/layer5_evidence/`
- `backend/app/layer3_chains/`
- `backend/app/layer4_markets/`
- `tests/test_layer5_evidence_foundation.py`

### 完成标准

- Layer5 full evidence chain 有代码、测试、merge gate。
- Layer3/4 snapshot 能关联到 evidence refs。
- 冲突/人工复核路径有明确 ADR 和测试。
- 不声明 production-live readiness。

---

## Batch 3D.2 — Five-Layer Model Input Whitelist — **DONE** @ `b09a3ca6`

**分支：** `chore/round3-model-input-whitelist`（已合入 `integration/round3-batch01` → `master`）  
**并行性：** 可并行；只改 docs/spec/config，不改 production fetch。  
**业务目的：** 明确系统不是全市场全量接入，而是先围绕五层模型需要的数据做白名单接入。

### 任务

| Task ID     | 任务                                | 业务目的                                                                            | 范围                                                         | 禁止范围                | Gate                               |
| ----------- | ----------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------ | ----------------------- | ---------------------------------- |
| `R3D-WL-01` | Layer1 P0 macro source whitelist    | 明确第一批 FRED/macroeconomic series                                                | `DGS10`, `T10Y3M`, `VIXCLS`, `SP500`, `DFII10` 等 P0/P1 分级 | 不实现 FRED fetch       | whitelist schema + doc tests       |
| `R3D-WL-02` | Layer2 cross-asset source whitelist | 明确 VIX/HYG/Copper/ETF/futures 等哪些是 display-only、eligible_for_model、deferred | Layer2 registry/source status mapping                        | 不接 live TDX/QMT/Yahoo | fixture vs production status tests |
| `R3D-WL-03` | Layer3 anchor source whitelist      | 明确产业链 P0 anchors 哪些已有 source_keys，哪些 needs_source                       | Layer3 anchor/source plan                                    | 不做全行业自动抓取      | source_validation_status coverage  |
| `R3D-WL-04` | Layer4 market source whitelist      | 明确 CN_A market breadth/calendar 第一批真实输入                                    | CN_A first, US/HK/FUT/options deferred                       | 不做全市场 breadth      | staged/production status matrix    |
| `R3D-WL-05` | Layer5 instrument source whitelist  | 明确第一批股票/ETF/期货/公告/财报证据源                                             | baostock/cninfo/FRED first；TDX validation-only candidate    | 不做全股票池            | cross-layer input map review       |

### 建议输出文件

- `specs/model_inputs/layer1_source_whitelist.yaml`
- `specs/model_inputs/layer2_source_whitelist.yaml`
- `specs/model_inputs/layer3_anchor_source_plan.yaml`
- `specs/model_inputs/layer4_market_source_plan.yaml`
- `specs/model_inputs/layer5_instrument_source_plan.yaml`
- `docs/quality/model_input_readiness_matrix.md`

### 完成标准

- 每个输入有：业务用途、source_id、domain、operation、Primary/Validation/Fallback、production-ready/staged-only/deferred 状态、gate。
- 执行者能据此知道下一批真实数据接哪些，不会误接全市场。

---

## Batch 3D.3 — Lineage & Layer3 Hygiene Debt — **PARTIAL HYGIENE DONE** @ `06bcfde1`; registry closure moved to Round 3F

**分支：** `fix/round3-batch6-lineage-and-layer3-hygiene`（已合入 `integration/round3-batch01` → `master`）  
**并行性：** 可与 3D.1 并行，但不得修改同一 Layer5 core file；若冲突，以 3D.1 为主。  
**业务目的：** 让 staged lineage 更接近真实生产证据链要求，避免未来 sandbox clean write 使用合成 ID 冒充真实 evidence。  
**最新状态说明：** 该批次完成的是 Batch 01 hygiene / negative tests / staged guardrail；`ADV-R3X-LINEAGE-001`、`R3Y-LINEAGE-VR-001`、`R3-B6-021-O-01`、`R3-B6-021-O-02` 在 `UNRESOLVED_ISSUES_REGISTRY.md` 与 `ROUND3_WAVE_B_PENDING_FIX_REGISTRY.md` 仍属 Batch 6 owner。前向执行不得把 3D.3 误读为 registry 全闭合；对应关闭任务集中在 Round 3F.6。

### 任务

| Task ID       | 任务                                              | 来源                                        | 范围                                                   | Gate                     |
| ------------- | ------------------------------------------------- | ------------------------------------------- | ------------------------------------------------------ | ------------------------ |
| `R3D-LIN-01`  | `ADV-R3X-LINEAGE-001` full L3/L4 snapshot lineage | `ROUND3_WAVE_B_PENDING_FIX_REGISTRY.md`     | snapshot lineage registry row + tests                  | lineage pytest           |
| `R3D-LIN-02`  | `R3Y-LINEAGE-VR-001` Layer2 VR/fetch_log binding  | AUD-05                                      | sandbox rehearsal 不得用 synthetic IDs 冒充 VR binding | negative test            |
| `R3D-L3-01`   | `R3-B6-021-O-01` malformed `bars[]` fail-closed   | `ROUND3_BATCH6_021_PENDING_FIX_REGISTRY.md` | Layer3 live manifest/bar schema validation             | malformed fixture fails  |
| `R3D-L3-02`   | `R3-B6-021-O-02` deterministic rebuild full tuple | same                                        | strengthen deterministic rebuild test                  | full row tuple assertion |
| `R3D-TEST-01` | `R3Y-TEST-DEPTH-001` runtime-strong test depth    | AUD-07                                      | per-ID runtime tests or explicit wont-fix ADR          | test-depth report        |

---

# Round 3E — Controlled Real Source Pilots

## Round 3E 业务目标

把真实数据源接入从“staged pilot v2 的小样本”推进到“按模型白名单进行受控扩样”，但仍然不进入 production clean write。

核心原则：真实源可以接，正式生产库不能写；所有数据先进入 raw/staging/sandbox，并带 evidence。

---

## Batch 3E.1 — FRED-only Authorized Sandbox Pilot — **DONE** @ `9ae91648`

**分支：** `feature/round3-fred-authorized-sandbox-pilot`（已合入 `integration/round3-batch01` → `master`）  
**并行性：** 可与 TDX probe 并行；不得与 production clean write 并行。  
**业务目的：** 五层模型大量依赖美股/宏观/FRED，必须补上 FRED 真实源，但先只做 sandbox pilot。

### 任务

| Task ID       | 任务                                  | 范围                                                         | 禁止范围                         | Gate                                   |
| ------------- | ------------------------------------- | ------------------------------------------------------------ | -------------------------------- | -------------------------------------- |
| `R3E-FRED-01` | Add `fred` source registry/capability | `macro_daily_series` 或等价 domain；P0 series only           | 不全量 FRED                      | registry/capability tests              |
| `R3E-FRED-02` | `FredFetchPort` raw-only fetch        | `DGS10`, `T10Y3M`, `VIXCLS`, `SP500`, `DFII10`               | 不写 clean table                 | mocked + optional authorized live test |
| `R3E-FRED-03` | FRED staged pilot evidence            | raw manifest、content_hash、source_fetch_id、as_of_timestamp | 不跑全历史                       | no-mutation proof                      |
| `R3E-FRED-04` | Data health checks for FRED           | stale/missing/value/date/vintage/update-time checks          | 不做 full source health table    | read-only health report                |
| `R3E-FRED-05` | Reconcile `B2.5-O-05`                 | 只在 FRED-only evidence 通过后关闭或继续 re-defer            | 不用 AkShare macro 替代关闭 FRED | registry update + tests                |

### 业务解释

FRED 是主干宏观水源。现在模型图纸里大量写了 FRED，但生产管道还没接上。这个批次只是先接一个小水管进测试水箱，确认水质、字段、日期、修订行为，不让它流进正式水库。

### 完成标准

- FRED P0 series 可 raw/staging 获取或明确记录授权/网络失败 taxonomy。
- `B2.5-O-05` 不再含糊：要么有 FRED-only sandbox proof，要么继续带 owner/test re-defer。
- 不产生 production-live readiness claim。

---

## Batch 3E.2 — TDX Manual Probe & Validation-only Candidate — **DONE** @ `01ad6a07`

**分支：** `debt/round3-tdx-manual-probe`（已合入 `integration/round3-batch01` → `master`）  
**并行性：** 可与 FRED pilot 并行；不得与 production clean write 并行。  
**业务目的：** 确认 TDX / pytdx 是否能作为 A 股 security list、指数日线、日线验证源候选。

### 任务

| Task ID      | 任务                                       | 范围                                    | 禁止范围         | Gate                    |
| ------------ | ------------------------------------------ | --------------------------------------- | ---------------- | ----------------------- |
| `R3E-TDX-01` | Manual authorization gate                  | host/port/symbol/max_rows/user approval | 不允许无授权联网 | authorization test      |
| `R3E-TDX-02` | Raw-only probe: one equity daily bar       | 1 个股票，最近 30 天                    | 不写 DB          | raw evidence + taxonomy |
| `R3E-TDX-03` | Raw-only probe: one index daily bar        | 1 个指数，最近 30 天                    | 不设 Primary     | raw evidence            |
| `R3E-TDX-04` | Small security list probe                  | capped rows                             | 不全量市场       | row cap proof           |
| `R3E-TDX-05` | Compare vs baostock/akshare where possible | validation-only comparison              | 不自动 fallback  | conflict/defer report   |

### 业务解释

TDX 不是现在直接接 production 的源。它先像候选供应商试送样品：能不能连上、字段稳不稳定、和 baostock/akshare 差多少。先 validation-only，不当主源。

### 完成标准

- TDX 仍 `enabled_by_default=false`。
- TDX 仍 validation-only candidate。
- Layer2 production source 禁止规则不放松。
- 所有 live call 都有授权、上限和 no-mutation proof。

---

## Batch 3E.3 — baostock / cninfo / akshare Model-driven Expansion v3 — **DONE** @ `1a099e8d`

**分支：** `feature/round3-real-data-staged-pilot-v3`（已合入 `integration/round3-batch01` → `master`）  
**并行性：** 可与 3E.1/3E.2 并行，但合并前要统一 source readiness matrix。  
**业务目的：** 把 v2 的小样本扩成更贴近模型输入白名单的真实数据样本。

### 任务

| Task ID      | 任务                          | 范围                                            | 禁止范围                             | Gate                                    |
| ------------ | ----------------------------- | ----------------------------------------------- | ------------------------------------ | --------------------------------------- |
| `R3E-SP3-01` | baostock A 股日线扩样         | 5–20 个 model-input symbols，30–120 个交易日    | 不全 A 股，不 production clean write | raw/staging manifest + health PASS/WARN |
| `R3E-SP3-02` | cninfo metadata 扩样          | model-input symbols，公告/披露 metadata         | 不下载全量 PDF                       | metadata schema/URL/source tests        |
| `R3E-SP3-03` | akshare validation-only retry | 只用于 baostock 对照                            | 不作为 Primary                       | taxonomy + validation-only guard        |
| `R3E-SP3-04` | source conflict dry-run       | baostock vs akshare aligned samples             | 不自动覆盖 clean table               | conflict summary                        |
| `R3E-SP3-05` | route/status/readiness matrix | selected/disabled/validation/user-auth coverage | 不改 default enablement              | matrix test                             |

### 完成标准

- 证明本系统是 model-driven source ingestion，而不是 full-market ingestion。
- 每个 source/domain 都有 close/retry/re-defer 结论。
- 仍然 staged/raw/sandbox-only。

---

## Batch 3E.4 — Read-only Data Health v2 — **DONE** @ `dd5fda5f`

**分支：** `feature/round3-readonly-data-health-v2`（已合入 `integration/round3-batch01` → `master`）  
**并行性：** 可在 3E pilot 之后或并行开发 fixtures，最终合并需读取 pilots evidence。  
**业务目的：** 让系统能检查 FRED、TDX、baostock、cninfo、akshare 的 staged evidence 是否可进入下一步 sandbox clean-write rehearsal。

### 范围

- 扩展 `backend/app/ops/data_health.py`。
- 增加 FRED profile、TDX profile、source readiness report。
- 支持 model input whitelist 对照。
- 输出 `PASS/WARN/FAIL` 与 task-local evidence。

### 禁止范围

- 不写 `source_health_snapshot` clean table；那属于 Round 3F。
- 不执行 fetch。
- 不做 API/前端。

---

# Round 3V — Verified Audit Cleanup & Routing — **DONE** @ `2aeb6f0`

## Round 3V 业务目标

把 `quant_monitor_desk_verified_audit_report_2026-06-25_v3` 中已核实属实的新增 `VR-*` 问题写入项目计划，并按执行边界分批处理：底座硬化先行，Layer5/模型 schema 做核对闭环，Batch6/Round4/Round5 问题分别挂到原有后续批次，避免后续执行者反复重排批次。

Round 3V 不是 production-entry；不得启用 production clean write，不得声称 production-ready。

---

## Batch 3V.1 — Verified Audit Cleanup: Contract / Storage / Sync Hardening — **DONE**

**建议分支（六路并行，见 playbook §3.0）：**  
`fix/round3v-contract-drift-write-modes` · `fix/round3v-schema-hash-fail-closed` · `fix/round3v-rawstore-atomic-write` · `fix/round3v-sync-support-matrix-recovery` · `fix/round3v-registry-manifest-consistency`  
**协调手册：** `BATCH_3V_VERIFIED_AUDIT_CLEANUP/BATCH_3V_COORDINATOR_PLAYBOOK.md`（canonical）；索引 `docs/quality/coordination/BATCH_3V_COORDINATOR_PLAYBOOK_POINTER.md`  
**并行性：** 可与 Batch 01 后续文档收口并行；可与 Round 3F 规划并行；不得与 migration/schema 同文件分支并行提交。  
**业务目的：** 先清理会影响后续生产门禁可信度的底座问题：契约漂移、schema_hash fail-closed、RawStore 原子写、sync job support matrix、migration registry 对齐、manifest/doc 一致性。

| Task ID            | 来源           | 任务                                                          | 解决批次           | 禁止范围                              | Gate                                             |
| ------------------ | -------------- | ------------------------------------------------------------- | ------------------ | ------------------------------------- | ------------------------------------------------ |
| `R3V-B02-OPS-01`   | `VR-OPS-001`   | db-inspect contract single source of truth                    | Batch 3V.1         | 不改 DB，不联网                       | contract drift test                              |
| `R3V-B02-WRITE-01` | `VR-WRITE-001` | write_contract implemented/reserved modes                     | Batch 3V.1         | 不实现 manual_patch/replace_partition | contract/runtime parity test                     |
| `R3V-B02-DATA-01`  | `VR-DATA-001`  | CSV/Parquet schema_hash required + ValidationGate fail-closed | Batch 3V.1         | 不做 full scan，不 clean write        | schema_hash missing rejects write                |
| `R3V-B02-STOR-01`  | `VR-STOR-001`  | RawStore atomic write                                         | Batch 3V.1         | 不改 file registry semantics          | crash simulation/idempotency tests               |
| `R3V-B02-SYNC-01`  | `VR-SYNC-002`  | sync job implemented/reserved support matrix                  | Batch 3V.1         | 不裸抛 NotImplementedError            | reserved job deferred error test                 |
| `R3V-B02-SYNC-02`  | `VR-SYNC-001`  | COMPLETED/write crash-window recovery planning                | Batch 3V.1 或 3F.4 | 不做 production write                 | injected crash/recovery test or precise re-defer |
| `R3V-B02-REG-01`   | `VR-REG-001`   | migration 009 registry / coverage reconcile                   | Batch 3V.1         | 不重复实现已完成 CHECK                | registry + coverage consistency check            |
| `R3V-B02-DOC-01`   | `VR-DOC-001`   | FINAL_AUDIT_REPORT manifest/doc consistency                   | Batch 3V.1         | 不伪造审计闭环                        | manifest existence/hash check                    |

---

## Batch 3V.2 — Layer5 / Model Schema Post-audit Reconcile — **DONE**

**建议分支：** `review/round3v-layer5-model-schema-reconcile`  
**任务卡目录：** `docs/implementation_tasks/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/`（card `B03_01`）  
**协调手册：** `BATCH_3V_VERIFIED_AUDIT_CLEANUP/BATCH_3V_COORDINATOR_PLAYBOOK.md`  
**并行性：** 可与 Batch 3V.1 并行，只读核对为主；若需要改 Layer5 runtime/schema，必须独立分支并与 Round 3D done evidence 对齐。  
**业务目的：** 把审计报告中 `VR-L5-001` / `VR-MODEL-001` 与当前 post Batch 01 master 状态对齐：若已由 `376e30e6` 关闭，则更新 registry/coverage；若仍缺 schema/migration/runtime，则精确 re-defer 到 Round 3F/3G blocker。

| Task ID            | 来源           | 任务                                               | 解决批次                                | 禁止范围                                      | Gate                                      |
| ------------------ | -------------- | -------------------------------------------------- | --------------------------------------- | --------------------------------------------- | ----------------------------------------- |
| `R3V-B03-L5-01`    | `VR-L5-001`    | Layer5 full evidence chain post-audit verification | Batch 3V.2                              | 不重复实现已完成 023；不声明 production-ready | evidence-chain tests + registry reconcile |
| `R3V-B03-MODEL-01` | `VR-MODEL-001` | L3/L4/L5 designed vs implemented table matrix      | Batch 3V.2 → 3F migration if still open | 不把 designed table 当 existing table         | schema/migration/docs coverage matrix     |

---

## Verified audit items routed to later batches

| 来源                     | 归属批次               | 原因                                                                          |
| ------------------------ | ---------------------- | ----------------------------------------------------------------------------- |
| `VR-DATAHEALTH-001`      | Round 3F.3             | `source_health_snapshot` 是 Batch6 data governance，不属于 Batch 01 DH2。     |
| `VR-RG-001`              | Round 3F.5             | ResourceGuard shared cache/L3-L4 production entry guard 属 ops/perf hygiene。 |
| `VR-L1PERF-001`          | Round 3F.5             | Layer1 feature complexity 是 performance hygiene，不阻塞 Batch 3V.1。         |
| `VR-PERF-001`            | Round 3F.5 / Round 5.2 | performance budget 先由 Batch6 形成 artifact，release 阶段变 gate。           |
| `VR-API-001`             | Round 4.1              | API runtime/security 属产品化 API 阶段。                                      |
| `VR-FE-001`, `VR-FE-002` | Round 4.3              | ErrorBoundary 与页面能力属前端产品化。                                        |
| `VR-AGENT-001`           | Round 4.2              | Agent runtime policy 属 Agent/API 产品化。                                    |
| `VR-BT-001`              | Round 4.5              | Backtest/review runtime 属 Round4 产品化，不得提前混入数据治理。              |
| `VR-NOTIF-001`           | Round 4.4              | Notification/report runtime 属通知中心批次。                                  |
| `VR-SEC-001`             | Round 5.1              | gitleaks / security CI 属 release gate。                                      |

---

# Round 3F — Batch6 Data Governance & Ops

## Round 3F 业务目标

把系统从“能跑 staged pilot”推进到“具备生产数据治理工具链”：迁移、CLI、source health、reconcile/backfill、packaging、性能预算和技术债务收口。

---

## Batch 3F.1 — Migration 009 residual + 008 plan items & DB Constraint Coverage

**建议分支：** `feature/round3f-migration-residual-checks`  
**并行性：** 与 CLI/packaging 可并行，但 migration 文件只能单分支拥有。  
**最新状态说明：** `B2.5-O-06` / `A9-P1-01` / `A9-P2-02` 已由 migration 009 关闭，不得重复派工；3F.1 只处理 009 残余和 008 历史计划中仍未关闭的项目。

| Task ID      | 来源                              | 当前状态 / 任务类型 | 范围                                                                 | Gate                      |
| ------------ | --------------------------------- | ------------------- | -------------------------------------------------------------------- | ------------------------- |
| `R3F-MIG-01` | `A9-P1-01` / `A9-P2-02`           | **DONE via 009**    | Registry/coverage verify only；不得重复实现已完成 CHECK              | registry consistency      |
| `R3F-MIG-02` | `A9-P2-01` / `R2-RISK-4`          | **PARTIAL**         | `manual_review_queue.priority` CHECK: migration vs app-layer ADR     | migration test or ADR     |
| `R3F-MIG-03` | `A9-P3-01`                        | **PARTIAL**         | `fetch_log` + `manual_review_queue` rebuild explicit column list     | migration review sign-off |
| `R3F-MIG-04` | `D2-P3-1`                         | OPEN                | `registry_generation` / `removed_from_yaml_at` columns               | migration + sync tests    |
| `R3F-MIG-05` | Migration 008 plan residual       | routing task        | Map 008 plan items to 009-resolved / 3F-open / wont-fix ADR buckets  | `MIGRATION_COVERAGE.md`   |
| `R3F-MIG-06` | `R3F-BR-03` / `R3-PARTIAL-5` refs | **CLOSED B3V**      | Ensure roadmap/registry stop reopening crash-window path A as active | no duplicate task check   |

---

## Batch 3F.2 — `qmd data` CLI & Production Ops Entrypoints

**建议分支：** `feature/round3-qmd-data-cli`  
**业务目的：** 给数据运维一个统一入口，不再依赖零散脚本。

| Task ID      | 来源                              | 范围                                                                | 禁止范围                                    | Gate                              |
| ------------ | --------------------------------- | ------------------------------------------------------------------- | ------------------------------------------- | --------------------------------- |
| `R3F-CLI-01` | `R2.6-IMPL-6`                     | `qmd data` dry-run / route-preview / error_code/docs_anchor         | 不默认 live fetch                           | CLI smoke                         |
| `R3F-CLI-02` | `D2-P1-3`                         | `python -m quant_monitor.sync` 或 successor console script          | 不绕过 ResourceGuard                        | packaging smoke                   |
| `R3F-CLI-03` | `R2-GAP-1`                        | `init_db --sync-registry` 或 CI one-liner                           | 不隐式生产写入                              | init smoke                        |
| `R3F-CLI-04` | `D7-P2-2`                         | remove `sys.path.insert` smell via editable install/console scripts | 不破坏 local scripts                        | command tests                     |
| `R3F-CLI-05` | `R2.6-IMPL-8` / `R3-AUDIT-DEF-02` | user-authorized staging E2E runner/runbook for live vendor soak gap | 不默认 live fetch；不启用 QMT/Yahoo/xqshare | authorization + no-mutation proof |

---

## Batch 3F.3 — Source Health & Quality Runners

**建议分支：** `feature/round3-source-health-and-quality-runners`  
**业务目的：** 从 read-only data health 升级到生产前必需的数据健康状态跟踪。

| Task ID     | 来源                                              | 范围                                                                                                      | Gate                                                                      |
| ----------- | ------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `R3F-SH-01` | `D2-P2-1`                                         | `source_health_snapshot` table + writer                                                                   | migration + snapshot pytest                                               |
| `R3F-SH-02` | `D2-P1-1`                                         | `run_revision_audit` runner                                                                               | job type pytest                                                           |
| `R3F-SH-03` | `D2-P1-1`                                         | `run_data_quality` runner                                                                                 | job type pytest                                                           |
| `R3F-SH-04` | Data health v2                                    | source readiness rollup                                                                                   | report tests                                                              |
| `R3F-SH-05` | `VR-DATAHEALTH-001`                               | `source_health_snapshot` deferred-to-persistent transition plan                                           | no Batch01/DH2 table creation; migration task only                        |
| `R3F-SH-06` | `B2.5-O-05` / `PROMPT_04`                         | live FRED primary closeout remains Batch6/user-authorized only                                            | FRED-only live pilot authorization + sandbox/no-production-mutation proof |
| `R3F-SH-07` | `R3-B2.75-REQ2-EM` / `R3-PROMPT14-AKSHARE-VAL-01` | hard-constraint tracking: Eastmoney hist/AkShare validation family must not be closed by sidecar evidence | registry no-false-close test                                              |

禁止：不得把 source health snapshot 当作 production-ready 证明；它只是健康检查结果；Batch 01 / DH2 路径不得创建该表。`B2.5-O-05` 的 Batch 01 FRED sandbox evidence 不等于 live FRED primary；Eastmoney/AkShare validation 失败也不得由 TDX/Sina/其他 sidecar 自动关闭。

---

## Batch 3F.4 — Backfill / Reconcile / Recovery Parity

**建议分支：** `feature/round3-backfill-reconcile-parity`  
**业务目的：** 生产入库之前，必须证明坏数据、冲突数据、回填数据不会绕过验证和冲突处理。

| Task ID     | 来源                       | 范围                                                                                                    | Gate                          |
| ----------- | -------------------------- | ------------------------------------------------------------------------------------------------------- | ----------------------------- |
| `R3F-BR-01` | `R3-PARTIAL-1`             | Backfill parity ADR or pytest note                                                                      | parity test / ADR             |
| `R3F-BR-02` | `R3-PARTIAL-3` / `D2-P2-2` | Reconcile re-fetch/compare closure                                                                      | re-fetch pytest               |
| `R3F-BR-03` | `R3-PARTIAL-5`             | **CLOSED B3V-C04**: crash-window path A already has recovery tests; keep only regression/registry guard | no duplicate reopen check     |
| `R3F-BR-04` | `D7-P1-1` / `R2-RISK-1`    | Orchestrator handler registry extraction                                                                | handler registry pytest       |
| `R3F-BR-05` | `R3-PARTIAL-4` / ADR-023   | Registry closeout pending main-session update: ADR path chosen; no review UI implementation here        | registry reconcile + ADR link |

---

## Batch 3F.5 — Technical Debt / Packaging / Performance Hygiene

**建议分支：** `chore/round3-batch6-technical-debt`  
**并行性：** 可拆成多个小分支；不得与 core migration 同文件冲突。

| Task ID      | 来源                                                                           | 范围                                                                                                         | Gate                             |
| ------------ | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------ | -------------------------------- |
| `R3F-HYG-01` | `D3-P1-2`                                                                      | C901 refactor or justified ADR/noqa                                                                          | ruff / tests                     |
| `R3F-HYG-02` | `R2-HYG-4`                                                                     | `test_duckdb_connection` inter-call smell                                                                    | test refactor                    |
| `R3F-HYG-03` | `R2-HYG-5`                                                                     | Adapter metadata fields + skeleton metadata pytest                                                           | metadata tests                   |
| `R3F-HYG-04` | `D2-P3-1`                                                                      | `registry_generation` / `removed_from_yaml_at`                                                               | migration + sync tests           |
| `R3F-HYG-05` | `R3Y-TEST-DEPTH-001`                                                           | runtime-strong closed claim tests or wont-fix ADR                                                            | coverage report                  |
| `R3F-HYG-06` | `R3-B25-HYG-03` / `VR-PERF-001` / `PROMPT_03`                                  | production-equivalent smoke threshold/budget artifact + perf registry refresh                                | bounded smoke evidence           |
| `R3F-HYG-07` | `R3-B25-HYG-01` / `R3-B25-INGEST-SPLIT-R2B` / `R3-B25-INGEST-MONOLITH-R2C-R2D` | ingestion R2b–R2d monolith split per rollback plan                                                           | rollback checklist + tests       |
| `R3F-HYG-08` | `VR-RG-001`                                                                    | ResourceGuard shared cache + L3/L4 production-entry guard coverage                                           | ResourceGuard behavior tests     |
| `R3F-HYG-09` | `VR-L1PERF-001`                                                                | Layer1 feature computation pre-group/pre-sort optimization                                                   | complexity regression test       |
| `R3F-HYG-10` | `R2-RISK-2`                                                                    | adapter/storage decoupling: evidence port injection or explicit re-defer                                     | module boundary test             |
| `R3F-HYG-11` | `R2-RISK-3` / `R3-AUDIT-DEF-01` / `R3-AUDIT-DEF-03`                            | write_contract matrix + ops contract drift + scan-limit registry reconcile; do not reimplement resolved rows | registry alignment + drift tests |
| `R3F-HYG-12` | `PROMPT_05`                                                                    | CI gate hardening handoff before Round5 release gate                                                         | CI command matrix                |
| `R3F-HYG-13` | `WAVE-B-HYG-01/02/03`                                                          | registry wording normalization + test strictness + `QMD_SYNC_ALLOW_ADAPTER=1` escape-hatch ops docs          | docs/tests consistency check     |

---

## Batch 3F.6 — Lineage / Layer3 Hygiene Registry Closure

**建议分支：** `fix/round3f-batch6-lineage-layer3-registry-closure`  
**业务目的：** 集中关闭 3D.3 留给 Batch6 的 registry-owned lineage / Layer3 hygiene open items，防止执行者把 3D.3 的 partial hygiene merge 当成全量关闭。

| Task ID      | 来源                                    | 范围                                                                         | Gate                                      |
| ------------ | --------------------------------------- | ---------------------------------------------------------------------------- | ----------------------------------------- |
| `R3F-LIN-01` | `ADV-R3X-LINEAGE-001`                   | Full L3/L4 snapshot lineage persistence beyond staged envelopes              | snapshot lineage pytest + registry update |
| `R3F-LIN-02` | `R3Y-LINEAGE-VR-001`                    | Layer2 VR / fetch_log binding; synthetic IDs cannot masquerade as VR binding | negative binding test                     |
| `R3F-L3-01`  | `R3-B6-021-O-01`                        | Layer3 manifest/bar schema fail-closed for non-mapping `bars[]` elements     | malformed manifest pytest                 |
| `R3F-L3-02`  | `R3-B6-021-O-02`                        | deterministic rebuild compares full `IndustryChainDailySnapshotRow` tuple    | full row tuple/hash test                  |
| `R3F-LIN-03` | `ROUND3_WAVE_B_PENDING_FIX_REGISTRY.md` | final registry reconcile for Wave-B residual hygiene rows                    | unresolved/resolved no-conflict check     |

---

# Round 3F-R — Reference Adoption Refactor（3G 前置）

## Round 3F-R 业务目标

Batch 3F 已完成并保持全量测试绿，但它完成的是治理链、CLI 骨架、source health、TDX 探测门禁等基础设施；并不表示 data health、TDX provider、provider catalog、backtest/review lifecycle 已经达到成熟外部项目水平。

Round 3F-R 是 3G 前置闸门：在任何 sandbox clean-write rehearsal 之前，必须先处理以下重复造轮子风险，并把未来批次不得从零实现的能力写入本 roadmap。

**Canonical entrypoint:** `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/README.md`

## Batch 3F-R.1 — Task-local reference rules / license guardrails

| Task ID   | 范围                                                                                                                        | 参考项目                                                                                                     | Gate                                                  |
| --------- | --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------- |
| `R3FR-01` | 更新 task-local reference adoption 规则、license gate、反过度工程规则；不得建立执行者必须追踪的 central reference inventory | EasyXT、JQ2PTrade、OpenBB、agents-for-openbb、TradingAgents、TradingAgents-astock、digital-oracle、tdx-quant | guardrail tests；task cards carry source-path details |

必须明确：EasyXT/JQ2PTrade 可按 scoped adaptation 写入 QMD-owned modules；OpenBB 主仓库 AGPLv3 只能架构参考；`参考项目/**` 不得成为 backend runtime import。可存在非执行索引，但 executable adoption details 必须写在对应任务卡内。

## Batch 3F-R.2 — EasyXT data health refactor

| Task ID   | 当前重复轮子                                                                           | 替换/重构目标                                                                                               | 参考项目                                                                  | Gate                                             |
| --------- | -------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------ |
| `R3FR-02` | `backend/app/ops/data_health.py::check_daily_bars` 仅有薄 OHLCV/duplicate/history 检查 | 新建 `backend/app/ops/data_health_profiles/**`，把 EasyXT 数据完整性规则改造成 QMD 全仓 data health profile | EasyXT `data_manager/data_integrity_checker.py`、`smart_data_detector.py` | bad fixture tests；no mutation；no live fetch    |
| `R3FR-06` | `backend/app/cli/data_commands.py::health_check` 仍返回 `not_implemented_phase_c`      | `qmd data health` 接入真实 read-only profile runner                                                         | EasyXT report shape + QMD `DataHealthReport`                              | CLI smoke；structured error；DH2 no snapshot DDL |

必须覆盖：缺失交易日、空值/必填字段、非正价格、OHLC 关系、异常涨跌幅、成交量异常、duplicate key、history floor。不得只服务 QMT；必须支持 baostock/AkShare/TDX/Yahoo/future QMT/backtest frozen datasets 等全仓 profile。R3FR-02 与 R3FR-06 是同一垂直闭环，不得拆成“先加一个指标、以后再接 CLI”的微切片。

## Batch 3F-R.3 — TDX provider refactor behind QMD gates

| Task ID   | 当前重复轮子风险                                               | 替换/重构目标                                                                                                                      | 参考项目                                                 | Gate                                                              |
| --------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- | ----------------------------------------------------------------- |
| `R3FR-03` | `TdxPytdxProbeFetchPort` 若继续扩写，会变成自研 TDX downloader | 新建 `backend/app/datasources/fetch_ports/tdx_pytdx_port.py` 与 `normalizers/tdx.py`；保留 QMD 授权/caps/raw-only/no-mutation gate | EasyXT `easy_xt/realtime_data/providers/tdx_provider.py` | TDX auth tests；disabled-by-default route tests；fake pytdx tests |

不得从零写 TDX 协议、server failover、security list/daily/index extractor；必须先复用/改造成熟 pytdx provider 逻辑。TDX 仍 validation/raw-only、disabled-by-default，不得关闭 Eastmoney/AkShare validation open rows。

## Batch 3F-R.4 — Future work anti-reinvention planning

| Task ID   | 未来批次                | 不得从零写                                                                | 必须参考                                                                                          | Gate                                          |
| --------- | ----------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| `R3FR-04` | Round4 backtest/review  | DuckDB local loader、backtest CLI、report builder、API allow/deny mapping | JQ2PTrade `ptrade_local/**`、`api_mapping.json`；EasyXT `easyxt_backtest/**` metrics/report ideas | Round4 task card rewrite；no-action semantics |
| `R3FR-05` | provider/plugin/catalog | provider metadata、optional extras、auth/cost/terms/quality role taxonomy | OpenBB provider structure only；no AGPL source copy                                               | provider catalog contract tests               |

Round4 可以做分析、建议、观察列表、风险提示、人工复核建议；仍禁止自动交易、broker connection、直接仓位指令、`order/order_target/order_value`。

## Batch 3F-R.5 — Legacy wrapper cleanup and batch-folder rehome

| Task ID   | 范围                                                                                                                                                  | Gate                                                               |
| --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `R3FR-07` | replacement tests 通过后，清理薄 wrapper 内部逻辑；未来未完成任务卡按一个批次一个文件夹重组；旧 loose task card 先加 pointer/redirect，不做无引用删除 | roadmap/index consistency；no historical task silently invalidated |

## Round 3F-R 完成标准

- `PROJECT_IMPLEMENTATION_ROADMAP.md` 明确列出未来不得从零写的能力域和参考项目。
- `docs/implementation_tasks/README.md` 把 3F-R 作为 3G 前执行入口。
- task-local reference adoption rules + guardrail contract 已更新；不再要求 central executable reference inventory。
- EasyXT-style data health profile 接入 QMD read-only runner。
- `qmd data health` 不再返回 `not_implemented_phase_c`。
- TDX provider 细节与 probe orchestration 分离，仍保持 disabled/raw-only/authorized/capped。
- Round4 backtest/review 任务卡明确要求 JQ2PTrade/EasyXT adaptation，不得从零写 engine。
- provider catalog 任务明确 OpenBB 只能 architecture-only reference。
- 旧薄 wrapper 清理有 tests 和 redirects，不破坏 3F 绿基线。

---

# Round 3G — Sandbox Clean Write & Limited Production Entry

## Round 3G 业务目标

这是从“真实数据 staged 试跑”进入“生产数据入库前彩排”的阶段。Round 3G 之前不得启用 production clean write。

---

## Batch 3G.1 — Sandbox Clean-write Rehearsal

**建议分支：** `feature/round3-sandbox-clean-write-rehearsal`  
**前置必须全部满足：**

- Round 3D full Layer5 evidence chain 完成。
- Round 3E FRED/baostock/cninfo/akshare/TDX 的 source readiness 有明确结论。
- Round 3F data health / migration / CLI 核心 gate 已通过。
- Round 3F-R reference adoption refactor 完成，或每个未完成采纳项都有 ADR 明确 deferred reason、owner、closure gate；不得带着 `qmd data health` 占位、薄 OHLCV 规则、未分离的 TDX provider 进入 3G。

### 第一批 rehearsal 只允许

- `baostock` → `cn_equity_daily_bar`
- `cninfo` → `cn_announcements` metadata
- `fred` → P0 macro series

### 禁止

- 不写 production DB。
- 不做全市场。
- 不做分钟线。
- 不启用 QMT/TDX/Yahoo production。
- 不下载全量 PDF。

### Gate

- sandbox clean table row counts。
- WriteManager audit。
- DbValidationGate PASS。
- DataHealth PASS/WARN。
- source_conflict summary。
- rollback/no-mutation proof for production DB。
- Layer5 evidence chain refs complete。

---

## Batch 3G.2 — Strict Pre-production Adversarial Audit

**建议分支：** `review/round3-pre-production-data-audit`  
**业务目的：** 在第一次 production clean write 前，用攻击性审计证明不会污染生产库。

### 审计必须覆盖

- source routing 是否可能 silent fallback。
- validation-only 是否可能被当 Primary。
- production DB 是否有 no-mutation proof。
- WriteManager / DbValidationGate 是否是唯一 clean-write 边界。
- FRED/TDX/QMT/Yahoo 是否仍需授权。
- Layer2/3/4 是否仍使用 staged/fixture 输入冒充 production。
- Layer5 evidence chain 是否能追溯 source_fetch_id/content_hash。
- failed tests 是否被改了测试目标。

### Gate 输出

- `PASS_ALLOW_LIMITED_PROD_WRITE`
- `WARN_ALLOW_WITH_MANUAL_APPROVAL`
- `BLOCK_PRODUCTION_WRITE`

---

## Batch 3G.3 — Limited Production Clean Write

**建议分支：** `feature/round3-limited-production-clean-write`  
**业务目的：** 第一次正式生产入库，只开一条小产线。

### 允许范围

- 1–3 个 source。
- 3–10 个 symbols / series。
- 30–120 天窗口。
- 仅日线 / metadata / macro daily。
- 手动审批。
- 可回滚。

### 禁止范围

- 全市场。
- 全历史。
- 分钟线。
- 期权链全量。
- TDX/QMT production primary。
- Yahoo production primary。
- 自动告警驱动交易语义。

### Gate

- production DB before/after hash + row counts。
- data health report。
- conflict summary。
- source health snapshot。
- Layer5 evidence chain。
- rollback procedure dry-run。
- user approval evidence。

---

# Round 4 — API, UI, Notifications

## Round 4 业务目标

把后端数据能力变成可被用户、前端、Agent 查询的产品能力。

Round4 的执行入口是 `docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/`。下列 4.1–4.5 是同一个 Batch 04 内的产品化 track，不是给同一模块继续追加 5 个微批次。每个 track 的第一张 canonical card 必须交付真实可运行的最小垂直闭环：API 要有真实 read-only endpoint，Agent 要有 policy 保护下的一个 read-only tool，Frontend 要有至少一个 API-bound 页面/面板，Notification/Report 要有 event → report/notification_log 流程，Backtest/Review 要有一个 read-only review scenario。后续每个模块最多再用两个批次完成 full production-stable closure 与硬化，不允许 shell/deferred-only 交付。

---

## Batch 4.1 — Backend API & Auth/Security Gate

**建议分支：** `feature/round4-backend-api-security`  
**业务目的：** 提供安全的 read-only API，不让用户或 Agent 自由 SQL、无限分页、无认证访问生产数据。

| Task ID     | 来源                              | 范围                                       | Gate            |
| ----------- | --------------------------------- | ------------------------------------------ | --------------- |
| `R4-API-01` | `R2-GAP-2` / `VR-API-001`         | `GET /api/sources` / source capability API | HTTP tests      |
| `R4-API-02` | `R4-API-SEC-3..13` / `VR-API-001` | auth/page-size/startup security tests      | security pytest |
| `R4-API-03` | docs/api contracts                | Layer1–5 read-only context endpoints       | contract tests  |
| `R4-API-04` | ResourceGuard                     | query budget / page limit / no free SQL    | guard tests     |

---

## Batch 4.2 — Agent Tool Context APIs

**建议分支：** `feature/round4-agent-tool-context-apis`  
**业务目的：** 让 Agent 能读取 Layer1–5 的摘要上下文，但不能直接写库或自由查库。  
**新增审计来源：** `VR-AGENT-001` — agent contract 已定义 allowed/forbidden tools，但 runtime policy 仍需在 Round 4.2 落地。

范围：

- `/api/agent-tools/layer1/context`
- `/api/agent-tools/layer2/context`
- `/api/agent-tools/layer3/context`
- `/api/agent-tools/layer4/context`
- `/api/agent-tools/layer5/context`

Gate：

- read-only tests。
- no-free-SQL tests。
- source/evidence truncation tests。
- query budget tests。

---

## Batch 4.3 — Layer1–5 Dashboard Pages

**建议分支：** `feature/round4-layer-dashboard-pages`  
**来源：** `R4-FE-3`, `VR-FE-001`, `VR-FE-002`  
**业务目的：** 用户能看到五层模型状态、数据质量、证据链，而不是只看后端日志；同时补最小 ErrorBoundary 与 deferred route shell，避免 page_contracts 被误读为已实现页面。

范围：

- Layer1 axis dashboard。
- Layer2 cross-asset sensors。
- Layer3 industry chain graph。
- Layer4 market structure。
- Layer5 evidence detail。
- Data health/source readiness panel。

禁止：

- 不写死最终 UI 设计。
- 不加入交易动作建议。
- 不绕过 API 直接读 DB。

Gate：frontend tests + API contract snapshots + bundle budget。

---

## Batch 4.4 — Notification Center

**建议分支：** `feature/round4-notification-center`  
**来源：** `R4-NOTIF-1..3`, `R4-FE-2`, `VR-NOTIF-001`  
**业务目的：** 让系统在数据风险、source failure、quality failure、ResourceGuard 触发时能通知用户；补 notification/report runtime、dedup/cooldown、notification_log/report 表落地计划。

范围：

- notification model。
- dedup key。
- notification center page。
- no desktop throttle in Phase1 unless explicitly enabled。

Gate：unit tests + page smoke + dedup stability tests。

---

## Batch 4.5 — Backtest / Review Runtime

**建议分支：** `feature/round4-backtest-review-runtime`  
**来源：** `VR-BT-001`, existing `029_implement_backtest_and_review.md`, Round 3F-R `R3FR-04`  
**业务目的：** 将 backtest/review 从 schema/docs 推进到最小 read-only runtime；允许输出分析型建议、风险提示、观察列表建议、人工复核建议；不得输出自动交易动作，不得绕过 ResourceGuard。

范围：

- 不得从零设计 backtest engine；必须先按 §1.4 与 `R3FR-04` 读取并评估 JQ2PTrade `ptrade_local/**`、`api_mapping.json` 和 EasyXT `easyxt_backtest/**`。
- 将 JQ2PTrade DuckDB loader / run_backtest CLI / report builder 改造成 QMD `backend/app/review/**` read-only review lifecycle。
- 将 `api_mapping.json` 改造成 review sandbox allow/deny map：数据 API 可参考，`order/order_target/order_value/cancel_order` 必须 forbidden。
- 最小 `BacktestScenarioRegistry` / read-only review runner。
- 1–2 个 event-study / evidence-chain-review 场景。
- `DEFERRED_BACKTEST_TYPE` for unimplemented types。
- no-lookahead / no-action-semantics / ResourceGuard tests。

Gate：runtime pytest + report artifact + reserved-type tests。

---

# Round 5+ — Security, Scale, Release Hardening

## Round 5+ 业务目标

为真实生产长期运行补齐安全、CI、性能、运维闭环。

Round5 的执行入口是 `docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/`。Round5 不再拆产品功能；它只把已完成能力收束成 security / integration-resource / release-manifest 三类 gate。若发现 Round3G 或 Round4 功能未完成，Round5 必须阻断或精确列入 manifest，不得新增“补一个功能”的 release micro-slice。

## Batch 5.1 — Security CI

**建议分支：** `chore/round5-security-ci`  
**来源：** `R2-RISK-5`, `VR-SEC-001`  
**范围：** gitleaks / secret scanning / Python/backend security scan / dependency audit / release gate。

Gate：CI job green。

## Batch 5.2 — Production Scale Budget

**建议分支：** `chore/round5-production-scale-budget`  
**来源：** `VR-PERF-001` release-gate continuation after Round 3F budget artifact.  
**范围：** production-equivalent smoke、latency budget、row/window caps、ResourceGuard budget、nightly/CI threshold gate。

Gate：bounded performance report + threshold artifact。

## Batch 5.3 — Release Runbook & Ops Drills

**建议分支：** `chore/round5-release-runbook`  
**范围：** backup/restore, rollback, bad source quarantine, re-run data health, production clean write disable switch。

Gate：operator dry-run checklist。

---

# 3. 推荐执行顺序

1. ~~**Round 3D.1**~~ — full `023` Layer5 evidence chain — **DONE** (`376e30e6`).
2. ~~**Round 3D.2 / 3D.3**~~ — 模型输入白名单 + lineage/Layer3 hygiene — **DONE** (Batch 01 Track A).
3. ~~**Round 3E.1 / 3E.2 / 3E.3**~~ — FRED、TDX、baostock/cninfo/akshare v3 pilots — **DONE** (Batch 01 Track A).
4. ~~**Round 3E.4**~~ — data health v2 — **DONE** (`dd5fda5f`).
5. ~~**Round 3V.1**~~ — verified audit cleanup — contract/storage/sync hardening — **DONE** (`2aeb6f0`).
6. ~~**Round 3V.2**~~ — Layer5 / model schema post-audit reconcile — **DONE** (`2aeb6f0`).
7. ~~**Round 3F**~~：Batch6 data governance / migration / CLI / source health / backfill / hygiene — **DONE** (`d0393153`).
8. **Round 3F-R**：reference adoption refactor；用 EasyXT/JQ2PTrade/OpenBB 等成熟参考项目重构薄轮子，并把未来不得从零写的能力固化进规划。
9. **Round 3G.1**：sandbox clean-write rehearsal；必须等 3F-R 完成或 ADR defer。
10. **Round 3G.2**：pre-production adversarial audit。
11. **Round 3G.3**：limited production clean write。
12. **Round 4**：API / frontend / notification / backtest 产品化；Backtest/Agent/UI/provider 不得绕过 §1.4 参考采纳规则。
13. **Round 5+**：security / scale / release hardening。

---

# 4. 生产接入判断线

## 4.1 什么时候可以开始真实数据接入？

已经可以继续做真实数据 **raw/staging/sandbox** 试跑：baostock、cninfo、akshare validation-only、FRED-only sandbox、TDX manual probe。

## 4.2 什么时候可以开始 sandbox clean write？

必须等：

- Layer5 full evidence chain 完成。
- source readiness matrix 完成。
- data health v2 能覆盖将写入的数据。
- Batch6 migration/CLI/source-health 核心 gate 可用。
- Round 3F-R 完成：EasyXT-style data health profile、`qmd data health` runtime、TDX provider 分离、provider catalog/backtest reference adoption planning 已完成或有 ADR 明确延期。

## 4.3 什么时候可以启用 production clean write？

必须等：

- sandbox clean-write rehearsal PASS。
- strict pre-production adversarial audit 输出 `PASS_ALLOW_LIMITED_PROD_WRITE` 或 `WARN_ALLOW_WITH_MANUAL_APPROVAL`。
- 用户明确批准 source/domain/symbol/window/row cap。

第一批 production clean write 只建议：

- `baostock` A 股日线小样本。
- `cninfo` 公告 metadata 小样本。
- `fred` P0 macro series 小样本。

不建议第一批：TDX/QMT/Yahoo production primary、全市场、全历史、分钟线、期权链。

---

# 5. 执行者避免跑偏的最终规则

1. 每个分支必须声明属于哪个 Round / Batch / Task ID。
2. 每个任务必须有 `/to-issues` vertical slices。
3. 每个 issue 必须说明业务目的、实现范围、禁止范围、gate、evidence。
4. 任何 source 接入必须先 route preview，再 fetch。
5. 任何 clean write 必须先 data health，再 conflict summary，再 WriteManager。
6. 任何生产库相关任务必须有 before/after no-mutation 或 mutation proof。
7. 涉及 data health、TDX/provider、backtest/review、provider catalog、Agent/UI artifacts 的未来任务，必须先执行 §1.4 成熟参考项目采纳规则；若从零写，必须有 ADR。
8. 所有 deferred item 要么关闭并移入 `RESOLVED_ISSUES_REGISTRY.md`，要么继续在 `AUDIT_DEFERRED_REGISTRY.md` / `UNRESOLVED_ISSUES_REGISTRY.md` 中带 owner、phase、closure test。
9. 若本文件与旧 `ROUND3_BATCH_IMPLEMENTATION_MAP.md` 冲突：未来规划以本文件为准；历史证据追踪仍以旧 map 和 Trellis archive 为准。
