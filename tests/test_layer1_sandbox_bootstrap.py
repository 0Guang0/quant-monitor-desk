"""Tests for Layer1 ingestion sandbox bootstrap (PR-R2b / R3F-HYG-07)."""

from __future__ import annotations

from pathlib import Path

import duckdb
from backend.app.layer1_axes.sandbox_bootstrap import (
    PHASE3_SANDBOX_DIRNAME,
    bootstrap_empty_migrated_db,
    prepare_phase3_sandbox,
    prepare_phase4_data_root,
    prepare_phase4_fallback_sandbox,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_preparePhase3Sandbox_createsMigratedDbAndDataRoot(tmp_path: Path) -> None:
    """覆盖范围：Phase3 证据沙箱是否一次性建好 DB+data_root
    测试对象：prepare_phase3_sandbox
    目的/目标：R2b 抽取共享 bootstrap，消除 ingestion_evidence 重复建库逻辑
    验证点：db/data 路径存在；schema_version 表可读
    失败含义：Phase3 micro-fetch 证据无法隔离复现，回滚计划 I1–I7 风险升高
    """
    evidence_out = tmp_path / "evidence"
    layout = prepare_phase3_sandbox(evidence_out)
    assert layout.db_path.is_file()
    assert layout.data_root.is_dir()
    assert PHASE3_SANDBOX_DIRNAME in layout.base_dir.name
    con = duckdb.connect(str(layout.db_path), read_only=True)
    try:
        row = con.execute("SELECT COUNT(*) FROM schema_version").fetchone()
        assert row is not None and row[0] >= 1
    finally:
        con.close()


def test_preparePhase4FallbackSandbox_matchesRollbackPlanR2b(tmp_path: Path) -> None:
    """覆盖范围：Phase4 fallback 沙箱与 data_root 准备
    测试对象：prepare_phase4_fallback_sandbox / prepare_phase4_data_root
    目的/目标：R2b 覆盖 phase3/4 共享 bootstrap（rollback plan PR-R2b）
    验证点：fallback DB 已迁移；prepare_phase4_data_root 目录存在
    失败含义：Phase4 clean-write 证据仍内联 shutil/duckdb，R2c/R2d 无法继续
    """
    evidence_out = tmp_path / "evidence"
    fallback = prepare_phase4_fallback_sandbox(evidence_out)
    assert fallback.db_path.is_file()
    data_root = prepare_phase4_data_root(evidence_out)
    assert data_root.is_dir()
    assert data_root == evidence_out / ".phase4-clean-write-sandbox" / "data"


def test_bootstrapEmptyMigratedDb_idempotentOnFreshPath(tmp_path: Path) -> None:
    """覆盖范围：空路径 bootstrap 不抛错且 schema_version 可读
    测试对象：bootstrap_empty_migrated_db
    目的/目标：sandbox_bootstrap 为 phase2/3/4 共享最小原语
    验证点：DB 文件存在；schema_version COUNT(*) >= 1
    失败含义：证据捕获在 Windows deep basetemp 下间歇失败或迁移未落地
    """
    db_path = tmp_path / "duckdb" / "quant_monitor.duckdb"
    bootstrap_empty_migrated_db(db_path)
    assert db_path.is_file()
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        row = con.execute("SELECT COUNT(*) FROM schema_version").fetchone()
        assert row is not None and row[0] >= 1
    finally:
        con.close()


def test_bootstrapEmptyMigratedDb_idempotentOnSamePath(tmp_path: Path) -> None:
    """覆盖范围：同一 DB 路径二次 bootstrap 仍成功
    测试对象：bootstrap_empty_migrated_db
    目的/目标：重复 prepare 证据链时不得因已存在文件而失败
    验证点：两次调用后 schema_version 仍可查询
    失败含义：二次证据捕获在已有 duckdb 文件时崩溃
    """
    db_path = tmp_path / "duckdb" / "quant_monitor.duckdb"
    bootstrap_empty_migrated_db(db_path)
    first_mtime = db_path.stat().st_mtime_ns
    bootstrap_empty_migrated_db(db_path)
    assert db_path.is_file()
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        row = con.execute("SELECT COUNT(*) FROM schema_version").fetchone()
        assert row is not None and row[0] >= 1
    finally:
        con.close()
    assert db_path.stat().st_mtime_ns >= first_mtime


def test_preparePhase3Sandbox_doublePrepareRecreatesFreshSandbox(tmp_path: Path) -> None:
    """覆盖范围：二次 prepare_phase3_sandbox 重置并重建沙箱
    测试对象：prepare_phase3_sandbox
    目的/目标：R2b bootstrap 真幂等——重复调用产出干净隔离环境
    验证点：第二次调用后 marker 文件消失；DB 仍可读
    失败含义：二次 prepare 残留旧 data_root 污染证据
    """
    evidence_out = tmp_path / "evidence"
    first = prepare_phase3_sandbox(evidence_out)
    marker = first.data_root / "stale-marker.txt"
    marker.write_text("stale", encoding="utf-8")
    second = prepare_phase3_sandbox(evidence_out)
    assert second.base_dir == first.base_dir
    assert second.db_path.is_file()
    assert not marker.exists()
    con = duckdb.connect(str(second.db_path), read_only=True)
    try:
        row = con.execute("SELECT COUNT(*) FROM schema_version").fetchone()
        assert row is not None and row[0] >= 1
    finally:
        con.close()
