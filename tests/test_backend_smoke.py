"""后端配置与健康检查端点冒烟测试。"""

from __future__ import annotations

import os

import pytest
from backend.app.config import get_resource_profile
from backend.app.main import app
from fastapi.testclient import TestClient


def test_getResourceProfile_defaultEco_shouldReturnEco(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：未设置环境变量时的资源档位
    测试对象：get_resource_profile
    目的/目标：默认应使用 eco 档位以控制资源占用
    验证点：清除 QMD_RESOURCE_PROFILE 后返回 'eco'
    失败含义：默认档位过高或未知，部署未配置即吃满资源
    """
    monkeypatch.delenv("QMD_RESOURCE_PROFILE", raising=False)
    assert get_resource_profile() == "eco"


def test_getResourceProfile_invalidValue_shouldRaise() -> None:
    """覆盖范围：非法 QMD_RESOURCE_PROFILE 值
    测试对象：get_resource_profile
    目的/目标：未契约登记的档位名必须立即报错而非静默回退
    验证点：QMD_RESOURCE_PROFILE=turbo 时抛出 ValueError（Invalid QMD_RESOURCE_PROFILE）
    失败含义：拼写错误的档位被接受，运行时策略与文档不一致
    """
    original = os.environ.get("QMD_RESOURCE_PROFILE")
    os.environ["QMD_RESOURCE_PROFILE"] = "turbo"
    try:
        with pytest.raises(ValueError, match="Invalid QMD_RESOURCE_PROFILE"):
            get_resource_profile()
    finally:
        if original is None:
            os.environ.pop("QMD_RESOURCE_PROFILE", None)
        else:
            os.environ["QMD_RESOURCE_PROFILE"] = original


def test_healthEndpoint_returnsOkWithEcoProfile(monkeypatch: pytest.MonkeyPatch) -> None:
    """覆盖范围：/health HTTP 冒烟
    测试对象：FastAPI app 与 TestClient GET /health
    目的/目标：健康端点在默认 eco 配置下应 200 并回传档位
    验证点：status_code==200；JSON status=='ok' 且 resource_profile=='eco'
    失败含义：服务无法启动探测或健康 JSON 缺档位，编排与探活失效
    """
    monkeypatch.delenv("QMD_RESOURCE_PROFILE", raising=False)
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["resource_profile"] == "eco"
