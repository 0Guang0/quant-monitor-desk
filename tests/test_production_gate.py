"""发布前 production_gate 冒烟测试（ADV-A5-002）。

覆盖范围：scripts/production_gate.py 子进程能否在本仓库正常退出并打印 PASS。
"""

from __future__ import annotations

import subprocess
import sys

from tests.contract_gate_support import PROJECT_ROOT


def test_productionGate_exitsZero() -> None:
    """覆盖范围：运行 scripts/production_gate.py 做发布前冒烟检查
    测试对象：scripts/production_gate.py 子进程退出码与 stdout
    目的/目标：确认发布前门禁脚本在本仓库能正常跑完
    验证点：returncode == 0；stdout 含 production_gate: PASS
    失败含义：发布门禁脚本挂了，CI 或人工发布前检查会误报失败
    """
    script = PROJECT_ROOT / "scripts" / "production_gate.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "production_gate: PASS" in result.stdout
