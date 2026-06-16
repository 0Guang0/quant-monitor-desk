# 性能、内存与磁盘限制

> 文件定位：本机友好运行约束。本文是实现 `ResourceGuard`、查询限流、后台任务降级、磁盘保护的权威文件。  
> 核心目标：系统运行在用户本机时，只能占据较小的一部分内存、CPU、磁盘和 I/O，不影响用户日常使用。

---

## 配置文件权威（Round 1 repair · GPT）

| 文件 | 角色 |
|------|------|
| `specs/contracts/resource_limits.yaml` | **权威契约**：`system_thresholds`、`project_size_thresholds`（含 cache / system pct / duckdb temp 上限） |
| `configs/resource_limits.yaml` | **本地 override**：仅 `profiles`（eco/normal/batch 进程与 DuckDB 限制） |

运行时 `load_thresholds()` 将 contract 中的 thresholds **合并**进 config。`configs/` 中缺少的阈值字段**并非未生效**——它们来自 `specs/contracts/`。修改阈值时请优先改 contract，再在 README/本文件记录 rationale。

---

# 1. 总原则

本项目不是服务器集群系统，而是本地优先、少数人使用的量化监控系统。因此所有默认参数都采用 **Conservative Desktop Mode**。

```text
默认少占资源
重任务后台化
重任务错峰执行
查询必须分页
大表必须分区
内存必须有限制
磁盘必须有硬停止线
CPU 持续过高必须暂停非核心任务
```

禁止：

```text
默认全市场全历史扫描
默认全量分钟线入内存
默认大范围 backfill 并发执行
默认使用全部 CPU 核心
默认占用 50% 以上系统内存
默认吃满磁盘剩余空间
```

---

# 2. 资源配置分级

系统提供三档资源模式。

| 模式 | 场景 | CPU 线程 | 进程内存软上限 | DuckDB memory_limit | 临时目录硬上限 |
|---|---|---:|---:|---:|---:|
| `eco` | 默认、本机日常使用 | 1-2 | 1.0 GB | 768 MB - 1.5 GB | 2 GB |
| `normal` | 用户主动盘后运行 | 2-4 | 2.0 GB | 1.5 - 3 GB | 5 GB |
| `batch` | 用户明确执行回补/重建 | ≤ 半数 CPU 核心 | 4.0 GB | 3 - 6 GB | 10 GB |

默认永远使用：

```text
resource_profile = eco
```

`batch` 模式只能由用户显式开启，不能由 API 或 Agent 自动开启。

---

# 3. 动态上限公式

实际运行时不能只看固定值，还要看用户机器剩余资源。

## 3.1 DuckDB memory_limit

```text
duckdb_memory_limit = min(profile_limit, total_memory * 0.15, available_memory * 0.50)
```

约束：

```text
eco:    768MB <= memory_limit <= 1.5GB
normal: 1.5GB <= memory_limit <= 3GB
batch:  3GB <= memory_limit <= 6GB
```

如果机器总内存 ≤ 8GB，默认强制：

```text
resource_profile = eco
DuckDB memory_limit <= 768MB
threads = 1
```

## 3.2 DuckDB threads

```text
threads = min(profile_threads, max(1, physical_cores // 2))
```

默认：

```sql
SET threads = 2;
```

低内存或用户正在使用电脑时：

```sql
SET threads = 1;
```

## 3.3 DuckDB temp directory

必须设置专用目录：

```text
data/cache/duckdb_tmp/
```

必须设置临时目录硬上限：

```text
max_temp_directory_size = min(profile_temp_limit, free_disk_space * 0.05)
```

默认不允许 DuckDB 临时文件占用大量系统盘空间。

---

# 4. Python / 进程内存限制

建议用 `psutil` 实现进程与系统资源监控。

| 指标 | WARN | PAUSE_NON_CORE | HARD_STOP |
|---|---:|---:|---:|
| 当前进程 RSS | 800 MB | 1.2 GB | 1.8 GB |
| 系统可用内存 | < 4 GB | < 2 GB | < 1 GB |
| 系统内存占用率 | > 70% | > 80% | > 90% |
| swap 使用率 | > 20% | > 35% | > 50% |

动作：

```text
WARN: 写 resource_guard_log，降低 page_size / batch_size
PAUSE_NON_CORE: 暂停 backfill、revision_audit、全市场扫描、报告重生成
HARD_STOP: 停止非核心任务，保留状态并等待用户确认
```

核心任务仅包括：

```text
保存已抓取数据
写 audit log
关闭数据库连接
释放锁文件
生成失败摘要
```

---

# 5. CPU 限制

| 指标 | WARN | PAUSE_NON_CORE | HARD_STOP |
|---|---:|---:|---:|
| 本进程 CPU 持续占用 5 分钟 | > 30% | > 45% | > 70% |
| 系统 CPU 持续占用 5 分钟 | > 70% | > 85% | > 95% |

默认限制：

```text
非核心后台任务同一时间最多 1 个
FullLoad / Backfill / RevisionAudit 不能并行执行
Snapshot build 和 report generation 不能同时跑大范围历史
```

如果触发 PAUSE：

```text
降低 threads 到 1
缩小 batch_size
暂停低优先级 job
前端继续可读旧 snapshot
```

---

# 6. 磁盘限制

本系统默认不能无限增长。

| 指标 | WARN | PAUSE_NON_CORE | HARD_STOP |
|---|---:|---:|---:|
| 项目目录总大小 | > 15 GB | > 25 GB | > 40 GB |
| data/raw | > 5 GB | > 10 GB | > 20 GB |
| data/parquet | > 8 GB | > 15 GB | > 25 GB |
| data/cache | > 1 GB | > 2 GB | > 4 GB |
| data/backups | > 5 GB | > 10 GB | > 15 GB |
| 磁盘剩余空间 | < 30 GB | < 20 GB | < 10 GB |
| 系统盘使用率 | > 75% | > 85% | > 92% |

动作：

```text
WARN: 提示用户并建议清理 cache / old logs
PAUSE_NON_CORE: 停止 backfill / full reload / 大历史导出
HARD_STOP: 停止所有非核心写入，只允许 audit 和安全退出
```

清理顺序：

```text
1. data/cache/api_cache
2. data/cache/duckdb_tmp
3. 旧的临时 raw 包
4. 压缩 audit logs
5. 删除过期日报 HTML 临时文件
6. 按策略清理旧备份
```

禁止默认删除：

```text
公告 PDF
财报 PDF
revision_log
source_conflict_log
clean tables
正式 Parquet 历史归档
```

---

# 7. 查询限制

| 查询类型 | 默认 | 硬上限 | 超限处理 |
|---|---:|---:|---|
| 前端表格 | 100 行 | 500 行 | 分页 |
| Agent 查询 | 100 行 | 500 行 | 截断 + truncated=true |
| 日线历史 | 90 天 | 1 年 | 超过转后台任务 |
| 分钟线历史 | 5 个交易日 | 20 个交易日 | 超过转后台任务 |
| Layer 3 图谱 | P0/P1 默认 | 全量允许但不带历史行情 | 历史另查 |
| source_conflict 列表 | 100 行 | 500 行 | 分页 |

禁止接口：

```text
SELECT * FROM minute_bar
SELECT * FROM stock_bar_1d without date_range
SELECT * FROM evidence_chain without target_id or date_range
```

---

# 8. Batch size 默认值

| 场景 | 默认 batch | 最大 batch |
|---|---:|---:|
| 日线写入 | 5,000 rows | 20,000 rows |
| 分钟线写入 | 20,000 rows | 100,000 rows |
| 文件解析 | 50 files | 200 files |
| source conflict 检查 | 10,000 rows | 50,000 rows |
| backfill 日期窗口 | 5 trading days | 20 trading days |

触发 ResourceGuard WARN 时所有 batch 减半；触发 PAUSE 时停止非核心 batch。

---

# 9. 前端性能限制

```text
页面首次加载只取 snapshot
图表默认最近 90 天
长表必须虚拟滚动或分页
Layer 3 图谱默认只展示 P0/P1 节点
Layer 5 历史明细需要用户主动展开
Data Health 自动刷新间隔 >= 60 秒
```

---

# 10. Agent 性能限制

```text
Agent 一次最多读取 500 条结构化记录
Agent 不读取原始 PDF 全文，先读取解析摘要和 evidence refs
Agent 不触发实时大查询
Agent 不在前端请求链路里执行长推理
日报生成默认盘后运行
盘中提醒只处理增量事件
```

---

# 11. ResourceGuard 状态机

```text
OK
  → WARN
  → PAUSE_NON_CORE
  → HARD_STOP
  → RECOVERY
  → OK
```

状态记录表：

```sql
CREATE TABLE IF NOT EXISTS resource_guard_log (
    event_id VARCHAR PRIMARY KEY,
    event_time TIMESTAMP,
    status VARCHAR,
    metric_name VARCHAR,
    metric_value DOUBLE,
    threshold_value DOUBLE,
    action_taken VARCHAR,
    affected_job_id VARCHAR,
    message TEXT
);
```

---

# 12. 验收测试

```text
低内存机器默认使用 eco 模式
全市场无 date_range 分钟线查询被拒绝
磁盘剩余 < 20GB 时 backfill 暂停
进程 RSS > 1.2GB 时非核心任务暂停
前端列表默认 page_size=100
Agent tool 超过 500 条返回 truncated=true
DuckDB temp 目录不会占用超过 profile limit
HARD_STOP 时能释放锁并写 audit log
```

---

# 13. 与 resource_limits.yaml 的字段映射

实现代码必须同时读取 `specs/contracts/resource_limits.yaml`。其中关键字段包括：

```text
disk_free_warn_gb
disk_free_pause_gb
disk_free_hard_stop_gb
process_rss_warn_mb
process_rss_pause_mb
process_rss_hard_stop_mb
```

文档中的中文阈值说明和 YAML 中的机器可读阈值必须保持一致；若未来调整，以同一轮修改同时更新二者为准。
