# 005 Schema 初始化 — 深度实现计划

> **给执行者：** 本计划配合 `005_create_schema_sql.md` 使用，按任务逐步执行（红 → 绿 → 重构）。
> 必须遵守 `/karpathy-guidelines`（最小改动、可验证）与 `/testing-guidelines`（业务语义断言）。

**目标：** 用幂等 migration 机制在 DuckDB 上建出 5 张 foundation 表，并记录 `schema_version`。

**架构：** `scripts/init_db.py` 调 `backend/app/db/migrate.py` 的 runner；runner 顺序读取 `migrations/*.sql`，跳过 `schema_version` 中已记录的文件，执行后写入版本行。

**范围（DECISIONS.md §3）：** 只建 `schema_version`、`file_registry`、`write_audit_log`、`resource_guard_log`、`stg_foundation_smoke`，不整库执行 `specs/schema/schema.sql`。

---

## 文件结构

- 创建：`backend/app/db/__init__.py`（如已存在则跳过）
- 创建：`backend/app/db/migrations/001_foundation.sql`
- 创建：`backend/app/db/migrate.py`
- 修改：`scripts/init_db.py`
- 测试：`tests/test_schema_migration.py`
- 依赖：在 `pyproject.toml` 的 `dependencies` 增加 `duckdb>=1.1.0`

---

## API 签名

```python
# backend/app/db/migrate.py
from pathlib import Path
import duckdb

MIGRATIONS_DIR = Path(__file__).parent / "migrations"

def apply_migrations(con: duckdb.DuckDBPyConnection,
                     migrations_dir: Path = MIGRATIONS_DIR) -> list[str]:
    """按文件名顺序应用未执行的 migration，返回本次新应用的 version_id 列表。幂等。"""

def applied_versions(con: duckdb.DuckDBPyConnection) -> set[str]:
    """返回 schema_version 中已记录的 version_id 集合；表不存在时返回空集合。"""
```

`version_id` 取 SQL 文件名去扩展名（如 `001_foundation`）；`checksum` 取文件内容 sha256。

---

## 001_foundation.sql 表清单（列以 specs/schema/schema.sql 为准裁剪）

```sql
CREATE TABLE IF NOT EXISTS schema_version (
    version_id      VARCHAR PRIMARY KEY,
    applied_at      TIMESTAMP,
    migration_file  VARCHAR,
    checksum        VARCHAR,
    applied_by      VARCHAR,
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS file_registry (
    file_id         VARCHAR PRIMARY KEY,
    file_type       VARCHAR,
    source          VARCHAR,
    source_url      VARCHAR,
    local_path      VARCHAR,
    content_hash    VARCHAR,
    schema_hash     VARCHAR,
    fetch_time      TIMESTAMP,
    as_of_timestamp TIMESTAMP,
    parse_status    VARCHAR,
    quality_flag    VARCHAR
);

CREATE TABLE IF NOT EXISTS write_audit_log (
    write_id        VARCHAR PRIMARY KEY,
    run_id          VARCHAR,
    job_id          VARCHAR,
    target_table    VARCHAR,
    staging_table   VARCHAR,
    write_mode      VARCHAR,
    primary_keys    VARCHAR,
    rows_in_staging INTEGER,
    rows_inserted   INTEGER,
    rows_updated    INTEGER,
    rows_deleted    INTEGER,
    rows_rejected   INTEGER,
    validation_status VARCHAR,
    source_used     VARCHAR,
    started_at      TIMESTAMP,
    finished_at     TIMESTAMP,
    status          VARCHAR,
    error_message   TEXT
);

CREATE TABLE IF NOT EXISTS resource_guard_log (
    event_id        VARCHAR PRIMARY KEY,
    decision        VARCHAR,
    reason          VARCHAR,
    profile         VARCHAR,
    available_memory_gb DOUBLE,
    disk_free_gb    DOUBLE,
    process_rss_mb  DOUBLE,
    project_size_gb DOUBLE,
    created_at      TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stg_foundation_smoke (
    instrument_id   VARCHAR,
    trade_date      DATE,
    close           DOUBLE,
    source_used     VARCHAR,
    batch_id        VARCHAR,
    PRIMARY KEY (instrument_id, trade_date)
);
```

---

## 任务步骤（TDD）

### Step 1: 写失败测试

`tests/test_schema_migration.py`：

```python
import duckdb
from backend.app.db.migrate import apply_migrations, applied_versions

def test_applyMigrations_freshDb_createsFoundationTables():
    con = duckdb.connect(":memory:")
    applied = apply_migrations(con)
    assert "001_foundation" in applied
    tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    assert {"schema_version", "file_registry", "write_audit_log",
            "resource_guard_log", "stg_foundation_smoke"}.issubset(tables)

def test_applyMigrations_runTwice_isIdempotent():
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    second = apply_migrations(con)
    assert second == []
    count = con.execute(
        "SELECT COUNT(*) FROM schema_version WHERE version_id='001_foundation'"
    ).fetchone()[0]
    assert count == 1

def test_appliedVersions_emptyDb_returnsEmptySet():
    con = duckdb.connect(":memory:")
    assert applied_versions(con) == set()
```

### Step 2: 运行测试确认失败

Run: `pytest tests/test_schema_migration.py -v`
Expected: FAIL（`ModuleNotFoundError: backend.app.db.migrate`）

### Step 3: 写 `001_foundation.sql`（上方表清单）与 `migrate.py`

`migrate.py` 要点：
- `applied_versions`：先查 `schema_version` 是否存在（`information_schema` 或 try/except），不存在返回空集。
- `apply_migrations`：排序 `*.sql` → 跳过已应用 → `con.execute(sql)` → INSERT `schema_version` 行（含 sha256 checksum，`applied_by='init_db'`）。

### Step 4: 运行测试确认通过

Run: `pytest tests/test_schema_migration.py -v`
Expected: PASS（3 passed）

### Step 5: 接好 `scripts/init_db.py`

```python
from pathlib import Path
import duckdb
from backend.app.config import DATA_ROOT
from backend.app.db.migrate import apply_migrations

def main() -> None:
    db_path = DATA_ROOT / "duckdb" / "quant_monitor.duckdb"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    applied = apply_migrations(con)
    print(f"init_db: applied {applied or 'none (up to date)'}")

if __name__ == "__main__":
    main()
```

### Step 6: 验收 + 提交

Run: `pytest -q && ruff check . && python -m compileall backend scripts`
Expected: 全部通过。
Commit: `feat(db): add foundation schema migration runner (task 005)`

---

## 自检

- [ ] 仅建 5 张 foundation 表，未整库执行 schema.sql
- [ ] migration 幂等（重复执行不重复写 version 行）
- [ ] 测试含业务断言（表存在、幂等行数），非仅「不抛异常」
- [ ] 路径全部在 `backend/app/db/`
