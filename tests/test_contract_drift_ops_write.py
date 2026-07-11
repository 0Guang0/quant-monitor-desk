"""Contract drift — ops/write runtime fail-closed（B3V-C01）。

静态 YAML↔常量 parity：`uv run python scripts/check_contract_drift.py --strict`
（亦由 production_gate 调用）。
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from backend.app.ops.db_inspector import _key_tables_from_contract
from tests.db_helpers import (
    create_test_write_manager,
    setup_write_smoke_db,
    write_smoke_request,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WRITE_CONTRACT = _REPO_ROOT / "specs/contracts/write_contract.yaml"


def _load_contract_yaml(path: Path) -> dict:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


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
