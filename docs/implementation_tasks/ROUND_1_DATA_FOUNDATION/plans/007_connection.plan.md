# 007 DuckDB 连接管理 — 深度实现计划

> **给执行者：** 配合 `007_implement_duckdb_connection_manager.md`，按 TDD 执行。
> 遵守 `/karpathy-guidelines` 与 `/testing-guidelines`。

**目标：** 提供唯一可写连接 + 多个只读连接，按 profile 设置 DuckDB 运行参数，并用本地文件锁保证单写边界。

**架构：** `ConnectionManager` 持有 DB 路径与 profile；`writer()` 是上下文管理器，进入时获取文件锁并设置 PRAGMA，退出时释放；`reader()` 返回 `read_only=True` 连接，可多开。

**范围（DECISIONS.md §1）：** 路径 `backend/app/db/connection.py`，允许 `duckdb`。锁文件超时不自动删除，先验 pid。

---

## 文件结构

- 创建：`backend/app/db/connection.py`
- 测试：`tests/test_duckdb_connection.py`

---

## API 签名

```python
# backend/app/db/connection.py
from contextlib import contextmanager
from pathlib import Path
import duckdb

class WriteLockError(RuntimeError): ...

class ConnectionManager:
    def __init__(self, db_path: Path, profile: str = "eco",
                 limits: dict | None = None): ...

    @contextmanager
    def writer(self) -> duckdb.DuckDBPyConnection:
        """唯一可写连接：获取文件锁 → set PRAGMA → yield → 释放锁。重复获取报 WriteLockError。"""

    def reader(self) -> duckdb.DuckDBPyConnection:
        """只读连接（read_only=True），可多开。"""

    def _apply_pragmas(self, con) -> None:
        """按 profile 设置 memory_limit / threads / temp_directory。"""
```

锁文件：`<db_path>.write.lock`，内容 JSON（pid、started_at、target）。
PRAGMA 取自 `resource_limits.yaml` 当前 profile：`memory_limit`（duckdb_memory_max_mb）、`threads`（max_threads）、`temp_directory`（data/cache/duckdb_tmp）。

---

## 任务步骤（TDD）

### Step 1: 写失败测试

```python
import duckdb, pytest
from pathlib import Path
from backend.app.db.connection import ConnectionManager, WriteLockError
from backend.app.db.migrate import apply_migrations

def _init(db_path: Path):
    con = duckdb.connect(str(db_path)); apply_migrations(con); con.close()

def test_writer_writesRow_readerSeesIt(tmp_path):
    db = tmp_path / "t.duckdb"; _init(db)
    cm = ConnectionManager(db)
    with cm.writer() as w:
        w.execute("INSERT INTO file_registry(file_id, source) VALUES ('f1','qmt')")
    r = cm.reader()
    got = r.execute("SELECT source FROM file_registry WHERE file_id='f1'").fetchone()
    assert got[0] == "qmt"

def test_writer_whenLockHeld_raisesWriteLockError(tmp_path):
    db = tmp_path / "t.duckdb"; _init(db)
    cm = ConnectionManager(db)
    with cm.writer():
        with pytest.raises(WriteLockError):
            with ConnectionManager(db).writer():
                pass

def test_applyPragmas_ecoProfile_setsLowMemoryLimit(tmp_path):
    db = tmp_path / "t.duckdb"; _init(db)
    cm = ConnectionManager(db, profile="eco",
                           limits={"eco": {"duckdb_memory_max_mb": 1536, "max_threads": 2}})
    with cm.writer() as w:
        threads = w.execute("SELECT current_setting('threads')").fetchone()[0]
    assert int(threads) == 2
```

### Step 2: 运行确认失败

Run: `pytest tests/test_duckdb_connection.py -v`
Expected: FAIL（模块不存在）

### Step 3: 实现 ConnectionManager

- `writer()`：检查锁文件存在且 pid 存活 → 抛 `WriteLockError`；否则写锁 → `duckdb.connect(path)` → `_apply_pragmas` → yield → finally 关连接并删锁。
- `reader()`：`duckdb.connect(path, read_only=True)`。
- `_apply_pragmas`：`SET memory_limit`、`SET threads`、`SET temp_directory`。

### Step 4: 运行确认通过

Run: `pytest tests/test_duckdb_connection.py -v`
Expected: PASS（3 passed）

### Step 5: 重构 + 验收

确认与 005 的 migration、配置 profile 衔接顺畅。
Run: `pytest -q && ruff check . && python -m compileall backend scripts`
Commit: `feat(db): add single-writer ConnectionManager with file lock (task 007)`

---

## 自检

- [ ] 单写边界用真实并发场景测试（第二个 writer 抛错）
- [ ] reader 只读、可多开
- [ ] PRAGMA 来自 profile，非硬编码
- [ ] 锁不自动强删（先验 pid）
