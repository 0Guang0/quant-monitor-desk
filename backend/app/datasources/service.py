"""DataSourceService — production fetch facade (Round2.6 Phase C)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from backend.app.config import DATA_ROOT
from backend.app.core.resource_guard import Decision, ResourceGuard, format_pause_event
from backend.app.datasources.adapters import create_adapter
from backend.app.datasources.adapters.fetch_port import FetchPort, StubFetchPort
from backend.app.datasources.capability_registry import (
    OperationDisabledError,
    SourceCapabilityRegistry,
    UnknownCapabilityError,
)
from backend.app.datasources.fetch_log import FetchLogWriter
from backend.app.datasources.fetch_result import FetchRequest, FetchResult
from backend.app.datasources.route_models import SourceRoutePlan
from backend.app.datasources.route_planner import SourceRoutePlanner
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.storage.file_registry import FileRegistry

if TYPE_CHECKING:
    from backend.app.sync.jobs import SyncJobStateMachine


class ResourceGuardBlockedError(RuntimeError):
    """Raised when ResourceGuard blocks fetch before adapter construction."""

    def __init__(self, message: str, *, decision: Decision | None = None) -> None:
        super().__init__(message)
        self.decision = decision


class DataSourceService:
    """Single production fetch facade: route → capability → guard → adapter → fetch_log."""

    def __init__(
        self,
        *,
        source_registry: SourceRegistry | None = None,
        capability_registry: SourceCapabilityRegistry | None = None,
        route_planner: SourceRoutePlanner | None = None,
        data_root: Path | None = None,
        fetch_port: FetchPort | None = None,
        file_registry_factory: Callable[[], FileRegistry | None] | None = None,
        job_events: SyncJobStateMachine | None = None,
    ) -> None:
        self._source_registry = source_registry or SourceRegistry()
        if not self._source_registry._sources:
            self._source_registry.load()
        self._capability_registry = capability_registry or SourceCapabilityRegistry()
        if not self._capability_registry.sources:
            self._capability_registry.load()
        self._route_planner = route_planner or SourceRoutePlanner(
            source_registry=self._source_registry,
            capability_registry=self._capability_registry,
        )
        self._data_root = data_root or DATA_ROOT
        self._fetch_port = fetch_port
        self._file_registry_factory = file_registry_factory
        self._job_events = job_events
        self._fetch_log = FetchLogWriter()

    def preview_route(
        self,
        *,
        data_domain: str,
        operation: str,
        market_id: str | None = None,
        run_id: str = "preview-run",
        job_id: str = "preview-job",
        use_fallback: bool = False,
    ) -> SourceRoutePlan:
        return self._route_planner.plan(
            data_domain=data_domain,
            operation=operation,
            market_id=market_id,
            run_id=run_id,
            job_id=job_id,
            use_fallback=use_fallback,
        )

    def _emit_route_plan(self, con, job_id: str, plan: SourceRoutePlan) -> None:
        from backend.app.sync.event_payload import build_route_plan_payload

        payload = build_route_plan_payload(plan)
        if self._job_events is not None:
            self._job_events.emit_custom_event(
                job_id,
                event_type="ROUTE_PLAN",
                message=f"route_status={plan.route_status}",
                payload_json=payload,
                con=con,
            )
            return
        con.execute(
            """
            INSERT INTO job_event_log (
                event_id, job_id, event_type, message, payload_json, created_at
            ) VALUES (uuid(), ?, 'ROUTE_PLAN', ?, ?, CURRENT_TIMESTAMP)
            """,
            [job_id, f"route_status={plan.route_status}", payload],
        )

    def fetch(
        self,
        req: FetchRequest,
        *,
        con,
        job_id: str | None = None,
        operation: str | None = None,
        on_enter_fetching: Callable[[], None] | None = None,
    ) -> FetchResult:
        op = operation or _default_operation(req.data_domain)
        plan = self._route_planner.plan(
            data_domain=req.data_domain,
            operation=op,
            run_id=req.run_id,
            job_id=job_id or req.run_id,
            market_id=req.market_id,
        )
        if job_id:
            self._emit_route_plan(con, job_id, plan)

        guard = ResourceGuard(con=con)
        decision, reason = guard.check()
        if decision in (Decision.PAUSE, Decision.HARD_STOP):
            from dataclasses import replace

            blocked_plan = replace(
                plan,
                route_status="RESOURCE_GUARD_PAUSED",
                selected_source_id=None,
            )
            if job_id:
                self._emit_route_plan(con, job_id, blocked_plan)
            snap = guard.snapshot()
            message = format_pause_event(decision, reason, snap, guard.profile)
            raise ResourceGuardBlockedError(message, decision=decision)

        fetch_time = datetime.now(UTC).isoformat()
        if plan.route_status != "READY" or plan.selected_source_id is None:
            result = FetchResult(
                run_id=req.run_id,
                source_id=req.source_id,
                data_domain=req.data_domain,
                status="DISABLED_SOURCE",
                row_count=0,
                fetch_time=fetch_time,
                error_message=f"route_status={plan.route_status}",
            )
            self._fetch_log.write(con, result, req=req, job_id=job_id)
            return result

        selected = plan.selected_source_id
        try:
            self._capability_registry.assert_source_domain_operation(selected, req.data_domain, op)
        except (UnknownCapabilityError, OperationDisabledError) as exc:
            result = FetchResult(
                run_id=req.run_id,
                source_id=selected,
                data_domain=req.data_domain,
                status="DISABLED_SOURCE",
                row_count=0,
                fetch_time=fetch_time,
                error_message=str(exc),
            )
            self._fetch_log.write(con, result, req=req, job_id=job_id)
            return result

        if on_enter_fetching is not None:
            on_enter_fetching()

        fetch_port = self._fetch_port or StubFetchPort(payload=b"{}")
        file_registry = self._file_registry_factory() if self._file_registry_factory else None
        if file_registry is None:
            from backend.app.datasources.adapters import create_test_adapter

            adapter = create_test_adapter(
                selected,
                self._source_registry,
                self._data_root,
                fetch_port=fetch_port,
            )
        else:
            adapter = create_adapter(
                selected,
                self._source_registry,
                self._data_root,
                fetch_port=fetch_port,
                file_registry=file_registry,
            )
        routed_req = req.model_copy(update={"source_id": selected})
        result = adapter.fetch(routed_req, con=con, job_id=job_id)
        self._fetch_log.write(con, result, req=routed_req, job_id=job_id)
        return result


def _default_operation(data_domain: str) -> str:
    defaults = {
        "cn_equity_daily_bar": "fetch_daily_bar",
        "cn_equity_minute_bar": "fetch_minute_bar",
        "cn_equity_realtime": "fetch_realtime_quote",
        "us_equity_daily_bar": "fetch_us_daily_bar_validation",
        "market_bar_1d": "fetch_daily_bar",
    }
    return defaults.get(data_domain, "fetch_daily_bar")
