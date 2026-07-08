# 数据架构

> 文件定位：数据层总架构文件。本文描述 DuckDB、Parquet、本地文件系统、staging、clean、snapshot、audit、specs 的关系。  
> 详细表结构以 `specs/schema/schema.sql` 为准。

---

# 1. 数据分层

```text
Raw Store / File Lake
  → Staging Tables
  → Clean Tables
  → Snapshot Tables
  → API Views / Reports / Agent Context
```

旁路审计：

```text
Audit Logs
Source Conflict Logs
Revision Logs
Resource Guard Logs
Agent Run Logs
```

---

# 2. 存储边界

| 数据类型                      | 存储位置               | 原因               |
| ----------------------------- | ---------------------- | ------------------ |
| 标准行情、指标、快照          | DuckDB                 | 结构化查询和聚合   |
| 长历史分钟线、大历史归档      | Parquet                | 文件分区和压缩     |
| 公告 PDF、网页快照、原始 JSON | 本地文件系统           | 可审计、可重放     |
| 文件索引                      | DuckDB `file_registry` | 查找和引用原始文件 |
| 配置                          | `specs/`               | 可版本化、可加载   |
| 日志                          | `data/audit/`          | 可追溯             |
| 临时缓存                      | `data/cache/`          | 可清理             |

---

# 3. DuckDB 表族

```text
registry tables:
  source_registry
  instrument_registry
  axis_registry
  industry_chain_registry
  market_registry

observation tables:
  axis_observation
  cross_asset_observation
  security_bar_daily
  futures_bar_daily

snapshot tables:
  axis_feature_snapshot
  axis_interpretation_snapshot
  cross_asset_daily_snapshot
  industry_chain_daily_snapshot
  market_index_snapshot
  market_breadth_snapshot
  valuation_snapshot

quality / audit tables:
  data_quality_log
  source_conflict
  write_audit_log
  resource_guard_log
  agent_run_log

report tables:
  report_registry
  report_section
  notification_log
```

---

# 4. Staging / Clean / Snapshot / Audit

## Staging

```text
临时落地
允许重复
允许缺字段但必须标记
不供前端直接读取
```

## Clean

```text
已校验
已去重
已处理 source conflict
可供 Repository 读取
```

Clean 不等于“永远来自正常主源”。Clean 的含义是“已通过校验、可追溯、可被系统读取”。最终成品必须进一步区分：

```text
primary-grade clean  正常 Primary 源写入，可作为默认主事实输入
degraded clean       FallbackPolicy 授权后的降级写入，可读但必须带 source_switched / quality_flags / stale_reason
```

下游模块、前端和 Agent 不得把 degraded clean 静默当作 primary-grade clean。若某个模型或指标只接受主源级输入，遇到 degraded clean 必须 fail-closed、降权、仅展示或返回诚实 NULL。

## Snapshot

```text
前端和 Agent 默认读取
每日或盘中增量生成
字段更接近展示层
```

## Audit

```text
记录 fetch / write / quality / conflict / revision / agent / resource
不可被业务逻辑静默删除
```

---

# 5. 数据生命周期

```text
Fetched Raw
  → Staged
  → Validated
  → Conflict Checked
  → Clean Merged
  → Snapshot Built
  → Reported / Displayed
  → Archived / Pruned by Policy
```

任何阶段失败都必须：

```text
保留 raw
写 audit
标记 failed status
可重试
不污染 clean table
```

若失败后按 FallbackPolicy 使用 Validation 源或 last_good_cache，不能视为“失败消失”。必须保留原始失败事件，并将后续写入标记为 degraded clean。

---

# 6. Schema Version

必须维护：

```text
schema_version
migration_id
applied_at
applied_by
rollback_plan
```

schema 变更前必须：

```text
before_schema_change backup
migration dry-run
smoke test
```

---

# 7. Parquet 分区

推荐：

```text
data/parquet/daily_bar/market=CN_A/year=2026/month=06/
data/parquet/minute_bar/market=US_EQ/year=2026/month=06/
data/parquet/futures_bar/market=CN_FUT/year=2026/month=06/
data/parquet/layer1_axis/axis=RISK_APPETITE/year=2026/
```

查询必须尽量命中分区过滤：

```text
market
year/month
instrument_id
axis_id
```

---

# 8. Specs 与数据库关系

```text
specs/layer1_axes → axis_registry / axis_indicator_registry / axis_indicator_profile
specs/layer3_global_industry_chains → industry_chain_* tables
specs/contracts → 实现约束和校验规则
specs/schema/schema.sql → 表结构权威定义
```

机器可读 spec 不应被实现代码静默修改。变更必须走：

```text
manual edit
schema/spec validation
migration note
audit log
```

> **L3/L4/L5 migration matrix (2026-06-25):** `docs/schema/MIGRATION_COVERAGE.md`; closure `tests/test_migration_coverage.py`.

---

# 9. 数据访问边界

| 调用方           | 允许读取                               | 禁止            |
| ---------------- | -------------------------------------- | --------------- |
| Frontend         | API snapshot / paginated detail        | 直连 DuckDB     |
| Agent            | Agent tools / evidence refs            | 自由 SQL / 写库 |
| DataSync         | staging / raw / clean via WriteManager | 绕过 Validation |
| Research scripts | read-only workspace                    | 直接覆盖 clean  |
| Ops scripts      | audit / backup / health                | 删除正式数据    |

---

# 10. 本机资源友好原则

```text
前端读 snapshot，不动态拼全库大 join
Agent 读摘要，不读原始大文件全文
大历史进 Parquet，不长期占 DuckDB 热表
cache 可清理，raw 和 audit 谨慎清理
Backfill 分区分批，不全市场并发
```

---

# 11. 数据架构验收测试

```text
所有 clean 表写入有 write_audit_log
所有 snapshot 能追溯到 clean / spec / source
所有 file_registry local_path 存在或标记 missing
所有 source switch 有 quality_flags
所有 degraded clean 可从 write_audit_log / route plan 追溯到主源失败原因和 fallback 策略
所有 specs 能加载并初始化 registry
无分页大查询被拒绝
ResourceGuard 可阻止重任务污染本机体验
```
