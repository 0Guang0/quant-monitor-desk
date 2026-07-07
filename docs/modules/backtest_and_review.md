# 回测与复盘模块

> 权威定位：本文件定义本系统的回测与复盘能力。它不是自动交易模块，不直接生成买卖信号，不执行下单，不承诺未来收益。  
> 当前定位：第一阶段做“监控规则、证据链、状态事件、产业链锚点、市场结构异常”的历史复盘与解释力评估；第二阶段再考虑更标准的策略回测。

---

# 1. 模块目标

回测与复盘模块回答：

```text
某类五轴状态出现后，后续 N 天市场发生了什么？
某个 Layer 3 产业链锚点事件后，相关链条是否扩散？
某个 Layer 4 市场结构异常后，市场宽度、板块和个股证据如何变化？
某条盘中提醒规则历史上触发了多少次，误报多少次，是否有信息价值？
某段 Agent 解释是否被后续证据支持？
```

第一阶段不回答：

```text
应该买什么
应该卖什么
应该加仓多少
自动下单是否执行
某策略保证盈利
```

---

# 2. 回测类型

| backtest_type                    | 中文名         | 目标                                         |
| -------------------------------- | -------------- | -------------------------------------------- |
| `event_study`                    | 事件研究       | 观察事件发生后 N 天的价格、波动、扩散变化    |
| `alert_rule_review`              | 提醒规则复盘   | 评估某条提醒规则的触发频率、重复率、后续表现 |
| `layer1_state_review`            | 五轴状态复盘   | 评估某个五轴状态/突变后的市场变化            |
| `layer3_chain_review`            | 产业链扩散复盘 | 评估产业链节点/边/锚点事件的扩散路径         |
| `layer4_market_structure_review` | 市场结构复盘   | 评估宽度、涨跌停、期权波动等市场结构事件     |
| `evidence_chain_review`          | 证据链复盘     | 评估当时证据链是否完整、是否存在数据风险     |
| `agent_explanation_review`       | Agent 解释复盘 | 检查 Agent 解释是否符合事实、边界和后续证据  |

---

# 3. 数据输入

回测只能读取已归档数据：

```text
axis_feature_snapshot
axis_interpretation_snapshot
cross_asset_daily_snapshot
industry_chain_daily_snapshot
market_breadth_snapshot
market_sector_snapshot
security_bar_daily
futures_bar_daily
options_chain_snapshot
evidence_chain
alert_event
report_registry / report_section
agent_run_log / agent_output_staging
```

回测可以直接用 DuckDB 查询 Parquet 历史数据，但必须经过 ResourceGuard 限制扫描范围。

---

# 4. 核心表结构

## 4.1 backtest_scenario_registry

```sql
CREATE TABLE IF NOT EXISTS backtest_scenario_registry (
    scenario_id            VARCHAR PRIMARY KEY,
    scenario_name          TEXT,
    backtest_type          VARCHAR,
    description            TEXT,
    input_requirements_json JSON,
    default_window_json    JSON,
    metric_set_json        JSON,
    resource_profile       VARCHAR,
    no_action_semantics    BOOLEAN,
    created_at             TIMESTAMP,
    updated_at             TIMESTAMP
);
```

## 4.2 backtest_run_log

```sql
CREATE TABLE IF NOT EXISTS backtest_run_log (
    run_id                 VARCHAR PRIMARY KEY,
    scenario_id            VARCHAR,
    run_status             VARCHAR,
    started_at             TIMESTAMP,
    finished_at            TIMESTAMP,
    requested_by           VARCHAR,
    resource_mode          VARCHAR,
    date_range_start       DATE,
    date_range_end         DATE,
    universe_size          INTEGER,
    event_count            INTEGER,
    output_path            TEXT,
    error_code             VARCHAR,
    quality_flags_json     JSON
);
```

## 4.3 backtest_event_set

```sql
CREATE TABLE IF NOT EXISTS backtest_event_set (
    event_id               VARCHAR PRIMARY KEY,
    run_id                 VARCHAR,
    event_type             VARCHAR,
    source_layer           VARCHAR,
    target_id              VARCHAR,
    event_timestamp        TIMESTAMP,
    evidence_ids_json      JSON,
    facts_used_json        JSON,
    quality_flags_json     JSON
);
```

## 4.4 backtest_metric_snapshot

```sql
CREATE TABLE IF NOT EXISTS backtest_metric_snapshot (
    metric_id              VARCHAR PRIMARY KEY,
    run_id                 VARCHAR,
    event_id               VARCHAR,
    target_id              VARCHAR,
    horizon                VARCHAR,
    metric_name            VARCHAR,
    metric_value           DOUBLE,
    metric_unit            VARCHAR,
    sample_size            INTEGER,
    quality_flags_json     JSON,
    created_at             TIMESTAMP
);
```

## 4.5 backtest_report

```sql
CREATE TABLE IF NOT EXISTS backtest_report (
    backtest_report_id     VARCHAR PRIMARY KEY,
    run_id                 VARCHAR,
    title                  TEXT,
    summary                TEXT,
    local_path             TEXT,
    limitations            TEXT,
    no_action_semantics    BOOLEAN,
    generated_at           TIMESTAMP,
    needs_human_review     BOOLEAN
);
```

---

# 5. 指标与窗口

默认观察窗口：

```text
T+1
T+3
T+5
T+10
T+20
```

可选指标：

```text
forward_return
max_drawdown
realized_volatility
hit_rate
false_positive_rate
average_adverse_move
average_favorable_move
chain_diffusion_count
cross_layer_confirmation_count
data_quality_failure_rate
```

第一阶段不做复杂参数寻优，不做高频撮合，不做真实交易费用建模。若未来要做策略级回测，必须新增交易成本、滑点、成交约束、停牌、涨跌停、主力合约换月、复权和 survivorship bias 规则。

---

# 6. 运行链路

```text
User selects scenario
  → ResourceGuard checks date range / universe / estimated scan size
  → BacktestScenarioLoader loads scenario
  → BacktestEventBuilder builds event set
  → BacktestDataLoader loads historical snapshots / Parquet data
  → BacktestMetricEngine computes metrics
  → BacktestReportBuilder writes report
  → WriteManager writes run logs and metric snapshots
  → Frontend displays review result
```

---

# 7. 资源限制

第一阶段回测默认使用 `normal` 或 `batch` 模式，但必须用户显式触发。

默认限制：

```text
date_range 默认不超过 3 年
universe 默认不超过 500 个 instrument
单次 run 事件数默认不超过 5000
扫描 Parquet 文件预估超过 5GB 时要求用户确认
系统可用内存 < 2GB 时暂停
磁盘剩余 < 20GB 时暂停
```

回测不得在盘中轻量模式自动运行。

---

# 8. API 契约

```text
GET /api/backtest/scenarios
POST /api/backtest/runs
GET /api/backtest/runs/{run_id}
GET /api/backtest/runs/{run_id}/events
GET /api/backtest/runs/{run_id}/metrics
GET /api/backtest/reports/{backtest_report_id}
```

所有 API 默认分页，返回 `query_cost_class`。

---

# 9. CLI 契约

```bash
python -m quant_monitor.backtest.list_scenarios
python -m quant_monitor.backtest.run --scenario layer3_chain_review --date-range 2024-01-01:2026-06-14 --resource-mode normal
python -m quant_monitor.backtest.generate_report --run-id <run_id>
```

---

# 10. 与 Agent 的关系

Agent 可以：

```text
解释回测报告
生成局限性说明
把 metric_snapshot 转为通俗语言
列出需要人工复核的异常样本
```

Agent 不可以：

```text
改写 backtest_metric_snapshot
编造不存在的历史表现
把回测结果改写成交易建议
绕过 NoActionSemanticGuard
```

---

# 11. 验收测试

```text
回测 run 必须写 backtest_run_log
回测事件必须来自已存在 snapshot / evidence / alert_event
回测结果必须包含 limitations
回测报告 no_action_semantics=true
ResourceGuard PAUSE 时不能启动回测
回测 API 默认分页
Agent 不能把回测结果渲染为交易建议
```

---

# 12. BacktestReviewEngine 生命周期与指标契约

Round4 `029_implement_backtest_and_review.md` 必须先对齐以下新增设计：

- `docs/modules/backtest_review_lifecycle.md`
- `docs/modules/review_sandbox_api.md`
- `specs/contracts/backtest_metric_contract.yaml`
- `specs/contracts/review_sandbox_contract.yaml`
- `specs/contracts/reference_adoption_guardrails.yaml`

默认回测/复盘只回答“事件后发生了什么、证据链是否支持、数据质量如何”，不得输出买卖动作。JQ2PTrade 的生命周期可作为实现形态参考，但其 order API、策略 exec、持仓/交易语义不得进入默认实现。

策略导入如未来启用，必须先走 Review Sandbox AST 静态扫描，禁止 `order*`、`os/sys/subprocess/network` 与任意外部 import。
