"""Layer 1 observation ingestion bridge — route preview and staged ingest (Batch 2.5)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import duckdb
from backend.app import config as app_config
from backend.app.core.resource_guard import Decision
from backend.app.datasources.route_models import SourceRoutePlan
from backend.app.datasources.service import DataSourceService, ResourceGuardBlockedError
from backend.app.layer1_axes.axis_loader import AxisSpecLoader
from backend.app.layer1_axes.models import AxisIndicatorDefinition, AxisLoadResult

FROZEN_STAGED_INDICATOR = "ENV-E1-DGS10"
STAGED_DATA_DOMAIN = "macro_supplementary"
STAGED_OPERATION = "fetch_macro_series"
STAGED_SERIES_ID = "DGS10"
STAGED_UNIT = "pct"
MACRO_FIXTURE_RELATIVE = "tests/fixtures/layer1_macro_observation_fixture.json"
FRED_PRIMARY_DEFERRED_NOTE = (
    "B2.5-O-05: declared primary_source FRED:DGS10 deferred; "
    "staged route macro_supplementary.fetch_macro_series used"
)

DEFAULT_INGESTION_ALLOWLIST: frozenset[str] = frozenset({FROZEN_STAGED_INDICATOR})

FORBIDDEN_INDICATOR_REJECTED = "FORBIDDEN_INDICATOR"
BLINDSPOT_INDICATOR_REJECTED = "BLINDSPOT_INDICATOR"
NOT_OBSERVABLE_REJECTED = "NOT_OBSERVABLE"
DISABLED_INDICATOR_REJECTED = "DISABLED_INDICATOR"
UNKNOWN_INDICATOR_REJECTED = "UNKNOWN_INDICATOR"
NOT_ON_ALLOWLIST_REJECTED = "NOT_ON_ALLOWLIST"

PHASE2_MUTATION_TABLES: tuple[str, ...] = (
    "axis_observation",
    "fetch_log",
    "file_registry",
    "axis_feature_snapshot",
    "axis_interpretation_snapshot",
    "axis_snapshot_lineage",
)

ROUTE_PREVIEW_JSON = "phase2_route_preview.json"
ROUTE_PREVIEW_MD = "phase2_route_preview_matrix.md"
NO_MUTATION_MD = "phase2_no_mutation_proof.md"


class IngestionRejectedError(ValueError):
    """Indicator blocked before route preview or fetch."""

    def __init__(self, message: str, *, reason_code: str, indicator_id: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.indicator_id = indicator_id


@dataclass(frozen=True)
class IngestionRouteBinding:
    indicator_id: str
    axis_id: str
    data_domain: str
    operation: str
    frequency: str
    unit: str
    primary_source_declared: str
    validation_source: str
    fallback_policy: str
    series_id: str | None = None
    staged_route_note: str | None = None


@dataclass(frozen=True)
class IndicatorRoutePreview:
    indicator_id: str
    as_of: date
    binding: IngestionRouteBinding
    route_plan: SourceRoutePlan
    resource_guard_decision: str
    resource_guard_reason: str
    capability_verified: bool
    stop_reason: str | None = None


@dataclass(frozen=True)
class RoutePreviewResult:
    previews: tuple[IndicatorRoutePreview, ...]
    dry_run: bool = True


class Layer1ObservationIngestionService:
    """Controlled Layer 1 observation ingestion facade (§3.4 wiring)."""

    def __init__(
        self,
        *,
        db_path: Path | str,
        data_root: Path | str | None = None,
        datasource: DataSourceService | None = None,
        axis_loader: AxisSpecLoader | None = None,
        allowlist: frozenset[str] | None = None,
    ) -> None:
        self._db_path = Path(db_path)
        self._data_root = Path(data_root) if data_root is not None else app_config.DATA_ROOT
        self._datasource = datasource or DataSourceService(data_root=self._data_root)
        self._axis_loader = axis_loader or AxisSpecLoader()
        self._allowlist = allowlist if allowlist is not None else DEFAULT_INGESTION_ALLOWLIST
        self._axis_load: AxisLoadResult | None = None

    def _load_axes(self) -> AxisLoadResult:
        if self._axis_load is None:
            self._axis_load = self._axis_loader.load()
        return self._axis_load

    def _indicator_by_id(self, indicator_id: str) -> AxisIndicatorDefinition:
        loaded = self._load_axes()
        for indicator in loaded.indicators:
            if indicator.indicator_id == indicator_id:
                return indicator
        raise IngestionRejectedError(
            f"unknown indicator {indicator_id!r}",
            reason_code=UNKNOWN_INDICATOR_REJECTED,
            indicator_id=indicator_id,
        )

    @staticmethod
    def _assert_indicator_eligible(indicator: AxisIndicatorDefinition) -> None:
        if indicator.is_forbidden:
            raise IngestionRejectedError(
                f"indicator {indicator.indicator_id!r} is forbidden",
                reason_code=FORBIDDEN_INDICATOR_REJECTED,
                indicator_id=indicator.indicator_id,
            )
        if indicator.is_blindspot:
            raise IngestionRejectedError(
                f"indicator {indicator.indicator_id!r} is BlindSpot",
                reason_code=BLINDSPOT_INDICATOR_REJECTED,
                indicator_id=indicator.indicator_id,
            )
        if not indicator.is_observable:
            raise IngestionRejectedError(
                f"indicator {indicator.indicator_id!r} is not observable",
                reason_code=NOT_OBSERVABLE_REJECTED,
                indicator_id=indicator.indicator_id,
            )
        if not indicator.is_enabled:
            raise IngestionRejectedError(
                f"indicator {indicator.indicator_id!r} is disabled",
                reason_code=DISABLED_INDICATOR_REJECTED,
                indicator_id=indicator.indicator_id,
            )

    @staticmethod
    def _resolve_binding(indicator: AxisIndicatorDefinition) -> IngestionRouteBinding:
        if indicator.indicator_id == FROZEN_STAGED_INDICATOR:
            return IngestionRouteBinding(
                indicator_id=indicator.indicator_id,
                axis_id=indicator.axis_id,
                data_domain=STAGED_DATA_DOMAIN,
                operation=STAGED_OPERATION,
                frequency=indicator.frequency,
                unit=STAGED_UNIT,
                primary_source_declared=indicator.primary_source,
                validation_source=indicator.validation_source,
                fallback_policy=indicator.fallback_policy,
                series_id=STAGED_SERIES_ID,
                staged_route_note=FRED_PRIMARY_DEFERRED_NOTE,
            )
        raise IngestionRejectedError(
            f"indicator {indicator.indicator_id!r} has no staged route binding",
            reason_code=NOT_ON_ALLOWLIST_REJECTED,
            indicator_id=indicator.indicator_id,
        )

    def _verify_capability(
        self,
        binding: IngestionRouteBinding,
        route_plan: SourceRoutePlan,
    ) -> bool:
        """018A Phase 2 step 5: capability registry must declare domain/operation."""
        source_id = route_plan.selected_source_id
        if source_id is not None:
            self._datasource.assert_capability_declared(
                source_id,
                binding.data_domain,
                binding.operation,
            )
            return True
        primary = self._datasource.primary_source_for_domain(binding.data_domain)
        self._datasource.assert_capability_declared(
            primary,
            binding.data_domain,
            binding.operation,
        )
        return True

    @staticmethod
    def _enforce_resource_guard(guard_decision: Decision, guard_reason: str) -> None:
        if guard_decision in (Decision.PAUSE, Decision.HARD_STOP):
            raise ResourceGuardBlockedError(
                guard_reason or f"ResourceGuard {guard_decision.value}",
                decision=guard_decision,
            )

    @staticmethod
    def _compose_stop_reason(
        *,
        guard_decision: Decision,
        guard_reason: str,
        route_plan: SourceRoutePlan,
    ) -> str | None:
        reasons: list[str] = []
        if guard_decision in (Decision.PAUSE, Decision.HARD_STOP):
            reasons.append(f"resource_guard={guard_decision.value}: {guard_reason or 'blocked'}")
        if route_plan.route_status != "READY":
            reasons.append(
                f"route_status={route_plan.route_status}; "
                "Phase 2 stops until staged/authorized route is READY"
            )
        return "; ".join(reasons) if reasons else None

    def _row_counts(self, tables: tuple[str, ...]) -> dict[str, int | None]:
        con = duckdb.connect(str(self._db_path), read_only=True)
        counts: dict[str, int | None] = {}
        try:
            for name in tables:
                exists = con.execute(
                    """
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'main' AND table_name = ?
                    """,
                    [name],
                ).fetchone()[0]
                if not exists:
                    counts[name] = None
                    continue
                counts[name] = int(con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0])
        finally:
            con.close()
        return counts

    def preview_routes(
        self,
        *,
        indicators: list[str],
        as_of: date,
        run_id: str = "layer1-route-preview",
        job_id: str = "layer1-route-preview",
    ) -> RoutePreviewResult:
        """Dry-run SourceRoutePlan preview — no fetch or DB writes (Phase 2)."""
        previews: list[IndicatorRoutePreview] = []
        guard_decision, guard_reason = self._datasource.check_resource_guard()
        self._enforce_resource_guard(guard_decision, guard_reason)

        for indicator_id in indicators:
            indicator = self._indicator_by_id(indicator_id)
            self._assert_indicator_eligible(indicator)
            if indicator_id not in self._allowlist:
                raise IngestionRejectedError(
                    f"indicator {indicator_id!r} is not on the ingestion allowlist",
                    reason_code=NOT_ON_ALLOWLIST_REJECTED,
                    indicator_id=indicator_id,
                )
            binding = self._resolve_binding(indicator)
            route_plan = self._datasource.preview_route(
                data_domain=binding.data_domain,
                operation=binding.operation,
                run_id=run_id,
                job_id=job_id,
            )
            capability_verified = self._verify_capability(binding, route_plan)
            stop_reason = self._compose_stop_reason(
                guard_decision=guard_decision,
                guard_reason=guard_reason,
                route_plan=route_plan,
            )
            previews.append(
                IndicatorRoutePreview(
                    indicator_id=indicator_id,
                    as_of=as_of,
                    binding=binding,
                    route_plan=route_plan,
                    resource_guard_decision=guard_decision.value,
                    resource_guard_reason=guard_reason,
                    capability_verified=capability_verified,
                    stop_reason=stop_reason,
                )
            )
        return RoutePreviewResult(previews=tuple(previews), dry_run=True)


def _binding_to_dict(binding: IngestionRouteBinding) -> dict[str, Any]:
    return asdict(binding)


def _preview_to_dict(preview: IndicatorRoutePreview) -> dict[str, Any]:
    return {
        "indicator_id": preview.indicator_id,
        "as_of": preview.as_of.isoformat(),
        "intended_as_of_range": {
            "start": preview.as_of.isoformat(),
            "end": preview.as_of.isoformat(),
        },
        "binding": _binding_to_dict(preview.binding),
        "route_plan": preview.route_plan.to_payload_dict(),
        "resource_guard_decision": preview.resource_guard_decision,
        "resource_guard_reason": preview.resource_guard_reason,
        "capability_verified": preview.capability_verified,
        "stop_reason": preview.stop_reason,
    }


def format_phase2_route_preview_md(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 2 — Route Preview Matrix",
        "",
        f"- **Generated at:** {payload['generated_at']}",
        f"- **Frozen indicator:** `{payload['frozen_indicator']}`",
        f"- **Dry-run:** {payload['dry_run']}",
        f"- **FRED live deferred:** {payload.get('fred_primary_deferred')}",
        "",
        "## Allowlist",
        "",
    ]
    for item in payload.get("allowlist", []):
        lines.append(f"- `{item}`")
    lines.extend(["", "## Route previews", ""])
    for entry in payload.get("previews", []):
        plan = entry["route_plan"]
        binding = entry["binding"]
        lines.extend(
            [
                f"### `{entry['indicator_id']}` @ {entry['as_of']}",
                "",
                f"- data_domain: `{binding['data_domain']}`",
                f"- operation: `{binding['operation']}`",
                f"- series_id: `{binding.get('series_id')}`",
                f"- declared primary: `{binding['primary_source_declared']}`",
                f"- staged note: {binding.get('staged_route_note')}",
                f"- route_status: `{plan['route_status']}`",
                f"- selected_source_id: `{plan.get('selected_source_id')}`",
                f"- resource_guard: `{entry['resource_guard_decision']}`",
                f"- capability_verified: {entry.get('capability_verified')}",
                f"- intended_as_of_range: {entry.get('intended_as_of_range')}",
                f"- stop_reason: {entry.get('stop_reason')}",
                "",
                "| source_id | role | enabled | skip_reason |",
                "| --------- | ---- | ------- | ----------- |",
            ]
        )
        for candidate in plan.get("candidates", []):
            lines.append(
                f"| `{candidate['source_id']}` | {candidate['role']} | "
                f"{candidate['enabled']} | {candidate.get('skip_reason')} |"
            )
        lines.append("")
    proof = payload.get("mutation_proof", {})
    lines.extend(
        [
            "## No-mutation proof",
            "",
            f"- db_path: `{proof.get('db_path')}`",
            f"- db_capture_strategy: `{proof.get('db_capture_strategy')}`",
            f"- db_file_hash_unchanged: {proof.get('db_file_hash_unchanged')}",
            f"- row_counts_unchanged: {proof.get('row_counts_unchanged')}",
            f"- before: `{proof.get('before_counts')}`",
            f"- after: `{proof.get('after_counts')}`",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def format_phase2_no_mutation_md(proof: dict[str, Any]) -> str:
    lines = [
        "# Phase 2 — No Mutation Proof",
        "",
        f"- **Generated at:** {proof['generated_at']}",
        f"- **DB path:** `{proof['db_path']}`",
        f"- **DB file hash unchanged:** {proof.get('db_file_hash_unchanged')}",
        f"- **Capture strategy:** {proof.get('db_capture_strategy')}",
        f"- **Row counts unchanged:** {proof['row_counts_unchanged']}",
        "",
        "## Before preview",
        "",
        "| table | row_count |",
        "| ----- | --------- |",
    ]
    for name, count in proof.get("before_counts", {}).items():
        lines.append(f"| `{name}` | {count} |")
    lines.extend(["", "## After preview", "", "| table | row_count |", "| ----- | --------- |"])
    for name, count in proof.get("after_counts", {}).items():
        lines.append(f"| `{name}` | {count} |")
    lines.append("")
    return "\n".join(lines) + "\n"


def _relative_path(path: Path) -> str:
    from backend.app.layer1_axes.ingestion_inventory import _relative_to_project

    return _relative_to_project(path)


def _db_file_hash(db_path: Path) -> str:
    if not db_path.is_file():
        return hashlib.sha256(b"").hexdigest()
    return hashlib.sha256(db_path.read_bytes()).hexdigest()


def capture_phase2_route_evidence(
    *,
    service: Layer1ObservationIngestionService,
    indicators: list[str],
    as_of: date,
    evidence_dir: Path | str,
    phase2_gate: dict[str, Any] | None = None,
    db_capture_strategy: str = "unspecified",
    baseline_db_relative: str | None = None,
) -> dict[str, Any]:
    """Run dry-run preview and persist Phase 2 evidence artifacts."""
    out = Path(evidence_dir)
    out.mkdir(parents=True, exist_ok=True)
    db_path = service._db_path
    before_hash = _db_file_hash(db_path)
    before_counts = service._row_counts(PHASE2_MUTATION_TABLES)
    result = service.preview_routes(indicators=indicators, as_of=as_of)
    after_hash = _db_file_hash(db_path)
    after_counts = service._row_counts(PHASE2_MUTATION_TABLES)
    mutation_proof = {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "db_path": _relative_path(db_path),
        "db_path_absolute": str(db_path.resolve()),
        "db_file_hash_before": before_hash,
        "db_file_hash_after": after_hash,
        "db_file_hash_unchanged": before_hash == after_hash,
        "db_capture_strategy": db_capture_strategy,
        "baseline_db_relative": baseline_db_relative,
        "before_counts": before_counts,
        "after_counts": after_counts,
        "row_counts_unchanged": before_counts == after_counts,
    }
    fixture_path = app_config.PROJECT_ROOT / MACRO_FIXTURE_RELATIVE
    payload: dict[str, Any] = {
        "phase": "phase2_route_preview",
        "generated_at": mutation_proof["generated_at"],
        "frozen_indicator": FROZEN_STAGED_INDICATOR,
        "fred_primary_deferred": True,
        "fred_primary_deferred_note": FRED_PRIMARY_DEFERRED_NOTE,
        "staged_fixture_path": MACRO_FIXTURE_RELATIVE,
        "staged_fixture_exists": fixture_path.is_file(),
        "allowlist": sorted(service._allowlist),
        "dry_run": result.dry_run,
        "route_persistence_phase3_note": (
            "Phase 3 will persist SourceRoutePlan via job_event_log.payload_json "
            "(per source_route_plan.md §5 option 2); no source_route_log in this batch."
        ),
        "source_conflict_phase4_note": (
            "Frozen indicator validation_source=none_optional; SourceConflictValidator "
            "not applicable for single-source staged scope unless validation source added."
        ),
        "previews": [_preview_to_dict(p) for p in result.previews],
        "mutation_proof": mutation_proof,
    }
    if phase2_gate is not None:
        payload["phase2_gate"] = phase2_gate
    json_path = out / ROUTE_PREVIEW_JSON
    md_path = out / ROUTE_PREVIEW_MD
    proof_path = out / NO_MUTATION_MD
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_phase2_route_preview_md(payload), encoding="utf-8")
    proof_path.write_text(format_phase2_no_mutation_md(mutation_proof), encoding="utf-8")
    return payload


def _load_phase2_gate(evidence_dir: Path) -> dict[str, Any] | None:
    """Require Phase 1 authorization when inventory evidence is present (018A §8 Phase 1)."""
    from backend.app.layer1_axes.ingestion_inventory import INVENTORY_JSON_NAME

    inv_path = evidence_dir / INVENTORY_JSON_NAME
    if not inv_path.is_file():
        return None
    inventory = json.loads(inv_path.read_text(encoding="utf-8"))
    gate = inventory.get("phase2_gate") or {}
    if not gate.get("phase2_authorized"):
        raise RuntimeError(
            gate.get("stop_reason")
            or "Phase 2 route preview blocked: phase1 inventory not authorized"
        )
    return gate


def capture_task_phase2_evidence(
    evidence_dir: Path | str,
    *,
    as_of: date,
    db_path: Path | str | None = None,
    data_root: Path | str | None = None,
) -> dict[str, Any]:
    """Write task execute-evidence for Phase 2 using project/sandbox targets."""
    from backend.app.db.migrate import apply_migrations
    from backend.app.layer1_axes.ingestion_inventory import (
        INVENTORY_JSON_NAME,
        SANDBOX_BASELINE_DIRNAME,
        TARGET_DB_RELATIVE,
        copy_sandbox_db,
        resolve_phase1_target_paths,
    )

    targets = resolve_phase1_target_paths(data_root=data_root, db_path=db_path)
    out = Path(evidence_dir)
    _load_phase2_gate(out)
    phase2_gate = None
    inv_path = out / INVENTORY_JSON_NAME
    if inv_path.is_file():
        phase2_gate = json.loads(inv_path.read_text(encoding="utf-8")).get("phase2_gate")
    sandbox_db = out / SANDBOX_BASELINE_DIRNAME / TARGET_DB_RELATIVE
    db_capture_strategy = "synthetic_migrated_schema_only"
    baseline_db_relative = _relative_path(sandbox_db)

    if sandbox_db.is_file():
        inspect_db = sandbox_db
        db_capture_strategy = "phase1_sandbox_copy_reused"
    elif targets.target_db_exists:
        sandbox_db.parent.mkdir(parents=True, exist_ok=True)
        copy_sandbox_db(targets.target_db, sandbox_db)
        inspect_db = sandbox_db
        db_capture_strategy = "sandbox_copy_aligned_with_phase1"
    else:
        inspect_db = sandbox_db
        inspect_db.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(str(inspect_db))
        try:
            apply_migrations(con)
        finally:
            con.close()
        db_capture_strategy = "synthetic_migrated_schema_only"

    service = Layer1ObservationIngestionService(
        db_path=inspect_db,
        data_root=targets.data_root,
    )
    return capture_phase2_route_evidence(
        service=service,
        indicators=[FROZEN_STAGED_INDICATOR],
        as_of=as_of,
        evidence_dir=out,
        phase2_gate=phase2_gate,
        db_capture_strategy=db_capture_strategy,
        baseline_db_relative=baseline_db_relative,
    )
