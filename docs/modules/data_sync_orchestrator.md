# 数据同步模块

> 拆分说明：本文件由 `quant_monitor_design_document_v1_6.md` 拆分生成；当前步骤只做结构拆分与明显版本/编号残留修正，不删减原有细节。
> 来源：第 12 章

# 12. 数据同步模块：全量、增量、回补、修订审计、冲突重抓

## 12.1 总体原则

数据抓取对用户表现为一个“数据同步模块”，但代码内部必须解耦为多类任务，避免把初始化、日常更新、失败回补和多源冲突处理混成一个函数。

```text
DataSyncOrchestrator
├── FullLoadJob
├── IncrementalUpdateJob
├── BackfillJob
├── RevisionAuditJob
├── ReconcileJob
└── DataQualityJob
```

## 12.2 FullLoadJob：初始化全量抓取

只在第一次建库或重大重建时运行。任务包括：股票列表、市场日历、历史日线、复权因子、基础财务、Layer 1 五轴历史、Layer 2 跨资产历史、Layer 3/4 基础映射。

## 12.3 IncrementalUpdateJob：日常增量更新

日常默认只抓新增或变化数据，不每天全量重抓。每次运行先读取本地最新 `trade_date`、`as_of_timestamp`、`content_hash` 或数据源 cursor，再只补缺失部分。

## 12.4 BackfillJob：缺失与失败回补

用于网络失败、数据源延迟、节假日错位、公告 PDF 后补、复权因子变化、财报修订等情况。Backfill 按市场、日期、标的、数据域分区执行，不做无差别全量重抓。

## 12.5 RevisionAuditJob：历史修订审计

用于检测数据源对历史数据的回填或修订。核心方法是记录 `content_hash`、`schema_hash`、`revision_id`、`fetch_time`，若发现同一观测日期的内容变化，则写入 revision log 并触发局部重算。

## 12.6 ReconcileJob：多源冲突重抓

当 `source_conflict` 出现严重冲突时，ReconcileJob 会重新抓取主源与备用源，重新标准化后再判断。若仍无法解决，才进入人工确认。

## 12.7 data_sync_job 表

```sql
CREATE TABLE IF NOT EXISTS data_sync_job (
    job_id          VARCHAR PRIMARY KEY,
    job_type        VARCHAR, -- full_load / incremental / backfill / revision_audit / reconcile
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
```

---

---

# 13. P0 扩展：DataSyncOrchestrator 实现规格

> 本节为第一轮扩展新增内容，不删除上方原始拆分内容。  
> 目标：把同步模块扩展为可实现的任务状态机、CLI、调度策略、失败恢复和审计协议。

## 13.1 模块职责

DataSyncOrchestrator 是后台任务总控，不负责具体抓取实现，也不直接写 clean 表。

它负责：

```text
1. 根据调度计划创建 job。
2. 根据 data_domain 选择 adapter。
3. 管理 FullLoad / Incremental / Backfill / RevisionAudit / Reconcile / DataQualityJob。
4. 维护 job 状态机。
5. 控制任务重试、跳过、失败、人工确认。
6. 把 Adapter 输出交给 Validation 和 WriteManager。
7. 写入 data_sync_job、fetch_log、job_event_log。
```

不负责：

```text
1. 不直接解析所有数据源细节。
2. 不直接写 clean 表。
3. 不绕过 DataQualityValidator。
4. 不替代 ReconcileJob 的多源比较逻辑。
```

---

## 13.2 任务状态机

```text
CREATED
  ↓
PLANNED
  ↓
FETCHING
  ↓
STAGED
  ↓
VALIDATING
  ↓
WAITING_RECONCILE ──→ RECONCILING
  ↓                      ↓
READY_TO_WRITE ←─────────
  ↓
WRITING
  ↓
COMPLETED
```

异常状态：

```text
FAILED_RETRYABLE
FAILED_FINAL
SKIPPED
CANCELLED
MANUAL_REVIEW_REQUIRED
```

### 状态含义

| 状态                     | 含义                              |
| ------------------------ | --------------------------------- |
| `CREATED`                | job 已创建但未展开任务            |
| `PLANNED`                | 已确定数据域、日期、标的、adapter |
| `FETCHING`               | 正在抓取 raw 数据                 |
| `STAGED`                 | 已写入 staging 或 temp parquet    |
| `VALIDATING`             | 正在质量检查或冲突检查            |
| `WAITING_RECONCILE`      | 发现严重冲突，等待重抓            |
| `READY_TO_WRITE`         | 可以交给 WriteManager             |
| `WRITING`                | 正在写 clean / snapshot           |
| `COMPLETED`              | 完成                              |
| `MANUAL_REVIEW_REQUIRED` | 需要人工确认                      |

---

## 13.3 job_id / run_id / task_id

```text
run_id  = 一次调度运行的总 ID
job_id  = 一类数据同步任务 ID
task_id = job 下具体分片任务 ID
```

示例：

```text
run_id  = RUN_20260616_DAILY_CLOSE
job_id  = JOB_20260616_CN_A_DAILY_BAR_INCREMENTAL
task_id = TASK_20260616_CN_A_DAILY_BAR_0001
```

规则：

```text
1. run_id 贯穿 fetch / validate / write / report。
2. job_id 对应 data_sync_job。
3. task_id 用于大任务分片。
4. 所有日志必须至少包含 run_id 和 job_id。
```

---

## 13.4 任务类型详细流程

### 13.4.1 FullLoadJob

用于初始化或重大重建。

```text
1. 读取 market_registry / source_registry。
2. 创建 full_load run_id。
3. 分 data_domain 生成 job。
4. 分 market / date_range / instrument 分片。
5. 调用 adapter fetch。
6. 写 raw 与 staging。
7. 运行 DataQualityValidator。
8. 对关键字段运行 SourceConflictValidator。
9. 通过后调用 WriteManager。
10. 生成 full_load_report。
```

FullLoad 必须支持断点续跑。

### 13.4.2 IncrementalUpdateJob

日常默认任务。

```text
1. 读取 clean 表最新 trade_date / as_of_timestamp。
2. 读取 source cursor 或 last_success_time。
3. 根据交易日历计算待更新窗口。
4. 只抓新增或变化数据。
5. 写 staging。
6. 校验、冲突检查、写入。
7. 更新 cursor。
8. 生成 incremental_report。
```

### 13.4.3 BackfillJob

用于缺失、失败、修订、人工指定范围。

```text
1. 接收 market + data_domain + date_range + instrument_id。
2. 检查回补范围是否过大。
3. 大范围任务自动拆分。
4. 抓取指定范围。
5. 校验和写入。
6. 标记 affected_snapshot 需要重算。
```

Backfill 必须写明触发原因：

```text
network_failure
source_lag
missing_partition
corporate_action_update
revision_detected
manual_request
```

### 13.4.4 RevisionAuditJob

用于发现历史数据被源头修订。

```text
1. 选取需要审计的 data_domain。
2. 重抓小范围历史样本或官方修订窗口。
3. 比较 content_hash / schema_hash / revision_id。
4. 若变化，写 revision_log。
5. 创建 BackfillJob。
6. 标记受影响 feature / snapshot 需要重算。
```

### 13.4.5 ReconcileJob

用于严重多源冲突。

```text
1. 读取 source_conflict。
2. 重抓 primary 与 validation 源。
3. 重新标准化单位、时间、复权口径。
4. 再次比较。
5. 若解决，更新 conflict 状态。
6. 若仍冲突，manual_review_required=true。
```

### 13.4.6 DataQualityJob

可独立运行，用于抽样审计或定期检查。

```text
1. 检查 clean 表主键重复。
2. 检查价格/成交量范围。
3. 检查日期连续性。
4. 检查 snapshot 新鲜度。
5. 检查 file_registry 路径有效性。
```

---

## 13.5 data_sync_job 扩展表

```sql
CREATE TABLE IF NOT EXISTS data_sync_job (
    job_id              VARCHAR PRIMARY KEY,
    run_id              VARCHAR,
    job_type            VARCHAR,
    data_domain         VARCHAR,
    market_id           VARCHAR,
    instrument_id       VARCHAR,
    partition_key       VARCHAR,
    date_start          DATE,
    date_end            DATE,
    source_id           VARCHAR,
    adapter_id          VARCHAR,
    status              VARCHAR,
    priority            INTEGER,
    retry_count         INTEGER,
    max_retries         INTEGER,
    watermark_before       VARCHAR,
    watermark_after        VARCHAR,
    validation_report_id VARCHAR,
    conflict_report_id  VARCHAR,
    write_id            VARCHAR,
    error_type          VARCHAR,
    error_message       TEXT,
    created_at          TIMESTAMP,
    started_at          TIMESTAMP,
    finished_at         TIMESTAMP,
    updated_at          TIMESTAMP
);
```

### job_event_log

```sql
CREATE TABLE IF NOT EXISTS job_event_log (
    event_id        VARCHAR PRIMARY KEY,
    run_id          VARCHAR,
    job_id          VARCHAR,
    task_id         VARCHAR,
    event_type      VARCHAR,
    old_status      VARCHAR,
    new_status      VARCHAR,
    message         TEXT,
    payload_json    TEXT,
    created_at      TIMESTAMP
);
```

---

## 13.6 调度计划

| 任务                   | 建议频率           | 说明                        |
| ---------------------- | ------------------ | --------------------------- |
| CN_A daily bar         | A 股收盘后         | 日线与复权                  |
| US_EQ daily bar        | 美股收盘后         | 美股/ETF/锚点               |
| Layer 1 axis           | 按指标频率         | 日频、周频、月频分别调度    |
| Layer 2 sensors        | 每日               | 跨资产快照                  |
| Layer 3 config check   | 每日或每次配置变更 | 校验 chain/node/edge/anchor |
| Layer 3 daily snapshot | 每日               | 读取 Layer 5 最新行情与事件 |
| Backfill               | 按需               | 手动或系统触发              |
| RevisionAudit          | 每周/每月          | 视数据源修订风险            |
| DuckDB backup          | 每日盘后           | 写入完成后                  |

---

## 13.7 CLI 设计

```bash
# 初始化全量
python -m quant_monitor.sync full-load --domain market_bar_1d --market CN_A --start 2015-01-01

# 日常增量
python -m quant_monitor.sync incremental --profile daily_close

# 指定回补
python -m quant_monitor.sync backfill --domain market_bar_1d --market CN_A --start 2026-06-01 --end 2026-06-15

# 修订审计
python -m quant_monitor.sync revision-audit --domain corporate_action --market CN_A --lookback-days 90

# 冲突重抓
python -m quant_monitor.sync reconcile --conflict-id CONFLICT_20260616_001

# 质量检查
python -m quant_monitor.sync quality-check --domain layer3 --date 2026-06-16
```

---

## 13.8 错误分类

| error_type               |       是否重试 | 说明                  |
| ------------------------ | -------------: | --------------------- |
| `NETWORK_TIMEOUT`        |             是 | 网络超时              |
| `RATE_LIMITED`           |       延迟重试 | 限流                  |
| `AUTH_FAILED`            |             否 | 授权失败              |
| `SCHEMA_DRIFT`           |             否 | 字段结构变化          |
| `EMPTY_RESPONSE`         |         视情况 | 可能未发布或源异常    |
| `VALIDATION_FAILED`      |             否 | 质量检查失败          |
| `SOURCE_CONFLICT_SEVERE` | 进入 Reconcile | 多源严重冲突          |
| `WRITE_FAILED`           |         视情况 | 写入失败，需 rollback |
| `DISK_SPACE_LOW`         |             否 | 磁盘不足              |

---

## 13.9 断点续跑

每个 job 必须能从以下位置恢复：

```text
1. raw 文件已抓但 staging 未写。
2. staging 已写但 validation 未跑。
3. validation 已通过但 write 未执行。
4. write 失败但事务已 rollback。
5. 部分 task 完成，其他 task 失败。
```

断点续跑优先使用：

```text
run_id
job_id
task_id
raw_file_paths
staging_table
watermark_before/watermark_after
write_audit_log
```

---

## 13.10 与其他模块关系

| 模块                              | 关系                            |
| --------------------------------- | ------------------------------- |
| `data_sources.md`                 | 提供 adapter 与 source registry |
| `duckdb_and_parquet.md`           | 提供表结构和归档规则            |
| `data_validation_and_conflict.md` | 校验 staging 数据               |
| `write_manager.md`                | 完成最终写入                    |
| `ops_and_performance.md`          | 定义调度、备份、健康检查        |
| `fastapi_backend.md`              | 读取任务状态和数据健康          |

---

## 13.11 验收测试

| 测试                   | 预期                                     |
| ---------------------- | ---------------------------------------- |
| incremental 重复运行   | 不产生重复主键                           |
| adapter 网络失败       | job 进入 FAILED_RETRYABLE，写 error_type |
| schema drift           | 停止写入，进入人工/适配器更新            |
| backfill 大日期范围    | 自动拆分 task                            |
| source conflict severe | 创建 ReconcileJob，不写 clean            |
| WriteManager rollback  | job 标记失败但 clean 表无半写入          |
| 断点续跑               | 已完成 task 不重复写                     |
| 手动取消               | 状态为 CANCELLED，保留审计               |

---

## 13.12 Runner fetch 入口正式边界

`IncrementalJobRunner`、`BackfillShardRunner`、`FullLoadJobRunner`、`ReconcileJobRunner`、pipeline contract、backfill validate/write 与 reconcile re-fetch 都必须服务同一条正式抓取入口。生产 runner 的 fetch 入口必须从“直接传 adapter”收敛为：

```text
Sync runner
  → DataSourceService.fetch / narrow fetch callable
  → SourceRoutePlan
  → SourceCapabilityRegistry
  → ResourceGuard
  → internal adapter factory
```

新增设计权威：

- `docs/modules/datasource_service.md`
- `docs/modules/source_route_plan.md`
- `specs/contracts/datasource_service_contract.yaml`
- `specs/contracts/source_route_contract.yaml`

正式业务实现不得通过 runner 直传 adapter 绕过 `DataSourceService`、`SourceRoutePlan`、capability、ResourceGuard 或 route/audit 记录。adapter 直传只允许作为单元测试隔离外部 I/O 的测试 helper，不得出现在产品 CLI、production-equivalent acceptance、指标全链路验收或正式 clean 写入路径中。
