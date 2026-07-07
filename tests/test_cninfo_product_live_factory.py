from __future__ import annotations

import json

import pytest
from backend.app.datasources.fetch_result import FetchRequest


def test_cninfoProductLiveFactory_useMockFalseUsesReplayFirstPort(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：cninfo product-live factory 的 use_mock=False 出口
    测试对象：create_cninfo_fetch_port(use_mock=False)
    目的/目标：product live 路径经 live gate 后使用 replay-first port，不依赖外部 akshare 网络
    验证点：返回 CninfoProductLiveFetchPort；fetch_payload 产出 cninfo filings metadata
    失败含义：pre-commit/full pytest 会被外部 CNINFO 网络波动打红，product-live 口径不稳定
    """
    from backend.app.datasources.fetch_ports.cninfo_port import (
        CninfoProductLiveFetchPort,
        create_cninfo_fetch_port,
    )

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")

    port = create_cninfo_fetch_port(symbols=("sh.600519",), max_rows=5, use_mock=False)
    req = FetchRequest(
        run_id="cninfo-product-live-factory",
        source_id="cninfo",
        data_domain="cn_announcements",
        instrument_id="sh.600519",
    )
    body = json.loads(port.fetch_payload(req).content.decode())

    assert isinstance(port, CninfoProductLiveFetchPort)
    assert body["filings"]
    assert body["filings"][0]["source_used"] == "cninfo"
