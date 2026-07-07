"""R3-DCP-02 S02-02 — fred_port incremental window tests."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from unittest.mock import patch

import pytest

from backend.app.datasources.fetch_ports.fred_port import (
    MAX_WINDOW_DAYS,
    FredLiveFetchPort,
    FredMockFetchPort,
    create_fred_fetch_port,
)
from backend.app.datasources.fetch_result import FetchRequest

FIXED_TODAY = date(2026, 6, 30)


def _req(**kwargs) -> FetchRequest:
    base = {
        "run_id": "run-port",
        "source_id": "fred",
        "data_domain": "macro_series",
        "instrument_id": "DGS10",
    }
    base.update(kwargs)
    return FetchRequest(**base)


def test_fredPort_startTime_mapsToObservationStart() -> None:
    """覆盖范围：FetchRequest.start_time → FRED observation_start
    测试对象：FredLiveFetchPort._live_observations
    目的/目标：增量窗由调用方水位注入，非固定回溯
    验证点：mock HTTP 参数 observation_start == 2026-01-15
    失败含义：port 忽略 start_time，增量水位失效
    """
    port = FredLiveFetchPort(series_ids=("DGS10",), max_rows=3)
    captured: dict[str, str] = {}

    def _fake_urlopen(url, timeout=30):
        captured["url"] = url

        class _Resp:
            def read(self):
                return b'{"observations":[{"date":"2026-01-20","value":"4.2"}]}'

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        return _Resp()

    with patch.dict("os.environ", {"FRED_API_KEY": "a" * 32}):
        with patch("urllib.request.urlopen", _fake_urlopen):
            port.fetch_payload(_req(start_time="2026-01-15"))
    assert "observation_start=2026-01-15" in captured["url"]


def test_fredPort_coldStart_usesCappedWindow() -> None:
    """覆盖范围：无 start_time 时 capped 冷启动窗
    测试对象：FredMockFetchPort._resolve_observation_start
    目的/目标：冷启动回溯不超过 MAX_WINDOW_DAYS
    验证点：since ≈ today-120（容差 1 天）
    失败含义：无水位时拉无限历史，违反 cap
    """
    port = FredMockFetchPort(series_ids=("DGS10",), max_rows=3)
    with patch(
        "backend.app.datasources.fetch_ports.fred_port.datetime",
        wraps=datetime,
    ) as mock_dt:
        mock_dt.now.return_value = datetime.combine(FIXED_TODAY, datetime.min.time(), tzinfo=UTC)
        start = port._resolve_observation_start(_req())
    assert start is not None
    assert (FIXED_TODAY - start).days == MAX_WINDOW_DAYS


def test_fredPort_mock_filtersObservationsBeforeStart() -> None:
    """覆盖范围：mock 路径按 start_time 过滤观测
    测试对象：FredMockFetchPort.fetch_payload
    目的/目标：replay 只保留 since 之后的观测点
    验证点：start_time=今天-15天 时 row_count<=2（过滤掉更旧点）
    失败含义：mock 仍返回全窗，增量语义无法在 CI 证明
    """
    port = create_fred_fetch_port(series_ids=("DGS10",), max_rows=3, use_mock=True)
    since = (FIXED_TODAY - timedelta(days=15)).isoformat()
    with patch(
        "backend.app.datasources.fetch_ports.fred_port.datetime",
        wraps=datetime,
    ) as mock_dt:
        mock_dt.now.return_value = datetime.combine(FIXED_TODAY, datetime.min.time(), tzinfo=UTC)
        payload = port.fetch_payload(_req(start_time=since))
    assert payload.row_count >= 1
    import json

    bundle = json.loads(payload.content.decode())
    for obs in bundle["observations"]:
        assert obs["observation_date"] >= since


def test_fredPort_live_rejectsWithoutApiKey(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：live 分支无 key 负例
    测试对象：create_fred_fetch_port(use_mock=False)
    目的/目标：无 FRED_API_KEY 须 USER_AUTH_REQUIRED（禁止 silent 回退 mock）
    验证点：PortError status == USER_AUTH_REQUIRED
    失败含义：EasyXT 式 silent 换源/回退
    """
    from backend.app.datasources.adapters.fetch_port import PortError
    from backend.app.datasources.product_live_gate import ProductLiveGateError

    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    port = create_fred_fetch_port(series_ids=("DGS10",), max_rows=3, use_mock=False)
    with pytest.raises(PortError) as exc_info:
        port.fetch_payload(_req())
    assert exc_info.value.status == "USER_AUTH_REQUIRED"


def test_fredPort_live_succeedsWhenKeyPresent(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：live 分支有 key 时可 fetch
    测试对象：create_fred_fetch_port(use_mock=False) + patched HTTP
    目的/目标：FRED_API_KEY 存在时 live port 不抛 USER_AUTH_REQUIRED
    验证点：fetch_payload row_count>=1
    失败含义：有 key 仍无法 live fetch，产品 live 路径断裂
    """
    monkeypatch.setenv("QMD_ALLOW_LIVE_FETCH", "1")
    monkeypatch.setenv("FRED_API_KEY", "a" * 32)
    port = create_fred_fetch_port(series_ids=("DGS10",), max_rows=3, use_mock=False)
    with patch(
        "backend.app.datasources.fetch_ports.fred_port.FredLiveFetchPort._live_observations",
        return_value=[{"series_id": "DGS10", "observation_date": "2026-01-01", "value": "4.0"}],
    ):
        result = port.fetch_payload(_req())
    assert result.row_count >= 1
