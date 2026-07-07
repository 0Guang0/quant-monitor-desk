"""Contract drift tests — ops db-inspect YAML SSOT and WriteManager parity (B3V-C01).

Artifact-gate：YAML↔常量 parity；CI 可迁至 scripts/check_contract_drift.py 减负。
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from backend.app.db.write_manager import WriteManager
from backend.app.ops.db_inspector import (
    DEFERRED_ITEM_MAPPING,
    FUTURE_PHASE_KEY_TABLES,
    KEY_TABLES,
    REQUIRED_TOP_LEVEL_FIELDS,
    _deferred_mapping_from_contract,
    _key_tables_from_contract,
)
from tests.db_helpers import (
    create_test_write_manager,
    setup_write_smoke_db,
    write_smoke_request,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_OPS_CONTRACT = _REPO_ROOT / "specs/contracts/ops_db_inspect_contract.yaml"
_WRITE_CONTRACT = _REPO_ROOT / "specs/contracts/write_contract.yaml"


def _load_contract_yaml(path: Path) -> dict:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def test_opsInspect_keyTables_matchContract() -> None:
    """覆盖范围：db-inspect key_tables 全量列表
    测试对象：KEY_TABLES vs ops_db_inspect_contract.yaml key_tables
    目的/目标：契约 YAML 为 SSOT；仅改 YAML 未同步 loader 时漂移测 FAIL
    验证点：运行时 tuple 与契约列表顺序、元素完全一致
    失败含义：inspect 输出表清单与冻结契约分叉，审计 gate 不可信
    """
    contract_tables = tuple(_load_contract_yaml(_OPS_CONTRACT)["key_tables"])
    assert KEY_TABLES == contract_tables


def test_opsInspect_keyTables_rejectsEmptyContract() -> None:
    """覆盖范围：ops inspect 契约 loader 对空 key_tables 的 fail-closed
    测试对象：_key_tables_from_contract 对缺失/空 key_tables 的处理
    目的/目标：空契约不得静默降级为空表清单（DOUBT-01 fail-open 修复）
    验证点：空 dict 或空 key_tables 列表均 raise ValueError
    失败含义：损坏/空契约仍允许 inspect 运行，运维看不到配置缺失
    """
    with pytest.raises(ValueError, match="key_tables required"):
        _key_tables_from_contract({})
    with pytest.raises(ValueError, match="key_tables required"):
        _key_tables_from_contract({"key_tables": []})


def test_opsInspect_futurePhaseKeyTables_matchContract() -> None:
    """覆盖范围：Layer5 前向表清单 future_phase_key_tables
    测试对象：FUTURE_PHASE_KEY_TABLES vs ops_db_inspect_contract.yaml
    目的/目标：AA-B3V-ADV-01 硬编码清单改为契约 SSOT，防 Batch5 前瞻表漂移
    验证点：运行时 frozenset 与契约列表元素完全一致
    失败含义：migration 门禁与 inspect 前向清单分叉，L5 表边界不可信
    """
    contract_tables = frozenset(_load_contract_yaml(_OPS_CONTRACT)["future_phase_key_tables"])
    assert FUTURE_PHASE_KEY_TABLES == contract_tables


def test_opsInspect_requiredOutputFields_matchContract() -> None:
    """覆盖范围：inspect JSON 顶层必填字段清单
    测试对象：REQUIRED_TOP_LEVEL_FIELDS vs ops_db_inspect_contract.yaml
    目的/目标：A4 硬编码 required 字段改为契约 SSOT
    验证点：运行时 tuple 与 required_output_fields 顺序、元素完全一致
    失败含义：CLI/证据链必填字段与冻结契约不一致
    """
    contract_fields = tuple(_load_contract_yaml(_OPS_CONTRACT)["required_output_fields"])
    assert REQUIRED_TOP_LEVEL_FIELDS == contract_fields


def test_opsInspect_deferredMapping_matchContract() -> None:
    """覆盖范围：deferred_item_mapping 全量条目
    测试对象：DEFERRED_ITEM_MAPPING vs ops_db_inspect_contract.yaml
    目的/目标：延期项 id 与 evidence_fields/rule 与契约一致
    验证点：运行时 tuple 与契约规范化结果逐条相等（item_id 排序物化）
    失败含义：延期项追溯字段与文档不一致，Plan/Audit 对照断档
    """
    expected = _deferred_mapping_from_contract(_load_contract_yaml(_OPS_CONTRACT))
    assert DEFERRED_ITEM_MAPPING == expected


@pytest.mark.parametrize(
    ("contract_key", "manager_attr"),
    [
        ("implemented_modes", "SUPPORTED_MODES"),
        ("reserved_modes", "UNSUPPORTED_MODES"),
    ],
)
def test_writeContract_modes_matchWriteManager(contract_key: str, manager_attr: str) -> None:
    """覆盖范围：write_contract 分栏与 WriteManager 支持/未实现集 parity
    测试对象：write_contract.yaml implemented_modes/reserved_modes vs WriteManager 类常量
    目的/目标：契约分栏与 runtime 枚举双向锁定，防漂移
    验证点：契约 tuple 与对应 WriteManager 类属性完全一致
    失败含义：契约宣称的模式集与代码早拒/支持集分叉
    """
    contract_modes = tuple(_load_contract_yaml(_WRITE_CONTRACT)[contract_key])
    runtime_modes = getattr(WriteManager, manager_attr)
    assert contract_modes == runtime_modes


def test_writeContract_writeModeEnum_matchesImplementedUnionReserved() -> None:
    """覆盖范围：write_request.write_mode enum 与 implemented∪reserved 并集
    测试对象：write_contract.yaml write_request.fields.write_mode vs 顶层分栏
    目的/目标：enum 声明覆盖全部已实现+保留模式，防仅改 enum 不同步分栏
    验证点：enum tuple == implemented_modes + reserved_modes（顺序一致）
    失败含义：API/契约 enum 与分栏漂移，调用方可传入未登记模式
    """
    raw = _load_contract_yaml(_WRITE_CONTRACT)
    implemented = tuple(raw["implemented_modes"])
    reserved = tuple(raw["reserved_modes"])
    enum_modes = tuple(raw["write_request"]["fields"]["write_mode"])
    assert enum_modes == implemented + reserved


def test_writeManager_reservedModes_rejectWithoutWrite(tmp_path: Path) -> None:
    """覆盖范围：write_contract reserved_modes 早拒且无写副作用
    测试对象：WriteManager.write 对 reserved write_mode 的处理
    目的/目标：reserved 模式稳定 ValueError，目标表行数不变
    验证点：每个 reserved 模式抛约定错误；循环结束后 clean 表 COUNT 仍等于初始值
    失败含义：未实现模式误写或静默成功，生产写路径语义错误
    """
    reserved = tuple(_load_contract_yaml(_WRITE_CONTRACT)["reserved_modes"])
    cm = setup_write_smoke_db(tmp_path, with_clean_table=True)
    wm = create_test_write_manager(cm)
    with cm.writer() as con:
        before = con.execute("SELECT COUNT(*) FROM security_bar_smoke_clean").fetchone()[0]
    for mode in reserved:
        with pytest.raises(
            ValueError,
            match=r"defined in contract but not implemented yet",
        ):
            wm.write(write_smoke_request(mode))
    with cm.writer() as con:
        after = con.execute("SELECT COUNT(*) FROM security_bar_smoke_clean").fetchone()[0]
    assert after == before, "reserved modes must not mutate target table"
