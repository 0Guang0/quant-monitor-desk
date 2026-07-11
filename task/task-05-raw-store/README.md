# task-05-raw-store

> 流水线 **05**/19 · 详见 [`../TASK_PIPELINE_INDEX.md`](../TASK_PIPELINE_INDEX.md)

## 完成哪个模块

**原始数据仓（Raw Store / File Lake / fetch_log）**

## 负责什么（业务视角）

保存「刚抓回来的原样数据」与审计痕迹：raw 文件、fetch_log、`file_registry` 索引。原始数据永不删除，供重放与修订审计。

## 上下游

| 方向     | 谁                                           |
| -------- | -------------------------------------------- |
| **上游** | **task-04-datasource-fetch**（抓取结果）     |
| **下游** | **task-06-staging**（标准化进入 staging 表） |

## 权威文件

权威文件必须在 `**/design/**` 下，详见：`docs/modules/design/local_file_system.md`、`docs/architecture/design/04_data_architecture.md`、`docs/modules/design/duckdb_and_parquet.md`、`docs/modules/design/data_sources.md`、`docs/ops/design/logs_health_audit.md`、`specs/contracts/design/log_audit_contract.yaml`、`docs/ops/design/privacy_retention_policy.md`、`docs/architecture/design/02_solution_strategy.md`。

> 倒查说明（`MIGRATION_MAP.md` 数据存储域 文件1/2/3 → 全文）：本票管 **Raw Store / File Lake、`file_registry`、原始抓取包路径、`fetch_log`（表 + `data/audit/fetch_log.ndjson`）**；原始数据永不删（`04_data_architecture.md` §5）。`privacy_retention_policy.md`（D-05）规定 raw 默认保留 1 年与归档 manifest；PDF/HTML 等大文件只进文件系统，DuckDB 存索引（`local_file_system.md` §2.3）。

## 运行时文件

> 非 design 路径：本模块**落库与路径对照**所用；设计口径以上节权威文件为准。

| 文件                                                        | 作用                                                                                         |
| ----------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `specs/schema/schema.sql`                                   | **表结构依赖/产出对照**：`file_registry`、`fetch_log` 等建表定义，迁移与 DuckDB 落库         |
| `data/raw/` · `data/files/` · `data/audit/fetch_log.ndjson` | **运行时产出**：原始包、大文件证据、fetch 审计 NDJSON（路径由 design 规定，非 specs 内文件） |

## 代码主区（实现时收窄）

```text
data/raw/ · data/files/ · fetch_log 写入路径 · file_registry 表
```

## 本票文档

| 文件           | 用途                 |
| -------------- | -------------------- |
| `task_plan.md` | R4 验收标准与关账 AC |
| `findings.md`  | **只记本票**问题     |
| `progress.md`  | 关账勾选             |
