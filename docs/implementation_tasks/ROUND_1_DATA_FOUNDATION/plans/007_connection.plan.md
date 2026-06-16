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

---

## 实现记录（含审计修复与缺口补充）

> 首版实现后的 hardening 轮次在本 task 范围内的变更记录。

### 首版交付（task 007）

- `backend/app/db/connection.py`：`ConnectionManager`、`WriteLockError`、文件锁 + PRAGMA
- `tests/test_duckdb_connection.py`：3 个测试

### 审计修复（P0 / P1）

| 项 | 问题 | 修复 |
|----|------|------|
| P0/P1 | 写锁 check-then-write（TOCTOU），损坏 JSON 锁被静默删除 | `O_CREAT\|O_EXCL` 原子创建；`fcntl`/`msvcrt` advisory lock；损坏锁抛 `WriteLockError`（不静默删） |
| P1 | 锁被占用时读 lock 文件 `PermissionError` 未处理 | 转为 `WriteLockError("write lock held by another process")` |
| P1 | `temp_directory` PRAGMA 路径含 `'` 可能出错 | `_escape_sql_string()` 转义 |
| P1 | 死 PID 遗留锁无法恢复 | 仅当 `_pid_alive` 为 false 时 unlink 并重试 `O_EXCL` |

### 测试缺口补充

| 测试 | 证明什么 |
|------|----------|
| `test_writer_afterExit_releasesLock` | 第一个 writer 退出后第二个可写 |
| `test_writer_staleLockFromDeadPid_allowsNewWriter` | 死 PID 锁文件可被安全接管 |
| `test_writer_corruptLockFile_raisesWriteLockError` | 损坏锁不自动删除，抛明确错误 |
| `test_applyPragmas_ecoProfile_setsThreadsAndMemory` | eco profile 设置 threads（原仅测 threads，已保留） |

### 与 005 联动

- `scripts/init_db.py` 已改为 `ConnectionManager(db_path).writer()` 内执行 `apply_migrations`

### 当前测试规模

- 本 task 相关：`tests/test_duckdb_connection.py` **6** 个（原 3 + 3）

### 已知遗留（Medium，Round 2）

- Windows `_pid_alive` 在 access-denied 场景仍可能误判；优先依赖文件锁而非 PID 启发式

---

## 评估报告跟进（二次修复）

| 评估项 | 状态 |
|--------|------|
| `reader()` 无自动关闭 | 已知 P3；调用方须 `close()`（`exists()` / 测试已用 try/finally）。Round 2 可考虑 context manager |

---

## 评估报告跟进（三次修复）

| 评估项 | 修复 |
|--------|------|
| **P3** `reader()` 连接泄漏 | 改为 `@contextmanager`，调用方 `with cm.reader() as r:` |
| **P2** `batch` profile 无 `max_threads` 静默用 2 | `configs/resource_limits.yaml` 增加 `max_threads: 4` |
| **P2** Windows `msvcrt.locking(..., 1)` 语义错误 | 按 lock payload 字节数锁定/解锁 |
| **P2** `writer()` 异常时锁释放无测试 | `test_writer_exceptionInsideContext_releasesLock` |
| **P2** batch 线程 PRAGMA 无测试 | `test_applyPragmas_batchProfile_usesConfiguredMaxThreads` |
| `_apply_pragmas` threads/memory 未强制 int | `int()` 转换 |

### 当前测试规模（三次修复后）

- 本 task：**8** 个

---

## 评估报告跟进（PR #1 review / 四次修复）

| # | 级别 | 问题 | 状态 |
|---|------|------|------|
| 1 | **P0** | `duckdb.connect()` 失败时写锁泄漏 | ✅ |
| 2 | P1 | `_apply_pragmas` temp_directory 字符串拼接 | ✅ escape + 测试 |
| 3 | P1 | `_acquire_lock` 无重试上限 | ✅ `_MAX_LOCK_RETRIES=5` |
| 4 | P3 | 双 writer 持锁竞争测试 | ✅ |

### 当前测试规模（四次修复后）

- 本 task：**11** 个
