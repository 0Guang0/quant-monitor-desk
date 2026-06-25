"""Contract drift tests — ops db-inspect YAML SSOT and WriteManager parity (B3V-C01).

覆盖范围：ops_db_inspect_contract.yaml 与 write_contract.yaml 对 runtime 的漂移检测。
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.db.write_manager import WriteManager, WriteRequest
from backend.app.ops.db_inspector import (
    DEFERRED_ITEM_MAPPING,
    KEY_TABLES,
    _deferred_mapping_from_contract,
)
from tests.db_helpers import create_test_write_manager

_REPO_ROOT = Path(__file__).resolve().parents[1]
_OPS_CONTRACT = _REPO_ROOT / "specs/contracts/ops_db_inspect_contract.yaml"
_WRITE_CONTRACT = _REPO_ROOT / "specs/contracts/write_contract.yaml"


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def test_opsInspect_keyTables_matchContract() -> None:
    """覆盖范围：db-inspect key_tables 全量列表
    测试对象：KEY_TABLES vs ops_db_inspect_contract.yaml key_tables
    目的/目标：契约 YAML 为 SSOT；仅改 YAML 未同步 loader 时漂移测 FAIL
    验证点：运行时 tuple 与契约列表顺序、元素完全一致
    失败含义：inspect 输出表清单与冻结契约分叉，审计 gate 不可信
    """
    contract_tables = tuple(_load_yaml(_OPS_CONTRACT)["key_tables"])
    assert KEY_TABLES == contract_tables


def test_opsInspect_deferredMapping_matchContract() -> None:
    """覆盖范围：deferred_item_mapping 全量条目
    测试对象：DEFERRED_ITEM_MAPPING vs ops_db_inspect_contract.yaml
    目的/目标：延期项 id 与 evidence_fields/rule 与契约一致
    验证点：运行时 tuple 与契约规范化结果逐条相等
    失败含义：延期项追溯字段与文档不一致，Plan/Audit 对照断档
    """
    expected = _deferred_mapping_from_contract(_load_yaml(_OPS_CONTRACT))
    assert DEFERRED_ITEM_MAPPING == expected


def test_writeContract_implementedModes_matchWriteManager() -> None:
    """覆盖范围：write_contract implemented_modes 与 WriteManager 支持集
    测试对象：write_contract.yaml implemented_modes vs WriteManager.SUPPORTED_MODES
    目的/目标：已实现写模式契约与 runtime 枚举 parity
    验证点：implemented_modes tuple 与 SUPPORTED_MODES 完全一致
    失败含义：契约宣称支持的模式与代码不一致，调用方误用 reserved 模式
    """
    implemented = tuple(_load_yaml(_WRITE_CONTRACT)["implemented_modes"])
    assert implemented == WriteManager.SUPPORTED_MODES


def test_writeContract_reservedModes_matchUnsupportedModes() -> None:
    """覆盖范围：write_contract reserved_modes 与 WriteManager 未实现集
    测试对象：write_contract.yaml reserved_modes vs WriteManager.UNSUPPORTED_MODES
    目的/目标：契约 reserved 模式与 runtime 早拒枚举 parity
    验证点：reserved_modes tuple 与 UNSUPPORTED_MODES 完全一致
    失败含义：契约 reserved 与代码早拒集分叉，漂移 gate 漏检未实现模式
    """
    reserved = tuple(_load_yaml(_WRITE_CONTRACT)["reserved_modes"])
    assert reserved == WriteManager.UNSUPPORTED_MODES


def _write_setup(tmp_path: Path) -> ConnectionManager:
    cm = ConnectionManager(tmp_path / "t.duckdb")
    with cm.writer() as con:
        apply_migrations(con)
        con.execute(
            "INSERT INTO stg_foundation_smoke VALUES ('AAPL','2026-06-15',195.0,'qmt','b1')"
        )
        con.execute(
            "CREATE TABLE security_bar_smoke_clean AS "
            "SELECT * FROM stg_foundation_smoke WHERE 1=0"
        )
    return cm


def _write_req(mode: str) -> WriteRequest:
    return WriteRequest(
        run_id="r1",
        job_id="j1",
        target_table="security_bar_smoke_clean",
        staging_table="stg_foundation_smoke",
        write_mode=mode,
        primary_keys=("instrument_id", "trade_date"),
        validation_report_id="stub-pass-1",
        source_used="qmt",
        data_domain="cn_equity_daily_bar",
    )


def test_writeManager_reservedModes_rejectWithoutWrite(tmp_path: Path) -> None:
    """覆盖范围：write_contract reserved_modes 早拒且无写副作用
    测试对象：WriteManager.write 对 reserved write_mode 的处理
    目的/目标：reserved 模式稳定 ValueError，目标表行数不变
    验证点：每个 reserved 模式抛约定错误；clean 表 COUNT 前后相等
    失败含义：未实现模式误写或静默成功，生产写路径语义错误
    """
    reserved = tuple(_load_yaml(_WRITE_CONTRACT)["reserved_modes"])
    cm = _write_setup(tmp_path)
    wm = create_test_write_manager(cm)
    with cm.writer() as con:
        before = con.execute("SELECT COUNT(*) FROM security_bar_smoke_clean").fetchone()[0]
    for mode in reserved:
        with pytest.raises(
            ValueError,
            match=r"defined in contract but not implemented yet",
        ):
            wm.write(_write_req(mode))
        with cm.writer() as con:
            after = con.execute("SELECT COUNT(*) FROM security_bar_smoke_clean").fetchone()[0]
        assert after == before, f"reserved mode {mode!r} must not mutate target table"
