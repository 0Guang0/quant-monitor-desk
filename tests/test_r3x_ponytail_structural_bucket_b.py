"""Slice 4 Bucket B 结构性 ponytail 回归测试。

覆盖范围：snapshot_lineage 共享内核、write_mode 拒绝、live_pilot LOC 上限、
Layer1/2 evidence 拆分、sync mixin 与能力注册表公开 API 等结构性闭合项。
"""

from __future__ import annotations

import inspect
from pathlib import Path

import duckdb
import pytest

from backend.app.core.snapshot_lineage import LINEAGE_REQUIRED_FIELDS, parameter_hash_for
from tests.db_helpers import create_test_write_manager

_REPO_ROOT = Path(__file__).resolve().parents[1]
_OPS_DIR = _REPO_ROOT / "backend/app/ops"
_LAYER1_DIR = _REPO_ROOT / "backend/app/layer1_axes"


def test_snapshot_lineage_kernel_exports_contract_fields():
    """覆盖范围：共享 snapshot_lineage 内核导出（B-015/SC-01）
    测试对象：LINEAGE_REQUIRED_FIELDS、parameter_hash_for
    目的/目标：血缘必填字段与参数哈希须符合跨层合约
    验证点：含 layer_id；parameter_hash 长度为 64
    失败含义：各层快照血缘字段不一致，追溯链断裂
    """
    assert "layer_id" in LINEAGE_REQUIRED_FIELDS
    assert len(parameter_hash_for(rule_version="v", inputs=("a",))) == 64


def test_write_manager_rejects_unimplemented_contract_modes(tmp_path):
    """覆盖范围：未实现 write_mode fail-closed（B-008）
    测试对象：WriteManager.write(write_mode=manual_patch)
    目的/目标：合约列出但未实现的写模式须拒绝并提示允许模式
    验证点：抛出 ValueError 且消息含 not implemented yet
    失败含义：未实现写模式被误用，clean 表写入语义不明
    """
    from backend.app.db.connection import ConnectionManager
    from backend.app.db.migrate import apply_migrations
    from backend.app.db.write_manager import WriteRequest

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
    """覆盖范围：health_check 结构化 stub（B-009）
    测试对象：BaseDataAdapter.health_check
    目的/目标：运维探针须获 STUB_OK 及 supported_domains
    验证点：status=STUB_OK；含 cn_equity_daily_bar
    失败含义：健康检查返回形态漂移，ops 合约无法解析
    """
    from backend.app.datasources.adapters import create_test_adapter
    from backend.app.datasources.source_registry import SourceRegistry

    registry = SourceRegistry()
    registry.load()
    adapter = create_test_adapter("baostock", registry, tmp_path)
    report = adapter.health_check()
    assert report["status"] == "STUB_OK"
    assert "cn_equity_daily_bar" in report["supported_domains"]


def test_live_pilot_modules_under_loc_cap():
    """覆盖范围：live_pilot 拆分后各模块行数上限（OP-01）
    测试对象：backend/app/ops/live_pilot_*.py
    目的/目标：ponytail 拆分后单文件不得膨胀超 LOC 门禁
    验证点：多数模块 ≤300 行；phase3 ≤400；phase4 ≤480
    失败含义：门面模块再次臃肿，后续维护与审查成本失控
    """
    ops = _OPS_DIR
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
    """覆盖范围：fetch_port recent_window 单点定义（OP-03）
    测试对象：fetch_port_common.recent_window_start
    目的/目标：live_pilot 与 interface_probe 不得各自复制 _recent_window_start
    验证点：common 模块导出 recent_window_start；两 fetch_ports 源码无私有副本
    失败含义：时间窗口逻辑分叉，探针与 pilot 行为不一致
    """
    from backend.app.ops import fetch_port_common, interface_probe_fetch_ports, live_pilot_fetch_ports

    assert hasattr(fetch_port_common, "recent_window_start")
    assert "_recent_window_start" not in inspect.getsource(live_pilot_fetch_ports)
    assert "_recent_window_start" not in inspect.getsource(interface_probe_fetch_ports)


def test_l1_04_resolve_task_sandbox_db_helper():
    """覆盖范围：Layer1 evidence 沙箱 DB 解析（L1-04）
    测试对象：evidence_sandbox.resolve_task_sandbox_db
    目的/目标：ingestion 证据路径须复用统一沙箱解析辅助函数
    验证点：模块导出 resolve_task_sandbox_db
    失败含义：各调用方自行拼路径，沙箱隔离易出错
    """
    from backend.app.layer1_axes import evidence_sandbox

    assert hasattr(evidence_sandbox, "resolve_task_sandbox_db")


def test_l1_06_inventory_lives_under_ops():
    """覆盖范围：Layer1 inventory 包位置（L1-06）
    测试对象：ops/layer1_evidence/inventory.py
    目的/目标：inventory 应从 layer1_axes 迁至 ops，与 runtime 分离
    验证点：文件存在且体积 >1000 字节
    失败含义：evidence 与运行时逻辑仍耦合在同一包
    """
    inv = _OPS_DIR / "layer1_evidence/inventory.py"
    assert inv.is_file()
    assert inv.stat().st_size > 1000


def test_l1_07_formatters_split_under_ops():
    """覆盖范围：evidence formatters 拆分（L1-07）
    测试对象：ops.layer1_evidence.formatters
    目的/目标：格式化逻辑迁出 ingestion_evidence，主文件 ≤520 行
    验证点：含 format_phase2_route_preview_md；ingestion_evidence ≤520 行
    失败含义：证据格式化仍堆在巨型模块，可读性与 LOC 门禁失败
    """
    from backend.app.ops.layer1_evidence import formatters

    assert hasattr(formatters, "format_phase2_route_preview_md")
    evidence = _LAYER1_DIR / "ingestion_evidence.py"
    assert len(evidence.read_text(encoding="utf-8").splitlines()) <= 520


def test_l1_09_with_writer_connection_helper():
    """覆盖范围：Layer1 lineage writer 连接样板（L1-09）
    测试对象：lineage._with_writer_connection
    目的/目标：写 lineage 须复用统一 writer 连接上下文管理
    验证点：lineage 模块导出 _with_writer_connection
    失败含义：多处重复 open/close 连接，资源泄漏风险
    """
    from backend.app.layer1_axes import lineage

    assert hasattr(lineage, "_with_writer_connection")


def test_l1_12_axis_loader_observable_defaults_extracted():
    """覆盖范围：axis_loader 可观测字段默认值（L1-12）
    测试对象：axis_loader._ensure_observable_contract_fields
    目的/目标：indicator 构建中的合约字段填充须独立为辅助函数
    验证点：axis_loader 导出 _ensure_observable_contract_fields
    失败含义：默认值逻辑仍内联在巨型 loader，拆分目标未达成
    """
    from backend.app.layer1_axes import axis_loader

    assert hasattr(axis_loader, "_ensure_observable_contract_fields")


def test_sy02_finalize_staged_on_pipeline_mixin():
    """覆盖范围：sync runners 共享 finalize（SY-02）
    测试对象：_PipelineMixin._finalize_staged
    目的/目标：各 runner 须复用 mixin 上的 staged 收尾逻辑
    验证点：_PipelineMixin 含 _finalize_staged
    失败含义：finalize 逻辑复制多份，行为易漂移
    """
    from backend.app.sync.runners import _PipelineMixin

    assert hasattr(_PipelineMixin, "_finalize_staged")


def test_sy06_default_pipeline_config_in_orchestrator():
    """覆盖范围：orchestrator PipelineConfig 默认构造（SY-06）
    测试对象：orchestrator._default_pipeline_config
    目的/目标：Pipeline 配置默认值须单点定义
    验证点：orchestrator 模块导出 _default_pipeline_config
    失败含义：各 runner 自行拼 PipelineConfig，默认值不一致
    """
    from backend.app.sync import orchestrator

    assert hasattr(orchestrator, "_default_pipeline_config")


def test_sy07_job_transition_extras_table_driven():
    """覆盖范围：SyncJobStateMachine 转移矩阵（SY-07）
    测试对象：jobs._JOB_TYPE_TRANSITION_EXTRAS
    目的/目标：job 类型额外转移须表驱动而非散落 if/else
    验证点：jobs 模块导出 _JOB_TYPE_TRANSITION_EXTRAS
    失败含义：状态机转移硬编码，新 job 类型易漏边
    """
    from backend.app.sync import jobs

    assert hasattr(jobs, "_JOB_TYPE_TRANSITION_EXTRAS")


def test_ds04_compat_map_empty():
    """覆盖范围：能力兼容映射清空（DS-04 CLOSED）
    测试对象：ADAPTER_DOMAIN_COMPATIBILITY_MAP
    目的/目标：适配器域须完全来自 registry，兼容表须为空
    验证点：ADAPTER_DOMAIN_COMPATIBILITY_MAP == {}
    失败含义：双轨域定义残留，路由与 registry 可能冲突
    """
    from backend.app.datasources.capability_registry import ADAPTER_DOMAIN_COMPATIBILITY_MAP

    assert ADAPTER_DOMAIN_COMPATIBILITY_MAP == {}


def test_ds06_default_operation_from_capability_registry():
    """覆盖范围：能力注册表默认 operation（DS-06）
    测试对象：SourceCapabilityRegistry.default_operation_for_domain
    目的/目标：cn_equity_daily_bar 默认 operation 应为 fetch_daily_bar
    验证点：返回值 == 'fetch_daily_bar'
    失败含义：能力层默认 operation 错误，服务 fetch 传错操作名
    """
    from backend.app.datasources.capability_registry import SourceCapabilityRegistry

    reg = SourceCapabilityRegistry()
    reg.load()
    assert reg.default_operation_for_domain("cn_equity_daily_bar") == "fetch_daily_bar"


def test_ds07_source_registry_is_loaded_public_api():
    """覆盖范围：SourceRegistry.is_loaded 公开 API（DS-07）
    测试对象：SourceRegistry.is_loaded
    目的/目标：调用方须能查询注册表是否已 load，避免隐式空状态
    验证点：未 load 为 False；load 后为 True
    失败含义：无法判断 registry 就绪状态，易在未加载时路由
    """
    from backend.app.datasources.source_registry import SourceRegistry

    reg = SourceRegistry()
    assert reg.is_loaded() is False
    reg.load()
    assert reg.is_loaded() is True


def test_l2_04_snapshot_writer_module_split():
    """覆盖范围：Layer2 snapshot writer 模块拆分（L2-04）
    测试对象：layer2_sensors.snapshot_writer.Layer2SnapshotWriter
    目的/目标：builder 与 writer 须分离为独立模块
    验证点：Layer2SnapshotWriter 可导入且非 None
    失败含义：写入逻辑仍挤在 builder，职责边界模糊
    """
    from backend.app.layer2_sensors.snapshot_writer import Layer2SnapshotWriter

    assert Layer2SnapshotWriter is not None


def test_l2_05_staged_observations_helper():
    """覆盖范围：Layer2 observation staging 辅助（L2-05）
    测试对象：prepare_staged_observations
    目的/目标：staging 观测数据准备须为可复用函数
    验证点：prepare_staged_observations 可调用
    失败含义：staging 逻辑内联复制，Layer2 写入路径难维护
    """
    from backend.app.layer2_sensors.staged_observations import prepare_staged_observations

    assert callable(prepare_staged_observations)


def test_l2_06_write_staging_helper():
    """覆盖范围：Layer2 staging 写表样板（L2-06）
    测试对象：write_staging_table
    目的/目标：写 staging 表的 DuckDB 样板须抽成共享 helper
    验证点：write_staging_table 可调用
    失败含义：各路径重复 CREATE/INSERT 样板，易漏字段
    """
    from backend.app.layer2_sensors.write_staging import write_staging_table

    assert callable(write_staging_table)
