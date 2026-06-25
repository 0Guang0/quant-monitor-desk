"""FRED live primary closeout — R3F-SH-06."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from backend.app.ops.fred_live_primary import (
    FRED_LIVE_AUTHORIZATION_DEFAULT,
    FredLivePrimaryAuthorizationError,
    run_fred_live_primary_closeout,
    validate_fred_live_authorization,
)


def test_fredLivePrimary_requiresAuthorizationYaml() -> None:
    """覆盖范围：FRED live primary 授权 YAML fail-closed 门
    测试对象：validate_fred_live_authorization / run_fred_live_primary_closeout
    目的/目标：AC-SH-06 — 无授权不得 live；有 YAML 时 sandbox closeout
    验证点：缺失 YAML 抛 FredLivePrimaryAuthorizationError；present 时 production_clean_write=False
    失败含义：无用户授权仍可 live，违反 hardening §3
    """
    assert FRED_LIVE_AUTHORIZATION_DEFAULT.is_file(), (
        "authorization YAML must exist for Plan freeze"
    )
    with pytest.raises(FredLivePrimaryAuthorizationError):
        validate_fred_live_authorization(
            Path("/nonexistent/fred_live_authorization.yaml"),
            live_requested=True,
        )
    payload = validate_fred_live_authorization(
        FRED_LIVE_AUTHORIZATION_DEFAULT, live_requested=False
    )
    assert payload["authorization_present"] is True
    closeout = run_fred_live_primary_closeout(
        authorization_path=FRED_LIVE_AUTHORIZATION_DEFAULT,
        skip_live_fetch=True,
    )
    assert closeout["sandbox_only"] is True
    assert closeout["production_clean_write"] is False


def test_fredLivePrimary_rejectsProductionCleanWriteFlag(tmp_path) -> None:
    """覆盖范围：FRED 授权 YAML allow_production_clean_write 负向门
    测试对象：validate_fred_live_authorization
    目的/目标：W-A8-01 / A3 — production clean write 字段须为 false
    验证点：allow_production_clean_write=true 时抛 FredLivePrimaryAuthorizationError
    失败含义：授权 YAML 可误开 production 写入
    """
    bad_yaml = tmp_path / "fred_bad_prod_write.yaml"
    bad_yaml.write_text(
        yaml.safe_dump(
            {
                "authorization_present": True,
                "scope": "fred_live_primary_sandbox_only",
                "allow_production_clean_write": True,
                "skip_live_fetch_default": True,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(FredLivePrimaryAuthorizationError, match="allow_production_clean_write"):
        validate_fred_live_authorization(bad_yaml, live_requested=False)


def test_fredLivePrimary_rejectsWrongScope(tmp_path) -> None:
    """覆盖范围：FRED 授权 scope 负向门
    测试对象：validate_fred_live_authorization
    目的/目标：W-A8-02 — scope 须为 fred_live_primary_sandbox_only
    验证点：错误 scope 抛 FredLivePrimaryAuthorizationError
    失败含义：非 sandbox scope 可绕过 live 门
    """
    bad_yaml = tmp_path / "fred_bad_scope.yaml"
    bad_yaml.write_text(
        yaml.safe_dump(
            {
                "authorization_present": True,
                "scope": "production_primary",
                "allow_production_clean_write": False,
                "skip_live_fetch_default": True,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(FredLivePrimaryAuthorizationError, match="scope must be"):
        validate_fred_live_authorization(bad_yaml, live_requested=False)


def test_fredLivePrimary_rejectsLiveWithoutOptIn(tmp_path) -> None:
    """覆盖范围：FRED live_requested 与 skip_live_fetch_default 冲突负向门
    测试对象：validate_fred_live_authorization
    目的/目标：W-A8-03 — live 须显式 opt-in，不得默认 skip
    验证点：live_requested=True 且 skip_live_fetch_default=True 时拒绝
    失败含义：默认 skip 下仍可 live fetch
    """
    yaml_path = tmp_path / "fred_skip_default.yaml"
    yaml_path.write_text(
        yaml.safe_dump(
            {
                "authorization_present": True,
                "scope": "fred_live_primary_sandbox_only",
                "allow_production_clean_write": False,
                "skip_live_fetch_default": True,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(FredLivePrimaryAuthorizationError, match="skip_live_fetch_default"):
        validate_fred_live_authorization(yaml_path, live_requested=True)
