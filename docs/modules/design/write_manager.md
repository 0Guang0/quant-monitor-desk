# WriteManager 写入管理模块

> 扩展轮次：P0 第一轮模块扩展。  
> 模块定位：系统唯一标准写入口。任何 clean 表、snapshot 表、audit 表写入都必须通过 WriteManager 或其受控子类执行。  
> 边界：前端、Agent、研究脚本、临时 notebook、数据源 adapter 均不得绕过 WriteManager 写主库。

---

## 1. 模块目标

WriteManager 解决的是“数据可信写入”问题，而不是“如何抓数据”。

它必须保证：

```text
1. 所有写入先进入 staging。
2. 所有写入必须经过 DataQualityValidator。
3. 关键字段必须经过 SourceConflictValidator。
4. clean 表只接受通过校验的数据。
5. 写入过程可回滚、可审计、可复盘。
6. DuckDB 始终保持单写边界。
7. 任何 source switch、fallback、manual review 都有记录。
8. clean 写入必须区分 primary-grade clean 与 degraded clean，不允许降级数据伪装成正常主源数据。
```

---

## 2. 总体链路

```text
Fetcher / SyncJob / FactorJob / SnapshotJob
        ↓
raw files / temp parquet
        ↓
staging table
        ↓
DataQualityValidator
        ↓
SourceConflictValidator
        ↓
WriteManager
        ↓
clean table / snapshot table / audit table
```

WriteManager 不是校验器本身，但它必须检查校验结果是否允许写入。

---

## 3. 组件划分

```text
WriteManager
├── DuckDBConnectionManager
├── StagingWriter
├── ValidationGate
├── MergePlanner
├── TransactionRunner
├── AuditLogger
├── RollbackHandler
└── WriteLockManager
```

| 组件                    | 职责                                           |
| ----------------------- | ---------------------------------------------- |
| DuckDBConnectionManager | 创建唯一可写连接，提供只读连接工厂             |
| StagingWriter           | 把标准化后的批次写入 staging                   |
| ValidationGate          | 检查质量和冲突结果是否允许写入                 |
| MergePlanner            | 根据主键生成 insert/update/delete/replace 计划 |
| TransactionRunner       | 事务执行与回滚                                 |
| AuditLogger             | 记录写入审计                                   |
| RollbackHandler         | 失败恢复和 staging 保留                        |
| WriteLockManager        | 防止多个进程同时写同一个 DuckDB 文件           |

---

## 4. 写入模式

| write_mode          | 用途                       | 是否允许覆盖 | 说明                    |
| ------------------- | -------------------------- | -----------: | ----------------------- |
| `append_only`       | 日志、审计、事件           |           否 | 不更新旧行              |
| `upsert_by_pk`      | 行情、指标观测、snapshot   |           是 | 按主键更新              |
| `replace_partition` | 某市场某日、某轴某窗口重算 |           是 | 删除分区后重写          |
| `manual_patch`      | 人工确认后的少量修正       |           是 | 必须写 patch reason     |
| `schema_migration`  | 表结构变更                 |         特殊 | 必须走 migration runner |

禁止：

```text
1. 研究脚本直接 INSERT clean 表。
2. Agent 直接生成 SQL 修改表。
3. 前端 API 直接写 DuckDB。
4. 多进程同时 read-write 连接同一个 DuckDB 文件。
5. validation_status != PASSED 时写 clean 表。
```

---

## 5. 输入契约

WriteManager 接受的输入必须包含：

```yaml
write_request:
  run_id: string
  job_id: string
  target_table: string
  staging_table: string
  write_mode: append_only | upsert_by_pk | replace_partition | manual_patch
  data_domain: string
  primary_keys: [string]
  partition_keys: [string]
  validation_report_id: string
  conflict_report_id: string | null
  source_used: string
  source_role: primary | validation | fallback
  source_switched: boolean
  quality_flags: string
  stale_reason: string | null
  allow_partial_write: false
  requested_by: sync_job | backfill_job | revision_audit_job | human
```

### 5.1 必填字段

| 字段                   | 为什么必填                                   |
| ---------------------- | -------------------------------------------- |
| `run_id`               | 串联一次任务全过程                           |
| `job_id`               | 对应 data_sync_job                           |
| `target_table`         | 明确写入目标                                 |
| `staging_table`        | 只能从 staging 写入                          |
| `write_mode`           | 确定 merge 策略                              |
| `primary_keys`         | 防止重复与错写                               |
| `validation_report_id` | 确保质量检查已完成                           |
| `source_used`          | 可追溯                                       |
| `source_role`          | 区分 primary-grade 与 degraded/fallback 写入 |
| `source_switched`      | 明确是否发生主源切换                         |

### 5.2 降级写入输入要求

当写入不是正常 Primary，而是 `FallbackPolicy` 授权后的降级数据时，WriteManager 必须要求：

```text
source_role = fallback
source_switched = true
quality_flags 包含 SOURCE_FALLBACK_USED
若使用 Validation 源，还必须包含 VALIDATION_SOURCE_USED
stale_reason 或 fallback_reason 非空
route/audit payload 能说明 primary_source_failed=true 以及失败原因
```

禁止：

```text
1. source_role=validation 直接写 normal clean。
2. source_switched=true 但缺少 stale_reason / fallback_reason。
3. 使用 Validation 源降级写入却缺少 FallbackPolicy 授权证据。
4. 把 degraded clean 暴露给下游时不带 quality_flags。
```

---

## 6. ValidationGate 规则

写入前必须读取质量和冲突报告。

| 条件                                       |                                  是否允许写入 |
| ------------------------------------------ | --------------------------------------------: |
| `validation_status = PASSED`               |                                          允许 |
| `validation_status = WARNING` 且无严重冲突 |                      允许，但写 quality_flags |
| `validation_status = FAILED`               |                                          禁止 |
| `source_conflict.severity = severe`        |                                          禁止 |
| `manual_review_required = true`            |                       禁止，除非 manual_patch |
| `schema_hash_changed = true` 且未确认      |                                          禁止 |
| `stale_reason` 非空但允许 fallback         | 允许，但必须写 source_switched / stale_reason |

ValidationGate 的最终状态应能区分：

```text
PASSED_PRIMARY      正常主源写入，可作为 primary-grade clean
PASSED_DEGRADED     FallbackPolicy 授权后的降级写入，可读但必须带降级语义
FAILED              不允许写 clean
MANUAL_REVIEW_REQUIRED 只允许 manual_patch 或进入人工复核
```

---

## 7. Upsert 模板

DuckDB 可使用 `INSERT OR REPLACE` 或先删除分区再插入，具体方式按表选择。

### 7.1 append_only

```sql
INSERT INTO target_table
SELECT * FROM staging_table;
```

### 7.2 upsert_by_pk

推荐显式删除冲突主键后插入，避免字段缺省造成隐性覆盖。

```sql
DELETE FROM target_table t
USING staging_table s
WHERE t.instrument_id = s.instrument_id
  AND t.trade_date = s.trade_date;

INSERT INTO target_table
SELECT * FROM staging_table;
```

### 7.3 replace_partition

```sql
DELETE FROM target_table
WHERE market_id = $market_id
  AND trade_date BETWEEN $start_date AND $end_date;

INSERT INTO target_table
SELECT * FROM staging_table;
```

replace_partition 只能用于明确分区，不允许无条件全表替换。

---

## 8. 事务与回滚

### 8.1 标准事务流程

```text
1. acquire write lock
2. begin transaction
3. verify staging row count
4. verify validation report
5. execute merge plan
6. verify target row count delta
7. write audit log
8. commit
9. release write lock
```

### 8.2 失败处理

```text
1. rollback transaction
2. 保留 staging 表或 temp parquet
3. 写 write_audit_log(status=FAILED)
4. 写 error_message 与 traceback_digest
5. 标记 data_sync_job(status=FAILED)
6. 按 job policy 判断是否 retry
```

---

## 9. 并发与连接规则

### 9.1 单写连接

```text
只有 WriteManager 持有 read-write DuckDB 连接。
FastAPI 默认只读。
Agent 默认只读。
研究脚本默认只读。
```

### 9.2 多读连接

只读服务使用：

```python
import duckdb
con = duckdb.connect("data/duckdb/quant_monitor.duckdb", read_only=True)
```

### 9.3 锁策略

建议本地文件锁：

```text
data/duckdb/quant_monitor.write.lock
```

锁内容：

```json
{
  "run_id": "...",
  "job_id": "...",
  "pid": 12345,
  "started_at": "2026-06-16T10:00:00",
  "target_table": "security_bar_1d"
}
```

如果锁超过超时时间，不能自动删除，必须先检查进程是否还在运行。

---

## 10. 审计表

```sql
CREATE TABLE IF NOT EXISTS write_audit_log (
    write_id            VARCHAR PRIMARY KEY,
    run_id              VARCHAR,
    job_id              VARCHAR,
    target_table        VARCHAR,
    staging_table       VARCHAR,
    write_mode          VARCHAR,
    primary_keys        VARCHAR,
    partition_keys      VARCHAR,
    rows_in_staging     INTEGER,
    rows_inserted       INTEGER,
    rows_updated        INTEGER,
    rows_deleted        INTEGER,
    rows_rejected       INTEGER,
    validation_status   VARCHAR,
    conflict_status     VARCHAR,
    source_used         VARCHAR,
    source_role         VARCHAR,
    source_switched     BOOLEAN,
    stale_reason        VARCHAR,
    started_at          TIMESTAMP,
    finished_at         TIMESTAMP,
    status              VARCHAR,
    error_message       TEXT,
    traceback_digest    VARCHAR
);
```

---

## 11. Python 接口契约

```python
from dataclasses import dataclass
from typing import Literal

WriteMode = Literal["append_only", "upsert_by_pk", "replace_partition", "manual_patch"]

@dataclass(frozen=True)
class WriteRequest:
    run_id: str
    job_id: str
    target_table: str
    staging_table: str
    write_mode: WriteMode
    data_domain: str
    primary_keys: list[str]
    partition_keys: list[str]
    validation_report_id: str
    conflict_report_id: str | None
    source_used: str
    source_role: str
    allow_partial_write: bool = False
    requested_by: str = "sync_job"

class DuckDBWriteManager:
    def write(self, request: WriteRequest) -> str:
        """Return write_id after successful commit."""
        self.acquire_lock(request)
        try:
            self.begin()
            self.validation_gate(request)
            plan = self.build_merge_plan(request)
            stats = self.execute_plan(plan)
            write_id = self.write_audit(request, stats, status="COMMITTED")
            self.commit()
            return write_id
        except Exception as exc:
            self.rollback()
            self.write_audit(request, None, status="FAILED", error=exc)
            raise
        finally:
            self.release_lock(request)
```

---

## 12. 测试清单

| 测试                                  | 预期                                                          |
| ------------------------------------- | ------------------------------------------------------------- |
| staging 表缺失                        | 拒绝写入                                                      |
| validation_report 不存在              | 拒绝写入                                                      |
| severe conflict                       | 拒绝写入                                                      |
| upsert 主键重复                       | 写入后 clean 表无重复主键                                     |
| replace_partition                     | 仅目标分区被替换                                              |
| 事务中途失败                          | clean 表无半写入                                              |
| 多个写入同时启动                      | 只有一个获取 write lock                                       |
| Agent 尝试写入                        | 被工具层拒绝                                                  |
| source_switched=true                  | audit 和 clean 表质量字段可追溯                               |
| degraded clean                        | source_role=fallback 且 quality_flags 含 SOURCE_FALLBACK_USED |
| Validation 源未经 FallbackPolicy 授权 | 不得写 clean 主值                                             |

---

## 13. 与其他模块关系

| 模块                              | 关系                              |
| --------------------------------- | --------------------------------- |
| `duckdb_and_parquet.md`           | 定义表和存储边界                  |
| `data_validation_and_conflict.md` | 输出 validation / conflict report |
| `data_sync_orchestrator.md`       | 调用 WriteManager                 |
| `data_sources.md`                 | 提供 source_used / source_role    |
| `fastapi_backend.md`              | 只读，不直接写                    |
| `agent_module.md`                 | 只读，不直接写                    |

---

## 14. 官方依据与工程注记

DuckDB 官方并发说明支持当前“单写多读”的架构边界：read-write 模式适合一个进程读写数据库，read-only 模式允许多个进程读取但不写入。该约束不是可选优化，而是本系统防止数据库损坏和写入竞态的底层规则。

---

## 15. 标准链路短句

本模块的统一短句为：

```text
staging → validation → WriteManager → clean table
```

任何实现、测试、日报与运维说明都应使用这一链路表达，避免出现“直接写 clean 表”的歧义。
