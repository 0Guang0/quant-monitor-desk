# 日 / 周 / 月运维检查清单

> 文件定位：低打扰本机运维清单。默认只做轻量检查，重任务必须由用户确认或安排盘后执行。

---

# 1. 每日轻量检查

默认运行时间：盘后或用户指定空闲时段。

```text
1. 检查 ResourceGuard 状态
2. 检查 IncrementalUpdateJob 是否成功
3. 检查 source_health 是否有 DOWN / SCHEMA_DRIFT
4. 检查 data_quality_log 是否有 ERROR
5. 检查 source_conflict 是否新增 severe 冲突
6. 检查最新 DuckDB 备份是否成功
7. 检查 data/cache 是否超过 1GB
8. 检查 data/backups 是否超过 10GB
9. 检查磁盘剩余空间是否低于 30GB
10. 生成 data_health_summary
```

每日检查不得执行：

```text
全历史多源审计
全量重建 snapshot
大范围 backfill
完整 Parquet 复制
```

---

# 2. 每日输出

生成：

```text
reports/system/daily_health_YYYYMMDD.md
```

必须包含：

```text
资源状态
数据同步状态
数据源健康
数据质量摘要
冲突摘要
备份状态
需要人工确认事项
```

---

# 3. 每周检查

默认运行时间：周末或用户明确确认。

```text
1. 压缩旧 audit logs
2. 清理 cache
3. 检查 Parquet 分区完整性
4. 检查 DuckDB 文件大小变化
5. 检查 Layer 3 配置健康
6. 检查 specs 与 schema 是否一致
7. 抽样恢复测试最近 daily backup
8. 生成 weekly_ops_report
```

资源限制：

```text
默认 eco 模式
如需 normal 模式必须用户确认
单次运行不超过 30 分钟
磁盘剩余 < 30GB 时跳过非必要检查
```

---

# 4. 每月检查

```text
1. 做一次完整备份或提醒用户迁移外部备份
2. 做一次 restore dry-run
3. 检查 schema migration 记录
4. 检查 source_registry 是否有长期失败源
5. 检查未处理 manual_review_queue
6. 检查 Layer 1 指标是否有长期 stale
7. 检查 Layer 3 source_validation_status 是否仍大量 needs_source
8. 回顾资源占用趋势
```

每月检查可以耗时更长，但必须用户确认后执行。

---

# 5. 人工确认清单

以下情况必须进入人工确认：

```text
严重 source_conflict 重抓后仍冲突
schema migration 前
restore 执行前
删除正式备份前
删除 raw / files / parquet 正式数据前
开启 batch 模式前
```

---

# 6. CLI

```bash
python -m quant_monitor.ops.health --daily
python -m quant_monitor.ops.health --weekly --dry-run
python -m quant_monitor.ops.health --monthly --dry-run
python -m quant_monitor.ops.health --monthly --confirm
```

---

# 7. 验收测试

```text
每日检查在 eco 模式下完成
每日检查不会触发 backfill
磁盘低于 20GB 时周检查自动降级
月检查没有 --confirm 不执行重任务
所有报告写入 report_registry
所有异常写 logs_health_audit
```
