"""M-G1-03 P1-09 — qmd-data data full-load CLI."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

from backend.app.core.resource_guard import Decision, ResourceGuard
from tests.backfill_cap_support import CN_EQUITY_FIVE_TRADING_DAYS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLI_CONTRACT = PROJECT_ROOT / "specs/contracts/data_cli_contract.yaml"


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


def test_qmdDataFullLoad_cliRegisteredInDataCliContract() -> None:
    """覆盖范围：qmd-data data full-load CLI
    测试对象：backend.app.cli.data_commands · data_cli_contract.yaml
    目的/目标：CLI 登记；失败走 CliFailure；默认 --dry-run
    验证点：must_use orchestrator 金路径
    失败含义：平行 CLI 或契约未登记
    """
    contract = yaml.safe_load(CLI_CONTRACT.read_text(encoding="utf-8")) or {}
    entry = contract["commands"]["qmd data full-load"]
    assert entry["default_mode"] == "dry_run"
    assert "domain" in entry["required_args"]
    assert "DataSyncOrchestrator.run_full_load" in entry["must_use"]
    required_tests = contract.get("required_tests") or []
    assert any("test_qmd_data_full_load_cli" in t for t in required_tests)


def test_qmd_data_full_load_dry_run_json_auditable(monkeypatch, tmp_path: Path) -> None:
    """覆盖范围：qmd data full-load 默认 dry-run JSON
    测试对象：backend.app.cli.main data full-load
    目的/目标：operator 可审计 shard 计划且不写库
    验证点：exit 0；JSON 含 shard_count、shards、dry_run=true、command=full-load
    失败含义：full-load CLI 不可规划则 §13.7 产品路径断裂
    """
    sandbox = tmp_path / ".audit-sandbox" / "fl-cli"
    sandbox.mkdir(parents=True)
    monkeypatch.setenv("QMD_DATA_ROOT", str(sandbox))
    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    proc = _run_qmd_data(
        "full-load",
        "--domain",
        "cn_equity_daily_bar",
        "--source-id",
        "baostock",
        "--start",
        CN_EQUITY_FIVE_TRADING_DAYS[0],
        "--end",
        CN_EQUITY_FIVE_TRADING_DAYS[1],
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["command"] == "full-load"
    assert payload["dry_run"] is True
    assert payload["shard_count"] >= 1
    assert len(payload["shards"]) == payload["shard_count"]
