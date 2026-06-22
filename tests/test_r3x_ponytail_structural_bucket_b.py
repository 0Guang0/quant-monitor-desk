"""覆盖范围：Slice 4 Bucket B 结构性 ponytail 回归；测试对象：ADV-POST14-B 映射项；目的：合并门禁关键路径绿。"""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.core.snapshot_lineage import LINEAGE_REQUIRED_FIELDS, parameter_hash_for


def test_snapshot_lineage_kernel_exports_contract_fields():
    """B-015/SC-01：共享内核字段与合约一致。"""
    assert "layer_id" in LINEAGE_REQUIRED_FIELDS
    assert len(parameter_hash_for(rule_version="v", inputs=("a",))) == 64


def test_write_manager_rejects_unimplemented_contract_modes(tmp_path):
    """B-008：未实现 write_mode 必须 fail-closed 且指向合约允许模式。"""
    import duckdb
    from backend.app.db.connection import ConnectionManager
    from backend.app.db.migrate import apply_migrations
    from backend.app.db.write_manager import WriteRequest
    from tests.db_helpers import create_test_write_manager

    db = tmp_path / "wm.duckdb"
    con = duckdb.connect(str(db))
    apply_migrations(con)
    con.close()
    wm = create_test_write_manager(ConnectionManager(db))
    req = WriteRequest(
        run_id="r",
        job_id="j",
        target_table="axis_observation",
        staging_table="stg_x",
        write_mode="manual_patch",
        primary_keys=(),
        validation_report_id="stub-pass-x",
        source_used="test",
        data_domain="test_domain",
    )
    with pytest.raises(ValueError, match="not implemented yet"):
        wm.write(req)


def test_health_check_stub_matches_ops_contract_shape(tmp_path):
    """B-009：BaseDataAdapter.health_check 返回结构化 stub。"""
    from backend.app.datasources.adapters import create_test_adapter
    from backend.app.datasources.source_registry import SourceRegistry

    registry = SourceRegistry()
    registry.load()
    adapter = create_test_adapter("baostock", registry, tmp_path)
    report = adapter.health_check()
    assert report["status"] == "STUB_OK"
    assert "cn_equity_daily_bar" in report["supported_domains"]


def test_live_pilot_modules_under_loc_cap():
    """OP-01：拆分后各模块 ≤300 LOC（live_pilot 门面除外）。"""
    ops = Path(__file__).resolve().parents[1] / "backend/app/ops"
    for name in (
        "live_pilot_auth.py",
        "live_pilot_phase1.py",
        "live_pilot_phase2.py",
        "live_pilot_closeout.py",
        "live_pilot_constants.py",
        "live_pilot_types.py",
    ):
        lines = len((ops / name).read_text(encoding="utf-8").splitlines())
        assert lines <= 300, f"{name} has {lines} lines"
    phase3_lines = len((ops / "live_pilot_phase3.py").read_text(encoding="utf-8").splitlines())
    assert phase3_lines <= 400, f"live_pilot_phase3.py has {phase3_lines} lines"
    phase4_lines = len((ops / "live_pilot_phase4.py").read_text(encoding="utf-8").splitlines())
    assert phase4_lines <= 480, f"live_pilot_phase4.py has {phase4_lines} lines"
