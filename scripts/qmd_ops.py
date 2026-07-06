#!/usr/bin/env python3
"""Transitional QMD ops CLI (Round 3 Batch 1 — thin wrapper only)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from backend.app.config import DATA_ROOT
from backend.app.ops.db_inspector import DbInspector, format_text_report


def _default_db_path() -> Path:
    return DATA_ROOT / "duckdb" / "quant_monitor.duckdb"


def _default_data_root() -> Path:
    return DATA_ROOT


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="QMD transitional ops CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    inspect_parser = sub.add_parser("db-inspect", help="Read-only DB and data-root inspection")
    inspect_parser.add_argument("--db", type=Path, default=None, help="DuckDB path")
    inspect_parser.add_argument("--data-root", type=Path, default=None, help="Data root path")
    inspect_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    inspect_parser.add_argument("--output", type=Path, default=None, help="Optional output file")
    inspect_parser.add_argument("--limit", type=int, default=20, help="Scan/evidence row cap")
    inspect_parser.add_argument(
        "--include-path-check",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Count raw/parquet files under data root",
    )
    inspect_parser.add_argument(
        "--profile",
        default=os.getenv("QMD_RESOURCE_PROFILE", "eco"),
        help="Resource profile for ConnectionManager",
    )

    data_parser = sub.add_parser("data", help="Data sync CLI (dry-run / route-preview)")
    data_parser.add_argument("rest", nargs=argparse.REMAINDER)

    accept_parser = sub.add_parser(
        "accept-source-route-db",
        help="Production-equivalent source-route DB acceptance spine",
    )
    accept_parser.add_argument(
        "--target",
        required=True,
        help="Acceptance target as data_domain:source_id:operation",
    )
    accept_parser.add_argument("--data-root", required=True, type=Path, help="Isolated data root")
    accept_parser.add_argument(
        "--report",
        required=True,
        type=Path,
        help="Acceptance report JSON path",
    )
    accept_parser.add_argument(
        "--allow-live-fetch",
        action="store_true",
        help="Authorize live external fetch attempts when implementation supports them",
    )
    accept_parser.add_argument("--format", choices=["json", "text"], default="json")

    args = parser.parse_args(argv)
    if args.command == "data":
        from backend.app.cli.main import main as data_main

        rest = list(args.rest or [])
        if rest and rest[0] == "--":
            rest = rest[1:]
        return data_main(["data", *rest])

    if args.command == "accept-source-route-db":
        from backend.app.ops.source_route_db_acceptance import (
            AcceptanceRequest,
            SourceRouteDbAcceptanceSpine,
            write_acceptance_report,
        )

        try:
            request = AcceptanceRequest.from_target(args.target)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

        report = SourceRouteDbAcceptanceSpine().execute(
            request,
            data_root=args.data_root,
            live_authorized=args.allow_live_fetch,
        )
        payload = report.to_dict()
        output = write_acceptance_report(report, args.report)
        if args.format == "json":
            print(output)
        else:
            print(f"{payload['status']} {payload['failure_class']}: {', '.join(payload['errors'])}")
        return 0 if payload["status"] == "PASS" else 1

    if args.command != "db-inspect":
        parser.error(f"unsupported command: {args.command}")

    db_path = args.db if args.db is not None else _default_db_path()
    data_root = args.data_root if args.data_root is not None else _default_data_root()
    inspector = DbInspector(
        db_path,
        data_root,
        limit=args.limit,
        include_path_check=args.include_path_check,
        profile=args.profile,
    )
    report = inspector.inspect()

    if args.format == "json":
        output = json.dumps(report.to_dict(), indent=2)
    else:
        output = format_text_report(report)

    if args.output is not None:
        if not args.output.parent.is_dir():
            print(
                f"error: output parent directory does not exist: {args.output.parent}",
                file=sys.stderr,
            )
            return 2
        try:
            args.output.write_text(
                output + ("\n" if args.format == "text" else ""),
                encoding="utf-8",
            )
        except OSError as exc:
            print(f"error: failed to write output file: {exc}", file=sys.stderr)
            return 2
    else:
        print(output)

    return 0 if report.status != "FAIL" else 1


if __name__ == "__main__":
    sys.exit(main())
