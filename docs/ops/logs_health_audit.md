# 日志、健康检查与审计

> 文件定位：日志与审计实现文件。所有关键任务必须可追踪、可复盘、可解释，但日志不能无限增长。

---

# 1. 日志目录

```text
data/audit/
  fetch_log.ndjson
  data_quality_log.ndjson
  source_conflict_log.ndjson
  revision_log.ndjson
  write_audit_log.ndjson
  resource_guard_log.ndjson
  agent_run_log.ndjson
  notification_log.ndjson
  ops_health_log.ndjson
```

---

# 2. 日志通用字段

```json
{
  "event_id": "uuid",
  "event_time": "2026-06-16T18:00:00",
  "event_type": "FETCH_SUCCESS",
  "severity": "INFO",
  "module": "data_sources",
  "run_id": "run_20260616_001",
  "job_id": "incremental_daily",
  "task_id": "fetch_cn_a_daily",
  "message": "string",
  "detail": {},
  "quality_flags": []
}
```

---

# 3. 严重级别

```text
DEBUG: 仅开发环境
INFO: 正常事件
WARN: 可恢复异常
ERROR: 任务失败或数据不可用
CRITICAL: 可能破坏数据或影响系统安全退出
```

默认生产/本机运行不写 DEBUG。

---

# 4. 日志保留策略

| 日志 | 热保留 | 压缩保留 | 删除策略 |
|---|---:|---:|---|
| fetch_log | 30 天 | 180 天 | 超过后可归档 |
| data_quality_log | 90 天 | 1 年 | 不直接删除，先压缩 |
| source_conflict_log | 1 年 | 长期 | 默认不删除 |
| revision_log | 1 年 | 长期 | 默认不删除 |
| write_audit_log | 1 年 | 长期 | 默认不删除 |
| resource_guard_log | 90 天 | 1 年 | 可压缩 |
| agent_run_log | 90 天 | 1 年 | 可压缩 |
| notification_log | 90 天 | 1 年 | 可压缩 |

日志压缩触发：

```text
data/audit > 1GB 或每周检查
```

---

# 5. Health Summary

每日生成：

```text
health_summary
```

字段：

```text
as_of_date
resource_status
sync_status
source_status_summary
data_quality_summary
source_conflict_summary
backup_status
manual_review_count
latest_report_status
```

---

# 6. 审计边界

必须写审计：

```text
任何 clean table 写入
任何 schema migration
任何 source switch
任何 fallback 接管
任何严重 source_conflict
任何 manual review
任何 Agent 输出入 staging
任何通知发送
任何备份恢复
```

---

# 7. 日志不能导致系统不可用

如果日志写入失败：

```text
1. 尝试写 emergency_log
2. 若 emergency_log 也失败，停止非核心任务
3. 不允许继续写 clean table
```

---

# 8. CLI

```bash
python -m quant_monitor.ops.logs --summary
python -m quant_monitor.ops.logs --compress --older-than 30d
python -m quant_monitor.ops.logs --audit-check
python -m quant_monitor.ops.logs --export-health-summary
```

---

# 9. 验收测试

```text
所有 clean 写入有 write_audit_log
source switch 有日志
fallback 接管有日志
Agent 输出有 agent_run_log
日志压缩不会删除 source_conflict_log 正式记录
日志目录超过 1GB 会触发 WARN
日志写入失败会阻止继续写 clean table
```
