# 项目级导航地图

> 本文件按**功能域 / 主域**索引经用户审阅的**最终成品**设计文档。  
> **收录范围**：`docs/**/design/`、`specs/**/design/` 与 `rules/**/design/` 下经审阅的最终成品（`.md` / `.yaml` 等规格文件）。  
> **不收录**：同目录非 `design/` 的阶段性、一次性或偏离设计预期的文档。  
> **不按文件夹分组**：按文件**主要内容**归入主域（如 API 域、五层域）。  
> 路径一律使用仓库相对路径；同域内用 **文件1、文件2…** 区分条目。  
> `specs/contracts/` 等机器契约可在跨域触点引用，但不单独建卡片（除非纳入 `specs/**/design/`）。
> 权威来源："C:\Users\Guang\Desktop\quant-monitor-desk\MIGRATION_MAP.md"中索引的文件为本项目的最高权威来源，"C:\Users\Guang\Desktop\quant-monitor-desk\MIGRATION_MAP.md"中索引文件改动之前必须要求用户进行确认，改动之后要求用户进行详细审阅（必须有ADR作为决策记录否则不得通过）。所有模块、本项目的最终成品形态均有"C:\Users\Guang\Desktop\quant-monitor-desk\MIGRATION_MAP.md"中索引文件来定义，模块是否达到R4等级，必须根据"C:\Users\Guang\Desktop\quant-monitor-desk\MIGRATION_MAP.md"下的索引文件作为最高权威来源来确认，与索引文件的设计完全一致则视为达到R4，否则不得视为达到R4。所有执行、审计与plan、设计均需要以"C:\Users\Guang\Desktop\quant-monitor-desk\MIGRATION_MAP.md"内的索引文件作为最高权威来源。
> **卡片格式**

| 区块     | 规则                     |
| -------- | ------------------------ |
| 定位     | 一句话                   |
| 涉及内容 | bullet ≤ 7 条            |
| 跨域触点 | 按类别分表，每类条目不限 |

---

## 项目总览与系统边界

---

### 文件1 · `docs/architecture/design/01_context_and_scope.md`

**定位** 系统上下文与范围边界（导航摘要，不替代模块原文）

**涉及内容**

- 系统目标：可信数据 → 多层建模 → 证据链 → Agent 解释 → 人工确认
- 范围内：多源数据、DuckDB 底座、Layer1~5、FastAPI/React/Agent、运维
- 范围外：全自动交易、Agent 写库/自由上网/交易语义、PostgreSQL/Next.js/Airflow/微服务
- 指向更详细的架构来源文档

**跨域触点**

| 类别        | 触点                                                                                             |
| ----------- | ------------------------------------------------------------------------------------------------ |
| 模块        | 数据同步 · 五层建模 · FastAPI · React · Agent                                                    |
| 契约 / 文档 | `docs/architecture/design/02_solution_strategy.md` · `docs/architecture/design/05_module_map.md` |

---

### 文件2 · `rules/design/RESEARCHER_GUIDE.md`

**定位** 研究/复盘角色入口（五层模块读法与数据可信边界）

**涉及内容**

- 研究入口：Layer1–5 模块设计文档与回测生命周期文档指针
- 结果须可追溯：`source_used` · SourceRoutePlan · `quality_flags` · `rule_version` · snapshot lineage · `evidence_id`
- 禁止：研究复盘渲染为买卖建议
- 导入策略/研究文本默认 local-only，不写 clean；保存为 evidence 须用户确认

**跨域触点**

| 类别           | 触点                                                                                                  |
| -------------- | ----------------------------------------------------------------------------------------------------- |
| Layer          | **→ 五层域** Layer1–5 模块卡片 · Layer snapshot / evidence                                            |
| 模块           | **→ 回测域** `backtest_review_lifecycle.md` · Agent · WriteManager 只读边界                           |
| 契约 / 文档    | **→ 数据存储域 文件5** `snapshot_lineage_contract.yaml` · **→ 数据源域 文件3** `source_route_plan.md` |
| 数据与基础设施 | `evidence_chain` · no_action 语义 · local-only 导入                                                   |

---

## 总体架构与技术选型

### 文件1 · `docs/architecture/design/02_solution_strategy.md`

**定位** 本地优先总体架构与技术栈选型

**涉及内容**

- 端到端架构分层图（数据源 → Fetcher/Sync → Raw → Validator → DuckDB → FastAPI/Agent → 前端）
- 第一阶段技术栈：Python 3.11+ / FastAPI / DuckDB / Vite+React / APScheduler
- 明确第一阶段不采用的组件（PostgreSQL、Next.js、Airflow、多 Agent 编排）
- DuckDB 五条使用规则（单写多读、WriteManager、Agent 不写库等）
- DuckDB + Pandas 研究/ETL 允许与禁止边界
- 数据源优先组合（QMT/baostock/AkShare/巨潮/东财）与补充源

**跨域触点**

| 类别           | 触点                                                                                 |
| -------------- | ------------------------------------------------------------------------------------ |
| 模块           | `data_sources` · `data_sync_orchestrator` · FastAPI · Agent 只读工具层 · 前端看板    |
| 契约 / 文档    | `docs/modules/design/duckdb_and_parquet.md` · `docs/modules/design/write_manager.md` |
| 数据与基础设施 | Raw 层 · Parquet 归档 · `uv` / pytest / ruff · QMT/xtdata · Yahoo/同花顺/腾讯/百度   |

---

### 文件2 · `specs/contracts/design/runtime_versions.md`

**定位** 运行时版本与依赖锁策略（D-01 / QM-AUD-005）

**涉及内容**

- Python `>=3.11,<3.13` · Node `>=20,<23` · npm `>=10` 基线
- D-01：`uv.lock` 为 Python 主锁文件，须提交 Git 并与 pyproject 同步
- 前端 `package-lock.json` 锁定；禁止擅自改用 Poetry
- 默认验收：`uv sync` / `uv run` · CI 与本地同版本
- DuckDB/FastAPI/Pydantic 版本以 lock 文件为准，不在任务文档硬编码补丁号

**跨域触点**

| 类别           | 触点                                                                   |
| -------------- | ---------------------------------------------------------------------- |
| 模块           | CI · 本地开发 · Claude Code / Codex 执行环境                           |
| 契约 / 文档    | **→ 运维域 文件1** `06_deployment_and_local_ops.md` · `pyproject.toml` |
| 数据与基础设施 | `uv.lock` · `package-lock.json` · pre-commit                           |

---

## 五层分析建模

### 文件1 · `docs/architecture/design/05_module_map.md`

**定位** 五层分析建模框架与工程模块地图

**涉及内容**

- Layer1~5 各层中英文定义与职责边界
- Top-down 与 Bottom-up 双向分析路径
- 核心工程模块清单（data_sources、sync、validation、write_manager、layers、API、前端、Agent、ops、reports）
- Agent 与 `notification_and_reports` 的职责分工（解释 vs 归档发送）
- 实现细节落点 `docs/modules/design/`

**跨域触点**

| 类别        | 触点                                                                                                                                                                                                                                                                                         |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Layer       | Layer1 Global Regime · Layer2 Cross-Asset Sensor · Layer3 Shock-Anchor · Layer4 Market Structure · Layer5 Security Evidence                                                                                                                                                                  |
| 模块        | `docs/modules/design/layer1_global_regime_panel.md` … `docs/modules/design/layer5_security_evidence.md` · `docs/modules/design/agent_module.md` · `docs/modules/design/notification_and_reports.md` · `docs/modules/design/fastapi_backend.md` · `docs/modules/design/frontend_dashboard.md` |
| 契约 / 文档 | 各 Layer 对应 `specs/layer*` 与 `docs/modules/design/*`                                                                                                                                                                                                                                      |

---

### 文件2 · `docs/modules/design/layer1_global_regime_panel.md`

**定位** Layer1 全球底层状态面板（五轴环境状态向量，可审计可解释）

**涉及内容**

- 五轴：ENVIRONMENT / CREDIT_STRESS / RISK_APPETITE / LIQUIDITY / SENTIMENT
- Primary / Validation / FallbackPolicy 数据源角色
- 指标规格外置 `specs/layer1_axes/design/restructured_axes_v1_1/`
- 回答「全球底层状态是什么」；不输出交易动作、不伪造 BlindSpot
- 与 data_sync、validation、write_manager、前端展示依赖

**跨域触点**

| 类别           | 触点                                                                    |
| -------------- | ----------------------------------------------------------------------- |
| Layer          | Layer1 axis 表 · observation · snapshot                                 |
| 模块           | **→ 五层域 文件19–20** Layer2–3 · **→ 数据同步域** IncrementalUpdateJob |
| 契约 / 文档    | **→ 五层域 文件3–18** Layer1 轴规格 · **→ ADR 域** ADR-0003             |
| 数据与基础设施 | standardized fields 仅 Layer1 物化 · BlindSpot 标注                     |

---

### 文件3 · `specs/layer1_axes/design/restructured_axes_v1_1/common/common_axis_rules.md`

**定位** Layer1 五轴共同规则（舱位、数据源角色、状态字段与全链路管道）

**涉及内容**

- 五轴身份：ENVIRONMENT / CREDIT_STRESS / RISK_APPETITE / LIQUIDITY / SENTIMENT
- 前端统一解释口径（是什么、历史位置、变化、能/不能说明什么、新鲜度）
- 统一舱位 A/B/C/D/SHADOW/Forbidden 与主面板准入规则
- Primary / Validation / FallbackPolicy 数据源角色重构
- 每个指标建议落地字段（raw_value、stale_reason、quality_flags 等）
- 全链路须走 sync → clean → 特征 → 解读，舱位不豁免管道

**跨域触点**

| 类别           | 触点                                                                                |
| -------------- | ----------------------------------------------------------------------------------- |
| Layer          | Layer1 全轴 observation / snapshot 语义                                             |
| 模块           | **→ 五层域 文件2** `layer1_global_regime_panel.md` · **→ 五层域 文件4–18** 各轴规格 |
| 契约 / 文档    | 各轴 `*_indicator_spec.yaml` · `specs/contracts/` 数据源契约                        |
| 数据与基础设施 | `primary_source` · BlindSpot 诚实失败 · SHADOW 不得接管主值                         |

---

### 文件4 · `specs/layer1_axes/design/restructured_axes_v1_1/environment_axis/environment_axis_user_guide.md`

**定位** 环境轴（ENVIRONMENT）用户说明（宏观水位、利率、通胀与实体经济底板）

**涉及内容**

- 一句话定义：钱的水位、无风险利率、通胀压力、经济底板
- 能说明：央行资产负债表、收益率曲线、真实利率、通胀与就业底板
- 不能说明：信用利差、VIX/SKEW、盘口摩擦、仓位情绪（归其他四轴）
- 前端展示：今日值、历史位置、变化、滞后、质量、通俗解释与边界提醒
- 典型指标解释示例（WRESBAL、NET_LIQ_PROXY_BN、EFFR/DGS10/T10Y3M 等）

**跨域触点**

| 类别           | 触点                                      |
| -------------- | ----------------------------------------- |
| Layer          | ENVIRONMENT axis · E0–E4 模块语义         |
| 模块           | **→ 五层域 文件5–6** 工程规则与指标 YAML  |
| 契约 / 文档    | **→ 五层域 文件3** `common_axis_rules.md` |
| 数据与基础设施 | FRED 宏观序列 · 混频投影须标注 lag        |

---

### 文件5 · `specs/layer1_axes/design/restructured_axes_v1_1/environment_axis/environment_axis_engineering_rules.md`

**定位** 环境轴工程规则（混频投影、lag gate、禁止跨轴指标）

**涉及内容**

- 只输出宏观状态向量，不输出交易动作
- E0 净水位 proxy 须标记 `projection_method` 与 `source_frequency_map`
- NET_LIQ_PROXY_BN 仅归因解释，不参与 gate/scoring
- 月频/周频数据 honest lag；ACMTP10 等模型输出须有 lag gate
- 禁止 WM2NS、跨轴指标塞入、GDPNow 回写 Layer1
- 自检：E0–E4 主状态覆盖、混频双算风险阻断

**跨域触点**

| 类别           | 触点                                                      |
| -------------- | --------------------------------------------------------- |
| Layer          | ENVIRONMENT gate/scoring 边界                             |
| 模块           | data_sync FRED adapter · Layer1 计算管道                  |
| 契约 / 文档    | **→ 五层域 文件6** `environment_axis_indicator_spec.yaml` |
| 数据与基础设施 | `diagnostic_only` · `excluded_from_gate` 元数据           |

---

### 文件6 · `specs/layer1_axes/design/restructured_axes_v1_1/environment_axis/environment_axis_indicator_spec.yaml`

**定位** 环境轴指标机器规格（indicator_id、数据源、舱位与输出字段）

**涉及内容**

- `axis_id: ENVIRONMENT` 与 E0–E4 模块划分
- 每指标：indicator_id、display_name_cn、layer/dest_tag、gate_scoring
- primary_source / validation_source / fallback_policy 逐条登记
- 混频与诊断指标必填 metadata（projection_method、boundary）
- 输出字段：raw_value、z_score、percentile_rank、state_bucket、data_lag_days
- Layer2_Background / BlindSpot 降级指标显式标注

**跨域触点**

| 类别           | 触点                                                  |
| -------------- | ----------------------------------------------------- |
| Layer          | Layer1 ENVIRONMENT 表初始化与 snapshot 字段           |
| 模块           | Layer1 registry loader · sync FRED · 前端 Layer1 面板 |
| 契约 / 文档    | **→ 五层域 文件4–5** 用户说明与工程规则               |
| 数据与基础设施 | FRED series ID · weekly/monthly frequency 标注        |

---

### 文件7 · `specs/layer1_axes/design/restructured_axes_v1_1/credit_stress_axis/credit_stress_axis_user_guide.md`

**定位** 信用压力轴（CREDIT_STRESS）用户说明（融资信任温度计）

**涉及内容**

- 一句话定义：市场为企业/金融机构融资要求的额外补偿是否变高
- 能说明：信用风险补偿、HY 定价、短端融资、repo、银行贷款标准、离岸美元压力
- 不能说明：国债收益率、期权保险费、盘口摩擦、仓位拥挤（归其他轴）
- 用户版前端展示与通俗解释口径
- 与 OAS、融资利差、商业票据等典型指标边界

**跨域触点**

| 类别           | 触点                                      |
| -------------- | ----------------------------------------- |
| Layer          | CREDIT_STRESS axis                        |
| 模块           | **→ 五层域 文件8–9** 工程规则与指标 YAML  |
| 契约 / 文档    | **→ 五层域 文件3** `common_axis_rules.md` |
| 数据与基础设施 | 信用利差序列 · FRED / 市场数据源          |

---

### 文件8 · `specs/layer1_axes/design/restructured_axes_v1_1/credit_stress_axis/credit_stress_axis_engineering_rules.md`

**定位** 信用压力轴工程规则（信用利差、融资市场与跨轴隔离）

**涉及内容**

- 只输出信用压力状态向量，禁止交易动作语义
- 信用指标与国债收益率、VIX、流动性摩擦严格分轴
- Primary / Validation / FallbackPolicy 与 honest lag
- 禁止把环境轴或情绪轴指标塞入信用轴计分
- 自检：主状态指标覆盖、滞后标注、禁止 substitute

**跨域触点**

| 类别           | 触点                                                        |
| -------------- | ----------------------------------------------------------- |
| Layer          | CREDIT_STRESS gate/scoring                                  |
| 模块           | data_sync · Layer1 计算                                     |
| 契约 / 文档    | **→ 五层域 文件9** `credit_stress_axis_indicator_spec.yaml` |
| 数据与基础设施 | OAS / spread 序列 · stale_reason                            |

---

### 文件9 · `specs/layer1_axes/design/restructured_axes_v1_1/credit_stress_axis/credit_stress_axis_indicator_spec.yaml`

**定位** 信用压力轴指标机器规格

**涉及内容**

- `axis_id: CREDIT_STRESS` 与模块/指标清单
- 每指标数据源角色、舱位、gate_scoring 与 boundary
- 输出字段与 fallback_policy 枚举
- 诊断/背景指标与主状态指标分离
- 与 common_axis_rules 舱位表对齐

**跨域触点**

| 类别           | 触点                                       |
| -------------- | ------------------------------------------ |
| Layer          | Layer1 CREDIT_STRESS 表族                  |
| 模块           | **→ 五层域 文件7–8** 用户说明与工程规则    |
| 契约 / 文档    | `source_registry` · platform_source_matrix |
| 数据与基础设施 | FRED / 市场 credit 序列                    |

---

### 文件10 · `specs/layer1_axes/design/restructured_axes_v1_1/risk_appetite_axis/risk_appetite_axis_user_guide.md`

**定位** 风险偏好轴（RISK_APPETITE）用户说明（波动与尾部保险费）

**涉及内容**

- 一句话定义：市场为波动、尾部灾难与路径不确定性支付的保险费
- 能说明：VIX 类波动保险、尾部保护、VRP、股债对冲有效性
- 不能说明：PCR/COT/NAAIM（情绪轴）、信用利差、盘口冲击、宏观水位
- 前端命名建议：用「波动保险费」而非「恐慌指数」
- 典型指标边界与用户可理解解释

**跨域触点**

| 类别           | 触点                                       |
| -------------- | ------------------------------------------ |
| Layer          | RISK_APPETITE axis                         |
| 模块           | **→ 五层域 文件11–12** 工程规则与指标 YAML |
| 契约 / 文档    | **→ 五层域 文件3** `common_axis_rules.md`  |
| 数据与基础设施 | 期权隐含波动序列 · VRP 计算边界            |

---

### 文件11 · `specs/layer1_axes/design/restructured_axes_v1_1/risk_appetite_axis/risk_appetite_axis_engineering_rules.md`

**定位** 风险偏好轴工程规则（期权隐含波动、尾部风险与股债共振）

**涉及内容**

- 波动/尾部指标与情绪轴成交行为指标分离
- VIX、SKEW、VRP 等须有来源与 lag 标注
- 禁止跨轴 substitute 与回写 Layer1 外轴
- gate/scoring 与 diagnostic_only 边界
- 自检清单与禁止项

**跨域触点**

| 类别           | 触点                                                         |
| -------------- | ------------------------------------------------------------ |
| Layer          | RISK_APPETITE gate/scoring                                   |
| 模块           | data_sync 期权/指数源                                        |
| 契约 / 文档    | **→ 五层域 文件12** `risk_appetite_axis_indicator_spec.yaml` |
| 数据与基础设施 | 期权链数据 freshness                                         |

---

### 文件12 · `specs/layer1_axes/design/restructured_axes_v1_1/risk_appetite_axis/risk_appetite_axis_indicator_spec.yaml`

**定位** 风险偏好轴指标机器规格

**涉及内容**

- `axis_id: RISK_APPETITE` 指标登记
- 波动保险费、尾部保护、股债对冲类指标条目
- primary_source / fallback_policy / dest_tag 逐条定义
- boundary 与 no_main_score_input 约束
- 输出字段与频率标注

**跨域触点**

| 类别           | 触点                                      |
| -------------- | ----------------------------------------- |
| Layer          | Layer1 RISK_APPETITE 表族                 |
| 模块           | **→ 五层域 文件10–11** 用户说明与工程规则 |
| 契约 / 文档    | FRED / CBOE / 市场数据源登记              |
| 数据与基础设施 | 日频/周频混用 honest lag                  |

---

### 文件13 · `specs/layer1_axes/design/restructured_axes_v1_1/liquidity_axis/liquidity_axis_user_guide.md`

**定位** 流动性轴（LIQUIDITY）用户说明（交易成本与市场可交易性）

**涉及内容**

- 一句话定义：交易是否变难——价差、冲击成本、可交易性
- 能说明：隐含价差 proxy、价格冲击、可交易性干涸 proxy、ETF 摩擦阵列
- 不能说明：宏观水位、信用利差、情绪拥挤、期权保险费
- 不等于真实 L2/L3 订单簿深度
- 用户版前端展示建议（核心 ETF 阵列摩擦指标）

**跨域触点**

| 类别           | 触点                                       |
| -------------- | ------------------------------------------ |
| Layer          | LIQUIDITY axis                             |
| 模块           | **→ 五层域 文件14–15** 工程规则与指标 YAML |
| 契约 / 文档    | **→ 五层域 文件3** `common_axis_rules.md`  |
| 数据与基础设施 | ETF bar · Amihud 类 proxy                  |

---

### 文件14 · `specs/layer1_axes/design/restructured_axes_v1_1/liquidity_axis/liquidity_axis_engineering_rules.md`

**定位** 流动性轴工程规则（交易成本 proxy 与跨轴隔离）

**涉及内容**

- 流动性摩擦指标与环境/信用/风险/情绪轴严格分轴
- Amihud、价差 proxy 等须有资产范围与频率说明
- 禁止把宏观流动性水位塞入本轴主计分
- diagnostic 与主状态分离；honest lag
- 自检：核心 ETF 传感器覆盖、禁止 substitute

**跨域触点**

| 类别           | 触点                                                     |
| -------------- | -------------------------------------------------------- |
| Layer          | LIQUIDITY gate/scoring                                   |
| 模块           | data_sync 行情 · Layer1 计算                             |
| 契约 / 文档    | **→ 五层域 文件15** `liquidity_axis_indicator_spec.yaml` |
| 数据与基础设施 | ETF ticker 阵列 · volume 质量标记                        |

---

### 文件15 · `specs/layer1_axes/design/restructured_axes_v1_1/liquidity_axis/liquidity_axis_indicator_spec.yaml`

**定位** 流动性轴指标机器规格

**涉及内容**

- `axis_id: LIQUIDITY` 与模块/指标清单
- 交易成本、冲击、可交易性 proxy 条目
- ETF 传感器阵列与 primary_source 登记
- gate_scoring、boundary、fallback_policy
- 输出字段与舱位 dest_tag

**跨域触点**

| 类别           | 触点                                      |
| -------------- | ----------------------------------------- |
| Layer          | Layer1 LIQUIDITY 表族                     |
| 模块           | **→ 五层域 文件13–14** 用户说明与工程规则 |
| 契约 / 文档    | 行情源 capability · QMT/Yahoo 补充边界    |
| 数据与基础设施 | 日频 bar · quality_flags                  |

---

### 文件16 · `specs/layer1_axes/design/restructured_axes_v1_1/sentiment_axis/sentiment_axis_user_guide.md`

**定位** 情绪轴（SENTIMENT）用户说明（仓位拥挤与行为倾斜）

**涉及内容**

- 一句话定义：参与者是否挤在船同一侧——仓位、行为、信念、杠杆燃料
- 能说明：COT、PCR、RSP-SPY 集中度、AAII、融资杠杆等
- 不能说明：VIX/SKEW/VRP、信用利差、盘口冲击、宏观水位
- 只输出状态向量，不输出单一情绪总分
- AAII 是「说什么」非「做什么」；RSP-SPY 是集中度投影

**跨域触点**

| 类别           | 触点                                       |
| -------------- | ------------------------------------------ |
| Layer          | SENTIMENT axis                             |
| 模块           | **→ 五层域 文件17–18** 工程规则与指标 YAML |
| 契约 / 文档    | **→ 五层域 文件3** `common_axis_rules.md`  |
| 数据与基础设施 | COT / 调查序列 · 融资余额数据              |

---

### 文件17 · `specs/layer1_axes/design/restructured_axes_v1_1/sentiment_axis/sentiment_axis_engineering_rules.md`

**定位** 情绪轴工程规则（行为/仓位指标与期权保险费分离）

**涉及内容**

- 情绪行为指标与风险偏好轴期权指标严格分轴
- COT、PCR、AAII、NAAIM 等须有频率与滞后说明
- 禁止合成单一情绪总分冒充主状态
- 禁止跨轴 substitute 与交易动作语义
- 自检：主指标覆盖、边界字段完整

**跨域触点**

| 类别           | 触点                                                     |
| -------------- | -------------------------------------------------------- |
| Layer          | SENTIMENT gate/scoring                                   |
| 模块           | data_sync · Layer1 计算                                  |
| 契约 / 文档    | **→ 五层域 文件18** `sentiment_axis_indicator_spec.yaml` |
| 数据与基础设施 | 周频/月频调查 honest lag                                 |

---

### 文件18 · `specs/layer1_axes/design/restructured_axes_v1_1/sentiment_axis/sentiment_axis_indicator_spec.yaml`

**定位** 情绪轴指标机器规格

**涉及内容**

- `axis_id: SENTIMENT` 指标登记
- 仓位、行为、信念、杠杆类指标条目
- primary_source / validation / fallback_policy
- boundary 与 diagnostic_only 标注
- 输出字段与舱位 dest_tag

**跨域触点**

| 类别           | 触点                                      |
| -------------- | ----------------------------------------- |
| Layer          | Layer1 SENTIMENT 表族                     |
| 模块           | **→ 五层域 文件16–17** 用户说明与工程规则 |
| 契约 / 文档    | FRED / CFTC / 调查数据源                  |
| 数据与基础设施 | 融资余额 · COT 报告 lag                   |

---

### 文件19 · `docs/modules/design/layer2_cross_asset_sensor.md`

**定位** Layer2 跨资产传感器（已交易出来的跨资产价格/量/持仓变化）

**涉及内容**

- 资产范围：USD、Rates、Metals、Energy、Credit ETF、Volatility、Shipping、Futures
- 观察跨资产异常是否支持/反驳 Layer1
- 不回写 Layer1、不替代宏观判断
- `cross_asset_registry` 表结构与观测字段
- 与 Layer3/4/5 的引用边界

**跨域触点**

| 类别           | 触点                                                       |
| -------------- | ---------------------------------------------------------- |
| Layer          | Layer2 cross-asset observation · **→ 五层域 文件2** Layer1 |
| 模块           | data_sync · validation · **→ 五层域 文件20** Layer3        |
| 契约 / 文档    | `specs/layer2_*`（以仓库当前 specs 为准）                  |
| 数据与基础设施 | 跨资产 bar / spread 观测 · freshness                       |

---

### 文件20 · `docs/modules/design/layer3_industry_shock_anchor.md`

**定位** Layer3 全球产业链资金震动锚点（引发产业链资金重定价的锚点，非普通行业清单）

**涉及内容**

- Shock-Anchor 概念（NVIDIA、TSMC、Capex Setters、商品价格锚等）
- 与 Layer5 边界：结构/锚点在 L3，行情/证据在 L5
- `anchor_tier`（A_GLOBAL_DOMINANT → E_REGIONAL_PROXY）
- `anchor_priority`（P0_CORE → P2_WATCH）与监控频率
- 私有公司只进事件系统，不进普通行情表

**跨域触点**

| 类别           | 触点                                                                      |
| -------------- | ------------------------------------------------------------------------- |
| Layer          | `industry_chain_*` graph · anchor/node/edge registry                      |
| 模块           | **→ 五层域 文件30** `layer3_config_health_check.md` · Layer3SpecValidator |
| 契约 / 文档    | **→ 五层域 文件21–27** Layer3 配置规格 · **→ ADR 域** ADR-0004            |
| 数据与基础设施 | `source_keys` · P0 锚点来源约束 · event_only 语义                         |

---

### 文件21 · `specs/layer3_global_industry_chains/design/layer3_global_industry_chains_v1_2/layer3_data_dictionary.md`

**定位** Layer3 产业链锚点字段说明与实现规则（v1.2 可实现版本）

**涉及内容**

- Layer3 定位：全球产业链资金震动锚点层，非行业列表或股票池
- chain / anchor / node / edge 字段字典与含义
- `chain_priority`、`anchor_priority`、`anchor_tier`、`source_validation_status`
- 锚点类型：Capex 总开关、全球定价锚、私有事件锚、商品/指数锚、区域映射
- 文件包清单与程序读取顺序
- 与 Layer5 边界：L3 存结构，L5 存行情与证据

**跨域触点**

| 类别           | 触点                                                                                         |
| -------------- | -------------------------------------------------------------------------------------------- |
| Layer          | `industry_chain_*` 表族字段语义                                                              |
| 模块           | **→ 五层域 文件20** `layer3_industry_shock_anchor.md` · **→ 五层域 文件22–26** registry 文件 |
| 契约 / 文档    | **→ 五层域 文件33** `layer3_loader_contract.yaml`                                            |
| 数据与基础设施 | `status_explanation_cn` · `layer5_mapping_hint`                                              |

---

### 文件22 · `specs/layer3_global_industry_chains/design/layer3_global_industry_chains_v1_2/layer3_global_industry_chain_registry.yaml`

**定位** Layer3 产业链主配置（chain 定义、锚点列表与 v1.2 方案 B 图结构）

**涉及内容**

- `version: 1.2` · 方案 B：功能节点、链内边与 AI 主链跨链传导边
- `anchor_tier_dictionary` 与 `anchor_role_dictionary`
- 每条 chain：`chain_id`、`chain_priority`、`chain_type`、`anchors[]`
- P0 仅 AI 基础设施核心链；非 AI 链为 P1/P2
- 私有公司/商品/指数锚与区域映射锚规则
- 后端初始化 `industry_chain` 基础表的主输入

**跨域触点**

| 类别           | 触点                                                        |
| -------------- | ----------------------------------------------------------- |
| Layer          | Layer3 chain registry                                       |
| 模块           | Layer3RegistryLoader · **→ 五层域 文件23–26** 扁平 registry |
| 契约 / 文档    | **→ 五层域 文件21** `layer3_data_dictionary.md`             |
| 数据与基础设施 | P0_CORE chain · root node 必生成                            |

---

### 文件23 · `specs/layer3_global_industry_chains/design/layer3_global_industry_chains_v1_2/layer3_anchor_registry.json`

**定位** Layer3 扁平化锚点表（前端卡片、搜索索引与 Agent 输入）

**涉及内容**

- 锚点快速读取：`anchor_id`、display_name、ticker、anchor_tier
- `status_explanation_cn` / `impact_explanation_cn` 直出前端
- `anchor_priority`（P0_CORE → P2_WATCH）与 `source_keys`
- `instrument_type`：public_equity / private_company / future_or_commodity 等
- `source_validation_status`：verified / needs_source / event_only
- 不做全量股票池；每个锚点须有地位与作用

**跨域触点**

| 类别           | 触点                                                                         |
| -------------- | ---------------------------------------------------------------------------- |
| Layer          | Layer3 anchor 索引                                                           |
| 模块           | 前端 graph/card · Agent Layer3 context · **→ 五层域 文件27** source_registry |
| 契约 / 文档    | **→ 五层域 文件22** chain registry YAML                                      |
| 数据与基础设施 | P0 锚点 `source_keys` 必填                                                   |

---

### 文件24 · `specs/layer3_global_industry_chains/design/layer3_global_industry_chains_v1_2/layer3_node_registry.json`

**定位** Layer3 功能节点注册表（方案 B 图节点）

**涉及内容**

- `node_id` 唯一性与 chain 归属
- 每条 chain 至少一个 root node（可初始化 `industry_chain_node`）
- 功能节点语义（AI 服务器、光模块、电力冷却等分组）
- 与 anchor 的 `node_id` 引用关系
- 供 Layer3GraphBuilder 构图

**跨域触点**

| 类别           | 触点                                                        |
| -------------- | ----------------------------------------------------------- |
| Layer          | `industry_chain_node` 初始化                                |
| 模块           | Layer3GraphBuilder · **→ 五层域 文件25–26** edge registries |
| 契约 / 文档    | **→ 五层域 文件33** loader hard_validation_rules            |
| 数据与基础设施 | node_id 唯一 · anchor.node_id 必须存在                      |

---

### 文件25 · `specs/layer3_global_industry_chains/design/layer3_global_industry_chains_v1_2/layer3_edge_registry.json`

**定位** Layer3 链内有向边注册表（产业链内传导关系）

**涉及内容**

- `from_node_id` / `to_node_id` 端点须在 node registry 存在
- 链内资金/供给传导边语义
- 与 cross_chain 边分离
- 图视图边渲染与 Agent 解释输入
- 断边/孤儿节点为健康检查失败项

**跨域触点**

| 类别           | 触点                                                |
| -------------- | --------------------------------------------------- |
| Layer          | `industry_chain_edge`                               |
| 模块           | **→ 五层域 文件30** `layer3_config_health_check.md` |
| 契约 / 文档    | **→ 五层域 文件24** node registry                   |
| 数据与基础设施 | 有向边 · 禁止悬空端点                               |

---

### 文件26 · `specs/layer3_global_industry_chains/design/layer3_global_industry_chains_v1_2/layer3_cross_chain_edge_registry.json`

**定位** Layer3 跨产业链传导边（AI 主链跨链联动）

**涉及内容**

- 跨 `chain_id` 的传导边（方案 B 核心增量）
- AI 基础设施主链与其他链的联动关系
- 端点引用 node_id 完整性约束
- 前端跨链 graph 展示
- 与链内 edge 分表管理

**跨域触点**

| 类别           | 触点                                                            |
| -------------- | --------------------------------------------------------------- |
| Layer          | cross_chain edge 表族                                           |
| 模块           | Layer3GraphBuilder · 前端 graph view                            |
| 契约 / 文档    | **→ 五层域 文件25** 链内 edge · **→ 五层域 文件33** loader 契约 |
| 数据与基础设施 | 跨链边端点校验                                                  |

---

### 文件27 · `specs/layer3_global_industry_chains/design/layer3_global_industry_chains_v1_2/references/source_registry.md`

**定位** Layer3 P0 锚点官方/权威来源索引（source_keys 可审计依据）

**涉及内容**

- 各 `source_keys` 对应标题、URL 与用途说明
- 覆盖 Microsoft/Meta/Amazon/Alphabet/NVIDIA 等 Capex 与 AI 收入锚
- 半导体、能源、商品等产业链锚点来源
- 供 `source_validation_status=verified` 人工核对
- 禁止 needs_source 的 P0 锚点静默上线

**跨域触点**

| 类别           | 触点                                                          |
| -------------- | ------------------------------------------------------------- |
| Layer          | Layer3 anchor `source_keys`                                   |
| 模块           | **→ 五层域 文件23** anchor registry · data_sync 公告/财报抓取 |
| 契约 / 文档    | **→ 五层域 文件30** 健康检查 P0 来源约束                      |
| 数据与基础设施 | 官方 URL · 财报 press release                                 |

---

### 文件28 · `docs/modules/design/layer4_market_structure.md`

**定位** Layer4 市场结构（各市场内部规则、宽度、板块、制度与内部状态）

**涉及内容**

- 市场范围：CN_A、US_EQ、HK_EQ、CN_FUT、GLOBAL_FUT、OPTIONS、FX
- MarketAdapter 设计（每市场独立适配器）
- 市场宽度、板块扩散、制度性异常（涨跌停、连板、换月）
- 不负责全量个股行情（L5）或宏观 regime（L1）
- 统一 MarketAdapter 接口（calendar、index、sector、breadth、rule_events）

**跨域触点**

| 类别           | 触点                                                 |
| -------------- | ---------------------------------------------------- |
| Layer          | Layer4 market structure snapshot                     |
| 模块           | **→ 五层域 文件29** Layer5 · data_sync MarketAdapter |
| 契约 / 文档    | **→ 五层域 文件2** Layer1 regime 只读引用            |
| 数据与基础设施 | 涨跌停 / 连板 rule_events · sector breadth           |

---

### 文件29 · `docs/modules/design/layer5_security_evidence.md`

**定位** Layer5 个股/合约证据模块（最终证据落点，非技术指标信号层）

**涉及内容**

- 资产范围：股票、ETF、期货、期权、指数、商品代理
- `instrument_registry`、`security_bar_daily` 等核心表
- 证据链可追溯；来源不明新闻不作事实
- 技术指标仅作 baseline/reference
- 不输出买卖建议；须经 WriteManager 写入

**跨域触点**

| 类别           | 触点                                                          |
| -------------- | ------------------------------------------------------------- |
| Layer          | Layer5 evidence chain · latest mapping                        |
| 模块           | **→ 五层域 文件20** Layer3 锚点引用 · Agent evidence tools    |
| 契约 / 文档    | **→ API 域** evidence 路由 · **→ Agent 域** `agent_module.md` |
| 数据与基础设施 | `evidence_chain` · `quality_flags` · QMT 行情接入             |

---

### 文件30 · `docs/ops/design/layer3_config_health_check.md`

**定位** Layer3 产业链配置可执行健康检查（防断边、孤儿节点、P0 来源缺失）

**涉及内容**

- 检查对象：chain/anchor/node/edge/cross_chain registry 与 **→ 五层域 文件27** `references/source_registry.md`
- 结构唯一性与引用完整性（chain_id、anchor→node、edge 端点、跨链边）
- chain / anchor / node 字段完整性（`chain_priority`、`anchor_priority`、`source_validation_status` 等）
- P0 锚点来源约束（`source_keys`、禁止 `needs_source`）
- ticker 类型、私有公司误作行情锚、event_only 等语义检查
- 可执行校验脚本与失败含义（配置不得静默带病上线）

**跨域触点**

| 类别           | 触点                                                                                                                                                                                          |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Layer          | Layer3 shock-anchor · `industry_chain_*` 表初始化                                                                                                                                             |
| 模块           | `Layer3SpecValidator` · `Layer3RegistryLoader` · `Layer3GraphBuilder` · 前端 graph view                                                                                                       |
| 契约 / 文档    | **→ 五层域 文件21–27** Layer3 design 规格 · `docs/modules/design/layer3_industry_shock_anchor.md` · **→ 五层域 文件33** `layer3_loader_contract.yaml` · **→ 五层域 文件1** `05_module_map.md` |
| 数据与基础设施 | `source_validation_status` · P0/P1/P2 优先级 · pytest 健康检查                                                                                                                                |

---

### 文件31 · `specs/contracts/design/layer1_axis_contract.yaml`

**定位** Layer1 五轴指标机器契约（必填字段与 quality_flags 枚举）

**涉及内容**

- `required_indicator_fields`：indicator_id、axis_id、primary_source、fallback_policy 等
- `quality_flags`：MISSING_VALUE、STALE_DATA、SOURCE_SWITCHED、FORBIDDEN_SUBSTITUTE_USED 等
- 与 **→ 五层域 文件3–18** Layer1 轴 YAML 规格对齐
- 权威模块：**→ 五层域 文件2** `layer1_global_regime_panel.md`
- loader/validator 实现与 pytest 绑定

**跨域触点**

| 类别           | 触点                                      |
| -------------- | ----------------------------------------- |
| Layer          | Layer1 observation / snapshot 字段校验    |
| 模块           | Layer1 registry loader · data_sync FRED   |
| 契约 / 文档    | **→ 五层域 文件3** `common_axis_rules.md` |
| 数据与基础设施 | standardized fields · BlindSpot 标注      |

---

### 文件32 · `specs/contracts/design/layer2_sensor_contract.yaml`

**定位** Layer2 跨资产传感器注册表机器契约

**涉及内容**

- `asset_groups`：USD、Rates、Metals、Energy、Volatility 等
- `required_registry_fields`：asset_id、primary_source、is_axis_input、double_count_guard
- `is_axis_input` vs `display_only` 防回写 Layer1
- 权威模块：**→ 五层域 文件19** `layer2_cross_asset_sensor.md`
- registry loader 硬校验规则

**跨域触点**

| 类别           | 触点                                    |
| -------------- | --------------------------------------- |
| Layer          | `cross_asset_registry`                  |
| 模块           | data_sync · **→ 五层域 文件19**         |
| 契约 / 文档    | **→ 五层域 文件2** Layer1 只读引用边界  |
| 数据与基础设施 | double_count_guard · eligible_for_model |

---

### 文件33 · `specs/contracts/design/layer3_loader_contract.yaml`

**定位** Layer3 配置加载器硬校验契约（registry 文件集与 P0 来源规则）

**涉及内容**

- `input_files`：chain YAML + anchor/node/edge/cross_chain JSON
- `hard_validation_rules`：ID 唯一、边端点存在、P0 须有 source_keys
- `source_validation_status` 枚举与 event_only 私有公司规则
- 权威模块：**→ 五层域 文件20** `layer3_industry_shock_anchor.md`
- 与 **→ 五层域 文件30** 健康检查脚本对齐

**跨域触点**

| 类别           | 触点                                       |
| -------------- | ------------------------------------------ |
| Layer          | Layer3 graph 初始化                        |
| 模块           | Layer3RegistryLoader · Layer3SpecValidator |
| 契约 / 文档    | **→ 五层域 文件21–27** design 规格全集     |
| 数据与基础设施 | pytest layer3 config health                |

---

### 文件34 · `specs/contracts/design/layer4_market_contract.yaml`

**定位** Layer4 市场结构表族机器契约（registry / calendar / snapshot）

**涉及内容**

- `market_registry`、`market_calendar`、`market_index_snapshot` 等表 primary_key
- `required_fields` 与 `quality_rules`（非交易日 snapshot、source 必填等）
- 权威模块：**→ 五层域 文件28** `layer4_market_structure.md`
- MarketAdapter 输出边界
- 不负责 Layer5 全量个股行情

**跨域触点**

| 类别           | 触点                                     |
| -------------- | ---------------------------------------- |
| Layer          | Layer4 market structure snapshot         |
| 模块           | MarketAdapter · data_sync                |
| 契约 / 文档    | **→ 五层域 文件28**                      |
| 数据与基础设施 | trade_date · session_type · quality_flag |

---

## 数据存储与分层架构

### 文件1 · `docs/architecture/design/04_data_architecture.md`

**定位** 数据层总架构（DuckDB / Parquet / 文件系统 / staging / clean / snapshot）

**涉及内容**

- 数据分层：Raw → Staging → Clean → Snapshot → API/Agent
- 旁路审计日志族（conflict、revision、resource_guard、agent_run 等）
- 存储边界表（DuckDB / Parquet / 文件系统 / specs / audit 各司其职）
- DuckDB 表族（registry、observation、snapshot、quality、report）
- Staging / Clean / Snapshot / Audit 语义；`primary-grade` vs `degraded clean`
- 数据生命周期、schema 版本、Parquet 分区、specs 与 DB 映射
- 数据访问边界表（Frontend / Agent / DataSync / Ops）与验收测试

**跨域触点**

| 类别           | 触点                                                                                                                                        |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Layer          | Layer1 axis 表 · Layer3 industry_chain 表 · 各层 snapshot                                                                                   |
| 模块           | WriteManager · ReadOnlyRepository · Agent tools · DataSync                                                                                  |
| 契约 / 文档    | `specs/schema/schema.sql` · `specs/contracts/`\* · `docs/modules/design/duckdb_and_parquet.md` · `docs/modules/design/local_file_system.md` |
| 数据与基础设施 | `file_registry` · `source_conflict` · `write_audit_log` · `degraded clean` / FallbackPolicy · ResourceGuard · Parquet 分区路径              |

---

### 文件2 · `docs/modules/design/duckdb_and_parquet.md`

**定位** DuckDB 与 Parquet 数据底座模块（表族、归档、schema 与查询边界）

**涉及内容**

- DuckDB / Parquet / 文件系统三层存储边界与分工
- Raw → Staging → Validation → WriteManager → Clean 流水线
- DuckDB 表族命名、建表、分层与 Parquet 分区归档策略
- 避免 DuckDB 被误用为高并发业务库的五条规则
- schema version 与上层模块统一读取可信数据
- 与 WriteManager、ReadOnlyRepository 的协作边界

**跨域触点**

| 类别           | 触点                                                                          |
| -------------- | ----------------------------------------------------------------------------- |
| Layer          | 各层 registry / observation / snapshot 表族                                   |
| 模块           | **→ 本域 文件4** `write_manager.md` · **→ 本域 文件3** `local_file_system.md` |
| 契约 / 文档    | **→ 数据存储域 文件1** `04_data_architecture.md` · `specs/schema/schema.sql`  |
| 数据与基础设施 | Clean / Snapshot / Audit 表 · Parquet `data/parquet/` 分区 · `schema_version` |

---

### 文件3 · `docs/modules/design/local_file_system.md`

**定位** 本地文件系统模块（原始资料仓库、文件型数据湖与审计留痕）

**涉及内容**

- `data/` 目录结构（raw、files、parquet、audit、reports、cache、backups）
- DuckDB 与文件系统分工：结构化查询 vs 原始 PDF/HTML/ZIP 证据
- Raw Store / File Lake / Audit Store 边界
- 原始证据保留策略；DuckDB 只存路径、hash 与元数据
- `file_registry` 与手动导入证据登记

**跨域触点**

| 类别           | 触点                                                                             |
| -------------- | -------------------------------------------------------------------------------- |
| 模块           | WriteManager · Agent manual import · **→ 数据源域** `data_sources.md`            |
| 契约 / 文档    | **→ 本域 文件1** `04_data_architecture.md` · **→ 隐私域** `privacy_data_flow.md` |
| 数据与基础设施 | `data/raw/` · `data/files/` · `data/audit/` · pre-migration 备份目录             |

---

### 文件4 · `docs/modules/design/write_manager.md`

**定位** 系统唯一标准写入口（所有 clean / snapshot / audit 写入须经 WriteManager）

**涉及内容**

- staging → validation → WriteManager → clean 写入链路
- 组件划分：ValidationGate、MergePlanner、TransactionRunner、WriteLockManager
- DuckDB 单写边界、短事务与失败回滚
- primary-grade vs degraded clean 区分与写入规则
- 禁止前端 / Agent / adapter 绕过写库直写 clean
- `write_audit_log` STARTED / COMMITTED / FAILED 语义

**跨域触点**

| 类别           | 触点                                                                                                   |
| -------------- | ------------------------------------------------------------------------------------------------------ |
| 模块           | DataSyncOrchestrator · DataQualityValidator · **→ 数据同步域 文件5** `data_validation_and_conflict.md` |
| 契约 / 文档    | **→ 运维域** `lock_and_concurrency_policy.md` · **→ 本域 文件2** `duckdb_and_parquet.md`               |
| 数据与基础设施 | `DuckDBWriteManager` · `data/duckdb/.write.lock` · degraded clean merge                                |

---

### 文件5 · `specs/contracts/design/snapshot_lineage_contract.yaml`

**定位** Layer1–5 Snapshot 血缘与可重现性机器契约

**涉及内容**

- 必填字段：snapshot_id、as_of_timestamp、source_dataset_ids、rule_version、parameter_hash
- `no_future_data`：as_of 不得晚于输入观测可见时间
- `deterministic_rebuild`：同输入同规则须重现业务结果
- `agent_outputs_not_source`：Agent 散文不得进入 source_dataset_ids
- 验收测试：future input 拒绝、lineage 含 source hash

**跨域触点**

| 类别           | 触点                                                                                       |
| -------------- | ------------------------------------------------------------------------------------------ |
| Layer          | Layer1–5 snapshot 全层                                                                     |
| 模块           | snapshot builder · Agent tools 只读                                                        |
| 契约 / 文档    | **→ 本域 文件1** `04_data_architecture.md` · **→ 运维域 文件11** `log_audit_contract.yaml` |
| 数据与基础设施 | incremental rebuild · upstream_snapshot_ids                                                |

---

## 数据同步与运行时编排

### 文件1 · `docs/architecture/design/03_runtime_flows.md`

**定位** 系统运行时关键链路（每日 / 盘中 / 回补 / 冲突 / 报告 / 恢复）

**涉及内容**

- 总链路：Scheduler/CLI → ResourceGuard → Sync → Validator → WriteManager → API/前端/Agent
- 每日盘后 10 步链路与 eco 模式资源限制
- 盘中轻量链路与禁止项（FullLoad / 大范围 Backfill 等）
- Layer1 / Layer3 更新链路
- 数据冲突、回补、报告、API 读取、备份恢复链路
- ResourceGuard 介入点与 PAUSE 行为
- 盘中提醒链路与回测复盘链路

**跨域触点**

| 类别           | 触点                                                                                                                                                             |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Layer          | Layer1 axis 更新 · Layer3 graph/snapshot · Layer5 latest mapping                                                                                                 |
| 模块           | `DataSyncOrchestrator` · `DataQualityValidator` · `SourceConflictValidator` · `ReconcileJob` · Agent staging · `ReportBuilder` · `AlertRuleEngine` · Backtest    |
| 契约 / 文档    | **→ API 域** FastAPI Response Envelope · `QUERY_TOO_LARGE` · `docs/modules/design/data_sync_orchestrator.md` · `docs/modules/design/notification_and_reports.md` |
| 数据与基础设施 | ResourceGuard · WriteManager · `source_conflict` · `no_action_semantics_guard` · BackupManager · smoke test                                                      |

---

### 文件2 · `docs/ops/design/idempotency_retry_dlq_policy.md`

**定位** 数据同步幂等、重试退避、死信与部分成功策略（QM-AUD-011）

**涉及内容**

- `idempotency_key` 组成与重复执行行为（成功复用 / 失败重试 / running 超时转人工）
- 按错误类型的重试策略（NETWORK、RATE_LIMIT、AUTH、SCHEMA_DRIFT 等）
- `manual_review_queue` 死信字段与推荐下一步动作
- 批量任务 item-level 状态与部分成功补偿规则
- snapshot 构建只能读取通过 quality gate 的 clean 数据

**跨域触点**

| 类别           | 触点                                                                                                               |
| -------------- | ------------------------------------------------------------------------------------------------------------------ |
| 模块           | `DataSyncOrchestrator` · `DataQualityValidator` · `ReconcileJob` · `docs/modules/design/data_sync_orchestrator.md` |
| 契约 / 文档    | **→ 文件1** `03_runtime_flows.md` 冲突/回补链路                                                                    |
| 数据与基础设施 | staging · clean merge · `source_conflict` · manual review                                                          |

---

### 文件3 · `docs/ops/design/lock_and_concurrency_policy.md`

**定位** DuckDB 单写多读、文件锁与崩溃恢复（QM-AUD-009）

**涉及内容**

- 单写多读、短事务；所有 clean 写入经 `DuckDBWriteManager`
- 跨进程写锁（如 `data/duckdb/.write.lock`）
- 读连接 `read_only=True` 与 writer 一致的 memory/threads/temp 配置
- `write_audit_log` STARTED/COMMITTED/FAILED 与启动时 ABANDONED 扫描
- 禁止自动重放长时间停留的 STARTED 写任务

**跨域触点**

| 类别           | 触点                                                                                |
| -------------- | ----------------------------------------------------------------------------------- |
| 模块           | WriteManager · DataSync · ReadOnlyRepository                                        |
| 契约 / 文档    | **→ 数据存储域** `04_data_architecture.md` · `docs/modules/design/write_manager.md` |
| 数据与基础设施 | DuckDB 并发 · `write_audit_log` · `test_concurrentWriters_secondWriterBlocked` 等   |

---

### 文件4 · `docs/modules/design/data_sync_orchestrator.md`

**定位** 数据同步总控模块（全量、增量、回补、修订审计、冲突重抓 Job 解耦）

**涉及内容**

- `DataSyncOrchestrator` 与六类 Job：FullLoad / Incremental / Backfill / RevisionAudit / Reconcile / DataQuality
- `data_sync_job` 表与任务状态机
- 日常增量基于 cursor / hash 只补缺失，禁止无差别全量重抓
- RevisionAudit 检测历史修订（`content_hash` / `revision_id`）
- ReconcileJob 多源冲突重抓与人工确认 escalation
- CLI、调度策略、失败恢复与审计协议

**跨域触点**

| 类别           | 触点                                                                                                         |
| -------------- | ------------------------------------------------------------------------------------------------------------ |
| Layer          | Layer1 五轴历史 · Layer2 跨资产 · Layer3/4 基础映射初始化                                                    |
| 模块           | **→ 数据同步域 文件5** `data_validation_and_conflict.md` · **→ 本域 文件4** `write_manager.md`（数据存储域） |
| 契约 / 文档    | **→ 本域 文件1** `03_runtime_flows.md` · **→ 本域 文件2–3** 幂等/锁策略                                      |
| 数据与基础设施 | ResourceGuard · `idempotency_key` · manual_review_queue                                                      |

---

### 文件5 · `docs/modules/design/data_validation_and_conflict.md`

**定位** 数据质量检查与多源冲突治理（单份合格 vs 多源打架）

**涉及内容**

- `DataQualityValidator` 与 `SourceConflictValidator` 职责分离
- staging → validation → ValidationGate → clean / conflict 流程
- `validation_request` 输入与 ValidationReport 输出字段
- 质量检查（如 high < low）vs 冲突检查（多源 close 差异）
- 与 ReconcileJob、WriteManager 协作；snapshot 只读通过 gate 的 clean
- 原始数据永不删除、标准表只存一个主值

**跨域触点**

| 类别           | 触点                                                                                           |
| -------------- | ---------------------------------------------------------------------------------------------- |
| 模块           | **→ 数据源域 文件1** `data_sources.md` 冲突原则 · **→ 本域 文件4** `data_sync_orchestrator.md` |
| 契约 / 文档    | **→ 数据存储域 文件4** `write_manager.md` · `source_conflict` 表语义                           |
| 数据与基础设施 | `source_conflict` · degraded clean · 人工确认清单                                              |

---

### 文件6 · `specs/contracts/design/runtime_flow_contract.yaml`

**定位** 运行时流程机器契约（盘后 / 盘中 / 回补等 flow 步骤与禁止项）

**涉及内容**

- `daily_after_close`：eco 模式步骤链（incremental → validation → write → snapshot → report → backup）
- `intraday_light`：P0 watchlist、核心指数、Layer3 P0 锚点范围
- 各 flow 的 `forbidden` 清单（full_load、large_backfill、全市场分钟扫描等）
- `resource_profile` 与 ResourceGuard 对齐
- 与 **→ 本域 文件1** `03_runtime_flows.md` 叙事一致

**跨域触点**

| 类别           | 触点                                                                                |
| -------------- | ----------------------------------------------------------------------------------- |
| 模块           | DataSyncOrchestrator · scheduler · ResourceGuard                                    |
| 契约 / 文档    | **→ 本域 文件1** `03_runtime_flows.md` · **→ 运维域 文件13** `resource_limits.yaml` |
| 数据与基础设施 | eco 默认 · incremental_update 步骤序                                                |

---

### 文件7 · `specs/contracts/design/source_conflict_rules.yaml`

**定位** 多源冲突判定机器契约（可比字段、阈值与严重级别）

**涉及内容**

- `comparable_fields`：objective_fact（OHLCV 等）vs separate_by_source（口径差异）
- `thresholds`：market_bar_1d close/volume 相对 warning/severe 阈值
- futures_bar、index_level 等域别阈值
- 与 SourceConflictValidator 实现绑定
- 冲突 escalation 至 manual_review

**跨域触点**

| 类别           | 触点                                                                                        |
| -------------- | ------------------------------------------------------------------------------------------- |
| 模块           | **→ 本域 文件5** `data_validation_and_conflict.md` · **→ 数据源域 文件1** `data_sources.md` |
| 契约 / 文档    | `source_conflict` 表 · **→ 排障域** ERROR_CODE_GUIDE                                        |
| 数据与基础设施 | relative_warning / relative_severe                                                          |

---

## 数据源注册与路由

### 文件1 · `docs/modules/design/data_sources.md`

**定位** 数据源注册与优先级模块（多源分层、冲突原则与 `source_registry`）

**涉及内容**

- 数据源分层表（QMT、baostock、AkShare、CNINFO、东财、Yahoo 等角色定位）
- `source_registry` 表结构与 trust_level / priority / is_enabled
- 多源冲突六级治理（raw 保留 → 标准化 → 分级 → 人工确认）
- 客观事实类 vs 口径差异类字段处理规则
- Primary / Validation / FallbackPolicy 数据源角色
- 原始数据永不删除、标准表只保存一个主值

**跨域触点**

| 类别           | 触点                                                                                                                                                                        |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 模块           | **→ 本域 文件2–4** capability / route / 来源质量契约 · **→ 本域 文件5** QMT adapter · DataSync                                                                              |
| 契约 / 文档    | `specs/contracts/design/source_provenance_quality_contract.yaml` · `specs/contracts/platform_source_matrix.yaml` · **→ 数据同步域 文件5** `data_validation_and_conflict.md` |
| 数据与基础设施 | `source_registry` · `source_conflict` · silent fallback 禁止                                                                                                                |

---

### 文件2 · `docs/modules/design/source_capability_registry.md`

**定位** `SourceCapabilityRegistry`：声明 source/domain/operation/field 细粒度能力

**涉及内容**

- 与 `SourceRegistry` 职责分离；绑定 `source_capabilities.yaml`
- Adapter `supported_domains` 必须是 capability 子集
- fetch 前必须确认 capability 存在
- Capability 不授予 fallback 权限
- 未来实现 `backend/app/datasources/capability_registry.py`

**跨域触点**

| 类别           | 触点                                                                                   |
| -------------- | -------------------------------------------------------------------------------------- |
| 模块           | DataSourceService · 各 vendor adapter · **→ 本域 文件3** `source_route_plan.md`        |
| 契约 / 文档    | `specs/contracts/source_capability_contract.yaml` · **→ 本域 文件1** `data_sources.md` |
| 数据与基础设施 | `CAPABILITY_MISSING` 错误码 · route-preview                                            |

---

### 文件3 · `docs/modules/design/source_route_plan.md`

**定位** 运行时显式源路由计划（选源、跳过、fallback、禁止 silent fallback）

**涉及内容**

- RoutePlan 必录字段（route_status、candidates、quality_flags、route_grade）
- 关键状态：READY / READY_DEGRADED / BLOCKED_MANUAL_REVIEW / NO_AVAILABLE_SOURCE 等
- FallbackPolicy 决策记录与失败原因枚举
- `route_grade=primary|degraded|blocked` 防误读
- 缺授权时须返回 `USER_AUTH_REQUIRED`

**跨域触点**

| 类别           | 触点                                                                                       |
| -------------- | ------------------------------------------------------------------------------------------ |
| 模块           | DataSyncOrchestrator · **→ 本域 文件2** capability registry                                |
| 契约 / 文档    | `specs/contracts/source_route_contract.yaml` · **→ 排障域** ERROR_CODE_GUIDE · INC-001/004 |
| 数据与基础设施 | `disabled_reason` · qmt_xqshare env gate                                                   |

---

### 文件4 · `specs/contracts/design/source_provenance_quality_contract.yaml`

**定位** 跨数据源、质量、五层、API、前端与告警的来源风险／质量语义契约

**涉及内容**

- `PRIMARY|DEGRADED` 与 `QUALITY_PASSED|QUALITY_FAILED` 的独立枚举
- RoutePlan、来源、覆盖层版本、失败原因与内容版本的最小血缘字段
- 可信最终库、连续监控区、审计归档区的写入与默认读取边界
- `MISSING`、人工复核、主源恢复与异常 payload 留存不可违反规则

**跨域触点**

| 类别 | 触点                                                                                    |
| ---- | --------------------------------------------------------------------------------------- |
| 模块 | Source Registry · RoutePlan · WriteManager · Layer1–5 · API · Frontend · Notification   |
| 决策 | `docs/decisions/design/ADR-017-dynamic-source-fallback-and-exception-data-lifecycle.md` |

---

### 文件5 · `docs/modules/design/qmt_xtdata_adapter.md`

**定位** QMT/xtdata 适配层封装（业务层不得直接调用 QMT API）

**涉及内容**

- `QMTDataAdapter` 接口（历史缓存、K 线、实时行情、订阅）
- 内部 API 版本选择（download_history_data、get_market_data_ex 等）
- 第一版默认禁用，须用户确认安装路径与授权（D-11）
- `qmt_xqshare` 可选远程源边界与禁止自动探测/登录
- Phase A 不修改 registry、不新增未登记 adapter

**跨域触点**

| 类别           | 触点                                                                               |
| -------------- | ---------------------------------------------------------------------------------- |
| 模块           | DataSourceService · **→ 本域 文件6** `qmt_xqshare_setup.md`                        |
| 契约 / 文档    | **→ 本域 文件1** `data_sources.md` · **→ 运维域** `06_deployment_and_local_ops.md` |
| 数据与基础设施 | xtdata 本地路径 · optional extra `qmt`                                             |

---

### 文件6 · `docs/ops/design/qmt_xqshare_setup.md`

**定位** 可选远程 QMT 源 `qmt_xqshare` 的配置与路由边界

**涉及内容**

- `qmt_xqshare` 默认禁用，仅用户明确配置远程 QMT 授权后可调度
- 必需环境变量 `XQSHARE_REMOTE_HOST` / `XQSHARE_REMOTE_PORT`
- 禁止自动探测端口、自动登录、处理验证码、默认启用、silent fallback
- 缺 env 或授权时 `SourceRoutePlan` 须返回 `USER_AUTH_REQUIRED`
- 凭证须放 `.env.local` 或用户确认的本地 secret 机制

**跨域触点**

| 类别           | 触点                                                                                                                                                      |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 模块           | `DataSourceService` · QMT / xtdata 适配器                                                                                                                 |
| 契约 / 文档    | `specs/contracts/platform_source_matrix.yaml` · `source_route_contract.yaml` · `source_capabilities.yaml` · **→ 运维域** `06_deployment_and_local_ops.md` |
| 数据与基础设施 | `disabled_reason=missing_xqshare_env_or_user_authorization` · **→ 排障域** INC-004                                                                        |

---

## API 相关功能权威文档

### 文件1 · `docs/api/design/agent_tool_contracts.md`

**定位** Agent 工具 API 与数据边界实现

**涉及内容**

- 8 个 `GET/POST /api/agent-tools/*` 路径（layer1~5 context、evidence、data-health、submit-staging）
- Agent 工具允许/禁止能力（只读 snapshot 与 evidence、写 staging、禁 SQL/clean/Repository 绕过/联网/重任务/交易语义）
- 统一 Tool Response 必填字段（`evidence_refs`、`quality_flags`、`truncated` 等）
- 各工具默认行数与硬上限（局部上限不得高于 `api_security_contract` 全局 200/1000）
- Layer1 / Layer3 / Evidence 工具的 Query Params 与返回字段
- `submit-staging` 请求体、`no_action_semantics_guard` 禁词表与拒绝规则
- Agent 工具验收测试清单

**跨域触点**

| 类别           | 触点                                                                                                                         |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Layer          | Layer1 五轴 · Layer2 传感器 · Layer3 产业链 · Layer4 市场结构 · Layer5 证据摘要                                              |
| 契约 / 文档    | `docs/modules/design/agent_module.md` · `specs/contracts/agent_contract.yaml` · `specs/contracts/api_security_contract.yaml` |
| 数据与基础设施 | `evidence_chain` · `data_health` / `RESOURCE_GUARD_PAUSED` · `agent_output_staging` · FastAPI / Repository / DuckDB 只读边界 |

---

### 文件2 · `docs/api/design/fastapi_routes.md`

**定位** API 路由级实现清单与全局契约

**涉及内容**

- 全部路由全局约束（Response Envelope、分页、`quality_flags`/`source_used`、禁直拼 SQL / 绕过 Repository / 直写 clean）
- 默认调用链：Router → Validation → Service → ReadOnlyRepository → DuckDB / Parquet / Snapshot
- 本机资源友好限制（`page_size`、`date_range`、分钟线范围、超时、`query_cost`）
- 路由组：market / layer1~5 / evidence / reports / data-health / agent-tools / admin / notifications / backtest
- 统一错误码与 Admin Job 仅 `REQUESTED` 任务
- D-02 API 安全模式；`api_security_contract.yaml` 为分页与 token 机器权威

**跨域触点**

| 类别           | 触点                                                                                                 |
| -------------- | ---------------------------------------------------------------------------------------------------- |
| Layer          | Layer1~5 全层读接口                                                                                  |
| 模块           | `docs/modules/design/fastapi_backend.md` · 日报/周报 · 通知中心 · 回测复盘 · **→ 文件1** agent-tools |
| 契约 / 文档    | `specs/contracts/api_security_contract.yaml` · `agent_contract.yaml`                                 |
| 数据与基础设施 | `evidence_chain` · data_health / source_conflict · ResourceGuard · ReadOnlyRepository · 后台任务边界 |

---

### 文件3 · `docs/modules/design/fastapi_backend.md`

**定位** FastAPI 后端实现级设计（将 DuckDB/Parquet/文件索引以稳定 API 暴露）

**涉及内容**

- 只读边界：不直接抓数、不绕过 WriteManager 写库
- 服务目录结构（routers、schemas、services、ReadOnlyRepository）
- 统一分页、freshness、`quality_flags`、错误码与 Response Envelope
- Layer1–5、evidence、reports、data_health、agent_tools 路由实现落点
- 与 **→ API 域 文件2** `fastapi_routes.md` 路由清单对齐
- 前端与 Agent 权限边界分离

**跨域触点**

| 类别           | 触点                                                                                                             |
| -------------- | ---------------------------------------------------------------------------------------------------------------- |
| Layer          | Layer1~5 全层读服务                                                                                              |
| 模块           | **→ 前端域 文件2** `frontend_dashboard.md` · **→ Agent 域** agent-tools                                          |
| 契约 / 文档    | **→ API 域 文件2** `fastapi_routes.md` · **→ API 域 文件4** `openapi_contract.md` · `api_security_contract.yaml` |
| 数据与基础设施 | ReadOnlyRepository · `QUERY_TOO_LARGE` · page_size 200/1000                                                      |

---

### 文件4 · `specs/api/design/openapi_contract.md`

**定位** OpenAPI Contract v1（Response Envelope 与路由组机器落点）

**涉及内容**

- 统一响应 Envelope：`ok` / `data` / `meta` / `errors` 必填结构
- `meta` 字段：as_of_timestamp、quality_flags、source_used、分页（page/page_size/total）
- 必须实现的路由组：`/api/market` · layer1~5 · evidence · reports · data-health · agent-tools
- 禁止 router 直拼 SQL、API 直写 clean、无分页大历史、Agent 返回无来源数据
- 权威实现对齐 **→ API 域 文件3** `fastapi_backend.md`；供 OpenAPI 生成与校验

**跨域触点**

| 类别           | 触点                                                                             |
| -------------- | -------------------------------------------------------------------------------- |
| Layer          | Layer1~5 读接口 envelope 一致性                                                  |
| 模块           | **→ API 域 文件2** `fastapi_routes.md` · **→ API 域 文件3** `fastapi_backend.md` |
| 契约 / 文档    | `specs/contracts/api_security_contract.yaml` · `agent_contract.yaml`             |
| 数据与基础设施 | page_size 200 默认 · quality_flags 透传                                          |

---

## Agent 相关功能权威文档

### 文件1 · `docs/ops/design/agent_security_policy.md`

**定位** Agent 工具安全、来源白名单与提示注入防护（D-12 / QM-AUD-015）

**涉及内容**

- D-12 已拍板来源策略：固定 adapter、用户手动导入、已登记 file_registry；禁自由联网
- Agent 工具白名单与 `agent_contract.yaml` 登记字段（max_rows、PII、output_schema 等）
- 禁止自由 SQL、直写 DuckDB、联网抓新闻、LLM 覆盖数据库事实、交易动作语义
- 用户手动导入文本须进 registry、仅作待验证 evidence
- 提示注入防护（忽略数据源内嵌指令）
- 验收测试（free SQL、unknown tool、free web search、prompt injection 等）

**跨域触点**

| 类别           | 触点                                                                                 |
| -------------- | ------------------------------------------------------------------------------------ |
| Layer          | Layer1~5 context 读取边界                                                            |
| 模块           | `docs/modules/design/agent_module.md` · **→ API 域 文件1** `agent_tool_contracts.md` |
| 契约 / 文档    | `specs/contracts/agent_contract.yaml` · `file_registry` · `text_source_registry`     |
| 数据与基础设施 | `evidence_ids` · `facts_used` · `no_action_semantics` · manual import 审计           |

---

### 文件2 · `docs/modules/design/agent_module.md`

**定位** Agent 模块实现级文档（解释、摘要、结构化报告与问答）

**涉及内容**

- Agent 清单：日报、新闻事件、公告、五轴解释、五层解释、数据质量、策略复盘
- 统一受控工具边界（`get_layer*_snapshot` 等只读工具）
- 禁止工具：自由 SQL、直写 DuckDB、自由联网、交易动作语义
- 各 Agent 写库权限（仅 report staging / event staging）
- 不把 LLM 推理当成数据库事实；`facts_used_json` 追溯
- 与 **→ API 域 文件1** `agent_tool_contracts.md` 路径与字段对齐

**跨域触点**

| 类别           | 触点                                                                             |
| -------------- | -------------------------------------------------------------------------------- |
| Layer          | Layer1~5 context 读取 · evidence 摘要                                            |
| 模块           | **→ 通知域** `notification_and_reports.md` · **→ 隐私域** `privacy_data_flow.md` |
| 契约 / 文档    | **→ 本域 文件1** `agent_security_policy.md` · `agent_contract.yaml`              |
| 数据与基础设施 | `agent_output_staging` · `no_action_semantics_guard` · ResourceGuard 行数限制    |

---

## 模块边界与工程契约

### 文件1 · `docs/architecture/design/module_boundary_matrix.md`

**定位** 模块 import 边界矩阵（低耦合工程契约）

**涉及内容**

- 六条总原则（datasource 不写 clean、sync 不依赖 API/Agent、API 不 import adapter 等）
- 关键禁止边界表（datasources / api / agents / layer\* / frontend）
- Layer 模块不得直连 `DataSourceService`，须经 sync seam
- 检查脚本 `check_module_boundaries.py` 与 pytest
- 机器契约 `specs/contracts/module_boundary_contract.yaml`

**跨域触点**

| 类别           | 触点                                                                                                                                  |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Layer          | `layer1_axes` … `layer5_evidence` 的 `must_not_import`                                                                                |
| 模块           | `backend.app.datasources` · `backend.app.api` · `backend.app.agents` · `backend.app.sync` · WriteManager · vendor adapters · frontend |
| 契约 / 文档    | `specs/contracts/module_boundary_contract.yaml` · `tests/test_module_boundaries.py`                                                   |
| 数据与基础设施 | EasyXT 低耦合理念 · `sync_indicator` seam · 全树边界扫描须保持绿色                                                                    |

---

## 运维与本地部署

### 文件1 · `docs/architecture/design/06_deployment_and_local_ops.md`

**定位** 部署形态与本地运维入口（指向 ops 细则）

**涉及内容**

- 本地优先部署形态（DuckDB 单写多读、前端/Agent 经 FastAPI）
- 运维文件索引（手册、验证命令、同步速查、排障、qmt_xqshare）
- Canonical 生产 DuckDB 路径与 `QMD_DATA_ROOT` 隔离规则（ACC-USER-LIVE-PATH）
- 运维逃生口 `QMD_SYNC_ALLOW_ADAPTER=1` 限制
- CI 一键初始化 `init_db.py --sync-registry` 与 perf budget 产物
- 平台矩阵与 optional extras 边界摘要

**跨域触点**

| 类别           | 触点                                                                                                                                                                                                                           |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 模块           | 数据同步 CLI · QMT / qmt_xqshare · 回测 / Agent / docs site optional extras                                                                                                                                                    |
| 契约 / 文档    | **→ 本域 文件2** `docs/ops/design/ops_and_performance_v1_2.md` · `specs/contracts/platform_source_matrix.yaml` · `specs/contracts/dependency_extras_contract.yaml` · `specs/contracts/production_equivalent_smoke_budget.yaml` |
| 数据与基础设施 | `<PROJECT_ROOT>/data/duckdb/quant_monitor.duckdb` · `.audit-sandbox/` · `pyproject.toml` / `package.json` 变更门禁 · baostock/akshare/qmt/yahoo 平台表                                                                         |

---

### 文件2 · `docs/ops/design/ops_and_performance_v1_2.md`

**定位** 运维与性能手册 v1.2（本地文件系统 / DuckDB / Parquet / 同步 / 备份总手册）

**涉及内容**

- DuckDB、本地文件系统、Parquet 三类存储分工与 `data/` 目录规范
- DuckDB 单写多读、写入流程与库文件备份要点
- Parquet 分区规范与转档时机
- 五类同步任务运维规则（FullLoad / Incremental / Backfill / Revision / Reconcile）
- 多源冲突处理（客观字段 / 口径差异 / 主源失效接管）
- 内存、磁盘、查询性能与 Agent 查询限制
- 备份恢复、日志审计、健康检查与运维清单（与细分 policy 配套）

**跨域触点**

| 类别           | 触点                                                                                                                                  |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Layer          | Layer3 配置健康检查章节 · Layer1 历史观测 Parquet                                                                                     |
| 模块           | DataSync · ResourceGuard · BackupManager · 前端/API 查询                                                                              |
| 契约 / 文档    | **→ 本域** `performance_limits.md` · `backup_and_recovery.md` · `daily_weekly_monthly_checklist.md` · `layer3_config_health_check.md` |
| 数据与基础设施 | v1.6 配套运维手册 · raw/parquet/audit 目录 · ReconcileJob                                                                             |

---

### 文件3 · `docs/ops/design/performance_limits.md`

**定位** ResourceGuard 与本机资源限制权威实现（Conservative Desktop Mode）

**涉及内容**

- 总原则：少占资源、重任务后台化、查询分页、磁盘硬停止线
- 三档资源模式 `eco` / `normal` / `batch` 的 CPU、内存、DuckDB、临时目录上限
- 查询超时、`query_cost` 分级与 HEAVY 任务禁止前台执行
- ResourceGuard PAUSE/STOP 行为与日志
- 与 `api_security_contract`、FastAPI、Agent 行数上限的对齐

**跨域触点**

| 类别           | 触点                                                                                                                     |
| -------------- | ------------------------------------------------------------------------------------------------------------------------ |
| 模块           | DataSync · Backtest · Report · Backup · API · Agent tools                                                                |
| 契约 / 文档    | `specs/contracts/resource_limits.yaml` · `specs/contracts/api_security_contract.yaml` · **→ API 域** `fastapi_routes.md` |
| 数据与基础设施 | `resource_guard_log` · `QUERY_TOO_LARGE` · `RESOURCE_GUARD_PAUSED` · eco 默认模式                                        |

---

### 文件4 · `docs/ops/design/daily_weekly_monthly_checklist.md`

**定位** 日 / 周 / 月轻量运维检查清单

**涉及内容**

- 每日 10 项轻量检查（ResourceGuard、增量任务、source_health、quality/conflict、备份、cache/磁盘）
- 每日禁止项（全历史审计、全量 snapshot 重建、大范围 backfill 等）
- 每日输出 `daily_health_YYYYMMDD.md` 必含字段
- 每周检查（备份抽检、Parquet 索引、Layer3 配置健康、日志体积）
- 每月检查（归档 dry-run、留存策略、恢复演练提醒）

**跨域触点**

| 类别           | 触点                                                                                                               |
| -------------- | ------------------------------------------------------------------------------------------------------------------ |
| Layer          | Layer3 配置健康（周检）                                                                                            |
| 模块           | IncrementalUpdateJob · data_health_summary · notification                                                          |
| 契约 / 文档    | **→ 本域** `logs_health_audit.md` · `backup_and_recovery.md` · **→ 五层域 文件30** `layer3_config_health_check.md` |
| 数据与基础设施 | `data/cache` 1GB · `data/backups` 10GB · 磁盘 30GB 警戒线                                                          |

---

### 文件5 · `docs/ops/design/backup_and_recovery.md`

**定位** 本机低占用备份与恢复实现（`backup_manager` / `restore_manager`）

**涉及内容**

- 必须备份 / 按策略备份 / 默认不备份对象清单
- `data/backups/` 目录结构（daily、weekly、before_schema_change、manifest）
- 备份触发时机与 ResourceGuard、WriteManager idle 协调
- 恢复流程：停调度 → 备份坏库 → 校验 manifest → 恢复 → smoke test → 人工确认
- 恢复演练频率与验收要求

**跨域触点**

| 类别           | 触点                                                                                                                                       |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| 模块           | BackupManager · RestoreManager · scheduler                                                                                                 |
| 契约 / 文档    | `specs/contracts/backup_recovery_contract.yaml` · **→ 本域 文件6** `migration_recovery_policy.md` · **→ 数据同步域** `03_runtime_flows.md` |
| 数据与基础设施 | `quant_monitor.duckdb` · `specs/` · `data/audit/` · manifest hash                                                                          |

---

### 文件6 · `docs/ops/design/migration_recovery_policy.md`

**定位** Schema migration 回滚与恢复策略（D-06 / QM-AUD-008）

**涉及内容**

- D-06：非破坏性可无 down SQL；破坏性必须先备份再执行
- migration 元数据基线（version、checksum、`pre_migration_backup_path` 等）
- 执行顺序：锁 → 破坏性判断 → 备份 → up → smoke → 失败恢复
- 禁止手写 ALTER、改写旧 migration、无恢复方案的 prod migration
- 与 schema 版本表、audit 的联动

**跨域触点**

| 类别           | 触点                                                            |
| -------------- | --------------------------------------------------------------- |
| 模块           | migration runner · ResourceGuard · BackupManager                |
| 契约 / 文档    | `specs/schema/schema.sql` · **→ 本域 文件5**                    |
| 数据与基础设施 | migration lock · `schema_version` · `before_schema_change` 备份 |

---

### 文件7 · `docs/ops/design/logs_health_audit.md`

**定位** 日志、健康检查与审计实现（`data/audit/` 族）

**涉及内容**

- 审计日志目录与文件清单（fetch、quality、conflict、write、resource_guard、agent_run 等）
- 日志通用 JSON 字段与严重级别
- 健康检查事件类型与 `ops_health_log` 写入规则
- 日志轮转、体积上限与禁止静默删除 audit
- 与 data_health API、运维清单的衔接

**跨域触点**

| 类别           | 触点                                                                   |
| -------------- | ---------------------------------------------------------------------- |
| Layer          | 各层 snapshot 构建可追溯性                                             |
| 模块           | DataSync · Agent · notification · ResourceGuard                        |
| 契约 / 文档    | **→ 数据存储域** `04_data_architecture.md` · **→ 本域 文件4** 日检清单 |
| 数据与基础设施 | `data/audit/*.ndjson` · `write_audit_log` · **→ 隐私域** 留存策略      |

---

### 文件8 · `docs/ops/design/config_secret_policy.md`

**定位** 配置、Secret 存储、脱敏与扫描（D-03 / QM-AUD-007）

**涉及内容**

- D-03：第一版 `.env.local` + `.env.example` + gitignore + 启动检查 + secret scan
- 配置优先级（环境变量 > `.env.local` > example > yaml > 代码默认）
- Secret 文件规则与 prod 缺失 secret 拒绝启动
- 日志/异常/报告/Agent 输出脱敏字段清单
- Secret scan 与轮换建议；OS keyring 为后续增强

**跨域触点**

| 类别           | 触点                                                                                       |
| -------------- | ------------------------------------------------------------------------------------------ |
| 模块           | FastAPI 启动 · Agent 输出 · 报告/通知                                                      |
| 契约 / 文档    | `specs/contracts/api_security_contract.yaml` · **→ API 域** D-02 · **→ 前端域** token 存储 |
| 数据与基础设施 | `.env.local` · `QMD_API_TOKEN` · SMTP/Webhook secret · pre-commit secret scan              |

---

### 文件9 · `docs/modules/design/ops_and_performance.md`

**定位** 运维模块实现级入口（脚本、检查项、错误码与恢复流程落点）

**涉及内容**

- 运维目标：能启动、检查、备份、恢复、发现异常、解释失败
- 运维范围：目录初始化、DuckDB 备份、Parquet 分区、DataSync/Quality、Layer3 配置健康
- CLI 脚本清单（`qm ops init-directories`、`health-check`、`backup-duckdb` 等）
- `data/` 子目录初始化规则（duckdb/raw/files/parquet/audit/backups）
- API/前端/Agent run log 健康检查衔接
- 详细手册见 **→ 本域 文件2** `ops_and_performance_v1_2.md`

**跨域触点**

| 类别           | 触点                                               |
| -------------- | -------------------------------------------------- |
| Layer          | Layer3 配置健康（周检）                            |
| 模块           | BackupManager · ResourceGuard · notification       |
| 契约 / 文档    | **→ 本域 文件2–8** ops/design 细则全集             |
| 数据与基础设施 | `data/backups/` · daily_health 报告 · eco 模式默认 |

---

### 文件10 · `specs/contracts/design/ops_health_check_contract.yaml`

**定位** 运维健康检查机器契约（检查项枚举与磁盘阈值）

**涉及内容**

- `health_check_status_enum`：ok / warning / critical
- `checks`：duckdb_exists、incremental job、layer3_config_health、api_health、disk_usage 等
- `thresholds`：disk_warning 70% · critical 85% · stop_non_core 95%
- `default_frontend_page_size` / `default_agent_query_limit`：200
- backup 策略布尔开关与 **→ 本域 文件5** 备份文档对齐

**跨域触点**

| 类别           | 触点                                                                  |
| -------------- | --------------------------------------------------------------------- |
| 模块           | **→ 本域 文件9** `ops_and_performance.md` · **→ 本域 文件4** 日检清单 |
| 契约 / 文档    | **→ 五层域 文件30** layer3_config_health                              |
| 数据与基础设施 | `ops_health_log` · disk 警戒线                                        |

---

### 文件11 · `specs/contracts/design/log_audit_contract.yaml`

**定位** 审计日志机器契约（NDJSON 通用字段与必审计事件）

**涉及内容**

- `common_fields`：event_id、event_time、severity、run_id、quality_flags
- `required_logs`：fetch、quality、conflict、write、resource_guard、agent_run 等
- `must_audit`：clean_table_write、schema_migration、agent_run 等
- severity 枚举与默认 runtime 最低 INFO
- 与 **→ 本域 文件7** `logs_health_audit.md` 目录清单对齐

**跨域触点**

| 类别           | 触点                                                                              |
| -------------- | --------------------------------------------------------------------------------- |
| 模块           | DataSync · Agent · WriteManager                                                   |
| 契约 / 文档    | **→ 本域 文件7** `logs_health_audit.md` · **→ 数据存储域 文件5** snapshot_lineage |
| 数据与基础设施 | `data/audit/*.ndjson` · 禁止静默删 audit                                          |

---

### 文件12 · `specs/contracts/design/backup_recovery_contract.yaml`

**定位** 备份恢复机器契约（必备份对象、留存与 workflow）

**涉及内容**

- `required_backup_items`：DuckDB、specs、docs、config、recent audit
- `excluded_by_default`：cache、duckdb_tmp、frontend build artifacts
- `retention`：daily/weekly/before_schema_change 保留份数
- `workflow`：wait_write_manager_idle → checkpoint → manifest → prune
- `size_limits`：backups_warn_gb 10 · pause_gb 15

**跨域触点**

| 类别           | 触点                                                                            |
| -------------- | ------------------------------------------------------------------------------- |
| 模块           | BackupManager · RestoreManager                                                  |
| 契约 / 文档    | **→ 本域 文件5** `backup_and_recovery.md` · **→ 本域 文件6** migration_recovery |
| 数据与基础设施 | `data/backups/` manifest hash                                                   |

---

### 文件13 · `specs/contracts/design/resource_limits.yaml`

**定位** ResourceGuard 资源限制机器契约（eco / normal / batch 三档）

**涉及内容**

- `default_profile: eco` 与三档 CPU、RSS、DuckDB memory/temp 上限
- `batch` 须 `requires_user_confirm: true`
- 查询超时、`query_cost` 分级与 HEAVY 任务规则
- 与 **→ 本域 文件3** `performance_limits.md` 叙事一致
- 对齐 API/Agent 行数上限 200/1000

**跨域触点**

| 类别           | 触点                                                                                    |
| -------------- | --------------------------------------------------------------------------------------- |
| 模块           | ResourceGuard · DataSync · API · Agent                                                  |
| 契约 / 文档    | **→ 本域 文件3** `performance_limits.md` · **→ 数据同步域 文件6** runtime_flow_contract |
| 数据与基础设施 | `RESOURCE_GUARD_PAUSED` · `QUERY_TOO_LARGE`                                             |

---

### 文件14 · `rules/design/OPERATOR_GUIDE.md`

**定位** 运维操作者角色指南（常用入口与安全运行原则）

**涉及内容**

- 运维入口索引：部署入口 · 运行时验收 · 日检清单 · 同步链路/编排 · 幂等与路由 · 错误码/排障/事故手册（均为 `docs/**/design/` 或 `specs/**/design/`）
- 安全运行五步：先 dry-run 再写入 · 先 route-preview 再 fetch · 不绕过 disabled source · ResourceGuard 暂停则缩小范围 · 生产等价验证用隔离 DB
- QMT / qmt_xqshare 默认禁用；启用须用户授权、路径/env 与安全边界
- 与 **→ 排障域**、**→ 数据源域 文件5** 联动

**跨域触点**

| 类别           | 触点                                                                                                                                                                                 |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 模块           | DataSync CLI · SourceRoutePlan · ResourceGuard                                                                                                                                       |
| 契约 / 文档    | **→ 排障域** `ERROR_CODE_GUIDE.md` · `TROUBLESHOOTING.md` · `incident_playbook.md` · **→ 本域 文件1** `06_deployment_and_local_ops.md` · **→ 数据源域 文件5** `qmt_xqshare_setup.md` |
| 数据与基础设施 | dry-run · route-preview · `.audit-sandbox/`                                                                                                                                          |

---

### 文件15 · `rules/design/GLOBAL_RESOURCE_LIMITS.md`

**定位** 本机资源限制人类可读规则（eco 默认、硬暂停与禁止项）

**涉及内容**

- 三档模式 eco / normal / batch 的 CPU、内存、DuckDB memory_limit、临时目录上限表
- 硬暂停：可用内存 < 2GB、磁盘 < 20GB、项目目录 > 25GB 等
- 硬停止线：内存 < 1GB、磁盘 < 10GB、项目目录 > 40GB
- 禁止：默认全市场全历史扫描、前端大范围 backfill、Agent 大查询、无分页 API
- 暂停时须输出 `RESOURCE_GUARD_PAUSED` 与建议动作

**跨域触点**

| 类别           | 触点                                                                                |
| -------------- | ----------------------------------------------------------------------------------- |
| 模块           | ResourceGuard · DataSync · API · Agent                                              |
| 契约 / 文档    | **→ 本域 文件3** `performance_limits.md` · **→ 本域 文件13** `resource_limits.yaml` |
| 数据与基础设施 | eco 默认 · batch 须用户确认 · **→ 排障域** INC-002                                  |

---

## 运维排障与错误处理

### 文件1 · `docs/ops/design/ERROR_CODE_GUIDE.md`

**定位** CLI/API/job 统一错误码与处置矩阵

**涉及内容**

- 11 类错误码：`DISABLED_SOURCE`、`NO_AVAILABLE_SOURCE`、`CAPABILITY_MISSING`、`USER_AUTH_REQUIRED`、`RESOURCE_GUARD_PAUSED`、`NOT_PUBLISHED_YET`、`SCHEMA_DRIFT`、`AUTH_FAILED`、`RATE_LIMITED`、`QUERY_TOO_LARGE`、`DUCKDB_LOCKED`
- 每码含义、是否可安全重试、用户动作、明确禁止行为
- 失败输出最低字段：`error_code`、`message`、`docs_anchor`、`retryable`、`manual_confirmation_required`

**跨域触点**

| 类别           | 触点                                                            |
| -------------- | --------------------------------------------------------------- |
| 模块           | DataSync · API · ResourceGuard · SourceRoutePlan                |
| 契约 / 文档    | `specs/contracts/data_cli_contract.yaml` · **→ 排障域 文件2–3** |
| 数据与基础设施 | silent fallback 禁止 · QMT/Yahoo/xqshare 自动启用禁止           |

---

### 文件2 · `docs/ops/design/TROUBLESHOOTING.md`

**定位** 用户/运维排障入口（常见问题处置流程）

**涉及内容**

- 数据源 disabled、ResourceGuard 暂停、Schema drift、DuckDB locked、前端无法解释数据来源
- 每类问题的分步安全动作与禁止绕过 gate
- 指向错误码指南与事故手册

**跨域触点**

| 类别           | 触点                                                                             |
| -------------- | -------------------------------------------------------------------------------- |
| 模块           | SourceRoutePlan · DataSourceService · WriteManager · 前端 freshness 展示         |
| 契约 / 文档    | **→ 本域 文件1** `ERROR_CODE_GUIDE.md` · **→ 本域 文件3** `incident_playbook.md` |
| 数据与基础设施 | `quality_flags` / `source_used` · 临时 DB 清理                                   |

---

### 文件3 · `docs/ops/design/incident_playbook.md`

**定位** 场景化事故处理手册（INC-001～005）

**涉及内容**

- INC-001 `DISABLED_SOURCE`：检查 route/registry/matrix，禁止自动启用与 silent fallback
- INC-002 `RESOURCE_GUARD_PAUSED`：缩小范围/分片 backfill，禁止关闭 ResourceGuard
- INC-003 `SCHEMA_DRIFT`：保留 raw、暂停 clean write、更新 adapter/契约/测试
- INC-004 `USER_AUTH_REQUIRED`：用户授权与 route-preview，禁止自动登录/探测
- INC-005 `PRODUCTION_EQUIVALENT_SMOKE`：隔离 DB 与 fixture 规模，禁止污染生产写路径

**跨域触点**

| 类别           | 触点                                                                                                                 |
| -------------- | -------------------------------------------------------------------------------------------------------------------- |
| 模块           | DataSync · ResourceGuard · adapter · CI smoke                                                                        |
| 契约 / 文档    | **→ 本域 文件1** · ADR-016 · `production_equivalent_smoke_budget.yaml` · **→ 数据源域 文件5** `qmt_xqshare_setup.md` |
| 数据与基础设施 | `.audit-sandbox/` · `ci_perf_budget_artifact.py`                                                                     |

---

## 隐私与数据留存

### 文件1 · `docs/ops/design/privacy_retention_policy.md`

**定位** 隐私分级、通知/报告状态机与留存归档（D-05 / QM-AUD-016）

**涉及内容**

- 报告与通知状态机（DRAFT→SENT→ARCHIVED 等）
- `dedup_key` 组成与去重/cooldown 规则
- 隐私四级分类（public_market / internal_system / sensitive_user / secret）
- D-05：raw、audit、report、notification 默认保留 1 年
- 归档 CLI（`qmd archive --dry-run`）与删除前 manifest/hash 校验
- D-04：默认通知渠道为前端 Notification Center

**跨域触点**

| 类别           | 触点                                                                                                      |
| -------------- | --------------------------------------------------------------------------------------------------------- |
| Layer          | 各层进入报告/通知的 evidence                                                                              |
| 模块           | `notification_and_reports` · Agent 输出 · 前端 Notification Center                                        |
| 契约 / 文档    | **→ 本域 文件2** `privacy_data_flow.md` · **→ 运维域** `logs_health_audit.md` · `config_secret_policy.md` |
| 数据与基础设施 | `notification_log` · report snapshot · secret-like payload mask                                           |

---

### 文件2 · `docs/ops/design/privacy_data_flow.md`

**定位** 用户输入、Agent、前端与 evidence 之间的隐私数据流

**涉及内容**

- 三种模式：仅本地预览、保存为 evidence、Agent 上下文输入（持久化与 evidence 化规则）
- 保存 evidence 必填字段（`source_label`、`provenance_note`、`retention_policy` 等）
- 禁止默认上传、用户输入直写 clean、Agent 将未证据化输入当事实、用导入文本生成买卖建议
- local-first / local-only，不上传外部服务

**跨域触点**

| 类别           | 触点                                                                                                              |
| -------------- | ----------------------------------------------------------------------------------------------------------------- |
| 模块           | Agent · 前端本地工具页 · `file_registry`                                                                          |
| 契约 / 文档    | `specs/contracts/user_input_privacy_contract.yaml` · **→ 本域 文件1** · **→ Agent 域** `agent_security_policy.md` |
| 数据与基础设施 | `evidence_chain` · `untrusted` 标注 · D-12 固定来源                                                               |

---

## 前端安全与界面边界

### 文件1 · `docs/ops/design/frontend_security_policy.md`

**定位** 前端 CSP、会话、缓存、分页与错误边界（QM-AUD-018）

**涉及内容**

- CSP 基线：禁 inline script、禁任意外部域
- API token 不得进 localStorage；富文本按纯文本渲染防 XSS
- 列表必须分页；stale 数据须 FreshnessLabel
- 各主页面 ErrorBoundary 与错误展示不泄露 secret/路径
- UI 布局仅为占位，正式实现前须用户确认
- 分页/token 权威口径对齐 `api_security_contract.yaml`

**跨域触点**

| 类别           | 触点                                                                            |
| -------------- | ------------------------------------------------------------------------------- |
| Layer          | 各层列表/详情页的 freshness 展示                                                |
| 模块           | `docs/modules/design/frontend_dashboard.md` · FastAPI 只读 API                  |
| 契约 / 文档    | `specs/contracts/api_security_contract.yaml` · **→ API 域** `fastapi_routes.md` |
| 数据与基础设施 | Bearer token · `page_size` 200/1000 · `test_pageSizeContract_matchesDocs`       |

---

### 文件2 · `docs/modules/design/frontend_dashboard.md`

**定位** Vite + React + TypeScript 前端看板权威设计（五层模型与证据链展示）

**涉及内容**

- 核心目标：看得懂、查得到、不误导、不越权、可配置、可扩展
- 实现前须用户确认 UI 风格、信息层级、图谱呈现方式
- 只消费 FastAPI，不直连 DuckDB
- 配置驱动 + 条件渲染（map/条件展示 Layer3 graph 等）
- 前端目录建议：pages、api client、components、charts
- FreshnessLabel 与 `quality_flags` / `source_used` 必展示

**跨域触点**

| 类别           | 触点                                                                                                                   |
| -------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Layer          | 各层列表/详情页 · Layer3 graph view                                                                                    |
| 模块           | **→ API 域 文件3** `fastapi_backend.md` · Notification Center                                                          |
| 契约 / 文档    | **→ 本域 文件1** `frontend_security_policy.md` · **→ 本域 文件3** `page_contracts.yaml` · `api_security_contract.yaml` |
| 数据与基础设施 | Bearer token 存储边界 · 分页 200/1000 · ErrorBoundary                                                                  |

---

### 文件3 · `specs/frontend/design/page_contracts.yaml`

**定位** 前端页面契约 v2（路由、API 依赖与必备组件能力清单，reference_not_final_design）

**涉及内容**

- `implementation_guardrail`：页面布局未固定、路由仅参考、视觉设计须用户确认（D-08）
- 页面清单：MarketOverview、Layer1–5、Reports、Notifications、Backtest、DataHealth 及 API 依赖
- `required_components`：QualityBadge、FreshnessLabel、SourceLabel、BoundaryReminder、NoActionSemanticGuard 等
- `configuration_driven_sources`：axis/chain/anchor/market/instrument registry 驱动，禁止硬编码列表长度
- `must_not_hardcode`：indicator_count、chain_count、anchor_list 等
- 权威对齐 **→ 本域 文件2** `frontend_dashboard.md`

**跨域触点**

| 类别           | 触点                                                                          |
| -------------- | ----------------------------------------------------------------------------- |
| Layer          | 各层页面与 Layer3 graph 路由                                                  |
| 模块           | **→ 本域 文件2** `frontend_dashboard.md` · **→ API 域** `fastapi_routes.md`   |
| 契约 / 文档    | **→ 本域 文件1** `frontend_security_policy.md` · `api_security_contract.yaml` |
| 数据与基础设施 | registry 配置驱动 · D-08 用户确认门禁                                         |

---

## 通知与报告

### 文件1 · `docs/modules/design/notification_and_reports.md`

**定位** 日报、周报、数据质量报告、盘中提醒与通知发送流程

**涉及内容**

- 报告类型：daily_market、weekly_review、data_quality、manual_review、intraday_alert、ops_health、backtest_review
- 报告不输出买卖/仓位/收益承诺
- 只使用结构化数据 + Agent `facts_used_json`
- NoActionSemanticGuard 输出校验
- `report_registry`、通知状态机与 dedup_key
- D-04 默认通知渠道为前端 Notification Center

**跨域触点**

| 类别           | 触点                                                                           |
| -------------- | ------------------------------------------------------------------------------ |
| Layer          | 各层进入报告/通知的 evidence                                                   |
| 模块           | **→ Agent 域 文件2** `agent_module.md` · **→ 回测域** `backtest_and_review.md` |
| 契约 / 文档    | **→ 隐私域** `privacy_retention_policy.md` · `privacy_data_flow.md`            |
| 数据与基础设施 | `notification_log` · report snapshot · cooldown                                |

---

## 回测与复盘

### 文件1 · `docs/modules/design/backtest_and_review.md`

**定位** 回测与复盘能力定义（监控规则/证据链/状态事件的历史复盘与解释力评估）

**涉及内容**

- 回测类型：event_study、alert_rule_review、layer1/3/4 review、evidence_chain、agent_explanation
- 第一阶段不回答买卖/加仓/收益承诺
- 只读已归档数据，须经 ResourceGuard 限制扫描范围
- `backtest_scenario_registry` 等核心表
- 与 DuckDB/Parquet 历史查询集成

**跨域触点**

| 类别           | 触点                                                                     |
| -------------- | ------------------------------------------------------------------------ |
| Layer          | Layer1/3/4 snapshot 历史 as-of 查询                                      |
| 模块           | **→ 本域 文件2** `backtest_review_lifecycle.md` · ReportBuilder          |
| 契约 / 文档    | **→ 运维域** `performance_limits.md` · **→ 通知域** backtest_review 报告 |
| 数据与基础设施 | Parquet 历史分区 · ResourceGuard HEAVY 任务                              |

---

### 文件2 · `docs/modules/design/backtest_review_lifecycle.md`

**定位** 回测复盘固定生命周期（借鉴 MiniPTrade 结构，不含下单/持仓语义）

**涉及内容**

- 生命周期：load scenario → frozen snapshot → event set → forward windows → metrics → report
- 硬边界：禁止 order API、`as-of` freeze、`no_action_semantics=true`
- 指标契约 `backtest_metric_contract.yaml`
- 未来模块：backtest_engine、review_context、report_builder、metrics
- 验收 pytest 与 smoke 边界

**跨域触点**

| 类别           | 触点                                                                                 |
| -------------- | ------------------------------------------------------------------------------------ |
| 模块           | **→ 本域 文件1** `backtest_and_review.md` · **→ 本域 文件3** `review_sandbox_api.md` |
| 契约 / 文档    | `specs/contracts/backtest_metric_contract.yaml`                                      |
| 数据与基础设施 | frozen snapshot · forward window 分区                                                |

---

### 文件3 · `docs/modules/design/review_sandbox_api.md`

**定位** 可选只读策略/规则复盘兼容层（读历史数据、记录复盘指标，禁止交易语义）

**涉及内容**

- 可借鉴 JQ2PTrade/EasyXT lifecycle 思路；禁止 order/compile/exec
- 权威契约：review_sandbox_contract、reference_adoption_guardrails、user_input_privacy
- 默认 AST 静态扫描，检测 order-like API 即 violation
- 禁止 os/sys/subprocess/socket/requests
- 不写 clean 表、不把复盘结果写成交易建议

**跨域触点**

| 类别           | 触点                                                                                  |
| -------------- | ------------------------------------------------------------------------------------- |
| 模块           | **→ 本域 文件2** lifecycle · **→ Agent 域** no_action 守卫                            |
| 契约 / 文档    | `specs/contracts/review_sandbox_contract.yaml` · `reference_adoption_guardrails.yaml` |
| 数据与基础设施 | sandbox 隔离执行 · violation 审计                                                     |

---

## 运维报告 CLI

### 文件1 · `docs/ops/design/ops_report_cli.md`

**定位** `qmd ops report` 设计：将本地 JSON 证据转为 Markdown/HTML 报告（Phase E）

**涉及内容**

- 回答：本机 JSON 证据能否离线渲染运维可读报告且不上传网络
- 依赖 `db-inspect` / `data health` / 未来 source-health 的 JSON 形态
- CLI：`--input` / `--format markdown|html` / `--output` / `--redact`
- 报告章节：隐私横幅、执行摘要、DB 血缘、域健康、deferred 映射、下一步（链到排障文档 anchor）
- Round 3 v1 **不**实现；禁止 `--upload` / 网络 / CDN / `--show-secrets`

**跨域触点**

| 类别           | 触点                                                                                                         |
| -------------- | ------------------------------------------------------------------------------------------------------------ |
| 模块           | `backend/app/ops/report_models.py` · `data/reports/`                                                         |
| 契约 / 文档    | **→ 隐私域** `privacy_data_flow.md` · `user_input_privacy_contract.yaml` · **→ 排障域** `TROUBLESHOOTING.md` |
| 数据与基础设施 | ptqmt-site / EasyXT / JQ2PTrade 参考采纳边界 · 纯本地 JSON→文件转换                                          |

---

## 项目工程结构

### 文件1 · `docs/architecture/design/07_project_directory_structure.md`

**定位** 项目目录结构蓝图（v1.6 设计文档第 16 章拆分）

**涉及内容**

- `backend/app/` 分包（api、datasources、db、etl、validators、layer1~5、agents、notifications）
- `backend/scripts/` 同步与报告脚本清单
- `frontend/src/` 页面/组件/api/charts 结构
- `data/` 下 duckdb/raw/files/parquet/audit/reports/cache
- `configs/` 与 `specs/` 目录布局

**跨域触点**

| 类别           | 触点                                                                                                                                                                     |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Layer          | `layer1_axes/` … `layer5_evidence/` 代码目录                                                                                                                             |
| 模块           | API · datasources · agents · notifications · frontend                                                                                                                    |
| 契约 / 文档    | `specs/layer1_axes/design/` · `specs/layer3_global_industry_chains/design/` · `specs/frontend/design/` · `specs/contracts/design/` · `rules/design/` · `docs/**/design/` |
| 数据与基础设施 | `data/duckdb/` · `init_db.py` · `sync_daily.py` 等脚本                                                                                                                   |

---

### 文件2 · `specs/contracts/design/release_cleanup_allowlist.yaml`

**定位** 发布打包清理白名单（防止误删正式 docs/specs/contracts）

**涉及内容**

- `allowlist_roots`：README、MIGRATION_MAP、docs/\*\*、specs 各子目录等
- `forbidden_patterns`：`__pycache__`、`.scratch`、`task_plan.md` 等可删临时物
- 打包/清理脚本须先匹配 allowlist 再删除
- 保护 `specs/**/design/` 与 `docs/**/design/` 审阅成品
- 与最终审计/发布流程衔接

**跨域触点**

| 类别           | 触点                                                                 |
| -------------- | -------------------------------------------------------------------- |
| 模块           | release/packaging 脚本 · CI 清理 job                                 |
| 契约 / 文档    | **→ 本域 文件1** `07_project_directory_structure.md` · MANIFEST.json |
| 数据与基础设施 | 禁止误删 `uv.lock` · `specs/schema/`                                 |

---

## 架构决策（ADR）

### 文件1 · `docs/architecture/design/08_decision_log_index.md`

**定位** ADR 决策记录索引（「为什么这样设计」）

**涉及内容**

- ADR-0001 DuckDB 本地核心分析库
- ADR-0002 Agent 只读、不直接写库
- ADR-0003 Layer1 才物化完整标准化字段
- ADR-0004 Layer3 资金震动锚点模型方案B
- ADR-0005 Primary / Validation / FallbackPolicy 数据源角色
- ADR-017 动态降级、异常数据生命周期与主源恢复回补
- 各 ADR 对应模块文档指针

**跨域触点**

| 类别        | 触点                                                                                                                                                                                                                                     |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Layer       | Layer1 标准化 · Layer3 shock-anchor                                                                                                                                                                                                      |
| 模块        | `docs/modules/design/agent_module.md` · `docs/modules/design/data_sources.md` · `docs/modules/design/layer1_global_regime_panel.md` · `docs/modules/design/layer3_industry_shock_anchor.md` · `docs/modules/design/local_file_system.md` |
| 契约 / 文档 | 本文件为 ADR 骨架索引；各 ADR 决策要点见涉及内容与模块文档                                                                                                                                                                               |

---

### 文件2 · `docs/decisions/design/ADR-017-dynamic-source-fallback-and-exception-data-lifecycle.md`

**定位** 已接受的动态数据源降级、连续监控、主源恢复与异常归档决策

**涉及内容**

- 稳定 Source Registry 与管理员持久化启用覆盖层分离
- 按领域固定候选顺序的可审计自动兜底，Validation 不升格为 Primary
- 来源风险与质量风险独立标签，质量异常可连续监控但不得伪装可信
- 可信最终库、连续监控区、审计归档区和按频率异常 payload 留存规则
- 主源恢复后的按领域窗口回补、版本切换与归档前置条件

**跨域触点**

| 类别        | 触点                                                                                                                   |
| ----------- | ---------------------------------------------------------------------------------------------------------------------- |
| 模块        | Source Registry · RoutePlan · Scheduler · WriteManager · Layer1–5 · API · Frontend · Notification                      |
| 契约 / 文档 | `specs/contracts/design/source_provenance_quality_contract.yaml` · `docs/architecture/design/08_decision_log_index.md` |

---

## 外部参考与架构依据

### 文件1 · `docs/architecture/design/10_external_references.md`

**定位** 外部官方文档与依据索引（支撑架构选型与 Layer3 锚点来源）

**涉及内容**

- DuckDB 并发、Parquet、SQL-on-Pandas 官方文档
- FRED API（Layer1 宏观指标）
- xtdata/QMT、FastAPI、Vite、React 官方文档
- MSCI/S&P 评分方法论（z-score vs percentile）
- Airbyte 增量同步、Dagster backfill、Great Expectations、dbt tests
- OpenAI Structured Outputs（Agent 结构化输出）
- Layer3 锚点来源（OpenAI/Anthropic/NVIDIA/Microsoft/Meta/Counterpoint/IEA/Arm 等）

**跨域触点**

| 类别        | 触点                                                                                                                     |
| ----------- | ------------------------------------------------------------------------------------------------------------------------ |
| Layer       | Layer1 宏观/评分方法 · Layer3 各 `source_keys` 锚点                                                                      |
| 模块        | DuckDB · FastAPI · 前端 · Agent · 增量/回补工程 · 数据质量                                                               |
| 契约 / 文档 | `specs/layer3_global_industry_chains/design/` 锚点 `source_keys` · `docs/modules/design/layer3_industry_shock_anchor.md` |
