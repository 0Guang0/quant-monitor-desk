"""Application config tests."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from backend.app.config import VALID_RESOURCE_PROFILES, get_resource_profile


def test_dataRoot_emptyEnv_fallsBackToProjectData(monkeypatch) -> None:
    monkeypatch.setenv("QMD_DATA_ROOT", "")
    import backend.app.config as cfg

    importlib.reload(cfg)
    assert cfg.DATA_ROOT == cfg.PROJECT_ROOT / "data"


def test_configsRoot_emptyEnv_fallsBackToProjectConfigs(monkeypatch) -> None:
    monkeypatch.setenv("QMD_CONFIGS_ROOT", "")
    import backend.app.config as cfg

    importlib.reload(cfg)
    assert cfg.CONFIGS_ROOT == cfg.PROJECT_ROOT / "configs"


def test_dataRoot_tildePath_expandsUserHome(monkeypatch) -> None:
    monkeypatch.setenv("QMD_DATA_ROOT", "~")
    import backend.app.config as cfg

    importlib.reload(cfg)
    assert cfg.DATA_ROOT == Path("~").expanduser()


def test_getResourceProfile_validProfiles_shouldReturnNormalized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：get_resource_profile 合法 env 值。

    测试对象：backend.app.config.get_resource_profile。

    目的/目标：确认 eco/normal/batch 均被接受且小写归一化。
    """
    for profile in sorted(VALID_RESOURCE_PROFILES):
        monkeypatch.setenv("QMD_RESOURCE_PROFILE", profile.upper())
        assert get_resource_profile() == profile


def test_getResourceProfile_invalidProfile_shouldRaiseValueError(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：get_resource_profile 非法 env 值。

    测试对象：backend.app.config.get_resource_profile。

    目的/目标：非法 profile 必须 fail-fast 并提示合法集合。
    """
    monkeypatch.setenv("QMD_RESOURCE_PROFILE", "turbo")
    with pytest.raises(ValueError, match="Invalid QMD_RESOURCE_PROFILE"):
        get_resource_profile()
