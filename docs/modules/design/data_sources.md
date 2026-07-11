# 数据源注册与优先级模块

> 拆分说明：本文件由 `quant_monitor_design_document_v1_6.md` 拆分生成；当前步骤只做结构拆分与明显版本/编号残留修正，不删减原有细节。
> 来源：第 4 章

# 4. 数据源注册与优先级

## 4.1 数据源分层

| 数据源                | 推荐角色                     | 产品定位                       |
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
    is_enabled          BOOLEAN, -- 基础启用状态；运行时有效状态须与 activation overlay 合成
    default_priority    INTEGER,
    notes               TEXT
);
```

## 4.3 数据源冲突原则

1. 原始数据永远不删。
2. 可信最终库对同一事实位置只保存一个默认可信版本；降级/质量异常活动版本进入独立连续监控区。
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

| 情况             | 处理                                                               |
| ---------------- | ------------------------------------------------------------------ |
| 差异在容忍范围内 | 质量通过的主源值进入可信最终库，备用源记录为校验通过               |
| 差异略超容忍范围 | 质量通过的主源值进入可信最终库，但记录 `source_divergence_warning` |
| 差异严重         | 不写可信最终库，写入 `source_conflict`，触发 ReconcileJob 重抓     |
| 重抓后仍严重冲突 | 标记 `manual_review_required=true`，等待人工确认                   |

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
    is_enabled             BOOLEAN, -- 基础启用状态；不是唯一运行时开关
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

### 5.2.1 有效启用覆盖层

稳定 `source_registry` 不记录临时运营开关。运行时只可使用基础状态与下表合成后的有效启用结果：

```sql
CREATE TABLE IF NOT EXISTS source_activation_overlay (
    overlay_id          VARCHAR PRIMARY KEY,
    source_id           VARCHAR NOT NULL,
    data_domain         VARCHAR NOT NULL,
    operation           VARCHAR NOT NULL,
    enabled             BOOLEAN NOT NULL,
    reason              TEXT NOT NULL,
    changed_by          VARCHAR NOT NULL,
    changed_at          TIMESTAMP NOT NULL,
    revision            VARCHAR NOT NULL,
    revoked_at          TIMESTAMP,
    revoked_by          VARCHAR,
    revoke_reason       TEXT
);
```

有效启用 = 基础 `is_enabled`、最新未撤销 overlay、license/auth、platform matrix、capability 与
ResourceGuard 均允许。任何一项不满足即失败关闭；任务、CLI 和调度器只能读取这个结果，不能在
内存中改写 registry 或 platform 判定。

**接缝分层（ADR-018）：** overlay「开关本」层只回答管理员是否允许（输出含 `overlay_revision`）；
RoutePlanner「安检」层再做执照/平台/能力/护栏。测试仅在隔离根写入正规 overlay，禁止内存撬门；
FRED 编排壳与启用撬门分离，合并关账见 ADR-018。

---

## 5.3 Primary / Validation / FallbackPolicy

新版统一使用三角色，不再使用旧的 旧三源命名。

| 新角色           | 含义                                                   | 历史说明                                                                                                                                       |
| ---------------- | ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `Primary`        | 质量通过时进入可信最终库的主源                         | 旧文档中的 Primary 仅作为历史迁移参考                                                                                                          |
| `Validation`     | 用于校验主源；仅经领域 FallbackPolicy 授权时可降级兜底 | 旧数据源角色名 `Shadow` 不得作为 source role / default role / fallback role；Layer 1 `SHADOW` 诊断标签不是数据源角色，见本页“旧角色名强约束”。 |
| `FallbackPolicy` | 不是第三外部源，而是失败时如何处理                     | 旧数据源角色名 `Emergency` 不得作为 source role / default role / fallback role。                                                               |

FallbackPolicy 可以是：

```text
retry_same_source
use_validation_source_with_flag
use_last_good_cache
mark_missing
manual_review_required
skip_until_next_publish
```

### 5.3.1 Validation-as-Fallback 降级连续监控规则

`Validation` 源不能进入可信最终库，也不能无标记、无策略、无审计地伪装成 Primary。最终成品仅允许在严格条件下使用验证源作为降级连续监控数据，且必须由 domain 级 `FallbackPolicy` 明确授权。

允许进入连续监控区的降级场景：

```text
1. 当前 domain 的 FallbackPolicy 明确为 use_validation_source_with_flag。
2. Primary 已失败或不可用，且失败原因已记录：auth failed / rate limit / schema drift / empty response / not published / network failure 等。
3. 被选中的 Validation 源支持该 data_domain，且通过 capability、license/auth、ResourceGuard 和 DataQualityValidator。
4. SourceConflictValidator 未发现 severe conflict；若存在 severe conflict，必须 `manual_review_required=true`，且只有归一化值和血缘完整时才可进入连续监控区。
5. 写入必须保留 raw、fetch_log、validation_report、write_audit_log 和 route-plan 证据。
```

降级连续监控写入必须带以下语义，不得缺省：

```text
source_used = 实际使用的源
selected_role = FallbackPolicy
source_switched = true
quality_flags 包含 SOURCE_FALLBACK_USED
若来源是 Validation 源，还必须包含 VALIDATION_SOURCE_USED
stale_reason 或 fallback_reason = 主源失败或缓存使用原因
primary_source_failed = true（可在 route/audit payload 中表达）
```

下游读取规则：

```text
1. 读模型、Layer、前端和 Agent 必须能区分可信最终库与连续监控区，并识别来源等级和质量等级。
2. 连续监控数据可以展示、计算、告警或进入人工审查，但不能静默参与等同可信 Primary 的解释。
3. 若某个指标/模型声明只接受主源可信输入，遇到非 `PRIMARY + QUALITY_PASSED` 数据必须 fail-closed 或返回诚实 NULL。
4. Validation 源若未被 FallbackPolicy 授权，只能用于 validation/source_conflict/manual_review/evidence，不得写可信最终库或连续监控区。
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

| 场景              | 处理                                                                                 |
| ----------------- | ------------------------------------------------------------------------------------ |
| 网络超时          | 指数退避重试，最多 3 次                                                              |
| 429 / rate limit  | 按 source policy 暂停，不换源伪装成功                                                |
| 403 / auth failed | 标记 AUTH_FAILED，停止该源任务                                                       |
| 空数据            | 标记 EMPTY_RESPONSE，进入质量检查                                                    |
| schema drift      | 标记 SCHEMA_DRIFT，不写可信最终库；合格次源可按 RoutePlan 进入连续监控并创建修复事件 |
| 数据尚未发布      | 标记 NOT_PUBLISHED_YET，可等待下次调度                                               |
| 接口字段变更      | 写 schema_hash 变化，触发人工或适配器更新                                            |

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

## 5.9 数据源产品定位

| 数据源                | 产品角色                     | 注意事项                                    |
| --------------------- | ---------------------------- | ------------------------------------------- |
| QMT / xtdata          | A 股实时、分钟线、本地授权源 | 需要本地客户端和授权，作为核心源但仍需校验  |
| baostock              | A 股历史日线、基础财务       | 适合历史补齐，不适合实时                    |
| AkShare               | 快速补充、板块、指数、资金流 | 口径变化需严格 schema drift 检测            |
| 巨潮 CNINFO           | 公告、财报 PDF               | 公告原文权威源，文件入 File Lake            |
| 东方财富              | 资金流、板块、公告备份       | 资金流口径独立保存，不强行合并              |
| Yahoo / yfinance      | 美股、ETF、全球资产辅助      | 研究/辅助，不做关键生产唯一源               |
| 同花顺 / iFinD        | 题材、概念、研报             | 正式使用必须确认授权                        |
| FRED / Cboe / CFTC 等 | 五轴和全球指标               | 进入 Layer 1 / Layer 2 专用 source registry |

---

### 5.9.1 总数据源扩展清单与定位

`specs/datasource_registry/source_registry.yaml` 是机器可读权威；本表是面向设计、实现和审核的解释口径。新增外部源默认 `enabled_by_default=false`，只有完成 adapter、capability、route plan、ResourceGuard、license/auth gate 和回放证据后才能启用。

| 数据源                   | 数据类型                                    | 推荐定位                                                                        | 用途                                      | 可靠性/稳定性/实时性判断                                                           |
| ------------------------ | ------------------------------------------- | ------------------------------------------------------------------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------- |
| QMT / xtdata             | A 股实时、分钟线、日线                      | A 股实时 Primary（用户本机授权后）                                              | 实时行情、分钟线、交易日内监控            | 授权终端可靠性高、实时性强；默认禁用，需用户确认本机授权                           |
| baostock                 | A 股历史日线、基础财务                      | A 股低频 Primary                                                                | 历史日线补齐、基础财务                    | 免费稳定，适合日频/低频；不适合实时                                                |
| AkShare                  | A 股/宏观聚合数据                           | Validation                                                                      | 指数、板块、宏观补充、快速验证            | 覆盖广但上游口径可能变化；必须 schema_hash 与 quality_flags                        |
| 巨潮 CNINFO              | 公告、财报、PDF 原文                        | A 股披露 Primary                                                                | 公告索引、财报 PDF、文件证据链            | 官方/准官方披露源，权威性高；需 polite fetch 与文件哈希                            |
| Yahoo Finance / yfinance | 美股、ETF、期权链、全球资产参考             | Validation                                                                      | 美股/ETF/US option chain 辅助校验         | 覆盖方便但条款和稳定性敏感；不做生产唯一主源                                       |
| Alpha Vantage            | 美股、ETF、期权链、FX、商品、宏观、加密参考 | API-key gated Primary candidate                                                 | 文档化 API 补充美国市场与跨资产数据       | 稳定性好于网页源；受 API key、限流和授权条款约束                                   |
| Stooq                    | 股票/ETF/外汇/商品历史行情                  | Validation；仅在 domain FallbackPolicy 明确授权时可 degraded fallback           | 全球历史价格趋势、低频交叉验证            | 适合日频历史，不适合实时生产；不得无标记接管主值                                   |
| Deribit                  | 加密期货、期权、IV、term structure          | Crypto derivatives Primary candidate                                            | BTC/ETH 期货曲线、期权 IV surface         | 交易所级市场数据，实时性强；只允许 market-data，禁止账户/交易能力                  |
| CoinGecko                | 加密现货聚合、币种映射、市值                | Spot/reference Primary candidate + Validation                                   | BTC/ETH 现货参考价、市值、asset reference | 聚合源覆盖广；不能替代交易所逐笔/盘口事实源                                        |
| US Treasury              | 国债收益率、利率曲线、通胀预期参考          | Official Primary                                                                | 利率曲线、期限利差、通胀预期上下文        | 官方源，可靠性最高；日频/低频，适合 Layer 1 regime                                 |
| SEC EDGAR                | 公司披露、Form 4 内部人交易                 | Official Primary                                                                | 美国 filings、Form 4 买卖信号、原文证据   | 官方披露源，准确性高；必须保存 accession/content_hash                              |
| CFTC COT                 | 期货持仓                                    | Official Primary                                                                | 机构/非商业仓位方向、smart-money 背景     | 官方周频，稳定但滞后；不得当实时仓位                                               |
| BIS                      | 央行、政策利率、信贷缺口                    | Official Primary                                                                | 全球政策利率、credit/GDP gap、宏观 regime | 官方/央行协作数据，低频稳健                                                        |
| World Bank               | GDP、人口、贸易、发展指标                   | Official Primary                                                                | 长周期宏观背景变量                        | 官方低频数据，可靠但滞后，不做短线触发                                             |
| FRED                     | 美国宏观序列                                | API-key gated Primary candidate                                                 | Layer 1 宏观序列、官方/准官方美国宏观     | 已有 sandbox_candidate；需 key 与 live gate                                        |
| Kalshi                   | 监管预测市场合约                            | Prediction probability Primary candidate                                        | 美国政治/经济事件概率、二元合约价格       | 受监管事件市场，适合概率信号；不是事实结果源                                       |
| Polymarket               | 预测市场合约                                | Prediction probability Validation                                               | 全球事件概率、市场情绪、流动性观察        | 流动性和 resolution 质量差异大；必须记录 volume/liquidity/spread/resolution_source |
| mootdx / TDX compatible  | A 股 security list、日线、指数              | Validation                                                                      | 通达信兼容校验、A 股代码表探针            | 默认禁用；只读校验，不得 silent fallback                                           |
| 东方财富                 | A 股行情、板块、资金流、公告备份            | Validation                                                                      | 资金流、板块、公告备份和日线交叉验证      | 覆盖强但网页/API 口径可能变；资金流必须分源保存                                    |
| 新浪财经                 | A 股行情轻量备份                            | Validation；仅在 domain FallbackPolicy 明确授权时可作为 `DEGRADED` 连续监控候选 | 实时/日线轻量校验、故障诊断               | 稳定性和授权边界弱于主源；不得无标记接管主值                                       |
| 同花顺 / iFinD           | 概念、题材、研报、资金流                    | Licensed Validation                                                             | 题材、概念、研报索引、授权数据补充        | 仅商业授权后启用；免费网页端不得生产化                                             |
| Web Search               | 网页补充证据                                | Manual-review Validation only                                                   | VIX、CDS、事件解释、resolution 佐证       | 非结构化且不稳定；只能进 evidence/manual_review，不直接写 clean 表                 |

### 5.9.2 四点关键实现建议

1. **按 domain-level role 分配，不按 provider 平铺。** 新增 source 必须同时写入 `source_registry.yaml`、`source_capabilities.yaml` 和 route plan 规则；同一个 provider 在不同 domain 可以是 Primary、Validation 或 fallback candidate。示例：Alpha Vantage 可作为 `us_equity_daily_bar` 的 API-key gated Primary candidate，但在 `macro_series` 中只能作为 FRED/官方源的补充候选。
2. **预测市场单独建概率信号语义。** `kalshi`、`polymarket` 只能写入 `prediction_market_probability`、`regulated_event_contract`、`event_market_contract` 等概率/合约域；必须保存 `liquidity`、`volume`、`spread`、`resolution_source`、`closed/active` 状态。其价格不得被解释为事实结果，也不得替代 SEC/CFTC/Treasury/CNINFO 等事实源。
3. **官方宏观源按低频/滞后处理。** US Treasury、CFTC COT、BIS、World Bank、FRED 等应进入 Layer 1/Layer 2 regime 和背景变量，不得驱动分钟级 UI 或实时告警；允许 `use_last_good_cache`，但必须写 `stale_reason`、`source_fetch_id`、`content_hash`。
4. **中国市场继续保持授权终端/官方披露优先。** QMT 授权后才可作为实时主源；CNINFO 是公告/财报原文主源；baostock 是历史日线/基础财务主源；AkShare、东方财富、Sina、mootdx、同花顺免费端只能做验证、补充或经 domain FallbackPolicy 明确授权后的 degraded fallback，并强制 schema drift、限速、缓存和 no-silent-fallback。

---

## 5.10 验收测试

| 测试                                           | 预期                                                                                                                                   |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| 未声明 data_domain 的 adapter 被调用           | 拒绝                                                                                                                                   |
| source disabled                                | 不执行抓取                                                                                                                             |
| 403 auth failed                                | 写 fetch_log，停止该源任务                                                                                                             |
| schema_hash 变化                               | 标记 SCHEMA_DRIFT，不直接写可信最终库；合格次源可经 RoutePlan 维持连续监控并创建修复事件                                               |
| 主源失败且 fallback_policy=mark_missing        | 不接管，写缺失                                                                                                                         |
| 使用 last_good_cache                           | 必须写 stale_reason 和 source_switched                                                                                                 |
| Validation 源数据不同                          | 进入 SourceConflictValidator，不在 Adapter 内判断                                                                                      |
| FallbackPolicy=use_validation_source_with_flag | 允许进入连续监控区，但必须 `source_grade=DEGRADED`、`selected_role=FallbackPolicy`、`source_switched=true`，并含来源/质量/人工复核语义 |
| Validation 源无 FallbackPolicy 授权            | 不得写可信最终库或连续监控区，只能进入 validation/source_conflict/manual_review/evidence                                               |

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
DuckDB 可信最终库 / 连续监控视图 / snapshot
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

## ADR-017：动态启用、自动降级与数据去向（最终口径）

本节的字段、写入目标和留存约束以
`specs/contracts/design/source_provenance_quality_contract.yaml` 为唯一机器契约。

1. `source_registry` 是稳定能力目录；基础启用状态不因任务或一次故障被改写。另设管理员通过受控配置/CLI 维护的持久化启用覆盖层，记录操作者、原因、版本和撤销；覆盖层不能绕过 license、auth、ResourceGuard 或 capability。
2. 每个领域 RoutePlan 必须声明固定次源优先级。所有 Primary 失败都可按顺序尝试已登记、审核、有效启用且能力匹配的 Validation 候选；候选永远以 `FallbackPolicy` 被选中、`DEGRADED` 被记录，绝不升格为 Primary。
3. 每次选择必须保留 `source_used`、主源失败原因、RoutePlan、覆盖层/注册版本和来源/质量独立标签。代码、适配器、格式或 schema 失败还必须创建高优先级修复事件。
4. `PRIMARY + QUALITY_PASSED` 才能写可信最终库。可归一化且血缘完整的降级或质量异常结果只能写连续监控区；不可解析、无有效数值或无完整血缘的结果必须为 `MISSING`。
5. QMT、Yahoo 及其他默认关闭源仍保持失败关闭；管理员覆盖层只能在既有授权和环境前置条件满足后激活，绝不 mass-enable。

---
