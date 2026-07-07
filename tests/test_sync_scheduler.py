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


def test_syncScheduler_nonDryRun_invokesExecuteBindingLivePath(tmp_path, monkeypatch) -> None:
    """覆盖范围：scheduler profile 非 dry-run 增量路径
    测试对象：run_profile(dry_run=False) → execute_binding
    目的/目标：daily_close 展开后须以 live 模式调用 binding executor
    验证点：execute_binding 收到 dry_run=False；返回消息含 watermark 或 SKIPPED/COMPLETED
    失败含义：scheduler 仅 dry-run 可用，运维无法经 profile 触发真实 incremental
    """
    cm = ConnectionManager(db_path=tmp_path / "sched-live.duckdb")
    with cm.writer() as con:
        apply_migrations(con)

    monkeypatch.setattr(ResourceGuard, "check", lambda self: (Decision.OK, ""))
    from backend.app.sync import scheduler as sched_mod
    from backend.app.sync.scheduler import SchedulerJobResult

    _orig_run_entry = sched_mod._run_scheduler_entry

    def _run_entry_skip_empty_bar(entry, **kwargs):
        if (
            not kwargs.get("dry_run")
            and entry.get("domain") == "cn_equity_daily_bar"
            and entry.get("job_type") == "incremental"
        ):
            return SchedulerJobResult(
                job_type="incremental",
                domain="cn_equity_daily_bar",
                source_id=str(entry.get("source_id") or "baostock"),
                status="SKIPPED",
                binding_ids=(),
                message="no bar bindings in test profile",
                job_id="job-sched-bar-skip",
            )
        return _orig_run_entry(entry, **kwargs)

    monkeypatch.setattr(sched_mod, "_run_scheduler_entry", _run_entry_skip_empty_bar)
    dry_run_flags: list[bool] = []

    def _fake_execute(binding, job_type, **kwargs):
        dry_run_flags.append(kwargs.get("dry_run", True))
        return SyncJobResult(
            job_id=f"job-live-{binding.indicator_id}",
            status="SKIPPED",
            message=f"incremental from watermark window for {binding.indicator_id}",
        )

    with patch("backend.app.sync.scheduler.execute_binding", side_effect=_fake_execute):
        run = run_profile("daily_close", dry_run=False, connection_manager=cm)

    assert dry_run_flags
    assert all(flag is False for flag in dry_run_flags)
    macro_job = next(j for j in run.results if j.domain == "macro_series")
    assert macro_job.status in {"SKIPPED", "COMPLETED", "FAILED_FINAL"}
    assert macro_job.message and "watermark" in macro_job.message.lower()
