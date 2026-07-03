"""Tier B CN equity live fetch ports — registry-aligned vendor seams (M-DATA-03)."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
import pytest

from backend.app.datasources.adapters.fetch_port import PortError
from backend.app.datasources.fetch_ports.tier_b_validation_live import (
    AkshareLiveFetchPort,
    EastmoneyLiveFetchPort,
    SinaFinanceLiveFetchPort,
)
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.ops.live_pilot_constants import (
    ORIGINAL_REQUEST2_ENDPOINT_HOST,
    ORIGINAL_REQUEST2_VENDOR_API,
    SIDECAR_REQUEST2_ENDPOINT_HOST,
    SIDECAR_REQUEST2_VENDOR_API,
)


def _cn_req(source_id: str, instrument_id: str = "sh.600519") -> FetchRequest:
    return FetchRequest(
        run_id="tier-b-cn-live-test",
        source_id=source_id,
        data_domain="cn_equity_daily_bar",
        instrument_id=instrument_id,
    )


def _hist_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "日期": "2025-07-01",
                "开盘": 1400.0,
                "最高": 1410.0,
                "最低": 1395.0,
                "收盘": 1405.0,
                "成交量": 1000,
            }
        ]
    )


def test_sinaFinanceLiveFetchPort_usesStockZhADailyVendor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：SinaFinanceLiveFetchPort 真网 seam
    测试对象：SinaFinanceLiveFetchPort.fetch_payload
    目的/目标：sina_finance 必须走 stock_zh_a_daily（新浪链），不得调用 stock_zh_a_hist
    验证点：payload bundle 含 vendor_api=stock_zh_a_daily、upstream=finance.sina.com.cn
    失败含义：三源仍共用 push2his，registry 语义错误
    """
    hist_calls: list[str] = []

    def _forbid_hist(*_a: object, **_k: object) -> pd.DataFrame:
        hist_calls.append("hist")
        raise AssertionError("stock_zh_a_hist must not be used for sina_finance")

    def _sina_daily(*_a: object, **k: object) -> pd.DataFrame:
        assert k.get("symbol") == "sh600519"
        return _hist_frame()

    monkeypatch.setattr("akshare.stock_zh_a_hist", _forbid_hist)
    monkeypatch.setattr("akshare.stock_zh_a_daily", _sina_daily)
    monkeypatch.setattr(
        "backend.app.datasources.fetch_ports.cn_rehearsal_live_ports._run_akshare_call",
        lambda fn: fn(),
    )

    port = SinaFinanceLiveFetchPort(symbols=("sh.600519",), max_rows=3)
    payload = port.fetch_payload(_cn_req("sina_finance"))
    bundle = json.loads(payload.content.decode("utf-8"))

    assert hist_calls == []
    assert bundle["vendor_api"] == SIDECAR_REQUEST2_VENDOR_API
    assert bundle["upstream"] == SIDECAR_REQUEST2_ENDPOINT_HOST
    assert bundle["bars"][0]["source_used"] == "sina_finance"


def test_akshareLiveFetchPort_histEvidenceMetadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：AkshareLiveFetchPort push2his seam
    测试对象：AkshareLiveFetchPort.fetch_payload
    目的/目标：akshare 走 stock_zh_a_hist 且 evidence 标注东财 upstream
    验证点：vendor_api/upstream 与 live_pilot_constants 一致
    失败含义：验收报告无法区分 vendor 链
    """
    monkeypatch.setattr("akshare.stock_zh_a_hist", lambda **_k: _hist_frame())
    monkeypatch.setattr(
        "backend.app.datasources.fetch_ports.tier_b_validation_live._run_akshare_call_with_retry",
        lambda fn: fn(),
    )

    port = AkshareLiveFetchPort(symbols=("sh.600519",), max_rows=3)
    bundle = json.loads(port.fetch_payload(_cn_req("akshare")).content.decode("utf-8"))

    assert bundle["vendor_api"] == ORIGINAL_REQUEST2_VENDOR_API
    assert bundle["upstream"] == ORIGINAL_REQUEST2_ENDPOINT_HOST


def test_akshareHistFetch_retriesWithBackoffBeforeFail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：push2his 有限重试
    测试对象：_run_akshare_call_with_retry
    目的/目标：东财 hist 在 1s/2s/4s 退避下最多尝试 4 次后仍失败则 PortError
    验证点：失败 4 次、sleep 调用 (1,2,4)
    失败含义：单次 RemoteDisconnected 即放弃或无限重试
    """
    from backend.app.datasources.fetch_ports import cn_rehearsal_live_ports as cr

    attempts = {"n": 0}
    sleeps: list[float] = []

    def _always_fail() -> None:
        attempts["n"] += 1
        raise ConnectionError("Remote end closed")

    monkeypatch.setattr("time.sleep", lambda s: sleeps.append(s))

    with pytest.raises(PortError):
        cr._run_akshare_call_with_retry(_always_fail)

    assert attempts["n"] == 4
    assert sleeps == [1, 2, 4]


def test_akshareHistFetch_retriesThenSucceeds(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：push2his 重试成功路径
    测试对象：_run_akshare_call_with_retry
    目的/目标：间歇失败时第二次尝试可成功，不必 FAIL_EXTERNAL
    验证点：总尝试 2 次、返回成功值
    失败含义：重试逻辑未生效
    """
    from backend.app.datasources.fetch_ports import cn_rehearsal_live_ports as cr

    attempts = {"n": 0}

    def _flaky() -> str:
        attempts["n"] += 1
        if attempts["n"] < 2:
            raise ConnectionError("Remote end closed")
        return "ok"

    monkeypatch.setattr("time.sleep", lambda _s: None)
    assert cr._run_akshare_call_with_retry(_flaky) == "ok"
    assert attempts["n"] == 2


def test_eastmoneyLiveFetchPort_usesHistRetryPath(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：EastmoneyLiveFetchPort 与 akshare 共享 hist+retry
    测试对象：EastmoneyLiveFetchPort.fetch_payload
    目的/目标：eastmoney validation hist 仍走 push2his 但经重试包装
    验证点：_run_akshare_call_with_retry 被调用
    失败含义：eastmoney 未获得与 akshare 相同的网络韧性
    """
    retry_used: dict[str, bool] = {"v": False}

    def _retry(fn: Any) -> Any:
        retry_used["v"] = True
        return fn()

    monkeypatch.setattr(
        "backend.app.datasources.fetch_ports.tier_b_validation_live._run_akshare_call_with_retry",
        _retry,
    )
    monkeypatch.setattr("akshare.stock_zh_a_hist", lambda **_k: _hist_frame())

    port = EastmoneyLiveFetchPort(symbols=("sh.600519",), max_rows=3)
    port.fetch_payload(_cn_req("eastmoney"))
    assert retry_used["v"] is True
