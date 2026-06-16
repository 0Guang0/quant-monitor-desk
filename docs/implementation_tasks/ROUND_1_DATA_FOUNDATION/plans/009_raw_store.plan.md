# 009 file_registry 与 Raw Store — 深度实现计划

> **给执行者：** 配合 `009_implement_file_registry_and_raw_store.md`，按 TDD 执行。
> 遵守 `/karpathy-guidelines` 与 `/testing-guidelines`。

**目标：** 把原始文件落到本地磁盘，算 sha256，并通过 WriteManager 把索引写入 `file_registry`（不直接 INSERT）。

**架构：** `RawStore.save()` 负责落盘 + 算 hash + 返回元数据；`FileRegistry.register()` 把元数据写入 staging 再经 WriteManager（append_only）入 `file_registry`。去重以 content_hash 为准。

**范围（DECISIONS.md §1/§5）：** 路径 `backend/app/storage/*`，hash 用 sha256，写库必须走 WriteManager。

---

## 文件结构

- 创建：`backend/app/storage/__init__.py`
- 创建：`backend/app/storage/raw_store.py`
- 创建：`backend/app/storage/file_registry.py`
- 测试：`tests/test_raw_store.py`

---

## API 签名

```python
# backend/app/storage/raw_store.py
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class SavedFile:
    file_id: str          # = content_hash 前 16 位 + source，保证幂等
    source: str
    data_domain: str
    local_path: str
    content_hash: str     # sha256 全量
    file_type: str
    as_of: str            # 数据 as-of（YYYY-MM-DD），写入 file_registry.as_of_timestamp

class RawStore:
    def __init__(self, data_root: Path): ...
    def save(self, content: bytes, *, source: str, data_domain: str,
             file_type: str, as_of: str) -> SavedFile:
        """落盘到 data/raw/<source>/<data_domain>/<as_of>/<hash>.<ext>，算 sha256，返回 SavedFile。"""

def sha256_hex(content: bytes) -> str: ...
```

```python
# backend/app/storage/file_registry.py
class FileRegistry:
    def __init__(self, conn_manager, write_manager): ...
    def register(self, saved: SavedFile) -> str:
        """写入 file_registry（经 WriteManager append_only）。同 content_hash 已存在则跳过，返回 file_id。"""
    def exists(self, content_hash: str) -> bool: ...
```

---

## 任务步骤（TDD）

### Step 1: 写失败测试

```python
import duckdb
from pathlib import Path
from backend.app.storage.raw_store import RawStore, sha256_hex
from backend.app.storage.file_registry import FileRegistry
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.db.write_manager import WriteManager

def test_sha256Hex_knownInput_matchesExpected():
    assert sha256_hex(b"abc") == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

def test_save_writesFileAndComputesHash(tmp_path):
    store = RawStore(tmp_path)
    saved = store.save(b"hello", source="qmt", data_domain="daily_bar",
                       file_type="json", as_of="2026-06-15")
    assert Path(saved.local_path).read_bytes() == b"hello"
    assert saved.content_hash == sha256_hex(b"hello")

def _cm(tmp_path):
    db = tmp_path / "t.duckdb"
    con = duckdb.connect(str(db)); apply_migrations(con); con.close()
    return ConnectionManager(db)

def test_register_newFile_insertsRegistryRow(tmp_path):
    cm = _cm(tmp_path)
    store = RawStore(tmp_path); reg = FileRegistry(cm, WriteManager(cm))
    saved = store.save(b"x", source="qmt", data_domain="daily_bar",
                       file_type="json", as_of="2026-06-15")
    fid = reg.register(saved)
    r = cm.reader()
    got = r.execute("SELECT source, content_hash FROM file_registry WHERE file_id=?",
                    [fid]).fetchone()
    assert got == ("qmt", saved.content_hash)

def test_register_duplicateHash_doesNotInsertTwice(tmp_path):
    cm = _cm(tmp_path)
    store = RawStore(tmp_path); reg = FileRegistry(cm, WriteManager(cm))
    saved = store.save(b"x", source="qmt", data_domain="daily_bar",
                       file_type="json", as_of="2026-06-15")
    reg.register(saved); reg.register(saved)
    cnt = cm.reader().execute(
        "SELECT COUNT(*) FROM file_registry WHERE content_hash=?",
        [saved.content_hash]).fetchone()[0]
    assert cnt == 1
```

### Step 2: 运行确认失败

Run: `pytest tests/test_raw_store.py -v`
Expected: FAIL（模块不存在）

### Step 3: 实现 raw_store.py + file_registry.py

- `sha256_hex`：`hashlib.sha256(content).hexdigest()`。
- `save`：建目录 → 写文件（文件名用 hash + 扩展名）→ 返回 SavedFile。
- `register`：先 `exists(content_hash)` → 已存在返回原 file_id；否则写入 staging 临时表 → WriteManager append_only 入 `file_registry`。

### Step 4: 运行确认通过

Run: `pytest tests/test_raw_store.py -v`
Expected: PASS（5 passed）

### Step 5: 验收 + 提交

Run: `pytest -q && ruff check . && python -m compileall backend scripts`
Commit: `feat(storage): add RawStore and file_registry via WriteManager (task 009)`

---

## 自检

- [ ] 写库经 WriteManager，未直接 INSERT file_registry
- [ ] sha256 用已知向量断言（业务正确性）
- [ ] 同 hash 去重生效
- [ ] 文件 I/O 落在 data_root 下，未污染主库

---

## 实现记录（含审计修复与缺口补充）

> 首版实现后的 hardening 轮次在本 task 范围内的变更记录。

### 首版交付（task 009）

- `backend/app/storage/raw_store.py`：`RawStore`、`sha256_hex`
- `backend/app/storage/file_registry.py`：`FileRegistry`（经 WriteManager 写 `file_registry`）
- `tests/test_raw_store.py`：5 个测试

### 审计修复（P0 / P1）

| 项 | 问题 | 修复 |
|----|------|------|
| P0 | `source`/`data_domain`/`as_of` 可路径穿越 | `_safe_segment()` + `resolve()` + `is_relative_to(data_root)` |
| P0 | `FileRegistry.register()` 分两次 `writer()`，staging 竞态 | staging + `WriteManager.write(con=con)` 在同一 `writer()` 会话内完成 |
| P1 | dedup 在 writer 外查询，TOCTOU | `content_hash` 查重移入 `writer()` 内；DB 层 `UNIQUE INDEX`（见 005 的 `002` migration） |
| P1 | 无原始文件大小上限，DoS 风险 | `MAX_RAW_FILE_BYTES = 256MB`，超限 `ValueError` |
| 缺口 | `file_type` 任意扩展名 | 仅允许 `json`/`csv`/`parquet` 白名单 |
| 缺口 | `stg_file_registry` 运行时 DDL | 改由 `002_registry_hardening.sql` 迁移创建 |

### 测试缺口补充

| 测试 | 证明什么 |
|------|----------|
| `test_save_pathLayout_matchesConvention` | 路径 `raw/{source}/{domain}/{as_of}/{hash}.ext` |
| `test_save_fileIdFormat_isHashPrefixPlusSource` | `file_id = hash[:16] + source` |
| `test_save_pathTraversal_raises` | `source='..'` 拒绝 |
| `test_save_unsupportedFileType_raises` | 非白名单 file_type 拒绝 |
| `test_save_oversizedContent_raises` | 超 256MB 拒绝 |
| `test_register_writesAuditLog` | 注册写 `write_audit_log` |
| `test_exists_whenHashPresent_returnsTrue` | `exists()` API |
| `test_register_duplicateHash_returnsSameFileId` | 重复注册返回同一 `file_id` 且仅 1 行 |

### 当前测试规模

- 本 task 相关：`tests/test_raw_store.py` **11** 个（原 5 + 6）

---

## 评估报告跟进（二次修复）

| 评估项 | 修复 |
|--------|------|
| `exists()` 半死代码 | 抽取 `_lookup_by_content_hash()`；`exists()` 与 `register()` 共用 |
| staging 与 merge 跨 autocommit | `register()` 外层显式 `BEGIN`；`WriteManager.write(..., own_transaction=False)` 与 staging 同事务后 `COMMIT` |

---

## 评估报告跟进（三次修复）

| 评估项 | 修复 |
|--------|------|
| **P0** FAILED write 路径 double ROLLBACK | 移除内联 ROLLBACK；`except RuntimeError: raise` 与 `except Exception: ROLLBACK` 分离 |
| **P1** `as_of_timestamp` 误用 `now` | `SavedFile` 增加 `as_of`；`_parse_as_of_timestamp()` 写入 DB |
| register 失败 / as_of 语义无测试 | `test_register_whenWriteFails_raisesRuntimeError`、`test_register_asOfTimestamp_matchesAsOfArgument` |
| `reader()` 泄漏 | 随 007 context manager 一并修复 |

### 当前测试规模（三次修复后）

- 本 task：**13** 个
