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

    args = parser.parse_args(argv)
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
