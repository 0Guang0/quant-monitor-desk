# 008 WriteManager — 深度实现计划

> **给执行者：** 配合 `008_implement_write_manager.md`，按 TDD 执行。
> 遵守 `/karpathy-guidelines` 与 `/testing-guidelines`。

**目标：** 实现系统唯一标准写入口：staging → stub ValidationGate → clean，全程事务化，失败 rollback，并写 `write_audit_log`。

**架构：** `WriteManager` 通过 `ConnectionManager.writer()` 拿可写连接；`StubValidationGate` 按 `validation_report_id` 前缀放行/拒绝；merge 按 write_mode 生成 SQL（append_only / upsert_by_pk）；事务内执行，异常 rollback 并落 FAILED 审计。

**范围（DECISIONS.md §2/§7）：** 仅 `append_only` 与 `upsert_by_pk`；ValidationGate 为 stub，Round 2 替换为真实校验器（接口不变）。

---

## 文件结构

- 创建：`backend/app/db/validation_gate.py`
- 创建：`backend/app/db/write_manager.py`
- 测试：`tests/test_write_manager.py`

---

## API 签名

```python
# backend/app/db/validation_gate.py
class ValidationGateError(RuntimeError): ...
class ValidationRejected(RuntimeError): ...

class StubValidationGate:
    def assert_can_write(self, validation_report_id: str, write_mode: str) -> None:
        """stub-pass-* → 放行；stub-fail-* → raise ValidationRejected；其他 → raise ValidationGateError。"""
```

```python
# backend/app/db/write_manager.py
from dataclasses import dataclass, field

@dataclass
class WriteRequest:
    run_id: str
    job_id: str
    target_table: str
    staging_table: str
    write_mode: str            # append_only | upsert_by_pk
    primary_keys: list[str]
    validation_report_id: str
    source_used: str

@dataclass
class WriteResult:
    write_id: str
    status: str                # SUCCESS | FAILED
    rows_inserted: int = 0
    rows_updated: int = 0
    error_message: str | None = None

class WriteManager:
    SUPPORTED_MODES = ("append_only", "upsert_by_pk")

    def __init__(self, conn_manager, gate=None): ...
    def write(self, req: WriteRequest) -> WriteResult:
        """事务化写入；成功/失败都写 write_audit_log。"""
    def _build_merge_sql(self, req: WriteRequest) -> list[str]: ...
```

`_build_merge_sql`：
- `append_only` → `INSERT INTO target SELECT * FROM staging`
- `upsert_by_pk` → 先 `DELETE FROM target USING staging WHERE <pk 等值>`，再 `INSERT`

---

## 任务步骤（TDD）

### Step 1: 写失败测试（ValidationGate）

```python
import pytest
from backend.app.db.validation_gate import (
    StubValidationGate, ValidationRejected, ValidationGateError)

def test_assertCanWrite_stubPass_allows():
    StubValidationGate().assert_can_write("stub-pass-001", "append_only")  # 不抛即通过

def test_assertCanWrite_stubFail_raisesRejected():
    with pytest.raises(ValidationRejected):
        StubValidationGate().assert_can_write("stub-fail-001", "append_only")

def test_assertCanWrite_unknownId_raisesGateError():
    with pytest.raises(ValidationGateError):
        StubValidationGate().assert_can_write("real-123", "append_only")
```

### Step 2: 写失败测试（WriteManager）

```python
import duckdb, pytest
from pathlib import Path
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.db.write_manager import WriteManager, WriteRequest

def _setup(tmp_path: Path) -> ConnectionManager:
    db = tmp_path / "t.duckdb"
    con = duckdb.connect(str(db)); apply_migrations(con)
    con.execute("""INSERT INTO stg_foundation_smoke
                   VALUES ('AAPL','2026-06-15',195.0,'qmt','b1')""")
    con.close()
    return ConnectionManager(db)

def _req(mode="append_only", report="stub-pass-1"):
    return WriteRequest(run_id="r1", job_id="j1",
                        target_table="security_bar_smoke_clean",
                        staging_table="stg_foundation_smoke",
                        write_mode=mode, primary_keys=["instrument_id","trade_date"],
                        validation_report_id=report, source_used="qmt")

def test_write_appendOnlyStubPass_insertsAndAudits(tmp_path):
    cm = _setup(tmp_path)
    with cm.writer() as w:
        w.execute("""CREATE TABLE security_bar_smoke_clean AS
                     SELECT * FROM stg_foundation_smoke WHERE 1=0""")
    res = WriteManager(cm).write(_req())
    assert res.status == "SUCCESS"
    assert res.rows_inserted == 1
    r = cm.reader()
    assert r.execute("SELECT COUNT(*) FROM security_bar_smoke_clean").fetchone()[0] == 1
    audit = r.execute(
        "SELECT status, rows_inserted FROM write_audit_log WHERE write_id=?",
        [res.write_id]).fetchone()
    assert audit == ("SUCCESS", 1)

def test_write_stubFail_rollsBackAndAuditsFailed(tmp_path):
    cm = _setup(tmp_path)
    with cm.writer() as w:
        w.execute("""CREATE TABLE security_bar_smoke_clean AS
                     SELECT * FROM stg_foundation_smoke WHERE 1=0""")
    res = WriteManager(cm).write(_req(report="stub-fail-1"))
    assert res.status == "FAILED"
    r = cm.reader()
    assert r.execute("SELECT COUNT(*) FROM security_bar_smoke_clean").fetchone()[0] == 0
    cnt = r.execute(
        "SELECT COUNT(*) FROM write_audit_log WHERE status='FAILED'").fetchone()[0]
    assert cnt == 1

def test_write_unsupportedMode_raises(tmp_path):
    cm = _setup(tmp_path)
    with pytest.raises(ValueError):
        WriteManager(cm).write(_req(mode="replace_partition"))

def test_write_upsertByPk_replacesExistingRow(tmp_path):
    cm = _setup(tmp_path)
    with cm.writer() as w:
        w.execute("CREATE TABLE security_bar_smoke_clean AS SELECT * FROM stg_foundation_smoke")
        w.execute("UPDATE stg_foundation_smoke SET close=200.0")
    res = WriteManager(cm).write(_req(mode="upsert_by_pk"))
    assert res.status == "SUCCESS"
    r = cm.reader()
    close = r.execute(
        "SELECT close FROM security_bar_smoke_clean WHERE instrument_id='AAPL'").fetchone()[0]
    assert close == 200.0  # 被 upsert 覆盖，未重复插入
    assert r.execute("SELECT COUNT(*) FROM security_bar_smoke_clean").fetchone()[0] == 1
```

### Step 3: 运行确认失败

Run: `pytest tests/test_write_manager.py -v`
Expected: FAIL（模块不存在）

### Step 4: 实现 validation_gate.py + write_manager.py

`write()` 流程：
1. `write_mode not in SUPPORTED_MODES` → `raise ValueError`
2. 生成 `write_id`，记 `started_at`
3. `with conn_manager.writer() as con:`
4. `con.begin()`
5. `gate.assert_can_write(...)`（抛错则进 except）
6. 执行 `_build_merge_sql`，统计 rows_inserted/updated
7. INSERT `write_audit_log(status=SUCCESS)`
8. `con.commit()` → 返回 SUCCESS WriteResult
9. except：`con.rollback()` → 另起写 `write_audit_log(status=FAILED, error_message=...)` → 返回 FAILED WriteResult（不再抛，业务可读结果）
   - 注意：FAILED 审计行必须在 rollback 之后、独立提交，避免被回滚掉。

### Step 5: 运行确认通过

Run: `pytest tests/test_write_manager.py -v`
Expected: PASS（7 passed）

### Step 6: 验收 + 提交

Run: `pytest -q && ruff check . && python -m compileall backend scripts`
Commit: `feat(db): add WriteManager with stub validation gate and audit (task 008)`

---

## 自检

- [ ] 仅 append_only / upsert_by_pk，其余 mode 显式 ValueError
- [ ] 成功写 SUCCESS 审计、失败写 FAILED 审计且数据已 rollback
- [ ] FAILED 审计行未被事务回滚（独立提交）
- [ ] upsert 覆盖而非重复插入（业务语义断言）
- [ ] 未实现任何真实校验逻辑（留 Round 2）

---

## 实现记录（含审计修复与缺口补充）

> 首版实现后的 hardening 轮次在本 task 范围内的变更记录。

### 首版交付（task 008）

- `backend/app/db/validation_gate.py`：`StubValidationGate`（`stub-pass-*` / `stub-fail-*`）
- `backend/app/db/write_manager.py`：`WriteRequest` / `WriteResult` / `write()`
- `tests/test_write_manager.py`：7 个测试

### 审计修复（P0 / P1）

| 项 | 问题 | 修复 |
|----|------|------|
| P0 | 表名/列名 f-string 拼接，存在 SQL 标识符注入 | 新增 `backend/app/db/sql_identifiers.py` 的 `quote_ident()`；写入前 allowlist 校验 |
| P1 | `except Exception` 吞掉编程错误 | 仅捕获 `ValidationRejected`、`ValidationGateError`、`duckdb.Error`；其余向上抛 |
| P0 | `FileRegistry` 需与 staging 同事务 | `write(req, con=...)` 支持在外部已持锁连接上执行（供 009 单会话写入） |
| 缺口 | FAILED 路径 rollback 后误 `COMMIT` | rollback 后 audit 独立 autocommit，不再 `COMMIT` 空事务 |

### 测试缺口补充

| 测试 | 证明什么 |
|------|----------|
| `test_write_invalidIdentifier_raisesBeforeWrite` | 非法表名在写前 `ValueError` |
| `test_write_gateError_rollsBackAndAuditsFailed` | 未知 validation id → FAILED 审计 |
| `test_write_sqlError_rollsBackAndAuditsError` | 目标表不存在 → `validation_status=ERROR`、数据 rollback |
| `test_write_emptyStaging_insertsZeroRows` | 空 staging → SUCCESS 且 0 行 |

### 当前测试规模

- 本 task 相关：`tests/test_write_manager.py` **12** 个（原 11 + 1）

---

## 评估报告跟进（二次修复）

| 评估项 | 修复 |
|--------|------|
| **P1 Bug** `rows_updated` 误报 | DELETE 前用 PK join 计真实匹配数 `_count_pk_matches()`；`rows_inserted = after - before` |
| FAILED 审计靠 autocommit | `_commit_audit_after_rollback()`：ROLLBACK 后显式 `BEGIN` → audit → `COMMIT` |
| `stub-pass` 测试仅断言不抛异常 | 改为 `test_assertCanWrite_stubPass_allowsWhileStubFailRejects`，对比 pass/fail 行为 |
| 审计列无断言 | upsert 测试断言 `write_audit_log.rows_updated/rows_inserted` |

### 新增测试

- `test_write_upsertByPk_pureNewRow_reportsZeroUpdated` — staging 全新 PK、target 无匹配 → `updated=0, inserted=1`
- upsert 覆盖路径补 audit 断言 `(1, 0)`

---

## 评估报告跟进（三次修复）

| 评估项 | 修复 |
|--------|------|
| **P3** `WriteRequest` 可变 | 改为 `@dataclass(frozen=True)` |
| **P3** `_validated_tables()` 在 `write()` 重复调用 | 拆出 `_validate_request()` 供 `write()` 早失败 |
| **P3** 重复测试 | 删除 `test_assertCanWrite_stubFail_raisesRejected` |
| gateError/sqlError 未断言 rollback / error_message | 补断言 |
| mixed upsert 计数无测试 | `test_write_upsertByPk_mixedNewAndExisting_reportsCorrectCounts` |
| `rows_in_staging` 无断言 | append 测试补 audit 列断言 |

### 当前测试规模（三次修复后）

- 本 task：**12** 个
