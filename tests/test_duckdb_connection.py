"""DuckDB 连接管理器测试（Round 1 任务 007）。

覆盖范围：读写连接、写锁互斥、资源 pragma 配置及锁文件自愈。
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest
import backend.app.db.connection as conn_mod
from backend.app.db.connection import ConnectionManager, WriteLockError
from backend.app.db.migrate import apply_migrations


def _init(db_path: Path) -> None:
    con = duckdb.connect(str(db_path))
    apply_migrations(con)
    con.close()


class _FakePsutilMem:
    total = 32 * 1024 * 1024 * 1024
    available = 16 * 1024 * 1024 * 1024


def _patch_psutil_mem(monkeypatch) -> None:
    monkeypatch.setattr(conn_mod.psutil, "virtual_memory", lambda: _FakePsutilMem())


def test_writer_writesRow_readerSeesIt(tmp_path: Path) -> None:
    """覆盖范围：writer 写入后 reader 能读到同一行
    测试对象：ConnectionManager.writer / reader
    目的/目标：写读分离连接共享同一 DuckDB 文件，提交后数据对读者可见
    验证点：writer INSERT 后 reader SELECT source == 'qmt'
    失败含义：写读隔离或事务可见性异常，同步流水线读不到刚写入数据
    """
    db = tmp_path / "t.duckdb"
    _init(db)
    cm = ConnectionManager(db)
    with cm.writer() as w:
        w.execute("INSERT INTO file_registry(file_id, source) VALUES ('f1','qmt')")
    with cm.reader() as r:
        got = r.execute("SELECT source FROM file_registry WHERE file_id='f1'").fetchone()
    assert got[0] == "qmt"


def test_writer_whenLockHeld_raisesWriteLockError(tmp_path: Path) -> None:
    """覆盖范围：写锁已被持有时第二个 writer 须被拒绝
    测试对象：ConnectionManager.writer 互斥锁
    目的/目标：同一库同时只允许一个写连接，防止并发写损坏
    验证点：持锁期间新建 ConnectionManager.writer 抛 WriteLockError（write lock held）
    失败含义：双写并发可破坏 DuckDB 文件或审计一致性
    """
    db = tmp_path / "t.duckdb"
    _init(db)
    cm = ConnectionManager(db)
    with cm.writer():
        with pytest.raises(WriteLockError, match="write lock held"):
            with ConnectionManager(db).writer():
                pass


def test_applyPragmas_readerProfile_setsThreadsAndMemory(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：reader 连接应用 eco profile 的线程与内存 pragma（GPT P0-3 别名）
    测试对象：ConnectionManager.reader 的 pragma 配置
    目的/目标：只读连接须按 profile 限制 threads 与 memory_limit
    验证点：threads=2；memory_limit 含 1536 或等价表示
    失败含义：reader 未受资源上限约束，大批量查询可能拖垮主机
    """
    db = tmp_path / "t.duckdb"
    _init(db)
    _assert_reader_threads_and_memory_limit(db, monkeypatch)


def test_reader_appliesThreadsAndMemoryLimit(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：reader 连接应用 eco profile 的线程与内存 pragma
    测试对象：ConnectionManager.reader 的 pragma 配置
    目的/目标：只读路径与 writer 一样遵守 limits 配置
    验证点：threads=2；memory_limit 含 1536 或等价表示
    失败含义：reader pragma 未生效，资源护栏在查询侧失效
    """
    db = tmp_path / "t.duckdb"
    _init(db)
    _assert_reader_threads_and_memory_limit(db, monkeypatch)


def _assert_reader_threads_and_memory_limit(db: Path, monkeypatch=None) -> None:
    if monkeypatch is not None:
        _patch_psutil_mem(monkeypatch)
    cm = ConnectionManager(
        db,
        profile="eco",
        limits={"eco": {"duckdb_memory_max_mb": 1536, "max_threads": 2}},
    )
    with cm.reader() as r:
        threads = r.execute("SELECT current_setting('threads')").fetchone()[0]
        mem = r.execute("SELECT current_setting('memory_limit')").fetchone()[0]
    assert int(threads) == 2
    assert "1536" in mem or "1.5" in mem.lower() or "1.4" in mem.lower()


def test_reader_appliesTempDirectory(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：reader 连接设置 temp_directory 到 DATA_ROOT 下缓存目录
    测试对象：ConnectionManager.reader 的 temp_directory pragma
    目的/目标：临时文件须落在项目数据根下的 duckdb_tmp，便于磁盘治理
    验证点：current_setting 含 duckdb_tmp；data/cache/duckdb_tmp 目录存在
    失败含义：临时文件散落到系统盘或错误路径，长查询占满根分区
    """
    db = tmp_path / "t.duckdb"
    _init(db)
    data_root = tmp_path / "data"
    monkeypatch.setattr(conn_mod, "DATA_ROOT", data_root)
    cm = ConnectionManager(
        db,
        profile="eco",
        limits={"eco": {"duckdb_memory_max_mb": 512, "max_threads": 1}},
    )
    with cm.reader() as r:
        temp = r.execute("SELECT current_setting('temp_directory')").fetchone()[0]
    assert "duckdb_tmp" in temp
    assert data_root.joinpath("cache", "duckdb_tmp").exists()


def test_applyPragmas_setsMaxTempDirectorySize(tmp_path: Path) -> None:
    """覆盖范围：writer 连接设置 max_temp_directory_size
    测试对象：ConnectionManager.writer 的 max_temp_directory_size pragma
    目的/目标：临时目录须有上限，防止 spill 无限增长
    验证点：current_setting 值为 GiB/MiB 量级字符串
    失败含义：临时目录无上限，大批量排序/聚合可能撑爆磁盘
    """
    db = tmp_path / "t.duckdb"
    _init(db)
    cm = ConnectionManager(
        db,
        profile="eco",
        limits={"eco": {"duckdb_memory_max_mb": 512, "max_threads": 1, "duckdb_temp_max_gb": 3}},
    )
    with cm.writer() as w:
        temp_max = w.execute("SELECT current_setting('max_temp_directory_size')").fetchone()[0]
    lower = str(temp_max).lower()
    assert any(unit in lower for unit in ("gib", "mib"))


def test_applyPragmas_ecoProfile_setsThreadsAndMemory(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：writer 连接 eco profile 的 threads pragma
    测试对象：ConnectionManager.writer 对 eco limits 的应用
    目的/目标：写入路径同样遵守 max_threads 配置
    验证点：current_setting('threads') == 2
    失败含义：writer 线程数未受限，与 reader 资源策略不一致
    """
    db = tmp_path / "t.duckdb"
    _init(db)
    _patch_psutil_mem(monkeypatch)
    cm = ConnectionManager(
        db,
        profile="eco",
        limits={"eco": {"duckdb_memory_max_mb": 1536, "max_threads": 2}},
    )
    with cm.writer() as w:
        threads = w.execute("SELECT current_setting('threads')").fetchone()[0]
    assert int(threads) == 2


def test_applyPragmas_batchProfile_usesConfiguredMaxThreads(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：batch profile 使用独立的 max_threads 配置
    测试对象：ConnectionManager 对 profile=batch 的 pragma
    目的/目标：批处理场景允许更高线程上限，与 eco 区分
    验证点：current_setting('threads') == 4（limits.batch.max_threads）
    失败含义：batch 与 eco 共用错误线程数，回补任务过慢或过激
    """
    db = tmp_path / "t.duckdb"
    _init(db)
    _patch_psutil_mem(monkeypatch)
    cm = ConnectionManager(
        db,
        profile="batch",
        limits={"batch": {"duckdb_memory_max_mb": 6144, "max_threads": 4}},
    )
    with cm.writer() as w:
        threads = w.execute("SELECT current_setting('threads')").fetchone()[0]
    assert int(threads) == 4


def test_writer_afterExit_releasesLock(tmp_path: Path) -> None:
    """覆盖范围：writer 上下文正常退出后释放写锁
    测试对象：ConnectionManager.writer 上下文管理器
    目的/目标：with 块结束后下一 writer 应能立即获取锁并写入
    验证点：连续两次 with cm.writer() 成功；第二次写入可读
    失败含义：锁泄漏导致后续所有写操作永久 WriteLockError
    """
    db = tmp_path / "t.duckdb"
    _init(db)
    cm = ConnectionManager(db)
    with cm.writer():
        pass
    with cm.writer() as w:
        w.execute("INSERT INTO file_registry(file_id, source) VALUES ('f2','qmt')")
    with cm.reader() as r:
        assert r.execute("SELECT COUNT(*) FROM file_registry WHERE file_id='f2'").fetchone()[0] == 1


def test_writer_staleLockFromDeadPid_allowsNewWriter(tmp_path: Path) -> None:
    """覆盖范围：锁文件记录已死亡 PID 时的陈旧锁回收
    测试对象：ConnectionManager 写锁文件的 PID 校验
    目的/目标：进程崩溃遗留的锁不得永久阻塞新 writer
    验证点：写入不存在 PID 的锁文件后，新 writer 仍能 INSERT 成功
    失败含义：陈旧锁无法自动清理，需人工删锁才能恢复写入
    """
    db = tmp_path / "t.duckdb"
    _init(db)
    lock_path = db.with_suffix(db.suffix + ".write.lock")
    lock_path.write_text(
        json.dumps({"pid": 999999999, "started_at": "2020-01-01T00:00:00+00:00"}),
        encoding="utf-8",
    )
    cm = ConnectionManager(db)
    with cm.writer() as w:
        w.execute("INSERT INTO file_registry(file_id, source) VALUES ('f3','qmt')")
    with cm.reader() as r:
        assert r.execute("SELECT COUNT(*) FROM file_registry WHERE file_id='f3'").fetchone()[0] == 1


def test_writer_corruptLockFile_autoRecovers(tmp_path: Path) -> None:
    """覆盖范围：锁文件内容非 JSON 时的自愈
    测试对象：ConnectionManager 写锁解析容错
    目的/目标：损坏锁文件应被覆盖重建，不得永久拒绝写入
    验证点：写入 "not-json" 锁后新 writer 仍能 INSERT
    失败含义：一次锁文件损坏即锁死整个库，运维成本高
    """
    db = tmp_path / "t.duckdb"
    _init(db)
    lock_path = db.with_suffix(db.suffix + ".write.lock")
    lock_path.write_text("not-json", encoding="utf-8")
    cm = ConnectionManager(db)
    with cm.writer() as w:
        w.execute("INSERT INTO file_registry(file_id, source) VALUES ('f3','qmt')")
    with cm.reader() as r:
        assert r.execute("SELECT COUNT(*) FROM file_registry WHERE file_id='f3'").fetchone()[0] == 1


def test_writer_exceptionInsideContext_releasesLock(tmp_path: Path) -> None:
    """覆盖范围：writer 上下文内抛异常后仍释放锁
    测试对象：ConnectionManager.writer 的 finally 清理
    目的/目标：业务异常不得导致写锁悬挂
    验证点：with 内 ValueError 后下一次 writer 可正常写入
    失败含义：异常路径泄漏锁，后续同步任务全部失败
    """
    db = tmp_path / "t.duckdb"
    _init(db)
    cm = ConnectionManager(db)
    with pytest.raises(ValueError, match="simulated error"):
        with cm.writer() as w:
            raise ValueError("simulated error inside write")
    with cm.writer() as w:
        w.execute("INSERT INTO file_registry(file_id, source) VALUES ('x','test')")
    with cm.reader() as r:
        assert r.execute("SELECT COUNT(*) FROM file_registry WHERE file_id='x'").fetchone()[0] == 1


def test_writer_connectFailure_releasesLock(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：duckdb.connect 首次失败时锁仍被释放
    测试对象：ConnectionManager.writer 连接失败路径
    目的/目标：连接打不开时不得占着写锁不放
    验证点：第一次 connect 抛 duckdb.Error；第二次 writer 可写入
    失败含义：瞬时连接失败后锁残留，需重启进程才能恢复
    """
    db = tmp_path / "t.duckdb"
    db.parent.mkdir(parents=True, exist_ok=True)
    cm = ConnectionManager(db)
    real_connect = conn_mod.duckdb.connect
    calls = {"n": 0}

    def _connect_once_fail(path, *args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise duckdb.Error("simulated connect failure")
        return real_connect(path, *args, **kwargs)

    monkeypatch.setattr(conn_mod.duckdb, "connect", _connect_once_fail)
    with pytest.raises(duckdb.Error, match="simulated connect"):
        with cm.writer():
            pass
    _init(db)
    with cm.writer() as w:
        w.execute("INSERT INTO file_registry(file_id, source) VALUES ('lock_ok','qmt')")
    with cm.reader() as r:
        cnt = r.execute("SELECT COUNT(*) FROM file_registry WHERE file_id='lock_ok'").fetchone()[0]
        assert cnt == 1


def test_applyPragmas_tempDirectoryWithQuote_doesNotBreakPragma(
    tmp_path: Path, monkeypatch
) -> None:
    """覆盖范围：DATA_ROOT 路径含单引号时 temp_directory pragma 仍合法
    测试对象：ConnectionManager 对含引号路径的 SQL 转义
    目的/目标：特殊字符路径不得导致 pragma 语句语法错误
    验证点：writer 可打开；current_setting('temp_directory') 含 duckdb_tmp
    失败含义：含引号的数据根在 Windows/定制部署下连接直接失败
    """
    db = tmp_path / "t.duckdb"
    _init(db)
    quoted_root = tmp_path / "data'quote"
    monkeypatch.setattr(conn_mod, "DATA_ROOT", quoted_root)
    limits = {"eco": {"duckdb_memory_max_mb": 512, "max_threads": 1}}
    cm = ConnectionManager(db, profile="eco", limits=limits)
    with cm.writer() as w:
        temp = w.execute("SELECT current_setting('temp_directory')").fetchone()[0]
    assert "duckdb_tmp" in temp
