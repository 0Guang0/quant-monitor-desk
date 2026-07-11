# Layer 5 个股 / 合约证据模块

> 权威定位：本文件是 Layer 5 的实现级模块文档。Layer 5 是最终证据落点，保存个股、ETF、期货、期权、商品合约的可验证证据链。它不是传统技术指标信号层，不输出买卖动作。
> 来源继承：由 `quant_monitor_design_document_v1_6.md` 第 10 章拆分而来，并在本轮扩展为可交给 Claude Code / Codex 实现的模块规格。

---

# 1. 模块目标

Layer 5 回答的问题是：

```text
某个具体标的今天发生了什么？
它的行情、财务、公告、新闻、资金、事件和产业链映射是否形成证据？
这个证据能否被 Layer 1-4 的背景解释？
证据来源是否可追溯？
是否需要人工复核？
```

Layer 5 是全系统最终落点，但它仍然必须遵守：

```text
不直接输出买卖建议。
不绕过 WriteManager 写入。
不把 Agent 生成文本当作事实来源。
不把来源不明的新闻/观点写成客观事实。
不把技术指标当作核心信号，只作为 baseline / reference。
```

---

# 2. 资产范围

第一阶段支持：

```text
股票：A 股、美股、港股
ETF：行业 ETF、风格 ETF、债券 ETF、商品 ETF
期货：商品期货、股指期货、利率期货等
期权：股票期权、ETF 期权、指数期权
指数：主要宽基指数、行业指数
商品/价格代理：铜、油、金、铀、锂等，如有可得数据
```

---

# 3. 核心表结构

## 3.1 instrument_registry

```sql
CREATE TABLE IF NOT EXISTS instrument_registry (
    instrument_id       VARCHAR PRIMARY KEY,
    symbol              VARCHAR,
    instrument_name     VARCHAR,
    instrument_name_cn  VARCHAR,
    asset_type          VARCHAR,
    market_id           VARCHAR,
    exchange            VARCHAR,
    currency            VARCHAR,
    list_date           DATE,
    delist_date         DATE,
    is_active           BOOLEAN,
    board               VARCHAR,
    sector              VARCHAR,
    industry            VARCHAR,
    concept_tags_json   JSON,
    source              VARCHAR,
    updated_at          TIMESTAMP
);
```

## 3.2 security_bar_daily

```sql
CREATE TABLE IF NOT EXISTS security_bar_daily (
    instrument_id       VARCHAR,
    trade_date          DATE,
    open                DOUBLE,
    high                DOUBLE,
    low                 DOUBLE,
    close               DOUBLE,
    pre_close           DOUBLE,
    change              DOUBLE,
    pct_change          DOUBLE,
    volume              DOUBLE,
    amount              DOUBLE,
    turnover_rate       DOUBLE,
    amplitude           DOUBLE,
    vwap                DOUBLE,
    adjust_type         VARCHAR,
    adjust_factor       DOUBLE,
    source              VARCHAR,
    as_of_timestamp     TIMESTAMP,
    fetch_time          TIMESTAMP,
    quality_flag        VARCHAR,
    PRIMARY KEY (instrument_id, trade_date, adjust_type)
);
```

## 3.3 futures_bar_daily

```sql
CREATE TABLE IF NOT EXISTS futures_bar_daily (
    instrument_id           VARCHAR,
    trade_date              DATE,
    contract_code           VARCHAR,
    underlying_id           VARCHAR,
    maturity_month          VARCHAR,
    open                    DOUBLE,
    high                    DOUBLE,
    low                     DOUBLE,
    close                   DOUBLE,
    settlement_price        DOUBLE,
    volume                  DOUBLE,
    amount                  DOUBLE,
    open_interest           DOUBLE,
    basis                   DOUBLE,
    main_contract_flag      BOOLEAN,
    roll_adjustment         DOUBLE,
    source                  VARCHAR,
    as_of_timestamp         TIMESTAMP,
    quality_flag            VARCHAR,
    PRIMARY KEY (instrument_id, trade_date)
);
```

## 3.4 options_chain_snapshot

```sql
CREATE TABLE IF NOT EXISTS options_chain_snapshot (
    option_id               VARCHAR,
    underlying_id           VARCHAR,
    trade_date              DATE,
    expiry_date             DATE,
    strike_price            DOUBLE,
    option_type             VARCHAR,
    open                    DOUBLE,
    high                    DOUBLE,
    low                     DOUBLE,
    close                   DOUBLE,
    volume                  DOUBLE,
    amount                  DOUBLE,
    open_interest           DOUBLE,
    implied_volatility      DOUBLE,
    delta                   DOUBLE,
    gamma                   DOUBLE,
    vega                    DOUBLE,
    theta                   DOUBLE,
    rho                     DOUBLE,
    source                  VARCHAR,
    as_of_timestamp         TIMESTAMP,
    quality_flag            VARCHAR,
    PRIMARY KEY (option_id, trade_date)
);
```

## 3.5 financial_statement_snapshot

```sql
CREATE TABLE IF NOT EXISTS financial_statement_snapshot (
    instrument_id       VARCHAR,
    report_period       DATE,
    statement_type      VARCHAR,
    revenue             DOUBLE,
    net_profit          DOUBLE,
    roe                 DOUBLE,
    roa                 DOUBLE,
    gross_margin        DOUBLE,
    operating_cash_flow DOUBLE,
    source              VARCHAR,
    as_of_timestamp     TIMESTAMP,
    quality_flag        VARCHAR,
    PRIMARY KEY (instrument_id, report_period, statement_type)
);
```

## 3.6 valuation_snapshot

```sql
CREATE TABLE IF NOT EXISTS valuation_snapshot (
    instrument_id           VARCHAR,
    trade_date              DATE,
    market_cap              DOUBLE,
    free_float_market_cap   DOUBLE,
    pe_ttm                  DOUBLE,
    pb                      DOUBLE,
    ps                      DOUBLE,
    pcf                     DOUBLE,
    dividend_yield          DOUBLE,
    source                  VARCHAR,
    as_of_timestamp         TIMESTAMP,
    quality_flag            VARCHAR,
    PRIMARY KEY (instrument_id, trade_date)
);
```

## 3.7 event_registry

```sql
CREATE TABLE IF NOT EXISTS event_registry (
    event_id            VARCHAR PRIMARY KEY,
    instrument_id       VARCHAR,
    event_date          DATE,
    event_type          VARCHAR,
    event_title         TEXT,
    event_summary       TEXT,
    source              VARCHAR,
    source_url          TEXT,
    local_path          TEXT,
    content_hash        VARCHAR,
    as_of_timestamp     TIMESTAMP,
    quality_flag        VARCHAR
);
```

## 3.8 evidence_chain

```sql
CREATE TABLE IF NOT EXISTS evidence_chain (
    evidence_id         VARCHAR PRIMARY KEY,
    target_id           VARCHAR,
    target_type         VARCHAR,
    trade_date          DATE,
    layer1_context      TEXT,
    layer2_context      TEXT,
    layer3_context      TEXT,
    layer4_context      TEXT,
    layer5_context      TEXT,
    evidence_summary    TEXT,
    confidence          DOUBLE,
    need_human_review   BOOLEAN,
    created_by          VARCHAR,
    created_at          TIMESTAMP
);
```

## 3.9 stock_model_evidence

```sql
CREATE TABLE IF NOT EXISTS stock_model_evidence (
    evidence_id         VARCHAR PRIMARY KEY,
    instrument_id       VARCHAR,
    trade_date          DATE,
    evidence_type       VARCHAR,
    evidence_source     VARCHAR,
    evidence_detail     TEXT,
    related_layer       VARCHAR,
    confidence          DOUBLE,
    created_at          TIMESTAMP
);
```

---

# 4. 证据类型

Layer 5 证据类型建议：

| evidence_type       | 含义         | 示例                             |
| ------------------- | ------------ | -------------------------------- |
| `price_volume`      | 价量证据     | 放量突破、缩量下跌、异常成交额   |
| `financial`         | 财务证据     | 收入增速、利润变化、现金流变化   |
| `valuation`         | 估值证据     | PE/PB/PS/市值分位                |
| `announcement`      | 公告证据     | 财报、订单、回购、增发、诉讼     |
| `news_event`        | 新闻事件     | 产业新闻、政策、监管、供应链事件 |
| `capital_flow`      | 资金证据     | 北向、融资融券、主力资金等       |
| `industry_exposure` | 产业链映射   | 归属 Layer 3 某锚点或节点        |
| `market_structure`  | 市场结构证据 | 所在市场/板块宽度配合            |
| `risk_flag`         | 风险标记     | ST、停牌、退市、重大诉讼         |

---

# 5. 数据流

```text
InstrumentRegistry 初始化
    ↓
行情 / 财务 / 公告 / 新闻 / 资金流 / 事件抓取
    ↓
staging_layer5_* 表
    ↓
DataQualityValidator
    ↓
SourceConflictValidator
    ↓
WriteManager
    ↓
Layer 5 可信最终库 / 连续监控视图 / snapshot / event 表
    ↓
evidence_chain_builder
    ↓
FastAPI /api/layer5/securities/{instrument_id}
    ↓
前端个股证据页 / Agent 五层解释
```

---

# 6. 证据链生成规则

`evidence_chain_builder` 只能使用结构化事实：

```text
Layer 1: axis_feature_snapshot / axis_interpretation_snapshot
Layer 2: cross_asset_daily_snapshot / cross_asset_signal_snapshot
Layer 3: industry_chain_daily_snapshot / anchor / node / edge
Layer 4: market_index_snapshot / sector / breadth / rule_event
Layer 5: security_bar_daily / financial / event / valuation
```

不得使用：

```text
Agent 自己编造的未验证结论
未入库的网页片段
无 source_url / content_hash 的新闻
无 quality_flag 的来源
```

---

# 7. API 契约

```text
GET /api/layer5/securities/{instrument_id}
GET /api/layer5/securities/{instrument_id}/bars
GET /api/layer5/securities/{instrument_id}/financials
GET /api/layer5/securities/{instrument_id}/valuation
GET /api/layer5/securities/{instrument_id}/events
GET /api/layer5/securities/{instrument_id}/evidence
GET /api/evidence/{evidence_id}
```

每个 Layer 5 API 返回的事实和 evidence ref 必须带 `source_used`、`source_grade`、`quality_grade`、
`manual_review_required` 与 `route_plan_id`；连续监控事实还必须带主源失败原因，不能仅以单一
`quality_flag` 表示。

---

# 8. CLI 契约

```bash
python -m qm sync-layer5 --market CN_A --date 2026-06-15
python -m qm sync-instrument --instrument 000001.SZ --date 2026-06-15
python -m qm build-evidence --instrument 000001.SZ --date 2026-06-15
python -m qm validate-layer5 --instrument 000001.SZ --date 2026-06-15
```

---

# 9. 验收测试

必须通过：

```text
instrument_registry 中 instrument_id 不重复。
security_bar_daily 不允许同一 instrument_id + trade_date + adjust_type 重复。
行情字段 high 不得小于 low。
volume / amount / open_interest 不得为负。
财报字段必须带 report_period 与 statement_type。
event_registry 必须带 source 或 local_path，不能无来源。
evidence_chain 必须至少包含一层结构化 context。
Agent 不得把 evidence_chain 输出成买卖建议。
Layer 5 不得直接写 Layer 1 / Layer 2 / Layer 3 / Layer 4 表。
```

## 用户决策补充：不复制 Layer 1 全套标准化字段

落实 D-09：Layer 5 不默认复制 Layer 1 的完整标准化字段。Layer 5 只保留本层业务必需字段；如后续确需引入 z-score、历史百分位、状态桶等标准化字段，必须在本层 contract 中按需增加，不得全量套用 Layer 1 模型。

## ADR-017 连续监控消费规则

Layer 5 的行情、财务、事件和 evidence refs 必须可追溯到 `source_grade`、`quality_grade`、实际
来源、RoutePlan 和人工复核状态。质量异常但可归一化的数据可以形成带风险标记的连续监控证据；
不得写成可信 clean 事实或无标签证据。
