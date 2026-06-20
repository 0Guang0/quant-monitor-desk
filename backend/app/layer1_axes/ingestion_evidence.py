"""Phase 2–4 task evidence capture and markdown formatters (PR-R2a extract)."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import duckdb
from backend.app import config as app_config
from backend.app.datasources.service import DataSourceService, build_staged_fixture_service
from backend.app.db.migrate import apply_migrations
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
PHASE3_SANDBOX_DIRNAME = ".phase3-micro-fetch-sandbox"
PHASE4_SANDBOX_DIRNAME = ".phase4-clean-write-sandbox"
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


def _format_count_table_md(title: str, counts: dict[str, int | None]) -> list[str]:
    lines = [f"## {title}", "", "| table | row_count |", "| ----- | --------- |"]
    for name, count in counts.items():
        lines.append(f"| `{name}` | {count} |")
    lines.append("")
    return lines


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
    ]
    lines.extend(_format_count_table_md("Before preview", proof.get("before_counts", {})))
    lines.extend(_format_count_table_md("After preview", proof.get("after_counts", {})))
    return "\n".join(lines) + "\n"


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


def format_phase3_no_clean_write_md(proof: dict[str, Any]) -> str:
    lines = [
        "# Phase 3 — No Clean Write Proof",
        "",
        f"- **Generated at:** {proof['generated_at']}",
        f"- **DB path:** `{proof['db_path']}`",
        f"- **axis_observation unchanged:** {proof['axis_observation_unchanged']}",
        f"- **fetch_log delta:** {proof['fetch_log_delta']}",
        f"- **file_registry delta:** {proof['file_registry_delta']}",
        "",
    ]
    lines.extend(_format_count_table_md("Before micro-fetch", proof.get("before_counts", {})))
    lines.extend(_format_count_table_md("After micro-fetch", proof.get("after_counts", {})))
    return "\n".join(lines) + "\n"


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
    from backend.app.layer1_axes.ingestion_inventory import TARGET_DB_RELATIVE

    out = Path(evidence_dir)
    _load_phase2_gate(out)
    sandbox_base = out / PHASE3_SANDBOX_DIRNAME
    if sandbox_base.exists():
        shutil.rmtree(sandbox_base)
    phase3_db = sandbox_base / TARGET_DB_RELATIVE
    phase3_data_root = sandbox_base / "data"
    phase3_db.parent.mkdir(parents=True, exist_ok=True)
    phase3_data_root.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(phase3_db))
    try:
        apply_migrations(con)
    finally:
        con.close()

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


def format_phase4_inventory_delta_md(delta: dict[str, Any]) -> str:
    lines = [
        "# Phase 4 — Inventory Delta",
        "",
        f"- **Generated at:** {delta['generated_at']}",
        f"- **DB path:** `{delta['db_path']}`",
        f"- **Frozen indicator:** `{delta['frozen_indicator']}`",
        f"- **Staged fixture:** `{delta.get('staged_fixture_path')}`",
        "",
        "## Row-count deltas",
        "",
        "| table | before | after | delta |",
        "| ----- | ------ | ----- | ----- |",
    ]
    for name, counts in delta.get("table_deltas", {}).items():
        before = counts.get("before")
        after = counts.get("after")
        delta_val = (after or 0) - (before or 0)
        lines.append(f"| `{name}` | {before} | {after} | {delta_val} |")
    lines.append("")
    return "\n".join(lines) + "\n"


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
    db_capture_strategy = "synthetic_migrated_schema_only"

    if sandbox_db.is_file():
        inspect_db = sandbox_db
        db_capture_strategy = "phase1_sandbox_copy_reused"
    elif targets.target_db_exists:
        sandbox_db.parent.mkdir(parents=True, exist_ok=True)
        copy_sandbox_db(targets.target_db, sandbox_db)
        inspect_db = sandbox_db
        db_capture_strategy = "sandbox_copy_aligned_with_phase1"
    else:
        sandbox_base = out / PHASE4_SANDBOX_DIRNAME
        if sandbox_base.exists():
            shutil.rmtree(sandbox_base)
        inspect_db = sandbox_base / TARGET_DB_RELATIVE
        inspect_db.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(str(inspect_db))
        try:
            apply_migrations(con)
        finally:
            con.close()
        db_capture_strategy = "fresh_phase4_sandbox_fallback"

    fixture_path = app_config.PROJECT_ROOT / MACRO_FIXTURE_RELATIVE
    phase4_data_root = out / PHASE4_SANDBOX_DIRNAME / "data"
    phase4_data_root.mkdir(parents=True, exist_ok=True)
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
]
