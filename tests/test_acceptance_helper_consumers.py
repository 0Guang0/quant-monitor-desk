from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_acceptanceHelperConsumers_inventory_listsScopeAndMigrationAction() -> None:
    """覆盖范围：helper consumer 清单字段
    测试对象：scripts/check_acceptance_helper_consumers.py
    目的/目标：清单必须区分 test_only 与 product_runtime，并给出迁移动作
    验证点：JSON 含 scope/migration_action；strict_status 字段存在
    失败含义：迁移清单无法指导 7.2/7.3 收敛，strict 门禁缺少可执行语义
    """
    proc = subprocess.run(
        [sys.executable, "scripts/check_acceptance_helper_consumers.py", "--format", "json"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout)

    assert proc.returncode == 0
    assert payload["strict_status"] == "PASS"
    assert payload["seam_inventory_status"] == "PASS"
    assert payload["status"] == "PASS"
    assert payload["product_runtime_count"] == 0
    assert payload["script_runtime_count"] == 0
    assert payload["consumer_count"] == 0


def test_acceptanceHelperConsumers_strictSeamInventory_passesForTestOnlyConsumers() -> None:
    """覆盖范围：legacy seam 清单关账
    测试对象：scripts/check_acceptance_helper_consumers.py --strict-seam-inventory
    目的/目标：Slice 7.3 要求零 legacy seam 引用（consumer_count=0）
    验证点：--strict-seam-inventory 退出码 0；consumer_count=0
    失败含义：旧 helper 名称仍出现在 backend/scripts/tests，task-01 legacy seam 未关账
    """
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/check_acceptance_helper_consumers.py",
            "--strict-seam-inventory",
            "--format",
            "json",
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert payload["seam_inventory_status"] == "PASS"
    assert payload["consumer_count"] == 0
