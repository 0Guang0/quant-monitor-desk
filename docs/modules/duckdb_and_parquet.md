# DuckDB 与 Parquet 数据底座模块

> 扩展轮次：P0 第一轮模块扩展。  
> 本文件在 `docs_split_v1` 已拆分内容基础上新增实现级细节，不删减原 v1.6 设计原则。  
> 模块定位：本地优先系统的数据底座，负责 DuckDB 标准表、Parquet 历史归档、本地文件索引、schema version 与查询边界。

---

## 1. 模块目标

DuckDB 与 Parquet 模块要解决四件事：

```text
1. 哪些数据进 DuckDB，哪些数据进 Parquet，哪些数据只放文件系统。
2. 所有结构化数据表如何命名、建表、分层、归档。
3. 如何避免 DuckDB 被当作高并发业务库误用。
4. 如何让前端、Agent、回测和调度任务都读取同一套可信数据。
```

本模块不是单独业务模块，而是所有上层模块的公共底座：

```text
Data Sources / Fetchers
        ↓
Raw Store / File Lake
        ↓
Staging Tables / Temp Parquet
        ↓
DataQualityValidator / SourceConflictValidator
        ↓
WriteManager
        ↓
DuckDB Clean Tables + Snapshot Tables + Audit Tables
        ↓
FastAPI / Agent Tools / Frontend / Reports
```

---

## 2. 存储边界

### 2.1 DuckDB 存什么

DuckDB 负责结构化、可查询、需要经常 join 的数据。

| 类型 | 是否放 DuckDB | 说明 |
|---|---:|---|
| 标准化日线行情 | 是 | 查询、回测、前端展示 |
| 近期分钟线聚合 | 可选 | 高频全量分钟线优先 Parquet，DuckDB 可保留近期索引或聚合 |
| source_registry | 是 | 数据源元数据 |
| file_registry | 是 | 本地文件索引 |
| axis_observation / axis_feature_snapshot | 是 | Layer 1 核心状态 |
| layer2 / layer3 / layer4 / layer5 snapshot | 是 | 前端与 Agent 快速读取 |
| data_quality_log / source_conflict | 是 | 审计与人工确认 |
| 原始 PDF / HTML / ZIP | 否 | 放本地文件系统，DuckDB 只存路径和 hash |
| 超大历史 tick/minute 数据 | 否 | 优先 Parquet 分区归档 |

### 2.2 Parquet 存什么

Parquet 负责大历史、宽表、长期归档和可批量扫描数据。

| 数据 | 建议目录 | 分区键 |
|---|---|---|
| 日线历史归档 | `data/parquet/daily_bar/` | `market/year/month` |
| 分钟线 | `data/parquet/minute_bar/` | `market/year/month/trade_date` |
| 期货行情 | `data/parquet/futures_bar/` | `exchange/year/month` |
| 期权行情 | `data/parquet/options_bar/` | `market/year/month/expiry` |
| Layer 1 历史观测归档 | `data/parquet/layer1_axis/` | `axis/year` |
| raw JSON/CSV 归档转换 | `data/parquet/raw_archive/` | `source/data_domain/year/month` |

### 2.3 本地文件系统存什么

本地文件系统保存原始证据，不承担结构化查询职责。

```text
data/raw/       原始抓取包，按 source/data_domain/date 保存
data/files/     PDF、HTML、公告、新闻、研报、网页快照
data/audit/     fetch_log、revision_log、quality_log、conflict_log
data/cache/     last_good_cache、api_cache
data/backups/   DuckDB / 配置 / spec / 关键日志备份
```

---

## 3. 推荐目录结构

```text
data/
  duckdb/
    quant_monitor.duckdb
    quant_monitor.readonly.duckdb      # 可选：只读快照副本

  parquet/
    daily_bar/market=CN_A/year=2026/month=06/
    minute_bar/market=CN_A/year=2026/month=06/trade_date=2026-06-15/
    futures_bar/exchange=SHFE/year=2026/month=06/
    layer1_axis/axis=RISK_APPETITE/year=2026/
    layer3_snapshot/year=2026/month=06/

  raw/
    qmt/
    baostock/
    akshare/
    eastmoney/
    cninfo/
    yahoo/
    fred/
    cboe/

  files/
    announcements/
    filings/
    news/
    html_snapshots/
    research_reports/

  audit/
    fetch_log.ndjson
    write_log.ndjson
    data_quality_log.ndjson
    source_conflict_log.ndjson
    revision_log.ndjson

  backups/
    daily/
    weekly/
    before_schema_change/
```

---

## 4. 表分层规则

系统中所有 DuckDB 表必须归到以下层级之一。

| 表层级 | 命名建议 | 是否可被前端直接查 | 是否可被 Agent 查 | 是否允许人工改 |
|---|---|---:|---:|---:|
| raw index | `raw_*_index` | 否 | 受控只读 | 否 |
| staging | `stg_*` | 否 | 否 | 否 |
| clean | `*_bar_1d`, `axis_observation` | 是 | 是 | 否 |
| snapshot | `*_snapshot` | 是 | 是 | 否 |
| registry | `*_registry` | 是 | 是 | 通过配置更新 |
| audit | `*_log`, `source_conflict` | 限制 | 是 | 只允许状态字段 |
| manual review | `manual_review_queue` | 是 | 是 | 是 |

### 4.1 staging 表

staging 表只作为写入前缓冲区。

规则：

```text
1. staging 可以临时重建。
2. staging 不作为前端或 Agent 数据源。
3. staging 必须带 batch_id / run_id / source_id。
4. staging 通过校验后才进入 clean 表。
5. staging 保留期默认 7-30 天，取决于数据域。
```

### 4.2 clean 表

clean 表保存标准化后的可信主值。

规则：

```text
1. 每个客观事实字段只保存一个主值。
2. 必须能追溯 source_used、batch_id、content_hash。
3. 不能被 Agent、前端、研究脚本直接写入。
4. 所有写入必须通过 WriteManager。
```

### 4.3 snapshot 表

snapshot 表是面向前端和 Agent 的读取优化层。

```text
Layer 1 → axis_feature_snapshot / axis_interpretation_snapshot
Layer 2 → cross_asset_sensor_snapshot
Layer 3 → industry_chain_daily_snapshot
Layer 4 → market_index_snapshot / market_breadth_snapshot
Layer 5 → security_daily_snapshot / evidence_chain_snapshot
```

snapshot 不是原始真相来源，可以被重算。

---

## 5. 核心表清单

### 5.1 公共注册表

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
    notes               TEXT,
    updated_at          TIMESTAMP
);

CREATE TABLE IF NOT EXISTS file_registry (
    file_id             VARCHAR PRIMARY KEY,
    file_type           VARCHAR,
    source              VARCHAR,
    source_url          VARCHAR,
    local_path          VARCHAR,
    content_hash        VARCHAR,
    schema_hash         VARCHAR,
    fetch_time          TIMESTAMP,
    as_of_timestamp     TIMESTAMP,
    parse_status        VARCHAR,
    quality_flag        VARCHAR
);
```

### 5.2 同步与写入审计表

```sql
CREATE TABLE IF NOT EXISTS data_sync_job (
    job_id          VARCHAR PRIMARY KEY,
    job_type        VARCHAR,
    data_domain     VARCHAR,
    market_id       VARCHAR,
    instrument_id   VARCHAR,
    start_time      TIMESTAMP,
    end_time        TIMESTAMP,
    status          VARCHAR,
    retry_count     INTEGER,
    cursor_value    VARCHAR,
    error_message   TEXT,
    created_at      TIMESTAMP,
    updated_at      TIMESTAMP
);

CREATE TABLE IF NOT EXISTS write_audit_log (
    write_id            VARCHAR PRIMARY KEY,
    run_id              VARCHAR,
    target_table        VARCHAR,
    staging_table       VARCHAR,
    write_mode          VARCHAR,
    rows_in_staging     INTEGER,
    rows_inserted       INTEGER,
    rows_updated        INTEGER,
    rows_rejected       INTEGER,
    validation_status   VARCHAR,
    conflict_status     VARCHAR,
    started_at          TIMESTAMP,
    finished_at         TIMESTAMP,
    error_message       TEXT
);
```

### 5.3 标的与行情基础表

```sql
CREATE TABLE IF NOT EXISTS instrument_registry (
    instrument_id       VARCHAR PRIMARY KEY,
    symbol              VARCHAR,
    name                VARCHAR,
    market_id           VARCHAR,
    asset_type          VARCHAR,
    currency            VARCHAR,
    exchange            VARCHAR,
    is_active           BOOLEAN,
    list_date           DATE,
    delist_date         DATE,
    source_used         VARCHAR,
    updated_at          TIMESTAMP
);

CREATE TABLE IF NOT EXISTS security_bar_1d (
    instrument_id       VARCHAR,
    trade_date          DATE,
    open                DOUBLE,
    high                DOUBLE,
    low                 DOUBLE,
    close               DOUBLE,
    pre_close           DOUBLE,
    volume              DOUBLE,
    amount              DOUBLE,
    adjustment_type     VARCHAR,
    source_used         VARCHAR,
    batch_id            VARCHAR,
    quality_flags       VARCHAR,
    created_at          TIMESTAMP,
    PRIMARY KEY (instrument_id, trade_date, adjustment_type)
);
```

### 5.4 五层快照表

```sql
CREATE TABLE IF NOT EXISTS cross_layer_evidence_snapshot (
    snapshot_id         VARCHAR PRIMARY KEY,
    as_of_timestamp     TIMESTAMP,
    layer_id            VARCHAR,
    target_id           VARCHAR,
    target_name         VARCHAR,
    level_label         VARCHAR,
    change_label        VARCHAR,
    summary_sentence    TEXT,
    quality_flags       VARCHAR,
    source_used         VARCHAR,
    created_at          TIMESTAMP
);
```

各层专用表仍以各模块文档为准，本文件只定义公共存储边界。

---

## 6. Parquet 分区与命名规范

### 6.1 分区原则

```text
1. 常用于过滤的字段放在目录分区里。
2. 不要把高基数字段随便作为顶层分区，例如 instrument_id 不适合做第一层目录。
3. 日线按 market/year/month 分区。
4. 分钟线可以增加 trade_date 分区。
5. 期权可增加 expiry 分区。
6. Layer 1 按 axis/year 分区。
```

### 6.2 推荐路径

```text
# 日线
data/parquet/daily_bar/market=US_EQ/year=2026/month=06/part-000.parquet

# 分钟线
data/parquet/minute_bar/market=CN_A/year=2026/month=06/trade_date=2026-06-15/part-000.parquet

# Layer 1
data/parquet/layer1_axis/axis=RISK_APPETITE/year=2026/part-000.parquet

# Layer 3 快照归档
data/parquet/layer3_snapshot/year=2026/month=06/part-000.parquet
```

### 6.3 读写建议

```sql
-- 直接查询 Parquet
SELECT *
FROM read_parquet('data/parquet/daily_bar/market=US_EQ/year=2026/month=06/*.parquet')
WHERE trade_date >= DATE '2026-06-01';

-- schema 不完全一致时使用 union_by_name
SELECT *
FROM read_parquet('data/parquet/raw_archive/source=*/year=2026/*.parquet', union_by_name = true);

-- 从 DuckDB 导出归档
COPY (
    SELECT * FROM security_bar_1d
    WHERE trade_date < DATE '2025-01-01'
) TO 'data/parquet/daily_bar_archive/year=2024/security_bar_1d.parquet' (FORMAT PARQUET);
```

---

## 7. Schema version 与 migration

### 7.1 schema_version 表

```sql
CREATE TABLE IF NOT EXISTS schema_version (
    version_id          VARCHAR PRIMARY KEY,
    applied_at          TIMESTAMP,
    migration_file      VARCHAR,
    checksum            VARCHAR,
    applied_by          VARCHAR,
    notes               TEXT
);
```

### 7.2 migration 规则

```text
1. 任何 schema 变更前必须备份 DuckDB。
2. migration 文件命名：YYYYMMDD_HHMM_description.sql。
3. migration 必须可重复执行或显式检查前置状态。
4. migration 后写入 schema_version。
5. migration 后运行 smoke test。
6. 重要字段删除必须先 deprecate，不得直接 drop。
```

### 7.3 禁止事项

```text
禁止在业务代码里临时 ALTER 主表。
禁止让 Agent 生成 SQL 直接修改主表。
禁止无备份执行破坏性 migration。
禁止把 schema migration 和数据回补混成一个任务。
```

---

## 8. 查询性能边界

### 8.1 前端查询

```text
1. 默认分页。
2. 默认最近 N 天。
3. 大表必须带 market / date_range / instrument_id 至少一个过滤条件。
4. Layer 3 / Layer 4 页面优先查询 snapshot 表。
5. 不允许前端触发全市场全历史扫描。
```

### 8.2 Agent 查询

```text
1. Agent 工具默认 limit 200。
2. Agent 工具绝对最高 limit 1000；唯一机器权威为 `specs/contracts/api_security_contract.yaml`，不得保留高于全局绝对上限的特殊工具例外。
3. Agent 只能查受控 view。
4. Agent 查询必须记录 query_audit_log。
5. Agent 不允许执行 DDL / DML。
```

### 8.3 研究查询

研究查询允许更重，但必须在 Research Workspace 执行，不能直接覆盖 clean 表。

```text
Research SQL / Pandas / Polars
        ↓
临时表 / 临时 Parquet
        ↓
人工确认
        ↓
Staging
        ↓
Validation
        ↓
WriteManager
```

---

## 9. Python / DuckDB / Polars 使用边界

### 9.1 DuckDB 优先承担 SQL 聚合

大表聚合、过滤、join 优先交给 DuckDB SQL，不要先全部 `.df()` 到 Pandas。

```python
# 推荐
con.execute("""
SELECT instrument_id, avg(volume) AS avg_volume
FROM security_bar_1d
WHERE trade_date >= DATE '2026-01-01'
GROUP BY instrument_id
""").df()

# 不推荐
# df = con.execute("SELECT * FROM security_bar_1d").df()
# df.groupby("instrument_id")["volume"].mean()
```

### 9.2 Polars Lazy 用于复杂 DataFrame 计算

当计算需要 DataFrame 表达力时，优先使用 Polars Lazy，避免 Pandas 全量中间表。

```python
import polars as pl

lf = pl.scan_parquet("data/parquet/daily_bar/market=US_EQ/year=2026/month=06/*.parquet")
result = (
    lf.filter(pl.col("trade_date") >= "2026-06-01")
      .group_by("instrument_id")
      .agg(pl.col("volume").mean().alias("avg_volume"))
      .collect()
)
```

---

## 10. 健康检查

每日检查：

```text
1. DuckDB 文件是否存在且可连接。
2. schema_version 是否为最新。
3. 关键 clean 表是否有今日或最近交易日数据。
4. snapshot 表是否完成生成。
5. Parquet 分区是否新增。
6. DuckDB 文件大小是否异常增长。
7. audit 日志是否持续写入。
```

每周检查：

```text
1. 随机抽样 Parquet 可读性。
2. 检查 orphan 文件，即 file_registry 中无记录但文件系统存在的文件。
3. 检查 dangling path，即 file_registry 有记录但文件不存在。
4. 检查 schema drift 统计。
5. 检查 query slow log。
```

---

## 11. 实现任务

建议实现顺序：

```text
001_create_schema_sql
002_create_duckdb_connection_manager
003_create_file_registry
004_create_parquet_partition_policy
005_create_schema_version_migration_runner
006_create_query_readonly_service
007_create_duckdb_health_check
```

---

## 12. 官方依据与工程注记

- DuckDB 官方说明其 in-process 模式下 read-write 适合单个进程读写，read-only 模式允许多个进程读取，因此本项目继续坚持“单写多读、统一 WriteManager 写入”。
- DuckDB 官方支持高效读取和写入 Parquet，并支持对 Parquet 查询进行过滤和列裁剪，因此大历史数据优先 Parquet 是合理选择。
- Polars Lazy API 会推迟执行并进行查询优化，适合复杂 DataFrame 计算和较大数据集处理。

本文件中的技术约束应与 `write_manager.md`、`data_sync_orchestrator.md`、`data_validation_and_conflict.md` 保持一致。
