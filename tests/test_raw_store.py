"""原始文件存储与 file_registry 注册测试（Round 1 任务 009）。

覆盖范围：原始文件落盘与哈希、注册表写入、去重与 staged 证据挂接。
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.db.write_manager import WriteResult
from backend.app.storage import raw_store
from backend.app.storage.file_registry import FileRegistry
from backend.app.storage.raw_store import RawStore, sha256_hex
from tests.db_helpers import create_test_write_manager

_SAVE_KW = {
    "source": "qmt",
    "data_domain": "daily_bar",
    "file_type": "json",
    "as_of": "2026-06-15",
}


def _save_default(store: RawStore, content: bytes = b"x"):
    return store.save(content, **_SAVE_KW)


def test_sha256Hex_knownInput_matchesExpected() -> None:
    """覆盖范围：sha256_hex 对已知字节的哈希输出
    测试对象：raw_store.sha256_hex
    目的/目标：内容指纹算法须与标准 SHA-256 一致，供去重与校验
    验证点：b'abc' 的哈希等于 NIST 标准向量
    失败含义：哈希实现错误，文件去重与完整性校验全线失效
    """
    assert sha256_hex(b"abc") == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_save_writesFileAndComputesHash(tmp_path: Path) -> None:
    """覆盖范围：RawStore.save 落盘与元数据
    测试对象：RawStore.save
    目的/目标：原始字节写入磁盘并返回 content_hash、as_of 等 SavedRawFile
    验证点：文件内容一致；content_hash=sha256(内容)；as_of 保留入参
    失败含义：原始证据未落盘或哈希不对，注册表无法可信引用文件
    """
    store = RawStore(tmp_path)
    saved = store.save(
        b"hello", source="qmt", data_domain="daily_bar", file_type="json", as_of="2026-06-15"
    )
    assert Path(saved.local_path).read_bytes() == b"hello"
    assert saved.content_hash == sha256_hex(b"hello")
    assert saved.as_of == "2026-06-15"


def test_save_pathLayout_matchesConvention(tmp_path: Path) -> None:
    """覆盖范围：原始文件目录布局约定 raw/{source}/{domain}/{as_of}/
    测试对象：RawStore.save 路径生成
    目的/目标：路径须可预测，便于运维浏览与清理
    验证点：local_path 含 raw/qmt/daily_bar/2026-06-15/；后缀为 {hash}.json
    失败含义：路径布局漂移，下游工具与文档约定的目录结构不一致
    """
    store = RawStore(tmp_path)
    saved = store.save(
        b"hello", source="qmt", data_domain="daily_bar", file_type="json", as_of="2026-06-15"
    )
    expected_hash = sha256_hex(b"hello")
    assert f"raw{os.sep}qmt{os.sep}daily_bar{os.sep}2026-06-15{os.sep}" in saved.local_path
    assert saved.local_path.endswith(f"{expected_hash}.json")


def test_save_fileIdFormat_isHashPrefixPlusSource(tmp_path: Path) -> None:
    """覆盖范围：file_id 由内容哈希前缀与 source 拼接
    测试对象：RawStore.save 的 file_id 规则
    目的/目标：短且确定性的 ID，便于注册表主键与跨系统引用
    验证点：file_id == content_hash[:16] + source
    失败含义：file_id 规则变化，历史注册行与路径无法对齐
    """
    store = RawStore(tmp_path)
    saved = store.save(
        b"hello", source="qmt", data_domain="daily_bar", file_type="json", as_of="2026-06-15"
    )
    assert saved.file_id == saved.content_hash[:16] + "qmt"


def test_save_pathTraversal_raises(tmp_path: Path) -> None:
    """覆盖范围：source 含路径穿越字符时拒绝
    测试对象：RawStore.save 入参校验
    目的/目标：防止 .. 等 source 写出 data_root 沙箱
    验证点：source='..' 抛 ValueError match invalid source
    失败含义：路径穿越可写任意目录，存在任意文件写入风险
    """
    store = RawStore(tmp_path)
    with pytest.raises(ValueError, match="invalid source"):
        store.save(b"x", source="..", data_domain="daily_bar", file_type="json", as_of="2026-06-15")


def test_save_invalidDataDomain_raises(tmp_path: Path) -> None:
    """覆盖范围：data_domain 非法时拒绝
    测试对象：RawStore.save 入参校验
    目的/目标：domain 须为安全标识符，禁止 ../escape
    验证点：data_domain='../escape' 抛 ValueError match invalid data_domain
    失败含义：恶意 domain 可逃逸目录布局或混淆注册分类
    """
    store = RawStore(tmp_path)
    with pytest.raises(ValueError, match="invalid data_domain"):
        store.save(
            b"x",
            source="qmt",
            data_domain="../escape",
            file_type="json",
            as_of="2026-06-15",
        )


def test_save_invalidAsOf_raises(tmp_path: Path) -> None:
    """覆盖范围：as_of 非合法日期字符串时拒绝
    测试对象：RawStore.save 入参校验
    目的/目标：分区目录名须为可解析的 as_of 日期
    验证点：as_of='bad as of!' 抛 ValueError match invalid as_of
    失败含义：非法 as_of 仍落盘，目录排序与查询分区混乱
    """
    store = RawStore(tmp_path)
    with pytest.raises(ValueError, match="invalid as_of"):
        store.save(
            b"x",
            source="qmt",
            data_domain="daily_bar",
            file_type="json",
            as_of="bad as of!",
        )


def test_save_unsupportedFileType_raises(tmp_path: Path) -> None:
    """覆盖范围：不支持的 file_type 扩展名
    测试对象：RawStore.save 类型白名单
    目的/目标：仅允许 json/parquet 等约定类型，避免未知格式入库
    验证点：file_type='xml' 抛 ValueError match unsupported file_type
    失败含义：任意扩展名可写，解析链与注册元数据不可信
    """
    store = RawStore(tmp_path)
    with pytest.raises(ValueError, match="unsupported file_type"):
        store.save(b"x", source="qmt", data_domain="daily_bar", file_type="xml", as_of="2026-06-15")


def test_save_oversizedContent_raises(tmp_path: Path) -> None:
    """覆盖范围：单文件超过 MAX_RAW_FILE_BYTES 时拒绝
    测试对象：RawStore.save 大小上限
    目的/目标：防止超大原始包撑满磁盘或拖垮同步
    验证点：MAX+1 字节抛 ValueError match exceeds max size
    失败含义：无大小护栏，恶意或异常抓取可 OOM/占满分区
    """
    store = RawStore(tmp_path)
    huge = b"x" * (raw_store.MAX_RAW_FILE_BYTES + 1)
    with pytest.raises(ValueError, match="exceeds max size"):
        store.save(
            huge, source="qmt", data_domain="daily_bar", file_type="json", as_of="2026-06-15"
        )


def _cm(tmp_path: Path) -> ConnectionManager:
    cm = ConnectionManager(tmp_path / "t.duckdb")
    with cm.writer() as con:
        apply_migrations(con)
    return cm


def _registry(cm: ConnectionManager) -> FileRegistry:
    return FileRegistry(
        cm,
        create_test_write_manager(cm),
        validation_report_id="stub-pass-registry",
    )


def test_register_newFile_insertsRegistryRow(tmp_path: Path) -> None:
    """覆盖范围：新原始文件首次注册到 file_registry
    测试对象：FileRegistry.register
    目的/目标：落盘后的 SavedRawFile 应插入注册行并标记 pending_validation
    验证点：source 与 content_hash 一致；parse_status=raw_saved、quality_flag=pending_validation
    失败含义：原始文件已存盘但未注册，流水线无法追踪证据
    """
    cm = _cm(tmp_path)
    store = RawStore(tmp_path)
    reg = _registry(cm)
    saved = _save_default(store)
    fid = reg.register(saved)
    with cm.reader() as r:
        got = r.execute(
            "SELECT source, content_hash FROM file_registry WHERE file_id=?",
            [fid],
        ).fetchone()
    assert got == ("qmt", saved.content_hash)
    with cm.reader() as r:
        status = r.execute(
            "SELECT parse_status, quality_flag FROM file_registry WHERE file_id=?",
            [fid],
        ).fetchone()
    assert status == ("raw_saved", "pending_validation")


def test_register_writesAuditLog(tmp_path: Path) -> None:
    """覆盖范围：注册成功时写入 write_audit_log
    测试对象：FileRegistry.register 经 WriteManager 的审计
    目的/目标：每次注册须有 SUCCESS 审计记录 target_table=file_registry
    验证点：write_audit_log 一行 (SUCCESS, file_registry)
    失败含义：注册成功无审计，合规与故障排查缺少写入痕迹
    """
    cm = _cm(tmp_path)
    store = RawStore(tmp_path)
    reg = _registry(cm)
    saved = _save_default(store)
    reg.register(saved)
    with cm.reader() as r:
        audit = r.execute(
            "SELECT status, target_table FROM write_audit_log WHERE target_table='file_registry'"
        ).fetchone()
    assert audit == ("SUCCESS", "file_registry")


def test_register_asOfTimestamp_matchesAsOfArgument(tmp_path: Path) -> None:
    """覆盖范围：注册行 as_of_timestamp 与 save 的 as_of 对齐
    测试对象：FileRegistry.register 时间字段映射
    目的/目标：库内时间维度须与原始文件分区日期一致
    验证点：CAST(as_of_timestamp AS DATE) == '2026-06-15'
    失败含义：注册时间与文件 as_of 错位，按日查询与对账失败
    """
    cm = _cm(tmp_path)
    store = RawStore(tmp_path)
    reg = _registry(cm)
    saved = _save_default(store)
    reg.register(saved)
    with cm.reader() as r:
        as_of_ts = r.execute(
            "SELECT CAST(as_of_timestamp AS DATE) FROM file_registry WHERE file_id=?",
            [saved.file_id],
        ).fetchone()[0]
    assert str(as_of_ts) == "2026-06-15"


def test_exists_whenHashPresent_returnsTrue(tmp_path: Path) -> None:
    """覆盖范围：按 content_hash 查询是否已注册
    测试对象：FileRegistry.exists
    目的/目标：注册前 False，注册后 True，支持去重短路
    验证点：register 前 exists=False；register 后 exists=True
    失败含义：哈希去重探测不准，重复抓取浪费 IO 或插重复行
    """
    cm = _cm(tmp_path)
    store = RawStore(tmp_path)
    reg = _registry(cm)
    saved = _save_default(store)
    assert reg.exists(saved.content_hash) is False
    reg.register(saved)
    assert reg.exists(saved.content_hash) is True


def test_register_duplicateHash_returnsSameFileId(tmp_path: Path) -> None:
    """覆盖范围：同内容哈希重复 register 的幂等
    测试对象：FileRegistry.register 去重
    目的/目标：第二次 register 返回同一 file_id，表中仅一行
    验证点：fid1==fid2；content_hash COUNT=1
    失败含义：重复注册插多行，file_registry 膨胀且审计重复
    """
    cm = _cm(tmp_path)
    store = RawStore(tmp_path)
    reg = _registry(cm)
    saved = _save_default(store)
    fid1 = reg.register(saved)
    fid2 = reg.register(saved)
    assert fid1 == fid2
    with cm.reader() as r:
        cnt = r.execute(
            "SELECT COUNT(*) FROM file_registry WHERE content_hash=?",
            [saved.content_hash],
        ).fetchone()[0]
    assert cnt == 1


def test_register_duplicateHashViaConstraint_returnsSameFileId(tmp_path: Path) -> None:
    """覆盖范围：竞态下 UNIQUE 约束兜底的去重（预检 miss 后插入冲突）
    测试对象：FileRegistry.register 与 _lookup_by_content_hash
    目的/目标：lookup 漏检时仍靠唯一索引返回已有 file_id，不插第二行
    验证点：预插同行后 mock lookup 一次 miss；register 返回原 file_id；COUNT=1
    失败含义：并发双注册产生重复行，哈希唯一约束未转化为幂等语义
    """
    cm = _cm(tmp_path)
    store = RawStore(tmp_path)
    reg = _registry(cm)
    saved = _save_default(store)

    with cm.writer() as con:
        con.execute("BEGIN")
        con.execute(
            """
            INSERT INTO file_registry (
                file_id, file_type, source, local_path, content_hash,
                fetch_time, as_of_timestamp, parse_status, quality_flag
            ) VALUES (
                ?, 'json', 'qmt', '/p', ?,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'parsed', 'ok'
            )
            """,
            [saved.file_id, saved.content_hash],
        )
        con.execute("COMMIT")

    import backend.app.storage.file_registry as fr_mod

    original_lookup = FileRegistry._lookup_by_content_hash

    def _miss_once(self, content_hash, con=None):
        if not hasattr(_miss_once, "called"):
            _miss_once.called = True
            return None
        return original_lookup(self, content_hash, con=con)

    fr_mod.FileRegistry._lookup_by_content_hash = _miss_once  # type: ignore[method-assign]
    try:
        fid = reg.register(saved)
        assert fid == saved.file_id
    finally:
        fr_mod.FileRegistry._lookup_by_content_hash = original_lookup  # type: ignore[method-assign]

    with cm.reader() as r:
        cnt = r.execute(
            "SELECT COUNT(*) FROM file_registry WHERE content_hash=?",
            [saved.content_hash],
        ).fetchone()[0]
    assert cnt == 1


def test_register_whenWriteFails_raisesRuntimeError(tmp_path: Path) -> None:
    """覆盖范围：WriteManager 返回 FAILED 时 register 抛错且不留行
    测试对象：FileRegistry.register 对写失败的处理
    目的/目标：底层写入失败须 RuntimeError，file_registry 保持空
    验证点：抛 RuntimeError match file_registry write failed；COUNT=0
    失败含义：写失败仍报成功或留半行，注册表与磁盘不一致
    """
    cm = _cm(tmp_path)
    store = RawStore(tmp_path)
    wm = MagicMock()
    wm.write.return_value = WriteResult(write_id="x", status="FAILED", error_message="db error")
    reg = FileRegistry(cm, wm, validation_report_id="stub-pass-registry")
    saved = _save_default(store)
    with pytest.raises(RuntimeError, match="file_registry write failed"):
        reg.register(saved)
    with cm.reader() as r:
        cnt = r.execute("SELECT COUNT(*) FROM file_registry").fetchone()[0]
    assert cnt == 0


def test_register_validationRejected_persistsFailedAudit(tmp_path: Path) -> None:
    """覆盖范围：stub-fail 校验拒绝时仍留 FAILED 审计再抛错
    测试对象：FileRegistry.register 校验失败路径
    目的/目标：拒绝注册须写 FAILED audit 且 file_registry 零行
    验证点：RuntimeError；audit=(FAILED, file_registry, validation rejected:...)；file_cnt=0
    失败含义：校验拒绝无审计痕迹，无法追查哪份报告挡下了注册
    """
    cm = _cm(tmp_path)
    store = RawStore(tmp_path)
    reg = FileRegistry(
        cm,
        create_test_write_manager(cm),
        validation_report_id="stub-fail-registry",
    )
    saved = _save_default(store)
    with pytest.raises(RuntimeError, match="file_registry write failed"):
        reg.register(saved)
    with cm.reader() as r:
        audit = r.execute(
            "SELECT status, target_table, error_message FROM write_audit_log"
        ).fetchone()
        file_cnt = r.execute("SELECT COUNT(*) FROM file_registry").fetchone()[0]
    assert file_cnt == 0
    assert audit == ("FAILED", "file_registry", "validation rejected: stub-fail-registry")


def test_stagedEvidence_publicBypassNotExported() -> None:
    """覆盖范围：R3Y-STAGED-REG-001 — file_registry 旁路不得为公开 API
    测试对象：staged_evidence 模块导出面
    目的/目标：staging 写路径须经 WriteManager；legacy 旁路仅保留为私有符号
    验证点：register_staged_file_registry_rows 不在模块属性中；__all__ 不含该名
    失败含义：公开旁路仍可被 ops/adapter 导入，AUD-03 WriteManager 绕过未关闭
    """
    import backend.app.storage.staged_evidence as staged_mod

    assert not hasattr(staged_mod, "register_staged_file_registry_rows")
    assert "register_staged_file_registry_rows" not in getattr(staged_mod, "__all__", ())


def test_stagedEvidence_noProductionReferenceToRegistryBypass() -> None:
    """覆盖范围：R3Y-STAGED-REG-001 — 生产代码不得引用 registry 旁路符号
    测试对象：backend/ 下除 staged_evidence.py 外的全部 .py
    目的/目标：私有化后仅测试可 import 私有 helper；ops/staged_pilot 等须零引用
    验证点：无文件含 register_staged_file_registry_rows 或 _register_staged_file_registry_rows
    失败含义：生产模块仍可调用裸 INSERT 旁路，WriteManager 门禁被击穿
    """
    backend_root = Path(__file__).resolve().parents[1] / "backend"
    legacy = "register_staged_file_registry_rows"
    private = "_register_staged_file_registry_rows"
    offenders: list[str] = []
    for path in backend_root.rglob("*.py"):
        if path.name == "staged_evidence.py":
            continue
        text = path.read_text(encoding="utf-8")
        if legacy in text or private in text:
            offenders.append(str(path.relative_to(backend_root.parent)))
    assert offenders == []


def test_stagedEvidence_pathEscape_rejected(tmp_path: Path) -> None:
    """覆盖范围：staged 证据路径逃出 data_root 时拒绝
    测试对象：_register_staged_file_registry_rows
    目的/目标：FetchResult 中的 raw_file_paths 须在 data_root 沙箱内
    验证点：data_root 外路径抛 ValueError match escapes data_root
    失败含义：外部路径可被注册，证据链与真实落盘位置脱节
    """
    from datetime import UTC, datetime

    from backend.app.datasources.fetch_result import FetchResult
    from backend.app.storage.staged_evidence import _register_staged_file_registry_rows

    cm = _cm(tmp_path)
    data_root = tmp_path / "data"
    data_root.mkdir()
    evil = tmp_path / "outside" / "evil.json"
    evil.parent.mkdir(parents=True)
    evil.write_text("{}", encoding="utf-8")
    result = FetchResult(
        run_id="r1",
        source_id="akshare",
        data_domain="macro_supplementary",
        status="SUCCESS",
        row_count=1,
        fetch_time=datetime.now(UTC).isoformat(),
        raw_file_paths=[str(evil)],
        content_hash="abc123",
        schema_hash="def456",
    )
    with cm.writer() as con:
        with pytest.raises(ValueError, match="escapes data_root"):
            _register_staged_file_registry_rows(con, result, data_root=data_root)


def test_stagedEvidence_rejectsWrongPhase() -> None:
    """覆盖范围：staged evidence 旁路 phase 门禁（R3Y-STAGED-REG-001 私有旁路）
    测试对象：_register_staged_file_registry_rows
    目的/目标：非 phase3_staged 不得旁路写入 file_registry
    验证点：phase=phase4_clean 时 pytest.raises(ValueError, match='phase3_staged')
    失败含义：任意 phase 可写 registry，staged 旁路与 clean 路径混淆
    """
    from datetime import UTC, datetime

    import duckdb
    from backend.app.datasources.fetch_result import FetchResult
    from backend.app.storage.staged_evidence import _register_staged_file_registry_rows

    con = duckdb.connect(":memory:")
    result = FetchResult(
        run_id="r1",
        source_id="akshare",
        data_domain="macro_supplementary",
        status="SUCCESS",
        row_count=1,
        fetch_time=datetime.now(UTC).isoformat(),
        raw_file_paths=["raw.json"],
        content_hash="hash1",
    )
    with pytest.raises(ValueError, match="phase3_staged"):
        _register_staged_file_registry_rows(
            con,
            result,
            data_root=Path("."),
            phase="phase4_clean",
        )


def test_stagedEvidence_allowedPath_registersRow(tmp_path: Path) -> None:
    """覆盖范围：data_root 内合法 staged 证据路径注册
    测试对象：_register_staged_file_registry_rows
    目的/目标：抓取结果中的 raw 文件应插入 file_registry 且 quality_flag=STAGED
    验证点：返回 1 个 file_id；local_path 含 evidence.json；quality_flag=STAGED
    失败含义：合法证据无法挂接注册表，下游校验找不到原始文件
    """
    from datetime import UTC, datetime

    from backend.app.datasources.fetch_result import FetchResult
    from backend.app.storage.staged_evidence import _register_staged_file_registry_rows

    cm = _cm(tmp_path)
    data_root = tmp_path / "data"
    raw_dir = data_root / "raw" / "akshare" / "macro_supplementary" / "2024-06-15"
    raw_dir.mkdir(parents=True)
    raw_file = raw_dir / "evidence.json"
    raw_file.write_text('{"v":1}', encoding="utf-8")
    result = FetchResult(
        run_id="r1",
        source_id="akshare",
        data_domain="macro_supplementary",
        status="SUCCESS",
        row_count=1,
        fetch_time=datetime.now(UTC).isoformat(),
        raw_file_paths=[str(raw_file)],
        content_hash="abc123unique",
        schema_hash="def456",
    )
    with cm.writer() as con:
        ids = _register_staged_file_registry_rows(con, result, data_root=data_root)
    assert len(ids) == 1
    with cm.reader() as r:
        row = r.execute(
            "SELECT local_path, quality_flag FROM file_registry WHERE file_id = ?",
            [ids[0]],
        ).fetchone()
    assert row[1] == "STAGED"
    assert "evidence.json" in row[0]


def test_writeBytesAtomic_writesCompleteFile(tmp_path: Path) -> None:
    """覆盖范围：path_compat.write_bytes_atomic 完整落盘
    测试对象：write_bytes_atomic
    目的/目标：原子 helper 须将完整字节写入目标路径（AC-STOR-01 / S1）
    验证点：目标文件存在且 read_bytes 等于输入
    失败含义：原子写 helper 缺失或直写不完整，证据链无法依赖该 API
    """
    from backend.app.storage.path_compat import write_bytes_atomic

    dest = tmp_path / "evidence.json"
    payload = b'{"v":1}'
    write_bytes_atomic(dest, payload)
    assert dest.read_bytes() == payload


def test_writeBytesAtomic_replaceFailure_cleansTempAndLeavesTargetAbsent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：write_bytes_atomic 在 os.replace 失败时的清理
    测试对象：write_bytes_atomic 错误路径
    目的/目标：replace 前失败不得留下目标文件或残留 temp（AC-STOR-01 / S1）
    验证点：抛 OSError；目标不存在；目录无 .*.tmp.* 残留
    失败含义：失败泄漏半写目标或 temp，崩溃窗口可污染证据目录
    """
    from backend.app.storage.path_compat import write_bytes_atomic

    dest = tmp_path / "evidence.json"

    def _boom(*_args: object, **_kwargs: object) -> None:
        raise OSError("simulated replace failure")

    monkeypatch.setattr(os, "replace", _boom)
    with pytest.raises(OSError, match="simulated replace failure"):
        write_bytes_atomic(dest, b"x")
    assert not dest.exists()
    assert list(tmp_path.glob(".*.tmp.*")) == []


def test_writeBytesAtomic_preexistingTarget_replaceFailure_preservesOriginalBytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：已有目标时 write_bytes_atomic 在 os.replace 失败须保留原字节
    测试对象：write_bytes_atomic 覆盖失败路径
    目的/目标：replace 失败不得损坏既有文件（AC-STOR-03 / A4 helper 层）
    验证点：预置 dest 字节；replace 抛错后 read_bytes 仍等于 original
    失败含义：原子写失败截断或清空已有证据，同路径覆盖场景不可信
    """
    from backend.app.storage.path_compat import write_bytes_atomic

    dest = tmp_path / "evidence.json"
    original = b'{"v":1}'
    dest.write_bytes(original)

    def _boom(*_args: object, **_kwargs: object) -> None:
        raise OSError("simulated replace failure")

    monkeypatch.setattr(os, "replace", _boom)
    with pytest.raises(OSError, match="simulated replace failure"):
        write_bytes_atomic(dest, b'{"v":2}')
    assert dest.read_bytes() == original


def test_writeBytesAtomic_writeFailure_cleansTemp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：write_bytes_atomic 在 open 写阶段失败时的 temp 清理
    测试对象：write_bytes_atomic 写失败错误路径
    目的/目标：写中途异常须删除 temp、不创建目标（A8-D01）
    验证点：handle.write 抛 OSError；目标不存在；无 .*.tmp.* 残留
    失败含义：写失败泄漏 temp 或半写目标，证据目录可被孤儿文件污染
    """
    import builtins

    from backend.app.storage.path_compat import write_bytes_atomic

    dest = tmp_path / "evidence.json"
    real_open = builtins.open

    def _open_fail_on_write(
        path: str | os.PathLike[str],
        mode: str = "r",
        *args: object,
        **kwargs: object,
    ):
        handle = real_open(path, mode, *args, **kwargs)  # type: ignore[arg-type]
        if "w" in mode and "b" in mode:
            real_write = handle.write

            def _write_fail(data: bytes) -> int:
                real_write(data)
                raise OSError("simulated write failure")

            handle.write = _write_fail  # type: ignore[method-assign]
        return handle

    monkeypatch.setattr(builtins, "open", _open_fail_on_write)
    with pytest.raises(OSError, match="simulated write failure"):
        write_bytes_atomic(dest, b"x")
    assert not dest.exists()
    assert list(tmp_path.glob(".*.tmp.*")) == []


def test_save_midWriteFailure_leavesTargetAbsentOrUnchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：RawStore.save 写中途失败时目标文件状态
    测试对象：RawStore.save 与原子写接线
    目的/目标：写失败不得创建半写目标（AC-STOR-03 / S3）
    验证点：os.replace 抛错后目标路径不存在
    失败含义：崩溃或 I/O 异常后留下截断证据文件，证据链完整性破坏
    """
    store = RawStore(tmp_path)

    def _boom(*_args: object, **_kwargs: object) -> None:
        raise OSError("mid-write failure")

    monkeypatch.setattr(os, "replace", _boom)
    with pytest.raises(OSError, match="mid-write failure"):
        store.save(b"new content", **_SAVE_KW)
    expected_hash = sha256_hex(b"new content")
    dest = tmp_path / "raw" / "qmt" / "daily_bar" / "2026-06-15" / f"{expected_hash}.json"
    assert not dest.exists()


def test_save_midWriteFailure_whenTargetExists_preservesOriginalBytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """覆盖范围：已有目标文件时同内容 save 写失败须保留原字节
    测试对象：RawStore.save 同路径覆盖失败
    目的/目标：同 content 二次 save + replace 失败不得损坏既有证据（AC-STOR-03 / A4）
    验证点：两次 save 同 content；失败后 dest read_bytes 仍等于写前 original
    失败含义：同路径 replace 失败截断已有 raw 文件，注册表引用的证据损坏
    """
    store = RawStore(tmp_path)
    content = b"same-payload-for-replace-fail"
    saved = store.save(content, **_SAVE_KW)
    dest = Path(saved.local_path)
    original = dest.read_bytes()
    assert original == content

    def _boom(*_args: object, **_kwargs: object) -> None:
        raise OSError("replace blocked")

    monkeypatch.setattr(os, "replace", _boom)
    with pytest.raises(OSError, match="replace blocked"):
        store.save(content, **_SAVE_KW)
    assert dest.read_bytes() == original


def test_save_csvFileType_writesWithCsvSuffix(tmp_path: Path) -> None:
    """覆盖范围：RawStore.save 对 csv file_type 的落盘与后缀
    测试对象：RawStore.save file_type=csv
    目的/目标：csv 原始证据须写入 {hash}.csv 且字节完整（A8-D02）
    验证点：local_path 以 .csv 结尾；磁盘内容与输入一致
    失败含义：csv 类型未走原子写或后缀错误，下游解析无法定位文件
    """
    store = RawStore(tmp_path)
    payload = b"symbol,close\n000001,10.5\n"
    saved = store.save(
        payload,
        source="qmt",
        data_domain="daily_bar",
        file_type="csv",
        as_of="2026-06-15",
    )
    assert saved.local_path.endswith(".csv")
    assert Path(saved.local_path).read_bytes() == payload


def test_save_repeatedSameContent_isIdempotent(tmp_path: Path) -> None:
    """覆盖范围：同内容重复 RawStore.save 的幂等性
    测试对象：RawStore.save
    目的/目标：同 content_hash 重复保存须同路径同字节（AC-STOR-04 / S4）
    验证点：两次 local_path、content_hash 相同；磁盘字节不变
    失败含义：重复 save 损坏文件或路径漂移，去重与注册引用不可靠
    """
    store = RawStore(tmp_path)
    saved1 = store.save(b"same-payload", **_SAVE_KW)
    saved2 = store.save(b"same-payload", **_SAVE_KW)
    assert saved1.local_path == saved2.local_path
    assert saved1.content_hash == saved2.content_hash
    assert Path(saved1.local_path).read_bytes() == b"same-payload"


def test_save_windowsLongPath_writesSuccessfully(tmp_path: Path) -> None:
    """覆盖范围：Windows 超长路径（≥260 字符）下 RawStore.save 仍可写
    测试对象：RawStore.save 与 path_compat.is_file
    目的/目标：深层 audit-sandbox 目录不得触发 MAX_PATH 失败
    验证点：非 NT 跳过；NT 下 is_file 为真且解析路径长度 ≥260
    失败含义：Windows 证据沙箱路径稍深即保存失败，layer1 取证回归
    """
    import os

    if os.name != "nt":
        pytest.skip("Windows long-path regression only")
    deep_root = tmp_path
    for segment in (
        ".audit-sandbox",
        "pytest-9agent-restored-targeted",
        "test_layer1Ingestion_phase3_taskEvidenceArtifacts0",
        "evidence",
        ".phase3-micro-fetch-sandbox",
        "data",
    ):
        deep_root = deep_root / segment
    store = RawStore(deep_root)
    saved = store.save(
        b'{"observations":[{"metric_value":1.0}]}',
        source="akshare",
        data_domain="macro_supplementary",
        file_type="json",
        as_of="2024-06-15",
    )
    from backend.app.storage.path_compat import is_file

    assert is_file(Path(saved.local_path))
    assert len(str(Path(saved.local_path).resolve())) >= 260
