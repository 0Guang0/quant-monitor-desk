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
from backend.app.datasources.base_adapter import BaseDataAdapter
from backend.app.datasources.exceptions import AdapterConfigurationError
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
        staged_fixture_mode: bool = False,
    ) -> None:
        self._source_registry = source_registry or SourceRegistry()
        if not self._source_registry.is_loaded():
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
        # ponytail: one flag for staged fixture + test fetch_port without FileRegistry
        self._fixture_mode = staged_fixture_mode or (
            fetch_port is not None and file_registry_factory is None
        )

    @property
    def staged_fixture_mode(self) -> bool:
        return self._fixture_mode

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

    def primary_source_for_domain(self, data_domain: str) -> str:
        return self._source_registry.get_domain_roles(data_domain).primary_source_id

    def assert_capability_declared(
        self,
        source_id: str,
        data_domain: str,
        operation: str,
    ) -> None:
        """Public capability gate for Layer1 ingestion (no private registry access)."""
        self._capability_registry.assert_source_domain_operation(
            source_id,
            data_domain,
            operation,
        )

    def check_resource_guard(self) -> tuple[Decision, str]:
        return ResourceGuard().check()

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
        op = operation or self._capability_registry.default_operation_for_domain(req.data_domain)
        plan = self._route_planner.plan(
            data_domain=req.data_domain,
            operation=op,
            run_id=req.run_id,
            job_id=job_id or req.run_id,
            market_id=req.market_id,
        )
        plan = _augment_plan_with_requested_source(plan, req.source_id)
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
        staged_route_override = (
            self._fixture_mode
            and self._fetch_port is not None
            and plan.route_status in {"VALIDATION_ONLY_BLOCKED", "DISABLED_SOURCE"}
        )
        if (plan.route_status != "READY" or plan.selected_source_id is None) and not staged_route_override:
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

        selected = plan.selected_source_id if plan.selected_source_id is not None else req.source_id
        if staged_route_override:
            selected = req.source_id

        if on_enter_fetching is not None:
            on_enter_fetching()

        # Planner validates capability for READY routes; re-assert only for overrides (DS-05).
        if plan.route_status != "READY" or staged_route_override:
            try:
                self._capability_registry.assert_source_domain_operation(
                    selected, req.data_domain, op
                )
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

        if self._fetch_port is None and not self._fixture_mode:
            raise AdapterConfigurationError(
                "fetch_port is required for production DataSourceService.fetch(); "
                "inject FetchPort or use build_staged_fixture_service()"
            )
        fetch_port = self._fetch_port or StubFetchPort(payload=b"{}")
        file_registry = self._file_registry_factory() if self._file_registry_factory else None
        if file_registry is None:
            if self._fixture_mode:
                from backend.app.datasources.adapters import create_test_adapter

                adapter = create_test_adapter(
                    selected,
                    self._source_registry,
                    self._data_root,
                    fetch_port=fetch_port,
                )
            else:
                raise AdapterConfigurationError(
                    "file_registry_factory is required for production "
                    "DataSourceService.fetch(); inject FileRegistry or use "
                    "build_staged_fixture_service() for staged fixture paths"
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
        fetch_kwargs: dict = {"con": con, "job_id": job_id}
        if isinstance(adapter, BaseDataAdapter):
            fetch_kwargs["record_fetch_log"] = False
        result = adapter.fetch(routed_req, **fetch_kwargs)
        self._fetch_log.write(con, result, req=routed_req, job_id=job_id)
        return result


def _augment_plan_with_requested_source(plan: SourceRoutePlan, requested_source_id: str) -> SourceRoutePlan:
    if (
        plan.route_status == "READY"
        and plan.selected_source_id
        and requested_source_id != plan.selected_source_id
    ):
        from dataclasses import replace

        flags = list(plan.quality_flags)
        flags.append("REQUESTED_SOURCE_OVERRIDDEN_BY_ROUTE")
        return replace(
            plan,
            quality_flags=flags,
            requested_source_id=requested_source_id,
        )
    return plan


def _default_operation(data_domain: str) -> str:
    defaults = {
        "cn_equity_daily_bar": "fetch_daily_bar",
        "cn_equity_minute_bar": "fetch_minute_bar",
        "cn_equity_realtime": "fetch_realtime_quote",
        "cn_equity_basic_financial": "fetch_basic_financial",
        "cn_filings": "fetch_filing_index",
        "cn_announcements": "fetch_announcement_index",
        "cn_pdf_reports": "fetch_pdf_report",
        "cn_index": "fetch_index_daily_bar",
        "cn_index_daily_bar": "fetch_index_daily_bar",
        "sector_board": "fetch_sector_board",
        "us_equity_daily_bar": "fetch_us_daily_bar_validation",
        "etf_daily_bar": "fetch_etf_daily_bar_validation",
        "global_asset_reference": "fetch_global_asset_reference",
        "security_list": "fetch_security_list",
        "market_bar_1d": "fetch_daily_bar",
        "macro_supplementary": "fetch_macro_series",
        "macro_series": "fetch_macro_series",
        "capital_flow": "fetch_capital_flow",
        "central_bank_policy": "fetch_policy_rate",
        "commodity_daily_bar": "fetch_commodity_daily_bar",
        "concept_theme": "fetch_concept_theme",
        "cot_positioning": "fetch_cot_positioning",
        "credit_gap": "fetch_credit_to_gdp_gap",
        "crypto_asset_reference": "fetch_crypto_asset_reference",
        "crypto_derivatives": "fetch_derivatives_instruments",
        "crypto_futures_term_structure": "fetch_futures_term_structure",
        "crypto_options_surface": "fetch_options_surface",
        "crypto_spot_market": "fetch_spot_market_reference",
        "development_indicator": "fetch_indicator_series",
        "event_market_contract": "fetch_event_market_contracts",
        "event_resolution_evidence": "fetch_event_resolution_evidence",
        "fx_daily_bar": "fetch_fx_daily_bar",
        "global_macro_reference": "fetch_macro_reference",
        "global_market_daily_bar": "fetch_global_daily_bar",
        "inflation_expectation": "fetch_inflation_expectation_reference",
        "prediction_market_probability": "fetch_prediction_market_probability",
        "regulated_event_contract": "fetch_regulated_event_contracts",
        "research_report": "fetch_research_report_index",
        "supplemental_web_evidence": "fetch_supplemental_web_evidence",
        "us_filings": "fetch_company_filings",
        "us_insider_form4": "fetch_form4_transactions",
        "us_option_chain": "fetch_us_option_chain_validation",
        "us_treasury_yield_curve": "fetch_yield_curve",
        "vix_cds_supplement": "fetch_vix_cds_supplement",
        # ponytail: domain default only; catalog loader not on fetch hot path
        "provider_metadata_only": "describe_architecture_reference",
    }
    return defaults.get(data_domain, "fetch_daily_bar")


def build_staged_fixture_service(
    *,
    data_root: Path,
    fixture_path: Path,
    row_count: int = 1,
) -> DataSourceService:
    """Staged micro-fetch facade with injected fixture port (Batch 2.5 Phase 3)."""
    from backend.app.datasources.adapters.fetch_port import LocalFixtureFetchPort

    return DataSourceService(
        data_root=data_root,
        fetch_port=LocalFixtureFetchPort(fixture_path, row_count=row_count),
        staged_fixture_mode=True,
    )
