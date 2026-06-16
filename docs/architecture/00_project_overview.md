# 项目总览与版本确认

> 拆分说明：本文件由 `quant_monitor_design_document_v1_6.md` 拆分生成；当前步骤只做结构拆分与明显版本/编号残留修正，不删减原有细节。
> 来源：文档前言 + 第 0 章

---
title: "量化监控系统设计文档 v1.6"
subtitle: "本地优先、多源数据、五层建模、DuckDB 核心库、Agent 只读分析"
date: "2026-06-16"
author: "ChatGPT 生成，供 Claude Code / Codex 实现使用"
---

# 量化监控系统设计文档 v1.6

> 目标读者：后续使用 Claude Code / Codex 实现系统的开发者。  
> 目标系统：少数人使用、低门槛、本地优先、可逐步扩展的量化监控系统。  
> 核心目标：不是第一天做全自动交易，而是建立“可信数据 → 多层建模 → 证据链监控 → Agent 汇总解释 → 人工确认”的监控系统。

---

## 0. v1.6 版本确认结论

本版本在 v1.4 的基础上做一致性修订，采纳 12 项检查建议；同时保留此前全部架构结论。最终确认如下：

1. 新增五层分析建模框架。
2. 将“策略信号层”改名为“建模与证据层”。
3. 明确传统技术指标只作为 baseline / reference，不是核心模型。
4. 新增五轴 Axis 数据表。
5. 新增跨资产传感器层。
6. 新增全球产业链图谱层。
7. 新增市场结构层。
8. 扩展个股数据字典。
9. 新增 evidence_chain / stock_model_evidence 表。
10. Agent 增加 cross_layer_explain_agent。
11. DuckDB + Pandas 定位为研究 / ETL 临时层。
12. 数据源章节补充 Yahoo、同花顺、腾讯财经、百度股市通。
13. 新增本地文件系统定位：Raw Store / File Lake / Audit Store。
14. 新增五轴 spec 外置规则。
15. 新增产业链 spec 外置规则。
16. 新增 axis_observation 表。
17. 新增 axis_feature_snapshot 表。
18. 新增 rolling_window_policy。
19. 新增 feature_materialization_policy，规定完整标准化字段第一版只用于 Layer 1。
20. 新增 Layer 3 产业链展开视图：产业链页面可展示映射股票、ETF、期货、期权、商品合约的行情细节，但不重复保存全量历史行情。
21. 新增 Layer 4 市场详情视图：美股、A 股、港股、期货、期权等市场可展示各自指数、板块、宽度、关键资产和市场规则。
22. 新增 DataSyncOrchestrator：数据同步拆分为 FullLoad、IncrementalUpdate、Backfill、RevisionAudit、Reconcile 五类任务。
23. 新增多源冲突分级治理：客观字段按主源优先与阈值校验处理；严重冲突重抓后仍未解决才人工确认；口径不同字段分源保存。
24. 新增独立运维文件 `docs/ops_and_performance_v1_2.md`：覆盖本地文件系统、DuckDB、Parquet、增量/回补、备份恢复、内存/磁盘/查询性能和日常检查。
25. 新增 Layer 1 前端解释展示模型：在五轴指标的静态说明和每日数据之间建立 `axis_indicator_profile` 与 `axis_interpretation_snapshot`，让前端能展示“这个指标是什么、今天处于什么位置、意味着什么、不能说明什么”。
26. 明确 Layer 1 解释职责边界：程序负责数值计算、状态标签和预警；Agent 只基于结构化事实与静态说明生成受控自然语言，不直接判断预警、不写库、不输出动作语义。
27. 将数据验证层明确拆为 `DataQualityValidator` 与 `SourceConflictValidator / ReconcileJob`：质量检查负责“数据自己有没有问题”，冲突检查负责“多个来源是否打架”。
28. 新增冲突检查范围策略：日常检查最新批次与近期窗口；修订审计检查受影响历史；全历史多源检查只在初始化、重建、模型训练前或定期抽样审计时触发。
29. 将 Layer 3 从“行业/股票清单”重构为“全球产业链资金震动锚点层”：只追踪能通过 Capex、产能、供给瓶颈、商品价格、政策或重大事件引发产业链重定价的核心锚点。
30. 新增 Layer 3 锚点字段体系：`anchor_tier`、`anchor_roles`、`status_explanation_cn`、`impact_explanation_cn`、`event_only`、`frontend_group`，并新增 `specs/layer3_global_industry_chains_v1_2/` 文件包作为可实现配置。
31. 统一文档版本残留：最终结论、运维引用和外置 spec 路径均更新到 v1.6 / v1_1。
32. 运维手册配套对象更新为 `quant_monitor_design_document_v1_6.md`。
33. Layer 3 在总体定义中统一为 `Global Industry Chain Shock-Anchor Layer`，不再保留“普通行业图谱层”的旧表述。
34. Layer 1 数据源角色统一为 `Primary / Validation / FallbackPolicy`，旧 `Shadow` 视为 validation，旧 `Emergency` 视为 fallback policy，不再强制第三外部源。
35. Layer 3 chain 字段统一为 `chain_priority`，anchor 字段统一为 `anchor_priority`。
36. Layer 3 锚点不再全部标为 P0，而按 `P0_CORE / P0_EVENT / P1_ACTIVE / P1_EVENT / P1_PRICE / P2_WATCH` 分级。
37. Layer 3 每条 chain 至少生成一个 root node，确保 `industry_chain_node` 不为空。
38. Layer 3 新增 `source_validation_status`，区分 verified、needs_source、event_only_verified、price_proxy_needs_feed 等状态。
39. 补充 OpenAI 官方融资来源键 `openai_2026_funding`。
40. 运维手册新增 Layer 3 配置文件健康检查。
41. 五轴重构包补齐 SHADOW / BlindSpot / Forbidden 指标的最小解释字段。
42. Layer 1 spec 路径改为 `specs/layer1_axes/restructured_axes_v1_1/` 结构。
43. Layer 3 从 v1.6 的轻量 root node 方案升级为方案B：每条 chain 都补充功能节点、链内有向边和可视化传导逻辑。
44. 新增 Layer 3 跨链传导边：AI Capex 买方 → GPU/ASIC → HBM → 服务器/网络/光模块 → 电力/冷却 → 铜/能源约束。
45. Layer 3 优先补齐所有 P0 锚点来源，P0 锚点必须有 `source_keys` 且 `source_validation_status` 不得为 `needs_source`。
46. 新增 `layer3_node_registry.json`、`layer3_edge_registry.json`、`layer3_cross_chain_edge_registry.json`，可直接初始化 `industry_chain_node` 与 `industry_chain_edge`。

### 0.1 再次确认：Layer 4 与 Layer 5 的定位

Layer 4 与 Layer 5 不使用第一层那套完整的 `raw_value + z_score + robust_z + percentile + delta + state_bucket` 标准化物化字段体系。第一版只在 Layer 1 物化完整标准化字段。

Layer 4 是市场结构层，重点是建立“市场自己的规则”。不同市场不能强行共用一套字段和解释逻辑。例如 A 股有涨跌停、ST、北向资金、融资融券、龙虎榜、连板高度；美股有盘前盘后、ETF 行业代理、财报季、期权链、Mag7；港股有南向资金、窝轮牛熊证、流动性折价；期货市场有期限结构、主力合约切换、库存、持仓；期权市场有到期日、行权价、隐含波动、成交量、未平仓量。

Layer 5 是个股 / 合约 / ETF / 期货 / 期权证据层。它首先应保存基础可验证数据，例如开盘价、最高价、最低价、收盘价、成交量、成交额、换手率、复权因子、财务、估值、公告、新闻、事件、持仓和资金数据。第一层新增的完整标准化套件不默认扩展到 Layer 5，避免字段爆炸和过度工程化。

### 0.2 再次确认：Layer 3 与 Layer 4 可以“展开看细节”，但不重复存储大表

Layer 3 不是普通行业列表，也不是全量股票池。v1.6 继续将其定义为“全球产业链资金震动锚点层”：只追踪那些能通过财报、Capex、订单、产能、供给瓶颈、商品价格、政策或重大事件，引发全球产业链资金重定价的锚点。

Layer 3 前端仍然需要能展开看到映射标的的最新行情和关键事实，例如 NVIDIA、TSMC、ASML、SK hynix、美光、Microsoft、Meta、铜、BDI 等的开盘价、收盘价、涨跌幅、成交量、成交额、持仓量、事件和数据质量。但实现方式不是在 Layer 3 重复保存行情历史，而是：Layer 3 保存产业链关系、锚点身份、地位解释和传导逻辑；Layer 5 保存具体标的行情、财务、公告和事件；Layer 3 通过 view 或 daily snapshot 展示展开结果。

Layer 3 的每个锚点必须明确 `anchor_tier` 与 `anchor_roles`，避免把 NVIDIA、TSMC、ASML、SK hynix 这类全球定价锚与普通区域映射股放在同一级。私有公司如 OpenAI、Anthropic、SpaceX、Unitree 只能作为事件锚，不能作为日度行情锚；铜、原油、BDI 等是商品/指数价格锚，不能作为普通股票。

v1.6 已执行方案B：每条产业链不再只有 root node，而是补充功能节点和传导边。前端可以绘制“Capex 买方 → GPU/ASIC → HBM → 服务器/网络/光模块 → 电力/冷却”的链式图谱；Agent 可以按边上的 `transmission_logic_cn` 解释资金震动如何从需求侧传导到供给瓶颈和成本约束。

Layer 4 不是抽象市场名称。每个市场页面需要能展开查看自己的重要指数、板块、宽度和关键资产。例如美股市场应看到 S&P 500、Nasdaq Composite、Nasdaq 100、Dow、Russell 2000、行业 ETF、Mag7 等；A 股市场应看到上证指数、深证成指、创业板指、科创50、沪深300、中证500、中证1000、主板、创业板、科创板、北交所、申万行业、概念板块、涨跌停、成交额等。

### 0.3 再次确认：Layer 1 解释展示、质量检查与冲突检查

Layer 1 五轴指标不是普通行情字段。前端不能只展示数值，还需要展示指标的通俗名称、物理意义、覆盖范围、穿透力度、边界、盲区、今日水位、今日变化、数据质量和一句话解释。因此本版本新增 `axis_indicator_profile` 与 `axis_interpretation_snapshot`。

质量检查和冲突检查不是同一件事。质量检查看单份数据自己是否合格，例如空值、重复、缺失、日期错误、schema drift、历史不足；冲突检查看多个来源之间是否互相打架，例如 QMT 与东方财富对同一收盘价返回明显不同数值。两者同属 Data Validation Layer，但拆成两个子模块。

冲突检查不应每天全历史扫描。日常检查最新批次和近期窗口；若发现复权、修订、schema 变化或人工指定，再检查受影响历史；全历史多源审计只用于建库、重建、模型训练前或定期抽样审计。

---
