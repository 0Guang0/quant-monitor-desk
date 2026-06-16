# 010 数据底座 Smoke Test — 深度实现计划

> **给执行者：** 配合 `010_foundation_smoke_tests.md`，按 TDD 执行。
> 遵守 `/karpathy-guidelines` 与 `/testing-guidelines`。
> 执行前确认 Checkpoint：Foundation（见本目录 README）已全绿。

**目标：** 把 005~009 串成一条端到端最小验证：建库 → 资源检查 → 落原始文件 → 注册 file_registry → staging 写 clean → 审计 → 失败回滚。

**架构：** 单个 smoke 测试文件，按真实调用顺序组装各模块，只 mock psutil 系统读数。使用临时 DuckDB，不碰 `data/duckdb/quant_monitor.duckdb`。

**范围：** 不新增业务逻辑；只验证已实现模块协同正确。

---

## 文件结构

- 创建：`tests/smoke/__init__.py`
- 创建：`tests/smoke/test_foundation_smoke.py`

---

## 端到端步骤与断言

```python
import duckdb
from pathlib import Path
from backend.app.db.migrate import apply_migrations
from backend.app.db.connection import ConnectionManager
from backend.app.db.write_manager import WriteManager, WriteRequest
from backend.app.core.resource_guard import ResourceGuard, Decision, ResourceSnapshot
from backend.app.storage.raw_store import RawStore
from backend.app.storage.file_registry import FileRegistry


def test_foundation_endToEnd_writesCleanAndAudits(tmp_path, monkeypatch):
    # 1. 建库：5 张 foundation 表
    db = tmp_path / "smoke.duckdb"
    con = duckdb.connect(str(db)); applied = apply_migrations(con)
    tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    con.close()
    assert "001_foundation" in applied
    assert {"schema_version", "file_registry", "write_audit_log",
            "resource_guard_log", "stg_foundation_smoke"}.issubset(tables)

    cm = ConnectionManager(db)

    # 2. ResourceGuard：mock 健康读数 → OK
    guard = ResourceGuard(profile="eco", con=None)
    monkeypatch.setattr(guard, "snapshot",
                        lambda: ResourceSnapshot(8, 100, 300, 1))
    decision, _ = guard.check()
    assert decision == Decision.OK

    # 3. Raw Store + file_registry
    store = RawStore(tmp_path)
    reg = FileRegistry(cm, WriteManager(cm))
    saved = store.save(b"raw-bytes", source="qmt", data_domain="daily_bar",
                       file_type="json", as_of="2026-06-15")
    fid = reg.register(saved)
    assert cm.reader().execute(
        "SELECT COUNT(*) FROM file_registry WHERE file_id=?", [fid]).fetchone()[0] == 1

    # 4. staging → clean（stub-pass）
    with cm.writer() as w:
        w.execute("""INSERT INTO stg_foundation_smoke
                     VALUES ('AAPL','2026-06-15',195.0,'qmt','b1')""")
        w.execute("""CREATE TABLE security_bar_smoke_clean AS
                     SELECT * FROM stg_foundation_smoke WHERE 1=0""")
    ok = WriteManager(cm).write(WriteRequest(
        run_id="r1", job_id="j1", target_table="security_bar_smoke_clean",
        staging_table="stg_foundation_smoke", write_mode="append_only",
        primary_keys=["instrument_id", "trade_date"],
        validation_report_id="stub-pass-1", source_used="qmt"))
    assert ok.status == "SUCCESS" and ok.rows_inserted == 1

    r = cm.reader()
    assert r.execute(
        "SELECT close FROM security_bar_smoke_clean WHERE instrument_id='AAPL'"
    ).fetchone()[0] == 195.0
    assert r.execute(
        "SELECT status FROM write_audit_log WHERE write_id=?", [ok.write_id]
    ).fetchone()[0] == "SUCCESS"

    # 5. 失败路径：stub-fail → rollback + FAILED 审计
    bad = WriteManager(cm).write(WriteRequest(
        run_id="r2", job_id="j2", target_table="security_bar_smoke_clean",
        staging_table="stg_foundation_smoke", write_mode="append_only",
        primary_keys=["instrument_id", "trade_date"],
        validation_report_id="stub-fail-1", source_used="qmt"))
    assert bad.status == "FAILED"
    # clean 仍只有 1 行（失败写未落地）
    assert r.execute(
        "SELECT COUNT(*) FROM security_bar_smoke_clean").fetchone()[0] == 1
    assert r.execute(
        "SELECT COUNT(*) FROM write_audit_log WHERE status='FAILED'"
    ).fetchone()[0] == 1
```

---

## 任务步骤（TDD）

### Step 1: 写上面的 smoke 测试

先写完整测试文件。

### Step 2: 运行

Run: `pytest tests/smoke/test_foundation_smoke.py -v`
Expected: 若 005~009 都已实现 → PASS（1 passed）；若有缺口 → 按报错回到对应任务修复。

### Step 3: 全量验收

Run: `pytest -q && ruff check . && python -m compileall backend scripts`
Expected: 全部通过。
Commit: `test(smoke): add foundation end-to-end smoke test (task 010)`

---

## 自检

- [ ] 串联 005~009 全部模块
- [ ] 成功与失败两条路径都断言（业务语义）
- [ ] 使用临时库，未污染主 DuckDB
- [ ] 仅 mock psutil，未 mock 业务逻辑
