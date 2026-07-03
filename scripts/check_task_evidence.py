#!/usr/bin/env python3
"""Validate per-task loop engineering evidence chain."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from loop_engineering_common import (
    extract_plan_ac_ids,
    infer_task_touched_paths,
    load_json,
    loop_required,
    normalize_ac_id,
    repo_relative,
    validate_context_pack,
)


REPO_ROOT = Path(__file__).resolve().parents[1]

M_DATA_03_CLOSEOUT_PATHS = (
    ".audit-sandbox/m-data-03/r2-live-20260703220000/tier-a-report.json",
    ".audit-sandbox/m-data-03/r2-live-20260703220000/tier-a-report-run2.json",
    ".audit-sandbox/m-data-03/r2-thicken-wb-deribit-20260703224024/tier-a-report.json",
    ".audit-sandbox/m-data-03/tier-b-closeout/tier-b-report.json",
    ".audit-sandbox/m-data-03/tier-c-closeout/tier-c-report.json",
)


def _read_json(path: Path) -> dict:
    return load_json(path) if path.is_file() else {}


def _audit_final_from_report(task_dir: Path) -> str | None:
    report = task_dir / "audit.report.md"
    if not report.is_file():
        return None
    text = report.read_text(encoding="utf-8")
    for line in reversed(text.splitlines()):
        if "PASS" in line.upper() or "FAIL" in line.upper():
            return line.strip()
    return None


def _evidence_path_exists(task_dir: Path, repo_root: Path, rel: str) -> bool:
    norm = rel.replace("\\", "/")
    if norm.startswith("..") or "/../" in norm:
        return False
    local = (task_dir / norm).resolve()
    try:
        local.relative_to(task_dir.resolve())
        if local.is_file():
            return True
    except ValueError:
        pass
    from repo_path_resolve import resolve_repo_path

    root = resolve_repo_path(norm).resolve()
    try:
        root.relative_to(repo_root.resolve())
        return root.is_file()
    except ValueError:
        return False


def check_task_evidence(task_dir: Path, *, repo_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    if not loop_required(task_dir):
        return []
    if repo_root is None:
        repo_root = REPO_ROOT

    context_pack_path = task_dir / "context_pack.json"
    if not context_pack_path.is_file():
        errors.append("missing context_pack.json")
    else:
        pack = _read_json(context_pack_path)
        errors.extend(validate_context_pack(pack))
        if not (pack.get("modules") or pack.get("source_authorities")):
            if any(
                p.startswith(("backend/", "scripts/"))
                for p in infer_task_touched_paths(task_dir)
            ):
                errors.append("context_pack.json has empty modules and source_authorities")

    loop_manifest = _read_json(task_dir / "loop_manifest.json")
    evidence_index = _read_json(task_dir / "evidence_index.json")
    audit_matrix = _read_json(task_dir / "audit_matrix.json")

    plan_acs = [normalize_ac_id(a) for a in extract_plan_ac_ids(task_dir)]
    manifest_acs = {
        normalize_ac_id(str(item.get("id")))
        for item in loop_manifest.get("acs") or []
        if item.get("id")
    }
    if plan_acs and loop_manifest:
        if not manifest_acs:
            errors.append(
                "loop_manifest has no AC entries (expected EXECUTION_INDEX §2 AC ids)"
            )
        else:
            missing = sorted(set(plan_acs) - manifest_acs)
            if missing:
                errors.append(f"loop_manifest missing plan AC ids: {missing}")

    def _walk_evidence(node: object, prefix: str = "") -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                _walk_evidence(value, f"{prefix}.{key}" if prefix else key)
        elif isinstance(node, list):
            for item in node:
                _walk_evidence(item, prefix)
        elif isinstance(node, str):
            rel = node.replace("\\", "/")
            if rel.endswith((".txt", ".md", ".json", ".jsonl")):
                if not _evidence_path_exists(task_dir, repo_root, rel):
                    errors.append(f"evidence_index missing file at {prefix}: {rel}")

    if evidence_index:
        _walk_evidence(evidence_index)

    if audit_matrix:
        final = str(audit_matrix.get("final", "")).upper()
        report_line = _audit_final_from_report(task_dir)
        if report_line and final and final not in report_line.upper():
            errors.append("audit_matrix.final inconsistent with audit.report.md conclusion")

        dimensions = audit_matrix.get("dimensions") or {}
        for dim, payload in dimensions.items():
            result = str((payload or {}).get("result", "")).lower()
            if "fail" in result and "fixed" not in result and "pass" not in result:
                repairs = loop_manifest.get("acs") or []
                has_repair = any((item.get("repair_items") or []) for item in repairs if isinstance(item, dict))
                repair_plan = task_dir / "REPAIR.plan.md"
                deferred = task_dir / "research" / "audit-deferred.md"
                if not has_repair and not repair_plan.is_file() and not deferred.is_file():
                    errors.append(f"audit dimension {dim} failed without repair/deferred artifact")

    task_json = load_json(task_dir / "task.json")
    status = str(task_json.get("status", "")).lower()
    if audit_matrix and status == "in_progress":
        final = str(audit_matrix.get("final", "")).upper()
        if final.startswith("PASS"):
            errors.append("task.json still in_progress but audit_matrix indicates pass")

    errors.extend(_check_m_data_03_closeout_sandboxes(task_dir, repo_root))

    return errors


def _check_m_data_03_closeout_sandboxes(task_dir: Path, repo_root: Path) -> list[str]:
    """M-DATA-03 grill AC: closeout sandbox reports must exist on disk."""
    if task_dir.name != "m-data-03-tier-a-live":
        return []
    missing = [
        rel
        for rel in M_DATA_03_CLOSEOUT_PATHS
        if not _evidence_path_exists(task_dir, repo_root, rel)
    ]
    if missing:
        return [f"m-data-03 closeout sandbox missing: {missing}"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_dir", help="Path to .trellis/tasks/<task>")
    args = parser.parse_args()

    task_dir = Path(args.task_dir)
    if not task_dir.is_absolute():
        task_dir = REPO_ROOT / args.task_dir
    if not task_dir.is_dir():
        print(f"task directory not found: {args.task_dir}", file=sys.stderr)
        return 1

    errors = check_task_evidence(task_dir)
    if errors:
        print("task evidence check FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print(f"OK: task evidence for {repo_relative(task_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
