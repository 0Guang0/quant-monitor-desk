# 数据质量检查与多源冲突治理模块

> 扩展轮次：P0 第一轮模块扩展。  
> 本文件从原 `data_validation_write_concurrency.md` 中拆出数据质量与冲突治理职责，并保留原 v1.6 所有原则。  
> 写入并发与事务细节已移入 `write_manager.md`，避免职责混淆。

---

## 1. 模块目标

本模块回答两个问题：

```text
1. 单份数据自己有没有问题？ → DataQualityValidator
2. 多个来源对同一事实是否打架？ → SourceConflictValidator + ReconcileJob
```

这两个问题不能混在一起：

```text
质量检查：一份数据内部是否合格。
冲突检查：多个来源之间是否一致。
```

示例：

```text
high < low                         → 质量问题
QMT close = 10.00, baostock = 10.01 → 可能是多源差异
东方财富主力资金流 vs 同花顺主力资金流 → 口径差异，不强行冲突
```

---

## 2. 总体流程

```text
staging table / temp parquet
        ↓
DataQualityValidator
        ↓
Normalize for conflict comparison
        ↓
SourceConflictValidator
        ↓
ValidationReport + ConflictReport
        ↓
WriteManager ValidationGate
        ↓
clean table / source_conflict / manual_review_queue
```

---

## 3. DataQualityValidator

### 3.1 输入

```yaml
validation_request:
  run_id: string
  job_id: string
  data_domain: string
  staging_table: string
  source_id: string
  market_id: string | null
  instrument_id: string | null
  date_start: date | null
  date_end: date | null
  rule_set_id: string
```

### 3.2 输出

```yaml
validation_report:
  validation_report_id: string
  status: PASSED | WARNING | FAILED
  checked_rows: integer
  failed_rows: integer
  warning_rows: integer
  quality_flags: [string]
  stale_reason: string | null
  can_write_clean: boolean
  needs_manual_review: boolean
```

---

## 4. 质量检查规则

### 4.1 通用规则

| 检查              | 失败标记                 | 说明                    |
| ----------------- | ------------------------ | ----------------------- |
| 主键为空          | `MISSING_PRIMARY_KEY`    | 不能入 clean            |
| 复合主键重复      | `DUPLICATE_PRIMARY_KEY`  | 不能入 clean            |
| 关键字段为空      | `MISSING_REQUIRED_FIELD` | 视字段决定失败或警告    |
| 时间戳为空        | `MISSING_TIMESTAMP`      | 不能入 clean            |
| 非法枚举          | `INVALID_ENUM`           | 不能入 clean            |
| schema_hash 变化  | `SCHEMA_DRIFT`           | 暂停写入，需确认        |
| content_hash 变化 | `CONTENT_CHANGED`        | 可能触发 revision audit |
| 数据滞后          | `STALE_DATA`             | 可写但必须标记          |
| 样本不足          | `INSUFFICIENT_HISTORY`   | Layer 1/特征计算常见    |

### 4.2 行情字段规则

| 规则                                           | 标记                  |
| ---------------------------------------------- | --------------------- |
| `high < low`                                   | `INVALID_PRICE_RANGE` |
| `open < 0 or high < 0 or low < 0 or close < 0` | `NEGATIVE_PRICE`      |
| `volume < 0`                                   | `INVALID_VOLUME`      |
| `amount < 0`                                   | `INVALID_AMOUNT`      |
| `pre_close <= 0` 且不是新股/特殊资产           | `INVALID_PRE_CLOSE`   |
| `trade_date` 非交易日                          | `INVALID_TRADE_DATE`  |
| 缺少 expected trading date                     | `MISSING_TRADING_DAY` |

### 4.3 五轴指标规则

| 规则                                  | 标记                              |
| ------------------------------------- | --------------------------------- |
| `as_of_timestamp` 缺失                | `MISSING_AS_OF_TIMESTAMP`         |
| `publish_timestamp` 晚于 `fetch_time` | `INVALID_PUBLISH_TIME`            |
| `data_lag_days` 超过规则              | `STALE_DATA`                      |
| 窗口样本不足                          | `INSUFFICIENT_HISTORY`            |
| source_used 缺失                      | `MISSING_SOURCE_USED`             |
| fallback 未记录                       | `FALLBACK_WITHOUT_REASON`         |
| BlindSpot 出现 raw_value              | `BLINDSPOT_SHOULD_NOT_HAVE_VALUE` |

### 4.4 Layer 3 配置规则

| 规则                                 | 标记                              |
| ------------------------------------ | --------------------------------- |
| anchor_id 重复                       | `DUPLICATE_ANCHOR_ID`             |
| anchor.node_id 不存在                | `MISSING_NODE_REFERENCE`          |
| edge.from_node_id 不存在             | `INVALID_EDGE_FROM_NODE`          |
| edge.to_node_id 不存在               | `INVALID_EDGE_TO_NODE`            |
| event_only 私有公司却有 ticker       | `PRIVATE_EVENT_ANCHOR_HAS_TICKER` |
| commodity/index 被标为 public_equity | `INVALID_INSTRUMENT_TYPE`         |
| P0 anchor 缺 source_keys             | `P0_MISSING_SOURCE_KEYS`          |

---

## 5. SourceConflictValidator

### 5.1 输入

```yaml
conflict_check_request:
  run_id: string
  job_id: string
  data_domain: string
  primary_source: string
  validation_sources: [string]
  key_fields: [string]
  comparable_fields: [string]
  tolerance_rule_set_id: string
```

### 5.2 输出

```yaml
conflict_report:
  conflict_report_id: string
  status: PASSED | WARNING | SEVERE_CONFLICT
  conflicts: [conflict_id]
  can_write_primary_value: boolean
  needs_reconcile: boolean
  needs_manual_review: boolean
```

---

## 6. 字段分类与处理规则

### 6.1 客观事实类字段

这些字段存在“较明确事实值”，可做多源比较。

```text
open
high
low
close
pre_close
volume
amount
settlement_price
open_interest
index_level
```

处理规则：

| 差异         | 处理                                              |
| ------------ | ------------------------------------------------- |
| 容忍范围内   | 主源写入，记录校验通过                            |
| 略超容忍范围 | 主源写入，标 `source_divergence_warning`          |
| 严重差异     | 不写 clean，写 source_conflict，触发 ReconcileJob |
| 重抓后仍冲突 | `manual_review_required=true`                     |

### 6.2 口径差异类字段

这些字段天然没有统一口径，不强行合成一个主值。

```text
主力资金流
大单资金流
题材概念
新闻情绪
机构观点
估值分位
平台热度
```

处理方式：

```text
1. 分源保存。
2. 前端显示来源。
3. Agent 解释时必须说明口径差异。
4. 不把差异当作 source_conflict。
```

---

## 7. 容忍阈值配置

建议用 YAML 配置，不写死在代码里。

```yaml
market_bar_1d:
  close:
    relative_warning: 0.0005
    relative_severe: 0.002
  volume:
    relative_warning: 0.005
    relative_severe: 0.02
  amount:
    relative_warning: 0.005
    relative_severe: 0.02

index_level:
  index_level:
    relative_warning: 0.0002
    relative_severe: 0.001

futures_bar:
  settlement_price:
    relative_warning: 0.0005
    relative_severe: 0.002
  open_interest:
    relative_warning: 0.01
    relative_severe: 0.05
```

阈值必须按数据域、市场、字段调参，不应全局一套阈值。

---

## 8. source_conflict 表

```sql
CREATE TABLE IF NOT EXISTS source_conflict (
    conflict_id             VARCHAR PRIMARY KEY,
    run_id                  VARCHAR,
    job_id                  VARCHAR,
    data_domain             VARCHAR,
    market_id               VARCHAR,
    instrument_id           VARCHAR,
    field_name              VARCHAR,
    as_of_timestamp         TIMESTAMP,
    primary_source          VARCHAR,
    primary_value           VARCHAR,
    competing_source        VARCHAR,
    competing_value         VARCHAR,
    normalized_diff         DOUBLE,
    tolerance_warning       DOUBLE,
    tolerance_severe        DOUBLE,
    severity                VARCHAR,
    reconcile_status        VARCHAR,
    manual_review_required  BOOLEAN,
    resolution              VARCHAR,
    resolution_note         TEXT,
    created_at              TIMESTAMP,
    resolved_at             TIMESTAMP
);
```

---

## 9. ReconcileJob 规则

### 9.1 触发条件

```text
1. source_conflict.severity = severe
2. schema drift 后主源与 validation 源字段无法对齐
3. primary source 返回明显异常值
4. 用户手动指定重新对账
```

### 9.2 流程

```text
source_conflict created
        ↓
ReconcileJob 重新抓 primary source
        ↓
重新抓 validation source
        ↓
统一单位、时区、复权、字段名
        ↓
再次比较
        ↓
解决 → 更新 source_conflict.resolution
未解决 → manual_review_required=true
```

---

## 10. Manual Review Queue

```sql
CREATE TABLE IF NOT EXISTS manual_review_queue (
    review_id           VARCHAR PRIMARY KEY,
    source_object_type  VARCHAR, -- conflict / validation / revision / schema
    source_object_id    VARCHAR,
    priority            VARCHAR,
    title               VARCHAR,
    description         TEXT,
    suggested_action    TEXT,
    status              VARCHAR,
    assigned_to         VARCHAR,
    created_at          TIMESTAMP,
    resolved_at         TIMESTAMP,
    resolution_note     TEXT
);
```

人工确认后，不直接改 clean 表，而是创建 `manual_patch` 写入请求交给 WriteManager。

---

## 11. Validation Report 表

```sql
CREATE TABLE IF NOT EXISTS validation_report (
    validation_report_id    VARCHAR PRIMARY KEY,
    run_id                  VARCHAR,
    job_id                  VARCHAR,
    data_domain             VARCHAR,
    staging_table           VARCHAR,
    source_id               VARCHAR,
    status                  VARCHAR,
    checked_rows            INTEGER,
    failed_rows             INTEGER,
    warning_rows            INTEGER,
    quality_flags           VARCHAR,
    stale_reason            VARCHAR,
    can_write_clean         BOOLEAN,
    needs_manual_review     BOOLEAN,
    created_at              TIMESTAMP
);
```

---

## 12. data_quality_log 表

```sql
CREATE TABLE IF NOT EXISTS data_quality_log (
    log_id              VARCHAR PRIMARY KEY,
    validation_report_id VARCHAR,
    run_id              VARCHAR,
    job_id              VARCHAR,
    data_domain         VARCHAR,
    source_id           VARCHAR,
    table_name          VARCHAR,
    row_key             VARCHAR,
    field_name          VARCHAR,
    rule_id             VARCHAR,
    severity            VARCHAR,
    observed_value      VARCHAR,
    expected_condition  VARCHAR,
    message             TEXT,
    created_at          TIMESTAMP
);
```

---

## 13. 验收测试

| 测试                             | 预期                               |
| -------------------------------- | ---------------------------------- |
| high < low                       | validation FAILED                  |
| volume < 0                       | validation FAILED                  |
| missing source_used              | validation FAILED                  |
| schema_hash 变化                 | validation FAILED 或 MANUAL_REVIEW |
| 客观字段轻微差异                 | warning 或 passed                  |
| 客观字段严重差异                 | source_conflict severe             |
| 主力资金流多源差异               | 分源保存，不创建 severe conflict   |
| P0 Layer 3 anchor 缺 source_keys | validation FAILED                  |
| BlindSpot 出现 raw_value         | validation FAILED                  |
| manual review 通过               | 生成 manual_patch write request    |

---

## 14. 与其他模块关系

| 模块                        | 关系                         |
| --------------------------- | ---------------------------- |
| `data_sources.md`           | 提供 raw/staging/source 信息 |
| `data_sync_orchestrator.md` | 调用验证任务并接收报告       |
| `write_manager.md`          | 读取验证报告，决定是否可写   |
| `duckdb_and_parquet.md`     | 提供表结构和审计存储         |
| `ops_and_performance.md`    | 定期执行质量报告和冲突检查   |

---

## 15. 保留原 v1.6 原则

本文件继续保留以下原则：

```text
1. 质量检查和冲突检查是两件事。
2. 冲突检查不每天全历史扫描。
3. 客观事实字段按阈值分级处理。
4. 口径差异字段分源保存。
5. 严重冲突先重抓，仍冲突再人工。
6. 标准表不接受未验证数据。
7. Agent 不能直接写库。
```
