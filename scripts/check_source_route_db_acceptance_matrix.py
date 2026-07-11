#!/usr/bin/env python3
"""Validate documented source-route DB acceptance matrix against registry/capabilities."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from backend.app.ops.matrix_live_evidence_honesty import (
    resolve_matrix_report_data_root,
    validate_matrix_live_evidence_honesty,
)
from backend.app.ops.source_route_db_acceptance_matrix import (
    DOCUMENTED_SOURCE_MATRIX,
    evaluate_matrix_row_closure,
    find_matrix_target_by_key,
    iter_matrix_targets,
    matrix_target_key,
    summarize_matrix_closure,
    validate_matrix_against_registry,
)


def _report_metadata_violations(
    payload: dict[str, object],
    *,
    live_authorized: bool,
) -> list[str]:
    if not live_authorized:
        return []
    violations: list[str] = []
    if payload.get("live_authorized") is not True:
        violations.append("report was not generated with live_authorized=true")
    closure_mode = payload.get("closure_mode")
    if closure_mode not in (None, "final_live_authorized"):
        violations.append(
            f"report closure_mode={closure_mode!r} incompatible with --live-authorized "
            "(expected final_live_authorized)"
        )
    return violations


def _closure_violations(
    *,
    report_rows: dict[str, dict[str, object]],
    closure_mode: str,
) -> list[str]:
    violations: list[str] = []
    for target in iter_matrix_targets():
        key = matrix_target_key(target)
        row = report_rows.get(key)
        if row is None:
            violations.append(f"{key} missing from report rows")
            continue
        outcome = evaluate_matrix_row_closure(
            target,
            row,
            closure_mode=closure_mode,  # type: ignore[arg-type]
        )
        cached = row.get("closure_outcome")
        if isinstance(cached, str) and cached != outcome:
            violations.append(
                f"{key} closure_outcome mismatch stored={cached!r} recomputed={outcome}"
            )
        if outcome != "PASS":
            violations.append(
                f"{key} closure_outcome={outcome} status={row.get('status')} "
                f"failure_class={row.get('failure_class')}"
            )
    return violations


def _matrix_scale_violations() -> list[str]:
    """文档 5.9.1 规模：22 源且 target key 唯一（原 pytest hasTwentyTwoDocumentedSources）。"""
    keys = [matrix_target_key(target) for target in iter_matrix_targets()]
    errors: list[str] = []
    if len(DOCUMENTED_SOURCE_MATRIX) != 22:
        errors.append(f"DOCUMENTED_SOURCE_MATRIX length={len(DOCUMENTED_SOURCE_MATRIX)} != 22")
    if len(keys) != len(set(keys)):
        errors.append("matrix target keys are not unique")
    return errors


def build_report(
    *,
    report_path: str | None = None,
    live_authorized: bool = False,
    data_root: str | None = None,
) -> dict[str, object]:
    closure_mode = "final_live_authorized" if live_authorized else "dry_run"
    violations = list(validate_matrix_against_registry()) + _matrix_scale_violations()
    rows: list[dict[str, object]] = []
    report_rows: dict[str, dict[str, object]] = {}
    closure_violations: list[str] = []
    report_metadata_violations: list[str] = []
    evidence_honesty_violations: list[str] = []
    closure_summary: dict[str, object] | None = None
    report_file: Path | None = Path(report_path) if report_path else None
    matrix_payload: dict[str, object] | None = None

    if report_path:
        matrix_payload = json.loads(Path(report_path).read_text(encoding="utf-8"))
        payload = matrix_payload
        if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
            for item in payload["rows"]:
                if isinstance(item, dict) and item.get("target"):
                    report_rows[str(item["target"])] = item
            report_metadata_violations = _report_metadata_violations(
                payload,
                live_authorized=live_authorized,
            )
            closure_summary = summarize_matrix_closure(
                payload,
                closure_mode=closure_mode,
            )
            closure_violations = _closure_violations(
                report_rows=report_rows,
                closure_mode=closure_mode,
            )
            if live_authorized and isinstance(matrix_payload, dict):
                resolved_root = resolve_matrix_report_data_root(
                    report_path=report_file,
                    payload=matrix_payload,
                    explicit_data_root=Path(data_root) if data_root else None,
                )
                if resolved_root is None:
                    evidence_honesty_violations.append(
                        "live-authorized report requires --data-root or report.data_root "
                        "or reports/source-matrix-acceptance.json under sandbox root"
                    )
                elif not resolved_root.is_dir():
                    evidence_honesty_violations.append(
                        f"matrix data_root does not exist: {resolved_root}"
                    )
                else:
                    evidence_honesty_violations.extend(
                        validate_matrix_live_evidence_honesty(resolved_root, matrix_payload)
                    )

    for target in iter_matrix_targets():
        key = matrix_target_key(target)
        row = {
            "target": key,
            "display_name": target.display_name,
            "positioning": target.positioning,
            "auth_env": list(target.auth_env),
            "requires_local_terminal": target.requires_local_terminal,
            "requires_license": target.requires_license,
            "expected_write_grade": target.expected_write_grade,
            "downstream_expectation": target.downstream_expectation,
        }
        if key in report_rows:
            report_row = report_rows[key]
            row["report"] = report_row
            cached = report_row.get("closure_outcome")
            if isinstance(cached, str):
                row["closure_outcome"] = cached
            else:
                row["closure_outcome"] = evaluate_matrix_row_closure(
                    target,
                    report_row,
                    closure_mode=closure_mode,
                )
        rows.append(row)

    missing_report_rows: list[str] = []
    if report_path:
        expected = {matrix_target_key(target) for target in iter_matrix_targets()}
        missing_report_rows = sorted(expected - set(report_rows))
    unexpected_report_targets = sorted(
        set(report_rows) - {matrix_target_key(target) for target in iter_matrix_targets()}
    )
    unknown_targets = sorted(
        target_key
        for target_key in report_rows
        if find_matrix_target_by_key(target_key) is None
    )
    if unknown_targets:
        unexpected_report_targets = sorted(set(unexpected_report_targets) | set(unknown_targets))

    status = (
        "PASS"
        if not violations
        and not missing_report_rows
        and not unexpected_report_targets
        and not closure_violations
        and not report_metadata_violations
        and not evidence_honesty_violations
        else "FAIL"
    )
    return {
        "status": status,
        "matrix_count": len(DOCUMENTED_SOURCE_MATRIX),
        "violations": violations,
        "rows": rows,
        "missing_report_targets": missing_report_rows,
        "unexpected_report_targets": unexpected_report_targets,
        "closure_violations": closure_violations,
        "report_metadata_violations": report_metadata_violations,
        "evidence_honesty_violations": evidence_honesty_violations,
        "closure_summary": closure_summary,
        "live_authorized": live_authorized,
        "closure_mode": closure_mode if live_authorized else "dry_run",
        "data_root": data_root,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=["json", "text"], default="json")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--report", default=None, help="Optional aggregated acceptance report JSON")
    parser.add_argument(
        "--live-authorized",
        action="store_true",
        help="Evaluate report rows against live-authorized closure semantics",
    )
    parser.add_argument(
        "--data-root",
        default=None,
        help="Isolated sandbox data_root for live evidence honesty scan (--live-authorized)",
    )
    args = parser.parse_args(argv)

    report = build_report(
        report_path=args.report,
        live_authorized=args.live_authorized,
        data_root=args.data_root,
    )
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            f"status={report['status']} matrix_count={report['matrix_count']} "
            f"violations={len(report['violations'])} "
            f"closure_violations={len(report['closure_violations'])} "
            f"report_metadata_violations={len(report['report_metadata_violations'])} "
            f"evidence_honesty_violations={len(report['evidence_honesty_violations'])}"
        )
        for violation in report["violations"]:
            print(f"CONTRACT_VIOLATION: {violation}")
        for violation in report["report_metadata_violations"]:
            print(f"REPORT_METADATA_VIOLATION: {violation}")
        for violation in report["closure_violations"]:
            print(f"CLOSURE_VIOLATION: {violation}")
        for violation in report["evidence_honesty_violations"]:
            print(f"EVIDENCE_HONESTY_VIOLATION: {violation}")
    strict_fail = report["status"] != "PASS"
    return 1 if args.strict and strict_fail else 0


if __name__ == "__main__":
    sys.exit(main())
