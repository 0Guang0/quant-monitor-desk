from __future__ import annotations

import json

import pytest
from backend.app.datasources.fetch_result import FetchRequest


def test_cninfoProductLiveFactory_useMockFalseUsesLiveHttpPort(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：cninfo product-live factory 的 use_mock=False 出口
    测试对象：create_cninfo_fetch_port(use_mock=False)
    目的/目标：product live 路径经 live gate 后使用真实 HTTP port，禁止 replay-first 假绿
    验证点：返回 CninfoLiveFetchPort；fetch_payload 产出 cninfo-live source_fetch_id
    失败含义：matrix cninfo 行仍可用 replay fixture 冒充 live PASS
    """
    from backend.app.datasources.fetch_ports.cninfo_port import (
        CninfoLiveFetchPort,
        create_cninfo_fetch_port,
    )

    class _FakeFrame:
        def __init__(self) -> None:
            self.empty = False

        def tail(self, _n: int):
            return self

        def to_dict(self, orient: str):
            assert orient == "records"
            return [{"公告标题": "测试公告", "公告时间": "2026-07-01 10:00:00"}]

    class _FakeAk:
        @staticmethod
        def stock_zh_a_disclosure_report_cninfo(*, symbol: str, start_date: str, end_date: str):
            assert symbol == "600519"
            assert start_date
            assert end_date
            return _FakeFrame()

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setitem(__import__("sys").modules, "akshare", _FakeAk())

    port = create_cninfo_fetch_port(symbols=("sh.600519",), max_rows=5, use_mock=False)
    req = FetchRequest(
        run_id="cninfo-product-live-factory",
        source_id="cninfo",
        data_domain="cn_announcements",
        instrument_id="sh.600519",
    )
    body = json.loads(port.fetch_payload(req).content.decode())

    assert isinstance(port, CninfoLiveFetchPort)
    assert str(body["source_fetch_id"]).startswith("cninfo-live-")
    assert body["filings"]
    assert body["filings"][0]["source_used"] == "cninfo"
