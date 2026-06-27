"""Phase 2–4 task evidence capture and markdown formatters (PR-R2a extract)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from backend.app import config as app_config
from backend.app.datasources.service import DataSourceService, build_staged_fixture_service
from backend.app.layer1_axes.evidence_sandbox import resolve_task_sandbox_db
from backend.app.layer1_axes.ingestion import (
    FRED_PRIMARY_DEFERRED_NOTE,
    FROZEN_STAGED_INDICATOR,
    MACRO_FIXTURE_RELATIVE,
    IndicatorRoutePreview,
    IngestionRouteBinding,
    Layer1ObservationIngestionService,
    MicroFetchResult,
)
from backend.app.layer1_axes.ingestion_inventory import _relative_to_project
from backend.app.layer1_axes.sandbox_bootstrap import (
    PHASE3_SANDBOX_DIRNAME,
    PHASE4_SANDBOX_DIRNAME,
    prepare_phase3_sandbox,
    prepare_phase4_data_root,
    prepare_phase4_fallback_sandbox,
)
from backend.app.ops.layer1_evidence.formatters import (
    format_phase2_no_mutation_md,
    format_phase2_route_preview_md,
    format_phase3_no_clean_write_md,
    format_phase4_inventory_delta_md,
)

_relative_path = _relative_to_project

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
PHASE3_EVIDENCE_JSON = "phase3_micro_fetch_evidence.json"
PHASE3_NO_CLEAN_WRITE_MD = "phase3_no_clean_write_proof.md"
PHASE4_EVIDENCE_JSON = "phase4_clean_write_and_snapshot_evidence.json"
PHASE4_INVENTORY_DELTA_MD = "phase4_inventory_delta.md"

PHASE4_MUTATION_TABLES: tuple[str, ...] = (
    "axis_observation",
    "fetch_log",
    "file_registry",
    "validation_report",
    "write_audit_log",
    "axis_feature_snapshot",
    "axis_interpretation_snapshot",
    "axis_snapshot_lineage",
    "data_quality_log",
)

PHASE3_MUTATION_TABLES: tuple[str, ...] = (
    "axis_observation",
    "fetch_log",
    "file_registry",
    "job_event_log",
)


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


def _micro_fetch_to_dict(result: MicroFetchResult) -> dict[str, Any]:
    return {
        "indicator_id": result.indicator_id,
        "as_of": result.as_of.isoformat(),
        "binding": _binding_to_dict(result.binding),
        "route_plan": result.route_plan.to_payload_dict(),
        "fetch_result": result.fetch_result.model_dump(),
        "run_id": result.run_id,
        "job_id": result.job_id,
        "fetch_id": result.fetch_id,
        "file_registry_ids": list(result.file_registry_ids),
        "resource_guard_decision": result.resource_guard_decision,
        "resource_guard_reason": result.resource_guard_reason,
        "staged_fixture_path": result.staged_fixture_path,
        "fred_primary_deferred": True,
        "fred_primary_deferred_note": FRED_PRIMARY_DEFERRED_NOTE,
    }


def capture_phase3_micro_fetch_evidence(
    *,
    service: Layer1ObservationIngestionService,
    indicator_id: str,
    as_of: date,
    evidence_dir: Path | str,
) -> dict[str, Any]:
    """Run micro-fetch staging and persist Phase 3 evidence artifacts."""
    out = Path(evidence_dir)
    out.mkdir(parents=True, exist_ok=True)
    db_path = service._db_path
    before_counts = service._row_counts(PHASE3_MUTATION_TABLES)
    result = service.micro_fetch_staging(indicator_id=indicator_id, as_of=as_of)
    after_counts = service._row_counts(PHASE3_MUTATION_TABLES)
    before_obs = before_counts.get("axis_observation") or 0
    after_obs = after_counts.get("axis_observation") or 0
    before_fetch = before_counts.get("fetch_log") or 0
    after_fetch = after_counts.get("fetch_log") or 0
    before_files = before_counts.get("file_registry") or 0
    after_files = after_counts.get("file_registry") or 0
    proof = {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "db_path": _relative_path(db_path),
        "axis_observation_unchanged": before_obs == after_obs,
        "fetch_log_delta": after_fetch - before_fetch,
        "file_registry_delta": after_files - before_files,
        "before_counts": before_counts,
        "after_counts": after_counts,
    }
    payload: dict[str, Any] = {
        "phase": "phase3_micro_fetch",
        "generated_at": proof["generated_at"],
        "frozen_indicator": FROZEN_STAGED_INDICATOR,
        "micro_fetch": _micro_fetch_to_dict(result),
        "no_clean_write_proof": proof,
    }
    json_path = out / PHASE3_EVIDENCE_JSON
    md_path = out / PHASE3_NO_CLEAN_WRITE_MD
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_phase3_no_clean_write_md(proof), encoding="utf-8")
    return payload


def capture_task_phase3_evidence(
    evidence_dir: Path | str,
    *,
    as_of: date,
    db_path: Path | str | None = None,
    data_root: Path | str | None = None,
    datasource: DataSourceService | None = None,
) -> dict[str, Any]:
    """Write task execute-evidence for Phase 3 using an isolated fresh sandbox."""
    out = Path(evidence_dir)
    _load_phase2_gate(out)
    layout = prepare_phase3_sandbox(out)
    phase3_db = layout.db_path
    phase3_data_root = layout.data_root

    fixture_path = app_config.PROJECT_ROOT / MACRO_FIXTURE_RELATIVE
    resolved_datasource = datasource or build_staged_fixture_service(
        data_root=phase3_data_root,
        fixture_path=fixture_path,
    )
    service = Layer1ObservationIngestionService(
        db_path=phase3_db,
        data_root=phase3_data_root,
        datasource=resolved_datasource,
    )
    payload = capture_phase3_micro_fetch_evidence(
        service=service,
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=as_of,
        evidence_dir=out,
    )
    payload["evidence_baseline_strategy"] = "fresh_phase3_sandbox"
    payload["evidence_data_root"] = _relative_path(phase3_data_root)
    payload["evidence_db_path"] = _relative_path(phase3_db)
    json_path = out / PHASE3_EVIDENCE_JSON
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def capture_task_phase2_evidence(
    evidence_dir: Path | str,
    *,
    as_of: date,
    db_path: Path | str | None = None,
    data_root: Path | str | None = None,
) -> dict[str, Any]:
    """Write task execute-evidence for Phase 2 using project/sandbox targets."""
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
    resolved = resolve_task_sandbox_db(
        evidence_dir=out,
        sandbox_db=sandbox_db,
        target_db=targets.target_db,
        target_db_exists=targets.target_db_exists,
        copy_sandbox_db=copy_sandbox_db,
    )
    inspect_db = resolved.inspect_db
    db_capture_strategy = resolved.db_capture_strategy
    baseline_db_relative = resolved.baseline_db_relative or _relative_path(sandbox_db)

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


def capture_phase4_clean_write_evidence(
    *,
    service: Layer1ObservationIngestionService,
    indicator_id: str,
    as_of: date,
    evidence_dir: Path | str,
    phase1_inventory: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run Phase 4 commit and persist clean-write + snapshot evidence."""
    out = Path(evidence_dir)
    out.mkdir(parents=True, exist_ok=True)
    db_path = service._db_path
    before_counts = service._row_counts(PHASE4_MUTATION_TABLES)
    result = service.commit_clean_observation_and_snapshots(
        indicator_id=indicator_id,
        as_of=as_of,
    )
    after_counts = service._row_counts(PHASE4_MUTATION_TABLES)
    table_deltas = {
        name: {"before": before_counts.get(name), "after": after_counts.get(name)}
        for name in PHASE4_MUTATION_TABLES
    }
    delta_doc = {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "db_path": _relative_path(db_path),
        "frozen_indicator": FROZEN_STAGED_INDICATOR,
        "staged_fixture_path": MACRO_FIXTURE_RELATIVE,
        "fred_primary_deferred": True,
        "table_deltas": table_deltas,
        "phase1_baseline_attached": phase1_inventory is not None,
    }
    payload: dict[str, Any] = {
        "phase": "phase4_clean_write",
        "generated_at": delta_doc["generated_at"],
        "frozen_indicator": FROZEN_STAGED_INDICATOR,
        "commit": {
            "indicator_id": result.indicator_id,
            "as_of": result.as_of.isoformat(),
            "validation_report_id": result.validation_report_id,
            "observation_id": result.observation_id,
            "feature_id": result.feature_id,
            "interpretation_id": result.interpretation_id,
            "lineage_snapshot_id": result.lineage_snapshot_id,
            "source_fetch_ids": list(result.source_fetch_ids),
            "source_content_hashes": list(result.source_content_hashes),
            "observation_write_status": result.observation_write_status,
            "feature_write_status": result.feature_write_status,
            "interpretation_write_status": result.interpretation_write_status,
            "lineage_write_status": result.lineage_write_status,
            "staged_fixture_path": result.staged_fixture_path,
            "fred_primary_deferred_note": FRED_PRIMARY_DEFERRED_NOTE,
        },
        "inventory_delta": delta_doc,
    }
    if phase1_inventory is not None:
        payload["phase1_baseline_classification"] = phase1_inventory.get(
            "db_evidence_classification"
        )
    json_path = out / PHASE4_EVIDENCE_JSON
    md_path = out / PHASE4_INVENTORY_DELTA_MD
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_phase4_inventory_delta_md(delta_doc), encoding="utf-8")
    return payload


def capture_task_phase4_evidence(
    evidence_dir: Path | str,
    *,
    as_of: date,
    db_path: Path | str | None = None,
    data_root: Path | str | None = None,
    datasource: DataSourceService | None = None,
) -> dict[str, Any]:
    """Write task execute-evidence for Phase 4 aligned with Phase 1 sandbox baseline."""
    from backend.app.layer1_axes.ingestion_inventory import (
        INVENTORY_JSON_NAME,
        SANDBOX_BASELINE_DIRNAME,
        TARGET_DB_RELATIVE,
        copy_sandbox_db,
        resolve_phase1_target_paths,
    )

    out = Path(evidence_dir)
    _load_phase2_gate(out)
    phase1_inventory = None
    inv_path = out / INVENTORY_JSON_NAME
    if inv_path.is_file():
        phase1_inventory = json.loads(inv_path.read_text(encoding="utf-8"))

    targets = resolve_phase1_target_paths(data_root=data_root, db_path=db_path)
    sandbox_db = out / SANDBOX_BASELINE_DIRNAME / TARGET_DB_RELATIVE
    fallback_layout = prepare_phase4_fallback_sandbox(out)
    resolved = resolve_task_sandbox_db(
        evidence_dir=out,
        sandbox_db=sandbox_db,
        target_db=targets.target_db,
        target_db_exists=targets.target_db_exists,
        copy_sandbox_db=copy_sandbox_db,
        fallback_sandbox_db=fallback_layout.db_path,
        fallback_strategy="fresh_phase4_sandbox_fallback",
    )
    inspect_db = resolved.inspect_db
    db_capture_strategy = resolved.db_capture_strategy

    fixture_path = app_config.PROJECT_ROOT / MACRO_FIXTURE_RELATIVE
    phase4_data_root = prepare_phase4_data_root(out)
    resolved_datasource = datasource or build_staged_fixture_service(
        data_root=phase4_data_root,
        fixture_path=fixture_path,
    )
    service = Layer1ObservationIngestionService(
        db_path=inspect_db,
        data_root=phase4_data_root,
        datasource=resolved_datasource,
    )
    payload = capture_phase4_clean_write_evidence(
        service=service,
        indicator_id=FROZEN_STAGED_INDICATOR,
        as_of=as_of,
        evidence_dir=out,
        phase1_inventory=phase1_inventory,
    )
    payload["evidence_baseline_strategy"] = db_capture_strategy
    payload["evidence_data_root"] = _relative_path(phase4_data_root)
    payload["evidence_db_path"] = _relative_path(inspect_db)
    payload["phase1_baseline_attached"] = phase1_inventory is not None
    json_path = out / PHASE4_EVIDENCE_JSON
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def official_macro_bundle_layer1_preview(bundle: dict[str, Any]) -> dict[str, Any]:
    """Map official_macro_evidence_v1 to minimal Layer1 ingestion evidence preview (R3H-01 §9.7)."""
    if not bundle.get("source_fetch_id") or not bundle.get("content_hash"):
        raise ValueError("official macro bundle missing source_fetch_id or content_hash")
    observations = bundle.get("observations") or []
    sample = observations[0] if observations else {}
    return {
        "source_id": bundle.get("source_id"),
        "data_domain": bundle.get("data_domain") or bundle.get("series_id"),
        "source_fetch_id": bundle.get("source_fetch_id"),
        "content_hash": bundle.get("content_hash"),
        "as_of_timestamp": bundle.get("as_of_timestamp"),
        "retrieved_at": bundle.get("retrieved_at"),
        "observation_count": len(observations),
        "sample_observation_date": sample.get("observation_date") or sample.get("report_date"),
    }


def official_macro_bundle_layer5_provenance(bundle: dict[str, Any]) -> dict[str, Any]:
    """Extract Layer5 factual_source provenance fields from official macro replay bundle."""
    fid, ch = str(bundle.get("source_fetch_id") or ""), str(bundle.get("content_hash") or "")
    return {"source_fetch_ids": (fid,) if fid else (), "source_content_hashes": (ch,) if ch else ()}


__all__ = [
    "NO_MUTATION_MD",
    "PHASE2_MUTATION_TABLES",
    "PHASE3_EVIDENCE_JSON",
    "PHASE3_MUTATION_TABLES",
    "PHASE3_NO_CLEAN_WRITE_MD",
    "PHASE3_SANDBOX_DIRNAME",
    "PHASE4_EVIDENCE_JSON",
    "PHASE4_INVENTORY_DELTA_MD",
    "PHASE4_MUTATION_TABLES",
    "PHASE4_SANDBOX_DIRNAME",
    "ROUTE_PREVIEW_JSON",
    "ROUTE_PREVIEW_MD",
    "capture_phase2_route_evidence",
    "capture_phase3_micro_fetch_evidence",
    "capture_phase4_clean_write_evidence",
    "capture_task_phase2_evidence",
    "capture_task_phase3_evidence",
    "capture_task_phase4_evidence",
    "format_phase2_no_mutation_md",
    "format_phase2_route_preview_md",
    "format_phase3_no_clean_write_md",
    "format_phase4_inventory_delta_md",
    "official_macro_bundle_layer1_preview",
    "official_macro_bundle_layer5_provenance",
]
