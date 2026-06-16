# Layer 1 全球底层状态面板模块

> 文件定位：实现级模块设计。本文保留 v1.6 原有 Layer 1 设计，并补充可直接交给 Claude Code / Codex 实现的加载流程、表结构边界、计算流程、接口契约、错误处理与测试清单。  
> 权威输入：`specs/layer1_axes/restructured_axes_v1_1/` 下五轴用户说明、指标 YAML 与工程规则。  
> 不做事项：本模块不输出交易动作，不生成买卖建议，不把 Layer 2 慢变量回写 Layer 1，不伪造 BlindSpot。

---

# 1. 模块目标

Layer 1 统一采用 Primary / Validation / FallbackPolicy 数据源角色。

Layer 1 是系统的“全球底层状态面板”，负责把环境、信用压力、风险偏好、流动性、情绪五条轴转换为可审计、可解释、可前端展示的状态向量。

它回答的问题是：

```text
当前全球金融环境的底层状态是什么？
哪些状态是数据真实观测出来的？
哪些状态因为数据缺失、延迟、历史不足而不能解释？
这些状态能说明什么，不能说明什么？
```

Layer 1 不回答：

```text
应该买什么？
应该卖什么？
应该加仓还是减仓？
某个行业或股票必然会上涨吗？
```

---

# 2. 五轴清单

| axis_id | 中文名 | 作用 |
|---|---|---|
| `ENVIRONMENT` | 环境轴 | 观察宏观流动性、利率、财政/央行资产负债表、经济环境等底层背景。 |
| `CREDIT_STRESS` | 信用压力轴 | 观察企业信用、短端融资、系统性融资摩擦。 |
| `RISK_APPETITE` | 风险偏好轴 | 观察期权保险费、股债风险共振、风险资产偏好。 |
| `LIQUIDITY` | 流动性轴 | 观察微观交易摩擦、价差、冲击成本与可交易性。 |
| `SENTIMENT` | 情绪轴 | 观察仓位、调查、期权倾斜、融资杠杆等行为/情绪变量。 |

五轴的指标选择、金融语义、数据源地址、公式、禁止项、BlindSpot 和解释边界全部外置，不在本模块硬编码。

权威路径：

```text
specs/layer1_axes/restructured_axes_v1_1/common/common_axis_rules.md
specs/layer1_axes/restructured_axes_v1_1/environment_axis/environment_axis_indicator_spec.yaml
specs/layer1_axes/restructured_axes_v1_1/credit_stress_axis/credit_stress_axis_indicator_spec.yaml
specs/layer1_axes/restructured_axes_v1_1/risk_appetite_axis/risk_appetite_axis_indicator_spec.yaml
specs/layer1_axes/restructured_axes_v1_1/liquidity_axis/liquidity_axis_indicator_spec.yaml
specs/layer1_axes/restructured_axes_v1_1/sentiment_axis/sentiment_axis_indicator_spec.yaml
```

---

# 3. 与其他模块的关系

| 依赖模块 | 关系 |
|---|---|
| `data_sources.md` | Layer 1 指标从注册数据源读取。 |
| `data_sync_orchestrator.md` | 由 `sync_layer1_axes` 或 `Layer1AxisUpdateJob` 调度。 |
| `data_validation_and_conflict.md` | 每条观测写入前必须通过质量检查；多源口径冲突时进入冲突处理。 |
| `write_manager.md` | Layer 1 表只允许通过 WriteManager 写入。 |
| `layer2_cross_asset_sensor.md` | Layer 2 可展示与 Layer 1 相关的市场价格，但不得回写 Layer 1。 |
| `agent_module.md` | Agent 只能基于结构化事实和解释模板生成自然语言，不直接判定状态。 |
| `frontend_dashboard.md` | 前端展示五轴状态、指标解释、质量状态与边界提醒。 |

---

# 4. 核心数据流

```text
Layer1 axis spec YAML
        ↓
AxisSpecLoader
        ↓
axis_registry / axis_indicator_registry / axis_indicator_profile 初始化
        ↓
DataSyncOrchestrator 调度指标抓取
        ↓
primary_source 抓取 + validation_source 校验 + fallback_policy 记录
        ↓
axis_observation 写入 staging
        ↓
DataQualityValidator / SourceConflictValidator
        ↓
DuckDBWriteManager 写入 clean table
        ↓
AxisFeatureEngine 计算 z_score / robust_z_score / percentile / delta / state_bucket
        ↓
axis_feature_snapshot
        ↓
AxisInterpretationEngine + 受控 Agent
        ↓
axis_interpretation_snapshot
        ↓
FastAPI / 前端五轴卡片 / Agent 日报
```

---

# 5. Spec Loader 设计

## 5.1 输入文件

每条轴至少有三类文件：

```text
axis_user_guide.md              给用户和前端解释的通俗说明
axis_indicator_spec.yaml        给程序读取的指标配置
axis_engineering_rules.md       给实现和运维读取的工程约束
```

## 5.2 Loader 输出

`AxisSpecLoader` 应输出 4 类对象：

| 对象 | 用途 |
|---|---|
| `AxisDefinition` | 初始化 `axis_registry`。 |
| `AxisIndicatorDefinition` | 初始化 `axis_indicator_registry`。 |
| `AxisIndicatorProfile` | 初始化 `axis_indicator_profile`。 |
| `AxisEngineeringGuardrail` | 初始化规则检查器与解释护栏。 |

## 5.3 必填字段

每个可观测指标必须具备：

```text
indicator_id
axis_id
display_name_cn
plain_language_summary
layer
module
frequency
unit
primary_source
validation_source
fallback_policy
formula 或 raw_input
allow_score
diagnostic_only
quality_rules
stale_rules
forbidden_substitutes
```

Shadow / BlindSpot / Forbidden 指标也必须有最小解释字段，避免前端或 Agent 出现“有 ID 无解释”。

---

# 6. 表结构

## 6.1 `axis_registry`

```sql
CREATE TABLE IF NOT EXISTS axis_registry (
    axis_id         VARCHAR PRIMARY KEY,
    axis_name       VARCHAR,
    axis_name_cn    VARCHAR,
    description     TEXT,
    spec_path       VARCHAR,
    updated_at      TIMESTAMP
);
```

## 6.2 `axis_indicator_registry`

```sql
CREATE TABLE IF NOT EXISTS axis_indicator_registry (
    indicator_id        VARCHAR PRIMARY KEY,
    axis_id             VARCHAR,
    indicator_name      VARCHAR,
    display_name_cn     VARCHAR,
    dest_tag            VARCHAR,
    layer_tag           VARCHAR,
    exec_tier           VARCHAR,
    frequency           VARCHAR,
    unit                VARCHAR,
    directionality      VARCHAR,
    primary_source      VARCHAR,
    validation_source   VARCHAR,
    fallback_policy     VARCHAR,
    formula             TEXT,
    allow_score         BOOLEAN,
    diagnostic_only     BOOLEAN,
    is_blindspot        BOOLEAN,
    is_forbidden        BOOLEAN,
    spec_path           VARCHAR,
    is_enabled          BOOLEAN,
    updated_at          TIMESTAMP
);
```

## 6.3 `axis_observation`

保存未经标准化的原始观测值。

```sql
CREATE TABLE IF NOT EXISTS axis_observation (
    observation_id      VARCHAR PRIMARY KEY,
    indicator_id        VARCHAR,
    as_of_timestamp     TIMESTAMP,
    publish_timestamp   TIMESTAMP,
    fetch_time          TIMESTAMP,
    raw_value           DOUBLE,
    raw_unit            VARCHAR,
    frequency           VARCHAR,
    source_used         VARCHAR,
    source_channel_id   VARCHAR,
    data_lag_days       DOUBLE,
    stale_reason        VARCHAR,
    quality_flags       VARCHAR,
    content_hash        VARCHAR,
    schema_hash         VARCHAR,
    source_switched     BOOLEAN,
    created_at          TIMESTAMP
);
```

## 6.4 `axis_feature_snapshot`

保存第一层标准化特征。第一版只对 Layer 1 物化完整标准化字段。

```sql
CREATE TABLE IF NOT EXISTS axis_feature_snapshot (
    feature_id              VARCHAR PRIMARY KEY,
    indicator_id            VARCHAR,
    as_of_timestamp         TIMESTAMP,
    raw_value               DOUBLE,
    z_score                 DOUBLE,
    robust_z_score          DOUBLE,
    percentile_rank         DOUBLE,
    percentile_left_tail    DOUBLE,
    percentile_right_tail   DOUBLE,
    raw_delta_abs           DOUBLE,
    raw_delta_pct           DOUBLE,
    raw_delta_log           DOUBLE,
    z_score_delta           DOUBLE,
    percentile_delta        DOUBLE,
    level_state             VARCHAR,
    delta_state             VARCHAR,
    state_bucket            VARCHAR,
    extreme_flags           VARCHAR,
    standardize_method      VARCHAR,
    delta_method            VARCHAR,
    window_len              INTEGER,
    window_unit             VARCHAR,
    min_obs_required        INTEGER,
    valid_obs_count         INTEGER,
    coverage_ratio          DOUBLE,
    quality_flags           VARCHAR,
    stale_reason            VARCHAR,
    created_at              TIMESTAMP
);
```

## 6.5 `axis_indicator_profile`

保存静态解释。

```sql
CREATE TABLE IF NOT EXISTS axis_indicator_profile (
    indicator_id                    VARCHAR PRIMARY KEY,
    axis_id                         VARCHAR,
    display_name_cn                 VARCHAR,
    plain_language_name             VARCHAR,
    plain_language_summary          TEXT,
    physical_meaning_static         TEXT,
    financial_meaning_static        TEXT,
    coverage_scope_static           TEXT,
    penetration_power_static        TEXT,
    boundary_static                 TEXT,
    blind_spot_static               TEXT,
    update_frequency                VARCHAR,
    primary_source                  VARCHAR,
    validation_source               VARCHAR,
    fallback_policy                 VARCHAR,
    display_template                TEXT,
    interpretation_guardrails       TEXT,
    no_action_semantics             BOOLEAN,
    spec_path                       VARCHAR,
    updated_at                      TIMESTAMP
);
```

## 6.6 `axis_interpretation_snapshot`

保存每日解释快照。

```sql
CREATE TABLE IF NOT EXISTS axis_interpretation_snapshot (
    interpretation_id       VARCHAR PRIMARY KEY,
    indicator_id            VARCHAR,
    as_of_timestamp         TIMESTAMP,
    level_label             VARCHAR,
    change_label            VARCHAR,
    quality_label           VARCHAR,
    level_interpretation    TEXT,
    change_interpretation   TEXT,
    boundary_reminder       TEXT,
    warning_level           VARCHAR,
    warning_type            VARCHAR,
    warning_reason_code     VARCHAR,
    summary_sentence        TEXT,
    generated_by            VARCHAR,
    explanation_version     VARCHAR,
    needs_human_review      BOOLEAN,
    created_at              TIMESTAMP
);
```

---

# 7. 标准化与窗口策略

## 7.1 默认字段

Layer 1 推荐物化：

```text
raw_value
z_score
robust_z_score
raw_delta_abs
raw_delta_pct
raw_delta_log
z_score_delta
percentile_rank
percentile_delta
level_state
delta_state
state_bucket
extreme_flags
valid_obs_count
coverage_ratio
quality_flags
```

## 7.2 `state_bucket` 枚举

```text
normal
elevated
depressed
extreme_high
extreme_low
stale
insufficient_history
invalid
```

## 7.3 rolling window policy

| 指标频率 | 默认主窗口 | 最小样本数 | 说明 |
|---|---:|---:|---|
| Daily | 3Y | 500 | 主力窗口，适合日频状态。 |
| Weekly | 5Y | 156 | 适合周频拥挤、情绪、流动性观察。 |
| Monthly | 10Y | 60，优先 120 | 5Y 偏短，仅参考。 |
| Quarterly | 10Y-15Y | 40，优先 60 | 5Y 不足以判断极端。 |
| Irregular/Event | by obs_count | 30/60/120 | 视指标而定。 |
| Long-cycle macro | expanding + regime annotation | 视指标而定 | 可用全历史，但要标注 regime break 风险。 |

窗口不足时：

```text
raw_value 可以展示
z_score / percentile 不得伪造
state_bucket = insufficient_history
quality_flags 包含 INSUFFICIENT_HISTORY
```

---

# 8. 特征计算流程

## 8.1 计算顺序

```text
1. 读取 clean axis_observation
2. 按 indicator_id 分组
3. 按频率选择 rolling_window_policy
4. 检查 valid_obs_count / coverage_ratio
5. 计算 raw_delta_abs / raw_delta_pct / raw_delta_log
6. 计算 z_score / robust_z_score / percentile_rank
7. 映射 level_state / delta_state / state_bucket
8. 写入 axis_feature_snapshot staging
9. 经 WriteManager 写入 clean snapshot
```

## 8.2 robust z-score

默认使用中位数与 MAD：

```text
robust_z_score = 0.6745 * (x - median) / MAD
```

如果 MAD 为 0 或历史样本不足：

```text
robust_z_score = NULL
quality_flags += ROBUST_Z_UNAVAILABLE
```

## 8.3 百分位口径

默认保存：

```text
percentile_rank
percentile_left_tail
percentile_right_tail
```

避免只保存一个百分位造成方向歧义。

---

# 9. 质量规则

Layer 1 必须识别：

```text
MISSING_VALUE
STALE_DATA
SOURCE_SWITCHED
SCHEMA_DRIFT
INSUFFICIENT_HISTORY
OUTLIER_REVIEW_REQUIRED
NO_ACCEPTED_CHANNEL
FORBIDDEN_SUBSTITUTE_USED
BLINDSPOT_NOT_OBSERVABLE
```

禁止：

```text
用禁用替代指标填补主指标
用 Layer 2 慢变量回写 Layer 1
用 last_good_cache 冒充今天真实值
把 BlindSpot 伪造成可观测指标
```

---

# 10. 解释生成规则

解释分三层：

| 层级 | 生成者 | 说明 |
|---|---|---|
| 状态标签 | 程序 | `level_label`、`change_label`、`quality_label`。 |
| 模板解释 | 程序 | 根据 profile + state_bucket 生成结构化解释。 |
| 自然语言润色 | Agent | 只能基于结构化事实润色，不得新增结论。 |

Agent 输入必须包含：

```text
indicator_id
display_name_cn
raw_value
state_bucket
level_label
change_label
quality_label
plain_language_summary
boundary_static
quality_flags
source_used
data_lag_days
```

Agent 输出必须包含：

```text
summary_sentence
level_interpretation
change_interpretation
boundary_reminder
needs_human_review
```

禁止输出：

```text
买入
卖出
加仓
减仓
入场
出场
信号
```

---

# 11. API 契约

| API | 用途 |
|---|---|
| `GET /api/layer1/axes` | 获取五轴清单。 |
| `GET /api/layer1/state-snapshot` | 获取五轴最新状态快照。 |
| `GET /api/layer1/axis/{axis_id}` | 获取单轴状态和指标卡片。 |
| `GET /api/layer1/indicator/{indicator_id}` | 获取单指标历史、profile 与解释。 |
| `GET /api/layer1/quality` | 获取 Layer 1 数据质量概览。 |

所有 API 响应必须带：

```text
as_of_timestamp
fetch_time
quality_flags
stale_reason
source_used
```

---

# 12. CLI 契约

```bash
python -m quant_monitor layer1 load-specs
python -m quant_monitor layer1 sync --axis ENVIRONMENT
python -m quant_monitor layer1 compute-features --date 2026-06-14
python -m quant_monitor layer1 build-interpretation --date 2026-06-14
python -m quant_monitor layer1 health-check
```

---

# 13. 验收测试清单

| 测试 | 预期 |
|---|---|
| spec 缺少 `indicator_id` | loader 拒绝初始化。 |
| 指标历史不足 | 输出 `INSUFFICIENT_HISTORY`，不伪造 z-score。 |
| 主源失败但 fallback 生效 | 写 `SOURCE_SWITCHED`，并保留 fallback_policy。 |
| 使用 forbidden substitute | 阻断写入，写质量错误。 |
| BlindSpot 指标 | 只登记，不进入 observation。 |
| Agent 输出交易动作词 | 解释快照拒绝写入，进入人工复核。 |
| Layer 2 值试图回写 Layer 1 | 阻断。 |

---

# 14. 实现任务拆分

```text
1. 实现 AxisSpecLoader
2. 初始化 axis_registry / axis_indicator_registry / axis_indicator_profile
3. 实现 Layer1AxisFetcher
4. 实现 AxisObservationWriter
5. 实现 AxisFeatureEngine
6. 实现 AxisInterpretationEngine
7. 实现 Layer 1 API
8. 实现 Layer 1 前端卡片数据契约
9. 实现测试集
```
