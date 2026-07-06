"""R3-DCP-09 qmd data backfill CLI tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from backend.app.cli.errors import CliFailure
from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.sync.jobs import BackfillShardCapExceededError

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_qmd_data(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    base = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
    if env:
        base.update(env)
    return subprocess.run(
        [sys.executable, "-m", "backend.app.cli.main", "data", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=base,
        check=False,
    )


def test_qmd_data_backfill_dry_run_json_auditable(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：qmd data backfill 默认 dry-run JSON
    测试对象：backend.app.cli.main data backfill
    目的/目标：operator 可审计 shard 计划且不写库
    验证点：exit 0；JSON 含 shard_count、shards、dry_run=true
    失败含义：backfill CLI 不可规划则 DCP-09 产品路径断裂
    """
    sandbox = tmp_path / ".audit-sandbox" / "bf-cli"
    sandbox.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(sandbox))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    proc = _run_qmd_data(
        "backfill",
        "--domain",
        "cn_equity_daily_bar",
        "--source-id",
        "baostock",
        "--start",
        "2026-01-01",
        "--end",
        "2026-02-15",
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["command"] == "backfill"
    assert payload["dry_run"] is True
    assert payload["shard_count"] >= 1
    assert len(payload["shards"]) == payload["shard_count"]


def test_qmd_data_backfill_cap_exceeded_fail_closed(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：超 max_shards 默认 fail-closed
    测试对象：data_commands.backfill_plan
    目的/目标：无 --truncate-to-cap 时 CLI 须拒绝
    验证点：BACKFILL_CAP_EXCEEDED 或 CliFailure
    失败含义：CLI 可绕过 cap 触发无界 backfill
    """
    from backend.app.cli import data_commands

    sandbox = tmp_path / ".audit-sandbox" / "bf-cap"
    sandbox.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(sandbox))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    with pytest.raises(CliFailure) as exc:
        data_commands.backfill_plan(
            data_domain="cn_equity_daily_bar",
            source_id="baostock",
            start="2026-01-01",
            end="2026-06-30",
            max_shards=3,
            dry_run=True,
        )
    assert exc.value.error_code == "BACKFILL_CAP_EXCEEDED"


def test_qmd_data_backfill_without_dry_run_requires_sandbox(
    monkeypatch, non_sandbox_data_root: Path
) -> None:
    """覆盖范围：非 dry-run 须 sandbox/live gate
    测试对象：qmd data backfill --no-dry-run
    目的/目标：生产路径 fail-closed；仅隔离库可执行
    验证点：非 sandbox QMD_DATA_ROOT 时 exit≠0
    失败含义：backfill 可在主库 silent 写入
    """
    data_root = non_sandbox_data_root
    monkeypatch.setenv("QMD_DATA_ROOT", str(data_root))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    proc = _run_qmd_data(
        "backfill",
        "--domain",
        "cn_equity_daily_bar",
        "--source-id",
        "baostock",
        "--start",
        "2026-01-01",
        "--end",
        "2026-01-31",
        "--no-dry-run",
    )
    assert proc.returncode != 0
    assert "USER_AUTH_REQUIRED" in proc.stderr


def test_qmd_data_backfill_truncate_to_cap_cli(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：CLI --truncate-to-cap 超窗截断
    测试对象：qmd data backfill --truncate-to-cap
    目的/目标：S00 AC 显式 truncate 须在 CLI 层可审计
    验证点：shard_count≤max_shards；JSON truncate_to_cap=true
    失败含义：CLI 无法传递 truncate 标志，cap 策略断裂
    """
    sandbox = tmp_path / ".audit-sandbox" / "bf-trunc"
    sandbox.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(sandbox))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    proc = _run_qmd_data(
        "backfill",
        "--domain",
        "cn_equity_daily_bar",
        "--source-id",
        "baostock",
        "--start",
        "2026-01-01",
        "--end",
        "2026-06-30",
        "--max-shards",
        "3",
        "--truncate-to-cap",
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["truncate_to_cap"] is True
    assert payload["shard_count"] <= 3


def test_qmd_data_backfill_max_shards_absolute_cap_cli(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：CLI --max-shards 硬顶 12
    测试对象：qmd data backfill --max-shards
    目的/目标：超过 ABSOLUTE_MAX_BACKFILL_SHARDS 须 INVALID_INPUT
    验证点：--max-shards 13 dry-run exit≠0 且 error_code=INVALID_INPUT
    失败含义：CLI 可请求无界 shard 数，绕过 ADR-011 硬顶
    """
    sandbox = tmp_path / ".audit-sandbox" / "bf-max"
    sandbox.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(sandbox))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    proc = _run_qmd_data(
        "backfill",
        "--domain",
        "cn_equity_daily_bar",
        "--source-id",
        "baostock",
        "--start",
        "2026-01-01",
        "--end",
        "2026-01-31",
        "--max-shards",
        "13",
    )
    assert proc.returncode != 0
    assert "INVALID_INPUT" in proc.stderr


@pytest.mark.parametrize(
    "source_id",
    __import__(
        "backend.app.sync.incremental_source_registry",
        fromlist=["iter_tier_a_incremental_sources"],
    ).iter_tier_a_incremental_sources(),
)
def test_qmd_data_backfill_tier_a_domains_dry_run(
    monkeypatch, tmp_path: Path, source_id: str
) -> None:
    """覆盖范围：Tier A 全 incremental registry domain dry-run backfill
    测试对象：data_commands.backfill_plan + incremental_source_registry
    目的/目标：11 源 canonical domain 均可规划 shard（ADR-011 cap 保留）
    验证点：exit 0；JSON shard_count>=1；domain 与 registry 一致
    失败含义：Backfill 仍限 baostock pilot，P1-10 未扩域
    """
    from backend.app.sync.incremental_source_registry import resolve_tier_a_incremental

    sandbox = tmp_path / ".audit-sandbox" / f"bf-tier-{source_id}"
    sandbox.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(sandbox))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    entry = resolve_tier_a_incremental(source_id)
    proc = _run_qmd_data(
        "backfill",
        "--domain",
        entry.canonical_domain,
        "--source-id",
        source_id,
        "--start",
        "2026-01-01",
        "--end",
        "2026-02-15",
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["data_domain"] == entry.canonical_domain
    assert payload["source_id"] == source_id
    assert payload["shard_count"] >= 1


def test_qmd_data_backfill_macro_series_fred_dry_run(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：macro_series + fred backfill dry-run
    测试对象：qmd data backfill --domain macro_series --source-id fred
    目的/目标：macro 域可 backfill 规划（P1-10 显式验收）
    验证点：operation==fetch_macro_series；instrument 默认 DGS10
    失败含义：macro backfill 仍 CAPABILITY_MISSING
    """
    sandbox = tmp_path / ".audit-sandbox" / "bf-macro-fred"
    sandbox.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(sandbox))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    proc = _run_qmd_data(
        "backfill",
        "--domain",
        "macro_series",
        "--source-id",
        "fred",
        "--start",
        "2026-01-01",
        "--end",
        "2026-03-01",
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["operation"] == "fetch_macro_series"
    assert payload["instrument_id"] == "DGS10"
