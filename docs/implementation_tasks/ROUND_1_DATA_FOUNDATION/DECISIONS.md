# Round 1 已确认决策

> 本文记录 Round 1 开工前用户已拍板的架构与范围决策。实现阶段不得 silent override；若需变更，先更新本文并征得用户确认。

## 1. 目录约定

**决策：统一使用 `backend/app/*`，与 Round 0 骨架一致。**

| 模块 | 路径 |
|------|------|
| DuckDB 连接与写入 | `backend/app/db/` |
| 资源保护 | `backend/app/core/` |
| 原始文件与索引 | `backend/app/storage/` |
| CLI 入口 | `scripts/`（仓库根目录，与 Round 0 一致） |

不再使用 `backend/db/`、`backend/core/`、`backend/storage/` 等与 `app/` 平级的旧路径字面量。

## 2. WriteManager Round 1 范围

**决策：A — 最小可运行实现 + stub ValidationGate。**

Round 1 必须交付：

- staging → ValidationGate（stub）→ clean 写入
- 事务、失败 rollback、`write_audit_log` 审计
- 单写连接边界（与 ConnectionManager 配合）

Round 1 **不做**（留给 Round 2）：

- 真实 `DataQualityValidator`
- 真实 `SourceConflictValidator`
- `replace_partition`、`manual_patch`、`schema_migration` 写入模式

Round 1 **支持的 write_mode**：

- `append_only`
- `upsert_by_pk`

## 3. Schema Round 1 范围

**决策：只建 foundation 表 + migration 机制，不一次性应用完整 `specs/schema/schema.sql`。**

Round 1 migration `001_foundation.sql` 仅包含：

| 表名 | 用途 |
|------|------|
| `schema_version` | 记录已应用的 migration |
| `file_registry` | 本地文件索引（Raw Store 写入目标） |
| `write_audit_log` | WriteManager 审计 |
| `resource_guard_log` | ResourceGuard 触发记录 |
| `stg_foundation_smoke` | Round 1 smoke 用 staging 表（列结构与 smoke 场景对齐） |

完整 Layer / 行情 / snapshot 表在 Round 2 及以后通过后续 migration 追加。

**权威来源分工：**

- `specs/schema/schema.sql` — 全量 schema 契约（只读参考，Round 1 不整库执行）
- `backend/app/db/migrations/` — 按 Round 增量执行的 SQL
- `scripts/init_db.py` — 本地初始化 CLI

**Schema 契约测试：** `tests/test_schema_contract.py` 断言 `001_foundation.sql` / `002_registry_hardening.sql` 中 foundation 表的列名集合为 `specs/schema/schema.sql` 同表的子集（migrations = runtime truth；schema.sql = 目标契约）。

## 4. 文档补充深度

**决策：方案 B — 每个正式任务配独立 `plans/*.plan.md`。**

正式任务文件（`005_*.md` … `010_*.md`）保留治理结构与边界；可执行细节（TDD 步骤、API 签名、命令与预期输出）放在 `plans/` 下。

## 5. 依赖库

**决策：Round 1 允许新增以下运行时依赖（实现阶段写入 `pyproject.toml`）；Round 0 已引入 fastapi / uvicorn / pydantic / pyyaml，本节为 Round 1 增量：**

| 包 | 用途 |
|----|------|
| `duckdb` | 本地 DuckDB 引擎 |
| `psutil` | ResourceGuard 读取内存/磁盘/进程 RSS |

不引入 Polars/Pandas 作为 Round 1 写入路径依赖；校验与 ETL heavy 逻辑仍留后续 Round。

## 6. 测试与 TDD 约定

实现 Round 1 代码时必须：

1. 先写失败测试（红）→ 最小实现（绿）→ 必要时重构（refactor）
2. 遵守 `/karpathy-guidelines`：最小改动、可验证成功标准
3. 遵守 `/testing-guidelines`：业务语义断言，不只测「不抛异常」
4. 集成/smoke 测试使用临时 DuckDB 文件或 `:memory:`，不污染 `data/duckdb/quant_monitor.duckdb`

## 7. ResourceGuard Round 1 范围

- `evaluate()` / `snapshot()` 已接入全部 contract 阈值信号：
  - available_memory / disk_free / project_size / process_rss（Round 1 原有）
  - `duckdb_temp_max_gb`（扫描 `DATA_ROOT/cache/duckdb_tmp` 目录体量）
  - `cache_warn_gb` / `cache_pause_gb` / `cache_hard_stop_gb`（扫描 `DATA_ROOT/cache`）
  - `system_memory_usage_*_pct`（`psutil.virtual_memory().percent`）
  - `system_disk_usage_*_pct`（`psutil.disk_usage(DATA_ROOT 父目录).percent`）
- 运行时阈值来源：`configs/resource_limits.yaml` profiles + `specs/contracts/resource_limits.yaml` system/project 段（`load_thresholds()` 合并）。
- 自动化：`tests/test_resource_guard.py` 覆盖 cache/temp/system pct 信号；`tests/test_schema_contract.py` 校验 migration 列 ⊆ `schema.sql`。

## 8. RawStore 元数据（三次审计确认）

- `SavedFile` 必须携带 `as_of`（与落盘路径段一致）。
- `file_registry.as_of_timestamp` 写入数据 as-of 日期；`fetch_time` 为注册时刻。

## 9. ValidationGate stub 契约（Round 1 固定口径）

stub 仅用于 Round 1；Round 2 替换为真实校验器，接口保持不变。

```python
# backend/app/db/validation_gate.py
class StubValidationGate:
    def assert_can_write(self, validation_report_id: str, write_mode: str) -> None: ...
```

规则：

- `validation_report_id` 以 `stub-pass-` 开头 → 视为 `PASSED`，允许写入
- `validation_report_id` 以 `stub-fail-` 开头 → 视为 `FAILED`，拒绝写入并 rollback
- 其他 ID → 抛出 `ValidationGateError`（Round 1 不查库）

Round 2 将把同一方法改为读取 `validation_report` 表。
