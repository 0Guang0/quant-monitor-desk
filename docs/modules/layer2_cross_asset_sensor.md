# Layer 2 跨资产传感器模块

> 文件定位：实现级模块设计。Layer 2 记录市场已经交易出来的跨资产价格、成交量、持仓与方向变化，是连接底层状态与产业链/市场结构的“传感器层”。  
> 重要边界：Layer 2 不替代 Layer 1，不生成完整五轴标准化字段，不把慢变量回写 Layer 1，不输出交易动作。

---

# 1. 模块目标

Layer 2 用来观察跨资产市场是否正在验证或反驳 Layer 1 的底层状态。

它回答：

```text
美元、黄金、原油、铜、美债、信用 ETF、波动率、航运等市场价格是否出现异常？
这些异常是否支持 Layer 1 的底层状态判断？
是否有跨资产背离，需要进入 Agent 日报或人工复核？
```

Layer 2 不回答：

```text
宏观状态本身是什么？
哪个行业必然受益？
是否应该交易某个资产？
```

---

# 2. 资产范围

第一版建议覆盖：

| asset_group | 示例 | 用途 |
|---|---|---|
| USD | DXY / 美元指数代理 | 观察美元流动性与风险偏好。 |
| Rates | DGS10、DGS2、T10Y3M、TLT、IEF | 观察利率、期限结构与债券市场。 |
| Metals | Gold、Silver、Copper | 观察避险、工业需求和电力/AI 约束。 |
| Energy | WTI、Brent、Natural Gas | 观察能源价格和通胀/成本约束。 |
| Credit ETF | HYG、LQD | 观察信用风险市场价格。 |
| Equity ETF | SPY、QQQ、IWM、RSP | 观察权益市场广度与风格。 |
| Volatility | VIX、VVIX、VIX futures | 观察期权保险费和风险定价。 |
| Shipping | BDI、SCFI、油运/干散货代理 | 观察全球贸易和运输成本。 |
| Futures | 铜、原油、天然气、黄金、股指期货 | 观察期货主力和期限结构。 |

---

# 3. 与其他层的关系

| 层 | 关系 |
|---|---|
| Layer 1 | Layer 2 可以作为旁证，但不能回写 Layer 1。 |
| Layer 3 | 铜、能源、BDI 等既可作为 Layer 2 资产，也可被 Layer 3 引用为价格锚；数据仍由 Layer 5/Layer 2 提供。 |
| Layer 4 | 不同市场结构页可引用 Layer 2 资产快照。 |
| Layer 5 | 具体 ETF、期货、指数、商品合约的行情明细在 Layer 5 保存。 |

---

# 4. 核心表结构

## 4.1 `cross_asset_registry`

```sql
CREATE TABLE IF NOT EXISTS cross_asset_registry (
    asset_id              VARCHAR PRIMARY KEY,
    display_name          VARCHAR,
    display_name_cn       VARCHAR,
    asset_group           VARCHAR,
    asset_type            VARCHAR,
    market                VARCHAR,
    instrument_id         VARCHAR,
    layer5_instrument_id  VARCHAR,
    primary_source        VARCHAR,
    validation_source     VARCHAR,
    fallback_policy       VARCHAR,
    mapped_axis           VARCHAR,
    is_axis_input         BOOLEAN,
    display_only          BOOLEAN,
    eligible_for_model    BOOLEAN,
    double_count_guard    VARCHAR,
    updated_at            TIMESTAMP
);
```

## 4.2 `cross_asset_observation`

```sql
CREATE TABLE IF NOT EXISTS cross_asset_observation (
    asset_id            VARCHAR,
    trade_time          TIMESTAMP,
    market              VARCHAR,
    asset_type          VARCHAR,
    open                DOUBLE,
    high                DOUBLE,
    low                 DOUBLE,
    close               DOUBLE,
    pre_close           DOUBLE,
    volume              DOUBLE,
    amount              DOUBLE,
    open_interest       DOUBLE,
    source              VARCHAR,
    as_of_timestamp     TIMESTAMP,
    fetch_time          TIMESTAMP,
    quality_flag        VARCHAR,
    PRIMARY KEY (asset_id, trade_time, source)
);
```

## 4.3 `cross_asset_daily_snapshot`

```sql
CREATE TABLE IF NOT EXISTS cross_asset_daily_snapshot (
    snapshot_id          VARCHAR PRIMARY KEY,
    asset_id             VARCHAR,
    trade_date           DATE,
    close                DOUBLE,
    pct_change           DOUBLE,
    volume               DOUBLE,
    amount               DOUBLE,
    open_interest        DOUBLE,
    level_label          VARCHAR,
    change_label         VARCHAR,
    quality_flags        VARCHAR,
    source_used          VARCHAR,
    as_of_timestamp      TIMESTAMP,
    created_at           TIMESTAMP
);
```

## 4.4 `cross_asset_signal_snapshot`

本表只保存轻量状态，不保存 Layer 1 完整标准化套件。

```sql
CREATE TABLE IF NOT EXISTS cross_asset_signal_snapshot (
    signal_id            VARCHAR PRIMARY KEY,
    asset_id             VARCHAR,
    trade_date           DATE,
    signal_type          VARCHAR,
    signal_value         DOUBLE,
    signal_label         VARCHAR,
    lookback_window      VARCHAR,
    quality_flags        VARCHAR,
    created_at           TIMESTAMP
);
```

---

# 5. 防双算规则

Layer 2 中某些资产也是 Layer 1 的输入，例如 VIX、HYG、TLT、美债利率、信用 ETF 等。必须在 `cross_asset_registry` 标注：

```text
mapped_axis
is_axis_input
display_only
eligible_for_model
double_count_guard
```

规则：

| 情况 | 处理 |
|---|---|
| 资产已是 Layer 1 指标直接输入 | `is_axis_input=true`，默认 `display_only=true`。 |
| 资产只是 Layer 1 旁证 | 可展示，可用于 Agent 解释，但不参与 Layer 1 计算。 |
| 资产同时被 Layer 3 引用 | 不重复抓取，由统一 instrument_id 映射。 |
| 资产缺少稳定数据源 | 标 `quality_flags=NO_ACCEPTED_CHANNEL`。 |

---

# 6. 期货与主力合约规则

期货资产必须区分：

```text
continuous_contract
front_month
main_contract
specific_contract
```

保存字段：

```text
contract_code
contract_month
roll_rule
roll_date
open_interest
volume
settlement_price
```

主力合约切换不得 silent switch，必须写：

```text
roll_event=true
old_contract
new_contract
roll_reason
roll_date
```

---

# 7. 更新流程

```text
1. 读取 cross_asset_registry
2. 根据 asset_group 分批抓取
3. 写入 staging_cross_asset_observation
4. 执行 DataQualityValidator
5. 对关键资产执行 SourceConflictValidator
6. WriteManager 写入 cross_asset_observation
7. 生成 cross_asset_daily_snapshot
8. 生成轻量 cross_asset_signal_snapshot
9. 提供 FastAPI 与 Agent 查询
```

---

# 8. 异动检测

Layer 2 第一版使用轻量规则，不做复杂模型：

```text
1D pct_change
5D pct_change
20D pct_change
volume_spike
open_interest_spike
new_high_new_low
cross_asset_divergence
```

示例：

| signal_type | 说明 |
|---|---|
| `PRICE_MOVE_1D` | 单日价格显著变化。 |
| `PRICE_MOVE_5D` | 5 日趋势显著变化。 |
| `VOLUME_SPIKE` | 成交量放大。 |
| `OI_SPIKE` | 期货/期权持仓变化。 |
| `DIVERGENCE_WITH_LAYER1` | 与 Layer 1 状态出现背离。 |
| `DIVERGENCE_WITH_LAYER3` | 与产业链锚点走势背离。 |

---

# 9. API 契约

| API | 用途 |
|---|---|
| `GET /api/layer2/assets` | 获取跨资产清单。 |
| `GET /api/layer2/sensors` | 获取最新跨资产传感器快照。 |
| `GET /api/layer2/asset/{asset_id}` | 获取单个资产历史与状态。 |
| `GET /api/layer2/divergence` | 获取跨资产背离清单。 |
| `GET /api/layer2/quality` | 获取 Layer 2 数据质量。 |

响应必须包含：

```text
asset_id
display_name_cn
asset_group
latest_value
pct_change
quality_flags
source_used
as_of_timestamp
is_axis_input
double_count_guard
```

---

# 10. CLI 契约

```bash
python -m quant_monitor layer2 load-registry
python -m quant_monitor layer2 sync --group metals
python -m quant_monitor layer2 build-snapshot --date 2026-06-14
python -m quant_monitor layer2 detect-divergence --date 2026-06-14
python -m quant_monitor layer2 health-check
```

---

# 11. 测试清单

| 测试 | 预期 |
|---|---|
| VIX 同时出现在 Layer 1 和 Layer 2 | Layer 2 标 `is_axis_input=true`，不参与 Layer 1 重算。 |
| 期货主力切换 | 写 roll_event，不 silent switch。 |
| 商品价格缺源 | 输出 `NO_ACCEPTED_CHANNEL`。 |
| Layer 3 引用铜价 | 通过 instrument_id 映射，不重复抓取。 |
| 前端请求大历史 | API 强制分页和日期窗口。 |

---

# 12. 实现任务拆分

```text
1. 实现 cross_asset_registry loader
2. 实现 CrossAssetFetcher
3. 实现 futures roll handler
4. 实现 CrossAssetSnapshotBuilder
5. 实现 divergence detector
6. 实现 Layer 2 API
7. 实现 Layer 2 前端卡片数据契约
8. 实现测试集
```
