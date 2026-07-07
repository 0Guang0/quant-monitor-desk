"""init_db 最小引导测试。"""

from __future__ import annotations


def test_initDb_createsDuckDbDirectory(tmp_path, monkeypatch) -> None:
    """覆盖范围：scripts/init_db 初始化数据目录
    测试对象：init_db.main 与 DATA_ROOT
    目的/目标：init_db 应在 data_root 下创建 duckdb 子目录及 quant_monitor.duckdb
    验证点：duckdb/ 为目录；quant_monitor.duckdb 为文件
    失败含义：一键建库脚本失败，本地/CI 无法获得默认 DuckDB 路径
    """
    import scripts.init_db as init_db_mod

    data_root = tmp_path / "data"
    monkeypatch.setattr(init_db_mod, "DATA_ROOT", data_root)
    init_db_mod.main([])
    assert (data_root / "duckdb").is_dir()
    assert (data_root / "duckdb" / "quant_monitor.duckdb").is_file()
