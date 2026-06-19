# Layer 3 全球产业链资金震动锚点模块

> 拆分说明：本文件由 `quant_monitor_design_document_v1_6.md` 拆分生成；当前步骤只做结构拆分与明显版本/编号残留修正，不删减原有细节。
> 来源：第 8 章

# 8. Layer 3：全球产业链资金震动锚点层

## 8.1 定位

Layer 3 不再定义为普通“全球产业链清单”，而定义为：

```text
Global Industry Chain Shock-Anchor Layer
全球产业链资金震动锚点层
```

它追踪的不是所有行业和所有股票，而是能引发产业链资金重定价的锚点。例如：

```text
Microsoft / Amazon / Alphabet / Meta 决定 AI 基础设施 Capex 周期。
NVIDIA 决定 AI GPU 与算力链资金情绪。
TSMC 决定先进制程与先进封装供给瓶颈。
ASML 决定 EUV 光刻设备瓶颈。
SK hynix / Micron / Samsung 决定 HBM/DRAM 存储瓶颈。
Vertiv / Eaton / Schneider 决定 AI 数据中心电力和冷却扩散链。
铜、原油、铀、BDI 等作为商品/指数价格锚。
OpenAI、Anthropic、SpaceX、Unitree 等私有公司作为事件锚。
```

通俗解释：Layer 3 不是“把所有相关股票放进来”，而是回答：

```text
谁的财报、订单、Capex、产能、价格、政策或重大事件，能让整条产业链重新定价？
```

## 8.2 与 Layer 5 的边界

Layer 3 保存：产业链结构、锚点身份、锚点地位、传导逻辑、前端解释字段和事件触发规则。

Layer 5 保存：具体股票、ETF、期货、商品、指数的行情、成交量、成交额、持仓量、财务、公告、新闻和事件。

实现原则：

```text
Layer 3 不重复保存全量历史行情。
Layer 3 通过 view / daily snapshot 从 Layer 5 读取最新行情和关键事实。
Layer 3 可以展示价格、成交量、成交额和持仓量，但这些字段来自 Layer 5。
私有公司只进事件系统，不进普通行情表。
```

## 8.3 锚点分层字段

新增 `anchor_tier` 字段，用于说明“这个标的是什么地位”：

| anchor_tier | 中文含义 | 示例 |
|---|---|---|
| `A_GLOBAL_DOMINANT` | 全球绝对统治型/定价型锚点。单家公司或变量足以影响全球产业链资金重定价。 | NVIDIA、TSMC、ASML、SK hynix、Arm、CATL、Eli Lilly、Novo Nordisk |
| `A_CAPEX_SETTER` | 资本开支总开关。不是供应商，但决定 AI 基础设施花多少钱、买多少算力、建多少数据中心。 | Microsoft、Amazon、Alphabet、Meta |
| `B_OLIGOPOLY_ANCHOR` | 寡头型资金锚。几家公司共同影响赛道资金，没有单一绝对统治者。 | Micron、Samsung、Broadcom、Arista、Dell、Eaton |
| `B_SUPPLY_CHAIN_BETA` | 供应链高弹性锚。对产业链景气度反应快、波动大。 | Marvell、中际旭创、新易盛、Super Micro、CoreWeave、Vertiv |
| `C_PRIVATE_EVENT_ANCHOR` | 私有公司/不可直接交易事件锚。融资、产品、订单或合作能影响市场，但不是常规行情标的。 | OpenAI、Anthropic、SpaceX、Unitree、Figure AI |
| `D_COMMODITY_PROXY` | 商品/期货/指数价格锚。通过价格、库存、运价直接反映供需约束。 | 铜、原油、天然气、锂、铀、BDI、SCFI |
| `E_REGIONAL_PROXY` | 区域市场映射锚。主要反映 A 股、港股、韩股、日股等局部市场弹性，全球统治力不足。 | 寒武纪、华为昇腾生态相关标的、A 股光模块链 |

新增 `anchor_priority` 字段，用于说明“系统多频繁、多靠前地监控它”：

| anchor_priority | 中文含义 |
|---|---|
| `P0_CORE` | 核心日度监控锚点，默认进入首页和日报。 |
| `P0_EVENT` | 核心事件锚，私有公司或重大项目不进普通行情，但事件必须进入日报。 |
| `P1_ACTIVE` | 重要锚点，进入产业链页面和事件驱动摘要。 |
| `P1_EVENT` | 重要事件锚，默认不进首页行情，但事件进入产业链解释。 |
| `P1_PRICE` | 商品/指数价格锚，用于供需约束和成本传导解释。 |
| `P2_WATCH` | 观察锚点，先保留映射，默认不进核心首页。 |

新增 `anchor_roles` 字段，用于说明“这个标的在链条里起什么作用”：

```text
demand_setter              需求/Capex 制定者
supply_bottleneck          供给瓶颈
sentiment_leader           资金情绪领涨/领跌锚
capacity_signal            产能与供货信号
price_proxy                商品/价格代理
event_source               事件源
regional_beta              区域市场弹性映射
ai_server                  AI 服务器/整机锚
ai_networking              AI 网络/互联锚
optical_module             光模块/光器件锚
power_cooling              电力/冷却基础设施锚
enterprise_ai_application  企业 AI 应用锚
data_platform              企业数据平台锚
```

## 8.4 第一版主链结构

第一版 Layer 3 不平铺几十条行业，而分为三组：

### A. P0：AI 基础设施核心链

```text
1. AI_CAPEX_COMMAND_CENTER
   AI资本开支总开关：Microsoft / Amazon / Alphabet / Meta / Oracle / CoreWeave / OpenAI / Anthropic

2. AI_COMPUTE_ASIC
   AI芯片、加速器、ASIC：NVIDIA / AMD / Broadcom / Marvell

3. AI_MEMORY_BOTTLENECK
   HBM、DRAM、NAND：SK hynix / Micron / Samsung

4. SEMICONDUCTOR_MANUFACTURING_BOTTLENECK
   先进制程、先进封装、设备、EDA/IP：TSMC / ASML / AMAT / Lam / TEL / KLA / Synopsys / Cadence / Arm

5. AI_INFRASTRUCTURE_EXPANSION
   AI服务器、AI网络、光模块：Dell / HPE / Super Micro / Foxconn / Quanta / Arista / 中际旭创 / 新易盛 / Coherent / 天孚通信

6. AI_POWER_COOLING
   AI电力、配电、变压器、液冷、热管理：Vertiv / Eaton / Schneider / GE Vernova / Siemens Energy / 铜 / 天然气
```

### B. P1：AI 商业化与具身智能主题链

```text
7. MODEL_ENTERPRISE_AI_PLATFORM
   模型层与企业AI平台：OpenAI / Anthropic / Google DeepMind / Microsoft / Palantir / Snowflake / Databricks / ServiceNow / Salesforce

8. ROBOTICS_EMBODIED_AI
   机器人、具身智能、自动驾驶：Tesla / NVIDIA / Unitree / Figure AI / ABB / FANUC / Yaskawa
```

### C. P1/P2：非 AI 全球产业链

```text
9. ENERGY_LNG
   油气/LNG/传统能源：WTI / Brent / Henry Hub / Exxon / Chevron / Shell / Cheniere

10. CRITICAL_MINERALS_URANIUM
    关键矿产与铀：铜 / 锂 / 铀 / Freeport / BHP / Rio Tinto / Albemarle / Cameco

11. AEROSPACE_DEFENSE_SPACE
    航空航天、国防、商业航天：Lockheed / RTX / Northrop / BAE / General Dynamics / SpaceX / Rocket Lab

12. SHIPPING_GLOBAL_TRADE
    航运与全球贸易：BDI / SCFI / Maersk / COSCO / Hapag-Lloyd / Frontline / Scorpio Tankers

13. GLP1_METABOLIC_DRUGS
    GLP-1、肥胖药、代谢药：Eli Lilly / Novo Nordisk / Amgen / Viking Therapeutics

14. EV_BATTERY_STORAGE
    新能源车、动力电池、储能：Tesla / BYD / CATL / Lithium Price / First Solar / Enphase
```

## 8.5 细节外置文件

Layer 3 的具体配置不全部写入主设计文档，而外置为可实现文件包：

```text
specs/layer3_global_industry_chains_v1_2/
  README.md
  layer3_global_industry_chain_registry.yaml
  layer3_anchor_registry.json
  layer3_node_registry.json
  layer3_edge_registry.json
  layer3_cross_chain_edge_registry.json
  layer3_data_dictionary.md
  references/source_registry.md
```

其中：

```text
layer3_global_industry_chain_registry.yaml
  作为后端初始化产业链与锚点基础表的主配置。

layer3_anchor_registry.json
  作为扁平化锚点表，供前端、搜索、Agent 输入使用。

layer3_node_registry.json
  作为扁平化节点表，可直接初始化 industry_chain_node。

layer3_edge_registry.json
  作为链内有向边表，可直接初始化 industry_chain_edge。

layer3_cross_chain_edge_registry.json
  作为跨链传导边表，用于绘制 AI 主链从 Capex 到电力/冷却和资源约束的传导路径。

layer3_data_dictionary.md
  说明字段、前端展示规则和 Layer 3 / Layer 5 边界。

references/source_registry.md
  记录官方/权威来源与用途。
```

## 8.6 表结构调整

### 8.6.1 产业链节点表

```sql
CREATE TABLE IF NOT EXISTS industry_chain_node (
    node_id             VARCHAR PRIMARY KEY,
    node_name           VARCHAR,
    parent_node_id      VARCHAR,
    chain_id            VARCHAR,
    chain_name          VARCHAR,
    chain_priority      VARCHAR,   -- P0_CORE / P1_THEME / P1_GLOBAL_MACRO / P2_OPTIONAL
    chain_type          VARCHAR,
    node_level          INTEGER,
    node_role           VARCHAR,
    description         TEXT,
    frontend_summary_cn TEXT,
    avoid_confusion_cn  TEXT,
    spec_path           VARCHAR,
    display_order       INTEGER,
    updated_at          TIMESTAMP
);
```

v1.6 规则：每条产业链仍保留 `chain_id + "_ROOT"` 作为根节点，但已执行方案B，必须额外提供功能节点和链内有向边。root node 负责页面聚合，功能节点负责表达产业链环节，edge 负责表达传导逻辑。

### 8.6.2 产业链关系表

```sql
CREATE TABLE IF NOT EXISTS industry_chain_edge (
    edge_id             VARCHAR PRIMARY KEY,
    from_node_id        VARCHAR,
    to_node_id          VARCHAR,
    relation_type       VARCHAR,   -- demand_to_supply / bottleneck_to_downstream / price_to_margin / event_to_sentiment
    direction           VARCHAR,
    description         TEXT,
    transmission_logic_cn TEXT,
    updated_at          TIMESTAMP
);
```



#### 方案B：节点与边落地规则

Layer 3 v1.6 采用方案B，不再只依赖 root node。每条 chain 至少包含：

```text
1 个 root node：页面聚合和链条入口；
2 个以上功能节点：例如 Capex买方、GPU/ASIC、HBM、服务器/网络/光模块、电力/冷却；
1 条以上链内边：说明同一链内部资金、订单、价格或产能如何传导；
若属于 AI 主链，还可拥有 cross-chain edge：说明跨产业链传导。
```

示例：

```text
AI Capex 买方
  → GPU/ASIC
  → HBM
  → 服务器/网络/光模块
  → 电力/冷却
  → 铜/能源约束
```

这条路径只表达 Layer 3 的关系和解释，不复制 Layer 5 的行情数据。

#### 8.6.2.1 跨链传导边表

```sql
CREATE TABLE IF NOT EXISTS industry_chain_cross_edge (
    edge_id                 VARCHAR PRIMARY KEY,
    from_chain_id           VARCHAR,
    from_node_id            VARCHAR,
    to_chain_id             VARCHAR,
    to_node_id              VARCHAR,
    relation_type           VARCHAR,
    transmission_logic_cn   TEXT,
    display_order           INTEGER,
    updated_at              TIMESTAMP
);
```

通俗解释：`industry_chain_edge` 说明一条链内部怎么传导；`industry_chain_cross_edge` 说明不同链之间怎么传导，例如 AI Capex 传导到 GPU/ASIC，GPU/ASIC 再传导到 HBM、服务器和电力冷却。

### 8.6.3 产业链锚点映射表

```sql
CREATE TABLE IF NOT EXISTS industry_chain_instrument_map (
    map_id                  VARCHAR PRIMARY KEY,
    chain_id                VARCHAR,
    node_id                 VARCHAR,
    instrument_id           VARCHAR,
    instrument_type         VARCHAR,   -- public_equity / etf / future_or_commodity / commodity_index / index / private_company
    ticker                  VARCHAR,
    exchange                VARCHAR,
    market                  VARCHAR,
    anchor_tier             VARCHAR,
    anchor_roles_json       JSON,
    frontend_group          VARCHAR,
    anchor_priority         VARCHAR,
    event_only              BOOLEAN,
    role_in_chain           VARCHAR,
    importance_level        INTEGER,
    exposure_type           VARCHAR,
    revenue_exposure_pct    DOUBLE,
    confidence              DOUBLE,
    status_explanation_cn   TEXT,      -- 前端展示：它是什么地位
    impact_explanation_cn   TEXT,      -- 前端展示：它会影响什么
    monitor_events_json     JSON,
    source_keys_json        JSON,
    source_validation_status VARCHAR,
    evidence_sources_json   JSON,
    layer5_mapping_hint     VARCHAR,
    source                  VARCHAR,
    updated_at              TIMESTAMP
);
```

### 8.6.4 私有事件锚表

私有公司、监管机构、政策事件、融资事件不进入普通行情表，单独进入事件表：

```sql
CREATE TABLE IF NOT EXISTS industry_chain_event_anchor (
    event_anchor_id         VARCHAR PRIMARY KEY,
    chain_id                VARCHAR,
    anchor_name             VARCHAR,
    anchor_type             VARCHAR,   -- private_company / regulator / policy_body / major_project
    anchor_tier             VARCHAR,
    anchor_roles_json       JSON,
    status_explanation_cn   TEXT,
    impact_explanation_cn   TEXT,
    watch_event_types_json  JSON,
    source_whitelist_json   JSON,
    latest_event_time       TIMESTAMP,
    latest_event_summary    TEXT,
    updated_at              TIMESTAMP
);
```

### 8.6.5 展开视图

```sql
CREATE VIEW industry_chain_instrument_view AS
SELECT
    m.chain_id,
    m.node_id,
    m.instrument_id,
    m.instrument_type,
    m.ticker,
    m.exchange,
    m.market,
    m.anchor_tier,
    m.anchor_roles_json,
    m.frontend_group,
    m.anchor_priority,
    m.event_only,
    m.status_explanation_cn,
    m.impact_explanation_cn,
    b.trade_date,
    b.open,
    b.high,
    b.low,
    b.close,
    b.pct_change,
    b.volume,
    b.amount,
    b.open_interest,
    b.source,
    b.quality_flag
FROM industry_chain_instrument_map m
LEFT JOIN instrument_daily_bar b
  ON m.instrument_id = b.instrument_id
WHERE COALESCE(m.event_only, FALSE) = FALSE;
```

### 8.6.6 每日快照表

```sql
CREATE TABLE IF NOT EXISTS industry_chain_daily_snapshot (
    chain_id                    VARCHAR,
    trade_date                  DATE,
    leading_anchors_json        JSON,
    top_movers_json             JSON,
    top_turnover_json           JSON,
    commodity_proxy_status_json JSON,
    private_event_status_json   JSON,
    global_leaders_status_json  JSON,
    chain_total_amount          DOUBLE,
    chain_heat_score            DOUBLE,
    event_count                 INTEGER,
    source_quality              VARCHAR,
    created_at                  TIMESTAMP,
    PRIMARY KEY (chain_id, trade_date)
);
```

通俗解释：产业链页面可以看到具体股票/期货/商品/指数的成交量、成交额、价格表现和事件解释，但行情来自 Layer 5；Layer 3 只保存“为什么它重要、它属于什么地位、它影响哪条链”。

## 8.7 前端展示规则

每条产业链页面默认分五栏：

```text
1. 核心震动锚：A_GLOBAL_DOMINANT / A_CAPEX_SETTER
2. 扩散锚：B_OLIGOPOLY_ANCHOR / B_SUPPLY_CHAIN_BETA
3. 事件锚：C_PRIVATE_EVENT_ANCHOR
4. 商品/指数代理：D_COMMODITY_PROXY
5. 区域映射：E_REGIONAL_PROXY 或区域市场高弹性标的
```

每个锚点卡片至少展示：

```text
中文名 / 英文名 / 代码 / 市场
anchor_tier：它是什么地位
anchor_roles：它起什么作用
status_explanation_cn：为什么它重要
impact_explanation_cn：它会影响什么
monitor_events：要盯哪些事件
今日涨跌幅 / 成交额 / 成交量 / 持仓量（如适用）
数据质量与更新时间
```

---

---

# 8.12 实现级扩展：Loader 与 Snapshot

> 本节为 v1.6 之后新增的实现级说明。它不改变 Layer 3 的金融语义，只把 `specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/` 中的配置变成可落地的数据初始化与快照生成流程。

## 8.12.1 输入文件

Layer 3 loader 必须读取：

```text
layer3_global_industry_chain_registry.yaml
layer3_anchor_registry.json
layer3_node_registry.json
layer3_edge_registry.json
layer3_cross_chain_edge_registry.json
layer3_data_dictionary.md
references/source_registry.md
```

## 8.12.2 Loader 输出表

| 输入文件 | 输出表 |
|---|---|
| `layer3_global_industry_chain_registry.yaml` | `industry_chain_registry` |
| `layer3_node_registry.json` | `industry_chain_node` |
| `layer3_edge_registry.json` | `industry_chain_edge` |
| `layer3_cross_chain_edge_registry.json` | `industry_chain_cross_edge` |
| `layer3_anchor_registry.json` | `industry_chain_anchor`、`industry_chain_instrument_map` |
| `references/source_registry.md` | `source_reference_registry`，或先作为文档参考保留 |

## 8.12.3 推荐新增表结构

### `industry_chain_registry`

```sql
CREATE TABLE IF NOT EXISTS industry_chain_registry (
    chain_id              VARCHAR PRIMARY KEY,
    chain_name_cn         VARCHAR,
    chain_name_en         VARCHAR,
    chain_priority        VARCHAR,
    chain_group           VARCHAR,
    chain_type            VARCHAR,
    description_cn        TEXT,
    frontend_summary_cn   TEXT,
    spec_path             VARCHAR,
    is_enabled            BOOLEAN,
    updated_at            TIMESTAMP
);
```

### `industry_chain_anchor`

```sql
CREATE TABLE IF NOT EXISTS industry_chain_anchor (
    anchor_id                  VARCHAR PRIMARY KEY,
    chain_id                   VARCHAR,
    node_id                    VARCHAR,
    display_name               VARCHAR,
    display_name_cn            VARCHAR,
    instrument_type            VARCHAR,
    ticker                     VARCHAR,
    market                     VARCHAR,
    anchor_tier                VARCHAR,
    anchor_priority            VARCHAR,
    anchor_roles               VARCHAR,
    event_only                 BOOLEAN,
    frontend_group             VARCHAR,
    status_explanation_cn      TEXT,
    impact_explanation_cn      TEXT,
    source_validation_status   VARCHAR,
    source_keys                VARCHAR,
    layer5_mapping_hint        VARCHAR,
    monitor_events             VARCHAR,
    is_enabled                 BOOLEAN,
    updated_at                 TIMESTAMP
);
```

### `industry_chain_cross_edge`

```sql
CREATE TABLE IF NOT EXISTS industry_chain_cross_edge (
    cross_edge_id        VARCHAR PRIMARY KEY,
    from_chain_id        VARCHAR,
    from_node_id         VARCHAR,
    to_chain_id          VARCHAR,
    to_node_id           VARCHAR,
    transmission_type    VARCHAR,
    direction            VARCHAR,
    explanation_cn       TEXT,
    evidence_required    VARCHAR,
    display_order        INTEGER,
    is_enabled           BOOLEAN,
    updated_at           TIMESTAMP
);
```

### `industry_chain_daily_snapshot`

```sql
CREATE TABLE IF NOT EXISTS industry_chain_daily_snapshot (
    snapshot_id             VARCHAR PRIMARY KEY,
    chain_id                VARCHAR,
    anchor_id               VARCHAR,
    node_id                 VARCHAR,
    trade_date              DATE,
    latest_price            DOUBLE,
    pct_change_1d           DOUBLE,
    pct_change_5d           DOUBLE,
    volume                  DOUBLE,
    amount                  DOUBLE,
    open_interest           DOUBLE,
    latest_event_title      TEXT,
    latest_event_time       TIMESTAMP,
    quality_flags           VARCHAR,
    source_used             VARCHAR,
    as_of_timestamp         TIMESTAMP,
    created_at              TIMESTAMP
);
```

## 8.12.4 Loader 流程

```text
1. 校验所有 spec 文件存在
2. 校验 chain_id 唯一
3. 校验 node_id 唯一
4. 校验 edge 起点/终点 node_id 存在
5. 校验 anchor_id 唯一
6. 校验 anchor.node_id 存在
7. 校验 event_only=true 的私有公司不要求 ticker
8. 校验 commodity/index/future 不被标为 ordinary public_equity
9. 校验 P0_CORE / P0_EVENT 必须有 source_keys
10. 校验 source_validation_status 不为空
11. 写入 staging
12. WriteManager 写入 clean registry 表
```

## 8.12.5 source_validation_status 规则

| 状态 | 含义 | 处理 |
|---|---|---|
| `verified` | 已有官方/权威来源支持。 | 可进入默认展示。 |
| `needs_source` | 暂无充分来源键。 | 可保留映射，但前端标“待补来源”。 |
| `event_only_verified` | 私有事件锚已由官方/权威事件源支持。 | 只进事件流，不进普通行情。 |
| `price_proxy_needs_feed` | 商品/指数价格锚需要后续接入稳定行情源。 | 不阻断 chain 初始化，但阻断价格快照。 |

## 8.12.6 Daily Snapshot 生成

```text
1. 读取 industry_chain_anchor
2. 跳过 event_only=true 的普通行情抓取
3. 对 public_equity / ETF / future / commodity / index 读取 Layer 5 最新行情
4. 对 commodity/index 无稳定 feed 的锚点标 price_proxy_needs_feed
5. 读取最近事件
6. 生成 industry_chain_daily_snapshot
7. 前端产业链页面只读 snapshot + registry，不动态全库 join
```

## 8.12.7 Layer 5 映射规则

| instrument_type | 映射方式 |
|---|---|
| `public_equity` | 必须映射到 `instrument_registry.instrument_id`。 |
| `etf` | 映射到 ETF instrument_id。 |
| `future` | 映射到期货合约或连续合约。 |
| `commodity_proxy` | 映射到商品价格源或期货连续合约。 |
| `index_proxy` | 映射到指数源。 |
| `private_company` | 不映射行情，只进入 event registry。 |
| `regulatory_body` | 不映射行情，只进入政策/规则事件。 |

## 8.12.8 前端展示字段

每个 anchor 卡片至少展示：

```text
display_name_cn
anchor_tier
anchor_priority
status_explanation_cn
impact_explanation_cn
frontend_group
event_only
latest_price / pct_change_1d，如果适用
latest_event_title，如果适用
quality_flags
source_validation_status
```

## 8.12.9 API 契约

| API | 用途 |
|---|---|
| `GET /api/layer3/chains` | 获取产业链列表。 |
| `GET /api/layer3/chain/{chain_id}` | 获取单条产业链节点、边、锚点和快照。 |
| `GET /api/layer3/anchors` | 按 tier / role / priority 查询锚点。 |
| `GET /api/layer3/graph` | 获取可视化图谱数据。 |
| `GET /api/layer3/cross-chain-edges` | 获取跨链传导边。 |
| `GET /api/layer3/quality` | 获取配置健康状态。 |

## 8.12.10 CLI 契约

```bash
python -m quant_monitor layer3 validate-specs
python -m quant_monitor layer3 load-specs
python -m quant_monitor layer3 build-snapshot --date 2026-06-14
python -m quant_monitor layer3 health-check
```

## 8.12.11 验收测试

| 测试 | 预期 |
|---|---|
| anchor 指向不存在 node_id | loader 阻断。 |
| P0_CORE 缺少 source_keys | loader 阻断或标严重错误。 |
| private_company event_only=false | loader 阻断。 |
| commodity 被标为 public_equity | loader 阻断。 |
| edge 起点不存在 | loader 阻断。 |
| snapshot 试图写入 Layer 3 全量行情历史 | 测试失败。 |
| Layer 3 页面请求锚点行情 | 从 Layer 5 snapshot/view 读取。 |

## 8.12.12 实现任务拆分

```text
1. 实现 Layer3SpecValidator
2. 实现 Layer3RegistryLoader
3. 实现 Layer3GraphBuilder
4. 实现 Layer3SnapshotBuilder
5. 实现 Layer3QualityChecker
6. 实现 Layer 3 FastAPI routes
7. 实现前端图谱数据 contract
8. 实现测试集
```

## 用户决策补充：不复制 Layer 1 全套标准化字段

落实 D-09：Layer 3 不默认复制 Layer 1 的完整标准化字段。Layer 3 只保留本层业务必需字段；如后续确需引入 z-score、历史百分位、状态桶等标准化字段，必须在本层 contract 中按需增加，不得全量套用 Layer 1 模型。
