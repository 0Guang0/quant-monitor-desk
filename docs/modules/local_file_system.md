# 本地文件系统模块

> 拆分说明：本文件由 `quant_monitor_design_document_v1_6.md` 拆分生成；当前步骤只做结构拆分与明显版本/编号残留修正，不删减原有细节。
> 来源：第 2 章

# 2. 本地文件系统定位：Raw Store / File Lake / Audit Store

## 2.1 定位不变，但要明确边界

本地文件系统不是数据库，而是：

```text
原始资料仓库 + 文件型数据湖 + 审计留痕层
```

DuckDB 存结构化数据、索引、快照、状态、因子、证据链；本地文件系统保存原始文件、PDF、HTML、JSON、CSV、XLSX、ZIP、Parquet、日志和审计产物。

## 2.2 本地文件系统保存内容

推荐目录：

```text
data/
  duckdb/
    quant_monitor.duckdb

  raw/
    qmt/
    baostock/
    akshare/
    eastmoney/
    cninfo/
    yahoo/
    tencent/
    baidu/
    ths/

  files/
    announcements/
    news/
    filings/
    research_reports/
    html_snapshots/

  parquet/
    stock_bar_1d/
    stock_bar_1m/
    futures_bar_1d/
    cross_asset_sensor/
    axis_observation_archive/

  audit/
    fetch_log.ndjson
    endpoint_audit.csv
    endpoint_audit_report.md
    latest_snapshot.json
    channel_registry_clean.yaml

  reports/
    daily/
    weekly/
    agent/

  cache/
    last_good_cache/
    api_cache/
```

## 2.3 DuckDB 与本地文件系统分工

| 类型 | 存储位置 | 说明 |
|---|---|---|
| 标准化行情表 | DuckDB | 查询、计算、回测、前端读取 |
| 因子 / 状态快照 | DuckDB | 结构化分析 |
| 信号 / 证据链 | DuckDB | Agent 和前端读取 |
| 公告 PDF / 财报 PDF | 本地文件系统 | 文件大，不适合表内 BLOB |
| 新闻 HTML 快照 | 本地文件系统 | 保留可复盘原文 |
| 原始抓取包 | 本地文件系统 | 可审计、可重放 |
| Parquet 历史归档 | 本地文件系统 | 大规模历史数据归档 |
| 文件索引 | DuckDB | local_path、url、hash、source、parse_status |

对应 DuckDB 文件索引表：

```sql
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

---
