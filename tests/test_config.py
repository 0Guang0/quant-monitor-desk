"""应用配置路径与资源档位解析测试。

覆盖范围：backend.app.config 中 DATA_ROOT、CONFIGS_ROOT 与 QMD_RESOURCE_PROFILE 的解析行为。
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from backend.app.config import VALID_RESOURCE_PROFILES, get_resource_profile


def _reload_config(monkeypatch: pytest.MonkeyPatch, **env: str):
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    import backend.app.config as cfg

    importlib.reload(cfg)
    return cfg


def test_dataRoot_emptyEnv_fallsBackToProjectData(monkeypatch) -> None:
    """覆盖范围：未设置 QMD_DATA_ROOT 时的默认数据目录
    测试对象：backend.app.config.DATA_ROOT（reload 后）
    目的/目标：空环境变量应回落到项目内 data/，避免误指向系统路径
    验证点：DATA_ROOT == PROJECT_ROOT / 'data'
    失败含义：默认数据根目录漂移，同步与存储会写到错误位置
    """
    cfg = _reload_config(monkeypatch, QMD_DATA_ROOT="")
    assert cfg.DATA_ROOT == cfg.PROJECT_ROOT / "data"


def test_configsRoot_emptyEnv_fallsBackToProjectConfigs(monkeypatch) -> None:
    """覆盖范围：未设置 QMD_CONFIGS_ROOT 时的默认配置目录
    测试对象：backend.app.config.CONFIGS_ROOT（reload 后）
    目的/目标：空环境变量应回落到项目内 configs/
    验证点：CONFIGS_ROOT == PROJECT_ROOT / 'configs'
    失败含义：配置模板与契约 YAML 查找路径错误
    """
    cfg = _reload_config(monkeypatch, QMD_CONFIGS_ROOT="")
    assert cfg.CONFIGS_ROOT == cfg.PROJECT_ROOT / "configs"


def test_dataRoot_tildePath_expandsUserHome(monkeypatch) -> None:
    """覆盖范围：QMD_DATA_ROOT 使用 ~ 时的路径展开
    测试对象：backend.app.config.DATA_ROOT（reload 后）
    目的/目标：支持用户主目录简写，与常见 shell 约定一致
    验证点：DATA_ROOT == Path('~').expanduser()
    失败含义：波浪号未展开会导致读写落到字面量 ~ 目录
    """
    cfg = _reload_config(monkeypatch, QMD_DATA_ROOT="~")
    assert cfg.DATA_ROOT == Path("~").expanduser()


def test_getResourceProfile_validProfiles_shouldReturnNormalized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：合法 QMD_RESOURCE_PROFILE 环境值
    测试对象：backend.app.config.get_resource_profile
    目的/目标：eco/normal/batch 均应被接受且归一化为小写
    验证点：大写 env 输入时返回值等于对应小写 profile
    失败含义：合法档位被拒绝会导致 ResourceGuard 与限流策略失效
    """
    for profile in sorted(VALID_RESOURCE_PROFILES):
        monkeypatch.setenv("QMD_RESOURCE_PROFILE", profile.upper())
        assert get_resource_profile() == profile


def test_getResourceProfile_invalidProfile_shouldRaiseValueError(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """覆盖范围：非法 QMD_RESOURCE_PROFILE 环境值
    测试对象：backend.app.config.get_resource_profile
    目的/目标：未知档位必须 fail-fast 并提示合法集合
    验证点：profile=turbo 时抛出 ValueError 且消息含 Invalid QMD_RESOURCE_PROFILE
    失败含义：静默接受非法档位会绕过资源护栏
    """
    monkeypatch.setenv("QMD_RESOURCE_PROFILE", "turbo")
    with pytest.raises(ValueError, match="Invalid QMD_RESOURCE_PROFILE"):
        get_resource_profile()
