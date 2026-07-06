"""M-G1-03 P1-16 — sync scheduler §13.6 profiles."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.indicator_binding import bindings_for_source
from backend.app.sync.jobs import SyncJobResult
from backend.app.sync.scheduler import run_profile


def test_syncScheduler_profileExpandsRegistryToExecuteBinding(tmp_path, monkeypatch) -> None:
    """覆盖范围：内置 scheduler + sync_scheduler_profiles.yaml
    测试对象：backend.app.sync.scheduler.run_profile
    目的/目标：profile job 经 registry 展开为 execute_binding；非硬编码 series
    验证点：scheduler run --profile daily_close 登记 data_cli_contract
    失败含义：分散 crontab 或绕过 binding executor
    """
    cm = ConnectionManager(db_path=tmp_path / "sched.duckdb")
    with cm.writer() as con:
        apply_migrations(con)

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    expected_fred = {b.indicator_id for b in bindings_for_source("fred")}
    assert len(expected_fred) > 1

    captured: list[str] = []

    def _fake_execute(binding, job_type, **kwargs):
        captured.append(binding.indicator_id)
        return SyncJobResult(
            job_id=f"job-{binding.indicator_id}",
            status="SKIPPED",
            message="dry-run stub",
        )

    with patch("backend.app.sync.scheduler.execute_binding", side_effect=_fake_execute):
        run = run_profile("daily_close", dry_run=True, connection_manager=cm)

    macro_job = next(j for j in run.results if j.domain == "macro_series")
    assert set(macro_job.binding_ids) == expected_fred
    assert set(captured) == expected_fred
    assert "DGS10" in captured or any("DGS10" in bid for bid in captured)
    bar_job = next(j for j in run.results if j.domain == "cn_equity_daily_bar")
    assert bar_job.binding_ids == ()
