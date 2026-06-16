# 备份与恢复

> 文件定位：本机低占用备份恢复实现文件。本文约束 `backup_manager.py`、`restore_manager.py`、`backup_recovery_contract.yaml`。  
> 原则：备份必须可恢复，但不能无限占用本机磁盘。

---

# 1. 备份对象

必须备份：

```text
data/duckdb/quant_monitor.duckdb
specs/
docs/
data/audit/ 近期审计日志
config/
```

按策略备份：

```text
data/parquet/ 仅备份目录索引和最近分区；长期完整备份可手动触发
data/files/announcements/ 公告和财报 PDF 可独立归档
```

默认不备份：

```text
data/cache/
data/cache/duckdb_tmp/
临时导出文件
前端构建产物
```

---

# 2. 备份目录

```text
data/backups/
  daily/
  weekly/
  before_schema_change/
  manifest/
```

每个备份必须生成 manifest：

```json
{
  "backup_id": "backup_20260616_180000",
  "created_at": "2026-06-16T18:00:00",
  "backup_type": "daily",
  "files": [],
  "total_size_bytes": 0,
  "schema_version": "v1",
  "duckdb_hash": "sha256",
  "restore_test_status": "not_tested"
}
```

---

# 3. 低磁盘占用保留策略

| 类型 | 默认保留 | 最大保留 | 说明 |
|---|---:|---:|---|
| daily | 3 份 | 7 份 | 不无限保留 |
| weekly | 2 份 | 4 份 | 只保留关键周备份 |
| before_schema_change | 3 份 | 5 份 | schema 变更前备份 |
| full manual | 用户手动 | 用户手动 | 不自动删除，需提示占用 |

如果 `data/backups/` 超过 10GB：

```text
进入 WARN
停止自动 weekly backup
提示用户清理或外部迁移
```

超过 15GB：

```text
进入 PAUSE_NON_CORE
只允许 before_schema_change 最小备份
```

---

# 4. DuckDB 备份流程

```text
1. 检查 WriteManager 是否空闲
2. 阻止新写入任务进入 merge 阶段
3. 等待当前事务完成
4. checkpoint DuckDB
5. 复制 .duckdb 到 backups/daily
6. 计算 sha256
7. 写 backup_manifest
8. 释放写入阻塞
```

禁止：

```text
在写入事务中直接复制 DuckDB 文件
备份 data/cache/duckdb_tmp
备份失败但标记成功
```

---

# 5. Parquet 备份策略

默认不每天全量复制 Parquet。做法：

```text
每日：记录 Parquet manifest、分区路径、文件 hash
每周：备份最近 1-2 个活跃分区
手动：用户确认后做完整 Parquet 归档
```

---

# 6. 恢复流程

```text
1. 停止调度器
2. 停止 FastAPI 写任务请求入口
3. 备份当前坏库到 data/backups/before_restore/
4. 校验目标备份 manifest 和 hash
5. 恢复 DuckDB 文件
6. 恢复 specs / config
7. 执行 smoke test
8. 重建必要 snapshot
9. 重新开启只读 API
10. 人工确认后开启调度
```

---

# 7. 恢复验收测试

必须通过：

```text
DuckDB 能打开
source_registry 可读
axis_registry 可读
industry_chain_registry 可读
最新 data_health 可读
FastAPI /api/data-health 返回 ok=true
无未释放 lock 文件
```

---

# 8. CLI

```bash
python -m quant_monitor.ops.backup --type daily
python -m quant_monitor.ops.backup --type before-schema-change --reason "add layer4 tables"
python -m quant_monitor.ops.restore --backup-id backup_20260616_180000 --dry-run
python -m quant_monitor.ops.restore --backup-id backup_20260616_180000 --confirm
python -m quant_monitor.ops.backup-prune --dry-run
```

---

# 9. 错误码

```text
BACKUP_LOCK_BUSY
BACKUP_DISK_LOW
BACKUP_HASH_MISMATCH
BACKUP_MANIFEST_MISSING
RESTORE_HASH_MISMATCH
RESTORE_SMOKE_TEST_FAILED
RESTORE_NEEDS_HUMAN_CONFIRMATION
```
