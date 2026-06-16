---
title: "量化监控系统运维与性能手册 v1.2"
subtitle: "本地文件系统、DuckDB、Parquet、增量/回补、备份恢复、内存/空间/查询性能"
date: "2026-06-14"
author: "ChatGPT 生成，供 Claude Code / Codex 实现使用"
---

# 量化监控系统运维与性能手册 v1.2

> 目标：让系统在少数人、本地优先、低门槛的前提下长期稳定运行。  
> 原则：先保证数据可追溯、可恢复、可控写入，再优化性能。  
> 范围：本文件是 `quant_monitor_design_document_v1_6.md` 的配套运维文件，不替代主设计文档。

---

# 1. 通俗版总原则

系统里有三类东西：

```text
DuckDB：结构化数据库，放标准表、快照、索引、证据链。
本地文件系统：原始文件仓库，放 PDF、HTML、JSON、CSV、日志、备份。
Parquet：大历史数据归档，放分钟线、长期行情、跨资产历史、Layer 1 历史观测。
```

不要把所有东西都塞进 DuckDB。PDF、网页快照、原始抓取包、日志、历史大表更适合放在文件系统或 Parquet。DuckDB 负责把它们索引起来、查询起来。

---

# 2. 本地目录规范

推荐目录：

```text
data/
├── duckdb/
│   └── quant_monitor.duckdb
├── raw/
│   ├── qmt/
│   ├── baostock/
│   ├── akshare/
│   ├── eastmoney/
│   ├── cninfo/
│   ├── yahoo/
│   ├── tencent/
│   ├── baidu/
│   └── ths/
├── parquet/
│   ├── daily_bar/
│   ├── minute_bar/
│   ├── futures_bar/
│   ├── options_bar/
│   ├── layer1_axis/
│   └── cross_asset/
├── files/
│   ├── announcements/
│   ├── news/
│   ├── filings/
│   └── reports/
├── audit/
│   ├── fetch_log.ndjson
│   ├── data_quality_log.ndjson
│   ├── source_conflict_log.ndjson
│   └── revision_log.ndjson
├── cache/
│   ├── api_cache/
│   └── last_good_cache/
└── backups/
    ├── daily/
    ├── weekly/
    └── before_schema_change/
```

## 2.1 哪些目录可以清理？

| 目录 | 是否可清理 | 建议 |
|---|---|---|
| `data/cache/` | 可以 | 7-30 天定期清理 |
| `data/audit/` | 不直接删除 | 90 天热日志，历史压缩 |
| `data/raw/` | 谨慎 | 原始数据建议至少保留 1-3 年 |
| `data/files/announcements/` | 不建议删 | 公告、财报、PDF 长期保留 |
| `data/parquet/` | 不建议删 | 历史大表归档 |
| `data/backups/` | 按策略清理 | 保留最近 N 份日备份和周备份 |

---

# 3. DuckDB 运维规则

## 3.1 单写多读

DuckDB 用作本地分析库。写入必须统一通过 `DuckDBWriteManager`，前端、Agent、研究脚本默认只读。

规则：

```text
所有写入 → Staging → Validation → WriteManager → Clean Table
所有读取 → FastAPI / ReadOnlyQueryService
Agent → 只能调用受控查询工具
前端 → 只能请求 FastAPI
```

禁止：

```text
Agent 直接写 DuckDB
前端直接连接 DuckDB
多个 Python 进程同时写同一个 .duckdb 文件
研究脚本绕过 WriteManager 写主表
```

## 3.2 写入流程

```text
1. 抓到数据
2. 写入 staging 表或临时 parquet
3. 执行质量检查
4. 去重
5. 多源校验
6. merge/upsert 到 clean 表
7. 写入 audit 日志
8. 生成 data_quality_report
```

## 3.3 DuckDB 文件备份

建议：

```text
每日盘后备份一次 quant_monitor.duckdb
重大 schema 变更前手动备份
每周保留一份完整备份
备份文件命名：quant_monitor_YYYYMMDD_HHMM.duckdb
```

示例路径：

```text
data/backups/daily/quant_monitor_20260614_1800.duckdb
```

---

# 4. Parquet 归档规则

Parquet 适合大历史表，例如：

```text
分钟线
长期日线
期货历史
期权历史
跨资产历史行情
Layer 1 五轴历史观测
原始抓取归档
```

## 4.1 分区规范

推荐按市场、资产类型、年份、月份分区：

```text
data/parquet/daily_bar/market=CN_A/year=2026/month=06/
data/parquet/minute_bar/market=US_EQ/year=2026/month=06/
data/parquet/futures_bar/market=CN_FUT/year=2026/month=06/
data/parquet/layer1_axis/axis=RISK_APPETITE/year=2026/
```

通俗解释：

```text
按 market 分区，方便只查 A 股或美股。
按 year/month 分区，方便只查最近几个月。
按 axis 分区，方便只查某条五轴。
```

## 4.2 什么时候转 Parquet？

| 数据 | 建议 |
|---|---|
| 日线标准表 | 可留 DuckDB，也可定期归档 Parquet |
| 分钟线 | 优先 Parquet |
| Tick 数据 | 如未来接入，优先 Parquet，且短期保留 |
| Layer 1 历史观测 | DuckDB 近期 + Parquet 归档 |
| Raw 原始数据 | JSON/CSV 起步，后期可压缩或 Parquet 化 |

---

# 5. 数据同步：全量、增量、回补、修订、冲突重抓

数据同步不是一个大函数，而是一组任务。

```text
DataSyncOrchestrator
├── FullLoadJob
├── IncrementalUpdateJob
├── BackfillJob
├── RevisionAuditJob
├── ReconcileJob
└── DataQualityJob
```

## 5.1 FullLoadJob

第一次建库或重大重建时使用。

抓取：

```text
股票列表
市场日历
历史日线
分钟线初始化窗口
复权因子
基础财务
公告索引
五轴历史指标
跨资产历史数据
产业链 / 市场基础映射
```

## 5.2 IncrementalUpdateJob

日常默认使用。只抓新增或变化数据，不每天全量重抓。

判断依据：

```text
本地最新 trade_date
本地最新 as_of_timestamp
上次 fetch_time
source cursor
content_hash
schema_hash
market_calendar
```

## 5.3 BackfillJob

用于补缺失或失败数据。

触发场景：

```text
网络中断
数据源延迟
任务失败
节假日/半日市错位
复权因子变化
公告 PDF 后补
财报修订
用户指定日期范围重算
```

Backfill 必须按分区执行：

```text
market + date_range + data_domain + instrument_id
```

不要无差别全量重抓。

## 5.4 RevisionAuditJob

用于检查数据源是否修订历史数据。

核心字段：

```text
content_hash
schema_hash
revision_id
fetch_time
as_of_timestamp
```

发现修订后：

```text
写 revision_log
触发局部 backfill
触发局部 feature 重算
触发受影响报告重生成
```

## 5.5 ReconcileJob

用于解决数据源冲突。

流程：

```text
source_conflict 出现严重冲突
    ↓
重新抓主源与备用源
    ↓
标准化口径
    ↓
再次比较
    ↓
仍冲突 → manual_review_required=true
```

---

# 6. 多源冲突处理流程

## 6.1 客观事实类字段

字段：

```text
open, high, low, close, pre_close, volume, amount, settlement_price, open_interest, index_level
```

规则：

| 情况 | 处理 |
|---|---|
| 差异很小 | 主源入标准表，备用源记录为校验通过 |
| 差异中等 | 主源入标准表，但 `quality_flag=source_divergence_warning` |
| 差异严重 | 不写标准表，写 `source_conflict`，触发 ReconcileJob |
| 重抓后仍严重 | 人工确认 |

## 6.2 口径差异类字段

字段：

```text
主力资金流
大单资金流
题材概念
新闻情绪
机构观点
估值分位
热度指标
```

这些不合并成一个唯一值。分源保存：

```text
eastmoney_main_inflow
ths_main_inflow
tencent_main_inflow
```

## 6.3 主源失效时备用源接管

必须记录：

```text
source_switched = true
primary_source_failed = true
fallback_source = xxx
stale_reason = xxx
quality_flag = source_switched
```

禁止 silent switch。

---

# 7. 内存控制策略

通俗原则：

```text
不要一次把全市场、全历史、全字段读进 Pandas。
```

规则：

```text
按市场分批
按日期分批
按股票池分批
按字段选择读取
优先用 DuckDB SQL 聚合
只有小结果才转 Pandas
前端查询必须分页
Agent 查询必须限行
```

建议默认限制：

| 场景 | 建议限制 |
|---|---|
| 前端表格 | 默认 100-500 行分页 |
| Agent 查询 | 默认最多 200 行，特殊工具最多 2000 行 |
| Pandas 转换 | 只转换聚合后的小结果 |
| 分钟线查询 | 必须带 market、date_range 或 instrument_id |
| 全市场扫描 | 只允许后台任务，不允许前端直接触发 |

---

# 8. 磁盘空间控制策略

监控项：

```text
DuckDB 文件大小
Parquet 目录大小
raw 目录大小
files 目录大小
audit 日志大小
cache 大小
backups 大小
剩余磁盘空间
```

阈值建议：

| 磁盘使用率 | 动作 |
|---|---|
| > 70% | 提醒 |
| > 85% | 警告，停止非必要历史回补 |
| > 95% | 停止非核心抓取，只保留当天核心数据同步 |

清理顺序：

```text
1. cache
2. 旧日志压缩
3. 过旧临时 raw
4. 过旧非关键新闻快照
5. 旧备份按策略清理
```

公告、财报、审计日志、Parquet 历史归档默认不直接删除。

---

# 9. 查询性能规则

## 9.1 前端查询

规则：

```text
默认分页
默认最近 N 天
大表必须带日期条件
禁止 SELECT * FROM 大表不加 LIMIT
常用页面使用 snapshot 表
```

## 9.2 第三层和第四层性能

第三层产业链页面、第四层市场详情页不应每次动态 join 全库。推荐：

```text
industry_chain_daily_snapshot
market_index_snapshot
market_sector_snapshot
market_board_snapshot
market_detail_view
```

页面优先查 snapshot。需要下钻时，再按具体 chain_id / market_id / date_range 查询明细。

## 9.3 Agent 查询

Agent 不能自由 SQL。只能调用受控工具：

```text
get_market_summary(date)
get_chain_snapshot(chain_id, date)
get_market_detail(market_id, date)
get_stock_evidence(instrument_id, date_range)
get_data_quality_report(date)
```

每个工具都必须有：

```text
最大返回行数
默认日期范围
字段白名单
超时限制
只读权限
```

---

# 10. 备份与恢复

## 10.1 备份策略

| 对象 | 频率 | 说明 |
|---|---|---|
| DuckDB | 每日盘后 | 保存最近 7-14 份日备份 |
| Parquet | 每周 | 备份分区目录或同步到外部盘 |
| raw/files | 每周 | 公告和财报长期保留 |
| audit | 每周压缩 | 不直接删除 |
| schema.sql | 每次变更 | 进入版本控制 |
| configs | 每次变更 | 进入版本控制 |

## 10.2 恢复原则

```text
DuckDB 损坏 → 从 backup 恢复
标准表错误 → 从 raw / parquet 重建
文件丢失 → 从 backups/files 恢复
schema 错误 → 回退 schema.sql
某日数据错误 → BackfillJob 局部重跑
```

## 10.3 恢复演练

每月至少做一次小型恢复演练：

```text
复制备份 DuckDB 到临时目录
用 file_registry 检查文件路径是否存在
抽查几条公告 PDF、行情和 Layer 1 指标
运行 schema check 和 sample query
```

---

# 11. 日志与审计

必须保留：

```text
fetch_log.ndjson
source_conflict_log.ndjson
data_quality_log.ndjson
revision_log.ndjson
agent_report_log.ndjson
write_manager_log.ndjson
```

每条日志至少包含：

```text
timestamp
job_id
data_domain
source
status
row_count
error_message
elapsed_seconds
quality_flag
```

---

# 12. 健康检查与报警

每日检查：

```text
今日核心数据是否更新
是否有 source_conflict
是否有 schema_drift
是否有 long_stale 数据
是否有任务失败
DuckDB 是否备份成功
磁盘空间是否足够
Agent 日报是否生成
```

报警级别：

| 级别 | 示例 |
|---|---|
| INFO | 普通任务完成 |
| WARN | 某备用源失败、少量数据滞后 |
| ERROR | 主源失败、核心表缺失、严重冲突 |
| CRITICAL | DuckDB 写入失败、磁盘 > 95%、核心数据全量缺失 |

---


# 13. Layer 3 配置文件健康检查

Layer 3 已经从普通行业清单升级为“全球产业链资金震动锚点层”，并在 v1.6 执行方案B，补充功能节点、链内边与跨链传导边，因此运维中必须对配置文件做定期自检，避免前端或 Agent 把普通映射股误认为全球定价锚。

建议检查文件：

```text
specs/layer3_global_industry_chains_v1_2/
  layer3_global_industry_chain_registry.yaml
  layer3_anchor_registry.json
  references/source_registry.md
```

每日或每次配置变更后检查：

```text
1. chain_id 是否唯一
2. anchor_id 是否唯一或是否存在同名不同链的合理别名
3. 每条 chain 是否存在 chain_priority
4. 每个 anchor 是否存在 anchor_priority
5. 每条 chain 是否至少有一个 root node
6. 每条 chain 是否至少有 2 个功能节点
7. 每条 chain 是否至少有 1 条链内 edge
8. 每个 anchor.node_id 是否能在 node registry 中找到
9. cross-chain edge 的 from_node_id / to_node_id 是否都存在
10. private_company 是否 event_only=true
11. commodity/index 是否没有被误标为 public_equity
12. source_keys 是否能在 source_registry.md 中找到
13. P0 anchor 是否都有 source_keys 且 source_validation_status 不为 needs_source
14. source_validation_status 是否为空
15. event_only=true 的锚点是否没有进入普通行情抓取任务
```

通俗解释：这一步是为了防止第三层又退化成“股票池”。Layer 3 只说明“谁重要、为什么重要、会影响什么”；具体价格、成交量、成交额仍然从 Layer 5 读取。

异常处理：

```text
缺 chain_priority / anchor_priority：拒绝发布配置。
private_company 未设置 event_only=true：拒绝发布配置。
source_keys 缺失：允许发布，但 source_validation_status 必须标为 needs_source 或 event_only_needs_source。
root node 缺失：自动生成或拒绝发布。
功能节点或 edge 缺失：拒绝发布，防止 Layer 3 退回“只有股票池没有产业链关系”。
P0 anchor source_keys 缺失：拒绝发布，或降级为非 P0。
```

---
# 14. 每日 / 每周 / 每月运维清单

## 每日盘后

```text
1. 检查 IncrementalUpdateJob 是否成功
2. 检查 source_conflict 是否新增
3. 检查 data_quality_report
4. 检查 DuckDB 是否备份成功
5. 检查磁盘空间
6. 检查 Agent 日报是否生成
```

## 每周

```text
1. 压缩旧日志
2. 清理 cache
3. 检查 Parquet 分区是否正常
4. 检查数据库大小增长
5. 检查失败任务是否长期未修复
6. 抽查 raw 文件和 file_registry 是否一致
```

## 每月

```text
1. 做一次完整备份
2. 做一次恢复演练
3. 检查 schema drift 和 source endpoint 是否变化
4. 检查是否需要归档旧分钟线
5. 检查 Agent 工具是否存在超大查询
```

---

# 15. Claude Code / Codex 实现任务

1. 创建 `data/` 目录结构。
2. 实现 `DuckDBWriteManager` 单写规则。
3. 实现 `file_registry` 与本地文件索引。
4. 实现 `data_sync_job`、`source_conflict`、`revision_log` 表。
5. 实现 `DataSyncOrchestrator`。
6. 实现 `IncrementalUpdateJob` 和 `BackfillJob`。
7. 实现 `disk_usage_check.py`。
8. 实现 `duckdb_backup.py`。
9. 实现 `parquet_partition_check.py`。
10. 实现 `daily_health_check.py`。
11. 实现 Agent 查询限流与行数限制。
12. 实现每日/每周/月度运维报告生成。
13. 实现 Layer 3 配置文件健康检查。

---

# 16. 外部依据与参考资料

1. DuckDB 官方：并发模型。  
   https://duckdb.org/docs/current/connect/concurrency.html
2. DuckDB 官方：Parquet 读写。  
   https://duckdb.org/docs/current/data/parquet/overview.html
3. DuckDB 官方：Partitioned Writes。  
   https://duckdb.org/docs/current/data/partitioning/partitioned_writes.html
4. DuckDB 官方：Hive Partitioning。  
   https://duckdb.org/docs/current/data/partitioning/hive_partitioning.html
5. Airbyte 官方：Incremental Sync。  
   https://docs.airbyte.com/platform/connector-development/connector-builder-ui/incremental-sync
6. Dagster 官方：Backfilling data。  
   https://docs.dagster.io/guides/build/partitions-and-backfills/backfilling-data

---

# 17. 最终结论

本运维文件的核心是：

```text
DuckDB 管结构化数据；
本地文件系统管原始文件、审计、备份和归档；
Parquet 管大历史表；
日常默认增量更新；
回补、修订审计和冲突重抓单独处理；
写入单通道，读取多通道；
前端和 Agent 都不直接写库；
空间、内存、查询都必须有限制；
每日、每周、每月都要有检查清单。
```

这份文件可直接作为 `docs/ops_and_performance_v1_2.md` 交给 Claude Code / Codex 实现。
