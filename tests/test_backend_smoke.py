"""Backend config and health endpoint smoke tests."""

from __future__ import annotations

import os

import pytest
from backend.app.config import get_resource_profile
from backend.app.main import app
from fastapi.testclient import TestClient


def test_getResourceProfile_defaultEco_shouldReturnEco(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("QMD_RESOURCE_PROFILE", raising=False)
    assert get_resource_profile() == "eco"


def test_getResourceProfile_invalidValue_shouldRaise() -> None:
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
    monkeypatch.delenv("QMD_RESOURCE_PROFILE", raising=False)
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["resource_profile"] == "eco"
