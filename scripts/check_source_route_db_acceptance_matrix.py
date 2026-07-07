#!/usr/bin/env python3
"""Validate documented source-route DB acceptance matrix against registry/capabilities."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

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
    if payload.get("live_authorized") is not True:
        return ["report was not generated with live_authorized=true"]
    return []


def _closure_violations(
    *,
    report_rows: dict[str, dict[str, object]],
    live_authorized: bool,
) -> list[str]:
    violations: list[str] = []
    for target in iter_matrix_targets():
        key = matrix_target_key(target)
        row = report_rows.get(key)
        if row is None:
            continue
        outcome = evaluate_matrix_row_closure(target, row, live_authorized=live_authorized)
        if outcome != "PASS":
            violations.append(
                f"{key} closure_outcome={outcome} status={row.get('status')} "
                f"failure_class={row.get('failure_class')}"
            )
    return violations


def build_report(
    *,
    report_path: str | None = None,
    live_authorized: bool = False,
) -> dict[str, object]:
    violations = validate_matrix_against_registry()
    rows: list[dict[str, object]] = []
    report_rows: dict[str, dict[str, object]] = {}
    closure_violations: list[str] = []
    report_metadata_violations: list[str] = []
    closure_summary: dict[str, object] | None = None

    if report_path:
        payload = json.loads(Path(report_path).read_text(encoding="utf-8"))
        if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
            for item in payload["rows"]:
                if isinstance(item, dict) and item.get("target"):
                    report_rows[str(item["target"])] = item
            report_metadata_violations = _report_metadata_violations(
                payload,
                live_authorized=live_authorized,
            )
            closure_summary = summarize_matrix_closure(payload, live_authorized=live_authorized)
            closure_violations = _closure_violations(
                report_rows=report_rows,
                live_authorized=live_authorized,
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
            row["closure_outcome"] = evaluate_matrix_row_closure(
                target,
                report_row,
                live_authorized=live_authorized,
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
        "closure_summary": closure_summary,
        "live_authorized": live_authorized,
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
    args = parser.parse_args(argv)

    report = build_report(
        report_path=args.report,
        live_authorized=args.live_authorized,
    )
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            f"status={report['status']} matrix_count={report['matrix_count']} "
            f"violations={len(report['violations'])} "
            f"closure_violations={len(report['closure_violations'])} "
            f"report_metadata_violations={len(report['report_metadata_violations'])}"
        )
        for violation in report["violations"]:
            print(f"CONTRACT_VIOLATION: {violation}")
        for violation in report["report_metadata_violations"]:
            print(f"REPORT_METADATA_VIOLATION: {violation}")
        for violation in report["closure_violations"]:
            print(f"CLOSURE_VIOLATION: {violation}")
    strict_fail = report["status"] != "PASS"
    return 1 if args.strict and strict_fail else 0


if __name__ == "__main__":
    sys.exit(main())
