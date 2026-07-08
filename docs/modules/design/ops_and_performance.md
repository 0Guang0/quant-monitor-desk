# 运维与性能模块

> 权威定位：本文件是运维模块的实现级入口文档。详细历史内容保留在 `docs/ops/ops_and_performance_v1_2.md`，本文件负责把运维能力拆成可实现的脚本、检查项、错误码、告警和恢复流程。

---

# 1. 模块目标

运维模块负责让系统长期稳定运行，重点不是追求复杂，而是做到：

```text
能启动
能检查
能备份
能恢复
能发现数据源异常
能发现磁盘/内存/查询性能问题
能解释失败原因
能给用户人工确认清单
```

---

# 2. 运维范围

```text
本地目录初始化
DuckDB 备份与恢复
Parquet 分区检查
raw/files/audit/cache/backups 目录检查
DataSync 任务状态检查
DataQuality 与 SourceConflict 检查
Layer 3 配置健康检查
API 健康检查
前端资源健康检查
Agent run log 检查
日报/通知检查
磁盘空间与内存边界检查
```

---

# 3. 运维脚本清单

建议实现这些 CLI：

```bash
python -m qm ops init-directories
python -m qm ops health-check --date 2026-06-15
python -m qm ops backup-duckdb
python -m qm ops restore-duckdb --backup data/backups/daily/xxx.duckdb
python -m qm ops check-parquet-partitions
python -m qm ops check-layer3-config
python -m qm ops check-data-quality --date 2026-06-15
python -m qm ops check-source-conflicts --date 2026-06-15
python -m qm ops disk-usage
python -m qm ops generate-runbook-report
```

---

# 4. 目录初始化规则

必须创建：

```text
data/duckdb/
data/raw/
data/files/
data/parquet/
data/audit/
data/reports/
data/cache/
data/backups/daily/
data/backups/weekly/
data/backups/before_schema_change/
```

初始化脚本必须幂等：重复执行不应删除已有文件。

---

# 5. 每日健康检查

`daily_health_check.py` 应检查：

```text
DuckDB 文件是否存在
最新 IncrementalUpdateJob 是否成功
最新 DataQualityJob 是否成功
source_conflict 是否有严重未处理冲突
manual_review_queue 是否有待处理项
Layer 1 五轴是否有 stale / missing / insufficient_history
Layer 3 配置是否通过健康检查
API 是否可访问
日报是否生成
磁盘使用率是否超过阈值
```

输出：

```json
{
  "check_date": "2026-06-15",
  "overall_status": "ok|warning|critical",
  "checks": [],
  "manual_actions": []
}
```

---

# 6. 备份与恢复

DuckDB 备份规则：

```text
每日盘后备份一次。
schema migration 前必须备份。
每周保留一份完整备份。
恢复演练每月至少一次。
```

备份文件命名：

```text
quant_monitor_YYYYMMDD_HHMM.duckdb
```

恢复流程：

```text
1. 停止写入任务
2. 复制当前 DuckDB 到 emergency_backup
3. 选择备份文件
4. 校验文件 hash
5. 替换 quant_monitor.duckdb
6. 执行 smoke test
7. 恢复调度任务
```

---

# 7. 磁盘与内存阈值

| 指标                |    warning |   critical | 动作                     |
| ------------------- | ---------: | ---------: | ------------------------ |
| 磁盘使用率          |        70% |  85% / 95% | 清 cache、暂停非核心回补 |
| DuckDB 文件大小增长 | 日增 > 20% | 日增 > 50% | 检查重复写入             |
| audit 日志大小      |      > 1GB |      > 5GB | 压缩归档                 |
| 单次查询返回行数    |     > 5000 |    > 50000 | 拒绝或要求分页           |
| Pandas 转换行数     |     > 200k |       > 1M | 改 DuckDB/Polars 聚合    |

---

# 8. Layer 3 配置健康检查

必须检查：

```text
chain_id 不重复
anchor_id 不重复
node_id 不重复
edge 起点/终点存在
cross_chain_edge 起点/终点存在
private event anchor 必须 event_only=true
source_validation_status 必须是合法枚举
P0 anchor 必须有 source_keys
commodity/index/future 不得误标为普通 public_equity
```

---

# 9. 错误码

| error_code                 | 含义             | 处理                       |
| -------------------------- | ---------------- | -------------------------- |
| `SOURCE_UNAVAILABLE`       | 数据源不可用     | 重试或进入 fallback_policy |
| `SCHEMA_DRIFT`             | 字段结构变化     | 停止写 clean，人工确认     |
| `DATA_STALE`               | 数据过期         | 标 stale，不静默替换       |
| `SOURCE_CONFLICT_CRITICAL` | 多源严重冲突     | ReconcileJob               |
| `WRITE_LOCKED`             | 写锁存在         | 等待或退出                 |
| `QUERY_TOO_LARGE`          | 查询过大         | 要求分页或缩小范围         |
| `AGENT_OUTPUT_INVALID`     | Agent 输出不合规 | 不写 clean，重试或人工审核 |
| `REPORT_SEND_FAILED`       | 报告发送失败     | 重试并写 run log           |

---

# 10. 验收测试

必须通过：

```text
init-directories 重复执行不删除数据。
backup-duckdb 生成文件并校验 hash。
restore-duckdb 可完成 smoke test。
daily_health_check 可以输出 ok/warning/critical。
磁盘 critical 时非核心 backfill 不应继续执行。
Layer 3 配置健康检查能发现孤立 edge。
Agent 输出非法时能被 NoActionSemanticGuard 拦截。
```
