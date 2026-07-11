# Layer 4 市场结构模块

> 权威定位：本文件是 Layer 4 的实现级模块文档。Layer 4 负责“市场自己的规则、结构、宽度、板块、制度与内部状态”，不是简单市场名称列表，也不复用 Layer 1 的完整标准化物化字段体系。
> 来源继承：由 `quant_monitor_design_document_v1_6.md` 第 9 章拆分而来，并在本轮扩展为可交给 Claude Code / Codex 实现的模块规格。

---

# 1. 模块目标

Layer 4 的目标是把不同市场的“市场内部结构”转为可查询、可展示、可被 Agent 解释的结构化快照。

Layer 4 回答的问题是：

```text
这个市场今天内部是否健康？
上涨是否有宽度？
是指数少数权重股拉动，还是多数板块/股票同步扩散？
市场制度性状态是否异常，例如涨跌停、停牌、连板、期货换月、期权到期等？
这个市场结构是否支持 Layer 3 产业链主题扩散到 Layer 5 个股证据？
```

Layer 4 不负责：

```text
不负责存储全量个股历史行情，那个属于 Layer 5。
不负责宏观 regime 判断，那个属于 Layer 1。
不负责跨资产信号，那个属于 Layer 2。
不负责产业链锚点关系，那个属于 Layer 3。
不输出买卖动作。
```

---

# 2. 市场范围

第一阶段支持这些 `market_id`：

| market_id         | 中文名         | 类型            | 说明                                    |
| ----------------- | -------------- | --------------- | --------------------------------------- |
| `CN_A`            | A 股           | equity_market   | 上证、深证、创业板、科创板、北交所      |
| `US_EQ`           | 美股           | equity_market   | NYSE / Nasdaq / AMEX，含 ETF            |
| `HK_EQ`           | 港股           | equity_market   | 港股主板、南向资金、AH 溢价             |
| `CN_FUT`          | 中国期货       | futures_market  | 商品期货、金融期货                      |
| `GLOBAL_FUT`      | 全球期货       | futures_market  | 原油、黄金、铜、美债等全球期货/连续合约 |
| `GLOBAL_OPTIONS`  | 期权市场       | options_market  | 期权链、隐含波动、到期结构              |
| `FX`              | 外汇           | fx_market       | DXY、主要货币对                         |
| `CRYPTO_OPTIONAL` | 加密资产，可选 | optional_market | 仅做观察，不进入第一版核心              |

---

# 3. MarketAdapter 设计

每个市场必须有自己的 `MarketAdapter`，因为不同市场的规则不同，不能强行共用一套字段。

```text
AStockMarketAdapter
USEquityMarketAdapter
HKMarketAdapter
ChinaFuturesMarketAdapter
GlobalFuturesMarketAdapter
OptionsMarketAdapter
FXMarketAdapter
```

统一接口：

```python
class MarketAdapter:
    market_id: str

    def load_calendar(self, date_range) -> list[MarketCalendarRow]: ...
    def load_index_snapshot(self, trade_date) -> list[MarketIndexSnapshot]: ...
    def load_sector_snapshot(self, trade_date) -> list[MarketSectorSnapshot]: ...
    def load_breadth_snapshot(self, trade_date) -> MarketBreadthSnapshot: ...
    def load_rule_events(self, trade_date) -> list[MarketRuleEvent]: ...
```

Adapter 只负责读取/转换，不直接写 clean table。所有写入必须经过：

```text
MarketAdapter → staging_market_* → DataQualityValidator → SourceConflictValidator → WriteManager → 可信最终库或连续监控区 → snapshot table
```

---

# 4. 市场自己的规则

## 4.1 A 股

A 股需要独立处理：

```text
涨跌停
ST / *ST / 风险警示
主板 / 创业板 / 科创板 / 北交所
北向资金
融资融券
龙虎榜
连板高度
成交额
板块强度
停复牌
退市风险
新股 / 次新股
```

A 股宽度不能只看上涨家数，还应看：

```text
涨停数
跌停数
连板高度
炸板率，如有来源
成交额是否放大
申万行业扩散数量
概念板块扩散数量
融资余额变化
北向资金流向
```

## 4.2 美股

美股需要独立处理：

```text
盘前 / 盘中 / 盘后
财报季
S&P 500 / Nasdaq 100 / Russell 2000 / Dow
Sector ETF
Style ETF
Mag7
期权链
VIX / VVIX
新高新低
涨跌家数
成交额
```

美股的市场结构解释必须区分：

```text
大盘指数上涨，但小盘/等权不跟随
科技权重股推动指数
行业 ETF 扩散
信用 ETF / 长债 ETF 是否确认
期权波动是否同步变化
```

## 4.3 港股

港股需要独立处理：

```text
南向资金
窝轮牛熊证
低流动性折价
AH 溢价
恒生指数 / 恒生科技
地产 / 金融 / 科技权重
成交额集中度
```

## 4.4 期货

期货需要独立处理：

```text
主力合约切换
期限结构
基差
库存
持仓
交割月
连续合约拼接
换月事件
```

期货数据必须保留：

```text
contract_id
underlying_id
expiry_month
is_main_contract
open_interest
roll_event
term_structure_bucket
```

## 4.5 期权

期权需要独立处理：

```text
标的
到期日
行权价
Call / Put
成交量
未平仓量
隐含波动率
Greeks
Skew
Term Structure
```

第一版可以先实现期权链元数据和快照，不强制完整 Greeks。若无可靠来源，Greeks 可以标记为 `not_available`，不能伪造。

---

# 5. 表结构

## 5.1 market_registry

```sql
CREATE TABLE IF NOT EXISTS market_registry (
    market_id           VARCHAR PRIMARY KEY,
    market_name         VARCHAR,
    market_name_cn      VARCHAR,
    region              VARCHAR,
    currency            VARCHAR,
    timezone            VARCHAR,
    market_type         VARCHAR,
    calendar_id         VARCHAR,
    adapter_name        VARCHAR,
    is_enabled          BOOLEAN,
    notes               TEXT,
    updated_at          TIMESTAMP
);
```

## 5.2 market_calendar

```sql
CREATE TABLE IF NOT EXISTS market_calendar (
    market_id           VARCHAR,
    trade_date          DATE,
    is_trading_day      BOOLEAN,
    session_type        VARCHAR,
    open_time           TIME,
    close_time          TIME,
    timezone            VARCHAR,
    notes               TEXT,
    source              VARCHAR,
    quality_flag        VARCHAR,
    PRIMARY KEY (market_id, trade_date)
);
```

## 5.3 market_index_snapshot

```sql
CREATE TABLE IF NOT EXISTS market_index_snapshot (
    market_id           VARCHAR,
    index_id            VARCHAR,
    trade_date          DATE,
    open                DOUBLE,
    high                DOUBLE,
    low                 DOUBLE,
    close               DOUBLE,
    pre_close           DOUBLE,
    pct_change          DOUBLE,
    volume              DOUBLE,
    amount              DOUBLE,
    source              VARCHAR,
    as_of_timestamp     TIMESTAMP,
    fetch_time          TIMESTAMP,
    quality_flag        VARCHAR,
    PRIMARY KEY (market_id, index_id, trade_date)
);
```

## 5.4 market_sector_snapshot

```sql
CREATE TABLE IF NOT EXISTS market_sector_snapshot (
    market_id                   VARCHAR,
    sector_id                   VARCHAR,
    trade_date                  DATE,
    sector_name                 VARCHAR,
    sector_type                 VARCHAR,
    pct_change                  DOUBLE,
    volume                      DOUBLE,
    amount                      DOUBLE,
    advancers                   INTEGER,
    decliners                   INTEGER,
    unchanged                   INTEGER,
    leading_instruments_json    JSON,
    source                      VARCHAR,
    as_of_timestamp             TIMESTAMP,
    quality_flag                VARCHAR,
    PRIMARY KEY (market_id, sector_id, trade_date)
);
```

## 5.5 market_breadth_snapshot

```sql
CREATE TABLE IF NOT EXISTS market_breadth_snapshot (
    market_id                   VARCHAR,
    trade_date                  DATE,
    advancers                   INTEGER,
    decliners                   INTEGER,
    unchanged                   INTEGER,
    new_high_count              INTEGER,
    new_low_count               INTEGER,
    limit_up_count              INTEGER,
    limit_down_count            INTEGER,
    total_amount                DOUBLE,
    total_volume                DOUBLE,
    up_amount_ratio             DOUBLE,
    down_amount_ratio           DOUBLE,
    breadth_label               VARCHAR,
    source                      VARCHAR,
    as_of_timestamp             TIMESTAMP,
    quality_flag                VARCHAR,
    PRIMARY KEY (market_id, trade_date)
);
```

## 5.6 market_rule_event

```sql
CREATE TABLE IF NOT EXISTS market_rule_event (
    event_id            VARCHAR PRIMARY KEY,
    market_id           VARCHAR,
    trade_date          DATE,
    event_type          VARCHAR,
    event_level         VARCHAR,
    affected_scope      VARCHAR,
    description_cn      TEXT,
    source              VARCHAR,
    as_of_timestamp     TIMESTAMP,
    quality_flag        VARCHAR
);
```

---

# 6. 快照生成流程

```text
1. SyncJob 触发指定市场更新
2. MarketAdapter 抓取 calendar / index / sector / breadth / rule_event
3. 写入 staging_market_* 表
4. DataQualityValidator 检查字段、日期、空值、异常值
5. SourceConflictValidator 检查主源与验证源差异
6. WriteManager 按来源/质量准入写入 market_* 可信最终库或连续监控区，再构建带标签 snapshot
7. 构建 market_detail_view
8. FastAPI 提供 /api/layer4/markets 与 /api/layer4/markets/{market_id}
9. 前端展示市场结构卡片
10. Agent 只读取结构化事实，不输出动作语义
```

---

# 7. 与其他层的关系

| 关系              | 说明                                               |
| ----------------- | -------------------------------------------------- |
| Layer 1 → Layer 4 | 底层环境影响市场结构解释背景，但不直接改写市场快照 |
| Layer 2 → Layer 4 | 跨资产波动可作为市场结构解释背景                   |
| Layer 3 → Layer 4 | 产业链主题是否扩散到市场板块，由 Layer 4 验证      |
| Layer 4 → Layer 5 | 市场结构异常需要落到具体个股/ETF/期货/期权证据     |
| Layer 5 → Layer 4 | 个股异动可以反推市场内部扩散或结构异常             |

---

# 8. API 契约

```text
GET /api/layer4/markets
GET /api/layer4/markets/{market_id}
GET /api/layer4/markets/{market_id}/calendar
GET /api/layer4/markets/{market_id}/indices
GET /api/layer4/markets/{market_id}/sectors
GET /api/layer4/markets/{market_id}/breadth
GET /api/layer4/markets/{market_id}/rule-events
```

统一返回字段必须包含：

```text
market_id
as_of_timestamp
source_used
quality_flags
source_grade
quality_grade
manual_review_required
route_plan_id
stale_reason
```

---

# 9. CLI 契约

```bash
python -m qm sync-layer4 --market CN_A --date 2026-06-15
python -m qm sync-layer4 --market US_EQ --date 2026-06-15
python -m qm build-market-snapshot --market CN_A --date 2026-06-15
python -m qm validate-market --market CN_A --date 2026-06-15
```

---

# 10. 验收测试

必须通过：

```text
market_registry 初始化后 market_id 不重复。
market_calendar 不能出现同一 market_id + trade_date 多条记录。
非交易日不能生成普通市场快照，除非 session_type 明确允许。
A 股涨跌停字段缺失时，quality_flag 必须提示。
期货主力合约切换必须写入 roll_event 或 rule_event。
Layer 4 不得写入 Layer 5 个股全量历史表。
Layer 4 不得使用 Layer 1 的完整标准化物化字段。
Agent 输出不得包含买、卖、加仓、减仓等动作语义。
```

## 用户决策补充：不复制 Layer 1 全套标准化字段

落实 D-09：Layer 4 不默认复制 Layer 1 的完整标准化字段。Layer 4 只保留本层业务必需字段；如后续确需引入 z-score、历史百分位、状态桶等标准化字段，必须在本层 contract 中按需增加，不得全量套用 Layer 1 模型。

## ADR-017 连续监控消费规则

市场结构快照可使用受治理连续监控视图维持业务监控，但 API 输出中的 `source_used` 与
`quality_flags` 必须扩展为共享契约的来源等级、质量等级、RoutePlan 和人工复核语义；默认读取与
默认回测仍排除审计归档区。
