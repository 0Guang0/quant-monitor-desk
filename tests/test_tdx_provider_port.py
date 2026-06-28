"""R3H-03 TDX family provider port boot extension."""

from __future__ import annotations


def test_tdxProviderPort_mootdxPortModuleExists() -> None:
    """覆盖范围：Execute 9.0 mootdx port 模块可导入
    测试对象：backend.app.datasources.fetch_ports.mootdx_port
    目的/目标：确认 R3H-03 TDX family 第二条独立 source_id port 已落地
    验证点：create_mootdx_fetch_port 可调用
    失败含义：mootdx_port 缺失，9.5 无法闭合
    """
    from backend.app.datasources.fetch_ports.mootdx_port import create_mootdx_fetch_port

    port = create_mootdx_fetch_port(symbols=("sh.600519",), max_rows=3)
    assert port is not None
