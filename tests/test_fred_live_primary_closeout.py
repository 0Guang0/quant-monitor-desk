"""FRED live primary closeout — R3F-SH-06."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.ops.fred_live_primary import (
    FredLivePrimaryAuthorizationError,
    run_fred_live_primary_closeout,
    validate_fred_live_authorization,
)

_AUTH_YAML = (
    Path(__file__).resolve().parents[1]
    / ".trellis/tasks/round3-source-health-and-quality-runners/execute-evidence/fred_live_authorization_2026-06-25.yaml"
)


def test_fredLivePrimary_requiresAuthorizationYaml() -> None:
    """覆盖范围：FRED live primary 授权 YAML fail-closed 门
    测试对象：validate_fred_live_authorization / run_fred_live_primary_closeout
    目的/目标：AC-SH-06 — 无授权不得 live；有 YAML 时 sandbox closeout
    验证点：缺失 YAML 抛 FredLivePrimaryAuthorizationError；present 时 production_clean_write=False
    失败含义：无用户授权仍可 live，违反 hardening §3
    """
    assert _AUTH_YAML.is_file(), "authorization YAML must exist for Plan freeze"
    with pytest.raises(FredLivePrimaryAuthorizationError):
        validate_fred_live_authorization(
            Path("/nonexistent/fred_live_authorization.yaml"),
            live_requested=True,
        )
    payload = validate_fred_live_authorization(_AUTH_YAML, live_requested=False)
    assert payload["authorization_present"] is True
    closeout = run_fred_live_primary_closeout(
        authorization_path=_AUTH_YAML,
        skip_live_fetch=True,
    )
    assert closeout["sandbox_only"] is True
    assert closeout["production_clean_write"] is False
