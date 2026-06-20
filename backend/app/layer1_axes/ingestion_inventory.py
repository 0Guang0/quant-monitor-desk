"""Phase 1 read-only pre-ingestion inventory (Batch 2.5 §8.2 / 018A §8 Phase 1)."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import duckdb
from backend.app import config as app_config
from backend.app.db.migrate import apply_migrations
from backend.app.ops.db_inspector import REQUIRED_TOP_LEVEL_FIELDS, DbInspector, InspectReport

# 018A §8 Phase 1 minimum key tables (row counts required in inventory evidence).
PHASE1_MINIMUM_KEY_TABLES: tuple[str, ...] = (
    "schema_version",
    "source_registry",
    "file_registry",
    "fetch_log",
    "data_sync_job",
    "job_event_log",
    "validation_report",
    "data_quality_log",
    "source_conflict",
    "manual_review_queue",
    "write_audit_log",
    "resource_guard_log",
    "axis_observation",
    "axis_feature_snapshot",
    "axis_interpretation_snapshot",
    "axis_snapshot_lineage",
)

TARGET_DB_RELATIVE = Path("duckdb") / "quant_monitor.duckdb"

DbEvidenceClassification = Literal[
    "schema_only_empty",
    "schema_with_config_only",
    "fixture_or_staged_evidence",
    "user_provided_data",
    "production_like_data",
    "unknown_data_present",
]

PHASE2_AUTHORIZED_CLASSIFICATIONS: frozenset[str] = frozenset(
    {"schema_only_empty", "schema_with_config_only"}
)

INVENTORY_JSON_NAME = "phase1_before_ingestion_inventory.json"
INVENTORY_MD_NAME = "phase1_before_ingestion_inventory.md"
SANDBOX_BASELINE_DIRNAME = ".phase1-baseline-sandbox"
STAGING_TABLES: tuple[str, ...] = ("stg_file_registry", "stg_foundation_smoke")
DATA_ROOT_SAMPLE_LIMIT = 20
CLASSIFICATION_MEMO_NAME = "phase1_data_classification.md"


@dataclass(frozen=True)
class Phase1TargetPaths:
    data_root: Path
    target_db: Path
    target_db_exists: bool

    def to_baseline_context(self) -> dict[str, Any]:
        return {
            "target_data_root": str(self.data_root.resolve()),
            "target_data_root_relative": _relative_to_project(self.data_root),
            "target_db_path": str(self.target_db.resolve()),
            "target_db_path_relative": _relative_to_project(self.target_db),
            "target_db_exists_at_capture": self.target_db_exists,
            "qmd_data_root_env": "QMD_DATA_ROOT",
        }


def _relative_to_project(path: Path) -> str:
    try:
        return path.resolve().relative_to(app_config.PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def resolve_phase1_target_paths(
    *,
    data_root: Path | str | None = None,
    db_path: Path | str | None = None,
) -> Phase1TargetPaths:
    """Resolve canonical project DB/data-root targets per config + ops contract."""
    root = Path(data_root) if data_root is not None else app_config.DATA_ROOT
    target_db = Path(db_path) if db_path is not None else root / TARGET_DB_RELATIVE
    return Phase1TargetPaths(
        data_root=root,
        target_db=target_db,
        target_db_exists=target_db.is_file(),
    )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def data_root_content_fingerprint(data_root: Path) -> dict[str, Any]:
    """Stable hash of file paths + sizes under data_root (read-only)."""
    if not data_root.exists():
        return {"exists": False, "file_count": 0, "content_sha256": file_sha256_bytes(b"")}
    files: list[tuple[str, int]] = []
    for path in sorted(data_root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(data_root).as_posix()
            files.append((rel, path.stat().st_size))
    payload = "\n".join(f"{name}:{size}" for name, size in files).encode("utf-8")
    return {
        "exists": True,
        "file_count": len(files),
        "content_sha256": file_sha256_bytes(payload),
    }


def file_sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def copy_provenance_for(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "copy_source": str(path.resolve()),
        "copy_sha256": file_sha256(path),
        "copy_size_bytes": int(stat.st_size),
    }


def copy_sandbox_db(source: Path, dest: Path) -> dict[str, Any]:
    """Copy DB for sandbox inspect; returns provenance recorded before use."""
    provenance = copy_provenance_for(source)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return provenance


def create_migrated_baseline_db(db_path: Path) -> None:
    """Create schema-only migrated DB (setup only — not called during read-only capture)."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    try:
        apply_migrations(con)
    finally:
        con.close()


def classify_db_evidence(
    report: InspectReport,
    *,
    staging_table_row_counts: dict[str, int] | None = None,
) -> DbEvidenceClassification:
    """Classify whether the DB holds only schema/config or ingestible evidence."""
    tables_by_name = {t["name"]: t for t in report.key_tables}
    schema_version_rows = int(tables_by_name.get("schema_version", {}).get("row_count") or 0)
    axis_obs_rows = int(tables_by_name.get("axis_observation", {}).get("row_count") or 0)
    fetch_rows = int(tables_by_name.get("fetch_log", {}).get("row_count") or 0)
    registry_rows = int(tables_by_name.get("source_registry", {}).get("row_count") or 0)
    file_registry_rows = int(tables_by_name.get("file_registry", {}).get("row_count") or 0)
    validation_rows = int(tables_by_name.get("validation_report", {}).get("row_count") or 0)
    manual_review_rows = int(tables_by_name.get("manual_review_queue", {}).get("row_count") or 0)
    staging_rows = sum((staging_table_row_counts or {}).values())
    data_rows = sum(
        int(tables_by_name[name].get("row_count") or 0)
        for name in PHASE1_MINIMUM_KEY_TABLES
        if name != "schema_version"
        and name in tables_by_name
        and tables_by_name[name].get("exists")
    )
    has_fetch_evidence = bool(report.evidence.get("latest_fetch", {}).get("fetch_time"))
    raw_count = int(report.data_root.get("raw_files_count") or 0)
    parquet_count = int(report.data_root.get("parquet_files_count") or 0)

    if axis_obs_rows > 0:
        return "production_like_data"
    if fetch_rows > 0 or has_fetch_evidence or raw_count > 0 or parquet_count > 0:
        return "fixture_or_staged_evidence"
    if staging_rows > 0:
        return "fixture_or_staged_evidence"
    if data_rows > 0:
        if (
            file_registry_rows > 0
            or validation_rows > 0
            or manual_review_rows > 0
            or int(tables_by_name.get("data_quality_log", {}).get("row_count") or 0) > 0
        ):
            return "user_provided_data"
        return "unknown_data_present"
    if registry_rows > 0:
        return "schema_with_config_only"
    if schema_version_rows > 0:
        return "schema_only_empty"
    return "schema_only_empty"


def assess_phase2_gate(inventory: dict[str, Any]) -> dict[str, Any]:
    """018A §8 Phase 1: block Phase 2 until baseline is authorized.

    Authorization paths (in order):
    1. Schema-only automated classifications.
    2. Signed operator classification memo linked in inventory.
    """
    classification = inventory["db_evidence_classification"]
    operator = inventory.get("operator_classification") or {}
    data_root_note = (
        "Data-root raw/parquet files alone trigger fixture_or_staged_evidence on dev "
        "machines; use operator_classification memo when lineage is known fixture."
    )

    if operator.get("operator_ack") and operator.get("memo_sha256"):
        return {
            "phase2_authorized": True,
            "stop_reason": None,
            "classification": classification,
            "authorization_source": "operator_classification_memo",
            "memo_path": operator.get("memo_path"),
            "data_root_classification_note": data_root_note,
        }

    authorized = classification in PHASE2_AUTHORIZED_CLASSIFICATIONS
    stop_reason = None
    if not authorized:
        stop_reason = (
            f"Phase 1 classification `{classification}` requires explicit lineage review "
            "before Phase 2 (018A §8 Phase 1 stop rule)."
        )
    return {
        "phase2_authorized": authorized,
        "stop_reason": stop_reason,
        "classification": classification,
        "authorization_source": "automated_classification" if authorized else None,
        "data_root_classification_note": data_root_note,
    }


def _sample_data_root_files(
    data_root: Path,
    *,
    limit: int = DATA_ROOT_SAMPLE_LIMIT,
) -> list[dict[str, Any]]:
    if not data_root.exists():
        return []
    samples: list[dict[str, Any]] = []
    for sub in ("raw", "parquet", "audit", "report"):
        base = data_root / sub
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            try:
                rel = path.relative_to(data_root).as_posix()
            except ValueError:
                continue
            samples.append(
                {
                    "relative_path": rel,
                    "size_bytes": path.stat().st_size,
                    "sha256": file_sha256(path),
                }
            )
            if len(samples) >= limit:
                return samples
    return samples


def _collect_readonly_db_extras(db_path: Path) -> dict[str, Any]:
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        tables = {
            str(row[0])
            for row in con.execute(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'main'
                """
            ).fetchall()
        }
        staging: dict[str, int] = {}
        for name in STAGING_TABLES:
            if name in tables:
                staging[name] = int(con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0])
        registry_rows: list[dict[str, Any]] = []
        if "source_registry" in tables:
            cols = {
                r[0]
                for r in con.execute(
                    """
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'source_registry'
                    """
                ).fetchall()
            }
            select_cols = [
                c for c in ("source_id", "source_name", "is_enabled", "allowed_domain") if c in cols
            ]
            if select_cols:
                quoted = ", ".join(f'"{c}"' for c in select_cols)
                query = f"SELECT {quoted} FROM source_registry ORDER BY source_id"
                rows = con.execute(query).fetchall()
                registry_rows = [dict(zip(select_cols, row, strict=True)) for row in rows]
        return {
            "staging_table_row_counts": staging,
            "source_registry_snapshot": registry_rows,
        }
    finally:
        con.close()


def record_operator_classification(
    inventory: dict[str, Any],
    *,
    memo_path: Path | str,
    classification: str,
    operator_ack: str,
    evidence_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Attach operator memo provenance and recompute phase2_gate (F-A3-01)."""
    memo = Path(memo_path)
    inventory = dict(inventory)
    inventory["operator_classification"] = {
        "classification": classification,
        "memo_path": str(memo.resolve()),
        "memo_path_relative": _relative_to_project(memo) if memo.is_file() else None,
        "memo_sha256": file_sha256(memo) if memo.is_file() else None,
        "operator_ack": operator_ack,
        "recorded_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    inventory["phase2_gate"] = assess_phase2_gate(inventory)
    if evidence_dir is not None:
        out = Path(evidence_dir)
        out.mkdir(parents=True, exist_ok=True)
        json_path = out / INVENTORY_JSON_NAME
        md_path = out / INVENTORY_MD_NAME
        payload = json.dumps(inventory, indent=2, sort_keys=True) + "\n"
        json_path.write_text(payload, encoding="utf-8")
        md_path.write_text(format_phase1_inventory_md(inventory), encoding="utf-8")
    return inventory


def capture_phase1_inventory(
    db_path: Path | str,
    data_root: Path | str,
    *,
    evidence_dir: Path | str | None = None,
    copy_source: Path | str | None = None,
    baseline_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run read-only DbInspector and optionally persist Phase 1 inventory evidence."""
    db = Path(db_path)
    root = Path(data_root)
    inspector = DbInspector(db, root)
    report = inspector.inspect()
    db_extras = _collect_readonly_db_extras(db)
    data_root_samples = _sample_data_root_files(root)
    classification = classify_db_evidence(
        report,
        staging_table_row_counts=db_extras.get("staging_table_row_counts"),
    )

    inventory: dict[str, Any] = {
        "phase": "phase1_before_ingestion",
        "inventory_type": "read_only",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "db_evidence_classification": classification,
        "baseline_context": baseline_context or {},
        "copy_provenance": copy_provenance_for(Path(copy_source)) if copy_source else None,
        "inspect": report.to_dict(),
        "phase1_minimum_key_tables": {
            name: _phase1_table_row_count(report, name) for name in PHASE1_MINIMUM_KEY_TABLES
        },
        "staging_table_row_counts": db_extras.get("staging_table_row_counts", {}),
        "source_registry_snapshot": db_extras.get("source_registry_snapshot", []),
        "data_root_file_samples": data_root_samples,
        "data_root_fingerprint": data_root_content_fingerprint(root),
        "phase2_gate": {},
    }
    inventory["phase2_gate"] = assess_phase2_gate(inventory)

    if evidence_dir is not None:
        out = Path(evidence_dir)
        out.mkdir(parents=True, exist_ok=True)
        json_path = out / INVENTORY_JSON_NAME
        md_path = out / INVENTORY_MD_NAME
        payload = json.dumps(inventory, indent=2, sort_keys=True) + "\n"
        json_path.write_text(payload, encoding="utf-8")
        md_path.write_text(format_phase1_inventory_md(inventory), encoding="utf-8")

    return inventory


def capture_task_phase1_evidence(evidence_dir: Path | str) -> dict[str, Any]:
    """Write task execute-evidence using project target paths + sandbox synthetic baseline."""
    targets = resolve_phase1_target_paths()
    out = Path(evidence_dir)
    sandbox_dir = out / SANDBOX_BASELINE_DIRNAME
    sandbox_db = sandbox_dir / TARGET_DB_RELATIVE

    if targets.target_db_exists:
        sandbox_db.parent.mkdir(parents=True, exist_ok=True)
        provenance = copy_sandbox_db(targets.target_db, sandbox_db)
        capture_strategy = "sandbox_copy_of_target_db"
        capture_note = (
            "Target project DB existed; read-only inspect used a sandbox copy with provenance."
        )
        inspect_db = sandbox_db
        copy_source: Path | None = targets.target_db
    else:
        create_migrated_baseline_db(sandbox_db)
        provenance = None
        copy_source = None
        capture_strategy = "synthetic_migrated_schema_only"
        capture_note = (
            "No project DB at target path; synthetic migrated schema-only baseline captured "
            "under execute-evidence sandbox. Re-run Phase 1 before Phase 4 if a real project DB "
            "is initialized later."
        )
        inspect_db = sandbox_db

    targets.data_root.mkdir(parents=True, exist_ok=True)
    baseline_context = targets.to_baseline_context()
    baseline_context.update(
        {
            "capture_strategy": capture_strategy,
            "capture_note": capture_note,
            "sandbox_db_path": str(inspect_db.resolve()),
            "sandbox_db_path_relative": _relative_to_project(inspect_db),
        }
    )
    if provenance is not None:
        baseline_context["sandbox_copy_provenance"] = provenance

    inventory = capture_phase1_inventory(
        inspect_db,
        targets.data_root,
        evidence_dir=out,
        copy_source=copy_source,
        baseline_context=baseline_context,
    )
    memo = out / CLASSIFICATION_MEMO_NAME
    if memo.is_file():
        inventory = record_operator_classification(
            inventory,
            memo_path=memo,
            classification=inventory["db_evidence_classification"],
            operator_ack="phase1_data_classification_memo_present",
            evidence_dir=out,
        )
    return inventory


def finalize_task_phase1_evidence(evidence_dir: Path | str) -> dict[str, Any]:
    """Regenerate inventory and apply operator classification memo when present."""
    return capture_task_phase1_evidence(evidence_dir)


def _phase1_table_row_count(report: InspectReport, table_name: str) -> int | None:
    for entry in report.key_tables:
        if entry.get("name") == table_name:
            if not entry.get("exists"):
                return None
            return entry.get("row_count")
    return None


def format_phase1_inventory_md(inventory: dict[str, Any]) -> str:
    inspect_payload = inventory["inspect"]
    classification = inventory["db_evidence_classification"]
    copy_prov = inventory.get("copy_provenance")
    gate = inventory.get("phase2_gate", {})
    baseline = inventory.get("baseline_context", {})
    operator = inventory.get("operator_classification") or {}
    inspect_status = inspect_payload.get("status")
    phase2_ok = gate.get("phase2_authorized", False)

    lines = [
        "# Phase 1 — Before Ingestion Inventory",
        "",
        f"- **Phase:** {inventory['phase']}",
        f"- **Mode:** {inspect_payload.get('mode')}",
        f"- **Inspect status:** {inspect_status}",
        f"- **DB evidence classification:** `{classification}`",
        f"- **Phase 2 authorized:** {phase2_ok}",
        f"- **Authorization source:** {gate.get('authorization_source')}",
        f"- **Generated at:** {inventory['generated_at']}",
    ]

    if operator:
        lines.extend(
            [
                "",
                "## Operator classification",
                "",
                f"- classification: `{operator.get('classification')}`",
                f"- memo_path: `{operator.get('memo_path')}`",
                f"- memo_sha256: `{operator.get('memo_sha256')}`",
                f"- operator_ack: {operator.get('operator_ack')}",
            ]
        )

    if baseline:
        lines.extend(
            [
                "",
                "## Baseline target (project)",
                "",
                f"- target_db_path: `{baseline.get('target_db_path')}`",
                f"- target_db_exists_at_capture: {baseline.get('target_db_exists_at_capture')}",
                f"- target_data_root: `{baseline.get('target_data_root')}`",
                f"- capture_strategy: `{baseline.get('capture_strategy')}`",
                f"- capture_note: {baseline.get('capture_note')}",
            ]
        )

    lines.extend(
        [
            "",
            "## Database (inspected)",
            "",
            f"- Path: `{inspect_payload['db']['path']}`",
            f"- Exists: {inspect_payload['db']['exists']}",
            f"- Read-only open: {inspect_payload['db']['read_only_open']}",
            f"- File size (bytes): {inspect_payload['db'].get('file_size_bytes')}",
            "",
            "## Data root",
            "",
            f"- Path: `{inspect_payload['data_root']['path']}`",
            f"- raw_files_count: {inspect_payload['data_root'].get('raw_files_count')}",
            f"- parquet_files_count: {inspect_payload['data_root'].get('parquet_files_count')}",
            f"- audit_files_count: {inspect_payload['data_root'].get('audit_files_count')}",
            f"- report_files_count: {inspect_payload['data_root'].get('report_files_count')}",
            "",
            "## Phase 1 minimum key table row counts",
            "",
            "| table | row_count |",
            "| ----- | --------- |",
        ]
    )
    for name, count in inventory["phase1_minimum_key_tables"].items():
        lines.append(f"| `{name}` | {count} |")

    staging = inventory.get("staging_table_row_counts") or {}
    if staging:
        lines.extend(
            [
                "",
                "## Staging table row counts",
                "",
                "| table | row_count |",
                "| ----- | --------- |",
            ]
        )
        for name, count in staging.items():
            lines.append(f"| `{name}` | {count} |")

    samples = inventory.get("data_root_file_samples") or []
    if samples:
        lines.extend(["", "## Data-root file samples (read-only)", ""])
        for entry in samples:
            rel = entry["relative_path"]
            size = entry["size_bytes"]
            digest = entry["sha256"]
            lines.append(f"- `{rel}` size={size} sha256=`{digest}`")

    registry = inventory.get("source_registry_snapshot") or []
    if registry:
        registry_json = json.dumps(registry, indent=2)
        lines.extend(
            ["", "## source_registry snapshot", "", "```json", registry_json, "```"]
        )

    validation_counts = inspect_payload["evidence"].get("validation_status_counts")
    lines.extend(
        [
            "",
            "## Evidence summary",
            "",
            f"- Latest fetch: {inspect_payload['evidence'].get('latest_fetch')}",
            f"- Job status counts: {inspect_payload['evidence'].get('job_status_counts')}",
            f"- Validation status counts: {validation_counts}",
            "",
            "## Inspect status note",
            "",
            _inspect_status_note(inspect_status, classification),
            "",
            "## Classification note",
            "",
            _classification_note(classification, phase2_ok, gate.get("stop_reason")),
        ]
    )

    if copy_prov:
        lines.extend(
            [
                "",
                "## Sandbox copy provenance",
                "",
                f"- copy_source: `{copy_prov['copy_source']}`",
                f"- copy_sha256: `{copy_prov['copy_sha256']}`",
                f"- copy_size_bytes: {copy_prov['copy_size_bytes']}",
            ]
        )

    missing = [f for f in REQUIRED_TOP_LEVEL_FIELDS if f not in inspect_payload]
    if missing:
        lines.extend(["", f"**Warning:** inspect missing fields: {missing}"])

    return "\n".join(lines) + "\n"


def _inspect_status_note(inspect_status: str | None, classification: str) -> str:
    if inspect_status == "WARN" and classification in PHASE2_AUTHORIZED_CLASSIFICATIONS:
        return (
            "Inspect status WARN reflects an empty data root / no vendor evidence yet. "
            "This does **not** block Phase 2 when classification is schema-only."
        )
    if inspect_status == "FAIL":
        return "Inspect status FAIL — do not proceed until inspect errors are resolved."
    return f"Inspect status `{inspect_status}` recorded for audit traceability."


def _classification_note(
    classification: str,
    phase2_authorized: bool,
    stop_reason: str | None,
) -> str:
    notes = {
        "schema_only_empty": (
            "Database has migrated schema only; no fetch/raw/parquet evidence."
        ),
        "schema_with_config_only": (
            "Database contains registry/config rows only; no fetch or observation evidence."
        ),
        "fixture_or_staged_evidence": (
            "Fetch log or data-root files present — classify as fixture/staged before Phase 2."
        ),
        "user_provided_data": (
            "Manual/file/validation evidence without fetch_log — confirm user authorization."
        ),
        "production_like_data": (
            "axis_observation rows present — stop and classify data lineage before Phase 2."
        ),
        "unknown_data_present": (
            "Unexpected row counts in Phase 1 tables — classify before Phase 2."
        ),
    }
    body = notes.get(classification, "Review inventory before Phase 2.")
    if phase2_authorized:
        return f"{body} Phase 2 route dry-run is authorized."
    return f"{body} **STOP:** {stop_reason}"
