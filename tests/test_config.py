"""Application config tests."""

from __future__ import annotations

import importlib


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
