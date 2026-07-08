# 运行时链路

> 文件定位：系统运行场景实现文件。本文描述每日、盘中、回补、冲突、报告、恢复等关键运行链路。  
> 原则：本机友好、低资源占用、可暂停、可恢复、可审计。

---

# 1. 总运行链路

```text
Scheduler / CLI / User Request
  → ResourceGuard
  → DataSyncOrchestrator
  → Fetcher / Adapter
  → Raw Store / File Lake
  → Staging Table
  → DataQualityValidator
  → SourceConflictValidator
  → DuckDBWriteManager
  → Clean Table / Snapshot Table / Audit Log
  → FastAPI ReadOnlyRepository
  → Frontend / Agent Tools / Reports
```

---

# 2. 每日盘后链路

```text
1. ResourceGuard 检查本机资源
2. IncrementalUpdateJob 拉取新增行情、公告、财务、跨资产数据
3. 写 raw / staging
4. DataQualityValidator 检查
5. SourceConflictValidator 检查关键字段
6. WriteManager 写 clean table
7. 生成 Layer 1-5 snapshot
8. 生成 data_health_summary
9. 生成 daily report
10. 轻量备份 DuckDB
```

资源限制：

```text
默认 eco 模式
不执行大范围 backfill
不做全历史多源审计
不做完整 Parquet 复制
```

---

# 3. 盘中轻量链路

```text
1. 只抓 P0 watchlist / 核心指数 / 核心期货 / Layer 3 P0 anchors
2. 只更新 latest snapshot
3. 不重算长期 rolling features
4. 只触发轻量提醒
5. 前端读取 snapshot
```

盘中禁止：

```text
FullLoad
大范围 Backfill
全市场分钟线扫描
完整报告重生成
```

---

# 4. Layer 1 更新链路

```text
AxisSpecLoader
  → source registry
  → fetch axis observation
  → validate freshness / lag / source switch
  → write axis_observation
  → compute axis_feature_snapshot
  → generate axis_interpretation_snapshot
```

窗口不足时：

```text
state_bucket = insufficient_history
warning_type = historical_insufficient
不生成极端判断
```

---

# 5. Layer 3 更新链路

```text
Layer3SpecValidator
  → Layer3RegistryLoader
  → Layer3GraphBuilder
  → Layer 5 latest mapping
  → industry_chain_daily_snapshot
  → frontend graph view
```

Layer 3 只保存关系、锚点身份、传导逻辑和每日快照，不保存全量历史行情。

---

# 6. 数据冲突链路

```text
SourceConflictValidator 发现严重冲突
  → 写 source_conflict
  → ReconcileJob 重抓 primary / validation source
  → 重新标准化
  → 再次比较
  → 仍冲突：manual_review_required=true
```

禁止自动覆盖严重冲突字段。

---

# 7. 回补链路

```text
User / RevisionAudit / Failed Task 触发 Backfill Request
  → ResourceGuard 检查
  → 拆成 market + date_range + data_domain + instrument_id 分区任务
  → 限制 batch size
  → 写 staging
  → validate / conflict check
  → WriteManager merge
  → 局部重建受影响 snapshot
```

回补默认不超过：

```text
5 个交易日窗口
eco 模式 1 个任务并发
磁盘剩余 < 20GB 时暂停
系统可用内存 < 2GB 时暂停
```

---

# 8. 报告链路

```text
Snapshot tables
  → Agent tools read context
  → Agent structured output staging
  → No Action Semantics Guard
  → ReportBuilder
  → report_registry / report_section
  → notification queue
```

Agent 不直接发布报告，不直接写 clean table。

---

# 9. API 链路

```text
Frontend Request
  → FastAPI Router
  → Query Params Validation
  → ReadOnlyRepository
  → Snapshot / Clean Table
  → Response Envelope
```

如果查询过大：

```text
返回 QUERY_TOO_LARGE
建议缩小范围或提交后台任务
```

---

# 10. 备份恢复链路

```text
BackupManager
  → wait WriteManager idle
  → checkpoint DuckDB
  → copy db
  → hash manifest
  → prune old backups
```

恢复链路：

```text
stop scheduler
stop write requests
backup current broken state
verify target backup
restore DuckDB / specs / config
smoke test
start readonly API
human confirm
start scheduler
```

---

# 11. ResourceGuard 介入点

ResourceGuard 在以下位置必须检查：

```text
任务开始前
每个 batch 开始前
写入 clean table 前
生成大 snapshot 前
报告生成前
备份前
```

触发 PAUSE 时：

```text
停止非核心任务
保留已有 staging
不删除 raw
写 resource_guard_log
前端继续读取旧 snapshot
```

---

# 12. 运行时验收测试

```text
每日链路不会触发全量回补
盘中链路不会全市场扫描
严重 source conflict 不会自动覆盖 clean table
ResourceGuard PAUSE 后旧 snapshot 仍可读
Backfill 可以从失败 task 继续
报告链路通过 no_action_semantics_guard
恢复链路能通过 smoke test
```

---

# 12. 盘中提醒链路

```text
IntradayLightJob
  → ResourceGuard
  → 读取 P0 watchlist / P0 anchors / 核心市场结构 snapshot
  → AlertRuleEngine
  → dedup_key 去重
  → cooldown / throttle
  → alert_event staging
  → NoActionSemanticGuard
  → WriteManager
  → dashboard_notification / local_audit_log / optional channel
```

盘中提醒不触发：

```text
FullLoad
全历史 Backfill
策略级回测
完整日报重生成
```

ResourceGuard 处于 PAUSE / STOP_NON_CORE 时，只允许 DATA_RISK / OPS_RISK 提醒。

---

# 13. 回测与复盘链路

```text
User selects scenario
  → ResourceGuard estimates scan size / memory / date range
  → BacktestScenarioLoader
  → BacktestEventBuilder
  → BacktestDataLoader reads snapshot / Parquet / evidence_chain
  → BacktestMetricEngine
  → BacktestReportBuilder
  → WriteManager writes backtest_run_log / metric_snapshot / report
  → Frontend BacktestReviewPage
```

回测必须用户显式触发，不在盘中自动运行。回测报告必须包含 limitations，不得输出交易动作。
