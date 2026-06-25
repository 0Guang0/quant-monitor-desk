# 数据源注册与优先级模块

> 拆分说明：本文件由 `quant_monitor_design_document_v1_6.md` 拆分生成；当前步骤只做结构拆分与明显版本/编号残留修正，不删减原有细节。
> 来源：第 4 章

# 4. 数据源注册与优先级

## 4.1 数据源分层

| 数据源                | 推荐角色                     | 第一阶段定位                   |
| --------------------- | ---------------------------- | ------------------------------ |
| QMT / xtdata          | 实时行情、分钟线、实盘相关   | 核心源之一                     |
| baostock              | A 股历史日线、基础财务       | 主历史源之一                   |
| AkShare               | 补充数据、指数、板块、资金流 | 快速接入与补充                 |
| 巨潮 CNINFO           | 公告、财报、PDF 原文         | 权威公告源                     |
| 东方财富              | 资金流、板块、公告备份       | 重要补充源                     |
| Yahoo / yfinance      | 美股、ETF、全球资产辅助      | 研究与补充，不做核心生产源     |
| 同花顺 / 问财 / iFinD | 概念、题材、智能查询、研报   | 正式使用需授权；免费端只做辅助 |
| 腾讯财经              | 实时行情备份、轻量校验       | 备份源                         |
| 百度股市通            | 新闻、行情辅助               | 辅助源，不做主源               |

## 4.2 source_registry

```sql
CREATE TABLE IF NOT EXISTS source_registry (
    source_id           VARCHAR PRIMARY KEY,
    source_name         VARCHAR,
    source_type         VARCHAR,
    allowed_domain      VARCHAR,
    trust_level         INTEGER,
    license_type        VARCHAR,
    official_api        BOOLEAN,
    is_enabled          BOOLEAN,
    default_priority    INTEGER,
    notes               TEXT
);
```

## 4.3 数据源冲突原则

1. 原始数据永远不删。
2. 标准表只保存一个主值。
3. 关键字段多源校验。
4. 衍生指标自己计算。
5. 口径不统一的数据分开存。
6. 冲突严重时进入 conflict 表，不自动覆盖。

## 4.4 多源冲突分级治理

不同数据源不能简单“谁优先级高就永远覆盖”，也不能“只要有差异就人工确认”。系统采用分级处理：

```text
raw 数据保留
    ↓
字段/单位/时间/复权标准化
    ↓
按字段类型判断冲突
    ↓
小差异自动接受，记录校验
中等差异主源写入但标 warning
严重差异进入 source_conflict 并触发重抓
重抓后仍严重冲突才人工确认
```

### 4.4.1 客观事实类字段

适用字段：

```text
open, high, low, close, pre_close, volume, amount, settlement_price, open_interest, index_level
```

处理规则：

| 情况             | 处理                                                          |
| ---------------- | ------------------------------------------------------------- |
| 差异在容忍范围内 | 主源值进入标准表，备用源记录为校验通过                        |
| 差异略超容忍范围 | 主源值进入标准表，但 `quality_flag=source_divergence_warning` |
| 差异严重         | 不写标准表，写入 `source_conflict`，触发 ReconcileJob 重抓    |
| 重抓后仍严重冲突 | 标记 `manual_review_required=true`，等待人工确认              |

### 4.4.2 口径差异类字段

适用字段：

```text
主力资金流、大单资金流、题材概念、新闻情绪、机构观点、估值分位、平台热度
```

这些字段本来就没有统一口径，不强行合成一个最终值。建议分源保存：

```text
eastmoney_main_inflow
ths_main_inflow
tencent_main_inflow
```

或者使用长表：

```sql
CREATE TABLE IF NOT EXISTS source_metric_observation (
    metric_id       VARCHAR,
    instrument_id   VARCHAR,
    source          VARCHAR,
    as_of_timestamp TIMESTAMP,
    value           DOUBLE,
    unit            VARCHAR,
    quality_flag    VARCHAR,
    PRIMARY KEY (metric_id, instrument_id, source, as_of_timestamp)
);
```

### 4.4.3 备用源接管规则

当主源缺失、过期、接口失败或 schema drift 时，可以用备用源接管，但必须写入：

```text
source_switched = true
primary_source_failed = true
fallback_source = xxx
stale_reason = xxx
quality_flag = source_switched
```

禁止 silent switch。

### 4.4.4 source_conflict 表

```sql
CREATE TABLE IF NOT EXISTS source_conflict (
    conflict_id         VARCHAR PRIMARY KEY,
    data_domain         VARCHAR,
    instrument_id       VARCHAR,
    field_name          VARCHAR,
    as_of_timestamp     TIMESTAMP,
    primary_source      VARCHAR,
    primary_value       VARCHAR,
    competing_source    VARCHAR,
    competing_value     VARCHAR,
    normalized_diff     DOUBLE,
    severity            VARCHAR,
    reconcile_status    VARCHAR,
    manual_review_required BOOLEAN,
    created_at          TIMESTAMP,
    resolved_at         TIMESTAMP
);
```

---

---

# 5. P0 扩展：实现级数据源设计

> 本节为第一轮扩展新增内容，不删除上方原始拆分内容。  
> 目标：把“数据源清单”升级为可实现的 Source Registry、Adapter Contract、Health Check 与 Primary / Validation / FallbackPolicy 规则。

## 5.1 数据源模块职责

数据源模块不直接决定最终数据是否可信，它负责把外部数据以可审计、可复盘的方式拉回本地。

职责包括：

```text
1. 维护 source_registry。
2. 定义每个 source 可抓取的数据域。
3. 定义每个数据源的授权、频率、延迟、稳定性和 fallback 边界。
4. 提供统一 DataAdapter 接口。
5. 输出 raw 文件、staging 数据和 fetch_log。
6. 提供 source health check。
7. 发现 schema drift、限流、认证失败、空数据、延迟更新。
```

不负责：

```text
1. 不负责最终主值选择。
2. 不直接写 clean 表。
3. 不跳过 Validation。
4. 不在 Adapter 内部做复杂金融解释。
5. 不把 fallback 伪装成 primary。
```

---

## 5.2 Source Registry 字段最终版

```sql
CREATE TABLE IF NOT EXISTS source_registry (
    source_id              VARCHAR PRIMARY KEY,
    source_name            VARCHAR,
    source_type            VARCHAR, -- CHECK: broker_terminal / public_market_data / aggregator / filing_announcement / official_api / local_sdk / vendor_api
    allowed_domain         VARCHAR, -- JSON array string or comma-separated list
    trust_level            INTEGER, -- 0-100 confidence score; higher is more trusted
    license_type           VARCHAR, -- CHECK: user_local_authorized / public_free / public_free_aggregator / public_official / public_terms_sensitive / official_free / local_authorized / public_web
    official_api           BOOLEAN,
    is_enabled             BOOLEAN,
    default_priority       INTEGER,
    rate_limit_policy      VARCHAR,
    auth_required          BOOLEAN,
    requires_local_client  BOOLEAN,
    expected_frequency     VARCHAR,
    expected_lag           VARCHAR,
    timezone               VARCHAR,
    fallback_allowed       BOOLEAN,
    validation_only        BOOLEAN,
    notes                  TEXT,
    updated_at             TIMESTAMP
);
```

### 字段解释

| 字段               | 解释                                                                                                                                                                                             |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `source_type`      | 必须兼容 `specs/schema/schema.sql` 与 migration 009 的 CHECK 枚举：`broker_terminal` / `public_market_data` / `aggregator` / `filing_announcement` / `official_api` / `local_sdk` / `vendor_api` |
| `allowed_domain`   | 该源允许服务的数据域，避免一个源被滥用到所有地方                                                                                                                                                 |
| `trust_level`      | 用于默认主源排序，但不能绕过冲突检查                                                                                                                                                             |
| `license_type`     | 必须兼容 `specs/schema/schema.sql` 与 migration 009 的 CHECK 枚举；决定是否能正式生产使用                                                                                                        |
| `expected_lag`     | 用于 stale 判断                                                                                                                                                                                  |
| `fallback_allowed` | 该源是否允许作为 fallback 接管                                                                                                                                                                   |
| `validation_only`  | 是否只做校验，不进入主值                                                                                                                                                                         |

---

## 5.3 Primary / Validation / FallbackPolicy

新版统一使用三角色，不再使用旧的 旧三源命名。

| 新角色           | 含义                               | 历史说明                                                                                                                                       |
| ---------------- | ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `Primary`        | 正常情况下进入 clean 表的主源      | 旧文档中的 Primary 仅作为历史迁移参考                                                                                                          |
| `Validation`     | 用于校验主源，不默认接管           | 旧数据源角色名 `Shadow` 不得作为 source role / default role / fallback role；Layer 1 `SHADOW` 诊断标签不是数据源角色，见本页“旧角色名强约束”。 |
| `FallbackPolicy` | 不是第三外部源，而是失败时如何处理 | 旧数据源角色名 `Emergency` 不得作为 source role / default role / fallback role。                                                               |

FallbackPolicy 可以是：

```text
retry_same_source
use_validation_source_with_flag
use_last_good_cache
mark_missing
manual_review_required
skip_until_next_publish
```

### 禁止事项

```text
1. 不允许 silent switch。
2. 不允许把 Validation 源无标记地写成 Primary。
3. 不允许没有 source_used 的数据入库。
4. 不允许用 unknown license 的源做生产主源。
5. 不允许把网页抓取当成官方 API；网页/搜索类补充源必须用 schema CHECK 允许的 `aggregator` 或其他合规 `source_type` 标注，并保持 `validation_only=true` / evidence-only 边界。
```

---

## 5.4 数据域分类

```text
market_bar_1d          日线行情
market_bar_1m          分钟线行情
corporate_action       复权、分红、拆股
fundamental            财务与估值
announcement           公告、财报 PDF
news_event             新闻、事件
capital_flow           资金流
layer1_axis            五轴指标
layer2_sensor          跨资产传感器
layer3_anchor_event    产业链锚点事件
layer4_market_structure 市场结构
layer5_security_evidence 个股/合约证据
```

每个 Adapter 只能声明自己支持的 `data_domain`，调度器不得要求它抓未声明领域。

---

## 5.5 Adapter 接口协议

### 5.5.1 Python 抽象接口

```python
from dataclasses import dataclass
from typing import Protocol, Iterable, Any

@dataclass(frozen=True)
class FetchRequest:
    run_id: str
    source_id: str
    data_domain: str
    market_id: str | None
    instrument_id: str | None
    start_time: str | None
    end_time: str | None
    cursor: str | None
    force_refresh: bool = False

@dataclass(frozen=True)
class FetchResult:
    run_id: str
    source_id: str
    data_domain: str
    status: str
    raw_file_paths: list[str]
    staging_table: str | None
    row_count: int
    content_hash: str | None
    schema_hash: str | None
    as_of_timestamp: str | None
    publish_timestamp: str | None
    fetch_time: str
    error_message: str | None

class DataAdapter(Protocol):
    source_id: str
    supported_domains: list[str]

    def fetch(self, request: FetchRequest) -> FetchResult:
        ...

    def health_check(self) -> dict[str, Any]:
        ...
```

### 5.5.2 Adapter 输出要求

Adapter 每次 fetch 必须输出：

```text
source_id
run_id
data_domain
fetch_time
as_of_timestamp
raw_file_paths
content_hash
schema_hash
row_count
status
```

如果接口失败，也必须写 fetch_log，不允许静默失败。

---

## 5.6 Fetch Log

```sql
CREATE TABLE IF NOT EXISTS fetch_log (
    fetch_id            VARCHAR PRIMARY KEY,
    run_id              VARCHAR,
    job_id              VARCHAR,
    source_id           VARCHAR,
    data_domain         VARCHAR,
    market_id           VARCHAR,
    instrument_id       VARCHAR,
    request_params_hash VARCHAR,
    status              VARCHAR,
    row_count           INTEGER,
    raw_file_paths      VARCHAR,
    content_hash        VARCHAR,
    schema_hash         VARCHAR,
    as_of_timestamp     TIMESTAMP,
    publish_timestamp   TIMESTAMP,
    fetch_time          TIMESTAMP,
    latency_ms          INTEGER,
    retry_count         INTEGER,
    error_type          VARCHAR,
    error_message       TEXT
);
```

---

## 5.7 重试、限流、缓存策略

| 场景              | 处理                                      |
| ----------------- | ----------------------------------------- |
| 网络超时          | 指数退避重试，最多 3 次                   |
| 429 / rate limit  | 按 source policy 暂停，不换源伪装成功     |
| 403 / auth failed | 标记 AUTH_FAILED，停止该源任务            |
| 空数据            | 标记 EMPTY_RESPONSE，进入质量检查         |
| schema drift      | 标记 SCHEMA_DRIFT，不写 clean 表          |
| 数据尚未发布      | 标记 NOT_PUBLISHED_YET，可等待下次调度    |
| 接口字段变更      | 写 schema_hash 变化，触发人工或适配器更新 |

缓存规则：

```text
1. api_cache 可短期缓存，默认 1-7 天。
2. last_good_cache 只能在 FallbackPolicy 允许时使用。
3. 使用 last_good_cache 必须写 stale_reason。
4. 缓存不能覆盖 raw 原始证据。
```

---

## 5.8 Source Health Check

每日检查：

```text
1. source 是否启用。
2. 最近一次成功 fetch 时间。
3. 最近 7 次 fetch 成功率。
4. 平均 latency。
5. schema_hash 是否变化。
6. 是否连续 EMPTY_RESPONSE。
7. 是否触发 rate limit。
8. license / auth 是否失效。
```

输出表：

```sql
CREATE TABLE IF NOT EXISTS source_health_snapshot (
    snapshot_id         VARCHAR PRIMARY KEY,
    source_id           VARCHAR,
    as_of_timestamp     TIMESTAMP,
    health_status       VARCHAR,
    success_rate_7d     DOUBLE,
    last_success_time   TIMESTAMP,
    last_error_time     TIMESTAMP,
    last_error_type     VARCHAR,
    avg_latency_ms_7d   DOUBLE,
    schema_drift_count  INTEGER,
    rate_limit_count    INTEGER,
    notes               TEXT
);
```

---

## 5.9 第一阶段数据源定位

| 数据源                | 第一阶段角色                 | 注意事项                                    |
| --------------------- | ---------------------------- | ------------------------------------------- |
| QMT / xtdata          | A 股实时、分钟线、本地授权源 | 需要本地客户端和授权，作为核心源但仍需校验  |
| baostock              | A 股历史日线、基础财务       | 适合历史补齐，不适合实时                    |
| AkShare               | 快速补充、板块、指数、资金流 | 口径变化需严格 schema drift 检测            |
| 巨潮 CNINFO           | 公告、财报 PDF               | 公告原文权威源，文件入 File Lake            |
| 东方财富              | 资金流、板块、公告备份       | 资金流口径独立保存，不强行合并              |
| Yahoo / yfinance      | 美股、ETF、全球资产辅助      | 第一阶段研究/辅助，不做关键生产唯一源       |
| 同花顺 / iFinD        | 题材、概念、研报             | 正式使用必须确认授权                        |
| FRED / Cboe / CFTC 等 | 五轴和全球指标               | 进入 Layer 1 / Layer 2 专用 source registry |

---

### 5.9.1 总数据源扩展清单与定位

`specs/datasource_registry/source_registry.yaml` 是机器可读权威；本表是面向设计、实现和审核的解释口径。新增外部源默认 `enabled_by_default=false`，只有完成 adapter、capability、route plan、ResourceGuard、license/auth gate 和回放证据后才能启用。

| 数据源                   | 数据类型                                    | 推荐定位                                      | 用途                                      | 可靠性/稳定性/实时性判断                                                           |
| ------------------------ | ------------------------------------------- | --------------------------------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------- |
| QMT / xtdata             | A 股实时、分钟线、日线                      | A 股实时 Primary（用户本机授权后）            | 实时行情、分钟线、交易日内监控            | 授权终端可靠性高、实时性强；默认禁用，需用户确认本机授权                           |
| baostock                 | A 股历史日线、基础财务                      | A 股低频 Primary                              | 历史日线补齐、基础财务                    | 免费稳定，适合日频/低频；不适合实时                                                |
| AkShare                  | A 股/宏观聚合数据                           | Validation                                    | 指数、板块、宏观补充、快速验证            | 覆盖广但上游口径可能变化；必须 schema_hash 与 quality_flags                        |
| 巨潮 CNINFO              | 公告、财报、PDF 原文                        | A 股披露 Primary                              | 公告索引、财报 PDF、文件证据链            | 官方/准官方披露源，权威性高；需 polite fetch 与文件哈希                            |
| Yahoo Finance / yfinance | 美股、ETF、期权链、全球资产参考             | Validation                                    | 美股/ETF/US option chain 辅助校验         | 覆盖方便但条款和稳定性敏感；不做生产唯一主源                                       |
| Alpha Vantage            | 美股、ETF、期权链、FX、商品、宏观、加密参考 | API-key gated Primary candidate               | 文档化 API 补充美国市场与跨资产数据       | 稳定性好于网页源；受 API key、限流和授权条款约束                                   |
| Stooq                    | 股票/ETF/外汇/商品历史行情                  | Validation / low-frequency fallback           | 全球历史价格趋势、低频交叉验证            | 适合日频历史，不适合实时生产                                                       |
| Deribit                  | 加密期货、期权、IV、term structure          | Crypto derivatives Primary candidate          | BTC/ETH 期货曲线、期权 IV surface         | 交易所级市场数据，实时性强；只允许 market-data，禁止账户/交易能力                  |
| CoinGecko                | 加密现货聚合、币种映射、市值                | Spot/reference Primary candidate + Validation | BTC/ETH 现货参考价、市值、asset reference | 聚合源覆盖广；不能替代交易所逐笔/盘口事实源                                        |
| US Treasury              | 国债收益率、利率曲线、通胀预期参考          | Official Primary                              | 利率曲线、期限利差、通胀预期上下文        | 官方源，可靠性最高；日频/低频，适合 Layer 1 regime                                 |
| SEC EDGAR                | 公司披露、Form 4 内部人交易                 | Official Primary                              | 美国 filings、Form 4 买卖信号、原文证据   | 官方披露源，准确性高；必须保存 accession/content_hash                              |
| CFTC COT                 | 期货持仓                                    | Official Primary                              | 机构/非商业仓位方向、smart-money 背景     | 官方周频，稳定但滞后；不得当实时仓位                                               |
| BIS                      | 央行、政策利率、信贷缺口                    | Official Primary                              | 全球政策利率、credit/GDP gap、宏观 regime | 官方/央行协作数据，低频稳健                                                        |
| World Bank               | GDP、人口、贸易、发展指标                   | Official Primary                              | 长周期宏观背景变量                        | 官方低频数据，可靠但滞后，不做短线触发                                             |
| FRED                     | 美国宏观序列                                | API-key gated Primary candidate               | Layer 1 宏观序列、官方/准官方美国宏观     | 已有 sandbox_candidate；需 key 与 live gate                                        |
| Kalshi                   | 监管预测市场合约                            | Prediction probability Primary candidate      | 美国政治/经济事件概率、二元合约价格       | 受监管事件市场，适合概率信号；不是事实结果源                                       |
| Polymarket               | 预测市场合约                                | Prediction probability Validation             | 全球事件概率、市场情绪、流动性观察        | 流动性和 resolution 质量差异大；必须记录 volume/liquidity/spread/resolution_source |
| mootdx / TDX compatible  | A 股 security list、日线、指数              | Validation                                    | 通达信兼容校验、A 股代码表探针            | 默认禁用；只读校验，不得 silent fallback                                           |
| 东方财富                 | A 股行情、板块、资金流、公告备份            | Validation                                    | 资金流、板块、公告备份和日线交叉验证      | 覆盖强但网页/API 口径可能变；资金流必须分源保存                                    |
| 新浪财经                 | A 股行情轻量备份                            | Fallback / Validation                         | 实时/日线轻量校验、故障诊断               | 稳定性和授权边界弱于主源；不进入主值接管                                           |
| 同花顺 / iFinD           | 概念、题材、研报、资金流                    | Licensed Validation                           | 题材、概念、研报索引、授权数据补充        | 仅商业授权后启用；免费网页端不得生产化                                             |
| Web Search               | 网页补充证据                                | Manual-review Validation only                 | VIX、CDS、事件解释、resolution 佐证       | 非结构化且不稳定；只能进 evidence/manual_review，不直接写 clean 表                 |

### 5.9.2 四点关键实现建议

1. **按 domain-level role 分配，不按 provider 平铺。** 新增 source 必须同时写入 `source_registry.yaml`、`source_capabilities.yaml` 和 route plan 规则；同一个 provider 在不同 domain 可以是 Primary、Validation 或 fallback candidate。示例：Alpha Vantage 可作为 `us_equity_daily_bar` 的 API-key gated Primary candidate，但在 `macro_series` 中只能作为 FRED/官方源的补充候选。
2. **预测市场单独建概率信号语义。** `kalshi`、`polymarket` 只能写入 `prediction_market_probability`、`regulated_event_contract`、`event_market_contract` 等概率/合约域；必须保存 `liquidity`、`volume`、`spread`、`resolution_source`、`closed/active` 状态。其价格不得被解释为事实结果，也不得替代 SEC/CFTC/Treasury/CNINFO 等事实源。
3. **官方宏观源按低频/滞后处理。** US Treasury、CFTC COT、BIS、World Bank、FRED 等应进入 Layer 1/Layer 2 regime 和背景变量，不得驱动分钟级 UI 或实时告警；允许 `use_last_good_cache`，但必须写 `stale_reason`、`source_fetch_id`、`content_hash`。
4. **中国市场继续保持授权终端/官方披露优先。** QMT 授权后才可作为实时主源；CNINFO 是公告/财报原文主源；baostock 是历史日线/基础财务主源；AkShare、东方财富、Sina、mootdx、同花顺免费端只能做验证、补充或授权后候选，并强制 schema drift、限速、缓存和 no-silent-fallback。

---

## 5.10 验收测试

| 测试                                    | 预期                                              |
| --------------------------------------- | ------------------------------------------------- |
| 未声明 data_domain 的 adapter 被调用    | 拒绝                                              |
| source disabled                         | 不执行抓取                                        |
| 403 auth failed                         | 写 fetch_log，停止该源任务                        |
| schema_hash 变化                        | 标记 SCHEMA_DRIFT，不直接写 clean                 |
| 主源失败且 fallback_policy=mark_missing | 不接管，写缺失                                    |
| 使用 last_good_cache                    | 必须写 stale_reason 和 source_switched            |
| Validation 源数据不同                   | 进入 SourceConflictValidator，不在 Adapter 内判断 |

---

## 5.11 与其他模块关系

```text
data_sources.md
        ↓ 输出 raw / staging / fetch_log
DataQualityValidator
        ↓
SourceConflictValidator
        ↓
WriteManager
        ↓
DuckDB clean / snapshot
```

数据源模块的任何变化，都需要同步：

```text
source_registry.yaml
source_capabilities.yaml
source_capability_contract.yaml
source_route_contract.yaml
source_route_plan.md
data_adapter_contract.md
data_sync_orchestrator.md
data_validation_and_conflict.md
```

## 用户决策补充：QMT 默认禁用

落实 D-11：第一版 `qmt_xtdata` 默认禁用。只有用户确认本机 QMT/miniQMT 环境、账号授权、路径配置后，才允许启用 QMT adapter。实现角色不得默认连接本机交易/行情终端。

## 数据源默认启用与 domain gating

`specs/datasource_registry/source_registry.yaml` 是数据源启用状态的机器契约。若某个 domain 的 primary source `enabled_by_default=false`，该 domain 第一版必须标记为 `domain_enabled_by_default=false` 与 `disabled_until_configured=true`，调度器不得尝试抓取，而应返回或记录 `DISABLED_SOURCE`。

D-11 已拍板：QMT 默认禁用，只有用户确认本机授权与账号环境后才可启用。因此 `cn_equity_minute_bar` 默认不可调度；`cn_equity_daily_bar` 可以用 baostock 作为 primary，但 QMT fallback 必须在用户启用后才允许接管。Yahoo 也默认禁用，`us_equity_daily_bar` 第一版应标记为 disabled until configured。

必须补测试：`test_disabledPrimaryDomain_returnsDisabledSource`、`test_fallbackDisabledByDefault_isSkippedUntilConfigured`。

## 旧角色名强约束

`Shadow`、`Emergency`、`shadow_source`、`emergency_source` 是旧**数据源角色**口径，不得恢复为运行时 source role。禁止范围限定为数据源角色语义，而不是禁止所有文本或诊断标签字面量。

禁止进入或恢复的位置：

```text
source_registry 的 source_role / default_role / domain role
API response 中表示数据源角色的字段
数据库列名或枚举值中的数据源角色
前端展示字段中的数据源角色
Python 代码、测试期望中的数据源角色枚举
运行时 YAML 配置中的数据源角色字段
```

允许的窄例外：

```text
specs/datasource_registry/source_registry.yaml 的 legacy_roles_forbidden 禁用清单
Layer 1 indicator specs 中明确带诊断/旁证语义的 *.SHADOW.* indicator 条目
Layer 1 indicator specs 中 shadow_diagnostics 下的 *.SHADOW.* 诊断指标命名
Layer 1 indicator specs / common rules 的 schema_note 或说明文字
历史迁移说明文档
```

Layer 1 的 `SHADOW` 只能表示“诊断/旁证信号”，不得表示数据源角色。所有 `*.SHADOW.*` 诊断指标必须满足：

```text
允许用于明确带诊断/旁证语义的 Layer 1 indicator 条目、shadow_diagnostics 分组、schema_note 或说明文字
不得作为 source role、default role、fallback role、API role、DB role、frontend source-role 或 source_registry role
不得进入 clean 主值接管路径
必须具备 no_main_score_input / no_takeover / validation_only 等约束语义
若不在 shadow_diagnostics 分组下，必须显式写明 diagnostic_only / evidence_only / does_not_replace_main_indicator 或同等约束
必须保留 source_used、quality_flags 或 audit 线索，以便解释而非接管
```

实现角色发现旧数据源角色名被恢复为运行时配置、代码或测试中的 source role 时，必须视为 P0 级口径回退并停止执行。

---

## Round2.6 补充：Capability / Route / Service 三层边界

Round2.6 不删除本文件既有 source_registry 与 adapter 设计，而是在其上增加三层明确边界：

1. `SourceCapabilityRegistry`：声明 source/domain/operation/field/frequency/auth 能力，权威文件为 `specs/datasource_registry/source_capabilities.yaml` 与 `specs/contracts/source_capability_contract.yaml`。
2. `SourceRoutePlan`：fetch 前必须解释候选源、禁用源、跳过原因、fallback 标记，权威契约为 `specs/contracts/source_route_contract.yaml`。
3. `DataSourceService`：生产路径唯一 fetch facade，避免 Orchestrator/API/Agent 直接触碰 adapter factory，权威契约为 `specs/contracts/datasource_service_contract.yaml`。

当前实现已具备 `SourceCapabilityRegistry`、`SourceRoutePlan` 与 `DataSourceService` facade，并保留 adapter skeleton、vendor fixture E2E、backfill validate/write、reconcile 相关证据。后续真实源扩展不得再从零自建重复 provider/health/backtest 轮子；应优先从已下载到 `参考项目/` 的成熟项目中做有边界的源码阅读、架构借鉴或 QMD-owned 改造，并通过 license gate、source registry、capability registry、route plan、ResourceGuard、ValidationGate、WriteManager 与 fetch/evidence lineage 约束落地。

`参考项目/EasyXT` 可作为数据完整性检查、TDX/pytdx provider 连接管理、A 股量化工具结构的直接改造参考，但不得引入其交易/自动登录/默认全市场下载语义。`参考项目/JQ2PTrade` 可作为只读 backtest/review 数据加载、报告形态、API deny-list 的改造参考，但不得引入 order/trade/portfolio execution API。`参考项目/OpenBB` 仅作为 provider/package/catalog 架构参考，不得复制 AGPL runtime source。`参考项目/agents-for-openbb` 仅供未来 Agent/UI artifact 形态参考，不得替代 QMD evidence source 或触发写入。

qmt_xqshare 仅作为 P2 可选远程 QMT 源设计，默认禁用；不得自动探测、自动登录或 silent fallback。

必须补测试：`test_legacySourceRoles_forbiddenAsSourceRoles`、`test_layer1ShadowDiagnostics_areExplicitlyAllowedButNoTakeover`、`test_shadowDiagnosticLabels_doNotEnterSourceRegistryRoles`、`test_shadowDiagnosticsOutsideGroup_requireExplicitDiagnosticOnly`。
