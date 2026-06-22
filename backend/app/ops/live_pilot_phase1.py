"""Live pilot — phase1 (split from live_pilot.py, OP-01)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.app.config import DATA_ROOT, PROJECT_ROOT
from backend.app.datasources.capability_registry import SourceCapabilityRegistry
from backend.app.datasources.source_registry import SourceRegistry
from backend.app.ops.db_inspector import KEY_TABLES, DbInspector, format_text_report
from backend.app.ops.live_pilot_constants import (
    APPROVED_PILOT_REQUESTS,
    DEFAULT_PRODUCTION_DB,
    DEFAULT_SANDBOX_ROOT,
    DISABLED_PILOT_SOURCE_IDS,
    PHASE1_BASELINE_JSON,
    PHASE1_BASELINE_MD,
    PHASE1_CAPABILITY_JSON,
    PHASE1_NO_MUTATION_MD,
)
from backend.app.ops.mutation_proof import key_table_row_counts as _key_table_row_counts

def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_phase1_capability_snapshot() -> dict[str, Any]:
    """Read-only registry/capability status for approved pilot requests."""
    source_registry = SourceRegistry()
    source_registry.load()
    capability_registry = SourceCapabilityRegistry()
    capability_registry.load()

    pilot_requests: list[dict[str, Any]] = []
    for source_id, data_domain, operation in sorted(APPROVED_PILOT_REQUESTS):
        try:
            source = source_registry.get(source_id)
            source_in_registry = True
            source_enabled = source.is_enabled
            allowed_domains = sorted(source.allowed_domains)
        except SourceNotFoundError:
            source_in_registry = False
            source_enabled = False
            allowed_domains = []

        pilot_requests.append(
            {
                "source_id": source_id,
                "data_domain": data_domain,
                "operation": operation,
                "source_in_registry": source_in_registry,
                "source_enabled": source_enabled,
                "domain_allowed_for_source": data_domain in allowed_domains,
                "capability_declared": capability_registry.is_capability_declared(
                    source_id, data_domain
                ),
                "pilot_source_disabled": source_id in DISABLED_PILOT_SOURCE_IDS,
            }
        )

    return {
        "generated_at": _utc_now_iso(),
        "pilot_requests": pilot_requests,
        "disabled_pilot_source_ids": sorted(DISABLED_PILOT_SOURCE_IDS),
    }


def _format_phase1_baseline_md(
    payload: dict[str, Any],
    *,
    inspect_text: str,
) -> str:
    inspect = payload["inspect"]
    context = payload["baseline_context"]
    lines = [
        "# Phase 1 Baseline Inventory — Batch 2.75",
        "",
        f"- **Generated at:** {payload['generated_at']}",
        f"- **Inspect status:** {inspect.get('status')}",
        f"- **Mode:** {inspect.get('mode')}",
        f"- **DB path:** `{context.get('target_db_path')}`",
        f"- **DB exists:** {context.get('target_db_exists_at_capture')}",
        f"- **Data root:** `{context.get('target_data_root')}`",
        f"- **Capture strategy:** {context.get('capture_strategy')}",
        f"- **Read-only open:** {inspect.get('db', {}).get('read_only_open')}",
        "",
        inspect_text,
        "",
        "## Capability snapshot",
        "",
        f"See `{PHASE1_CAPABILITY_JSON}` for three approved pilot requests.",
    ]
    return "\n".join(lines) + "\n"


def _format_phase1_no_mutation_md(proof: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 — No Mutation Proof",
        "",
        f"- **Generated at:** {proof['generated_at']}",
        f"- **DB path:** `{proof['db_path']}`",
        f"- **DB hash unchanged:** {proof['db_hash_unchanged']}",
        f"- **Phase 1 zero mutation:** {proof['phase1_zero_mutation']}",
        "",
        "## Key table row counts",
        "",
        "| Table | Before | After |",
        "| ----- | ------ | ----- |",
    ]
    before = proof.get("before_key_table_counts") or {}
    after = proof.get("after_key_table_counts") or {}
    for name in KEY_TABLES:
        lines.append(f"| {name} | {before.get(name)} | {after.get(name)} |")
    return "\n".join(lines) + "\n"


def capture_phase1_baseline(
    *,
    db_path: Path,
    data_root: Path,
    evidence_dir: Path,
) -> dict[str, Any]:
    """Read-only Phase 1 baseline inventory + capability snapshot (zero mutation)."""
    db_path = Path(db_path)
    data_root = Path(data_root)
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    before_bytes = db_path.read_bytes() if db_path.is_file() else None
    before_counts = _key_table_row_counts(db_path)

    report = DbInspector(db_path, data_root).inspect()
    inspect_dict = report.to_dict()
    capability_snapshot = build_phase1_capability_snapshot()

    after_bytes = db_path.read_bytes() if db_path.is_file() else None
    after_counts = _key_table_row_counts(db_path)

    mutation_proof = {
        "generated_at": _utc_now_iso(),
        "db_path": str(db_path),
        "db_hash_unchanged": before_bytes == after_bytes,
        "before_key_table_counts": before_counts,
        "after_key_table_counts": after_counts,
        "phase1_zero_mutation": before_counts == after_counts and before_bytes == after_bytes,
    }

    baseline_context = {
        "target_db_path": str(db_path),
        "target_data_root": str(data_root),
        "target_db_exists_at_capture": db_path.is_file(),
        "capture_strategy": (
            "production_read_only" if db_path.is_file() else "synthetic_migrated_schema_only"
        ),
    }

    generated_at = _utc_now_iso()
    inventory_payload = {
        "generated_at": generated_at,
        "inspect": inspect_dict,
        "baseline_context": baseline_context,
        "capability_snapshot_ref": PHASE1_CAPABILITY_JSON,
    }

    (evidence_dir / PHASE1_BASELINE_JSON).write_text(
        json.dumps(inventory_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / PHASE1_BASELINE_MD).write_text(
        _format_phase1_baseline_md(inventory_payload, inspect_text=format_text_report(report)),
        encoding="utf-8",
    )
    (evidence_dir / PHASE1_NO_MUTATION_MD).write_text(
        _format_phase1_no_mutation_md(mutation_proof),
        encoding="utf-8",
    )
    (evidence_dir / PHASE1_CAPABILITY_JSON).write_text(
        json.dumps(capability_snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return {
        "generated_at": generated_at,
        "inspect": inspect_dict,
        "baseline_context": baseline_context,
        "capability_snapshot": capability_snapshot,
        "mutation_proof": mutation_proof,
    }


def capture_task_phase1_baseline_evidence(
    evidence_dir: Path | str,
    *,
    db_path: Path | None = None,
    data_root: Path | None = None,
) -> dict[str, Any]:
    """Execute helper: baseline against production paths or schema-only sandbox."""
    out = Path(evidence_dir)
    target_db = db_path or DEFAULT_PRODUCTION_DB
    target_root = data_root or DATA_ROOT

    if not target_db.is_file():
        sandbox = out / ".phase1-baseline-sandbox"
        sandbox_db_dir = sandbox / "duckdb"
        sandbox_db_dir.mkdir(parents=True, exist_ok=True)
        sandbox_data = sandbox / "data"
        sandbox_data.mkdir(parents=True, exist_ok=True)
        target_db = sandbox_db_dir / "quant_monitor.duckdb"
        if not target_db.is_file():
            import duckdb
            from backend.app.db.migrate import apply_migrations

            con = duckdb.connect(str(target_db))
            apply_migrations(con)
            con.close()
        target_root = sandbox_data

    return capture_phase1_baseline(
        db_path=target_db,
        data_root=target_root,
        evidence_dir=out,
    )
