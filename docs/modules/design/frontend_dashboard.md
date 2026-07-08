# 前端看板模块

> 文件定位：实现级模块设计。本文是 Vite + React + TypeScript 前端实现的权威文件。  
> 重要边界：本文件中的页面路由、页面名称、组件组合、排版结构、布局示意均为**实现参考 / 占位方案**，不得视为最终 UI 设计。正式实现前，Claude Code / Codex 必须提醒用户进行前端页面、信息层级、排版、视觉风格和交互方式的亲自设计与确认。  
> 前端边界：前端只消费 FastAPI，不直接连接 DuckDB，不直接读取本地文件，不直接写 clean table，不输出交易动作语义。

---

# 1. 模块目标

前端负责把五层模型、数据质量、证据链、报告、盘中提醒和 Agent 解释以可理解、可追溯、可展开的方式展示给用户。

核心目标：

```text
看得懂：指标、产业链、市场结构、证据链解释必须通俗。
查得到：每个状态都能展开到来源、时间戳、质量标记、证据链。
不误导：缺失、滞后、冲突、历史不足必须显眼展示。
不越权：不出现买、卖、加仓、减仓、入场、出场等动作语义。
可配置：页面展示内容、排序、卡片组合、列显示、图表开关应尽量由配置驱动。
可扩展：当前功能不是最终全部功能，后续可以继续增加页面、组件、视图和交互。
```

React 页面应使用数据驱动渲染：指标列表、产业链节点、表格列、报告章节、提醒类型不应写死在组件内部。React 官方文档说明可以用数组 `map()` 把数据集合渲染成组件列表，也可以使用条件渲染根据状态展示不同 UI，这支持本项目采用“配置驱动 + 条件渲染”的前端实现方式。

---

# 2. 实现前必须提醒用户确认的内容

正式写前端页面之前，Claude Code / Codex 必须输出提醒并等待用户确认：

```text
前端页面设计尚未最终定稿。当前文档中的页面名称、路由、布局和组件组合仅作参考。
请用户确认：
1. 页面整体风格：专业金融终端 / 简洁仪表盘 / 研究看板 / 移动优先 / 桌面优先。
2. 首页信息层级：先看五轴、先看市场、先看产业链、还是先看数据健康。
3. Layer 3 图谱呈现：节点图、分组卡片、表格、桑基图、时间线或组合方式。
4. 报告和提醒呈现：通知中心、报告页、弹窗、侧边栏、消息流或只写本地文件。
5. 颜色语义：风险、数据质量、状态异常、人工复核如何用颜色和图标区分。
6. 是否需要深色模式、紧凑模式、多屏模式。
```

未经用户确认，前端实现只能生成基础 skeleton 和可替换组件，不得把排版、配色、信息优先级写成不可调整的最终版本。

---

# 3. 前端目录建议

目录仅为建议，最终可以按用户确认的前端方案调整。

```text
frontend/
  src/
    app/
      router.tsx
      providers.tsx
      featureFlags.ts
    api/
      client.ts
      generated-types.ts
      layer1.ts
      layer2.ts
      layer3.ts
      layer4.ts
      layer5.ts
      reports.ts
      notifications.ts
      dataHealth.ts
      backtest.ts
    pages/
      MarketOverviewPage.tsx
      Layer1AxesPage.tsx
      Layer2SensorsPage.tsx
      Layer3ChainsPage.tsx
      Layer4MarketsPage.tsx
      Layer5SecurityPage.tsx
      ReportsPage.tsx
      NotificationsPage.tsx
      BacktestReviewPage.tsx
      DataHealthPage.tsx
      SettingsPage.tsx
    components/
      common/
      charts/
      quality/
      layer1/
      layer2/
      layer3/
      layer4/
      layer5/
      reports/
      notifications/
      backtest/
    hooks/
    utils/
    styles/
```

---

# 4. 页面清单：参考而非最终固定

| 页面                   | 参考路由                | 作用                                        | 是否可改 |
| ---------------------- | ----------------------- | ------------------------------------------- | -------- |
| 市场总览页             | `/`                     | 展示市场状态、五层摘要、数据健康、最新提醒  | 可改     |
| Layer 1 五轴状态页     | `/layer1`               | 展示五轴状态、指标解释、质量状态            | 可改     |
| Layer 2 跨资产传感器页 | `/layer2`               | 展示美元、黄金、原油、铜、美债、ETF、VIX 等 | 可改     |
| Layer 3 产业链图谱页   | `/layer3`               | 展示产业链、节点、边、锚点、事件与价格锚    | 可改     |
| Layer 4 市场结构页     | `/layer4`               | 展示 A 股、美股、港股、期货、期权市场结构   | 可改     |
| Layer 5 个股证据页     | `/layer5/:instrumentId` | 展示行情、财务、公告、新闻、证据链          | 可改     |
| 报告页                 | `/reports`              | 展示日报、周报、数据质量报告、人工确认清单  | 可改     |
| 通知中心               | `/notifications`        | 展示盘中提醒、数据风险、系统风险、人工确认  | 可改     |
| 回测与复盘页           | `/backtest`             | 展示事件复盘、规则命中、历史表现、误报分析  | 可改     |
| 数据源健康页           | `/data-health`          | 展示数据质量、冲突、任务状态、资源状态      | 可改     |
| 系统配置页             | `/settings`             | 展示配置状态，不直接修改核心数据            | 可改     |

说明：页面清单代表当前系统需要展示的信息域，不代表最终页面数量、路由、布局或视觉设计。

---

# 5. API Client 规则

所有 API 调用都通过 `src/api/client.ts`。

统一处理：

```text
base_url
timeout
retry
response envelope
error code
quality_flags
pagination
date_range guard
resource_guard_paused
```

禁止：

```text
页面组件直接手写 fetch
页面组件直接拼 URL 查询大范围数据
页面组件直接访问本地文件路径
页面组件绕过 API client 读取后端
```

前端类型来源：

```text
specs/api/openapi_contract.md
后续由 OpenAPI 自动生成 TypeScript types
```

---

# 6. 通用组件：必须具备，但外观可由用户设计

这些组件代表必须展示的信息能力，不代表最终样式。

## 6.1 QualityBadge

展示：

```text
NORMAL
STALE_DATA
SOURCE_SWITCHED
SOURCE_CONFLICT
INSUFFICIENT_HISTORY
MANUAL_REVIEW_REQUIRED
NO_ACCEPTED_CHANNEL
RESOURCE_GUARD_PAUSED
```

## 6.2 FreshnessLabel

展示：

```text
as_of_timestamp
fetch_time
data_lag_days
stale_reason
```

## 6.3 SourceLabel

展示：

```text
source_used
source_channel_id
source_validation_status
primary / validation / fallback_policy
```

## 6.4 BoundaryReminder

展示指标、模型、报告、回测、提醒不能说明什么，防止误读。

## 6.5 NoActionSemanticGuard

前端渲染 Agent 文本、报告文本、提醒文本前检查禁用词：

```text
买入
卖出
加仓
减仓
入场
出场
信号
保证收益
```

发现后：

```text
隐藏原文
展示“该解释需要人工复核”
写前端错误日志
```

## 6.6 ResourceStatusBadge

展示 ResourceGuard 当前状态：

```text
OK
WARN
PAUSE
STOP_NON_CORE
```

## 6.7 EvidenceDrawer

任何提醒、报告段落、Layer 1 状态、Layer 3 事件、回测结论都必须能展开证据链：

```text
evidence_ids
source_used
as_of_timestamp
quality_flags
facts_used_json
boundary_reminder
```

---

# 7. 页面内容要求

## 7.1 Layer 1 页面

必须能展示：

```text
五轴状态卡
单轴指标列表
指标解释
原始值 / 标准化值 / 分位数
数据质量
边界提醒
来源与时间戳
```

不应写死：

```text
五轴指标数量
指标排序
指标卡片布局
颜色方案
```

## 7.2 Layer 2 页面

必须能展示：

```text
跨资产传感器列表
资产类别过滤
latest value
change label
quality flags
roll event / 主力合约切换
与 Layer 1 / Layer 3 的关联提示
```

## 7.3 Layer 3 页面

必须能展示：

```text
产业链列表
chain_priority
anchor_priority
anchor_tier
node / edge / cross-chain edge
source_validation_status
event_only 私有公司标记
Layer 5 映射行情摘要
```

页面交互可以是图谱、表格、卡片、时间线、分组视图或组合视图，正式实现前必须由用户确认。

## 7.4 Layer 4 页面

必须能展示：

```text
市场规则
主要指数
板块/行业
宽度指标
市场事件
数据质量
```

## 7.5 Layer 5 页面

必须能展示：

```text
instrument registry
行情
财务
估值
公告
新闻
事件
证据链
```

## 7.6 报告页

必须能展示：

```text
daily_market_report
weekly_review_report
data_quality_report
manual_review_report
ops_health_report
facts_used_json
quality_warnings_json
```

## 7.7 通知中心

必须能展示：

```text
intraday_alert
data_risk_alert
ops_risk_alert
manual_review_required
notification status
cooldown / dedup 信息
```

## 7.8 回测与复盘页

必须能展示：

```text
backtest scenario
backtest run log
event set
outcome window
metrics
review conclusion
limitations
resource usage
```

回测页面不得展示为交易建议页面，只能展示历史复盘与规则评估。

---

# 8. 配置驱动原则

前端至少应从这些配置或 API 结果动态生成页面：

```text
axis_registry
axis_indicator_registry
axis_indicator_profile
layer3_chain_registry
layer3_anchor_registry
layer3_node_registry
layer3_edge_registry
market_registry
instrument_registry
report_registry
notification_rule_registry
backtest_scenario_registry
```

禁止硬编码：

```text
指标总数
产业链总数
锚点列表
市场列表
报告章节数量
提醒类型数量
回测场景数量
```

---

# 9. 前端性能规则

```text
默认 page_size = 200
硬上限 page_size = 1000
唯一机器权威 = specs/contracts/api_security_contract.yaml
大表使用分页或虚拟滚动
图谱默认只展示当前 chain，不一次加载全局所有边
历史图默认最近 90 天
分钟线默认最近 5 个交易日
Agent context 默认展示摘要，展开后再加载详情
```

当前系统运行在用户本机，前端不得默认触发重查询、全历史扫描或后台大任务。

---

# 10. 验收测试

```text
前端能在 API 返回 DATA_STALE 时显示 FreshnessLabel
前端能在 SOURCE_CONFLICT 时显示 QualityBadge
前端能在 RESOURCE_GUARD_PAUSED 时阻止重查询
前端不写死 Layer 3 锚点
前端不写死 Layer 1 指标数量
Agent 文本触发禁用词时被 NoActionSemanticGuard 拦截
回测结果显示限制说明，不显示交易建议
通知中心能展示 dedup / cooldown 状态
```

## 用户决策补充：UI 必须先确认

落实 D-08：当前文件中的页面结构、组件组合、布局示意仅为参考/占位。正式实现前，Claude Code / Codex 必须提醒用户确认：

```text
页面信息架构
核心页面清单
每页展示哪些模块
交互方式
视觉风格与排版
```

不得把当前文档里的页面布局写死为最终 UI。

---

# 11. SourceRoute 与 Local-only UI 边界

后续前端实现必须展示数据来源解释，而不是只展示最终数值：

```text
source_used
route_status
quality_flags
as_of_timestamp
freshness
rule_version 或等效 lineage
error_code / docs_anchor
```

新增 UI 能力仍是占位能力，不代表最终布局：

- 只读 Diagnostics 入口：展示 source route preview、ResourceGuard snapshot、registry validation。
- Local-only disclosure：用户导入文本、策略片段、研究笔记时，默认只在本地预览；保存为 evidence 前必须明确确认。
- Disabled/fallback/source missing 状态不得隐藏，必须显示解释和排障入口。

权威契约：`specs/contracts/source_route_contract.yaml`、`specs/contracts/diagnostics_api_contract.yaml`、`specs/contracts/user_input_privacy_contract.yaml`。
