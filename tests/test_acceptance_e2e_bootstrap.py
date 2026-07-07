"""acceptance_e2e_bootstrap path contract tests."""

from __future__ import annotations

from pathlib import Path

from tests.acceptance_e2e_bootstrap import ACCEPTANCE_DUCKDB_NAME, acceptance_db_path


def test_acceptanceDbPath_matchesAdr015Layout(tmp_path: Path) -> None:
    """覆盖范围：acceptance harness DuckDB 路径契约
    测试对象：acceptance_db_path
    目的/目标：ADR-015 sandbox 下 DB 须落在 duckdb/quant_monitor.duckdb
    验证点：路径 == sandbox_root/duckdb/quant_monitor.duckdb
    失败含义：acceptance bootstrap 路径漂移，live e2e 与 isolation 脚本不一致
    """
    sandbox = tmp_path / "acceptance-sandbox"
    expected = sandbox / "duckdb" / ACCEPTANCE_DUCKDB_NAME
    assert acceptance_db_path(sandbox) == expected
