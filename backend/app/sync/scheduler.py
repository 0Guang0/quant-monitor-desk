"""Built-in sync scheduler — profile YAML → registry expand → execute_binding (M-G1-03 §13.6)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Literal

import yaml
from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.db.connection import ConnectionManager
from backend.app.sync.binding_executor import execute_binding
from backend.app.sync.indicator_binding import IndicatorBinding, bindings_for_source
from backend.app.sync.jobs import SyncJobResult, SyncJobSpec
from backend.app.sync.orchestrator import DataSyncOrchestrator

PROFILES_PATH = (
    Path(__file__).resolve().parents[3]
    / "specs"
    / "layer1_axes"
    / "sync_scheduler_profiles.yaml"
)

_NON_CORE_JOB_TYPES = frozenset({"revision_audit", "full_load", "backfill"})
_BINDING_JOB_TYPES = frozenset({"incremental", "backfill", "full_load"})


@dataclass(frozen=True)
class SchedulerJobResult:
    job_type: str
    domain: str | None
    source_id: str | None
    status: str
    binding_ids: tuple[str, ...]
    message: str | None = None
    job_id: str | None = None
    window: dict[str, str] | None = None
    acceptance_report: Any | None = None
    acceptance_extra: dict[str, Any] | None = None


@dataclass(frozen=True)
class SchedulerProfileRun:
    profile: str
    dry_run: bool
    skipped_non_core: bool
    results: tuple[SchedulerJobResult, ...]


def load_scheduler_profiles(*, path: Path = PROFILES_PATH) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"missing scheduler profiles: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    profiles = payload.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError("scheduler profiles must be a non-empty mapping")
    return profiles


def _profile_jobs(profile_name: str, *, path: Path = PROFILES_PATH) -> list[dict[str, Any]]:
    profiles = load_scheduler_profiles(path=path)
    if profile_name not in profiles:
        raise KeyError(f"unknown scheduler profile: {profile_name!r}")
    jobs = profiles[profile_name].get("jobs") or []
    if not isinstance(jobs, list) or not jobs:
        raise ValueError(f"profile {profile_name!r} has no jobs")
    return jobs


def _bindings_for_job(domain: str, source_id: str) -> tuple[IndicatorBinding, ...]:
    return tuple(
        binding
        for binding in bindings_for_source(source_id)
        if binding.data_domain == domain
    )


def _resource_guard_blocks_non_core() -> tuple[bool, str]:
    decision, reason = ResourceGuard().check()
    return decision in (Decision.PAUSE, Decision.HARD_STOP), reason or decision.value


def _run_binding_job(
    binding: IndicatorBinding,
    job_type: Literal["incremental", "backfill", "full_load"],
    *,
    dry_run: bool,
    connection_manager: ConnectionManager | None,
    orchestrator: DataSyncOrchestrator | None,
    datasource_service=None,
    date_start: date | None = None,
    date_end: date | None = None,
) -> SyncJobResult:
    return execute_binding(
        binding,
        job_type,
        dry_run=dry_run,
        connection_manager=connection_manager,
        orchestrator=orchestrator,
        datasource_service=datasource_service,
        date_start=date_start,
        date_end=date_end,
    )


def _run_orchestrator_job(
    entry: dict[str, Any],
    *,
    dry_run: bool,
    orchestrator: DataSyncOrchestrator | None,
) -> SyncJobResult:
    job_type = str(entry["job_type"])
    domain = str(entry.get("domain") or "macro_series")
    source_id = str(entry.get("source_id") or "fred")
    suffix = uuid.uuid4().hex[:8]
    spec = SyncJobSpec(
        run_id=f"sched-{job_type}-{suffix}",
        job_id=f"job-sched-{job_type}-{suffix}",
        job_type=job_type,
        data_domain=domain,
        market_id="GLOBAL" if domain == "macro_series" else "CN_A",
        source_id=source_id,
        adapter_id=source_id,
        date_start=None,
        date_end=None,
        instrument_id=None,
        partition_key=None,
        trigger_reason=f"scheduler:{job_type}",
    )
    if dry_run:
        return SyncJobResult(
            job_id=spec.job_id,
            status="SKIPPED",
            message=f"dry-run only; would run {job_type}",
        )
    if orchestrator is None:
        raise ValueError(f"live {job_type} requires orchestrator")
    if job_type == "revision_audit":
        return orchestrator.run_revision_audit(spec)
    if job_type == "data_quality":
        return orchestrator.run_data_quality(spec)
    if job_type == "reconcile":
        conflict_id = entry.get("conflict_id")
        if not conflict_id:
            raise ValueError("reconcile scheduler job requires conflict_id")
        return orchestrator.run_reconcile(str(conflict_id))
    raise ValueError(f"unsupported orchestrator scheduler job_type={job_type!r}")


def _run_scheduler_entry(
    entry: dict[str, Any],
    *,
    dry_run: bool,
    connection_manager: ConnectionManager | None,
    orchestrator: DataSyncOrchestrator | None,
    datasource_service=None,
) -> SchedulerJobResult:
    job_type = str(entry["job_type"])
    domain = entry.get("domain")
    source_id = entry.get("source_id")
    domain_s = str(domain) if domain is not None else None
    source_s = str(source_id) if source_id is not None else None
    window: dict[str, str] | None = None
    if entry.get("date_start") and entry.get("date_end"):
        window = {
            "date_start": str(entry["date_start"])[:10],
            "date_end": str(entry["date_end"])[:10],
        }

    if job_type in _BINDING_JOB_TYPES and domain_s and source_s:
        bindings = _bindings_for_job(domain_s, source_s)
        if bindings:
            if not dry_run:
                from backend.app.cli.phase1_acceptance import (
                    is_production_equivalent_acceptance_root,
                    live_authorized_from_env,
                    resolve_cli_data_root,
                )

                if is_production_equivalent_acceptance_root(
                    resolve_cli_data_root()
                ) and not live_authorized_from_env():
                    from backend.app.cli.phase1_acceptance import (
                        acceptance_request_for_domain,
                        execute_spine_or_binding_live,
                    )

                    data_root = resolve_cli_data_root()
                    request = acceptance_request_for_domain(
                        source_id=source_s,
                        data_domain=domain_s,
                        start=(window or {}).get("date_start"),
                        end=(window or {}).get("date_end"),
                    )
                    report, extra = execute_spine_or_binding_live(
                        request,
                        data_root=data_root,
                        live_authorized=False,
                        job_type=job_type,  # type: ignore[arg-type]
                    )
                    return SchedulerJobResult(
                        job_type=job_type,
                        domain=domain_s,
                        source_id=source_s,
                        status="BLOCKED",
                        binding_ids=tuple(binding.indicator_id for binding in bindings),
                        message=f"live authorization missing for {domain_s}:{source_s}:{job_type}",
                        job_id=None,
                        window=window,
                        acceptance_report=report,
                        acceptance_extra=extra,
                    )
            results: list[SyncJobResult] = []
            binding_ids: list[str] = []
            for binding in bindings:
                binding_ids.append(binding.indicator_id)
                from backend.app.cli.phase1_acceptance import resolve_binding_datasource_service

                binding_service = resolve_binding_datasource_service(
                    binding,
                    datasource_service=datasource_service,
                    dry_run=dry_run,
                    orchestrator=orchestrator,
                    connection_manager=connection_manager,
                )
                if job_type == "incremental":
                    results.append(
                        _run_binding_job(
                            binding,
                            "incremental",
                            dry_run=dry_run,
                            connection_manager=connection_manager,
                            orchestrator=orchestrator,
                            datasource_service=binding_service,
                        )
                    )
                else:
                    if dry_run:
                        results.append(
                            SyncJobResult(
                                job_id=f"job-{binding.indicator_id}",
                                status="SKIPPED",
                                message=(
                                    f"dry-run plan for {job_type}; "
                                    "date window required for live run"
                                ),
                            )
                        )
                        continue
                    date_start = entry.get("date_start")
                    date_end = entry.get("date_end")
                    if not date_start or not date_end:
                        results.append(
                            SyncJobResult(
                                job_id=f"job-{binding.indicator_id}",
                                status="FAILED_FINAL",
                                message=(
                                    f"{job_type} via scheduler requires profile date_start "
                                    "and date_end for live run"
                                ),
                            )
                        )
                        continue
                    from datetime import date as date_cls

                    parsed_start = date_cls.fromisoformat(str(date_start)[:10])
                    parsed_end = date_cls.fromisoformat(str(date_end)[:10])
                    results.append(
                        _run_binding_job(
                            binding,
                            job_type,  # type: ignore[arg-type]
                            dry_run=dry_run,
                            connection_manager=connection_manager,
                            orchestrator=orchestrator,
                            datasource_service=binding_service,
                            date_start=parsed_start,
                            date_end=parsed_end,
                        )
                    )
            last = results[-1]
            acceptance_report = None
            acceptance_extra = None
            if (
                not dry_run
                and connection_manager is not None
                and last.job_id
                and domain_s
                and source_s
            ):
                from backend.app.cli.phase1_acceptance import (
                    capture_scheduler_binding_child_acceptance,
                    resolve_cli_data_root,
                )

                acceptance_report, acceptance_extra = capture_scheduler_binding_child_acceptance(
                    job_type=job_type,  # type: ignore[arg-type]
                    source_id=source_s,
                    data_domain=domain_s,
                    data_root=resolve_cli_data_root(),
                    cm=connection_manager,
                    job_result=last,
                    window=window,
                    trigger_reason="eco_catchup" if job_type == "backfill" else f"scheduler:{job_type}",
                )
            return SchedulerJobResult(
                job_type=job_type,
                domain=domain_s,
                source_id=source_s,
                status=last.status,
                binding_ids=tuple(binding_ids),
                message=last.message,
                job_id=last.job_id,
                window=window,
                acceptance_report=acceptance_report,
                acceptance_extra=acceptance_extra,
            )

        suffix = uuid.uuid4().hex[:8]
        if dry_run:
            return SchedulerJobResult(
                job_type=job_type,
                domain=domain_s,
                source_id=source_s,
                status="SKIPPED",
                binding_ids=(),
                message=(
                    f"dry-run only; no registry bindings for {domain_s}/{source_s}; "
                    f"would run {job_type}"
                ),
                job_id=f"job-sched-{suffix}",
                window=window,
            )
        if job_type == "incremental":
            from backend.app.cli.phase1_acceptance import (
                acceptance_request_for_domain,
                execute_spine_or_binding_live,
                is_production_equivalent_acceptance_root,
                live_authorized_from_env,
                resolve_cli_data_root,
            )

            data_root = resolve_cli_data_root()
            if is_production_equivalent_acceptance_root(data_root):
                request = acceptance_request_for_domain(
                    source_id=source_s,
                    data_domain=domain_s,
                )
                report, extra = execute_spine_or_binding_live(
                    request,
                    data_root=data_root,
                    live_authorized=live_authorized_from_env(),
                    job_type="incremental",
                )
                status = "COMPLETED" if report.status == "PASS" else report.failure_class
                return SchedulerJobResult(
                    job_type=job_type,
                    domain=domain_s,
                    source_id=source_s,
                    status=status,
                    binding_ids=(),
                    message=report.errors[0] if report.errors else report.status,
                    job_id=extra.get("job_id"),
                    window=window,
                    acceptance_report=report,
                    acceptance_extra=extra,
                )
        if job_type in {"backfill", "full_load"} and window:
            from datetime import date as date_cls

            from backend.app.cli.phase1_acceptance import (
                acceptance_request_for_domain,
                execute_spine_or_binding_live,
                is_production_equivalent_acceptance_root,
                live_authorized_from_env,
                resolve_cli_data_root,
            )
            from backend.app.sync.jobs import BackfillShardCapExceededError, plan_backfill_shards

            data_root = resolve_cli_data_root()
            if is_production_equivalent_acceptance_root(data_root):
                parsed_start = date_cls.fromisoformat(window["date_start"][:10])
                parsed_end = date_cls.fromisoformat(window["date_end"][:10])
                if job_type == "backfill":
                    try:
                        plan_backfill_shards(
                            parsed_start,
                            parsed_end,
                            data_domain=domain_s,
                            truncate_to_cap=True,
                        )
                    except BackfillShardCapExceededError as exc:
                        return SchedulerJobResult(
                            job_type=job_type,
                            domain=domain_s,
                            source_id=source_s,
                            status="FAILED_FINAL",
                            binding_ids=(),
                            message=str(exc),
                            window=window,
                        )
                request = acceptance_request_for_domain(
                    source_id=source_s,
                    data_domain=domain_s,
                    start=window["date_start"],
                    end=window["date_end"],
                )
                report, extra = execute_spine_or_binding_live(
                    request,
                    data_root=data_root,
                    live_authorized=live_authorized_from_env(),
                    job_type=job_type,  # type: ignore[arg-type]
                    date_start=parsed_start,
                    date_end=parsed_end,
                    trigger_reason=(
                        "eco_catchup" if job_type == "backfill" else f"scheduler:{job_type}"
                    ),
                )
                status = "COMPLETED" if report.status == "PASS" else report.failure_class
                return SchedulerJobResult(
                    job_type=job_type,
                    domain=domain_s,
                    source_id=source_s,
                    status=status,
                    binding_ids=(),
                    message=report.errors[0] if report.errors else report.status,
                    job_id=extra.get("job_id"),
                    window=window,
                    acceptance_report=report,
                    acceptance_extra=extra,
                )
        raise ValueError(
            f"live {job_type} for {domain_s}/{source_s} requires registry "
            "bindings or CLI backfill/sync"
        )

    if orchestrator is None and connection_manager is not None and not dry_run:
        orchestrator = DataSyncOrchestrator(connection_manager)
    if orchestrator is None and not dry_run:
        raise ValueError(
            "scheduler quality/revision job requires connection_manager or orchestrator"
        )
    orch_result = _run_orchestrator_job(entry, dry_run=dry_run, orchestrator=orchestrator)
    return SchedulerJobResult(
        job_type=job_type,
        domain=domain_s,
        source_id=source_s,
        status=orch_result.status,
        binding_ids=(),
        message=orch_result.message,
        job_id=orch_result.job_id,
        window=window,
    )


def run_profile(
    profile_name: str,
    *,
    dry_run: bool = True,
    job_type_filter: str | None = None,
    connection_manager: ConnectionManager | None = None,
    orchestrator: DataSyncOrchestrator | None = None,
    datasource_service=None,
    profiles_path: Path = PROFILES_PATH,
) -> SchedulerProfileRun:
    """Expand profile jobs → registry bindings → execute_binding sequence."""
    jobs = _profile_jobs(profile_name, path=profiles_path)
    if job_type_filter is not None:
        jobs = [j for j in jobs if str(j.get("job_type")) == job_type_filter]

    blocked, guard_reason = _resource_guard_blocks_non_core()
    results: list[SchedulerJobResult] = []
    skipped_non_core = False

    for entry in jobs:
        job_type = str(entry.get("job_type", ""))
        is_core = bool(entry.get("core", job_type not in _NON_CORE_JOB_TYPES))
        if blocked and not is_core:
            skipped_non_core = True
            results.append(
                SchedulerJobResult(
                    job_type=job_type,
                    domain=entry.get("domain"),
                    source_id=entry.get("source_id"),
                    status="SKIPPED",
                    binding_ids=(),
                    message=f"non-core job skipped: {guard_reason}",
                )
            )
            continue
        results.append(
            _run_scheduler_entry(
                entry,
                dry_run=dry_run,
                connection_manager=connection_manager,
                orchestrator=orchestrator,
                datasource_service=datasource_service,
            )
        )

    return SchedulerProfileRun(
        profile=profile_name,
        dry_run=dry_run,
        skipped_non_core=skipped_non_core,
        results=tuple(results),
    )
