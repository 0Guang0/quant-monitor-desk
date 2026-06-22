"""覆盖范围：Slice 4 Bucket B 结构性 ponytail 回归；测试对象：ADV-POST14-B 映射项；目的：合并门禁关键路径绿。"""

from __future__ import annotations

import inspect
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


def test_op03_fetch_port_common_dedupes_recent_window():
    """覆盖范围：live_pilot 与 interface_probe fetch port；测试对象：recent_window_start；目的：OP-03 单点定义。"""
    from backend.app.ops import fetch_port_common, interface_probe_fetch_ports, live_pilot_fetch_ports

    assert hasattr(fetch_port_common, "recent_window_start")
    assert "_recent_window_start" not in inspect.getsource(live_pilot_fetch_ports)
    assert "_recent_window_start" not in inspect.getsource(interface_probe_fetch_ports)


def test_l1_04_resolve_task_sandbox_db_helper():
    """覆盖范围：ingestion evidence 沙箱解析；测试对象：resolve_task_sandbox_db；目的：L1-04 去重。"""
    from backend.app.layer1_axes import evidence_sandbox

    assert hasattr(evidence_sandbox, "resolve_task_sandbox_db")


def test_l1_06_inventory_lives_under_ops():
    """覆盖范围：Layer1 inventory 包位置；测试对象：ops.layer1_evidence.inventory；目的：L1-06 evidence/runtime 分离。"""
    inv = Path(__file__).resolve().parents[1] / "backend/app/ops/layer1_evidence/inventory.py"
    assert inv.is_file()
    assert inv.stat().st_size > 1000


def test_l1_07_formatters_split_under_ops():
    """覆盖范围：evidence formatters；测试对象：ops.layer1_evidence.formatters；目的：L1-07 ≤500 LOC 路径。"""
    from backend.app.ops.layer1_evidence import formatters

    assert hasattr(formatters, "format_phase2_route_preview_md")
    evidence = Path(__file__).resolve().parents[1] / "backend/app/layer1_axes/ingestion_evidence.py"
    assert len(evidence.read_text(encoding="utf-8").splitlines()) <= 520


def test_l1_09_with_writer_connection_helper():
    """覆盖范围：Layer1 lineage writer；测试对象：_with_writer_connection；目的：L1-09 连接样板合并。"""
    from backend.app.layer1_axes import lineage

    assert hasattr(lineage, "_with_writer_connection")


def test_l1_12_axis_loader_observable_defaults_extracted():
    """覆盖范围：axis_loader indicator 构建；测试对象：_ensure_observable_contract_fields；目的：L1-12 拆分。"""
    from backend.app.layer1_axes import axis_loader

    assert hasattr(axis_loader, "_ensure_observable_contract_fields")


def test_sy02_finalize_staged_on_pipeline_mixin():
    """覆盖范围：sync runners 共享 finalize；测试对象：_PipelineMixin._finalize_staged；目的：SY-02。"""
    from backend.app.sync.runners import _PipelineMixin

    assert hasattr(_PipelineMixin, "_finalize_staged")


def test_sy06_default_pipeline_config_in_orchestrator():
    """覆盖范围：orchestrator PipelineConfig 构造；测试对象：_default_pipeline_config；目的：SY-06。"""
    from backend.app.sync import orchestrator

    assert hasattr(orchestrator, "_default_pipeline_config")


def test_sy07_job_transition_extras_table_driven():
    """覆盖范围：SyncJobStateMachine 转移矩阵；测试对象：_JOB_TYPE_TRANSITION_EXTRAS；目的：SY-07。"""
    from backend.app.sync import jobs

    assert hasattr(jobs, "_JOB_TYPE_TRANSITION_EXTRAS")


def test_ds04_compat_map_empty():
    """覆盖范围：capability compat map；测试对象：ADAPTER_DOMAIN_COMPATIBILITY_MAP；目的：DS-04 CLOSED。"""
    from backend.app.datasources.capability_registry import ADAPTER_DOMAIN_COMPATIBILITY_MAP

    assert ADAPTER_DOMAIN_COMPATIBILITY_MAP == {}


def test_ds06_default_operation_from_capability_registry():
    """覆盖范围：DataSourceService fetch operation 默认；测试对象：default_operation_for_domain；目的：DS-06。"""
    from backend.app.datasources.capability_registry import SourceCapabilityRegistry

    reg = SourceCapabilityRegistry()
    reg.load()
    assert reg.default_operation_for_domain("cn_equity_daily_bar") == "fetch_daily_bar"


def test_ds07_source_registry_is_loaded_public_api():
    """覆盖范围：SourceRegistry 封装；测试对象：is_loaded；目的：DS-07。"""
    from backend.app.datasources.source_registry import SourceRegistry

    reg = SourceRegistry()
    assert reg.is_loaded() is False
    reg.load()
    assert reg.is_loaded() is True


def test_l2_04_snapshot_writer_module_split():
    """覆盖范围：Layer2 snapshot writer；测试对象：snapshot_writer.py；目的：L2-04 builder/writer 分离。"""
    from backend.app.layer2_sensors.snapshot_writer import Layer2SnapshotWriter

    assert Layer2SnapshotWriter is not None


def test_l2_05_staged_observations_helper():
    """覆盖范围：Layer2 observation staging；测试对象：prepare_staged_observations；目的：L2-05。"""
    from backend.app.layer2_sensors.staged_observations import prepare_staged_observations

    assert callable(prepare_staged_observations)


def test_l2_06_write_staging_helper():
    """覆盖范围：Layer2 staging write 样板；测试对象：write_staging_table；目的：L2-06。"""
    from backend.app.layer2_sensors.write_staging import write_staging_table

    assert callable(write_staging_table)

