"""Foundation 端到端冒烟：迁移、资源守卫、原始存储、注册与写入审计。"""

from __future__ import annotations

from pathlib import Path

import duckdb
from backend.app.core.resource_guard import Decision, ResourceGuard, ResourceSnapshot
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.db.write_manager import WriteRequest
from backend.app.storage.file_registry import FileRegistry
from backend.app.storage.raw_store import RawStore
from tests.db_helpers import create_test_write_manager, insert_stg_foundation_smoke_row

FOUNDATION_TABLES = {
    "schema_version",
    "file_registry",
    "write_audit_log",
    "resource_guard_log",
    "stg_foundation_smoke",
}


def test_foundation_endToEnd_writesCleanAndAudits(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：Round 1 foundation 主路径串联
    测试对象：apply_migrations、ResourceGuard、RawStore、FileRegistry、WriteManager
    目的/目标：验证迁移建表、资源 WARN/OK、原始文件登记、校验门控写入与审计成败各走一路
    验证点：001–002 迁移与 foundation 表齐全；guard WARN 写 log；成功写入 1 行且 audit SUCCESS；stub-fail 写入 FAILED 且不增行
    失败含义：foundation 链路任一环节断裂，后续 batch 数据落库无法信任
    """
    db = tmp_path / "smoke.duckdb"
    con = duckdb.connect(str(db))
    applied = apply_migrations(con)
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    con.close()
    assert "001_foundation" in applied
    assert "002_registry_hardening" in applied
    assert FOUNDATION_TABLES.issubset(tables)

    cm = ConnectionManager(db)
    wm = create_test_write_manager(cm)

    guard_warn = ResourceGuard(profile="eco", con=duckdb.connect(str(db)))
    monkeypatch.setattr(
        guard_warn,
        "snapshot",
        lambda: ResourceSnapshot(3.5, 100, 300, 1),
    )
    warn_decision, _ = guard_warn.check()
    assert warn_decision == Decision.WARN
    assert guard_warn.con.execute("SELECT COUNT(*) FROM resource_guard_log").fetchone()[0] == 1
    guard_warn.con.close()

    guard = ResourceGuard(profile="eco", con=None)
    monkeypatch.setattr(
        guard,
        "snapshot",
        lambda: ResourceSnapshot(8, 100, 300, 1),
    )
    decision, _ = guard.check()
    assert decision == Decision.OK

    store = RawStore(tmp_path)
    reg = FileRegistry(cm, wm, validation_report_id="stub-pass-registry")
    saved = store.save(
        b"raw-bytes", source="qmt", data_domain="daily_bar", file_type="json", as_of="2026-06-15"
    )
    fid = reg.register(saved)
    with cm.reader() as r_reg:
        assert (
            r_reg.execute("SELECT COUNT(*) FROM file_registry WHERE file_id=?", [fid]).fetchone()[0]
            == 1
        )

    with cm.writer() as w:
        insert_stg_foundation_smoke_row(w, "AAPL", "2026-06-15", 195.0)
        w.execute(
            "CREATE TABLE security_bar_smoke_clean AS SELECT * FROM stg_foundation_smoke WHERE 1=0"
        )
    ok = wm.write(
        WriteRequest(
            run_id="r1",
            job_id="j1",
            target_table="security_bar_smoke_clean",
            staging_table="stg_foundation_smoke",
            write_mode="append_only",
            primary_keys=("instrument_id", "trade_date", "adjustment_type"),
            validation_report_id="stub-pass-1",
            source_used="qmt",
            data_domain="cn_equity_daily_bar",
        )
    )
    assert ok.status == "SUCCESS" and ok.rows_inserted == 1

    with cm.reader() as r:
        close_val = r.execute(
            "SELECT close FROM security_bar_smoke_clean WHERE instrument_id='AAPL'"
        ).fetchone()[0]
        assert close_val == 195.0
        assert (
            r.execute(
                "SELECT status FROM write_audit_log WHERE write_id=?",
                [ok.write_id],
            ).fetchone()[0]
            == "SUCCESS"
        )

    bad = wm.write(
        WriteRequest(
            run_id="r2",
            job_id="j2",
            target_table="security_bar_smoke_clean",
            staging_table="stg_foundation_smoke",
            write_mode="append_only",
            primary_keys=("instrument_id", "trade_date"),
            validation_report_id="stub-fail-1",
            source_used="qmt",
            data_domain="cn_equity_daily_bar",
        )
    )
    assert bad.status == "FAILED"
    with cm.reader() as r:
        assert r.execute("SELECT COUNT(*) FROM security_bar_smoke_clean").fetchone()[0] == 1
        failed_audits = r.execute(
            "SELECT COUNT(*) FROM write_audit_log WHERE status='FAILED'"
        ).fetchone()[0]
        assert failed_audits == 1
