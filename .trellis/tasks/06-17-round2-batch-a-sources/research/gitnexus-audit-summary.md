# GitNexus Audit 摘要 — Round 2 Batch A（7.pre）

> **日期：** 2026-06-17  
> **任务：** `06-17-round2-batch-a-sources`  
> **用途：** A1–A8 派发前只读索引；Execute 摘要见 `gitnexus-execute-summary.md`（若存在）

---

## 1. 刷新命令

| 工具 | 命令 / MCP | 状态 |
|------|------------|------|
| GitNexus query | `query("SourceRegistry BaseDataAdapter fetch_log apply_migrations ingestion")` | ✅ |
| GitNexus context | `context(SourceRegistry)` | ✅ |
| GitNexus context | `context(BaseDataAdapter, file_path=base_adapter.py)` | ⚠️ 部分（LadybugDB 偶发未初始化） |
| GitNexus context | `context(apply_migrations)` | ✅ |

**Execute 后索引：** §8.4 完成后建议 `node .gitnexus/run.cjs analyze`（MASTER §0.1 P3-2）。

---

## 2. 命中文件（query 定义）

| 路径 | 角色 |
|------|------|
| `backend/app/datasources/source_registry.py` | SourceRegistry |
| `backend/app/datasources/base_adapter.py` | BaseDataAdapter 模板 |
| `backend/app/datasources/fetch_log.py` | FetchLogWriter |
| `backend/app/datasources/fetch_result.py` | FetchRequest/FetchResult |
| `backend/app/db/migrations/004_ingestion_sources.sql` | migration 004 |
| `tests/test_source_registry.py` | registry 测试 |
| `tests/test_data_adapter_contract.py` | adapter 契约测试 |
| `tests/test_schema_migration.py` | 004 migration 回归 |
| `tests/test_schema_contract.py` | 两表列契约 |
| `scripts/init_db.py` | prod-path CLI |

---

## 3. SourceRegistry（context）

**Importers：** `test_source_registry.py`, `test_data_adapter_contract.py`, `conftest.py`, `__init__.py`, `base_adapter.py`

**Methods：** `load`, `get`, `get_domain_roles`, `assert_enabled`, `assert_domain_allowed`, `sync_to_db`, `_validate_domain_roles`

**Processes：** （索引未分组 process；A1 可补 query）

---

## 4. apply_migrations（context）

**Callers（节选）：** `init_db.main`, `conftest._open`, `test_schema_migration`（含 **004 ingestion** 用例）, `test_data_adapter_contract.test_write_underWriterLock_insertsFetchLogRow`, Round 1 测试集

**Callees：** `_file_checksum`, `applied_versions`, `verify_applied_checksums`

**Processes：** `_open → _file_checksum`, `main → applied_versions`

---

## 5. Audit 关注点（§2 映射）

| 维 | GitNexus 建议 query/context |
|----|----------------------------|
| A1 | SourceRegistry + DECISIONS §4；check.jsonl 对照 |
| A2 | diff `backend/app/datasources/`（ponytail-review） |
| A3 | 静态 grep WriteManager（期望无） |
| A4 | base_adapter + fetch_log 模板方法 |
| A5 | AC-1..8 ↔ §8 测试名 |
| A7 | init_db → apply_migrations → 004 表 |
| A8 | pytest Red Flags 边界 |

---

## 6. Ghost 依赖初筛

Batch A 模块 import 应限于：`duckdb`, `pydantic`, `yaml`, 项目内 `connection`/`sql_identifiers`。**A1 须确认无未文档化 vendor SDK。**
