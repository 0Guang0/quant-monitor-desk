"""M-G1-03 P1-09 — qmd-data data full-load CLI."""

from __future__ import annotations

import pytest

from tests._m_g1_03_red_stub import red_skip

pytestmark = pytest.mark.skip(reason="M-G1-03 RED: P1-09 full-load CLI (S03)")


def test_qmdDataFullLoad_cliRegisteredInDataCliContract() -> None:
    """覆盖范围：qmd-data data full-load CLI
    测试对象：backend.app.cli.data_commands · data_cli_contract.yaml
    目的/目标：CLI 登记；失败走 CliFailure；默认 --dry-run
    验证点：must_use orchestrator 金路径
    失败含义：平行 CLI 或契约未登记
    """
    red_skip("S03", "P1-09")
